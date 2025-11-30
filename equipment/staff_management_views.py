"""
Equipment Staff Management Views
Personal-Verwaltung für Ausrüstung & Geräte-Modul
Modulverantwortliche können hier Bearbeiter und Lesende zuweisen
"""

from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import Group
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from django.db.models import Q

from core.models import User
from permissions.mixins import RoleRequiredMixin
from permissions.constants import Roles
from permissions.utils import PermissionHelper


class EquipmentStaffManagementView(LoginRequiredMixin, TemplateView):
    """
    Personal-Verwaltung für Equipment-Modul

    Modulverantwortliche können hier:
    - Benutzer als Bearbeiter (equipment_editors) zuweisen
    - Benutzer als Lesende (equipment_readers) zuweisen
    - Übersicht über alle zugewiesenen Personen erhalten
    """
    template_name = 'equipment/staff_management.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_module'] = 'equipment'

        # Hole die Module-spezifischen Groups (oder erstelle sie)
        editors_group, _ = Group.objects.get_or_create(name='equipment_editors')
        readers_group, _ = Group.objects.get_or_create(name='equipment_readers')

        # Benutzer in den Gruppen
        context['editors'] = User.objects.filter(
            groups=editors_group,
            is_active=True
        ).order_by('last_name', 'first_name')

        context['readers'] = User.objects.filter(
            groups=readers_group,
            is_active=True
        ).exclude(groups=editors_group)  # Editoren nicht als Reader anzeigen

        # Alle verfügbaren Benutzer (nicht zugewiesen)
        assigned_user_ids = list(
            User.objects.filter(
                Q(groups=editors_group) | Q(groups=readers_group)
            ).values_list('id', flat=True)
        )

        context['available_users'] = User.objects.filter(
            is_active=True
        ).exclude(
            id__in=assigned_user_ids
        ).order_by('last_name', 'first_name')

        # Alle Benutzer für Dropdown (inkl. bereits zugewiesener)
        context['all_users'] = User.objects.filter(
            is_active=True
        ).order_by('last_name', 'first_name')

        # Statistiken
        context['editors_count'] = context['editors'].count()
        context['readers_count'] = context['readers'].count()
        context['total_staff'] = context['editors_count'] + context['readers_count']

        # Prüfe ob User Modulverantwortlicher ist
        context['is_module_admin'] = self.request.user.groups.filter(
            name__in=[Roles.ADMINISTRATOR, 'equipment_module_admin']
        ).exists() or self.request.user.is_superuser

        return context

    def post(self, request, *args, **kwargs):
        """
        Handle Zuweisungen und Entfernungen
        """
        # Prüfe Berechtigung
        if not (request.user.groups.filter(
            name__in=[Roles.ADMINISTRATOR, 'equipment_module_admin']
        ).exists() or request.user.is_superuser):
            messages.error(request, 'Sie haben keine Berechtigung für diese Aktion.')
            return redirect('equipment:staff_management')

        action = request.POST.get('action')
        user_id = request.POST.get('user_id')
        role = request.POST.get('role')  # 'editor' oder 'reader'

        if not user_id:
            messages.error(request, 'Kein Benutzer ausgewählt.')
            return redirect('equipment:staff_management')

        user = get_object_or_404(User, id=user_id)

        editors_group = Group.objects.get(name='equipment_editors')
        readers_group = Group.objects.get(name='equipment_readers')

        if action == 'assign':
            if role == 'editor':
                # Füge zu Editors hinzu
                user.groups.add(editors_group)
                # Entferne aus Readers (falls vorhanden)
                user.groups.remove(readers_group)

                # Weise Equipment-Permissions zu
                self._assign_editor_permissions(user)

                messages.success(
                    request,
                    f'{user.get_full_name()} wurde als Bearbeiter für Ausrüstung & Geräte zugewiesen.'
                )

            elif role == 'reader':
                # Füge zu Readers hinzu (nur wenn nicht bereits Editor)
                if not user.groups.filter(name='equipment_editors').exists():
                    user.groups.add(readers_group)

                    # Weise View-Permissions zu
                    self._assign_reader_permissions(user)

                    messages.success(
                        request,
                        f'{user.get_full_name()} wurde als Lesender für Ausrüstung & Geräte zugewiesen.'
                    )
                else:
                    messages.warning(
                        request,
                        f'{user.get_full_name()} ist bereits Bearbeiter und hat erweiterte Rechte.'
                    )

        elif action == 'remove':
            # Entferne aus beiden Gruppen
            user.groups.remove(editors_group, readers_group)

            # Entferne Equipment-Permissions
            self._remove_equipment_permissions(user)

            messages.success(
                request,
                f'{user.get_full_name()} wurde aus dem Ausrüstung & Geräte-Team entfernt.'
            )

        elif action == 'upgrade':
            # Von Reader zu Editor hochstufen
            user.groups.remove(readers_group)
            user.groups.add(editors_group)

            # Weise Editor-Permissions zu
            self._assign_editor_permissions(user)

            messages.success(
                request,
                f'{user.get_full_name()} wurde zu Bearbeiter hochgestuft.'
            )

        elif action == 'downgrade':
            # Von Editor zu Reader herabstufen
            user.groups.remove(editors_group)
            user.groups.add(readers_group)

            # Entferne Editor-Permissions, behalte nur View
            self._remove_equipment_permissions(user)
            self._assign_reader_permissions(user)

            messages.success(
                request,
                f'{user.get_full_name()} wurde zu Lesender herabgestuft.'
            )

        return redirect('equipment:staff_management')

    def _assign_editor_permissions(self, user):
        """Weise alle Equipment CRUD-Permissions zu"""
        from django.contrib.contenttypes.models import ContentType
        from django.contrib.auth.models import Permission

        # Alle Equipment-Models
        equipment_models = [
            'equipmentitem',
            'equipmentitemmaster',
            'equipmentdeviceinstance',
            'equipmentstockmovement',
            'equipmentbatch',
            'inspectionrecord',
            'maintenancerecord',
        ]

        permissions_to_add = []
        for model_name in equipment_models:
            try:
                content_type = ContentType.objects.get(
                    app_label='equipment',
                    model=model_name
                )

                # CRUD Permissions
                for action in ['add', 'change', 'delete', 'view']:
                    perm = Permission.objects.get(
                        content_type=content_type,
                        codename=f'{action}_{model_name}'
                    )
                    permissions_to_add.append(perm)
            except (ContentType.DoesNotExist, Permission.DoesNotExist):
                pass

        user.user_permissions.add(*permissions_to_add)

    def _assign_reader_permissions(self, user):
        """Weise nur View-Permissions zu"""
        from django.contrib.contenttypes.models import ContentType
        from django.contrib.auth.models import Permission

        equipment_models = [
            'equipmentitem',
            'equipmentitemmaster',
            'equipmentdeviceinstance',
            'equipmentstockmovement',
            'equipmentbatch',
            'inspectionrecord',
            'maintenancerecord',
        ]

        permissions_to_add = []
        for model_name in equipment_models:
            try:
                content_type = ContentType.objects.get(
                    app_label='equipment',
                    model=model_name
                )

                # Nur View
                perm = Permission.objects.get(
                    content_type=content_type,
                    codename=f'view_{model_name}'
                )
                permissions_to_add.append(perm)
            except (ContentType.DoesNotExist, Permission.DoesNotExist):
                pass

        user.user_permissions.add(*permissions_to_add)

    def _remove_equipment_permissions(self, user):
        """Entferne alle Equipment-Permissions"""
        from django.contrib.contenttypes.models import ContentType
        from django.contrib.auth.models import Permission

        equipment_models = [
            'equipmentitem',
            'equipmentitemmaster',
            'equipmentdeviceinstance',
            'equipmentstockmovement',
            'equipmentbatch',
            'inspectionrecord',
            'maintenancerecord',
        ]

        permissions_to_remove = []
        for model_name in equipment_models:
            try:
                content_type = ContentType.objects.get(
                    app_label='equipment',
                    model=model_name
                )

                for action in ['add', 'change', 'delete', 'view']:
                    perm = Permission.objects.get(
                        content_type=content_type,
                        codename=f'{action}_{model_name}'
                    )
                    permissions_to_remove.append(perm)
            except (ContentType.DoesNotExist, Permission.DoesNotExist):
                pass

        user.user_permissions.remove(*permissions_to_remove)
