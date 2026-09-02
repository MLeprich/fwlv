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
