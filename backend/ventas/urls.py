# /backend/ventas/urls.py

from django.urls import path, include
from .views import (
    ProductoListCreateAPIView, # CRUD Productos y Stocks:
    ProductoDetailAPIView,
    ProductoBulkImportAPIView,
    ProductoBulkUpdateAPIView,
    StockListCreateAPIView,
    StockDetailAPIView,
    #Metricas de ventas:
    MetricsView,
    DashboardMetricsView, # Added import
    SalesChartDataView,   # Added import
)


urlpatterns = [


    # --- CRUD Productos ---
    path('productos/', ProductoListCreateAPIView.as_view(), name='producto-list-create'),
    path('productos/<int:pk>/', ProductoDetailAPIView.as_view(), name='producto-detail'),
    path('productos/bulk-import/', ProductoBulkImportAPIView.as_view(), name='producto-bulk-import'),
    path('productos/bulk-update/', ProductoBulkUpdateAPIView.as_view(), name='producto-bulk-update'),

    # --- CRUD Stocks ---
    path('stocks/', StockListCreateAPIView.as_view(), name='stock-list-create'),
    path('stocks/<int:pk>/', StockDetailAPIView.as_view(), name='stock-detail'),


    # --- Metricas de venta ---
    path('dashboard/metrics/', DashboardMetricsView.as_view(), name='dashboard-metrics'),
    path('metrics/', MetricsView.as_view(), name='metrics'),
    path('metrics/chart/', SalesChartDataView.as_view(), name='sales-chart-data'),
]








