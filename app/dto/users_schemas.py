# app/dto/users_schema.py

from __future__ import annotations
from pydantic import BaseModel, EmailStr, Field
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
                "email": "email@gmail.com",
                "password": "weakpassword"
            }
        }

class UserSignUp(BaseModel):
    """
    Pydantic model for user registration.
    """
    email: EmailStr
    password: str
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
