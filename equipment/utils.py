"""
Equipment Utilities
OCR und Dokumenten-Verarbeitung
"""

import os
import logging
from PIL import Image
from pdf2image import convert_from_path
import pytesseract

logger = logging.getLogger(__name__)


def extract_text_from_file(file_path):
    """
    Extrahiert Text aus PDF oder Bilddatei mittels OCR

    Args:
        file_path: Pfad zur Datei

    Returns:
        str: Extrahierter Text
    """
    if not os.path.exists(file_path):
        logger.error(f"Datei nicht gefunden: {file_path}")
        return ""

    file_extension = os.path.splitext(file_path)[1].lower()
    extracted_text = ""

    try:
        if file_extension == '.pdf':
            # PDF zu Bildern konvertieren und OCR anwenden
            extracted_text = extract_text_from_pdf(file_path)
        elif file_extension in ['.jpg', '.jpeg', '.png', '.tiff', '.bmp', '.gif']:
            # Direkt OCR auf Bild anwenden
            extracted_text = extract_text_from_image(file_path)
        else:
            logger.warning(f"Nicht unterstütztes Dateiformat: {file_extension}")
            return ""

        logger.info(f"Text erfolgreich extrahiert aus {file_path} ({len(extracted_text)} Zeichen)")
        return extracted_text.strip()

    except Exception as e:
        logger.error(f"Fehler beim Extrahieren von Text aus {file_path}: {str(e)}")
        return ""


def extract_text_from_pdf(pdf_path):
    """
    Extrahiert Text aus PDF mittels OCR

    Args:
        pdf_path: Pfad zur PDF-Datei

    Returns:
        str: Extrahierter Text
    """
    try:
        # PDF zu Bildern konvertieren (erste 50 Seiten)
        images = convert_from_path(pdf_path, first_page=1, last_page=50, dpi=300)

        extracted_text = []
        for i, image in enumerate(images, start=1):
            logger.debug(f"Verarbeite Seite {i}/{len(images)}")
            text = pytesseract.image_to_string(image, lang='deu+eng')
            extracted_text.append(text)

        return "\n\n".join(extracted_text)

    except Exception as e:
        logger.error(f"Fehler beim Verarbeiten von PDF {pdf_path}: {str(e)}")
        return ""


def extract_text_from_image(image_path):
    """
    Extrahiert Text aus Bild mittels OCR

    Args:
        image_path: Pfad zur Bilddatei

    Returns:
        str: Extrahierter Text
    """
    try:
        image = Image.open(image_path)

        # Konvertiere zu RGB falls notwendig
        if image.mode != 'RGB':
            image = image.convert('RGB')

        # OCR mit deutscher und englischer Sprache
        text = pytesseract.image_to_string(image, lang='deu+eng')

        return text

    except Exception as e:
        logger.error(f"Fehler beim Verarbeiten von Bild {image_path}: {str(e)}")
        return ""


def process_equipment_manual(equipment_item):
    """
    Verarbeitet das hochgeladene Handbuch eines Equipment-Items
    und extrahiert den Text mittels OCR

    Args:
        equipment_item: EquipmentItem Instanz

    Returns:
        bool: True wenn erfolgreich, False bei Fehler
    """
    if not equipment_item.manual_document:
        return False

    try:
        file_path = equipment_item.manual_document.path
        extracted_text = extract_text_from_file(file_path)

        if extracted_text:
            equipment_item.manual_ocr_text = extracted_text
            equipment_item.save(update_fields=['manual_ocr_text'])
            logger.info(f"OCR-Text erfolgreich gespeichert für {equipment_item}")
            return True
        else:
            logger.warning(f"Kein Text extrahiert für {equipment_item}")
            return False

    except Exception as e:
        logger.error(f"Fehler beim Verarbeiten des Handbuchs für {equipment_item}: {str(e)}")
        return False
