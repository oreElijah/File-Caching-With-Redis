from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi.encoders import jsonable_encoder
from fastapi import UploadFile, Depends
from datetime import datetime
from sqlmodel import select
import uuid
import time
import json
import os
from app.file.model import File
from app.database.main import get_session
from settings.config import get_config, Configs
from app.caches.service import Cache, get_cache_service, CacheService
from app.file.schemas.upload_schema import FileMetadatCreateModel, FileModel

class FileService:
    def __init__(self, cache_service: CacheService, session: AsyncSession= Depends(get_session), config: Configs= Depends(get_config)):
        self.session = session
        self.cache_service = cache_service
        self.config = config


    async def get_file(self):
        stmt = select(File)

        result = await self.session.exec(stmt)

        return result.all()
    
    async def store_file_metadata(self, user_id: str, model: FileMetadatCreateModel) -> File:
        new_model = model.model_dump()

        file = File(**new_model, user_id=uuid.UUID(user_id))

        self.session.add(file)

        await self.session.commit()

        return file
    
    async def extract_metadata(self, file: UploadFile) -> FileMetadatCreateModel:
        content = await file.read()

        size = len(content)

        filename = f"{uuid.uuid4()}_{file.filename}"
        
        upload_dir = self.config.UPLOAD_PATH
        os.makedirs(upload_dir, exist_ok=True)
        storage_path = os.path.join(upload_dir, filename)

        with open(storage_path, "wb") as f:
            f.write(content)
        file.file.seek(0)

        return FileMetadatCreateModel(
        filename=file.filename,  # type: ignore
        content_type=file.content_type, # type: ignore
        size=size,
        storage_path=storage_path,
    )

    async def get_file_by_id(self, file_id: str):
        stmt = select(File).where(file_id==File.id)

        result = await self.session.exec(stmt)

        return result.first()
    
    async def get_file_by_Owners_id(self, session: AsyncSession, user_id: str):
        stmt = select(File).where(user_id==File.user_id)

        result = await session.exec(stmt)

        return result.all()
    
    async def upload_file(self, file: UploadFile, user_id: str) -> File:
        metadata = await self.extract_metadata(file)

        new_file = await self.store_file_metadata(user_id, metadata)

        file_data = jsonable_encoder(new_file)
        await self.cache_service.set(
            str(new_file.id),
              json.dumps(file_data),
                exp=self.config.CACHE_EXPIRATION_TIME
                ) # type: ignore

        return new_file

    async def get_file_metadata_by_cache(self, file_id: str): 
        start = time.perf_counter()
        cached = await self.cache_service.get(file_id)

        if cached:
            duration = time.perf_counter() - start
            print(f"CACHE HIT: {duration:.4f}s")
            return {"metadata": json.loads(cached.decode()), "from_cache": True}


        metadata = await self.get_file_by_id(file_id=file_id)

        if not metadata:
            return {"metadata": None, "from_cache": False}
        
        data = jsonable_encoder(metadata)

        await self.cache_service.set(file_id, json.dumps(data), exp=Config.CACHE_EXPIRATION_TIME) # type: ignore
        duration = time.perf_counter() - start
        print(f"DB HIT: {duration:.4f}s")
        
        return {"metadata":metadata, "from_cache": False}
    
    async def get_file_metadata_by_db(self, file_id: str):
        start = time.perf_counter()
        metadata = await self.get_file_by_id(file_id=file_id)
        duration = time.perf_counter() - start
        print(f"DB HIT: {duration:.4f}s")

        return metadata
    
    async def download_file(self, file_id: str):
        metadata = await self.get_file_metadata_by_cache(file_id=file_id)

        if not metadata:
            return None
        
        return metadata
    
def get_file_service(
    config: Configs = Depends(get_config) ,
    cache_service: Cache = Depends(get_cache_service), # type: ignore
    session: AsyncSession = Depends(get_session),
    ):
        return FileService(cache_service, session, config)