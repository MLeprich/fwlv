"""
URL configuration for procurement app
"""

from django.urls import path
from . import views
from .staff_management_views import ProcurementStaffManagementView

app_name = 'procurement'

urlpatterns = [
    # Dashboard
    path('', views.ProcurementDashboardView.as_view(), name='dashboard'),

    # Staff Management
    path('personal/', ProcurementStaffManagementView.as_view(), name='staff_management'),

    # Departments (Fachbereiche)
    path('fachbereiche/', views.DepartmentListView.as_view(), name='department_list'),
    path('fachbereiche/neu/', views.DepartmentCreateView.as_view(), name='department_create'),
    path('fachbereiche/<int:pk>/bearbeiten/', views.DepartmentUpdateView.as_view(), name='department_update'),
    path('fachbereiche/<int:pk>/loeschen/', views.DepartmentDeleteView.as_view(), name='department_delete'),

    # Stammdaten Overview
    path('stammdaten/', views.StammdatenOverviewView.as_view(), name='stammdaten_overview'),

    # Sachkonten
    path('stammdaten/sachkonten/', views.SachkontoListView.as_view(), name='sachkonto_list'),
    path('stammdaten/sachkonten/neu/', views.SachkontoCreateView.as_view(), name='sachkonto_create'),
    path('stammdaten/sachkonten/<int:pk>/bearbeiten/', views.SachkontoUpdateView.as_view(), name='sachkonto_update'),
    path('stammdaten/sachkonten/<int:pk>/loeschen/', views.SachkontoDeleteView.as_view(), name='sachkonto_delete'),

    # NKF-Nummern
    path('stammdaten/nkf/', views.NKFListView.as_view(), name='nkf_list'),
    path('stammdaten/nkf/neu/', views.NKFCreateView.as_view(), name='nkf_create'),
    path('stammdaten/nkf/<int:pk>/bearbeiten/', views.NKFUpdateView.as_view(), name='nkf_update'),
    path('stammdaten/nkf/<int:pk>/loeschen/', views.NKFDeleteView.as_view(), name='nkf_delete'),

    # Verwendung Allgemein
    path('stammdaten/verwendung/', views.VerwendungListView.as_view(), name='verwendung_list'),
    path('stammdaten/verwendung/neu/', views.VerwendungCreateView.as_view(), name='verwendung_create'),
    path('stammdaten/verwendung/<int:pk>/bearbeiten/', views.VerwendungUpdateView.as_view(), name='verwendung_update'),
    path('stammdaten/verwendung/<int:pk>/loeschen/', views.VerwendungDeleteView.as_view(), name='verwendung_delete'),

    # Mengeneinheiten
    path('stammdaten/mengeneinheiten/', views.MengeneinheitListView.as_view(), name='mengeneinheit_list'),
    path('stammdaten/mengeneinheiten/neu/', views.MengeneinheitCreateView.as_view(), name='mengeneinheit_create'),
    path('stammdaten/mengeneinheiten/<int:pk>/bearbeiten/', views.MengeneinheitUpdateView.as_view(), name='mengeneinheit_update'),
    path('stammdaten/mengeneinheiten/<int:pk>/loeschen/', views.MengeneinheitDeleteView.as_view(), name='mengeneinheit_delete'),

    # Orders CRUD
    path('bestellungen/', views.OrderListView.as_view(), name='order_list'),
    path('bestellungen/neu/', views.OrderCreateView.as_view(), name='order_create'),
    path('bestellungen/<int:pk>/', views.OrderDetailView.as_view(), name='order_detail'),
    path('bestellungen/<int:pk>/bearbeiten/', views.OrderUpdateView.as_view(), name='order_update'),
    path('bestellungen/<int:pk>/loeschen/', views.OrderDeleteView.as_view(), name='order_delete'),

    # Status Actions
    path('bestellungen/<int:pk>/einreichen/', views.OrderSubmitView.as_view(), name='order_submit'),
    path('bestellungen/<int:pk>/stornieren/', views.OrderCancelView.as_view(), name='order_cancel'),
    path('bestellungen/<int:pk>/bestellt/', views.OrderMarkOrderedView.as_view(), name='order_mark_ordered'),
    path('bestellungen/<int:pk>/status/', views.OrderChangeStatusView.as_view(), name='order_change_status'),
    path('bestellungen/<int:pk>/pdf/', views.OrderPDFView.as_view(), name='order_pdf'),

    # Approval Workflow
    path('freigaben/', views.PendingApprovalsView.as_view(), name='approval_list'),
    path('freigaben/<int:pk>/entscheidung/', views.ApprovalActionView.as_view(), name='approval_action'),

    # Goods Receipt
    path('wareneingang/', views.GoodsReceiptListView.as_view(), name='receipt_list'),
    path('wareneingang/neu/', views.GoodsReceiptCreateView.as_view(), name='receipt_create'),
    path('wareneingang/neu/<int:order_pk>/', views.GoodsReceiptCreateView.as_view(), name='receipt_create_for_order'),
    path('wareneingang/<int:pk>/', views.GoodsReceiptDetailView.as_view(), name='receipt_detail'),

    # Suppliers
    path('lieferanten/', views.SupplierListView.as_view(), name='supplier_list'),
]
