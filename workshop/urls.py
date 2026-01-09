"""
Workshop URLs
URL-Konfiguration für KFZ-Werkstatt
"""

from django.urls import path
from . import views

# Inventur Views
from .inventory_views import (
    WorkshopInventoryListView,
    WorkshopInventoryCreateView,
    WorkshopInventoryDetailView,
    WorkshopInventoryStartView,
    WorkshopInventoryCountingView,
    WorkshopInventoryCompleteView,
    WorkshopInventoryApproveView,
    WorkshopInventoryItemUpdateView,
    WorkshopInventoryProgressView,
    WorkshopInventoryExportView,
)

# Staff Management
from .staff_management_views import WorkshopStaffManagementView

app_name = 'workshop'

urlpatterns = [
    # Dashboard
    path('', views.WorkshopDashboardView.as_view(), name='dashboard'),

    # Stammdaten (Master Data)
    path('masters/', views.WorkshopMasterListView.as_view(), name='master_list'),
    path('master/create/', views.WorkshopMasterCreateView.as_view(), name='master_create'),
    path('master/<int:pk>/', views.WorkshopMasterDetailView.as_view(), name='master_detail'),
    path('master/<int:pk>/edit/', views.WorkshopMasterUpdateView.as_view(), name='master_update'),

    # Werkzeug-Instanzen (Tool Instances)
    path('tools/', views.WorkshopToolListView.as_view(), name='tool_list'),
    path('tool/create/', views.WorkshopToolCreateView.as_view(), name='tool_create'),
    path('tool/<int:pk>/', views.WorkshopToolDetailView.as_view(), name='tool_detail'),
    path('tool/<int:pk>/edit/', views.WorkshopToolUpdateView.as_view(), name='tool_update'),

    # Device-Aliase (für Abwärtskompatibilität - zeigen auf Tool-Views)
    path('device/create/', views.WorkshopToolCreateView.as_view(), name='device_create'),
    path('device/<int:pk>/', views.WorkshopToolDetailView.as_view(), name='device_detail'),
    path('device/<int:pk>/edit/', views.WorkshopToolUpdateView.as_view(), name='device_edit'),

    # Workshop Item Verwaltung (Legacy)
    path('items/', views.WorkshopItemListView.as_view(), name='item_list'),
    path('item/<int:pk>/', views.WorkshopItemDetailView.as_view(), name='item_detail'),
    path('item/create/', views.WorkshopItemCreateView.as_view(), name='item_create'),
    path('item/<int:pk>/update/', views.WorkshopItemUpdateView.as_view(), name='item_update'),
    path('item/<int:pk>/delete/', views.WorkshopItemDeleteView.as_view(), name='item_delete'),
    path('item/<int:pk>/qrcode/', views.item_qrcode_view, name='item_qrcode'),
    path('item/<int:pk>/barcode/', views.item_barcode_view, name='item_barcode'),

    # Batch-Aliase (für Abwärtskompatibilität - zeigen auf Item-Views)
    path('batch/create/', views.WorkshopItemCreateView.as_view(), name='batch_create'),
    path('batch/<int:pk>/', views.WorkshopItemDetailView.as_view(), name='batch_detail'),
    path('batch/<int:pk>/edit/', views.WorkshopItemUpdateView.as_view(), name='batch_edit'),

    # Lagerbewegungen
    path('movement/', views.WorkshopStockMovementListView.as_view(), name='movement_list'),
    path('movement/<int:pk>/', views.WorkshopStockMovementDetailView.as_view(), name='movement_detail'),
    path('movement/create/', views.WorkshopStockMovementCreateView.as_view(), name='movement_create'),

    # Fahrzeug-Service
    path('service/', views.VehicleServiceRecordListView.as_view(), name='service_list'),
    path('service/<int:pk>/', views.VehicleServiceRecordDetailView.as_view(), name='service_detail'),
    path('service/create/', views.VehicleServiceRecordCreateView.as_view(), name='service_create'),
    path('service/<int:pk>/update/', views.VehicleServiceRecordUpdateView.as_view(), name='service_update'),
    path('service/<int:pk>/delete/', views.VehicleServiceRecordDeleteView.as_view(), name='service_delete'),

    # Special Views
    path('hazardous/', views.HazardousItemsListView.as_view(), name='hazardous_list'),
    path('low-stock/', views.LowStockItemsListView.as_view(), name='low_stock_list'),
    path('expired/', views.ExpiredItemsListView.as_view(), name='expired_list'),
    path('services/upcoming/', views.UpcomingServicesView.as_view(), name='upcoming_services'),
    path('services/overdue/', views.OverdueServicesView.as_view(), name='overdue_services'),
    path('vehicle/<int:vehicle_id>/services/', views.VehicleServicesView.as_view(), name='vehicle_services'),

    # Type Management (Werkzeug-/Artikeltypen)
    path('type-management/', views.WorkshopToolTypeListView.as_view(), name='type_management'),
    path('type-management/create/', views.WorkshopToolTypeCreateView.as_view(), name='type_create'),
    path('type-management/<int:pk>/edit/', views.WorkshopToolTypeUpdateView.as_view(), name='type_update'),
    path('type-management/<int:pk>/delete/', views.WorkshopToolTypeDeleteView.as_view(), name='type_delete'),

    # Kalender
    path('calendar/', views.workshop_calendar, name='calendar'),

    # ========================================================================
    # INVENTUR (Inventory Check)
    # ========================================================================
    path('inventory/', WorkshopInventoryListView.as_view(), name='inventory_list'),
    path('inventory/create/', WorkshopInventoryCreateView.as_view(), name='inventory_create'),
    path('inventory/<int:pk>/', WorkshopInventoryDetailView.as_view(), name='inventory_detail'),
    path('inventory/<int:pk>/start/', WorkshopInventoryStartView.as_view(), name='inventory_start'),
    path('inventory/<int:pk>/count/', WorkshopInventoryCountingView.as_view(), name='inventory_count'),
    path('inventory/<int:pk>/complete/', WorkshopInventoryCompleteView.as_view(), name='inventory_complete'),
    path('inventory/<int:pk>/approve/', WorkshopInventoryApproveView.as_view(), name='inventory_approve'),
    # HTMX Endpoints
    path('inventory/item/<int:pk>/update/', WorkshopInventoryItemUpdateView.as_view(), name='inventory_item_update'),
    path('inventory/<int:pk>/progress/', WorkshopInventoryProgressView.as_view(), name='inventory_progress'),
    # Export
    path('inventory/<int:pk>/export/', WorkshopInventoryExportView.as_view(), name='inventory_export'),

    # ========================================================================
    # IMPORT/EXPORT
    # ========================================================================
    path('import-export/', views.ImportExportView.as_view(), name='import_export'),

    # Export
    path('export/masters/', views.export_masters, name='export_masters'),
    path('export/tools/', views.export_tools, name='export_tools'),
    path('export/services/', views.export_services, name='export_services'),

    # Templates
    path('template/masters/', views.template_masters, name='template_masters'),
    path('template/tools/', views.template_tools, name='template_tools'),

    # Import
    path('import/masters/', views.import_masters, name='import_masters'),
    path('import/tools/', views.import_tools, name='import_tools'),

    # ========================================================================
    # PERSONAL-VERWALTUNG (Staff Management)
    # ========================================================================
    path('staff-management/', WorkshopStaffManagementView.as_view(), name='staff_management'),
]
