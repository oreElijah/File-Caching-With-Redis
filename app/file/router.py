from fastapi import UploadFile, status, Depends, File
from app.common.utils.router import VersionRouter
from fastapi.exceptions import HTTPException
from fastapi.responses import FileResponse
from typing import Annotated
from app.user.models import User
from app.common.utils.response import HTTPResponse
from app.file.service import FileService, get_file_service
from app.common.utils.dependencies import get_current_user, AccessTokenBearer
from app.file.schemas.upload_response_schema import FileMetadataResponseModel

cache_route = VersionRouter(
    version="1",
    path="file",
    tags=["file"]
)

HTTP_201_CREATED = 201
HTTP_200_OK = 200

# file_service = FileService()

@cache_route.post("/store_file", response_model=HTTPResponse[FileMetadataResponseModel])
async def store_file(file_service: Annotated[FileService, Depends(get_file_service)],
                        file: UploadFile = File(...),
                            user: User= Depends(get_current_user)
                     ):
    user_id = str(user.id)

    new_file = await file_service.upload_file(file, user_id)

    file_data = new_file.model_dump()
    
    return HTTPResponse(
        message="File stored successfully",
        data=FileMetadataResponseModel(**file_data),
        status_code=HTTP_201_CREATED
    )

@cache_route.get(   "/get_file_by_cache/{file_id}", response_model=HTTPResponse[FileMetadataResponseModel])
async def get_file_metadata_by_caching(
    file_service: Annotated[FileService, Depends(FileService)],
    file_id: str,
    user: User = Depends(get_current_user),
):
    result = await file_service.get_file_metadata_by_cache(file_id=file_id)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    metadata = result["metadata"]
    if result["from_cache"]:
        message="Data retrieved from cache"

    else:
        message="Data retrieved from DB and cached"


    return HTTPResponse(
       message =message,
        data=FileMetadataResponseModel(**metadata),
        status_code=HTTP_200_OK
    )

@cache_route.get("/get_file_by_db/{file_id}", response_model=HTTPResponse[FileMetadataResponseModel])
async def get_file_metadata_by_hitting_db(file_service: Annotated[FileService, Depends(get_file_service)],
                        file_id: str,
                        user: User= Depends(get_current_user)):
    file = await file_service.get_file_metadata_by_db(file_id=file_id)

    if file:
        if file.user_id == user.id:
            return HTTPResponse(
                message=f"Data retrieved from db",
                data=file,
                status_code=HTTP_200_OK
            )
        
@cache_route.get("/files/{file_id}/download")
async def download_file(file_id: str, file_service: Annotated[FileService, Depends(get_file_service)]):
    metadata = await file_service.download_file(file_id=file_id)
    if not metadata:
        raise HTTPException(
            detail="File Doesn't exist",
            status_code=404
        )
    metadata = metadata["metadata"]
    return FileResponse(
        path=metadata["storage_path"],
        filename=metadata["filename"],
        media_type=metadata["content_type"]
    )