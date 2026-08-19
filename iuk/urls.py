"""URL-Konfiguration für das IUK-Modul (Drohnenstaffel)."""

from django.urls import path

from . import views

app_name = 'iuk'

urlpatterns = [
    path('', views.IukDashboardView.as_view(), name='dashboard'),

    # Drohnen
    path('drohnen/', views.DroneListView.as_view(), name='drone_list'),
    path('drohnen/neu/', views.DroneCreateView.as_view(), name='drone_create'),
    path('drohnen/<int:pk>/bearbeiten/', views.DroneUpdateView.as_view(), name='drone_edit'),
    path('drohnen/<int:pk>/loeschen/', views.DroneDeleteView.as_view(), name='drone_delete'),

    # Drohnenführerscheine
    path('fuehrerscheine/', views.DroneLicenseListView.as_view(), name='license_list'),
    path('fuehrerscheine/neu/', views.DroneLicenseCreateView.as_view(), name='license_create'),
    path('fuehrerscheine/<int:pk>/bearbeiten/', views.DroneLicenseUpdateView.as_view(), name='license_edit'),
    path('fuehrerscheine/<int:pk>/loeschen/', views.DroneLicenseDeleteView.as_view(), name='license_delete'),

    # Flugbuch
    path('flugbuch/', views.FlightLogListView.as_view(), name='flight_list'),
    path('flugbuch/neu/', views.FlightLogCreateView.as_view(), name='flight_create'),
    path('flugbuch/pdf/', views.flight_book_pdf, name='flight_book_pdf'),
    path('flugbuch/statistik/', views.FlightStatisticsView.as_view(), name='flight_statistics'),
    path('flugbuch/statistik/csv/', views.flight_statistics_csv, name='flight_statistics_csv'),
    path('flugbuch/checklisten.json', views.drone_checklists_json, name='drone_checklists_json'),
    path('flugbuch/checklisten/', views.DroneChecklistListView.as_view(), name='checklist_list'),
    path('flugbuch/checklisten/neu/', views.DroneChecklistCreateView.as_view(), name='checklist_create'),
    path('flugbuch/checklisten/<int:pk>/bearbeiten/', views.DroneChecklistUpdateView.as_view(), name='checklist_edit'),
    path('flugbuch/checklisten/<int:pk>/loeschen/', views.DroneChecklistDeleteView.as_view(), name='checklist_delete'),
    path('flugbuch/<int:pk>/', views.FlightLogDetailView.as_view(), name='flight_detail'),
    path('flugbuch/<int:pk>/pdf/', views.flight_log_pdf, name='flight_pdf'),

    # Gutscheincodes
    path('gutscheine/', views.VoucherListView.as_view(), name='voucher_list'),
    path('gutscheine/neu/', views.VoucherCreateView.as_view(), name='voucher_create'),
    path('gutscheine/import/', views.VoucherImportView.as_view(), name='voucher_import'),
    path('gutscheine/import/vorlage/', views.voucher_import_template, name='voucher_import_template'),
    path('gutscheine/<int:pk>/', views.VoucherDetailView.as_view(), name='voucher_detail'),
    path('gutscheine/<int:pk>/bearbeiten/', views.VoucherUpdateView.as_view(), name='voucher_edit'),
    path('gutscheine/<int:pk>/vergeben/', views.VoucherAssignView.as_view(), name='voucher_assign'),
    path('gutscheine/<int:pk>/einloesen/', views.VoucherUseView.as_view(), name='voucher_use'),
    path('gutscheine/<int:pk>/loeschen/', views.VoucherDeleteView.as_view(), name='voucher_delete'),
]
