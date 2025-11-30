"""
Management Command: Setup Standard-Rollen
Usage: python manage.py setup_roles
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType


class Command(BaseCommand):
    help = 'Erstellt Standard-Rollen für FLVS'

    def handle(self, *args, **options):
        self.stdout.write('Erstelle Standard-Rollen...')

        # Administrator
        admin_group, created = Group.objects.get_or_create(name='Administrator')
        if created:
            self.stdout.write(self.style.SUCCESS('✓ Administrator-Rolle erstellt'))
            # Admins bekommen alle Permissions später zugewiesen

        # Modulverantwortlicher
        module_manager, created = Group.objects.get_or_create(name='Modulverantwortlicher')
        if created:
            self.stdout.write(self.style.SUCCESS('✓ Modulverantwortlicher-Rolle erstellt'))

        # Lagerverwalter
        warehouse_manager, created = Group.objects.get_or_create(name='Lagerverwalter')
        if created:
            self.stdout.write(self.style.SUCCESS('✓ Lagerverwalter-Rolle erstellt'))

        # Werkstattmeister
        workshop_master, created = Group.objects.get_or_create(name='Werkstattmeister')
        if created:
            self.stdout.write(self.style.SUCCESS('✓ Werkstattmeister-Rolle erstellt'))

        # BTM-Beauftragter
        btm_officer, created = Group.objects.get_or_create(name='BTM-Beauftragter')
        if created:
            self.stdout.write(self.style.SUCCESS('✓ BTM-Beauftragter-Rolle erstellt'))

        # Bereichsleitung
        bereichsleitung, created = Group.objects.get_or_create(name='Bereichsleitung')
        if created:
            self.stdout.write(self.style.SUCCESS('✓ Bereichsleitung-Rolle erstellt'))

        # Wachleiter
        watch_commander, created = Group.objects.get_or_create(name='Wachleiter')
        if created:
            self.stdout.write(self.style.SUCCESS('✓ Wachleiter-Rolle erstellt'))

        # Standard-Nutzer
        standard_user, created = Group.objects.get_or_create(name='Standard-Nutzer')
        if created:
            self.stdout.write(self.style.SUCCESS('✓ Standard-Nutzer-Rolle erstellt'))

        self.stdout.write(self.style.SUCCESS('\n✓ Alle Rollen erfolgreich erstellt!'))
