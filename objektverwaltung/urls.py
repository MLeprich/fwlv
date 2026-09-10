from django.urls import path

from . import views, views_bvs

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

    # Nutzungsarten verwalten
    path('nutzungsarten/', views.UsageCategoryListView.as_view(), name='usage_category_list'),
    path('nutzungsarten/neu/', views.UsageCategoryCreateView.as_view(), name='usage_category_create'),
    path('nutzungsarten/<int:pk>/bearbeiten/', views.UsageCategoryUpdateView.as_view(), name='usage_category_edit'),
    path('nutzungsarten/<int:pk>/loeschen/', views.UsageCategoryDeleteView.as_view(), name='usage_category_delete'),

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

    # Brandverhütungsschau: Übersicht, Vor-Ort-Schablone, Mängel, PDF
    path('bvs/', views_bvs.BVSOverviewView.as_view(), name='bvs_overview'),
    path('bvs/neu/', views_bvs.BVSStartView.as_view(), name='bvs_start'),
    path('objekte/<int:pk>/bvs/neu/', views_bvs.BVSStartView.as_view(), name='bvs_start_for_building'),
    path('bvs/<int:pk>/', views_bvs.BVSDetailView.as_view(), name='bvs_detail'),
    path('bvs/<int:pk>/speichern/', views_bvs.BVSSaveView.as_view(), name='bvs_save'),
    path('bvs/<int:pk>/abschliessen/', views_bvs.BVSCompleteView.as_view(), name='bvs_complete'),
    path('bvs/<int:pk>/wieder-oeffnen/', views_bvs.BVSReopenView.as_view(), name='bvs_reopen'),
    path('bvs/<int:pk>/loeschen/', views_bvs.BVSDeleteView.as_view(), name='bvs_delete'),
    path('bvs/<int:pk>/<str:part>.pdf', views_bvs.BVSPdfView.as_view(), name='bvs_pdf'),
    path('bvs/<int:pk>/mangel/neu/', views_bvs.DefectAddView.as_view(), name='bvs_defect_add'),
    path('bvs/<int:pk>/maengel/neu-nummerieren/', views_bvs.DefectRenumberView.as_view(), name='bvs_defect_renumber'),
    path('bvs/mangel/<int:pk>/', views_bvs.DefectSaveView.as_view(), name='bvs_defect_save'),
    path('bvs/mangel/<int:pk>/loeschen/', views_bvs.DefectDeleteView.as_view(), name='bvs_defect_delete'),
    path('bvs/mangel/<int:pk>/hoch/', views_bvs.DefectMoveView.as_view(), {'direction': 'hoch'}, name='bvs_defect_up'),
    path('bvs/mangel/<int:pk>/runter/', views_bvs.DefectMoveView.as_view(), {'direction': 'runter'}, name='bvs_defect_down'),
    path('bvs/mangel/<int:pk>/behoben/', views_bvs.DefectResolveView.as_view(), name='bvs_defect_resolve'),

    # Brandverhütungsschau: PSV-Fristen
    path('bvs/fristen/', views_bvs.PSVOverviewView.as_view(), name='psv_overview'),
    path('objekte/<int:pk>/psv/neu/', views_bvs.PSVRequirementAddView.as_view(), name='psv_add'),
    path('psv/<int:pk>/', views_bvs.PSVRequirementDetailView.as_view(), name='psv_detail'),
    path('psv/<int:pk>/bearbeiten/', views_bvs.PSVRequirementEditView.as_view(), name='psv_edit'),
    path('psv/<int:pk>/loeschen/', views_bvs.PSVRequirementDeleteView.as_view(), name='psv_delete'),
    path('psv/<int:pk>/pruefung/neu/', views_bvs.PSVCertificateAddView.as_view(), name='psv_certificate_add'),
    path('psv-pruefung/<int:pk>/bearbeiten/', views_bvs.PSVCertificateEditView.as_view(), name='psv_certificate_edit'),
    path('psv-pruefung/<int:pk>/loeschen/', views_bvs.PSVCertificateDeleteView.as_view(), name='psv_certificate_delete'),

    # Brandverhütungsschau: Pflege von Prüfarten und Mustersätzen
    path('bvs/pruefarten/', views_bvs.PSVTypeListView.as_view(), name='psv_type_list'),
    path('bvs/pruefarten/neu/', views_bvs.PSVTypeFormView.as_view(), name='psv_type_create'),
    path('bvs/pruefarten/<int:pk>/bearbeiten/', views_bvs.PSVTypeFormView.as_view(), name='psv_type_edit'),
    path('bvs/pruefarten/<int:pk>/loeschen/', views_bvs.PSVTypeDeleteView.as_view(), name='psv_type_delete'),
    path('bvs/mustersaetze/', views_bvs.PhraseListView.as_view(), name='bvs_phrase_list'),
    path('bvs/mustersaetze/neu/', views_bvs.PhraseFormView.as_view(), name='bvs_phrase_create'),
    path('bvs/mustersaetze/<int:pk>/bearbeiten/', views_bvs.PhraseFormView.as_view(), name='bvs_phrase_edit'),
    path('bvs/mustersaetze/<int:pk>/loeschen/', views_bvs.PhraseDeleteView.as_view(), name='bvs_phrase_delete'),
    path('bvs/mustersaetze/kapitel/neu/', views_bvs.PhraseCategoryFormView.as_view(), name='bvs_category_create'),
    path('bvs/mustersaetze/kapitel/<int:pk>/bearbeiten/', views_bvs.PhraseCategoryFormView.as_view(), name='bvs_category_edit'),
    path('bvs/mustersaetze/kapitel/<int:pk>/loeschen/', views_bvs.PhraseCategoryDeleteView.as_view(), name='bvs_category_delete'),

    # Bisherige FSD-Adressen bleiben gültig
    path('fsd/', views.InspectionOverviewView.as_view(), {'type': 'fsd'}, name='keydepot_list'),
    path('fsd/<int:pk>/', views.AssetDetailView.as_view(), {'type': 'fsd'}, name='keydepot_detail'),
    path('fsd/<int:pk>/pruefbericht/neu/', views.AddReportView.as_view(), {'type': 'fsd'}, name='fsd_report_add'),
    path('fsd/<int:pk>/pruefbericht-leer.pdf', views.AssetBlankPdfView.as_view(), {'type': 'fsd'}, name='keydepot_blank_pdf'),
    path('fsd-pruefbericht/<int:pk>/bearbeiten/', views.EditReportView.as_view(), name='fsd_report_edit'),
    path('fsd-pruefbericht/<int:pk>/loeschen/', views.DeleteReportView.as_view(), name='fsd_report_delete'),
    path('fsd-pruefbericht/<int:pk>/pdf/', views.ReportPdfView.as_view(), name='fsd_report_pdf'),
]
