"""
Django Signals für automatische OCR-Verarbeitung
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from .models import Document
from .utils import extract_text_from_file
import logging
import os

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Document)
def auto_process_ocr(sender, instance, created, **kwargs):
    """
    Automatische OCR-Verarbeitung nach Document-Upload

    Wird ausgeführt:
    - Bei neuem Document (created=True)
    - Wenn noch nicht verarbeitet (ocr_processed=False)
    - Wenn Datei vorhanden ist
    """

    # Nur verarbeiten wenn:
    # 1. Neu erstellt ODER noch nicht verarbeitet
    # 2. Datei vorhanden
    # 3. Relevanter Dateityp

    if instance.ocr_processed:
        return  # Bereits verarbeitet

    if not instance.file:
        return  # Keine Datei

    file_path = instance.file.path

    if not os.path.exists(file_path):
        logger.warning(f"Datei nicht gefunden für OCR: {file_path}")
        return

    # Nur bestimmte Dateitypen verarbeiten
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()

    supported_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.docx']

    if ext not in supported_extensions:
        logger.info(f"Dateityp {ext} nicht für OCR unterstützt")
        return

    try:
        logger.info(f"Starte OCR für Dokument: {instance.title} (ID: {instance.id})")

        # Text extrahieren
        text = extract_text_from_file(file_path)

        if text:
            # Text speichern (verhindere erneutes Signal durch update_fields)
            Document.objects.filter(pk=instance.pk).update(
                ocr_text=text,
                ocr_processed=True,
                ocr_processed_at=timezone.now()
            )

            char_count = len(text)
            word_count = len(text.split())
            logger.info(
                f"OCR erfolgreich für '{instance.title}': "
                f"{char_count} Zeichen, {word_count} Wörter"
            )
        else:
            # Keine Text-Extraktion möglich, als verarbeitet markieren
            Document.objects.filter(pk=instance.pk).update(
                ocr_processed=True,
                ocr_processed_at=timezone.now()
            )
            logger.info(f"Keine Text-Extraktion möglich für '{instance.title}'")

    except Exception as e:
        logger.error(f"Fehler bei OCR-Verarbeitung für '{instance.title}': {e}", exc_info=True)
