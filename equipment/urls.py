"""
Equipment URLs
URL-Konfiguration für Ausrüstung & Geräte
"""

from django.urls import path
from . import views
from .staff_management_views import EquipmentStaffManagementView

app_name = 'equipment'

urlpatterns = [
    # Dashboard
    path('', views.EquipmentDashboardView.as_view(), name='dashboard'),

    # Master Data (Stammdaten)
    path('masters/', views.EquipmentMasterListView.as_view(), name='master_list'),
    path('master/<int:pk>/', views.EquipmentMasterDetailView.as_view(), name='master_detail'),
    path('master/create/', views.EquipmentMasterCreateView.as_view(), name='master_create'),
    path('master/<int:pk>/edit/', views.EquipmentMasterUpdateView.as_view(), name='master_edit'),
    path('master/<int:pk>/delete/', views.EquipmentMasterDeleteView.as_view(), name='master_delete'),
    path('master/<int:pk>/qrcode/', views.EquipmentMasterQRCodeView.as_view(), name='master_qrcode'),
    path('master/<int:pk>/barcode/', views.EquipmentMasterBarcodeView.as_view(), name='master_barcode'),

    # Batches (Chargen für Verbrauchsmaterial)
    path('batches/', views.EquipmentBatchListView.as_view(), name='batch_list'),
    path('batch/<int:pk>/', views.EquipmentBatchDetailView.as_view(), name='batch_detail'),
    path('batch/create/', views.EquipmentBatchCreateView.as_view(), name='batch_create'),
    path('batch/<int:pk>/edit/', views.EquipmentBatchUpdateView.as_view(), name='batch_edit'),
    path('batch/<int:pk>/delete/', views.EquipmentBatchDeleteView.as_view(), name='batch_delete'),

    # Device Instances (Geräte mit Inventarnummer)
    path('devices/', views.EquipmentDeviceListView.as_view(), name='device_list'),
    path('device/<int:pk>/', views.EquipmentDeviceDetailView.as_view(), name='device_detail'),
    path('device/create/', views.EquipmentDeviceCreateView.as_view(), name='device_create'),
    path('device/<int:pk>/edit/', views.EquipmentDeviceUpdateView.as_view(), name='device_edit'),
    path('device/<int:pk>/qrcode/', views.EquipmentDeviceQRCodeView.as_view(), name='device_qrcode'),
    path('device/<int:pk>/barcode/', views.EquipmentDeviceBarcodeView.as_view(), name='device_barcode'),
    path('devices/print-labels/', views.device_print_labels, name='device_print_labels'),
    path('devices/batch-qrcodes/', views.device_batch_qrcodes, name='device_batch_qrcodes'),
    path('devices/batch-barcodes/', views.device_batch_barcodes, name='device_batch_barcodes'),

    # Item-Verwaltung (Legacy)
    path('items/', views.EquipmentItemListView.as_view(), name='item_list'),
    path('item/<int:pk>/', views.EquipmentItemDetailView.as_view(), name='item_detail'),
    path('item/create/', views.EquipmentItemCreateView.as_view(), name='item_create'),
    path('item/<int:pk>/update/', views.EquipmentItemUpdateView.as_view(), name='item_update'),
    path('item/<int:pk>/edit/', views.EquipmentItemUpdateView.as_view(), name='item_edit'),  # Alias für item_update
    path('item/<int:pk>/delete/', views.EquipmentItemDeleteView.as_view(), name='item_delete'),

    # Equipment-Verwaltung (Aliase für Abwärtskompatibilität mit equipment_*.html Templates)
    path('equipment/', views.EquipmentItemListView.as_view(), name='equipment_list'),
    path('equipment/<int:pk>/', views.EquipmentItemDetailView.as_view(), name='equipment_detail'),
    path('equipment/create/', views.EquipmentItemCreateView.as_view(), name='equipment_create'),
    path('equipment/<int:pk>/update/', views.EquipmentItemUpdateView.as_view(), name='equipment_update'),
    path('equipment/<int:pk>/delete/', views.EquipmentItemDeleteView.as_view(), name='equipment_delete'),

    # Lagerbewegungen
    path('movement/', views.EquipmentStockMovementListView.as_view(), name='movement_list'),
    path('movement/<int:pk>/', views.EquipmentStockMovementDetailView.as_view(), name='movement_detail'),
    path('movement/create/', views.EquipmentStockMovementCreateView.as_view(), name='movement_create'),

    # Wartung & Prüfung
    path('maintenance/', views.MaintenanceListView.as_view(), name='maintenance_list'),
    path('maintenance/due/', views.MaintenanceDueView.as_view(), name='maintenance_due'),
    path('maintenance/management/', views.MaintenanceManagementView.as_view(), name='maintenance_management'),
    path('inspection/', views.InspectionListView.as_view(), name='inspection_list'),
    path('inspection/due/', views.InspectionDueView.as_view(), name='inspection_due'),

    # Fahrzeug-Ausrüstung
    path('vehicle/<int:vehicle_id>/', views.VehicleEquipmentListView.as_view(), name='vehicle_equipment'),

    # Defekte Geräte
    path('defective/', views.DefectiveEquipmentListView.as_view(), name='defective_list'),

    # Kategorien
    path('categories/', views.CategoryListView.as_view(), name='category_list'),
    path('categories/create/', views.CategoryCreateView.as_view(), name='category_create'),
    path('categories/<int:pk>/edit/', views.CategoryUpdateView.as_view(), name='category_edit'),
    path('categories/<int:pk>/delete/', views.CategoryDeleteView.as_view(), name='category_delete'),

    # Prüfungsarten-Verwaltung
    path('inspection-types/', views.InspectionTypeListView.as_view(), name='inspection_type_list'),
    path('inspection-types/create/', views.InspectionTypeCreateView.as_view(), name='inspection_type_create'),
    path('inspection-types/<int:pk>/edit/', views.InspectionTypeUpdateView.as_view(), name='inspection_type_edit'),
    path('inspection-types/<int:pk>/delete/', views.InspectionTypeDeleteView.as_view(), name='inspection_type_delete'),

    # Prüfprotokolle API
    path('api/inspection-types-by-device/', views.get_inspection_types_by_device, name='api_inspection_types_by_device'),
    path('api/inspection-checklist/', views.get_inspection_type_checklist, name='api_inspection_checklist'),

    # Prüfungszuweisungen (für Geräte)
    path('inspection-assignments/', views.EquipmentInspectionAssignmentListView.as_view(), name='inspection_assignment_list'),
    path('inspection-assignments/create/', views.EquipmentInspectionAssignmentCreateView.as_view(), name='inspection_assignment_create'),
    path('inspection-assignments/<int:pk>/edit/', views.EquipmentInspectionAssignmentUpdateView.as_view(), name='inspection_assignment_edit'),
    path('inspection-assignments/<int:pk>/delete/', views.EquipmentInspectionAssignmentDeleteView.as_view(), name='inspection_assignment_delete'),

    # Prüfprotokolle
    path('inspection-records/', views.InspectionRecordListView.as_view(), name='inspection_record_list'),
    path('inspection-records/create/', views.InspectionRecordCreateView.as_view(), name='inspection_record_create'),
    path('inspection-records/<int:pk>/', views.InspectionRecordDetailView.as_view(), name='inspection_record_detail'),

    # Wartungsarten-Verwaltung
    path('maintenance-types/', views.MaintenanceTypeListView.as_view(), name='maintenance_type_list'),
    path('maintenance-types/create/', views.MaintenanceTypeCreateView.as_view(), name='maintenance_type_create'),
    path('maintenance-types/<int:pk>/edit/', views.MaintenanceTypeUpdateView.as_view(), name='maintenance_type_edit'),
    path('maintenance-types/<int:pk>/delete/', views.MaintenanceTypeDeleteView.as_view(), name='maintenance_type_delete'),

    # Wartungszuweisungen (für einzelne Geräte - Legacy)
    path('maintenance-assignments/', views.MaintenanceAssignmentListView.as_view(), name='maintenance_assignment_list'),
    path('maintenance-assignments/create/', views.MaintenanceAssignmentCreateView.as_view(), name='maintenance_assignment_create'),
    path('maintenance-assignments/<int:pk>/edit/', views.MaintenanceAssignmentUpdateView.as_view(), name='maintenance_assignment_edit'),
    path('maintenance-assignments/<int:pk>/delete/', views.MaintenanceAssignmentDeleteView.as_view(), name='maintenance_assignment_delete'),

    # Stammdaten-Wartungszuweisungen (für Artikelstammdaten)
    path('master-maintenance-assignments/', views.MasterMaintenanceAssignmentListView.as_view(), name='master_maintenance_assignment_list'),
    path('master-maintenance-assignments/create/', views.MasterMaintenanceAssignmentCreateView.as_view(), name='master_maintenance_assignment_create'),
    path('master-maintenance-assignments/<int:pk>/', views.MasterMaintenanceAssignmentDetailView.as_view(), name='master_maintenance_assignment_detail'),
    path('master-maintenance-assignments/<int:pk>/edit/', views.MasterMaintenanceAssignmentUpdateView.as_view(), name='master_maintenance_assignment_edit'),
    path('master-maintenance-assignments/<int:pk>/delete/', views.MasterMaintenanceAssignmentDeleteView.as_view(), name='master_maintenance_assignment_delete'),

    # Wartungsprotokolle
    path('maintenance-records/', views.MaintenanceRecordListView.as_view(), name='maintenance_record_list'),
    path('maintenance-records/create/', views.MaintenanceRecordCreateView.as_view(), name='maintenance_record_create'),
    path('maintenance-records/<int:pk>/', views.MaintenanceRecordDetailView.as_view(), name='maintenance_record_detail'),

    # Import/Export
    path('import-export/', views.ImportExportView.as_view(), name='import_export'),

    # Export
    path('export/categories/', views.export_categories, name='export_categories'),
    path('export/masters/', views.export_masters, name='export_masters'),
    path('export/devices/', views.export_devices, name='export_devices'),
    path('export/movements/', views.export_movements, name='export_movements'),

    # Templates
    path('template/categories/', views.template_categories, name='template_categories'),
    path('template/masters/', views.template_masters, name='template_masters'),
    path('template/devices/', views.template_devices, name='template_devices'),

    # Import
    path('import/categories/', views.import_categories, name='import_categories'),
    path('import/masters/', views.import_masters, name='import_masters'),
    path('import/devices/', views.import_devices, name='import_devices'),

    # ========================================================================
    # INVENTUR (Inventory Check)
    # ========================================================================
    path('inventory/', views.EquipmentInventoryListView.as_view(), name='inventory_list'),
    path('inventory/create/', views.EquipmentInventoryCreateView.as_view(), name='inventory_create'),
    path('inventory/<int:pk>/', views.EquipmentInventoryDetailView.as_view(), name='inventory_detail'),
    path('inventory/<int:pk>/start/', views.EquipmentInventoryStartView.as_view(), name='inventory_start'),
    path('inventory/<int:pk>/count/', views.EquipmentInventoryCountingView.as_view(), name='inventory_count'),
    path('inventory/<int:pk>/complete/', views.EquipmentInventoryCompleteView.as_view(), name='inventory_complete'),
    path('inventory/<int:pk>/approve/', views.EquipmentInventoryApproveView.as_view(), name='inventory_approve'),
    # HTMX Endpoints
    path('inventory/item/<int:pk>/update/', views.EquipmentInventoryItemUpdateView.as_view(), name='inventory_item_update'),
    path('inventory/<int:pk>/progress/', views.EquipmentInventoryProgressView.as_view(), name='inventory_progress'),
    # Export
    path('inventory/<int:pk>/export/', views.EquipmentInventoryExportView.as_view(), name='inventory_export'),

    # ========================================================================
    # PERSONAL-VERWALTUNG (Staff Management)
    # ========================================================================
    path('staff-management/', EquipmentStaffManagementView.as_view(), name='staff_management'),
]
