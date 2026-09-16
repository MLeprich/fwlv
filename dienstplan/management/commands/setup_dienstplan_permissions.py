"""
Legt die Rollen für das Dienstplan-Modul an – additiv, es wird niemandem ein Recht entzogen.

    python manage.py setup_dienstplan_permissions [--dry-run]

- Dienstplan Leser: ansehen
- Sachbearbeiter Dienstplan: ansehen und bearbeiten (Upload, Dienstcodes)
- Modulverantwortlicher Dienstplan: alles inkl. Löschen und Statistik
- Dienstplan Statistik: Zusatzrecht statistische Auswertung
- Administrator: alle Rechte; Wachleiter: Leserecht
"""
from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand
from django.db import transaction

from dienstplan.roles import APP, setup_dienstplan_roles
from permissions.constants import Roles


class Command(BaseCommand):
    help = 'Legt die Dienstplan-Rollen an (additiv, entzieht keine Rechte)'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Nur anzeigen, was geändert würde')

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        self.stdout.write(self.style.MIGRATE_HEADING('=== Dienstplan-Rollen ==='))
        perms = list(Permission.objects.filter(content_type__app_label=APP))
        if not any(p.codename == 'dienstplan_view' for p in perms):
            self.stdout.write(self.style.ERROR('Dienstplan-Rechte fehlen. Bitte zuerst "manage.py migrate" ausführen.'))
            return
        with transaction.atomic():
            setup_dienstplan_roles(out=lambda msg: self.stdout.write(self.style.SUCCESS(msg)))
            admin = Group.objects.filter(name=Roles.ADMINISTRATOR).first()
            if admin:
                admin.permissions.add(*perms)
                self.stdout.write(f'  ✓ {Roles.ADMINISTRATOR}: alle Dienstplan-Rechte')
            wachleiter = Group.objects.filter(name=Roles.WACHLEITER).first()
            if wachleiter:
                wachleiter.permissions.add(*[p for p in perms if p.codename == 'dienstplan_view'])
                self.stdout.write(f'  ✓ {Roles.WACHLEITER}: Leserecht')
            if dry_run:
                transaction.set_rollback(True)
        self.stdout.write(self.style.SUCCESS('✓ Fertig'))
