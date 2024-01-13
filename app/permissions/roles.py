# app/permissions/roles.py

from enum import Enum
from app.permissions.models_permissions import *
from typing import List

class Role(str, Enum):
    SUPERADMIN = "SUPERADMIN"
    MANAGER = "MANAGER"
    AGENT= "AGENT"

    @classmethod
    def get_roles(cls):
        values = []
        for member in cls:
            values.append(f"{member.value}")
        return values

ROLE_PERMISSIONS = {
    Role.SUPERADMIN: [
        Users.permissions.FULL_PERMISSIONS,
        
    ],
    Role.MANAGER: [
        [
            Users.permissions.CHANGE_PASSWORD,  
            Users.permissions.VIEW_ME,
            Users.permissions.EDIT_ME,
            Users.permissions.CREATE_AGENT,
        ]
    ],
    Role.AGENT: [
        [
            Users.permissions.VIEW_ME,
            Users.permissions.EDIT_ME,
            Users.permissions.CHANGE_PASSWORD

        ]
    ]
}

def get_role_permissions(role: Role):
    permissions = set()
    for permissions_group in ROLE_PERMISSIONS[role]:
        for permission in permissions_group:
            permissions.add(str(permission))
    return list(permissions)
