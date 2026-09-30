"""Einsatzvorbereitung – Rollen und Zugriffsstufen (Muster: termine.roles)."""
from django.contrib.auth.models import Group, Permission

from permissions.constants import Roles
from permissions.utils import PermissionHelper

APP = 'einsatzvorbereitung'

EINSATZ_ROLES = {
    Roles.EINSATZ_LESER: ['einsatz_view'],
    Roles.SACHBEARBEITER_EINSATZ: ['einsatz_view', 'einsatz_edit'],
    Roles.MODUL_EINSATZ: ['einsatz_view', 'einsatz_edit', 'einsatz_manage'],
}
LEVEL_GROUPS = tuple(EINSATZ_ROLES)

EINSATZ_LEVELS = [
    ('none', 'Kein Zugriff', None, 'Gefahrenstellen und Karte sind nicht sichtbar'),
    ('view', 'Nur ansehen', Roles.EINSATZ_LESER, 'Gefahrenstellen, Karte und betroffene Objekte ansehen, Rückmeldungen schreiben'),
    ('edit', 'Bearbeiten', Roles.SACHBEARBEITER_EINSATZ, 'Zusätzlich Gefahrenstellen anlegen und ändern'),
    ('manage', 'Verwalten', Roles.MODUL_EINSATZ, 'Zusätzlich löschen, Karteneinstellungen und Kacheln verwalten'),
]
_LEVEL_BY_KEY = {key: group for key, _label, group, _desc in EINSATZ_LEVELS}
_PERM_BY_LEVEL = {'view': 'einsatz_view', 'edit': 'einsatz_edit', 'manage': 'einsatz_manage'}


def role_permissions(codenames, all_model_perms=False):
    perms = list(Permission.objects.filter(content_type__app_label=APP, codename__in=codenames))
    if all_model_perms:
        perms += list(Permission.objects.filter(content_type__app_label=APP).exclude(codename__startswith='einsatz_'))
    return perms


def setup_einsatz_roles(out=print, replace=False):
    for group_name, codenames in EINSATZ_ROLES.items():
        group, created = Group.objects.get_or_create(name=group_name)
        perms = role_permissions(codenames, all_model_perms=group_name == Roles.MODUL_EINSATZ)
        if replace:
            group.permissions.set(perms)
        else:
            group.permissions.add(*perms)
        out(f"  ✓ {group_name}: {'erstellt' if created else 'aktualisiert'} ({len(perms)} Permissions)")


def group_level(user):
    names = set(user.groups.filter(name__in=LEVEL_GROUPS).values_list('name', flat=True))
    level = 'none'
    for key, _label, group, _desc in EINSATZ_LEVELS:
        if group in names:
            level = key
    return level


def effective_level(user):
    level = 'none'
    for key, perm in _PERM_BY_LEVEL.items():
        if user.has_perm(f'{APP}.{perm}'):
            level = key
    return level


def set_level(user, level, assigned_by=None):
    if level not in _LEVEL_BY_KEY:
        raise ValueError(f'Unbekannte Stufe: {level}')
    target = _LEVEL_BY_KEY[level]
    if Group.objects.filter(name__in=EINSATZ_ROLES).count() != len(EINSATZ_ROLES):
        setup_einsatz_roles(out=lambda msg: None)
    for group_name in LEVEL_GROUPS:
        if group_name != target and user.groups.filter(name=group_name).exists():
            PermissionHelper.remove_role(user, group_name, removed_by=assigned_by)
    if target and not user.groups.filter(name=target).exists():
        PermissionHelper.assign_role(user, target, assigned_by=assigned_by)
    user.user_permissions.remove(*Permission.objects.filter(content_type__app_label=APP, codename__startswith='einsatz_'))
