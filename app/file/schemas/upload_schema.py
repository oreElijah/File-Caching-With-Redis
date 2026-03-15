from pydantic import BaseModel
from datetime import datetime
from typing import Optional
import uuid

class FileMetadataModel(BaseModel):#Change model to schema scema is for validation while model is for anything related to database One schema to one python file
    id: uuid.UUID
    filename: str
    content_type: str
    size: int
    storage_path: str
    user_id: uuid.UUID
    uploaded_at: datetime

class FileMetadatCreateModel(BaseModel):
    filename: str
    content_type: str
    size: int
    storage_path: str

class FileModel(BaseModel):
    name: Optional[str]
    path: str
    content_type: Optional[str]
    size: Optional[int]
