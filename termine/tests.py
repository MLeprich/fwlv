from datetime import date, time, timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from . import services
from .models import Event, EventCategory, Recurrence

User = get_user_model()


class ServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='t', password='pw')
        self.cat = EventCategory.objects.get(name='Übung')

    def _event(self, **kwargs):
        kwargs.setdefault('category', self.cat)
        kwargs.setdefault('created_by', self.user)
        kwargs.setdefault('updated_by', self.user)
        return Event.objects.create(**kwargs)

    def test_default_categories_seeded(self):
        self.assertGreaterEqual(EventCategory.objects.count(), 6)

    def test_occurrences_single_multiday_and_recurring(self):
        self._event(title='Übung', start_date=date(2026, 10, 5), all_day=False, start_time=time(19, 0))
        self._event(title='Lehrgang', start_date=date(2026, 10, 7), end_date=date(2026, 10, 9))
        self._event(title='Dienstbesprechung', start_date=date(2026, 10, 1), recurrence=Recurrence.WEEKLY,
                    recurrence_until=date(2026, 10, 20))
        self._event(title='Jahreshauptversammlung', start_date=date(2025, 3, 15), recurrence=Recurrence.YEARLY)
        self._event(title='Monatlich 31.', start_date=date(2026, 1, 31), recurrence=Recurrence.MONTHLY)
        items = services.occurrences(date(2026, 10, 1), date(2026, 10, 31))
        titles = [(o.title, o.start) for o in items]
        self.assertIn(('Übung', date(2026, 10, 5)), titles)
        self.assertIn(('Lehrgang', date(2026, 10, 7)), titles)
        self.assertEqual([s for t, s in titles if t == 'Dienstbesprechung'],
                         [date(2026, 10, 1), date(2026, 10, 8), date(2026, 10, 15)])
        self.assertEqual([s for t, s in titles if t == 'Monatlich 31.'], [date(2026, 10, 31)])
        self.assertNotIn('Jahreshauptversammlung', [t for t, _ in titles])
        march = services.occurrences(date(2027, 3, 1), date(2027, 3, 31))
        self.assertEqual([o.start for o in march if o.title == 'Jahreshauptversammlung'], [date(2027, 3, 15)])
        # Mehrtägiger Termin berührt den Bereich nur mit seinem Ende
        self.assertEqual([o.title for o in services.occurrences(date(2026, 10, 9), date(2026, 10, 9))], ['Lehrgang'])
        days = services.group_by_day(items, date(2026, 10, 7), date(2026, 10, 9))
        self.assertTrue(all(any(o.title == 'Lehrgang' for o in d['items']) for d in days))

    def test_filters_and_ics_roundtrip(self):
        from locations.models import Location
        site = Location.objects.create(name='Wache 1', code='W1', location_type='site', created_by=self.user, updated_by=self.user)
        e = self._event(title='Nur Wache 1', start_date=date(2026, 11, 2), is_public=False, location='Halle')
        e.sites.add(site)
        self._event(title='Für alle', start_date=date(2026, 11, 3), is_public=True, show_on_monitor=True,
                    all_day=False, start_time=time(18, 30), end_time=time(20, 0), description='Zeile 1\nZeile 2')
        rng = (date(2026, 11, 1), date(2026, 11, 30))
        self.assertEqual([o.title for o in services.occurrences(*rng, sites=[site.pk])], ['Nur Wache 1', 'Für alle'])
        other = Location.objects.create(name='Wache 2', code='W2', location_type='site', created_by=self.user, updated_by=self.user)
        self.assertEqual([o.title for o in services.occurrences(*rng, sites=[other.pk])], ['Für alle'])
        self.assertEqual([o.title for o in services.occurrences(*rng, public_only=True)], ['Für alle'])
        self.assertEqual([o.title for o in services.occurrences(*rng, query='halle')], ['Nur Wache 1'])
        ics = services.export_ics(services.occurrences(*rng))
        self.assertIn('BEGIN:VEVENT', ics)
        self.assertIn('DTSTART;VALUE=DATE:20261102', ics)
        self.assertIn('DTSTART:20261103T183000', ics)
        self.assertIn('DESCRIPTION:Zeile 1\\nZeile 2', ics)
        parsed = services.parse_ics(ics)
        self.assertEqual(len(parsed), 2)
        self.assertEqual(parsed[0]['title'], 'Nur Wache 1')
        self.assertTrue(parsed[0]['all_day'])
        self.assertIsNone(parsed[0]['end_date'])
        self.assertEqual((parsed[1]['start_time'], parsed[1]['end_time']), (time(18, 30), time(20, 0)))
        self.assertEqual(parsed[1]['description'], 'Zeile 1\nZeile 2')
        with self.assertRaises(services.IcsFormatError):
            services.parse_ics(b'kein kalender')


class ViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='kal', password='pw')
        self.user.user_permissions.add(*Permission.objects.filter(content_type__app_label='termine'))
        self.client.force_login(self.user)
        self.cat = EventCategory.objects.get(name='Übung')
        self.today = timezone.localdate()

    def test_calendar_list_create_edit_delete(self):
        response = self.client.get(reverse('termine:calendar'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Nächste 14 Tage')
        response = self.client.post(reverse('termine:event_create'), {
            'title': 'Atemschutzübung', 'category': self.cat.pk, 'start_date': self.today.isoformat(), 'end_date': '',
            'all_day': '', 'start_time': '19:00', 'end_time': '21:00', 'location': 'Wache 1', 'description': 'Bitte PSA',
            'recurrence': 'none', 'recurrence_until': '', 'show_on_monitor': 'on',
        })
        event = Event.objects.get(title='Atemschutzübung')
        self.assertRedirects(response, event.get_absolute_url())
        self.assertEqual(event.created_by, self.user)
        self.assertEqual(event.time_display, '19:00–21:00 Uhr')
        response = self.client.get(reverse('termine:calendar'))
        self.assertContains(response, 'Atemschutzübung')
        response = self.client.get(reverse('termine:list'))
        self.assertContains(response, 'Atemschutzübung')
        response = self.client.get(reverse('termine:list'), {'q': 'gibtesnicht'})
        self.assertNotContains(response, 'Atemschutzübung')
        # Validierung: Uhrzeit fehlt, Ende vor Beginn
        response = self.client.post(reverse('termine:event_create'), {
            'title': 'Kaputt', 'category': self.cat.pk, 'start_date': self.today.isoformat(),
            'end_date': (self.today - timedelta(days=1)).isoformat(), 'all_day': '', 'recurrence': 'none',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Event.objects.filter(title='Kaputt').exists())
        # Bearbeiten und Löschen
        response = self.client.post(reverse('termine:event_edit', args=[event.pk]), {
            'title': 'Atemschutzübung Zug 2', 'category': self.cat.pk, 'start_date': self.today.isoformat(),
            'all_day': 'on', 'recurrence': 'weekly', 'recurrence_until': (self.today + timedelta(days=30)).isoformat(),
            'show_on_monitor': 'on',
        })
        event.refresh_from_db()
        self.assertEqual(event.title, 'Atemschutzübung Zug 2')
        self.assertTrue(event.all_day)
        self.assertIsNone(event.start_time)
        response = self.client.get(event.get_absolute_url())
        self.assertContains(response, 'Nächste Vorkommen')
        response = self.client.post(reverse('termine:event_delete', args=[event.pk]))
        self.assertRedirects(response, reverse('termine:calendar'))
        self.assertFalse(Event.objects.exists())

    def test_permissions_levels(self):
        from . import roles
        reader = User.objects.create_user(username='leser', password='pw')
        roles.set_level(reader, 'view')
        self.client.force_login(reader)
        self.assertEqual(self.client.get(reverse('termine:calendar')).status_code, 200)
        self.assertEqual(self.client.get(reverse('termine:event_create')).status_code, 403)
        self.assertEqual(self.client.get(reverse('termine:category_list')).status_code, 403)
        roles.set_level(reader, 'edit')
        reader = User.objects.get(pk=reader.pk)
        self.client.force_login(reader)
        self.assertEqual(self.client.get(reverse('termine:event_create')).status_code, 200)
        self.assertEqual(self.client.get(reverse('termine:ics_import')).status_code, 403)
        self.assertEqual(roles.group_level(reader), 'edit')

    def test_ics_export_import_and_categories(self):
        Event.objects.create(title='Export mich', category=self.cat, start_date=self.today + timedelta(days=3),
                             created_by=self.user, updated_by=self.user)
        response = self.client.get(reverse('termine:ics_export'))
        self.assertEqual(response['Content-Type'], 'text/calendar; charset=utf-8')
        self.assertIn('SUMMARY:Export mich', response.content.decode())
        ics = ('BEGIN:VCALENDAR\r\nVERSION:2.0\r\nBEGIN:VEVENT\r\nUID:abc-1\r\nSUMMARY:Importiert\r\n'
               'DTSTART;VALUE=DATE:20261205\r\nDTEND;VALUE=DATE:20261207\r\nLOCATION:Rathaus\r\nEND:VEVENT\r\nEND:VCALENDAR\r\n')
        data = {'file': SimpleUploadedFile('k.ics', ics.encode(), content_type='text/calendar'),
                'category': self.cat.pk, 'show_on_monitor': 'on'}
        response = self.client.post(reverse('termine:ics_import'), data)
        self.assertRedirects(response, reverse('termine:calendar'))
        event = Event.objects.get(uid='abc-1')
        self.assertEqual((event.start_date, event.end_date), (date(2026, 12, 5), date(2026, 12, 6)))
        self.assertEqual(event.location, 'Rathaus')
        # Erneuter Import mit gleicher UID aktualisiert statt dupliziert
        data['file'] = SimpleUploadedFile('k.ics', ics.replace('Rathaus', 'Feuerwache').encode(), content_type='text/calendar')
        self.client.post(reverse('termine:ics_import'), data)
        self.assertEqual(Event.objects.filter(uid='abc-1').count(), 1)
        self.assertEqual(Event.objects.get(uid='abc-1').location, 'Feuerwache')
        # Kategorie anlegen
        response = self.client.post(reverse('termine:category_create'), {'name': 'Brandschutzerziehung', 'color': 'green', 'icon': '🧯', 'sort_order': 25, 'is_active': 'on'})
        self.assertRedirects(response, reverse('termine:category_list'))
        self.assertTrue(EventCategory.objects.filter(name='Brandschutzerziehung').exists())

    def test_widget_dashboard_tile_and_user_card(self):
        from core.models import SystemSettings
        from info_monitors.models import Dashboard, MonitorProfile, Widget
        s = SystemSettings.load(); s.termine_enabled = True; s.save()
        Event.objects.create(title='Öffentlich', category=self.cat, start_date=self.today + timedelta(days=1), is_public=True,
                             created_by=self.user, updated_by=self.user)
        Event.objects.create(title='Intern', category=self.cat, start_date=self.today + timedelta(days=2), is_public=False,
                             created_by=self.user, updated_by=self.user)
        Event.objects.create(title='Nicht auf Monitor', category=self.cat, start_date=self.today, show_on_monitor=False,
                             created_by=self.user, updated_by=self.user)
        profile = MonitorProfile.objects.create(name='Wache', created_by=self.user, updated_by=self.user)
        dashboard = Dashboard.objects.create(profile=profile, name='Halle', is_public=True, created_by=self.user, updated_by=self.user)
        dashboard.allowed_users.add(self.user)
        widget = Widget.objects.create(dashboard=dashboard, title='Termine', widget_type='kalender', config={'days': '14'},
                                       created_by=self.user, updated_by=self.user)
        html = self.client.get(dashboard.get_kiosk_url()).content.decode()
        self.assertIn('Öffentlich', html)
        self.assertNotIn('>🚒 Intern<', html)
        self.assertNotIn('Nicht auf Monitor', html)
        dashboard.is_public = False
        dashboard.save()
        html = self.client.get(dashboard.get_kiosk_url()).content.decode()
        self.assertIn('Intern', html)
        # Widget-Optionen speichern
        response = self.client.post(reverse('info_monitors:widget_edit', args=[widget.pk]),
                                    {'title': 'Termine', 'days': '30', 'limit': '5', 'categories': [str(self.cat.pk)]})
        widget.refresh_from_db()
        self.assertEqual(widget.config['days'], '30')
        self.assertEqual(widget.config['categories'], [str(self.cat.pk)])
        # Haupt-Dashboard-Kachel
        response = self.client.get(reverse('core:dashboard'))
        self.assertContains(response, 'Nächste Termine')
        self.assertContains(response, 'Intern')
        # Benutzerverwaltung
        admin = User.objects.create_superuser(username='root', password='pw', email='r@x.de')
        target = User.objects.create_user(username='ziel', password='pw')
        self.client.force_login(admin)
        self.assertContains(self.client.get(reverse('core:user_detail', args=[target.pk])), 'name="termine_level"')
        self.client.post(reverse('core:user_termine_permissions', args=[target.pk]), {'termine_level': 'manage'})
        target = User.objects.get(pk=target.pk)
        self.assertTrue(target.has_perm('termine.termine_manage'))
