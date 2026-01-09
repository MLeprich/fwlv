"""
Vehicles URLs
URL-Konfiguration für Fahrzeugverwaltung
"""

from django.urls import path
from . import views

app_name = 'vehicles'

urlpatterns = [
    # Dashboard
    path('', views.VehicleDashboardView.as_view(), name='dashboard'),

    # Vehicle CRUD
    path('list/', views.VehicleListView.as_view(), name='list'),
    path('create/', views.VehicleCreateView.as_view(), name='create'),
    path('<int:pk>/', views.VehicleDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.VehicleUpdateView.as_view(), name='update'),
    path('<int:pk>/delete/', views.VehicleDeleteView.as_view(), name='delete'),

    # Lifecycle Management
    path('<int:pk>/set-replacement/', views.SetReplacementVehicleView.as_view(), name='set_replacement'),

    # Inspections & Maintenance
    path('<int:vehicle_pk>/inspection/create/', views.VehicleInspectionCreateView.as_view(), name='inspection_create'),
    path('inspection/create/', views.InspectionCreateDirectView.as_view(), name='inspection_create_direct'),
    path('inspection/<int:pk>/', views.InspectionDetailView.as_view(), name='inspection_detail'),
    path('inspection/<int:pk>/edit/', views.VehicleInspectionUpdateView.as_view(), name='inspection_update'),
    path('inspection/<int:pk>/delete/', views.VehicleInspectionDeleteView.as_view(), name='inspection_delete'),
    path('inspections/', views.InspectionListView.as_view(), name='inspection_list'),

    # Calendar
    path('calendar/', views.vehicle_calendar, name='calendar'),
    path('calendar/data/', views.CalendarDataView.as_view(), name='calendar_data'),  # Für alte FullCalendar-API falls noch benötigt

    # Quick Actions (HTMX Modals)
    path('<int:pk>/modal/mileage/', views.MileageUpdateModalView.as_view(), name='mileage_modal'),
    path('<int:pk>/modal/status/', views.StatusUpdateModalView.as_view(), name='status_modal'),
    path('<int:pk>/modal/inspection/', views.InspectionModalView.as_view(), name='inspection_modal'),

    # Mobile Storage / Beladungspläne
    path('<int:pk>/loading-plan/', views.LoadingPlanView.as_view(), name='loading_plan'),
    path('<int:pk>/loading-plan/edit/', views.LoadingPlanEditView.as_view(), name='loading_plan_edit'),

    # Handover - Verwende stattdessen die vehicle_handover App
    # path('<int:pk>/handover/create/', views.HandoverCreateView.as_view(), name='handover_create'),
    # path('handover/<int:pk>/', views.HandoverDetailView.as_view(), name='handover_detail'),

    # Manufacturers (Aliase für Abwärtskompatibilität - zeigen auf Models)
    path('manufacturers/', views.VehicleModelListView.as_view(), name='manufacturer_list'),
    path('manufacturers/create/', views.VehicleModelCreateView.as_view(), name='manufacturer_create'),
    path('manufacturers/<int:pk>/edit/', views.VehicleModelUpdateView.as_view(), name='manufacturer_update'),
    path('manufacturers/<int:pk>/delete/', views.VehicleModelDeleteView.as_view(), name='manufacturer_delete'),

    # Vehicle Detail Alias
    path('vehicle/<int:pk>/', views.VehicleDetailView.as_view(), name='vehicle_detail'),

    # Models
    path('models/', views.VehicleModelListView.as_view(), name='model_list'),
    path('models/create/', views.VehicleModelCreateView.as_view(), name='model_create'),
    path('models/<int:pk>/edit/', views.VehicleModelUpdateView.as_view(), name='model_update'),
    path('models/<int:pk>/delete/', views.VehicleModelDeleteView.as_view(), name='model_delete'),

    # Import & Export
    path('import-export/', views.ImportExportView.as_view(), name='import_export'),
    path('export/vehicles/', views.ExportVehiclesView.as_view(), name='export_vehicles'),
    path('export/models/', views.ExportModelsView.as_view(), name='export_models'),
    path('import/vehicles/', views.ImportVehiclesView.as_view(), name='import_vehicles'),
    path('import/models/', views.ImportModelsView.as_view(), name='import_models'),
    path('download-template/<str:template_type>/', views.DownloadTemplateView.as_view(), name='download_template'),
]
