"""
Celery-Tasks für die Dienstausweis-Verwaltung.
"""

import logging

from celery import shared_task

from .services import expire_due_cards


logger = logging.getLogger(__name__)


@shared_task(name='idcards.expire_due_cards')
def expire_due_cards_task():
    """
    Setzt alle aktiven Dienstausweise mit überschrittenem valid_until auf EXPIRED.
    Wird von Celery-Beat täglich ausgeführt (siehe management command
    `setup_idcards_schedule`).
    """
    count = expire_due_cards()
    logger.info('idcards.expire_due_cards: %s Karte(n) auf EXPIRED gesetzt.', count)
    return count
