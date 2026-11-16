from rest_framework import permissions


class IsOwnerOrAdmin(permissions.BasePermission):
    """Libera o objeto apenas para o próprio usuário ou para administradores."""

    def has_object_permission(self, request, view, obj):
        return request.user.is_staff or obj.pk == request.user.pk
