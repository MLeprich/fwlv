"""Celery-Tasks für das IUK-Modul."""

import logging

from celery import shared_task

from .services import send_license_reminders

logger = logging.getLogger(__name__)


@shared_task(name='iuk.drone_license_reminders')
def drone_license_reminders_task(lead_days=None):
    """
    Erinnert an ablaufende Drohnenführerscheine.

    Wird von Celery-Beat täglich ausgeführt (siehe Management-Command
    `setup_iuk_schedule`). Ohne Celery kann stattdessen der Command
    `send_drone_license_reminders` per Cron laufen.
    """
    kwargs = {'lead_days': lead_days} if lead_days else {}
    result = send_license_reminders(**kwargs)
    logger.info('iuk.drone_license_reminders: %s', result)
    return result
