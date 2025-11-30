"""
URL configuration for diving app
"""

from django.urls import path
from .views import (
    DivingMasterListView,
    DivingMasterCreateView,
    DivingMasterUpdateView,
    DivingMasterDetailView,
    DivingMasterQRCodeView,
    DivingMasterBarcodeView,
    DivingDeviceListView,
    DivingDeviceCreateView,
    DivingDeviceUpdateView,
    DivingDeviceDetailView,
    DivingDeviceQRCodeView,
    DivingDeviceBarcodeView,
    DivingDashboardView,
    DivingItemListView,
    DivingItemCreateView,
    DivingItemUpdateView,
    DivingMovementListView,
    DivingMovementDetailView,
    DivingMovementCreateView,
    DivingServiceListView,
    DivingServiceLogCreateView,
    DivingServiceManagementView,
    InspectionDueListView,
    ServiceRecordCreateView,
    AssignServiceTypeView,
    DeviceServiceAssignmentsView,
    ServiceTypeListView,
    ServiceTypeCreateView,
    ServiceTypeUpdateView,
    ServiceTypeDeleteView,
    TypeManagementView,
    EquipmentTypeListView,
    EquipmentTypeCreateView,
    EquipmentTypeUpdateView,
    EquipmentTypeDeleteView,
    BottleTypeListView,
    BottleTypeCreateView,
    BottleTypeUpdateView,
    BottleTypeDeleteView,
    DivingBatchListView,
    DivingBatchCreateView,
    DivingBatchUpdateView,
    DivingBatchDeleteView,
    # Import/Export
    ImportExportView,
    export_masters,
    export_devices,
    export_services,
    template_masters,
    template_devices,
    import_masters,
    import_devices,
)

# Inventur Views
from .inventory_views import (
    DivingInventoryListView,
    DivingInventoryCreateView,
    DivingInventoryDetailView,
    DivingInventoryStartView,
    DivingInventoryCountingView,
    DivingInventoryCompleteView,
    DivingInventoryApproveView,
    DivingInventoryItemUpdateView,
    DivingInventoryProgressView,
    DivingInventoryExportView,
)

# Staff Management
from .staff_management_views import DivingStaffManagementView

app_name = 'diving'

urlpatterns = [
    # Dashboard
    path('', DivingDashboardView.as_view(), name='dashboard'),

    # Stammdaten (Master Data)
    path('masters/', DivingMasterListView.as_view(), name='master_list'),
    path('master/create/', DivingMasterCreateView.as_view(), name='master_create'),
    path('master/<int:pk>/', DivingMasterDetailView.as_view(), name='master_detail'),
    path('master/<int:pk>/edit/', DivingMasterUpdateView.as_view(), name='master_update'),
    path('master/<int:pk>/qrcode/', DivingMasterQRCodeView.as_view(), name='master_qrcode'),
    path('master/<int:pk>/barcode/', DivingMasterBarcodeView.as_view(), name='master_barcode'),

    # Geräte-Instanzen (Device Instances)
    path('devices/', DivingDeviceListView.as_view(), name='device_list'),
    path('device/create/', DivingDeviceCreateView.as_view(), name='device_create'),
    path('device/<int:pk>/', DivingDeviceDetailView.as_view(), name='device_detail'),
    path('device/<int:pk>/edit/', DivingDeviceUpdateView.as_view(), name='device_update'),
    path('device/<int:pk>/qrcode/', DivingDeviceQRCodeView.as_view(), name='device_qrcode'),
    path('device/<int:pk>/barcode/', DivingDeviceBarcodeView.as_view(), name='device_barcode'),

    # Items (Legacy)
    path('items/', DivingItemListView.as_view(), name='item_list'),
    path('items/create/', DivingItemCreateView.as_view(), name='item_create'),
    path('items/<int:pk>/edit/', DivingItemUpdateView.as_view(), name='item_update'),

    # Lagerbewegungen
    path('movements/', DivingMovementListView.as_view(), name='movement_list'),
    path('movements/<int:pk>/', DivingMovementDetailView.as_view(), name='movement_detail'),
    path('movements/create/', DivingMovementCreateView.as_view(), name='movement_create'),

    # Wartungsverwaltung
    path('service-management/', DivingServiceManagementView.as_view(), name='service_management'),
    path('services/', DivingServiceListView.as_view(), name='service_list'),

    # Service Types (Wartungstypen)
    path('service-types/', ServiceTypeListView.as_view(), name='service_type_list'),
    path('service-types/create/', ServiceTypeCreateView.as_view(), name='service_type_create'),
    path('service-types/<int:pk>/edit/', ServiceTypeUpdateView.as_view(), name='service_type_edit'),
    path('service-types/<int:pk>/delete/', ServiceTypeDeleteView.as_view(), name='service_type_delete'),

    # Type Management (Typenverwaltung)
    path('type-management/', TypeManagementView.as_view(), name='type_management'),

    # Equipment Types
    path('equipment-types/', EquipmentTypeListView.as_view(), name='equipment_type_list'),
    path('equipment-types/create/', EquipmentTypeCreateView.as_view(), name='equipment_type_create'),
    path('equipment-types/<int:pk>/edit/', EquipmentTypeUpdateView.as_view(), name='equipment_type_edit'),
    path('equipment-types/<int:pk>/delete/', EquipmentTypeDeleteView.as_view(), name='equipment_type_delete'),

    # Bottle Types
    path('bottle-types/', BottleTypeListView.as_view(), name='bottle_type_list'),
    path('bottle-types/create/', BottleTypeCreateView.as_view(), name='bottle_type_create'),
    path('bottle-types/<int:pk>/edit/', BottleTypeUpdateView.as_view(), name='bottle_type_edit'),
    path('bottle-types/<int:pk>/delete/', BottleTypeDeleteView.as_view(), name='bottle_type_delete'),

    # Batch Management (Chargenverwaltung)
    path('master/<int:master_pk>/batches/', DivingBatchListView.as_view(), name='batch_list'),
    path('master/<int:master_pk>/batch/create/', DivingBatchCreateView.as_view(), name='batch_create'),
    path('batch/<int:pk>/edit/', DivingBatchUpdateView.as_view(), name='batch_edit'),
    path('batch/<int:pk>/delete/', DivingBatchDeleteView.as_view(), name='batch_delete'),

    # ========================================================================
    # INVENTUR (Inventory Check)
    # ========================================================================
    path('inventory/', DivingInventoryListView.as_view(), name='inventory_list'),
    path('inventory/create/', DivingInventoryCreateView.as_view(), name='inventory_create'),
    path('inventory/<int:pk>/', DivingInventoryDetailView.as_view(), name='inventory_detail'),
    path('inventory/<int:pk>/start/', DivingInventoryStartView.as_view(), name='inventory_start'),
    path('inventory/<int:pk>/count/', DivingInventoryCountingView.as_view(), name='inventory_count'),
    path('inventory/<int:pk>/complete/', DivingInventoryCompleteView.as_view(), name='inventory_complete'),
    path('inventory/<int:pk>/approve/', DivingInventoryApproveView.as_view(), name='inventory_approve'),
    # HTMX Endpoints
    path('inventory/item/<int:pk>/update/', DivingInventoryItemUpdateView.as_view(), name='inventory_item_update'),
    path('inventory/<int:pk>/progress/', DivingInventoryProgressView.as_view(), name='inventory_progress'),
    # Export
    path('inventory/<int:pk>/export/', DivingInventoryExportView.as_view(), name='inventory_export'),

    # Placeholder URLs für Template-Links
    path('items/<int:pk>/', DivingDashboardView.as_view(), name='item_detail'),
    path('inspection-due/', InspectionDueListView.as_view(), name='inspection_due'),
    path('retired/', DivingDashboardView.as_view(), name='retired_list'),
    path('inspection-management/', DivingServiceManagementView.as_view(), name='inspection_management'),
    path('inspections/list/', DivingServiceListView.as_view(), name='inspection_list'),
    path('service-log/create/', DivingServiceLogCreateView.as_view(), name='service_log_create'),

    # ========================================================================
    # NEUES WARTUNGSSYSTEM MIT CHECKLISTEN
    # ========================================================================
    # Service Record (Wartungsprotokoll) mit dynamischer Checkliste
    path('service-record/assignment/<int:assignment_pk>/create/',
         ServiceRecordCreateView.as_view(), name='service_record_create'),

    # Service Assignment (Wartungsart zu Gerät zuweisen)
    path('device/<int:device_pk>/assign-service-type/',
         AssignServiceTypeView.as_view(), name='assign_service_type'),

    # Gerät Wartungszuweisungen anzeigen
    path('device/<int:pk>/service-assignments/',
         DeviceServiceAssignmentsView.as_view(), name='device_service_assignments'),

    # ========================================================================
    # IMPORT/EXPORT
    # ========================================================================
    path('import-export/', ImportExportView.as_view(), name='import_export'),

    # Export
    path('export/masters/', export_masters, name='export_masters'),
    path('export/devices/', export_devices, name='export_devices'),
    path('export/services/', export_services, name='export_services'),

    # Templates
    path('template/masters/', template_masters, name='template_masters'),
    path('template/devices/', template_devices, name='template_devices'),

    # Import
    path('import/masters/', import_masters, name='import_masters'),
    path('import/devices/', import_devices, name='import_devices'),

    # ========================================================================
    # PERSONAL-VERWALTUNG (Staff Management)
    # ========================================================================
    path('staff-management/', DivingStaffManagementView.as_view(), name='staff_management'),
]
