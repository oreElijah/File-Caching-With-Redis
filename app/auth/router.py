from fastapi import Depends, status, BackgroundTasks, UploadFile, File
from fastapi.exceptions import HTTPException
from datetime import timedelta
from typing import List
from settings.config import Config
from app.auth.models import User
from app.auth.service import AuthService
from typing import Annotated
from app.redis.main import add_jti_to_blocklist
from app.common.utils.router import VersionRouter
from app.user.service import UserService
from app.common.utils.response import HTTPResponse
from app.common.utils.dependencies import get_current_user, RoleChecker, AccessTokenBearer, RefreshTokenBearer
from app.auth.schemas.forgot_password_schema import ForgotPasswordRequestSchema
from app.auth.schemas.login_schema import LoginResponseSchema, LoginRequestSchema
from app.auth.schemas.register_schema import RegisterRequestSchema, RegisterResponseSchema
from app.common.utils.utils import create_access_token, create_url_safe_token, decode_url_safe_token, verify_password, generate_password_hash
from January_project.app.auth.schemas.login_schema import UserCreateModel, UserLoginModel, UserUpdateModel, ResetPasswordModel, EmailModel

auth_router = VersionRouter(
    version="1",
    path="auth",
    tags=["auth"]
)

@auth_router.post("/register", response_model=HTTPResponse[RegisterResponseSchema], status_code=status.HTTP_201_CREATED)
async def create_user(auth_service: Annotated[AuthService, Depends(AuthService)],
    user_model: RegisterRequestSchema
                      ):
    user = await auth_service.register(user_model)

    return HTTPResponse(
            message="User registered successfully. Please check your email to verify your account.",
            data=RegisterResponseSchema(user=user),
            status_code=status.HTTP_201_CREATED
        )
    
@auth_router.get("/verify/{token}", response_model=HTTPResponse[RegisterResponseSchema])
async def verify_email(auth_service: Annotated[AuthService, Depends(AuthService)],token: str):
    token_data = decode_url_safe_token(token)

    email = token_data.get("email")
    user = await auth_service.get_user_by_email(email)
    if user is not None:
        print(user)
        await auth_service.update_user(user, {"is_verified": True})
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
async def login_user(auth_service: Annotated[AuthService, Depends(AuthService)],login_schema: LoginRequestSchema):
    user = await auth_service.login(login_schema)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User with this email does not exist"
        )
    else:

        return HTTPResponse(
                message="Login successful",
                data=LoginResponseSchema(
                    access_token=user.access_token,
                    refresh_token=user.refresh_token
                ),
                status_code=status.HTTP_200_OK
            )
    
@auth_router.post("/forgot_password")
async def forgot_password(auth_service: Annotated[AuthService, Depends(AuthService)], model: ForgotPasswordRequestSchema):
    user = await auth_service.ForgotPassword(model)

    return HTTPResponse(
            message="Check email to reset your password",
            data= user,
            status_code=status.HTTP_202_ACCEPTED
        )
    
@auth_router.post("/reset_password/{token}")
async def reset_password(user_service: Annotated[UserService, Depends(UserService)],token: str, model: ResetPasswordModel):
    token_data = decode_url_safe_token(token)

    email = token_data.get("email")
    user = await user_service.get_user_by_email(email)
    if user is not None:
        hashed_password = generate_password_hash(model.new_password)
        await user_service.update_user(user, {"password": hashed_password})
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
