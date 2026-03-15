from sqlmodel import SQLModel, Field, Column
import sqlalchemy.dialects.postgresql as pg
from datetime import datetime   
from typing import Optional
import uuid

class User(SQLModel, table=True):
    __tablename__ = "users" # type: ignore
    id: uuid.UUID = Field(
         sa_column=Column(pg.UUID(),
                          primary_key=True,
                         default=uuid.uuid4,
                         unique=True,
                         index=True,
                         nullable=False))
    username: str
    email: str
    firstname: str
    lastname: str
    is_verified: bool = Field(default=False)
    created_at: datetime = Field(
        sa_column=Column(
        pg.TIMESTAMP,
        nullable=False,
        default=datetime.now
        )
    )
    updated_at: datetime = Field(
        sa_column=Column(
        pg.TIMESTAMP,
        nullable=False,
        default=datetime.now
        )
    )
    password: str

    def __repr__(self):
        return f"<User> {self.username}"