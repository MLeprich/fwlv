"""
User Management Views für Administratoren
Benutzerverwaltung, Rollen-Zuweisung, Permission-Management
"""

import csv
import io
import re
import unicodedata
from uuid import uuid4

from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.urls import reverse_lazy
from django.db import transaction
from django.db.models import Q, Prefetch
from django.conf import settings
from django import forms
from django.contrib.auth.models import Group
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

        # Info-Monitor & Mappe-Berechtigungen
        context['has_view_infomonitor'] = user_obj.has_perm('tickets.view_infomonitor')
        context['has_edit_infomonitor'] = user_obj.has_perm('tickets.edit_infomonitor')
        context['has_edit_mappe'] = user_obj.has_perm('tickets.edit_mappe')

        # Feuerwachen für WBF-Dropdown (Typ 'site' = Standort/Wache)
        context['wbf_locations'] = Location.objects.filter(
            location_type='site'
        ).order_by('name')

        # Wachabteilungen für WBF-Dropdown
        from core.models.user import WatchDivisionChoices, StaffPosition
        context['watch_divisions'] = WatchDivisionChoices.choices

        # Dienststellung-Optionen
        context['staff_positions'] = StaffPosition.choices

        # FF-Einheiten für FF-Einstellungen
        from organization.models import VolunteerUnit
        context['ff_units'] = VolunteerUnit.objects.filter(is_active=True).order_by('sort_order', 'name')

        # Aktuelle FF-Zuweisung ermitteln
        context['ff_current_role'] = ''
        context['ff_current_unit'] = None
        context['ff_has_person'] = False
        try:
            person = user_obj.person
        except Exception:
            person = None
        if person:
            context['ff_has_person'] = True
            led_unit = VolunteerUnit.objects.filter(leader=person).first()
            deputy_unit = VolunteerUnit.objects.filter(deputy_leader=person).first()
            if led_unit:
                context['ff_current_role'] = 'leader'
                context['ff_current_unit'] = led_unit
            elif deputy_unit:
                context['ff_current_role'] = 'deputy'
                context['ff_current_unit'] = deputy_unit

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

        # Get all Leitstelle permissions
        create_perm = Permission.objects.get(codename='create_ticket', content_type__app_label='tickets')
        process_perm = Permission.objects.get(codename='process_ticket', content_type__app_label='tickets')
        view_infomonitor_perm = Permission.objects.get(codename='view_infomonitor', content_type__app_label='tickets')
        edit_infomonitor_perm = Permission.objects.get(codename='edit_infomonitor', content_type__app_label='tickets')
        edit_mappe_perm = Permission.objects.get(codename='edit_mappe', content_type__app_label='tickets')

        # Handle each permission
        for perm, field_name in [
            (create_perm, 'create_ticket'),
            (process_perm, 'process_ticket'),
            (view_infomonitor_perm, 'view_infomonitor'),
            (edit_infomonitor_perm, 'edit_infomonitor'),
            (edit_mappe_perm, 'edit_mappe'),
        ]:
            if request.POST.get(field_name):
                user_obj.user_permissions.add(perm)
            else:
                user_obj.user_permissions.remove(perm)

        messages.success(request, f'Leitstelle-Berechtigungen für {user_obj.get_full_name()} wurden aktualisiert.')
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


class UserStaffPositionView(RoleRequiredMixin, View):
    """Dienststellung für einen Benutzer verwalten"""
    required_roles = [Roles.ADMINISTRATOR]

    def post(self, request, pk):
        user_obj = get_object_or_404(User, pk=pk)

        staff_position = request.POST.get('staff_position', '')
        user_obj.staff_position = staff_position
        user_obj.save()

        # Freigabe-Gruppen synchronisieren
        user_obj.sync_approval_groups()

        messages.success(
            request,
            f'Dienststellung für {user_obj.get_full_name()} wurde aktualisiert.'
        )
        return redirect('core:user_detail', pk=user_obj.pk)


class UserCreatePersonView(RoleRequiredMixin, View):
    """Automatisch Personendatensatz aus Benutzerdaten erstellen"""
    required_roles = [Roles.ADMINISTRATOR]

    def post(self, request, pk):
        from personnel.models import Person

        user_obj = get_object_or_404(User, pk=pk)

        # Prüfen ob bereits eine Person verknüpft ist
        try:
            if user_obj.person:
                messages.info(request, f'{user_obj.get_full_name()} hat bereits einen Personendatensatz.')
                return redirect('core:user_detail', pk=user_obj.pk)
        except Exception:
            pass

        # Personalnummer generieren falls nötig
        personnel_number = user_obj.personnel_number
        if not personnel_number:
            # Auto-generieren: FF-<user_id>
            personnel_number = f'FF-{user_obj.pk:04d}'
            # Sicherstellen, dass eindeutig
            counter = 1
            base_number = personnel_number
            while Person.objects.filter(personnel_number=personnel_number).exists():
                personnel_number = f'{base_number}-{counter}'
                counter += 1

        person = Person(
            first_name=user_obj.first_name or user_obj.username,
            last_name=user_obj.last_name or '',
            personnel_number=personnel_number,
            email=user_obj.email or '',
            phone=user_obj.phone or '',
            user=user_obj,
            is_active=True,
            created_by=request.user,
            updated_by=request.user,
        )
        person.save()

        messages.success(
            request,
            f'Personendatensatz für {user_obj.get_full_name()} wurde erstellt '
            f'(Personalnummer: {personnel_number}).'
        )
        return redirect('core:user_detail', pk=user_obj.pk)


class UserFFSettingsView(RoleRequiredMixin, View):
    """FF-Einheitsführer/Vertreter Einstellungen für einen Benutzer verwalten"""
    required_roles = [Roles.ADMINISTRATOR]

    def post(self, request, pk):
        from organization.models import VolunteerUnit

        user_obj = get_object_or_404(User, pk=pk)

        # Person muss verknüpft sein
        try:
            person = user_obj.person
        except Exception:
            person = None

        if not person:
            messages.error(
                request,
                f'{user_obj.get_full_name()} hat keinen verknüpften Personendatensatz. '
                f'Bitte zuerst einen Personendatensatz erstellen.'
            )
            return redirect('core:user_detail', pk=user_obj.pk)

        ff_role = request.POST.get('ff_role', '')  # 'leader', 'deputy', or ''
        ff_unit_id = request.POST.get('ff_unit')

        # Alte Zuweisungen entfernen
        VolunteerUnit.objects.filter(leader=person).update(leader=None)
        VolunteerUnit.objects.filter(deputy_leader=person).update(deputy_leader=None)

        # Alte FF-Gruppen entfernen
        PermissionHelper.remove_role(user_obj, Roles.FF_EINHEITSFUEHRER, removed_by=request.user)
        PermissionHelper.remove_role(user_obj, Roles.FF_VERTRETER, removed_by=request.user)

        if ff_role and ff_unit_id:
            try:
                unit = VolunteerUnit.objects.get(pk=ff_unit_id, is_active=True)
            except VolunteerUnit.DoesNotExist:
                messages.error(request, 'Ungültige FF-Einheit ausgewählt.')
                return redirect('core:user_detail', pk=user_obj.pk)

            if ff_role == 'leader':
                unit.leader = person
                unit.save(update_fields=['leader'])
                PermissionHelper.assign_role(user_obj, Roles.FF_EINHEITSFUEHRER, assigned_by=request.user)
                messages.success(
                    request,
                    f'{user_obj.get_full_name()} ist jetzt Einheitsführer von {unit.name}.'
                )
            elif ff_role == 'deputy':
                unit.deputy_leader = person
                unit.save(update_fields=['deputy_leader'])
                PermissionHelper.assign_role(user_obj, Roles.FF_VERTRETER, assigned_by=request.user)
                messages.success(
                    request,
                    f'{user_obj.get_full_name()} ist jetzt Stellv. Einheitsführer von {unit.name}.'
                )
        else:
            messages.success(
                request,
                f'FF-Zuweisung für {user_obj.get_full_name()} wurde entfernt.'
            )

        return redirect('core:user_detail', pk=user_obj.pk)


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


# =============================================================================
# CSV-Benutzer-Import
# =============================================================================

def _import_user_is_admin(user):
    """Nur Administratoren/Superuser dürfen importieren."""
    return user.is_authenticated and (user.is_superuser or user.has_role(Roles.ADMINISTRATOR))


def _generate_import_password(length=12):
    """Zufallspasswort für importierte Benutzer (ohne verwechselbare Zeichen)."""
    import secrets
    alphabet = 'ABCDEFGHJKLMNPQRSTUVWXYZ' 'abcdefghijkmnopqrstuvwxyz' '23456789'
    specials = '!$%&*+-?'
    rng = secrets.SystemRandom()
    while True:
        chars = [rng.choice(alphabet) for _ in range(length - 1)] + [rng.choice(specials)]
        rng.shuffle(chars)
        pw = ''.join(chars)
        # Mindestens ein Groß-, ein Kleinbuchstabe und eine Ziffer
        if any(c.isupper() for c in pw) and any(c.islower() for c in pw) and any(c.isdigit() for c in pw):
            return pw


def _parse_bool(value, default=True):
    v = (value or '').strip().lower()
    if not v:
        return default
    return v in ('ja', 'yes', 'y', '1', 'true', 'wahr', 'x', 'aktiv', 'active')


def _normalize_username_part(text):
    text = (text or '').strip().lower()
    for a, b in (('ä', 'ae'), ('ö', 'oe'), ('ü', 'ue'), ('ß', 'ss')):
        text = text.replace(a, b)
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')
    return re.sub(r'[^a-z0-9]', '', text)


def _generate_username(first_name, last_name, taken):
    base = (_normalize_username_part(first_name) + '.' + _normalize_username_part(last_name)).strip('.')
    if not base:
        base = 'benutzer'
    username = base
    counter = 1
    while username in taken or User.objects.filter(username=username).exists():
        counter += 1
        username = f'{base}{counter}'
    return username


def _map_user_columns(header):
    """Fuzzy-Mapping der CSV-Spalten (deutsch) auf Feldnamen."""
    col = {}
    for idx, name in enumerate(header):
        n = (name or '').strip().lower()
        if n in ('benutzername', 'username', 'login', 'benutzer'):
            col['username'] = idx
        elif n in ('vorname', 'first name', 'firstname'):
            col['first_name'] = idx
        elif n in ('nachname', 'last name', 'lastname', 'name'):
            col['last_name'] = idx
        elif 'mail' in n:
            col['email'] = idx
        elif 'personalnummer' in n or n == 'pn':
            col['personnel_number'] = idx
        elif 'ticket' in n and ('erstell' in n or 'anleg' in n):
            col['ticket_create'] = idx
        elif 'ticket' in n and ('bearbeit' in n or 'process' in n):
            col['ticket_process'] = idx
        elif 'rolle' in n:
            col['roles'] = idx
        elif n in ('aktiv', 'active', 'status'):
            col['active'] = idx
    return col


def user_import_page(request):
    """Startseite des Benutzer-Imports (Upload-Formular)."""
    if not _import_user_is_admin(request.user):
        messages.error(request, 'Keine Berechtigung.')
        return redirect('core:dashboard')
    # Passwörter eines früheren Imports nicht länger als nötig in der Session halten
    for key in [k for k in request.session.keys() if k.startswith('userimportpw_')]:
        del request.session[key]
        request.session.modified = True

    context = {
        'current_module': 'administration',
        'available_roles': sorted(Group.objects.values_list('name', flat=True)),
    }
    return render(request, 'core/user_management/user_import.html', context)


def user_import_template(request):
    """CSV-Vorlage zum Download."""
    if not _import_user_is_admin(request.user):
        return redirect('core:dashboard')
    roles = sorted(Group.objects.values_list('name', flat=True))
    lines = [
        '# FLVS – Benutzer-Import (CSV, Trennzeichen Semikolon)',
        '# Pflicht: Vorname und Nachname (Benutzername wird sonst automatisch erzeugt).',
        '# Benutzer-Rollen: kommagetrennt, exakt wie hier gelistet:',
        '# ' + ', '.join(roles),
        '# Aktiv: Ja/Nein (Standard: Ja). Zeilen mit # werden ignoriert.',
        '# Ticket erstellen / Ticket bearbeiten: Ja/Nein – Einzelberechtigungen (keine Rolle).',
        'Benutzername;Vorname;Nachname;E-Mail;Personalnummer;Benutzer-Rollen;Aktiv;Ticket erstellen;Ticket bearbeiten',
        ';Max;Mustermann;max.mustermann@example.com;12345;Standard-Nutzer;Ja;Ja;Nein',
    ]
    body = '﻿' + '\r\n'.join(lines) + '\r\n'
    resp = HttpResponse(body, content_type='text/csv; charset=utf-8')
    resp['Content-Disposition'] = 'attachment; filename="benutzer-import-vorlage.csv"'
    return resp


def user_import_validate(request):
    """CSV parsen, validieren, Vorschau anzeigen (gültige Zeilen in Session)."""
    if not _import_user_is_admin(request.user):
        messages.error(request, 'Keine Berechtigung.')
        return redirect('core:dashboard')
    if request.method != 'POST':
        return redirect('core:user_import')

    upload = request.FILES.get('import_file')

    if not upload:
        messages.error(request, 'Bitte eine CSV-Datei auswählen.')
        return redirect('core:user_import')
    if not upload.name.lower().endswith('.csv'):
        messages.error(request, 'Bitte eine CSV-Datei (.csv) hochladen.')
        return redirect('core:user_import')

    raw = upload.read()
    try:
        content = raw.decode('utf-8-sig')
    except UnicodeDecodeError:
        content = raw.decode('latin-1')

    reader = csv.reader(io.StringIO(content), delimiter=';')
    rows = [r for r in reader if r and any(c.strip() for c in r) and not r[0].strip().startswith('#')]
    if len(rows) < 2:
        messages.error(request, 'Die Datei enthält keine Datenzeilen.')
        return redirect('core:user_import')

    header = rows[0]
    col = _map_user_columns(header)
    valid_groups = set(Group.objects.values_list('name', flat=True))

    preview = []
    taken = set()
    existing_pn = set()
    for line in rows[1:]:
        def get(key):
            return line[col[key]].strip() if key in col and col[key] < len(line) else ''

        first = get('first_name')
        last = get('last_name')
        username = get('username')
        email = get('email')
        pn = get('personnel_number')
        roles_raw = get('roles')
        row_errors = []

        if not username and not (first or last):
            row_errors.append('Weder Benutzername noch Vor-/Nachname angegeben')

        if username:
            if username in taken or User.objects.filter(username=username).exists():
                row_errors.append(f'Benutzername „{username}" existiert bereits')
        else:
            username = _generate_username(first, last, taken)

        role_names = [r.strip() for r in roles_raw.split(',') if r.strip()] if roles_raw else []
        unknown = [r for r in role_names if r not in valid_groups]
        if unknown:
            row_errors.append('Unbekannte Rolle(n): ' + ', '.join(unknown))

        if pn:
            if pn in existing_pn or User.objects.filter(personnel_number=pn).exists():
                row_errors.append(f'Personalnummer „{pn}" bereits vergeben')

        active = _parse_bool(get('active'), default=True)
        ticket_create = _parse_bool(get('ticket_create'), default=False)
        ticket_process = _parse_bool(get('ticket_process'), default=False)

        if not row_errors:
            taken.add(username)
            if pn:
                existing_pn.add(pn)

        preview.append({
            'username': username,
            'first_name': first,
            'last_name': last,
            'email': email,
            'personnel_number': pn,
            'roles': role_names,
            'active': active,
            'ticket_create': ticket_create,
            'ticket_process': ticket_process,
            'errors': row_errors,
        })

    valid_rows = [p for p in preview if not p['errors']]
    session_key = 'userimport_' + uuid4().hex
    request.session[session_key] = {'rows': valid_rows}
    request.session.modified = True

    context = {
        'current_module': 'administration',
        'preview': preview,
        'valid_count': len(valid_rows),
        'error_count': len(preview) - len(valid_rows),
        'session_key': session_key,
        'available_roles': sorted(valid_groups),
    }
    return render(request, 'core/user_management/user_import.html', context)


def user_import_execute(request):
    """Angelegte, validierte Zeilen als Benutzer anlegen."""
    if not _import_user_is_admin(request.user):
        messages.error(request, 'Keine Berechtigung.')
        return redirect('core:dashboard')
    if request.method != 'POST':
        return redirect('core:user_import')

    session_key = request.POST.get('session_key', '')
    payload = request.session.get(session_key)
    if not payload:
        messages.error(request, 'Import-Sitzung abgelaufen. Bitte die Datei erneut hochladen.')
        return redirect('core:user_import')

    rows = payload.get('rows', [])
    created = 0
    failed = 0
    credentials = []
    for r in rows:
        password = _generate_import_password()
        try:
            with transaction.atomic():
                user = User.objects.create_user(
                    username=r['username'],
                    email=r.get('email') or '',
                    password=password,
                    first_name=r.get('first_name') or '',
                    last_name=r.get('last_name') or '',
                    password_must_change=True,
                    is_active=r.get('active', True),
                    personnel_number=(r.get('personnel_number') or None),
                )
                role_names = r.get('roles') or []
                if role_names:
                    groups = Group.objects.filter(name__in=role_names)
                    user.groups.add(*groups)
                perm_codes = []
                if r.get('ticket_create'):
                    perm_codes.append('create_ticket')
                if r.get('ticket_process'):
                    perm_codes.append('process_ticket')
                if perm_codes:
                    from django.contrib.auth.models import Permission
                    perms = Permission.objects.filter(codename__in=perm_codes, content_type__app_label='tickets')
                    user.user_permissions.add(*perms)
            created += 1
            credentials.append({
                'username': user.username,
                'name': f"{r.get('first_name') or ''} {r.get('last_name') or ''}".strip(),
                'email': r.get('email') or '',
                'password': password,
            })
        except Exception:
            failed += 1

    try:
        del request.session[session_key]
        request.session.modified = True
    except KeyError:
        pass

    if not created:
        messages.error(request, 'Es wurden keine Benutzer angelegt.')
        return redirect('core:user_import')

    msg = f'{created} Benutzer wurden angelegt (Zufallspasswort, Änderung beim ersten Login erforderlich).'
    if failed:
        msg += f' {failed} Zeile(n) fehlgeschlagen.'
    messages.success(request, msg)

    pw_key = 'userimportpw_' + uuid4().hex
    request.session[pw_key] = credentials
    request.session.modified = True

    context = {
        'current_module': 'administration',
        'credentials': credentials,
        'created_count': created,
        'failed_count': failed,
        'password_key': pw_key,
    }
    return render(request, 'core/user_management/user_import.html', context)


def user_import_passwords(request):
    """Die generierten Zugangsdaten des letzten Imports als CSV herunterladen."""
    if not _import_user_is_admin(request.user):
        messages.error(request, 'Keine Berechtigung.')
        return redirect('core:dashboard')

    pw_key = request.GET.get('key', '')
    credentials = request.session.get(pw_key) if pw_key.startswith('userimportpw_') else None
    if not credentials:
        messages.error(request, 'Die Zugangsdaten sind nicht mehr verfügbar. Passwörter bitte einzeln neu setzen.')
        return redirect('core:user_list')

    buf = io.StringIO()
    writer = csv.writer(buf, delimiter=';', lineterminator='\r\n')
    writer.writerow(['Benutzername', 'Name', 'E-Mail', 'Passwort'])
    for c in credentials:
        writer.writerow([c['username'], c['name'], c['email'], c['password']])

    resp = HttpResponse('﻿' + buf.getvalue(), content_type='text/csv; charset=utf-8')
    resp['Content-Disposition'] = 'attachment; filename="benutzer-zugangsdaten.csv"'
    resp['Cache-Control'] = 'no-store'
    return resp
    return redirect('core:user_list')
