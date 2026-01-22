from pydantic import BaseModel, EmailStr
from fastapi import Form
from typing import Optional
import uuid
from datetime import datetime

class UserModel(BaseModel):
    uid: uuid.UUID
    username: str
    email: EmailStr
    firstname: str
    lastname: str
    is_verified: bool = False
    created_at: datetime
    updated_at: datetime
    password: str


class UserCreateModel(BaseModel):
    username: str
    email: EmailStr
    firstname: str
    lastname: str
    password: str

class UserUpdateModel(BaseModel):
    username: str | None = None

class UserLoginModel(BaseModel):
    email: EmailStr
    password: str

class ResetPasswordModel(BaseModel):
    new_password: str
    confirm_password: str

class EmailModel(BaseModel):
    email: str

class RoleUpdateModel(BaseModel):
    role: str

class TokenUser(BaseModel):
    id: str
    email: str

class TokenData(BaseModel):
    user: TokenUser
    exp: int
    jti: str
    refresh: bool = False