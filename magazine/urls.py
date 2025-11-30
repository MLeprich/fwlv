"""
Magazine URLs
URL-Konfiguration für das Magazin-Modul
"""

from django.urls import path
from . import views
from .staff_management_views import MagazineStaffManagementView

app_name = 'magazine'

urlpatterns = [
    # Dashboard
    path('', views.MagazineDashboardView.as_view(), name='dashboard'),

    # ========================================================================
    # STAMMDATEN (Masters)
    # ========================================================================
    path('masters/', views.MagazineMasterListView.as_view(), name='master_list'),
    path('masters/create/', views.MagazineMasterCreateView.as_view(), name='master_create'),
    path('masters/<int:pk>/', views.MagazineMasterDetailView.as_view(), name='master_detail'),
    path('masters/<int:pk>/edit/', views.MagazineMasterUpdateView.as_view(), name='master_update'),
    path('masters/<int:pk>/barcode/', views.master_barcode_view, name='master_barcode'),
    path('masters/<int:pk>/qr-code/', views.master_qr_code_view, name='master_qr_code'),

    # ========================================================================
    # ARTIKEL (Legacy Items)
    # ========================================================================
    path('items/', views.MagazineItemListView.as_view(), name='item_list'),
    path('items/create/', views.MagazineItemCreateView.as_view(), name='item_create'),
    path('items/<int:pk>/', views.MagazineItemDetailView.as_view(), name='item_detail'),
    path('items/<int:pk>/edit/', views.MagazineItemUpdateView.as_view(), name='item_update'),
    path('items/<int:pk>/delete/', views.MagazineItemDeleteView.as_view(), name='item_delete'),
    path('items/<int:pk>/barcode/', views.item_barcode, name='item_barcode'),
    path('items/<int:pk>/qr-code/', views.item_qr_code, name='item_qr_code'),

    # Low Stock & Reorder
    path('low-stock/', views.LowStockListView.as_view(), name='low_stock'),
    path('reorder-needed/', views.ReorderNeededListView.as_view(), name='reorder_needed'),

    # Hazardous Items
    path('hazardous/', views.HazardousItemsListView.as_view(), name='hazardous_items'),

    # Stock Movements
    path('movements/', views.StockMovementListView.as_view(), name='movement_list'),
    path('movements/create/', views.StockMovementCreateView.as_view(), name='movement_create'),
    path('movements/<int:pk>/', views.StockMovementDetailView.as_view(), name='movement_detail'),

    # Batches
    path('batches/', views.BatchListView.as_view(), name='batch_list'),
    path('batches/expiring/', views.ExpiringBatchesListView.as_view(), name='expiring_batches'),

    # Categories
    path('categories/', views.CategoryListView.as_view(), name='category_list'),
    path('categories/create/', views.CategoryCreateView.as_view(), name='category_create'),
    path('categories/<int:pk>/edit/', views.CategoryUpdateView.as_view(), name='category_edit'),
    path('categories/<int:pk>/delete/', views.CategoryDeleteView.as_view(), name='category_delete'),

    # Import/Export
    path('import-export/', views.ImportExportView.as_view(), name='import_export'),

    # Export
    path('export/categories/', views.export_categories, name='export_categories'),
    path('export/items/', views.export_items, name='export_items'),
    path('export/batches/', views.export_batches, name='export_batches'),
    path('export/movements/', views.export_movements, name='export_movements'),

    # Templates
    path('template/categories/', views.template_categories, name='template_categories'),
    path('template/items/', views.template_items, name='template_items'),
    path('template/batches/', views.template_batches, name='template_batches'),

    # Import
    path('import/categories/', views.import_categories, name='import_categories'),
    path('import/items/', views.import_items, name='import_items'),
    path('import/batches/', views.import_batches, name='import_batches'),

    # ========================================================================
    # INVENTUR (Inventory Check)
    # ========================================================================
    path('inventory/', views.MagazineInventoryListView.as_view(), name='inventory_list'),
    path('inventory/create/', views.MagazineInventoryCreateView.as_view(), name='inventory_create'),
    path('inventory/<int:pk>/', views.MagazineInventoryDetailView.as_view(), name='inventory_detail'),
    path('inventory/<int:pk>/start/', views.MagazineInventoryStartView.as_view(), name='inventory_start'),
    path('inventory/<int:pk>/count/', views.MagazineInventoryCountingView.as_view(), name='inventory_count'),
    path('inventory/<int:pk>/complete/', views.MagazineInventoryCompleteView.as_view(), name='inventory_complete'),
    path('inventory/<int:pk>/approve/', views.MagazineInventoryApproveView.as_view(), name='inventory_approve'),
    # HTMX Endpoints
    path('inventory/item/<int:pk>/update/', views.MagazineInventoryItemUpdateView.as_view(), name='inventory_item_update'),
    path('inventory/<int:pk>/progress/', views.MagazineInventoryProgressView.as_view(), name='inventory_progress'),
    # Export
    path('inventory/<int:pk>/export/', views.MagazineInventoryExportView.as_view(), name='inventory_export'),

    # ========================================================================
    # PERSONAL-VERWALTUNG (Staff Management)
    # ========================================================================
    path('staff-management/', MagazineStaffManagementView.as_view(), name='staff_management'),
]
