from django.test import TestCase
from django.urls import reverse

from core.models import User


CSV = (
    "Benutzername;Vorname;Nachname;E-Mail;Personalnummer;Benutzer-Rollen;Aktiv;Ticket erstellen;Ticket bearbeiten\r\n"
    ";Max;Mustermann;max@example.com;99001;;Ja;Ja;Nein\r\n"
    ";Erika;Musterfrau;erika@example.com;99002;;Ja;Nein;Nein\r\n"
)


class UserImportRandomPasswordTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(username='tmpadmin', password='x' * 20, email='a@b.de')
        self.client.force_login(self.admin)

    def test_import_creates_users_with_distinct_random_passwords(self):
        from django.core.files.uploadedfile import SimpleUploadedFile

        upload = SimpleUploadedFile('u.csv', CSV.encode('utf-8'), content_type='text/csv')
        resp = self.client.post(reverse('core:user_import_validate'), {'import_file': upload})
        self.assertEqual(resp.status_code, 200)
        session_key = resp.context['session_key']
        self.assertEqual(resp.context['valid_count'], 2)

        resp = self.client.post(reverse('core:user_import_execute'), {'session_key': session_key})
        self.assertEqual(resp.status_code, 200)
        creds = resp.context['credentials']
        self.assertEqual(len(creds), 2)
        pw_key = resp.context['password_key']

        passwords = {c['password'] for c in creds}
        self.assertEqual(len(passwords), 2, 'Passwörter müssen unterschiedlich sein')
        self.assertNotIn('Feuerwehr.0112', passwords)

        for c in creds:
            u = User.objects.get(username=c['username'])
            self.assertTrue(u.check_password(c['password']))
            self.assertTrue(u.password_must_change)

        resp = self.client.get(reverse('core:user_import_passwords'), {'key': pw_key})
        self.assertEqual(resp.status_code, 200)
        body = resp.content.decode('utf-8-sig')
        for c in creds:
            self.assertIn(c['password'], body)

        # Neuer Import-Start löscht die Passwörter aus der Session
        self.client.get(reverse('core:user_import'))
        resp = self.client.get(reverse('core:user_import_passwords'), {'key': pw_key})
        self.assertEqual(resp.status_code, 302)
