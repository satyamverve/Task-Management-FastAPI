# app/dto/users_schema.py

from __future__ import annotations
from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List
from app.permissions.roles import Role

class UserSignUp(BaseModel):
    email: EmailStr
    password: Optional[str]
    name: str
    role: Role

class UserUpdate(BaseModel):
    # password: Optional[str]
    name: Optional[str]
    role: Optional[Role]

class UserChangePassword(BaseModel):
    old_password: str
    new_password: str

class User(UserSignUp):
    # created_at: datetime
    class Config:
        from_attributes = True

class UserOut(BaseModel):
    ID : int
    email: EmailStr
    name: Optional[str]
    role: Role
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True

class UserMe(BaseModel):
    ID : int
    email: EmailStr
    name: Optional[str]
    created_at: datetime
    updated_at: datetime
    role: Role
    permissions: List[str]

class Token(BaseModel):
    access_token: str
    token_type: str
