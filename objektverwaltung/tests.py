from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from .models import BuildingContact, BuildingObject, BuildingPlan, Floor, UsageCategory

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
        self.assertContains(response, 'Fällige Prüfungen')

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
        self.assertContains(response, reverse('objektverwaltung:report_pdf', args=[report.pk]))
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
            'object_number': 'OBJ-9', 'name': 'Schule', 'usage_type': '', 'street': '', 'house_number': '',
            'postal_code': '', 'city': 'Oberhausen', 'latitude': '', 'longitude': '', 'floor_count': '',
            'basement_count': '', 'has_fire_alarm_system': '', 'notes': '', 'status': 'active',
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
        self.assertIn('Feuerwehrschlüsseldepot „FSD Tor“ geprüft', pruefungen[0]['title'])
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
        response = self.client.get(url, {'filter': 'due'})
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

    def test_list_sorting_and_address_columns(self):
        url = reverse('objektverwaltung:list')
        self.a.street, self.a.house_number, self.a.postal_code, self.a.city = 'Zeppelinstraße', '3', '46049', 'Oberhausen'
        self.a.save()
        self.b.street, self.b.house_number, self.b.postal_code, self.b.city = 'Am Bahnhof', '1', '45127', 'Essen'
        self.b.save()
        # Standard: nach Name aufsteigend -> Bahnhof vor Rathaus; Adresse wird angezeigt
        html = self.client.get(url).content.decode()
        self.assertLess(html.index('>Bahnhof<'), html.index('>Rathaus<'))
        self.assertIn('Zeppelinstraße 3', html)
        self.assertIn('46049 Oberhausen', html)
        # absteigend nach Name
        html = self.client.get(url, {'sort': 'name', 'dir': 'desc'}).content.decode()
        self.assertLess(html.index('>Rathaus<'), html.index('>Bahnhof<'))
        # nach Ort aufsteigend: Essen (Bahnhof) vor Oberhausen (Rathaus)
        html = self.client.get(url, {'sort': 'city'}).content.decode()
        self.assertLess(html.index('>Bahnhof<'), html.index('>Rathaus<'))
        # nach Straße absteigend: Zeppelinstraße (Rathaus) vor Am Bahnhof
        html = self.client.get(url, {'sort': 'street', 'dir': 'desc'}).content.decode()
        self.assertLess(html.index('>Rathaus<'), html.index('>Bahnhof<'))
        # unbekannter Sortierschlüssel fällt auf Name zurück, kein Fehler
        response = self.client.get(url, {'sort': 'evil', 'dir': 'x'})
        self.assertEqual(response.status_code, 200)
        # Sortierung bleibt in Filter-Links erhalten, Suche findet Adresse
        html = self.client.get(url, {'sort': 'city', 'dir': 'desc', 'q': '45127'}).content.decode()
        self.assertIn('>Bahnhof<', html)
        self.assertNotIn('>Rathaus<', html)
        self.assertIn('name="sort" value="city"', html)
        self.assertIn('name="dir" value="desc"', html)



class GenericInspectionTests(TestCase):
    """Prüfungen für BMZ und Löschanlagen, zentraler Einstieg, Übersicht."""

    def setUp(self):
        self.user = User.objects.create_user(username='modul', password='pw', first_name='Max', last_name='Prüfer')
        self.user.user_permissions.add(
            *Permission.objects.filter(content_type__app_label='objektverwaltung',
                                       codename__in=['view_buildingobject', 'change_buildingobject'])
        )
        self.client.force_login(self.user)
        self.building = BuildingObject.objects.create(
            object_number='OBJ-3', name='Halle', created_by=self.user, updated_by=self.user,
        )

    def test_bmz_report_via_central_entry(self):
        from datetime import date
        from .models import FireAlarmPanel, InspectionReport
        bmz = FireAlarmPanel.objects.create(building=self.building, designation='BMZ Foyer',
                                            inspection_interval_months=36)
        self.assertIsNone(bmz.next_inspection)
        # Schritt 1+2: Objekt und Art wählen
        response = self.client.get(reverse('objektverwaltung:inspection_new'), {'building': self.building.pk, 'type': 'bmz'})
        add_url = reverse('objektverwaltung:report_add', args=['bmz', bmz.pk])
        self.assertContains(response, 'BMZ Foyer')
        self.assertContains(response, add_url)
        # Formular ohne FSD-Felder
        response = self.client.get(add_url)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Depot-Inhalt')
        self.assertNotContains(response, 'Schließanlage')
        # Schritt 3: Bericht speichern
        response = self.client.post(add_url, {
            'inspection_date': '2026-06-01', 'participant_operator': '', 'participant_fire_dept': 'Max',
            'participant_other': '', 'condition_report': 'Melder geprüft, ÜE i.O.', 'result': 'ok',
        })
        self.assertRedirects(response, bmz.get_absolute_url())
        report = InspectionReport.objects.get()
        self.assertEqual(report.inspection_type, 'bmz')
        self.assertEqual(report.building, self.building)
        self.assertEqual(report.fire_alarm_panel, bmz)
        self.assertIsNone(report.depot)
        bmz.refresh_from_db()
        self.assertEqual(bmz.last_inspection, date(2026, 6, 1))
        self.assertEqual(bmz.next_inspection, date(2029, 6, 1))
        # PDF (generisches Layout) und Anlagen-Detailseite
        response = self.client.get(reverse('objektverwaltung:report_pdf', args=[report.pk]))
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn('BMZ-Pruefbericht_OBJ-3_2026-06-01.pdf', response['Content-Disposition'])
        response = self.client.get(bmz.get_absolute_url())
        self.assertContains(response, 'Brandmeldezentrale')
        self.assertContains(response, '01.06.2026')
        # Akte
        response = self.client.get(self.building.get_absolute_url())
        self.assertContains(response, 'Brandmeldezentrale „BMZ Foyer“ geprüft')

    def test_suppression_interval_and_manual_next_date(self):
        from datetime import date
        from .models import FireSuppressionSystem
        # Ohne letzte Prüfung bleibt ein manuell gesetzter Termin erhalten
        sys_ = FireSuppressionSystem.objects.create(building=self.building, designation='Sprinkler',
                                                    next_inspection=date(2027, 1, 1))
        self.assertEqual(sys_.next_inspection, date(2027, 1, 1))
        sys_.last_inspection = date(2026, 2, 1)
        sys_.save()
        self.assertEqual(sys_.next_inspection, date(2027, 2, 1))
        self.assertEqual(sys_.inspection_type_label, 'Löschanlage')
        response = self.client.post(reverse('objektverwaltung:add_suppression', args=[self.building.pk]), {
            'system_type': 'gas', 'designation': 'Gaslöschanlage Serverraum', 'location_description': '',
            'manufacturer': '', 'inspection_interval_months': 6, 'last_inspection': '2026-03-01',
            'is_operational': 'on', 'notes': '', 'tab': 'technik',
        })
        self.assertEqual(response.status_code, 302)
        gas = FireSuppressionSystem.objects.get(system_type='gas')
        self.assertEqual(gas.next_inspection, date(2026, 9, 1))

    def test_overview_lists_all_types_and_filters(self):
        from datetime import date, timedelta
        from django.utils import timezone
        from .models import FireAlarmPanel, FireSuppressionSystem, FireKeyDepot
        today = timezone.localdate()
        FireKeyDepot.objects.create(building=self.building, designation='FSD Tor', last_inspection=today - timedelta(days=400))
        FireAlarmPanel.objects.create(building=self.building, designation='BMZ Foyer', last_inspection=today - timedelta(days=10))
        FireSuppressionSystem.objects.create(building=self.building, designation='Sprinkler')
        url = reverse('objektverwaltung:inspection_list')
        response = self.client.get(url)
        for name in ('FSD Tor', 'BMZ Foyer', 'Sprinkler'):
            self.assertContains(response, name)
        response = self.client.get(url, {'status': 'overdue'})
        self.assertContains(response, 'FSD Tor')
        self.assertNotContains(response, 'BMZ Foyer')
        response = self.client.get(url, {'type': 'bmz'})
        self.assertContains(response, 'BMZ Foyer')
        self.assertNotContains(response, 'FSD Tor')
        response = self.client.get(url, {'status': 'open'})
        self.assertContains(response, 'Sprinkler')
        self.assertNotContains(response, 'BMZ Foyer')
        # Alte FSD-Adresse zeigt nur Depots
        response = self.client.get(reverse('objektverwaltung:keydepot_list'))
        self.assertContains(response, 'FSD Tor')
        self.assertNotContains(response, 'BMZ Foyer')
        # Dashboard zählt über alle Arten
        response = self.client.get(reverse('objektverwaltung:dashboard'))
        self.assertContains(response, 'Fällige Prüfungen')
        self.assertContains(response, 'FSD Tor')

    def test_new_inspection_without_assets_hints_to_technik_tab(self):
        response = self.client.get(reverse('objektverwaltung:inspection_new'), {'building': self.building.pk, 'type': 'loeschanlage'})
        self.assertContains(response, 'noch keine Anlage dieser Art')
        self.assertContains(response, self.building.get_absolute_url() + '#technik')


class StatusAndUsageCategoryTests(TestCase):
    """Objektstatus (Aktiv, In Planung, Inaktiv, Zum Löschen vorgemerkt) und pflegbare Nutzungsarten."""

    def setUp(self):
        self.user = User.objects.create_user(username='modul', password='pw')
        self.user.user_permissions.add(
            *Permission.objects.filter(content_type__app_label='objektverwaltung',
                                       codename__in=['view_buildingobject', 'change_buildingobject',
                                                     'add_buildingobject'])
        )
        self.client.force_login(self.user)
        # Tests laufen ohne Migrationen (--no-migrations), daher Standardwerte selbst anlegen
        self.school = UsageCategory.objects.create(name='Schule', sort_order=10)
        UsageCategory.objects.create(name='Krankenhaus / Pflege', sort_order=30)
        UsageCategory.objects.create(name='Sonstiges', sort_order=80)
        self.building = BuildingObject.objects.create(
            object_number='OBJ-1', name='Rathaus', usage_type=self.school,
            created_by=self.user, updated_by=self.user,
        )

    def _form_data(self, **overrides):
        data = {
            'object_number': 'OBJ-1', 'name': 'Rathaus', 'usage_type': str(self.school.pk),
            'status': 'active', 'street': '', 'house_number': '', 'postal_code': '', 'city': '',
            'latitude': '', 'longitude': '', 'floor_count': '', 'basement_count': '',
            'has_fire_alarm_system': '', 'notes': '',
        }
        data.update(overrides)
        return data

    def test_status_choices_in_form_and_badges(self):
        response = self.client.get(reverse('objektverwaltung:update', args=[self.building.pk]))
        self.assertContains(response, 'In Planung')
        self.assertContains(response, 'Zum Löschen vorgemerkt')
        for status, label in [('planned', 'In Planung'), ('for_deletion', 'Zum Löschen vorgemerkt')]:
            self.client.post(reverse('objektverwaltung:update', args=[self.building.pk]),
                             self._form_data(status=status))
            self.building.refresh_from_db()
            self.assertEqual(self.building.status, status)
            self.assertFalse(self.building.is_active)
            self.assertContains(self.client.get(reverse('objektverwaltung:list')), label)
            self.assertContains(self.client.get(self.building.get_absolute_url()), label)

    def test_status_filters_and_dashboard_count(self):
        planned = BuildingObject.objects.create(object_number='OBJ-2', name='Neubau', status='planned',
                                                created_by=self.user, updated_by=self.user)
        BuildingObject.objects.create(object_number='OBJ-3', name='Abriss', status='for_deletion',
                                      created_by=self.user, updated_by=self.user)
        url = reverse('objektverwaltung:list')
        html = self.client.get(url, {'filter': 'planung'}).content.decode()
        self.assertIn('>Neubau<', html)
        self.assertNotIn('>Rathaus<', html)
        html = self.client.get(url, {'filter': 'loeschen'}).content.decode()
        self.assertIn('>Abriss<', html)
        self.assertNotIn('>Neubau<', html)
        # Statussortierung: Aktiv, In Planung, ..., Zum Löschen vorgemerkt
        html = self.client.get(url, {'sort': 'status'}).content.decode()
        self.assertLess(html.index('>Rathaus<'), html.index('>Neubau<'))
        self.assertLess(html.index('>Neubau<'), html.index('>Abriss<'))
        response = self.client.get(reverse('objektverwaltung:dashboard'))
        self.assertEqual(response.context['object_count'], 1)
        self.assertEqual(planned.get_status_display(), 'In Planung')

    def test_usage_category_crud(self):
        list_url = reverse('objektverwaltung:usage_category_list')
        response = self.client.get(list_url)
        self.assertContains(response, 'Schule')
        self.assertContains(response, '1 Objekt')
        # anlegen
        response = self.client.post(reverse('objektverwaltung:usage_category_create'),
                                    {'name': 'Hochhaus', 'sort_order': '5', 'is_active': 'on'})
        self.assertRedirects(response, list_url)
        new = UsageCategory.objects.get(name='Hochhaus')
        # Duplikat (auch bei anderer Schreibweise) wird abgelehnt
        response = self.client.post(reverse('objektverwaltung:usage_category_create'),
                                    {'name': 'hochhaus', 'sort_order': '0', 'is_active': 'on'})
        self.assertContains(response, 'existiert bereits')
        # steht im Objektformular zur Verfügung
        response = self.client.get(reverse('objektverwaltung:create'))
        self.assertContains(response, '>Hochhaus</option>')
        # deaktivieren -> nicht mehr im Formular für neue Objekte
        self.client.post(reverse('objektverwaltung:usage_category_edit', args=[new.pk]),
                         {'name': 'Hochhaus', 'sort_order': '5'})
        new.refresh_from_db()
        self.assertFalse(new.is_active)
        self.assertNotContains(self.client.get(reverse('objektverwaltung:create')), '>Hochhaus</option>')
        # löschen (unbenutzt) klappt
        response = self.client.post(reverse('objektverwaltung:usage_category_delete', args=[new.pk]))
        self.assertRedirects(response, list_url)
        self.assertFalse(UsageCategory.objects.filter(pk=new.pk).exists())

    def test_usage_category_in_use_cannot_be_deleted_but_stays_selectable(self):
        response = self.client.post(reverse('objektverwaltung:usage_category_delete', args=[self.school.pk]),
                                    follow=True)
        self.assertContains(response, 'kann nicht gelöscht werden')
        self.assertTrue(UsageCategory.objects.filter(pk=self.school.pk).exists())
        # deaktivierte, aber verwendete Nutzungsart bleibt im Bearbeiten-Formular wählbar
        self.school.is_active = False
        self.school.save()
        response = self.client.get(reverse('objektverwaltung:update', args=[self.building.pk]))
        self.assertContains(response, 'Schule')
        # Liste filtert nach Nutzungsart-ID
        html = self.client.get(reverse('objektverwaltung:list'), {'usage_type': self.school.pk}).content.decode()
        self.assertIn('>Rathaus<', html)

    def test_usage_category_management_requires_change_permission(self):
        reader = User.objects.create_user(username='leser', password='pw')
        reader.user_permissions.add(Permission.objects.get(codename='view_buildingobject'))
        self.client.force_login(reader)
        response = self.client.get(reverse('objektverwaltung:usage_category_list'))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Neue Nutzungsart')
        self.assertEqual(self.client.get(reverse('objektverwaltung:usage_category_create')).status_code, 403)

    def test_csv_import_and_export_use_category_names(self):
        from io import BytesIO
        export = self.client.get(reverse('objektverwaltung:export')).content.decode('utf-8-sig')
        self.assertIn('Schule', export)
        self.assertIn('Aktiv', export)
        csv_text = (
            'objektnummer,bezeichnung,nutzungsart,status\n'
            'OBJ-7,Import-Halle,krankenhaus / pflege,In Planung\n'
        )
        upload = BytesIO(csv_text.encode('utf-8'))
        upload.name = 'objekte.csv'
        self.client.post(reverse('objektverwaltung:import'), {'import_file': upload})
        imported = BuildingObject.objects.get(object_number='OBJ-7')
        self.assertEqual(imported.usage_type.name, 'Krankenhaus / Pflege')
        self.assertEqual(imported.status, 'planned')
        # unbekannte Nutzungsart -> verständlicher Fehler, nichts importiert
        upload = BytesIO(b'objektnummer,bezeichnung,nutzungsart\nOBJ-8,Halle,Raumstation\n')
        upload.name = 'objekte.csv'
        response = self.client.post(reverse('objektverwaltung:import'), {'import_file': upload}, follow=True)
        self.assertContains(response, 'Raumstation')
        self.assertContains(response, 'unbekannt')
        self.assertFalse(BuildingObject.objects.filter(object_number='OBJ-8').exists())
