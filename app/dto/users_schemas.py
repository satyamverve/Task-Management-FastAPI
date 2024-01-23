# app/dto/users_schema.py

from __future__ import annotations
from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional
from app.permissions.roles import Role

class UserSignUp(BaseModel):
    email: EmailStr
    password: Optional[str]
    name: str
    role: Role

class RolesUpdate(BaseModel):
    role: Optional[Role]

class UserUpdate(BaseModel):
    name: Optional[str]
    email: Optional[EmailStr]
    old_password: str
    new_password: str

class UserOut(BaseModel):
    ID : int
    email: EmailStr
    name: Optional[str]
    role: Role
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
