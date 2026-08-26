"""
Clothing URLs
URL-Konfiguration für Kleiderkammer
"""

from django.urls import path
from . import views
from .staff_management_views import ClothingStaffManagementView
from . import issue_list_views as issue

app_name = 'clothing'

urlpatterns = [
    # Dashboard
    path('', views.ClothingDashboardView.as_view(), name='dashboard'),

    # Kategorien
    path('categories/', views.ClothingCategoryListView.as_view(), name='category_list'),
    path('categories/create/', views.ClothingCategoryCreateView.as_view(), name='category_create'),
    path('categories/<int:pk>/update/', views.ClothingCategoryUpdateView.as_view(), name='category_update'),
    path('categories/<int:pk>/delete/', views.ClothingCategoryDeleteView.as_view(), name='category_delete'),

    # Item-Verwaltung
    path('items/', views.ClothingItemListView.as_view(), name='item_list'),
    path('items/<int:pk>/', views.ClothingItemDetailView.as_view(), name='item_detail'),
    path('items/create/', views.ClothingItemCreateView.as_view(), name='item_create'),
    path('items/<int:pk>/update/', views.ClothingItemUpdateView.as_view(), name='item_update'),
    path('items/<int:pk>/delete/', views.ClothingItemDeleteView.as_view(), name='item_delete'),

    # Barcode & QR-Code
    path('items/<int:pk>/barcode/', views.item_barcode, name='item_barcode'),
    path('items/<int:pk>/qr-code/', views.item_qr_code, name='item_qr_code'),

    # Lagerbewegungen
    path('movement/', views.ClothingStockMovementListView.as_view(), name='movement_list'),
    path('movement/<int:pk>/', views.ClothingStockMovementDetailView.as_view(), name='movement_detail'),
    path('movement/create/', views.ClothingStockMovementCreateView.as_view(), name='movement_create'),

    # AJAX Endpoints
    path('api/item/<int:pk>/locations/', views.get_item_locations, name='api_item_locations'),

    # PSA-Übersicht
    path('psa/', views.PSAOverviewView.as_view(), name='psa_overview'),
    path('psa/expiring/', views.PSAExpiringView.as_view(), name='psa_expiring'),

    # Prüfungen
    path('inspections/', views.InspectionListView.as_view(), name='inspection_list'),
    path('inspections/due/', views.InspectionDueView.as_view(), name='inspection_due'),

    # Personenzuordnungen
    path('assignments/', views.PersonAssignmentListView.as_view(), name='assignment_list'),
    path('person/<int:person_id>/sizes/', views.PersonSizeManagementView.as_view(), name='person_sizes'),

    # Import/Export
    path('import-export/', views.ImportExportView.as_view(), name='import_export'),

    # Export
    path('export/categories/', views.export_categories, name='export_categories'),
    path('export/items/', views.export_items, name='export_items'),
    path('export/movements/', views.export_movements, name='export_movements'),

    # Templates
    path('template/categories/', views.template_categories, name='template_categories'),
    path('template/items/', views.template_items, name='template_items'),

    # Import
    path('import/categories/', views.import_categories, name='import_categories'),
    path('import/items/', views.import_items, name='import_items'),

    # ========================================================================
    # STAMMDATEN / MASTER (Produktkatalog)
    # ========================================================================
    path('masters/', views.ClothingMasterListView.as_view(), name='master_list'),
    path('masters/create/', views.ClothingMasterCreateView.as_view(), name='master_create'),
    path('masters/<int:pk>/', views.ClothingMasterDetailView.as_view(), name='master_detail'),
    path('masters/<int:pk>/update/', views.ClothingMasterUpdateView.as_view(), name='master_update'),
    path('masters/<int:pk>/delete/', views.ClothingMasterDeleteView.as_view(), name='master_delete'),

    # ========================================================================
    # EXEMPLARE / INSTANZEN (konkrete Stücke zu einem Stammdatensatz)
    # ========================================================================
    path('instances/', views.ClothingInstanceListView.as_view(), name='instance_list'),
    path('instances/create/', views.ClothingInstanceCreateView.as_view(), name='instance_create'),
    path('instances/<int:pk>/', views.ClothingInstanceDetailView.as_view(), name='instance_detail'),
    path('instances/<int:pk>/update/', views.ClothingInstanceUpdateView.as_view(), name='instance_update'),
    path('instances/<int:pk>/delete/', views.ClothingInstanceDeleteView.as_view(), name='instance_delete'),

    # ========================================================================
    # PRODUKTTYPEN
    # ========================================================================
    path('producttypes/', views.ClothingProductTypeListView.as_view(), name='producttype_list'),
    path('producttypes/create/', views.ClothingProductTypeCreateView.as_view(), name='producttype_create'),
    path('producttypes/<int:pk>/update/', views.ClothingProductTypeUpdateView.as_view(), name='producttype_update'),
    path('producttypes/<int:pk>/delete/', views.ClothingProductTypeDeleteView.as_view(), name='producttype_delete'),

    # ========================================================================
    # INVENTUR (Inventory Check)
    # ========================================================================
    path('inventory/', views.ClothingInventoryListView.as_view(), name='inventory_list'),
    path('inventory/create/', views.ClothingInventoryCreateView.as_view(), name='inventory_create'),
    path('inventory/<int:pk>/', views.ClothingInventoryDetailView.as_view(), name='inventory_detail'),
    path('inventory/<int:pk>/start/', views.ClothingInventoryStartView.as_view(), name='inventory_start'),
    path('inventory/<int:pk>/count/', views.ClothingInventoryCountingView.as_view(), name='inventory_count'),
    path('inventory/<int:pk>/complete/', views.ClothingInventoryCompleteView.as_view(), name='inventory_complete'),
    path('inventory/<int:pk>/approve/', views.ClothingInventoryApproveView.as_view(), name='inventory_approve'),
    # HTMX Endpoints
    path('inventory/item/<int:pk>/update/', views.ClothingInventoryItemUpdateView.as_view(), name='inventory_item_update'),
    path('inventory/<int:pk>/progress/', views.ClothingInventoryProgressView.as_view(), name='inventory_progress'),
    # Export
    path('inventory/<int:pk>/export/', views.ClothingInventoryExportView.as_view(), name='inventory_export'),

    # ========================================================================
    # PERSONAL-VERWALTUNG (Staff Management)
    # ========================================================================
    path('staff-management/', ClothingStaffManagementView.as_view(), name='staff_management'),

    # ========================================================================
    # AUSGABELISTEN (Vorlagen + Ausgaben je Person)
    # ========================================================================
    path('issue-templates/', issue.IssueTemplateListView.as_view(), name='issue_template_list'),
    path('issue-templates/create/', issue.IssueTemplateCreateView.as_view(), name='issue_template_create'),
    path('issue-templates/<int:pk>/', issue.IssueTemplateDetailView.as_view(), name='issue_template_detail'),
    path('issue-templates/<int:pk>/update/', issue.IssueTemplateUpdateView.as_view(), name='issue_template_update'),
    path('issue-templates/<int:pk>/delete/', issue.IssueTemplateDeleteView.as_view(), name='issue_template_delete'),
    path('issue-templates/<int:pk>/pdf/', issue.IssueTemplatePdfView.as_view(), name='issue_template_pdf'),
    path('issue-templates/item/<int:pk>/delete/', issue.IssueTemplateItemDeleteView.as_view(), name='issue_template_item_delete'),
    path('issue-templates/item/<int:pk>/move/<str:direction>/', issue.IssueTemplateItemMoveView.as_view(), name='issue_template_item_move'),

    path('issue-lists/', issue.IssueListListView.as_view(), name='issue_list_list'),
    path('issue-lists/create/', issue.IssueListCreateView.as_view(), name='issue_list_create'),
    path('issue-lists/<int:pk>/', issue.IssueListDetailView.as_view(), name='issue_list_detail'),
    path('issue-lists/<int:pk>/update/', issue.IssueListUpdateView.as_view(), name='issue_list_update'),
    path('issue-lists/<int:pk>/delete/', issue.IssueListDeleteView.as_view(), name='issue_list_delete'),
    path('issue-lists/<int:pk>/pdf/', issue.IssueListPdfView.as_view(), name='issue_list_pdf'),
    path('issue-lists/<int:pk>/book-all/', issue.IssueListBookAllView.as_view(), name='issue_list_book_all'),
    path('issue-lists/<int:pk>/status/', issue.IssueListStatusPartialView.as_view(), name='issue_list_status'),
    path('issue-lists/item/<int:pk>/update/', issue.IssueListItemUpdateView.as_view(), name='issue_list_item_update'),
    path('issue-lists/item/<int:pk>/book/', issue.IssueListItemBookView.as_view(), name='issue_list_item_book'),
    path('issue-lists/item/<int:pk>/delete/', issue.IssueListItemDeleteView.as_view(), name='issue_list_item_delete'),
]
