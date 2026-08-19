"""
Core URLs für FLVS
URL-Konfiguration für Core-App
"""

from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from core.views import user_management

app_name = 'core'

urlpatterns = [
    # Landing Page (öffentlich) & Dashboard (authentifiziert)
    path('', views.LandingPageView.as_view(), name='landing'),
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),

    # User Profile & Settings
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('settings/', views.SettingsView.as_view(), name='settings'),
    path('settings/api-token/generate/', views.generate_api_token, name='generate_api_token'),
    path('settings/api-token/revoke/', views.revoke_api_token, name='revoke_api_token'),
    path('settings/backup/export/', views.backup_export, name='backup_export'),
    path('settings/backup/import/', views.backup_import, name='backup_import'),

    # Search (HTMX)
    path('search/', views.global_search_view, name='global_search'),

    # Barcode/QR-Code Scanner
    path('scan/', views.barcode_scan_view, name='barcode_scan'),

    # Notifications
    path('notifications/', views.notifications_list_view, name='notifications_list'),
    path('notifications/dropdown/', views.notifications_dropdown_view, name='notifications_dropdown'),

    # Alerts & Warnings
    path('alerts/', views.alerts_view, name='alerts'),

    # Inventory Overview
    path('inventory/critical/', views.inventory_critical_view, name='inventory_critical'),

    # Inspections Overview
    path('inspections/upcoming/', views.inspections_upcoming_view, name='inspections_upcoming'),

    # Activity Log
    path('activity/', views.activity_log_view, name='activity_log'),

    # Tasks (HTMX)
    path('tasks/<int:task_id>/toggle/', views.tasks_toggle_view, name='tasks_toggle'),

    # Email
    path('send-test-email/', views.send_test_email_view, name='send_test_email'),

    # Force Password Change
    path('force-password-change/', views.force_password_change_view, name='force_password_change'),

    # Authentication (Django built-in views)
    path('login/', auth_views.LoginView.as_view(
        template_name='core/login.html',
        redirect_authenticated_user=True
    ), name='login'),

    path('logout/', auth_views.LogoutView.as_view(
        next_page='core:landing'
    ), name='logout'),

    path('password-change/', auth_views.PasswordChangeView.as_view(
        template_name='core/password_change.html',
        success_url='/settings/'
    ), name='password_change'),

    path('password-reset/', auth_views.PasswordResetView.as_view(
        template_name='core/password_reset.html',
        email_template_name='core/password_reset_email.html',
        subject_template_name='core/password_reset_subject.txt'
    ), name='password_reset'),

    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='core/password_reset_done.html'
    ), name='password_reset_done'),

    path('password-reset-confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='core/password_reset_confirm.html'
    ), name='password_reset_confirm'),

    path('password-reset-complete/', auth_views.PasswordResetCompleteView.as_view(
        template_name='core/password_reset_complete.html'
    ), name='password_reset_complete'),

    # User Management (Admins only)
    path('verwaltung/users/', user_management.UserListView.as_view(), name='user_list'),
    path('verwaltung/users/create/', user_management.UserCreateView.as_view(), name='user_create'),
    path('verwaltung/users/import/', user_management.user_import_page, name='user_import'),
    path('verwaltung/users/import/template/', user_management.user_import_template, name='user_import_template'),
    path('verwaltung/users/import/validate/', user_management.user_import_validate, name='user_import_validate'),
    path('verwaltung/users/import/execute/', user_management.user_import_execute, name='user_import_execute'),
    path('verwaltung/users/import/passwords/', user_management.user_import_passwords, name='user_import_passwords'),
    path('verwaltung/users/<int:pk>/', user_management.UserDetailView.as_view(), name='user_detail'),
    path('verwaltung/users/<int:pk>/edit/', user_management.UserUpdateView.as_view(), name='user_edit'),
    path('verwaltung/users/<int:pk>/set-password/', user_management.UserSetPasswordView.as_view(), name='user_set_password'),
    path('verwaltung/users/<int:pk>/roles/', user_management.UserRoleAssignView.as_view(), name='assign_roles'),
    path('verwaltung/users/<int:pk>/ticket-permissions/', user_management.UserTicketPermissionsView.as_view(), name='user_ticket_permissions'),
    path('verwaltung/users/<int:pk>/wbf-settings/', user_management.UserWBFSettingsView.as_view(), name='user_wbf_settings'),
    path('verwaltung/users/<int:pk>/ff-settings/', user_management.UserFFSettingsView.as_view(), name='user_ff_settings'),
    path('verwaltung/users/<int:pk>/create-person/', user_management.UserCreatePersonView.as_view(), name='user_create_person'),
    path('verwaltung/users/<int:pk>/staff-position/', user_management.UserStaffPositionView.as_view(), name='user_staff_position'),
]
