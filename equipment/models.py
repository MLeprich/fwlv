"""
Equipment Models
Ausrüstung & Geräte-Verwaltung (Feuerwehr-Ausrüstung, Spezialgeräte, Werkzeuge)
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
    AbstractInventoryCheck,
    AbstractInventoryCheckItem,
)


# ============================================================================
# ENUMS & CHOICES
# ============================================================================

class EquipmentType(models.TextChoices):
    """Arten von Ausrüstung/Geräten"""
    # Persönliche Schutzausrüstung
    HELMET = 'helmet', _('Helm')
    MASK = 'mask', _('Atemschutzmaske')
    GLOVES = 'gloves', _('Handschuhe')
    BOOTS = 'boots', _('Stiefel')

    # Atemschutz
    BREATHING_APPARATUS = 'breathing_apparatus', _('Atemschutzgerät')
    OXYGEN_TANK = 'oxygen_tank', _('Sauerstoffflasche')
    FILTER = 'filter', _('Filter')

    # Schläuche & Armaturen
    HOSE = 'hose', _('Schlauch')
    COUPLING = 'coupling', _('Kupplung')
    NOZZLE = 'nozzle', _('Strahlrohr')
    VALVE = 'valve', _('Ventil')

    # Leiter & Höhengeräte
    LADDER = 'ladder', _('Leiter')
    ROPE = 'rope', _('Seil')
    CARABINER = 'carabiner', _('Karabiner')
    HARNESS = 'harness', _('Gurt')

    # Pumpen & Aggregate
    PUMP = 'pump', _('Pumpe')
    GENERATOR = 'generator', _('Stromerzeuger')
    COMPRESSOR = 'compressor', _('Kompressor')

    # Werkzeuge
    TOOL_HYDRAULIC = 'tool_hydraulic', _('Hydraulisches Werkzeug')
    TOOL_HAND = 'tool_hand', _('Handwerkzeug')
    TOOL_POWER = 'tool_power', _('Elektrowerkzeug')
    CHAINSAW = 'chainsaw', _('Motorsäge')

    # Messgeräte
    DETECTOR_GAS = 'detector_gas', _('Gaswarngerät')
    DETECTOR_CO = 'detector_co', _('CO-Warngerät')
    DETECTOR_RADIATION = 'detector_radiation', _('Strahlenmessgerät')
    THERMAL_CAMERA = 'thermal_camera', _('Wärmebildkamera')

    # Beleuchtung
    SPOTLIGHT = 'spotlight', _('Scheinwerfer')
    FLASHLIGHT = 'flashlight', _('Taschenlampe')
    HEADLAMP = 'headlamp', _('Stirnlampe')

    # Sonstiges
    RADIO = 'radio', _('Funkgerät')
    CONTAINER = 'container', _('Behälter/Container')
    OTHER = 'other', _('Sonstiges')


class EquipmentStatus(models.TextChoices):
    """Betriebszustand der Ausrüstung"""
    OPERATIONAL = 'operational', _('Einsatzbereit')
    MAINTENANCE = 'maintenance', _('In Wartung')
    DEFECTIVE = 'defective', _('Defekt')
    TESTING = 'testing', _('In Prüfung')
    DECOMMISSIONED = 'decommissioned', _('Ausgemustert')


class PowerSource(models.TextChoices):
    """Stromversorgung/Antrieb"""
    NONE = 'none', _('Keine')
    MANUAL = 'manual', _('Manuell')
    ELECTRIC_BATTERY = 'electric_battery', _('Elektrisch (Akku)')
    ELECTRIC_MAINS = 'electric_mains', _('Elektrisch (Netz)')
    GASOLINE = 'gasoline', _('Benzin')
    DIESEL = 'diesel', _('Diesel')
    HYDRAULIC = 'hydraulic', _('Hydraulisch')
    PNEUMATIC = 'pneumatic', _('Pneumatisch')
    GAS = 'gas', _('Gas')


class CertificationStatus(models.TextChoices):
    """Zertifizierungs-/Prüfstatus"""
    VALID = 'valid', _('Gültig')
    EXPIRING_SOON = 'expiring_soon', _('Läuft bald ab')
    EXPIRED = 'expired', _('Abgelaufen')
    NOT_REQUIRED = 'not_required', _('Nicht erforderlich')


# ============================================================================
# EQUIPMENT ITEM MASTER (STAMMDATEN)
# ============================================================================

class EquipmentItemMaster(models.Model):
    """
    Ausrüstungs-/Gerätestammdaten - Produktdefinition ohne Lagerort
    Analog zu MedicalItemMaster im Medical-Modul

    Beispiele:
    - Pumpe TP15-1000 (Hersteller Rosenbauer)
    - Generator Honda EU22i
    - Schlauch B-75 (20m)
    """

    # Basis-Identifikation
    master_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_('Stammdaten-Nummer'),
        help_text=_('Eindeutige Stammdatennummer (z.B. EQ-2025-001)')
    )

    name = models.CharField(
        max_length=200,
        verbose_name=_('Bezeichnung')
    )

    description = models.TextField(
        blank=True,
        verbose_name=_('Beschreibung')
    )

    # Typ & Kategorie
    equipment_type = models.CharField(
        max_length=30,
        choices=EquipmentType.choices,
        verbose_name=_('Gerätetyp')
    )

    category = models.ForeignKey(
        'inventory_base.Category',
        on_delete=models.PROTECT,
        related_name='equipment_masters',
        null=True, blank=True,
        verbose_name=_('Kategorie')
    )

    # Hersteller & Modell
    manufacturer = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Hersteller')
    )

    model = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Modell/Typ')
    )

    model_year = models.PositiveIntegerField(
        null=True, blank=True,
        verbose_name=_('Baujahr')
    )

    # Lieferant
    supplier = models.ForeignKey(
        'inventory_base.Supplier',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='equipment_masters',
        verbose_name=_('Lieferant')
    )

    supplier_item_number = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Lieferanten-Artikelnummer')
    )

    # Technische Daten
    power_source = models.CharField(
        max_length=20,
        choices=PowerSource.choices,
        default=PowerSource.NONE,
        verbose_name=_('Stromversorgung/Antrieb')
    )

    weight_kg = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True, blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name=_('Gewicht (kg)')
    )

    dimensions = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Abmessungen'),
        help_text=_('z.B. "100x50x30 cm"')
    )

    technical_specs = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Technische Spezifikationen'),
        help_text=_('Zusätzliche technische Daten als JSON')
    )

    # Zertifizierung & Prüfung (Standard-Vorgaben)
    requires_certification = models.BooleanField(
        default=False,
        verbose_name=_('Zertifizierungspflichtig'),
        help_text=_('Erfordert regelmäßige Zertifizierung')
    )

    requires_maintenance = models.BooleanField(
        default=True,
        verbose_name=_('Wartungspflichtig')
    )

    maintenance_interval_months = models.PositiveIntegerField(
        null=True, blank=True,
        verbose_name=_('Wartungsintervall (Monate)')
    )

    requires_inspection = models.BooleanField(
        default=False,
        verbose_name=_('Prüfpflicht'),
        help_text=_('z.B. UVV-Prüfung, TÜV')
    )

    inspection_interval_months = models.PositiveIntegerField(
        null=True, blank=True,
        verbose_name=_('Prüfintervall (Monate)')
    )

    # Lebensdauer & Austausch (Standard-Vorgaben)
    max_operating_hours = models.PositiveIntegerField(
        null=True, blank=True,
        verbose_name=_('Max. Betriebsstunden'),
        help_text=_('Maximale Betriebsstunden laut Hersteller')
    )

    max_usage_years = models.PositiveIntegerField(
        null=True, blank=True,
        verbose_name=_('Max. Nutzungsdauer (Jahre)')
    )

    # Dokumentation
    manual_document = models.FileField(
        upload_to='equipment/manuals/%Y/%m/',
        null=True, blank=True,
        verbose_name=_('Handbuch/Dokument'),
        help_text=_('PDF oder Bild (wird per OCR durchsuchbar gemacht)')
    )

    manual_ocr_text = models.TextField(
        blank=True,
        verbose_name=_('OCR-Text aus Handbuch'),
        help_text=_('Automatisch extrahierter Text für Suchfunktion')
    )

    image = models.ImageField(
        upload_to='equipment/images/%Y/%m/',
        null=True, blank=True,
        verbose_name=_('Bild')
    )

    # Kosten (Anschaffungspreis als Referenz)
    purchase_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True, blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name=_('Anschaffungspreis (EUR)'),
        help_text=_('Durchschnittlicher Anschaffungspreis')
    )

    # Einheit (für Verbrauchsmaterial)
    unit = models.CharField(
        max_length=20,
        default='Stück',
        verbose_name=_('Einheit'),
        help_text=_('Stück, Meter, Liter, etc.')
    )

    # Meta
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Aktiv')
    )

    notes = models.TextField(
        blank=True,
        verbose_name=_('Notizen')
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Erstellt am'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Aktualisiert am'))
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='created_equipment_masters',
        verbose_name=_('Erstellt von')
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='updated_equipment_masters',
        verbose_name=_('Aktualisiert von')
    )

    class Meta:
        verbose_name = _('Ausrüstungs-Stammdaten')
        verbose_name_plural = _('Ausrüstungs-Stammdaten')
        ordering = ['master_number']
        indexes = [
            models.Index(fields=['master_number']),
            models.Index(fields=['equipment_type', 'category']),
            models.Index(fields=['manufacturer', 'model']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.master_number} - {self.name}"

    def get_total_stock(self):
        """Gesamtbestand über alle Instanzen/Chargen"""
        # Für Geräte: Anzahl der Instanzen
        device_count = self.device_instances.filter(is_active=True).count()
        # Für Verbrauchsmaterial: Summe der Bestände (falls später implementiert)
        return device_count

    def get_operational_count(self):
        """Anzahl einsatzbereiter Geräte"""
        return self.device_instances.filter(
            is_active=True,
            is_operational=True
        ).count()


# ============================================================================
# EQUIPMENT DEVICE INSTANCE (GERÄTE MIT INVENTARNUMMER)
# ============================================================================

class EquipmentDeviceInstance(models.Model):
    """
    Einzelgerät mit Inventarnummer
    Analog zu MedicalDeviceInstance im Medical-Modul

    Beispiele:
    - Pumpe TP15-1000 mit Inv.-Nr. P-2025-042
    - Generator Honda EU22i mit Inv.-Nr. G-2025-015
    """

    # Referenz zu Stammdaten
    master = models.ForeignKey(
        EquipmentItemMaster,
        on_delete=models.PROTECT,
        related_name='device_instances',
        verbose_name=_('Stammdaten')
    )

    # Inventarnummer (eindeutig)
    inventory_number = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_('Inventarnummer'),
        help_text=_('Eindeutige Inventarnummer (z.B. P-2025-042)')
    )

    # Seriennummer (Hersteller)
    serial_number = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Seriennummer'),
        help_text=_('Eindeutige Herstellernummer')
    )

    # Zusätzliche Inventarnummern für Module/Komponenten
    additional_inventory_numbers = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_('Zusätzliche Inventarnummern'),
        help_text=_('Inventarnummern für Module/Komponenten dieses Geräts')
    )

    # Lagerort
    location = models.ForeignKey(
        'locations.Location',
        on_delete=models.PROTECT,
        related_name='equipment_devices',
        null=True, blank=True,
        verbose_name=_('Lagerort')
    )

    # Fahrzeug-Zuordnung
    assigned_vehicle = models.ForeignKey(
        'vehicles.Vehicle',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='assigned_equipment_devices',
        verbose_name=_('Zugeordnet zu Fahrzeug')
    )

    # Betriebszustand
    is_operational = models.BooleanField(
        default=True,
        verbose_name=_('Einsatzbereit')
    )

    equipment_status = models.CharField(
        max_length=20,
        choices=EquipmentStatus.choices,
        default=EquipmentStatus.OPERATIONAL,
        verbose_name=_('Betriebszustand')
    )

    # Zertifizierung (individuelle Werte)
    certification_number = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Zertifizierungsnummer')
    )

    certification_expires = models.DateField(
        null=True, blank=True,
        verbose_name=_('Zertifizierung läuft ab')
    )

    certification_status = models.CharField(
        max_length=20,
        choices=CertificationStatus.choices,
        default=CertificationStatus.NOT_REQUIRED,
        verbose_name=_('Zertifizierungsstatus')
    )

    # Wartung (individuelle Termine)
    last_maintenance_date = models.DateField(
        null=True, blank=True,
        verbose_name=_('Letzte Wartung')
    )

    next_maintenance_date = models.DateField(
        null=True, blank=True,
        verbose_name=_('Nächste Wartung')
    )

    maintenance_notes = models.TextField(
        blank=True,
        verbose_name=_('Wartungsnotizen')
    )

    # Prüfung (individuelle Termine)
    last_inspection_date = models.DateField(
        null=True, blank=True,
        verbose_name=_('Letzte Prüfung')
    )

    next_inspection_date = models.DateField(
        null=True, blank=True,
        verbose_name=_('Nächste Prüfung')
    )

    inspection_notes = models.TextField(
        blank=True,
        verbose_name=_('Prüfnotizen')
    )

    # Betriebsstunden
    current_operating_hours = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Aktuelle Betriebsstunden')
    )

    # Austauschtermin
    replacement_due_date = models.DateField(
        null=True, blank=True,
        verbose_name=_('Austausch fällig am')
    )

    # Anschaffung
    purchase_date = models.DateField(
        null=True, blank=True,
        verbose_name=_('Anschaffungsdatum')
    )

    purchase_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True, blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name=_('Anschaffungspreis (EUR)')
    )

    # QR-Code / Barcode
    has_qr_code = models.BooleanField(
        default=False,
        verbose_name=_('QR-Code vorhanden')
    )

    qr_code_data = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('QR-Code Daten')
    )

    # Meta
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Aktiv')
    )

    notes = models.TextField(
        blank=True,
        verbose_name=_('Notizen')
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Erstellt am'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Aktualisiert am'))
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='created_equipment_devices',
        verbose_name=_('Erstellt von')
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='updated_equipment_devices',
        verbose_name=_('Aktualisiert von')
    )

    class Meta:
        verbose_name = _('Ausrüstungs-Gerät (Instanz)')
        verbose_name_plural = _('Ausrüstungs-Geräte (Instanzen)')
        ordering = ['inventory_number']
        indexes = [
            models.Index(fields=['inventory_number']),
            models.Index(fields=['master', 'is_active']),
            models.Index(fields=['next_maintenance_date']),
            models.Index(fields=['next_inspection_date']),
            models.Index(fields=['is_operational']),
            models.Index(fields=['assigned_vehicle']),
        ]

    def __str__(self):
        vehicle = f" [{self.assigned_vehicle}]" if self.assigned_vehicle else ""
        return f"{self.inventory_number} - {self.master.name}{vehicle}"

    def is_maintenance_due(self):
        """Prüft ob Wartung fällig ist"""
        if self.next_maintenance_date:
            from django.utils import timezone
            return self.next_maintenance_date <= timezone.now().date()
        return False

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

    def is_replacement_due(self):
        """Prüft ob Austausch fällig ist"""
        if self.replacement_due_date:
            from django.utils import timezone
            return self.replacement_due_date <= timezone.now().date()
        return False

    def is_operating_hours_exceeded(self):
        """Prüft ob maximale Betriebsstunden erreicht"""
        if self.master.max_operating_hours:
            return self.current_operating_hours >= self.master.max_operating_hours
        return False


# ============================================================================
# EQUIPMENT ITEM (LEGACY - wird deprecated)
# ============================================================================

class EquipmentItem(AbstractInventoryItem):
    """
    Ausrüstungs-/Gerätestück
    Erbt alle Basis-Felder von AbstractInventoryItem
    """

    # Geräte-spezifische Felder
    equipment_type = models.CharField(
        max_length=30,
        choices=EquipmentType.choices,
        verbose_name=_('Gerätetyp')
    )

    equipment_status = models.CharField(
        max_length=20,
        choices=EquipmentStatus.choices,
        default=EquipmentStatus.OPERATIONAL,
        verbose_name=_('Betriebszustand')
    )

    # Technische Daten
    model_year = models.PositiveIntegerField(
        null=True, blank=True,
        verbose_name=_('Baujahr')
    )

    serial_number = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Seriennummer'),
        help_text=_('Eindeutige Herstellernummer')
    )

    power_source = models.CharField(
        max_length=20,
        choices=PowerSource.choices,
        default=PowerSource.NONE,
        verbose_name=_('Stromversorgung/Antrieb')
    )

    weight_kg = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True, blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name=_('Gewicht (kg)')
    )

    dimensions = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Abmessungen'),
        help_text=_('z.B. "100x50x30 cm"')
    )

    # Zertifizierung & Prüfung
    requires_certification = models.BooleanField(
        default=False,
        verbose_name=_('Zertifizierungspflichtig'),
        help_text=_('Erfordert regelmäßige Zertifizierung')
    )

    certification_number = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Zertifizierungsnummer')
    )

    certification_expires = models.DateField(
        null=True, blank=True,
        verbose_name=_('Zertifizierung läuft ab')
    )

    certification_status = models.CharField(
        max_length=20,
        choices=CertificationStatus.choices,
        default=CertificationStatus.NOT_REQUIRED,
        verbose_name=_('Zertifizierungsstatus')
    )

    # Wartung & Prüfung
    requires_maintenance = models.BooleanField(
        default=True,
        verbose_name=_('Wartungspflichtig')
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

    maintenance_notes = models.TextField(
        blank=True,
        verbose_name=_('Wartungsnotizen')
    )

    # Prüfung (z.B. TÜV, UVV)
    requires_inspection = models.BooleanField(
        default=False,
        verbose_name=_('Prüfpflicht'),
        help_text=_('z.B. UVV-Prüfung, TÜV')
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

    inspection_notes = models.TextField(
        blank=True,
        verbose_name=_('Prüfnotizen')
    )

    # Lebensdauer & Austausch
    max_operating_hours = models.PositiveIntegerField(
        null=True, blank=True,
        verbose_name=_('Max. Betriebsstunden'),
        help_text=_('Maximale Betriebsstunden laut Hersteller')
    )

    current_operating_hours = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Aktuelle Betriebsstunden')
    )

    max_usage_years = models.PositiveIntegerField(
        null=True, blank=True,
        verbose_name=_('Max. Nutzungsdauer (Jahre)')
    )

    replacement_due_date = models.DateField(
        null=True, blank=True,
        verbose_name=_('Austausch fällig am')
    )

    # Fahrzeug-/Standort-Zuordnung
    assigned_vehicle = models.ForeignKey(
        'vehicles.Vehicle',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='assigned_equipment',
        verbose_name=_('Zugeordnet zu Fahrzeug')
    )

    # QR-Code / Barcode
    has_qr_code = models.BooleanField(
        default=False,
        verbose_name=_('QR-Code vorhanden')
    )

    qr_code_data = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('QR-Code Daten')
    )

    # Technische Spezifikationen (JSON)
    technical_specs = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Technische Spezifikationen'),
        help_text=_('Zusätzliche technische Daten als JSON')
    )

    # Dokumenten-Upload (Handbücher, Anleitungen, etc.)
    manual_document = models.FileField(
        upload_to='equipment/manuals/%Y/%m/',
        null=True, blank=True,
        verbose_name=_('Handbuch/Dokument'),
        help_text=_('PDF oder Bild (wird per OCR durchsuchbar gemacht)')
    )

    manual_ocr_text = models.TextField(
        blank=True,
        verbose_name=_('OCR-Text aus Handbuch'),
        help_text=_('Automatisch extrahierter Text für Suchfunktion')
    )

    class Meta:
        verbose_name = _('Ausrüstung/Gerät')
        verbose_name_plural = _('Ausrüstung/Geräte')
        ordering = ['equipment_type', 'name']
        indexes = [
            models.Index(fields=['equipment_type']),
            models.Index(fields=['equipment_status']),
            models.Index(fields=['serial_number']),
            models.Index(fields=['next_maintenance_date']),
            models.Index(fields=['next_inspection_date']),
            models.Index(fields=['assigned_vehicle']),
        ]

    def __str__(self):
        vehicle = f" [{self.assigned_vehicle}]" if self.assigned_vehicle else ""
        return f"{self.get_equipment_type_display()} - {self.item_number}{vehicle}"

    def is_maintenance_due(self):
        """Prüft ob Wartung fällig ist"""
        if self.next_maintenance_date:
            from django.utils import timezone
            return self.next_maintenance_date <= timezone.now().date()
        return False

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

    def is_replacement_due(self):
        """Prüft ob Austausch fällig ist"""
        if self.replacement_due_date:
            from django.utils import timezone
            return self.replacement_due_date <= timezone.now().date()
        return False

    def is_operating_hours_exceeded(self):
        """Prüft ob maximale Betriebsstunden erreicht"""
        if self.max_operating_hours:
            return self.current_operating_hours >= self.max_operating_hours
        return False


# ============================================================================
# EQUIPMENT STOCK MOVEMENT
# ============================================================================

class EquipmentStockMovement(AbstractStockMovement):
    """
    Lagerbewegungen für Ausrüstung/Geräte
    """

    item = models.ForeignKey(
        EquipmentItem,
        on_delete=models.PROTECT,
        related_name='stock_movements',
        verbose_name=_('Ausrüstung/Gerät')
    )

    # Fahrzeug-Zuordnung (bei Aus-/Einlagerung)
    vehicle = models.ForeignKey(
        'vehicles.Vehicle',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='equipment_movements',
        verbose_name=_('Fahrzeug'),
        help_text=_('Fahrzeug bei Aus-/Einlagerung')
    )

    # Person (wer entnimmt/zurückgibt)
    person = models.ForeignKey(
        'personnel.Person',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='equipment_movements',
        verbose_name=_('Person')
    )

    # Zustandsnotizen
    condition_before = models.TextField(
        blank=True,
        verbose_name=_('Zustand vorher'),
        help_text=_('Zustand bei Entnahme')
    )

    condition_after = models.TextField(
        blank=True,
        verbose_name=_('Zustand nachher'),
        help_text=_('Zustand bei Rückgabe')
    )

    # Defekt/Schaden
    is_defective = models.BooleanField(
        default=False,
        verbose_name=_('Defekt gemeldet')
    )

    defect_description = models.TextField(
        blank=True,
        verbose_name=_('Defektbeschreibung')
    )

    # Betriebsstunden (bei Bewegung)
    operating_hours_delta = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Betriebsstunden (Delta)'),
        help_text=_('Zusätzliche Betriebsstunden seit letzter Bewegung')
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
            models.Index(fields=['vehicle', '-movement_date']),
            models.Index(fields=['person', '-movement_date']),
            models.Index(fields=['movement_type', '-movement_date']),
        ]

    def __str__(self):
        vehicle_info = f" - {self.vehicle}" if self.vehicle else ""
        return f"{self.get_movement_type_display()} - {self.item.equipment_type}{vehicle_info}"

    def save(self, *args, **kwargs):
        """
        Automatische Berechnungen und Fahrzeugzuordnung
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

        # Bei Ausgabe an Fahrzeug: Item dem Fahrzeug zuordnen
        from inventory_base.models import StockMovementType
        if self.movement_type == StockMovementType.OUTGOING and self.vehicle:
            self.item.assigned_vehicle = self.vehicle
            self.item.save(update_fields=['assigned_vehicle'])

        # Bei Rückgabe: Fahrzeug-Zuweisung entfernen
        elif self.movement_type == StockMovementType.RETURN:
            self.item.assigned_vehicle = None
            self.item.save(update_fields=['assigned_vehicle'])

        # Betriebsstunden aktualisieren
        if self.operating_hours_delta > 0:
            self.item.current_operating_hours += self.operating_hours_delta
            self.item.save(update_fields=['current_operating_hours'])

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
# PRÜFUNGEN (INSPECTION TYPES & RECORDS)
# ============================================================================

class InspectionType(models.Model):
    """
    Prüfungsart (z.B. Sichtprüfung, Belastungsprüfung, Wiederholungsprüfung)
    Kann individuell erstellt und Geräten zugewiesen werden
    """

    name = models.CharField(
        max_length=200,
        verbose_name=_('Prüfungsbezeichnung'),
        help_text=_('z.B. Sichtprüfung, Belastungsprüfung')
    )

    description = models.TextField(
        blank=True,
        verbose_name=_('Beschreibung'),
        help_text=_('Was wird bei dieser Prüfung geprüft?')
    )

    # Prüfnorm/Grundlage
    inspection_standard = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Prüfnorm'),
        help_text=_('z.B. DIN 14811, DGUV 3, BetrSichV')
    )

    # Intervall
    interval_months = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Intervall (Monate)'),
        help_text=_('Wie oft muss diese Prüfung durchgeführt werden?')
    )

    # Checkliste als JSON
    checklist = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_('Prüfpunkte'),
        help_text=_('Liste der zu prüfenden Punkte')
    )

    # Zuweisbare Gerätetypen
    applicable_equipment_types = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_('Anwendbar auf Gerätetypen'),
        help_text=_('Für welche Gerätetypen ist diese Prüfung relevant?')
    )

    # Benutzerdefinierte Messfelder als JSON
    # Format: [{"name": "Durchbiegung Mitte", "type": "number", "unit": "mm", "required": true, "min": 0, "max": 100}]
    custom_fields = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_('Benutzerdefinierte Messfelder'),
        help_text=_('Individuelle Felder für Messwerte (z.B. Durchbiegung, Abstand, etc.)')
    )

    # Prüfung erfordert
    requires_certification = models.BooleanField(
        default=False,
        verbose_name=_('Befähigungsnachweis erforderlich'),
        help_text=_('Darf nur von zertifizierten Personen durchgeführt werden')
    )

    requires_external_service = models.BooleanField(
        default=False,
        verbose_name=_('Externe Prüfung'),
        help_text=_('Muss durch externen Dienstleister durchgeführt werden')
    )

    # Meta
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Aktiv')
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Erstellt am'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Aktualisiert am'))
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='created_inspection_types',
        verbose_name=_('Erstellt von')
    )

    class Meta:
        verbose_name = _('Prüfungsart')
        verbose_name_plural = _('Prüfungsarten')
        ordering = ['name']

    def __str__(self):
        return self.name


class EquipmentInspectionAssignment(models.Model):
    """
    Zuweisung einer Prüfungsart zu einem Gerät
    Ein Gerät kann mehrere verschiedene Prüfungsarten haben
    """

    device = models.ForeignKey(
        EquipmentDeviceInstance,
        on_delete=models.CASCADE,
        related_name='inspection_assignments',
        verbose_name=_('Gerät')
    )

    inspection_type = models.ForeignKey(
        InspectionType,
        on_delete=models.CASCADE,
        related_name='equipment_assignments',
        verbose_name=_('Prüfungsart')
    )

    # Individuelle Intervall-Überschreibung
    custom_interval_months = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Individuelles Intervall (Monate)'),
        help_text=_('Überschreibt Standard-Intervall der Prüfungsart')
    )

    # Termine
    last_inspection_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Letzte Prüfung')
    )

    next_inspection_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Nächste Prüfung')
    )

    # Meta
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Aktiv'),
        help_text=_('Prüfung wird noch durchgeführt')
    )

    notes = models.TextField(
        blank=True,
        verbose_name=_('Notizen')
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Erstellt am'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Aktualisiert am'))
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='created_inspection_assignments',
        verbose_name=_('Erstellt von')
    )

    class Meta:
        verbose_name = _('Prüfungszuweisung')
        verbose_name_plural = _('Prüfungszuweisungen')
        ordering = ['device', 'inspection_type']
        unique_together = ['device', 'inspection_type']

    def __str__(self):
        return f"{self.device.inventory_number} - {self.inspection_type.name}"

    def get_interval_months(self):
        """Gibt das effektive Intervall zurück (custom oder standard)"""
        return self.custom_interval_months or self.inspection_type.interval_months


class InspectionRecord(models.Model):
    """
    Prüfungsprotokoll - Dokumentation einer durchgeführten Prüfung
    """

    # Direkte Verknüpfung zu Gerät und Prüfungsart
    device = models.ForeignKey(
        EquipmentDeviceInstance,
        on_delete=models.CASCADE,
        related_name='inspection_records',
        verbose_name=_('Gerät')
    )

    inspection_type = models.ForeignKey(
        InspectionType,
        on_delete=models.PROTECT,
        related_name='inspection_records',
        verbose_name=_('Prüfungsart')
    )

    # Prüfungsdaten
    inspection_date = models.DateField(
        verbose_name=_('Prüfungsdatum')
    )

    inspector = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='conducted_inspections',
        verbose_name=_('Prüfer')
    )

    # Prüfergebnis
    RESULT_CHOICES = [
        ('passed', _('Bestanden')),
        ('passed_with_remarks', _('Bestanden mit Anmerkungen')),
        ('failed', _('Nicht bestanden')),
        ('incomplete', _('Unvollständig')),
    ]

    result = models.CharField(
        max_length=30,
        choices=RESULT_CHOICES,
        verbose_name=_('Prüfergebnis')
    )

    # Prüfpunkte Ergebnisse (JSON)
    checklist_results = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Checklisten-Ergebnisse'),
        help_text=_('Detaillierte Ergebnisse der einzelnen Prüfpunkte')
    )

    # Benutzerdefinierte Feldwerte (JSON)
    # Format: {"Durchbiegung Mitte": "12.5", "Abstand Boden": "11.8"}
    custom_field_values = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Messwerte'),
        help_text=_('Werte der benutzerdefinierten Messfelder')
    )

    # Befunde
    findings = models.TextField(
        blank=True,
        verbose_name=_('Feststellungen/Mängel')
    )

    recommendations = models.TextField(
        blank=True,
        verbose_name=_('Empfehlungen/Maßnahmen')
    )

    # Nächste Prüfung
    next_inspection_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Nächste Prüfung fällig am')
    )

    # Prüfplakette
    inspection_sticker_number = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Prüfplaketten-Nummer')
    )

    # Dokumentation
    inspection_certificate = models.FileField(
        upload_to='equipment/inspection_certificates/',
        null=True,
        blank=True,
        verbose_name=_('Prüfprotokoll (PDF)')
    )

    photos = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_('Fotos'),
        help_text=_('Liste der Foto-URLs')
    )

    # Meta
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Erstellt am'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Aktualisiert am'))

    class Meta:
        verbose_name = _('Prüfungsprotokoll')
        verbose_name_plural = _('Prüfungsprotokolle')
        ordering = ['-inspection_date']

    def __str__(self):
        return f"{self.device.inventory_number} - {self.inspection_type.name} ({self.inspection_date})"

    def save(self, *args, **kwargs):
        """Speichert das Prüfprotokoll"""
        super().save(*args, **kwargs)


# ============================================================================
# WARTUNGEN (MAINTENANCE TYPES & RECORDS)
# ============================================================================

class MaintenanceType(models.Model):
    """
    Wartungsart (z.B. Ölwechsel, Filterwechsel, Funktionsprüfung)
    Kann individuell erstellt und Geräten zugewiesen werden
    """

    name = models.CharField(
        max_length=200,
        verbose_name=_('Wartungsbezeichnung'),
        help_text=_('z.B. Ölwechsel, Filterwechsel, Jahreswartung')
    )

    description = models.TextField(
        blank=True,
        verbose_name=_('Beschreibung'),
        help_text=_('Was wird bei dieser Wartung durchgeführt?')
    )

    # Wartungsstandard/Grundlage
    maintenance_standard = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Wartungsstandard'),
        help_text=_('z.B. Herstellervorgabe, DIN-Norm')
    )

    # Intervall
    interval_months = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Intervall (Monate)'),
        help_text=_('Wie oft muss diese Wartung durchgeführt werden?')
    )

    # Checkliste als JSON
    checklist = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_('Wartungspunkte'),
        help_text=_('Liste der durchzuführenden Wartungsarbeiten')
    )

    # Zuweisbare Gerätetypen
    applicable_equipment_types = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_('Anwendbar auf Gerätetypen'),
        help_text=_('Für welche Gerätetypen ist diese Wartung relevant?')
    )

    # Benutzerdefinierte Messfelder als JSON
    custom_fields = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_('Benutzerdefinierte Messfelder'),
        help_text=_('Individuelle Felder für Messwerte (z.B. Ölstand, Betriebsstunden, etc.)')
    )

    # Wartung erfordert
    requires_certification = models.BooleanField(
        default=False,
        verbose_name=_('Befähigungsnachweis erforderlich'),
        help_text=_('Darf nur von zertifizierten Personen durchgeführt werden')
    )

    requires_external_service = models.BooleanField(
        default=False,
        verbose_name=_('Externe Wartung'),
        help_text=_('Muss durch externen Dienstleister durchgeführt werden')
    )

    # Meta
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Aktiv')
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Erstellt am'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Aktualisiert am'))
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='created_maintenance_types',
        verbose_name=_('Erstellt von')
    )

    class Meta:
        verbose_name = _('Wartungsart')
        verbose_name_plural = _('Wartungsarten')
        ordering = ['name']

    def __str__(self):
        return self.name


class MasterMaintenanceAssignment(models.Model):
    """
    Zuweisung einer Wartungsart zu Artikelstammdaten (EquipmentItemMaster).
    Alle Geräte dieses Stammdatentyps erhalten automatisch diese Wartungszuweisung.
    """

    master = models.ForeignKey(
        EquipmentItemMaster,
        on_delete=models.CASCADE,
        related_name='maintenance_assignments',
        verbose_name=_('Artikelstammdaten')
    )

    maintenance_type = models.ForeignKey(
        MaintenanceType,
        on_delete=models.CASCADE,
        related_name='master_assignments',
        verbose_name=_('Wartungsart')
    )

    # Individuelles Intervall (überschreibt Standard)
    custom_interval_months = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Individuelles Intervall (Monate)'),
        help_text=_('Überschreibt Standard-Intervall der Wartungsart')
    )

    # Status
    is_active = models.BooleanField(
        default=True,
        help_text=_('Wartung wird noch durchgeführt'),
        verbose_name=_('Aktiv')
    )

    notes = models.TextField(
        blank=True,
        verbose_name=_('Notizen')
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Erstellt am'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Aktualisiert am'))
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='created_master_maintenance_assignments',
        verbose_name=_('Erstellt von')
    )

    class Meta:
        verbose_name = _('Stammdaten-Wartungszuweisung')
        verbose_name_plural = _('Stammdaten-Wartungszuweisungen')
        ordering = ['master', 'maintenance_type']
        unique_together = ['master', 'maintenance_type']

    def __str__(self):
        return f"{self.master.name} - {self.maintenance_type.name}"

    def get_interval_months(self):
        """Gibt das effektive Intervall zurück (custom oder standard)"""
        return self.custom_interval_months or self.maintenance_type.interval_months

    def get_device_count(self):
        """Anzahl der Geräte, die zu diesen Stammdaten gehören"""
        return self.master.device_instances.filter(is_active=True).count()


class EquipmentMaintenanceAssignment(models.Model):
    """
    Zuweisung einer Wartungsart zu einem Gerät
    """

    device = models.ForeignKey(
        EquipmentDeviceInstance,
        on_delete=models.CASCADE,
        related_name='maintenance_assignments',
        verbose_name=_('Gerät')
    )

    maintenance_type = models.ForeignKey(
        MaintenanceType,
        on_delete=models.CASCADE,
        related_name='equipment_assignments',
        verbose_name=_('Wartungsart')
    )

    # Individuelles Intervall (überschreibt Standard)
    custom_interval_months = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Individuelles Intervall (Monate)'),
        help_text=_('Überschreibt Standard-Intervall der Wartungsart')
    )

    # Wartungsdaten
    last_maintenance_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Letzte Wartung')
    )

    next_maintenance_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Nächste Wartung')
    )

    # Status
    is_active = models.BooleanField(
        default=True,
        help_text=_('Wartung wird noch durchgeführt'),
        verbose_name=_('Aktiv')
    )

    notes = models.TextField(
        blank=True,
        verbose_name=_('Notizen')
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Erstellt am'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Aktualisiert am'))
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='created_maintenance_assignments',
        verbose_name=_('Erstellt von')
    )

    class Meta:
        verbose_name = _('Wartungszuweisung')
        verbose_name_plural = _('Wartungszuweisungen')
        ordering = ['device', 'maintenance_type']
        unique_together = ['device', 'maintenance_type']

    def __str__(self):
        return f"{self.device.inventory_number} - {self.maintenance_type.name}"


class MaintenanceRecord(models.Model):
    """
    Protokoll einer durchgeführten Wartung
    """

    assignment = models.ForeignKey(
        EquipmentMaintenanceAssignment,
        on_delete=models.CASCADE,
        related_name='maintenance_records',
        verbose_name=_('Wartungszuweisung')
    )

    maintenance_date = models.DateField(
        verbose_name=_('Wartungsdatum')
    )

    technician = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='conducted_maintenances',
        verbose_name=_('Techniker')
    )

    # Wartungsergebnis
    STATUS_CHOICES = [
        ('completed', _('Abgeschlossen')),
        ('completed_with_remarks', _('Abgeschlossen mit Anmerkungen')),
        ('incomplete', _('Unvollständig')),
        ('parts_required', _('Ersatzteile erforderlich')),
    ]

    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        verbose_name=_('Status')
    )

    # Checklisten-Ergebnisse (JSON)
    checklist_results = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Checklisten-Ergebnisse'),
        help_text=_('Detaillierte Ergebnisse der einzelnen Wartungspunkte')
    )

    # Benutzerdefinierte Feldwerte (JSON)
    custom_field_values = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Messwerte'),
        help_text=_('Werte der benutzerdefinierten Messfelder')
    )

    # Befunde
    findings = models.TextField(
        blank=True,
        verbose_name=_('Feststellungen/Befunde')
    )

    work_performed = models.TextField(
        blank=True,
        verbose_name=_('Durchgeführte Arbeiten')
    )

    # Nächste Wartung
    next_maintenance_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Nächste Wartung fällig am')
    )

    # Ersatzteile
    parts_used = models.TextField(
        blank=True,
        verbose_name=_('Verwendete Ersatzteile')
    )

    # Kosten
    labor_hours = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_('Arbeitsstunden')
    )

    total_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_('Gesamtkosten')
    )

    # Dokumentation
    maintenance_report = models.FileField(
        upload_to='equipment/maintenance_reports/',
        null=True,
        blank=True,
        verbose_name=_('Wartungsbericht (PDF)')
    )

    photos = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_('Fotos'),
        help_text=_('Liste der Foto-URLs')
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Erstellt am'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Aktualisiert am'))

    class Meta:
        verbose_name = _('Wartungsprotokoll')
        verbose_name_plural = _('Wartungsprotokolle')
        ordering = ['-maintenance_date']

    def __str__(self):
        return f"{self.assignment.device.inventory_number} - {self.assignment.maintenance_type.name} ({self.maintenance_date})"

    def save(self, *args, **kwargs):
        """Aktualisiert die Wartungszuweisung beim Speichern"""
        super().save(*args, **kwargs)

        # Aktualisiere last_maintenance_date und next_maintenance_date in der Zuweisung
        if self.status in ['completed', 'completed_with_remarks']:
            self.assignment.last_maintenance_date = self.maintenance_date
            if self.next_maintenance_date:
                self.assignment.next_maintenance_date = self.next_maintenance_date
            self.assignment.save(update_fields=['last_maintenance_date', 'next_maintenance_date', 'updated_at'])


# ============================================================================
# BATCHES (Chargen für Verbrauchsmaterial)
# ============================================================================

class EquipmentBatch(models.Model):
    """
    Chargen-/Batch-Tracking für Equipment-Verbrauchsmaterial
    Wichtig für Rückverfolgbarkeit und Rückrufe
    Jede Charge referenziert die Stammdaten (EquipmentItemMaster)
    """

    master = models.ForeignKey(
        EquipmentItemMaster,
        on_delete=models.CASCADE,
        related_name='batches',
        verbose_name=_('Stammdaten')
    )

    batch_number = models.CharField(
        max_length=100,
        verbose_name=_('Chargen-Nummer')
    )

    received_date = models.DateField(
        verbose_name=_('Eingangsdatum')
    )

    expiry_date = models.DateField(
        null=True,
        blank=True,
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
        related_name='equipment_batches',
        verbose_name=_('Lagerort')
    )

    supplier_batch_number = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Lieferanten-Chargen-Nr.')
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

    notes = models.TextField(
        blank=True,
        verbose_name=_('Notizen')
    )

    # Audit-Felder
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Erstellt am'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Aktualisiert am'))
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='equipment_batches_created',
        null=True,
        blank=True,
        verbose_name=_('Erstellt von')
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='equipment_batches_updated',
        null=True,
        blank=True,
        verbose_name=_('Aktualisiert von')
    )

    class Meta:
        verbose_name = _('Charge/Batch')
        verbose_name_plural = _('Chargen/Batches')
        ordering = ['expiry_date', 'received_date']
        unique_together = ['master', 'batch_number']
        indexes = [
            models.Index(fields=['master', 'expiry_date']),
            models.Index(fields=['batch_number']),
            models.Index(fields=['is_recalled']),
            models.Index(fields=['expiry_date']),
        ]

    def __str__(self):
        recall_marker = ' [RÜCKRUF]' if self.is_recalled else ''
        return f"{self.master.name} - Charge {self.batch_number}{recall_marker}"

    def is_expired(self):
        """Prüft ob Charge abgelaufen ist"""
        if not self.expiry_date:
            return False
        return self.expiry_date < timezone.now().date()

    def is_expiring_soon(self, days=90):
        """Prüft ob Charge bald abläuft"""
        if not self.expiry_date:
            return False

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
        if not self.expiry_date:
            return None
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


# ============================================================================
# INVENTUR (INVENTORY CHECK)
# ============================================================================

class EquipmentInventoryCheck(AbstractInventoryCheck):
    """
    Inventur-Check für Equipment (Ausrüstung & Geräte)
    Erbt alle Basis-Funktionalität von AbstractInventoryCheck
    """

    # Equipment-spezifische Felder
    check_certifications = models.BooleanField(
        default=True,
        verbose_name=_('Zertifizierungen prüfen'),
        help_text=_('Prüfungen und Zertifizierungen auf Ablauf kontrollieren')
    )

    check_operational_status = models.BooleanField(
        default=True,
        verbose_name=_('Einsatzbereitschaft prüfen'),
        help_text=_('Betriebszustand und Einsatzfähigkeit kontrollieren')
    )

    check_maintenance_due = models.BooleanField(
        default=True,
        verbose_name=_('Wartungsstatus prüfen'),
        help_text=_('Fällige Wartungen und Prüfungen identifizieren')
    )

    defective_items_found = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Defekte Geräte gefunden')
    )

    expired_certifications_found = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Abgelaufene Zertifizierungen gefunden')
    )

    maintenance_due_found = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Wartungen fällig gefunden')
    )

    class Meta:
        verbose_name = _('Equipment Inventur')
        verbose_name_plural = _('Equipment Inventuren')
        ordering = ['-scheduled_start_date']
        permissions = [
            ('approve_equipmentinventorycheck', 'Kann Equipment-Inventuren genehmigen'),
        ]

    def get_number_prefix(self):
        """Equipment-spezifisches Präfix für Inventurnummern"""
        return 'EQP-INV'

    def update_progress(self):
        """Equipment-spezifische Fortschritts-Berechnung"""
        from django.utils import timezone

        self.total_items = self.items.count()
        self.counted_items = self.items.filter(is_counted=True).count()
        self.items_with_discrepancies = self.items.filter(has_discrepancy=True).count()

        # Zähle defekte Geräte
        if self.check_operational_status:
            self.defective_items_found = self.items.filter(is_defective=True).count()

        # Zähle abgelaufene Zertifizierungen
        if self.check_certifications:
            self.expired_certifications_found = self.items.filter(
                has_certification=True,
                certification_expired=True
            ).count()

        # Zähle fällige Wartungen
        if self.check_maintenance_due:
            self.maintenance_due_found = self.items.filter(maintenance_due=True).count()

        self.save(update_fields=[
            'total_items',
            'counted_items',
            'items_with_discrepancies',
            'defective_items_found',
            'expired_certifications_found',
            'maintenance_due_found'
        ])


class EquipmentInventoryCheckItem(AbstractInventoryCheckItem):
    """Einzelne Position in Equipment-Inventur"""

    inventory_check = models.ForeignKey(
        EquipmentInventoryCheck,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_('Inventur')
    )

    equipment_item = models.ForeignKey(
        EquipmentItem,
        on_delete=models.PROTECT,
        null=True, blank=True,
        related_name='inventory_items',
        verbose_name=_('Equipment-Artikel')
    )

    equipment_device = models.ForeignKey(
        EquipmentDeviceInstance,
        on_delete=models.PROTECT,
        null=True, blank=True,
        related_name='inventory_items',
        verbose_name=_('Equipment-Gerät')
    )

    # Equipment-spezifische Felder
    equipment_type = models.CharField(
        max_length=30,
        choices=EquipmentType.choices,
        blank=True,
        verbose_name=_('Gerätetyp')
    )

    serial_number = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Seriennummer')
    )

    operational_status = models.CharField(
        max_length=20,
        choices=EquipmentStatus.choices,
        blank=True,
        verbose_name=_('Betriebszustand')
    )

    is_defective = models.BooleanField(
        default=False,
        verbose_name=_('Defekt')
    )

    has_certification = models.BooleanField(
        default=False,
        verbose_name=_('Hat Zertifizierung')
    )

    certification_expires = models.DateField(
        null=True, blank=True,
        verbose_name=_('Zertifizierung läuft ab')
    )

    certification_expired = models.BooleanField(
        default=False,
        verbose_name=_('Zertifizierung abgelaufen')
    )

    maintenance_due = models.BooleanField(
        default=False,
        verbose_name=_('Wartung fällig')
    )

    next_maintenance_date = models.DateField(
        null=True, blank=True,
        verbose_name=_('Nächste Wartung')
    )

    class Meta:
        verbose_name = _('Equipment Inventur Position')
        verbose_name_plural = _('Equipment Inventur Positionen')
        ordering = ['location', 'item_name']

    def __str__(self):
        return f"{self.inventory_check.check_number} - {self.item_name}"
