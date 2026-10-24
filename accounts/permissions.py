"""
Role-based access control (RBAC) permissions and decorators.
"""

from functools import wraps
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import AccessMixin
from django.core.exceptions import PermissionDenied


def has_role(user, allowed_roles):
    """Check if user has any of the specified roles or administrative privileges."""
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser or user.is_staff:
        return True
    return getattr(user, "role", None) in allowed_roles


def role_required(*allowed_roles):
    """
    Decorator for views that checks that the user is logged in and has one of
    the allowed roles (or is superuser/staff). Raises PermissionDenied (403)
    if the user is authenticated but lacks the required role.
    """
    def decorator(view_func):
        @login_required
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if has_role(request.user, allowed_roles):
                return view_func(request, *args, **kwargs)
            raise PermissionDenied("You do not have permission to access this resource.")
        return _wrapped_view
    return decorator


class RoleRequiredMixin(AccessMixin):
    """Verify that the current user has one of the allowed roles."""
    allowed_roles = ()

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not has_role(request.user, self.allowed_roles):
            raise PermissionDenied("You do not have permission to access this resource.")
        return super().dispatch(request, *args, **kwargs)
