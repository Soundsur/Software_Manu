# /backend/trans/urls.py

from django.urls import path, include
from .views import (
    # Transacciones:
    TransaccionCreateAPIView,
    TransaccionDetailAPIView,
    ConfirmarTransaccionAPIView,
    TransaccionDetalleAPIView,    
    # Historial de Ventas:
    HistorialVentasAPIView,
)

urlpatterns = [
    # --- Gestión de Transacciones ---
    # 1) Crear una Transacción (con lista de items y descuento global):
    path('transacciones/', TransaccionCreateAPIView.as_view(), name='transaccion-create'),
    # 2) Obtener detalle de transacción (incluye items, totales y descuento):
    path('transacciones/<int:pk>/', TransaccionDetailAPIView.as_view(), name='transaccion-detail'),
    # 3) Confirmar la transacción (verificar stock y descontar):
    path('transacciones/<int:pk>/confirmar/', ConfirmarTransaccionAPIView.as_view(), name='transaccion-confirmar'),    
    path('transacciones/<int:transaccion_id>/detalle/', TransaccionDetalleAPIView.as_view(), name='transaccion-detalle'),

    # Historial de Ventas
    path('historial-ventas/', HistorialVentasAPIView.as_view(), name='historial-ventas'),

]