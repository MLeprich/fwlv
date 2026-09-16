"""
Einheitsführung der Freiwilligen Feuerwehr.

Einheitsführer und Vertreter werden pro FF-Einheit an der VolunteerUnit
hinterlegt; die Rollen "FF Einheitsführer" / "FF Vertreter" leiten sich
daraus ab. Alle Wege, die die Führung ändern (Benutzerverwaltung und
FF-Verwaltung), laufen über diese Funktionen, damit Einheit und Rolle
nie auseinanderlaufen.
"""

from django.db import transaction

from organization.models import VolunteerUnit
from permissions.constants import Roles
from permissions.utils import PermissionHelper


def sync_ff_roles(person, actor=None):
    """
    Leitet die FF-Rollen einer Person aus ihrer Einheitsführung ab:
    Führer einer aktiven Einheit -> FF Einheitsführer, Vertreter -> FF Vertreter.
    Ohne Benutzerkonto gibt es nichts zu synchronisieren.
    """
    user = getattr(person, 'user', None)
    if not user:
        return
    leads = VolunteerUnit.objects.filter(leader=person, is_active=True).exists()
    deputies = VolunteerUnit.objects.filter(deputy_leader=person, is_active=True).exists()
    for role, wanted in ((Roles.FF_EINHEITSFUEHRER, leads), (Roles.FF_VERTRETER, deputies)):
        if wanted:
            PermissionHelper.assign_role(user, role, assigned_by=actor)
        else:
            PermissionHelper.remove_role(user, role, removed_by=actor)


def set_unit_leadership(unit, leader, deputy, actor=None):
    """
    Setzt Einheitsführer und Vertreter einer Einheit und gleicht die Rollen
    aller betroffenen Personen ab (alte und neue Führung).

    Gibt die Personen der neuen Führung ohne Benutzerkonto zurück, damit
    die Oberfläche darauf hinweisen kann.
    """
    with transaction.atomic():
        affected = {p for p in (unit.leader, unit.deputy_leader, leader, deputy) if p}
        unit.leader = leader
        unit.deputy_leader = deputy
        unit.save(update_fields=['leader', 'deputy_leader', 'updated_at'])
        for person in affected:
            sync_ff_roles(person, actor=actor)
    return [p for p in (leader, deputy) if p and not getattr(p, 'user', None)]


def leadership_candidates(unit):
    """Aktive FF-Personen der Einheit; die aktuelle Führung bleibt wählbar."""
    from django.db.models import Q
    from personnel.models import Person

    q = Q(volunteer_unit=unit, is_volunteer_fire_brigade=True)
    if unit.leader_id:
        q |= Q(pk=unit.leader_id)
    if unit.deputy_leader_id:
        q |= Q(pk=unit.deputy_leader_id)
    return Person.objects.filter(q, is_active=True).select_related('user').order_by('last_name', 'first_name')
