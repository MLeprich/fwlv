from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from .models import BuildingContact, BuildingObject, BuildingPlan, Floor

User = get_user_model()


class EditChildViewTests(TestCase):
    """Bearbeiten von Unterobjekten (Ansprechpartner, Etagen, Pläne …) auf der Objekt-Detailseite."""

    def setUp(self):
        self.user = User.objects.create_user(username='modul', password='pw')
        self.user.user_permissions.add(
            *Permission.objects.filter(content_type__app_label='objektverwaltung',
                                       codename__in=['view_buildingobject', 'change_buildingobject'])
        )
        self.client.force_login(self.user)
        self.building = BuildingObject.objects.create(
            object_number='OBJ-1', name='Rathaus', created_by=self.user, updated_by=self.user,
        )
        self.contact = BuildingContact.objects.create(
            building=self.building, name='Alt', role='Hausmeister', phone='1', mobile='', email='',
        )

    def test_detail_shows_edit_links(self):
        response = self.client.get(self.building.get_absolute_url())
        self.assertContains(response, reverse('objektverwaltung:edit_contact', args=[self.contact.pk]))

    def test_edit_contact_get_prefills_form(self):
        response = self.client.get(reverse('objektverwaltung:edit_contact', args=[self.contact.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'value="Alt"')
        self.assertContains(response, 'Ansprechpartner bearbeiten')

    def test_edit_contact_post_updates_and_redirects(self):
        response = self.client.post(reverse('objektverwaltung:edit_contact', args=[self.contact.pk]), {
            'name': 'Neu', 'role': 'Betreiber', 'phone': '0208-1', 'mobile': '0170-1',
            'email': 'neu@example.de', 'is_primary': 'on', 'notes': '',
        })
        self.assertRedirects(response, self.building.get_absolute_url())
        self.contact.refresh_from_db()
        self.assertEqual(self.contact.name, 'Neu')
        self.assertEqual(self.contact.mobile, '0170-1')
        self.assertTrue(self.contact.is_primary)
        self.assertEqual(self.contact.building, self.building)

    def test_edit_contact_invalid_shows_errors(self):
        response = self.client.post(reverse('objektverwaltung:edit_contact', args=[self.contact.pk]), {
            'name': '', 'role': '', 'phone': '', 'mobile': '', 'email': 'keine-mail', 'notes': '',
        })
        self.assertEqual(response.status_code, 200)
        self.contact.refresh_from_db()
        self.assertEqual(self.contact.name, 'Alt')

    def test_edit_requires_change_permission(self):
        self.user.user_permissions.clear()
        self.user.user_permissions.add(Permission.objects.get(codename='view_buildingobject'))
        response = self.client.get(reverse('objektverwaltung:edit_contact', args=[self.contact.pk]))
        self.assertEqual(response.status_code, 403)
        response = self.client.get(self.building.get_absolute_url())
        self.assertNotContains(response, reverse('objektverwaltung:edit_contact', args=[self.contact.pk]))

    def test_edit_floor_duplicate_level_shows_form_error(self):
        Floor.objects.create(building=self.building, level=0, name='EG')
        og = Floor.objects.create(building=self.building, level=1, name='1. OG')
        response = self.client.post(reverse('objektverwaltung:edit_floor', args=[og.pk]), {
            'level': 0, 'name': '1. OG', 'description': '',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'existiert bereits', msg_prefix=response.content.decode()[:0])
        og.refresh_from_db()
        self.assertEqual(og.level, 1)

    def test_edit_plan_keeps_file_and_sets_updated_by(self):
        other = User.objects.create_user(username='other', password='pw')
        plan = BuildingPlan.objects.create(
            building=self.building, title='Laufkarte EG', plan_type='laufkarte',
            file=SimpleUploadedFile('lk.pdf', b'%PDF-1.4', content_type='application/pdf'),
            created_by=other, updated_by=other,
        )
        response = self.client.post(reverse('objektverwaltung:edit_plan', args=[plan.pk]), {
            'plan_type': 'feuerwehrplan', 'title': 'Feuerwehrplan gesamt', 'floor': '', 'notes': 'neu',
        })
        self.assertRedirects(response, self.building.get_absolute_url())
        plan.refresh_from_db()
        self.assertEqual(plan.title, 'Feuerwehrplan gesamt')
        self.assertEqual(plan.plan_type, 'feuerwehrplan')
        self.assertTrue(plan.file.name.endswith('.pdf'))
        self.assertEqual(plan.updated_by, self.user)
        self.assertEqual(plan.created_by, other)

    def test_all_edit_pages_render(self):
        from .models import CompensationMeasure, EscapeRoute, FireAlarmPanel, FireSuppressionSystem
        floor = Floor.objects.create(building=self.building, level=0, name='EG')
        route = EscapeRoute.objects.create(building=self.building, floor=floor, name='West')
        bmz = FireAlarmPanel.objects.create(building=self.building, designation='BMZ 1')
        system = FireSuppressionSystem.objects.create(building=self.building, designation='Sprinkler')
        measure = CompensationMeasure.objects.create(
            building=self.building, title='Wache', escape_route=route, suppression_system=system,
        )
        plan = BuildingPlan.objects.create(
            building=self.building, title='LK', file=SimpleUploadedFile('a.pdf', b'%PDF'),
            created_by=self.user, updated_by=self.user,
        )
        for name, obj in [('edit_floor', floor), ('edit_escape_route', route), ('edit_fire_alarm_panel', bmz),
                          ('edit_suppression', system), ('edit_compensation', measure), ('edit_plan', plan),
                          ('edit_contact', self.contact)]:
            response = self.client.get(reverse(f'objektverwaltung:{name}', args=[obj.pk]))
            self.assertEqual(response.status_code, 200, name)
            self.assertContains(response, 'Speichern')


class FireKeyDepotTests(TestCase):
    """Feuerwehrschlüsseldepots: Intervalle, Prüfberichte, PDF."""

    def setUp(self):
        self.user = User.objects.create_user(username='modul', password='pw', first_name='Max', last_name='Prüfer')
        self.user.user_permissions.add(
            *Permission.objects.filter(content_type__app_label='objektverwaltung',
                                       codename__in=['view_buildingobject', 'change_buildingobject'])
        )
        self.client.force_login(self.user)
        self.building = BuildingObject.objects.create(
            object_number='OBJ-7', name='Rathaus', street='Schwartzstr.', house_number='72',
            postal_code='46045', city='Oberhausen', created_by=self.user, updated_by=self.user,
        )

    def _depot(self, **kwargs):
        from .models import FireKeyDepot
        defaults = dict(building=self.building, depot_type='fsd3', designation='FSD Haupteingang',
                        inspection_interval_months=12, contents='1x Generalhauptschlüssel')
        defaults.update(kwargs)
        return FireKeyDepot.objects.create(**defaults)

    def test_add_months_and_next_inspection(self):
        from datetime import date
        from .models import add_months
        self.assertEqual(add_months(date(2026, 1, 31), 1), date(2026, 2, 28))
        self.assertEqual(add_months(date(2026, 11, 15), 3), date(2027, 2, 15))
        depot = self._depot(last_inspection=date(2026, 3, 10))
        self.assertEqual(depot.next_inspection, date(2027, 3, 10))
        depot = self._depot(designation='FSD 2', installed_at=date(2026, 1, 1), inspection_interval_months=6)
        self.assertEqual(depot.next_inspection, date(2026, 7, 1))
        depot = self._depot(designation='FSD 3')
        self.assertIsNone(depot.next_inspection)
        self.assertEqual(depot.inspection_status, 'unknown')

    def test_inspection_status(self):
        from datetime import timedelta
        from django.utils import timezone
        today = timezone.localdate()
        overdue = self._depot(last_inspection=today - timedelta(days=400))
        soon = self._depot(designation='b', last_inspection=today - timedelta(days=350))
        ok = self._depot(designation='c', last_inspection=today - timedelta(days=10))
        self.assertEqual(overdue.inspection_status, 'overdue')
        self.assertEqual(soon.inspection_status, 'due_soon')
        self.assertEqual(ok.inspection_status, 'ok')
        response = self.client.get(reverse('objektverwaltung:keydepot_list') + '?status=due')
        self.assertContains(response, 'FSD Haupteingang')
        self.assertContains(response, '>b<', html=False)
        self.assertNotContains(response, '>c<')
        response = self.client.get(reverse('objektverwaltung:dashboard'))
        self.assertContains(response, 'Fällige FSD-Prüfungen')

    def test_add_depot_via_detail_and_report_updates_dates(self):
        from datetime import date
        from .models import FireKeyDepot, FSDInspectionReport
        response = self.client.post(reverse('objektverwaltung:add_key_depot', args=[self.building.pk]), {
            'depot_type': 'fsd1', 'designation': 'FSD Tor Nord', 'location_description': '', 'manufacturer': '',
            'serial_number': '4711', 'installed_at': '', 'inspection_interval_months': 12,
            'last_inspection': '', 'contents': '2x Torschlüssel', 'is_active': 'on', 'notes': '',
        })
        self.assertRedirects(response, self.building.get_absolute_url())
        depot = FireKeyDepot.objects.get(serial_number='4711')
        self.assertEqual(depot.building, self.building)

        # Neuer Prüfbericht: Vorbelegung + Datumsfortschreibung
        response = self.client.get(reverse('objektverwaltung:fsd_report_add', args=[depot.pk]))
        self.assertContains(response, '2x Torschlüssel')
        self.assertContains(response, 'Max Prüfer')
        response = self.client.post(reverse('objektverwaltung:fsd_report_add', args=[depot.pk]), {
            'inspection_date': '2026-08-15', 'participant_operator': 'Hr. Meier', 'participant_fire_dept': 'Max Prüfer',
            'participant_other': '', 'depot_contents': '2x Torschlüssel\n1x GHS', 'condition_report': 'Alles in Ordnung',
            'result': 'ok', 'keys_match': 'on',
        })
        self.assertRedirects(response, depot.get_absolute_url())
        depot.refresh_from_db()
        self.assertEqual(depot.last_inspection, date(2026, 8, 15))
        self.assertEqual(depot.next_inspection, date(2027, 8, 15))
        report = FSDInspectionReport.objects.get()
        self.assertEqual(report.created_by, self.user)

        # Löschen des Berichts setzt die Daten zurück
        self.client.post(reverse('objektverwaltung:fsd_report_delete', args=[report.pk]))
        depot.refresh_from_db()
        self.assertIsNone(depot.last_inspection)
        self.assertIsNone(depot.next_inspection)

    def test_detail_pages_render(self):
        from datetime import date
        from .models import FSDInspectionReport
        depot = self._depot(last_inspection=date(2026, 3, 10))
        report = FSDInspectionReport.objects.create(
            depot=depot, inspection_date=date(2026, 3, 10), result='defects',
            condition_report='Schloss schwergängig', created_by=self.user, updated_by=self.user,
        )
        response = self.client.get(self.building.get_absolute_url())
        self.assertContains(response, 'Feuerwehrschlüsseldepots (1)')
        response = self.client.get(depot.get_absolute_url())
        self.assertContains(response, 'Mit Mängeln')
        self.assertContains(response, reverse('objektverwaltung:fsd_report_pdf', args=[report.pk]))
        response = self.client.get(reverse('objektverwaltung:fsd_report_edit', args=[report.pk]))
        self.assertContains(response, 'Schloss schwergängig')
        response = self.client.get(reverse('objektverwaltung:edit_key_depot', args=[depot.pk]))
        self.assertEqual(response.status_code, 200)

    def test_pdf_generation(self):
        import os
        from datetime import date
        from .models import FSDInspectionReport
        depot = self._depot(last_inspection=date(2026, 3, 10), location_description='Rechts neben Haupteingang')
        report = FSDInspectionReport.objects.create(
            depot=depot, inspection_date=date(2026, 3, 10), participant_operator='Hr. Meier (Hausmeister)',
            participant_fire_dept='Max Prüfer', depot_contents='1x Generalhauptschlüssel\n1x Torschlüssel Nord\n1x Schlüssel BMZ',
            condition_report='Depot unbeschädigt, Schloss leichtgängig.\nSchlüssel vollständig.',
            created_by=self.user, updated_by=self.user,
        )
        out_dir = os.environ.get('FSD_PDF_OUT')
        response = self.client.get(reverse('objektverwaltung:fsd_report_pdf', args=[report.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn('FSD-Pruefbericht_OBJ-7_2026-03-10.pdf', response['Content-Disposition'])
        self.assertTrue(response.content.startswith(b'%PDF'))
        if out_dir:
            open(os.path.join(out_dir, 'bericht.pdf'), 'wb').write(response.content)
        response = self.client.get(reverse('objektverwaltung:keydepot_blank_pdf', args=[depot.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertIn('_leer.pdf', response['Content-Disposition'])
        if out_dir:
            open(os.path.join(out_dir, 'leer.pdf'), 'wb').write(response.content)

    def test_view_only_user_cannot_add_report(self):
        depot = self._depot()
        self.user.user_permissions.clear()
        self.user.user_permissions.add(Permission.objects.get(codename='view_buildingobject'))
        self.assertEqual(self.client.get(depot.get_absolute_url()).status_code, 200)
        self.assertEqual(self.client.get(reverse('objektverwaltung:fsd_report_add', args=[depot.pk])).status_code, 403)
        self.assertEqual(self.client.get(reverse('objektverwaltung:keydepot_blank_pdf', args=[depot.pk])).status_code, 200)


class DetailTabTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='modul', password='pw')
        self.user.user_permissions.add(
            *Permission.objects.filter(content_type__app_label='objektverwaltung',
                                       codename__in=['view_buildingobject', 'change_buildingobject'])
        )
        self.client.force_login(self.user)
        self.building = BuildingObject.objects.create(
            object_number='OBJ-1', name='Rathaus', created_by=self.user, updated_by=self.user,
        )

    def test_detail_has_tabs(self):
        response = self.client.get(self.building.get_absolute_url())
        for label in ('Übersicht', 'Gebäude', 'Brandschutztechnik', 'Kompensation', 'Pläne &amp; Laufkarten'):
            self.assertContains(response, label)

    def test_add_and_delete_redirect_to_active_tab(self):
        response = self.client.post(reverse('objektverwaltung:add_floor', args=[self.building.pk]), {
            'level': 0, 'name': 'EG', 'description': '', 'tab': 'gebaeude',
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], self.building.get_absolute_url() + '#gebaeude')
        floor = Floor.objects.get()
        response = self.client.post(reverse('objektverwaltung:edit_floor', args=[floor.pk]), {
            'level': 0, 'name': 'Erdgeschoss', 'description': '', 'tab': 'gebaeude',
        })
        self.assertEqual(response['Location'], self.building.get_absolute_url() + '#gebaeude')
        response = self.client.post(reverse('objektverwaltung:delete_floor', args=[floor.pk]), {'tab': 'unbekannt'})
        self.assertEqual(response['Location'], self.building.get_absolute_url())


class AkteTests(TestCase):
    """e-Akte: Audit-Einträge, Zeitleiste, PDF-Auszug."""

    def setUp(self):
        self.user = User.objects.create_user(username='modul', password='pw', first_name='Max', last_name='Prüfer')
        self.user.user_permissions.add(
            *Permission.objects.filter(content_type__app_label='objektverwaltung',
                                       codename__in=['view_buildingobject', 'change_buildingobject',
                                                     'add_buildingobject', 'delete_buildingobject'])
        )
        self.client.force_login(self.user)
        self.building = BuildingObject.objects.create(
            object_number='OBJ-9', name='Schule', city='Oberhausen', created_by=self.user, updated_by=self.user,
        )

    def _akte(self):
        from .akte import build_timeline
        return build_timeline(self.building)

    def test_child_create_update_delete_are_logged_with_diff(self):
        from audit.models import AuditLog
        self.client.post(reverse('objektverwaltung:add_contact', args=[self.building.pk]), {
            'name': 'Hr. Meier', 'role': 'Hausmeister', 'phone': '1', 'mobile': '', 'email': '', 'notes': '',
        })
        contact = BuildingContact.objects.get()
        self.client.post(reverse('objektverwaltung:edit_contact', args=[contact.pk]), {
            'name': 'Hr. Meier', 'role': 'Betreiber', 'phone': '1', 'mobile': '0170', 'email': '', 'notes': '',
        })
        self.client.post(reverse('objektverwaltung:delete_contact', args=[contact.pk]))

        logs = AuditLog.objects.filter(extra_data__building_id=self.building.pk).order_by('timestamp')
        self.assertEqual([l.action for l in logs], ['create', 'update', 'delete'])
        update = logs[1]
        self.assertEqual(update.changes['Funktion'], {'old': 'Hausmeister', 'new': 'Betreiber'})
        self.assertEqual(update.changes['Mobil'], {'old': '–', 'new': '0170'})
        self.assertNotIn('Name', update.changes)
        self.assertEqual(update.user, self.user)

        entries = self._akte()
        # 3 Audit-Einträge + Anlage-Anker (kein CREATE-Log für das Objekt selbst)
        self.assertEqual(len(entries), 4)
        self.assertEqual(entries[0]['action'], 'delete')
        self.assertEqual(entries[-1]['title'], 'Objekt im System angelegt')

    def test_building_update_logs_changes_and_unchanged_save_logs_nothing(self):
        from audit.models import AuditLog
        data = {
            'object_number': 'OBJ-9', 'name': 'Schule', 'usage_type': 'other', 'street': '', 'house_number': '',
            'postal_code': '', 'city': 'Oberhausen', 'latitude': '', 'longitude': '', 'floor_count': '',
            'basement_count': '', 'has_fire_alarm_system': '', 'notes': '', 'is_active': 'on',
        }
        self.client.post(reverse('objektverwaltung:update', args=[self.building.pk]), data)
        self.assertEqual(AuditLog.objects.count(), 0)
        data['name'] = 'Gesamtschule'
        data['has_fire_alarm_system'] = 'on'
        self.client.post(reverse('objektverwaltung:update', args=[self.building.pk]), data)
        log = AuditLog.objects.get()
        self.assertEqual(log.action, 'update')
        self.assertEqual(log.changes['Bezeichnung'], {'old': 'Schule', 'new': 'Gesamtschule'})
        self.assertEqual(log.changes['Brandmeldeanlage vorhanden'], {'old': 'Nein', 'new': 'Ja'})

    def test_fsd_report_appears_once_as_pruefung(self):
        from datetime import date
        from .models import FireKeyDepot
        depot = FireKeyDepot.objects.create(building=self.building, designation='FSD Tor', inspection_interval_months=12)
        self.client.post(reverse('objektverwaltung:fsd_report_add', args=[depot.pk]), {
            'inspection_date': '2026-08-15', 'participant_operator': '', 'participant_fire_dept': 'Max',
            'participant_other': '', 'depot_contents': '', 'condition_report': 'i.O.', 'result': 'ok', 'keys_match': 'on',
        })
        entries = self._akte()
        pruefungen = [e for e in entries if e['kind'] == 'pruefung']
        self.assertEqual(len(pruefungen), 1)
        self.assertIn('FSD-Prüfung „FSD Tor“', pruefungen[0]['title'])
        self.assertEqual(pruefungen[0]['when'].date(), date(2026, 8, 15))

    def test_akte_tab_and_pdf(self):
        from audit.models import AuditLog
        response = self.client.get(self.building.get_absolute_url())
        self.assertContains(response, 'Objekt im System angelegt')
        self.assertContains(response, reverse('objektverwaltung:akte_pdf', args=[self.building.pk]))
        response = self.client.get(reverse('objektverwaltung:akte_pdf', args=[self.building.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertTrue(response.content.startswith(b'%PDF'))
        self.assertEqual(AuditLog.objects.filter(action='export').count(), 1)

    def test_building_delete_is_logged(self):
        from audit.models import AuditLog
        self.client.post(reverse('objektverwaltung:delete', args=[self.building.pk]))
        self.assertFalse(BuildingObject.objects.filter(pk=self.building.pk).exists())
        log = AuditLog.objects.get()
        self.assertEqual(log.action, 'delete')
        self.assertIn('Schule', log.object_repr)


class SearchTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='modul', password='pw')
        self.user.user_permissions.add(Permission.objects.get(codename='view_buildingobject'))
        self.client.force_login(self.user)
        self.a = BuildingObject.objects.create(object_number='A-1', name='Rathaus', created_by=self.user, updated_by=self.user)
        self.b = BuildingObject.objects.create(object_number='B-2', name='Bahnhof', created_by=self.user, updated_by=self.user)
        BuildingContact.objects.create(building=self.a, name='Frau Hermosin', role='Hausmeisterin')
        from .models import FireKeyDepot, FireAlarmPanel, CompensationMeasure
        from datetime import date
        FireKeyDepot.objects.create(building=self.b, designation='FSD Ost', serial_number='SN-4711',
                                    inspection_interval_months=12, last_inspection=date(2020, 1, 1))
        FireAlarmPanel.objects.create(building=self.a, designation='BMZ Foyer')
        CompensationMeasure.objects.create(building=self.a, title='Wache', status='active')

    def test_global_search_finds_children(self):
        response = self.client.get(reverse('core:global_search'), {'q': 'hermosin'})
        self.assertContains(response, 'Frau Hermosin')
        self.assertContains(response, 'Ansprechpartner - Rathaus')
        response = self.client.get(reverse('core:global_search'), {'q': 'SN-4711'})
        self.assertContains(response, 'Schlüsseldepot - Bahnhof')
        response = self.client.get(reverse('core:global_search'), {'q': 'foyer'})
        self.assertContains(response, 'Brandmeldezentrale - Rathaus')

    def test_list_search_over_children_and_filters(self):
        url = reverse('objektverwaltung:list')
        response = self.client.get(url, {'q': 'hermosin'})
        self.assertContains(response, 'Rathaus')
        self.assertNotContains(response, 'Bahnhof')
        response = self.client.get(url, {'filter': 'fsd_due'})
        self.assertContains(response, 'Bahnhof')
        self.assertNotContains(response, 'Rathaus')
        response = self.client.get(url, {'filter': 'komp'})
        self.assertContains(response, 'Komp. 1')
        self.assertNotContains(response, 'Bahnhof')
        response = self.client.get(url, {'filter': 'bmz'})
        self.assertContains(response, 'BMZ 1')
        # Objekt mit zwei passenden Kindern erscheint nur einmal
        BuildingContact.objects.create(building=self.a, name='Herr Hermosin')
        response = self.client.get(url, {'q': 'hermosin'})
        self.assertEqual(response.content.decode().count('>Rathaus<'), 1)
