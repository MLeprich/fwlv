"""
URL configuration for vehicle_handover app
"""

from django.urls import path
from . import views

app_name = 'vehicle_handover'

urlpatterns = [
    # Öffentliche Views (ohne Login)
    path('public/create/', views.PublicHandoverCreateView.as_view(), name='public_create'),
    path('public/success/', views.PublicHandoverSuccessView.as_view(), name='public_success'),
    path('public/api/vehicle/<int:vehicle_pk>/templates/', views.public_get_templates_for_vehicle, name='public_api_vehicle_templates'),
    path('public/api/check-person/', views.public_check_person, name='public_api_check_person'),

    # Dashboard
    path('', views.HandoverDashboardView.as_view(), name='dashboard'),

    # Checklisten-Templates
    path('templates/', views.ChecklistTemplateListView.as_view(), name='template_list'),
    path('templates/create/', views.ChecklistTemplateCreateView.as_view(), name='template_create'),
    path('templates/<int:pk>/', views.ChecklistTemplateDetailView.as_view(), name='template_detail'),
    path('templates/<int:pk>/edit/', views.ChecklistTemplateUpdateView.as_view(), name='template_update'),
    path('templates/<int:pk>/delete/', views.ChecklistTemplateDeleteView.as_view(), name='template_delete'),
    path('templates/<int:pk>/duplicate/', views.template_duplicate, name='template_duplicate'),

    # Kategorien verwalten
    path('templates/<int:template_pk>/categories/create/', views.CategoryCreateView.as_view(), name='category_create'),
    path('categories/<int:pk>/edit/', views.CategoryUpdateView.as_view(), name='category_update'),
    path('categories/<int:pk>/delete/', views.CategoryDeleteView.as_view(), name='category_delete'),

    # Items verwalten
    path('categories/<int:category_pk>/items/create/', views.ItemCreateView.as_view(), name='item_create'),
    path('items/<int:pk>/edit/', views.ItemUpdateView.as_view(), name='item_update'),
    path('items/<int:pk>/delete/', views.ItemDeleteView.as_view(), name='item_delete'),

    # API-Endpoints
    path('api/vehicle/<int:vehicle_pk>/templates/', views.get_templates_for_vehicle, name='api_vehicle_templates'),

    # Fahrzeugübergaben
    path('handovers/', views.HandoverListView.as_view(), name='handover_list'),
    path('handovers/create/', views.HandoverCreateWizardView.as_view(), name='handover_create'),
    path('handovers/<int:pk>/', views.HandoverDetailView.as_view(), name='handover_detail'),
    path('handovers/<int:pk>/resume/', views.handover_resume, name='handover_resume'),
    path('handovers/<int:pk>/pdf/', views.handover_pdf_export, name='handover_pdf_export'),
    path('handovers/<int:pk>/defect-pdf/', views.handover_defect_pdf_export, name='handover_defect_pdf_export'),

    # 360° Fahrzeuginnenraum-Verwaltung
    path('360/', views.Vehicle360PhotoListView.as_view(), name='photo_360_list'),
    path('360/upload/', views.Vehicle360PhotoCreateView.as_view(), name='photo_360_create'),
    path('360/<int:pk>/', views.Vehicle360PhotoDetailView.as_view(), name='photo_360_detail'),
    path('360/<int:pk>/edit/', views.Vehicle360PhotoUpdateView.as_view(), name='photo_360_update'),
    path('360/<int:pk>/delete/', views.Vehicle360PhotoDeleteView.as_view(), name='photo_360_delete'),
    path('360/<int:pk>/editor/', views.Vehicle360EditorView.as_view(), name='photo_360_editor'),

    # Hotspot-Verwaltung
    path('360/<int:photo_360_pk>/hotspots/create/', views.Vehicle360HotspotCreateView.as_view(), name='hotspot_create'),
    path('hotspots/<int:pk>/edit/', views.Vehicle360HotspotUpdateView.as_view(), name='hotspot_update'),
    path('hotspots/<int:pk>/delete/', views.Vehicle360HotspotDeleteView.as_view(), name='hotspot_delete'),
    path('hotspots/<int:pk>/update-position/', views.hotspot_update_position, name='hotspot_update_position'),
]
