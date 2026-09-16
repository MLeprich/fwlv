from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse

from .models import Dashboard, MonitorProfile, Widget

User = get_user_model()


class DashboardKioskTests(TestCase):
    """Vollbild-Link per Link-Name, Slug-Erzeugung und Ausrichtung."""

    def setUp(self):
        self.user = User.objects.create_user(username='monitor', password='pw')
        self.user.user_permissions.add(
            *Permission.objects.filter(content_type__app_label='info_monitors',
                                       codename__in=['add_dashboard', 'change_dashboard', 'view_dashboard'])
        )
        self.profile = MonitorProfile.objects.create(name='Wache 1', created_by=self.user, updated_by=self.user)

    def _dashboard(self, name='Haupteingang Monitor', **kwargs):
        kwargs.setdefault('created_by', self.user)
        kwargs.setdefault('updated_by', self.user)
        return Dashboard.objects.create(profile=self.profile, name=name, **kwargs)

    def test_slug_generated_from_name_and_unique(self):
        first = self._dashboard('Test')
        second = self._dashboard('test')
        self.assertEqual(first.slug, 'test')
        self.assertEqual(second.slug, 'test-2')
        self.assertEqual(first.get_kiosk_url(), '/monitors/kiosk/test/')
        custom = self._dashboard('Foyer', slug='foyer-links')
        self.assertEqual(custom.get_kiosk_url(), '/monitors/kiosk/foyer-links/')

    def test_public_dashboard_kiosk_without_login(self):
        dashboard = self._dashboard(is_public=True)
        Widget.objects.create(dashboard=dashboard, title='Uhr', widget_type='clock',
                              x_position=10, y_position=20, canvas_width=400, height=300,
                              created_by=self.user, updated_by=self.user)
        response = self.client.get('/monitors/kiosk/haupteingang-monitor/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="dashboard-canvas"')
        self.assertContains(response, 'data-canvas-width="1920"')
        self.assertContains(response, 'left: 10px; top: 20px;')
        dashboard.refresh_from_db()
        self.assertEqual(dashboard.view_count, 1)
        self.assertEqual(self.client.get('/monitors/kiosk/gibt-es-nicht/').status_code, 404)

    def test_private_dashboard_kiosk_requires_login_and_permission(self):
        dashboard = self._dashboard(is_public=False)
        url = dashboard.get_kiosk_url()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response['Location'])
        stranger = User.objects.create_user(username='fremd', password='pw')
        self.client.force_login(stranger)
        self.assertEqual(self.client.get(url).status_code, 403)
        dashboard.allowed_users.add(stranger)
        self.assertEqual(self.client.get(url).status_code, 200)

    def test_orientation_and_settings_view(self):
        dashboard = self._dashboard()
        self.assertFalse(dashboard.is_portrait)
        self.assertEqual(dashboard.orientation_display, 'Querformat')
        widget = Widget.objects.create(dashboard=dashboard, title='Text', widget_type='text',
                                       x_position=1500, y_position=100, canvas_width=400, height=300,
                                       created_by=self.user, updated_by=self.user)
        self.client.force_login(self.user)
        editor_url = reverse('info_monitors:dashboard_editor', args=[dashboard.pk])
        response = self.client.get(editor_url)
        self.assertContains(response, 'Monitor-Einstellungen')
        self.assertContains(response, '/monitors/kiosk/haupteingang-monitor/')
        self.assertContains(response, 'id="canvas-stage"')

        # Auf Hochformat umschalten: Breite/Höhe werden getauscht, Widget bleibt im Canvas
        response = self.client.post(reverse('info_monitors:dashboard_settings', args=[dashboard.pk]), {
            'canvas_width': 1920, 'canvas_height': 1080, 'orientation': 'portrait', 'slug': 'Foyer Hoch',
        })
        self.assertRedirects(response, editor_url)
        dashboard.refresh_from_db()
        widget.refresh_from_db()
        self.assertEqual((dashboard.canvas_width, dashboard.canvas_height), (1080, 1920))
        self.assertTrue(dashboard.is_portrait)
        self.assertEqual(dashboard.slug, 'foyer-hoch')
        self.assertEqual(widget.x_position, 1080 - 400)

        # Öffentlich schalten: Vollbild-Link ohne Anmeldung
        self.client.post(reverse('info_monitors:dashboard_settings', args=[dashboard.pk]), {
            'canvas_width': 1080, 'canvas_height': 1920, 'slug': 'foyer-hoch', 'is_public': '1',
        })
        dashboard.refresh_from_db()
        self.assertTrue(dashboard.is_public)
        self.client.logout()
        self.assertEqual(self.client.get(dashboard.get_kiosk_url()).status_code, 200)
        self.client.force_login(self.user)
        self.client.post(reverse('info_monitors:dashboard_settings', args=[dashboard.pk]), {
            'canvas_width': 1080, 'canvas_height': 1920, 'slug': 'foyer-hoch',
        })
        dashboard.refresh_from_db()
        self.assertFalse(dashboard.is_public)

        # Doppelter Link-Name wird abgewiesen
        self._dashboard('Anderer', slug='anderer')
        self.client.post(reverse('info_monitors:dashboard_settings', args=[dashboard.pk]), {
            'canvas_width': 1080, 'canvas_height': 1920, 'slug': 'anderer',
        })
        dashboard.refresh_from_db()
        self.assertEqual(dashboard.slug, 'foyer-hoch')

    def test_create_form_with_optional_slug_and_list_shows_link(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('info_monitors:dashboard_create'), {
            'name': 'Werkstatt Monitor', 'slug': '', 'profile': self.profile.pk, 'use_canvas_layout': 'on',
            'canvas_width': 1080, 'canvas_height': 1920, 'theme': 'light', 'is_public': 'on',
            'auto_refresh': 'on', 'refresh_interval': 30,
        })
        dashboard = Dashboard.objects.get(name='Werkstatt Monitor')
        self.assertRedirects(response, reverse('info_monitors:dashboard_editor', args=[dashboard.pk]))
        self.assertEqual(dashboard.slug, 'werkstatt-monitor')
        self.assertTrue(dashboard.is_portrait)
        response = self.client.get(reverse('info_monitors:dashboard_list'))
        self.assertContains(response, '/monitors/kiosk/werkstatt-monitor/')
        response = self.client.get(reverse('info_monitors:dashboard_detail', args=[dashboard.pk]))
        self.assertContains(response, 'Vollbild-Link')
        self.assertContains(response, 'Hochformat')
