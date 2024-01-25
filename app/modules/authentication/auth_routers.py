# app.modules.users.routes.py

import sys
sys.path.append("..")
from Final_Demo.app.auth.auth import get_user_by_email, signJWT as create_access_token, get_current_user_via_temp_token
from Final_Demo.app.config.database import get_db
from Final_Demo.app.dto.users_schemas import Token
from fastapi.responses import HTMLResponse
from fastapi import Depends, APIRouter, HTTPException, Request, Form, BackgroundTasks
from sqlalchemy.orm import Session
from Final_Demo.app.modules.authentication import auth_services as db_crud
from Final_Demo.app.dto.users_schemas import Token
from app.email_notifications.notify import  send_reset_password_mail
from fastapi.templating import Jinja2Templates
from app.models.users import Token, User
from Final_Demo.app.modules.authentication.auth_services import TEMP_TOKEN_EXPIRE_MINUTES

templates = Jinja2Templates(directory='./app/templates')

router = APIRouter()

# Reset Password
@router.post("/reset_password",
              summary="Reset password for users", tags=["Authentication"])
def user_reset_password(request: Request, user: User = Depends(get_current_user_via_temp_token),
                         db: Session = Depends(get_db), new_password: str = Form(...),
                         background_tasks: BackgroundTasks = BackgroundTasks()):
    """
    Bear the access token genereted from "/token_template" and validate this token for reset password 
    """
    try:
        result = db_crud.user_reset_password(db, user.email, new_password)
        # Update token status and is_expired status using the same expire_minutes value
        db_crud.update_token_status(db, TEMP_TOKEN_EXPIRE_MINUTES)
        db_crud.update_password_change_status(db, user.temp_token.token)
        background_tasks.add_task(db_crud.update_password_change_status, db, user.temp_token.token)
        return templates.TemplateResponse(
            "reset_password_result.html",
            {
                "request": request,
                "success": result 
            }
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400, detail=f"{e}")
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"An unexpected error occurred. Report this message to support: {e}")


# Retrieve the access token from incoming http(here is /forgot_password)
@router.get("/token_template",
              response_class=HTMLResponse,
              summary="Retrieve access token", tags=["Authentication"])
def user_reset_password_template(request: Request, user: User = Depends(get_current_user_via_temp_token)):
    """
    Retrieve the access token from incoming http(here is /forgot_password) and make this token valid until token expire time
    """
    try:
        token = request.query_params.get('access_token')
        return templates.TemplateResponse(
            "reset_password.html",
            {
                "request": request, 
                "user": user, 
                "access_token": token
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"An unexpected error occurred. Report this message to support: {e}")


# Forgot password
@router.post("/forgot_password",
              summary="Forgotten Password", tags=["Authentication"])
async def user_forgot_password(request: Request, user_email: str, db: Session = Depends(get_db)):
    """
    Triggers forgot password mechanism for a user.
    """
    try:
        user = get_user_by_email(db=db, user_email=user_email)
        if not user:
            return {
            "result": f"There is no user with this {user_email} username"
        }
        else:
            access_token = create_access_token(data=user_email, expire_minutes=TEMP_TOKEN_EXPIRE_MINUTES)
            # Store the token in the PasswordResetToken table
            reset_token = Token(
                token=access_token,
                user_email=user_email,
                reset_password=False,  # Initially set to False
                is_expired=False,  # Initially set to False
            )
            db.add(reset_token)
            db.commit()
            url = f"{request.base_url}token_template?access_token={access_token}"
            await send_reset_password_mail(recipient_email=user_email, user=user, url=url, expire_in_minutes=TEMP_TOKEN_EXPIRE_MINUTES)
        return {
            "result": f"An email has been sent to {user_email} with a link for password reset."
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"An unexpected error occurred. Report this message to support: {e}")