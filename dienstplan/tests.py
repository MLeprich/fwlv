import os
from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from . import services
from .models import DutyCode, RosterEntry, RosterUpload, UploadStatus
from .parser import RosterFormatError, parse_roster_csv

User = get_user_model()
SAMPLE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'tmp', 'dienstplan-muster', 'Export.csv')


def build_csv(start, persons, status='vorläufig', month='Oktober 2026'):
    """Nachbau des OC:Planner-Exports: Kopf in jeder Zeile, Name hinter „Konten“, Codes in lückenhaften Spalten."""
    days = len(next(iter(persons.values())))
    end = start + timedelta(days=days - 1)
    header = ['BFO - Test, Person', '', 'Dienstplan: Querformat', '', '', '', month,
              f'{start:%d.%m.%Y} - {end:%d.%m.%Y}', f'{days}  Tage', 'Fachabteilung: Führungsdienst',
              f'Zustand: {status}', 'Name']
    header += [''] * (76 - len(header)) + ['Konten']
    code_cols = [84 + 3 * i for i in range(days)]
    lines = []
    for name, codes in persons.items():
        row = list(header) + [''] * (200 - len(header))
        row[80] = name
        for col, code in zip(code_cols, codes):
            row[col] = code
        row[149] = '16.09.2026 08:23:51 - OC:Planner 4.85.60.3'
        row[150] = 'Seite 1'
        lines.append(','.join(f'"{c}"' if c and not c.isdigit() else c for c in row[:151]))
    return ('\r\n'.join(lines) + '\r\n').encode('utf-8')


class ParserTests(TestCase):
    def test_parses_synthetic_export(self):
        raw = build_csv(date(2026, 10, 1), {
            'Müller, Anna': ['A1', '-', 'BÜ'],
            'Schmidt, Ben': ['B', 'A1', 'U'],
            'Weber, Cem': ['CT', 'CTF', 'A1'],
        })
        parsed = parse_roster_csv(raw)
        self.assertEqual((parsed.period_start, parsed.period_end), (date(2026, 10, 1), date(2026, 10, 3)))
        self.assertEqual(parsed.month_label, 'Oktober 2026')
        self.assertEqual(parsed.department, 'Führungsdienst')
        self.assertEqual(parsed.plan_status, 'vorläufig')
        self.assertEqual(parsed.persons[0], ('Müller, Anna', ['A1', '-', 'BÜ']))
        self.assertEqual(parsed.persons[2][1], ['CT', 'CTF', 'A1'])
        self.assertEqual(parsed.codes, ['-', 'A1', 'B', 'BÜ', 'CT', 'CTF', 'U'])
        self.assertEqual(parsed.warnings, [])

    def test_rejects_wrong_day_count_and_garbage(self):
        raw = build_csv(date(2026, 10, 1), {'Müller, Anna': ['A1', '-', 'BÜ']})
        raw = raw.replace(b'01.10.2026 - 03.10.2026', b'01.10.2026 - 04.10.2026')
        with self.assertRaises(RosterFormatError):
            parse_roster_csv(raw)
        with self.assertRaises(RosterFormatError):
            parse_roster_csv(b'Name;Datum\nMueller;2026-10-01\n')

    def test_real_export_if_present(self):
        if not os.path.exists(SAMPLE):
            self.skipTest('Musterdatei nicht vorhanden')
        with open(SAMPLE, 'rb') as f:
            parsed = parse_roster_csv(f.read())
        self.assertEqual(len(parsed.days), 31)
        self.assertGreater(len(parsed.persons), 30)
        # Plausibilität: pro Tag genau ein A1, A2 und B
        for code in ('A1', 'A2', 'B'):
            for i in range(31):
                self.assertEqual(sum(1 for _, cs in parsed.persons if cs[i] == code), 1, f'{code} Tag {i + 1}')


@override_settings(MEDIA_ROOT='/tmp/claude-1000/-var-www-lager-resqware-de/dienstplan-test-media')
class ImportFlowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='plan', password='pw')
        self.user.user_permissions.add(*Permission.objects.filter(content_type__app_label='dienstplan'))
        self.client.force_login(self.user)
        self.today = timezone.localdate()

    def _upload(self, persons, start=None, status='vorläufig'):
        raw = build_csv(start or self.today, persons, status=status)
        response = self.client.post(reverse('dienstplan:upload'), {
            'file': SimpleUploadedFile('Export.csv', raw, content_type='text/csv'),
        })
        upload = RosterUpload.objects.latest('uploaded_at')
        self.assertRedirects(response, reverse('dienstplan:upload_preview', args=[upload.pk]))
        return upload

    def test_upload_preview_confirm_and_replace(self):
        upload = self._upload({'Müller, Anna': ['A1', '-', 'XY'], 'Schmidt, Ben': ['B', 'A1', 'B'], 'Weber, Cem': ['CT', 'B', 'A1']})
        self.assertEqual(upload.status, UploadStatus.PENDING)
        response = self.client.get(reverse('dienstplan:upload_preview', args=[upload.pk]))
        self.assertContains(response, 'Müller, Anna')
        self.assertContains(response, 'unbekannt')  # XY
        self.assertContains(response, 'jeden Tag genau 1')  # A1
        self.assertEqual(RosterEntry.objects.count(), 0)

        response = self.client.post(reverse('dienstplan:upload_confirm', args=[upload.pk]))
        self.assertRedirects(response, reverse('dienstplan:dashboard'))
        upload.refresh_from_db()
        self.assertEqual(upload.status, UploadStatus.IMPORTED)
        self.assertEqual(RosterEntry.objects.count(), 9)
        self.assertTrue(DutyCode.objects.filter(code='XY', verified=False).exists())
        self.assertEqual(services.fuehrungsdienst_for(self.today), {'a1': ['Müller, Anna'], 'b': ['Schmidt, Ben'], 'c': ['Weber, Cem']})
        self.assertEqual(services.fuehrungsdienst_for(self.today + timedelta(days=1)), {'a1': ['Schmidt, Ben'], 'b': ['Weber, Cem']})

        # Dashboard zeigt den Führungsdienst von heute
        response = self.client.get(reverse('dienstplan:dashboard'))
        self.assertContains(response, 'Müller, Anna')
        self.assertContains(response, 'aktuell')

        # Aktualisierter Export für denselben Zeitraum ersetzt den Stand
        second = self._upload({'Müller, Anna': ['B', '-', '-'], 'Schmidt, Ben': ['A1', 'A1', 'A1']}, status='genehmigt')
        self.client.post(reverse('dienstplan:upload_confirm', args=[second.pk]))
        upload.refresh_from_db(); second.refresh_from_db()
        self.assertEqual(upload.status, UploadStatus.REPLACED)
        self.assertEqual(second.status, UploadStatus.IMPORTED)
        self.assertEqual(upload.entries.count(), 0)
        self.assertEqual(services.fuehrungsdienst_for(self.today), {'a1': ['Schmidt, Ben'], 'b': ['Müller, Anna']})
        self.assertEqual(RosterUpload.objects.filter(status=UploadStatus.IMPORTED).count(), 1)

        # Monatsansicht
        response = self.client.get(reverse('dienstplan:month'), {'year': self.today.year, 'month': self.today.month})
        self.assertContains(response, 'Schmidt, Ben')
        response = self.client.get(reverse('dienstplan:month'), {'year': self.today.year, 'month': self.today.month, 'nur': 'fuehrung'})
        self.assertContains(response, 'Schmidt, Ben')

    def test_filters_in_preview_and_month(self):
        upload = self._upload({'Müller, Anna': ['A1', '-', 'BÜ'], 'Schmidt, Ben': ['B', 'A1', 'U'], 'Weber, Cem': ['CT', 'CTF', 'A1']})
        url = reverse('dienstplan:upload_preview', args=[upload.pk])
        response = self.client.get(url, {'name': 'schmidt'})
        self.assertContains(response, 'Schmidt, Ben')
        self.assertNotContains(response, 'Müller, Anna')
        self.assertContains(response, '1 von 3 Personen')
        response = self.client.get(url, {'code': 'CT'})
        self.assertContains(response, 'Weber, Cem')
        self.assertNotContains(response, 'Schmidt, Ben')
        self.assertNotContains(response, 'title="C-Dienst (Freitag)"')  # andere Codes der Person ausgeblendet
        response = self.client.get(url, {'name': 'niemand'})
        self.assertContains(response, 'Keine Person passt zum Filter')

        self.client.post(reverse('dienstplan:upload_confirm', args=[upload.pk]))
        month = {'year': self.today.year, 'month': self.today.month}
        response = self.client.get(reverse('dienstplan:month'), {**month, 'code': 'A1', 'name': 'weber'})
        self.assertContains(response, 'Weber, Cem')
        self.assertNotContains(response, 'Müller, Anna')
        self.assertNotContains(response, '>CT<')

    def test_stats_view_csv_and_permission(self):
        from django.contrib.auth.models import Group
        from dienstplan import roles
        upload = self._upload({'Müller, Anna': ['A1', 'A1', 'BÜ'], 'Schmidt, Ben': ['B', 'B', 'A1'], 'Weber, Cem': ['CT', 'CTF', 'CW']})
        self.client.post(reverse('dienstplan:upload_confirm', args=[upload.pk]))
        response = self.client.get(reverse('dienstplan:stats'))
        self.assertEqual(response.status_code, 200)
        rows = {r['name']: r for r in response.context['persons']}
        functions = [key for key, _ in response.context['functions']]
        self.assertEqual(rows['Müller, Anna']['counts'][functions.index('a1')], 2)
        self.assertEqual(rows['Schmidt, Ben']['counts'][functions.index('b')], 2)
        self.assertEqual(rows['Schmidt, Ben']['total'], 3)
        self.assertEqual(rows['Weber, Cem']['counts'][functions.index('c')], 3)
        self.assertEqual(sum(rows['Weber, Cem']['weekday_counts']), 3)
        self.assertEqual(response.context['total_all'], 8)
        # Nur eine Funktion
        response = self.client.get(reverse('dienstplan:stats'), {'funktion': 'a1'})
        names = [r['name'] for r in response.context['persons']]
        self.assertEqual(names, ['Müller, Anna', 'Schmidt, Ben'])
        # CSV
        response = self.client.get(reverse('dienstplan:stats'), {'export': 'csv'})
        self.assertEqual(response['Content-Type'], 'text/csv; charset=utf-8')
        self.assertIn('Müller, Anna;', response.content.decode('utf-8-sig'))
        # Rechte: Leser ohne Statistik-Zusatz sieht die Auswertung nicht, mit Zusatz schon
        reader = User.objects.create_user(username='leser', password='pw')
        roles.set_level(reader, 'view')
        self.client.force_login(reader)
        self.assertEqual(self.client.get(reverse('dienstplan:dashboard')).status_code, 200)
        self.assertEqual(self.client.get(reverse('dienstplan:stats')).status_code, 403)
        self.assertEqual(self.client.post(reverse('dienstplan:upload'), {}).status_code, 403)
        roles.set_level(reader, 'view', stats=True)
        reader = User.objects.get(pk=reader.pk)
        self.client.force_login(reader)
        self.assertEqual(self.client.get(reverse('dienstplan:stats')).status_code, 200)
        self.assertEqual(roles.group_level(reader), 'view')
        self.assertTrue(roles.has_stats_group(reader))
        roles.set_level(reader, 'none', stats=False)
        self.assertEqual(roles.group_level(reader), 'none')
        self.assertFalse(Group.objects.get(name='Dienstplan Statistik').user_set.filter(pk=reader.pk).exists())

    def test_user_management_card_sets_level(self):
        from core.models import SystemSettings
        settings_obj = SystemSettings.load(); settings_obj.dienstplan_enabled = True; settings_obj.save()
        admin = User.objects.create_superuser(username='root', password='pw', email='r@x.de')
        target = User.objects.create_user(username='ziel', password='pw')
        self.client.force_login(admin)
        response = self.client.get(reverse('core:user_detail', args=[target.pk]))
        self.assertContains(response, 'name="dienstplan_level"')
        response = self.client.post(reverse('core:user_dienstplan_permissions', args=[target.pk]),
                                    {'dienstplan_level': 'edit', 'dienstplan_stats': '1'})
        self.assertRedirects(response, reverse('core:user_detail', args=[target.pk]))
        target = User.objects.get(pk=target.pk)
        self.assertTrue(target.has_perm('dienstplan.dienstplan_edit'))
        self.assertTrue(target.has_perm('dienstplan.dienstplan_stats'))
        self.assertFalse(target.has_perm('dienstplan.delete_rosterupload'))

    def test_day_view(self):
        upload = self._upload({'Müller, Anna': ['A1', '-', 'BÜ'], 'Schmidt, Ben': ['B', 'A1', 'U'], 'Weber, Cem': ['U', 'CTF', 'A1']})
        self.client.post(reverse('dienstplan:upload_confirm', args=[upload.pk]))
        response = self.client.get(reverse('dienstplan:day'))  # heute
        self.assertEqual(response.status_code, 200)
        functions = dict(response.context['functions'])
        self.assertEqual(functions['A1-Dienst'], ['Müller, Anna'])
        self.assertEqual(functions['B-Dienst'], ['Schmidt, Ben'])
        groups = {g['code'].code: g['names'] for g in response.context['groups']}
        self.assertEqual(groups['U'], ['Weber, Cem'])
        self.assertContains(response, 'Urlaub')
        tomorrow = (self.today + timedelta(days=1)).isoformat()
        response = self.client.get(reverse('dienstplan:day'), {'datum': tomorrow, 'name': 'schmidt'})
        functions = dict(response.context['functions'])
        self.assertEqual(functions['A1-Dienst'], ['Schmidt, Ben'])
        self.assertEqual(functions['C-Dienst'], [])  # Weber vom Namensfilter ausgeblendet
        response = self.client.get(reverse('dienstplan:day'), {'datum': '2001-01-01'})
        self.assertContains(response, 'liegt kein Dienstplan vor')
        self.assertEqual(self.client.get(reverse('dienstplan:day'), {'datum': 'kaputt'}).status_code, 200)

    def test_bad_file_is_rejected_with_message(self):
        response = self.client.post(reverse('dienstplan:upload'), {
            'file': SimpleUploadedFile('x.csv', b'a;b;c\n1;2;3\n', content_type='text/csv'),
        }, follow=True)
        self.assertContains(response, 'Import abgelehnt')
        self.assertEqual(RosterUpload.objects.count(), 0)

    def test_code_edit_and_permissions(self):
        code = DutyCode.objects.get(code='A1')
        response = self.client.post(reverse('dienstplan:code_edit', args=[code.pk]), {
            'code': 'A1', 'label': 'A1-Dienst (Einsatzleitung)', 'kind': 'duty', 'function': 'a1', 'color': 'red',
            'show_on_monitor': 'on', 'verified': 'on', 'sort_order': 10,
        })
        self.assertRedirects(response, reverse('dienstplan:code_list'))
        code.refresh_from_db()
        self.assertTrue(code.verified)
        viewer = User.objects.create_user(username='viewer', password='pw')
        self.client.force_login(viewer)
        self.assertEqual(self.client.get(reverse('dienstplan:dashboard')).status_code, 403)

    def test_widget_shows_plan(self):
        from core.models import SystemSettings
        from info_monitors.models import Dashboard, MonitorProfile, Widget
        settings_obj = SystemSettings.load()
        settings_obj.dienstplan_enabled = True
        settings_obj.save()
        upload = self._upload({'Müller, Anna': ['A1', 'A1', 'A1'], 'Schmidt, Ben': ['B', 'B', 'B'], 'Weber, Cem': ['LD', 'LDS', 'LD']})
        self.client.post(reverse('dienstplan:upload_confirm', args=[upload.pk]))

        # Info-Monitor-Widget (heute und Woche)
        profile = MonitorProfile.objects.create(name='Wache', created_by=self.user, updated_by=self.user)
        dashboard = Dashboard.objects.create(profile=profile, name='Plan', is_public=True, created_by=self.user, updated_by=self.user)
        dashboard.allowed_users.add(self.user)
        widget = Widget.objects.create(dashboard=dashboard, title='Führungsdienst', widget_type='dienstplan',
                                       config={'mode': 'today', 'functions': ['a1', 'b']}, created_by=self.user, updated_by=self.user)
        response = self.client.get(dashboard.get_kiosk_url())
        self.assertContains(response, 'Müller, Anna')
        self.assertContains(response, 'Schmidt, Ben')
        self.assertNotContains(response, 'Weber, Cem')  # Lagedienst nicht ausgewählt
        widget.config = {'mode': 'week', 'functions': []}
        widget.save()
        response = self.client.get(dashboard.get_kiosk_url())
        self.assertContains(response, 'Weber, Cem')
        # Widget-Bearbeiten speichert Optionen
        response = self.client.post(reverse('info_monitors:widget_edit', args=[widget.pk]), {
            'title': 'FD', 'mode': 'week', 'functions': ['a1', 'lagedienst'],
        })
        widget.refresh_from_db()
        self.assertEqual(widget.config['functions'], ['a1', 'lagedienst'])
