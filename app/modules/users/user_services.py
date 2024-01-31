# app.modules.users.service.py

from datetime import datetime, timedelta
import sys
from typing import Optional

from sqlalchemy import or_
sys.path.append("..")
import string
import random
from sqlalchemy.orm import Session
from app.models.users import User, Token
from app.dto.users_schemas import ResponseData, RolesUpdate, UserSignUp, UserUpdate
from sqlalchemy.exc import IntegrityError
from app.auth.auth import get_password_hash, verify_password, get_current_user
from app.permissions.roles import Role, can_create
from app.config.database import msg

# Custom exception for duplicate error
class DuplicateError(Exception):
    pass

# Function to get users
def get_users(db: Session, current_user: get_current_user):
    query = db.query(User)
    if current_user.role == Role.SUPERADMIN:
        pass
    elif current_user.role == Role.MANAGER:
        query = query.filter(or_(User.ID == current_user.ID, User.role == Role.AGENT))
    elif current_user.role == Role.AGENT:
        query = query.filter(User.ID == current_user.ID)
    users = query.all()

    user_data = [user.to_dict() for user in users]
    return user_data

# Function to read user
def get_user(db: Session, user_id: int, current_user: get_current_user):
    user= db.query(User).filter(User.ID == user_id).first()
    if current_user.ID == user.ID:
        return user.to_dict()
    elif current_user.role == Role.AGENT:
        return None
    if not can_create(current_user.role, user.role):
        return None
    return user.to_dict()

# Function to add a new user
def add_user(db: Session, user: UserSignUp, current_user: get_current_user):
    if not can_create(current_user.role, user.role):
        return None
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
        
        return user.to_dict()
    except IntegrityError:
        db.rollback()
        return None


# Update User
def update_user(db: Session, user_id: int, user: UserUpdate,current_user: get_current_user):
    db_user = db.query(User).filter(User.ID == user_id).first()
    if current_user.ID == user_id:
        pass
    elif current_user.role== Role.AGENT:
        return ResponseData(
                    status=False,
                    message=msg['random_key_2'],
                    data={}
                )
    if not can_create(current_user.role, db_user.role):
        return ResponseData(
                    status=False,
                    message=msg['random_key_2'],
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
                message=msg['key_24'],
                data=db_user.to_dict()  # Convert user object to dictionary
            )
        else:
            # Old password does not match
            return ResponseData(
                status=False,
                message=msg['key_25'],
                data={}
            )
    else:
        return ResponseData(
            status=False,
            message=msg['key_26'],
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
            message=msg['key_26'],
            data={}
        )
    # using a can_create function defined in app/permissions/roles.py
    if not can_create(current_user.role, user_to_delete.role):
        return ResponseData(
                    status=False,
                    message=msg['random_key_2'],
                    data={}
                )
    db.delete(user_to_delete)
    db.commit()
    # Return a ResponseData model with the appropriate status, message, and data
    return ResponseData(
        status=True,
        message=msg['key_27'],
        data=user_to_delete.to_dict()
    )


# Function to update user roles
def update_roles(db: Session, user_id: int, current_user: get_current_user, user_update: RolesUpdate):
    user_to_update = db.query(User).filter(User.ID == user_id).first()
    updated_user = user_update.model_dump(exclude_unset=True)
    for key, value in updated_user.items():
        setattr(user_to_update, key, value)
    db.commit()
    response_data = ResponseData(
        status=True,
        message=msg['key_20'],
        data=user_to_update.to_dict() 
    )
    return response_data


# Function to reset user password for registered users
def user_reset_password(db: Session, email: str, new_password: str):
    try:
        user = db.query(User).filter(User.email == email).first()
        if user:
            user.password = get_password_hash(new_password)
            db.commit()
            return True
        else:
            return False
    except Exception as e:
        print(f"Error in user_reset_password: {e}")
        return False


# Function to validate OTP
def validate_otp_and_get_email(db: Session, otp: int):
    """
    Validate the OTP and return the associated user_email if valid.
    """
    token = db.query(Token).filter_by(otp=otp, is_expired=False).first()
    if token and not token.is_expired:
        return token.user_email
    return None


# Function to update the access_token status which was stored in Token model
def update_token_status(db: Session, expire_minutes: int):
    # Find tokens that are not expired and created more than `expire_minutes` minutes ago
    expired_tokens = db.query(Token).filter(
        Token.is_expired == False,
        Token.created_at < datetime.utcnow() - timedelta(minutes=expire_minutes)
    ).all()

    # Update the is_expired status for the found tokens
    for token in expired_tokens:
        token.is_expired = True

    # Commit the changes to the database
    db.commit()

    # Return True if at least one token was expired, otherwise False
    return len(expired_tokens) > 0


# Function to update the status of password 
def update_password_change_status(db: Session, otp: int):
    """
    Update the reset_password column to True for the given temp_token.
    """
    reset_token = db.query(Token).filter(Token.otp == otp).first()
    if reset_token:
        reset_token.reset_password = True
        db.commit()
        return True
    return False
