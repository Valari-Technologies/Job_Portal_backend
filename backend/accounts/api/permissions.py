from rest_framework.permissions import BasePermission


class IsAdminRole(BasePermission):
    """
    Allows access only to users with ADMIN role.
    """
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == 'ADMIN'
        )


class IsHRRole(BasePermission):
    """
    Allows access only to users with HR role.
    """
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == 'HR'
        )


class IsCandidateRole(BasePermission):
    """
    Allows access only to users with CANDIDATE role.
    """
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == 'CANDIDATE'
        )
