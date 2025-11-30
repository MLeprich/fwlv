"""
Notification Utility Functions
Helper-Funktionen zum Erstellen von Benachrichtigungen
"""

from .models import Notification, NotificationType, NotificationCategory
from django.contrib.auth import get_user_model

User = get_user_model()


def create_notification(recipient, title, message, notification_type=NotificationType.INFO,
                       category=NotificationCategory.GENERAL, obj=None, action_url='',
                       priority=0, expires_at=None, send_email=True):
    """
    Erstellt eine neue Benachrichtigung

    Args:
        send_email: Wenn True, wird zusätzlich eine E-Mail versendet (default: True)

    Usage:
        create_notification(
            recipient=user,
            title='Fahrzeugprüfung fällig',
            message='Die HU für Fahrzeug LF 10/6 ist in 30 Tagen fällig',
            notification_type=NotificationType.WARNING,
            category=NotificationCategory.VEHICLE,
            obj=vehicle,
            action_url='/vehicles/1/',
            priority=5,
            send_email=True
        )
    """
    notification = Notification(
        recipient=recipient,
        title=title,
        message=message,
        notification_type=notification_type,
        category=category,
        action_url=action_url,
        priority=priority,
        expires_at=expires_at,
    )

    if obj:
        notification.content_object = obj

    notification.save()

    # Sende E-Mail asynchron via Celery
    if send_email:
        from .tasks import send_notification_email
        send_notification_email.delay(notification.id)

    return notification


def notify_user(user_id, title, message, **kwargs):
    """
    Benachrichtigt einen Benutzer (per ID)
    """
    try:
        user = User.objects.get(pk=user_id)
        return create_notification(user, title, message, **kwargs)
    except User.DoesNotExist:
        return None


def notify_users(user_ids, title, message, **kwargs):
    """
    Benachrichtigt mehrere Benutzer

    Usage:
        notify_users(
            user_ids=[1, 2, 3],
            title='Systemwartung',
            message='Am 15.10. findet eine Systemwartung statt',
            notification_type=NotificationType.SYSTEM
        )
    """
    notifications = []
    for user_id in user_ids:
        notification = notify_user(user_id, title, message, **kwargs)
        if notification:
            notifications.append(notification)
    return notifications


def notify_all_users(title, message, **kwargs):
    """
    Benachrichtigt alle aktiven Benutzer
    """
    users = User.objects.filter(is_active=True)
    return [create_notification(user, title, message, **kwargs) for user in users]


def notify_by_role(role_name, title, message, **kwargs):
    """
    Benachrichtigt alle Benutzer mit einer bestimmten Rolle

    Usage:
        notify_by_role(
            role_name='Administrator',
            title='Kritischer Fehler',
            message='Ein kritischer Systemfehler ist aufgetreten',
            notification_type=NotificationType.ERROR,
            priority=10
        )
    """
    users = User.objects.filter(groups__name=role_name, is_active=True).distinct()
    return [create_notification(user, title, message, **kwargs) for user in users]


# ============================================================================
# Spezifische Benachrichtigungs-Funktionen
# ============================================================================

def notify_vehicle_inspection_due(user, vehicle, days_until):
    """
    Benachrichtigung: Fahrzeugprüfung fällig
    """
    return create_notification(
        recipient=user,
        title=f'Fahrzeugprüfung fällig: {vehicle.call_sign}',
        message=f'Die Hauptuntersuchung für {vehicle.call_sign} ist in {days_until} Tagen fällig.',
        notification_type=NotificationType.WARNING if days_until <= 30 else NotificationType.REMINDER,
        category=NotificationCategory.INSPECTION,
        obj=vehicle,
        action_url=f'/vehicles/{vehicle.pk}/',
        priority=5 if days_until <= 30 else 3
    )


def notify_qualification_expiring(user, qualification, days_until):
    """
    Benachrichtigung: Qualifikation läuft ab
    """
    return create_notification(
        recipient=user,
        title=f'Qualifikation läuft ab: {qualification.name}',
        message=f'Die Qualifikation "{qualification.name}" von {qualification.person.get_full_name()} läuft in {days_until} Tagen ab.',
        notification_type=NotificationType.EXPIRY,
        category=NotificationCategory.QUALIFICATION,
        obj=qualification,
        action_url=f'/personnel/{qualification.person.pk}/',
        priority=7 if days_until <= 14 else 4
    )


def notify_low_stock(user, item, current_quantity, min_quantity):
    """
    Benachrichtigung: Niedriger Lagerbestand
    """
    return create_notification(
        recipient=user,
        title=f'Niedriger Lagerbestand: {item}',
        message=f'Der Lagerbestand für "{item}" ist niedrig (Aktuell: {current_quantity}, Minimum: {min_quantity}).',
        notification_type=NotificationType.WARNING,
        category=NotificationCategory.INVENTORY,
        obj=item,
        priority=5
    )


def notify_approval_needed(user, obj, description):
    """
    Benachrichtigung: Freigabe erforderlich
    """
    return create_notification(
        recipient=user,
        title='Freigabe erforderlich',
        message=f'Eine Freigabe wird benötigt für: {description}',
        notification_type=NotificationType.APPROVAL,
        category=NotificationCategory.GENERAL,
        obj=obj,
        priority=8
    )


def notify_order_received(user, order):
    """
    Benachrichtigung: Bestellung eingegangen
    """
    return create_notification(
        recipient=user,
        title=f'Bestellung eingegangen',
        message=f'Ihre Bestellung wurde erfolgreich aufgegeben.',
        notification_type=NotificationType.SUCCESS,
        category=NotificationCategory.ORDER,
        obj=order,
        priority=3
    )


def notify_system_update(user, version, description):
    """
    Benachrichtigung: System-Update
    """
    return create_notification(
        recipient=user,
        title=f'System-Update: Version {version}',
        message=description,
        notification_type=NotificationType.SYSTEM,
        category=NotificationCategory.SYSTEM,
        priority=2
    )


# ============================================================================
# Bulk-Operationen
# ============================================================================

def mark_all_as_read(user):
    """
    Markiert alle Benachrichtigungen eines Benutzers als gelesen
    """
    return Notification.objects.filter(recipient=user).unread().mark_all_as_read()


def archive_old_notifications(days=30):
    """
    Archiviert alte gelesene Benachrichtigungen (älter als X Tage)

    Usage (in Celery-Task):
        from notifications.utils import archive_old_notifications
        archive_old_notifications(days=30)
    """
    from django.utils import timezone
    from datetime import timedelta

    cutoff_date = timezone.now() - timedelta(days=days)

    archived_count = Notification.objects.filter(
        is_read=True,
        is_archived=False,
        created_at__lt=cutoff_date
    ).update(is_archived=True)

    return archived_count


def delete_expired_notifications():
    """
    Löscht abgelaufene Benachrichtigungen

    Usage (in Celery-Task):
        from notifications.utils import delete_expired_notifications
        delete_expired_notifications()
    """
    from django.utils import timezone

    deleted_count, _ = Notification.objects.filter(
        expires_at__lt=timezone.now()
    ).delete()

    return deleted_count
