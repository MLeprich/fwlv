"""
Celery Tasks für asynchrone Dokumenten-Verarbeitung
"""

from celery import shared_task
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def process_document_ocr(self, document_id):
    """
    Asynchrone OCR-Verarbeitung für hochgeladene Dokumente

    Args:
        document_id: ID des Document-Objekts

    Returns:
        dict mit Status und Ergebnis
    """
    from documents.models import Document
    from documents.utils import extract_text_from_file

    try:
        # Dokument laden
        document = Document.objects.get(id=document_id)

        logger.info(f"Starte OCR-Verarbeitung für Dokument #{document_id}: {document.title}")

        # Datei-Pfad
        file_path = document.file.path

        # Text extrahieren
        extracted_text = extract_text_from_file(file_path, document.mime_type)

        if extracted_text:
            # Text in Datenbank speichern
            document.ocr_text = extracted_text
            document.ocr_processed = True
            document.ocr_processed_at = timezone.now()
            document.save(update_fields=['ocr_text', 'ocr_processed', 'ocr_processed_at'])

            logger.info(f"OCR erfolgreich: {len(extracted_text)} Zeichen extrahiert")

            return {
                'status': 'success',
                'document_id': document_id,
                'text_length': len(extracted_text),
                'message': f'OCR erfolgreich: {len(extracted_text)} Zeichen'
            }
        else:
            # Kein Text extrahierbar (z.B. ZIP-Datei)
            document.ocr_processed = True
            document.ocr_processed_at = timezone.now()
            document.save(update_fields=['ocr_processed', 'ocr_processed_at'])

            logger.info(f"Kein Text extrahierbar für Dokument #{document_id}")

            return {
                'status': 'no_text',
                'document_id': document_id,
                'message': 'Kein Text extrahierbar (Dateityp nicht unterstützt)'
            }

    except Document.DoesNotExist:
        logger.error(f"Dokument #{document_id} nicht gefunden")
        return {
            'status': 'error',
            'document_id': document_id,
            'message': 'Dokument nicht gefunden'
        }

    except Exception as exc:
        logger.error(f"Fehler bei OCR-Verarbeitung für Dokument #{document_id}: {exc}")

        # Retry bei Fehler (max 3x)
        try:
            raise self.retry(exc=exc, countdown=60)  # Retry nach 60 Sekunden
        except self.MaxRetriesExceededError:
            logger.error(f"Max Retries erreicht für Dokument #{document_id}")
            return {
                'status': 'error',
                'document_id': document_id,
                'message': str(exc)
            }


@shared_task
def bulk_process_ocr():
    """
    Verarbeitet alle Dokumente ohne OCR in einem Batch

    Nützlich für Migration oder manuelle Trigger
    """
    from documents.models import Document

    # Finde alle Dokumente ohne OCR
    documents = Document.objects.filter(
        ocr_processed=False
    ).values_list('id', flat=True)[:100]  # Max 100 pro Batch

    logger.info(f"Starte Bulk-OCR für {documents.count()} Dokumente")

    results = []
    for doc_id in documents:
        result = process_document_ocr.delay(doc_id)
        results.append(result.id)

    return {
        'status': 'success',
        'documents_queued': len(results),
        'task_ids': results
    }
