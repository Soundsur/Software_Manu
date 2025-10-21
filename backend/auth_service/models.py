# auth_service/models.py

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings

#
# --- Modelo de usuario personalizado (sin cambios) ---
#
class User(AbstractUser):
    ROLE_CHOICES = [
        ('ADMIN', 'Administrador'),
        ('EMPLOYEE', 'Empleado'),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, null=False, blank=False)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
