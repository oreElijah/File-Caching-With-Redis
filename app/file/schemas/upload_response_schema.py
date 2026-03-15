from pydantic import BaseModel, ConfigDict
from datetime import datetime
import uuid

class FileMetadataResponseModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    filename: str
    content_type: str
    size: int
    storage_path: str
    user_id: uuid.UUID
    uploaded_at: datetime