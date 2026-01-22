from sqlmodel import SQLModel, Field, Column
import sqlalchemy.dialects.postgresql as pg
from datetime import datetime
import uuid

class File(SQLModel, table=True):
    __tablename__="file"
    id: uuid.UUID = Field(
         sa_column=Column(pg.UUID(),
                          primary_key=True,
                         default=uuid.uuid4,
                         unique=True,
                         index=True,
                         nullable=False))
    filename: str
    content_type: str
    size: int
    checksum: str
    storage_path: str
    user_id: uuid.UUID = Field(
        foreign_key="users.uid"
    )
    uploaded_at: datetime = Field(
        sa_column=Column(
        pg.TIMESTAMP,
        nullable=False,
        default=datetime.now
        )
    )