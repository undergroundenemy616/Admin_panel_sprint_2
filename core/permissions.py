from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsAuthenticated(BasePermission):
    def has_permission(self, request, view):
        if request.user and request.user.is_authenticated:
            return True
        return False


class IsOwner(BasePermission):
    access = 1

    def has_permission(self, request, view):
        return bool(request.user and request.user.groups.access <= self.access)


class IsStaff(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_staff)


class IsAdmin(BasePermission):
    access = 2

    def has_permission(self, request, view):
        if bool(request.user and request.user.groups.access <= self.access):
            return True
        return False


class IsAdminOrReadOnly(IsAdmin):
    def has_permission(self, request, view):
        result = super(IsAdminOrReadOnly, self).has_permission(request, view)
        return result or request.method in SAFE_METHODS
