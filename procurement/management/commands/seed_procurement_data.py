"""
Management Command: Seed Procurement Stammdaten

Befuellt die Stammdaten-Tabellen mit den Werten aus der Excel-Vorlage
"Bestellanforderung".

Usage:
    python manage.py seed_procurement_data
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from procurement.models import (
    Sachkonto,
    NKFNummer,
    VerwendungAllgemein,
    Mengeneinheit,
    ProcurementDepartment,
)

User = get_user_model()


class Command(BaseCommand):
    help = 'Befuellt die Procurement-Stammdaten mit Werten aus der Excel-Vorlage'

    def handle(self, *args, **options):
        # Get or create a system user for audit fields
        self.system_user = User.objects.filter(is_superuser=True).first()
        if not self.system_user:
            self.stderr.write(self.style.ERROR('Kein Superuser gefunden. Bitte zuerst einen Superuser anlegen.'))
            return

        self.stdout.write('Procurement-Stammdaten werden angelegt...\n')

        self._seed_sachkonten()
        self._seed_nkf_nummern()
        self._seed_verwendung_allgemein()
        self._seed_mengeneinheiten()
        self._seed_fachbereiche()

        self.stdout.write(self.style.SUCCESS('\nAlle Stammdaten erfolgreich angelegt!'))

    def _seed_sachkonten(self):
        data = [
            {'typ': 'KFZ-Aufwendungen', 'nummer': '525135', 'sort_order': 1},
            {'typ': 'Beschaffungswesen', 'nummer': '543188', 'sort_order': 2},
        ]
        created = 0
        for item in data:
            _, was_created = Sachkonto.objects.get_or_create(
                typ=item['typ'],
                defaults={
                    'nummer': item['nummer'],
                    'sort_order': item['sort_order'],
                    'created_by': self.system_user,
                    'updated_by': self.system_user,
                },
            )
            if was_created:
                created += 1
        self.stdout.write(f'  Sachkonten: {created} neu, {len(data) - created} bereits vorhanden')

    def _seed_nkf_nummern(self):
        data = [
            {'nummer': '610002150100', 'bezeichnung': '', 'sort_order': 1},
            {'nummer': '610002150200', 'bezeichnung': '', 'sort_order': 2},
            {'nummer': '610002150300', 'bezeichnung': '', 'sort_order': 3},
            {'nummer': '610002150400', 'bezeichnung': '', 'sort_order': 4},
            {'nummer': '610002150500', 'bezeichnung': '', 'sort_order': 5},
            {'nummer': '610002150600', 'bezeichnung': '', 'sort_order': 6},
            {'nummer': '610002150700', 'bezeichnung': '', 'sort_order': 7},
            {'nummer': '610002150800', 'bezeichnung': '', 'sort_order': 8},
            {'nummer': '610002150900', 'bezeichnung': '', 'sort_order': 9},
            {'nummer': '610002151000', 'bezeichnung': '', 'sort_order': 10},
        ]
        created = 0
        for item in data:
            _, was_created = NKFNummer.objects.get_or_create(
                nummer=item['nummer'],
                defaults={
                    'bezeichnung': item['bezeichnung'],
                    'sort_order': item['sort_order'],
                    'created_by': self.system_user,
                    'updated_by': self.system_user,
                },
            )
            if was_created:
                created += 1
        self.stdout.write(f'  NKF-Nummern: {created} neu, {len(data) - created} bereits vorhanden')

    def _seed_verwendung_allgemein(self):
        data = [
            'Atemschutz',
            'Bekleidung',
            'Betriebsstoffe',
            'Brandschutzerziehung',
            'Buerobedarf',
            'Desinfektion',
            'EDV',
            'Einsatzplanung',
            'Elektrowerkstatt',
            'Fernmeldetechnik',
            'Gefahrgut',
            'Geraetewart',
            'Hoehensicherung',
            'Hygiene',
            'Jugendfeuerwehr',
            'Kantine',
            'Katastrophenschutz',
            'Kfz-Werkst.',
            'Kinderfeuerwehr',
            'Kleiderkammer',
            'Lager',
            'Leitstellentechnik',
            'Liegenschaftsverwaltung',
            'Logistik',
            'Maschinentechnik',
            'Medizintechnik',
            'Musikzug',
            'Nachrichtentechnik',
            'Notfallvorsorge',
            'Oeffentlichkeitsarbeit',
            'Personal',
            'Pressearbeit',
            'Rettungsdienst',
            'Schlauchwerkstatt',
            'Schreinerei',
            'Schulung',
            'Sicherheit',
            'Sondereinsatzgruppe',
            'Sprechfunk',
            'Tauchen',
            'Technik allgemein',
            'Telekommunikation',
            'Umweltschutz',
            'Unfallverhuetung',
            'Verwaltung',
            'Vorbeugender Brandschutz',
            'Wachabteilung',
            'Wasserfoerderung',
            'Werkfeuerwehr',
            'Zentrale Dienste',
        ]
        created = 0
        for i, name in enumerate(data, start=1):
            _, was_created = VerwendungAllgemein.objects.get_or_create(
                name=name,
                defaults={
                    'sort_order': i,
                    'created_by': self.system_user,
                    'updated_by': self.system_user,
                },
            )
            if was_created:
                created += 1
        self.stdout.write(f'  Verwendung Allgemein: {created} neu, {len(data) - created} bereits vorhanden')

    def _seed_mengeneinheiten(self):
        data = [
            'Stck.',
            'Pack',
            'Paar',
            'Rolle',
            'Liter',
            'Kanister',
            'Div.',
        ]
        created = 0
        for i, name in enumerate(data, start=1):
            _, was_created = Mengeneinheit.objects.get_or_create(
                name=name,
                defaults={
                    'sort_order': i,
                    'created_by': self.system_user,
                    'updated_by': self.system_user,
                },
            )
            if was_created:
                created += 1
        self.stdout.write(f'  Mengeneinheiten: {created} neu, {len(data) - created} bereits vorhanden')

    def _seed_fachbereiche(self):
        data = [
            {'name': 'Abt. 6-1-00 Abteilungsleitung', 'code': '6-1-00', 'sort_order': 1},
            {'name': 'Abt. 6-1-10 Einsatz', 'code': '6-1-10', 'sort_order': 2},
            {'name': 'Abt. 6-1-20 Technik', 'code': '6-1-20', 'sort_order': 3},
            {'name': 'Abt. 6-1-30 Vorbeugender Brandschutz', 'code': '6-1-30', 'sort_order': 4},
            {'name': 'Abt. 6-1-40 Rettungsdienst', 'code': '6-1-40', 'sort_order': 5},
            {'name': 'Abt. 6-1-50 Verwaltung', 'code': '6-1-50', 'sort_order': 6},
            {'name': 'Abt. 6-1-60 Ausbildung', 'code': '6-1-60', 'sort_order': 7},
            {'name': 'Abt. 6-1-70 Katastrophenschutz', 'code': '6-1-70', 'sort_order': 8},
            {'name': 'Abt. 6-1-80 Freiwillige Feuerwehr', 'code': '6-1-80', 'sort_order': 9},
        ]
        created = 0
        for item in data:
            _, was_created = ProcurementDepartment.objects.get_or_create(
                code=item['code'],
                defaults={
                    'name': item['name'],
                    'sort_order': item['sort_order'],
                    'created_by': self.system_user,
                    'updated_by': self.system_user,
                },
            )
            if was_created:
                created += 1
        self.stdout.write(f'  Fachbereiche: {created} neu, {len(data) - created} bereits vorhanden')
