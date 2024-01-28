# app/auth/auth_bearer.py

from fastapi import Request, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.auth import auth

class JWTBearer(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        """
        Initializes the JWTBearer class.

        Parameters:
        - auto_error (bool): If True, automatically raises an HTTPException on authentication error.
        """
        super(JWTBearer, self).__init__(auto_error=auto_error)

    async def __call__(self, request: Request):
        """
        Validates and extracts JWT from the request's Authorization header.

        Parameters:
        - request (Request): The incoming FastAPI request.

        Returns:
        - str: The JWT token if valid.

        Raises:
        - HTTPException: If authentication fails.
        """
        credentials: HTTPAuthorizationCredentials = await super(JWTBearer, self).__call__(request)
        if credentials:
            if not credentials.scheme == "Bearer":
                raise HTTPException(status_code=403, detail="Invalid authentication scheme.")
            if not self.verify_jwt(credentials.credentials):
                raise HTTPException(status_code=403, detail="Invalid token or expired token.")
            return credentials.credentials
        else:
            raise HTTPException(status_code=403, detail="Invalid authorization code.")

    def verify_jwt(self, jwtoken: str) -> bool:
        """
        Verifies the validity of a JWT.

        Parameters:
        - jwtoken (str): The JWT token.

        Returns:
        - bool: True if the token is valid, False otherwise.
        """
        isTokenValid: bool = False
        try:
            payload = auth.decodeJWT(jwtoken)
        except:
            payload = None
        if payload:
            isTokenValid = True
        return isTokenValid