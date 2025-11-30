"""
Admin-Konfiguration fuer Core App
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, SystemSettings


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Custom User Admin mit erweiterten Feldern
    """

    # Felder fuer die List-Ansicht
    list_display = [
        'username',
        'email',
        'first_name',
        'last_name',
        'personnel_number',
        'department',
        'is_active',
        'is_staff',
        'force_2fa'
    ]

    list_filter = [
        'is_staff',
        'is_superuser',
        'is_active',
        'force_2fa',
        'groups',
        'department'
    ]

    search_fields = [
        'username',
        'first_name',
        'last_name',
        'email',
        'personnel_number',
        'department'
    ]

    # Fieldsets fuer die Detail-Ansicht
    fieldsets = (
        (None, {
            'fields': ('username', 'password')
        }),
        (_('Personal info'), {
            'fields': (
                'first_name',
                'last_name',
                'email',
                'personnel_number',
                'phone',
                'mobile',
                'profile_picture'
            )
        }),
        (_('Organization'), {
            'fields': ('department', 'position')
        }),
        (_('Permissions'), {
            'fields': (
                'is_active',
                'is_staff',
                'is_superuser',
                'groups',
                'user_permissions'
            )
        }),
        (_('Security'), {
            'fields': (
                'force_2fa',
                'access_start_time',
                'access_end_time'
            )
        }),
        (_('Misc'), {
            'fields': ('notes',)
        }),
        (_('Important dates'), {
            'fields': ('last_login', 'date_joined', 'created_at', 'updated_at')
        }),
    )

    # Felder fuer neuen Benutzer
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'username',
                'email',
                'password1',
                'password2',
                'first_name',
                'last_name',
                'personnel_number',
                'department',
                'is_staff',
                'is_active'
            ),
        }),
    )

    readonly_fields = ['last_login', 'date_joined', 'created_at', 'updated_at']

    ordering = ['last_name', 'first_name']

    filter_horizontal = ['groups', 'user_permissions']


@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    """
    System-Einstellungen Admin (Singleton)
    """
    list_display = ['organization_name', 'wiki_enabled', 'updated_at', 'updated_by']
    readonly_fields = ['updated_at', 'updated_by']

    fieldsets = (
        ('Organisation', {
            'fields': ('organization_name', 'organization_logo', 'system_email')
        }),
        ('Module', {
            'fields': (
                'wiki_enabled',
                'procurement_enabled',
                'inventory_check_enabled',
                'info_monitors_enabled',
            ),
            'description': 'Aktivieren oder deaktivieren Sie Module für Ihre Organisation.'
        }),
        ('Features', {
            'fields': (
                'barcode_scanning_enabled',
                'mobile_app_enabled',
                'api_enabled',
            ),
            'classes': ('collapse',)
        }),
        ('Metadaten', {
            'fields': ('updated_at', 'updated_by'),
            'classes': ('collapse',)
        }),
    )

    def has_add_permission(self, request):
        # Nur ein Eintrag erlaubt (Singleton)
        return not SystemSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        # Nie löschen
        return False

    def save_model(self, request, obj, form, change):
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
