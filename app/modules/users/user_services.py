# app.modules.users.service.py

import app.models
import sys
sys.path.append("..")
import string
import random
from fastapi import HTTPException, status, Body
from sqlalchemy.orm import Session
from Final_Demo.app.models.users import User
from app.dto.users_schemas import RolesUpdate, Token, UserSignUp, UserUpdate
from sqlalchemy.exc import IntegrityError
from Final_Demo.app.auth.auth import get_password_hash, verify_password
from app.models.users import Token
from datetime import datetime, timedelta
from app.auth.auth import get_current_user  
from app.permissions.roles import Role, can_create
from typing import List, Optional
from sqlalchemy import or_

# Custom exception for duplicate error
class DuplicateError(Exception):
    pass

# Function to update user roles
def update_roles(db: Session,user_id:int, current_user: get_current_user, user_update: RolesUpdate):
    user_to_update = db.query(User).filter(User.ID == user_id).first()
    if not user_to_update:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    updated_user = user_update.model_dump(exclude_unset=True)
    for key, value in updated_user.items():
        setattr(user_to_update, key, value)
    db.commit()
    return user_to_update

# Function to get users with optional filtering by user_id
def get_users(db: Session, current_user: get_current_user,user_id: Optional[int] = None):
    query = db.query(User)
    if current_user.role == Role.SUPERADMIN:
        pass
    elif current_user.role == Role.MANAGER:
        query = query.filter(or_(User.ID == current_user.ID, User.role == Role.AGENT))
    elif current_user.role == Role.AGENT:
        query = query.filter(User.ID == current_user.ID)
    if user_id:
        query = db.query(User).filter(User.ID == user_id).first()
        if not query:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return [query]
    tasks = query.all()
    return tasks


# Function to add a new user
def add_user(db: Session, user: UserSignUp,current_user: get_current_user):
    # using a can_create function defined in app/permissions/roles.py
    if not can_create(current_user.role, user.role):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Not enough permissions to access this resource"
        )
    password = user.password
    if not password:
        characters = string.ascii_letters + string.digits + string.punctuation
        password = ''.join(random.choice(characters) for i in range(10))
    user = User(
        email=user.email,
        password=get_password_hash(password),
        name=user.name,
        role=user.role
    )
    try:
        db.add(user)
        db.commit()
        return user, password
    except IntegrityError:
        db.rollback()
        raise DuplicateError(
            f"Email {user.email} is already attached to a registered user.")


# Function to update user information
def update_user(db: Session, user: UserUpdate,current_user: get_current_user):
    user_to_update = db.query(User).filter(User.ID == current_user.ID).first()
    if not user_to_update:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    # Update optional fields if provided
    if user.name is not None:
        user_to_update.name = user.name
    if user.name is None:
        pass
    if user.email is not None:
        user_to_update.email = user.email
    # Update password if provided
    if verify_password(user.old_password, user_to_update.password):  
        user_to_update.password = get_password_hash(user.new_password)
        db.commit()
    else:
        raise ValueError("Old password provided doesn't match, please try again")


# Function to delete a user
def delete_users(db: Session,
                current_user: get_current_user,
                user_id: str):
    user_to_delete = db.query(User).filter(User.ID == user_id).first()
    if not user_to_delete:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    # using a can_create function defined in app/permissions/roles.py
    if not can_create(current_user.role, user_to_delete.role):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Not enough permissions to access this resource"
        )
    db.delete(user_to_delete)
    db.commit()
    return user_to_delete


# Function to update password change status
def user_reset_password(db: Session, email: str, new_password: str):
    try:
        user = db.query(User).filter(User.email == email).first()
        user.password = get_password_hash(new_password)
        db.commit()
    except Exception:
        return False
    return True

# Function to update the acess_token status which was stored in Token model
def update_token_status(db: Session, expire_minutes: int):
    expired_tokens = db.query(Token).filter(Token.is_expired == expire_minutes).first()
    Token.created_at < datetime.utcnow() - timedelta(minutes=expire_minutes)
    if expired_tokens:
        expired_tokens.is_expired
        db.commit()
        return True
    return False


# Function to update the status of password 
def update_password_change_status(db: Session, temp_token: str):
    """
    Update the reset_password column to True for the given temp_token.
    """
    reset_token = db.query(Token).filter(Token.token == temp_token).first()
    if reset_token:
        reset_token.reset_password = True
        db.commit()
        return True
    return False