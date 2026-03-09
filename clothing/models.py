"""
Clothing Models
Kleiderkammer-Verwaltung (Einsatzkleidung, PSA, Uniformen)
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from django.conf import settings
from decimal import Decimal

from inventory_base.models import (
    AbstractInventoryItem,
    AbstractStockMovement,
    AbstractInventoryCheck,
    AbstractInventoryCheckItem,
    ItemCondition,
)
from core.models.base import AuditedModel


# ============================================================================
# ENUMS & CHOICES
# ============================================================================

class ClothingUnit(models.TextChoices):
    """Einheiten für Kleidungsstücke"""
    PIECE = 'Stück', _('Stück')
    PAIR = 'Paar', _('Paar')
    SET = 'Set', _('Set/Satz')
    PACKAGE = 'Packung', _('Packung')
    BOX = 'Karton', _('Karton')

class ClothingType(models.TextChoices):
    """Typen von Kleidungsstücken"""
    JACKET = 'jacket', _('Jacke')
    PANTS = 'pants', _('Hose')
    OVERALL = 'overall', _('Overall/Kombi')
    SHIRT = 'shirt', _('Hemd/Shirt')
    UNDERWEAR = 'underwear', _('Unterwäsche')
    SHOES = 'shoes', _('Schuhe')
    BOOTS = 'boots', _('Stiefel')
    GLOVES = 'gloves', _('Handschuhe')
    HELMET = 'helmet', _('Helm')
    VEST = 'vest', _('Weste')
    COAT = 'coat', _('Mantel')
    HAT = 'hat', _('Kopfbedeckung')
    PROTECTIVE = 'protective', _('Schutzausrüstung')
    UNIFORM = 'uniform', _('Uniform')
    OTHER = 'other', _('Sonstiges')


class ClothingSize(models.TextChoices):
    """Größen für Kleidung"""
    XXS = 'xxs', _('XXS')
    XS = 'xs', _('XS')
    S = 's', _('S')
    M = 'm', _('M')
    L = 'l', _('L')
    XL = 'xl', _('XL')
    XXL = 'xxl', _('XXL')
    XXXL = 'xxxl', _('XXXL')
    XXXXL = 'xxxxl', _('XXXXL')
    # Numerische Größen
    SIZE_36 = '36', _('36')
    SIZE_38 = '38', _('38')
    SIZE_40 = '40', _('40')
    SIZE_42 = '42', _('42')
    SIZE_44 = '44', _('44')
    SIZE_46 = '46', _('46')
    SIZE_48 = '48', _('48')
    SIZE_50 = '50', _('50')
    SIZE_52 = '52', _('52')
    SIZE_54 = '54', _('54')
    SIZE_56 = '56', _('56')
    SIZE_58 = '58', _('58')
    SIZE_60 = '60', _('60')
    # Schuhgrößen
    SHOE_36 = 's36', _('Schuh 36')
    SHOE_37 = 's37', _('Schuh 37')
    SHOE_38 = 's38', _('Schuh 38')
    SHOE_39 = 's39', _('Schuh 39')
    SHOE_40 = 's40', _('Schuh 40')
    SHOE_41 = 's41', _('Schuh 41')
    SHOE_42 = 's42', _('Schuh 42')
    SHOE_43 = 's43', _('Schuh 43')
    SHOE_44 = 's44', _('Schuh 44')
    SHOE_45 = 's45', _('Schuh 45')
    SHOE_46 = 's46', _('Schuh 46')
    SHOE_47 = 's47', _('Schuh 47')
    SHOE_48 = 's48', _('Schuh 48')
    OTHER = 'other', _('Andere')


class Gender(models.TextChoices):
    """Geschlechtsspezifische Schnitte"""
    UNISEX = 'unisex', _('Unisex')
    MALE = 'male', _('Herren')
    FEMALE = 'female', _('Damen')


class ProtectionLevel(models.TextChoices):
    """Schutzlevel (für PSA)"""
    NONE = 'none', _('Keine PSA')
    BASIC = 'basic', _('Basisschutz')
    ENHANCED = 'enhanced', _('Erhöhter Schutz')
    HIGH = 'high', _('Hoher Schutz')
    SPECIALIST = 'specialist', _('Spezialschutz')


# ============================================================================
# CATEGORY
# ============================================================================

class ClothingCategory(AuditedModel):
    """
    Kategorien für Kleiderkammer
    (Nicht hierarchisch, einfacher als inventory_base.Category)
    """

    name = models.CharField(
        max_length=200,
        unique=True,
        verbose_name=_('Name')
    )

    code = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_('Code'),
        help_text=_('Eindeutiger Kategorie-Code, z.B. "PSA-EINSATZ"')
    )

    description = models.TextField(
        blank=True,
        verbose_name=_('Beschreibung')
    )

    color = models.CharField(
        max_length=7,
        default='#3B82F6',
        verbose_name=_('Farbe'),
        help_text=_('Hex-Farbcode für visuelle Kennzeichnung')
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Aktiv')
    )

    sort_order = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Sortierung')
    )

    class Meta:
        verbose_name = _('Kleiderkammer-Kategorie')
        verbose_name_plural = _('Kleiderkammer-Kategorien')
        ordering = ['sort_order', 'name']

    def __str__(self):
        return self.name


class ClothingProductType(AuditedModel):
    """
    Dynamisch verwaltbare Produkttypen für Kleidung
    (z.B. Jacke, Hose, Helm, etc.)
    """

    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_('Name'),
        help_text=_('z.B. "Jacke", "Hose", "Helm"')
    )

    code = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_('Code'),
        help_text=_('Eindeutiger Code, z.B. "JACKET", "PANTS"')
    )

    description = models.TextField(
        blank=True,
        verbose_name=_('Beschreibung')
    )

    icon = models.CharField(
        max_length=10,
        default='👕',
        verbose_name=_('Icon'),
        help_text=_('Emoji oder Symbol für visuelle Darstellung')
    )

    is_psa_typical = models.BooleanField(
        default=False,
        verbose_name=_('Typischerweise PSA'),
        help_text=_('Gibt an, ob dieser Produkttyp normalerweise PSA ist')
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Aktiv')
    )

    sort_order = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Sortierung')
    )

    class Meta:
        verbose_name = _('Produkttyp')
        verbose_name_plural = _('Produkttypen')
        ordering = ['sort_order', 'name']

    def __str__(self):
        return self.name


# ============================================================================
# CLOTHING ITEM
# ============================================================================

class ClothingItem(AbstractInventoryItem):
    """
    Kleidungsstück für Feuerwehr/Rettungsdienst
    Erbt alle Basis-Felder von AbstractInventoryItem
    """

    # Override category to use ClothingCategory
    category = models.ForeignKey(
        ClothingCategory,
        on_delete=models.PROTECT,
        related_name='items',
        verbose_name=_('Kategorie')
    )

    # Kleidungs-spezifische Felder
    clothing_type = models.CharField(
        max_length=20,
        choices=ClothingType.choices,
        verbose_name=_('Kleidungstyp')
    )

    # Größe
    size = models.CharField(
        max_length=10,
        choices=ClothingSize.choices,
        verbose_name=_('Größe')
    )

    gender = models.CharField(
        max_length=10,
        choices=Gender.choices,
        default=Gender.UNISEX,
        verbose_name=_('Schnitt')
    )

    # Farbe & Material
    color = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_('Farbe')
    )

    material = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Material'),
        help_text=_('z.B. "Nomex", "Gore-Tex", "Baumwolle"')
    )

    # PSA-Informationen (Persönliche Schutzausrüstung)
    is_psa = models.BooleanField(
        default=False,
        verbose_name=_('Persönliche Schutzausrüstung (PSA)'),
        help_text=_('Unterliegt PSA-Verordnung')
    )

    protection_level = models.CharField(
        max_length=20,
        choices=ProtectionLevel.choices,
        default=ProtectionLevel.NONE,
        verbose_name=_('Schutzlevel')
    )

    norm_standard = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Norm/Standard'),
        help_text=_('z.B. "EN 469", "EN ISO 20471"')
    )

    # Zertifizierung
    certification_number = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Zertifizierungsnummer')
    )

    certification_date = models.DateField(
        null=True, blank=True,
        verbose_name=_('Zertifizierungsdatum')
    )

    certification_expires = models.DateField(
        null=True, blank=True,
        verbose_name=_('Zertifizierung läuft ab')
    )

    # Lebensdauer & Wartung
    max_usage_years = models.PositiveIntegerField(
        null=True, blank=True,
        verbose_name=_('Max. Nutzungsdauer (Jahre)'),
        help_text=_('Maximale Nutzungsdauer laut Hersteller')
    )

    requires_inspection = models.BooleanField(
        default=False,
        verbose_name=_('Prüfpflicht'),
        help_text=_('Regelmäßige Prüfung erforderlich')
    )

    inspection_interval_months = models.PositiveIntegerField(
        null=True, blank=True,
        verbose_name=_('Prüfintervall (Monate)')
    )

    last_inspection_date = models.DateField(
        null=True, blank=True,
        verbose_name=_('Letzte Prüfung')
    )

    next_inspection_date = models.DateField(
        null=True, blank=True,
        verbose_name=_('Nächste Prüfung')
    )

    # Reinigung & Pflege
    washing_instructions = models.TextField(
        blank=True,
        verbose_name=_('Waschanleitung')
    )

    max_washing_cycles = models.PositiveIntegerField(
        null=True, blank=True,
        verbose_name=_('Max. Waschzyklen'),
        help_text=_('Maximale Anzahl Waschvorgänge laut Hersteller')
    )

    manual_document = models.FileField(
        upload_to='clothing/manuals/',
        null=True, blank=True,
        verbose_name=_('Handbuch / Pflegeanleitung'),
        help_text=_('PDF oder Bild-Datei (wird automatisch per OCR durchsuchbar gemacht)')
    )

    current_washing_cycles = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Aktuelle Waschzyklen'),
        help_text=_('Anzahl bisheriger Waschvorgänge')
    )

    # Personenzuordnung
    assigned_to = models.ForeignKey(
        'personnel.Person',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='assigned_clothing',
        verbose_name=_('Zugeordnet an'),
        help_text=_('Person der dieses Kleidungsstück zugeordnet ist')
    )

    assignment_date = models.DateField(
        null=True, blank=True,
        verbose_name=_('Zugeordnet am')
    )

    is_personal_issue = models.BooleanField(
        default=False,
        verbose_name=_('Persönliche Ausgabe'),
        help_text=_('Wurde persönlich ausgegeben und nicht Poolware')
    )

    # Spezielle Kennzeichnung
    has_name_tag = models.BooleanField(
        default=False,
        verbose_name=_('Namensschildversehen')
    )

    reflective_strips = models.BooleanField(
        default=False,
        verbose_name=_('Reflektierende Streifen')
    )

    # Zusatzinformationen
    special_features = models.TextField(
        blank=True,
        verbose_name=_('Besondere Merkmale'),
        help_text=_('z.B. "Verstärkte Knie", "Futter herausnehmbar"')
    )

    class Meta:
        verbose_name = _('Kleidungsstück')
        verbose_name_plural = _('Kleidungsstücke')
        ordering = ['clothing_type', 'size']
        indexes = [
            models.Index(fields=['clothing_type', 'size']),
            models.Index(fields=['is_psa']),
            models.Index(fields=['assigned_to']),
            models.Index(fields=['next_inspection_date']),
        ]

    def __str__(self):
        assigned = f" [{self.assigned_to}]" if self.assigned_to else ""
        return f"{self.get_clothing_type_display()} {self.size} - {self.item_number}{assigned}"

    def is_inspection_due(self):
        """Prüft ob Prüfung fällig ist"""
        if self.next_inspection_date:
            from django.utils import timezone
            return self.next_inspection_date <= timezone.now().date()
        return False

    def is_certification_expired(self):
        """Prüft ob Zertifizierung abgelaufen ist"""
        if self.certification_expires:
            from django.utils import timezone
            return self.certification_expires < timezone.now().date()
        return False

    def is_washing_limit_reached(self):
        """Prüft ob maximale Waschzyklen erreicht"""
        if self.max_washing_cycles:
            return self.current_washing_cycles >= self.max_washing_cycles
        return False

    def save(self, *args, **kwargs):
        """
        Überschreibt save() um automatisch Barcode zu generieren
        wenn keiner vorhanden ist
        """
        # Wenn kein Barcode vorhanden, nutze item_number
        if not self.barcode and self.item_number:
            self.barcode = self.item_number

        super().save(*args, **kwargs)

    def generate_qr_code(self):
        """
        Generiert QR-Code als SVG für das Kleidungsstück
        Enthält nur die URL für direkten Zugriff
        """
        import qrcode
        import qrcode.image.svg
        from io import BytesIO

        # Nur URL kodieren für maximale Scanner-Kompatibilität
        qr_string = f'/clothing/items/{self.pk}/'

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


# ============================================================================
# CLOTHING STOCK MOVEMENT
# ============================================================================

class ClothingStockMovement(AbstractStockMovement):
    """
    Lagerbewegungen für Kleidungsstücke
    """

    item = models.ForeignKey(
        ClothingItem,
        on_delete=models.PROTECT,
        related_name='stock_movements',
        verbose_name=_('Kleidungsstück')
    )

    # Personenzuordnung (bei Ausgabe/Rückgabe)
    person = models.ForeignKey(
        'personnel.Person',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='clothing_movements',
        verbose_name=_('Person'),
        help_text=_('Person die das Kleidungsstück erhält/zurückgibt')
    )

    # Rückgabegrund (bei Rückgabe)
    return_reason = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Rückgabegrund'),
        help_text=_('z.B. "Größe passt nicht", "Beschädigt", "Person ausgeschieden"')
    )

    # Zustand bei Rückgabe
    return_condition_notes = models.TextField(
        blank=True,
        verbose_name=_('Zustandsnotizen bei Rückgabe')
    )

    # Reinigung
    cleaned_before_return = models.BooleanField(
        default=False,
        verbose_name=_('Gereinigt vor Rückgabe')
    )

    # Kosten
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

    # Dokumente
    delivery_note = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Lieferschein-Nr.')
    )

    class Meta:
        verbose_name = _('Lagerbewegung')
        verbose_name_plural = _('Lagerbewegungen')
        ordering = ['-movement_date']
        indexes = [
            models.Index(fields=['item', '-movement_date']),
            models.Index(fields=['person', '-movement_date']),
            models.Index(fields=['movement_type', '-movement_date']),
        ]

    def __str__(self):
        person_info = f" - {self.person}" if self.person else ""
        return f"{self.get_movement_type_display()} - {self.item.clothing_type} {self.item.size}{person_info}"

    def save(self, *args, **kwargs):
        """
        Automatische Berechnungen und Personenzuordnung
        """
        # Kosten berechnen
        if self.unit_cost and not self.total_cost:
            self.total_cost = self.unit_cost * self.quantity

        # Unit von Item übernehmen
        if not self.unit and self.item:
            self.unit = self.item.unit

        super().save(*args, **kwargs)

        # Bestand aktualisieren
        self.update_item_stock()

        # Lagerort des Items aktualisieren
        from inventory_base.models import StockMovementType
        if self.movement_type == StockMovementType.TRANSFER and self.to_location:
            self.item.location = self.to_location
            self.item.save(update_fields=['location'])
        elif self.movement_type == StockMovementType.INCOMING and self.to_location:
            self.item.location = self.to_location
            self.item.save(update_fields=['location'])

        # Bei Ausgabe: Item der Person zuordnen
        if self.movement_type == StockMovementType.OUTGOING and self.person:
            self.item.assigned_to = self.person
            self.item.assignment_date = self.movement_date
            self.item.is_personal_issue = True
            self.item.save(update_fields=['assigned_to', 'assignment_date', 'is_personal_issue'])

        # Bei Rückgabe: Zuweisung entfernen
        elif self.movement_type == StockMovementType.RETURN:
            self.item.assigned_to = None
            self.item.assignment_date = None
            self.item.is_personal_issue = False
            self.item.save(update_fields=['assigned_to', 'assignment_date', 'is_personal_issue'])

    def update_item_stock(self):
        """
        Aktualisiert den Bestand des Items basierend auf der Bewegung
        """
        from inventory_base.models import StockMovementType

        if self.movement_type == StockMovementType.INCOMING:
            self.item.quantity += self.quantity
        elif self.movement_type in [StockMovementType.OUTGOING, StockMovementType.DAMAGE, StockMovementType.DISPOSAL]:
            self.item.quantity -= self.quantity
        elif self.movement_type == StockMovementType.RETURN:
            self.item.quantity += self.quantity
        elif self.movement_type == StockMovementType.INVENTORY:
            self.item.quantity = self.quantity

        self.item.save(update_fields=['quantity'])


# ============================================================================
# CLOTHING SIZE ASSIGNMENT (Größenzuordnung pro Person)
# ============================================================================

class ClothingSizeAssignment(models.Model):
    """
    Größenzuordnung für eine Person
    Speichert welche Größen eine Person für verschiedene Kleidungstypen benötigt
    """

    person = models.ForeignKey(
        'personnel.Person',
        on_delete=models.CASCADE,
        related_name='clothing_sizes',
        verbose_name=_('Person')
    )

    clothing_type = models.CharField(
        max_length=20,
        choices=ClothingType.choices,
        verbose_name=_('Kleidungstyp')
    )

    size = models.CharField(
        max_length=10,
        choices=ClothingSize.choices,
        verbose_name=_('Größe')
    )

    notes = models.TextField(
        blank=True,
        verbose_name=_('Notizen'),
        help_text=_('z.B. "Bevorzugt weite Passform"')
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Aktualisiert am')
    )

    class Meta:
        verbose_name = _('Größenzuordnung')
        verbose_name_plural = _('Größenzuordnungen')
        unique_together = ['person', 'clothing_type']
        ordering = ['person', 'clothing_type']

    def __str__(self):
        return f"{self.person} - {self.get_clothing_type_display()}: {self.size}"


# ============================================================================
# INVENTUR (Inventory Check)
# ============================================================================

class ClothingInventoryCheck(AbstractInventoryCheck):
    """
    Inventur-Check für Kleiderkammer
    Erbt alle Basis-Funktionalität von AbstractInventoryCheck
    """

    # Clothing-spezifische Felder
    check_sizes = models.BooleanField(
        default=True,
        verbose_name=_('Größenverteilung prüfen'),
        help_text=_('Überprüfung der Größenverteilung durchführen')
    )

    check_condition = models.BooleanField(
        default=True,
        verbose_name=_('Zustand prüfen'),
        help_text=_('Zustand und Beschädigungen erfassen')
    )

    check_psa = models.BooleanField(
        default=True,
        verbose_name=_('PSA-Zertifizierungen prüfen'),
        help_text=_('Zertifizierungen von PSA-Artikeln überprüfen')
    )

    damaged_items_found = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Beschädigte Artikel gefunden')
    )

    expired_certifications_found = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Abgelaufene Zertifizierungen gefunden')
    )

    class Meta:
        verbose_name = _('Kleiderkammer Inventur')
        verbose_name_plural = _('Kleiderkammer Inventuren')
        ordering = ['-scheduled_start_date']
        permissions = [
            ('approve_clothinginventorycheck', 'Kann Kleiderkammer-Inventuren genehmigen'),
        ]

    def get_number_prefix(self):
        """Clothing-spezifisches Präfix für Inventurnummern"""
        return 'CLO-INV'

    def update_progress(self):
        """Clothing-spezifische Fortschritts-Berechnung"""
        from django.utils import timezone

        self.total_items = self.items.count()
        self.counted_items = self.items.filter(is_counted=True).count()
        self.items_with_discrepancies = self.items.filter(has_discrepancy=True).count()

        # Zähle beschädigte Artikel
        if self.check_condition:
            self.damaged_items_found = self.items.filter(is_damaged=True).count()

        # Zähle abgelaufene PSA-Zertifizierungen
        if self.check_psa:
            self.expired_certifications_found = self.items.filter(
                is_psa=True,
                certification_expired=True
            ).count()

        self.save(update_fields=[
            'total_items',
            'counted_items',
            'items_with_discrepancies',
            'damaged_items_found',
            'expired_certifications_found'
        ])


class ClothingInventoryCheckItem(AbstractInventoryCheckItem):
    """
    Einzelne Position in Clothing-Inventur
    Erbt alle Basis-Felder von AbstractInventoryCheckItem
    """

    inventory_check = models.ForeignKey(
        ClothingInventoryCheck,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_('Inventur-Check')
    )

    # Referenz zu Clothing-Item
    clothing_item = models.ForeignKey(
        ClothingItem,
        on_delete=models.PROTECT,
        null=True, blank=True,
        related_name='inventory_items',
        verbose_name=_('Kleidungsstück')
    )

    # Clothing-spezifische Felder
    clothing_type = models.CharField(
        max_length=20,
        choices=ClothingType.choices,
        blank=True,
        verbose_name=_('Kleidungstyp')
    )

    size = models.CharField(
        max_length=10,
        choices=ClothingSize.choices,
        blank=True,
        verbose_name=_('Größe')
    )

    condition = models.CharField(
        max_length=20,
        choices=ItemCondition.choices,
        blank=True,
        verbose_name=_('Zustand')
    )

    is_psa = models.BooleanField(
        default=False,
        verbose_name=_('PSA-Artikel')
    )

    is_damaged = models.BooleanField(
        default=False,
        verbose_name=_('Beschädigt')
    )

    certification_expires = models.DateField(
        null=True, blank=True,
        verbose_name=_('Zertifizierung läuft ab')
    )

    certification_expired = models.BooleanField(
        default=False,
        verbose_name=_('Zertifizierung abgelaufen')
    )

    class Meta:
        verbose_name = _('Kleiderkammer Inventur-Position')
        verbose_name_plural = _('Kleiderkammer Inventur-Positionen')
        ordering = ['location__name', 'clothing_type', 'size', 'item_name']


# ============================================================================
# MASTER/INSTANCE ARCHITECTURE (NEW)
# ============================================================================

class ClothingItemMaster(AuditedModel):
    """
    Stammdaten für Kleidungsprodukte (z.B. Hupfjacke TEXPORT Fire Twin)
    Enthält allgemeine Produktinformationen, nicht größen-/farbspezifisch
    """

    name = models.CharField(
        max_length=255,
        verbose_name=_('Produktname'),
        help_text=_('z.B. "Hupfjacke TEXPORT Fire Twin", "Poloshirt Feuerwehr"')
    )

    category = models.ForeignKey(
        ClothingCategory,
        on_delete=models.PROTECT,
        related_name='masters',
        verbose_name=_('Kategorie')
    )

    product_type = models.ForeignKey(
        ClothingProductType,
        on_delete=models.PROTECT,
        related_name='masters',
        verbose_name=_('Produkttyp'),
        null=True,
        blank=True
    )

    # Legacy field - wird durch product_type ersetzt
    clothing_type = models.CharField(
        max_length=20,
        choices=ClothingType.choices,
        verbose_name=_('Kleidungstyp (Legacy)'),
        blank=True,
        default=''
    )

    # Hersteller-Informationen
    manufacturer = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Hersteller')
    )

    model_number = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Modellnummer/Artikelnummer')
    )

    description = models.TextField(
        blank=True,
        verbose_name=_('Beschreibung')
    )

    # Material & Eigenschaften
    material = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Material'),
        help_text=_('z.B. "Nomex", "Gore-Tex", "100% Baumwolle"')
    )

    # PSA-Informationen
    is_psa = models.BooleanField(
        default=False,
        verbose_name=_('Persönliche Schutzausrüstung (PSA)')
    )

    protection_level = models.CharField(
        max_length=20,
        choices=ProtectionLevel.choices,
        default=ProtectionLevel.NONE,
        verbose_name=_('Schutzlevel')
    )

    norm_standard = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Norm/Standard'),
        help_text=_('z.B. "EN 469", "EN ISO 20471"')
    )

    # Lebensdauer & Pflege
    max_usage_years = models.PositiveIntegerField(
        null=True, blank=True,
        verbose_name=_('Max. Nutzungsdauer (Jahre)')
    )

    max_washing_cycles = models.PositiveIntegerField(
        null=True, blank=True,
        verbose_name=_('Max. Waschzyklen')
    )

    washing_instructions = models.TextField(
        blank=True,
        verbose_name=_('Waschanleitung/Pflegehinweise')
    )

    # Prüfung
    requires_inspection = models.BooleanField(
        default=False,
        verbose_name=_('Prüfpflicht')
    )

    inspection_interval_months = models.PositiveIntegerField(
        null=True, blank=True,
        verbose_name=_('Prüfintervall (Monate)')
    )

    # Preis
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True, blank=True,
        verbose_name=_('Stückpreis (EUR)')
    )

    # Dokumente
    manual_document = models.FileField(
        upload_to='clothing/masters/manuals/',
        null=True, blank=True,
        verbose_name=_('Handbuch/Datenblatt')
    )

    image = models.ImageField(
        upload_to='clothing/masters/images/',
        null=True, blank=True,
        verbose_name=_('Produktbild')
    )

    # Besondere Merkmale
    special_features = models.TextField(
        blank=True,
        verbose_name=_('Besondere Merkmale'),
        help_text=_('z.B. "Verstärkte Knie", "Herausnehmbares Futter"')
    )

    # Verfügbare Größen (JSON Array)
    available_sizes = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_('Verfügbare Größen'),
        help_text=_('Liste der verfügbaren Größen')
    )

    # Verfügbare Farben (JSON Array)
    available_colors = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_('Verfügbare Farben'),
        help_text=_('Liste der verfügbaren Farben')
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Aktiv')
    )

    class Meta:
        verbose_name = _('Kleidungs-Stammdaten')
        verbose_name_plural = _('Kleidungs-Stammdaten')
        ordering = ['category', 'clothing_type', 'name']

    def __str__(self):
        return f"{self.name} ({self.get_clothing_type_display()})"

    @property
    def total_instances(self):
        """Gesamtzahl aller Instanzen"""
        return self.instances.count()

    @property
    def available_instances(self):
        """Anzahl verfügbarer (nicht zugewiesener) Instanzen"""
        return self.instances.filter(assigned_to__isnull=True, is_active=True).count()


class ClothingItemInstance(AuditedModel):
    """
    Konkretes Kleidungsstück mit spezifischen Eigenschaften
    (Größe, Farbe, Seriennummer, zugewiesene Person)
    """

    master = models.ForeignKey(
        ClothingItemMaster,
        on_delete=models.PROTECT,
        related_name='instances',
        verbose_name=_('Stammdaten')
    )

    # Eindeutige Kennung
    inventory_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_('Inventarnummer'),
        help_text=_('Eindeutige Inventarnummer, z.B. "CLO-0001"')
    )

    # Spezifische Eigenschaften
    size = models.CharField(
        max_length=10,
        choices=ClothingSize.choices,
        verbose_name=_('Größe')
    )

    gender = models.CharField(
        max_length=10,
        choices=Gender.choices,
        default=Gender.UNISEX,
        verbose_name=_('Schnitt')
    )

    color = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_('Farbe')
    )

    # Zustand
    condition = models.CharField(
        max_length=20,
        choices=ItemCondition.choices,
        default=ItemCondition.NEW,
        verbose_name=_('Zustand')
    )

    # Lagerort
    location = models.ForeignKey(
        'locations.Location',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='clothing_instances',
        verbose_name=_('Lagerort')
    )

    # Personenzuordnung
    assigned_to = models.ForeignKey(
        'personnel.Person',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='clothing_instances',
        verbose_name=_('Zugeordnet an')
    )

    assignment_date = models.DateField(
        null=True, blank=True,
        verbose_name=_('Zugeordnet am')
    )

    is_personal_issue = models.BooleanField(
        default=False,
        verbose_name=_('Persönliche Ausgabe')
    )

    # Zertifizierung (instanzspezifisch)
    certification_number = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Zertifizierungsnummer')
    )

    certification_date = models.DateField(
        null=True, blank=True,
        verbose_name=_('Zertifizierungsdatum')
    )

    certification_expires = models.DateField(
        null=True, blank=True,
        verbose_name=_('Zertifizierung läuft ab')
    )

    # Nutzung & Pflege
    purchase_date = models.DateField(
        null=True, blank=True,
        verbose_name=_('Kaufdatum')
    )

    first_use_date = models.DateField(
        null=True, blank=True,
        verbose_name=_('Erstverwendung')
    )

    current_washing_cycles = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Aktuelle Waschzyklen')
    )

    last_washing_date = models.DateField(
        null=True, blank=True,
        verbose_name=_('Letzte Wäsche')
    )

    # Prüfung
    last_inspection_date = models.DateField(
        null=True, blank=True,
        verbose_name=_('Letzte Prüfung')
    )

    next_inspection_date = models.DateField(
        null=True, blank=True,
        verbose_name=_('Nächste Prüfung')
    )

    # Kennzeichnung
    has_name_tag = models.BooleanField(
        default=False,
        verbose_name=_('Namensschildversehen')
    )

    serial_number = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Seriennummer')
    )

    # Notizen
    notes = models.TextField(
        blank=True,
        verbose_name=_('Notizen')
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Aktiv')
    )

    class Meta:
        verbose_name = _('Kleidungsstück-Instanz')
        verbose_name_plural = _('Kleidungsstück-Instanzen')
        ordering = ['master__name', 'size', 'inventory_number']
        indexes = [
            models.Index(fields=['inventory_number']),
            models.Index(fields=['assigned_to']),
            models.Index(fields=['master', 'size']),
        ]

    def __str__(self):
        assigned = f" [{self.assigned_to}]" if self.assigned_to else ""
        return f"{self.inventory_number} - {self.master.name} ({self.get_size_display()}){assigned}"

    def is_inspection_due(self):
        """Prüft ob Prüfung fällig ist"""
        if self.next_inspection_date:
            from django.utils import timezone
            return self.next_inspection_date <= timezone.now().date()
        return False

    def is_certification_expired(self):
        """Prüft ob Zertifizierung abgelaufen ist"""
        if self.certification_expires:
            from django.utils import timezone
            return self.certification_expires < timezone.now().date()
        return False

    def is_washing_limit_reached(self):
        """Prüft ob maximale Waschzyklen erreicht"""
        if self.master.max_washing_cycles:
            return self.current_washing_cycles >= self.master.max_washing_cycles
        return False

    def days_until_inspection(self):
        """Tage bis zur nächsten Prüfung"""
        if self.next_inspection_date:
            from django.utils import timezone
            delta = self.next_inspection_date - timezone.now().date()
            return delta.days
        return None
