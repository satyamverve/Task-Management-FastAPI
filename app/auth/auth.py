from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from app.models.users import User
from app.config.database import get_db
from fastapi import Depends, HTTPException, status
from typing import List, Dict
from app.permissions.base import ModelPermission
from app.permissions.roles import get_role_permissions
from app.data.data_class import settings
from app.auth.auth_bearer import JWTBearer
import time

# Initialize JWTBearer instance for handling JWT tokens
jwt_bearer = JWTBearer()

# JWT settings
JWT_SECRET = settings.secret_key
JWT_ALGORITHM = settings.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Function to verify plaintext password against hashed password
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# Function to generate hashed password
def get_password_hash(password):
    return pwd_context.hash(password)

# Function to create a token response
def token_response(token: str):
    return {
        "access_token": token
    }

# Function to sign a JWT token
def signJWT(data: str, expire_minutes: int = ACCESS_TOKEN_EXPIRE_MINUTES) -> str:
    expiration_time = time.time() + expire_minutes
    payload = {
        "data": data,
        "expires": expiration_time
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token

# Function to decode a JWT token
def decodeJWT(token: str = Depends(JWTBearer())) -> dict:
    try:
        decoded_token = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return decoded_token
    except JWTError:
        return {}

# Function to retrieve a user by email from the database
def get_user_by_email(db: Session, user_email: str):
    user = db.query(User).filter(User.email == user_email).first()
    return user

# Function to get the current user using a JWT token
def get_current_user(token: str = Depends(JWTBearer()), db: Session = Depends(get_db)) -> User:
    decoded_token = decodeJWT(token)
    user_email = decoded_token.get('data')  # Extract the email from the decoded token
    user = get_user_by_email(db, user_email)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user credentials")
    return user

# Function to get the current user using a temporary access token
import random
from datetime import timedelta

# Token expiration time for forgot password
otp_expire = 1

def generate_6_digit_otp():
    """Generates a random 6-digit OTP with expiration time."""
    otp = random.randint(100000, 999999)
    expiration_time = datetime.utcnow() + timedelta(minutes=int(otp_expire))
    return otp, expiration_time


# Class for checking permissions
class PermissionChecker:
    def __init__(self, permissions_required: List[ModelPermission]):
        self.permissions_required = permissions_required

    def __call__(self, user: User = Depends(get_current_user)):
        for permission_required in self.permissions_required:
            if permission_required not in get_role_permissions(user.role):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not enough permissions to access this resource")
        return user
