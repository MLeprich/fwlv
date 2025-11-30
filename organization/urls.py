"""
Organization URLs
URL-Konfiguration für Organization App
"""

from django.urls import path
from . import views

app_name = 'organization'

urlpatterns = [
    # Dashboard
    path('', views.organization_dashboard, name='dashboard'),

    # Department URLs
    path('departments/', views.DepartmentListView.as_view(), name='department_list'),
    path('departments/create/', views.DepartmentCreateView.as_view(), name='department_create'),
    path('departments/<int:pk>/edit/', views.DepartmentUpdateView.as_view(), name='department_update'),
    path('departments/<int:pk>/delete/', views.DepartmentDeleteView.as_view(), name='department_delete'),

    # Volunteer Unit URLs
    path('volunteer-units/', views.VolunteerUnitListView.as_view(), name='volunteer_unit_list'),
    path('volunteer-units/create/', views.VolunteerUnitCreateView.as_view(), name='volunteer_unit_create'),
    path('volunteer-units/<int:pk>/edit/', views.VolunteerUnitUpdateView.as_view(), name='volunteer_unit_update'),
    path('volunteer-units/<int:pk>/delete/', views.VolunteerUnitDeleteView.as_view(), name='volunteer_unit_delete'),

    # Watch Crew URLs
    path('watch-crews/', views.WatchCrewListView.as_view(), name='watch_crew_list'),
    path('watch-crews/create/', views.WatchCrewCreateView.as_view(), name='watch_crew_create'),
    path('watch-crews/<int:pk>/edit/', views.WatchCrewUpdateView.as_view(), name='watch_crew_update'),
    path('watch-crews/<int:pk>/delete/', views.WatchCrewDeleteView.as_view(), name='watch_crew_delete'),

    # Function URLs
    path('functions/', views.FunctionListView.as_view(), name='function_list'),
    path('functions/create/', views.FunctionCreateView.as_view(), name='function_create'),
    path('functions/<int:pk>/edit/', views.FunctionUpdateView.as_view(), name='function_update'),
    path('functions/<int:pk>/delete/', views.FunctionDeleteView.as_view(), name='function_delete'),

    # Qualification Template URLs
    path('qualification-templates/', views.QualificationTemplateListView.as_view(), name='qualification_template_list'),
    path('qualification-templates/create/', views.QualificationTemplateCreateView.as_view(), name='qualification_template_create'),
    path('qualification-templates/<int:pk>/edit/', views.QualificationTemplateUpdateView.as_view(), name='qualification_template_update'),
    path('qualification-templates/<int:pk>/delete/', views.QualificationTemplateDeleteView.as_view(), name='qualification_template_delete'),

    # Qualification Type URLs
    path('qualification-types/', views.QualificationTypeListView.as_view(), name='qualification_type_list'),
    path('qualification-types/create/', views.QualificationTypeCreateView.as_view(), name='qualification_type_create'),
    path('qualification-types/<int:pk>/edit/', views.QualificationTypeUpdateView.as_view(), name='qualification_type_update'),
    path('qualification-types/<int:pk>/delete/', views.QualificationTypeDeleteView.as_view(), name='qualification_type_delete'),

    # Duty Hours Requirement URLs
    path('duty-hours-requirements/', views.DutyHoursRequirementListView.as_view(), name='duty_hours_requirement_list'),
    path('duty-hours-requirements/create/', views.DutyHoursRequirementCreateView.as_view(), name='duty_hours_requirement_create'),
    path('duty-hours-requirements/<int:pk>/edit/', views.DutyHoursRequirementUpdateView.as_view(), name='duty_hours_requirement_update'),
    path('duty-hours-requirements/<int:pk>/delete/', views.DutyHoursRequirementDeleteView.as_view(), name='duty_hours_requirement_delete'),

    # Duty Hours Category URLs
    path('duty-hours-categories/', views.DutyHoursCategoryListView.as_view(), name='duty_hours_category_list'),
    path('duty-hours-categories/create/', views.DutyHoursCategoryCreateView.as_view(), name='duty_hours_category_create'),
    path('duty-hours-categories/<int:pk>/edit/', views.DutyHoursCategoryUpdateView.as_view(), name='duty_hours_category_update'),
    path('duty-hours-categories/<int:pk>/delete/', views.DutyHoursCategoryDeleteView.as_view(), name='duty_hours_category_delete'),

    # Supplier URLs
    path('suppliers/', views.SupplierListView.as_view(), name='supplier_list'),
    path('suppliers/<int:pk>/', views.SupplierDetailView.as_view(), name='supplier_detail'),
    path('suppliers/create/', views.SupplierCreateView.as_view(), name='supplier_create'),
    path('suppliers/<int:pk>/edit/', views.SupplierUpdateView.as_view(), name='supplier_edit'),
    path('suppliers/<int:pk>/delete/', views.SupplierDeleteView.as_view(), name='supplier_delete'),
]
