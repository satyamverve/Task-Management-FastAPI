# app.modules.users.routes.py

import sys
sys.path.append("..")

from fastapi import Depends, APIRouter, HTTPException, Request, Form, status, BackgroundTasks
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from typing import List
from Final_Demo.app.auth.auth import  create_access_token,\
      get_current_user, get_user_by_email, get_current_user_via_temp_token , PermissionChecker
from app.permissions.models_permissions import Users
from app.permissions.roles import get_role_permissions, Role
from Final_Demo.app.config.database import get_db
from Final_Demo.app.modules.users import service as db_crud
from Final_Demo.app.dto.users_schemas import User, UserSignUp, UserChangePassword, UserOut, UserMe, Token, UserUpdate, UserUpdateMe
from app.email_notifications.notify import send_registration_notification, send_reset_password_mail
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.models.users import Token
from Final_Demo.app.modules.users.service import TEMP_TOKEN_EXPIRE_MINUTES

templates = Jinja2Templates(directory='./app/templates')

router = APIRouter(prefix="")


@router.post("/users",
             dependencies=[Depends(PermissionChecker([Users.permissions.CREATE]))],
             response_model=UserOut, summary="Register a user", tags=["Users"])
async def create_user(user_signup: UserSignUp, db: Session = Depends(get_db)):
    """
    Registers a user.
    """
    try:
        user_created, password = db_crud.add_user(db, user_signup)
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
    
@router.post("/users/agent",
             dependencies=[Depends(PermissionChecker([Users.permissions.CREATE_AGENT]))],
             response_model=UserOut, summary="Register an Agent when You are a Manager", tags=["Users"])
async def create_user(user_signup: UserSignUp, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Registers an agent.
    """

    # Ensure that the user_signup.role is not SUPERADMIN
    if user_signup.role == Role.SUPERADMIN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Not Enough Permissions to create Superadmin"
        )
    if user_signup.role == Role.MANAGER:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Not Enough Permissions to Create Managers"
        )

    try:
        user_created, password = db_crud.add_user(db, user_signup)
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
    



@router.get("/users",
            dependencies=[Depends(PermissionChecker([Users.permissions.VIEW_LIST]))],
            response_model=List[UserOut], summary="Get all users", tags=["Users"])
def get_users(db: Session = Depends(get_db)):
    """
    Returns all users.
    """
    try:
        users = db_crud.get_users(db)
        return users
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"An unexpected error occurred. Report this message to support: {e}")


@router.patch("/users",
              dependencies=[Depends(PermissionChecker([Users.permissions.VIEW_DETAILS, Users.permissions.EDIT]))],
              response_model=UserOut,
              summary="Update a user", tags=["Users"])
def update_user(user_email: str, user_update: UserUpdate, db: Session = Depends(get_db)):
    """
    Updates a user.
    """
    try:
        user = db_crud.update_user(db, user_email, user_update)
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=404, detail=f"{e}")
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"An unexpected error occurred. Report this message to support: {e}")


@router.delete("/users",
               dependencies=[Depends(PermissionChecker([Users.permissions.DELETE]))],
               summary="Delete a user", tags=["Users"])
def delete_user(user_email: str, db: Session = Depends(get_db)):
    """
    Deletes a user.
    """
    try:
        db_crud.delete_user(db, user_email)
        return {"result": f"User with email {user_email} has been deleted successfully!"}
    except ValueError as e:
        raise HTTPException(
            status_code=404, detail=f"{e}")
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"An unexpected error occurred. Report this message to support: {e}")


@router.get("/users/roles",
            dependencies=[Depends(PermissionChecker([Users.permissions.VIEW_ROLES]))], 
            response_model=List[Role], summary="Get all user roles", tags=["Users"])
def get_user_roles(db: Session = Depends(get_db)):
    """
    Returns all user roles.
    """
    try:
        return Role.get_roles()
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"An unexpected error occurred. Report this message to support: {e}")


@router.get("/users/me",
            response_model=UserMe, summary="Get info for my account", tags=["Users"])
def get_users(user: User = Depends(PermissionChecker([Users.permissions.VIEW_ME]))):
    """
    Returns info of logged in account.
    """
    try:
        user = UserMe(
            id = user.id,
            email=user.email,
            name=user.name,
            surname=user.surname,
            register_date=user.register_date,
            role=user.role,
            permissions=get_role_permissions(user.role)
        )
        return user
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"An unexpected error occurred. Report this message to support: {e}")


@router.patch("/users/me",
              dependencies=[Depends(PermissionChecker([Users.permissions.VIEW_ME, Users.permissions.EDIT_ME]))],
              response_model=UserMe,
              summary="Change details for a logged in user", tags=["Users"])
def update_me(user_update: UserUpdateMe, user: User = Depends(get_current_user),
                         db: Session = Depends(get_db)):
    """
    Changes details for a logged in user.
    """
    # print(user.email)

    try:
        user = db_crud.update_me(db, user.email, user_update)
        user = UserMe(
            id= user.id,
            email=user.email,
            name=user.name,
            surname=user.surname,
            register_date=user.register_date,
            role=user.role,
            permissions=get_role_permissions(user.role)
        )
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=404, detail=f"{e}")
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"An unexpected error occurred. Report this message to support: {e}")


@router.patch("/users/me/change_password",
            #   dependencies=[Depends(PermissionChecker([Users.permissions.CHANGE_PASSWORD]))],
              summary="Change password for a logged in user", tags=["Users"])
def user_change_password(user_change_password_body: UserChangePassword, user: User = Depends(get_current_user),
                         db: Session = Depends(get_db)):
    """
    Changes password for a logged in user.
    """
    try:
        db_crud.user_change_password(db, user.email, user_change_password_body)
        return {"result": f"{user.name} your password has been updated!"}
    except ValueError as e:
        raise HTTPException(
            status_code=400, detail=f"{e}")
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"An unexpected error occurred. Report this message to support: {e}")


@router.post("/users/me/reset_password",
              summary="Resets password for a user", tags=["Users"])
def user_reset_password(request: Request, user: User = Depends(get_current_user_via_temp_token),
                         db: Session = Depends(get_db), new_password: str = Form(...),
                         background_tasks: BackgroundTasks = BackgroundTasks()):
    """
    Resets password for a user.
    """
    try:
        result = db_crud.user_reset_password(db, user.email, new_password)
        
        # Update token status using the same expire_minutes value
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
    
@router.get("/users/me/reset_password_template",
              response_class=HTMLResponse,
              summary="Reset password for a user", tags=["Users"])
def user_reset_password_template(request: Request, user: User = Depends(get_current_user_via_temp_token)):
    """
    Resets password for a user.
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


@router.post("/users/me/forgot_password",
              summary="Forgot password mechanism for a user", tags=["Users"])
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
            url = f"{request.base_url}users/me/reset_password_template?access_token={access_token}"
            await send_reset_password_mail(recipient_email=user_email, user=user, url=url, expire_in_minutes=TEMP_TOKEN_EXPIRE_MINUTES)
        return {
            "result": f"An email has been sent to {user_email} with a link for password reset."
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"An unexpected error occurred. Report this message to support: {e}")



