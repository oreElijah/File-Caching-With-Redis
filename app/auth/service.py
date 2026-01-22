from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from app.auth.models import User
from app.auth.schemas.auth_schemas import UserCreateModel
from app.common.utils.utils import generate_password_hash

class UserService:
    async def get_all_users(self, session: AsyncSession) -> list[User]:
        stmt = select(User)
        
        result = await session.exec(stmt)
        
        return result.all()

    async def get_user_by_email(self, email: str, session: AsyncSession) -> User | None:
        stmt = select(User).where(User.email == email)

        result = await session.exec(stmt)
        
        return result.first()
    
    async def get_user_by_id(self, id: str, session: AsyncSession) -> User | None:
        stmt = select(User).where(User.uid == id)

        result = await session.exec(stmt)
        
        return result.first()

    async def user_exists(self, email: str, session: AsyncSession) -> bool:
        user = await self.get_user_by_email(email, session)
        return user is not None
    
    async def create_user(self, user_data: UserCreateModel, session: AsyncSession) -> User:
        user_data_dict = user_data.model_dump()

        user = User(**user_data_dict)

        user.password_hash = generate_password_hash(user_data_dict["password"])

        session.add(user)

        await session.commit()

        return user
    
    async def update_user(self, user: User, user_data: dict, session: AsyncSession) -> User:
        for key, value in user_data.items():
            setattr(user, key, value)
        
        await session.commit()
        
        return user