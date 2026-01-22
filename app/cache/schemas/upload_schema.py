from pydantic import BaseModel
from datetime import datetime
import uuid

class FileMetadataModel(BaseModel):
    id: uuid.UUID
    filename: str
    content_type: str
    size: int
    checksum: str
    storage_path: str
    user_id: uuid.UUID
    uploaded_at: datetime

class FileMetadatCreateModel(BaseModel):
    filename: str
    content_type: str
    size: int
    checksum: str
    storage_path: str