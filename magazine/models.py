"""
Magazine Models
Magazin-Verwaltung für Verbrauchsmaterial (Batterien, Waschmittel, Handschuhe, Schrauben, etc.)
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from decimal import Decimal

from inventory_base.models import (
    AbstractInventoryItem,
    AbstractStockMovement,
    StockMovementType,
    AbstractInventoryCheck,
    AbstractInventoryCheckItem,
)


# ============================================================================
# ENUMS & CHOICES
# ============================================================================

class MagazineItemType(models.TextChoices):
    """Typen von Magazin-Artikeln (Verbrauchsmaterial)"""
    BATTERY = 'battery', _('Batterien')
    CLEANING = 'cleaning', _('Reinigungsmittel/Waschmittel')
    GLOVES = 'gloves', _('Handschuhe')
    FASTENER = 'fastener', _('Schrauben/Befestigungsmaterial')
    CHEMICAL = 'chemical', _('Chemikalien')
    OFFICE = 'office', _('Büromaterial')
    HYGIENE = 'hygiene', _('Hygieneartikel')
    ELECTRICAL = 'electrical', _('Elektromaterial/Leuchtmittel')
    PACKAGING = 'packaging', _('Verpackungsmaterial')
    ADHESIVE = 'adhesive', _('Klebebänder/Klebstoffe')
    CONSUMABLE = 'consumable', _('Sonstiges Verbrauchsmaterial')
    OTHER = 'other', _('Sonstiges')


class HazardClass(models.TextChoices):
    """Gefahrenklassen für Chemikalien"""
    NONE = 'none', _('Keine')
    EXPLOSIVE = 'explosive', _('Explosiv')
    FLAMMABLE = 'flammable', _('Entzündbar')
    OXIDIZING = 'oxidizing', _('Oxidierend')
    COMPRESSED_GAS = 'compressed_gas', _('Unter Druck stehende Gase')
    CORROSIVE = 'corrosive', _('Ätzend')
    TOXIC = 'toxic', _('Giftig')
    HARMFUL = 'harmful', _('Gesundheitsschädlich')
    ENVIRONMENTAL = 'environmental', _('Umweltgefährlich')


# ============================================================================
# MAGAZINE ITEM MASTER (STAMMDATEN)
# ============================================================================

class MagazineItemMaster(models.Model):
    """
    Stammdaten für Magazin-Artikel (Verbrauchsmaterial)

    Enthält alle produktspezifischen Informationen, die für alle
    Chargen/Instanzen eines Produkts gleich sind.
    """

    # Identifikation
    master_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_('Stammdaten-Nr.'),
        help_text=_('Eindeutige Nummer für diese Stammdaten (z.B. MAG-0001)')
    )

    name = models.CharField(
        max_length=200,
        verbose_name=_('Produktname')
    )

    description = models.TextField(
        blank=True,
        verbose_name=_('Beschreibung')
    )

    # Klassifizierung
    item_type = models.CharField(
        max_length=20,
        choices=MagazineItemType.choices,
        default=MagazineItemType.CONSUMABLE,
        verbose_name=_('Artikeltyp')
    )

    category = models.ForeignKey(
        'inventory_base.Category',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='magazine_masters',
        verbose_name=_('Kategorie')
    )

    # Hersteller & Produkt
    manufacturer = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Hersteller')
    )

    manufacturer_part_number = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Hersteller-Artikelnummer')
    )

    supplier = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Lieferant')
    )

    supplier_part_number = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Lieferanten-Artikelnummer')
    )

    # Physische Eigenschaften
    unit = models.CharField(
        max_length=20,
        default='Stück',
        verbose_name=_('Einheit'),
        help_text=_('z.B. Stück, Liter, kg, Packung')
    )

    size = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Größe/Maße'),
        help_text=_('z.B. "C-52", "3/4 Zoll", "M8"')
    )

    material = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Material'),
        help_text=_('z.B. "Stahl", "Kunststoff", "Aluminium"')
    )

    color = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_('Farbe')
    )

    weight_per_unit = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        null=True, blank=True,
        validators=[MinValueValidator(Decimal('0.001'))],
        verbose_name=_('Gewicht pro Einheit (kg)')
    )

    volume_per_unit = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        null=True, blank=True,
        validators=[MinValueValidator(Decimal('0.001'))],
        verbose_name=_('Volumen pro Einheit (Liter)')
    )

    # Gefahrgut
    is_hazardous = models.BooleanField(
        default=False,
        verbose_name=_('Gefahrgut')
    )

    hazard_class = models.CharField(
        max_length=20,
        choices=HazardClass.choices,
        default=HazardClass.NONE,
        verbose_name=_('Gefahrenklasse')
    )

    safety_data_sheet = models.FileField(
        upload_to='magazine/sds/',
        null=True, blank=True,
        verbose_name=_('Sicherheitsdatenblatt')
    )

    # Haltbarkeit & Lagerung
    has_expiry_date = models.BooleanField(
        default=False,
        verbose_name=_('Hat Verfallsdatum')
    )

    shelf_life_months = models.PositiveIntegerField(
        null=True, blank=True,
        verbose_name=_('Standard-Haltbarkeit (Monate)')
    )

    storage_temperature_min = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        null=True, blank=True,
        verbose_name=_('Min. Lagertemperatur (°C)')
    )

    storage_temperature_max = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        null=True, blank=True,
        verbose_name=_('Max. Lagertemperatur (°C)')
    )

    storage_instructions = models.TextField(
        blank=True,
        verbose_name=_('Lageranweisungen')
    )

    # Bestellung
    min_quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True, blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name=_('Mindestbestand')
    )

    reorder_point = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True, blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name=_('Bestellpunkt')
    )

    standard_order_quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True, blank=True,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name=_('Standard-Bestellmenge')
    )

    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True, blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name=_('Stückpreis (EUR)')
    )

    # Technische Informationen
    technical_specifications = models.TextField(
        blank=True,
        verbose_name=_('Technische Spezifikationen')
    )

    usage_instructions = models.TextField(
        blank=True,
        verbose_name=_('Verwendungshinweise')
    )

    manual_document = models.FileField(
        upload_to='magazine/manuals/',
        null=True, blank=True,
        verbose_name=_('Handbuch / Produktinformation')
    )

    # Bild
    image = models.ImageField(
        upload_to='magazine/masters/',
        null=True, blank=True,
        verbose_name=_('Produktbild')
    )

    # Status
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Aktiv')
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Erstellt am'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Aktualisiert am'))
    created_by = models.ForeignKey(
        'core.User',
        on_delete=models.PROTECT,
        related_name='created_magazine_masters',
        verbose_name=_('Erstellt von')
    )
    updated_by = models.ForeignKey(
        'core.User',
        on_delete=models.PROTECT,
        related_name='updated_magazine_masters',
        verbose_name=_('Aktualisiert von')
    )

    class Meta:
        verbose_name = _('Magazin-Stammdaten')
        verbose_name_plural = _('Magazin-Stammdaten')
        ordering = ['master_number']
        indexes = [
            models.Index(fields=['master_number']),
            models.Index(fields=['name']),
            models.Index(fields=['item_type']),
            models.Index(fields=['manufacturer']),
            models.Index(fields=['is_hazardous']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.master_number} - {self.name}"

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('magazine:master_detail', kwargs={'pk': self.pk})

    def get_total_stock(self):
        """Berechnet den Gesamtbestand über alle Chargen"""
        from django.db.models import Sum
        result = self.batches.aggregate(total=Sum('quantity_remaining'))
        return result['total'] or Decimal('0.00')

    def is_below_min_quantity(self):
        """Prüft ob Bestand unter Mindestmenge"""
        if self.min_quantity:
            return self.get_total_stock() < self.min_quantity
        return False

    def is_reorder_needed(self):
        """Prüft ob Nachbestellung erforderlich"""
        if self.reorder_point:
            return self.get_total_stock() <= self.reorder_point
        return False

    def generate_qr_code(self):
        """Generiert QR-Code als SVG für die Stammdaten"""
        import qrcode
        import qrcode.image.svg
        from io import BytesIO

        # Nur URL kodieren für maximale Scanner-Kompatibilität
        qr_string = f'/magazine/masters/{self.pk}/'

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_string)
        qr.make(fit=True)

        factory = qrcode.image.svg.SvgPathImage
        img = qr.make_image(fill_color="black", back_color="white", image_factory=factory)

        stream = BytesIO()
        img.save(stream)
        svg_string = stream.getvalue().decode('utf-8')

        return svg_string

    def generate_barcode(self):
        """Generiert Barcode als SVG für die Stammdaten-Nummer"""
        import barcode
        from barcode.writer import SVGWriter
        from io import BytesIO

        code128 = barcode.get_barcode_class('code128')

        rv = BytesIO()
        code = code128(self.master_number, writer=SVGWriter())
        code.write(rv)

        svg_string = rv.getvalue().decode('utf-8')
        return svg_string


# ============================================================================
# MAGAZINE ITEM (LEGACY - wird durch Master/Batch ersetzt)
# ============================================================================

class MagazineItem(AbstractInventoryItem):
    """
    Magazin-Artikel (Verbrauchsmaterial)
    Erbt alle Basis-Felder von AbstractInventoryItem
    """

    # Magazin-spezifische Felder
    item_type = models.CharField(
        max_length=20,
        choices=MagazineItemType.choices,
        default=MagazineItemType.CONSUMABLE,
        verbose_name=_('Artikeltyp')
    )

    # Größe/Maße
    size = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Größe/Maße'),
        help_text=_('z.B. "C-52", "3/4 Zoll", "M8"')
    )

    # Material
    material = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Material'),
        help_text=_('z.B. "Stahl", "Kunststoff", "Aluminium"')
    )

    # Farbe (wichtig für Schläuche)
    color = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_('Farbe')
    )

    # Gewicht (pro Einheit)
    weight_per_unit = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        null=True, blank=True,
        validators=[MinValueValidator(Decimal('0.001'))],
        verbose_name=_('Gewicht pro Einheit (kg)'),
        help_text=_('Gewicht einer einzelnen Einheit in kg')
    )

    # Volumen (pro Einheit)
    volume_per_unit = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        null=True, blank=True,
        validators=[MinValueValidator(Decimal('0.001'))],
        verbose_name=_('Volumen pro Einheit (Liter)'),
        help_text=_('Volumen einer einzelnen Einheit in Litern')
    )

    # Gefahrgut
    is_hazardous = models.BooleanField(
        default=False,
        verbose_name=_('Gefahrgut')
    )

    hazard_class = models.CharField(
        max_length=20,
        choices=HazardClass.choices,
        default=HazardClass.NONE,
        verbose_name=_('Gefahrenklasse')
    )

    safety_data_sheet = models.FileField(
        upload_to='magazine/sds/',
        null=True, blank=True,
        verbose_name=_('Sicherheitsdatenblatt'),
        help_text=_('PDF-Datei des Sicherheitsdatenblatts')
    )

    manual_document = models.FileField(
        upload_to='magazine/manuals/',
        null=True, blank=True,
        verbose_name=_('Handbuch / Produktinformation'),
        help_text=_('PDF oder Bild-Datei (wird automatisch per OCR durchsuchbar gemacht)')
    )

    # Haltbarkeit
    has_expiry_date = models.BooleanField(
        default=False,
        verbose_name=_('Hat Verfallsdatum')
    )

    shelf_life_months = models.PositiveIntegerField(
        null=True, blank=True,
        verbose_name=_('Haltbarkeit (Monate)'),
        help_text=_('Standard-Haltbarkeit in Monaten')
    )

    # Lagerung
    storage_temperature_min = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        null=True, blank=True,
        verbose_name=_('Min. Lagertemperatur (°C)')
    )

    storage_temperature_max = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        null=True, blank=True,
        verbose_name=_('Max. Lagertemperatur (°C)')
    )

    storage_instructions = models.TextField(
        blank=True,
        verbose_name=_('Lageranweisungen'),
        help_text=_('Spezielle Anweisungen zur Lagerung')
    )

    # Bestellung
    reorder_point = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True, blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name=_('Bestellpunkt'),
        help_text=_('Bei Unterschreitung automatische Bestellung auslösen')
    )

    standard_order_quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True, blank=True,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name=_('Standard-Bestellmenge')
    )

    last_ordered_date = models.DateField(
        null=True, blank=True,
        verbose_name=_('Zuletzt bestellt am')
    )

    # Zusätzliche Informationen
    technical_specifications = models.TextField(
        blank=True,
        verbose_name=_('Technische Spezifikationen')
    )

    usage_instructions = models.TextField(
        blank=True,
        verbose_name=_('Verwendungshinweise')
    )

    class Meta:
        verbose_name = _('Magazin-Artikel')
        verbose_name_plural = _('Magazin-Artikel')
        ordering = ['item_number']
        indexes = [
            models.Index(fields=['item_type', 'category']),
            models.Index(fields=['is_hazardous']),
            models.Index(fields=['has_expiry_date']),
        ]

    def __str__(self):
        return f"{self.item_number} - {self.name}"

    def is_reorder_needed(self):
        """Prüft ob Nachbestellung erforderlich"""
        if self.reorder_point:
            return self.quantity <= self.reorder_point
        return False

    def get_total_weight(self):
        """Gesamtgewicht des Bestands"""
        if self.weight_per_unit:
            return self.quantity * self.weight_per_unit
        return None

    def get_total_volume(self):
        """Gesamtvolumen des Bestands"""
        if self.volume_per_unit:
            return self.quantity * self.volume_per_unit
        return None

    def generate_barcode(self):
        """
        Generiert Barcode als SVG für die Artikelnummer
        Nutzt Code128 Format
        """
        import barcode
        from barcode.writer import SVGWriter
        from io import BytesIO

        # Verwende barcode-Feld, fallback zu item_number
        barcode_value = self.barcode or self.item_number

        if not barcode_value:
            return None

        # Code128 für Artikelnummer
        code128 = barcode.get_barcode_class('code128')

        # Barcode generieren
        rv = BytesIO()
        code = code128(barcode_value, writer=SVGWriter())
        code.write(rv)

        svg_string = rv.getvalue().decode('utf-8')
        return svg_string

    def generate_qr_code(self):
        """
        Generiert QR-Code als SVG für den Magazin-Artikel
        Enthält nur die URL für direkten Zugriff
        """
        import qrcode
        import qrcode.image.svg
        from io import BytesIO

        # Nur URL kodieren für maximale Scanner-Kompatibilität
        qr_string = f'/magazine/items/{self.pk}/'

        # QR-Code generieren
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_string)
        qr.make(fit=True)

        # Als SVG
        factory = qrcode.image.svg.SvgPathImage
        img = qr.make_image(fill_color="black", back_color="white", image_factory=factory)

        # SVG zu String konvertieren
        stream = BytesIO()
        img.save(stream)
        svg_string = stream.getvalue().decode('utf-8')

        return svg_string


# ============================================================================
# MAGAZINE STOCK MOVEMENT
# ============================================================================

class MagazineStockMovement(AbstractStockMovement):
    """
    Lagerbewegungen für Magazin-Artikel
    Erbt von AbstractStockMovement
    """

    item = models.ForeignKey(
        MagazineItem,
        on_delete=models.PROTECT,
        related_name='stock_movements',
        verbose_name=_('Artikel')
    )

    # Chargen-/Batch-Nummer (wichtig für Rückverfolgbarkeit)
    batch_number = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Chargen-/Batch-Nummer')
    )

    # Verfallsdatum (für Chargen)
    expiry_date = models.DateField(
        null=True, blank=True,
        verbose_name=_('Verfallsdatum')
    )

    # Kosten (bei Wareneingang)
    unit_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True, blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name=_('Stückkosten (EUR)')
    )

    total_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True, blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name=_('Gesamtkosten (EUR)')
    )

    # Verwendungszweck (bei Entnahme)
    purpose = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Verwendungszweck'),
        help_text=_('z.B. "Einsatz", "Übung", "Wartung"')
    )

    # Empfänger (bei Ausgabe)
    person = models.ForeignKey(
        'personnel.Person',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='magazine_movements',
        verbose_name=_('Person'),
        help_text=_('Person, die den Artikel erhält/zurückgibt')
    )

    recipient_name = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Empfänger (alternativ)'),
        help_text=_('Nur falls Person nicht in der Personaldatenbank vorhanden ist')
    )

    # Dokumente
    delivery_note = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Lieferschein-Nr.')
    )

    invoice_number = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Rechnungsnummer')
    )

    class Meta:
        verbose_name = _('Lagerbewegung')
        verbose_name_plural = _('Lagerbewegungen')
        ordering = ['-movement_date']
        indexes = [
            models.Index(fields=['item', '-movement_date']),
            models.Index(fields=['movement_type', '-movement_date']),
            models.Index(fields=['batch_number']),
            models.Index(fields=['expiry_date']),
        ]

    def __str__(self):
        return f"{self.get_movement_type_display()} - {self.item.name} ({self.quantity} {self.unit})"

    def save(self, *args, **kwargs):
        """
        Berechnet total_cost automatisch wenn unit_cost gegeben ist
        """
        if self.unit_cost and not self.total_cost:
            self.total_cost = self.unit_cost * self.quantity

        # Unit von Item übernehmen
        if not self.unit and self.item:
            self.unit = self.item.unit

        super().save(*args, **kwargs)

        # Bestand aktualisieren
        self.update_item_stock()

    def update_item_stock(self):
        """
        Aktualisiert den Bestand des Items basierend auf der Bewegung
        """
        if self.movement_type == StockMovementType.INCOMING:
            # Wareneingang: Bestand erhöhen
            self.item.quantity += self.quantity
        elif self.movement_type in [StockMovementType.OUTGOING, StockMovementType.DAMAGE, StockMovementType.DISPOSAL]:
            # Warenausgang/Schwund/Entsorgung: Bestand reduzieren
            self.item.quantity -= self.quantity
        elif self.movement_type == StockMovementType.INVENTORY:
            # Inventur: Bestand auf quantity setzen
            self.item.quantity = self.quantity
        # Bei TRANSFER: Bestand wird über from_location/to_location gehandhabt

        self.item.save(update_fields=['quantity'])


# ============================================================================
# BATCH/LOT TRACKING (für Chargen-Rückverfolgbarkeit)
# ============================================================================

class MagazineBatch(models.Model):
    """
    Chargen-/Batch-Tracking für Rückverfolgbarkeit
    Speichert Details zu einzelnen Lieferungen/Chargen
    """

    # Referenz zu Stammdaten (neu) oder Legacy-Item
    master = models.ForeignKey(
        MagazineItemMaster,
        on_delete=models.CASCADE,
        related_name='batches',
        null=True, blank=True,
        verbose_name=_('Stammdaten')
    )

    item = models.ForeignKey(
        MagazineItem,
        on_delete=models.CASCADE,
        related_name='batches',
        null=True, blank=True,
        verbose_name=_('Artikel (Legacy)')
    )

    batch_number = models.CharField(
        max_length=100,
        verbose_name=_('Chargen-Nummer')
    )

    received_date = models.DateField(
        verbose_name=_('Eingangsdatum')
    )

    expiry_date = models.DateField(
        null=True, blank=True,
        verbose_name=_('Verfallsdatum')
    )

    quantity_received = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name=_('Eingangsmenge')
    )

    quantity_remaining = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name=_('Restmenge')
    )

    location = models.ForeignKey(
        'locations.Location',
        on_delete=models.PROTECT,
        related_name='magazine_batches',
        verbose_name=_('Lagerort')
    )

    supplier_batch_number = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Lieferanten-Chargen-Nr.')
    )

    notes = models.TextField(
        blank=True,
        verbose_name=_('Notizen')
    )

    class Meta:
        verbose_name = _('Charge/Batch')
        verbose_name_plural = _('Chargen/Batches')
        ordering = ['expiry_date', 'received_date']
        unique_together = ['item', 'batch_number']
        indexes = [
            models.Index(fields=['item', 'expiry_date']),
            models.Index(fields=['batch_number']),
        ]

    def __str__(self):
        return f"{self.item.name} - Charge {self.batch_number}"

    def is_expired(self):
        """Prüft ob Charge abgelaufen ist"""
        if self.expiry_date:
            from django.utils import timezone
            return self.expiry_date < timezone.now().date()
        return False

    def is_depleted(self):
        """Prüft ob Charge aufgebraucht ist"""
        return self.quantity_remaining <= 0


# ============================================================================
# INVENTUR (INVENTORY CHECK)
# ============================================================================

class MagazineInventoryCheck(AbstractInventoryCheck):
    """
    Inventur-Check für Magazin (Verbrauchsmaterial)
    Erbt alle Basis-Funktionalität von AbstractInventoryCheck
    """

    # Magazine-spezifische Felder
    check_hazardous = models.BooleanField(
        default=True,
        verbose_name=_('Gefahrgut prüfen'),
        help_text=_('Gefahrgut-Artikel und Sicherheitsdatenblätter überprüfen')
    )

    check_expiry_dates = models.BooleanField(
        default=True,
        verbose_name=_('Verfallsdaten prüfen'),
        help_text=_('Artikel mit Verfallsdatum auf Ablauf prüfen')
    )

    check_storage_conditions = models.BooleanField(
        default=True,
        verbose_name=_('Lagerbedingungen prüfen'),
        help_text=_('Temperatur und Lagerbedingungen kontrollieren')
    )

    hazardous_items_found = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Gefahrgut-Artikel gefunden')
    )

    expired_items_found = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Abgelaufene Artikel gefunden')
    )

    class Meta:
        verbose_name = _('Magazin Inventur')
        verbose_name_plural = _('Magazin Inventuren')
        ordering = ['-scheduled_start_date']
        permissions = [
            ('approve_magazineinventorycheck', 'Kann Magazin-Inventuren genehmigen'),
        ]

    def get_number_prefix(self):
        """Magazine-spezifisches Präfix für Inventurnummern"""
        return 'MAG-INV'

    def update_progress(self):
        """Magazine-spezifische Fortschritts-Berechnung"""
        from django.utils import timezone

        self.total_items = self.items.count()
        self.counted_items = self.items.filter(is_counted=True).count()
        self.items_with_discrepancies = self.items.filter(has_discrepancy=True).count()

        # Zähle Gefahrgut-Artikel
        if self.check_hazardous:
            self.hazardous_items_found = self.items.filter(is_hazardous=True).count()

        # Zähle abgelaufene Artikel
        if self.check_expiry_dates:
            today = timezone.now().date()
            self.expired_items_found = self.items.filter(
                has_expiry_date=True,
                is_expired=True
            ).count()

        self.save(update_fields=[
            'total_items',
            'counted_items',
            'items_with_discrepancies',
            'hazardous_items_found',
            'expired_items_found'
        ])


class MagazineInventoryCheckItem(AbstractInventoryCheckItem):
    """Einzelne Position in Magazine-Inventur"""

    inventory_check = models.ForeignKey(
        MagazineInventoryCheck,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_('Inventur')
    )

    magazine_item = models.ForeignKey(
        MagazineItem,
        on_delete=models.PROTECT,
        null=True, blank=True,
        related_name='inventory_items',
        verbose_name=_('Magazin-Artikel')
    )

    # Magazine-spezifische Felder
    item_type = models.CharField(
        max_length=20,
        choices=MagazineItemType.choices,
        blank=True,
        verbose_name=_('Artikeltyp')
    )

    size = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Größe/Maße')
    )

    is_hazardous = models.BooleanField(
        default=False,
        verbose_name=_('Gefahrgut')
    )

    hazard_class = models.CharField(
        max_length=20,
        choices=HazardClass.choices,
        default=HazardClass.NONE,
        blank=True,
        verbose_name=_('Gefahrenklasse')
    )

    has_expiry_date = models.BooleanField(
        default=False,
        verbose_name=_('Hat Verfallsdatum')
    )

    expiry_date = models.DateField(
        null=True, blank=True,
        verbose_name=_('Verfallsdatum')
    )

    is_expired = models.BooleanField(
        default=False,
        verbose_name=_('Abgelaufen')
    )

    storage_condition_ok = models.BooleanField(
        default=True,
        verbose_name=_('Lagerbedingung OK')
    )

    class Meta:
        verbose_name = _('Magazin Inventur Position')
        verbose_name_plural = _('Magazin Inventur Positionen')
        ordering = ['location', 'item_name']

    def __str__(self):
        return f"{self.inventory_check.check_number} - {self.item_name}"
