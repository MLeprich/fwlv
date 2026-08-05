"""
Legt die Rollen für das Umfrage-Modul an – ohne bestehende Gruppen anzufassen.

Warum ein eigener Befehl statt `setup_permissions`?
`setup_permissions` ruft für jede Gruppe `permissions.clear()` auf und baut die
Rechte komplett neu auf. Für ein einzelnes nachgerüstetes Modul wäre das ein
unnötig großer Eingriff in eine laufende Installation. Dieser Befehl ist rein
additiv: er nimmt niemandem ein Recht weg.
"""

from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand
from django.db import transaction

from permissions.constants import Modules, Roles


#: Rollen, die an Umfragen teilnehmen dürfen. Bewusst nur bestehende Gruppen –
#: dieser Befehl soll keine Rollen erfinden, die es in der Installation nicht gibt.
PARTICIPANT_ROLES = [
    Roles.STANDARD_USER,
    Roles.SACHBEARBEITER,
    Roles.LAGERVERWALTER,
    Roles.WACHLEITER,
    Roles.BEREICHSLEITUNG,
    Roles.FF_EINHEITSFUEHRER,
    Roles.FF_VERTRETER,
]


class Command(BaseCommand):
    help = 'Legt die Umfrage-Rollen an (additiv, entzieht keine Rechte)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Nur anzeigen, was geändert würde',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        self.stdout.write(self.style.MIGRATE_HEADING('=== Umfrage-Rollen ==='))
        if dry_run:
            self.stdout.write(self.style.NOTICE('[DRY RUN] Es wird nichts gespeichert\n'))

        survey_perms = Permission.objects.filter(content_type__app_label=Modules.SURVEYS)
        if not survey_perms.exists():
            self.stdout.write(self.style.ERROR(
                'Keine Umfrage-Permissions gefunden. Bitte zuerst "manage.py migrate" ausführen.'
            ))
            return

        try:
            with transaction.atomic():
                self._setup_module_lead(survey_perms, dry_run)
                self._setup_participants(dry_run)

                if dry_run:
                    # Rollback erzwingen – so wird der Dry-Run wirklich nicht wirksam
                    transaction.set_rollback(True)
        except Exception as error:
            self.stdout.write(self.style.ERROR(f'\n✗ Fehler: {error}'))
            raise

        self.stdout.write(self.style.SUCCESS('\n✓ Fertig'))
        if not dry_run:
            self.stdout.write(
                'Denken Sie daran, das Modul unter Einstellungen → Module zu aktivieren.'
            )

    def _setup_module_lead(self, survey_perms, dry_run):
        """Modulverantwortlicher Umfragen: alle Rechte des Moduls"""
        self.stdout.write('\n1. Modulverantwortlicher Umfragen...')

        group, created = Group.objects.get_or_create(name=Roles.MODUL_SURVEYS)

        # Nur ergänzen, nie entfernen – eine bestehende Gruppe könnte bewusst
        # zusätzliche Rechte haben.
        already = set(group.permissions.values_list('codename', flat=True))
        missing = [perm for perm in survey_perms if perm.codename not in already]

        if not dry_run:
            group.permissions.add(*missing)

        status = 'neu angelegt' if created else 'bereits vorhanden'
        self.stdout.write(self.style.SUCCESS(
            f'  ✓ Gruppe {status}, {len(missing)} Recht(e) ergänzt'
        ))

    def _setup_participants(self, dry_run):
        """Teilnahme-Recht für die operativen Rollen"""
        self.stdout.write('\n2. Teilnahme-Recht (participate_survey)...')

        try:
            participate = Permission.objects.get(
                content_type__app_label=Modules.SURVEYS,
                codename='participate_survey',
            )
        except Permission.DoesNotExist:
            self.stdout.write(self.style.ERROR('  ✗ Permission fehlt'))
            return

        granted, skipped = [], []
        for role_name in PARTICIPANT_ROLES:
            group = Group.objects.filter(name=role_name).first()
            if group is None:
                skipped.append(role_name)
                continue
            if not dry_run:
                group.permissions.add(participate)
            granted.append(role_name)

        for role_name in granted:
            self.stdout.write(f'  ✓ {role_name}')
        for role_name in skipped:
            self.stdout.write(self.style.WARNING(
                f'  – {role_name}: Gruppe existiert nicht, übersprungen'
            ))
