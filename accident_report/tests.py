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
