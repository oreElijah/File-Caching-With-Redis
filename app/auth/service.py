from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi import Depends, HTTPException, status, BackgroundTasks
from sqlmodel import select
from typing import Annotated
from app.auth.models import User
from app.database.main import get_session
from app.auth.utils import create_access_token, create_url_safe_token
from datetime import timedelta
from app.auth.schemas.forgot_password_schema import ForgotPasswordRequestSchema
from app.auth.schemas.login_schema import LoginRequestSchema, LoginResponseSchema
from app.auth.schemas.register_schema import RegisterRequestSchema, RegisterResponseSchema
from app.common.utils.response import HTTPResponse
from app.mail.service import MailService
from app.user.service import UserService
from app.common.utils.utils import generate_password_hash, verify_password
from settings.config import GlobalConfig

class AuthService:
    def __init__(self,
                 config: GlobalConfig,
                 background_tasks: BackgroundTasks,
                 user_service: Annotated[UserService, Depends(UserService)],
                 mail_service: Annotated[MailService, Depends(MailService)],
                session: AsyncSession= Depends(get_session)):
        self.session = session
        self.config = config
        self.user_service = user_service
        self.mail_service = mail_service
    
    async def login(self, login_data: LoginRequestSchema) -> LoginResponseSchema | None:
        user = self.user_service.user_exists(email=login_data.email)

        if user is None:
            raise HTTPException(
             status_code=status.HTTP_404_NOT_FOUND,
            detail="User with this email does not exist"
        )
        else:
            email = login_data.email

            print(user)
            password = login_data.password
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
                    expiry_time=timedelta(days=self.config.REFRESH_TOKEN_EXPIRE_DAYS)
                        )
                return {
                    "access_token": access_token,
                    "refresh_token": refresh_token
                }
    
    async def register(self, register_data: RegisterRequestSchema) -> RegisterResponseSchema | None:
        user_exists = self.user_service.user_exists(email= register_data.email)

        if user_exists:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists"
            )
        
        else:
            user= await self.user_service.create_user(user_data=register_data)
            
            token = create_url_safe_token({"email": user.email})
            
            self.background_tasks.add_task(self.mail_service.send_verify_mail, first_name=user.firstname, email=user.email, verify_token=token)

            return user

    async def ForgotPassword(self, forgot_password_data: ForgotPasswordRequestSchema) -> User | None:
        user_exists = self.user_service.user_exists(email= forgot_password_data.email)

        if user_exists:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists"
            )
        
        else:
            user= await self.user_service.create_user(user_data=forgot_password_data)
            
            token = create_url_safe_token({"email": user.email})
            
            self.background_tasks.add_task(self.mail_service.send_password_reset, first_name=user.firstname, email=user.email, token=token)

            return user