"""
Dokumenten-Utils für OCR und Text-Extraktion
"""

import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def extract_text_from_pdf(file_path: str) -> Optional[str]:
    """
    Extrahiert Text aus PDF-Dateien

    Verwendet:
    1. pypdf für Text-Layer (wenn vorhanden)
    2. pytesseract + pdf2image für OCR bei gescannten PDFs
    """
    text = ""

    try:
        # Versuch 1: Text-Layer extrahieren (schnell)
        import pypdf
        with open(file_path, 'rb') as file:
            pdf_reader = pypdf.PdfReader(file)
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"

        # Wenn Text gefunden wurde, fertig
        if text.strip():
            logger.info(f"PDF Text-Layer extrahiert: {len(text)} Zeichen")
            return text.strip()

        # Versuch 2: OCR für gescannte PDFs
        logger.info("Kein Text-Layer gefunden, starte OCR...")
        from pdf2image import convert_from_path
        import pytesseract

        # PDF zu Bildern konvertieren
        images = convert_from_path(file_path, dpi=300)

        for i, image in enumerate(images):
            # OCR auf jedem Bild
            page_text = pytesseract.image_to_string(image, lang='deu+eng')
            text += f"\n--- Seite {i+1} ---\n{page_text}\n"

        logger.info(f"PDF OCR abgeschlossen: {len(text)} Zeichen")
        return text.strip()

    except ImportError as e:
        logger.warning(f"OCR-Bibliotheken nicht installiert: {e}")
        return None
    except Exception as e:
        logger.error(f"Fehler bei PDF-Textextraktion: {e}")
        return None


def extract_text_from_image(file_path: str) -> Optional[str]:
    """
    Extrahiert Text aus Bildern via OCR (Tesseract)

    Unterstützt: JPG, JPEG, PNG, GIF, BMP, TIFF
    """
    try:
        import pytesseract
        from PIL import Image

        # Bild öffnen
        image = Image.open(file_path)

        # OCR durchführen (Deutsch + Englisch)
        text = pytesseract.image_to_string(image, lang='deu+eng')

        logger.info(f"Bild OCR abgeschlossen: {len(text)} Zeichen")
        return text.strip()

    except ImportError as e:
        logger.warning(f"Tesseract nicht installiert: {e}")
        return None
    except Exception as e:
        logger.error(f"Fehler bei Bild-OCR: {e}")
        return None


def extract_text_from_docx(file_path: str) -> Optional[str]:
    """
    Extrahiert Text aus Word-Dokumenten (.docx)
    """
    try:
        import docx

        doc = docx.Document(file_path)
        text = "\n".join([paragraph.text for paragraph in doc.paragraphs])

        logger.info(f"DOCX Text extrahiert: {len(text)} Zeichen")
        return text.strip()

    except ImportError as e:
        logger.warning(f"python-docx nicht installiert: {e}")
        return None
    except Exception as e:
        logger.error(f"Fehler bei DOCX-Textextraktion: {e}")
        return None


def extract_text_from_file(file_path: str, mime_type: str = None) -> Optional[str]:
    """
    Haupt-Funktion: Extrahiert Text aus verschiedenen Dateitypen

    Args:
        file_path: Pfad zur Datei
        mime_type: MIME-Type (optional, wird automatisch erkannt)

    Returns:
        Extrahierter Text oder None
    """
    if not os.path.exists(file_path):
        logger.error(f"Datei nicht gefunden: {file_path}")
        return None

    # Dateiendung ermitteln
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()

    # PDF
    if ext == '.pdf':
        return extract_text_from_pdf(file_path)

    # Bilder
    elif ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif']:
        return extract_text_from_image(file_path)

    # Word
    elif ext == '.docx':
        return extract_text_from_docx(file_path)

    # Textdateien
    elif ext in ['.txt', '.csv', '.log']:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            try:
                with open(file_path, 'r', encoding='latin-1') as f:
                    return f.read()
            except Exception as e:
                logger.error(f"Fehler beim Lesen der Textdatei: {e}")
                return None

    else:
        logger.info(f"Keine OCR/Text-Extraktion für Dateityp: {ext}")
        return None
