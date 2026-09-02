"""
Tickets URLs
URL-Konfiguration für das Ticketsystem
"""

from django.urls import path
from . import views

app_name = 'tickets'

urlpatterns = [
    path('', views.TicketListView.as_view(), name='list'),
    path('create/', views.TicketCreateView.as_view(), name='create'),
    path('switch-role/', views.switch_role, name='switch_role'),
    path('<int:pk>/', views.TicketDetailView.as_view(), name='detail'),
    path('<int:pk>/comment/', views.add_comment, name='add_comment'),
    path('<int:pk>/update/', views.update_ticket, name='update_ticket'),
    path('<int:pk>/close/', views.close_ticket, name='close'),

    # Info-Monitor
    path('infomonitor/', views.InfoMonitorDisplayView.as_view(), name='infomonitor_display'),
    path('infomonitor/edit/', views.InfoMonitorEditView.as_view(), name='infomonitor_edit'),
    path('infomonitor/kiosk/', views.InfoMonitorKioskView.as_view(), name='infomonitor_kiosk'),

    # Kategorie-Verwaltung
    path('categories/', views.CategoryListView.as_view(), name='category_list'),
    path('categories/create/', views.CategoryCreateView.as_view(), name='category_create'),
    path('categories/<int:pk>/edit/', views.CategoryUpdateView.as_view(), name='category_edit'),
    path('categories/<int:pk>/delete/', views.category_delete, name='category_delete'),

    # Bereitschaftspersonen-Verwaltung
    path('infomonitor/bereitschaft/', views.BereitschaftPersonListView.as_view(), name='bereitschaft_person_list'),
    path('infomonitor/bereitschaft/create/', views.BereitschaftPersonCreateView.as_view(), name='bereitschaft_person_create'),
    path('infomonitor/bereitschaft/import/', views.bereitschaft_person_import, name='bereitschaft_person_import'),
    path('infomonitor/bereitschaft/import/template/', views.bereitschaft_person_import_template, name='bereitschaft_person_import_template'),
    path('infomonitor/bereitschaft/<int:pk>/edit/', views.BereitschaftPersonUpdateView.as_view(), name='bereitschaft_person_edit'),
    path('infomonitor/bereitschaft/<int:pk>/delete/', views.bereitschaft_person_delete, name='bereitschaft_person_delete'),

    # Digitale Mappe
    path('infomonitor/mappe/', views.MappeOverviewView.as_view(), name='mappe_overview'),

    path('infomonitor/mappe/links/', views.MappeLinkListView.as_view(), name='mappe_link_list'),
    path('infomonitor/mappe/links/create/', views.MappeLinkCreateView.as_view(), name='mappe_link_create'),
    path('infomonitor/mappe/links/<int:pk>/edit/', views.MappeLinkUpdateView.as_view(), name='mappe_link_edit'),
    path('infomonitor/mappe/links/<int:pk>/delete/', views.mappe_link_delete, name='mappe_link_delete'),

    path('infomonitor/mappe/kontakte/', views.MappeKontaktListView.as_view(), name='mappe_kontakt_list'),
    path('infomonitor/mappe/kontakte/create/', views.MappeKontaktCreateView.as_view(), name='mappe_kontakt_create'),
    path('infomonitor/mappe/kontakte/import/', views.mappe_kontakt_import, name='mappe_kontakt_import'),
    path('infomonitor/mappe/kontakte/import/template/', views.mappe_kontakt_import_template, name='mappe_kontakt_import_template'),
    path('infomonitor/mappe/kontakte/<int:pk>/edit/', views.MappeKontaktUpdateView.as_view(), name='mappe_kontakt_edit'),
    path('infomonitor/mappe/kontakte/<int:pk>/delete/', views.mappe_kontakt_delete, name='mappe_kontakt_delete'),

    path('infomonitor/mappe/anleitungen/', views.MappeAnleitungListView.as_view(), name='mappe_anleitung_list'),
    path('infomonitor/mappe/anleitungen/create/', views.MappeAnleitungCreateView.as_view(), name='mappe_anleitung_create'),
    path('infomonitor/mappe/anleitungen/<int:pk>/edit/', views.MappeAnleitungUpdateView.as_view(), name='mappe_anleitung_edit'),
    path('infomonitor/mappe/anleitungen/<int:pk>/delete/', views.mappe_anleitung_delete, name='mappe_anleitung_delete'),

    # Großveranstaltungen-Dashboards
    path('infomonitor/mappe/dashboards/', views.GVDashboardListView.as_view(), name='mappe_dashboard_list'),
    path('infomonitor/mappe/dashboards/create/', views.GVDashboardCreateView.as_view(), name='mappe_dashboard_create'),
    path('infomonitor/mappe/dashboards/<int:pk>/', views.GVDashboardDetailView.as_view(), name='mappe_dashboard_detail'),
    path('infomonitor/mappe/dashboards/<int:pk>/edit/', views.GVDashboardEditView.as_view(), name='mappe_dashboard_edit'),
    path('infomonitor/mappe/dashboards/<int:pk>/delete/', views.gv_dashboard_delete, name='mappe_dashboard_delete'),
]
