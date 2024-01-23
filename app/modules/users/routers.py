# app.modules.users.routes.py

import sys
sys.path.append("..")

from fastapi import Depends, APIRouter, HTTPException, Request, Form, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict
from Final_Demo.app.auth.auth import  create_access_token,\
      get_current_user, get_user_by_email, get_current_user_via_temp_token , PermissionChecker
from app.permissions.models_permissions import Users
from app.permissions.roles import get_role_permissions, Role
from Final_Demo.app.config.database import get_db
from Final_Demo.app.modules.users import service as db_crud
from Final_Demo.app.dto.users_schemas import  UserSignUp, UserUpdate, UserOut,Token, RolesUpdate
from app.email_notifications.notify import send_registration_notification, send_reset_password_mail
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.models.users import Token, User
from Final_Demo.app.modules.users.service import TEMP_TOKEN_EXPIRE_MINUTES
from typing import List, Optional


templates = Jinja2Templates(directory='./app/templates')

router = APIRouter(prefix="")

# LIST Roles with Permissions
@router.get("/roles/all",
            dependencies=[Depends(PermissionChecker([Users.permissions.VIEW_ROLES]))], 
            response_model=List[Dict[str, List[str]]], summary="Get all user roles with permissions", tags=["Roles"])
def get_user_roles(db: Session = Depends(get_db)):
    """
    Returns all user roles with their associated permissions.
    """
    try:
        roles_with_permissions = []
        for role in Role:
            role_permissions = get_role_permissions(role)
            roles_with_permissions.append({role.value: role_permissions})
        return roles_with_permissions
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"An unexpected error occurred. Report this message to support: {e}")


# CREATE User 
@router.post("/user/create",
             dependencies=[Depends(PermissionChecker([Users.permissions.CREATE]))],
             response_model=UserOut, summary="Register users", tags=["Users"])
async def create_user(user: UserSignUp, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Registers an user.
    """
    try:
        user_created, password = db_crud.add_user(db, user, current_user)
        await send_registration_notification(
            password=password, 
            recipient_email=user_created.email
        )
        return user_created
    except db_crud.DuplicateError as e:
        raise HTTPException(status_code=403, detail=f"{e}")
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"An unexpected error occurred. Report this message to support: {e}")

# LIST User with filter by user_id
@router.get("/user/all",
            dependencies=[Depends(PermissionChecker([Users.permissions.VIEW_LIST]))],
            response_model=List[UserOut], summary="Get all users", tags=["Users"])
def get_users(user_id: Optional[int] = None, 
              db: Session = Depends(get_db),
              current_user: get_current_user = Depends()):
    """
    Get list of all users with optional filter by user_id.
    """
    try:
        users = db_crud.get_users(db,current_user, user_id=user_id)
        return users
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"An unexpected error occurred. Report this message to support: {e}")    


# UPDATE Roles
@router.patch("/roles/update/{user_id}",
                dependencies=[Depends(PermissionChecker([Users.permissions.VIEW_DETAILS, Users.permissions.EDIT]))],
                response_model=UserOut,
                summary="Update users role", tags=["Roles"])
def update_roles(user_id: int, user_update: RolesUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Update role of user.
    """
    try:
        updated_role = db_crud.update_roles(db, user_id,current_user, user_update)
        return updated_role 
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred. Report this message to support: {e}")


# DELETE User
@router.delete("/user/{user_id}",
               dependencies=[Depends(PermissionChecker([Users.permissions.DELETE]))],
               summary="Delete users", tags=["Users"])
def delete_user(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Deletes a user.
    """
    try:
        db_crud.delete_users(db, current_user, user_id)
        return {"message": f"User {user_id} has been deleted successfully!"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred. Report this message to support: {e}")


# Update User
@router.patch("/user/update",
              summary="Update user", tags=["Users"])
def update_user(user: UserUpdate, current_user: User = Depends(get_current_user),
                         db: Session = Depends(get_db)):
    """
    Changes password, email, name for user.
    """
    try:
        db_crud.update_user(db, user, current_user)
        return {"result": f"User with ID {current_user.ID}'s password has been updated!"}
    except ValueError as e:
        raise HTTPException(
            status_code=400, detail=f"{e}")
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"An unexpected error occurred. Report this message to support: {e}")


# READ User
@router.get("/user/logged",response_model=UserOut,summary="Get infor of current user", tags=["General"])
def get_info_current_user(db: Session = Depends(get_db),current_user = Depends(get_current_user),):
    """
    Get Information of all users.
    """
    try:
        return db.query(User).filter(User.ID == current_user.ID).first()
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"An unexpected error occurred. Report this message to support: {e}")


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