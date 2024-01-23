# app.modules.users.service.py

import sys
sys.path.append("..")
from sqlalchemy.orm import Session
from Final_Demo.app.models.users import User
from Final_Demo.app.auth.auth import get_password_hash
from app.models.users import Token
from datetime import datetime, timedelta
TEMP_TOKEN_EXPIRE_MINUTES = 10


# Reset password 
def user_reset_password(db: Session, email: str, new_password: str):
    try:
        user = db.query(User).filter(User.email == email).first()
        user.password = get_password_hash(new_password)
        db.commit()
    except Exception:
        return False
    return True

# update the acess_token status which was stored in Token model
def update_token_status(db: Session, expire_minutes: int):
    expired_tokens = db.query(Token).filter(Token.is_expired == expire_minutes).first()
    Token.created_at < datetime.utcnow() - timedelta(minutes=expire_minutes)
    if expired_tokens:
        expired_tokens.is_expired
        db.commit()
        return True
    return False

# update the status of password 
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