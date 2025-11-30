"""
Permission Mixins für Class-Based Views
"""

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.contrib import messages


class ModulePermissionMixin(LoginRequiredMixin):
    """
    Prüft ob Benutzer Zugriff auf ein Modul hat
    """
    required_module = None  # z.B. 'medical', 'clothing', etc.

    def dispatch(self, request, *args, **kwargs):
        if not self.has_module_permission():
            messages.error(request, 'Sie haben keine Berechtigung für dieses Modul.')
            return redirect('core:dashboard')
        return super().dispatch(request, *args, **kwargs)

    def has_module_permission(self):
        """Prüft Modul-Zugriff"""
        if not self.required_module:
            return True

        user = self.request.user
        if user.is_superuser:
            return True

        # Prüfe ob User mindestens view-Permission für das Modul hat
        return user.has_perm(f'{self.required_module}.view_any')


class ObjectPermissionMixin:
    """
    Prüft Object-Level Permissions mit django-guardian
    """
    def has_object_permission(self, obj):
        """Override in Subclass"""
        return True

    def get_object(self, queryset=None):
        """Überschreibt get_object mit Permission-Check"""
        obj = super().get_object(queryset)
        if not self.has_object_permission(obj):
            raise PermissionDenied("Sie haben keine Berechtigung für dieses Objekt.")
        return obj


class BTMPermissionMixin(LoginRequiredMixin):
    """
    Spezielle Permissions für BTM-Bereich
    Erfordert BTM-Berechtigung
    """
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_btm_authorized():
            messages.error(request, 'Zugriff nur für BTM-Beauftragte.')
            return redirect('core:dashboard')
        return super().dispatch(request, *args, **kwargs)


class BTMSecurityMixin(LoginRequiredMixin):
    """
    Erweiterte Sicherheits-Features für BTM-Bereich:
    - BTM-Berechtigung erforderlich
    - 2FA-Pflicht
    - IP-Logging
    - Audit-Trail
    """
    require_2fa = True
    audit_action_type = None  # Wird von Subclass gesetzt

    def dispatch(self, request, *args, **kwargs):
        # BTM-Berechtigung prüfen
        if not request.user.is_btm_authorized():
            messages.error(request, 'Zugriff nur für BTM-Beauftragte.')
            return redirect('core:dashboard')

        # 2FA-Pflicht prüfen
        if self.require_2fa:
            if not hasattr(request.user, 'totp_device') or not request.user.totp_device.confirmed:
                messages.error(
                    request,
                    'BTM-Bereich erfordert Zwei-Faktor-Authentifizierung.'
                )
                return redirect('core:enable_2fa')

        # IP-Logging für BTM-Zugriff
        self._log_btm_access(request)

        return super().dispatch(request, *args, **kwargs)

    def _log_btm_access(self, request):
        """
        Loggt BTM-Zugriff mit IP-Adresse

        Args:
            request: HTTP Request
        """
        import logging
        logger = logging.getLogger('btm_access')

        logger.info(
            f"BTM Access: {request.user.username} - {request.path}",
            extra={
                'user_id': request.user.id,
                'username': request.user.username,
                'ip_address': request.META.get('REMOTE_ADDR'),
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                'path': request.path,
                'method': request.method,
            }
        )


class RoleRequiredMixin(LoginRequiredMixin):
    """
    Erfordert bestimmte Rolle (Group)
    """
    required_roles = []  # Liste von Rollen-Namen

    def dispatch(self, request, *args, **kwargs):
        if not self.has_required_role():
            messages.error(request, 'Sie haben nicht die erforderliche Rolle für diese Aktion.')
            return redirect('core:dashboard')
        return super().dispatch(request, *args, **kwargs)

    def has_required_role(self):
        """Prüft ob User eine der erforderlichen Rollen hat"""
        if not self.required_roles:
            return True

        user = self.request.user

        # Prüfe ob User authentifiziert ist
        if not user.is_authenticated:
            return False

        if user.is_superuser:
            return True

        return any(user.has_role(role) for role in self.required_roles)


class TimeBasedAccessMixin(LoginRequiredMixin):
    """
    Mixin für zeitbasierte Zugriffskontrolle
    Prüft User.access_start_time und access_end_time
    """
    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_time_based_access():
            messages.error(
                request,
                'Zugriff außerhalb Ihrer autorisierten Zeiten.'
            )
            return redirect('core:dashboard')
        return super().dispatch(request, *args, **kwargs)


class DelegationAwareMixin:
    """
    Mixin das Delegations-Info zum Context hinzufügt
    Zeigt in UI an wenn User mit delegierten Rechten agiert
    """
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        from permissions.backends import check_delegation_active, get_active_delegations

        if check_delegation_active(self.request.user):
            context['is_delegated'] = True
            context['active_delegations'] = get_active_delegations(self.request.user)

            delegators = [
                d.delegator.get_full_name()
                for d in context['active_delegations']
            ]
            context['delegator_names'] = ', '.join(delegators)

        return context


class AuditMixin:
    """
    Mixin für automatisches Audit-Logging bei Objekt-Änderungen
    """
    audit_action_create = 'created'
    audit_action_update = 'updated'
    audit_action_delete = 'deleted'

    def form_valid(self, form):
        """Loggt Objekt-Erstellung/-Änderung"""
        response = super().form_valid(form)

        # Determine action
        if hasattr(self, 'object') and self.object:
            if self.object.pk:
                action = self.audit_action_update
            else:
                action = self.audit_action_create
        else:
            action = self.audit_action_create

        self._log_audit(action)

        return response

    def delete(self, request, *args, **kwargs):
        """Loggt Objekt-Löschung"""
        response = super().delete(request, *args, **kwargs)
        self._log_audit(self.audit_action_delete)
        return response

    def _log_audit(self, action):
        """
        Erstellt Audit-Log Eintrag

        Args:
            action (str): Action-Type
        """
        import logging
        logger = logging.getLogger('audit')

        obj_info = {}
        if hasattr(self, 'object') and self.object:
            obj_info = {
                'object_type': self.object._meta.model_name,
                'object_id': self.object.pk,
                'object_str': str(self.object),
            }

        logger.info(
            f"Audit: {action} by {self.request.user.username}",
            extra={
                'user_id': self.request.user.id,
                'username': self.request.user.username,
                'action': action,
                'ip_address': self.request.META.get('REMOTE_ADDR'),
                **obj_info
            }
        )


class OwnershipMixin:
    """
    Mixin für Objekte mit Besitzer-Logik
    Erlaubt nur Bearbeitung eigener Objekte (außer für Admins)
    """
    ownership_field = 'created_by'  # Feld das auf Owner zeigt

    def get_queryset(self):
        """Filtert QuerySet auf eigene Objekte"""
        qs = super().get_queryset()

        # Admin/Superuser sehen alles
        if self.request.user.is_superuser or self.request.user.has_role('Administrator'):
            return qs

        # Normale User nur eigene
        filter_kwargs = {self.ownership_field: self.request.user}
        return qs.filter(**filter_kwargs)

    def has_object_permission(self, obj):
        """Prüft ob User das Objekt bearbeiten darf"""
        # Admin/Superuser dürfen alles
        if self.request.user.is_superuser or self.request.user.has_role('Administrator'):
            return True

        # Prüfe Besitz
        owner = getattr(obj, self.ownership_field, None)
        return owner == self.request.user


class ApprovalRequiredMixin:
    """
    Mixin für Objekte die Freigabe benötigen
    Zeigt Hinweis wenn Objekt noch nicht freigegeben
    """
    approval_field = 'is_approved'
    approval_required_message = 'Dieses Objekt wartet auf Freigabe.'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if hasattr(self, 'object') and self.object:
            is_approved = getattr(self.object, self.approval_field, True)

            if not is_approved:
                messages.warning(self.request, self.approval_required_message)
                context['requires_approval'] = True
                context['can_approve'] = self._can_approve()

        return context

    def _can_approve(self):
        """Prüft ob User freigeben darf"""
        # Nur für bestimmte Rollen
        return (
            self.request.user.is_superuser or
            self.request.user.has_role('Administrator') or
            self.request.user.has_role('Modulverantwortlicher')
        )
