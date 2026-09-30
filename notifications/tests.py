from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Notification

User = get_user_model()

# Create your tests here.


class MarkAllAsReadTests(TestCase):
    """„Alle als gelesen markieren“ aus der Glocke: Formular-POST führt zurück, kein 500."""

    def setUp(self):
        self.user = User.objects.create_user(username='glocke', password='pw')
        self.client.force_login(self.user)
        for i in range(3):
            Notification.objects.create(recipient=self.user, title=f'N{i}', message='m')

    def test_manager_queryset_methods(self):
        self.assertEqual(Notification.objects.filter(recipient=self.user).unread().count(), 3)

    def test_form_post_marks_and_redirects(self):
        response = self.client.post(reverse('notifications:mark_all_read'), HTTP_REFERER='/dashboard/')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], '/dashboard/')
        self.assertEqual(Notification.objects.filter(recipient=self.user, is_read=False).count(), 0)

    def test_ajax_post_returns_json(self):
        response = self.client.post(reverse('notifications:mark_all_read'), HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.json(), {'success': True, 'count': 3})
