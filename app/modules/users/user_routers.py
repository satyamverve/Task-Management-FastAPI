# app.modules.users.routes.py

from fastapi import BackgroundTasks, Depends, APIRouter, Form, Request
from app.models import User, Token
from sqlalchemy.orm import Session
from app.auth.auth import get_current_user, otp_expire_time, generate_6_digit_otp, get_user_by_email
from app.permissions.roles import get_role_permissions, Role
from app.config.database import get_db  
from app.modules.users import user_services as db_crud
from app.dto.users_schemas import UserSignUp, UserUpdate, RolesUpdate
from app.email_notifications.notify import send_reset_password_mail
from app.dto.tasks_schema import ResponseData
from fastapi.templating import Jinja2Templates
from app.config.database import msg

# Load HTML templates
templates = Jinja2Templates(directory='./app/templates')

router = APIRouter(prefix="")

# LIST of all Users
@router.get("/user/all",
            response_model=ResponseData, summary="Get all users", tags=["Users"])
def get_users_route(
              db: Session = Depends(get_db),
              current_user: get_current_user = Depends()):
    """
    Get list of all users.
    """
    try:
        users = db_crud.get_users(db, current_user)
        return ResponseData(
            status=True,
            message=msg['lst_user'],
            data={"users": users}
        )
    except Exception:
        return ResponseData(
            status=False,
            message=msg['unexp_error'],
            data={}
        )

# Function to read user by user_id
@router.get("/user/view/{user_id}",response_model=ResponseData,summary="Get info of users", tags=["Users"])
def get_user_by_user_id_route(user_id: int, 
                        db: Session = Depends(get_db),
                        current_user: User = Depends(get_current_user),
                        ):
    """
    Get Information of users with user_id.
    """
    try:
        user = db_crud.get_user(db, user_id, current_user)
        if user:
            return ResponseData(
                status=True,
                message=msg['user_detail'],
                data=user
            )
        else:
            return ResponseData(
                status=False,
                message=msg['enough_perm'],
                data={}
            )
    except Exception:
        return ResponseData(
            status=False,
            message=msg['user_not'],
            data={}
        )

# Function to add a new user
@router.post("/user/create",
             response_model=ResponseData, summary="Register users", tags=["Users"])
async def create_user_route(user: UserSignUp, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Register a users:
    - Enter role_id as 1 or 2 or 3
    - 1 = SUPERADMIN
    - 2 = MANAGER
    - 3 = AGENT
    """
    try:
        status, message, data =await  db_crud.add_user(db, user, current_user)
        return ResponseData(status=status, message=message, data=data)
    except Exception as e:
        return ResponseData(
            status=False,
            message=msg['unexp_error'],
            data={}
        )
    
# Function to update user information
@router.put("/user/update/{user_id}", response_model=ResponseData, summary="Update users", tags=["Users"])
def update_user_api(user_id: int, user: UserUpdate, db: Session = Depends(get_db),current_user: User = Depends(get_current_user)):
    try:
        status, message, data= db_crud.update_user(db, user_id, user, current_user)
        return ResponseData(status=status, message=message, data=data)
    except Exception:
        response_data = ResponseData(
            status=False,
            message=msg['incorrect_pass'],
            data={}
        )
        return response_data

# Function to delete a user
@router.delete("/user/delete/{user_id}",
               response_model=ResponseData,
               summary="Delete users", tags=["Users"])
def delete_user(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Deletes a user.
    """
    try:
        status, message, data=db_crud.delete_users(db, current_user, user_id)
        return ResponseData(status=status, message=message, data=data)
    except Exception:
        response_data = ResponseData(
            status=False,
            message=msg['user_not'],
            data={}
        )
        return response_data

# Function to update user role_ids
@router.put("/roles/update/{user_id}",
            response_model=ResponseData,
            summary="Update users role", tags=["Roles"])
def update_roles(user_id: int, user_update: RolesUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Update the roles of the existing users:
    - Enter role_id as 1 or 2 or 3
    - 1 = SUPERADMIN
    - 2 = MANAGER
    - 3 = AGENT
    """
    try:
        status, message, data = db_crud.update_roles(db, user_id, current_user, user_update)
        return ResponseData(status=status, message=message, data=data)
    except Exception:
        response_data = ResponseData(
            status=False,
            message=msg['user_not'],
            data={}
        )
        return response_data

# Function to LIST all user roles with permissions
@router.get("/roles/all",
            response_model=ResponseData, summary="Get all user roles with permissions", tags=["Roles"])
def get_user_roles(db: Session = Depends(get_db)):
    """
    Returns all roles with their associated permissions.
    """
    try:
        roles_with_permissions = []
        for role in Role:
            role_permissions = get_role_permissions(role)
            roles_with_permissions.append({role.value: role_permissions})
        response_data = ResponseData(
            status=True,
            message=msg['upd_roles'],
            data={"roles": roles_with_permissions}
        )
        return response_data
    except Exception:
        response_data = ResponseData(
            status=False,
            message=msg['enough_perm'],
            data={"roles": roles_with_permissions}
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
                message=msg['user_not'],
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
                message=msg['sent_otp'],
                data={"otp": otp, "expiration_time": expiration_time}
            )
            # Send the OTP via email or any other preferred method
            await send_reset_password_mail(recipient_email=user_email, user=user, otp=otp, expire_in_minutes=expiration_time)
        return response_data
    except Exception as e:
        print(e)
        response_data = ResponseData(
            status=False,
            message=msg['unexp_error'],
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
            message=msg['invalid_otp'],
            data={}
            )
            return response_data
        # Reset user password
        success = db_crud.user_reset_password(db, user_email, new_password)
        if success:
            # Update token status and is_expired status
            db_crud.update_token_status(db, otp_expire_time)
            db_crud.update_password_change_status(db, otp)
            background_tasks.add_task(db_crud.update_password_change_status, db, otp)
            background_tasks.add_task(db_crud.update_token_status, db, otp_expire_time)
            response_data = ResponseData(
                    status=True,
                    message=msg['updated_pass'],
                    data={}
                    )
            return response_data
        else:
            response_data = ResponseData(
            status=False,
            message=msg['invalidated'],
            data={}
            )
            return response_data
    except Exception as e:
        response_data = ResponseData(
            status=False,
            message=msg['unexp_error'],
            data={}
        )
        return response_data


# Retrieve the access token from incoming http(here is /forgot_password)
def user_reset_password_template(request: Request):
    """
    Retrieve the access token from incoming http(here is /forgot_password) and make this token valid until token expire time
    """
    try:
        token = request.query_params.get('otp')
        return templates.TemplateResponse(
            "282777",
            {
                "request": request, 
                "otp": token
            }
        )
    except Exception as e:
        response_data = ResponseData(
            status=False,
            message=msg['unexp_error'],
            data={}
        )
        return response_data




