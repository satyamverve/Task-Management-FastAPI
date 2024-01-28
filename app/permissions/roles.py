# app/permissions/roles.py

from enum import Enum
from app.permissions.models_permissions import *
from typing import List


# Enum class representing different user roles
class Role(str, Enum):
    SUPERADMIN = "SUPERADMIN"
    MANAGER = "MANAGER"
    AGENT= "AGENT"
    # Method to get a list of all role values
    @classmethod
    def get_roles(cls):
        values = []
        for member in cls:
            values.append(f"{member.value}")
        return values

# Dictionary mapping roles to their associated permissions
ROLE_PERMISSIONS = {
    Role.SUPERADMIN: [
        Users.permissions.FULL_PERMISSIONS,
    ],
    Role.MANAGER: [
        [
            Users.permissions.CREATE,
            Users.permissions.VIEW_DETAILS,
            Users.permissions.DELETE,
            Users.permissions.VIEW_LIST,
        ]
    ],
    Role.AGENT: [
        [
            Users.permissions.VIEW_DETAILS,
        ]
    ]
}

# Function to get permissions associated with a specific role
def get_role_permissions(role: Role):
    permissions = set()
    for permissions_group in ROLE_PERMISSIONS[role]:
        for permission in permissions_group:
            permissions.add(str(permission))
    return list(permissions)

# Function to check if the current user has permission to create a user with the specified role
def can_create(current_user_role: Role, user_role: Role) -> bool:
    """
    Check if the current user has permission to create a user with the specified role.
    """
    if current_user_role == Role.MANAGER and user_role in {Role.MANAGER, Role.SUPERADMIN}:
        return False
    return True

