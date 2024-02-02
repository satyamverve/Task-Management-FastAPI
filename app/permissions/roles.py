# app/permissions/roles.py

from enum import Enum
from app.permissions.models_permissions import *

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
def get_role_permissions(role_id: int):
    permissions = set()
    for permissions_group in ROLE_PERMISSIONS.get(role_id, []):
        for permission in permissions_group:
            permissions.add(str(permission))
    return list(permissions)

# Function to check if the current user has permission to create a user with the specified role
def can_create(current_user_role_id: int, user_role_id: int) -> bool:
    """
    Check if the current user has permission to create a user with the specified role.
    """
    if current_user_role_id == 1:  # Assuming SUPERADMIN role_id is 1
        return True  # Superadmin can create any user
    elif current_user_role_id == 3:  # Assuming AGENT role_id is 3
        return False  # Agent cannot create any user
    elif current_user_role_id == 2 and user_role_id in {2, 1}:  # Assuming MANAGER role_id is 2 and SUPERADMIN role_id is 1
        return False  # Manager cannot create users with roles MANAGER or SUPERADMIN
    return True  # For other cases, return True


