from fastapi import Request, Depends, status
from fastapi.security import HTTPBearer
from fastapi.security.http import HTTPAuthorizationCredentials
from fastapi.exceptions import HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession
from app.common.utils.utils import decode_access_token
from app.database.main import get_session
from app.auth.models import User
from app.auth.service import UserService
from app.auth.schemas.auth_schemas import TokenData

user_service = UserService()

class TokenBearer(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super().__init__(auto_error=auto_error)

    async def __call__(self, request: Request) -> HTTPAuthorizationCredentials:
        creds = await super().__call__(request)

        token = creds.credentials
        if not self.token_valid:
          ...  # raise InvalidTokenError()
        token_data = decode_access_token(token)

        self.verify_token_data(token_data)

        return token_data
    
    def verify_token_data(self, token_data: dict):
        raise NotImplementedError("Please Override this method in child classes")

    def token_valid(self, token: str) -> bool:
        token_data = decode_access_token(token)

        return True if token_data is not None else False
    
class AccessTokenBearer(TokenBearer):

    def verify_token_data(self, token_data: dict):
        if token_data and not token_data.get("refresh", False):
            return token_data
        raise HTTPException(
            detail="Invalid Access Token",
            status_code=status.HTTP_401_UNAUTHORIZED)

class RefreshTokenBearer(TokenBearer):

    def verify_token_data(self, token_data: dict):
        if token_data and token_data.get("refresh", False):
            return token_data
        raise HTTPException(
            detail="Invalid Refresh Token",
            status_code=status.HTTP_401_UNAUTHORIZED
        )

async def get_current_user(token_data: TokenData= Depends(AccessTokenBearer()),
                           session: AsyncSession = Depends(get_session)):
    user_email = token_data.get("user", {}).get("email")

    user = await user_service.get_user_by_email(session=session, email=user_email)

    return user

class RoleChecker:
    def __init__(self, allowed_roles: list[str]):

        self.allowed_roles = allowed_roles

    def __call__(self, current_user = Depends(get_current_user)):
        if not current_user.is_verified:
            raise HTTPException(
                detail="Operation not permitted. User is not verified.", 
                status_code=status.HTTP_403_FORBIDDEN
                )
        if current_user.role in self.allowed_roles:
            return True
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operation not permitted."
        )