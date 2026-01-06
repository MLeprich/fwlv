"""
Workshop Models
Datenmodelle für KFZ-Werkstatt
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from decimal import Decimal

from inventory_base.models import (
    AbstractInventoryItem,
    AbstractStockMovement,
    StockMovementType,
    InventoryCheckType,
)


# ============================================================================
# TYPE MANAGEMENT (Werkzeug-/Artikeltypen)
# ============================================================================

class WorkshopToolType(models.Model):
    """
    Verwaltbare Werkzeug-/Artikeltypen für Werkstatt
    Ersetzt die fest kodierten WorkshopItemType Choices
    """
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_('Werkzeug-/Artikeltyp'),
        help_text=_('z.B. Drehmomentschlüssel, Diagnosegerät, Motoröl')
    )

    code = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_('Code'),
        help_text=_('Eindeutiger Code, z.B. torque_wrench, diagnostic_tool')
    )

    description = models.TextField(
        blank=True,
        verbose_name=_('Beschreibung')
    )

    category = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_('Kategorie'),
        help_text=_('z.B. Werkzeug, Betriebsstoffe, Verschleißteile')
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
        related_name='created_workshop_tool_types',
        verbose_name=_('Erstellt von')
    )

    class Meta:
        verbose_name = _('Werkzeug-/Artikeltyp')
        verbose_name_plural = _('Werkzeug-/Artikeltypen')
        ordering = ['category', 'sort_order', 'name']

    def __str__(self):
        return self.name


# ============================================================================
# STAMMDATEN-VERWALTUNG (MASTER DATA)
# ============================================================================

class WorkshopItemMaster(models.Model):
    """
    Werkstatt-Artikel-Stammdaten - Produktdefinition ohne Lagerort

    Diese Tabelle enthält die Produktdefinitionen (z.B. "Diagnosegerät Bosch KTS 560")
    mit allen technischen Spezifikationen, Zertifizierungen und Herstellerinformationen.
    """

    # Identifikation
    master_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_('Stammdatennummer'),
        help_text=_('Eindeutige Nummer für dieses Produkt, z.B. WRK-2025-001')
    )

    name = models.CharField(
        max_length=200,
        verbose_name=_('Produktname'),
        help_text=_('z.B. Diagnosegerät Bosch KTS 560')
    )

    description = models.TextField(
        blank=True,
        verbose_name=_('Beschreibung'),
        help_text=_('Detaillierte Produktbeschreibung')
    )

    item_type = models.ForeignKey(
        'WorkshopToolType',
        on_delete=models.PROTECT,
        related_name='masters',
        verbose_name=_('Werkzeug-/Artikeltyp'),
        help_text=_('Wählen Sie den Typ aus der Typenverwaltung')
    )

    # Hersteller
    manufacturer = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Hersteller'),
        help_text=_('z.B. Bosch, Hazet, Stahlwille')
    )

    model = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Modell'),
        help_text=_('z.B. KTS 560, Drehmomentschlüssel 6123-1')
    )

    # Technische Spezifikationen - Werkzeuge
    tool_size = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Werkzeuggröße'),
        help_text=_('z.B. 10-13mm, 1/2 Zoll, M6-M24')
    )

    torque_range_nm = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Drehmomentbereich (Nm)'),
        help_text=_('z.B. 10-210 Nm für Drehmomentschlüssel')
    )

    max_load_kg = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Max. Tragkraft (kg)'),
        help_text=_('Für Wagenheber, Unterstellböcke')
    )

    # Technische Spezifikationen - Betriebsstoffe
    viscosity = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_('Viskosität'),
        help_text=_('z.B. 5W-30, 10W-40 für Öle')
    )

    specification_standard = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Spezifikation/Norm'),
        help_text=_('z.B. API SN/CF, ACEA C3, DIN 51524')
    )

    volume_content = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Inhalt/Volumen'),
        help_text=_('z.B. 5L, 20L, 200L für Betriebsstoffe')
    )

    # Gefahrstoff-Eigenschaften
    is_hazardous = models.BooleanField(
        default=False,
        verbose_name=_('Gefahrstoff'),
        help_text=_('Kennzeichnung als Gefahrstoff (z.B. brennbar, ätzend)')
    )

    hazard_symbols = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Gefahrensymbole'),
        help_text=_('z.B. GHS02 (Flamme), GHS07 (Ausrufezeichen)')
    )

    # Lagerung
    shelf_life_months = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Haltbarkeit (Monate)'),
        help_text=_('Maximale Lagerdauer in Monaten')
    )

    storage_temperature_min = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        null=True,
        blank=True,
        verbose_name=_('Min. Lagertemperatur (°C)')
    )

    storage_temperature_max = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        null=True,
        blank=True,
        verbose_name=_('Max. Lagertemperatur (°C)')
    )

    # Kalibrierung & Wartung (für Werkzeuge)
    requires_calibration = models.BooleanField(
        default=False,
        verbose_name=_('Kalibrierung erforderlich'),
        help_text=_('z.B. für Drehmomentschlüssel, Diagnosegeräte')
    )

    calibration_interval_months = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Kalibrierungsintervall (Monate)'),
        help_text=_('Drehmomentschlüssel: 12 Monate')
    )

    service_interval_months = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Wartungsintervall (Monate)')
    )

    # Lebenszyklus
    max_service_life_years = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Max. Nutzungsdauer (Jahre)'),
        help_text=_('Maximale Nutzungsdauer laut Hersteller')
    )

    # Fahrzeugkompatibilität
    compatible_vehicle_types = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_('Kompatible Fahrzeugtypen'),
        help_text=_('Liste der Fahrzeugtypen, z.B. ["PKW", "LKW", "Anhänger"]')
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
    safety_data_sheet = models.FileField(
        upload_to='workshop/masters/sds/',
        blank=True,
        null=True,
        verbose_name=_('Sicherheitsdatenblatt'),
        help_text=_('SDB für Gefahrstoffe')
    )

    manual_document = models.FileField(
        upload_to='workshop/masters/manuals/',
        blank=True,
        null=True,
        verbose_name=_('Bedienungsanleitung')
    )

    image = models.ImageField(
        upload_to='workshop/masters/images/',
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
        related_name='created_workshop_masters',
        verbose_name=_('Erstellt von')
    )

    class Meta:
        verbose_name = _('Werkstatt-Artikel-Stammdaten')
        verbose_name_plural = _('Werkstatt-Artikel-Stammdaten')
        ordering = ['master_number', 'name']
        indexes = [
            models.Index(fields=['master_number']),
            models.Index(fields=['item_type']),
            models.Index(fields=['manufacturer']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.master_number} - {self.name}"

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('workshop:master_detail', kwargs={'pk': self.pk})


class WorkshopToolInstance(models.Model):
    """
    Werkzeug-Instanz mit individueller Inventarnummer

    Jedes physische Werkzeug (z.B. ein spezifischer Diagnosegerät mit Seriennummer)
    wird hier als Instanz erfasst und mit den Stammdaten verknüpft.
    """

    # Verknüpfung zu Stammdaten
    master = models.ForeignKey(
        WorkshopItemMaster,
        on_delete=models.PROTECT,
        related_name='tool_instances',
        verbose_name=_('Stammdaten')
    )

    # Eindeutige Identifikation
    inventory_number = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_('Inventarnummer'),
        help_text=_('Eindeutige Inventarnummer, z.B. WRK-DG-001')
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
        related_name='workshop_tools',
        verbose_name=_('Lagerort')
    )

    # Herstellung & Inbetriebnahme
    manufacturing_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Herstellungsdatum')
    )

    purchase_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Kaufdatum')
    )

    first_use_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Erstinbetriebnahme')
    )

    # Kalibrierung (für Mess- und Prüfgeräte)
    last_calibration_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Letzte Kalibrierung')
    )

    next_calibration_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Nächste Kalibrierung'),
        help_text=_('Drehmomentschlüssel: jährlich')
    )

    calibration_certificate_number = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Kalibrierschein-Nr.')
    )

    calibration_status = models.CharField(
        max_length=20,
        choices=[
            ('not_required', _('Nicht erforderlich')),
            ('valid', _('Gültig')),
            ('due_soon', _('Demnächst fällig')),
            ('overdue', _('Überfällig')),
        ],
        default='not_required',
        verbose_name=_('Kalibrierstatus')
    )

    calibration_certificate = models.FileField(
        upload_to='workshop/tools/calibration/',
        blank=True,
        verbose_name=_('Kalibrierschein')
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
        related_name='serviced_workshop_tools',
        verbose_name=_('Letzter Servicetechniker')
    )

    service_log = models.FileField(
        upload_to='workshop/tools/service_logs/',
        blank=True,
        verbose_name=_('Wartungsprotokoll')
    )

    # Nutzung & Einsatz
    total_usage_hours = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name=_('Betriebsstunden'),
        help_text=_('Für elektrische Geräte')
    )

    usage_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Anzahl Einsätze')
    )

    last_use_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Letzter Einsatz')
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
        help_text=_('Kann das Werkzeug verwendet werden?')
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
        related_name='workshop_tools',
        verbose_name=_('Zugeordnetes Fahrzeug')
    )

    assigned_to = models.ForeignKey(
        'personnel.Person',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_workshop_tools',
        verbose_name=_('Zugeordnet an Person')
    )

    # Kosten
    purchase_price_actual = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_('Tatsächlicher Kaufpreis'),
        help_text=_('Einkaufspreis dieser spezifischen Instanz')
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
        upload_to='workshop/tools/qr_codes/',
        blank=True,
        null=True,
        verbose_name=_('QR-Code')
    )

    barcode = models.ImageField(
        upload_to='workshop/tools/barcodes/',
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
        related_name='created_workshop_tools',
        verbose_name=_('Erstellt von')
    )

    class Meta:
        verbose_name = _('Werkzeug-Instanz')
        verbose_name_plural = _('Werkzeug-Instanzen')
        ordering = ['inventory_number']
        indexes = [
            models.Index(fields=['inventory_number']),
            models.Index(fields=['serial_number']),
            models.Index(fields=['master']),
            models.Index(fields=['location']),
            models.Index(fields=['next_calibration_date']),
            models.Index(fields=['next_service_date']),
            models.Index(fields=['calibration_status']),
            models.Index(fields=['is_operational']),
            models.Index(fields=['assigned_vehicle']),
            models.Index(fields=['assigned_to']),
        ]

    def __str__(self):
        return f"{self.inventory_number} - {self.master.name}"

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('workshop:tool_detail', kwargs={'pk': self.pk})

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
        """Generiert QR-Code für das Werkzeug"""
        import qrcode
        from io import BytesIO
        from django.core.files import File

        # Nur URL kodieren für maximale Scanner-Kompatibilität
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(f"/workshop/tool/{self.pk}/")
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')

        self.qr_code.save(
            f'workshop_qr_{self.inventory_number}.png',
            File(buffer),
            save=False
        )
        self.save(update_fields=['qr_code'])

    def generate_barcode(self):
        """Generiert Barcode für das Werkzeug"""
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
            f'workshop_barcode_{self.inventory_number}.png',
            File(buffer),
            save=False
        )
        self.save(update_fields=['barcode'])

    def is_calibration_due(self):
        """Prüft ob Kalibrierung fällig ist"""
        from datetime import date
        if not self.next_calibration_date:
            return False
        return self.next_calibration_date <= date.today()

    def is_calibration_due_soon(self, days=30):
        """Prüft ob Kalibrierung bald fällig ist"""
        from datetime import date, timedelta
        if not self.next_calibration_date:
            return False
        return self.next_calibration_date <= date.today() + timedelta(days=days)

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

# CHOICE CLASSES

class WorkshopItemType(models.TextChoices):
    """Werkstatt-Artikel-Typen"""
    # Betriebsstoffe
    ENGINE_OIL = 'engine_oil', _('Motoröl')
    TRANSMISSION_OIL = 'transmission_oil', _('Getriebeöl')
    HYDRAULIC_OIL = 'hydraulic_oil', _('Hydrauliköl')
    BRAKE_FLUID = 'brake_fluid', _('Bremsflüssigkeit')
    COOLANT = 'coolant', _('Kühlflüssigkeit')
    ANTIFREEZE = 'antifreeze', _('Frostschutzmittel')
    WINDSHIELD_WASHER = 'windshield_washer', _('Scheibenwaschmittel')
    GREASE = 'grease', _('Schmierfett')
    DIESEL_FUEL = 'diesel_fuel', _('Diesel')
    GASOLINE = 'gasoline', _('Benzin')
    ADBLUE = 'adblue', _('AdBlue')

    # Verschleißteile
    OIL_FILTER = 'oil_filter', _('Ölfilter')
    AIR_FILTER = 'air_filter', _('Luftfilter')
    FUEL_FILTER = 'fuel_filter', _('Kraftstofffilter')
    CABIN_FILTER = 'cabin_filter', _('Innenraumfilter')
    BRAKE_PADS = 'brake_pads', _('Bremsbeläge')
    BRAKE_DISCS = 'brake_discs', _('Bremsscheiben')
    SPARK_PLUGS = 'spark_plugs', _('Zündkerzen')
    GLOW_PLUGS = 'glow_plugs', _('Glühkerzen')
    DRIVE_BELT = 'drive_belt', _('Keilriemen')
    TIMING_BELT = 'timing_belt', _('Zahnriemen')
    WIPER_BLADES = 'wiper_blades', _('Scheibenwischerblätter')

    # Reifen & Räder
    TIRE_SUMMER = 'tire_summer', _('Sommerreifen')
    TIRE_WINTER = 'tire_winter', _('Winterreifen')
    TIRE_ALLSEASON = 'tire_allseason', _('Ganzjahresreifen')
    WHEEL_RIM = 'wheel_rim', _('Felge')
    WHEEL_NUT = 'wheel_nut', _('Radmutter')
    VALVE_CAP = 'valve_cap', _('Ventilkappe')

    # Beleuchtung
    HEADLIGHT_BULB = 'headlight_bulb', _('Scheinwerferbirne')
    TAIL_LIGHT_BULB = 'tail_light_bulb', _('Rücklichtbirne')
    TURN_SIGNAL_BULB = 'turn_signal_bulb', _('Blinkerbirne')
    LED_UNIT = 'led_unit', _('LED-Einheit')

    # Batterie & Elektrik
    BATTERY = 'battery', _('Batterie')
    ALTERNATOR = 'alternator', _('Lichtmaschine')
    STARTER_MOTOR = 'starter_motor', _('Anlasser')
    FUSE = 'fuse', _('Sicherung')
    RELAY = 'relay', _('Relais')
    CABLE = 'cable', _('Kabel')

    # Karosserie & Lack
    PAINT = 'paint', _('Lack')
    PRIMER = 'primer', _('Grundierung')
    CLEAR_COAT = 'clear_coat', _('Klarlack')
    BODY_FILLER = 'body_filler', _('Spachtelmasse')
    RUST_PROTECTION = 'rust_protection', _('Rostschutz')

    # Werkzeug & Hilfsmittel
    WRENCH = 'wrench', _('Schraubenschlüssel')
    SOCKET_SET = 'socket_set', _('Steckschlüsselsatz')
    TORQUE_WRENCH = 'torque_wrench', _('Drehmomentschlüssel')
    JACK = 'jack', _('Wagenheber')
    JACK_STAND = 'jack_stand', _('Unterstellbock')
    DIAGNOSTIC_TOOL = 'diagnostic_tool', _('Diagnosegerät')
    MULTIMETER = 'multimeter', _('Multimeter')
    COMPRESSOR = 'compressor', _('Kompressor')
    GRINDER = 'grinder', _('Schleifgerät')
    DRILL = 'drill', _('Bohrmaschine')

    # Reinigungs- & Pflegemittel
    CAR_WASH = 'car_wash', _('Autowaschmittel')
    CAR_WAX = 'car_wax', _('Autowachs')
    POLISH = 'polish', _('Politur')
    DEGREASER = 'degreaser', _('Entfetter')
    BRAKE_CLEANER = 'brake_cleaner', _('Bremsenreiniger')
    GLASS_CLEANER = 'glass_cleaner', _('Glasreiniger')
    INTERIOR_CLEANER = 'interior_cleaner', _('Innenraumreiniger')

    # Sonstiges
    SEALANT = 'sealant', _('Dichtmittel')
    ADHESIVE = 'adhesive', _('Klebstoff')
    LUBRICANT_SPRAY = 'lubricant_spray', _('Schmierspray')
    RUST_REMOVER = 'rust_remover', _('Rostlöser')
    SHOP_TOWELS = 'shop_towels', _('Werkstatttücher')
    GLOVES = 'gloves', _('Handschuhe')
    SAFETY_GLASSES = 'safety_glasses', _('Schutzbrille')
    EAR_PROTECTION = 'ear_protection', _('Gehörschutz')
    OTHER = 'other', _('Sonstiges')


class WorkshopItemStatus(models.TextChoices):
    """Werkstatt-Artikel Status"""
    IN_STOCK = 'in_stock', _('Auf Lager')
    LOW_STOCK = 'low_stock', _('Niedriger Bestand')
    OUT_OF_STOCK = 'out_of_stock', _('Nicht vorrätig')
    ON_ORDER = 'on_order', _('Bestellt')
    RESERVED = 'reserved', _('Reserviert')
    EXPIRED = 'expired', _('Abgelaufen')
    DEFECTIVE = 'defective', _('Defekt')


class VehicleServiceType(models.TextChoices):
    """Fahrzeug-Service-Typen"""
    OIL_CHANGE = 'oil_change', _('Ölwechsel')
    INSPECTION = 'inspection', _('Inspektion')
    MAIN_INSPECTION = 'main_inspection', _('Hauptuntersuchung (HU)')
    EMISSION_TEST = 'emission_test', _('Abgasuntersuchung (AU)')
    TIRE_CHANGE = 'tire_change', _('Reifenwechsel')
    BRAKE_SERVICE = 'brake_service', _('Bremsenwartung')
    BATTERY_REPLACEMENT = 'battery_replacement', _('Batteriewechsel')
    FILTER_REPLACEMENT = 'filter_replacement', _('Filterwechsel')
    BELT_REPLACEMENT = 'belt_replacement', _('Riemenwechsel')
    REPAIR = 'repair', _('Reparatur')
    BODYWORK = 'bodywork', _('Karosseriearbeiten')
    PAINT_WORK = 'paint_work', _('Lackierung')
    WASHING = 'washing', _('Fahrzeugwäsche')
    CLEANING = 'cleaning', _('Innenreinigung')
    OTHER = 'other', _('Sonstiges')


class ServiceStatus(models.TextChoices):
    """Service-Status"""
    SCHEDULED = 'scheduled', _('Geplant')
    IN_PROGRESS = 'in_progress', _('In Bearbeitung')
    WAITING_PARTS = 'waiting_parts', _('Wartet auf Teile')
    WAITING_APPROVAL = 'waiting_approval', _('Wartet auf Freigabe')
    COMPLETED = 'completed', _('Abgeschlossen')
    CANCELLED = 'cancelled', _('Storniert')


# ============================================================================
# WORKSHOP ITEM MODEL
# ============================================================================

class WorkshopItem(AbstractInventoryItem):
    """
    Werkstatt-Artikel (Ersatzteile, Betriebsstoffe, Werkzeuge)
    Erweitert AbstractInventoryItem um werkstattspezifische Felder
    """

    # Typ & Status
    workshop_item_type = models.CharField(
        max_length=50,
        choices=WorkshopItemType.choices,
        verbose_name=_('Werkstatt-Artikel-Typ')
    )

    workshop_status = models.CharField(
        max_length=20,
        choices=WorkshopItemStatus.choices,
        default=WorkshopItemStatus.IN_STOCK,
        verbose_name=_('Werkstatt-Status')
    )

    # Fahrzeug-Zuordnung
    compatible_vehicles = models.ManyToManyField(
        'vehicles.Vehicle',
        related_name='compatible_workshop_items',
        blank=True,
        verbose_name=_('Kompatible Fahrzeuge'),
        help_text=_('Fahrzeuge, für die dieses Teil verwendet werden kann')
    )

    # Spezifikationen
    manufacturer_part_number = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Herstellerteilenummer')
    )

    oem_number = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('OEM-Nummer'),
        help_text=_('Original Equipment Manufacturer Nummer')
    )

    viscosity = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_('Viskosität'),
        help_text=_('z.B. 5W-30 für Motoröl')
    )

    specification = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Spezifikation'),
        help_text=_('z.B. API SN/CF, ACEA C3')
    )

    # Lagerung
    shelf_life_months = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Haltbarkeit (Monate)'),
        help_text=_('Maximale Lagerdauer in Monaten')
    )

    production_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Produktionsdatum')
    )

    storage_temperature_min = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        null=True,
        blank=True,
        verbose_name=_('Min. Lagertemperatur (°C)')
    )

    storage_temperature_max = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        null=True,
        blank=True,
        verbose_name=_('Max. Lagertemperatur (°C)')
    )

    # Gefahrstoff
    is_hazardous = models.BooleanField(
        default=False,
        verbose_name=_('Gefahrstoff'),
        help_text=_('Kennzeichnung als Gefahrstoff (z.B. brennbar, ätzend)')
    )

    hazard_symbols = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Gefahrensymbole'),
        help_text=_('z.B. GHS02 (Flamme), GHS07 (Ausrufezeichen)')
    )

    safety_data_sheet = models.FileField(
        upload_to='workshop/sds/',
        null=True,
        blank=True,
        verbose_name=_('Sicherheitsdatenblatt (SDB)')
    )

    # Wartungsintervall-Empfehlung
    recommended_change_interval_km = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Wechselintervall (km)'),
        help_text=_('Empfohlenes Wechselintervall in Kilometern')
    )

    recommended_change_interval_months = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Wechselintervall (Monate)'),
        help_text=_('Empfohlenes Wechselintervall in Monaten')
    )

    # Kosten
    core_charge = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name=_('Pfand'),
        help_text=_('Pfandbetrag für Altteilrückgabe')
    )

    class Meta:
        verbose_name = _('Werkstatt-Artikel')
        verbose_name_plural = _('Werkstatt-Artikel')
        ordering = ['workshop_item_type', 'name']
        indexes = [
            models.Index(fields=['workshop_item_type']),
            models.Index(fields=['workshop_status']),
            models.Index(fields=['manufacturer_part_number']),
            models.Index(fields=['oem_number']),
            models.Index(fields=['is_hazardous']),
        ]

    def __str__(self):
        return f"{self.item_number} - {self.name} ({self.get_workshop_item_type_display()})"

    def is_expired(self):
        """Prüft, ob Artikel abgelaufen ist (berechnet aus production_date + shelf_life_months)"""
        if not self.production_date or not self.shelf_life_months:
            return False
        from django.utils import timezone
        from dateutil.relativedelta import relativedelta
        expiry_date = self.production_date + relativedelta(months=self.shelf_life_months)
        return expiry_date <= timezone.now().date()

    def is_low_stock(self):
        """Prüft, ob Mindestbestand unterschritten"""
        if self.min_quantity is None:
            return False
        return self.quantity <= self.min_quantity

    def generate_qr_code(self):
        """
        Generiert QR-Code als SVG für den Werkstatt-Artikel
        Enthält nur die URL für direkten Zugriff
        """
        import qrcode
        import qrcode.image.svg
        from io import BytesIO

        # Nur URL kodieren für maximale Scanner-Kompatibilität
        qr_string = f'/workshop/item/{self.pk}/'

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_string)
        qr.make(fit=True)

        factory = qrcode.image.svg.SvgPathImage
        svg_img = qr.make_image(image_factory=factory)

        stream = BytesIO()
        svg_img.save(stream)
        svg_string = stream.getvalue().decode('utf-8')

        return svg_string

    def generate_barcode(self):
        """
        Generiert Barcode als SVG für die Artikelnummer
        """
        import barcode
        from barcode.writer import SVGWriter
        from io import BytesIO

        code128 = barcode.get_barcode_class('code128')

        rv = BytesIO()
        code = code128(self.item_number, writer=SVGWriter())
        code.write(rv)

        svg_string = rv.getvalue().decode('utf-8')
        return svg_string


# ============================================================================
# WORKSHOP STOCK MOVEMENT MODEL
# ============================================================================

class WorkshopStockMovement(AbstractStockMovement):
    """
    Werkstatt-Lagerbewegung
    Erweitert AbstractStockMovement um werkstattspezifische Felder
    """

    item = models.ForeignKey(
        WorkshopItem,
        on_delete=models.PROTECT,
        related_name='stock_movements',
        verbose_name=_('Werkstatt-Artikel')
    )

    # Fahrzeug-Bezug
    vehicle = models.ForeignKey(
        'vehicles.Vehicle',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='workshop_movements',
        verbose_name=_('Fahrzeug'),
        help_text=_('Fahrzeug, für das der Artikel verwendet wurde')
    )

    service_record = models.ForeignKey(
        'VehicleServiceRecord',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='used_items',
        verbose_name=_('Serviceeintrag'),
        help_text=_('Zugehöriger Fahrzeug-Serviceeintrag')
    )

    # Kilometerstand bei Verwendung
    vehicle_mileage = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Kilometerstand'),
        help_text=_('Kilometerstand des Fahrzeugs bei Verwendung')
    )

    # Chargen- & Verfallsdatum
    batch_number = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Chargen-/Batch-Nummer')
    )

    expiry_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Verfallsdatum')
    )

    # Pfandrückgabe
    core_returned = models.BooleanField(
        default=False,
        verbose_name=_('Pfand zurückgegeben'),
        help_text=_('Altteil wurde zurückgegeben')
    )

    core_return_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Pfand-Rückgabedatum')
    )

    # Kosten
    unit_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name=_('Stückkosten (EUR)')
    )

    total_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
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
        verbose_name = _('Werkstatt-Lagerbewegung')
        verbose_name_plural = _('Werkstatt-Lagerbewegungen')
        ordering = ['-movement_date', '-created_at']
        indexes = [
            models.Index(fields=['item', 'movement_date']),
            models.Index(fields=['vehicle', 'movement_date']),
            models.Index(fields=['service_record']),
            models.Index(fields=['movement_type', 'movement_date']),
        ]

    def __str__(self):
        return f"{self.get_movement_type_display()} - {self.item.name} ({self.movement_date})"

    def save(self, *args, **kwargs):
        # Kosten berechnen
        if self.unit_cost and not self.total_cost:
            self.total_cost = self.unit_cost * self.quantity

        super().save(*args, **kwargs)

        # Bestand aktualisieren
        self.update_item_stock()


# ============================================================================
# VEHICLE SERVICE RECORD MODEL
# ============================================================================

class VehicleServiceRecord(models.Model):
    """
    Fahrzeug-Serviceeintrag
    Dokumentiert alle Wartungs- und Reparaturarbeiten
    """

    # Basis-Info
    vehicle = models.ForeignKey(
        'vehicles.Vehicle',
        on_delete=models.PROTECT,
        related_name='service_records',
        verbose_name=_('Fahrzeug')
    )

    service_type = models.CharField(
        max_length=30,
        choices=VehicleServiceType.choices,
        verbose_name=_('Service-Typ')
    )

    service_status = models.CharField(
        max_length=20,
        choices=ServiceStatus.choices,
        default=ServiceStatus.SCHEDULED,
        verbose_name=_('Status')
    )

    # Zeitplanung
    scheduled_date = models.DateField(
        verbose_name=_('Geplantes Datum')
    )

    started_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Beginn')
    )

    completed_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Abschluss')
    )

    # Fahrzeugdaten
    mileage_at_service = models.PositiveIntegerField(
        verbose_name=_('Kilometerstand'),
        help_text=_('Kilometerstand bei Service-Beginn')
    )

    operating_hours_at_service = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Betriebsstunden'),
        help_text=_('Betriebsstunden bei Service-Beginn')
    )

    # Arbeit
    description = models.TextField(
        verbose_name=_('Beschreibung'),
        help_text=_('Detaillierte Beschreibung der durchgeführten Arbeiten')
    )

    technician = models.ForeignKey(
        'personnel.Person',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='performed_services',
        verbose_name=_('Mechaniker/Techniker')
    )

    labor_hours = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name=_('Arbeitsstunden')
    )

    # Kosten
    labor_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name=_('Arbeitskosten')
    )

    parts_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name=_('Teilekosten'),
        help_text=_('Wird automatisch aus verwendeten Artikeln berechnet')
    )

    external_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name=_('Externe Kosten'),
        help_text=_('z.B. Fremdwerkstatt, TÜV-Gebühren')
    )

    total_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name=_('Gesamtkosten')
    )

    # Freigabe & QS
    approved_by = models.ForeignKey(
        'core.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_services',
        verbose_name=_('Freigegeben von')
    )

    approval_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Freigabedatum')
    )

    # Dokumentation
    invoice_number = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_('Rechnungsnummer')
    )

    invoice_file = models.FileField(
        upload_to='workshop/invoices/',
        null=True,
        blank=True,
        verbose_name=_('Rechnung')
    )

    photos = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_('Fotos'),
        help_text=_('Liste von Foto-URLs der Arbeiten')
    )

    notes = models.TextField(
        blank=True,
        verbose_name=_('Notizen')
    )

    # Audit-Felder
    created_by = models.ForeignKey(
        'core.User',
        on_delete=models.PROTECT,
        related_name='created_service_records',
        verbose_name=_('Erstellt von')
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Erstellt am')
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Aktualisiert am')
    )

    class Meta:
        verbose_name = _('Fahrzeug-Serviceeintrag')
        verbose_name_plural = _('Fahrzeug-Serviceeinträge')
        ordering = ['-scheduled_date', '-created_at']
        indexes = [
            models.Index(fields=['vehicle', 'scheduled_date']),
            models.Index(fields=['service_type', 'service_status']),
            models.Index(fields=['technician', 'scheduled_date']),
            models.Index(fields=['service_status', 'scheduled_date']),
        ]

    def __str__(self):
        return f"{self.vehicle} - {self.get_service_type_display()} ({self.scheduled_date})"

    def save(self, *args, **kwargs):
        # Gesamtkosten berechnen
        self.total_cost = self.labor_cost + self.parts_cost + self.external_cost
        super().save(*args, **kwargs)

    def calculate_parts_cost(self):
        """Berechnet Teilekosten aus verwendeten Artikeln"""
        from django.db.models import Sum
        parts_total = self.used_items.aggregate(
            total=Sum('total_cost')
        )['total'] or Decimal('0.00')

        self.parts_cost = parts_total
        self.save(update_fields=['parts_cost', 'total_cost'])

        return self.parts_cost

    def is_overdue(self):
        """Prüft, ob Service überfällig ist"""
        if self.service_status in [ServiceStatus.COMPLETED, ServiceStatus.CANCELLED]:
            return False

        from django.utils import timezone
        return self.scheduled_date < timezone.now().date()


# ============================================================================
# INVENTUR (INVENTORY CHECK) - Workshop
# ============================================================================

class WorkshopInventoryCheck(models.Model):
    """
    Inventur für KFZ-Werkstatt Werkzeuge und Material
    """

    # Basis-Informationen
    check_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_('Inventur-Nummer'),
        help_text=_('Wird automatisch generiert, z.B. WS-INV-2025-001')
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
        related_name='responsible_workshop_inventory_checks',
        verbose_name=_('Verantwortliche Person')
    )

    team_members = models.ManyToManyField(
        'personnel.Person',
        blank=True,
        related_name='workshop_inventory_checks',
        verbose_name=_('Team-Mitglieder')
    )

    # Einschränkungen
    location = models.ForeignKey(
        'locations.Location',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='workshop_inventory_checks',
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

    # Workshop-spezifische Prüfungen
    check_tool_condition = models.BooleanField(
        default=True,
        verbose_name=_('Werkzeugzustand prüfen'),
        help_text=_('Verschleiß und Beschädigungen kontrollieren')
    )

    check_calibration = models.BooleanField(
        default=True,
        verbose_name=_('Kalibrierung prüfen'),
        help_text=_('Messgeräte auf fällige Kalibrierungen prüfen')
    )

    check_safety_equipment = models.BooleanField(
        default=True,
        verbose_name=_('Sicherheitsausrüstung prüfen'),
        help_text=_('PSA und Sicherheitswerkzeuge kontrollieren')
    )

    # Ergebnisse der Workshop-spezifischen Prüfungen
    damaged_tools_found = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Beschädigte Werkzeuge'),
        help_text=_('Anzahl beschädigter oder verschlissener Werkzeuge')
    )

    calibration_due_found = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Kalibrierung fällig'),
        help_text=_('Anzahl Messgeräte mit fälliger Kalibrierung')
    )

    safety_issues_found = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Sicherheitsprobleme'),
        help_text=_('Anzahl sicherheitsrelevanter Mängel')
    )

    # Genehmigung
    approved_by = models.ForeignKey(
        'core.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_workshop_inventory_checks',
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
        related_name='created_workshop_inventory_checks',
        verbose_name=_('Erstellt von')
    )
    updated_by = models.ForeignKey(
        'core.User',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='updated_workshop_inventory_checks',
        verbose_name=_('Aktualisiert von')
    )

    class Meta:
        verbose_name = _('Workshop Inventur')
        verbose_name_plural = _('Workshop Inventuren')
        ordering = ['-created_at']
        permissions = [
            ('approve_workshopinventorycheck', _('Kann Workshop-Inventur genehmigen')),
        ]

    def __str__(self):
        return f"{self.check_number} - {self.title}"

    def save(self, *args, **kwargs):
        # Auto-generate check_number if not set
        if not self.check_number:
            from django.utils import timezone
            year = timezone.now().year
            # Finde letzte Nummer für dieses Jahr
            last_check = WorkshopInventoryCheck.objects.filter(
                check_number__startswith=f'WS-INV-{year}-'
            ).order_by('-check_number').first()

            if last_check:
                # Extrahiere Nummer
                last_num = int(last_check.check_number.split('-')[-1])
                new_num = last_num + 1
            else:
                new_num = 1

            self.check_number = f'WS-INV-{year}-{new_num:03d}'

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
        self.total_items = self.items.count()
        self.counted_items = self.items.filter(is_counted=True).count()
        self.items_with_discrepancies = self.items.filter(has_discrepancy=True).count()

        # Zähle beschädigte Werkzeuge
        if self.check_tool_condition:
            self.damaged_tools_found = self.items.filter(is_damaged=True).count()

        # Zähle fällige Kalibrierungen
        if self.check_calibration:
            self.calibration_due_found = self.items.filter(calibration_due=True).count()

        # Zähle Sicherheitsprobleme
        if self.check_safety_equipment:
            self.safety_issues_found = self.items.filter(has_safety_issue=True).count()

        self.save(update_fields=[
            'total_items',
            'counted_items',
            'items_with_discrepancies',
            'damaged_tools_found',
            'calibration_due_found',
            'safety_issues_found'
        ])


class WorkshopInventoryCheckItem(models.Model):
    """
    Einzelner Artikel in einer Workshop-Inventur
    """

    # Verknüpfung zur Inventur
    inventory_check = models.ForeignKey(
        WorkshopInventoryCheck,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_('Inventur')
    )

    # Verknüpfung zum Werkzeug/Material
    workshop_tool = models.ForeignKey(
        'WorkshopToolInstance',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='inventory_items',
        verbose_name=_('Werkzeug')
    )

    workshop_item = models.ForeignKey(
        'WorkshopItem',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='inventory_items',
        verbose_name=_('Material/Teil')
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
        related_name='workshop_inventory_items',
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
        related_name='counted_workshop_items',
        verbose_name=_('Gezählt von')
    )

    # Workshop-spezifische Felder
    item_type = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_('Artikel-Typ')
    )

    # Zustand & Kalibrierung
    condition = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_('Zustand')
    )

    is_damaged = models.BooleanField(
        default=False,
        verbose_name=_('Beschädigt')
    )

    damage_description = models.TextField(
        blank=True,
        verbose_name=_('Schadensbeschreibung')
    )

    last_calibration_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Letzte Kalibrierung')
    )

    next_calibration_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Nächste Kalibrierung')
    )

    calibration_due = models.BooleanField(
        default=False,
        verbose_name=_('Kalibrierung fällig')
    )

    # Sicherheit
    is_safety_equipment = models.BooleanField(
        default=False,
        verbose_name=_('Sicherheitsausrüstung')
    )

    has_safety_issue = models.BooleanField(
        default=False,
        verbose_name=_('Sicherheitsproblem')
    )

    safety_issue_description = models.TextField(
        blank=True,
        verbose_name=_('Sicherheitsproblem Beschreibung')
    )

    # Notizen
    notes = models.TextField(
        blank=True,
        verbose_name=_('Notizen')
    )

    class Meta:
        verbose_name = _('Workshop Inventur-Position')
        verbose_name_plural = _('Workshop Inventur-Positionen')
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
