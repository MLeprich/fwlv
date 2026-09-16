"""
Legt die Rollen für das Termine-Modul an – additiv.

    python manage.py setup_termine_permissions [--dry-run]
"""
from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand
from django.db import transaction

from permissions.constants import Roles
from termine.roles import APP, setup_termine_roles


class Command(BaseCommand):
    help = 'Legt die Termine-Rollen an (additiv, entzieht keine Rechte)'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true')

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        self.stdout.write(self.style.MIGRATE_HEADING('=== Termine-Rollen ==='))
        perms = list(Permission.objects.filter(content_type__app_label=APP))
        if not any(p.codename == 'termine_view' for p in perms):
            self.stdout.write(self.style.ERROR('Termine-Rechte fehlen. Bitte zuerst "manage.py migrate" ausführen.'))
            return
        with transaction.atomic():
            setup_termine_roles(out=lambda msg: self.stdout.write(self.style.SUCCESS(msg)))
            admin = Group.objects.filter(name=Roles.ADMINISTRATOR).first()
            if admin:
                admin.permissions.add(*perms)
                self.stdout.write(f'  ✓ {Roles.ADMINISTRATOR}: alle Termine-Rechte')
            # Alle bestehenden Rollen dürfen den Kalender sehen (allgemeine Feuerwehr-Termine)
            view = [p for p in perms if p.codename == 'termine_view']
            for role_name in (Roles.STANDARD_USER, Roles.WACHLEITER, Roles.BEREICHSLEITUNG):
                group = Group.objects.filter(name=role_name).first()
                if group:
                    group.permissions.add(*view)
                    self.stdout.write(f'  ✓ {role_name}: Leserecht')
            if dry_run:
                transaction.set_rollback(True)
        self.stdout.write(self.style.SUCCESS('✓ Fertig'))
