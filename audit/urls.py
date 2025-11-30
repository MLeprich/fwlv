"""
Audit URLs
URL-Konfiguration für Audit App
"""

from django.urls import path
from . import views

app_name = 'audit'

urlpatterns = [
    # Alle Audit-Logs (nur mit Permission)
    path('', views.AuditLogListView.as_view(), name='list'),
    path('<int:pk>/', views.AuditLogDetailView.as_view(), name='detail'),

    # Meine eigenen Logs
    path('my/', views.MyAuditLogsView.as_view(), name='my_logs'),

    # Objekt-spezifische Logs
    path('object/<str:app_label>/<str:model_name>/<int:object_id>/',
         views.ObjectAuditLogsView.as_view(), name='object_logs'),

    # Sicherheitsrelevante Logs
    path('security/', views.SecurityLogsView.as_view(), name='security_logs'),
]
