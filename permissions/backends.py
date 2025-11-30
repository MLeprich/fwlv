"""
Custom Permission Backends
Erweitert Django's Standard Permission System um:
- Zeitbasierte Permissions
- Delegations-Permissions (Vertretungen)
"""

from django.contrib.auth.backends import ModelBackend
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()


class TimeBasedPermissionBackend(ModelBackend):
    """
    Backend für zeitbasierte Permissions
    Prüft ob User eine Permission hat und ob diese zeitlich gültig ist
    """

    def has_perm(self, user_obj, perm, obj=None):
        """
        Prüft Permission mit zeitlichen Einschränkungen

        Args:
            user_obj (User): User-Objekt
            perm (str): Permission-Code (z.B. 'medical.view_medication')
            obj: Optional - für Object-Level Permissions

        Returns:
            bool: True wenn Permission gewährt
        """
        # User muss aktiv sein
        if not user_obj.is_active:
            return False

        # Erst Standard-Django-Check
        has_standard_perm = super().has_perm(user_obj, perm, obj)

        # Wenn keine Standard-Permission: Ablehnen
        if not has_standard_perm:
            return False

        # Superuser: immer erlauben (keine zeitlichen Beschränkungen)
        if user_obj.is_superuser:
            return True

        # Prüfe zeitbasierte Einschränkungen
        from permissions.models import TimeBasedPermission

        # Hole alle zeitbasierten Permissions für diese Permission
        time_permissions = TimeBasedPermission.objects.filter(
            user=user_obj,
            permission=perm,
            is_active=True
        )

        # Wenn keine zeitbasierten Restrictions existieren: erlauben
        if not time_permissions.exists():
            return True

        # Mindestens eine muss aktuell gültig sein
        for time_perm in time_permissions:
            if time_perm.is_currently_valid():
                return True

        # Keine gültige zeitbasierte Permission gefunden
        return False


class DelegationPermissionBackend(ModelBackend):
    """
    Backend für Vertretungs-Permissions
    User können temporär Permissions von anderen Usern erhalten
    """

    def has_perm(self, user_obj, perm, obj=None):
        """
        Prüft ob User Permission hat (direkt oder durch Vertretung)

        Args:
            user_obj (User): User-Objekt
            perm (str): Permission-Code
            obj: Optional - für Object-Level Permissions

        Returns:
            bool: True wenn Permission gewährt
        """
        # User muss aktiv sein
        if not user_obj.is_active:
            return False

        # Erst Standard-Django-Check
        has_standard_perm = super().has_perm(user_obj, perm, obj)

        # Wenn bereits direkte Permission: erlauben
        if has_standard_perm:
            return True

        # Prüfe aktive Vertretungen
        from permissions.models import Delegation

        active_delegations = Delegation.objects.filter(
            delegate=user_obj,
            is_active=True,
            valid_from__lte=timezone.now(),
            valid_to__gte=timezone.now()
        ).select_related('delegator')

        # Prüfe jede aktive Vertretung
        for delegation in active_delegations:
            # Alle Permissions delegiert?
            if delegation.delegate_all_permissions:
                # User erhält alle Rechte des Vertretenen
                if delegation.delegator.has_perm(perm, obj):
                    return True
            else:
                # Nur explizit delegierte Permissions
                if perm in delegation.delegated_permissions:
                    # Prüfe ob Delegator die Permission hat
                    if delegation.delegator.has_perm(perm, obj):
                        return True

        return False

    def get_all_permissions(self, user_obj, obj=None):
        """
        Gibt alle Permissions zurück (direkt + delegiert)

        Args:
            user_obj (User): User-Objekt
            obj: Optional

        Returns:
            set: Set aller Permission-Codes
        """
        if not user_obj.is_active:
            return set()

        # Standard-Permissions
        perms = super().get_all_permissions(user_obj, obj)

        # Delegierte Permissions hinzufügen
        from permissions.models import Delegation

        active_delegations = Delegation.objects.filter(
            delegate=user_obj,
            is_active=True,
            valid_from__lte=timezone.now(),
            valid_to__gte=timezone.now()
        ).select_related('delegator')

        for delegation in active_delegations:
            if delegation.delegate_all_permissions:
                # Alle Permissions des Delegators
                delegator_perms = super().get_all_permissions(delegation.delegator, obj)
                perms.update(delegator_perms)
            else:
                # Nur explizit delegierte
                perms.update(delegation.delegated_permissions)

        return perms


class CombinedPermissionBackend(ModelBackend):
    """
    Kombiniertes Backend für zeitbasierte UND delegierte Permissions
    Dies ist das empfohlene Backend für Produktion
    """

    def has_perm(self, user_obj, perm, obj=None):
        """
        Prüft Permission mit allen Erweiterungen:
        - Standard Django Permissions
        - Zeitbasierte Einschränkungen
        - Delegationen

        Args:
            user_obj (User): User-Objekt
            perm (str): Permission-Code
            obj: Optional

        Returns:
            bool: True wenn Permission gewährt
        """
        # User muss aktiv sein
        if not user_obj.is_active:
            return False

        # Superuser: immer erlauben
        if user_obj.is_superuser:
            return True

        # Prüfe zeitbasierte Zugriffsbeschränkung auf User-Ebene
        if not user_obj.has_time_based_access():
            return False

        # Standard-Django-Permission-Check
        has_standard_perm = super().has_perm(user_obj, perm, obj)

        # Wenn direkte Permission vorhanden
        if has_standard_perm:
            # Prüfe zeitbasierte Einschränkungen
            if not self._check_time_based_permission(user_obj, perm):
                return False
            return True

        # Wenn keine direkte Permission: prüfe Delegation
        if self._check_delegation_permission(user_obj, perm, obj):
            return True

        return False

    def _check_time_based_permission(self, user_obj, perm):
        """
        Prüft zeitbasierte Einschränkungen für Permission

        Args:
            user_obj (User): User-Objekt
            perm (str): Permission-Code

        Returns:
            bool: True wenn zeitlich erlaubt
        """
        from permissions.models import TimeBasedPermission

        # Hole zeitbasierte Permissions
        time_permissions = TimeBasedPermission.objects.filter(
            user=user_obj,
            permission=perm,
            is_active=True
        )

        # Wenn keine Restrictions: erlauben
        if not time_permissions.exists():
            return True

        # Mindestens eine muss gültig sein
        return any(tp.is_currently_valid() for tp in time_permissions)

    def _check_delegation_permission(self, user_obj, perm, obj=None):
        """
        Prüft ob Permission durch Delegation gewährt wird

        Args:
            user_obj (User): User-Objekt
            perm (str): Permission-Code
            obj: Optional

        Returns:
            bool: True wenn delegiert
        """
        from permissions.models import Delegation

        # Hole aktive Delegationen
        active_delegations = Delegation.objects.filter(
            delegate=user_obj,
            is_active=True,
            valid_from__lte=timezone.now(),
            valid_to__gte=timezone.now()
        ).select_related('delegator')

        for delegation in active_delegations:
            # Prüfe ob Permission delegiert ist
            if delegation.delegate_all_permissions:
                # Alle Permissions des Delegators
                if delegation.delegator.has_perm(perm, obj):
                    return True
            else:
                # Nur spezifische Permissions
                if perm in delegation.delegated_permissions:
                    # Prüfe ob Delegator die Permission hat
                    if delegation.delegator.has_perm(perm, obj):
                        return True

        return False

    def get_all_permissions(self, user_obj, obj=None):
        """
        Gibt alle effektiven Permissions zurück

        Args:
            user_obj (User): User-Objekt
            obj: Optional

        Returns:
            set: Set aller Permission-Codes
        """
        if not user_obj.is_active:
            return set()

        if user_obj.is_superuser:
            # Superuser hat alle Permissions
            from django.contrib.auth.models import Permission
            return set(
                f"{p.content_type.app_label}.{p.codename}"
                for p in Permission.objects.all()
            )

        # Standard-Permissions
        perms = super().get_all_permissions(user_obj, obj)

        # Delegierte Permissions hinzufügen
        from permissions.models import Delegation

        active_delegations = Delegation.objects.filter(
            delegate=user_obj,
            is_active=True,
            valid_from__lte=timezone.now(),
            valid_to__gte=timezone.now()
        ).select_related('delegator')

        for delegation in active_delegations:
            if delegation.delegate_all_permissions:
                delegator_perms = super().get_all_permissions(delegation.delegator, obj)
                perms.update(delegator_perms)
            else:
                perms.update(delegation.delegated_permissions)

        return perms

    def get_user_permissions(self, user_obj, obj=None):
        """
        Gibt nur direkte User-Permissions zurück (keine Group-Permissions)

        Args:
            user_obj (User): User-Objekt
            obj: Optional

        Returns:
            set: Set von Permission-Codes
        """
        return super().get_user_permissions(user_obj, obj)

    def get_group_permissions(self, user_obj, obj=None):
        """
        Gibt Permissions aus Groups zurück

        Args:
            user_obj (User): User-Objekt
            obj: Optional

        Returns:
            set: Set von Permission-Codes
        """
        return super().get_group_permissions(user_obj, obj)


class ObjectLevelPermissionBackend(ModelBackend):
    """
    Backend für Object-Level Permissions
    Ergänzung zu django-guardian
    """

    def has_perm(self, user_obj, perm, obj=None):
        """
        Prüft Object-Level Permission

        Args:
            user_obj (User): User-Objekt
            perm (str): Permission-Code
            obj: Objekt für das die Permission geprüft wird

        Returns:
            bool: True wenn Permission gewährt
        """
        # User muss aktiv sein
        if not user_obj.is_active:
            return False

        # Superuser: immer erlauben
        if user_obj.is_superuser:
            return True

        # Standard-Check
        has_standard_perm = super().has_perm(user_obj, perm, obj)
        if has_standard_perm:
            return True

        # Wenn Objekt gegeben: prüfe Object-Level Permission
        if obj is not None:
            from permissions.models import ObjectPermission

            object_perms = ObjectPermission.objects.filter(
                user=user_obj,
                permission=perm,
                object_type=obj._meta.model_name,
                object_id=obj.pk,
                is_active=True
            )

            for obj_perm in object_perms:
                if obj_perm.is_currently_valid():
                    return True

        return False


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def check_delegation_active(user):
    """
    Prüft ob User aktive Delegationen hat (als Delegate)

    Args:
        user (User): User-Objekt

    Returns:
        bool: True wenn aktive Delegationen vorhanden
    """
    from permissions.models import Delegation

    return Delegation.objects.filter(
        delegate=user,
        is_active=True,
        valid_from__lte=timezone.now(),
        valid_to__gte=timezone.now()
    ).exists()


def get_active_delegations(user):
    """
    Gibt alle aktiven Delegationen für einen User zurück

    Args:
        user (User): User-Objekt

    Returns:
        QuerySet: Aktive Delegation-Objekte
    """
    from permissions.models import Delegation

    return Delegation.objects.filter(
        delegate=user,
        is_active=True,
        valid_from__lte=timezone.now(),
        valid_to__gte=timezone.now()
    ).select_related('delegator')


def get_delegated_permissions(user):
    """
    Gibt alle delegierten Permissions für einen User zurück

    Args:
        user (User): User-Objekt

    Returns:
        set: Set von Permission-Codes
    """
    delegations = get_active_delegations(user)
    perms = set()

    for delegation in delegations:
        if delegation.delegate_all_permissions:
            # Alle Permissions des Delegators
            backend = ModelBackend()
            delegator_perms = backend.get_all_permissions(delegation.delegator)
            perms.update(delegator_perms)
        else:
            # Nur explizite Permissions
            perms.update(delegation.delegated_permissions)

    return perms


def cleanup_expired_delegations():
    """
    Deaktiviert abgelaufene Delegationen (für Cron-Job)

    Returns:
        int: Anzahl deaktivierter Delegationen
    """
    from permissions.models import Delegation

    expired = Delegation.objects.filter(
        is_active=True,
        valid_to__lt=timezone.now()
    )

    count = expired.count()
    expired.update(is_active=False)

    return count


def cleanup_expired_time_permissions():
    """
    Deaktiviert abgelaufene zeitbasierte Permissions (für Cron-Job)

    Returns:
        int: Anzahl deaktivierter Permissions
    """
    from permissions.models import TimeBasedPermission

    expired = TimeBasedPermission.objects.filter(
        is_active=True,
        valid_to_date__lt=timezone.now().date()
    )

    count = expired.count()
    expired.update(is_active=False)

    return count
