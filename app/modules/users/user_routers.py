# app.modules.users.routes.py

import sys
from app.models import users

from app.auth.auth_bearer import JWTBearer
sys.path.append("..")

from fastapi import Body, Depends, APIRouter, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict
from app.auth.auth import  get_current_user, PermissionChecker, get_password_hash, signJWT, token_response
from app.permissions.models_permissions import Users
from app.permissions.roles import get_role_permissions, Role
from app.config.database import get_db
from app.modules.users import user_services as db_crud
from app.dto.users_schemas import  UserSignUp, UserUpdate, UserOut,RolesUpdate, Token
from app.email_notifications.notify import send_registration_notification
from fastapi.templating import Jinja2Templates
from app.models.users import User
from typing import List, Optional


templates = Jinja2Templates(directory='./app/templates')

router = APIRouter(prefix="")

# # CREATE User 
# @router.post("/user/create",
#              dependencies=[Depends(PermissionChecker([Users.permissions.CREATE]))],
#              response_model=Token, summary="Register users", tags=["Users"])
# async def create_user_route(user: UserSignUp, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
#     """
#     Registers a user.
#     """
#     try:
#         user_created, password = db_crud.create_user(db, user, current_user)
#         # Additional logic if needed
#         return signJWT(user_created.email)
    # except db_crud.DuplicateError as e:
    #     raise HTTPException(status_code=403, detail=f"{e}")
    # except Exception as e:
    #     raise HTTPException(
    #         status_code=500, detail=f"An unexpected error occurred. Report this message to support: {e}")

@router.post("/user/signup", tags=["user"])
async def create_user(user: UserSignUp = Body(...), db: Session = Depends(get_db)):
    try:
        hashed_password = get_password_hash(user.password)

        # Create a new User instance with the provided data
        new_user = User(
            email=user.email,
            name=user.name,
            password=hashed_password,
            role=user.role
        )

        # Add the new user to the database
        db.add(new_user)
        db.commit()
        db.refresh(new_user)  # Refresh to get the updated data from the database

        return signJWT(user.email)
    except db_crud.DuplicateError as e:
        raise HTTPException(status_code=403, detail=f"{e}")
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"An unexpected error occurred. Report this message to support: {e}")



# LIST User with filter by user_id
@router.get("/user/all",
            dependencies=[Depends(PermissionChecker([Users.permissions.VIEW_LIST])),Depends(JWTBearer())],
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

def update_password_change_status(db: Session, temp_token: str):
    reset_token = db.query(Token).filter(Token.token == temp_token).first()

    if reset_token and not reset_token.is_expired:
        reset_token.reset_password = True
        db.commit()
        return True
    else:
        return False
