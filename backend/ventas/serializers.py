# /backend/ventas/serializers.py

from rest_framework import serializers
from .models import Producto, Stock
from .bus_communication import BusCommunication


# ------------------------------
# Serializer para Producto
# ------------------------------

class ProductoSerializer(serializers.ModelSerializer):
    # Campo extra que toma obj.stock.cantidad o 0 si no existe relación
    stock = serializers.SerializerMethodField()

    class Meta:
        model = Producto
        fields = ['id', 'codigo', 'nombre', 'precio', 'stock']  # agregamos el campo “stock”

    def get_stock(self, obj):
        # Si existe un registro de Stock para este Producto, devolvemos la cantidad; si no, 0
        try:
            return obj.stock.cantidad
        except Stock.DoesNotExist:
            return 0


# ------------------------------
# Serializer para Stock
# ------------------------------

class StockSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stock
        fields = '__all__'



# ------------------------------
# Serializer para Historial de Ventas
# ------------------------------


class HistorialItemSerializer(serializers.Serializer):
    producto = serializers.CharField(source='producto.nombre')
    cantidad = serializers.IntegerField()

class HistorialVentasSerializer(serializers.ModelSerializer):
    vendedor = serializers.CharField(source='usuario.username', read_only=True)
    total = serializers.DecimalField(source='total_final', max_digits=12, decimal_places=2, read_only=True)
    fecha = serializers.DateTimeField(source='creado_en', read_only=True)
    items = HistorialItemSerializer(source='item_set', many=True)  # Nombre 'items' coincide con tu frontend

    class Meta:
        #model = Transaccion
        fields = [
            'id',
            'vendedor',
            'total',
            'fecha',
            'items',
        ]
    def get_items_vendidos(self, obj):
        return [
            {'producto': i.producto.nombre, 'cantidad': i.cantidad}
            for i in obj.item_set.all()
        ]  
    def get_transaccion(self, obj):
        # Inicializar la conexión al bus
        bus = BusCommunication()

        # Aquí se llama al servicio de transacciones a través del bus
        service_name = "trans_service"  # El nombre del servicio que quieres llamar
        data = f"ID:{obj.id}"  # Los datos de la transacción (puedes estructurarlos como desees)

        # Enviar la transacción al bus y recibir la respuesta
        response = bus.send_transaction(service_name, data)
        
        # Si la respuesta contiene el estado "OK", procesamos la transacción
        if "OK" in response:
            # Aquí puedes hacer algo más con la respuesta si es necesario
            return "Transacción procesada con éxito."
        else:
            return "Error al procesar la transacción."