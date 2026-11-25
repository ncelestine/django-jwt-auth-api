# users/permissions.py
# Purpose: Custom DRF permissions (e.g., role-based guards).

from rest_framework.permissions import BasePermission

class IsManager(BasePermission):
    """
    Only allow users in the 'manager' group.
    """
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.groups.filter(name="manager").exists()
        )