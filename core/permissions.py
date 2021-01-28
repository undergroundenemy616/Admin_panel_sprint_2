from rest_framework.permissions import SAFE_METHODS, BasePermission

from groups.models import ADMIN_ACCESS, OWNER_ACCESS


class IsAuthenticatedOnPost(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.method == 'POST'


class IsAuthenticated(BasePermission):
    def has_permission(self, request, view):
        if request.user and request.user.is_authenticated:
            return True
        return False


class IsOwner(BasePermission):
    access = OWNER_ACCESS

    def has_permission(self, request, view):
        try:
            access = [access_dict.get('access') for access_dict in request.user.account.groups.values('access')]
        except AttributeError:
            return False
        if len(access) != 0 and bool(request.user and min(access) <= self.access):
            return True
        return False


class IsStaff(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_staff)


class IsAdmin(BasePermission):
    access = ADMIN_ACCESS

    def has_permission(self, request, view):
        try:
            access = [access_dict.get('access') for access_dict in request.user.account.groups.values('access')]
        except AttributeError:
            return False
        if len(access) != 0 and bool(request.user and min(access) <= self.access):
            return True
        return False


class IsAdminOrReadOnly(IsAdmin):
    def has_permission(self, request, view):
        result = super(IsAdminOrReadOnly, self).has_permission(request, view)
        return result or request.method in SAFE_METHODS
