# auth_service/urls.py

from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    MyTokenObtainPairView,
    LogoutView,
    MeView,
    # Gestión de usuarios:
    UserListCreateAPIView,
    UserDetailAPIView,
    UserProfileAPIView,
    UsuarioActualAPIView,
)

auth_urls = [
    path('login/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('logout/', LogoutView.as_view(), name='auth_logout'),
    path('me/', MeView.as_view(), name='auth_me'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]

urlpatterns = [
    # Rutas de autenticación
    path('user/', include(auth_urls)),

    # Rutas de gestión de usuarios (solo para administradores)
    path('usuarios/', UserListCreateAPIView.as_view(), name='user-list-create'),  # Listar y crear usuarios
    path('usuarios/<int:pk>/', UserDetailAPIView.as_view(), name='user-detail'),  # Obtener detalles de un usuario
    path('usuario-actual/', UsuarioActualAPIView.as_view(), name='usuario-actual'),
    path('profile/', UserProfileAPIView.as_view(), name='user-profile'),
]