"""
Context Processors für globale Template-Variablen
Stellt Variablen bereit, die in allen Templates verfügbar sind
"""

from django.conf import settings
from core.models import UserSettings, SystemSettings


def notification_count(request):
    """
    Anzahl ungelesener Benachrichtigungen
    """
    if not request.user.is_authenticated:
        return {'notification_count': 0}

    # TODO: Später mit echten Benachrichtigungen aus notifications app
    count = 0

    return {
        'notification_count': count
    }


def app_settings(request):
    """
    Projekt-Einstellungen für Templates
    """
    return {
        'APP_NAME': 'FLVS',
        'APP_VERSION': '1.0.0',
        'DEBUG': settings.DEBUG,
    }


def user_permissions(request):
    """
    Benutzer-Berechtigungen für Template-Zugriff
    """
    if not request.user.is_authenticated:
        return {}

    # Überprüfe ob Benutzer bestimmte Rollen hat
    permissions = {
        'is_admin': request.user.is_superuser or request.user.has_role('Administrator'),
        'is_btm_authorized': request.user.is_btm_authorized() if hasattr(request.user, 'is_btm_authorized') else False,
        'requires_2fa': request.user.requires_2fa() if hasattr(request.user, 'requires_2fa') else False,
    }

    return permissions


def module_badges(request):
    """
    Badge-Counts für Module (Sidebar)
    """
    if not request.user.is_authenticated:
        return {}

    # TODO: Später mit echten Daten
    badges = {
        'critical_medications_count': 0,
        'pending_inspections': 0,
        'pending_approvals': 0,
        'vehicles_in_maintenance': 0,
    }

    return badges


def user_settings_context(request):
    """
    Lädt Benutzer-Einstellungen in den Context
    Stellt Theme, Sidebar-Verhalten und weitere Präferenzen bereit
    """
    context = {
        'user_settings_obj': None,
        'current_theme': 'light',
        'sidebar_behavior': 'expanded',
        'items_per_page': 25,
        'table_density': 'normal',
        'show_hints': True,
        'show_breadcrumbs': True,
        'compact_mode': False,
    }

    if request.user.is_authenticated:
        try:
            user_settings = UserSettings.objects.get(user=request.user)
            context.update({
                'user_settings_obj': user_settings,
                'current_theme': user_settings.theme,
                'sidebar_behavior': user_settings.sidebar_behavior,
                'items_per_page': user_settings.items_per_page,
                'table_density': user_settings.table_density,
                'show_hints': user_settings.show_hints,
                'show_breadcrumbs': user_settings.show_breadcrumbs,
                'compact_mode': user_settings.compact_mode,
            })
        except UserSettings.DoesNotExist:
            # Default-Werte bleiben bestehen
            pass

    return context


def module_settings(request):
    """
    System-weite Modul-Einstellungen
    Macht Module-Status für alle Templates verfügbar
    """
    try:
        sys_settings = SystemSettings.load()

        return {
            'modules': {
                'wiki_enabled': sys_settings.wiki_enabled,
                'procurement_enabled': sys_settings.procurement_enabled,
                'inventory_check_enabled': sys_settings.inventory_check_enabled,
                'info_monitors_enabled': sys_settings.info_monitors_enabled,
                'it_hardware_enabled': sys_settings.it_hardware_enabled,
                'tickets_enabled': sys_settings.tickets_enabled,
                'barcode_scanning_enabled': sys_settings.barcode_scanning_enabled,
                'mobile_app_enabled': sys_settings.mobile_app_enabled,
                'api_enabled': sys_settings.api_enabled,
            },
            'system_settings': sys_settings,
        }
    except Exception:
        # Fallback wenn SystemSettings noch nicht existiert (z.B. während Migration)
        return {
            'modules': {
                'wiki_enabled': False,
                'procurement_enabled': True,
                'inventory_check_enabled': True,
                'info_monitors_enabled': False,
                'it_hardware_enabled': True,
                'tickets_enabled': True,
                'barcode_scanning_enabled': True,
                'mobile_app_enabled': False,
                'api_enabled': False,
            },
            'system_settings': None,
        }
