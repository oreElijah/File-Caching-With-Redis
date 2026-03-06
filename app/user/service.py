from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi import Depends
from sqlmodel import select
from app.auth.models import User
from app.database.main import get_session
from January_project.app.auth.schemas.login_schema import UserCreateModel
from app.common.utils.utils import generate_password_hash

class UserService:
    def __init__(self, session: AsyncSession= Depends(get_session)):
        self.session = session

    async def get_all_users(self) -> list[User]:
        stmt = select(User)
        
        result = await self.session.exec(stmt)
        
        return result.all()

    async def get_user_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email)

        result = await self.session.exec(stmt)
        
        return result.first()
    
    async def get_user_by_id(self, id: str) -> User | None:
        stmt = select(User).where(User.uid == id)

        result = await self.session.exec(stmt)
        
        return result.first()

    async def user_exists(self, email: str) -> bool:
        user = await self.get_user_by_email(email)
        return user is not None
    
    async def create_user(self, user_data: UserCreateModel) -> User:
        user_data_dict = user_data.model_dump()

        user = User(**user_data_dict)

        user.password_hash = generate_password_hash(user_data_dict["password"])

        self.session.add(user)

        await self.session.commit()

        return user
    
    async def update_user(self, user: User, user_data: dict) -> User:
        for key, value in user_data.items():
            setattr(user, key, value)
        
        await self.session.commit()
        
        return user