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
    expired_tokens = db.query(Token).filter(Token.created_at < datetime.utcnow() - timedelta(minutes=expire_minutes), Token.is_expired == False).all()

    for token in expired_tokens:
        token.is_expired = True

    db.commit()
    return len(expired_tokens) > 0


# update the status of password 
def user_reset_password(db: Session, email: str, new_password: str):
    user = db.query(User).filter(User.email == email).first()

    # Check if the user has a valid non-expired token
    if user.temp_token and not user.temp_token.is_expired:
        user.password = get_password_hash(new_password)
        # Expire the token after password reset
        user.temp_token.is_expired = True
        db.commit()
        return True
    else:
        return False