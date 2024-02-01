# app/permissions/model_permissions.py

from app.permissions.base import ModelPermissionsMixin

# Define a class for user-related model permissions, inheriting from ModelPermissionsMixin
class Users(ModelPermissionsMixin):
    # List of permissions associated with the Users model
    __PERMISSIONS__ = [
        'VIEW',
        'EDIT',
    ]
