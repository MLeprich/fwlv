"""
Legt die Rollen der Brandverhütungsschau an – additiv, ohne anderen Gruppen
Rechte zu nehmen (vgl. setup_survey_permissions).

    BVS Leser:             bvs_view                 (nur ansehen)
    BVS Sachbearbeiter:    bvs_view + bvs_edit      (durchführen, PSV-Fristen pflegen)
    BVS Verantwortlicher:  zusätzlich bvs_manage    (Mustersätze, PSV-Prüfarten)

Alle Rollen erhalten außerdem Leserechte auf die Objektverwaltung, damit
Objekte und der Reiter „Brandverhütungsschau“ erreichbar sind. Zuordnen lassen
sie sich in der Benutzerverwaltung (Karte „Brandverhütungsschau“); fehlende
Gruppen werden dort bei Bedarf automatisch angelegt.
"""

from django.contrib.auth.models import Permission
from django.core.management.base import BaseCommand
from django.db import transaction

from objektverwaltung.bvs_roles import APP, setup_bvs_roles


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
        self.stdout.write('Benutzer in der Benutzerverwaltung unter „Brandverhütungsschau“ zuordnen.')
