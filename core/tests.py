from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.test import TestCase
from django.urls import reverse

from permissions.constants import Roles
from permissions.management.commands.setup_verwaltungsrollen import setup_verwaltungsrollen

User = get_user_model()


class BenutzerverwalterTests(TestCase):
    """Benutzerverwaltung über core.manage_users; Administrator-Konten geschützt."""

    @classmethod
    def setUpTestData(cls):
        setup_verwaltungsrollen()
        Group.objects.get_or_create(name=Roles.STANDARD_USER)
        # Administrator hat (wie in setup_permissions) alle Rechte
        admin_group = Group.objects.get(name=Roles.ADMINISTRATOR)
        admin_group.permissions.set(Permission.objects.all())
        cls.admin = User.objects.create_user(username='admin', password='pw')
        cls.admin.groups.add(admin_group)
        cls.verwalter = User.objects.create_user(username='verwalter', password='pw')
        cls.verwalter.groups.add(Group.objects.get(name=Roles.BENUTZERVERWALTER))
        cls.personaler = User.objects.create_user(username='personaler', password='pw')
        cls.personaler.groups.add(Group.objects.get(name=Roles.PERSONALVERWALTER))
        cls.normal = User.objects.create_user(username='normal', password='pw', first_name='Nora', last_name='Normal')

    def test_benutzerverwalter_hat_zugang(self):
        self.client.force_login(self.verwalter)
        self.assertEqual(self.client.get(reverse('core:user_list')).status_code, 200)
        self.assertEqual(self.client.get(reverse('core:user_detail', args=[self.normal.pk])).status_code, 200)
        self.assertEqual(self.client.get(reverse('core:user_edit', args=[self.normal.pk])).status_code, 200)
        self.assertEqual(self.client.get(reverse('core:user_import')).status_code, 200)

    def test_menuelink_nur_mit_recht(self):
        self.client.force_login(self.verwalter)
        self.assertContains(self.client.get(reverse('core:user_list')), reverse('core:user_list'))
        self.client.force_login(self.normal)
        self.assertNotContains(self.client.get(reverse('core:profile')), reverse('core:user_list'))

    def test_personalverwalter_und_standardnutzer_ohne_zugang(self):
        for user in (self.personaler, self.normal):
            self.client.force_login(user)
            resp = self.client.get(reverse('core:user_list'))
            self.assertEqual(resp.status_code, 302, user.username)
            self.assertEqual(resp.url, reverse('core:dashboard'))

    def test_benutzerverwalter_kann_normale_rollen_vergeben(self):
        self.client.force_login(self.verwalter)
        self.client.post(reverse('core:assign_roles', args=[self.normal.pk]),
                         {'action': 'add', 'role': Roles.STANDARD_USER})
        self.assertTrue(self.normal.groups.filter(name=Roles.STANDARD_USER).exists())

    def test_benutzerverwalter_kann_keine_administratorrolle_vergeben(self):
        self.client.force_login(self.verwalter)
        self.client.post(reverse('core:assign_roles', args=[self.normal.pk]),
                         {'action': 'add', 'role': Roles.ADMINISTRATOR})
        self.assertFalse(self.normal.groups.filter(name=Roles.ADMINISTRATOR).exists())
        # Auswahl im Formular enthält die Administrator-Rolle nicht
        resp = self.client.get(reverse('core:user_detail', args=[self.normal.pk]))
        self.assertNotContains(resp, f'<option value="{Roles.ADMINISTRATOR}">')

    def test_benutzerverwalter_darf_administratorkonto_nicht_aendern(self):
        self.client.force_login(self.verwalter)
        # Rolle entziehen
        self.client.post(reverse('core:assign_roles', args=[self.admin.pk]),
                         {'action': 'remove', 'role': Roles.ADMINISTRATOR})
        self.assertTrue(self.admin.groups.filter(name=Roles.ADMINISTRATOR).exists())
        # Stammdaten bearbeiten
        resp = self.client.get(reverse('core:user_edit', args=[self.admin.pk]))
        self.assertRedirects(resp, reverse('core:user_detail', args=[self.admin.pk]))
        resp = self.client.post(reverse('core:user_edit', args=[self.admin.pk]),
                                {'email': 'x@example.de', 'is_active': ''})
        self.assertRedirects(resp, reverse('core:user_detail', args=[self.admin.pk]))
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_active)
        # Passwort setzen
        old_hash = self.admin.password
        self.client.post(reverse('core:user_set_password', args=[self.admin.pk]),
                         {'new_password1': 'Neu.Sicher.2026', 'new_password2': 'Neu.Sicher.2026'})
        self.admin.refresh_from_db()
        self.assertEqual(self.admin.password, old_hash)

    def test_administrator_darf_alles(self):
        self.client.force_login(self.admin)
        self.client.post(reverse('core:assign_roles', args=[self.normal.pk]),
                         {'action': 'add', 'role': Roles.ADMINISTRATOR})
        self.assertTrue(self.normal.groups.filter(name=Roles.ADMINISTRATOR).exists())
        resp = self.client.get(reverse('core:user_edit', args=[self.normal.pk]))
        self.assertEqual(resp.status_code, 200)

    def test_rollen_haben_getrennte_rechte(self):
        benutzer = Group.objects.get(name=Roles.BENUTZERVERWALTER)
        personal = Group.objects.get(name=Roles.PERSONALVERWALTER)
        self.assertTrue(benutzer.permissions.filter(codename='manage_users').exists())
        self.assertFalse(benutzer.permissions.filter(content_type__app_label='personnel').exists())
        self.assertTrue(personal.permissions.filter(codename='change_person').exists())
        self.assertFalse(personal.permissions.filter(content_type__app_label__in=['core', 'auth']).exists())
        self.assertFalse(personal.permissions.filter(codename='manage_ff_person').exists())
