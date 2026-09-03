from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from .models import MappeKontakt, Grossereignis, InfoMonitor, BereitschaftPerson

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


class GrossereignisTests(TestCase):
    """Großereignis auf dem Info-Monitor: starten, korrigieren, beenden."""

    def setUp(self):
        self.editor = User.objects.create_user(username='lst', password='pw')
        self.editor.user_permissions.add(Permission.objects.get(codename='edit_infomonitor'))
        self.viewer = User.objects.create_user(username='viewer', password='pw')
        self.viewer.user_permissions.add(Permission.objects.get(codename='view_infomonitor'))

    def test_start_requires_edit_permission(self):
        self.client.force_login(self.viewer)
        self.client.post(reverse('tickets:grossereignis_start'),
                         {'titel': 'Test', 'beginn': '2026-09-03T10:00'})
        self.assertEqual(Grossereignis.objects.count(), 0)

    def test_start_and_end(self):
        self.client.force_login(self.editor)
        resp = self.client.post(reverse('tickets:grossereignis_start'),
                                {'titel': 'Großbrand Industriestraße', 'beginn': '2026-09-03T10:00'})
        self.assertRedirects(resp, reverse('tickets:infomonitor_display'))
        ereignis = Grossereignis.objects.get()
        self.assertTrue(ereignis.aktiv)
        self.assertEqual(ereignis.created_by, self.editor)

        # Anzeige und Kiosk zeigen das laufende Ereignis
        self.assertContains(self.client.get(reverse('tickets:infomonitor_display')), 'Großbrand Industriestraße')
        self.assertContains(self.client.get(reverse('tickets:infomonitor_kiosk')), 'Großbrand Industriestraße')

        self.client.post(reverse('tickets:grossereignis_end', args=[ereignis.pk]))
        ereignis.refresh_from_db()
        self.assertFalse(ereignis.aktiv)
        self.assertEqual(ereignis.ended_by, self.editor)
        self.assertNotContains(self.client.get(reverse('tickets:infomonitor_kiosk')), 'Großbrand Industriestraße')

    def test_update_corrects_start_time(self):
        self.client.force_login(self.editor)
        self.client.post(reverse('tickets:grossereignis_start'),
                         {'titel': 'Unwetter', 'beginn': '2026-09-03T10:00'})
        ereignis = Grossereignis.objects.get()
        self.client.post(reverse('tickets:grossereignis_update', args=[ereignis.pk]),
                         {'titel': 'Unwetterlage Stadtgebiet', 'beginn': '2026-09-03T08:30'})
        ereignis.refresh_from_db()
        self.assertEqual(ereignis.titel, 'Unwetterlage Stadtgebiet')
        from django.utils import timezone
        self.assertEqual(timezone.localtime(ereignis.beginn).strftime('%H:%M'), '08:30')

    def test_dauer_text(self):
        from datetime import timedelta
        from django.utils import timezone
        now = timezone.now()
        e = Grossereignis(titel='x', beginn=now - timedelta(hours=2, minutes=15), ende=now)
        self.assertEqual(e.dauer_text, '2 Std. 15 Min.')
        e = Grossereignis(titel='x', beginn=now - timedelta(minutes=37), ende=now)
        self.assertEqual(e.dauer_text, '37 Min.')
        e = Grossereignis(titel='x', beginn=now - timedelta(days=1, hours=3, minutes=5), ende=now)
        self.assertEqual(e.dauer_text, '1 Tag 3 Std. 5 Min.')


class BereitschaftFreitextTests(TestCase):
    """Freitext in der Bereitschafts-Kachel."""

    def test_freitext_shown_on_display_and_kiosk(self):
        monitor = InfoMonitor.load()
        monitor.bereitschaft_freitext = 'Vertretung LNA ab 18 Uhr'
        monitor.save()
        user = User.objects.create_user(username='v', password='pw')
        user.user_permissions.add(Permission.objects.get(codename='view_infomonitor'))
        self.client.force_login(user)
        self.assertContains(self.client.get(reverse('tickets:infomonitor_display')), 'Vertretung LNA ab 18 Uhr')
        self.assertContains(self.client.get(reverse('tickets:infomonitor_kiosk')), 'Vertretung LNA ab 18 Uhr')

    def test_kiosk_contact_button_with_phone_numbers(self):
        person = BereitschaftPerson.objects.create(name='Max Mustermann', phone='0208-123 / 0170-456')
        monitor = InfoMonitor.load()
        monitor.bereitschaft_a1_dienst = person
        monitor.save()
        resp = self.client.get(reverse('tickets:infomonitor_kiosk'))
        self.assertContains(resp, 'data-contact=')
        self.assertContains(resp, '0208-123')
        self.assertContains(resp, '0170-456')
        self.assertEqual(resp.context['bereitschaft_entries'][0]['phones'], ['0208-123', '0170-456'])
