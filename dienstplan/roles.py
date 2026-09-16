"""
Dienstplan – Rollen und Zugriffsstufen

Die Stufen werden über Gruppen vergeben (nicht über Einzelrechte), damit
„Kein Zugriff“ alles sauber entzieht. Genutzt von ``setup_dienstplan_permissions``
und der Benutzerverwaltung (Karte „Dienstplan“). Die Statistik ist ein
unabhängiger Zusatz (eigene Gruppe), der mit jeder Stufe kombinierbar ist.
"""
from django.contrib.auth.models import Group, Permission

from permissions.constants import Roles
from permissions.utils import PermissionHelper

APP = 'dienstplan'

#: Gruppe → Rechte
DIENSTPLAN_ROLES = {
    Roles.DIENSTPLAN_LESER: ['dienstplan_view'],
    Roles.SACHBEARBEITER_DIENSTPLAN: ['dienstplan_view', 'dienstplan_edit'],
    Roles.MODUL_DIENSTPLAN: ['dienstplan_view', 'dienstplan_edit', 'dienstplan_stats'],
    Roles.DIENSTPLAN_STATISTIK: ['dienstplan_stats'],
}
LEVEL_GROUPS = (Roles.DIENSTPLAN_LESER, Roles.SACHBEARBEITER_DIENSTPLAN, Roles.MODUL_DIENSTPLAN)

#: Zugriffsstufen: (Schlüssel, Bezeichnung, Gruppe, Beschreibung)
DIENSTPLAN_LEVELS = [
    ('none', 'Kein Zugriff', None, 'Dienstplan ist nicht sichtbar'),
    ('view', 'Nur ansehen', Roles.DIENSTPLAN_LESER,
     'Übersicht, Monatsansicht und Uploads ansehen'),
    ('edit', 'Bearbeiten', Roles.SACHBEARBEITER_DIENSTPLAN,
     'Zusätzlich Exporte hochladen und übernehmen, Dienstcodes pflegen'),
    ('manage', 'Verwalten', Roles.MODUL_DIENSTPLAN,
     'Zusätzlich Uploads löschen und statistische Auswertung'),
]
_LEVEL_BY_KEY = {key: group for key, _label, group, _desc in DIENSTPLAN_LEVELS}
_PERM_BY_LEVEL = {'view': 'dienstplan_view', 'edit': 'dienstplan_edit'}


def role_permissions(codenames, all_model_perms=False):
    perms = list(Permission.objects.filter(content_type__app_label=APP, codename__in=codenames))
    if all_model_perms:
        perms += list(Permission.objects.filter(content_type__app_label=APP).exclude(codename__startswith='dienstplan_'))
    return perms


def setup_dienstplan_roles(out=print, replace=False):
    """Gruppen anlegen; ``replace`` setzt die Rechte exakt, sonst nur ergänzen."""
    for group_name, codenames in DIENSTPLAN_ROLES.items():
        group, created = Group.objects.get_or_create(name=group_name)
        perms = role_permissions(codenames, all_model_perms=group_name == Roles.MODUL_DIENSTPLAN)
        if replace:
            group.permissions.set(perms)
        else:
            group.permissions.add(*perms)
        out(f"  ✓ {group_name}: {'erstellt' if created else 'aktualisiert'} ({len(perms)} Permissions)")


def group_level(user):
    """Stufe aus den Dienstplan-Gruppen des Benutzers (höchste gewinnt)."""
    names = set(user.groups.filter(name__in=LEVEL_GROUPS).values_list('name', flat=True))
    level = 'none'
    for key, _label, group, _desc in DIENSTPLAN_LEVELS:
        if group in names:
            level = key
    return level


def effective_level(user):
    """Tatsächliche Stufe inkl. anderer Rollen (z.B. Administrator) und Einzelrechten."""
    level = 'none'
    for key, perm in _PERM_BY_LEVEL.items():
        if user.has_perm(f'{APP}.{perm}'):
            level = key
    if user.has_perm(f'{APP}.delete_rosterupload') and level == 'edit':
        level = 'manage'
    return level


def has_stats_group(user):
    return user.groups.filter(name=Roles.DIENSTPLAN_STATISTIK).exists()


def set_level(user, level, stats=None, assigned_by=None):
    """Benutzer genau einer Stufen-Gruppe zuordnen (oder keiner); ``stats`` schaltet die Statistik-Gruppe."""
    if level not in _LEVEL_BY_KEY:
        raise ValueError(f'Unbekannte Stufe: {level}')
    target = _LEVEL_BY_KEY[level]
    if not Group.objects.filter(name__in=DIENSTPLAN_ROLES).count() == len(DIENSTPLAN_ROLES):
        setup_dienstplan_roles(out=lambda msg: None)
    for group_name in LEVEL_GROUPS:
        if group_name != target and user.groups.filter(name=group_name).exists():
            PermissionHelper.remove_role(user, group_name, removed_by=assigned_by)
    if target and not user.groups.filter(name=target).exists():
        PermissionHelper.assign_role(user, target, assigned_by=assigned_by)
    if stats is not None:
        has = has_stats_group(user)
        if stats and not has:
            PermissionHelper.assign_role(user, Roles.DIENSTPLAN_STATISTIK, assigned_by=assigned_by)
        elif not stats and has:
            PermissionHelper.remove_role(user, Roles.DIENSTPLAN_STATISTIK, removed_by=assigned_by)
    # Direkt vergebene Einzelrechte würden die Auswahl unterlaufen
    user.user_permissions.remove(*Permission.objects.filter(
        content_type__app_label=APP, codename__startswith='dienstplan_'))
