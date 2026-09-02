"""
Objektverwaltung - Signals

Abo-Benachrichtigungen: Folgt ein Nutzer einem Objekt, wird er bei
Änderungen (neue Laufkarte/Plan, neuer/geänderter Ansprechpartner,
Objektänderung) über das interne Notification-System informiert.

Es werden ausschließlich In-App-Benachrichtigungen erzeugt (send_email=False) –
das System versendet bewusst keine E-Mails.
"""

import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import (
    BuildingObject, BuildingPlan, BuildingContact, CompensationMeasure,
    FSDInspectionReport,
)

logger = logging.getLogger(__name__)


def notify_followers(building, title, message):
    """
    Benachrichtigt alle Abonnenten eines Objekts (nur In-App, keine E-Mail).
    Fehler werden geloggt, brechen aber niemals die auslösende Speicher-Operation.
    """
    try:
        from notifications.utils import notify_users
        from notifications.models import NotificationType, NotificationCategory

        user_ids = list(building.followers.values_list('id', flat=True))
        if not user_ids:
            return

        notify_users(
            user_ids,
            title=title,
            message=message,
            notification_type=NotificationType.INFO,
            category=NotificationCategory.GENERAL,
            obj=building,
            action_url=building.get_absolute_url(),
            send_email=False,
        )
    except Exception:  # pragma: no cover - Benachrichtigung darf nie blockieren
        logger.exception("Objektverwaltung: Abo-Benachrichtigung fehlgeschlagen")


@receiver(post_save, sender=BuildingPlan)
def plan_saved(sender, instance, created, **kwargs):
    if not created:
        return
    notify_followers(
        instance.building,
        title=f"Neue Laufkarte/Plan: {instance.building.name}",
        message=f'„{instance.title}" ({instance.get_plan_type_display()}) wurde hinzugefügt.',
    )


@receiver(post_save, sender=BuildingContact)
def contact_saved(sender, instance, created, **kwargs):
    verb = "hinzugefügt" if created else "aktualisiert"
    notify_followers(
        instance.building,
        title=f"Ansprechpartner {verb}: {instance.building.name}",
        message=f"{instance.name}{' (' + instance.role + ')' if instance.role else ''} wurde {verb}.",
    )


@receiver(post_save, sender=CompensationMeasure)
def compensation_saved(sender, instance, created, **kwargs):
    if not created:
        return
    notify_followers(
        instance.building,
        title=f"Neue Kompensationsmaßnahme: {instance.building.name}",
        message=f'„{instance.title}" wurde erfasst (Status: {instance.get_status_display()}).',
    )


@receiver(post_save, sender=BuildingObject)
def object_saved(sender, instance, created, **kwargs):
    if created:
        return
    notify_followers(
        instance,
        title=f"Objektdaten geändert: {instance.name}",
        message="Die Stammdaten des Objekts wurden aktualisiert.",
    )


@receiver(post_save, sender=FSDInspectionReport)
def fsd_report_saved(sender, instance, created, **kwargs):
    if not created:
        return
    depot = instance.depot
    notify_followers(
        depot.building,
        title=f"FSD-Prüfbericht: {depot.building.name}",
        message=f'Prüfbericht vom {instance.inspection_date:%d.%m.%Y} für „{depot.designation}" '
                f'erfasst ({instance.get_result_display()}).',
    )
