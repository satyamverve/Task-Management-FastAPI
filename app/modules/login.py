# app/modules/login.py

import sys
from app.auth.auth import signJWT, verify_password
from app.models.users import User
from app.config.database import get_db
from app.dto.users_schemas import Token, UserLoginSchema
from fastapi import Body, Depends, APIRouter
from sqlalchemy.orm import Session

router = APIRouter()

def check_user(data: UserLoginSchema, db: Session):
    """
    Helper function to check user credentials during login.

    Parameters:
    - data (UserLoginSchema): The login data containing email and password.
    - db (Session): The SQLAlchemy database session.

    Returns:
    - User: The user if credentials are valid, else None.
    """
    db_user = db.query(User).filter(User.email == data.email).first()
    if db_user and verify_password(data.password, db_user.password):
        return db_user
    return None

@router.post("/user/login", tags=["Authentication"])
async def user_login(user: UserLoginSchema = Body(...), db: Session = Depends(get_db)):
    """
    Endpoint to handle user login.

    Parameters:
    - user (UserLoginSchema): The login data containing email and password.
    - db (Session): The SQLAlchemy database session.

    Returns:
    - dict: JWT token if login is successful, otherwise an error message.
    """
    db_user = check_user(user, db)
    if db_user:
        return signJWT(db_user.email)
    return {
        "error": "Wrong login details!"
    }
