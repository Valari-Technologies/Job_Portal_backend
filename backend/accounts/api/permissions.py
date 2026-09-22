from rest_framework.permissions import BasePermission


class IsSuperAdminRole(BasePermission):
    """
    Allows access only to users with SUPER_ADMIN role or is_superuser.
    """
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and (request.user.role == 'SUPER_ADMIN' or request.user.is_superuser)
        )


class IsAdminRole(BasePermission):
    """
    Allows access only to users with ADMIN or SUPER_ADMIN role.
    """
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and (request.user.role in ['ADMIN', 'SUPER_ADMIN'] or request.user.is_superuser)
        )


class IsHRRole(BasePermission):
    """
    Allows access only to users with HR role.
    """
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == 'HR'
        )


class IsCandidateRole(BasePermission):
    """
    Allows access only to users with CANDIDATE role.
    """
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == 'CANDIDATE'
        )
