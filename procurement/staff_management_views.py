"""
Procurement Staff Management Views
Personal-Verwaltung fuer Bestellwesen-Modul
Modulverantwortliche koennen hier Besteller zuweisen
"""

from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import Group
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404

from core.models import User
from permissions.constants import Roles
from .views import ProcurementModuleGuardMixin


class ProcurementStaffManagementView(LoginRequiredMixin, ProcurementModuleGuardMixin, TemplateView):
    """
    Personal-Verwaltung fuer Procurement-Modul

    Modulverantwortliche koennen hier Benutzer als Besteller zuweisen.
    Besteller duerfen Bestellungen erstellen und eigene Bestellungen einsehen.
    """
    template_name = 'procurement/staff_management.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_module'] = 'procurement'

        orderers_group, _ = Group.objects.get_or_create(name='procurement_orderers')

        context['orderers'] = User.objects.filter(
            groups=orderers_group,
            is_active=True
        ).order_by('last_name', 'first_name')

        context['orderers_count'] = context['orderers'].count()

        # Alle verfuegbaren Benutzer (nicht zugewiesen)
        assigned_user_ids = list(
            context['orderers'].values_list('id', flat=True)
        )

        context['available_users'] = User.objects.filter(
            is_active=True
        ).exclude(
            id__in=assigned_user_ids
        ).order_by('last_name', 'first_name')

        # Alle Benutzer fuer Dropdown
        context['all_users'] = User.objects.filter(
            is_active=True
        ).order_by('last_name', 'first_name')

        # Pruefe ob User Modulverantwortlicher ist
        context['is_module_admin'] = self.request.user.groups.filter(
            name__in=[Roles.ADMINISTRATOR, Roles.MODUL_PROCUREMENT]
        ).exists() or self.request.user.is_superuser

        return context

    def dispatch(self, request, *args, **kwargs):
        has_permission = (
            request.user.is_superuser or
            request.user.groups.filter(
                name__in=[Roles.ADMINISTRATOR, Roles.MODUL_PROCUREMENT]
            ).exists()
        )
        if not has_permission:
            messages.error(request, 'Sie haben keine Berechtigung fuer die Personal-Verwaltung.')
            return redirect('procurement:dashboard')
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """Handle Zuweisungen und Entfernungen"""
        if not (request.user.groups.filter(
            name__in=[Roles.ADMINISTRATOR, Roles.MODUL_PROCUREMENT]
        ).exists() or request.user.is_superuser):
            messages.error(request, 'Sie haben keine Berechtigung fuer diese Aktion.')
            return redirect('procurement:staff_management')

        action = request.POST.get('action')
        user_id = request.POST.get('user_id')

        if not user_id:
            messages.error(request, 'Kein Benutzer ausgewaehlt.')
            return redirect('procurement:staff_management')

        user = get_object_or_404(User, id=user_id)
        orderers_group = Group.objects.get(name='procurement_orderers')

        if action == 'assign':
            user.groups.add(orderers_group)
            self._assign_orderer_permissions(user)
            messages.success(
                request,
                f'{user.get_full_name()} wurde als Besteller fuer Bestellwesen zugewiesen.'
            )

        elif action == 'remove':
            user.groups.remove(orderers_group)
            self._remove_orderer_permissions(user)
            messages.success(
                request,
                f'{user.get_full_name()} wurde als Besteller entfernt.'
            )

        return redirect('procurement:staff_management')

    def _assign_orderer_permissions(self, user):
        """Weise Besteller-Permissions zu: Bestellungen erstellen + eigene einsehen"""
        from django.contrib.contenttypes.models import ContentType
        from django.contrib.auth.models import Permission

        permissions_to_add = []

        # PurchaseOrder: add + view
        for model_name, actions in [
            ('purchaseorder', ['add', 'view', 'change']),
            ('orderitem', ['add', 'view', 'change', 'delete']),
        ]:
            try:
                content_type = ContentType.objects.get(
                    app_label='procurement',
                    model=model_name
                )
                for action in actions:
                    perm = Permission.objects.get(
                        content_type=content_type,
                        codename=f'{action}_{model_name}'
                    )
                    permissions_to_add.append(perm)
            except (ContentType.DoesNotExist, Permission.DoesNotExist):
                pass

        # View-only fuer restliche Models
        for model_name in ['orderapproval', 'goodsreceipt', 'goodsreceiptitem', 'procurementdepartment']:
            try:
                content_type = ContentType.objects.get(
                    app_label='procurement',
                    model=model_name
                )
                perm = Permission.objects.get(
                    content_type=content_type,
                    codename=f'view_{model_name}'
                )
                permissions_to_add.append(perm)
            except (ContentType.DoesNotExist, Permission.DoesNotExist):
                pass

        # Custom permissions
        for codename in ['create_order_request', 'view_own_orders']:
            try:
                perm = Permission.objects.get(
                    content_type__app_label='procurement',
                    codename=codename
                )
                permissions_to_add.append(perm)
            except Permission.DoesNotExist:
                pass

        user.user_permissions.add(*permissions_to_add)

    def _remove_orderer_permissions(self, user):
        """Entferne alle Besteller-Permissions"""
        from django.contrib.contenttypes.models import ContentType
        from django.contrib.auth.models import Permission

        all_models = [
            'purchaseorder', 'orderitem', 'orderapproval',
            'goodsreceipt', 'goodsreceiptitem', 'procurementdepartment',
        ]

        permissions_to_remove = []
        for model_name in all_models:
            try:
                content_type = ContentType.objects.get(
                    app_label='procurement',
                    model=model_name
                )
                for action in ['add', 'change', 'delete', 'view']:
                    try:
                        perm = Permission.objects.get(
                            content_type=content_type,
                            codename=f'{action}_{model_name}'
                        )
                        permissions_to_remove.append(perm)
                    except Permission.DoesNotExist:
                        pass
            except ContentType.DoesNotExist:
                pass

        for codename in ['create_order_request', 'view_own_orders', 'cancel_order']:
            try:
                perm = Permission.objects.get(
                    content_type__app_label='procurement',
                    codename=codename
                )
                permissions_to_remove.append(perm)
            except Permission.DoesNotExist:
                pass

        user.user_permissions.remove(*permissions_to_remove)
