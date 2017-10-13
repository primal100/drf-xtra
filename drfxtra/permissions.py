from rest_framework.permissions import BasePermission, SAFE_METHODS
from rest_framework.compat import is_authenticated
import operator

create_methods = ("POST", "OPTIONS")
update_methods = ("GET", "PUT", "PATCH", "DELETE")
write_required_methods = ("POST", "PUT", "PATCH", "DELETE", "OPTIONS")
read_methods = ("GET", "OPTIONS")

class WriteObjectPermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        method = request.method
        if method in write_required_methods:
            for k, v in view.can_write_object(request).items():
                value = operator.attrgetter(k)(obj)
                if value != v:
                    return False
            for k, v in view.cannot_write_object(request).items():
                value = operator.attrgetter(k)(obj)
                if value == v:
                    return False
        return True

class UserPermissions(WriteObjectPermission):
    def has_permission(self, request, view):
        method = request.method
        return (
            request.user and
            is_authenticated(request.user) and
            request.user.is_staff
        ) or (
            method in update_methods and
            request.user and
            is_authenticated(request.user)
         )

class ReadObjectPermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        method = request.method
        if method in read_methods:
            for k, v in view.can_read_object(request).items():
                value = operator.attrgetter(k)(obj)
                if value != v:
                    return False
            for k, v in view.cannot_read_object(request).items():
                value = operator.attrgetter(k)(obj)
                if value == v:
                    return False
        return True

class IsSuperuser(BasePermission):
    """
    The request is authenticated as a superuser only
    """

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_superuser and
            is_authenticated(request.user)
        )

class IsSuperuserOrWriteOnly(BasePermission):
    """
    The request is authenticated as a superuser, or is a write-only request.
    """

    def has_permission(self, request, view):
        return (
            request.method in write_required_methods or
            (request.user and
            request.user.is_superuser and
            is_authenticated(request.user))
        )

class IsSuperuserOrReadOnly(BasePermission):
    """
    The request is authenticated as a superuser, or is a read-only request.
    """

    def has_permission(self, request, view):
        return (
            request.method in SAFE_METHODS or
            (request.user and
            request.user.is_superuser and
            is_authenticated(request.user))
        )

class IsAdminOrWriteOnly(BasePermission):
    """
    The request is authenticated as a staff user, or is a write-only request.
    """

    def has_permission(self, request, view):
        return (
            request.method in write_required_methods or
            (request.user and
            request.user.is_staff and
            is_authenticated(request.user))
        )

class IsAdminOrReadOnly(BasePermission):
    """
    The request is authenticated as a staff user, or is a read-only request.
    """

    def has_permission(self, request, view):
        return (
            request.method in SAFE_METHODS or
            (request.user and
            request.user.is_staff and
            is_authenticated(request.user))
        )

class IsAuthenticatedOrWriteOnly(BasePermission):
    """
    The request is authenticated as a user, or is a write-only request.
    """

    def has_permission(self, request, view):
        return (
            request.method in write_required_methods or
            request.user and
            is_authenticated(request.user)
        )

class IsAuthenticatedOrCreateOnly(BasePermission):
    """
    The request is authenticated as a user, or is a create-only request.
    """

    def has_permission(self, request, view):
        return (
            request.method in "POST, OPTIONS" or
            request.user and
            is_authenticated(request.user)
        )