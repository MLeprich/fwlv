"""Tests für das Unfallbericht-Modul."""

from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import AccidentReport

User = get_user_model()


class AccidentReportModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='tester', password='pw12345')

    def _make(self, **kwargs):
        defaults = dict(
            injured_name='Mustermann, Max',
            accident_date=date(2026, 7, 1),
            location='Gerätehaus',
            description='Ausgerutscht in der Fahrzeughalle.',
            created_by=self.user,
            updated_by=self.user,
        )
        defaults.update(kwargs)
        return AccidentReport.objects.create(**defaults)

    def test_report_number_is_generated_and_sequential(self):
        r1 = self._make()
        r2 = self._make()
        self.assertTrue(r1.report_number.startswith('UB-'))
        self.assertNotEqual(r1.report_number, r2.report_number)
        self.assertEqual(r1.report_number[-5:], '00001')
        self.assertEqual(r2.report_number[-5:], '00002')

    def test_injured_display_prefers_freetext_when_no_person(self):
        r = self._make(injured_name='Externe Person')
        self.assertEqual(r.injured_display, 'Externe Person')


class AccidentReportPermissionTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='noperm', password='pw12345')
        self.client.force_login(self.user)

    def test_list_requires_permission(self):
        resp = self.client.get(reverse('accident_report:list'))
        self.assertEqual(resp.status_code, 403)


class PublicAccidentReportTests(TestCase):
    """Öffentliche Meldung ohne Login."""

    def test_public_create_is_reachable_without_login(self):
        resp = self.client.get(reverse('accident_report:public_create'))
        self.assertEqual(resp.status_code, 200)

    def test_public_form_does_not_expose_personnel_or_vehicles(self):
        body = self.client.get(reverse('accident_report:public_create')).content.decode()
        self.assertNotIn('name="injured_person"', body)
        self.assertNotIn('name="vehicle"', body)

    def test_anonymous_submission_creates_report_without_user(self):
        resp = self.client.post(reverse('accident_report:public_create'), {
            'report_type': 'personenunfall',
            'reporter_first_name': 'Anna',
            'reporter_last_name': 'Melder',
            'injured_name': 'Opfer, Otto',
            'accident_date': '2026-07-08',
            'location': 'Übungsgelände',
            'activity_type': 'uebung',
            'description': 'Von der Leiter gestürzt.',
        })
        self.assertRedirects(resp, reverse('accident_report:public_success'))
        report = AccidentReport.objects.get(injured_name='Opfer, Otto')
        self.assertIsNone(report.created_by)
        self.assertTrue(report.is_public_submission)
        self.assertEqual(report.reporter_display, 'Anna Melder')

    def test_anonymous_cannot_view_list(self):
        resp = self.client.get(reverse('accident_report:list'))
        self.assertEqual(resp.status_code, 302)  # Redirect zum Login


class TrafficAccidentWizardTests(TestCase):
    """Öffentlicher Wizard nach dem Muster des Europäischen Unfallberichts."""

    def _traffic_payload(self, **overrides):
        data = {
            'report_type': 'verkehrsunfall',
            'reporter_first_name': 'Anna',
            'reporter_last_name': 'Melder',
            'accident_date': '2026-09-01',
            'accident_time': '14:30',
            'location': 'Musterstadt, Hauptstraße 12',
            'activity_type': 'einsatz',
            'incident_number': '2026/0815',
            'activity_detail': 'BMA-Alarm',
            'special_rights': 'on',
            'blue_light_siren': 'on',
            'own_vehicle_name': 'Florian Musterstadt 1/46/1',
            'own_vehicle_plate': 'MS-FW 123',
            'own_driver_name': 'Fahrer, Fritz',
            'own_impact_point': 'front_left',
            'own_damage': 'Stoßstange vorne links',
            'own_circumstances': ['13', '17'],
            'other_vehicle_involved': 'True',
            'other_vehicle_plate': 'AB-CD 123',
            'other_vehicle_make': 'VW Golf',
            'other_holder_name': 'Gegner, Gustav',
            'other_insurer': 'Muster-Versicherung',
            'other_circumstances': ['16'],
            'other_property_damage': 'True',
            'other_property_damage_detail': 'Verkehrsschild',
            'police_involved': 'True',
            'police_detail': 'PI Musterstadt, TB 4711',
            'description': 'Beim Linksabbiegen mit Sonderrechten Kollision.',
            'injuries_occurred': 'False',
        }
        data.update(overrides)
        return data

    def test_traffic_accident_submission_stores_european_report_fields(self):
        resp = self.client.post(reverse('accident_report:public_create'), self._traffic_payload())
        self.assertRedirects(resp, reverse('accident_report:public_success'))
        report = AccidentReport.objects.get(incident_number='2026/0815')
        self.assertTrue(report.is_traffic_accident)
        self.assertTrue(report.special_rights)
        self.assertTrue(report.blue_light_siren)
        self.assertEqual(report.own_circumstances, [13, 17])
        self.assertEqual(report.other_circumstances, [16])
        self.assertTrue(report.other_vehicle_involved)
        self.assertEqual(report.other_vehicle_plate, 'AB-CD 123')
        self.assertTrue(report.police_involved)
        self.assertFalse(report.injuries_occurred)
        self.assertEqual(report.injured_display, 'Keine Verletzten')
        self.assertEqual(report.own_vehicle_display, 'Florian Musterstadt 1/46/1 · MS-FW 123')
        self.assertEqual([n for n, _ in report.own_circumstances_display], [13, 17])

    def test_traffic_accident_requires_driver_and_vehicle(self):
        resp = self.client.post(reverse('accident_report:public_create'),
                                self._traffic_payload(own_vehicle_name='', own_driver_name=''))
        self.assertEqual(resp.status_code, 200)
        form = resp.context['form']
        self.assertIn('own_vehicle_name', form.errors)
        self.assertIn('own_driver_name', form.errors)
        # Wizard springt zum Schritt "Fahrzeug A"
        self.assertEqual(resp.context['error_step'], 'fahrzeug_a')

    def test_other_vehicle_plate_required_only_when_involved(self):
        resp = self.client.post(reverse('accident_report:public_create'),
                                self._traffic_payload(other_vehicle_plate=''))
        self.assertIn('other_vehicle_plate', resp.context['form'].errors)

        resp = self.client.post(reverse('accident_report:public_create'),
                                self._traffic_payload(other_vehicle_involved='False', other_vehicle_plate='',
                                                      incident_number='2026/0816'))
        self.assertRedirects(resp, reverse('accident_report:public_success'))
        report = AccidentReport.objects.get(incident_number='2026/0816')
        self.assertFalse(report.other_vehicle_involved)
        # Angaben zu Fahrzeug B werden verworfen
        self.assertEqual(report.other_holder_name, '')
        self.assertEqual(report.other_circumstances, [])

    def test_injured_name_required_when_injuries_reported(self):
        resp = self.client.post(reverse('accident_report:public_create'),
                                self._traffic_payload(injuries_occurred='True'))
        self.assertIn('injured_name', resp.context['form'].errors)
        self.assertEqual(resp.context['error_step'], 'verletzte')

    def test_person_accident_ignores_vehicle_fields(self):
        resp = self.client.post(reverse('accident_report:public_create'), {
            'report_type': 'personenunfall',
            'reporter_first_name': 'Anna',
            'reporter_last_name': 'Melder',
            'injured_name': 'Opfer, Otto',
            'accident_date': '2026-07-08',
            'location': 'Übungsgelände',
            'activity_type': 'uebung',
            'incident_number': 'Ü-2026-3',
            'description': 'Von der Leiter gestürzt.',
            'own_driver_name': 'sollte verworfen werden',
            'special_rights': 'on',
        })
        self.assertRedirects(resp, reverse('accident_report:public_success'))
        report = AccidentReport.objects.get(injured_name='Opfer, Otto')
        self.assertFalse(report.is_traffic_accident)
        self.assertTrue(report.injuries_occurred)
        self.assertFalse(report.special_rights)
        self.assertEqual(report.own_driver_name, '')
        self.assertEqual(report.incident_number, 'Ü-2026-3')

    def test_wizard_page_lists_steps_and_circumstances(self):
        body = self.client.get(reverse('accident_report:public_create')).content.decode()
        self.assertIn('wizard-steps', body)
        self.assertIn('data-step="umstaende"', body)
        self.assertIn('beachtete Vorfahrtszeichen nicht', body)
        self.assertIn('name="incident_number"', body)
        self.assertIn('name="special_rights"', body)


class InternalTrafficAccidentTests(TestCase):
    """Interne Erfassung/Detailansicht mit den neuen Feldern."""

    def setUp(self):
        from django.contrib.auth.models import Group, Permission
        self.user = User.objects.create_user(username='admin', password='pw12345')
        self.user.user_permissions.add(*Permission.objects.filter(
            content_type__app_label='accident_report'))
        self.user.groups.add(Group.objects.create(name='Administrator'))
        self.client.force_login(self.user)

    def test_detail_shows_vehicle_sections_and_search_by_incident_number(self):
        report = AccidentReport.objects.create(
            report_type='verkehrsunfall',
            injuries_occurred=False,
            accident_date=date(2026, 9, 1),
            location='Hauptstraße',
            description='Kollision',
            incident_number='2026/0815',
            special_rights=True,
            own_vehicle_name='Florian 1/46/1',
            own_driver_name='Fahrer, Fritz',
            own_circumstances=[13],
            other_vehicle_involved=True,
            other_vehicle_plate='AB-CD 123',
            created_by=self.user,
            updated_by=self.user,
        )
        resp = self.client.get(reverse('accident_report:detail', kwargs={'pk': report.pk}))
        self.assertEqual(resp.status_code, 200)
        body = resp.content.decode()
        self.assertIn('Unfallgegner', body)
        self.assertIn('AB-CD 123', body)
        self.assertIn('bog links ab', body)
        self.assertIn('Einsatzfahrt', body)

        resp = self.client.get(reverse('accident_report:list'), {'search': '0815'})
        self.assertContains(resp, report.report_number)
        resp = self.client.get(reverse('accident_report:list'), {'search': 'AB-CD'})
        self.assertContains(resp, report.report_number)

    def test_internal_edit_form_renders_and_saves(self):
        report = AccidentReport.objects.create(
            report_type='verkehrsunfall', injuries_occurred=False,
            accident_date=date(2026, 9, 1), location='Hauptstraße', description='Kollision',
            own_vehicle_name='Florian 1/46/1', own_driver_name='Fahrer, Fritz',
            own_circumstances=[13], created_by=self.user, updated_by=self.user,
        )
        url = reverse('accident_report:edit', kwargs={'pk': report.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        # Vorbelegung der Umstände im Formular
        self.assertContains(resp, 'id="own_c_13"')
        self.assertIn('checked', resp.content.decode().split('id="own_c_13"')[1].split('>')[0])
        self.assertNotIn('checked', resp.content.decode().split('id="own_c_12"')[1].split('>')[0])

        resp = self.client.post(url, {
            'report_type': 'verkehrsunfall', 'severity': 'leicht',
            'injuries_occurred': 'False',
            'accident_date': '2026-09-01', 'location': 'Hauptstraße', 'activity_type': 'einsatz',
            'incident_number': '2026/0815', 'special_rights': 'on',
            'own_vehicle_name': 'Florian 1/46/1', 'own_driver_name': 'Fahrer, Fritz',
            'own_circumstances': ['1', '14'],
            'other_vehicle_involved': 'False',
            'other_property_damage': 'False', 'police_involved': 'False',
            'description': 'Kollision beim Rangieren.',
        })
        self.assertRedirects(resp, reverse('accident_report:detail', kwargs={'pk': report.pk}))
        report.refresh_from_db()
        self.assertEqual(report.own_circumstances, [1, 14])
        self.assertEqual(report.incident_number, '2026/0815')
        self.assertTrue(report.special_rights)


class AdminOnlyEditDeleteTests(TestCase):
    """Bearbeiten und Löschen nur für Administratoren, Ansehen/PDF für Beauftragte."""

    def setUp(self):
        from django.contrib.auth.models import Permission
        self.beauftragter = User.objects.create_user(username='beauftragter', password='pw12345')
        self.beauftragter.user_permissions.add(*Permission.objects.filter(
            content_type__app_label='accident_report'))
        self.report = AccidentReport.objects.create(
            report_type='verkehrsunfall', injuries_occurred=False,
            accident_date=date(2026, 9, 1), location='Hauptstraße', description='Kollision',
            own_vehicle_name='Florian 1/46/1', own_driver_name='Fahrer, Fritz',
            own_circumstances=[13], other_vehicle_involved=True, other_vehicle_plate='AB-CD 123',
        )

    def test_beauftragter_can_view_but_not_edit_or_delete(self):
        self.client.force_login(self.beauftragter)
        detail = self.client.get(reverse('accident_report:detail', kwargs={'pk': self.report.pk}))
        self.assertEqual(detail.status_code, 200)
        self.assertNotContains(detail, 'Bearbeiten')
        self.assertEqual(self.client.get(reverse('accident_report:edit', kwargs={'pk': self.report.pk})).status_code, 403)
        self.assertEqual(self.client.post(reverse('accident_report:delete', kwargs={'pk': self.report.pk})).status_code, 403)
        self.assertTrue(AccidentReport.objects.filter(pk=self.report.pk).exists())

    def test_superuser_can_edit_and_delete(self):
        admin = User.objects.create_superuser(username='root', password='pw12345', email='r@x.de')
        self.client.force_login(admin)
        detail = self.client.get(reverse('accident_report:detail', kwargs={'pk': self.report.pk}))
        self.assertContains(detail, 'Bearbeiten')
        self.assertEqual(self.client.get(reverse('accident_report:edit', kwargs={'pk': self.report.pk})).status_code, 200)
        resp = self.client.post(reverse('accident_report:delete', kwargs={'pk': self.report.pk}))
        self.assertRedirects(resp, reverse('accident_report:list'))
        self.assertFalse(AccidentReport.objects.filter(pk=self.report.pk).exists())

    def test_pdf_download_for_viewer(self):
        self.client.force_login(self.beauftragter)
        resp = self.client.get(reverse('accident_report:pdf', kwargs={'pk': self.report.pk}))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp['Content-Type'], 'application/pdf')
        self.assertTrue(resp.content.startswith(b'%PDF'))
        self.assertIn(self.report.report_number, resp['Content-Disposition'])

    def test_pdf_for_person_accident(self):
        self.client.force_login(self.beauftragter)
        report = AccidentReport.objects.create(
            injured_name='Opfer, Otto', accident_date=date(2026, 7, 1),
            location='Gerätehaus', description='Ausgerutscht.', first_aid_given=True,
        )
        resp = self.client.get(reverse('accident_report:pdf', kwargs={'pk': report.pk}))
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.content.startswith(b'%PDF'))
