"""
Personnel URLs
URL-Konfiguration für Personnel App
"""

from django.urls import path
from django.views.generic import TemplateView
from . import views

app_name = 'personnel'

urlpatterns = [
    # Dashboard
    path('', views.personnel_dashboard, name='dashboard'),

    # Person URLs
    path('persons/', views.PersonListView.as_view(), name='list'),
    path('persons/<int:pk>/', views.PersonDetailView.as_view(), name='detail'),
    path('persons/create/', views.PersonCreateView.as_view(), name='create'),
    path('persons/<int:pk>/edit/', views.PersonUpdateView.as_view(), name='update'),
    path('persons/<int:pk>/delete/', views.PersonDeleteView.as_view(), name='delete'),

    # Aliase für personnel_* URLs (Abwärtskompatibilität)
    path('personnel/', views.PersonListView.as_view(), name='personnel_list'),
    path('personnel/<int:pk>/', views.PersonDetailView.as_view(), name='personnel_detail'),
    path('personnel/create/', views.PersonCreateView.as_view(), name='personnel_create'),
    path('personnel/<int:pk>/edit/', views.PersonUpdateView.as_view(), name='personnel_update'),

    # Qualification URLs
    path('persons/<int:person_pk>/qualifications/add/', views.QualificationCreateView.as_view(), name='qualification_create'),
    path('qualifications/', views.qualifications_overview, name='qualifications_overview'),
    path('qualifications/<int:pk>/edit/', views.QualificationUpdateView.as_view(), name='qualification_update'),
    path('qualifications/<int:pk>/delete/', views.QualificationDeleteView.as_view(), name='qualification_delete'),

    # Qualification Template URLs
    path('qualifications/templates/create/', views.template_create, name='template_create'),
    path('qualifications/templates/<int:pk>/edit/', views.template_edit, name='template_edit'),
    path('qualifications/templates/<int:pk>/delete/', views.template_delete, name='template_delete'),
    path('qualifications/templates/<int:pk>/data/', views.template_data_json, name='template_data_json'),

    # Inspection Calendar
    path('inspections/', views.inspections_calendar, name='inspections_calendar'),

    # Inspection CRUD URLs
    path('persons/<int:person_pk>/inspections/add/', views.InspectionCreateView.as_view(), name='inspection_create'),
    path('inspections/<int:pk>/edit/', views.InspectionUpdateView.as_view(), name='inspection_update'),
    path('inspections/<int:pk>/delete/', views.InspectionDeleteView.as_view(), name='inspection_delete'),
    path('inspections/<int:pk>/complete/', views.inspection_complete, name='inspection_complete'),

    # Duty Hours CRUD URLs
    path('persons/<int:person_pk>/dutyhours/add/', views.DutyHoursEntryCreateView.as_view(), name='dutyhours_create'),
    path('dutyhours/<int:pk>/edit/', views.DutyHoursEntryUpdateView.as_view(), name='dutyhours_update'),
    path('dutyhours/<int:pk>/delete/', views.DutyHoursEntryDeleteView.as_view(), name='dutyhours_delete'),
    path('persons/<int:person_pk>/dutyhours/overview/', views.dutyhours_overview, name='dutyhours_overview'),

    # Training Management
    path('trainings/', views.trainings_list, name='trainings'),

    # Import / Export
    path('import/', views.import_export_page, name='import'),
    path('import/template/', views.import_template, name='import_template'),
    path('import/readme/', views.import_readme, name='import_readme'),
    path('import/validate/', views.import_validate, name='import_validate'),
    path('import/execute/', views.import_execute, name='import_execute'),
    path('export/', views.export_personnel, name='export'),

    # Duty Hours Dashboard
    path('duty-hours/', views.dutyhours_dashboard, name='duty_hours'),

    # Phonebook (Telefonbuch)
    path('phonebook/', views.PhonebookView.as_view(), name='phonebook'),

    # FF-Verwaltung (Dienstgrade, Jubilaeen, Befoerderungen, Personalverwaltung)
    path('ff/', views.ff_dashboard, name='ff_dashboard'),
    path('ff/person/create/', views.ff_person_create, name='ff_person_create'),
    path('ff/person/<int:pk>/edit/', views.ff_person_edit, name='ff_person_edit'),
    path('ff/ranks/', views.RankListView.as_view(), name='rank_list'),
    path('ff/ranks/create/', views.RankCreateView.as_view(), name='rank_create'),
    path('ff/ranks/<int:pk>/edit/', views.RankUpdateView.as_view(), name='rank_update'),
    path('ff/ranks/<int:pk>/delete/', views.RankDeleteView.as_view(), name='rank_delete'),
]
