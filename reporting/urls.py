"""
URL Configuration für Reporting App
"""
from django.urls import path
from .views import ReportingDashboardView, PersonnelReportView, module_report, dsgvo_personendaten_pdf

app_name = 'reporting'

urlpatterns = [
    path('', ReportingDashboardView.as_view(), name='dashboard'),
    path('personnel/', PersonnelReportView.as_view(), name='personnel_report'),
    path('dsgvo-personendaten/', dsgvo_personendaten_pdf, name='dsgvo_personendaten_pdf'),
    path('module/<str:module_name>/', module_report, name='module_report'),
]
