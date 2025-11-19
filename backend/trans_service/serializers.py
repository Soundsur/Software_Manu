# /backend/trans/serializers.py

from rest_framework import serializers
from .models import Transaccion, Item

# ------------------------------
# DTO para cada ítem que viene en el "inputTransaccion"
# ------------------------------
class InputItemDTO(serializers.Serializer):
    codigo = serializers.CharField()
    cantidad = serializers.IntegerField(min_value=1)


# ------------------------------
# DTO para la creación de la Transacción (antes "carrito")
# ------------------------------
class InputTransaccionSerializer(serializers.Serializer):
    descuento_carrito = serializers.DecimalField(
        max_digits=12, decimal_places=2, min_value=0
    )
    porcentaje_descuento  = serializers.DecimalField(max_digits=5,  decimal_places=2, min_value=0)
    items = InputItemDTO(many=True)

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError("Debe enviar al menos un ítem en la Transacción.")
        return value


# ------------------------------
# Serializer que muestra cada ítem en la respuesta (nombre, cantidad y estado)
# ------------------------------
class OutputItemDTO(serializers.Serializer):
    nombre = serializers.CharField()
    cantidad = serializers.IntegerField()
    estado = serializers.ChoiceField(choices=["PENDIENTE", "CONFIRMADA", "FALLIDA"])


# ------------------------------
# Serializer para detalle de Transacción
# (incluye items, totales y descuento global)
# ------------------------------
class TransaccionDetailSerializer(serializers.ModelSerializer):
    items = serializers.SerializerMethodField()
    total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    descuento_carrito = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    total_final = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    porcentaje_descuento = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)

    class Meta:
        model = Transaccion
        fields = [
            'id',
            'creado_en',
            'confirmado_en',
            'estado',
            'descuento_carrito',
            'porcentaje_descuento',
            'total',
            'total_final',
            'items',
        ]

    def get_items(self, obj):
        """
        Convertir cada Item en la respuesta: { nombre, cantidad, estado }.
        Estado en este punto se corresponde con Transaccion.estado:
        Si la transacción está PENDIENTE, todos los ítems salen "PENDIENTE".
        Si está CONFIRMADA/FALLIDA, todos los ítems heredan ese mismo estado.
        """
        estado_global = obj.estado
        resultado = []
        for item in obj.item_set.all():
            nombre = item.producto_nombre or f"Producto {item.producto_codigo or ''}".strip()
            resultado.append({
                'nombre': nombre,
                'cantidad': item.cantidad,
                'estado': estado_global
            })
        return resultado
    