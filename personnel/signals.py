"""
Personnel Signals
Automatische Verarbeitung von Person-Events
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.files.base import ContentFile
from PIL import Image
import io
import os

from .models import Person


@receiver(post_save, sender=Person)
def generate_id_card_photo(sender, instance, created, **kwargs):
    """
    Automatische Generierung eines Dienstausweis-Fotos beim Upload eines Fotos

    Dienstausweis-Foto Spezifikationen:
    - Größe: 35x45mm (413x531 Pixel bei 300 DPI)
    - Auflösung: 300 DPI
    - Format: JPEG, hohe Qualität
    """
    # Nur verarbeiten wenn ein Foto vorhanden ist
    if not instance.photo:
        return

    # Prüfen ob das Foto geändert wurde oder id_card_photo noch nicht existiert
    # Um Endlos-Loops zu vermeiden, prüfen wir ob wir gerade dabei sind zu speichern
    if hasattr(instance, '_generating_id_card'):
        return

    try:
        # Öffne das Original-Foto
        img = Image.open(instance.photo.path)

        # Konvertiere zu RGB wenn nötig (z.B. bei PNG mit Transparenz)
        if img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')

        # Dienstausweis-Foto Spezifikationen
        # 35x45mm bei 300 DPI = 413x531 Pixel
        target_width = 413
        target_height = 531
        target_dpi = 300

        # Berechne Aspect Ratio
        target_ratio = target_width / target_height
        current_ratio = img.width / img.height

        # Crop auf richtiges Seitenverhältnis (zentriert)
        if current_ratio > target_ratio:
            # Bild ist zu breit - crop links/rechts
            new_width = int(img.height * target_ratio)
            left = (img.width - new_width) // 2
            img = img.crop((left, 0, left + new_width, img.height))
        elif current_ratio < target_ratio:
            # Bild ist zu hoch - crop oben/unten (mehr oben für bessere Portrait-Position)
            new_height = int(img.width / target_ratio)
            top = int((img.height - new_height) * 0.3)  # 30% von oben statt 50% für bessere Kopf-Position
            img = img.crop((0, top, img.width, top + new_height))

        # Resize auf Zielgröße mit hoher Qualität
        img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)

        # Speichere in BytesIO mit hoher JPEG-Qualität
        output = io.BytesIO()
        img.save(output, format='JPEG', quality=95, dpi=(target_dpi, target_dpi), optimize=True)
        output.seek(0)

        # Generiere Dateinamen
        original_name = os.path.basename(instance.photo.name)
        name_without_ext = os.path.splitext(original_name)[0]
        id_card_filename = f"{name_without_ext}_idcard.jpg"

        # Setze Flag um Endlos-Loop zu vermeiden
        instance._generating_id_card = True

        # Speichere das Dienstausweis-Foto
        instance.id_card_photo.save(
            id_card_filename,
            ContentFile(output.read()),
            save=True
        )

        # Entferne Flag
        delattr(instance, '_generating_id_card')

    except Exception as e:
        # Bei Fehler: Log schreiben aber nicht crashen
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Fehler beim Generieren des Dienstausweis-Fotos für Person {instance.pk}: {str(e)}")
