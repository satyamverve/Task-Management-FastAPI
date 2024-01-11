# app/modules/login.py

import sys
sys.path.append("..")

from fastapi import Depends, APIRouter, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from Final_Demo.app.auth.auth import  create_access_token, authenticate_user
from Final_Demo.app.config.database import get_db
from Final_Demo.app.dto.users_schemas import Token
from fastapi.responses import HTMLResponse
# from pathlib import Path

router = APIRouter()

@router.post("/token", response_model=Token, summary="Authorize as a user", tags=["Authentication"])
def authorize(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Logs in a user.
    """
    user = authenticate_user(db=db, user_email=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(
            status_code=401, detail="Invalid user email or password.")
    try:
        access_token = create_access_token(data=user.email)
        return {
            "access_token": access_token,
            "token_type": "bearer"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"An unexpected error occurred. Report this message to support: {e}")