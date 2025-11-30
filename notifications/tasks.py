"""
Celery Tasks für Benachrichtigungen
Asynchroner Versand von E-Mails und Benachrichtigungen
"""

from celery import shared_task
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import get_user_model

from .models import Notification, NotificationPreference
from core.models import UserSettings

User = get_user_model()


@shared_task(bind=True, max_retries=3)
def send_notification_email(self, notification_id):
    """
    Sendet eine E-Mail-Benachrichtigung

    Args:
        notification_id: ID der Notification
    """
    try:
        notification = Notification.objects.get(id=notification_id)
        user = notification.recipient

        # Prüfe ob User E-Mail-Benachrichtigungen aktiviert hat
        try:
            user_settings = UserSettings.objects.get(user=user)
            if not user_settings.email_notifications:
                return f"E-Mail deaktiviert für User {user.username}"
        except UserSettings.DoesNotExist:
            pass  # Wenn keine Settings, sende trotzdem

        # Prüfe NotificationPreference (falls vorhanden)
        try:
            prefs = NotificationPreference.objects.get(user=user)
            if not prefs.email_enabled:
                return f"E-Mail deaktiviert (NotificationPreference) für User {user.username}"
        except NotificationPreference.DoesNotExist:
            pass

        # Render HTML und Text Templates
        html_content = render_to_string('emails/notification.html', {
            'notification': notification,
            'user': user,
        })
        text_content = render_to_string('emails/notification.txt', {
            'notification': notification,
            'user': user,
        })

        # Erstelle E-Mail mit HTML und Text Version
        subject = f"[FLVS] {notification.title}"
        from_email = settings.DEFAULT_FROM_EMAIL
        to_email = user.email

        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=from_email,
            to=[to_email]
        )
        email.attach_alternative(html_content, "text/html")
        email.send()

        return f"E-Mail erfolgreich gesendet an {to_email}"

    except Notification.DoesNotExist:
        return f"Notification {notification_id} nicht gefunden"
    except Exception as exc:
        # Retry nach Fehler
        raise self.retry(exc=exc, countdown=60)


@shared_task
def send_test_email(user_id):
    """
    Sendet eine Test-E-Mail an einen Benutzer

    Args:
        user_id: ID des Users
    """
    try:
        user = User.objects.get(id=user_id)

        html_content = render_to_string('emails/test_email.html', {
            'user': user,
            'current_time': timezone.now(),
        })
        text_content = render_to_string('emails/test_email.txt', {
            'user': user,
            'current_time': timezone.now(),
        })

        subject = "[FLVS] Test-Email"
        from_email = settings.DEFAULT_FROM_EMAIL
        to_email = user.email

        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=from_email,
            to=[to_email]
        )
        email.attach_alternative(html_content, "text/html")
        email.send()

        return f"Test-E-Mail erfolgreich gesendet an {to_email}"

    except User.DoesNotExist:
        return f"User {user_id} nicht gefunden"
    except Exception as e:
        return f"Fehler beim Senden: {str(e)}"


@shared_task
def send_bulk_notifications(user_ids, title, message, notification_type='info', category='general'):
    """
    Sendet Benachrichtigungen an mehrere Benutzer

    Args:
        user_ids: Liste von User-IDs
        title: Benachrichtigungs-Titel
        message: Benachrichtigungs-Text
        notification_type: Typ (info, warning, error, success)
        category: Kategorie
    """
    created_count = 0

    for user_id in user_ids:
        try:
            user = User.objects.get(id=user_id)

            # Erstelle Notification
            notification = Notification.objects.create(
                recipient=user,
                title=title,
                message=message,
                notification_type=notification_type,
                category=category
            )

            # Sende E-Mail asynchron
            send_notification_email.delay(notification.id)
            created_count += 1

        except User.DoesNotExist:
            continue

    return f"{created_count} Benachrichtigungen erstellt und versendet"


@shared_task
def send_daily_summary():
    """
    Sendet tägliche Zusammenfassung an alle User die es aktiviert haben
    """
    # Hole alle User mit aktivierter täglicher Zusammenfassung
    preferences = NotificationPreference.objects.filter(daily_summary=True)

    for pref in preferences:
        user = pref.user

        # Hole ungelesene Notifications der letzten 24h
        yesterday = timezone.now() - timezone.timedelta(days=1)
        notifications = Notification.objects.filter(
            recipient=user,
            is_read=False,
            created_at__gte=yesterday
        )

        if notifications.exists():
            # TODO: Erstelle Summary-Template
            html_content = render_to_string('emails/daily_summary.html', {
                'user': user,
                'notifications': notifications,
                'count': notifications.count(),
            })

            subject = f"[FLVS] Tägliche Zusammenfassung - {notifications.count()} neue Benachrichtigungen"
            send_mail(
                subject=subject,
                message=strip_tags(html_content),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_content,
            )

    return f"Tägliche Zusammenfassung an {preferences.count()} Benutzer gesendet"


@shared_task
def send_weekly_summary():
    """
    Sendet wöchentliche Zusammenfassung an alle User die es aktiviert haben
    """
    preferences = NotificationPreference.objects.filter(weekly_summary=True)

    for pref in preferences:
        user = pref.user

        # Hole Notifications der letzten 7 Tage
        last_week = timezone.now() - timezone.timedelta(days=7)
        notifications = Notification.objects.filter(
            recipient=user,
            created_at__gte=last_week
        )

        if notifications.exists():
            # TODO: Erstelle Weekly-Summary-Template
            html_content = render_to_string('emails/weekly_summary.html', {
                'user': user,
                'notifications': notifications,
                'count': notifications.count(),
            })

            subject = f"[FLVS] Wöchentliche Zusammenfassung - {notifications.count()} Benachrichtigungen"
            send_mail(
                subject=subject,
                message=strip_tags(html_content),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_content,
            )

    return f"Wöchentliche Zusammenfassung an {preferences.count()} Benutzer gesendet"


@shared_task
def cleanup_old_notifications():
    """
    Archiviert abgelaufene Benachrichtigungen
    """
    now = timezone.now()

    # Archiviere abgelaufene Notifications
    expired = Notification.objects.filter(
        expires_at__lt=now,
        is_archived=False
    )

    count = expired.count()
    expired.update(is_archived=True)

    return f"{count} abgelaufene Benachrichtigungen archiviert"
