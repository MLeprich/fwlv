import io
import json
import zipfile
from datetime import date, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse

from objektverwaltung.models import BuildingObject

from . import services, tiles
from .models import Hazard, HazardStatus, HazardType, MapConfig

User = get_user_model()


def _building(user, number, name, street, house, lat=None, lng=None, city='Oberhausen'):
    return BuildingObject.objects.create(
        object_number=number, name=name, street=street, house_number=house, city=city,
        latitude=lat, longitude=lng, created_by=user, updated_by=user,
    )


class ServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='t', password='pw')
        self.b12 = _building(self.user, 'O-1', 'Schule', 'Hauptstraße', '12', 51.4960, 6.8630)
        self.b13 = _building(self.user, 'O-2', 'Kita', 'Hauptstr.', '13a', 51.4961, 6.8631)
        self.b40 = _building(self.user, 'O-3', 'Halle', 'Haupt-Strasse', '40')
        self.other = _building(self.user, 'O-4', 'Rathaus', 'Marktplatz', '1', 51.5100, 6.9000)
        self.far = _building(self.user, 'O-5', 'Feuerwache', 'Hauptstraße', '12', city='Essen')

    def test_street_normalization_and_house_numbers(self):
        self.assertEqual(services.normalize_street('Haupt-Straße 12'), 'hauptstr')
        self.assertEqual(services.normalize_street('Hauptstr.'), 'hauptstr')
        self.assertEqual(services.house_number('13a'), 13)
        self.assertEqual(services.house_number('12-14'), 12)
        self.assertIsNone(services.house_number(''))

    def _hazard(self, **kwargs):
        kwargs.setdefault('title', 'Baustelle')
        kwargs.setdefault('start_date', date.today())
        kwargs.setdefault('created_by', self.user)
        kwargs.setdefault('updated_by', self.user)
        return Hazard.objects.create(**kwargs)

    def test_affected_by_house_range_and_side(self):
        h = self._hazard(street='Hauptstraße', house_from=10, house_to=20, city='Oberhausen')
        names = sorted(a['object'].name for a in services.affected_objects(h))
        self.assertEqual(names, ['Kita', 'Schule'])  # 40 außerhalb, Essen anderer Ort
        h.house_side = 'even'
        self.assertEqual([a['object'].name for a in services.affected_objects(h)], ['Schule'])
        h.house_side = 'odd'
        self.assertEqual([a['object'].name for a in services.affected_objects(h)], ['Kita'])
        # Ganze Straße ohne Hausnummern
        h2 = self._hazard(street='hauptstrasse', city='')
        self.assertEqual(sorted(a['object'].name for a in services.affected_objects(h2)),
                         ['Feuerwache', 'Halle', 'Kita', 'Schule'])

    def test_affected_by_radius_polygon_and_line(self):
        h = self._hazard(latitude=51.4960, longitude=6.8630, radius_m=50)
        self.assertEqual(sorted(a['object'].name for a in services.affected_objects(h)), ['Kita', 'Schule'])
        h.radius_m = 5
        self.assertEqual([a['object'].name for a in services.affected_objects(h)], ['Schule'])
        poly = self._hazard(geometry={'type': 'polygon', 'coords': [[51.50, 6.89], [51.52, 6.89], [51.52, 6.91], [51.50, 6.91]]})
        self.assertEqual([a['object'].name for a in services.affected_objects(poly)], ['Rathaus'])
        line = self._hazard(geometry={'type': 'line', 'coords': [[51.4960, 6.8600], [51.4960, 6.8660]]})
        self.assertEqual(sorted(a['object'].name for a in services.affected_objects(line)), ['Kita', 'Schule'])

    def test_effective_status_and_current(self):
        today = date.today()
        planned = self._hazard(title='geplant', start_date=today + timedelta(days=3))
        expired = self._hazard(title='abgelaufen', start_date=today - timedelta(days=10), end_date=today - timedelta(days=1))
        ended = self._hazard(title='beendet', status=HazardStatus.ENDED)
        active = self._hazard(title='aktiv', end_date=today)
        self.assertEqual(planned.effective_status, 'planned')
        self.assertEqual(expired.effective_status, 'ended')
        self.assertEqual(ended.effective_status, 'ended')
        self.assertEqual(active.effective_status, 'active')
        self.assertEqual(sorted(h.title for h in services.current_hazards()), ['aktiv', 'geplant'])
        self.assertEqual([h.title for h in services.current_hazards(include_planned=False)], ['aktiv'])

    def test_hazards_for_building(self):
        self._hazard(title='Sperrung', street='Hauptstraße', house_from=1, house_to=20)
        self._hazard(title='alt', street='Hauptstraße', status=HazardStatus.ENDED)
        hits = services.hazards_for_building(self.b12)
        self.assertEqual([h['hazard'].title for h in hits], ['Sperrung'])
        self.assertEqual(services.hazards_for_building(self.other), [])

    def test_location_display(self):
        h = Hazard(street='Hauptstraße', house_from=12, house_to=40, house_side='even', city='Oberhausen')
        self.assertEqual(h.location_display, 'Hauptstraße 12–40 (nur gerade Hausnummern), Oberhausen')
        self.assertEqual(Hazard(street='Marktplatz', house_from=1).location_display, 'Marktplatz 1')


class ViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='modul', password='pw')
        self.user.user_permissions.add(*Permission.objects.filter(
            content_type__app_label='einsatzvorbereitung', codename__in=['einsatz_view', 'einsatz_edit']))
        self.user.user_permissions.add(Permission.objects.get(codename='view_buildingobject'))
        self.client.force_login(self.user)
        self.school = _building(self.user, 'O-1', 'Schule', 'Hauptstraße', '12', 51.4960, 6.8630)
        from core.models import SystemSettings
        s = SystemSettings.load()
        s.einsatzvorbereitung_enabled = True
        s.objektverwaltung_enabled = True
        s.save()

    def _post_data(self, **extra):
        data = {'title': 'Kanalbau', 'hazard_type': 'baustelle', 'status': 'active',
                'start_date': date.today().isoformat(), 'end_date': '', 'description': '',
                'street': 'Hauptstraße', 'house_from': '1', 'house_to': '20', 'house_side': 'both', 'city': '',
                'latitude': '', 'longitude': '', 'radius_m': '', 'geometry': '',
                'detour': 'über Nebenstraße', 'hydrants_note': '', 'leitstelle_note': 'Bitte Alarmplan prüfen',
                'contact_name': '', 'contact_phone': '', 'source': 'VAO 12/26', 'internal_notes': '',
                'access_restricted': 'on', 'show_on_monitor': 'on'}
        data.update(extra)
        return data

    def test_create_with_geometry_and_detail(self):
        geometry = json.dumps({'type': 'line', 'coords': [[51.4960, 6.8600], [51.4960, 6.8660]]})
        response = self.client.post(reverse('einsatzvorbereitung:create'),
                                    self._post_data(latitude='51.496', longitude='6.863', radius_m='100', geometry=geometry))
        hazard = Hazard.objects.get()
        self.assertRedirects(response, hazard.get_absolute_url())
        self.assertEqual(hazard.geometry['type'], 'line')
        self.assertEqual(hazard.created_by, self.user)
        response = self.client.get(hazard.get_absolute_url())
        self.assertContains(response, 'Kanalbau')
        self.assertContains(response, 'Betroffene Objekte (1)')
        self.assertContains(response, 'Schule')
        self.assertContains(response, 'Adresse im Bereich')
        self.assertContains(response, 'hazard-map')
        # Listenansicht zählt betroffene Objekte, Karte liefert Daten
        response = self.client.get(reverse('einsatzvorbereitung:list'))
        self.assertContains(response, 'Kanalbau')
        self.assertContains(response, 'Zufahrt eingeschränkt')
        data = self.client.get(reverse('einsatzvorbereitung:map_data')).json()
        self.assertEqual(data['hazards'][0]['affected'], 1)
        self.assertEqual(data['hazards'][0]['point'], [51.496, 6.863])
        self.assertEqual(len(data['objects']), 1)

    def test_invalid_form(self):
        response = self.client.post(reverse('einsatzvorbereitung:create'), self._post_data(
            house_from='30', house_to='10', end_date='2020-01-01'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'kleiner als die erste')
        self.assertContains(response, 'vor dem Beginn')
        self.assertFalse(Hazard.objects.exists())

    def test_end_note_and_permissions(self):
        self.client.post(reverse('einsatzvorbereitung:create'), self._post_data())
        hazard = Hazard.objects.get()
        response = self.client.post(reverse('einsatzvorbereitung:note_add', args=[hazard.pk]), {'text': 'Leitstelle: Kenntnis genommen'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(hazard.notes_log.count(), 1)
        response = self.client.post(reverse('einsatzvorbereitung:end', args=[hazard.pk]))
        hazard.refresh_from_db()
        self.assertEqual(hazard.status, HazardStatus.ENDED)
        self.assertEqual(hazard.end_date, date.today())
        # Löschen nur mit manage
        self.assertEqual(self.client.get(reverse('einsatzvorbereitung:delete', args=[hazard.pk])).status_code, 403)
        self.assertEqual(self.client.get(reverse('einsatzvorbereitung:settings')).status_code, 403)
        # Nur-Leser: kein Anlegen, aber Rückmeldung
        self.user.user_permissions.remove(Permission.objects.get(codename='einsatz_edit'))
        self.assertEqual(self.client.get(reverse('einsatzvorbereitung:create')).status_code, 403)
        response = self.client.get(hazard.get_absolute_url())
        self.assertContains(response, 'Rückmeldung speichern')
        self.assertNotContains(response, reverse('einsatzvorbereitung:edit', args=[hazard.pk]))

    def test_object_detail_shows_hazard(self):
        self.client.post(reverse('einsatzvorbereitung:create'), self._post_data())
        response = self.client.get(self.school.get_absolute_url())
        self.assertContains(response, 'Aktuelle Gefahrenstellen im Umfeld (1)')
        self.assertContains(response, 'Kanalbau')

    def test_map_settings(self):
        self.user.user_permissions.add(Permission.objects.get(codename='einsatz_manage'))
        response = self.client.post(reverse('einsatzvorbereitung:settings'), {
            'center_lat': '51.5', 'center_lng': '6.86', 'zoom': '13', 'min_zoom': '11', 'max_zoom': '16',
            'bbox': '51.44,6.78,51.56,6.95', 'attribution': 'Test', 'show_objects': 'on'})
        self.assertRedirects(response, reverse('einsatzvorbereitung:settings'))
        self.assertEqual(MapConfig.load().max_zoom, 16)
        response = self.client.get(reverse('einsatzvorbereitung:settings'))
        self.assertContains(response, 'tiles_download --bbox 51.44,6.78,51.56,6.95 --zoom 11-16')
        self.assertContains(response, 'ca. ')

    def test_widget_tag(self):
        from django.template import Context, Template
        self.client.post(reverse('einsatzvorbereitung:create'), self._post_data())

        class W:
            config = {'limit': 5}
            title = ''
        html = Template('{% load einsatz_tags %}{% gefahren_widget w as d %}{{ d.count }}|{{ d.restricted }}|{{ d.items.0.title }}').render(Context({'w': W()}))
        self.assertEqual(html, '1|1|Kanalbau')
        html = Template('{% include "info_monitors/widgets/gefahrenstellen.html" with widget=w %}').render(Context({'w': W()}))
        self.assertIn('Zufahrt für Einsatzfahrzeuge eingeschränkt', html)
        self.assertIn('Bitte Alarmplan prüfen', html)

    def test_leitstelle_notification(self):
        from notifications.models import Notification
        lst = User.objects.create_user(username='lst', password='pw')
        group, _ = Group.objects.get_or_create(name='LST Infomonitor')
        lst.groups.add(group)
        self.client.post(reverse('einsatzvorbereitung:create'), self._post_data())
        self.assertEqual(Notification.objects.filter(recipient=lst, title__startswith='Neue Gefahrenstelle').count(), 1)

    def test_sidebar_and_module_toggle(self):
        response = self.client.get(reverse('einsatzvorbereitung:list'))
        self.assertContains(response, 'Einsatzvorbereitung')
        self.assertContains(response, reverse('einsatzvorbereitung:map'))


class TileTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='t', password='pw')
        self.client.force_login(self.user)

    def test_tile_math_and_count(self):
        self.assertEqual(tiles.deg2num(51.5, 6.86, 0), (0, 0))
        x, y = tiles.deg2num(51.4963, 6.8637, 13)
        self.assertEqual((x, y), (4252, 2724))
        self.assertGreater(tiles.count_tiles([51.44, 6.78, 51.56, 6.95], range(11, 15)), 20)

    def test_tile_view_placeholder_and_import(self):
        with TemporaryDirectory() as tmp:
            with override_settings(OFFLINE_TILES_DIR=tmp):
                response = self.client.get(reverse('einsatzvorbereitung:tile', args=[13, 4252, 2724]))
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response['X-Tile-Missing'], '1')
                # ZIP mit einer Kachel und einer Fremddatei einspielen
                zip_path = Path(tmp) / 'kacheln.zip'
                with zipfile.ZipFile(zip_path, 'w') as zf:
                    zf.writestr('13/4252/2724.png', b'\x89PNG-test')
                    zf.writestr('../evil.png', b'x')
                    zf.writestr('readme.txt', b'x')
                out = io.StringIO()
                call_command('tiles_import', str(zip_path), stdout=out)
                self.assertIn('1 Kacheln eingespielt', out.getvalue())
                response = self.client.get(reverse('einsatzvorbereitung:tile', args=[13, 4252, 2724]))
                self.assertFalse(response.has_header('X-Tile-Missing'))
                self.assertEqual(b''.join(response.streaming_content), b'\x89PNG-test')
                status = tiles.tiles_status()
                self.assertEqual(status['total'], 1)
                self.assertEqual(status['zooms'], [(13, 1)])
                # Download nur zählen (kein Netz nötig)
                out = io.StringIO()
                call_command('tiles_download', '--bbox', '51.49,6.86,51.50,6.87', '--zoom', '13-14', '--dry-run', stdout=out)
                self.assertIn('Kacheln', out.getvalue())

    def test_tile_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse('einsatzvorbereitung:tile', args=[13, 4252, 2724]))
        self.assertEqual(response.status_code, 302)


class RoleTests(TestCase):
    def test_setup_command_and_levels(self):
        from . import roles
        out = io.StringIO()
        call_command('setup_einsatzvorbereitung_permissions', stdout=out)
        self.assertIn('Fertig', out.getvalue())
        user = User.objects.create_user(username='u', password='pw')
        roles.set_level(user, 'edit')
        self.assertEqual(roles.group_level(user), 'edit')
        user = User.objects.get(pk=user.pk)
        self.assertTrue(user.has_perm('einsatzvorbereitung.einsatz_edit'))
        self.assertFalse(user.has_perm('einsatzvorbereitung.einsatz_manage'))
        roles.set_level(user, 'none')
        self.assertEqual(roles.group_level(User.objects.get(pk=user.pk)), 'none')


class HandoverTests(TestCase):
    """Übergabeliste für die Leitstelle: Punkte entstehen automatisch, werden zusammengefasst und abgehakt."""

    def setUp(self):
        self.user = User.objects.create_user(username='modul', password='pw')
        self.user.user_permissions.add(*Permission.objects.filter(
            content_type__app_label='einsatzvorbereitung', codename__in=['einsatz_view', 'einsatz_edit']))
        self.user.user_permissions.add(*Permission.objects.filter(
            content_type__app_label='objektverwaltung', codename__in=['view_buildingobject', 'add_buildingobject', 'change_buildingobject']))
        self.client.force_login(self.user)
        self.building = _building(self.user, 'O-1', 'Schule', 'Hauptstraße', '12')
        from core.models import SystemSettings
        s = SystemSettings.load()
        s.einsatzvorbereitung_enabled = True
        s.save()

    def _open(self):
        from .models import HandoverItem, HandoverStatus
        return list(HandoverItem.objects.filter(status=HandoverStatus.OPEN).order_by('pk'))

    def test_contact_lifecycle_merges_and_cleans_up(self):
        from objektverwaltung.models import BuildingContact
        # Neu
        self.client.post(reverse('objektverwaltung:add_contact', args=[self.building.pk]), {
            'name': 'Erna Muster', 'role': 'Hausmeisterin', 'phone': '0208-1', 'mobile': '', 'email': '', 'notes': ''})
        items = self._open()
        self.assertEqual([i.kind for i in items], ['contact_new'])
        self.assertIn('Schule: Erna Muster', items[0].title)
        self.assertIn('Tel. 0208-1', items[0].details)
        contact = BuildingContact.objects.get()
        # Änderung vor der Übergabe: bleibt EIN Punkt („neu“), Inhalt aktualisiert
        self.client.post(reverse('objektverwaltung:edit_contact', args=[contact.pk]), {
            'name': 'Erna Muster', 'role': 'Hausmeisterin', 'phone': '0208-2', 'mobile': '', 'email': '', 'notes': ''})
        items = self._open()
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].kind, 'contact_new')
        # Löschen vor Übergabe: Punkt verschwindet ganz
        self.client.post(reverse('objektverwaltung:delete_contact', args=[contact.pk]))
        self.assertEqual(self._open(), [])

    def test_change_after_done_creates_changed_item_and_collects(self):
        from objektverwaltung.models import BuildingContact
        self.client.post(reverse('objektverwaltung:add_contact', args=[self.building.pk]), {
            'name': 'Erna', 'role': '', 'phone': '1', 'mobile': '', 'email': '', 'notes': ''})
        item = self._open()[0]
        response = self.client.post(reverse('einsatzvorbereitung:handover_done', args=[item.pk]), {'note': 'im ELS eingetragen'})
        self.assertEqual(response.status_code, 302)
        item.refresh_from_db()
        self.assertTrue(item.is_done)
        self.assertEqual(item.done_by, self.user)
        self.assertEqual(item.done_note, 'im ELS eingetragen')
        contact = BuildingContact.objects.get()
        for phone in ('2', '3'):
            self.client.post(reverse('objektverwaltung:edit_contact', args=[contact.pk]), {
                'name': 'Erna', 'role': '', 'phone': phone, 'mobile': '', 'email': '', 'notes': ''})
        items = self._open()
        self.assertEqual([i.kind for i in items], ['contact_changed'])
        self.assertIn('Telefon: 1 → 2', items[0].details)
        self.assertIn('Telefon: 2 → 3', items[0].details)
        # Entfernen nach Übergabe → eigener Punkt „entfernt“, der offene „geändert“-Punkt entfällt
        self.client.post(reverse('objektverwaltung:delete_contact', args=[contact.pk]))
        self.assertEqual([i.kind for i in self._open()], ['contact_deleted'])

    def test_bmz_fsd_object_and_hazard_items(self):
        self.client.post(reverse('objektverwaltung:add_fire_alarm_panel', args=[self.building.pk]), {
            'designation': 'BMZ Haupteingang', 'location_description': 'EG', 'manufacturer': '', 'model': '',
            'inspection_interval_months': 12, 'last_inspection': '', 'notes': ''})
        self.client.post(reverse('objektverwaltung:add_key_depot', args=[self.building.pk]), {
            'depot_type': 'fsd3', 'designation': 'FSD Nord', 'location_description': '', 'manufacturer': '',
            'serial_number': '4711', 'installed_at': '', 'contents': '', 'inspection_interval_months': 12,
            'last_inspection': '', 'is_active': 'on', 'notes': ''})
        kinds = [i.kind for i in self._open()]
        self.assertIn('bmz_new', kinds)
        self.assertIn('fsd_new', kinds)
        # Objekt-Änderung: nur relevante Felder
        data = {'object_number': 'O-1', 'name': 'Schule', 'status': 'active', 'street': 'Hauptstraße', 'house_number': '12',
                'postal_code': '', 'city': 'Oberhausen', 'floor_count': '', 'basement_count': '', 'notes': 'nur intern'}
        self.client.post(reverse('objektverwaltung:update', args=[self.building.pk]), data)
        self.assertNotIn('object_changed', [i.kind for i in self._open()])  # Hinweise sind nicht leitstellenrelevant
        data['house_number'] = '14'
        self.client.post(reverse('objektverwaltung:update', args=[self.building.pk]), data)
        changed = [i for i in self._open() if i.kind == 'object_changed']
        self.assertEqual(len(changed), 1)
        self.assertIn('Hausnummer: 12 → 14', changed[0].details)
        # Gefahrenstelle mit Zufahrtseinschränkung → dringend; Beenden → eigener Punkt
        self.client.post(reverse('einsatzvorbereitung:create'), {
            'title': 'Sperrung', 'hazard_type': 'sperrung', 'status': 'active', 'start_date': date.today().isoformat(),
            'end_date': '', 'description': '', 'street': 'Hauptstraße', 'house_from': '', 'house_to': '',
            'house_side': 'both', 'city': '', 'latitude': '', 'longitude': '', 'radius_m': '', 'geometry': '',
            'detour': '', 'hydrants_note': '', 'leitstelle_note': '', 'contact_name': '', 'contact_phone': '',
            'source': '', 'internal_notes': '', 'access_restricted': 'on', 'show_on_monitor': 'on'})
        hazard = Hazard.objects.get()
        item = [i for i in self._open() if i.kind == 'hazard_new'][0]
        self.assertTrue(item.urgent)
        self.assertIn('Zufahrt für Einsatzfahrzeuge eingeschränkt', item.details)
        self.client.post(reverse('einsatzvorbereitung:handover_done', args=[item.pk]))
        self.client.post(reverse('einsatzvorbereitung:end', args=[hazard.pk]))
        self.assertEqual([i.kind for i in self._open() if i.hazard_id == hazard.pk], ['hazard_ended'])

    def test_list_bulk_and_pdf(self):
        for n in ('A', 'B', 'C'):
            self.client.post(reverse('objektverwaltung:add_contact', args=[self.building.pk]), {
                'name': n, 'role': '', 'phone': '', 'mobile': '', 'email': '', 'notes': ''})
        response = self.client.get(reverse('einsatzvorbereitung:handover'))
        self.assertContains(response, 'Schule: A')
        self.assertContains(response, 'Leitstellen-Übergabe')
        self.assertContains(response, 'Ausgewählte als erledigt markieren')
        ids = [i.pk for i in self._open()[:2]]
        response = self.client.post(reverse('einsatzvorbereitung:handover_bulk_done'), {'ids': ids, 'note': 'ELS'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(self._open()), 1)
        response = self.client.get(reverse('einsatzvorbereitung:handover'), {'status': 'erledigt'})
        self.assertContains(response, '„ELS“')
        self.assertContains(response, 'Wieder öffnen')
        response = self.client.get(reverse('einsatzvorbereitung:handover_pdf'))
        self.assertEqual(response['Content-Type'], 'application/pdf')
        # Zähler in der Modul-Navigation und im Widget
        response = self.client.get(reverse('einsatzvorbereitung:list'))
        self.assertContains(response, 'Leitstellen-Übergabe')
        from django.template import Context, Template

        class W:
            config = {}
            title = ''
        html = Template('{% include "info_monitors/widgets/gefahrenstellen.html" with widget=w %}').render(Context({'w': W()}))
        self.assertIn('1 offene Übergabepunkte', html)
