# app.modules.users.routes.py

import sys
from fastapi import Body, Depends, APIRouter, HTTPException, status, Form, Query, Request
from fastapi.responses import HTMLResponse
from app.models import users, User, Token
from app.auth.auth_bearer import JWTBearer
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from typing import List, Dict
from app.auth.auth import get_current_user, PermissionChecker, get_password_hash, signJWT, token_response, get_current_user_via_temp_token, get_user_by_email
from app.permissions.models_permissions import Users
from app.permissions.roles import get_role_permissions, Role
from app.config.database import get_db  
from app.modules.users import user_services as db_crud
from app.dto.users_schemas import UserSignUp, UserUpdate, UserOut, RolesUpdate, Token
from app.email_notifications.notify import send_registration_notification, send_reset_password_mail
from fastapi.templating import Jinja2Templates
from typing import List, Optional

# token time forgot password(token to be exipred in minutes) 
TEMP_TOKEN_EXPIRE_MINUTES = 10

#load the html templates 
templates = Jinja2Templates(directory='./app/templates')

router = APIRouter(prefix="")

# # create users
# @router.post("/user/signup", tags=["user"])
# async def create_user(user: UserSignUp = Body(...), db: Session = Depends(get_db), current_user: get_current_user = Depends()):
#     return db_crud.create_user(db, user, current_user)

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

#get the info of current user
@router.get("/user/logged", response_model=UserOut, summary="Get info of the current user", tags=["General"])
async def get_info_current_user(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Get information of the current user.
    """
    try:
        return db.query(User).filter(User.ID == current_user.ID).first()
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"An unexpected error occurred. Report this message to support: {e}")


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



# Reset Password
@router.post("/reset_password", summary="Reset password for users", tags=["Authentication"])
def user_reset_password(request: Request, user: User = Depends(get_current_user_via_temp_token),
                        db: Session = Depends(get_db), new_password: str = Form(...)):
    """
    Reset the password for the authenticated user.
    """
    try:
        result = db_crud.user_reset_password(db, user.email, new_password)
        return templates.TemplateResponse("reset_password_result.html", {"request": request, "success": result})
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")


# Retrieve the access token from incoming http(here is /forgot_password) in the html template
@router.get("/token_template",
              response_class=HTMLResponse,
              summary="Retrieve access token", tags=["Authentication"])
def user_reset_password_template(request: Request, access_token: str = Query(None), db: Session = Depends(get_db), user: User = Depends(get_current_user_via_temp_token)):
    """
    Retrieve the access token from incoming http(here is /forgot_password) and make this token valid until token expire time
    """
    try:
        return templates.TemplateResponse(
            "reset_password.html",
            {
                "request": request, 
                "user": user, 
                "access_token": access_token
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
            access_token = signJWT(data=user_email, expire_minutes=TEMP_TOKEN_EXPIRE_MINUTES)
            # Store the token in the PasswordResetToken table
            # reset_token = Token(
            #     token=access_token,
            #     user_email=user_email,
            #     reset_password=False,  # Initially set to False
            #     is_expired=False,  # Initially set to False
            # )
            # db.add(reset_token)
            # db.commit()
            url = f"{request.base_url}token_template?access_token={access_token}"
            await send_reset_password_mail(recipient_email=user_email, user=user, url=url, expire_in_minutes=TEMP_TOKEN_EXPIRE_MINUTES)
        return {
            "result": f"An email has been sent to {user_email} with a link for password reset."
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"An unexpected error occurred. Report this message to support: {e}")