"""Модуль permissions определяет пользовательские разрешения."""
from rest_framework import permissions


class AuthorOrReadOnly(permissions.BasePermission):
    """AuthorOrReadOnly.

    Разрешение для доступа к конечным точкам API
    только для автора или в режиме "только чтение".
    """

    def has_object_permission(self, request, view, obj):
        """Определяет, имеет ли пользователь разрешение на доступ к объекту."""
        return (
            request.method in permissions.SAFE_METHODS
            or obj.author == request.user
            or request.user.is_superuser
            or request.user.is_staff
        )
