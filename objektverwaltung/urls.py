from django.urls import path

from . import views

app_name = 'objektverwaltung'

urlpatterns = [
    path('', views.ObjektDashboardView.as_view(), name='dashboard'),

    # CSV Import/Export
    path('objekte/export/', views.BuildingObjectExportView.as_view(), name='export'),
    path('objekte/import/', views.BuildingObjectImportView.as_view(), name='import'),
    path('objekte/import/vorlage/', views.BuildingObjectImportTemplateView.as_view(), name='import_template'),

    # Objekt-CRUD
    path('objekte/', views.BuildingObjectListView.as_view(), name='list'),
    path('objekte/neu/', views.BuildingObjectCreateView.as_view(), name='create'),
    path('objekte/<int:pk>/', views.BuildingObjectDetailView.as_view(), name='detail'),
    path('objekte/<int:pk>/bearbeiten/', views.BuildingObjectUpdateView.as_view(), name='update'),
    path('objekte/<int:pk>/loeschen/', views.BuildingObjectDeleteView.as_view(), name='delete'),
    path('objekte/<int:pk>/akte.pdf', views.BuildingObjectAktePdfView.as_view(), name='akte_pdf'),

    # Abo / Folgen
    path('objekte/<int:pk>/folgen/', views.ToggleFollowView.as_view(), name='toggle_follow'),

    # Unterobjekte hinzufügen
    path('objekte/<int:pk>/etage/neu/', views.AddFloorView.as_view(), name='add_floor'),
    path('objekte/<int:pk>/fluchtweg/neu/', views.AddEscapeRouteView.as_view(), name='add_escape_route'),
    path('objekte/<int:pk>/bmz/neu/', views.AddFireAlarmPanelView.as_view(), name='add_fire_alarm_panel'),
    path('objekte/<int:pk>/ansprechpartner/neu/', views.AddContactView.as_view(), name='add_contact'),
    path('objekte/<int:pk>/plan/neu/', views.AddPlanView.as_view(), name='add_plan'),
    path('objekte/<int:pk>/fsd/neu/', views.AddKeyDepotView.as_view(), name='add_key_depot'),
    path('objekte/<int:pk>/loeschanlage/neu/', views.AddSuppressionSystemView.as_view(), name='add_suppression'),
    path('objekte/<int:pk>/kompensation/neu/', views.AddCompensationMeasureView.as_view(), name='add_compensation'),

    # Unterobjekte bearbeiten
    path('etage/<int:pk>/bearbeiten/', views.EditFloorView.as_view(), name='edit_floor'),
    path('fluchtweg/<int:pk>/bearbeiten/', views.EditEscapeRouteView.as_view(), name='edit_escape_route'),
    path('bmz/<int:pk>/bearbeiten/', views.EditFireAlarmPanelView.as_view(), name='edit_fire_alarm_panel'),
    path('ansprechpartner/<int:pk>/bearbeiten/', views.EditContactView.as_view(), name='edit_contact'),
    path('plan/<int:pk>/bearbeiten/', views.EditPlanView.as_view(), name='edit_plan'),
    path('fsd/<int:pk>/bearbeiten/', views.EditKeyDepotView.as_view(), name='edit_key_depot'),
    path('loeschanlage/<int:pk>/bearbeiten/', views.EditSuppressionSystemView.as_view(), name='edit_suppression'),
    path('kompensation/<int:pk>/bearbeiten/', views.EditCompensationMeasureView.as_view(), name='edit_compensation'),

    # Unterobjekte löschen
    path('etage/<int:pk>/loeschen/', views.DeleteFloorView.as_view(), name='delete_floor'),
    path('fluchtweg/<int:pk>/loeschen/', views.DeleteEscapeRouteView.as_view(), name='delete_escape_route'),
    path('bmz/<int:pk>/loeschen/', views.DeleteFireAlarmPanelView.as_view(), name='delete_fire_alarm_panel'),
    path('ansprechpartner/<int:pk>/loeschen/', views.DeleteContactView.as_view(), name='delete_contact'),
    path('plan/<int:pk>/loeschen/', views.DeletePlanView.as_view(), name='delete_plan'),
    path('fsd/<int:pk>/loeschen/', views.DeleteKeyDepotView.as_view(), name='delete_key_depot'),
    path('loeschanlage/<int:pk>/loeschen/', views.DeleteSuppressionSystemView.as_view(), name='delete_suppression'),
    path('kompensation/<int:pk>/loeschen/', views.DeleteCompensationMeasureView.as_view(), name='delete_compensation'),

    # Prüfungen: Übersicht, zentraler Einstieg, Anlagen, Prüfberichte
    path('pruefungen/', views.InspectionOverviewView.as_view(), name='inspection_list'),
    path('pruefungen/neu/', views.NewInspectionView.as_view(), name='inspection_new'),
    path('anlage/<str:type>/<int:pk>/', views.AssetDetailView.as_view(), name='asset_detail'),
    path('anlage/<str:type>/<int:pk>/pruefung/neu/', views.AddReportView.as_view(), name='report_add'),
    path('anlage/<str:type>/<int:pk>/pruefbericht-leer.pdf', views.AssetBlankPdfView.as_view(), name='asset_blank_pdf'),
    path('pruefung/<int:pk>/bearbeiten/', views.EditReportView.as_view(), name='report_edit'),
    path('pruefung/<int:pk>/loeschen/', views.DeleteReportView.as_view(), name='report_delete'),
    path('pruefung/<int:pk>/pdf/', views.ReportPdfView.as_view(), name='report_pdf'),

    # Bisherige FSD-Adressen bleiben gültig
    path('fsd/', views.InspectionOverviewView.as_view(), {'type': 'fsd'}, name='keydepot_list'),
    path('fsd/<int:pk>/', views.AssetDetailView.as_view(), {'type': 'fsd'}, name='keydepot_detail'),
    path('fsd/<int:pk>/pruefbericht/neu/', views.AddReportView.as_view(), {'type': 'fsd'}, name='fsd_report_add'),
    path('fsd/<int:pk>/pruefbericht-leer.pdf', views.AssetBlankPdfView.as_view(), {'type': 'fsd'}, name='keydepot_blank_pdf'),
    path('fsd-pruefbericht/<int:pk>/bearbeiten/', views.EditReportView.as_view(), name='fsd_report_edit'),
    path('fsd-pruefbericht/<int:pk>/loeschen/', views.DeleteReportView.as_view(), name='fsd_report_delete'),
    path('fsd-pruefbericht/<int:pk>/pdf/', views.ReportPdfView.as_view(), name='fsd_report_pdf'),
]
