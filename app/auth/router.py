from fastapi import Depends, status, BackgroundTasks, UploadFile, File
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi.exceptions import HTTPException
from datetime import timedelta
from typing import List
from settings.config import Config
from app.auth.models import User
from app.database.main import get_session
from app.auth.service import UserService
from app.mail.main import create_message, mails
from app.redis.main import add_jti_to_blocklist
from app.common.utils.router import VersionRouter
from app.common.utils.response import HTTPResponse
from app.common.utils.dependencies import get_current_user, RoleChecker, AccessTokenBearer, RefreshTokenBearer
from app.auth.schemas.auth_response_schema import UserResponseSchema, RegisterResponseSchema, LoginResponseSchema
from app.common.utils.utils import create_access_token, create_url_safe_token, decode_url_safe_token, verify_password, generate_password_hash
from app.auth.schemas.auth_schemas import UserCreateModel, UserLoginModel, UserUpdateModel, ResetPasswordModel, EmailModel

auth_router = VersionRouter(
    version="1",
    path="auth",
    tags=["auth"]
)
user_service = UserService()
CHUNK_SIZE = 1024*1024


@auth_router.get("/users", response_model=HTTPResponse[List[UserResponseSchema]])
async def get_users(session: AsyncSession= Depends(get_session), _: dict= Depends(AccessTokenBearer())):
    users = await user_service.get_all_users(session=session)

    if users is not None:
        return HTTPResponse(message="Users retrieved successfully", data=users, status_code=status.HTTP_200_OK)
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
                         detail="Sorry, no users found")


@auth_router.post("/register", response_model=HTTPResponse[RegisterResponseSchema], status_code=status.HTTP_201_CREATED)
async def create_user(user_model: UserCreateModel,
                      background_tasks: BackgroundTasks,
                      session: AsyncSession= Depends(get_session)):
    user_exists = await user_service.user_exists(session=session, email=user_model.email)

    if user_exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    
    else:
        user= await user_service.create_user(session=session, user_data=user_model)
        
        token = create_url_safe_token({"email": user.email})
        print(token)

        link = f"http://{Config.DOMAIN}/api/v1/auth/verify/{token}"
        html_message = f"""
        <h1>Verify your email</h1>
        <p> Please click the link below to verify your email address:</p>
        <a href="{link}">Verify Email</a>
        """
        message = create_message(
            subject="Please verify your email",
            recipients=[user_model.email],
            body=html_message
        )
        background_tasks.add_task(mails.send_message, message)

        return HTTPResponse(
            message="User registered successfully. Please check your email to verify your account.",
            data=RegisterResponseSchema(user=user),
            status_code=status.HTTP_201_CREATED
        )
    
@auth_router.get("/verify/{token}", response_model=HTTPResponse[UserResponseSchema])
async def verify_email(token: str, session: AsyncSession= Depends(get_session)):
    token_data = decode_url_safe_token(token)

    email = token_data.get("email")
    user = await user_service.get_user_by_email(email, session)
    if user is not None:
        print(user)
        await user_service.update_user(user, {"is_verified": True}, session)
        return HTTPResponse(
            message="Email verified successfully",
            data=user,
            status_code=status.HTTP_200_OK
        )
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Invalid token or user does not exist"
    )

@auth_router.post("/login", response_model=HTTPResponse[LoginResponseSchema])
async def login_user(login_schema: UserLoginModel, session: AsyncSession= Depends(get_session)):
    user_exists = await user_service.user_exists(email=login_schema.email, session=session)

    if user_exists is False:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User with this email does not exist"
        )
    else:
        user = await user_service.get_user_by_email(email=login_schema.email, session=session)

        print(user)
        password = login_schema.password
        hashed_password = user.password_hash 

        if user is not None:
            password_valid = verify_password(plain_password=password, hashed_password=hashed_password)
            if not password_valid:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid credentials"
                )
            access_token = create_access_token(
                user_data={
                    "id": str(user.uid),
                    "email": user.email
                    }
                    )
            
            refresh_token = create_access_token(
                user_data={
                    "id": str(user.uid),
                    "email": user.email
                    },
                refresh=True,
                expiry_time=timedelta(days=Config.REFRESH_TOKEN_EXPIRE_DAYS)
                    )
            return HTTPResponse(
                message="Login successful",
                data=LoginResponseSchema(
                    access_token=access_token,
                    refresh_token=refresh_token
                ),
                status_code=status.HTTP_200_OK
            )

@auth_router.get("/profile", response_model=HTTPResponse[UserResponseSchema])
async def get_current_user_profile(current_user = Depends(get_current_user), token: str= Depends(AccessTokenBearer())):
    return HTTPResponse(
        message="User profile retrieved successfully",
        data=current_user,
        status_code=status.HTTP_200_OK
    )

@auth_router.put("/profile_update", response_model=HTTPResponse[UserResponseSchema])
async def update_current_user_profile(user_update_model: UserUpdateModel,
                                        current_user: User= Depends(get_current_user),
                                        session: AsyncSession= Depends(get_session)):
    if current_user is not None:
        updated_user = await user_service.update_user(current_user, user_update_model, session)
    
        return HTTPResponse(
            message="User profile updated successfully",
            data=updated_user,
            status_code=status.HTTP_200_OK
        )
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="User not found"
    )
    
@auth_router.post("/forgot_password")
async def forgot_password(model: EmailModel, background_tasks: BackgroundTasks, session: AsyncSession= Depends(get_session)):
    email = model.email

    user_exist = await user_service.user_exists(email, session)
    if not user_exist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "message": "User with email does not exist"
            }
        )
    else:
        user = await user_service.get_user_by_email(email, session)

        token = create_url_safe_token({"email": email})

        link = f"http://{Config.DOMAIN}/api/v1/auth/reset_password/{token}"
        html_message = f"""
        <h1>Forgot Password</h1>
        <p> Please click the link below to create new password:</p>
        <a href="{link}">Reset password</a>
        """
        message = create_message(
            subject="Welcome to Shortlet",
                recipients=[email],
                body=html_message
        )
        background_tasks.add_task(mails.send_message, message)

        return HTTPResponse(
            message="Check email to reset your password",
            data= user,
            status_code=status.HTTP_202_ACCEPTED
        )
    
@auth_router.post("/reset_password/{token}")
async def reset_password(token: str, model: ResetPasswordModel, session: AsyncSession= Depends(get_session)):
    token_data = decode_url_safe_token(token)

    email = token_data.get("email")
    user = await user_service.get_user_by_email(email, session)
    if user is not None:
        hashed_password = generate_password_hash(model.new_password)
        await user_service.update_user(user, {"password": hashed_password}, session)
        return HTTPResponse(
            message="Password reset successfully",
            data=None,
            status_code=status.HTTP_200_OK
        )
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Invalid token or user does not exist"
    )

@auth_router.get("/logout")
async def logout_user(token_data: dict= Depends(AccessTokenBearer())):
    jti = token_data.get("jti")
    await add_jti_to_blocklist(jti)

    return HTTPResponse(
        message="Logout successful",
        data=None,
        status_code=status.HTTP_200_OK
    )

@auth_router.post("/refresh")
async def refresh_token(token_detail: dict= Depends(RefreshTokenBearer())):
    if token_detail.get("refresh"):
        new_access_token = create_access_token(
            user_data={
                "id": token_detail.get("id"),
                "email": token_detail.get("email"),
                "role": token_detail.get("role")
            }
        )
        return HTTPResponse(
            message="Access token refreshed successfully",
            data={"access_token": new_access_token},
            status_code=status.HTTP_200_OK
        )
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid refresh token"
    )

# @auth_router.get("/update_role")
# async def register_as_a_host(session: AsyncSession= Depends(get_session), token:dict=Depends(AccessTokenBearer()), user: User= Depends(get_current_user)):
#     if user is not None:
#         updated_user = await user_service.update_user(user, {"role": "admin"}, session)

#         return {
#             "message": "You are now registered as a host",
#             "user": updated_user
#         }
#     else:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail={
#                 "message": "user not found"
#             }
#         )