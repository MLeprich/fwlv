"""
Diving Models
Models für die Verwaltung von Tauchausrüstung
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from inventory_base.models import AbstractInventoryItem, AbstractStockMovement, InventoryCheckType


# ============================================================================
# STAMMDATEN-VERWALTUNG (MASTER DATA)
# ============================================================================

class DivingItemMaster(models.Model):
    """
    Tauchausrüstungs-Stammdaten - Produktdefinition ohne Lagerort

    Diese Tabelle enthält die Produktdefinitionen (z.B. "Atemregler Scubapro MK25 EVO")
    mit allen technischen Spezifikationen, Zertifizierungen und Herstellerinformationen.
    """

    # Identifikation
    master_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_('Stammdatennummer'),
        help_text=_('Eindeutige Nummer für dieses Produkt, z.B. DIV-2025-001')
    )

    name = models.CharField(
        max_length=200,
        verbose_name=_('Produktname'),
        help_text=_('z.B. Atemregler Scubapro MK25 EVO')
    )

    description = models.TextField(
        blank=True,
        verbose_name=_('Beschreibung'),
        help_text=_('Detaillierte Produktbeschreibung')
    )

    item_type = models.CharField(
        max_length=50,
        choices=[],  # Wird in __init__ gesetzt
        verbose_name=_('Ausrüstungstyp')
    )

    # Hersteller
    manufacturer = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Hersteller'),
        help_text=_('z.B. Scubapro, Mares, Aqualung')
    )

    model = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Modell'),
        help_text=_('z.B. MK25 EVO, Puck Pro')
    )

    # Zertifizierungen
    certifications = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_('Zertifizierungen'),
        help_text=_('Liste der Zertifizierungen, z.B. ["EN 250", "CE"]')
    )

    certification_number = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Zertifizierungsnummer')
    )

    # Technische Spezifikationen - Tauchflaschen
    tank_type = models.CharField(
        max_length=20,
        choices=[],  # Wird in __init__ gesetzt
        blank=True,
        verbose_name=_('Flaschentyp')
    )

    volume_liters = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        null=True,
        blank=True,
        verbose_name=_('Volumen (Liter)'),
        help_text=_('Flaschenvolumen, z.B. 10, 12, 15 Liter')
    )

    working_pressure_bar = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Nenndruck (bar)'),
        help_text=_('Betriebsdruck der Flasche, z.B. 200, 232, 300 bar')
    )

    test_pressure_bar = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Prüfdruck (bar)'),
        help_text=_('Druck bei TÜV-Prüfung')
    )

    # Technische Spezifikationen - Allgemein
    max_depth_m = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Max. Tauchtiefe (m)'),
        help_text=_('Maximale Einsatztiefe')
    )

    weight_kg = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_('Gewicht (kg)')
    )

    material = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Material'),
        help_text=_('z.B. Neopren 5mm, Trilaminat, Messing')
    )

    # Lebenszyklus
    max_service_life_years = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Max. Nutzungsdauer (Jahre)'),
        help_text=_('Maximale Nutzungsdauer laut Hersteller')
    )

    service_interval_months = models.PositiveIntegerField(
        default=12,
        verbose_name=_('Wartungsintervall (Monate)'),
        help_text=_('Standard-Wartungsintervall, z.B. 12 für jährlich')
    )

    tuv_interval_months = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_('TÜV-Intervall (Monate)'),
        help_text=_('Tauchflaschen: 30 Monate (2.5 Jahre)')
    )

    # Wirtschaftliche Daten
    purchase_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_('Standardpreis (netto)'),
        help_text=_('Durchschnittlicher Einkaufspreis')
    )

    # Dokumentation
    manual_document = models.FileField(
        upload_to='diving/masters/manuals/',
        blank=True,
        null=True,
        verbose_name=_('Bedienungsanleitung'),
        help_text=_('PDF-Dokument der Bedienungsanleitung')
    )

    image = models.ImageField(
        upload_to='diving/masters/images/',
        blank=True,
        null=True,
        verbose_name=_('Produktbild')
    )

    # Notizen
    notes = models.TextField(
        blank=True,
        verbose_name=_('Notizen')
    )

    # Status
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Aktiv'),
        help_text=_('Wird dieses Produkt noch verwendet?')
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Erstellt am'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Aktualisiert am'))
    created_by = models.ForeignKey(
        'core.User',
        on_delete=models.PROTECT,
        related_name='created_diving_masters',
        verbose_name=_('Erstellt von')
    )

    class Meta:
        verbose_name = _('Tauchausrüstungs-Stammdaten')
        verbose_name_plural = _('Tauchausrüstungs-Stammdaten')
        ordering = ['master_number', 'name']
        indexes = [
            models.Index(fields=['master_number']),
            models.Index(fields=['item_type']),
            models.Index(fields=['manufacturer']),
            models.Index(fields=['is_active']),
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Dynamische Choices-Zuweisung
        self._meta.get_field('item_type').choices = DivingItemType.choices
        self._meta.get_field('tank_type').choices = TankType.choices

    def __str__(self):
        return f"{self.master_number} - {self.name}"

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('diving:master_detail', kwargs={'pk': self.pk})


class DivingDeviceInstance(models.Model):
    """
    Tauchgerät-Instanz mit individueller Inventarnummer

    Jede physische Ausrüstung (z.B. eine spezifische Tauchflasche mit Seriennummer)
    wird hier als Instanz erfasst und mit den Stammdaten verknüpft.
    """

    # Verknüpfung zu Stammdaten
    master = models.ForeignKey(
        DivingItemMaster,
        on_delete=models.PROTECT,
        related_name='device_instances',
        verbose_name=_('Stammdaten')
    )

    # Eindeutige Identifikation
    inventory_number = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_('Inventarnummer'),
        help_text=_('Eindeutige Inventarnummer, z.B. DIV-FL-001')
    )

    serial_number = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Seriennummer'),
        help_text=_('Herstellerseriennummer')
    )

    # Lagerort (PFLICHTFELD für Instanzen)
    location = models.ForeignKey(
        'locations.Location',
        on_delete=models.PROTECT,
        related_name='diving_devices',
        verbose_name=_('Lagerort')
    )

    # Herstellung & Inbetriebnahme
    manufacturing_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Herstellungsdatum')
    )

    first_use_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Erstinbetriebnahme')
    )

    # TÜV-Prüfung (Tauchflaschen)
    last_tuv_inspection = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Letzte TÜV-Prüfung')
    )

    next_tuv_inspection = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Nächste TÜV-Prüfung'),
        help_text=_('Tauchflaschen: alle 2.5 Jahre')
    )

    tuv_certificate_number = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('TÜV-Zertifikatsnummer')
    )

    inspection_status = models.CharField(
        max_length=20,
        choices=[],  # Wird in __init__ gesetzt
        default='not_due',
        verbose_name=_('Prüfstatus')
    )

    tuv_certificate = models.FileField(
        upload_to='diving/devices/tuv_certificates/',
        blank=True,
        verbose_name=_('TÜV-Zertifikat')
    )

    # Wartung
    last_service_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Letzte Wartung')
    )

    next_service_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Nächste Wartung')
    )

    last_service_technician = models.ForeignKey(
        'personnel.Person',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='serviced_diving_devices',
        verbose_name=_('Letzter Servicetechniker')
    )

    service_log = models.FileField(
        upload_to='diving/devices/service_logs/',
        blank=True,
        verbose_name=_('Wartungsprotokoll')
    )

    # Nutzung & Einsatz
    total_dives = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Anzahl Tauchgänge')
    )

    total_hours = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0,
        verbose_name=_('Gesamte Tauchstunden')
    )

    last_use_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Letzter Einsatz')
    )

    # Aktueller Zustand (für Flaschen)
    current_gas_type = models.CharField(
        max_length=20,
        choices=[],  # Wird in __init__ gesetzt
        blank=True,
        verbose_name=_('Aktuelles Atemgas')
    )

    current_fill_pressure_bar = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Aktueller Fülldruck (bar)')
    )

    # Zustand
    condition = models.CharField(
        max_length=20,
        choices=[
            ('new', _('Neu')),
            ('excellent', _('Sehr gut')),
            ('good', _('Gut')),
            ('fair', _('Befriedigend')),
            ('poor', _('Schlecht')),
            ('defective', _('Defekt')),
        ],
        default='good',
        verbose_name=_('Zustand')
    )

    is_operational = models.BooleanField(
        default=True,
        verbose_name=_('Einsatzbereit'),
        help_text=_('Kann die Ausrüstung verwendet werden?')
    )

    condition_notes = models.TextField(
        blank=True,
        verbose_name=_('Zustandsnotizen')
    )

    defects = models.TextField(
        blank=True,
        verbose_name=_('Bekannte Mängel')
    )

    # Aussonderung
    retirement_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Aussonderungsdatum')
    )

    retirement_reason = models.TextField(
        blank=True,
        verbose_name=_('Aussonderungsgrund')
    )

    # Zuordnung
    assigned_vehicle = models.ForeignKey(
        'vehicles.Vehicle',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='diving_devices',
        verbose_name=_('Zugeordnetes Fahrzeug')
    )

    assigned_to = models.ForeignKey(
        'personnel.Person',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_diving_devices',
        verbose_name=_('Zugeordnet an Person')
    )

    # Fotos & Dokumentation
    photos = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_('Fotos'),
        help_text=_('Liste der Foto-URLs')
    )

    # QR-Code & Barcode
    qr_code = models.ImageField(
        upload_to='diving/devices/qr_codes/',
        blank=True,
        null=True,
        verbose_name=_('QR-Code')
    )

    barcode = models.ImageField(
        upload_to='diving/devices/barcodes/',
        blank=True,
        null=True,
        verbose_name=_('Barcode')
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
        related_name='created_diving_devices',
        verbose_name=_('Erstellt von')
    )

    class Meta:
        verbose_name = _('Tauchgerät-Instanz')
        verbose_name_plural = _('Tauchgeräte-Instanzen')
        ordering = ['inventory_number']
        indexes = [
            models.Index(fields=['inventory_number']),
            models.Index(fields=['serial_number']),
            models.Index(fields=['master']),
            models.Index(fields=['location']),
            models.Index(fields=['next_tuv_inspection']),
            models.Index(fields=['next_service_date']),
            models.Index(fields=['inspection_status']),
            models.Index(fields=['is_operational']),
            models.Index(fields=['assigned_vehicle']),
            models.Index(fields=['assigned_to']),
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Dynamische Choices-Zuweisung
        self._meta.get_field('inspection_status').choices = InspectionStatus.choices
        self._meta.get_field('current_gas_type').choices = GasType.choices

    def __str__(self):
        return f"{self.inventory_number} - {self.master.name}"

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('diving:device_detail', kwargs={'pk': self.pk})

    def save(self, *args, **kwargs):
        """Automatische QR-Code und Barcode Generierung"""
        super().save(*args, **kwargs)

        # QR-Code generieren
        if not self.qr_code:
            self.generate_qr_code()

        # Barcode generieren
        if not self.barcode:
            self.generate_barcode()

    def generate_qr_code(self):
        """Generiert QR-Code für das Gerät"""
        import qrcode
        from io import BytesIO
        from django.core.files import File

        # Nur URL kodieren für maximale Scanner-Kompatibilität
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(f"/diving/device/{self.pk}/")
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')

        self.qr_code.save(
            f'diving_qr_{self.inventory_number}.png',
            File(buffer),
            save=False
        )
        self.save(update_fields=['qr_code'])

    def generate_barcode(self):
        """Generiert Barcode für das Gerät"""
        import barcode
        from barcode.writer import ImageWriter
        from io import BytesIO
        from django.core.files import File

        # Verwende Code128
        code128 = barcode.get_barcode_class('code128')
        barcode_instance = code128(self.inventory_number, writer=ImageWriter())

        buffer = BytesIO()
        barcode_instance.write(buffer)

        self.barcode.save(
            f'diving_barcode_{self.inventory_number}.png',
            File(buffer),
            save=False
        )
        self.save(update_fields=['barcode'])

    def is_tuv_due(self):
        """Prüft ob TÜV-Prüfung fällig ist"""
        from datetime import date
        if not self.next_tuv_inspection:
            return False
        return self.next_tuv_inspection <= date.today()

    def is_tuv_due_soon(self, days=30):
        """Prüft ob TÜV-Prüfung bald fällig ist"""
        from datetime import date, timedelta
        if not self.next_tuv_inspection:
            return False
        return self.next_tuv_inspection <= date.today() + timedelta(days=days)

    def is_service_due(self):
        """Prüft ob Wartung fällig ist"""
        from datetime import date
        if not self.next_service_date:
            return False
        return self.next_service_date <= date.today()

    def is_service_due_soon(self, days=30):
        """Prüft ob Wartung bald fällig ist"""
        from datetime import date, timedelta
        if not self.next_service_date:
            return False
        return self.next_service_date <= date.today() + timedelta(days=days)


# ============================================================================
# LEGACY MODEL (bleibt für Abwärtskompatibilität)
# ============================================================================

# ============================================================================
# TYPENVERWALTUNG (TYPE MANAGEMENT)
# ============================================================================

class EquipmentType(models.Model):
    """
    Verwaltbare Ausrüstungstypen für Tauchausrüstung
    Ersetzt die fest kodierten DivingItemType Choices
    """
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_('Ausrüstungstyp'),
        help_text=_('z.B. Tauchflasche, Atemregler, Tarierjacket')
    )

    code = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_('Code'),
        help_text=_('Eindeutiger Code, z.B. scuba_tank, regulator')
    )

    description = models.TextField(
        blank=True,
        verbose_name=_('Beschreibung')
    )

    category = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_('Kategorie'),
        help_text=_('z.B. Atemausrüstung, Schutzausrüstung, Instrumente')
    )

    icon = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_('Icon'),
        help_text=_('Emoji oder Icon-Klasse')
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Aktiv')
    )

    sort_order = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Sortierung')
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Erstellt am'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Aktualisiert am'))
    created_by = models.ForeignKey(
        'core.User',
        on_delete=models.PROTECT,
        related_name='created_equipment_types',
        verbose_name=_('Erstellt von')
    )

    class Meta:
        verbose_name = _('Ausrüstungstyp')
        verbose_name_plural = _('Ausrüstungstypen')
        ordering = ['sort_order', 'name']

    def __str__(self):
        return self.name


class BottleType(models.Model):
    """
    Verwaltbare Flaschentypen für Tauchflaschen
    Ersetzt die fest kodierten TankType Choices
    """
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_('Flaschentyp'),
        help_text=_('z.B. Stahlflasche, Aluminiumflasche')
    )

    code = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_('Code'),
        help_text=_('Eindeutiger Code, z.B. steel, aluminum')
    )

    description = models.TextField(
        blank=True,
        verbose_name=_('Beschreibung')
    )

    material = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Material'),
        help_text=_('z.B. Stahl, Aluminium, Komposit')
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Aktiv')
    )

    sort_order = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Sortierung')
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Erstellt am'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Aktualisiert am'))
    created_by = models.ForeignKey(
        'core.User',
        on_delete=models.PROTECT,
        related_name='created_bottle_types',
        verbose_name=_('Erstellt von')
    )

    class Meta:
        verbose_name = _('Flaschentyp')
        verbose_name_plural = _('Flaschentypen')
        ordering = ['sort_order', 'name']

    def __str__(self):
        return self.name


# ============================================================================
# CHARGEN-VERWALTUNG (BATCH MANAGEMENT)
# ============================================================================

class DivingBatch(models.Model):
    """
    Chargen/Batch-Verwaltung für Verbrauchsmaterialien
    (z.B. Desinfektionsmittel, Tauchmasken-Pflege, O-Ringe, Schmiermittel)
    Ermöglicht Rückverfolgung und Ablaufdatums-Management
    """

    # Verknüpfung zu Stammdaten
    master = models.ForeignKey(
        DivingItemMaster,
        on_delete=models.CASCADE,
        related_name='batches',
        verbose_name=_('Stammdaten')
    )

    # Chargen-Identifikation
    batch_number = models.CharField(
        max_length=100,
        verbose_name=_('Chargennummer'),
        help_text=_('Herstellerchargennummer')
    )

    # Datumsangaben
    received_date = models.DateField(
        verbose_name=_('Eingangsdatum'),
        help_text=_('Wann wurde die Charge empfangen?')
    )

    expiry_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Ablaufdatum'),
        help_text=_('Mindesthaltbarkeitsdatum')
    )

    # Mengen
    quantity_received = models.PositiveIntegerField(
        verbose_name=_('Eingangsmenge'),
        help_text=_('Wie viele Einheiten wurden empfangen?')
    )

    quantity_remaining = models.PositiveIntegerField(
        verbose_name=_('Restmenge'),
        help_text=_('Wie viele Einheiten sind noch vorhanden?')
    )

    # Lagerort
    location = models.ForeignKey(
        'locations.Location',
        on_delete=models.PROTECT,
        related_name='diving_batches',
        verbose_name=_('Lagerort')
    )

    # Zusatzinformationen
    supplier = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Lieferant'),
        help_text=_('Von wem wurde die Charge bezogen?')
    )

    purchase_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_('Einkaufspreis (€)'),
        help_text=_('Preis für die gesamte Charge')
    )

    notes = models.TextField(
        blank=True,
        verbose_name=_('Notizen')
    )

    # Status
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Aktiv'),
        help_text=_('Ist die Charge noch im Bestand?')
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Erstellt am'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Aktualisiert am'))
    created_by = models.ForeignKey(
        'core.User',
        on_delete=models.PROTECT,
        related_name='created_diving_batches',
        verbose_name=_('Erstellt von')
    )

    class Meta:
        verbose_name = _('Charge')
        verbose_name_plural = _('Chargen')
        ordering = ['-received_date', 'expiry_date']
        indexes = [
            models.Index(fields=['master']),
            models.Index(fields=['batch_number']),
            models.Index(fields=['expiry_date']),
            models.Index(fields=['location']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.master.name} - Charge {self.batch_number}"

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('diving:batch_detail', kwargs={'pk': self.pk})

    @property
    def is_expired(self):
        """Prüft ob die Charge abgelaufen ist"""
        from datetime import date
        if not self.expiry_date:
            return False
        return self.expiry_date < date.today()

    @property
    def is_expiring_soon(self, days=30):
        """Prüft ob die Charge bald abläuft"""
        from datetime import date, timedelta
        if not self.expiry_date:
            return False
        return date.today() <= self.expiry_date <= date.today() + timedelta(days=days)

    @property
    def quantity_used(self):
        """Berechnet die bereits verbrauchte Menge"""
        return self.quantity_received - self.quantity_remaining

    @property
    def usage_percentage(self):
        """Berechnet den Verbrauch in Prozent"""
        if self.quantity_received == 0:
            return 0
        return (self.quantity_used / self.quantity_received) * 100


# Legacy TextChoices für Rückwärtskompatibilität
class DivingItemType(models.TextChoices):
    """Typen von Tauchausrüstung (Legacy - wird durch EquipmentType ersetzt)"""
    # Atemausrüstung
    SCUBA_TANK = 'scuba_tank', _('Tauchflasche')
    REGULATOR = 'regulator', _('Atemregler')
    OCTOPUS = 'octopus', _('Oktopus (Reserveatemregler)')
    BCD = 'bcd', _('Tarierjacket (BCD)')

    # Schutzausrüstung
    WETSUIT = 'wetsuit', _('Nassanzug')
    DRYSUIT = 'drysuit', _('Trockenanzug')
    DIVING_MASK = 'diving_mask', _('Tauchmaske')
    SNORKEL = 'snorkel', _('Schnorchel')
    FINS = 'fins', _('Flossen')
    DIVING_BOOTS = 'diving_boots', _('Tauchschuhe')
    DIVING_GLOVES = 'diving_gloves', _('Tauchhandschuhe')
    HOOD = 'hood', _('Kopfhaube')

    # Instrumente & Navigation
    DIVE_COMPUTER = 'dive_computer', _('Tauchcomputer')
    DEPTH_GAUGE = 'depth_gauge', _('Tiefenmesser')
    COMPASS = 'compass', _('Kompass')
    PRESSURE_GAUGE = 'pressure_gauge', _('Finimeter')

    # Sicherheit & Rettung
    KNIFE = 'knife', _('Tauchmesser')
    TORCH = 'torch', _('Tauchlampe')
    SMB = 'smb', _('Signalboje (SMB)')
    WHISTLE = 'whistle', _('Signalpfeife')
    SAFETY_REEL = 'safety_reel', _('Sicherheitsleine mit Rolle')

    # Gewichte & Zubehör
    WEIGHT_BELT = 'weight_belt', _('Bleigurt')
    WEIGHT = 'weight', _('Bleigewicht')
    MESH_BAG = 'mesh_bag', _('Netztasche')

    # Kompressor & Wartung
    COMPRESSOR = 'compressor', _('Tauchkompressor')
    FILL_STATION = 'fill_station', _('Füllstation')
    MAINTENANCE_KIT = 'maintenance_kit', _('Wartungskit')


class TankType(models.TextChoices):
    """Tauchflaschentypen (Legacy - wird durch BottleType ersetzt)"""
    STEEL = 'steel', _('Stahlflasche')
    ALUMINUM = 'aluminum', _('Aluminiumflasche')
    COMPOSITE = 'composite', _('Kompositflasche')


class GasType(models.TextChoices):
    """Atemgastypen"""
    AIR = 'air', _('Pressluft')
    NITROX_32 = 'nitrox_32', _('Nitrox 32 (EAN32)')
    NITROX_36 = 'nitrox_36', _('Nitrox 36 (EAN36)')
    TRIMIX = 'trimix', _('Trimix')
    HELIOX = 'heliox', _('Heliox')
    OXYGEN = 'oxygen', _('Reiner Sauerstoff (O2)')


class InspectionStatus(models.TextChoices):
    """Status der TÜV-Prüfung"""
    NOT_DUE = 'not_due', _('Nicht fällig')
    DUE_SOON = 'due_soon', _('Demnächst fällig')
    OVERDUE = 'overdue', _('Überfällig')
    PASSED = 'passed', _('Bestanden')
    FAILED = 'failed', _('Nicht bestanden')
    CONDEMNED = 'condemned', _('Ausgemustert')


class DivingItem(AbstractInventoryItem):
    """
    Tauchausrüstung

    Spezifische Felder für Tauchen:
    - TÜV-Prüfungen (Flaschen alle 2.5 Jahre)
    - Fülldruck und Volumen
    - Tauchtiefe und -dauer
    - Materialspezifikationen
    """

    # Typ und Klassifikation
    item_type = models.CharField(
        max_length=50,
        choices=DivingItemType.choices,
        verbose_name=_('Ausrüstungstyp')
    )

    # Tauchflaschen-spezifisch
    tank_type = models.CharField(
        max_length=20,
        choices=TankType.choices,
        blank=True,
        verbose_name=_('Flaschentyp')
    )

    volume_liters = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        null=True,
        blank=True,
        verbose_name=_('Volumen (Liter)'),
        help_text=_('Flaschenvolumen in Litern')
    )

    working_pressure_bar = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Nenndruck (bar)'),
        help_text=_('Betriebsdruck der Flasche')
    )

    test_pressure_bar = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Prüfdruck (bar)'),
        help_text=_('Druck bei TÜV-Prüfung')
    )

    current_gas_type = models.CharField(
        max_length=20,
        choices=GasType.choices,
        default=GasType.AIR,
        blank=True,
        verbose_name=_('Aktuelles Atemgas')
    )

    serial_number = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Seriennummer')
    )

    # TÜV-Prüfung (Flaschen: alle 2.5 Jahre)
    manufacturing_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Herstellungsdatum')
    )

    last_tuv_inspection = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Letzte TÜV-Prüfung')
    )

    next_tuv_inspection = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Nächste TÜV-Prüfung'),
        help_text=_('Tauchflaschen: alle 2.5 Jahre')
    )

    tuv_certificate_number = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('TÜV-Zertifikatsnummer')
    )

    inspection_status = models.CharField(
        max_length=20,
        choices=InspectionStatus.choices,
        default=InspectionStatus.NOT_DUE,
        verbose_name=_('Prüfstatus')
    )

    # Regelmäßige Wartung (Atemregler, BCD, etc.)
    last_service_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Letzte Wartung')
    )

    next_service_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Nächste Wartung'),
        help_text=_('Atemregler: jährlich')
    )

    service_interval_months = models.PositiveIntegerField(
        default=12,
        validators=[MinValueValidator(1), MaxValueValidator(120)],
        verbose_name=_('Wartungsintervall (Monate)'),
        help_text=_('Standard: 12 Monate')
    )

    last_service_technician = models.ForeignKey(
        'personnel.Person',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='serviced_diving_items',
        verbose_name=_('Letzter Servicetechniker')
    )

    # Technische Spezifikationen
    max_depth_m = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Max. Tauchtiefe (m)'),
        help_text=_('Maximale Einsatztiefe')
    )

    weight_kg = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_('Gewicht (kg)')
    )

    size = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_('Größe'),
        help_text=_('z.B. S/M/L oder EU-Schuhgröße')
    )

    material = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Material'),
        help_text=_('z.B. Neopren 5mm, Trilaminat')
    )

    # Nutzungshistorie
    total_dives = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Anzahl Tauchgänge')
    )

    total_hours = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0,
        verbose_name=_('Gesamte Tauchstunden')
    )

    last_use_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Letzter Einsatz')
    )

    # Zustand
    condition_notes = models.TextField(
        blank=True,
        verbose_name=_('Zustandsnotizen')
    )

    defects = models.TextField(
        blank=True,
        verbose_name=_('Mängel'),
        help_text=_('Bekannte Defekte oder Beschädigungen')
    )

    retirement_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Aussonderungsdatum')
    )

    retirement_reason = models.TextField(
        blank=True,
        verbose_name=_('Aussonderungsgrund')
    )

    # Dokumentation
    service_manual = models.FileField(
        upload_to='diving/manuals/',
        blank=True,
        verbose_name=_('Serviceanleitung')
    )

    tuv_certificate = models.FileField(
        upload_to='diving/tuv_certificates/',
        blank=True,
        verbose_name=_('TÜV-Zertifikat')
    )

    service_log = models.FileField(
        upload_to='diving/service_logs/',
        blank=True,
        verbose_name=_('Wartungsprotokoll')
    )

    photos = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_('Fotos')
    )

    # Fahrzeugzuordnung
    assigned_vehicles = models.ManyToManyField(
        'vehicles.Vehicle',
        blank=True,
        related_name='diving_equipment',
        verbose_name=_('Zugeordnete Fahrzeuge')
    )

    class Meta:
        verbose_name = _('Tauchausrüstung')
        verbose_name_plural = _('Tauchausrüstung')
        ordering = ['item_type', 'name']
        indexes = [
            models.Index(fields=['item_type']),
            models.Index(fields=['tank_type']),
            models.Index(fields=['next_tuv_inspection']),
            models.Index(fields=['next_service_date']),
            models.Index(fields=['inspection_status']),
            models.Index(fields=['serial_number']),
        ]

    def __str__(self):
        return f"{self.get_item_type_display()} - {self.name}"

    def is_tuv_due(self):
        """Prüft ob TÜV-Prüfung fällig ist"""
        from datetime import date
        if not self.next_tuv_inspection:
            return False
        return self.next_tuv_inspection <= date.today()

    def is_tuv_due_soon(self, days=30):
        """Prüft ob TÜV-Prüfung bald fällig ist"""
        from datetime import date, timedelta
        if not self.next_tuv_inspection:
            return False
        return self.next_tuv_inspection <= date.today() + timedelta(days=days)

    def is_service_due(self):
        """Prüft ob Wartung fällig ist"""
        from datetime import date
        if not self.next_service_date:
            return False
        return self.next_service_date <= date.today()

    def is_service_due_soon(self, days=30):
        """Prüft ob Wartung bald fällig ist"""
        from datetime import date, timedelta
        if not self.next_service_date:
            return False
        return self.next_service_date <= date.today() + timedelta(days=days)

    def is_condemned(self):
        """Prüft ob Ausrüstung ausgemustert ist"""
        return self.inspection_status == InspectionStatus.CONDEMNED or bool(self.retirement_date)

    def get_age_years(self):
        """Berechnet Alter in Jahren"""
        from datetime import date
        if not self.manufacturing_date:
            return None
        delta = date.today() - self.manufacturing_date
        return delta.days / 365.25


class DivingStockMovement(AbstractStockMovement):
    """
    Lagerbewegungen für Tauchausrüstung

    Erweitert AbstractStockMovement um tauchspezifische Felder:
    - Gasfüllung
    - Tauchgangsdokumentation
    - Wartung/Service
    """

    item = models.ForeignKey(
        DivingItem,
        on_delete=models.CASCADE,
        related_name='stock_movements',
        verbose_name=_('Ausrüstung')
    )

    # Gasfüllung (für Flaschen)
    gas_filled = models.BooleanField(
        default=False,
        verbose_name=_('Gas gefüllt')
    )

    gas_type = models.CharField(
        max_length=20,
        choices=GasType.choices,
        blank=True,
        verbose_name=_('Gastyp')
    )

    fill_pressure_bar = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Fülldruck (bar)')
    )

    oxygen_percentage = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        null=True,
        blank=True,
        validators=[MinValueValidator(21), MaxValueValidator(100)],
        verbose_name=_('Sauerstoffanteil (%)'),
        help_text=_('z.B. 32% für Nitrox 32')
    )

    # Tauchgangsdokumentation
    dive_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Tauchgangsdatum')
    )

    dive_location = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Tauchort')
    )

    max_depth_m = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Max. Tiefe (m)')
    )

    dive_duration_minutes = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Tauchzeit (Minuten)')
    )

    dive_purpose = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Taucheinsatz'),
        help_text=_('z.B. Rettungseinsatz, Bergung, Training, Suche')
    )

    # Service/Wartung
    service_performed = models.BooleanField(
        default=False,
        verbose_name=_('Wartung durchgeführt')
    )

    service_type = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Wartungsart'),
        help_text=_('z.B. Jahresservice, Reparatur, Dichtungswechsel')
    )

    service_notes = models.TextField(
        blank=True,
        verbose_name=_('Wartungsnotizen')
    )

    parts_replaced = models.TextField(
        blank=True,
        verbose_name=_('Ersetzte Teile')
    )

    service_technician = models.ForeignKey(
        'personnel.Person',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='diving_service_movements',
        verbose_name=_('Servicetechniker')
    )

    # Zustandsdokumentation
    condition_before = models.TextField(
        blank=True,
        verbose_name=_('Zustand vorher')
    )

    condition_after = models.TextField(
        blank=True,
        verbose_name=_('Zustand nachher')
    )

    photos = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_('Fotos')
    )

    class Meta:
        verbose_name = _('Lagerbewegung Tauchen')
        verbose_name_plural = _('Lagerbewegungen Tauchen')
        ordering = ['-movement_date', '-created_at']
        indexes = [
            models.Index(fields=['item', 'movement_date']),
            models.Index(fields=['gas_filled']),
            models.Index(fields=['service_performed']),
            models.Index(fields=['dive_date']),
        ]

    def __str__(self):
        return f"{self.get_movement_type_display()} - {self.item.name} ({self.movement_date})"

    def save(self, *args, **kwargs):
        """Automatische Updates bei Gasfüllung oder Service"""
        super().save(*args, **kwargs)

        # Lagerort des Items aktualisieren
        from inventory_base.models import StockMovementType
        if self.movement_type == StockMovementType.TRANSFER and self.to_location:
            self.item.location = self.to_location
            self.item.save(update_fields=['location'])
        elif self.movement_type == StockMovementType.INCOMING and self.to_location:
            self.item.location = self.to_location
            self.item.save(update_fields=['location'])

        # Bei Gasfüllung: Gas-Typ in Item aktualisieren
        if self.gas_filled and self.gas_type:
            self.item.current_gas_type = self.gas_type
            self.item.save()

        # Bei Service: Service-Datum aktualisieren
        if self.service_performed:
            from datetime import timedelta
            self.item.last_service_date = self.movement_date.date() if hasattr(self.movement_date, 'date') else self.movement_date
            self.item.next_service_date = self.item.last_service_date + timedelta(
                days=self.item.service_interval_months * 30
            )
            self.item.last_service_technician = self.service_technician
            self.item.save()

        # Bei Tauchgang: Statistiken aktualisieren
        if self.dive_date:
            self.item.total_dives += 1
            if self.dive_duration_minutes:
                self.item.total_hours += self.dive_duration_minutes / 60
            self.item.last_use_date = self.dive_date
            self.item.save()


class DivingServiceLog(models.Model):
    """
    Wartungsprotokoll für Tauchausrüstung

    Dokumentiert alle Wartungen und Reparaturen.
    Besonders wichtig für Atemregler und Tauchflaschen.
    """

    device = models.ForeignKey(
        DivingDeviceInstance,
        on_delete=models.CASCADE,
        related_name='service_logs',
        verbose_name=_('Geräte-Instanz')
    )

    # Service-Daten
    service_date = models.DateField(
        verbose_name=_('Servicedatum')
    )

    # Optionaler Wartungstyp mit Checkliste
    service_type_obj = models.ForeignKey(
        'DivingServiceType',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='service_logs',
        verbose_name=_('Wartungstyp (mit Checkliste)'),
        help_text=_('Optional: Wählen Sie einen vordefinierten Wartungstyp mit Checkliste')
    )

    # Fallback: Einfache Serviceart (wenn kein Wartungstyp gewählt)
    service_type = models.CharField(
        max_length=50,
        choices=[
            ('annual', _('Jahresservice')),
            ('tuv', _('TÜV-Prüfung')),
            ('repair', _('Reparatur')),
            ('visual', _('Sichtprüfung')),
            ('function_test', _('Funktionstest')),
            ('cleaning', _('Reinigung')),
            ('custom', _('Benutzerdefiniert')),
        ],
        default='annual',
        verbose_name=_('Einfache Serviceart'),
        help_text=_('Wird verwendet wenn kein Wartungstyp mit Checkliste gewählt wurde')
    )

    # Checklisten-Ergebnisse (JSON)
    checklist_results = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Checklisten-Ergebnisse'),
        help_text=_('Ergebnisse der Checklisten-Prüfpunkte')
    )

    # Messwerte (JSON)
    measurement_results = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Messwerte'),
        help_text=_('Erfasste Messwerte aus dem Wartungstyp')
    )

    technician = models.ForeignKey(
        'personnel.Person',
        on_delete=models.PROTECT,
        related_name='diving_service_logs',
        verbose_name=_('Techniker')
    )

    # Service-Ergebnis
    passed = models.BooleanField(
        verbose_name=_('Bestanden')
    )

    findings = models.TextField(
        blank=True,
        verbose_name=_('Feststellungen')
    )

    work_performed = models.TextField(
        blank=True,
        verbose_name=_('Durchgeführte Arbeiten')
    )

    parts_replaced = models.TextField(
        blank=True,
        verbose_name=_('Ersetzte Teile')
    )

    # Prüfwerte (für Atemregler)
    cracking_pressure_mbar = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Ansprechdruck (mbar)'),
        help_text=_('Atemregler: sollte 18-25 mbar sein')
    )

    flow_rate_l_min = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Durchflussrate (l/min)')
    )

    leak_test_passed = models.BooleanField(
        default=True,
        verbose_name=_('Dichtigkeitsprüfung bestanden')
    )

    # Kosten
    labor_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name=_('Arbeitskosten (€)')
    )

    parts_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name=_('Materialkosten (€)')
    )

    # Dokumentation
    service_report = models.FileField(
        upload_to='diving/service_reports/',
        blank=True,
        verbose_name=_('Serviceprotokoll (PDF)')
    )

    photos = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_('Fotos')
    )

    # Nächster Service
    next_service_due = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Nächster Service fällig')
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Erstellt am'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Aktualisiert am'))

    class Meta:
        verbose_name = _('Serviceprotokoll Tauchen')
        verbose_name_plural = _('Serviceprotokolle Tauchen')
        ordering = ['-service_date']
        indexes = [
            models.Index(fields=['device', 'service_date']),
            models.Index(fields=['technician', 'service_date']),
            models.Index(fields=['passed']),
        ]

    def __str__(self):
        status = "✓" if self.passed else "✗"
        return f"{status} {self.device.inventory_number} - {self.service_date}"

    def total_cost(self):
        """Berechnet Gesamtkosten"""
        return self.labor_cost + self.parts_cost


# ============================================================================
# WARTUNGSVERWALTUNG (SERVICE TYPES & ASSIGNMENTS)
# ============================================================================

class DivingServiceType(models.Model):
    """
    Wartungsart für Tauchausrüstung
    (z.B. Jahresservice, TÜV-Prüfung, Dichtungswechsel, Funktionsprüfung)
    Kann individuell erstellt und Ausrüstung zugewiesen werden
    """

    name = models.CharField(
        max_length=200,
        verbose_name=_('Wartungsbezeichnung'),
        help_text=_('z.B. Jahresservice Atemregler, TÜV-Prüfung Flasche, Dichtungswechsel')
    )

    description = models.TextField(
        blank=True,
        verbose_name=_('Beschreibung'),
        help_text=_('Was wird bei dieser Wartung durchgeführt?')
    )

    # Wartungsstandard/Grundlage
    service_standard = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Wartungsstandard'),
        help_text=_('z.B. Herstellervorgabe, DIN EN 250')
    )

    # Intervall
    interval_months = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Intervall (Monate)'),
        help_text=_('Wie oft muss diese Wartung durchgeführt werden?')
    )

    # Checkliste als JSON
    # Format: [{"id": 1, "text": "Atemregler auf Beschädigungen prüfen", "required": true}, ...]
    checklist = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_('Wartungspunkte'),
        help_text=_('Liste der durchzuführenden Wartungsarbeiten')
    )

    # Zuweisbare Ausrüstungstypen
    applicable_item_types = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_('Anwendbar auf Ausrüstungstypen'),
        help_text=_('Für welche Ausrüstungstypen ist diese Wartung relevant?')
    )

    # Benutzerdefinierte Messfelder als JSON
    # Format: [{"name": "Ansprechdruck", "type": "number", "unit": "mbar", "required": true, "min": 15, "max": 30}]
    custom_fields = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_('Benutzerdefinierte Messfelder'),
        help_text=_('Individuelle Felder für Messwerte (z.B. Ansprechdruck, Durchflussrate)')
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

    # Kritikalität
    is_mandatory = models.BooleanField(
        default=True,
        verbose_name=_('Pflichtwartung'),
        help_text=_('Gesetzlich oder herstellerseitig vorgeschriebene Wartung')
    )

    # Meta
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Aktiv')
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Erstellt am'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Aktualisiert am'))
    created_by = models.ForeignKey(
        'core.User',
        on_delete=models.PROTECT,
        related_name='created_diving_service_types',
        verbose_name=_('Erstellt von')
    )

    class Meta:
        verbose_name = _('Wartungsart Tauchen')
        verbose_name_plural = _('Wartungsarten Tauchen')
        ordering = ['name']

    def __str__(self):
        return self.name


class DivingServiceAssignment(models.Model):
    """
    Zuweisung einer Wartungsart zu einer Tauchausrüstung
    Eine Ausrüstung kann mehrere verschiedene Wartungsarten haben
    """

    device = models.ForeignKey(
        DivingDeviceInstance,
        on_delete=models.CASCADE,
        related_name='service_assignments',
        verbose_name=_('Geräte-Instanz')
    )

    service_type = models.ForeignKey(
        DivingServiceType,
        on_delete=models.CASCADE,
        related_name='item_assignments',
        verbose_name=_('Wartungsart')
    )

    # Individuelle Intervall-Überschreibung
    custom_interval_months = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Individuelles Intervall (Monate)'),
        help_text=_('Überschreibt Standard-Intervall der Wartungsart')
    )

    # Termine
    last_service_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Letzte Wartung')
    )

    next_service_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Nächste Wartung')
    )

    # Meta
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Aktiv'),
        help_text=_('Wartung wird noch durchgeführt')
    )

    notes = models.TextField(
        blank=True,
        verbose_name=_('Notizen')
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Erstellt am'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Aktualisiert am'))
    created_by = models.ForeignKey(
        'core.User',
        on_delete=models.PROTECT,
        related_name='created_diving_service_assignments',
        verbose_name=_('Erstellt von')
    )

    class Meta:
        verbose_name = _('Wartungszuweisung Tauchen')
        verbose_name_plural = _('Wartungszuweisungen Tauchen')
        ordering = ['device', 'service_type']
        unique_together = ['device', 'service_type']

    def __str__(self):
        return f"{self.device.inventory_number} - {self.service_type.name}"

    def get_interval_months(self):
        """Gibt das effektive Intervall zurück (custom oder standard)"""
        return self.custom_interval_months or self.service_type.interval_months


class DivingServiceRecord(models.Model):
    """
    Wartungsprotokoll - Dokumentation einer durchgeführten Wartung
    """

    assignment = models.ForeignKey(
        DivingServiceAssignment,
        on_delete=models.CASCADE,
        related_name='service_records',
        verbose_name=_('Wartungszuweisung')
    )

    # Wartungsdaten
    service_date = models.DateField(
        verbose_name=_('Wartungsdatum')
    )

    technician = models.ForeignKey(
        'personnel.Person',
        on_delete=models.PROTECT,
        related_name='conducted_diving_services',
        verbose_name=_('Techniker')
    )

    # Wartungsergebnis
    RESULT_CHOICES = [
        ('completed', _('Abgeschlossen')),
        ('completed_with_remarks', _('Abgeschlossen mit Anmerkungen')),
        ('incomplete', _('Unvollständig')),
        ('failed', _('Fehlgeschlagen')),
    ]

    result = models.CharField(
        max_length=30,
        choices=RESULT_CHOICES,
        verbose_name=_('Wartungsergebnis')
    )

    # Wartungspunkte Ergebnisse (JSON)
    # Format: {"1": true, "2": false, "3": true}  # ID: bestanden
    checklist_results = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Checklisten-Ergebnisse'),
        help_text=_('Detaillierte Ergebnisse der einzelnen Wartungspunkte')
    )

    # Benutzerdefinierte Feldwerte (JSON)
    # Format: {"Ansprechdruck": "22", "Durchflussrate": "150"}
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

    work_performed = models.TextField(
        blank=True,
        verbose_name=_('Durchgeführte Arbeiten')
    )

    parts_replaced = models.TextField(
        blank=True,
        verbose_name=_('Ersetzte Teile')
    )

    # Nächste Wartung
    next_service_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Nächste Wartung fällig am')
    )

    # Kosten
    labor_hours = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_('Arbeitsstunden')
    )

    parts_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_('Materialkosten (€)')
    )

    # Dokumentation
    service_certificate = models.FileField(
        upload_to='diving/service_certificates/',
        null=True,
        blank=True,
        verbose_name=_('Wartungsprotokoll (PDF)')
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
        verbose_name = _('Wartungsprotokoll Tauchen')
        verbose_name_plural = _('Wartungsprotokolle Tauchen')
        ordering = ['-service_date']

    def __str__(self):
        return f"{self.assignment.device.inventory_number} - {self.assignment.service_type.name} ({self.service_date})"

    def save(self, *args, **kwargs):
        """Aktualisiert die Wartungszuweisung beim Speichern"""
        super().save(*args, **kwargs)

        # Aktualisiere Wartungszuweisung
        if self.result in ['completed', 'completed_with_remarks']:
            self.assignment.last_service_date = self.service_date
            if self.next_service_date:
                self.assignment.next_service_date = self.next_service_date
            self.assignment.save(update_fields=['last_service_date', 'next_service_date', 'updated_at'])


# ============================================================================
# INVENTUR (INVENTORY CHECK) - Diving Equipment
# ============================================================================

class DivingInventoryCheck(models.Model):
    """
    Inventur für Tauchausrüstung
    Basierend auf AbstractInventoryCheck, aber mit tauchspezifischen Feldern
    """

    # Basis-Informationen
    check_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_('Inventur-Nummer'),
        help_text=_('Wird automatisch generiert, z.B. DIV-INV-2025-001')
    )

    title = models.CharField(
        max_length=200,
        verbose_name=_('Titel'),
        help_text=_('z.B. Jahresinventur 2025, Quartalsprüfung Q1')
    )

    description = models.TextField(
        blank=True,
        verbose_name=_('Beschreibung')
    )

    # Typ
    check_type = models.CharField(
        max_length=20,
        choices=InventoryCheckType.choices,
        default=InventoryCheckType.PARTIAL,
        verbose_name=_('Inventurart')
    )

    # Status
    STATUS_CHOICES = [
        ('planned', _('Geplant')),
        ('in_progress', _('In Bearbeitung')),
        ('counting_complete', _('Zählung abgeschlossen')),
        ('completed', _('Abgeschlossen')),
        ('cancelled', _('Abgebrochen')),
    ]

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='planned',
        verbose_name=_('Status')
    )

    # Termine
    scheduled_start_date = models.DateField(
        verbose_name=_('Geplanter Start')
    )

    scheduled_end_date = models.DateField(
        verbose_name=_('Geplantes Ende')
    )

    actual_start_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Tatsächlicher Start')
    )

    actual_end_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Tatsächliches Ende')
    )

    # Verantwortliche
    responsible_person = models.ForeignKey(
        'personnel.Person',
        on_delete=models.PROTECT,
        related_name='responsible_diving_inventory_checks',
        verbose_name=_('Verantwortliche Person')
    )

    team_members = models.ManyToManyField(
        'personnel.Person',
        blank=True,
        related_name='diving_inventory_checks',
        verbose_name=_('Team-Mitglieder')
    )

    # Einschränkungen
    location = models.ForeignKey(
        'locations.Location',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='diving_inventory_checks',
        verbose_name=_('Eingeschränkt auf Lagerort'),
        help_text=_('Leer = alle Lagerorte')
    )

    # Fortschritt
    total_items = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Gesamtanzahl Artikel')
    )

    counted_items = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Gezählte Artikel')
    )

    items_with_discrepancies = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Artikel mit Abweichungen')
    )

    # Diving-spezifische Prüfungen
    check_tuv_inspection = models.BooleanField(
        default=True,
        verbose_name=_('TÜV-Prüfung kontrollieren'),
        help_text=_('Tauchflaschen auf ablaufende TÜV-Prüfungen prüfen')
    )

    check_service_due = models.BooleanField(
        default=True,
        verbose_name=_('Wartungstermine kontrollieren'),
        help_text=_('Atemregler und andere Ausrüstung auf fällige Wartungen prüfen')
    )

    check_condition = models.BooleanField(
        default=True,
        verbose_name=_('Zustand prüfen'),
        help_text=_('Visuellen Zustand der Ausrüstung bewerten')
    )

    check_defects = models.BooleanField(
        default=True,
        verbose_name=_('Mängel erfassen'),
        help_text=_('Defekte und Beschädigungen dokumentieren')
    )

    # Ergebnisse der Diving-spezifischen Prüfungen
    tuv_overdue_found = models.PositiveIntegerField(
        default=0,
        verbose_name=_('TÜV überfällig'),
        help_text=_('Anzahl Flaschen mit überfälliger TÜV-Prüfung')
    )

    service_overdue_found = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Wartung überfällig'),
        help_text=_('Anzahl Ausrüstung mit überfälliger Wartung')
    )

    defective_items_found = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Defekte Ausrüstung'),
        help_text=_('Anzahl defekter oder beschädigter Ausrüstung')
    )

    # Genehmigung
    approved_by = models.ForeignKey(
        'core.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_diving_inventory_checks',
        verbose_name=_('Genehmigt von')
    )

    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Genehmigt am')
    )

    # Notizen
    notes = models.TextField(
        blank=True,
        verbose_name=_('Notizen')
    )

    # Meta
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Erstellt am'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Aktualisiert am'))
    created_by = models.ForeignKey(
        'core.User',
        on_delete=models.PROTECT,
        related_name='created_diving_inventory_checks',
        verbose_name=_('Erstellt von')
    )
    updated_by = models.ForeignKey(
        'core.User',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='updated_diving_inventory_checks',
        verbose_name=_('Aktualisiert von')
    )

    class Meta:
        verbose_name = _('Diving Inventur')
        verbose_name_plural = _('Diving Inventuren')
        ordering = ['-created_at']
        permissions = [
            ('approve_divinginventorycheck', _('Kann Diving-Inventur genehmigen')),
        ]

    def __str__(self):
        return f"{self.check_number} - {self.title}"

    def save(self, *args, **kwargs):
        # Auto-generate check_number if not set
        if not self.check_number:
            from django.utils import timezone
            year = timezone.now().year
            # Finde letzte Nummer für dieses Jahr
            last_check = DivingInventoryCheck.objects.filter(
                check_number__startswith=f'DIV-INV-{year}-'
            ).order_by('-check_number').first()

            if last_check:
                # Extrahiere Nummer
                last_num = int(last_check.check_number.split('-')[-1])
                new_num = last_num + 1
            else:
                new_num = 1

            self.check_number = f'DIV-INV-{year}-{new_num:03d}'

        super().save(*args, **kwargs)

    def get_progress_percentage(self):
        """Berechnet Fortschritt in Prozent"""
        if self.total_items == 0:
            return 0
        return int((self.counted_items / self.total_items) * 100)

    def can_start(self):
        """Prüft ob Inventur gestartet werden kann"""
        return self.status == 'planned'

    def can_complete(self):
        """Prüft ob Inventur abgeschlossen werden kann"""
        return self.status == 'counting_complete'

    def start_counting(self, user):
        """Startet die Zählung"""
        if not self.can_start():
            return False

        from django.utils import timezone
        self.status = 'in_progress'
        self.actual_start_date = timezone.now()
        self.updated_by = user
        self.save()
        return True

    def complete_counting(self, user):
        """Schließt die Zählung ab"""
        if self.status != 'in_progress':
            return False

        from django.utils import timezone
        self.status = 'counting_complete'
        self.actual_end_date = timezone.now()
        self.updated_by = user
        self.save()
        return True

    def approve_and_complete(self, user):
        """Genehmigt und schließt die Inventur ab"""
        if not self.can_complete():
            return False

        from django.utils import timezone
        self.status = 'completed'
        self.approved_by = user
        self.approved_at = timezone.now()
        self.updated_by = user
        self.save()
        return True

    def update_progress(self):
        """Aktualisiert Fortschritts-Statistiken"""
        from django.utils import timezone

        self.total_items = self.items.count()
        self.counted_items = self.items.filter(is_counted=True).count()
        self.items_with_discrepancies = self.items.filter(has_discrepancy=True).count()

        # Zähle defekte Ausrüstung
        self.defective_items_found = self.items.filter(is_defective=True).count()

        # Zähle überfällige TÜV-Prüfungen
        if self.check_tuv_inspection:
            self.tuv_overdue_found = self.items.filter(
                tuv_overdue=True
            ).count()

        # Zähle überfällige Wartungen
        if self.check_service_due:
            self.service_overdue_found = self.items.filter(
                service_overdue=True
            ).count()

        self.save(update_fields=[
            'total_items',
            'counted_items',
            'items_with_discrepancies',
            'defective_items_found',
            'tuv_overdue_found',
            'service_overdue_found'
        ])


class DivingInventoryCheckItem(models.Model):
    """
    Einzelner Artikel in einer Diving-Inventur
    Analog zu ITHardwareInventoryCheckItem, aber für Tauchausrüstung
    """

    # Verknüpfung zur Inventur
    inventory_check = models.ForeignKey(
        DivingInventoryCheck,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_('Inventur')
    )

    # Verknüpfung zur Tauchausrüstung
    diving_device = models.ForeignKey(
        'DivingDeviceInstance',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='inventory_items',
        verbose_name=_('Tauchgerät')
    )

    # Artikel-Informationen
    item_name = models.CharField(
        max_length=200,
        verbose_name=_('Artikelbezeichnung')
    )

    item_number = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Artikelnummer')
    )

    inventory_number = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Inventarnummer')
    )

    serial_number = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Seriennummer')
    )

    # Lagerort
    location = models.ForeignKey(
        'locations.Location',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='diving_inventory_items',
        verbose_name=_('Lagerort')
    )

    # Zählung
    expected_quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=1,
        verbose_name=_('Soll-Menge')
    )

    actual_quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_('Ist-Menge')
    )

    variance_quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name=_('Differenz')
    )

    is_counted = models.BooleanField(
        default=False,
        verbose_name=_('Gezählt')
    )

    has_discrepancy = models.BooleanField(
        default=False,
        verbose_name=_('Abweichung vorhanden')
    )

    counted_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Gezählt am')
    )

    counted_by = models.ForeignKey(
        'personnel.Person',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='counted_diving_items',
        verbose_name=_('Gezählt von')
    )

    # Diving-spezifische Felder
    item_type = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_('Ausrüstungstyp')
    )

    # TÜV & Wartung
    next_tuv_inspection = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Nächste TÜV-Prüfung')
    )

    tuv_overdue = models.BooleanField(
        default=False,
        verbose_name=_('TÜV überfällig')
    )

    next_service_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Nächste Wartung')
    )

    service_overdue = models.BooleanField(
        default=False,
        verbose_name=_('Wartung überfällig')
    )

    # Zustand
    condition = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_('Zustand')
    )

    is_operational = models.BooleanField(
        default=True,
        verbose_name=_('Einsatzbereit')
    )

    is_defective = models.BooleanField(
        default=False,
        verbose_name=_('Defekt')
    )

    defects_description = models.TextField(
        blank=True,
        verbose_name=_('Mängelbeschreibung')
    )

    # Zuordnung
    assigned_to_name = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Zugeordnet an')
    )

    assigned_vehicle_name = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Zugeordnetes Fahrzeug')
    )

    # Notizen
    notes = models.TextField(
        blank=True,
        verbose_name=_('Notizen')
    )

    class Meta:
        verbose_name = _('Diving Inventur-Position')
        verbose_name_plural = _('Diving Inventur-Positionen')
        ordering = ['item_name', 'inventory_number']

    def __str__(self):
        return f"{self.item_name} ({self.inventory_number or 'ohne INV-Nr'})"

    def get_discrepancy(self):
        """Berechnet Abweichung"""
        if self.actual_quantity is None:
            return 0
        return self.actual_quantity - self.expected_quantity

    def update_variance(self):
        """Aktualisiert Differenz und Abweichungs-Flag"""
        if self.actual_quantity is not None:
            self.variance_quantity = self.get_discrepancy()
            self.has_discrepancy = (self.variance_quantity != 0)
        else:
            self.variance_quantity = 0
            self.has_discrepancy = False
