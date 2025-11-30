"""
Permission Decorators für Function-Based Views
"""

from functools import wraps
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.contrib import messages
from django.core.exceptions import PermissionDenied


def module_permission_required(module_name):
    """
    Decorator für Modul-Zugriff
    Usage: @module_permission_required('medical')
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)

            if not request.user.has_perm(f'{module_name}.view_any'):
                messages.error(request, f'Keine Berechtigung für Modul: {module_name}')
                return redirect('core:dashboard')

            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def role_required(*roles):
    """
    Decorator für Rollen-Zugriff
    Usage: @role_required('Administrator', 'Modulverantwortlicher')
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)

            has_role = any(request.user.has_role(role) for role in roles)
            if not has_role:
                messages.error(request, 'Sie haben nicht die erforderliche Rolle.')
                return redirect('core:dashboard')

            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def btm_permission_required(view_func):
    """
    Decorator für BTM-Zugriff
    Usage: @btm_permission_required
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.is_btm_authorized():
            messages.error(request, 'Zugriff nur für BTM-Beauftragte.')
            return redirect('core:dashboard')

        return view_func(request, *args, **kwargs)
    return wrapper


def require_2fa(view_func):
    """
    Decorator für 2FA-Pflicht
    Usage: @require_2fa

    Erfordert dass User 2FA aktiviert hat
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        # Prüfe ob User 2FA aktiviert hat
        if not hasattr(request.user, 'totp_device'):
            messages.error(
                request,
                'Diese Funktion erfordert Zwei-Faktor-Authentifizierung. '
                'Bitte aktivieren Sie 2FA in Ihren Einstellungen.'
            )
            return redirect('core:enable_2fa')

        # Prüfe ob 2FA-Device aktiviert ist
        if not request.user.totp_device.confirmed:
            messages.error(request, 'Bitte bestätigen Sie Ihr 2FA-Gerät.')
            return redirect('core:confirm_2fa')

        return view_func(request, *args, **kwargs)
    return wrapper


def require_witness(permission):
    """
    Decorator für Vier-Augen-Prinzip
    Aktion benötigt Bestätigung durch zweiten User mit entsprechender Permission

    Usage:
        @require_witness('medical.approve_btm_action')
        def dispose_btm_medication(request, medication_id):
            # request.witness_user ist verfügbar
            pass

    Args:
        permission (str): Permission die der Zeuge haben muss
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            # Für POST-Requests: Prüfe Witness-Daten
            if request.method == 'POST':
                witness_id = request.POST.get('witness_user_id')
                witness_pin = request.POST.get('witness_pin')

                if not witness_id or not witness_pin:
                    messages.error(
                        request,
                        'Vier-Augen-Prinzip: Bestätigung durch zweiten Benutzer erforderlich.'
                    )
                    # Zeige Form mit Witness-Feldern an
                    request.witness_required = True
                    request.witness_permission = permission
                    return view_func(request, *args, **kwargs)

                # Validiere Witness
                try:
                    from django.contrib.auth import get_user_model
                    User = get_user_model()
                    witness = User.objects.get(id=witness_id, is_active=True)
                except User.DoesNotExist:
                    messages.error(request, 'Ungültiger Zeuge.')
                    raise PermissionDenied("Ungültiger Zeuge")

                # Prüfe ob Witness die erforderliche Permission hat
                if not witness.has_perm(permission):
                    messages.error(
                        request,
                        f'Der Zeuge hat nicht die erforderliche Berechtigung: {permission}'
                    )
                    raise PermissionDenied("Zeuge hat keine Berechtigung")

                # Prüfe PIN (vereinfacht - in Produktion: echter PIN-Check)
                # TODO: Implement proper PIN validation
                if not witness.check_password(witness_pin):
                    messages.error(request, 'Ungültige PIN des Zeugen.')
                    raise PermissionDenied("Ungültige Zeugen-PIN")

                # Witness darf nicht derselbe User sein
                if witness.id == request.user.id:
                    messages.error(request, 'Zeuge muss ein anderer Benutzer sein.')
                    raise PermissionDenied("Zeuge muss anderer Benutzer sein")

                # Füge Witness zum Request hinzu
                request.witness_user = witness
                messages.success(
                    request,
                    f'Bestätigt durch: {witness.get_full_name()}'
                )
            else:
                # GET-Request: Markiere dass Witness benötigt wird
                request.witness_required = True
                request.witness_permission = permission

            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def audit_action(action_type, get_object_info=None):
    """
    Decorator für automatisches Audit-Logging

    Usage:
        @audit_action('btm_dispensed', lambda req, kwargs: {'med_id': kwargs['medication_id']})
        def dispense_medication(request, medication_id):
            pass

    Args:
        action_type (str): Type der Action (z.B. 'btm_dispensed')
        get_object_info (callable): Optional - Funktion die Objekt-Info aus Request extrahiert
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            from permissions.constants import AuditActions

            # Führe View aus
            response = view_func(request, *args, **kwargs)

            # Log Action (nur bei erfolgreichen Requests)
            if response.status_code < 400:
                extra_data = {}
                if get_object_info:
                    extra_data = get_object_info(request, kwargs)

                # TODO: Implement AuditLog model and logging
                # AuditLog.objects.create(
                #     user=request.user,
                #     action=action_type,
                #     ip_address=request.META.get('REMOTE_ADDR'),
                #     user_agent=request.META.get('HTTP_USER_AGENT', ''),
                #     extra_data=extra_data
                # )

                # Für jetzt: nur logging
                import logging
                logger = logging.getLogger(__name__)
                logger.info(
                    f"Audit: {action_type} by {request.user.username}",
                    extra={
                        'user_id': request.user.id,
                        'action': action_type,
                        'ip': request.META.get('REMOTE_ADDR'),
                        **extra_data
                    }
                )

            return response
        return wrapper
    return decorator


def time_based_access_required(view_func):
    """
    Decorator für zeitbasierte Zugriffskontrolle
    Prüft ob User aktuell Zugriff haben darf (basierend auf access_start_time/access_end_time)

    Usage: @time_based_access_required
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.has_time_based_access():
            messages.error(
                request,
                'Zugriff außerhalb Ihrer autorisierten Zeiten.'
            )
            return redirect('core:dashboard')

        return view_func(request, *args, **kwargs)
    return wrapper


def delegation_allowed(view_func):
    """
    Decorator der Delegations-Permissions akzeptiert
    Zeigt in der UI an wenn User mit delegierten Rechten agiert

    Usage: @delegation_allowed
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        from permissions.backends import check_delegation_active, get_active_delegations

        # Prüfe ob User mit Delegation agiert
        if check_delegation_active(request.user):
            delegations = get_active_delegations(request.user)
            delegators = [d.delegator.get_full_name() for d in delegations]

            messages.info(
                request,
                f'Sie agieren als Vertretung für: {", ".join(delegators)}'
            )

            # Füge Info zum Request hinzu
            request.is_delegated = True
            request.active_delegations = delegations

        return view_func(request, *args, **kwargs)
    return wrapper


def permission_required_with_fallback(permission, fallback_permissions=None):
    """
    Decorator mit Fallback-Permissions
    Erlaubt alternative Permissions wenn Haupt-Permission nicht vorhanden

    Usage:
        @permission_required_with_fallback(
            'medical.change_medication',
            fallback_permissions=['medical.change_own_medication']
        )

    Args:
        permission (str): Haupt-Permission
        fallback_permissions (list): Liste alternativer Permissions
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            # Prüfe Haupt-Permission
            if request.user.has_perm(permission):
                request.permission_source = 'direct'
                return view_func(request, *args, **kwargs)

            # Prüfe Fallback-Permissions
            if fallback_permissions:
                for fallback_perm in fallback_permissions:
                    if request.user.has_perm(fallback_perm):
                        request.permission_source = 'fallback'
                        request.used_permission = fallback_perm
                        return view_func(request, *args, **kwargs)

            # Keine Permission gefunden
            messages.error(request, 'Sie haben keine Berechtigung für diese Aktion.')
            return redirect('core:dashboard')

        return wrapper
    return decorator
