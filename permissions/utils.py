"""
Permission Utility Functions und PermissionHelper Class
Zentrale Helper-Funktionen für Permission-Management
"""

from django.contrib.auth.models import Group, Permission
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from guardian.shortcuts import assign_perm, remove_perm
import logging

from permissions.constants import Roles, Modules, ApprovalLimits, get_module_from_role

User = get_user_model()
logger = logging.getLogger(__name__)


class PermissionHelper:
    """
    Helper-Klasse für Permission-Management
    Zentraler Einstiegspunkt für alle Permission-Operationen
    """

    @staticmethod
    def assign_role(user, role_name, assigned_by=None):
        """
        Weist einem User eine Rolle (Group) zu

        Args:
            user (User): User-Objekt
            role_name (str): Name der Rolle (z.B. 'Administrator')
            assigned_by (User): Optional - User der die Zuweisung vornimmt

        Returns:
            bool: True bei Erfolg, False bei Fehler
        """
        try:
            group = Group.objects.get(name=role_name)
            user.groups.add(group)

            logger.info(
                f"Role assigned: {role_name} to {user.username}",
                extra={
                    'user_id': user.id,
                    'role': role_name,
                    'assigned_by': assigned_by.username if assigned_by else None,
                }
            )

            return True
        except Group.DoesNotExist:
            logger.error(f"Role not found: {role_name}")
            return False

    @staticmethod
    def remove_role(user, role_name, removed_by=None):
        """
        Entfernt eine Rolle von einem User

        Args:
            user (User): User-Objekt
            role_name (str): Name der Rolle
            removed_by (User): Optional - User der die Entfernung vornimmt

        Returns:
            bool: True bei Erfolg, False bei Fehler
        """
        try:
            group = Group.objects.get(name=role_name)
            user.groups.remove(group)

            logger.info(
                f"Role removed: {role_name} from {user.username}",
                extra={
                    'user_id': user.id,
                    'role': role_name,
                    'removed_by': removed_by.username if removed_by else None,
                }
            )

            return True
        except Group.DoesNotExist:
            logger.error(f"Role not found: {role_name}")
            return False

    @staticmethod
    def assign_module_responsibility(user, module_name):
        """
        Macht User zum Modulverantwortlichen

        Args:
            user (User): User-Objekt
            module_name (str): Modul-Name (z.B. 'medical')

        Returns:
            bool: True bei Erfolg
        """
        module_display_map = {
            Modules.MEDICAL: 'Medical',
            Modules.CLOTHING: 'Clothing',
            Modules.MAGAZINE: 'Magazine',
            Modules.WORKSHOP: 'Workshop',
            Modules.DISINFECTION: 'Disinfection',
            Modules.HEIGHT_RESCUE: 'Height Rescue',
            Modules.DIVING: 'Diving',
            Modules.EQUIPMENT: 'Equipment',
            Modules.IT_HARDWARE: 'IT Hardware',
        }

        display_name = module_display_map.get(module_name)
        if not display_name:
            logger.error(f"Unknown module: {module_name}")
            return False

        role_name = f'Modulverantwortlicher {display_name}'
        return PermissionHelper.assign_role(user, role_name)

    @staticmethod
    def assign_location_management(user, location):
        """
        Gibt User Verwaltungsrechte für einen Lagerort

        Args:
            user (User): User-Objekt
            location: Location-Objekt

        Returns:
            bool: True bei Erfolg
        """
        try:
            assign_perm('locations.manage_location', user, location)

            # Auch für Kind-Lagerorte (falls hierarchisch)
            if hasattr(location, 'get_descendants'):
                for child in location.get_descendants():
                    assign_perm('locations.manage_location', user, child)

            logger.info(
                f"Location management assigned: {location} to {user.username}",
                extra={
                    'user_id': user.id,
                    'location_id': location.id,
                }
            )

            return True
        except Exception as e:
            logger.error(f"Error assigning location permission: {str(e)}")
            return False

    @staticmethod
    def remove_location_management(user, location):
        """
        Entfernt Verwaltungsrechte für einen Lagerort

        Args:
            user (User): User-Objekt
            location: Location-Objekt

        Returns:
            bool: True bei Erfolg
        """
        try:
            remove_perm('locations.manage_location', user, location)

            if hasattr(location, 'get_descendants'):
                for child in location.get_descendants():
                    remove_perm('locations.manage_location', user, child)

            return True
        except Exception as e:
            logger.error(f"Error removing location permission: {str(e)}")
            return False

    @staticmethod
    def get_user_modules(user):
        """
        Ermittelt Module für die ein User verantwortlich ist

        Args:
            user (User): User-Objekt

        Returns:
            list: Liste von Modul-Namen (app_labels)
        """
        modules = []
        for group in user.groups.all():
            if group.name.startswith('Modulverantwortlicher '):
                module = get_module_from_role(group.name)
                if module:
                    modules.append(module)
        return modules

    @staticmethod
    def check_btm_clearance(user):
        """
        Umfassende BTM-Berechtigung-Prüfung

        Args:
            user (User): User-Objekt

        Returns:
            bool: True wenn BTM-berechtigt
        """
        return (
            user.is_btm_authorized() and
            user.is_active and
            not getattr(user, 'is_locked', False)
        )

    @staticmethod
    def get_approval_limit(user):
        """
        Ermittelt Freigabelimit für Bestellungen in Euro

        Args:
            user (User): User-Objekt

        Returns:
            float: Limit in Euro (inf = unbegrenzt)
        """
        if user.has_perm('procurement.approve_order_high'):
            return float('inf')  # Unbegrenzt
        elif user.has_perm('procurement.approve_order_medium'):
            return ApprovalLimits.MEDIUM
        elif user.has_perm('procurement.approve_order_low'):
            return ApprovalLimits.LOW
        else:
            return 0

    @staticmethod
    def can_approve_order(user, order_amount):
        """
        Prüft ob User eine Bestellung freigeben darf

        Args:
            user (User): User-Objekt
            order_amount (Decimal): Bestellbetrag in Euro

        Returns:
            bool: True wenn User freigeben darf
        """
        user_limit = PermissionHelper.get_approval_limit(user)
        return order_amount <= user_limit

    @staticmethod
    def get_required_approval_permission(order_amount):
        """
        Ermittelt erforderliche Permission basierend auf Betrag

        Args:
            order_amount (Decimal): Bestellbetrag in Euro

        Returns:
            str: Permission-Code
        """
        return ApprovalLimits.get_required_permission(order_amount)

    @staticmethod
    def get_user_permission_summary(user):
        """
        Gibt Zusammenfassung aller User-Permissions zurück

        Args:
            user (User): User-Objekt

        Returns:
            dict: Permission-Summary
        """
        from permissions.backends import CombinedPermissionBackend
        backend = CombinedPermissionBackend()

        return {
            'user': user.username,
            'is_superuser': user.is_superuser,
            'is_active': user.is_active,
            'roles': list(user.groups.values_list('name', flat=True)),
            'modules': PermissionHelper.get_user_modules(user),
            'approval_limit': PermissionHelper.get_approval_limit(user),
            'btm_clearance': PermissionHelper.check_btm_clearance(user),
            'has_time_access': user.has_time_based_access(),
            'all_permissions_count': backend.get_all_permissions(user).__len__(),
        }

    @staticmethod
    def create_delegation(delegator, delegate, valid_from, valid_to,
                         delegate_all=False, permissions=None, reason=''):
        """
        Erstellt eine Vertretungsregelung

        Args:
            delegator (User): User der vertreten wird
            delegate (User): User der vertritt
            valid_from (datetime): Start der Vertretung
            valid_to (datetime): Ende der Vertretung
            delegate_all (bool): Alle Permissions delegieren?
            permissions (list): Liste spezifischer Permission-Codes
            reason (str): Grund der Vertretung

        Returns:
            Delegation: Delegation-Objekt oder None
        """
        from permissions.models import Delegation

        try:
            delegation = Delegation.objects.create(
                delegator=delegator,
                delegate=delegate,
                valid_from=valid_from,
                valid_to=valid_to,
                delegate_all_permissions=delegate_all,
                delegated_permissions=permissions or [],
                reason=reason,
                is_active=True
            )

            logger.info(
                f"Delegation created: {delegator.username} -> {delegate.username}",
                extra={
                    'delegator_id': delegator.id,
                    'delegate_id': delegate.id,
                    'valid_from': valid_from,
                    'valid_to': valid_to,
                }
            )

            return delegation
        except Exception as e:
            logger.error(f"Error creating delegation: {str(e)}")
            return None

    @staticmethod
    def end_delegation(delegation):
        """
        Beendet eine Vertretung vorzeitig

        Args:
            delegation (Delegation): Delegation-Objekt

        Returns:
            bool: True bei Erfolg
        """
        try:
            delegation.end_early()
            logger.info(
                f"Delegation ended: {delegation.delegator.username} -> {delegation.delegate.username}"
            )
            return True
        except Exception as e:
            logger.error(f"Error ending delegation: {str(e)}")
            return False


# ============================================================================
# STANDALONE HELPER FUNCTIONS
# ============================================================================

def get_users_by_role(role_name):
    """
    Gibt alle User mit einer bestimmten Rolle zurück

    Args:
        role_name (str): Name der Rolle

    Returns:
        QuerySet: User-QuerySet
    """
    try:
        group = Group.objects.get(name=role_name)
        return User.objects.filter(groups=group, is_active=True)
    except Group.DoesNotExist:
        return User.objects.none()


def get_btm_authorized_users():
    """
    Gibt alle BTM-berechtigten User zurück

    Returns:
        QuerySet: User-QuerySet
    """
    btm_group = Group.objects.filter(name=Roles.BTM_BEAUFTRAGTER).first()
    admin_group = Group.objects.filter(name=Roles.ADMINISTRATOR).first()

    users = User.objects.filter(is_active=True)

    if btm_group or admin_group:
        from django.db.models import Q
        query = Q()
        if btm_group:
            query |= Q(groups=btm_group)
        if admin_group:
            query |= Q(groups=admin_group)
        users = users.filter(query).distinct()

    return users


def get_module_responsible_users(module_name):
    """
    Gibt alle Modulverantwortlichen für ein Modul zurück

    Args:
        module_name (str): Modul-Name (app_label)

    Returns:
        QuerySet: User-QuerySet
    """
    module_display_map = {
        Modules.MEDICAL: 'Medical',
        Modules.CLOTHING: 'Clothing',
        Modules.MAGAZINE: 'Magazine',
        Modules.WORKSHOP: 'Workshop',
        Modules.DISINFECTION: 'Disinfection',
        Modules.HEIGHT_RESCUE: 'Height Rescue',
        Modules.DIVING: 'Diving',
        Modules.EQUIPMENT: 'Equipment',
        Modules.IT_HARDWARE: 'IT Hardware',
    }

    display_name = module_display_map.get(module_name)
    if not display_name:
        return User.objects.none()

    role_name = f'Modulverantwortlicher {display_name}'
    return get_users_by_role(role_name)


def get_approvers_for_amount(amount):
    """
    Gibt alle User zurück die einen Betrag freigeben dürfen

    Args:
        amount (Decimal): Betrag in Euro

    Returns:
        QuerySet: User-QuerySet
    """
    required_perm = ApprovalLimits.get_required_permission(amount)

    # Hole Permission-Objekt
    app_label, codename = required_perm.split('.')
    try:
        permission = Permission.objects.get(
            content_type__app_label=app_label,
            codename=codename
        )

        # User mit dieser Permission
        users = User.objects.filter(
            is_active=True
        ).filter(
            Q(user_permissions=permission) |
            Q(groups__permissions=permission) |
            Q(is_superuser=True)
        ).distinct()

        return users
    except Permission.DoesNotExist:
        return User.objects.none()


def has_any_inventory_permission(user):
    """
    Prüft ob User irgendeine Lager-Permission hat

    Args:
        user (User): User-Objekt

    Returns:
        bool: True wenn User Zugriff auf mindestens ein Lager-Modul hat
    """
    if user.is_superuser:
        return True

    inventory_modules = Modules.get_inventory_modules()

    for module in inventory_modules:
        if user.has_perm(f'{module}.view_any'):
            return True

    return False


def get_permission_conflicts(user):
    """
    Findet mögliche Permission-Konflikte (z.B. widersprüchliche Rollen)

    Args:
        user (User): User-Objekt

    Returns:
        list: Liste von Konflikten (Warnings)
    """
    conflicts = []

    user_groups = list(user.groups.values_list('name', flat=True))

    # BTM ohne 2FA
    if Roles.BTM_BEAUFTRAGTER in user_groups:
        if not hasattr(user, 'totp_device') or not user.totp_device.confirmed:
            conflicts.append({
                'type': 'security',
                'message': 'BTM-Beauftragter ohne 2FA',
                'severity': 'high'
            })

    # Modulverantwortlicher für zu viele Module
    module_roles = [g for g in user_groups if g.startswith('Modulverantwortlicher ')]
    if len(module_roles) > 3:
        conflicts.append({
            'type': 'workload',
            'message': f'Verantwortlich für {len(module_roles)} Module',
            'severity': 'low'
        })

    # Administrator + andere Rollen (redundant)
    if Roles.ADMINISTRATOR in user_groups and len(user_groups) > 1:
        conflicts.append({
            'type': 'redundancy',
            'message': 'Administrator hat bereits alle Rechte',
            'severity': 'low'
        })

    return conflicts


# Import fix for circular dependency
from django.db.models import Q
