from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from organization.models import VolunteerUnit
from permissions.constants import Roles
from permissions.management.commands.setup_verwaltungsrollen import setup_verwaltungsrollen

from .models import Person

User = get_user_model()


class FFVerwaltungRollenTests(TestCase):
    """FF-Verwaltung: FF Verwalter sieht alle Einheiten, Einheitsführer nur die eigene."""

    @classmethod
    def setUpTestData(cls):
        setup_verwaltungsrollen()
        Group.objects.get_or_create(name=Roles.STANDARD_USER)
        cls.unit_a = VolunteerUnit.objects.create(name='LZ Alpha', sort_order=1)
        cls.unit_b = VolunteerUnit.objects.create(name='LZ Beta', sort_order=2)
        creator = User.objects.create_user(username='creator', password='pw')
        audit = {'created_by': creator, 'updated_by': creator}
        cls.person_a = Person.objects.create(first_name='Anna', last_name='Alpha', personnel_number='FF-A1',
                                             is_volunteer_fire_brigade=True, volunteer_unit=cls.unit_a, **audit)
        cls.person_b = Person.objects.create(first_name='Bernd', last_name='Beta', personnel_number='FF-B1',
                                             is_volunteer_fire_brigade=True, volunteer_unit=cls.unit_b, **audit)

        cls.ff_verwalter = User.objects.create_user(username='ffverwalter', password='pw')
        cls.ff_verwalter.groups.add(Group.objects.get(name=Roles.FF_VERWALTER))

        cls.fuehrer = User.objects.create_user(username='fuehrer', password='pw')
        cls.fuehrer.groups.add(Group.objects.get(name=Roles.FF_EINHEITSFUEHRER))
        leader_person = Person.objects.create(first_name='Frida', last_name='Führer', personnel_number='FF-L1',
                                              user=cls.fuehrer, volunteer_unit=cls.unit_a, **audit)
        cls.unit_a.leader = leader_person
        cls.unit_a.save()

        cls.personaler = User.objects.create_user(username='personaler', password='pw')
        cls.personaler.groups.add(Group.objects.get(name=Roles.PERSONALVERWALTER))

        cls.normal = User.objects.create_user(username='normal', password='pw')
        cls.normal.groups.add(Group.objects.get(name=Roles.STANDARD_USER))

    def test_ff_verwalter_sieht_alle_einheiten(self):
        self.client.force_login(self.ff_verwalter)
        resp = self.client.get(reverse('personnel:ff_dashboard'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'LZ Alpha')
        self.assertContains(resp, 'LZ Beta')
        # Person aus jeder Einheit bearbeitbar
        for person in (self.person_a, self.person_b):
            self.assertEqual(self.client.get(reverse('personnel:ff_person_edit', args=[person.pk])).status_code, 200)

    def test_ff_verwalter_ohne_allgemeine_personalliste_und_benutzer(self):
        self.client.force_login(self.ff_verwalter)
        resp = self.client.get(reverse('personnel:list'))
        self.assertRedirects(resp, reverse('personnel:ff_dashboard'))
        self.assertEqual(self.client.get(reverse('core:user_list')).status_code, 302)

    def test_einheitsfuehrer_nur_eigene_einheit(self):
        self.client.force_login(self.fuehrer)
        resp = self.client.get(reverse('personnel:ff_dashboard'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'LZ Alpha')
        self.assertNotContains(resp, 'LZ Beta')
        self.assertEqual(self.client.get(reverse('personnel:ff_person_edit', args=[self.person_a.pk])).status_code, 200)
        resp = self.client.get(reverse('personnel:ff_person_edit', args=[self.person_b.pk]))
        self.assertRedirects(resp, reverse('personnel:ff_dashboard'))

    def test_personalverwalter_hat_personal_aber_keine_ff_verwaltung(self):
        self.client.force_login(self.personaler)
        self.assertEqual(self.client.get(reverse('personnel:list')).status_code, 200)
        self.assertEqual(self.client.get(reverse('personnel:update', args=[self.person_a.pk])).status_code, 200)
        resp = self.client.get(reverse('personnel:ff_dashboard'))
        self.assertRedirects(resp, reverse('core:dashboard'), fetch_redirect_response=False)

    def test_standardnutzer_ohne_ff_verwaltung(self):
        self.client.force_login(self.normal)
        resp = self.client.get(reverse('personnel:ff_dashboard'))
        self.assertRedirects(resp, reverse('core:dashboard'), fetch_redirect_response=False)
        self.assertFalse(self.normal.has_perm('personnel.manage_ff_person'))

    def test_manage_ff_person_recht_bei_ff_rollen(self):
        for role in (Roles.FF_EINHEITSFUEHRER, Roles.FF_VERTRETER, Roles.FF_VERWALTER, Roles.ADMINISTRATOR):
            self.assertTrue(Group.objects.get(name=role).permissions.filter(codename='manage_ff_person').exists(), role)
        self.assertFalse(Group.objects.get(name=Roles.PERSONALVERWALTER).permissions.filter(codename='manage_ff_person').exists())
