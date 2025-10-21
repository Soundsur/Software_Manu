# /backend/auth_service/permissions.py

from rest_framework.permissions import BasePermission

# ------------------------------
# Permisos personalizados
# ------------------------------

class IsAdminUser(BasePermission):
    """
    Permiso personalizado para permitir solo a usuarios con rol ADMIN
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'ADMIN'