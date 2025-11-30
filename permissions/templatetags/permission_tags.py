"""
Template Tags für Permission-Checks
"""

from django import template

register = template.Library()


@register.filter
def has_module_permission(user, module_name):
    """
    Prüft ob User Zugriff auf Modul hat
    Usage: {% if request.user|has_module_permission:'medical' %}
    """
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return user.has_perm(f'{module_name}.view_any')


@register.filter
def has_role(user, role_name):
    """
    Prüft ob User eine bestimmte Rolle hat
    Usage: {% if request.user|has_role:'Administrator' %}
    """
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return user.has_role(role_name)


@register.simple_tag
def can_add(user, model_name):
    """
    Prüft ob User ein Objekt erstellen kann
    Usage: {% can_add request.user 'medical.medication' as can_add_med %}
    """
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return user.has_perm(f'{model_name}.add')


@register.simple_tag
def can_change(user, model_name):
    """
    Prüft ob User ein Objekt ändern kann
    """
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return user.has_perm(f'{model_name}.change')


@register.simple_tag
def can_delete(user, model_name):
    """
    Prüft ob User ein Objekt löschen kann
    """
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return user.has_perm(f'{model_name}.delete')


@register.filter
def is_btm_authorized(user):
    """
    Prüft BTM-Berechtigung
    Usage: {% if request.user|is_btm_authorized %}
    """
    if not user.is_authenticated:
        return False
    return user.is_btm_authorized()


@register.filter
def can_edit_object(user, obj):
    """
    Prüft ob User ein Objekt bearbeiten kann
    Usage: {% if request.user|can_edit_object:medication %}
    """
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True

    model_name = obj._meta.model_name
    app_label = obj._meta.app_label

    # Prüfe globale Permission
    if user.has_perm(f'{app_label}.change_{model_name}'):
        return True

    # Prüfe Object-Level Permission (django-guardian)
    try:
        from guardian.shortcuts import get_perms
        perms = get_perms(user, obj)
        return f'change_{model_name}' in perms
    except ImportError:
        pass

    return False


@register.filter
def can_delete_object(user, obj):
    """
    Prüft ob User ein Objekt löschen kann
    Usage: {% if request.user|can_delete_object:medication %}
    """
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True

    model_name = obj._meta.model_name
    app_label = obj._meta.app_label

    # Prüfe globale Permission
    if user.has_perm(f'{app_label}.delete_{model_name}'):
        return True

    # Prüfe Object-Level Permission
    try:
        from guardian.shortcuts import get_perms
        perms = get_perms(user, obj)
        return f'delete_{model_name}' in perms
    except ImportError:
        pass

    return False


@register.simple_tag(takes_context=True)
def has_delegation(context):
    """
    Prüft ob User aktive Delegationen hat
    Usage: {% has_delegation as is_delegated %}
    """
    user = context['request'].user
    if not user.is_authenticated:
        return False

    from permissions.backends import check_delegation_active
    return check_delegation_active(user)


@register.simple_tag(takes_context=True)
def get_delegator_names(context):
    """
    Gibt Namen der Personen zurück die vertreten werden
    Usage: {% get_delegator_names as delegators %}
    """
    user = context['request'].user
    if not user.is_authenticated:
        return ""

    from permissions.backends import get_active_delegations

    delegations = get_active_delegations(user)
    delegators = [d.delegator.get_full_name() for d in delegations]

    return ', '.join(delegators)


@register.filter
def has_time_based_access(user):
    """
    Prüft zeitbasierte Zugriffsberechtigung
    Usage: {% if request.user|has_time_based_access %}
    """
    if not user.is_authenticated:
        return False
    return user.has_time_based_access()


@register.simple_tag
def user_roles(user):
    """
    Gibt alle Rollen eines Users zurück
    Usage: {% user_roles request.user as roles %}
    """
    if not user.is_authenticated:
        return []
    return user.get_roles()


@register.simple_tag
def user_has_any_role(user, roles_string):
    """
    Prüft ob User eine von mehreren Rollen hat
    Usage: {% user_has_any_role request.user "Administrator,BTM-Beauftragter" as has_role %}

    Args:
        user: User-Objekt
        roles_string: Comma-separated String von Rollen
    """
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True

    roles = [r.strip() for r in roles_string.split(',')]
    return any(user.has_role(role) for role in roles)


@register.filter
def is_owner(user, obj):
    """
    Prüft ob User der Ersteller/Besitzer eines Objekts ist
    Usage: {% if request.user|is_owner:medication %}
    """
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True

    # Prüfe created_by Feld
    if hasattr(obj, 'created_by'):
        return obj.created_by == user

    # Prüfe owner Feld (falls vorhanden)
    if hasattr(obj, 'owner'):
        return obj.owner == user

    return False


@register.simple_tag(takes_context=True)
def permission_debug_info(context):
    """
    DEBUG: Gibt Permission-Info für aktuellen User zurück
    Nur für Development!
    Usage: {% permission_debug_info as debug_perms %}
    """
    user = context['request'].user
    if not user.is_authenticated:
        return {}

    from permissions.backends import CombinedPermissionBackend
    backend = CombinedPermissionBackend()

    return {
        'username': user.username,
        'is_superuser': user.is_superuser,
        'groups': list(user.groups.values_list('name', flat=True)),
        'all_permissions': backend.get_all_permissions(user),
        'has_time_access': user.has_time_based_access(),
    }


@register.inclusion_tag('permissions/tags/permission_badge.html')
def show_user_roles(user):
    """
    Zeigt User-Rollen als Badges an
    Usage: {% show_user_roles request.user %}
    """
    if not user.is_authenticated:
        return {'roles': []}

    roles = user.get_roles()
    return {'roles': roles, 'user': user}


@register.inclusion_tag('permissions/tags/delegation_info.html', takes_context=True)
def show_delegation_info(context):
    """
    Zeigt Delegations-Info an (falls vorhanden)
    Usage: {% show_delegation_info %}
    """
    user = context['request'].user
    if not user.is_authenticated:
        return {}

    from permissions.backends import check_delegation_active, get_active_delegations

    if check_delegation_active(user):
        delegations = get_active_delegations(user)
        return {
            'is_delegated': True,
            'delegations': delegations,
            'user': user
        }

    return {'is_delegated': False}


@register.filter
def get_permission_display(perm_code):
    """
    Gibt lesbaren Namen für Permission-Code zurück
    Usage: {{ "medical.view_medication"|get_permission_display }}
    """
    from django.contrib.auth.models import Permission

    try:
        app_label, codename = perm_code.split('.')
        perm = Permission.objects.get(
            content_type__app_label=app_label,
            codename=codename
        )
        return perm.name
    except (Permission.DoesNotExist, ValueError):
        return perm_code


@register.simple_tag
def check_approval_permission(user, obj):
    """
    Prüft ob User ein Objekt freigeben darf
    Usage: {% check_approval_permission request.user order as can_approve %}
    """
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True

    # Admin und Modulverantwortliche dürfen freigeben
    if user.has_role('Administrator'):
        return True

    # Für Bestellungen: prüfe Betrag
    if hasattr(obj, 'total_amount'):
        from permissions.constants import ApprovalLimits
        amount = obj.total_amount

        if amount <= ApprovalLimits.LOW and user.has_perm('procurement.approve_order_low'):
            return True
        if amount <= ApprovalLimits.MEDIUM and user.has_perm('procurement.approve_order_medium'):
            return True
        if user.has_perm('procurement.approve_order_high'):
            return True

    return False
