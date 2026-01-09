"""
Medical URLs
URL-Konfiguration für das Medical-Modul (Rettungsdienst & BTM)
"""

from django.urls import path
from . import views
from .staff_management_views import MedicalStaffManagementView

app_name = 'medical'

urlpatterns = [
    # Dashboard
    path('', views.MedicalDashboardView.as_view(), name='dashboard'),

    # ========================================================================
    # STAMMDATEN (Master Data)
    # ========================================================================
    path('masters/', views.MedicalItemMasterListView.as_view(), name='master_list'),
    path('masters/create/', views.MedicalItemMasterCreateView.as_view(), name='master_create'),
    path('masters/<int:pk>/', views.MedicalItemMasterDetailView.as_view(), name='master_detail'),
    path('masters/<int:pk>/edit/', views.MedicalItemMasterUpdateView.as_view(), name='master_edit'),
    path('masters/<int:pk>/delete/', views.MedicalItemMasterDeleteView.as_view(), name='master_delete'),
    path('masters/<int:pk>/qrcode/', views.master_qrcode_view, name='master_qrcode'),
    path('masters/<int:pk>/barcode/', views.master_barcode_view, name='master_barcode'),

    # ========================================================================
    # GERÄTE-INSTANZEN (Device Instances)
    # ========================================================================
    path('devices/', views.MedicalDeviceInstanceListView.as_view(), name='device_list'),
    path('devices/create/', views.MedicalDeviceInstanceCreateView.as_view(), name='device_create'),
    path('devices/<int:pk>/', views.MedicalDeviceInstanceDetailView.as_view(), name='device_detail'),
    path('devices/<int:pk>/edit/', views.MedicalDeviceInstanceUpdateView.as_view(), name='device_edit'),
    path('devices/<int:pk>/delete/', views.MedicalDeviceInstanceDeleteView.as_view(), name='device_delete'),
    path('devices/<int:pk>/qrcode/', views.device_qrcode_view, name='device_qrcode'),
    path('devices/<int:pk>/barcode/', views.device_barcode_view, name='device_barcode'),
    path('devices/batch-qrcodes/', views.device_batch_qrcodes, name='device_batch_qrcodes'),
    path('devices/batch-barcodes/', views.device_batch_barcodes, name='device_batch_barcodes'),
    path('devices/print-labels/', views.device_print_labels, name='device_print_labels'),

    # ========================================================================
    # MEDICATION URLs (Aliase für Master-System - Abwärtskompatibilität)
    # ========================================================================
    path('medications/', views.MedicalItemMasterListView.as_view(), name='medication_list'),
    path('medications/create/', views.MedicalItemMasterCreateView.as_view(), name='medication_create'),
    path('medications/<int:pk>/', views.MedicalItemMasterDetailView.as_view(), name='medication_detail'),
    path('medications/<int:pk>/edit/', views.MedicalItemMasterUpdateView.as_view(), name='medication_update'),

    # BTM-Bereich
    path('btm/', views.BTMItemListView.as_view(), name='btm_list'),
    path('btm/approvals/', views.BTMApprovalListView.as_view(), name='btm_approvals'),
    path('btm/movement/<int:pk>/approve/', views.approve_btm_movement, name='approve_btm_movement'),
    path('btm/movement/<int:pk>/reject/', views.reject_btm_movement, name='reject_btm_movement'),

    # Low Stock & Expiring
    path('low-stock/', views.LowStockListView.as_view(), name='low_stock'),
    path('expiring-batches/', views.ExpiringBatchesListView.as_view(), name='expiring_batches'),

    # Kühlkette
    path('cold-chain/', views.ColdChainItemsListView.as_view(), name='cold_chain'),
    path('cold-chain/api-docs/', views.ColdChainAPIDocsView.as_view(), name='cold_chain_api_docs'),

    # Import/Export
    path('import-export/', views.ImportExportView.as_view(), name='import_export'),

    # Export
    path('export/masters/', views.export_masters, name='export_masters'),
    path('export/devices/', views.export_devices, name='export_devices'),
    path('export/batches/', views.export_batches, name='export_batches'),
    path('export/movements/', views.export_movements, name='export_movements'),

    # Templates
    path('template/masters/', views.template_masters, name='template_masters'),
    path('template/devices/', views.template_devices, name='template_devices'),
    path('template/batches/', views.template_batches, name='template_batches'),

    # Import
    path('import/masters/', views.import_masters, name='import_masters'),
    path('import/devices/', views.import_devices, name='import_devices'),
    path('import/batches/', views.import_batches, name='import_batches'),

    # Wartung
    path('maintenance-due/', views.MaintenanceDueListView.as_view(), name='maintenance_due'),

    # Stock Movements (Lagerbewegungen)
    path('movements/', views.StockMovementListView.as_view(), name='stock_movements'),
    path('movements/list/', views.StockMovementListView.as_view(), name='stock_movement_list'),  # Alias
    path('movements/create/', views.StockMovementCreateView.as_view(), name='stock_movement_create'),
    path('movements/incoming/', views.QuickIncomingView.as_view(), name='quick_incoming'),
    path('movements/outgoing/', views.QuickOutgoingView.as_view(), name='quick_outgoing'),
    path('movements/disposal/', views.DisposalView.as_view(), name='disposal'),
    path('movements/disposal-form/', views.DisposalView.as_view(), name='disposal_form'),  # Alias
    path('movements/<int:pk>/', views.StockMovementDetailView.as_view(), name='stock_movement_detail'),

    # Batches
    path('batches/', views.BatchListView.as_view(), name='batch_list'),
    path('batches/create/', views.UniversalBatchCreateView.as_view(), name='batch_create_universal'),
    path('batches/<int:pk>/', views.BatchDetailView.as_view(), name='batch_detail'),
    path('batches/recalled/', views.RecalledBatchesListView.as_view(), name='recalled_batches'),

    # Categories
    path('categories/', views.CategoryListView.as_view(), name='category_list'),
    path('categories/create/', views.CategoryCreateView.as_view(), name='category_create'),
    path('categories/<int:pk>/edit/', views.CategoryUpdateView.as_view(), name='category_edit'),
    path('categories/<int:pk>/delete/', views.CategoryDeleteView.as_view(), name='category_delete'),

    # Quick Stock Movement
    path('quick-movement/', views.QuickStockMovementView.as_view(), name='quick_stock_movement'),

    # Documents
    path('items/<int:item_pk>/documents/', views.item_documents_list, name='item_documents_list'),
    path('items/<int:item_pk>/documents/upload/', views.item_document_upload, name='item_document_upload'),
    path('items/<int:item_pk>/documents/<int:doc_pk>/download/', views.item_document_download, name='document_download'),
    path('items/<int:item_pk>/documents/<int:doc_pk>/delete/', views.item_document_delete, name='document_delete'),

    # ========================================================================
    # INVENTUR (Inventory Check)
    # ========================================================================
    path('inventory/', views.MedicalInventoryListView.as_view(), name='inventory_list'),
    path('inventory/create/', views.MedicalInventoryCreateView.as_view(), name='inventory_create'),
    path('inventory/<int:pk>/', views.MedicalInventoryDetailView.as_view(), name='inventory_detail'),
    path('inventory/<int:pk>/start/', views.MedicalInventoryStartView.as_view(), name='inventory_start'),
    path('inventory/<int:pk>/count/', views.MedicalInventoryCountingView.as_view(), name='inventory_count'),
    path('inventory/<int:pk>/complete/', views.MedicalInventoryCompleteView.as_view(), name='inventory_complete'),
    path('inventory/<int:pk>/approve/', views.MedicalInventoryApproveView.as_view(), name='inventory_approve'),
    # HTMX Endpoints
    path('inventory/item/<int:pk>/update/', views.MedicalInventoryItemUpdateView.as_view(), name='inventory_item_update'),
    path('inventory/<int:pk>/progress/', views.MedicalInventoryProgressView.as_view(), name='inventory_progress'),
    # Export
    path('inventory/<int:pk>/export/', views.MedicalInventoryExportView.as_view(), name='inventory_export'),

    # ========================================================================
    # PERSONAL-VERWALTUNG (Staff Management)
    # ========================================================================
    path('staff-management/', MedicalStaffManagementView.as_view(), name='staff_management'),
]
