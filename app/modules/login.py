# app/modules/login.py

import sys
from Final_Demo.app.auth.auth import signJWT, verify_password
from Final_Demo.app.models.users import User
from Final_Demo.app.config.database import get_db
from Final_Demo.app.dto.users_schemas import Token, UserLoginSchema
from fastapi import Body, Depends, APIRouter
from sqlalchemy.orm import Session

router = APIRouter()

def check_user(data: UserLoginSchema, db: Session):
    db_user = db.query(User).filter(User.email == data.email).first()
    if db_user and verify_password(data.password, db_user.password):
        return db_user
    return None

@router.post("/user/login", tags=["user"])
async def user_login(user: UserLoginSchema = Body(...), db: Session = Depends(get_db)):
    db_user = check_user(user, db)
    if db_user:
        return signJWT(db_user.email)
    return {
        "error": "Wrong login details!"
    }
