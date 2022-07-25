from rest_framework import permissions


class CreateOrIsAuthenticated(permissions.IsAuthenticated):
    def has_permission(self, request, view):
        if super().has_permission(request, view):
            return True
        return view.action == 'create'
