"""
Legt die Rollen der Brandverhütungsschau an – additiv, ohne anderen Gruppen
Rechte zu nehmen (vgl. setup_survey_permissions).

    BVS Sachbearbeiter:    bvs_view + bvs_edit      (durchführen, PSV-Fristen pflegen)
    BVS Verantwortlicher:  zusätzlich bvs_manage    (Mustersätze, PSV-Prüfarten)

Beide Rollen erhalten außerdem Leserechte auf die Objektverwaltung, damit
Objekte und der Reiter „Brandverhütungsschau“ erreichbar sind.
"""

from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand
from django.db import transaction

from permissions.constants import Roles

APP = 'objektverwaltung'
BVS_ROLES = {
    Roles.BVS_SACHBEARBEITER: ['bvs_view', 'bvs_edit'],
    Roles.BVS_VERANTWORTLICHER: ['bvs_view', 'bvs_edit', 'bvs_manage'],
}


def bvs_role_permissions(codenames):
    """BVS-Rechte plus alle view_*-Rechte der Objektverwaltung."""
    perms = list(Permission.objects.filter(content_type__app_label=APP, codename__in=codenames))
    perms += list(Permission.objects.filter(content_type__app_label=APP, codename__startswith='view_'))
    return perms


def setup_bvs_roles(out=print, replace=False):
    """Gruppen anlegen; ``replace`` setzt die Rechte exakt (für setup_permissions)."""
    for group_name, codenames in BVS_ROLES.items():
        group, created = Group.objects.get_or_create(name=group_name)
        perms = bvs_role_permissions(codenames)
        if replace:
            group.permissions.set(perms)
        else:
            group.permissions.add(*perms)
        out(f"  ✓ {group_name}: {'erstellt' if created else 'aktualisiert'} ({len(perms)} Permissions)")


class Command(BaseCommand):
    help = 'Legt die Rollen der Brandverhütungsschau an (additiv, entzieht keine Rechte)'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Nur anzeigen, nichts speichern')

    def handle(self, *args, **options):
        if not Permission.objects.filter(content_type__app_label=APP, codename='bvs_view').exists():
            self.stdout.write(self.style.ERROR('BVS-Rechte fehlen – bitte zuerst „manage.py migrate“ ausführen.'))
            return
        self.stdout.write(self.style.MIGRATE_HEADING('=== Rollen Brandverhütungsschau ==='))
        with transaction.atomic():
            setup_bvs_roles(out=lambda msg: self.stdout.write(self.style.SUCCESS(msg)))
            if options['dry_run']:
                transaction.set_rollback(True)
                self.stdout.write(self.style.NOTICE('[DRY RUN] Nichts gespeichert'))
        self.stdout.write('Benutzer über Benutzerverwaltung → Rollen den Gruppen zuordnen.')
