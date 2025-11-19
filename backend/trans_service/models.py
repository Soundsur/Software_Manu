# trans_service/models.py

from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser
#
# --- Transacción (antes “carrito”) con DESCUENTO A NIVEL GLOBAL ---
#
class Transaccion(models.Model):

    usuario = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT,related_name="transacciones",null=True,blank=True)

    ESTADOS = [
        ('PENDIENTE', 'Pendiente'),
        ('CONFIRMADA', 'Confirmada'),
        ('FALLIDA',   'Fallida'),
    ]
    # ¡Elimina la definición de UUID! Django usará un AutoField por defecto.
    # id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    creado_en = models.DateTimeField(auto_now_add=True)
    confirmado_en = models.DateTimeField(null=True, blank=True)
    estado = models.CharField(max_length=10, choices=ESTADOS, default='PENDIENTE')
    descuento_carrito = models.DecimalField(max_digits=12, decimal_places=2, default=0)    
    porcentaje_descuento = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    class Meta:
        db_table = 'transaccion'

    @property
    def total(self):
        return sum(item.subtotal for item in self.item_set.all())

    @property
    def total_final(self):
        return self.total - self.descuento_carrito



#
# --- Ítem de la transacción (modificado para permitir eliminación de productos) ---
#
class Item(models.Model):
    transaccion = models.ForeignKey(Transaccion, on_delete=models.CASCADE)

    #producto = models.ForeignKey(Producto, on_delete=models.SET_NULL, null=True, blank=True)
    # Campos para preservar información histórica cuando se elimina el producto
    producto_codigo = models.CharField(max_length=100, null=True, blank=True)
    producto_nombre = models.CharField(max_length=300, null=True, blank=True)
    producto_precio = models.IntegerField(null=True, blank=True)
    cantidad = models.PositiveIntegerField(default=1)

    # Nuevo campo para marcar productos eliminados
    eliminado = models.BooleanField(default=False)  # Indica si el producto ha sido eliminado

    class Meta:
        db_table = 'item'

    @property
    def subtotal(self):
        """
        Precio a pagar por este ítem: (precio unitario * cantidad).
        El descuento ya se aplica únicamente a nivel de Transaccion.descuento_carrito,
        así que aquí no descontamos nada.
        """
        if self.producto_precio is not None:
            return self.producto_precio * self.cantidad
        return 0

    def __str__(self):
        return f"{self.producto_codigo} x{self.cantidad} (Transacción {self.transaccion.id})" #return f"{self.producto.codigo} x{self.cantidad} (Transacción {self.transaccion.id})"
