"""
Brandverhütungsschau – Rollen und Zugriffsstufen

Die Stufen werden über Gruppen vergeben (nicht über Einzelrechte), damit die
nötigen Leserechte auf die Objektverwaltung immer mitkommen und „Kein Zugriff“
alles sauber entzieht. Genutzt von ``setup_bvs_permissions``,
``setup_permissions`` und der Benutzerverwaltung (Karte „Brandverhütungsschau“).
"""

from django.contrib.auth.models import Group, Permission

from permissions.constants import Roles
from permissions.utils import PermissionHelper

APP = 'objektverwaltung'

#: Gruppe → BVS-Rechte (zusätzlich immer alle view_*-Rechte der Objektverwaltung)
BVS_ROLES = {
    Roles.BVS_LESER: ['bvs_view'],
    Roles.BVS_SACHBEARBEITER: ['bvs_view', 'bvs_edit'],
    Roles.BVS_VERANTWORTLICHER: ['bvs_view', 'bvs_edit', 'bvs_manage'],
}

#: Zugriffsstufen in aufsteigender Reihenfolge: (Schlüssel, Bezeichnung, Gruppe, Beschreibung)
BVS_LEVELS = [
    ('none', 'Kein Zugriff', None, 'Brandverhütungsschau und PSV-Fristen sind nicht sichtbar'),
    ('view', 'Nur ansehen', Roles.BVS_LESER,
     'Niederschriften, PSV-Fristen und Mustersätze ansehen, PDFs öffnen'),
    ('edit', 'Durchführen', Roles.BVS_SACHBEARBEITER,
     'Brandverhütungsschauen durchführen, PSV-Fristen und Nachschau pflegen'),
    ('manage', 'Verwalten', Roles.BVS_VERANTWORTLICHER,
     'Zusätzlich Mustersätze (inkl. PDF-Import) und PSV-Prüfarten verwalten'),
]
_LEVEL_BY_KEY = {key: group for key, _label, group, _desc in BVS_LEVELS}
_PERM_BY_LEVEL = {'view': 'bvs_view', 'edit': 'bvs_edit', 'manage': 'bvs_manage'}


def bvs_role_permissions(codenames):
    """BVS-Rechte plus alle view_*-Rechte der Objektverwaltung."""
    perms = list(Permission.objects.filter(content_type__app_label=APP, codename__in=codenames))
    perms += list(Permission.objects.filter(content_type__app_label=APP, codename__startswith='view_'))
    return perms


def setup_bvs_roles(out=print, replace=False):
    """Gruppen anlegen; ``replace`` setzt die Rechte exakt (für setup_permissions), sonst nur ergänzen."""
    for group_name, codenames in BVS_ROLES.items():
        group, created = Group.objects.get_or_create(name=group_name)
        perms = bvs_role_permissions(codenames)
        if replace:
            group.permissions.set(perms)
        else:
            group.permissions.add(*perms)
        out(f"  ✓ {group_name}: {'erstellt' if created else 'aktualisiert'} ({len(perms)} Permissions)")


def group_level(user):
    """Stufe aus den BVS-Gruppen des Benutzers (höchste gewinnt)."""
    names = set(user.groups.filter(name__in=BVS_ROLES).values_list('name', flat=True))
    level = 'none'
    for key, _label, group, _desc in BVS_LEVELS:
        if group in names:
            level = key
    return level


def effective_level(user):
    """Tatsächliche Stufe inkl. anderer Rollen (z.B. Administrator) und Einzelrechten."""
    level = 'none'
    for key, perm in _PERM_BY_LEVEL.items():
        if user.has_perm(f'{APP}.{perm}'):
            level = key
    return level


def set_level(user, level, assigned_by=None):
    """Benutzer genau einer BVS-Gruppe zuordnen (oder keiner); fehlende Gruppen werden angelegt."""
    if level not in _LEVEL_BY_KEY:
        raise ValueError(f'Unbekannte Stufe: {level}')
    target = _LEVEL_BY_KEY[level]
    if target and not Group.objects.filter(name=target).exists():
        setup_bvs_roles(out=lambda msg: None)
    for group_name in BVS_ROLES:
        if group_name != target and user.groups.filter(name=group_name).exists():
            PermissionHelper.remove_role(user, group_name, removed_by=assigned_by)
    if target and not user.groups.filter(name=target).exists():
        PermissionHelper.assign_role(user, target, assigned_by=assigned_by)
    # Direkt vergebene BVS-Einzelrechte würden die Auswahl unterlaufen
    user.user_permissions.remove(*Permission.objects.filter(
        content_type__app_label=APP, codename__startswith='bvs_'))
