"""
Defect Management Staff Management Views
Personal-Verwaltung für Mängelwesen-Modul
Modulverantwortliche können hier Mängelmelder und Mängelbearbeiter zuweisen
"""

from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from django.db.models import Q

from core.models import User
from permissions.constants import Roles


# Gruppen-Namen
REPORTER_GROUP = Roles.SACHBEARBEITER_DEFECT_MANAGEMENT  # 'Sachbearbeiter Defect Management'
EDITOR_GROUP = 'defect_management_editors'


def _is_module_admin(user):
    """Prüft ob User Modulverantwortlicher Defect Management oder Admin/Superuser ist"""
    if user.is_superuser:
        return True
    return user.groups.filter(
        name__in=[Roles.ADMINISTRATOR, Roles.MODUL_DEFECT_MANAGEMENT]
    ).exists()


class DefectStaffManagementView(LoginRequiredMixin, TemplateView):
    """
    Personal-Verwaltung für Mängelwesen-Modul

    Modulverantwortliche können hier:
    - Benutzer als Mängelmelder (Sachbearbeiter DM - view + add) zuweisen
    - Benutzer als Mängelbearbeiter (Editoren - view + add + change + assign) zuweisen
    - Übersicht über alle zugewiesenen Personen erhalten
    """
    template_name = 'defect_management/staff_management.html'

    def dispatch(self, request, *args, **kwargs):
        if not _is_module_admin(request.user):
            messages.error(request, 'Keine Berechtigung für die Personal-Verwaltung.')
            return redirect('defect_management:dashboard')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_module'] = 'defect_management'

        # Gruppen holen/erstellen
        reporters_group, _ = Group.objects.get_or_create(name=REPORTER_GROUP)
        editors_group, _ = Group.objects.get_or_create(name=EDITOR_GROUP)

        # Benutzer in den Gruppen
        context['editors'] = User.objects.filter(
            groups=editors_group,
            is_active=True
        ).order_by('last_name', 'first_name')

        context['reporters'] = User.objects.filter(
            groups=reporters_group,
            is_active=True
        ).exclude(groups=editors_group).order_by('last_name', 'first_name')

        # Alle verfügbaren Benutzer (nicht zugewiesen)
        assigned_user_ids = list(
            User.objects.filter(
                Q(groups=editors_group) | Q(groups=reporters_group)
            ).values_list('id', flat=True)
        )

        context['available_users'] = User.objects.filter(
            is_active=True
        ).exclude(
            id__in=assigned_user_ids
        ).order_by('last_name', 'first_name')

        # Alle Benutzer für Dropdown
        context['all_users'] = User.objects.filter(
            is_active=True
        ).order_by('last_name', 'first_name')

        # Statistiken
        context['editors_count'] = context['editors'].count()
        context['reporters_count'] = context['reporters'].count()
        context['total_staff'] = context['editors_count'] + context['reporters_count']
        context['is_module_admin'] = True  # already checked in dispatch

        return context

    def post(self, request, *args, **kwargs):
        """Handle Zuweisungen und Entfernungen"""
        if not _is_module_admin(request.user):
            messages.error(request, 'Sie haben keine Berechtigung für diese Aktion.')
            return redirect('defect_management:staff_management')

        action = request.POST.get('action')
        user_id = request.POST.get('user_id')
        role = request.POST.get('role')  # 'reporter' oder 'editor'

        if not user_id:
            messages.error(request, 'Kein Benutzer ausgewählt.')
            return redirect('defect_management:staff_management')

        user = get_object_or_404(User, id=user_id)

        reporters_group = Group.objects.get_or_create(name=REPORTER_GROUP)[0]
        editors_group = Group.objects.get_or_create(name=EDITOR_GROUP)[0]

        if action == 'assign':
            if role == 'editor':
                user.groups.add(editors_group)
                user.groups.remove(reporters_group)
                self._assign_editor_permissions(user)
                messages.success(
                    request,
                    f'{user.get_full_name()} wurde als Mängelbearbeiter zugewiesen.'
                )
            elif role == 'reporter':
                if not user.groups.filter(name=EDITOR_GROUP).exists():
                    user.groups.add(reporters_group)
                    self._assign_reporter_permissions(user)
                    messages.success(
                        request,
                        f'{user.get_full_name()} wurde als Mängelmelder zugewiesen.'
                    )
                else:
                    messages.warning(
                        request,
                        f'{user.get_full_name()} ist bereits Mängelbearbeiter und hat erweiterte Rechte.'
                    )

        elif action == 'remove':
            user.groups.remove(editors_group, reporters_group)
            self._remove_defect_permissions(user)
            messages.success(
                request,
                f'{user.get_full_name()} wurde aus dem Mängelwesen-Team entfernt.'
            )

        elif action == 'upgrade':
            user.groups.remove(reporters_group)
            user.groups.add(editors_group)
            self._assign_editor_permissions(user)
            messages.success(
                request,
                f'{user.get_full_name()} wurde zu Mängelbearbeiter hochgestuft.'
            )

        elif action == 'downgrade':
            user.groups.remove(editors_group)
            user.groups.add(reporters_group)
            self._remove_defect_permissions(user)
            self._assign_reporter_permissions(user)
            messages.success(
                request,
                f'{user.get_full_name()} wurde zu Mängelmelder herabgestuft.'
            )

        return redirect('defect_management:staff_management')

    def _assign_editor_permissions(self, user):
        """Weise Mängelbearbeiter-Permissions zu (view + add + change + assign)"""
        permissions_to_add = []

        defect_models = ['defect', 'defectphoto', 'defectcomment', 'defectcategorymodel']
        for model_name in defect_models:
            try:
                content_type = ContentType.objects.get(
                    app_label='defect_management',
                    model=model_name
                )
                for action in ['add', 'change', 'delete', 'view']:
                    try:
                        perm = Permission.objects.get(
                            content_type=content_type,
                            codename=f'{action}_{model_name}'
                        )
                        permissions_to_add.append(perm)
                    except Permission.DoesNotExist:
                        pass
            except ContentType.DoesNotExist:
                pass

        # Custom permission: assign_defect
        try:
            ct = ContentType.objects.get(app_label='defect_management', model='defect')
            perm = Permission.objects.get(content_type=ct, codename='assign_defect')
            permissions_to_add.append(perm)
        except (ContentType.DoesNotExist, Permission.DoesNotExist):
            pass

        user.user_permissions.add(*permissions_to_add)

    def _assign_reporter_permissions(self, user):
        """Weise Mängelmelder-Permissions zu (view + add)"""
        permissions_to_add = []

        defect_models = ['defect', 'defectphoto', 'defectcomment']
        for model_name in defect_models:
            try:
                content_type = ContentType.objects.get(
                    app_label='defect_management',
                    model=model_name
                )
                for action in ['view', 'add']:
                    try:
                        perm = Permission.objects.get(
                            content_type=content_type,
                            codename=f'{action}_{model_name}'
                        )
                        permissions_to_add.append(perm)
                    except Permission.DoesNotExist:
                        pass
            except ContentType.DoesNotExist:
                pass

        user.user_permissions.add(*permissions_to_add)

    def _remove_defect_permissions(self, user):
        """Entferne alle Defect-Management-Permissions"""
        permissions_to_remove = []

        defect_models = ['defect', 'defectphoto', 'defectcomment', 'defectcategorymodel']
        for model_name in defect_models:
            try:
                content_type = ContentType.objects.get(
                    app_label='defect_management',
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

        # Custom permission
        try:
            ct = ContentType.objects.get(app_label='defect_management', model='defect')
            perm = Permission.objects.get(content_type=ct, codename='assign_defect')
            permissions_to_remove.append(perm)
        except (ContentType.DoesNotExist, Permission.DoesNotExist):
            pass

        user.user_permissions.remove(*permissions_to_remove)
