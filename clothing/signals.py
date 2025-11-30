"""
Django Signals für Clothing Items - OCR-Verarbeitung
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import ClothingItem
from documents.utils import extract_text_from_file
import logging
import os

logger = logging.getLogger(__name__)


@receiver(post_save, sender=ClothingItem)
def process_clothing_manual_ocr(sender, instance, created, **kwargs):
    """
    Automatische OCR-Verarbeitung für Clothing Item Handbücher/Pflegeanleitungen
    """

    # Nur bei neuem Upload verarbeiten
    if not created and not instance._state.adding:
        # Prüfe ob manual_document geändert wurde
        if instance.pk:
            try:
                old_instance = ClothingItem.objects.get(pk=instance.pk)
                if old_instance.manual_document == instance.manual_document:
                    return  # Keine Änderung
            except ClothingItem.DoesNotExist:
                pass

    # Verarbeite manual_document
    if instance.manual_document:
        file_path = instance.manual_document.path

        if os.path.exists(file_path):
            try:
                logger.info(f"Starte OCR für Clothing Item Handbuch: {instance.name} (ID: {instance.id})")

                text = extract_text_from_file(file_path)

                if text:
                    logger.info(
                        f"OCR erfolgreich für Clothing Item '{instance.name}': "
                        f"{len(text)} Zeichen extrahiert aus Handbuch"
                    )
                else:
                    logger.info(f"Keine Text-Extraktion möglich für '{instance.name}' Handbuch")

            except Exception as e:
                logger.error(f"Fehler bei OCR-Verarbeitung für Clothing Item '{instance.name}': {e}", exc_info=True)
