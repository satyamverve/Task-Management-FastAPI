# app/permissions/model_permissions.py

from app.permissions.base import ModelPermissionsMixin

class Users(ModelPermissionsMixin):
    __PERMISSIONS__ = [
        'VIEW',
        'EDIT',
        'CHANGE_PASSWORD',
        'VIEW_ROLES',
    ]
