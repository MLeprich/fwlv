"""
Civil Protection URLs
URL-Konfiguration für das Bevölkerungsschutz-Modul
"""

from django.urls import path
from . import views

app_name = 'civil_protection'

urlpatterns = [
    # Dashboard
    path('', views.DashboardView.as_view(), name='dashboard'),

    # Equipment Master
    path('equipment/', views.EquipmentMasterListView.as_view(), name='equipment_list'),
    path('equipment/create/', views.EquipmentMasterCreateView.as_view(), name='equipment_create'),
    path('equipment/<int:pk>/', views.EquipmentMasterDetailView.as_view(), name='equipment_detail'),
    path('equipment/<int:pk>/edit/', views.EquipmentMasterUpdateView.as_view(), name='equipment_update'),

    # Equipment Instances
    path('equipment/instances/', views.EquipmentInstanceListView.as_view(), name='equipment_instance_list'),
    path('equipment/instances/create/', views.EquipmentInstanceCreateView.as_view(), name='equipment_instance_create'),
    path('equipment/<int:master_pk>/instances/create/', views.EquipmentInstanceCreateView.as_view(), name='equipment_instance_create_for_master'),
    path('equipment/instances/<int:pk>/', views.EquipmentInstanceDetailView.as_view(), name='equipment_instance_detail'),
    path('equipment/instances/<int:pk>/edit/', views.EquipmentInstanceUpdateView.as_view(), name='equipment_instance_update'),

    # Vehicles (read-only, Fahrzeuge werden im Fahrzeug-Modul gepflegt)
    path('vehicles/', views.VehicleListView.as_view(), name='vehicle_list'),
    path('vehicles/calendar/', views.VehicleCalendarView.as_view(), name='vehicle_calendar'),
    path('vehicles/<int:pk>/', views.VehicleDetailView.as_view(), name='vehicle_detail'),

    # Medications
    path('medications/', views.MedicationMasterListView.as_view(), name='medication_list'),
    path('medications/create/', views.MedicationMasterCreateView.as_view(), name='medication_create'),
    path('medications/<int:pk>/', views.MedicationMasterDetailView.as_view(), name='medication_detail'),
    path('medications/<int:pk>/edit/', views.MedicationMasterUpdateView.as_view(), name='medication_update'),
    path('medications/<int:pk>/delete/', views.MedicationMasterDeleteView.as_view(), name='medication_delete'),

    # Medication Batches
    path('medications/<int:pk>/batches/create/', views.MedicationBatchCreateView.as_view(), name='batch_create'),
    path('batches/<int:pk>/', views.MedicationBatchDetailView.as_view(), name='batch_detail'),
    path('batches/<int:pk>/edit/', views.MedicationBatchUpdateView.as_view(), name='batch_update'),

    # Stock Movements
    path('movements/', views.StockMovementListView.as_view(), name='movement_list'),
    path('movements/create/', views.StockMovementCreateView.as_view(), name='movement_create'),

    # JSON-APIs für dynamisches Laden
    path('equipment/<int:pk>/instances-json/', views.equipment_instances_json, name='equipment_instances_json'),
    path('medications/<int:pk>/batches-json/', views.medication_batches_json, name='medication_batches_json'),

    # NIPs (read-only, data from Location model)
    path('nips/', views.NIPListView.as_view(), name='nip_list'),
    path('nips/<int:pk>/', views.NIPDetailView.as_view(), name='nip_detail'),

    # Leuchtturm (read-only, data from Location model)
    path('leuchtturm/', views.LeuchtturmListView.as_view(), name='leuchtturm_list'),
    path('leuchtturm/<int:pk>/', views.LeuchtturmDetailView.as_view(), name='leuchtturm_detail'),

    # Lending (Ausleihe)
    path('lending/', views.LendingListView.as_view(), name='lending_list'),
    path('lending/create/', views.LendingCreateView.as_view(), name='lending_create'),
    path('lending/<int:pk>/', views.LendingDetailView.as_view(), name='lending_detail'),
    path('lending/<int:pk>/edit/', views.LendingUpdateView.as_view(), name='lending_update'),
    path('lending/<int:pk>/return/', views.LendingReturnView.as_view(), name='lending_return'),
    path('lending/<int:pk>/ausgabe-pdf/', views.LendingAusgabePDFView.as_view(), name='lending_ausgabe_pdf'),
    path('lending/<int:pk>/rueckgabe-pdf/', views.LendingRueckgabePDFView.as_view(), name='lending_rueckgabe_pdf'),

    # Inventory Check
    path('inventory-checks/', views.InventoryCheckListView.as_view(), name='inventory_check_list'),
    path('inventory-checks/create/', views.InventoryCheckCreateView.as_view(), name='inventory_check_create'),
    path('inventory-checks/<int:pk>/', views.InventoryCheckDetailView.as_view(), name='inventory_check_detail'),
    path('inventory-checks/locations-json/', views.inventory_locations_json, name='inventory_locations_json'),

    # QR-Codes & Barcodes
    path('equipment/<int:pk>/qrcode/', views.equipment_master_qrcode, name='equipment_master_qrcode'),
    path('equipment/<int:pk>/barcode/', views.equipment_master_barcode, name='equipment_master_barcode'),
    path('equipment/instances/<int:pk>/qrcode/', views.equipment_instance_qrcode, name='equipment_instance_qrcode'),
    path('equipment/instances/<int:pk>/barcode/', views.equipment_instance_barcode, name='equipment_instance_barcode'),
    path('medications/<int:pk>/qrcode/', views.medication_master_qrcode, name='medication_master_qrcode'),
    path('medications/<int:pk>/barcode/', views.medication_master_barcode, name='medication_master_barcode'),
    path('batches/<int:pk>/qrcode/', views.batch_qrcode, name='batch_qrcode'),
    path('batches/<int:pk>/barcode/', views.batch_barcode, name='batch_barcode'),
]
