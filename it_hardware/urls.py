"""
URL configuration for it_hardware app
"""

from django.urls import path
from . import views

# Staff Management
from .staff_management_views import ITHardwareStaffManagementView

app_name = 'it_hardware'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),

    # Master Data (Stammdaten)
    path('masters/', views.ITHardwareMasterListView.as_view(), name='master_list'),
    path('master/<int:pk>/', views.ITHardwareMasterDetailView.as_view(), name='master_detail'),
    path('master/create/', views.ITHardwareMasterCreateView.as_view(), name='master_create'),
    path('master/<int:pk>/edit/', views.ITHardwareMasterUpdateView.as_view(), name='master_edit'),
    path('master/<int:pk>/qrcode/', views.ITHardwareMasterQRCodeView.as_view(), name='master_qrcode'),
    path('master/<int:pk>/barcode/', views.ITHardwareMasterBarcodeView.as_view(), name='master_barcode'),

    # Device Instances (Geräte mit Asset-Tag)
    path('devices/', views.ITHardwareDeviceListView.as_view(), name='device_list'),
    path('device/<int:pk>/', views.ITHardwareDeviceDetailView.as_view(), name='device_detail'),
    path('device/create/', views.ITHardwareDeviceCreateView.as_view(), name='device_create'),
    path('device/<int:pk>/edit/', views.ITHardwareDeviceUpdateView.as_view(), name='device_edit'),
    path('device/<int:pk>/qrcode/', views.ITHardwareDeviceQRCodeView.as_view(), name='device_qrcode'),
    path('device/<int:pk>/barcode/', views.ITHardwareDeviceBarcodeView.as_view(), name='device_barcode'),

    # IT Hardware Items (Legacy)
    path('items/', views.ITHardwareItemListView.as_view(), name='item_list'),
    path('items/create/', views.ITHardwareItemCreateView.as_view(), name='item_create'),
    path('items/<int:pk>/', views.ITHardwareItemDetailView.as_view(), name='item_detail'),
    path('items/<int:pk>/edit/', views.ITHardwareItemUpdateView.as_view(), name='item_update'),
    path('items/<int:pk>/delete/', views.ITHardwareItemDeleteView.as_view(), name='item_delete'),

    # Batch-Aliase (für Abwärtskompatibilität - zeigen auf Item-Views)
    path('batch/create/', views.ITHardwareItemCreateView.as_view(), name='batch_create'),
    path('batch/<int:pk>/', views.ITHardwareItemDetailView.as_view(), name='batch_detail'),
    path('batch/<int:pk>/edit/', views.ITHardwareItemUpdateView.as_view(), name='batch_edit'),

    # Stock Movements
    path('movements/', views.ITHardwareStockMovementListView.as_view(), name='movement_list'),
    path('movements/create/', views.ITHardwareStockMovementCreateView.as_view(), name='movement_create'),
    path('movements/<int:pk>/', views.ITHardwareStockMovementDetailView.as_view(), name='movement_detail'),

    # ========================================================================
    # INVENTUR (Inventory Check)
    # ========================================================================
    path('inventory/', views.ITHardwareInventoryListView.as_view(), name='inventory_list'),
    path('inventory/create/', views.ITHardwareInventoryCreateView.as_view(), name='inventory_create'),
    path('inventory/<int:pk>/', views.ITHardwareInventoryDetailView.as_view(), name='inventory_detail'),
    path('inventory/<int:pk>/start/', views.ITHardwareInventoryStartView.as_view(), name='inventory_start'),
    path('inventory/<int:pk>/count/', views.ITHardwareInventoryCountingView.as_view(), name='inventory_count'),
    path('inventory/<int:pk>/complete/', views.ITHardwareInventoryCompleteView.as_view(), name='inventory_complete'),
    path('inventory/<int:pk>/approve/', views.ITHardwareInventoryApproveView.as_view(), name='inventory_approve'),
    # HTMX Endpoints
    path('inventory/item/<int:pk>/update/', views.ITHardwareInventoryItemUpdateView.as_view(), name='inventory_item_update'),
    path('inventory/<int:pk>/progress/', views.ITHardwareInventoryProgressView.as_view(), name='inventory_progress'),
    # Export
    path('inventory/<int:pk>/export/', views.ITHardwareInventoryExportView.as_view(), name='inventory_export'),

    # ========================================================================
    # PERSONAL-VERWALTUNG (Staff Management)
    # ========================================================================
    path('staff-management/', ITHardwareStaffManagementView.as_view(), name='staff_management'),
]
