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

    try:
        from notifications.models import Notification
        count = Notification.objects.filter(
            recipient=request.user,
            is_read=False,
            is_archived=False
        ).count()
    except Exception:
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
    from permissions.constants import Roles
    permissions = {
        'is_admin': request.user.is_superuser or request.user.has_role('Administrator'),
        'is_btm_authorized': request.user.is_btm_authorized() if hasattr(request.user, 'is_btm_authorized') else False,
        'requires_2fa': request.user.requires_2fa() if hasattr(request.user, 'requires_2fa') else False,
        'is_ff_leader': (
            request.user.has_role(Roles.FF_EINHEITSFUEHRER) or
            request.user.has_role(Roles.FF_VERTRETER)
        ),
    }

    return permissions


def module_badges(request):
    """
    Badge-Counts für Module (Sidebar)
    """
    if not request.user.is_authenticated:
        return {}

    badges = {
        'critical_medications_count': 0,
        'pending_inspections': 0,
        'pending_approvals': 0,
        'vehicles_in_maintenance': 0,
    }

    # Offene Procurement-Freigaben fuer den aktuellen Benutzer
    try:
        if hasattr(request.user, 'person'):
            from procurement.models import OrderApproval, ApprovalStatus
            badges['pending_approvals'] = OrderApproval.objects.filter(
                approver=request.user.person,
                status=ApprovalStatus.PENDING,
            ).count()
    except Exception:
        pass

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
                'ff_dashboard_enabled': sys_settings.ff_dashboard_enabled,
                'vehicle_handover_enabled': sys_settings.vehicle_handover_enabled,
                'driving_license_enabled': sys_settings.driving_license_enabled,
                'height_rescue_enabled': sys_settings.height_rescue_enabled,
                'diving_enabled': sys_settings.diving_enabled,
                'workshop_enabled': sys_settings.workshop_enabled,
                'phonebook_enabled': sys_settings.phonebook_enabled,
                'defect_management_enabled': sys_settings.defect_management_enabled,
                'civil_protection_enabled': sys_settings.civil_protection_enabled,
                'objektverwaltung_enabled': sys_settings.objektverwaltung_enabled,
                'accident_report_enabled': sys_settings.accident_report_enabled,
                'surveys_enabled': sys_settings.surveys_enabled,
                'iuk_enabled': sys_settings.iuk_enabled,
                'barcode_scanning_enabled': sys_settings.barcode_scanning_enabled,
                'mobile_app_enabled': sys_settings.mobile_app_enabled,
                'api_enabled': sys_settings.api_enabled,
                # Personal - Tab Sichtbarkeit (Detail-Seite)
                'person_tab_duty_hours_visible': sys_settings.person_tab_duty_hours_visible,
                'person_tab_qualifications_visible': sys_settings.person_tab_qualifications_visible,
                'person_tab_inspections_visible': sys_settings.person_tab_inspections_visible,
                'person_tab_clothing_visible': sys_settings.person_tab_clothing_visible,
                # Personal - Formular-Kacheln
                'person_section_work_contact_visible': sys_settings.person_section_work_contact_visible,
                'person_section_private_contact_visible': sys_settings.person_section_private_contact_visible,
                'person_section_emergency_contact_visible': sys_settings.person_section_emergency_contact_visible,
                'person_section_fire_department_visible': sys_settings.person_section_fire_department_visible,
                'person_section_organization_visible': sys_settings.person_section_organization_visible,
                'person_section_driving_license_visible': sys_settings.person_section_driving_license_visible,
                'person_section_notes_visible': sys_settings.person_section_notes_visible,
            },
            'system_settings': sys_settings,
            'privacy_tab_visible': sys_settings.privacy_tab_visible,
            'person_sections': {
                'work_contact_visible': sys_settings.person_section_work_contact_visible,
                'private_contact_visible': sys_settings.person_section_private_contact_visible,
                'emergency_contact_visible': sys_settings.person_section_emergency_contact_visible,
                'fire_department_visible': sys_settings.person_section_fire_department_visible,
                'organization_visible': sys_settings.person_section_organization_visible,
                'user_photo_visible': sys_settings.person_section_user_photo_visible,
                'driving_license_visible': sys_settings.person_section_driving_license_visible,
                'notes_visible': sys_settings.person_section_notes_visible,
            },
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
                'ff_dashboard_enabled': True,
                'vehicle_handover_enabled': True,
                'driving_license_enabled': True,
                'height_rescue_enabled': True,
                'diving_enabled': True,
                'workshop_enabled': True,
                'phonebook_enabled': True,
                'defect_management_enabled': True,
                'civil_protection_enabled': False,
                'objektverwaltung_enabled': True,
                'accident_report_enabled': True,
                'surveys_enabled': False,
                'iuk_enabled': False,
                'barcode_scanning_enabled': True,
                'mobile_app_enabled': False,
                'api_enabled': False,
                # Personal - Tab Sichtbarkeit (Detail-Seite)
                'person_tab_duty_hours_visible': True,
                'person_tab_qualifications_visible': True,
                'person_tab_inspections_visible': True,
                'person_tab_clothing_visible': True,
                # Personal - Formular-Kacheln
                'person_section_work_contact_visible': True,
                'person_section_private_contact_visible': True,
                'person_section_emergency_contact_visible': True,
                'person_section_fire_department_visible': True,
                'person_section_organization_visible': True,
                'person_section_driving_license_visible': True,
                'person_section_notes_visible': True,
            },
            'system_settings': None,
            'privacy_tab_visible': False,
            'person_sections': {
                'work_contact_visible': True,
                'private_contact_visible': True,
                'emergency_contact_visible': True,
                'fire_department_visible': True,
                'organization_visible': True,
                'user_photo_visible': True,
                'driving_license_visible': True,
                'notes_visible': True,
            },
        }
