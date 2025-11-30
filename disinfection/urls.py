"""
Disinfection URLs
URL-Konfiguration für Desinfektions-Management
"""

from django.urls import path
from . import views

app_name = 'disinfection'

urlpatterns = [
    # Dashboard
    path('', views.disinfection_dashboard, name='dashboard'),

    # Kalender
    path('calendar/', views.disinfection_calendar, name='calendar'),

    # Desinfektionsmittel
    path('items/', views.item_list, name='item_list'),
    path('items/create/', views.item_create, name='item_create'),
    path('items/<int:pk>/edit/', views.item_update, name='item_update'),
    path('items/<int:pk>/delete/', views.item_delete, name='item_delete'),

    # Desinfektionspläne
    path('plans/', views.plan_list, name='plan_list'),
    path('plans/create/', views.plan_create, name='plan_create'),
    path('plans/<int:pk>/edit/', views.plan_update, name='plan_update'),
    path('plans/<int:pk>/delete/', views.plan_delete, name='plan_delete'),

    # Kategorien
    path('categories/', views.category_list, name='category_list'),

    # Protokolle
    path('logs/', views.log_list, name='log_list'),
    path('logs/create/', views.log_create, name='log_create'),
]
