# /backend/ventas/models.py

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings


#
# --- Producto y Stock (sin cambios) ---
#
class Producto(models.Model):
    codigo = models.CharField(max_length=100, unique=True, blank=True, null=True)
    nombre = models.CharField(max_length=300)
    # precio = models.DecimalField(max_digits=10, decimal_places=2) decimales
    precio = models.IntegerField()    # Antes DecimalField; ahora IntegerField
    eliminado = models.BooleanField(default=False)  # Soft delete
    eliminado_en = models.DateTimeField(null=True, blank=True)  # Fecha de eliminación
    creado_en = models.DateTimeField(auto_now_add=True, null=True)  # Fecha de creación
    actualizado_en = models.DateTimeField(auto_now=True, null=True)  # Fecha de última actualización

    
    class Meta:
        db_table = 'producto'

    def __str__(self):
        return f"{self.codigo} – {self.nombre}"


class Stock(models.Model):
    producto = models.OneToOneField(Producto, on_delete=models.CASCADE)
    cantidad = models.IntegerField(default=0)

    class Meta:
        db_table = 'stock'

    def __str__(self):
        return f"Stock({self.producto.codigo}): {self.cantidad}"
