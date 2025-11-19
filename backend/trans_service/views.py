import requests  # Para hacer las peticiones al servicio de ventas

from drf_yasg.utils import swagger_auto_schema
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone

from django.db.models import Q
from datetime import timedelta, datetime
import pytz
from .models import Transaccion, Item
from drf_yasg import openapi
import base64
import gzip
import json
from .bus_communication import BusCommunication  # Importar la clase BusCommunication
from ventas.serializers import HistorialVentasSerializer  # Importamos el serializer de ventas
from .serializers import (
    InputItemDTO,
    InputTransaccionSerializer,
    TransaccionDetailSerializer,
)

# ------------------------------
# Gestión de Transacciones
# ------------------------------

class TransaccionCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        security=[{"Bearer": []}],
        request_body=InputTransaccionSerializer,
        responses={201: TransaccionDetailSerializer, 400: "Error de validación"}
    )
    def post(self, request):
        # 1) Validar input
        serializer = InputTransaccionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        items_data = data["items"]
        porcentaje_descuento = data.get("porcentaje_descuento", 0)

        # Códigos de productos a consultar
        productos_codigos = [item["codigo"] for item in items_data]

        # Usamos BusCommunication para validar productos a través del bus
        bus_communication = BusCommunication()
        product_service = "ventas_api"  # Nombre del servicio que se encarga de productos

        # 2) Llamar al servicio de productos vía bus, con manejo de errores
        try:
            productos_response = bus_communication.send_transaction(
                product_service,
                f"{productos_codigos}",
            )
        except Exception as e:
            return Response(
                {
                    "error": "Error al comunicarse con el servicio de productos a través del bus",
                    "detalle": str(e),
                },
                status=status.HTTP_502_BAD_GATEWAY,
            )

        # 3) Validar formato de respuesta
        if not isinstance(productos_response, dict):
            return Response(
                {
                    "error": "Respuesta inválida desde el servicio de productos",
                    "respuesta": productos_response,
                },
                status=status.HTTP_502_BAD_GATEWAY,
            )

        # Se asume que el servicio remoto manda algo como: {"OK": true, "productos": [...]}
        if not productos_response.get("OK"):
            mensaje = productos_response.get("mensaje") or "No fue posible obtener los productos"
            return Response(
                {"error": mensaje, "respuesta": productos_response},
                status=status.HTTP_400_BAD_REQUEST,
            )

        productos_lista = productos_response.get("productos", [])
        productos = {p["codigo"]: p for p in productos_lista}

        # 4) Verificar que todos los códigos pedidos existen en la respuesta
        codigos_faltantes = [c for c in productos_codigos if c not in productos]
        if codigos_faltantes:
            return Response(
                {
                    "error": "Algunos productos no existen o están eliminados",
                    "codigos_no_encontrados": codigos_faltantes,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 5) Validar stock solo si el usuario es EMPLOYEE
        items_sin_stock = []
        if request.user.role == "EMPLOYEE":
            for item_data in items_data:
                codigo = item_data["codigo"]
                cantidad = item_data["cantidad"]
                producto = productos[codigo]

                try:
                    stock_response = bus_communication.send_transaction(
                        product_service,
                        f"stock-{codigo}",
                    )
                except Exception as e:
                    items_sin_stock.append(
                        {
                            "producto": producto["nombre"],
                            "stock_disponible": 0,
                            "cantidad_solicitada": cantidad,
                            "detalle": str(e),
                        }
                    )
                    continue

                if not isinstance(stock_response, dict) or not stock_response.get("OK"):
                    items_sin_stock.append(
                        {
                            "producto": producto["nombre"],
                            "stock_disponible": 0,
                            "cantidad_solicitada": cantidad,
                        }
                    )
                    continue

                stock = stock_response.get("stock", 0)
                if stock < cantidad:
                    items_sin_stock.append(
                        {
                            "producto": producto["nombre"],
                            "stock_disponible": stock,
                            "cantidad_solicitada": cantidad,
                        }
                    )

            if items_sin_stock:
                return Response(
                    {
                        "error": "Stock insuficiente",
                        "tipo_error": "STOCK_INSUFICIENTE_EMPLEADO",
                        "items_sin_stock": items_sin_stock,
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

        # 6) Crear transacción e items (para cualquier rol, si llegó hasta aquí)
        try:
            with transaction.atomic():
                # Calcular descuento en valor absoluto primero
                subtotal_temp = 0
                for item_data in items_data:
                    producto = productos[item_data["codigo"]]
                    cantidad = item_data["cantidad"]
                    item_subtotal = producto["precio"] * cantidad
                    subtotal_temp += item_subtotal

                descuento_valor = (subtotal_temp * porcentaje_descuento) / 100

                # Crear la transacción con el descuento calculado
                transaccion = Transaccion.objects.create(
                    usuario=request.user,
                    porcentaje_descuento=porcentaje_descuento,
                    descuento_carrito=descuento_valor,
                    estado="PENDIENTE",
                )

                # Crear los items
                for item_data in items_data:
                    producto = productos[item_data["codigo"]]
                    cantidad = item_data["cantidad"]

                    Item.objects.create(
                        transaccion=transaccion,
                        producto_codigo=producto["codigo"],
                        producto_nombre=producto["nombre"],
                        producto_precio=producto["precio"],
                        cantidad=cantidad,
                    )

                serializer_detalle = TransaccionDetailSerializer(transaccion)
                return Response(serializer_detalle.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TransaccionDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        security=[{"Bearer": []}],
        responses={200: TransaccionDetailSerializer, 404: "Transacción no encontrada"}
    )
    def get(self, request, pk):
        transaccion = get_object_or_404(Transaccion, pk=pk)
        serializer = TransaccionDetailSerializer(transaccion)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ConfirmarTransaccionAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        security=[{"Bearer": []}],
        responses={200: "Transacción confirmada", 404: "Transacción no encontrada", 400: "Error de validación"}
    )
    def post(self, request, pk):
        transaccion = get_object_or_404(Transaccion, pk=pk)
        
        if transaccion.estado == 'CONFIRMADA':
            return Response({"error": "La transacción ya está confirmada"}, status=status.HTTP_400_BAD_REQUEST)

        usuario = request.user
        items_sin_stock = []
        
        bus_communication = BusCommunication()
        product_service = "ventas_api"

        for item in transaccion.item_set.all():
            try:
                product_response = bus_communication.send_transaction(
                    product_service,
                    f"stock-{item.producto_codigo}"
                )

                if isinstance(product_response, dict) and product_response.get("OK"):
                    stock = product_response['stock']

                    # Verificar stock solo para empleados
                    if usuario.role == 'EMPLOYEE' and stock < item.cantidad:
                        items_sin_stock.append({
                            'producto': item.producto_nombre,
                            'stock_disponible': stock,
                            'cantidad_solicitada': item.cantidad
                        })
                        continue
                    
                    stock -= item.cantidad
                    stock_update_response = bus_communication.send_transaction(
                        product_service,
                        f"update-stock-{item.producto_codigo}-{stock}"
                    )

                    if not (isinstance(stock_update_response, dict) and stock_update_response.get("OK")):
                        items_sin_stock.append({
                            'producto': item.producto_nombre,
                            'stock_disponible': stock,
                            'cantidad_solicitada': item.cantidad
                        })
                        continue

                else:
                    # Si no existe stock, crear uno con cantidad negativa (solo para admins)
                    if usuario.role == 'ADMIN':
                        stock_create_response = bus_communication.send_transaction(
                            product_service,
                            f"create-stock-{item.producto_codigo}-{item.cantidad}"
                        )
                        
                        if not (isinstance(stock_create_response, dict) and stock_create_response.get("OK")):
                            items_sin_stock.append({
                                'producto': item.producto_nombre,
                                'stock_disponible': 0,
                                'cantidad_solicitada': item.cantidad
                            })
                    else:
                        items_sin_stock.append({
                            'producto': item.producto_nombre,
                            'stock_disponible': 0,
                            'cantidad_solicitada': item.cantidad
                        })
                    continue
                    
            except Exception:
                items_sin_stock.append({
                    'producto': item.producto_nombre,
                    'stock_disponible': 0,
                    'cantidad_solicitada': item.cantidad
                })

        # Para empleados, no permitir venta si hay items sin stock
        if usuario.role == 'EMPLOYEE' and items_sin_stock:
            return Response({
                "error": "Stock insuficiente",
                "items_sin_stock": items_sin_stock
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                transaccion.estado = 'CONFIRMADA'
                transaccion.confirmado_en = timezone.now()
                transaccion.save()

                return Response({
                    'mensaje': 'Transacción confirmada exitosamente',
                    'transaccion_id': transaccion.id,
                    'total_final': float(transaccion.total_final),
                    'items_sin_stock': items_sin_stock if usuario.role == 'ADMIN' and items_sin_stock else None
                }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TransaccionDetalleAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        security=[{"Bearer": []}],
        responses={200: "Detalle de transacción", 404: "Transacción no encontrada"}
    )
    def get(self, request, transaccion_id):
        """Obtener detalles completos de una transacción específica"""
        try:
            transaccion = Transaccion.objects.get(id=transaccion_id, estado='CONFIRMADA')
        except Transaccion.DoesNotExist:
            return Response(
                {"error": "Transacción no encontrada"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        vendedor_info = {
            'id': transaccion.usuario.id,
            'username': transaccion.usuario.username,
            'nombre_completo': f"{transaccion.usuario.first_name} {transaccion.usuario.last_name}".strip(),
            'role': transaccion.usuario.role
        }
        
        items = []
        for item in transaccion.item_set.all():
            items.append({
                'id': item.id,
                'producto_codigo': item.producto_codigo,
                'producto_nombre': item.producto_nombre,
                'cantidad': item.cantidad,
                'precio_unitario': float(item.producto_precio or 0),
                'subtotal': float(item.subtotal),
                # ya no hay FK, así que lo consideramos "histórico"
                'producto_activo': False
            })
        
        total_sin_descuento = float(transaccion.total)
        descuento_aplicado = float(transaccion.descuento_carrito)
        porcentaje_descuento = float(transaccion.porcentaje_descuento)
        total_final = float(transaccion.total_final)
        
        chile_tz = pytz.timezone('America/Santiago')
        fecha_creacion = transaccion.creado_en.astimezone(chile_tz) if transaccion.creado_en else None
        fecha_confirmacion = transaccion.confirmado_en.astimezone(chile_tz) if transaccion.confirmado_en else None
        
        detalle = {
            'id': transaccion.id,
            'estado': transaccion.estado,
            'fecha_creacion': fecha_creacion.isoformat() if fecha_creacion else None,
            'fecha_confirmacion': fecha_confirmacion.isoformat() if fecha_confirmacion else None,
            'fecha_creacion_local': fecha_creacion.strftime('%d/%m/%Y %H:%M:%S') if fecha_creacion else None,
            'fecha_confirmacion_local': fecha_confirmacion.strftime('%d/%m/%Y %H:%M:%S') if fecha_confirmacion else None,
            'vendedor': vendedor_info,
            'items': items,
            'total_sin_descuento': total_sin_descuento,
            'descuento_aplicado': descuento_aplicado,
            'porcentaje_descuento': porcentaje_descuento,
            'total_final': total_final,
            'cantidad_items': len(items),
            'cantidad_productos': sum(item['cantidad'] for item in items)
        }
        
        return Response(detalle, status=status.HTTP_200_OK)
    

# ------------------------------
# Historial de Ventas
# ------------------------------

class HistorialVentasAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        security=[{"Bearer": []}],
        manual_parameters=[
            openapi.Parameter('fecha_inicio', openapi.IN_QUERY, type=openapi.TYPE_STRING, description='Fecha inicio (YYYY-MM-DD)'),
            openapi.Parameter('fecha_fin', openapi.IN_QUERY, type=openapi.TYPE_STRING, description='Fecha fin (YYYY-MM-DD)'),
            openapi.Parameter('vendedor', openapi.IN_QUERY, type=openapi.TYPE_STRING, description='Filtrar por vendedor (username, nombre o apellido)'),
            openapi.Parameter('producto', openapi.IN_QUERY, type=openapi.TYPE_STRING, description='Filtrar por producto (código o nombre)'),
        ]
    )
    def get(self, request):
        """Obtener historial de ventas con filtros opcionales"""
        transacciones = Transaccion.objects.filter(estado='CONFIRMADA').order_by('-confirmado_en')
        
        fecha_inicio = request.query_params.get('fecha_inicio')
        fecha_fin = request.query_params.get('fecha_fin')
        vendedor = request.query_params.get('vendedor')
        producto = request.query_params.get('producto')
        
        if fecha_inicio:
            transacciones = transacciones.filter(confirmado_en__date__gte=fecha_inicio)
        if fecha_fin:
            transacciones = transacciones.filter(confirmado_en__date__lte=fecha_fin)
        if vendedor:
            transacciones = transacciones.filter(
                Q(usuario__username__icontains=vendedor) |
                Q(usuario__first_name__icontains=vendedor) |
                Q(usuario__last_name__icontains=vendedor)
            )
        if producto:
            transacciones = transacciones.filter(
                Q(item__producto_codigo__icontains=producto) |
                Q(item__producto_nombre__icontains=producto)
            ).distinct()

        historial = []
        for transaccion in transacciones:
            chile_tz = pytz.timezone('America/Santiago')
            fecha_local = transaccion.confirmado_en.astimezone(chile_tz) if transaccion.confirmado_en else None
            
            historial.append({
                'id': transaccion.id,
                'creado_en': transaccion.creado_en.isoformat() if transaccion.creado_en else None,
                'fecha': fecha_local.isoformat() if fecha_local else None,
                'fecha_local': fecha_local.strftime('%d/%m/%Y %H:%M:%S') if fecha_local else None,
                'vendedor': f"{transaccion.usuario.first_name} {transaccion.usuario.last_name}".strip() or transaccion.usuario.username,
                'vendedor_username': transaccion.usuario.username,
                'total': float(transaccion.total_final),
                'items': [
                    {
                        'producto': item.producto_nombre,
                        'cantidad': item.cantidad,
                        'precio_unitario': float(item.producto_precio or 0),
                        'subtotal': float(item.subtotal)
                    }
                    for item in transaccion.item_set.all()
                ]
            })
        
        return Response(historial, status=status.HTTP_200_OK)
