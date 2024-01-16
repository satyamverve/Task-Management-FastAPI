# app/permissions/model_permissions.py

from app.permissions.base import ModelPermissionsMixin

class Users(ModelPermissionsMixin):
    __PERMISSIONS__ = [
        'VIEW_ME',
        'EDIT_ME',
        'CHANGE_PASSWORD',
        'VIEW_ROLES',
        'CREATE_AGENT',
        'CREATE_TASK'
    ]
