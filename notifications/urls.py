"""
Notifications URLs
URL-Konfiguration für Notifications App
"""

from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    # Benachrichtigungsliste
    path('', views.NotificationListView.as_view(), name='list'),

    # Einstellungen
    path('preferences/', views.NotificationPreferenceView.as_view(), name='preferences'),

    # AJAX/HTMX Endpoints
    path('<int:pk>/mark-read/', views.mark_as_read, name='mark_read'),
    path('<int:pk>/mark-unread/', views.mark_as_unread, name='mark_unread'),
    path('<int:pk>/archive/', views.archive_notification, name='archive'),
    path('mark-all-read/', views.mark_all_as_read, name='mark_all_read'),

    # API-ähnliche Endpoints
    path('unread-count/', views.unread_count, name='unread_count'),
    path('dropdown/', views.notification_dropdown, name='dropdown'),
]
