from rest_framework.permissions import IsAuthenticated


class HasMinimalAccessOrIsAuthenticated(IsAuthenticated):
    access = 0

    def has_permission(self, request, view):
        is_authenticated = super().has_permission(request, view)
        if is_authenticated and request.user.groups.access <= self.access:
            return True
        return False


class IsEngineerOrReadOnly(HasMinimalAccessOrIsAuthenticated):
    access = get_


class IsAdminUserOrReadOnly(IsAdminUser):

    def has_permission(self, request, view):
        is_admin = super(
            IsAdminUserOrReadOnly,
            self).has_permission(request, view)
        # Python3: is_admin = super().has_permission(request, view)
        return request.method in SAFE_METHODS or is_admin