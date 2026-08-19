"""
Legt die Rollen für das IUK-Modul (Drohnenstaffel) an – additiv.

Wie beim Umfrage-Modul werden bestehende Gruppen nicht neu aufgebaut, sondern
nur ergänzt. Es wird niemandem ein Recht entzogen.

    python manage.py setup_iuk_permissions [--dry-run]
"""

from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand
from django.db import transaction

from permissions.constants import Modules, Roles

#: Rollen, die die Drohnenstaffel einsehen dürfen (nur view_*).
VIEWER_ROLES = [
    Roles.ADMINISTRATOR,
    Roles.BEREICHSLEITUNG,
    Roles.WACHLEITER,
]


class Command(BaseCommand):
    help = 'Legt die IUK-Rollen an (additiv, entzieht keine Rechte)'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true',
                            help='Nur anzeigen, was geändert würde')

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        self.stdout.write(self.style.MIGRATE_HEADING('=== IUK-Rollen (Drohnenstaffel) ==='))
        if dry_run:
            self.stdout.write(self.style.NOTICE('[DRY RUN] Es wird nichts gespeichert\n'))

        iuk_perms = list(Permission.objects.filter(content_type__app_label=Modules.IUK))
        if not iuk_perms:
            self.stdout.write(self.style.ERROR(
                'Keine IUK-Permissions gefunden. Bitte zuerst "manage.py migrate" ausführen.'
            ))
            return

        try:
            with transaction.atomic():
                self._setup_module_lead(iuk_perms, dry_run)
                self._setup_sachbearbeiter(iuk_perms, dry_run)
                self._setup_viewers(iuk_perms, dry_run)

                if dry_run:
                    transaction.set_rollback(True)
        except Exception as error:
            self.stdout.write(self.style.ERROR(f'\n✗ Fehler: {error}'))
            raise

        self.stdout.write(self.style.SUCCESS('\n✓ Fertig'))
        if not dry_run:
            self.stdout.write(
                'Denken Sie daran, das Modul unter Einstellungen → Module zu aktivieren.'
            )

    def _add(self, group, perms, dry_run):
        already = set(group.permissions.values_list('codename', flat=True))
        missing = [perm for perm in perms if perm.codename not in already]
        if not dry_run:
            group.permissions.add(*missing)
        return missing

    def _setup_module_lead(self, iuk_perms, dry_run):
        self.stdout.write('\n1. Modulverantwortlicher IUK (alle Rechte)...')
        group, created = Group.objects.get_or_create(name=Roles.MODUL_IUK)
        missing = self._add(group, iuk_perms, dry_run)
        status = 'neu angelegt' if created else 'bereits vorhanden'
        self.stdout.write(self.style.SUCCESS(
            f'  ✓ Gruppe {status}, {len(missing)} Recht(e) ergänzt'
        ))

    def _setup_sachbearbeiter(self, iuk_perms, dry_run):
        self.stdout.write('\n2. Sachbearbeiter IUK (ansehen, anlegen, ändern)...')
        group, created = Group.objects.get_or_create(name=Roles.SACHBEARBEITER_IUK)
        perms = [p for p in iuk_perms if not p.codename.startswith('delete_')]
        missing = self._add(group, perms, dry_run)
        status = 'neu angelegt' if created else 'bereits vorhanden'
        self.stdout.write(self.style.SUCCESS(
            f'  ✓ Gruppe {status}, {len(missing)} Recht(e) ergänzt'
        ))

    def _setup_viewers(self, iuk_perms, dry_run):
        self.stdout.write('\n3. Leserecht für bestehende Rollen...')
        view_perms = [p for p in iuk_perms if p.codename.startswith('view_')]
        for role_name in VIEWER_ROLES:
            group = Group.objects.filter(name=role_name).first()
            if group is None:
                self.stdout.write(self.style.WARNING(
                    f'  – {role_name}: Gruppe existiert nicht, übersprungen'
                ))
                continue
            perms = iuk_perms if role_name == Roles.ADMINISTRATOR else view_perms
            missing = self._add(group, perms, dry_run)
            self.stdout.write(f'  ✓ {role_name}: {len(missing)} Recht(e) ergänzt')
