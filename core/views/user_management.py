"""
User Management Views für Administratoren
Benutzerverwaltung, Rollen-Zuweisung, Permission-Management
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.db.models import Q, Prefetch
from django import forms
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from core.models import User
from locations.models import Location
from permissions.mixins import RoleRequiredMixin
from permissions.constants import Roles
from permissions.utils import PermissionHelper
from permissions.backends import get_active_delegations


class AdminSetPasswordForm(forms.Form):
    """Formular zum Setzen eines Passworts durch Admin"""
    new_password1 = forms.CharField(
        label='Neues Passwort',
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500',
            'placeholder': 'Neues Passwort eingeben'
        }),
        min_length=8,
    )
    new_password2 = forms.CharField(
        label='Passwort bestätigen',
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500',
            'placeholder': 'Passwort wiederholen'
        }),
        min_length=8,
    )
    force_change = forms.BooleanField(
        label='Benutzer muss Passwort beim nächsten Login ändern',
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'w-4 h-4 text-red-600 border-gray-300 rounded focus:ring-red-500'
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('new_password1')
        password2 = cleaned_data.get('new_password2')

        if password1 and password2:
            if password1 != password2:
                raise forms.ValidationError('Die Passwörter stimmen nicht überein.')

        return cleaned_data

    def clean_new_password1(self):
        password = self.cleaned_data.get('new_password1')
        if password:
            try:
                validate_password(password)
            except ValidationError as e:
                raise forms.ValidationError(list(e.messages))
        return password


class UserListView(RoleRequiredMixin, ListView):
    """Liste aller User für Admin"""
    model = User
    template_name = 'core/user_management/user_list.html'
    required_roles = [Roles.ADMINISTRATOR]
    context_object_name = 'users'
    paginate_by = 50

    def get_queryset(self):
        queryset = User.objects.all().prefetch_related('groups').order_by('last_name', 'first_name')

        # Suche
        search = self.request.GET.get('search', '').strip()
        if search:
            queryset = queryset.filter(
                Q(username__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(email__icontains=search) |
                Q(personnel_number__icontains=search)
            )

        # Filter nach Rolle
        role_filter = self.request.GET.get('role', '')
        if role_filter:
            queryset = queryset.filter(groups__name=role_filter)

        # Filter nach Status
        status_filter = self.request.GET.get('status', '')
        if status_filter == 'active':
            queryset = queryset.filter(is_active=True)
        elif status_filter == 'inactive':
            queryset = queryset.filter(is_active=False)

        return queryset.distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_module'] = 'administration'

        # Alle verfügbaren Rollen für Filter
        from django.contrib.auth.models import Group
        context['available_roles'] = Group.objects.all().order_by('name')

        # Aktuelle Filter
        context['search_query'] = self.request.GET.get('search', '')
        context['role_filter'] = self.request.GET.get('role', '')
        context['status_filter'] = self.request.GET.get('status', '')

        return context


class UserDetailView(RoleRequiredMixin, DetailView):
    """User-Details mit Rollen und Permissions"""
    model = User
    template_name = 'core/user_management/user_detail.html'
    required_roles = [Roles.ADMINISTRATOR]
    context_object_name = 'user_obj'  # Nicht 'user' wegen request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_module'] = 'administration'
        user_obj = self.object

        # Permission-Summary holen
        context['permission_summary'] = PermissionHelper.get_user_permission_summary(user_obj)

        # Alle verfügbaren Rollen
        from django.contrib.auth.models import Group
        context['available_roles'] = Group.objects.all().order_by('name')

        # Aktive Delegationen
        context['active_delegations'] = get_active_delegations(user_obj)

        # Delegationen wo User als Delegate fungiert
        from permissions.models import Delegation
        context['delegations_as_delegate'] = Delegation.objects.filter(
            delegate=user_obj,
            approved_at__isnull=False  # Nur genehmigte Delegationen
        ).select_related('delegator').order_by('-valid_from')[:5]

        # Ticket-Berechtigungen
        context['has_create_ticket'] = user_obj.has_perm('tickets.create_ticket')
        context['has_process_ticket'] = user_obj.has_perm('tickets.process_ticket')

        # Feuerwachen für WBF-Dropdown (Typ 'site' = Standort/Wache)
        context['wbf_locations'] = Location.objects.filter(
            location_type='site'
        ).order_by('name')

        # Wachabteilungen für WBF-Dropdown
        from core.models.user import WatchDivisionChoices
        context['watch_divisions'] = WatchDivisionChoices.choices

        return context


class UserRoleAssignView(RoleRequiredMixin, DetailView):
    """HTMX Endpoint für Rollen-Zuweisung"""
    model = User
    required_roles = [Roles.ADMINISTRATOR]

    def post(self, request, *args, **kwargs):
        user_obj = self.get_object()
        action = request.POST.get('action')  # 'add' oder 'remove'
        role_name = request.POST.get('role')

        # Verhindere, dass User sich selbst Admin-Rolle entfernt
        if action == 'remove' and role_name == Roles.ADMINISTRATOR and user_obj == request.user:
            messages.error(request, 'Sie können sich selbst die Administrator-Rolle nicht entziehen!')
            return redirect('core:user_detail', pk=user_obj.pk)

        if action == 'add':
            success = PermissionHelper.assign_role(user_obj, role_name, assigned_by=request.user)
            if success:
                messages.success(request, f'Rolle "{role_name}" wurde {user_obj.get_full_name()} zugewiesen')
            else:
                messages.error(request, f'Fehler beim Zuweisen der Rolle "{role_name}"')

        elif action == 'remove':
            success = PermissionHelper.remove_role(user_obj, role_name, removed_by=request.user)
            if success:
                messages.success(request, f'Rolle "{role_name}" wurde von {user_obj.get_full_name()} entfernt')
            else:
                messages.error(request, f'Fehler beim Entfernen der Rolle "{role_name}"')

        # Redirect zurück zu User-Detail
        return redirect('core:user_detail', pk=user_obj.pk)


class UserTicketPermissionsView(RoleRequiredMixin, DetailView):
    """Ticket-Berechtigungen verwalten"""
    model = User
    required_roles = [Roles.ADMINISTRATOR]

    def post(self, request, *args, **kwargs):
        from django.contrib.auth.models import Permission

        user_obj = self.get_object()

        # Get ticket permissions
        create_perm = Permission.objects.get(codename='create_ticket', content_type__app_label='tickets')
        process_perm = Permission.objects.get(codename='process_ticket', content_type__app_label='tickets')

        # Handle create_ticket permission
        if request.POST.get('create_ticket'):
            user_obj.user_permissions.add(create_perm)
        else:
            user_obj.user_permissions.remove(create_perm)

        # Handle process_ticket permission
        if request.POST.get('process_ticket'):
            user_obj.user_permissions.add(process_perm)
        else:
            user_obj.user_permissions.remove(process_perm)

        messages.success(request, f'Ticket-Berechtigungen für {user_obj.get_full_name()} wurden aktualisiert.')
        return redirect('core:user_detail', pk=user_obj.pk)


class UserCreateView(RoleRequiredMixin, CreateView):
    """Neuen User anlegen"""
    model = User
    template_name = 'core/user_management/user_form.html'
    required_roles = [Roles.ADMINISTRATOR]
    fields = [
        'username',
        'email',
        'first_name',
        'last_name',
        'personnel_number',
        'position',
        'department',
        'phone',
        'is_active'
    ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_module'] = 'administration'
        context['form_title'] = 'Neuen Benutzer anlegen'
        context['submit_text'] = 'Benutzer erstellen'
        return context

    def form_valid(self, form):
        """Setze initiales Passwort und erstelle User"""
        user = form.save(commit=False)

        # Initiales Passwort (muss beim ersten Login geändert werden)
        import secrets
        initial_password = secrets.token_urlsafe(12)
        user.set_password(initial_password)
        user.password_must_change = True

        user.save()

        # TODO: Email mit initalen Login-Daten senden
        messages.success(
            self.request,
            f'Benutzer {user.get_full_name()} wurde erfolgreich erstellt. '
            f'Initiales Passwort: {initial_password} '
            f'(Bitte notieren und sicher weitergeben!)'
        )

        return redirect('core:user_detail', pk=user.pk)

    def get_success_url(self):
        return reverse_lazy('core:user_detail', kwargs={'pk': self.object.pk})


class UserUpdateView(RoleRequiredMixin, UpdateView):
    """User bearbeiten"""
    model = User
    template_name = 'core/user_management/user_form.html'
    required_roles = [Roles.ADMINISTRATOR]
    fields = [
        'email',
        'first_name',
        'last_name',
        'personnel_number',
        'position',
        'department',
        'phone',
        'is_active'
    ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_module'] = 'administration'
        context['form_title'] = f'Benutzer bearbeiten: {self.object.get_full_name()}'
        context['submit_text'] = 'Änderungen speichern'
        return context

    def form_valid(self, form):
        messages.success(
            self.request,
            f'Benutzer {self.object.get_full_name()} wurde erfolgreich aktualisiert.'
        )
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('core:user_detail', kwargs={'pk': self.object.pk})


class UserSetPasswordView(RoleRequiredMixin, View):
    """Passwort für einen Benutzer setzen (nur für Admins)"""
    required_roles = [Roles.ADMINISTRATOR]

    def get(self, request, pk):
        user_obj = get_object_or_404(User, pk=pk)
        form = AdminSetPasswordForm()
        return render(request, 'core/user_management/user_set_password.html', {
            'form': form,
            'user_obj': user_obj,
            'current_module': 'administration',
        })

    def post(self, request, pk):
        user_obj = get_object_or_404(User, pk=pk)
        form = AdminSetPasswordForm(request.POST)

        if form.is_valid():
            new_password = form.cleaned_data['new_password1']
            force_change = form.cleaned_data['force_change']

            user_obj.set_password(new_password)
            user_obj.password_must_change = force_change
            user_obj.save()

            messages.success(
                request,
                f'Passwort für {user_obj.get_full_name()} wurde erfolgreich geändert.'
            )
            return redirect('core:user_detail', pk=user_obj.pk)

        return render(request, 'core/user_management/user_set_password.html', {
            'form': form,
            'user_obj': user_obj,
            'current_module': 'administration',
        })


class UserWBFSettingsView(RoleRequiredMixin, View):
    """WBF-Einstellungen für einen Benutzer verwalten"""
    required_roles = [Roles.ADMINISTRATOR]

    def post(self, request, pk):
        user_obj = get_object_or_404(User, pk=pk)

        # WBF-Status aus Checkbox
        is_wbf = request.POST.get('is_wbf') == '1'

        if is_wbf:
            # WBF aktiviert - Feuerwache und Wachabteilung speichern
            wbf_location_id = request.POST.get('wbf_location')
            wbf_watch_division = request.POST.get('wbf_watch_division', '')

            user_obj.is_wbf = True
            user_obj.wbf_location_id = wbf_location_id if wbf_location_id else None
            user_obj.wbf_watch_division = wbf_watch_division
        else:
            # WBF deaktiviert - Felder zurücksetzen
            user_obj.is_wbf = False
            user_obj.wbf_location = None
            user_obj.wbf_watch_division = ''

        user_obj.save()

        messages.success(
            request,
            f'WBF-Einstellungen für {user_obj.get_full_name()} wurden aktualisiert.'
        )
        return redirect('core:user_detail', pk=user_obj.pk)
