"""
URL Configuration für Reporting App
"""
from django.urls import path
from .views import ReportingDashboardView, PersonnelReportView, module_report

app_name = 'reporting'

urlpatterns = [
    path('', ReportingDashboardView.as_view(), name='dashboard'),
    path('personnel/', PersonnelReportView.as_view(), name='personnel_report'),
    path('module/<str:module_name>/', module_report, name='module_report'),
]
