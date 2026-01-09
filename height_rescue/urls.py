"""
URL configuration for height_rescue app
"""

from django.urls import path
from . import views
from .staff_management_views import HeightRescueStaffManagementView

app_name = 'height_rescue'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),

    # Equipment Types (Ausrüstungstypen-Verwaltung)
    path('equipment-types/', views.EquipmentTypeListView.as_view(), name='equipment_type_list'),
    path('equipment-types/create/', views.EquipmentTypeCreateView.as_view(), name='equipment_type_create'),
    path('equipment-types/<int:pk>/edit/', views.EquipmentTypeUpdateView.as_view(), name='equipment_type_edit'),
    path('equipment-types/<int:pk>/delete/', views.EquipmentTypeDeleteView.as_view(), name='equipment_type_delete'),

    # Master Data (Stammdaten)
    path('masters/', views.HeightRescueMasterListView.as_view(), name='master_list'),
    path('master/<int:pk>/', views.HeightRescueMasterDetailView.as_view(), name='master_detail'),
    path('master/create/', views.HeightRescueMasterCreateView.as_view(), name='master_create'),
    path('master/<int:pk>/edit/', views.HeightRescueMasterUpdateView.as_view(), name='master_edit'),
    path('master/<int:pk>/qrcode/', views.HeightRescueMasterQRCodeView.as_view(), name='master_qrcode'),
    path('master/<int:pk>/barcode/', views.HeightRescueMasterBarcodeView.as_view(), name='master_barcode'),

    # Device Instances (Geräte mit Inventarnummer)
    path('devices/', views.HeightRescueDeviceListView.as_view(), name='device_list'),
    path('device/<int:pk>/', views.HeightRescueDeviceDetailView.as_view(), name='device_detail'),
    path('device/create/', views.HeightRescueDeviceCreateView.as_view(), name='device_create'),
    path('device/<int:pk>/edit/', views.HeightRescueDeviceUpdateView.as_view(), name='device_edit'),
    path('device/<int:pk>/qrcode/', views.HeightRescueDeviceQRCodeView.as_view(), name='device_qrcode'),
    path('device/<int:pk>/barcode/', views.HeightRescueDeviceBarcodeView.as_view(), name='device_barcode'),

    # LEGACY Item URLs (Aliase für Abwärtskompatibilität - zeigen auf Device-Views)
    path('items/', views.HeightRescueDeviceListView.as_view(), name='item_list'),
    path('item/<int:pk>/', views.HeightRescueDeviceDetailView.as_view(), name='item_detail'),

    # Inspection Views
    path('inspections/due/', views.HeightRescueInspectionDueView.as_view(), name='inspection_due'),
    path('inspections/list/', views.HeightRescueInspectionListView.as_view(), name='inspection_list'),
    path('inspection-log/create/', views.HeightRescueInspectionLogCreateView.as_view(), name='inspection_log_create'),

    # Inspection Management
    path('inspection/management/', views.InspectionManagementView.as_view(), name='inspection_management'),
    path('inspection-types/', views.InspectionTypeListView.as_view(), name='inspection_type_list'),
    path('inspection-types/create/', views.InspectionTypeCreateView.as_view(), name='inspection_type_create'),
    path('inspection-types/<int:pk>/edit/', views.InspectionTypeUpdateView.as_view(), name='inspection_type_edit'),
    path('inspection-types/<int:pk>/delete/', views.InspectionTypeDeleteView.as_view(), name='inspection_type_delete'),

    # Retired Items
    path('retired/', views.HeightRescueRetiredListView.as_view(), name='retired_list'),
    path('falls/', views.HeightRescueFallListView.as_view(), name='fall_list'),

    # Movement Views
    path('movements/', views.HeightRescueMovementListView.as_view(), name='movement_list'),
    path('movements/<int:pk>/', views.HeightRescueMovementDetailView.as_view(), name='movement_detail'),
    path('movements/create/', views.HeightRescueMovementCreateView.as_view(), name='movement_create'),

    # Category Views
    path('categories/', views.CategoryListView.as_view(), name='category_list'),
    path('categories/create/', views.CategoryCreateView.as_view(), name='category_create'),
    path('categories/<int:pk>/edit/', views.CategoryUpdateView.as_view(), name='category_edit'),
    path('categories/<int:pk>/delete/', views.CategoryDeleteView.as_view(), name='category_delete'),

    # ========================================================================
    # INVENTUR (Inventory Check)
    # ========================================================================
    path('inventory/', views.HeightRescueInventoryListView.as_view(), name='inventory_list'),
    path('inventory/create/', views.HeightRescueInventoryCreateView.as_view(), name='inventory_create'),
    path('inventory/<int:pk>/', views.HeightRescueInventoryDetailView.as_view(), name='inventory_detail'),
    path('inventory/<int:pk>/start/', views.HeightRescueInventoryStartView.as_view(), name='inventory_start'),
    path('inventory/<int:pk>/count/', views.HeightRescueInventoryCountingView.as_view(), name='inventory_count'),
    path('inventory/<int:pk>/complete/', views.HeightRescueInventoryCompleteView.as_view(), name='inventory_complete'),
    path('inventory/<int:pk>/approve/', views.HeightRescueInventoryApproveView.as_view(), name='inventory_approve'),
    # HTMX Endpoints
    path('inventory/item/<int:pk>/update/', views.HeightRescueInventoryItemUpdateView.as_view(), name='inventory_item_update'),
    path('inventory/<int:pk>/progress/', views.HeightRescueInventoryProgressView.as_view(), name='inventory_progress'),
    # Export
    path('inventory/<int:pk>/export/', views.HeightRescueInventoryExportView.as_view(), name='inventory_export'),

    # ========================================================================
    # IMPORT/EXPORT
    # ========================================================================
    path('import-export/', views.ImportExportView.as_view(), name='import_export'),

    # Export
    path('export/masters/', views.export_masters, name='export_masters'),
    path('export/devices/', views.export_devices, name='export_devices'),
    path('export/inspections/', views.export_inspections, name='export_inspections'),

    # Templates
    path('template/masters/', views.template_masters, name='template_masters'),
    path('template/devices/', views.template_devices, name='template_devices'),

    # Import
    path('import/masters/', views.import_masters, name='import_masters'),
    path('import/devices/', views.import_devices, name='import_devices'),

    # ========================================================================
    # PERSONAL-VERWALTUNG (Staff Management)
    # ========================================================================
    path('staff-management/', HeightRescueStaffManagementView.as_view(), name='staff_management'),
]
