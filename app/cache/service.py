from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from fastapi import UploadFile, Depends
import uuid
from app.cache.model import File
from app.database.main import get_session
from app.common.utils.utils import generate_hash
from settings.config import Config
from app.cache.schemas.upload_schema import FileMetadatCreateModel, FileMetadataModel

class FileService:
    def __init__(self, session: AsyncSession= Depends(get_session)):
        self.session = session

    async def get_file(self):
        stmt = select(File)

        result = self.session.exec(stmt)

        return result.all()
    
    async def store_file_metadata(self, user_id: str, model: FileMetadatCreateModel) -> File:
        new_model = model.model_dump()

        file = File(**new_model, user_id=user_id)

        self.session.add(file)

        await self.session.commit()

        return file
    
    async def extract_metadata(self, file: UploadFile) -> FileMetadatCreateModel:
        content = await file.read()

        checksum = generate_hash(content)
        size = len(content)

        filename = f"{uuid.uuid4()}_{file.filename}"
        
        storage_path = (
            f"{Config.path}{file.filename}"
        )
        with open(storage_path, "wb") as f:
            f.write(content)
        file.file.seek(0)

        return FileMetadatCreateModel(
        filename=file.filename,
        content_type=file.content_type,
        size=size,
        checksum=checksum,
        storage_path=storage_path,
    )

    async def get_file_by_id(self, session: AsyncSession, file_id: str) -> FileMetadataModel:
        stmt = select(File).where(file_id==File.id)

        result = await session.exec(stmt)

        return result.first()
    
    async def get_file_by_Owners_id(self, session: AsyncSession, user_id: str):
        stmt = select(File).where(user_id==File.user_id)

        result = session.exec(stmt)

        return result.all()
