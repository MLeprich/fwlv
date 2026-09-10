"""Tests der Brandverhütungsschau: PSV-Fristen, Vor-Ort-Schablone, Mustersätze, Rechte."""

import json
from datetime import date, timedelta
from io import StringIO
from unittest import mock

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from . import akte
from .bvs_import import ParsedCategory, ParsedPhrase, ParseResult, parse_text
from .forms_bvs import FireSafetyInspectionForm, PSVCertificateForm
from .models import (
    BuildingObject, BVSPhrase, BVSPhraseCategory, BVSStatus, FireSafetyDefect,
    FireSafetyInspection, PSVCertificate, PSVInspectionType, PSVRequirement, PSVStatus,
)

User = get_user_model()

BVS_VIEW = ['bvs_view']
BVS_EDIT = ['bvs_view', 'bvs_edit']
BVS_MANAGE = ['bvs_view', 'bvs_edit', 'bvs_manage']


def make_user(username, codenames=(), with_objects=True):
    user = User.objects.create_user(username=username, password='pw', first_name='Erika', last_name='Muster',
                                    email=f'{username}@example.de')
    names = list(codenames) + (['view_buildingobject'] if with_objects else [])
    user.user_permissions.add(*Permission.objects.filter(content_type__app_label='objektverwaltung',
                                                         codename__in=names))
    return user


class BVSTestBase(TestCase):
    def setUp(self):
        self.user = make_user('bvs', BVS_EDIT)
        self.client.force_login(self.user)
        self.building = BuildingObject.objects.create(
            object_number='OBJ-7', name='Gesamtschule Süd', street='Schulstr.', house_number='5',
            postal_code='46045', city='Oberhausen', created_by=self.user, updated_by=self.user,
        )
        self.rwa = PSVInspectionType.objects.create(name='RWA-Test', interval_months=36, warning_days=90)
        chapter = BVSPhraseCategory.objects.create(number='98', title='Rettungswege Test', sort_order=98000)
        self.section = BVSPhraseCategory.objects.create(number='98.1', title='Türen', parent=chapter, sort_order=98001)
        self.phrase = BVSPhrase.objects.create(category=self.section, code='98101', title='Notausgang',
                                               text='Die Tür … ist freizuhalten.', sort_order=98101)

    def start(self):
        response = self.client.post(reverse('objektverwaltung:bvs_start_for_building', args=[self.building.pk]))
        inspection = FireSafetyInspection.objects.get(building=self.building)
        self.assertRedirects(response, inspection.get_absolute_url(), fetch_redirect_response=False)
        return inspection


# ---------------------------------------------------------------------------
# Import der Mustersätze
# ---------------------------------------------------------------------------

SAMPLE = """Der Oberbürgermeister
Fachbereich 6-1-60                                   Rettungswege
Vorbeugender Brandschutz


9.       Rettungswege
9.1      Allgemein



9101     Freihalten von Notausgängen

Sämtliche Türen im Verlauf von Rettungswegen sind in Fluchtrichtung jederzeit von innen
durch einen einzigen Griff leicht zu öffnen.                                               Kommentiert [HD1]: Besser „leicht“
                                                                                           streichen



9102     Zweiter Satz

Die Aufstellfläche ist so zu befestigen, dass der Ist-
Zustand erhalten bleibt.

         der erste Punkt einer Liste und

         der zweite Punkt.

38                                                                                  Stand: 10.09.2026
\fDer Oberbürgermeister
Rettungswege                                                           Fachbereich 6-1-60
                                                                Vorbeugender Brandschutz


Fortsetzung auf der nächsten Seite.



9103

9.2      Türen
"""


class ParserTests(TestCase):
    def test_structure_comments_and_page_breaks(self):
        result = parse_text(SAMPLE)
        self.assertEqual([c.number for c in result.categories], ['9', '9.1', '9.2'])
        self.assertEqual(result.categories[1].parent, '9')
        codes = {p.code: p for p in result.phrases}
        self.assertEqual(sorted(codes), ['9101', '9102', '9103'])

        first = codes['9101']
        self.assertEqual(first.title, 'Freihalten von Notausgängen')
        self.assertEqual(first.category, '9.1')
        self.assertNotIn('Kommentiert', first.text)
        self.assertTrue(first.text.endswith('leicht zu öffnen.'))
        self.assertEqual(first.notes, [['Besser „leicht“', 'streichen']])

        second = codes['9102']
        self.assertIn('Ist-Zustand', second.text)
        self.assertIn('– der erste Punkt einer Liste und', second.text)
        self.assertIn('Fortsetzung auf der nächsten Seite.', second.text)  # Kopfzeile der Folgeseite entfernt
        self.assertNotIn('Stand:', second.text)
        self.assertEqual(codes['9103'].text, '')

    def test_blank_line_inside_sentence_is_no_paragraph_break(self):
        text = SAMPLE.replace(
            'Die Aufstellfläche ist so zu befestigen, dass der Ist-\nZustand erhalten bleibt.',
            'Die Belehrung des Personals ist\n\nschriftlich zu dokumentieren.')
        second = [p for p in parse_text(text).phrases if p.code == '9102'][0]
        self.assertTrue(second.paragraphs[0].startswith('Die Belehrung des Personals ist schriftlich zu dokumentieren.'))
        # eingerückte Aufzählung nach Leerzeile bleibt ein eigener Punkt
        self.assertIn('– der erste Punkt einer Liste und', second.paragraphs)

    def test_import_command_creates_and_keeps_existing(self):
        parsed = ParseResult(
            categories=[ParsedCategory('97', 'Kapitel'), ParsedCategory('97.1', 'Abschnitt', parent='97')],
            phrases=[
                ParsedPhrase('97101', 'Mit Text', '97.1', ['Absatz eins.'], [['Randnotiz']]),
                ParsedPhrase('97102', 'Ohne Text', '97.1'),
                ParsedPhrase('97103', '', '97.1'),
            ],
        )
        target = 'objektverwaltung.management.commands.import_bvs_mustersaetze.parse_pdf'
        with mock.patch(target, return_value=parsed):
            call_command('import_bvs_mustersaetze', 'dummy.pdf', stdout=StringIO())
        with_text = BVSPhrase.objects.get(code='97101')
        self.assertEqual(with_text.category.number, '97.1')
        self.assertEqual(with_text.category.parent.number, '97')
        self.assertIn('Randnotiz', with_text.review_note)
        self.assertTrue(with_text.is_active)
        self.assertFalse(BVSPhrase.objects.get(code='97102').is_active)
        self.assertFalse(BVSPhrase.objects.filter(code='97103').exists())

        with_text.text = 'Im System überarbeitet'
        with_text.save()
        with mock.patch(target, return_value=parsed):
            call_command('import_bvs_mustersaetze', 'dummy.pdf', stdout=StringIO())
        self.assertEqual(BVSPhrase.objects.get(code='97101').text, 'Im System überarbeitet')
        with mock.patch(target, return_value=parsed):
            call_command('import_bvs_mustersaetze', 'dummy.pdf', '--update', stdout=StringIO())
        self.assertEqual(BVSPhrase.objects.get(code='97101').text, 'Absatz eins.')


# ---------------------------------------------------------------------------
# PSV-Fristen: Ampel und Bescheinigungen
# ---------------------------------------------------------------------------

class PSVStatusTests(BVSTestBase):
    def test_traffic_light(self):
        today = timezone.localdate()
        req = PSVRequirement.objects.create(building=self.building, inspection_type=self.rwa)
        self.assertEqual(req.status, PSVStatus.MISSING)

        def certify(valid_until):
            PSVCertificate.objects.create(requirement=req, inspection_date=today - timedelta(days=10),
                                          valid_until=valid_until, created_by=self.user, updated_by=self.user)
            req.refresh_from_db()

        certify(today + timedelta(days=200))
        self.assertEqual(req.status, PSVStatus.VALID)
        req.certificates.all().delete()
        certify(today + timedelta(days=90))
        self.assertEqual(req.status, PSVStatus.EXPIRING)
        self.assertEqual(req.remaining_display, 'noch 90 Tage')
        req.certificates.all().delete()
        certify(today - timedelta(days=1))
        self.assertEqual(req.status, PSVStatus.EXPIRED)
        self.assertEqual(req.remaining_display, 'seit 1 Tag abgelaufen')
        req.is_active = False
        self.assertEqual(req.status, PSVStatus.INACTIVE)

    def test_latest_certificate_wins_and_delete_resyncs(self):
        req = PSVRequirement.objects.create(building=self.building, inspection_type=self.rwa)
        old = PSVCertificate.objects.create(requirement=req, inspection_date=date(2023, 1, 10),
                                            valid_until=date(2026, 1, 10), created_by=self.user, updated_by=self.user)
        new = PSVCertificate.objects.create(requirement=req, inspection_date=date(2026, 1, 5),
                                            valid_until=date(2029, 1, 5), created_by=self.user, updated_by=self.user)
        req.refresh_from_db()
        self.assertEqual(req.valid_until, date(2029, 1, 5))
        self.client.post(reverse('objektverwaltung:psv_certificate_delete', args=[new.pk]))
        req.refresh_from_db()
        self.assertEqual(req.valid_until, old.valid_until)

    def test_certificate_form_suggests_valid_until(self):
        req = PSVRequirement.objects.create(building=self.building, inspection_type=self.rwa)
        form = PSVCertificateForm(data={'inspection_date': '2026-02-28', 'result': 'ok'}, requirement=req)
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['valid_until'], date(2029, 2, 28))
        form = PSVCertificateForm(data={'inspection_date': '2026-02-28', 'valid_until': '2026-01-01',
                                        'result': 'ok'}, requirement=req)
        self.assertFalse(form.is_valid())
        self.assertIn('valid_until', form.errors)


class PSVViewTests(BVSTestBase):
    def test_add_requirement_and_certificate_via_htmx(self):
        response = self.client.post(reverse('objektverwaltung:psv_add', args=[self.building.pk]),
                                    {'inspection_type': self.rwa.pk, 'designation': 'Treppenraum A', 'is_active': 'on'},
                                    HTTP_HX_REQUEST='true')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="psv-panel"')
        self.assertContains(response, 'RWA-Test – Treppenraum A')
        req = PSVRequirement.objects.get(building=self.building)

        response = self.client.post(reverse('objektverwaltung:psv_certificate_add', args=[req.pk]),
                                    {'inspection_date': '2026-09-01', 'expert_name': 'Dipl.-Ing. Prüfer',
                                     'result': 'ok'}, HTTP_HX_REQUEST='true')
        self.assertEqual(response.status_code, 200)
        req.refresh_from_db()
        self.assertEqual(req.valid_until, date(2029, 9, 1))
        self.assertContains(response, 'Dipl.-Ing. Prüfer')

    def test_invalid_certificate_via_htmx_reports_error(self):
        req = PSVRequirement.objects.create(building=self.building, inspection_type=self.rwa)
        response = self.client.post(reverse('objektverwaltung:psv_certificate_add', args=[req.pk]),
                                    {'inspection_date': '', 'result': 'ok'}, HTTP_HX_REQUEST='true')
        self.assertEqual(response.status_code, 200)
        self.assertIn('bvsError', json.loads(response['HX-Trigger']))
        self.assertFalse(req.certificates.exists())

    def test_overview_defaults_to_action_needed(self):
        ok = PSVRequirement.objects.create(building=self.building, inspection_type=self.rwa, designation='gültig')
        PSVCertificate.objects.create(requirement=ok, inspection_date=date.today(),
                                      valid_until=date.today() + timedelta(days=500),
                                      created_by=self.user, updated_by=self.user)
        PSVRequirement.objects.create(building=self.building, inspection_type=self.rwa, designation='fehlt')
        response = self.client.get(reverse('objektverwaltung:psv_overview'))
        self.assertContains(response, 'RWA-Test – fehlt')
        self.assertNotContains(response, 'RWA-Test – gültig')
        response = self.client.get(reverse('objektverwaltung:psv_overview') + '?status=valid')
        self.assertContains(response, 'RWA-Test – gültig')


# ---------------------------------------------------------------------------
# Rechte
# ---------------------------------------------------------------------------

class BVSPermissionTests(BVSTestBase):
    def test_object_permissions_alone_do_not_grant_bvs(self):
        user = make_user('modul')
        user.user_permissions.add(*Permission.objects.filter(
            content_type__app_label='objektverwaltung').exclude(codename__startswith='bvs_'))
        self.client.force_login(user)
        self.assertEqual(self.client.get(reverse('objektverwaltung:bvs_overview')).status_code, 403)
        self.assertEqual(self.client.get(reverse('objektverwaltung:psv_overview')).status_code, 403)
        response = self.client.get(self.building.get_absolute_url())
        self.assertNotContains(response, 'Brandverhütungsschau starten')
        self.assertNotContains(response, 'id="psv-panel"')

    def test_view_only_can_read_but_not_start(self):
        self.client.force_login(make_user('leser', BVS_VIEW))
        self.assertEqual(self.client.get(reverse('objektverwaltung:bvs_overview')).status_code, 200)
        response = self.client.get(self.building.get_absolute_url())
        self.assertContains(response, 'id="psv-panel"')
        self.assertNotContains(response, 'Brandverhütungsschau starten')
        response = self.client.post(reverse('objektverwaltung:bvs_start_for_building', args=[self.building.pk]))
        self.assertEqual(response.status_code, 403)

    def test_htmx_without_permission_returns_status_not_login_page(self):
        inspection = self.start()
        self.client.logout()
        response = self.client.post(reverse('objektverwaltung:bvs_save', args=[inspection.pk]),
                                    {'_fields': 'report_number', 'report_number': 'X'}, HTTP_HX_REQUEST='true')
        self.assertEqual(response.status_code, 401)

    def test_phrase_management_requires_manage(self):
        response = self.client.get(reverse('objektverwaltung:bvs_phrase_create'))
        self.assertEqual(response.status_code, 403)
        self.client.force_login(make_user('chef', BVS_MANAGE))
        response = self.client.post(reverse('objektverwaltung:bvs_phrase_create'), {
            'category': self.section.pk, 'code': '98102', 'title': 'Neu', 'text': 'Text', 'is_active': 'on',
            'review_note': '',
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(BVSPhrase.objects.get(code='98102').sort_order, 98102)

    def test_setup_roles_and_module_lead_exclusion(self):
        call_command('setup_bvs_permissions', stdout=StringIO())
        sb = Group.objects.get(name='BVS Sachbearbeiter')
        codes = set(sb.permissions.values_list('codename', flat=True))
        self.assertTrue({'bvs_view', 'bvs_edit', 'view_buildingobject'} <= codes)
        self.assertNotIn('bvs_manage', codes)
        self.assertIn('bvs_manage', Group.objects.get(name='BVS Verantwortlicher').permissions.values_list('codename', flat=True))

        from permissions.management.commands.setup_permissions import Command as SetupCommand
        command = SetupCommand(stdout=StringIO())
        command._setup_module_leads()
        lead = Group.objects.get(name='Modulverantwortlicher Objektverwaltung')
        self.assertTrue(lead.permissions.filter(codename='change_buildingobject').exists())
        self.assertFalse(lead.permissions.filter(codename__startswith='bvs_').exists())


# ---------------------------------------------------------------------------
# Vor-Ort-Schablone
# ---------------------------------------------------------------------------

class InspectionWorkflowTests(BVSTestBase):
    def test_start_prefills_and_reuses_draft(self):
        inspection = self.start()
        self.assertEqual(inspection.status, BVSStatus.DRAFT)
        self.assertEqual(inspection.inspection_date, timezone.localdate())
        self.assertEqual(inspection.participant_fire_dept, 'Erika Muster')
        self.assertIn('Schulstr. 5', inspection.recipient_address)
        response = self.client.post(reverse('objektverwaltung:bvs_start_for_building', args=[self.building.pk]))
        self.assertRedirects(response, inspection.get_absolute_url(), fetch_redirect_response=False)
        self.assertEqual(FireSafetyInspection.objects.count(), 1)

        page = self.client.get(inspection.get_absolute_url())
        self.assertContains(page, 'bvs-phrases')
        self.assertContains(page, 'Notausgang')  # Mustersatz in der Auswahl

    def test_next_inspection_prefills_from_previous(self):
        first = self.start()
        first.object_key = 'K-12'
        first.cost_bearer = 'Stadt'
        first.status = BVSStatus.COMPLETED
        first.save()
        response = self.client.post(reverse('objektverwaltung:bvs_start_for_building', args=[self.building.pk]))
        second = FireSafetyInspection.objects.exclude(pk=first.pk).get()
        self.assertEqual((second.object_key, second.cost_bearer), ('K-12', 'Stadt'))
        self.assertEqual(response.status_code, 302)

    def test_section_save_only_touches_its_fields(self):
        inspection = self.start()
        inspection.cost_bearer = 'Firma XY'
        inspection.save()
        response = self.client.post(reverse('objektverwaltung:bvs_save', args=[inspection.pk]), {
            '_fields': 'defect_deadline,next_inspection,is_fee_required',
            'defect_deadline': '2026-12-01', 'next_inspection': '2029-03',
        }, HTTP_HX_REQUEST='true')
        self.assertContains(response, 'Gespeichert')
        inspection.refresh_from_db()
        self.assertEqual(inspection.cost_bearer, 'Firma XY')
        self.assertEqual(inspection.defect_deadline, date(2026, 12, 1))
        self.assertEqual(inspection.next_inspection, date(2029, 3, 1))
        self.assertFalse(inspection.is_fee_required)  # nicht angehakt, aber übermittelt

    def test_section_save_reports_invalid_input(self):
        inspection = self.start()
        response = self.client.post(reverse('objektverwaltung:bvs_save', args=[inspection.pk]), {
            '_fields': 'inspection_date', 'inspection_date': '',
        }, HTTP_HX_REQUEST='true')
        self.assertContains(response, 'Bitte prüfen')
        inspection.refresh_from_db()
        self.assertIsNotNone(inspection.inspection_date)

    def test_month_field_accepts_month_input(self):
        form = FireSafetyInspectionForm(data={'next_inspection': '2030-11'})
        form.is_valid()
        self.assertEqual(form.cleaned_data['next_inspection'], date(2030, 11, 1))

    def test_defects_add_edit_move_renumber_delete(self):
        inspection = self.start()
        add = reverse('objektverwaltung:bvs_defect_add', args=[inspection.pk])
        response = self.client.post(add, {'phrase': self.phrase.pk}, HTTP_HX_REQUEST='true')
        self.assertContains(response, 'Die Tür … ist freizuhalten.')
        self.client.post(add, {'phrase': ''}, HTTP_HX_REQUEST='true')
        first, second = inspection.defects.all()
        self.assertEqual((first.number, second.number), ('1.1', '1.2'))
        self.assertEqual(first.phrase, self.phrase)

        response = self.client.post(reverse('objektverwaltung:bvs_defect_save', args=[second.pk]), {
            f'd{second.pk}-number': '1.2', f'd{second.pk}-location': 'Keller', f'd{second.pk}-text': 'Freitext',
        }, HTTP_HX_REQUEST='true')
        self.assertContains(response, 'Gespeichert')
        second.refresh_from_db()
        self.assertEqual((second.location, second.text), ('Keller', 'Freitext'))

        self.client.post(reverse('objektverwaltung:bvs_defect_up', args=[second.pk]), HTTP_HX_REQUEST='true')
        self.assertEqual([d.pk for d in inspection.defects.all()], [second.pk, first.pk])
        self.client.post(reverse('objektverwaltung:bvs_defect_renumber', args=[inspection.pk]), HTTP_HX_REQUEST='true')
        self.assertEqual([d.number for d in inspection.defects.all()], ['1.1', '1.2'])

        response = self.client.post(reverse('objektverwaltung:bvs_defect_delete', args=[first.pk]), HTTP_HX_REQUEST='true')
        self.assertEqual(response.content, b'')
        self.assertEqual(inspection.defects.count(), 1)

    def test_complete_requires_defect_text_then_locks(self):
        inspection = self.start()
        FireSafetyDefect.objects.create(inspection=inspection, position=1, number='1.1', text='  ')
        complete = reverse('objektverwaltung:bvs_complete', args=[inspection.pk])
        self.client.post(complete)
        inspection.refresh_from_db()
        self.assertEqual(inspection.status, BVSStatus.DRAFT)

        inspection.defects.update(text='Feuerlöscher fehlt.')
        self.client.post(complete)
        inspection.refresh_from_db()
        self.assertEqual(inspection.status, BVSStatus.COMPLETED)
        self.assertEqual(inspection.completed_by, self.user)

        response = self.client.post(reverse('objektverwaltung:bvs_save', args=[inspection.pk]),
                                    {'_fields': 'report_number', 'report_number': 'neu'}, HTTP_HX_REQUEST='true')
        self.assertEqual(response.status_code, 409)
        page = self.client.get(inspection.get_absolute_url())
        self.assertContains(page, 'Niederschrift (PDF)')
        self.assertNotContains(page, 'bvs-phrases')  # Leseansicht statt Schablone

        self.client.post(reverse('objektverwaltung:bvs_reopen', args=[inspection.pk]))
        inspection.refresh_from_db()
        self.assertEqual(inspection.status, BVSStatus.DRAFT)

    def test_resolve_defect_on_follow_up(self):
        inspection = self.start()
        defect = FireSafetyDefect.objects.create(inspection=inspection, position=1, number='1.1', text='Mangel')
        inspection.status = BVSStatus.COMPLETED
        inspection.defect_deadline = timezone.localdate() - timedelta(days=1)
        inspection.save()
        self.assertEqual(inspection.follow_up_status, 'overdue')
        response = self.client.post(reverse('objektverwaltung:bvs_defect_resolve', args=[defect.pk]),
                                    {'resolved_on': '2026-09-10'}, HTTP_HX_REQUEST='true')
        self.assertContains(response, 'behoben')
        defect.refresh_from_db()
        self.assertEqual(defect.resolved_on, date(2026, 9, 10))
        self.assertEqual(FireSafetyInspection.objects.get(pk=inspection.pk).follow_up_status, '')

    def test_delete_completed_requires_manage(self):
        inspection = self.start()
        inspection.status = BVSStatus.COMPLETED
        inspection.save()
        self.client.post(reverse('objektverwaltung:bvs_delete', args=[inspection.pk]))
        self.assertTrue(FireSafetyInspection.objects.filter(pk=inspection.pk).exists())
        self.client.force_login(make_user('chef', BVS_MANAGE))
        self.client.post(reverse('objektverwaltung:bvs_delete', args=[inspection.pk]))
        self.assertFalse(FireSafetyInspection.objects.filter(pk=inspection.pk).exists())

    def test_pdfs_render(self):
        inspection = self.start()
        FireSafetyDefect.objects.create(inspection=inspection, position=1, number='1.1', location='EG',
                                        text='Die Tür ist freizuhalten.')
        for part in ('niederschrift', 'erfassungsblatt'):
            response = self.client.get(reverse('objektverwaltung:bvs_pdf', args=[inspection.pk, part]))
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response['Content-Type'], 'application/pdf')
            self.assertTrue(response.content.startswith(b'%PDF'))
        inspection.is_fee_required = False
        inspection.save()
        response = self.client.get(reverse('objektverwaltung:bvs_pdf', args=[inspection.pk, 'niederschrift']))
        self.assertEqual(response.status_code, 200)

    def test_akte_hides_bvs_entries_without_permission(self):
        self.start()
        self.assertTrue(any(e['kind'] == 'bvs' for e in akte.build_timeline(self.building)))
        self.assertFalse(any(e['kind'] == 'bvs' for e in akte.build_timeline(self.building, include_bvs=False)))


class PhraseImportViewTests(BVSTestBase):
    PARSED = ParseResult(
        categories=[ParsedCategory('96', 'Kapitel Upload'), ParsedCategory('96.1', 'Abschnitt', parent='96')],
        phrases=[ParsedPhrase('96101', 'Aus der PDF', '96.1', ['Text aus der PDF.'])],
    )
    TARGET = 'objektverwaltung.bvs_import.parse_pdf'

    def setUp(self):
        super().setUp()
        self.manager = make_user('chef', BVS_MANAGE)
        self.client.force_login(self.manager)
        self.url = reverse('objektverwaltung:bvs_phrase_import')

    def pdf(self, content=b'%PDF-1.4 test', name='Mustersaetze.pdf'):
        from django.core.files.uploadedfile import SimpleUploadedFile
        return SimpleUploadedFile(name, content, content_type='application/pdf')

    def test_requires_manage_permission(self):
        self.client.force_login(self.user)  # nur bvs_view/bvs_edit
        self.assertEqual(self.client.get(self.url).status_code, 403)
        self.client.force_login(self.manager)
        self.assertContains(self.client.get(reverse('objektverwaltung:bvs_phrase_list')), self.url)

    def test_rejects_non_pdf(self):
        response = self.client.post(self.url, {'pdf': self.pdf(name='liste.docx')})
        self.assertContains(response, 'Nur PDF-Dateien')
        response = self.client.post(self.url, {'pdf': self.pdf(content=b'kein pdf')})
        self.assertContains(response, 'keine gültige PDF')
        self.assertFalse(BVSPhrase.objects.filter(code='96101').exists())

    def test_dry_run_saves_nothing(self):
        with mock.patch(self.TARGET, return_value=self.PARSED):
            response = self.client.post(self.url, {'pdf': self.pdf(), 'dry_run': 'on'})
        self.assertContains(response, 'Probelauf')
        self.assertContains(response, 'Mustersätze: 1 neu')
        self.assertFalse(BVSPhrase.objects.filter(code='96101').exists())

    def test_import_and_update(self):
        with mock.patch(self.TARGET, return_value=self.PARSED):
            response = self.client.post(self.url, {'pdf': self.pdf()})
        self.assertEqual(response.status_code, 302)
        phrase = BVSPhrase.objects.get(code='96101')
        self.assertEqual(phrase.category.number, '96.1')

        phrase.text = 'Überarbeitet'
        phrase.save()
        with mock.patch(self.TARGET, return_value=self.PARSED):
            self.client.post(self.url, {'pdf': self.pdf()})
        phrase.refresh_from_db()
        self.assertEqual(phrase.text, 'Überarbeitet')
        with mock.patch(self.TARGET, return_value=self.PARSED):
            self.client.post(self.url, {'pdf': self.pdf(), 'update': 'on'})
        phrase.refresh_from_db()
        self.assertEqual(phrase.text, 'Text aus der PDF.')

    def test_unreadable_pdf_shows_error(self):
        with mock.patch(self.TARGET, side_effect=RuntimeError('pdftotext (poppler-utils) ist nicht installiert.')):
            response = self.client.post(self.url, {'pdf': self.pdf()})
        self.assertContains(response, 'poppler-utils')


class BVSUserManagementTests(TestCase):
    """Zugriffsstufe über die Benutzerverwaltung (Karte „Brandverhütungsschau“)."""

    def setUp(self):
        from core.models.system_settings import SystemSettings
        settings_obj = SystemSettings.objects.first() or SystemSettings.objects.create()
        settings_obj.objektverwaltung_enabled = True
        settings_obj.save()
        self.admin = User.objects.create_user(username='verwalter', password='pw')
        self.admin.user_permissions.add(*Permission.objects.filter(
            content_type__app_label='core', codename__in=['manage_users', 'assign_roles']))
        self.target = User.objects.create_user(username='ziel', password='pw', first_name='Max', last_name='Ziel')
        self.url = reverse('core:user_bvs_permissions', args=[self.target.pk])
        self.client.force_login(self.admin)

    def fresh_target(self):
        return User.objects.get(pk=self.target.pk)  # Rechte-Cache verwerfen

    def test_card_shows_current_level(self):
        response = self.client.get(reverse('core:user_detail', args=[self.target.pk]))
        self.assertContains(response, 'Brandverhütungsschau')
        self.assertContains(response, 'name="bvs_level" value="none" checked')

    def test_levels_assign_exactly_one_group_and_object_read_access(self):
        self.client.post(self.url, {'bvs_level': 'edit'})
        target = self.fresh_target()
        self.assertEqual(list(target.groups.values_list('name', flat=True)), ['BVS Sachbearbeiter'])
        self.assertTrue(target.has_perm('objektverwaltung.bvs_edit'))
        self.assertTrue(target.has_perm('objektverwaltung.view_buildingobject'))
        self.assertFalse(target.has_perm('objektverwaltung.bvs_manage'))

        self.client.post(self.url, {'bvs_level': 'manage'})
        target = self.fresh_target()
        self.assertEqual(list(target.groups.values_list('name', flat=True)), ['BVS Verantwortlicher'])
        self.assertTrue(target.has_perm('objektverwaltung.bvs_manage'))

        response = self.client.get(reverse('core:user_detail', args=[self.target.pk]))
        self.assertContains(response, 'name="bvs_level" value="manage" checked')

        target.user_permissions.add(Permission.objects.get(codename='bvs_view'))
        self.client.post(self.url, {'bvs_level': 'none'})
        target = self.fresh_target()
        self.assertFalse(target.groups.exists())
        self.assertFalse(target.has_perm('objektverwaltung.bvs_view'))  # auch Einzelrecht entfernt

    def test_other_groups_stay_untouched(self):
        other = Group.objects.create(name='Sachbearbeiter Objektverwaltung')
        self.target.groups.add(other)
        self.client.post(self.url, {'bvs_level': 'view'})
        names = set(self.fresh_target().groups.values_list('name', flat=True))
        self.assertEqual(names, {'Sachbearbeiter Objektverwaltung', 'BVS Leser'})

    def test_requires_assign_roles(self):
        self.admin.user_permissions.remove(Permission.objects.get(content_type__app_label='core', codename='assign_roles'))
        self.client.post(self.url, {'bvs_level': 'manage'})
        self.assertFalse(self.fresh_target().groups.exists())

    def test_invalid_level_is_rejected(self):
        self.client.post(self.url, {'bvs_level': 'alles'})
        self.assertFalse(self.fresh_target().groups.exists())
