"""
Legt die Rollen für die Einsatzvorbereitung an – additiv.

    python manage.py setup_einsatzvorbereitung_permissions [--dry-run]
"""
from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand
from django.db import transaction

from einsatzvorbereitung.roles import APP, setup_einsatz_roles
from permissions.constants import Roles


class Command(BaseCommand):
    help = 'Legt die Rollen der Einsatzvorbereitung an (additiv, entzieht keine Rechte)'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true')

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('=== Einsatzvorbereitung-Rollen ==='))
        perms = list(Permission.objects.filter(content_type__app_label=APP))
        if not any(p.codename == 'einsatz_view' for p in perms):
            self.stdout.write(self.style.ERROR('Rechte fehlen. Bitte zuerst "manage.py migrate" ausführen.'))
            return
        with transaction.atomic():
            setup_einsatz_roles(out=lambda msg: self.stdout.write(self.style.SUCCESS(msg)))
            admin = Group.objects.filter(name=Roles.ADMINISTRATOR).first()
            if admin:
                admin.permissions.add(*perms)
                self.stdout.write(f'  ✓ {Roles.ADMINISTRATOR}: alle Rechte')
            # Leitstelle (Infomonitor/Mappe) darf Gefahrenstellen sehen und Rückmeldungen schreiben
            view = [p for p in perms if p.codename == 'einsatz_view']
            for role_name in (Roles.LST_INFOMONITOR, Roles.LST_MAPPE, Roles.WACHLEITER, Roles.BEREICHSLEITUNG):
                group = Group.objects.filter(name=role_name).first()
                if group:
                    group.permissions.add(*view)
                    self.stdout.write(f'  ✓ {role_name}: Leserecht')
            if options['dry_run']:
                transaction.set_rollback(True)
        self.stdout.write(self.style.SUCCESS('✓ Fertig'))
