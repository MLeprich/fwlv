from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from .models import MappeKontakt

User = get_user_model()


class MappeKontaktImportTests(TestCase):
    """CSV-Import der Ansprechpartner in der Digitalen Mappe."""

    def setUp(self):
        self.user = User.objects.create_user(username='mappe', password='pw')
        self.user.user_permissions.add(Permission.objects.get(codename='edit_mappe'))
        self.client.force_login(self.user)
        self.url = reverse('tickets:mappe_kontakt_import')

    def _upload(self, content, encoding='utf-8'):
        data = content.encode(encoding)
        return self.client.post(self.url, {
            'csv_file': SimpleUploadedFile('kontakte.csv', data, content_type='text/csv'),
        }, follow=True)

    def test_import_creates_contacts_with_all_phone_fields(self):
        csv = (
            'Name;Funktion;Festnetz;Mobil dienstlich;Mobil privat;E-Mail;Reihenfolge;Aktiv\n'
            'Max Mustermann;Leiter;0208-1;0170-1;0171-1;max@example.de;5;Ja\n'
            'Erika Beispiel;Presse;;0170-2;;;;Nein\n'
        )
        self._upload(csv)
        self.assertEqual(MappeKontakt.objects.count(), 2)
        max_ = MappeKontakt.objects.get(name='Max Mustermann')
        self.assertEqual(max_.funktion, 'Leiter')
        self.assertEqual(max_.phone, '0208-1')
        self.assertEqual(max_.phone_mobil_dienst, '0170-1')
        self.assertEqual(max_.phone_mobil_privat, '0171-1')
        self.assertEqual(max_.email, 'max@example.de')
        self.assertEqual(max_.order, 5)
        self.assertTrue(max_.is_active)
        erika = MappeKontakt.objects.get(name='Erika Beispiel')
        self.assertFalse(erika.is_active)
        self.assertEqual(erika.order, 0)
        self.assertEqual(erika.phone_mobil_dienst, '0170-2')

    def test_import_accepts_comma_and_alternative_headers(self):
        csv = (
            'Name,Rolle,Telefon,Handy,Mail\n'
            'Hans Schmidt,Hausmeister,0208-3,0172-3,hans@example.de\n'
        )
        self._upload(csv)
        hans = MappeKontakt.objects.get(name='Hans Schmidt')
        self.assertEqual(hans.funktion, 'Hausmeister')
        self.assertEqual(hans.phone, '0208-3')
        # "Handy" ohne Zusatz gilt als dienstlich
        self.assertEqual(hans.phone_mobil_dienst, '0172-3')
        self.assertEqual(hans.email, 'hans@example.de')

    def test_import_cp1252_excel_export(self):
        csv = 'Name;Funktion;Festnetz\nJürgen Müller;Führung;0208-9\n'
        self._upload(csv, encoding='cp1252')
        self.assertTrue(MappeKontakt.objects.filter(name='Jürgen Müller', funktion='Führung').exists())

    def test_existing_contact_only_fills_empty_fields(self):
        MappeKontakt.objects.create(name='Max Mustermann', funktion='Leiter',
                                    phone='0208-alt', email='')
        csv = 'Name;Funktion;Festnetz;Mobil dienstlich;E-Mail\nmax mustermann;leiter;0208-neu;0170-1;max@example.de\n'
        response = self._upload(csv)
        self.assertEqual(MappeKontakt.objects.count(), 1)
        obj = MappeKontakt.objects.get()
        self.assertEqual(obj.phone, '0208-alt')          # nicht überschrieben
        self.assertEqual(obj.phone_mobil_dienst, '0170-1')  # ergänzt
        self.assertEqual(obj.email, 'max@example.de')
        self.assertContains(response, '1 vorhandene Kontakte ergänzt')

    def test_rows_with_errors_are_reported_and_skipped(self):
        csv = (
            'Name;Funktion;E-Mail;Reihenfolge\n'
            'Ohne Funktion;;;\n'
            'Falsche Mail;Rolle;keine-mail;\n'
            'Falsche Zahl;Rolle;;abc\n'
            'Gut;Rolle;;\n'
        )
        response = self._upload(csv)
        self.assertEqual(MappeKontakt.objects.count(), 1)
        self.assertContains(response, '3 fehlerhafte Zeilen')

    def test_missing_required_columns(self):
        response = self._upload('Name;Telefon\nMax;0208\n')
        self.assertEqual(MappeKontakt.objects.count(), 0)
        self.assertContains(response, 'Spalten &quot;Name&quot; und &quot;Funktion&quot;')

    def test_import_requires_edit_mappe_permission(self):
        self.user.user_permissions.clear()
        response = self.client.post(self.url, {
            'csv_file': SimpleUploadedFile('k.csv', b'Name;Funktion\nMax;Leiter\n', content_type='text/csv'),
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(MappeKontakt.objects.count(), 0)

    def test_template_download(self):
        response = self.client.get(reverse('tickets:mappe_kontakt_import_template'))
        self.assertEqual(response.status_code, 200)
        body = response.content.decode('utf-8-sig')
        self.assertTrue(body.startswith('Name;Funktion;Festnetz;Mobil dienstlich;Mobil privat;E-Mail;Reihenfolge;Aktiv'))


class MappeKontaktModelTests(TestCase):

    def test_phone_entries_and_search_text(self):
        k = MappeKontakt(name='Max', funktion='Leiter', phone='', phone_mobil_dienst='0170', phone_mobil_privat='0171',
                         email='Max@Example.de')
        self.assertEqual(k.phone_entries, [('Mobil dienstlich', '0170'), ('Mobil privat', '0171')])
        self.assertEqual(k.search_text, 'max leiter 0170 0171 max@example.de')
