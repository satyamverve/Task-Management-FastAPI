# app.modules.users.service.py

import sys
sys.path.append("..")
import string
import random
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models.users import User, Token
from app.dto.users_schemas import ResponseData, RolesUpdate, UserSignUp, UserUpdate
from sqlalchemy.exc import IntegrityError
from app.auth.auth import get_password_hash, verify_password, get_current_user
from datetime import datetime, timedelta
from app.permissions.roles import Role, can_create
from typing import Optional
from sqlalchemy import or_

# Custom exception for duplicate error
class DuplicateError(Exception):
    pass

# Function to update user roles
def update_roles(db: Session, user_id: int, current_user: get_current_user, user_update: RolesUpdate):
    user_to_update = db.query(User).filter(User.ID == user_id).first()
    updated_user = user_update.model_dump(exclude_unset=True)
    for key, value in updated_user.items():
        setattr(user_to_update, key, value)
    db.commit()
    response_data = ResponseData(
        status=True,
        message="User roles updated successfully",
        data=user_to_update.to_dict() # Use to_dict() instead of dict()
    )
    return response_data



# Read User
def get_user(db: Session, 
             user_id: int,
             current_user: get_current_user):
    user= db.query(User).filter(User.ID == user_id).first()
    # If the user is requesting their own details, allow it
    if current_user.ID == user.ID:
        return ResponseData(
            status=True,
            message="User Details",
            data=user.to_dict()
        )
    elif current_user.role== Role.AGENT:
        return ResponseData(
                    status=False,
                    message="Not Authorized to perform the requested action",
                    data={}
                )
    if not can_create(current_user.role, user.role):
        return ResponseData(
                    status=False,
                    message="Not Authorized to perform the requested action",
                    data={}
                )
    return ResponseData(
                status=True,
                message="User Details",
                data=user.to_dict()
            )


# Function to add a new user
def add_user(db: Session,
            user: UserSignUp,
            current_user: get_current_user):
    # using a can_create function defined in app/permissions/roles.py
    if not can_create(current_user.role, user.role):
        return ResponseData(
            status=False,
            message="Not Authorized to perform the requested action",
            data={}
        )
    password = user.password
    if not password:
        characters = string.ascii_letters + string.digits + string.punctuation
        password = ''.join(random.choice(characters) for i in range(10))
    user = User(
        email=user.email,
        password=get_password_hash(password),
        name=user.name,
        role=user.role,
        created_by=current_user.ID 
    )
    try:
        db.add(user)
        db.commit()
        
        return ResponseData(
            status=True,
            message="User created successfully",
            data=user.to_dict()
        )
    except IntegrityError:
        db.rollback()
        return ResponseData(
            status=False,
            message=f"Email {user.email} is already attached to a registered user.",
            data={}
        )

# Update User
def update_user(db: Session, user_id: int, user: UserUpdate,current_user: get_current_user):
    db_user = db.query(User).filter(User.ID == user_id).first()
    if current_user.ID == user_id:
        pass
    elif current_user.role== Role.AGENT:
        return ResponseData(
                    status=False,
                    message="Not Authorized to perform the requested action",
                    data={}
                )
    if not can_create(current_user.role, db_user.role):
        return ResponseData(
                    status=False,
                    message="Not Authorized to perform the requested action",
                    data={}
                )
    if db_user:
        # Check if the provided old password matches the stored password
        if verify_password(user.old_password, db_user.password):
            db_user.password = get_password_hash(user.new_password)
            for key, value in user.model_dump(exclude_unset=True).items():
                setattr(db_user, key, value)
            db_user.updated_by = current_user.ID
            db.commit()
            db.refresh(db_user)

            # Return the updated user details in the ResponseData model
            return ResponseData(
                status=True,
                message="User details updated successfully",
                data=db_user.to_dict()  # Convert user object to dictionary
            )
        else:
            # Old password does not match
            return ResponseData(
                status=False,
                message="Old password provided is incorrect",
                data={}
            )
    else:
        return ResponseData(
            status=False,
            message="User not found",
            data={}
        )


# Function to delete a user
def delete_users(db: Session,
                current_user: get_current_user,
                user_id: str):
    user_to_delete = db.query(User).filter(User.ID == user_id).first()
    if not user_to_delete:
        return ResponseData(
            status=False,
            message="User not found",
            data={}
        )
    # using a can_create function defined in app/permissions/roles.py
    if not can_create(current_user.role, user_to_delete.role):
        return ResponseData(
                    status=False,
                    message="Not Authorized to perform the requested action",
                    data={}
                )
    db.delete(user_to_delete)
    db.commit()

    # Return a ResponseData model with the appropriate status, message, and data
    return ResponseData(
        status=True,
        message=f"User {user_id} has been deleted successfully!",
        data=user_to_delete.to_dict()
    )


# Function to reset user password for registered users
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