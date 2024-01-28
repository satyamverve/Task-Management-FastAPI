# app/dto/users_schema.py

from __future__ import annotations
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional
from app.permissions.roles import Role

class UserLoginSchema(BaseModel):
    """
    Pydantic model for user login credentials.
    """
    email: EmailStr = Field(...)
    password: str = Field(...)

    class Config:
        schema_extra = {
            "example": {
                "email": "sk@x.com",
                "password": "weakpassword"
            }
        }

class UserSignUp(BaseModel):
    """
    Pydantic model for user registration.
    """
    email: EmailStr
    password: Optional[str]
    name: str
    role: Role

class RolesUpdate(BaseModel):
    """
    Pydantic model for updating user roles.
    """
    role: Optional[Role]

class UserUpdate(BaseModel):
    """
    Pydantic model for updating user details.
    """
    name: Optional[str]
    email: Optional[EmailStr]
    old_password: str
    new_password: str

class UserOut(BaseModel):
    """
    Pydantic model for returning user details.
    """
    ID: int
    email: EmailStr
    name: Optional[str]
    role: Role
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    """
    Pydantic model for representing authentication token details.
    """
    access_token: str
    token_type: str
