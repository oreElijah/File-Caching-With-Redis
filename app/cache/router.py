from app.common.utils.router import VersionRouter
from fastapi import UploadFile, status, Depends
from fastapi.responses import FileResponse
from fastapi.exceptions import HTTPException
import json
import time
from sqlmodel.ext.asyncio.session import AsyncSession
from app.common.utils.response import HTTPResponse
from app.common.utils.dependencies import get_current_user, AccessTokenBearer
from app.database.main import get_session
from app.auth.models import User
from app.cache.schemas.upload_response_schema import FileMetadataResponseModel
from app.cache.service import FileService
from app.redis.main import store_metadata, get_stored_metadata

cache_route = VersionRouter(
    version="1",
    path="file",
    tags=["file"]
)

HTTP_201_CREATED = 201
HTTP_200_OK = 200

file_service = FileService()

@cache_route.post("/store_file", response_model=HTTPResponse[FileMetadataResponseModel])
async def store_file(file: UploadFile,
                     session: AsyncSession= Depends(get_session),
                        user: User= Depends(get_current_user)
                     ):
    user_id = user.uid

    metadata = await file_service.extract_metadata(file)

    new_file = await file_service.store_file_metadata(session, user_id, metadata)

    await store_metadata(str(new_file.id), metadata)
    
    return HTTPResponse(
        message="Successfully stored file",
        data=new_file,
        status_code=HTTP_201_CREATED)

@cache_route.get(
    "/get_file_by_cache/{file_id}",
    response_model=HTTPResponse[FileMetadataResponseModel]
)
async def get_file_metadata_by_cache(
    file_id: str,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    start = time.perf_counter()
    cached = await get_stored_metadata(file_id)

    if cached:
        cached = json.loads(cached.decode())
        if cached["user_id"] != str(user.uid):
            raise HTTPException(status_code=401, detail="Access denied")

        duration = time.perf_counter() - start
        print(f"CACHE HIT: {duration:.4f}s")

        return HTTPResponse(
            message="Data retrieved from cache",
            data=cached,
            status_code=HTTP_200_OK
        )

    metadata = await file_service.get_file_by_id(session, file_id)

    if not metadata:
        raise HTTPException(status_code=404, detail="File not found")

    if str(metadata.user_id) != str(user.uid):
        raise HTTPException(status_code=401, detail="Access denied")

    await store_metadata(file_id, metadata)

    duration = time.perf_counter() - start
    print(f"DB HIT: {duration:.4f}s")

    return HTTPResponse(
        message="Data retrieved from DB and cached",
        data=metadata,
        status_code=HTTP_200_OK
    )





@cache_route.get("/get_file_by_db/{file_id}", response_model=HTTPResponse[FileMetadataResponseModel])
async def get_file_metadata_by_db(file_id: str,
                        user: User= Depends(get_current_user),
                     session: AsyncSession= Depends(get_session)):
    start = time.perf_counter()
    file = await file_service.get_file_by_id(session, file_id)
    duration = time.perf_counter() - start
    print(f"DB HIT: {duration:.4f}s")

    if file:
        if file.user_id == user.uid:
            return HTTPResponse(
                message=f"Data retrieved from db",
                data=file,
                status_code=HTTP_200_OK
            )
        raise HTTPResponse(
            message="You don't have access to this file",
            data={},
            status_code=401
        )
    raise HTTPResponse(
            message="File Doesn't exist",
            data={},
            status_code=401
        )
@cache_route.get("/files/{file_id}/download")
async def download_file(file_id: str):
    metadata = await get_stored_metadata(file_id)
    if not metadata:
        raise HTTPResponse(
            message="Metadata not found",
            data=None,
            status_code=404
        )
    metadata = json.loads(metadata.decode())
    return FileResponse(
        path=metadata["storage_path"],
        filename=metadata["filename"],
        media_type=metadata["content_type"]
    )