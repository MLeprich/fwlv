"""
Legt die Rollen für das Dienstplan-Modul an – additiv, es wird niemandem ein Recht entzogen.

    python manage.py setup_dienstplan_permissions [--dry-run]

- Modulverantwortlicher Dienstplan: alle Rechte (Upload, Codes pflegen, löschen)
- Sachbearbeiter Dienstplan: ansehen und hochladen
- Administrator / Bereichsleitung / Wachleiter: Leserecht
"""
from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand
from django.db import transaction

from permissions.constants import Modules, Roles

VIEWER_ROLES = [Roles.ADMINISTRATOR, Roles.BEREICHSLEITUNG, Roles.WACHLEITER]


class Command(BaseCommand):
    help = 'Legt die Dienstplan-Rollen an (additiv, entzieht keine Rechte)'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Nur anzeigen, was geändert würde')

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        self.stdout.write(self.style.MIGRATE_HEADING('=== Dienstplan-Rollen ==='))
        perms = list(Permission.objects.filter(content_type__app_label=Modules.DIENSTPLAN))
        if not perms:
            self.stdout.write(self.style.ERROR('Keine Dienstplan-Permissions gefunden. Bitte zuerst "manage.py migrate" ausführen.'))
            return
        with transaction.atomic():
            group, created = Group.objects.get_or_create(name=Roles.MODUL_DIENSTPLAN)
            n = self._add(group, perms, dry_run)
            self.stdout.write(f'  ✓ {group.name}: {"neu" if created else "vorhanden"}, {n} Recht(e) ergänzt')

            group, created = Group.objects.get_or_create(name=Roles.SACHBEARBEITER_DIENSTPLAN)
            sachbearbeiter = [p for p in perms if p.codename.startswith('view_') or p.codename == 'add_rosterupload']
            n = self._add(group, sachbearbeiter, dry_run)
            self.stdout.write(f'  ✓ {group.name}: {"neu" if created else "vorhanden"}, {n} Recht(e) ergänzt')

            view_perms = [p for p in perms if p.codename.startswith('view_')]
            for role_name in VIEWER_ROLES:
                group = Group.objects.filter(name=role_name).first()
                if group is None:
                    self.stdout.write(self.style.WARNING(f'  – {role_name}: Gruppe existiert nicht, übersprungen'))
                    continue
                n = self._add(group, perms if role_name == Roles.ADMINISTRATOR else view_perms, dry_run)
                self.stdout.write(f'  ✓ {role_name}: {n} Recht(e) ergänzt')
            if dry_run:
                transaction.set_rollback(True)
        self.stdout.write(self.style.SUCCESS('✓ Fertig'))

    def _add(self, group, perms, dry_run):
        already = set(group.permissions.values_list('codename', flat=True))
        missing = [p for p in perms if p.codename not in already]
        if not dry_run:
            group.permissions.add(*missing)
        return len(missing)
