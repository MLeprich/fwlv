"""
Audit Utility Functions
Helper-Funktionen für Audit-Logging
"""

from .models import AuditLog, AuditAction, AuditSeverity


def get_client_ip(request):
    """
    Ermittelt die Client-IP-Adresse aus dem Request
    Berücksichtigt Proxy-Header
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_user_agent(request):
    """Ermittelt den User-Agent aus dem Request"""
    return request.META.get('HTTP_USER_AGENT', '')


def log_create(request, obj, description=None):
    """
    Loggt das Erstellen eines Objekts

    Usage:
        log_create(request, vehicle, 'Fahrzeug LF 10/6 erstellt')
    """
    if not description:
        description = f"{obj._meta.verbose_name} '{obj}' erstellt"

    return AuditLog.log_action(
        user=request.user,
        action=AuditAction.CREATE,
        description=description,
        obj=obj,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        request_path=request.path,
        http_method=request.method,
    )


def log_update(request, obj, changes=None, description=None):
    """
    Loggt die Änderung eines Objekts

    Usage:
        changes = {
            'status': {'old': 'operational', 'new': 'maintenance'},
            'mileage': {'old': 10000, 'new': 15000}
        }
        log_update(request, vehicle, changes, 'Fahrzeugstatus geändert')
    """
    if not description:
        description = f"{obj._meta.verbose_name} '{obj}' geändert"

    return AuditLog.log_action(
        user=request.user,
        action=AuditAction.UPDATE,
        description=description,
        obj=obj,
        changes=changes,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        request_path=request.path,
        http_method=request.method,
    )


def log_delete(request, obj, description=None):
    """
    Loggt das Löschen eines Objekts

    Usage:
        log_delete(request, vehicle, 'Fahrzeug außer Dienst gestellt')
    """
    if not description:
        description = f"{obj._meta.verbose_name} '{obj}' gelöscht"

    return AuditLog.log_action(
        user=request.user,
        action=AuditAction.DELETE,
        description=description,
        obj=obj,
        severity=AuditSeverity.WARNING,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        request_path=request.path,
        http_method=request.method,
    )


def log_view(request, obj, description=None, severity=AuditSeverity.INFO):
    """
    Loggt das Ansehen eines Objekts (z.B. für BTM-Bereich wichtig)

    Usage:
        log_view(request, medication, 'BTM-Medikament angesehen', severity=AuditSeverity.SECURITY)
    """
    if not description:
        description = f"{obj._meta.verbose_name} '{obj}' angesehen"

    return AuditLog.log_action(
        user=request.user,
        action=AuditAction.VIEW,
        description=description,
        obj=obj,
        severity=severity,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        request_path=request.path,
        http_method=request.method,
    )


def log_login(request, user, success=True):
    """
    Loggt Login-Versuch

    Usage:
        log_login(request, user, success=True)
    """
    if success:
        description = f"Benutzer '{user}' erfolgreich angemeldet"
        severity = AuditSeverity.INFO
    else:
        description = f"Fehlgeschlagener Login-Versuch für '{user}'"
        severity = AuditSeverity.WARNING

    return AuditLog.log_action(
        user=user if success else None,
        action=AuditAction.LOGIN,
        description=description,
        severity=severity,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        request_path=request.path,
        http_method=request.method,
    )


def log_logout(request, user):
    """
    Loggt Logout

    Usage:
        log_logout(request, request.user)
    """
    description = f"Benutzer '{user}' abgemeldet"

    return AuditLog.log_action(
        user=user,
        action=AuditAction.LOGOUT,
        description=description,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        request_path=request.path,
        http_method=request.method,
    )


def log_export(request, model_name, count, description=None):
    """
    Loggt Daten-Export

    Usage:
        log_export(request, 'Vehicle', 25, 'Fahrzeuge nach Excel exportiert')
    """
    if not description:
        description = f"{count} {model_name} exportiert"

    return AuditLog.log_action(
        user=request.user,
        action=AuditAction.EXPORT,
        description=description,
        severity=AuditSeverity.INFO,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        request_path=request.path,
        http_method=request.method,
        extra_data={'model': model_name, 'count': count}
    )


def log_import(request, model_name, count, description=None):
    """
    Loggt Daten-Import

    Usage:
        log_import(request, 'Vehicle', 10, 'Fahrzeuge aus Excel importiert')
    """
    if not description:
        description = f"{count} {model_name} importiert"

    return AuditLog.log_action(
        user=request.user,
        action=AuditAction.IMPORT,
        description=description,
        severity=AuditSeverity.WARNING,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        request_path=request.path,
        http_method=request.method,
        extra_data={'model': model_name, 'count': count}
    )


def log_custom(request, description, severity=AuditSeverity.INFO, obj=None, extra_data=None):
    """
    Loggt benutzerdefinierte Aktion

    Usage:
        log_custom(request, 'Backup erstellt', severity=AuditSeverity.INFO)
    """
    return AuditLog.log_action(
        user=request.user,
        action=AuditAction.CUSTOM,
        description=description,
        obj=obj,
        severity=severity,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        request_path=request.path,
        http_method=request.method,
        extra_data=extra_data,
    )


def compare_model_instances(old_instance, new_instance, fields=None):
    """
    Vergleicht zwei Model-Instanzen und gibt Änderungen zurück

    Usage:
        old_vehicle = Vehicle.objects.get(pk=1)
        # User ändert status
        new_vehicle.status = 'maintenance'
        changes = compare_model_instances(old_vehicle, new_vehicle, fields=['status', 'mileage'])
        # Returns: {'status': {'old': 'operational', 'new': 'maintenance'}}
    """
    changes = {}

    if fields is None:
        # Alle Felder vergleichen (außer Meta-Felder)
        fields = [f.name for f in new_instance._meta.fields if not f.name.startswith('_')]

    for field_name in fields:
        old_value = getattr(old_instance, field_name, None)
        new_value = getattr(new_instance, field_name, None)

        if old_value != new_value:
            changes[field_name] = {
                'old': str(old_value) if old_value is not None else None,
                'new': str(new_value) if new_value is not None else None,
            }

    return changes if changes else None
