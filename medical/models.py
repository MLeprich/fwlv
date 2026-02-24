"""
Medical Models
Rettungsdienst-Verwaltung (Medikamente, Medizintechnik, BTM)
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from django.conf import settings
from django.utils import timezone
from decimal import Decimal

from inventory_base.models import (
    AbstractInventoryItem,
    AbstractStockMovement,
    StockMovementType,
)


# ============================================================================
# ENUMS & CHOICES
# ============================================================================

class MedicalItemType(models.TextChoices):
    """Typen von Medizin-Artikeln"""
    MEDICATION = 'medication', _('Medikament')
    BTM = 'btm', _('Betäubungsmittel (BTM)')
    INFUSION = 'infusion', _('Infusion')
    INJECTION = 'injection', _('Injektion')
    BANDAGE = 'bandage', _('Verbandmaterial')
    DIAGNOSTIC = 'diagnostic', _('Diagnostik')
    DEVICE = 'device', _('Medizintechnik')
    DISINFECTANT = 'disinfectant', _('Desinfektionsmittel')
    OXYGEN = 'oxygen', _('Sauerstoff')
    DISPOSABLE = 'disposable', _('Einwegartikel')
    OTHER = 'other', _('Sonstiges')


class AdministrationRoute(models.TextChoices):
    """Verabreichungsweg"""
    ORAL = 'oral', _('Oral')
    IV = 'iv', _('Intravenös (i.v.)')
    IM = 'im', _('Intramuskulär (i.m.)')
    SC = 'sc', _('Subkutan (s.c.)')
    INHALATION = 'inhalation', _('Inhalation')
    TOPICAL = 'topical', _('Topisch (Haut)')
    RECTAL = 'rectal', _('Rektal')
    SUBLINGUAL = 'sublingual', _('Sublingual')
    OTHER = 'other', _('Sonstiges')


class StorageCondition(models.TextChoices):
    """Lagerungsbedingungen"""
    ROOM_TEMP = 'room_temp', _('Raumtemperatur (15-25°C)')
    REFRIGERATED = 'refrigerated', _('Gekühlt (2-8°C)')
    FROZEN = 'frozen', _('Gefroren (<-15°C)')
    DARK = 'dark', _('Dunkel')
    DRY = 'dry', _('Trocken')
    SPECIAL = 'special', _('Spezielle Bedingungen')


class BTMApprovalStatus(models.TextChoices):
    """Status für BTM-Freigaben (Vier-Augen-Prinzip)"""
    PENDING = 'pending', _('Ausstehend')
    APPROVED = 'approved', _('Freigegeben')
    REJECTED = 'rejected', _('Abgelehnt')


class MedicalUnit(models.TextChoices):
    """Einheiten für medizinische Artikel"""
    # Stück/Mengen
    PIECE = 'Stück', _('Stück')
    PACKAGE = 'Packung', _('Packung')
    BOX = 'Karton', _('Karton')
    PAIR = 'Paar', _('Paar')
    SET = 'Set', _('Set')

    # Volumen
    ML = 'ml', _('Milliliter (ml)')
    L = 'l', _('Liter (l)')

    # Gewicht
    MG = 'mg', _('Milligramm (mg)')
    G = 'g', _('Gramm (g)')
    KG = 'kg', _('Kilogramm (kg)')

    # Medizinische Einheiten
    AMPULE = 'Ampulle', _('Ampulle')
    VIAL = 'Durchstechflasche', _('Durchstechflasche')
    TABLET = 'Tablette', _('Tablette')
    CAPSULE = 'Kapsel', _('Kapsel')
    BLISTER = 'Blister', _('Blister')
    TUBE = 'Tube', _('Tube')
    BOTTLE = 'Flasche', _('Flasche')
    BAG = 'Beutel', _('Beutel')
    ROLL = 'Rolle', _('Rolle')

    # Gas
    LITER_GAS = 'Liter (Gas)', _('Liter (Gas)')
    M3 = 'm³', _('Kubikmeter (m³)')


# ============================================================================
# MEDICAL ITEM MASTER (Stammdaten)
# ============================================================================

class MedicalItemMaster(models.Model):
    """
    Artikel-Stammdaten für medizinische Artikel
    Beschreibt das Produkt allgemein (nicht einzelne Lagerartikel)
    Konkrete Lagerartikel werden über MedicalBatch (Verbrauchsmaterial)
    oder MedicalDeviceInstance (Medizintechnik) verwaltet
    """

    # Basis-Identifikation
    master_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_('Stammdatennummer'),
        help_text=_('Eindeutige Stammdatennummer (z.B. MASTER-MED-001)')
    )

    name = models.CharField(
        max_length=255,
        verbose_name=_('Artikelname')
    )

    description = models.TextField(
        blank=True,
        verbose_name=_('Beschreibung')
    )

    # Kategorisierung
    item_type = models.CharField(
        max_length=20,
        choices=MedicalItemType.choices,
        default=MedicalItemType.MEDICATION,
        verbose_name=_('Artikeltyp')
    )

    category = models.ForeignKey(
        'inventory_base.Category',
        on_delete=models.PROTECT,
        related_name='medical_master_items',
        null=True, blank=True,
        verbose_name=_('Kategorie')
    )

    # BTM-Kennzeichnung
    is_btm = models.BooleanField(
        default=False,
        verbose_name=_('Betäubungsmittel (BTM)'),
        help_text=_('Unterliegt dem Betäubungsmittelgesetz')
    )

    # Pharmazeutische Informationen
    active_ingredient = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Wirkstoff'),
        help_text=_('z.B. "Paracetamol", "Morphin"')
    )

    dosage = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Dosierung'),
        help_text=_('z.B. "500mg", "10ml"')
    )

    pharmaceutical_form = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Darreichungsform'),
        help_text=_('z.B. "Tabletten", "Ampullen", "Salbe"')
    )

    administration_route = models.CharField(
        max_length=20,
        choices=AdministrationRoute.choices,
        blank=True,
        verbose_name=_('Verabreichungsweg')
    )

    # Zulassung & Identifikation
    pzn = models.CharField(
        max_length=20,
        blank=True,
        unique=True,
        null=True,
        verbose_name=_('PZN (Pharmazentralnummer)'),
        help_text=_('Deutsche Pharmazentralnummer')
    )

    atc_code = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_('ATC-Code'),
        help_text=_('Anatomisch-Therapeutisch-Chemisches Klassifikationssystem')
    )

    approval_number = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_('Zulassungsnummer')
    )

    # Bestellinformationen
    manufacturer = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_('Hersteller')
    )

    supplier = models.ForeignKey(
        'inventory_base.Supplier',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='medical_master_items',
        verbose_name=_('Hauptlieferant')
    )

    internal_order_number = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Interne Bestellnummer'),
        help_text=_('Interne Artikelnummer des Lieferanten')
    )

    external_order_number = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Externe Bestellnummer'),
        help_text=_('Externe Bestellnummer / Herstellernummer')
    )

    # Generikum / Alternative Produkte
    generic_alternative = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_('Generikum'),
        help_text=_('Alternative Produkte / Generika')
    )

    # Einheit
    unit = models.CharField(
        max_length=50,
        choices=MedicalUnit.choices,
        default=MedicalUnit.PIECE,
        verbose_name=_('Einheit')
    )

    # Haltbarkeit & Lagerung
    expiry_warning_days = models.PositiveIntegerField(
        default=90,
        verbose_name=_('Ablauf-Warnung (Tage)'),
        help_text=_('Warnung X Tage vor Ablauf')
    )

    storage_condition = models.CharField(
        max_length=20,
        choices=StorageCondition.choices,
        default=StorageCondition.ROOM_TEMP,
        verbose_name=_('Lagerungsbedingungen')
    )

    requires_cold_chain = models.BooleanField(
        default=False,
        verbose_name=_('Kühlkette erforderlich'),
        help_text=_('Lückenlose Kühlung notwendig')
    )

    # Verschreibung & Rechtliches
    is_prescription_required = models.BooleanField(
        default=False,
        verbose_name=_('Verschreibungspflichtig')
    )

    # Dokumente
    package_insert = models.FileField(
        upload_to='medical/package_inserts/',
        null=True, blank=True,
        verbose_name=_('Beipackzettel'),
        help_text=_('PDF-Datei des Beipackzettels')
    )

    spc_document = models.FileField(
        upload_to='medical/spc/',
        null=True, blank=True,
        verbose_name=_('Fachinformation (SPC)'),
        help_text=_('Summary of Product Characteristics')
    )

    manual_document = models.FileField(
        upload_to='medical/manuals/',
        null=True, blank=True,
        verbose_name=_('Handbuch / Bedienungsanleitung'),
        help_text=_('PDF oder Bild-Datei (wird automatisch per OCR durchsuchbar gemacht)')
    )

    # Medizinprodukte
    is_medical_device = models.BooleanField(
        default=False,
        verbose_name=_('Medizinprodukt'),
        help_text=_('Unterliegt Medizinproduktegesetz (MPG)')
    )

    medical_device_class = models.CharField(
        max_length=10,
        blank=True,
        verbose_name=_('Medizinprodukte-Klasse'),
        help_text=_('z.B. "I", "IIa", "IIb", "III"')
    )

    udi = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('UDI (Unique Device Identifier)')
    )

    # Wartung & Prüfung (für Geräte)
    requires_maintenance = models.BooleanField(
        default=False,
        verbose_name=_('Wartung erforderlich')
    )

    maintenance_interval_months = models.PositiveIntegerField(
        null=True, blank=True,
        verbose_name=_('Wartungsintervall (Monate)')
    )

    # Bestandsmanagement
    min_quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True, blank=True,
        verbose_name=_('Mindestbestand')
    )

    max_quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True, blank=True,
        verbose_name=_('Maximalbestand')
    )

    # Zusatzinformationen
    indications = models.TextField(
        blank=True,
        verbose_name=_('Indikationen'),
        help_text=_('Anwendungsgebiete')
    )

    contraindications = models.TextField(
        blank=True,
        verbose_name=_('Kontraindikationen'),
        help_text=_('Gegenanzeigen')
    )

    side_effects = models.TextField(
        blank=True,
        verbose_name=_('Nebenwirkungen')
    )

    notes = models.TextField(
        blank=True,
        verbose_name=_('Notizen')
    )

    # Bild
    image = models.ImageField(
        upload_to='medical/items/',
        null=True, blank=True,
        verbose_name=_('Artikelbild')
    )

    # Status
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Aktiv')
    )

    # Audit-Felder
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Erstellt am')
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Aktualisiert am')
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='created_medical_masters',
        verbose_name=_('Erstellt von')
    )

    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='updated_medical_masters',
        verbose_name=_('Aktualisiert von')
    )

    class Meta:
        verbose_name = _('Medizinische Stammdaten')
        verbose_name_plural = _('Medizinische Stammdaten')
        ordering = ['master_number']
        indexes = [
            models.Index(fields=['master_number']),
            models.Index(fields=['item_type', 'category']),
            models.Index(fields=['is_btm']),
            models.Index(fields=['pzn']),
            models.Index(fields=['atc_code']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        btm_marker = ' [BTM]' if self.is_btm else ''
        return f"{self.master_number} - {self.name}{btm_marker}"

    def generate_qr_code(self):
        """
        Generiert QR-Code als SVG für die Stammdaten
        Enthält nur die URL für direkten Zugriff
        """
        import qrcode
        import qrcode.image.svg
        from io import BytesIO

        # Nur URL kodieren für maximale Scanner-Kompatibilität
        qr_string = f'/medical/masters/{self.pk}/'

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
        """
        Generiert Barcode als SVG für die Stammdatennummer
        """
        import barcode
        from barcode.writer import SVGWriter
        from io import BytesIO

        code128 = barcode.get_barcode_class('code128')

        rv = BytesIO()
        code = code128(self.master_number, writer=SVGWriter())
        code.write(rv)

        svg_string = rv.getvalue().decode('utf-8')
        return svg_string

    def get_total_stock(self):
        """
        Berechnet den Gesamtbestand über alle Chargen/Instanzen
        """
        if self.item_type == MedicalItemType.DEVICE:
            # Medizintechnik: Anzahl aktiver Instanzen
            return self.device_instances.filter(is_active=True).count()
        else:
            # Verbrauchsmaterial: Summe aller Chargen
            from django.db.models import Sum
            total = self.batches.filter(
                quantity_remaining__gt=0
            ).aggregate(total=Sum('quantity_remaining'))['total']
            return total or 0

    def get_available_batches(self):
        """
        Gibt verfügbare Chargen zurück (nur für Verbrauchsmaterial)
        """
        if self.item_type != MedicalItemType.DEVICE:
            return self.batches.filter(
                quantity_remaining__gt=0,
                is_recalled=False
            ).order_by('expiry_date')
        return []


# ============================================================================
# MEDICAL DEVICE INSTANCE (Medizintechnik-Instanzen)
# ============================================================================

class MedicalDeviceInstance(models.Model):
    """
    Konkrete Medizintechnik-Instanz mit eigener Inventarnummer
    Beispiel: Jedes Corpuls C3 Gerät bekommt eine eigene Instanz
    für individuelle Prüfungen und Wartungen
    """

    master = models.ForeignKey(
        MedicalItemMaster,
        on_delete=models.PROTECT,
        related_name='device_instances',
        verbose_name=_('Stammdaten')
    )

    inventory_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_('Inventarnummer'),
        help_text=_('Eindeutige Inventarnummer (z.B. DEV-CORPULS-001)')
    )

    serial_number = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Seriennummer'),
        help_text=_('Hersteller-Seriennummer')
    )

    # Zusätzliche Inventarnummern für Module/Komponenten
    additional_inventory_numbers = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_('Zusätzliche Inventarnummern'),
        help_text=_('Inventarnummern für Module/Komponenten dieses Geräts')
    )

    location = models.ForeignKey(
        'locations.Location',
        on_delete=models.PROTECT,
        related_name='medical_device_instances',
        verbose_name=_('Lagerort')
    )

    # Wartung & Prüfung
    purchase_date = models.DateField(
        null=True, blank=True,
        verbose_name=_('Anschaffungsdatum')
    )

    commissioning_date = models.DateField(
        null=True, blank=True,
        verbose_name=_('Inbetriebnahme')
    )

    last_maintenance_date = models.DateField(
        null=True, blank=True,
        verbose_name=_('Letzte Wartung')
    )

    next_maintenance_date = models.DateField(
        null=True, blank=True,
        verbose_name=_('Nächste Wartung')
    )

    last_inspection_date = models.DateField(
        null=True, blank=True,
        verbose_name=_('Letzte Prüfung')
    )

    next_inspection_date = models.DateField(
        null=True, blank=True,
        verbose_name=_('Nächste Prüfung')
    )

    # Kosten
    purchase_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True, blank=True,
        verbose_name=_('Anschaffungspreis (EUR)')
    )

    # Status
    condition = models.CharField(
        max_length=20,
        choices=[
            ('new', _('Neu')),
            ('good', _('Gut')),
            ('fair', _('Befriedigend')),
            ('poor', _('Mangelhaft')),
            ('defect', _('Defekt')),
        ],
        default='good',
        verbose_name=_('Zustand')
    )

    is_operational = models.BooleanField(
        default=True,
        verbose_name=_('Einsatzbereit'),
        help_text=_('Gerät ist funktionsfähig und einsatzbereit')
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Aktiv'),
        help_text=_('Gerät ist im Bestand (nicht ausgemustert)')
    )

    decommissioned_date = models.DateField(
        null=True, blank=True,
        verbose_name=_('Ausgemustert am')
    )

    decommissioned_reason = models.TextField(
        blank=True,
        verbose_name=_('Ausmusterungsgrund')
    )

    # Notizen
    notes = models.TextField(
        blank=True,
        verbose_name=_('Notizen')
    )

    # Audit-Felder
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Erstellt am')
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Aktualisiert am')
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='created_device_instances',
        verbose_name=_('Erstellt von')
    )

    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='updated_device_instances',
        verbose_name=_('Aktualisiert von')
    )

    class Meta:
        verbose_name = _('Medizintechnik-Instanz')
        verbose_name_plural = _('Medizintechnik-Instanzen')
        ordering = ['inventory_number']
        indexes = [
            models.Index(fields=['inventory_number']),
            models.Index(fields=['master', 'is_active']),
            models.Index(fields=['next_maintenance_date']),
            models.Index(fields=['next_inspection_date']),
            models.Index(fields=['is_operational']),
        ]

    def __str__(self):
        status = '✓' if self.is_operational else '✗'
        return f"{status} {self.inventory_number} - {self.master.name}"

    def generate_qr_code(self):
        """
        Generiert QR-Code als SVG für die Geräte-Instanz
        Enthält nur die URL für direkten Zugriff
        """
        import qrcode
        import qrcode.image.svg
        from io import BytesIO

        # Nur URL kodieren für maximale Scanner-Kompatibilität
        qr_string = f'/medical/devices/{self.pk}/'

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
        """
        Generiert Barcode als SVG für die Inventarnummer
        """
        import barcode
        from barcode.writer import SVGWriter
        from io import BytesIO

        code128 = barcode.get_barcode_class('code128')

        rv = BytesIO()
        code = code128(self.inventory_number, writer=SVGWriter())
        code.write(rv)

        svg_string = rv.getvalue().decode('utf-8')
        return svg_string

    def is_maintenance_due(self):
        """Prüft ob Wartung fällig ist"""
        if self.next_maintenance_date:
            return self.next_maintenance_date <= timezone.now().date()
        return False

    def is_inspection_due(self):
        """Prüft ob Prüfung fällig ist"""
        if self.next_inspection_date:
            return self.next_inspection_date <= timezone.now().date()
        return False


# ============================================================================
# LEGACY SUPPORT: MedicalItem (wird deprecated)
# ============================================================================

class MedicalItem(AbstractInventoryItem):
    """
    Medizinischer Artikel (Medikamente, Medizintechnik)
    Erbt alle Basis-Felder von AbstractInventoryItem
    """

    # Medizin-spezifische Felder
    item_type = models.CharField(
        max_length=20,
        choices=MedicalItemType.choices,
        default=MedicalItemType.MEDICATION,
        verbose_name=_('Artikeltyp')
    )

    # BTM-Kennzeichnung (wichtig für Sicherheit)
    is_btm = models.BooleanField(
        default=False,
        verbose_name=_('Betäubungsmittel (BTM)'),
        help_text=_('Unterliegt dem Betäubungsmittelgesetz')
    )

    # Pharmazeutische Informationen
    active_ingredient = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Wirkstoff'),
        help_text=_('z.B. "Paracetamol", "Morphin"')
    )

    dosage = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Dosierung'),
        help_text=_('z.B. "500mg", "10ml"')
    )

    pharmaceutical_form = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Darreichungsform'),
        help_text=_('z.B. "Tabletten", "Ampullen", "Salbe"')
    )

    administration_route = models.CharField(
        max_length=20,
        choices=AdministrationRoute.choices,
        blank=True,
        verbose_name=_('Verabreichungsweg')
    )

    # Zulassung & Identifikation
    pzn = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_('PZN (Pharmazentralnummer)'),
        help_text=_('Deutsche Pharmazentralnummer')
    )

    atc_code = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_('ATC-Code'),
        help_text=_('Anatomisch-Therapeutisch-Chemisches Klassifikationssystem')
    )

    approval_number = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_('Zulassungsnummer')
    )

    # Bestellnummern
    internal_order_number = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Interne Bestellnummer'),
        help_text=_('Interne Artikelnummer des Lieferanten')
    )

    external_order_number = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Externe Bestellnummer'),
        help_text=_('Externe Bestellnummer / Herstellernummer')
    )

    # Generikum / Alternative Produkte
    generic_alternative = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_('Generikum'),
        help_text=_('Alternative Produkte / Generika')
    )

    # Haltbarkeit & Lagerung
    expiry_warning_days = models.PositiveIntegerField(
        default=90,
        verbose_name=_('Ablauf-Warnung (Tage)'),
        help_text=_('Warnung X Tage vor Ablauf')
    )

    storage_condition = models.CharField(
        max_length=20,
        choices=StorageCondition.choices,
        default=StorageCondition.ROOM_TEMP,
        verbose_name=_('Lagerungsbedingungen')
    )

    requires_cold_chain = models.BooleanField(
        default=False,
        verbose_name=_('Kühlkette erforderlich'),
        help_text=_('Lückenlose Kühlung notwendig')
    )

    # Verschreibung & Rechtliches
    is_prescription_required = models.BooleanField(
        default=False,
        verbose_name=_('Verschreibungspflichtig')
    )

    package_insert = models.FileField(
        upload_to='medical/package_inserts/',
        null=True, blank=True,
        verbose_name=_('Beipackzettel'),
        help_text=_('PDF-Datei des Beipackzettels')
    )

    spc_document = models.FileField(
        upload_to='medical/spc/',
        null=True, blank=True,
        verbose_name=_('Fachinformation (SPC)'),
        help_text=_('Summary of Product Characteristics')
    )

    manual_document = models.FileField(
        upload_to='medical/manuals/',
        null=True, blank=True,
        verbose_name=_('Handbuch / Bedienungsanleitung'),
        help_text=_('PDF oder Bild-Datei (wird automatisch per OCR durchsuchbar gemacht)')
    )

    # Medizinprodukte
    is_medical_device = models.BooleanField(
        default=False,
        verbose_name=_('Medizinprodukt'),
        help_text=_('Unterliegt Medizinproduktegesetz (MPG)')
    )

    medical_device_class = models.CharField(
        max_length=10,
        blank=True,
        verbose_name=_('Medizinprodukte-Klasse'),
        help_text=_('z.B. "I", "IIa", "IIb", "III"')
    )

    udi = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('UDI (Unique Device Identifier)')
    )

    # Wartung & Prüfung (für Geräte)
    requires_maintenance = models.BooleanField(
        default=False,
        verbose_name=_('Wartung erforderlich')
    )

    maintenance_interval_months = models.PositiveIntegerField(
        null=True, blank=True,
        verbose_name=_('Wartungsintervall (Monate)')
    )

    last_maintenance_date = models.DateField(
        null=True, blank=True,
        verbose_name=_('Letzte Wartung')
    )

    next_maintenance_date = models.DateField(
        null=True, blank=True,
        verbose_name=_('Nächste Wartung')
    )

    # Zusatzinformationen
    indications = models.TextField(
        blank=True,
        verbose_name=_('Indikationen'),
        help_text=_('Anwendungsgebiete')
    )

    contraindications = models.TextField(
        blank=True,
        verbose_name=_('Kontraindikationen'),
        help_text=_('Gegenanzeigen')
    )

    side_effects = models.TextField(
        blank=True,
        verbose_name=_('Nebenwirkungen')
    )

    class Meta:
        verbose_name = _('Medizinischer Artikel')
        verbose_name_plural = _('Medizinische Artikel')
        ordering = ['item_number']
        indexes = [
            models.Index(fields=['item_type', 'category']),
            models.Index(fields=['is_btm']),
            models.Index(fields=['pzn']),
            models.Index(fields=['atc_code']),
            models.Index(fields=['next_maintenance_date']),
        ]

    def __str__(self):
        btm_marker = ' [BTM]' if self.is_btm else ''
        return f"{self.item_number} - {self.name}{btm_marker}"

    def generate_qr_code(self):
        """
        Generiert QR-Code als SVG für den Artikel
        Enthält nur die URL für direkten Zugriff
        """
        import qrcode
        import qrcode.image.svg
        from io import BytesIO

        # Nur URL kodieren für maximale Scanner-Kompatibilität
        qr_string = f'/medical/items/{self.pk}/'

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
        Generiert Barcode als SVG (falls PZN vorhanden)
        PZN wird als Code128 generiert
        """
        if not self.pzn:
            return None

        import barcode
        from barcode.writer import SVGWriter
        from io import BytesIO

        # Code128 für PZN
        code128 = barcode.get_barcode_class('code128')

        # Barcode generieren
        rv = BytesIO()
        code = code128(self.pzn, writer=SVGWriter())
        code.write(rv)

        svg_string = rv.getvalue().decode('utf-8')
        return svg_string

    def is_maintenance_due(self):
        """Prüft ob Wartung fällig ist"""
        if self.next_maintenance_date:
            return self.next_maintenance_date <= timezone.now().date()
        return False


# ============================================================================
# MEDICAL STOCK MOVEMENT
# ============================================================================

class MedicalStockMovement(AbstractStockMovement):
    """
    Lagerbewegungen für medizinische Artikel
    BTM-Bewegungen erfordern Freigabe (Vier-Augen-Prinzip)
    """

    item = models.ForeignKey(
        MedicalItemMaster,
        on_delete=models.PROTECT,
        null=True, blank=True,
        related_name='stock_movements',
        verbose_name=_('Artikel')
    )

    # Chargen-Information
    batch_number = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Chargen-/Batch-Nummer')
    )

    expiry_date = models.DateField(
        null=True, blank=True,
        verbose_name=_('Verfallsdatum')
    )

    # Medizinischer Kontext
    patient_id = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_('Patienten-ID'),
        help_text=_('Anonymisierte Patienten-ID (nur bei Verabreichung)')
    )

    diagnosis = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Diagnose/Indikation')
    )

    administered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='medical_administrations',
        verbose_name=_('Verabreicht durch'),
        help_text=_('Person die das Medikament verabreicht hat')
    )

    # BTM-spezifisch: Vier-Augen-Prinzip
    requires_approval = models.BooleanField(
        default=False,
        verbose_name=_('Freigabe erforderlich'),
        help_text=_('BTM-Bewegungen erfordern Freigabe')
    )

    approval_status = models.CharField(
        max_length=20,
        choices=BTMApprovalStatus.choices,
        default=BTMApprovalStatus.PENDING,
        verbose_name=_('Freigabe-Status')
    )

    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='btm_approvals',
        verbose_name=_('Freigegeben durch')
    )

    approved_at = models.DateTimeField(
        null=True, blank=True,
        verbose_name=_('Freigegeben am')
    )

    rejection_reason = models.TextField(
        blank=True,
        verbose_name=_('Ablehnungsgrund')
    )

    # Dokumente
    prescription_number = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Rezeptnummer')
    )

    delivery_note = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Lieferschein-Nr.')
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

    class Meta:
        verbose_name = _('Lagerbewegung')
        verbose_name_plural = _('Lagerbewegungen')
        ordering = ['-movement_date']
        indexes = [
            models.Index(fields=['item', '-movement_date']),
            models.Index(fields=['movement_type', '-movement_date']),
            models.Index(fields=['batch_number']),
            models.Index(fields=['expiry_date']),
            models.Index(fields=['approval_status']),
        ]

    def __str__(self):
        btm_marker = ' [BTM-Freigabe erforderlich]' if self.requires_approval else ''
        return f"{self.get_movement_type_display()} - {self.item.name} ({self.quantity} {self.unit}){btm_marker}"

    def save(self, *args, **kwargs):
        """
        Automatische Berechnungen und BTM-Check
        """
        # BTM-Check: Wenn Item BTM ist, Freigabe erforderlich
        if self.item and self.item.is_btm:
            if self.movement_type in [StockMovementType.OUTGOING, StockMovementType.DISPOSAL]:
                self.requires_approval = True

        # Kosten berechnen
        if self.unit_cost and not self.total_cost:
            self.total_cost = self.unit_cost * self.quantity

        # Unit von Item übernehmen
        if not self.unit and self.item:
            self.unit = self.item.unit

        super().save(*args, **kwargs)

        # Bestand nur aktualisieren wenn:
        # - Kein BTM ODER
        # - BTM mit approval_status APPROVED
        if not self.requires_approval or self.approval_status == BTMApprovalStatus.APPROVED:
            self.update_item_stock()

    def update_item_stock(self):
        """
        Aktualisiert den Chargen-Bestand basierend auf der Bewegung.
        Bestand wird über MedicalBatch.quantity_remaining verwaltet.
        """
        if not self.batch_number or not self.item:
            return

        try:
            batch = MedicalBatch.objects.get(
                master=self.item,
                batch_number=self.batch_number,
            )
        except MedicalBatch.DoesNotExist:
            return

        if self.movement_type in [StockMovementType.OUTGOING, StockMovementType.DAMAGE, StockMovementType.DISPOSAL]:
            batch.quantity_remaining -= self.quantity
        elif self.movement_type == StockMovementType.INVENTORY:
            batch.quantity_remaining = self.quantity
        elif self.movement_type == StockMovementType.RETURN:
            batch.quantity_remaining += self.quantity
        else:
            return

        batch.save(update_fields=['quantity_remaining'])

    def approve(self, approved_by_user):
        """
        Freigabe erteilen (Vier-Augen-Prinzip)
        """
        if self.created_by == approved_by_user:
            raise ValueError(_('Freigabe kann nicht durch denselben Benutzer erfolgen (Vier-Augen-Prinzip)'))

        self.approval_status = BTMApprovalStatus.APPROVED
        self.approved_by = approved_by_user
        self.approved_at = timezone.now()
        self.save()

        # Jetzt Bestand aktualisieren
        self.update_item_stock()

    def reject(self, rejected_by_user, reason):
        """
        Freigabe ablehnen
        """
        self.approval_status = BTMApprovalStatus.REJECTED
        self.approved_by = rejected_by_user
        self.approved_at = timezone.now()
        self.rejection_reason = reason
        self.save()


# ============================================================================
# MEDICAL BATCH (Chargen-Tracking)
# ============================================================================

class MedicalBatch(models.Model):
    """
    Chargen-/Batch-Tracking für Medikamente (Verbrauchsmaterial)
    Wichtig für Rückverfolgbarkeit und Rückrufe
    Jede Charge referenziert die Stammdaten (MedicalItemMaster)
    """

    master = models.ForeignKey(
        MedicalItemMaster,
        on_delete=models.CASCADE,
        related_name='batches',
        null=True, blank=True,  # Temporär nullable für Migration
        verbose_name=_('Stammdaten')
    )

    # Legacy-Support (wird in Migration auf master gesetzt)
    item = models.ForeignKey(
        MedicalItem,
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
        related_name='medical_batches',
        verbose_name=_('Lagerort')
    )

    supplier_batch_number = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Lieferanten-Chargen-Nr.')
    )

    internal_order_number = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Interne Bestellnummer'),
        help_text=_('Interne Bestellnummer aus dem eigenen System')
    )

    external_order_number = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Externe Bestellnummer'),
        help_text=_('Bestellnummer des Lieferanten/Herstellers')
    )

    # Temperatur-Logging (wichtig für Kühlkette)
    temperature_log = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Temperatur-Log'),
        help_text=_('JSON-Array mit Temperatur-Messungen')
    )

    cold_chain_break = models.BooleanField(
        default=False,
        verbose_name=_('Kühlketten-Unterbrechung'),
        help_text=_('Wurde die Kühlkette unterbrochen?')
    )

    # Qualitätskontrolle
    quality_check_passed = models.BooleanField(
        default=True,
        verbose_name=_('Qualitätskontrolle bestanden')
    )

    quality_check_date = models.DateField(
        null=True, blank=True,
        verbose_name=_('Qualitätskontrolle am')
    )

    quality_check_notes = models.TextField(
        blank=True,
        verbose_name=_('QK-Notizen')
    )

    # Rückruf
    is_recalled = models.BooleanField(
        default=False,
        verbose_name=_('Rückruf'),
        help_text=_('Wurde diese Charge zurückgerufen?')
    )

    recall_date = models.DateField(
        null=True, blank=True,
        verbose_name=_('Rückruf-Datum')
    )

    recall_reason = models.TextField(
        blank=True,
        verbose_name=_('Rückruf-Grund')
    )

    # Einkaufspreis
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True, blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name=_('Einkaufspreis pro Einheit (EUR)')
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
            models.Index(fields=['is_recalled']),
            models.Index(fields=['expiry_date']),
        ]

    def __str__(self):
        recall_marker = ' [RÜCKRUF]' if self.is_recalled else ''
        item_ref = self.master if self.master else self.item
        return f"{item_ref.name} - Charge {self.batch_number}{recall_marker}"

    def is_expired(self):
        """Prüft ob Charge abgelaufen ist"""
        return self.expiry_date < timezone.now().date()

    def is_expiring_soon(self, days=None):
        """Prüft ob Charge bald abläuft"""
        if days is None:
            item_ref = self.master if self.master else self.item
            days = item_ref.expiry_warning_days if item_ref else 90

        from datetime import timedelta
        threshold = timezone.now().date() + timedelta(days=days)
        return self.expiry_date <= threshold

    def is_depleted(self):
        """Prüft ob Charge aufgebraucht ist"""
        return self.quantity_remaining <= 0

    def get_percentage_remaining(self):
        """Berechnet den verbleibenden Prozentsatz"""
        if self.quantity_received > 0:
            return (self.quantity_remaining / self.quantity_received) * 100
        return 0

    def days_until_expiry(self):
        """Berechnet Tage bis zum Ablauf"""
        from datetime import date
        delta = self.expiry_date - date.today()
        return delta.days

    def days_in_stock(self):
        """Berechnet Tage im Lager"""
        from datetime import date
        delta = date.today() - self.received_date
        return delta.days

    @property
    def quantity(self):
        """Alias für quantity_remaining (für Template-Kompatibilität)"""
        return self.quantity_remaining

    def generate_qr_code(self):
        """
        Generiert QR-Code als SVG für die Charge
        Enthält nur die URL für direkten Zugriff
        """
        import qrcode
        import qrcode.image.svg
        from io import BytesIO

        # Nur URL kodieren für maximale Scanner-Kompatibilität
        qr_string = f'/medical/batches/{self.pk}/'

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

        stream = BytesIO()
        img.save(stream)
        svg_string = stream.getvalue().decode('utf-8')

        return svg_string

    def generate_barcode(self):
        """
        Generiert Barcode als SVG für die Chargennummer
        """
        import barcode
        from barcode.writer import SVGWriter
        from io import BytesIO

        code128 = barcode.get_barcode_class('code128')

        rv = BytesIO()
        code = code128(self.batch_number, writer=SVGWriter())
        code.write(rv)

        svg_string = rv.getvalue().decode('utf-8')
        return svg_string


# ============================================================================
# TEMPERATURE LOG (für kühlpflichtige Medikamente)
# ============================================================================

class TemperatureLog(models.Model):
    """
    Temperatur-Logging für kühlpflichtige Medikamente
    Wichtig für Nachweis der Kühlkette
    """

    batch = models.ForeignKey(
        MedicalBatch,
        on_delete=models.CASCADE,
        related_name='temperature_logs',
        verbose_name=_('Charge')
    )

    measured_at = models.DateTimeField(
        default=timezone.now,
        verbose_name=_('Messzeitpunkt')
    )

    temperature = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name=_('Temperatur (°C)')
    )

    location = models.ForeignKey(
        'locations.Location',
        on_delete=models.PROTECT,
        related_name='temperature_logs',
        verbose_name=_('Lagerort')
    )

    measured_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='temperature_measurements',
        verbose_name=_('Gemessen durch')
    )

    device_id = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Messgerät-ID'),
        help_text=_('ID des Temperatur-Sensors')
    )

    is_within_range = models.BooleanField(
        default=True,
        verbose_name=_('Im Sollbereich'),
        help_text=_('Temperatur im erlaubten Bereich?')
    )

    notes = models.TextField(
        blank=True,
        verbose_name=_('Notizen'),
        help_text=_('z.B. Maßnahmen bei Überschreitung')
    )

    class Meta:
        verbose_name = _('Temperatur-Messung')
        verbose_name_plural = _('Temperatur-Messungen')
        ordering = ['-measured_at']
        indexes = [
            models.Index(fields=['batch', '-measured_at']),
            models.Index(fields=['is_within_range']),
            models.Index(fields=['-measured_at']),
        ]

    def __str__(self):
        marker = '✓' if self.is_within_range else '⚠️'
        item_ref = self.batch.master if self.batch.master else self.batch.item
        item_name = item_ref.name if item_ref else 'Unbekannt'
        return f"{marker} {self.temperature}°C - {item_name} ({self.measured_at.strftime('%d.%m.%Y %H:%M')})"

    def save(self, *args, **kwargs):
        """
        Automatische Prüfung ob Temperatur im Sollbereich
        """
        if self.batch:
            item = self.batch.master if self.batch.master else self.batch.item

            if item:
                # Prüfe gegen Lagerungsbedingungen
                if item.storage_condition == StorageCondition.REFRIGERATED:
                    # Gekühlt (2-8°C)
                    self.is_within_range = 2 <= self.temperature <= 8
                elif item.storage_condition == StorageCondition.FROZEN:
                    # Gefroren (<-15°C)
                    self.is_within_range = self.temperature <= -15
                elif item.storage_condition == StorageCondition.ROOM_TEMP:
                    # Raumtemperatur (15-25°C)
                    self.is_within_range = 15 <= self.temperature <= 25

                # Kühlketten-Unterbrechung markieren
                if not self.is_within_range and item.requires_cold_chain:
                    self.batch.cold_chain_break = True
                    self.batch.save(update_fields=['cold_chain_break'])

        super().save(*args, **kwargs)

# ============================================================================
# INVENTUR MODELS
# ============================================================================

from inventory_base.models import (
    AbstractInventoryCheck,
    AbstractInventoryCheckItem
)


class MedicalInventoryCheck(AbstractInventoryCheck):
    """
    Inventur für Rettungsdienst-Lager

    Erbt alle Basis-Felder und -Methoden von AbstractInventoryCheck
    Fügt Medical-spezifische Felder hinzu (BTM, Ablaufdaten, etc.)
    """

    # BTM-spezifische Felder
    include_btm = models.BooleanField(
        default=False,
        verbose_name=_('BTM einbeziehen'),
        help_text=_('Betäubungsmittel in Inventur einbeziehen')
    )

    btm_verified_by = models.ForeignKey(
        'personnel.Person',
        on_delete=models.PROTECT,
        related_name='medical_btm_inventories_verified',
        null=True,
        blank=True,
        verbose_name=_('BTM verifiziert von'),
        help_text=_('Zweite Person für Vier-Augen-Prinzip bei BTM')
    )

    btm_verification_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('BTM Verifizierungsdatum')
    )

    # Medikamenten-spezifisch
    check_expiry_dates = models.BooleanField(
        default=True,
        verbose_name=_('Ablaufdaten prüfen')
    )

    expired_items_found = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Abgelaufene Medikamente gefunden')
    )

    class Meta:
        db_table = 'medical_inventory_check'
        verbose_name = _('Medical Inventur')
        verbose_name_plural = _('Medical Inventuren')
        ordering = ['-scheduled_start_date']
        permissions = [
            ('view_btm_inventory', 'Kann BTM-Inventuren sehen'),
            ('verify_btm_inventory', 'Kann BTM-Inventuren verifizieren'),
        ]

    def get_number_prefix(self):
        """Medical-spezifisches Präfix"""
        return 'MED-INV'

    def update_progress(self):
        """Medical-spezifische Fortschritts-Berechnung"""
        self.total_items = self.items.count()
        self.counted_items = self.items.filter(is_counted=True).count()
        self.items_with_discrepancies = self.items.filter(has_discrepancy=True).count()

        # Zähle abgelaufene Medikamente
        if self.check_expiry_dates:
            today = timezone.now().date()
            self.expired_items_found = self.items.filter(
                expiry_date__isnull=False,
                expiry_date__lt=today
            ).count()

        self.save(update_fields=[
            'total_items',
            'counted_items',
            'items_with_discrepancies',
            'expired_items_found'
        ])

    def requires_btm_verification(self):
        """Prüft ob BTM-Verifizierung erforderlich ist"""
        return self.include_btm and self.items.filter(is_btm=True).exists()

    def is_btm_verified(self):
        """Prüft ob BTM-Verifizierung durchgeführt wurde"""
        if not self.requires_btm_verification():
            return True
        return self.btm_verified_by is not None and self.btm_verification_date is not None


class MedicalInventoryCheckItem(AbstractInventoryCheckItem):
    """
    Medical Inventur-Position

    Einzelner Artikel in einer Medical-Inventur
    """

    inventory_check = models.ForeignKey(
        MedicalInventoryCheck,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_('Inventur')
    )

    # Referenz zum Medical-Item (kann MedicalItemMaster ODER MedicalDeviceInstance sein)
    medical_item = models.ForeignKey(
        'medical.MedicalItemMaster',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name=_('Medizinischer Artikel')
    )

    medical_device = models.ForeignKey(
        'medical.MedicalDeviceInstance',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name=_('Medizintechnik-Gerät')
    )

    # Medical-spezifische Felder
    batch_number = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Chargennummer')
    )

    expiry_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Ablaufdatum')
    )

    is_btm = models.BooleanField(
        default=False,
        verbose_name=_('Ist BTM')
    )

    btm_verified = models.BooleanField(
        default=False,
        verbose_name=_('BTM verifiziert')
    )

    # Zusätzliche Prüfungen
    physical_condition = models.CharField(
        max_length=20,
        choices=[
            ('good', _('Gut')),
            ('acceptable', _('Akzeptabel')),
            ('damaged', _('Beschädigt')),
            ('unusable', _('Unbrauchbar')),
        ],
        default='good',
        blank=True,
        verbose_name=_('Physischer Zustand')
    )

    class Meta:
        db_table = 'medical_inventory_check_item'
        verbose_name = _('Medical Inventur-Position')
        verbose_name_plural = _('Medical Inventur-Positionen')
        ordering = ['location', 'item_name']

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        # Update progress in parent
        if self.inventory_check_id:
            self.inventory_check.update_progress()

    def is_expired(self):
        """Prüft ob Artikel abgelaufen ist"""
        if not self.expiry_date:
            return False
        return self.expiry_date < timezone.now().date()

    def get_item_type(self):
        """Gibt Artikeltyp zurück"""
        if self.medical_item:
            return 'item'
        elif self.medical_device:
            return 'device'
        return 'unknown'
