# app.modules.users.service.py

import sys
import string
import random

sys.path.append("..")

from sqlalchemy.orm import Session
from Final_Demo.app.models.users import User
import Final_Demo.app.dto.users_schemas as users_schemas
from sqlalchemy.exc import IntegrityError
from Final_Demo.app.auth.auth import get_password_hash, verify_password
from app.models.users import Token
from datetime import datetime, timedelta
TEMP_TOKEN_EXPIRE_MINUTES = 1
class DuplicateError(Exception):
    pass

# CREATE User
def add_user(db: Session, user: users_schemas.UserSignUp):
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


# UPDATE User
def update_user(db: Session,user_id:int, user_update: users_schemas.UserUpdate):
    user = db.query(User).filter(User.ID == user_id).first()
    if not user:
        raise ValueError(
            f"There isn't any user with username {email}")
    updated_user = user_update.dict(exclude_unset=True)
    for key, value in updated_user.items():
        setattr(user, key, value)
    db.commit()
    return user


# Read User
def get_user(db: Session, user_id: int):
    # print("hello")
    user= db.query(User).filter(User.ID == user_id).first()
    if user:
        return user
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

# DELETE User
def delete_user(db: Session, email: str):
    user_cursor = db.query(User).filter(User.email == email)
    if not user_cursor.first():
        raise ValueError(f"There is no user with email {email}")
    else:
        user_cursor.delete()
        db.commit()

# Read Users for Get LIST of Users
def get_users(db: Session):
    users = list(db.query(User).all())
    return users


def user_change_password(db: Session, email: str, user_change_password_body: users_schemas.UserChangePassword):
    user = db.query(User).filter(User.email == email).first()

    if not verify_password(user_change_password_body.old_password, user.password):
        raise ValueError(
            f"Old password provided doesn't match, please try again")
    user.password = get_password_hash(user_change_password_body.new_password)
    db.commit()


def user_reset_password(db: Session, email: str, new_password: str):
    try:
        user = db.query(User).filter(User.email == email).first()
        user.password = get_password_hash(new_password)
        db.commit()
    except Exception:
        return False
    return True


def update_reset_token(db: Session, temp_token: str):
    reset_token = db.query(Token).filter(Token.token == temp_token).first()
    if reset_token:
        # Update the reset_password column to 1 and is_expired column to 1
        reset_token.reset_password = True
        reset_token.is_expired = True
        db.commit()
        return True
    return False


def update_token_status(db: Session, expire_minutes: int):
    expired_tokens = db.query(Token).filter(Token.is_expired == expire_minutes).first()
    Token.created_at < datetime.utcnow() - timedelta(minutes=expire_minutes)
    if expired_tokens:
        expired_tokens.is_expired
        db.commit()
        return True
    return False


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