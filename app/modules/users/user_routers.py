# app.modules.users.routes.py

from typing import Optional
from fastapi import BackgroundTasks, Depends, APIRouter, Form, Query, Request
from fastapi.responses import HTMLResponse
from app.models import User, Token
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from app.auth.auth import get_current_user, PermissionChecker, otp_expire, generate_6_digit_otp, get_user_by_email
from app.permissions.models_permissions import Users
from app.permissions.roles import get_role_permissions, Role
from app.config.database import get_db  
from app.modules.users import user_services as db_crud
from app.dto.users_schemas import ResponseData, UserSignUp, UserUpdate, RolesUpdate
from app.email_notifications.notify import send_reset_password_mail
from fastapi.templating import Jinja2Templates
from app.config.database import msg

# Load HTML templates
templates = Jinja2Templates(directory='./app/templates')

router = APIRouter(prefix="")

# LIST User with filter by user_id
@router.get("/user/all",
            response_model=ResponseData, summary="Get all users", tags=["Users"])
def get_users(
              db: Session = Depends(get_db),
              current_user: get_current_user = Depends()):
    """
    Get list of all users with optional filter by user_id.
    """
    try:
        return  db_crud.get_users(db,current_user)
    except Exception:
        response_data = ResponseData(
            status=False,
            message=msg['random_key_10'],
            data={}
        )
        return response_data  


# Function to LIST all user roles with permissions
@router.get("/roles/all",
            dependencies=[Depends(PermissionChecker([Users.permissions.VIEW_ROLES]))], 
            response_model=ResponseData, summary="Get all user roles with permissions", tags=["Roles"])
def get_user_roles(db: Session = Depends(get_db)):
    """
    Returns all user roles with their associated permissions.
    """
    try:
        roles_with_permissions = []
        for role in Role:
            role_permissions = get_role_permissions(role)
            roles_with_permissions.append({role.value: role_permissions})
        response_data = ResponseData(
            status=True,
            message=msg['key_28'],
            data={"roles": roles_with_permissions}
        )
        return response_data
    except Exception:
        response_data = ResponseData(
            status=False,
            message=msg['random_key_2'],
            data={"roles": roles_with_permissions}
        )
        return response_data


# Function to update user roles
@router.put("/roles/update/{user_id}",
            dependencies=[Depends(PermissionChecker([Users.permissions.VIEW_DETAILS, Users.permissions.EDIT]))],
            response_model=ResponseData,
            summary="Update users role", tags=["Roles"])
def update_roles(user_id: int, user_update: RolesUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Update role of user.
    """
    try:
        updated_role = db_crud.update_roles(db, user_id, current_user, user_update)
        return updated_role
    except Exception:
        response_data = ResponseData(
            status=False,
            message=msg['key_26'],
            data={}
        )
        return response_data


# READ User
@router.get("/user/view/{user_id}",response_model=ResponseData,summary="Get info of users", tags=["Users"])
def get_user_by_user_id(user_id: int, 
                        db: Session = Depends(get_db),
                        current_user: User = Depends(get_current_user),
                        ):
    """
    Get Information of all users.
    """
    try:
        return db_crud.get_user(db, user_id, current_user)
    except Exception:
        response_data = ResponseData(
            status=False,
            message=msg['key_26'],
            data={}
        )
        return response_data


# Function to add a new user
@router.post("/user/create",
             dependencies=[Depends(PermissionChecker([Users.permissions.CREATE]))],
             response_model=ResponseData, summary="Register users", tags=["Users"])
async def create_user(user: UserSignUp, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Registers a user.
    """
    try:
        response = db_crud.add_user(db, user, current_user)
        return response
    except Exception as e:
        return ResponseData(
            status=False,
            message=msg['random_key_10'],
            data={}
        )


# Function to update user information
@router.put("/user/update/{user_id}", response_model=ResponseData, summary="Update users", tags=["Users"])
def update_user_api(user_id: int, user: UserUpdate, db: Session = Depends(get_db),current_user: User = Depends(get_current_user)):
    try:
        return db_crud.update_user(db, user_id, user, current_user)
    except Exception:
        response_data = ResponseData(
            status=False,
            message=msg['key_26'],
            data={}
        )
        return response_data
    


# Function to delete a user
@router.delete("/user/{user_id}",
               dependencies=[Depends(PermissionChecker([Users.permissions.DELETE]))],
               response_model=ResponseData,
               summary="Delete users", tags=["Users"])
def delete_user(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Deletes a user.
    """
    try:
        return db_crud.delete_users(db, current_user, user_id)
    except Exception:
        response_data = ResponseData(
            status=False,
            message=msg['key_26'],
            data={}
        )
        return response_data


# Function to reset user password for registered users
@router.post("/reset_password", summary="Reset password for users", tags=["Forgot Password"])
def user_reset_password(
    request: Request,
    otp: str = Form(...),
    new_password: str = Form(...),
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Reset user password using the provided OTP.
    """
    try:
        # Validate the OTP and retrieve the associated user_email
        user_email = db_crud.validate_otp_and_get_email(db, otp)
        if not user_email:
            response_data = ResponseData(
            status=False,
            message=msg['key_33'],
            data={}
            )
            return response_data

        # Reset user password
        success = db_crud.user_reset_password(db, user_email, new_password)

        if success:
            # Update token status and is_expired status
            db_crud.update_token_status(db, otp_expire)
            db_crud.update_password_change_status(db, otp)
            background_tasks.add_task(db_crud.update_password_change_status, db, otp, otp_expire)

            return templates.TemplateResponse(
                "reset_password_result.html",
                {
                    "request": request,
                    "success": True
                }
            )
        else:
            response_data = ResponseData(
            status=False,
            message=msg['key_32'],
            data={}
            )
            return response_data
    except Exception as e:
        response_data = ResponseData(
            status=False,
            message=msg['random_key_10'],
            data={}
        )
        return response_data


## Retrieve the access token from incoming http(here is /forgot_password)
@router.get("/token_template",
              response_class=HTMLResponse,
              summary="Retrieve access token", tags=["Forgot Password"])
def user_reset_password_template(request: Request):
    """
    Retrieve the access token from incoming http(here is /forgot_password) and make this token valid until token expire time
    """
    try:
        token = request.query_params.get('otp')
        return templates.TemplateResponse(
            "reset_password.html",
            {
                "request": request, 
                "otp": token
            }
        )
    except Exception as e:
        response_data = ResponseData(
            status=False,
            message=msg['random_key_10'],
            data={}
        )
        return response_data



# Forgot password
@router.post("/forgot_password",
              summary="Forgotten Password", tags=["Forgot Password"])
async def user_forgot_password(request: Request, user_email: str, db: Session = Depends(get_db)):
    """
    Triggers forgot password mechanism for a user.
    """
    try:
        user = get_user_by_email(db=db, user_email=user_email)
        if not user:
            response_data = ResponseData(
                status=False,
                message=msg['key_26'],
                data={}
            )
        else:
            # Generate a 6-digit OTP with expiration time
            otp, expiration_time = generate_6_digit_otp()
            
            # Store the OTP in the password_reset_tokens table
            reset_token = Token(
                otp=otp,  # Updated from token to otp
                user_email=user_email,
                reset_password=False,  # Initially set to False
                is_expired=False,  # Initially set to False
                expiration_time=expiration_time  # Set expiration time
            )
            db.add(reset_token)
            db.commit()

            # Include OTP and expiration time in the response data
            response_data = ResponseData(
                status=True,
                message=msg['key_31'],
                data={"otp": otp, "expiration_time": expiration_time}
            )

            # Send the OTP via email or any other preferred method
            await send_reset_password_mail(recipient_email=user_email, user=user, otp=otp, expire_in_minutes=expiration_time)

        return response_data
    except Exception as e:
        print(e)
        response_data = ResponseData(
            status=False,
            message=msg['random_key_10'],
            data={}
        )
        return response_data

