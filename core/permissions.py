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
        access = bool(getattr(request.user.account.groups, 'access', None))
        return bool(request.user and access <= self.access)


class IsStaff(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_staff)


class IsAdmin(BasePermission):
    access = ADMIN_ACCESS  # fixme change to ACCESS from settings

    def has_permission(self, request, view):
        access = bool(getattr(request.user.account.groups, 'access', 4))
        if bool(request.user and access <= self.access):
            return True
        return False


class IsAdminOrReadOnly(IsAdmin):
    def has_permission(self, request, view):
        result = super(IsAdminOrReadOnly, self).has_permission(request, view)
        return result or request.method in SAFE_METHODS
