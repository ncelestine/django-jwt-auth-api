from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsOwnerOrReadOnly(BasePermission):
    """
    Custom permission:
    - Any authenticated user can view books (GET, HEAD, OPTIONS).
    - Only the owner of a book can update or delete it.
    """

    def has_object_permission(self, request, view, obj):
        # SAFE methods (GET, HEAD, OPTIONS) are allowed for anybody authenticated.
        if request.method in SAFE_METHODS:
            return True
        # For write methods (PUT/PATCH/DELETE) only the owner is allowed.
        return obj.owner == request.user
