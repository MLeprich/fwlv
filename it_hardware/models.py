"""
IT Hardware Models
Models für die Verwaltung von IT-Hardware
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from inventory_base.models import (
    AbstractInventoryItem,
    AbstractStockMovement,
    AbstractInventoryCheck,
    AbstractInventoryCheckItem
)


class ITHardwareType(models.TextChoices):
    """Typen von IT-Hardware"""
    # Computer & Notebooks
    DESKTOP_PC = 'desktop_pc', _('Desktop-PC')
    LAPTOP = 'laptop', _('Laptop')
    TABLET = 'tablet', _('Tablet')
    THIN_CLIENT = 'thin_client', _('Thin Client')
    ALL_IN_ONE = 'all_in_one', _('All-in-One PC')

    # Server & Netzwerk
    SERVER = 'server', _('Server')
    NAS = 'nas', _('NAS (Network Storage)')
    ROUTER = 'router', _('Router')
    SWITCH = 'switch', _('Switch')
    FIREWALL = 'firewall', _('Firewall')
    ACCESS_POINT = 'access_point', _('Access Point')
    MODEM = 'modem', _('Modem')

    # Peripherie
    MONITOR = 'monitor', _('Monitor')
    KEYBOARD = 'keyboard', _('Tastatur')
    MOUSE = 'mouse', _('Maus')
    PRINTER = 'printer', _('Drucker')
    SCANNER = 'scanner', _('Scanner')
    MULTIFUNCTION = 'multifunction', _('Multifunktionsgerät')
    WEBCAM = 'webcam', _('Webcam')
    HEADSET = 'headset', _('Headset')
    SPEAKER = 'speaker', _('Lautsprecher')

    # Mobilgeräte
    SMARTPHONE = 'smartphone', _('Smartphone')
    MOBILE_PHONE = 'mobile_phone', _('Mobiltelefon')
    MOBILE_RADIO = 'mobile_radio', _('Funkgerät')
    GPS_DEVICE = 'gps_device', _('GPS-Gerät')

    # Speicher & Komponenten
    EXTERNAL_HDD = 'external_hdd', _('Externe Festplatte')
    USB_STICK = 'usb_stick', _('USB-Stick')
    SSD = 'ssd', _('SSD')
    HDD = 'hdd', _('Interne Festplatte')
    RAM = 'ram', _('RAM-Modul')
    CPU = 'cpu', _('Prozessor')
    GPU = 'gpu', _('Grafikkarte')
    PSU = 'psu', _('Netzteil')
    MAINBOARD = 'mainboard', _('Mainboard')

    # Zubehör
    CABLE = 'cable', _('Kabel')
    ADAPTER = 'adapter', _('Adapter')
    DOCKING_STATION = 'docking_station', _('Dockingstation')
    UPS = 'ups', _('USV (Unterbrechungsfreie Stromversorgung)')
    KVM_SWITCH = 'kvm_switch', _('KVM-Switch')
    RACK = 'rack', _('Server-Rack')

    # Software
    LICENSE = 'license', _('Softwarelizenz')


class ITStatus(models.TextChoices):
    """Status der IT-Hardware"""
    IN_USE = 'in_use', _('In Betrieb')
    IN_STOCK = 'in_stock', _('Auf Lager')
    RESERVED = 'reserved', _('Reserviert')
    DEFECT = 'defect', _('Defekt')
    IN_REPAIR = 'in_repair', _('In Reparatur')
    RETIRED = 'retired', _('Ausgemustert')
    ORDERED = 'ordered', _('Bestellt')


class OperatingSystem(models.TextChoices):
    """Betriebssysteme"""
    WINDOWS_11 = 'windows_11', _('Windows 11')
    WINDOWS_10 = 'windows_10', _('Windows 10')
    WINDOWS_SERVER = 'windows_server', _('Windows Server')
    LINUX_UBUNTU = 'linux_ubuntu', _('Linux Ubuntu')
    LINUX_DEBIAN = 'linux_debian', _('Linux Debian')
    LINUX_CENTOS = 'linux_centos', _('Linux CentOS')
    MAC_OS = 'mac_os', _('macOS')
    ANDROID = 'android', _('Android')
    IOS = 'ios', _('iOS')
    OTHER = 'other', _('Sonstiges')


class ITHardwareItemMaster(models.Model):
    """
    IT-Hardware Stammdaten - Produktdefinition ohne Lagerort
    Analog zu EquipmentItemMaster und MedicalItemMaster
    """

    # Basis-Informationen
    master_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_('Stammdaten-Nummer'),
        help_text=_('Eindeutige Stammdaten-Nummer (z.B. IT-001)')
    )

    name = models.CharField(
        max_length=200,
        verbose_name=_('Bezeichnung'),
        help_text=_('z.B. ThinkPad T14 Gen 3, Dell Latitude 5420')
    )

    description = models.TextField(
        blank=True,
        verbose_name=_('Beschreibung')
    )

    hardware_type = models.CharField(
        max_length=50,
        choices=ITHardwareType.choices,
        verbose_name=_('Hardware-Typ')
    )

    # Hersteller-Informationen
    manufacturer = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Hersteller')
    )

    model = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Modell')
    )

    # Technische Spezifikationen (Standard)
    operating_system = models.CharField(
        max_length=50,
        choices=OperatingSystem.choices,
        blank=True,
        verbose_name=_('Standard-Betriebssystem')
    )

    cpu_model = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('CPU/Prozessor')
    )

    ram_gb = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_('RAM (GB)')
    )

    storage_gb = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Speicher (GB)')
    )

    gpu_model = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('GPU/Grafikkarte')
    )

    screen_size_inch = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        null=True,
        blank=True,
        verbose_name=_('Bildschirmgröße (Zoll)')
    )

    # Lebenszyklus
    depreciation_years = models.PositiveIntegerField(
        default=5,
        validators=[MinValueValidator(1)],
        verbose_name=_('Abschreibungsdauer (Jahre)')
    )

    # Wartungsintervalle
    maintenance_interval_months = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Wartungsintervall (Monate)'),
        help_text=_('0 = keine regelmäßige Wartung')
    )

    # Dokumentation
    manual_document = models.FileField(
        upload_to='it_hardware/manuals/',
        blank=True,
        verbose_name=_('Handbuch/Datenblatt')
    )

    image = models.ImageField(
        upload_to='it_hardware/images/',
        blank=True,
        verbose_name=_('Produktbild')
    )

    # Wirtschaftliche Daten
    purchase_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_('Standard-Kaufpreis (€)')
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
        help_text=_('Inaktive Stammdaten erscheinen nicht in Auswahllisten')
    )

    # Audit-Felder
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Erstellt am'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Aktualisiert am'))
    created_by = models.ForeignKey(
        'core.User',
        on_delete=models.PROTECT,
        related_name='created_it_masters',
        verbose_name=_('Erstellt von')
    )

    class Meta:
        verbose_name = _('IT-Hardware Stammdaten')
        verbose_name_plural = _('IT-Hardware Stammdaten')
        ordering = ['hardware_type', 'manufacturer', 'name']
        indexes = [
            models.Index(fields=['master_number']),
            models.Index(fields=['hardware_type', 'manufacturer']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.master_number} - {self.name}"

    def get_total_stock(self):
        """Gesamtbestand über alle Instanzen"""
        return self.device_instances.filter(is_active=True).count()

    def get_in_use_count(self):
        """Anzahl Geräte im Einsatz"""
        return self.device_instances.filter(
            is_active=True,
            it_status=ITStatus.IN_USE
        ).count()

    def get_available_count(self):
        """Anzahl verfügbarer Geräte"""
        return self.device_instances.filter(
            is_active=True,
            it_status=ITStatus.IN_STOCK
        ).count()


class ITHardwareDeviceInstance(models.Model):
    """
    IT-Hardware Geräte-Instanz mit Asset-Tag
    Analog zu EquipmentDeviceInstance und MedicalDeviceInstance
    """

    # Verknüpfung zu Stammdaten
    master = models.ForeignKey(
        ITHardwareItemMaster,
        on_delete=models.PROTECT,
        related_name='device_instances',
        verbose_name=_('IT-Hardware Stammdaten')
    )

    # Asset-Tracking
    inventory_number = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Inventarnummer'),
        help_text=_('Interne Inventarnummer')
    )

    asset_tag = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_('Asset-Tag'),
        help_text=_('Eindeutige Asset-Tag-Nummer (z.B. IT-2025-042)')
    )

    serial_number = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Seriennummer')
    )

    # Standort
    location = models.ForeignKey(
        'locations.Location',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='it_hardware_devices',
        verbose_name=_('Lagerort')
    )

    # Netzwerk-Informationen
    mac_address = models.CharField(
        max_length=17,
        blank=True,
        verbose_name=_('MAC-Adresse'),
        help_text=_('Format: XX:XX:XX:XX:XX:XX')
    )

    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name=_('IP-Adresse')
    )

    hostname = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Hostname')
    )

    # Betriebssystem (kann vom Master abweichen)
    operating_system = models.CharField(
        max_length=50,
        choices=OperatingSystem.choices,
        blank=True,
        verbose_name=_('Betriebssystem')
    )

    os_version = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('BS-Version')
    )

    last_os_update = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Letztes OS-Update')
    )

    # Status
    it_status = models.CharField(
        max_length=20,
        choices=ITStatus.choices,
        default=ITStatus.IN_STOCK,
        verbose_name=_('IT-Status')
    )

    # Benutzer-Zuordnung
    assigned_to = models.ForeignKey(
        'personnel.Person',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_it_devices',
        verbose_name=_('Zugewiesen an')
    )

    assignment_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Zuweisungsdatum')
    )

    # Fahrzeug-Zuordnung
    assigned_vehicle = models.ForeignKey(
        'vehicles.Vehicle',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='it_hardware_devices',
        verbose_name=_('Zugeordnetes Fahrzeug')
    )

    # Garantie & Support
    purchase_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Kaufdatum')
    )

    purchase_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_('Kaufpreis (€)')
    )

    warranty_end_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Garantieende')
    )

    support_contract = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Support-Vertrag')
    )

    support_end_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Support-Ende')
    )

    # Wartung
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

    maintenance_notes = models.TextField(
        blank=True,
        verbose_name=_('Wartungsnotizen')
    )

    # Lebenszyklus
    expected_replacement_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Geplanter Austausch')
    )

    # Lizenzinformationen
    license_key = models.CharField(
        max_length=500,
        blank=True,
        verbose_name=_('Lizenzschlüssel')
    )

    license_expiry_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Lizenz-Ablauf')
    )

    # Antivirus
    antivirus_software = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Antivirus-Software')
    )

    antivirus_last_update = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Letzte AV-Update')
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

    condition_notes = models.TextField(
        blank=True,
        verbose_name=_('Zustandsnotizen')
    )

    known_issues = models.TextField(
        blank=True,
        verbose_name=_('Bekannte Probleme')
    )

    # QR-Code
    has_qr_code = models.BooleanField(
        default=False,
        verbose_name=_('QR-Code vorhanden')
    )

    qr_code_data = models.CharField(
        max_length=500,
        blank=True,
        verbose_name=_('QR-Code Daten')
    )

    # Notizen
    notes = models.TextField(
        blank=True,
        verbose_name=_('Notizen')
    )

    # Status
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Aktiv')
    )

    # Audit-Felder
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Erstellt am'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Aktualisiert am'))
    created_by = models.ForeignKey(
        'core.User',
        on_delete=models.PROTECT,
        related_name='created_it_devices',
        verbose_name=_('Erstellt von')
    )

    class Meta:
        verbose_name = _('IT-Hardware Gerät')
        verbose_name_plural = _('IT-Hardware Geräte')
        ordering = ['asset_tag']
        indexes = [
            models.Index(fields=['asset_tag']),
            models.Index(fields=['serial_number']),
            models.Index(fields=['master', 'is_active']),
            models.Index(fields=['it_status']),
            models.Index(fields=['assigned_to']),
            models.Index(fields=['assigned_vehicle']),
            models.Index(fields=['warranty_end_date']),
            models.Index(fields=['support_end_date']),
            models.Index(fields=['next_maintenance_date']),
            models.Index(fields=['license_expiry_date']),
        ]

    def __str__(self):
        return f"{self.asset_tag} - {self.master.name}"

    def is_warranty_valid(self):
        """Prüft ob Garantie noch gültig ist"""
        from datetime import date
        if not self.warranty_end_date:
            return False
        return self.warranty_end_date >= date.today()

    def is_warranty_expiring_soon(self, days=30):
        """Prüft ob Garantie bald abläuft"""
        from datetime import date, timedelta
        if not self.warranty_end_date:
            return False
        return date.today() <= self.warranty_end_date <= date.today() + timedelta(days=days)

    def is_support_valid(self):
        """Prüft ob Support noch gültig ist"""
        from datetime import date
        if not self.support_end_date:
            return False
        return self.support_end_date >= date.today()

    def is_maintenance_due(self):
        """Prüft ob Wartung fällig ist"""
        from datetime import date
        if not self.next_maintenance_date:
            return False
        return self.next_maintenance_date <= date.today()

    def get_age_years(self):
        """Berechnet Alter in Jahren"""
        from datetime import date
        if not self.purchase_date:
            return None
        delta = date.today() - self.purchase_date
        return delta.days / 365.25

    def get_current_value(self):
        """Berechnet aktuellen Wert (linear abgeschrieben)"""
        if not self.purchase_price or not self.purchase_date:
            return None

        age_years = self.get_age_years()
        depreciation_years = self.master.depreciation_years if self.master else 5

        if age_years is None or age_years >= depreciation_years:
            return 0

        depreciation_per_year = self.purchase_price / depreciation_years
        return self.purchase_price - (depreciation_per_year * age_years)


class ITHardwareItem(AbstractInventoryItem):
    """
    IT-Hardware (LEGACY - wird ersetzt durch Master/Device-System)

    Spezifische Felder für IT-Geräte:
    - Asset-Tracking mit Seriennummern
    - Garantie und Support-Verträge
    - Benutzer-Zuordnung
    - Netzwerk-Informationen
    - Wartung und Updates
    """

    # Typ und Status
    hardware_type = models.CharField(
        max_length=50,
        choices=ITHardwareType.choices,
        verbose_name=_('Hardware-Typ')
    )

    it_status = models.CharField(
        max_length=20,
        choices=ITStatus.choices,
        default=ITStatus.IN_STOCK,
        verbose_name=_('IT-Status')
    )

    # Asset-Tracking
    asset_tag = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_('Asset-Tag'),
        help_text=_('Eindeutige Inventarnummer')
    )

    serial_number = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Seriennummer')
    )

    mac_address = models.CharField(
        max_length=17,
        blank=True,
        verbose_name=_('MAC-Adresse'),
        help_text=_('Format: XX:XX:XX:XX:XX:XX')
    )

    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name=_('IP-Adresse')
    )

    hostname = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Hostname')
    )

    # Technische Spezifikationen
    operating_system = models.CharField(
        max_length=50,
        choices=OperatingSystem.choices,
        blank=True,
        verbose_name=_('Betriebssystem')
    )

    os_version = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('BS-Version')
    )

    cpu_model = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('CPU/Prozessor')
    )

    ram_gb = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_('RAM (GB)')
    )

    storage_gb = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Speicher (GB)')
    )

    gpu_model = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('GPU/Grafikkarte')
    )

    screen_size_inch = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        null=True,
        blank=True,
        verbose_name=_('Bildschirmgröße (Zoll)')
    )

    # Benutzer-Zuordnung
    assigned_to = models.ForeignKey(
        'personnel.Person',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_it_hardware',
        verbose_name=_('Zugewiesen an')
    )

    assignment_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Zuweisungsdatum')
    )

    # Garantie & Support
    purchase_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Kaufdatum')
    )

    purchase_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_('Kaufpreis (€)')
    )

    warranty_end_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Garantieende')
    )

    support_contract = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Support-Vertrag'),
        help_text=_('z.B. Vertragsnummer')
    )

    support_end_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Support-Ende')
    )

    # Lebenszyklus
    depreciation_years = models.PositiveIntegerField(
        default=5,
        validators=[MinValueValidator(1)],
        verbose_name=_('Abschreibungsdauer (Jahre)')
    )

    expected_replacement_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Geplanter Austausch')
    )

    # Wartung & Updates
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

    last_os_update = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Letztes OS-Update')
    )

    antivirus_software = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Antivirus-Software')
    )

    antivirus_last_update = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Letzte AV-Update')
    )

    # Lizenzinformationen (für Software)
    license_key = models.CharField(
        max_length=500,
        blank=True,
        verbose_name=_('Lizenzschlüssel')
    )

    license_seats = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Anzahl Lizenzen')
    )

    license_expiry_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Lizenz-Ablauf')
    )

    # Zustand & Notizen
    condition_notes = models.TextField(
        blank=True,
        verbose_name=_('Zustandsnotizen')
    )

    known_issues = models.TextField(
        blank=True,
        verbose_name=_('Bekannte Probleme')
    )

    # Dokumentation
    invoice_file = models.FileField(
        upload_to='it_hardware/invoices/',
        blank=True,
        verbose_name=_('Rechnung')
    )

    manual_file = models.FileField(
        upload_to='it_hardware/manuals/',
        blank=True,
        verbose_name=_('Handbuch')
    )

    warranty_document = models.FileField(
        upload_to='it_hardware/warranties/',
        blank=True,
        verbose_name=_('Garantiedokument')
    )

    photos = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_('Fotos')
    )

    # Fahrzeug- oder Standort-Zuordnung
    assigned_vehicles = models.ManyToManyField(
        'vehicles.Vehicle',
        blank=True,
        related_name='it_hardware',
        verbose_name=_('Zugeordnete Fahrzeuge')
    )

    class Meta:
        verbose_name = _('IT-Hardware')
        verbose_name_plural = _('IT-Hardware')
        ordering = ['hardware_type', 'asset_tag']
        indexes = [
            models.Index(fields=['hardware_type']),
            models.Index(fields=['it_status']),
            models.Index(fields=['asset_tag']),
            models.Index(fields=['serial_number']),
            models.Index(fields=['assigned_to']),
            models.Index(fields=['warranty_end_date']),
            models.Index(fields=['support_end_date']),
        ]

    def __str__(self):
        return f"{self.asset_tag} - {self.name}"

    def is_warranty_valid(self):
        """Prüft ob Garantie noch gültig ist"""
        from datetime import date
        if not self.warranty_end_date:
            return False
        return self.warranty_end_date >= date.today()

    def is_warranty_expiring_soon(self, days=30):
        """Prüft ob Garantie bald abläuft"""
        from datetime import date, timedelta
        if not self.warranty_end_date:
            return False
        return date.today() <= self.warranty_end_date <= date.today() + timedelta(days=days)

    def is_support_valid(self):
        """Prüft ob Support noch gültig ist"""
        from datetime import date
        if not self.support_end_date:
            return False
        return self.support_end_date >= date.today()

    def get_age_years(self):
        """Berechnet Alter in Jahren"""
        from datetime import date
        if not self.purchase_date:
            return None
        delta = date.today() - self.purchase_date
        return delta.days / 365.25

    def get_current_value(self):
        """Berechnet aktuellen Wert (linear abgeschrieben)"""
        if not self.purchase_price or not self.purchase_date:
            return None

        age_years = self.get_age_years()
        if age_years is None or age_years >= self.depreciation_years:
            return 0

        depreciation_per_year = self.purchase_price / self.depreciation_years
        return self.purchase_price - (depreciation_per_year * age_years)


class ITHardwareStockMovement(AbstractStockMovement):
    """
    Lagerbewegungen für IT-Hardware

    Erweitert AbstractStockMovement um IT-spezifische Felder:
    - Zuweisungen an Benutzer
    - Wartungsarbeiten
    - Software-Updates
    """

    item = models.ForeignKey(
        ITHardwareItem,
        on_delete=models.CASCADE,
        related_name='stock_movements',
        verbose_name=_('Hardware')
    )

    # Benutzer-Zuweisung
    assigned_to = models.ForeignKey(
        'personnel.Person',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='it_hardware_assignments',
        verbose_name=_('Zugewiesen an')
    )

    assignment_reason = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Zuweisungsgrund'),
        help_text=_('z.B. Neueinstellung, Ersatz, Upgrade')
    )

    # Wartung & Reparatur
    maintenance_performed = models.BooleanField(
        default=False,
        verbose_name=_('Wartung durchgeführt')
    )

    maintenance_type = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Wartungsart'),
        help_text=_('z.B. Reinigung, Hardware-Upgrade, Software-Update')
    )

    maintenance_notes = models.TextField(
        blank=True,
        verbose_name=_('Wartungsnotizen')
    )

    parts_replaced = models.TextField(
        blank=True,
        verbose_name=_('Ersetzte Komponenten')
    )

    maintenance_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_('Wartungskosten (€)')
    )

    # Software-Updates
    os_updated = models.BooleanField(
        default=False,
        verbose_name=_('OS aktualisiert')
    )

    new_os_version = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Neue OS-Version')
    )

    software_installed = models.TextField(
        blank=True,
        verbose_name=_('Installierte Software'),
        help_text=_('Liste der installierten Programme')
    )

    # Zustand
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
        verbose_name = _('Lagerbewegung IT-Hardware')
        verbose_name_plural = _('Lagerbewegungen IT-Hardware')
        ordering = ['-movement_date', '-created_at']
        indexes = [
            models.Index(fields=['item', 'movement_date']),
            models.Index(fields=['assigned_to']),
            models.Index(fields=['maintenance_performed']),
        ]

    def __str__(self):
        return f"{self.get_movement_type_display()} - {self.item.asset_tag} ({self.movement_date})"

    def save(self, *args, **kwargs):
        """Automatische Updates bei Zuweisung oder Wartung"""
        super().save(*args, **kwargs)

        # Bei Zuweisung: Benutzer im Item aktualisieren
        if self.assigned_to:
            self.item.assigned_to = self.assigned_to
            self.item.assignment_date = self.movement_date.date() if hasattr(self.movement_date, 'date') else self.movement_date
            self.item.it_status = ITStatus.IN_USE
            self.item.save()

        # Bei Wartung: Wartungsdatum aktualisieren
        if self.maintenance_performed:
            self.item.last_maintenance_date = self.movement_date.date() if hasattr(self.movement_date, 'date') else self.movement_date
            self.item.save()

        # Bei OS-Update: Version aktualisieren
        if self.os_updated and self.new_os_version:
            self.item.os_version = self.new_os_version
            self.item.last_os_update = self.movement_date.date() if hasattr(self.movement_date, 'date') else self.movement_date
            self.item.save()


# ============================================================================
# INVENTUR (Inventory Check) - IT-Hardware
# ============================================================================

class ITHardwareInventoryCheck(AbstractInventoryCheck):
    """
    Inventur für IT-Hardware
    Erweitert AbstractInventoryCheck mit IT-spezifischen Feldern
    """

    # IT-Hardware-spezifische Prüfungen
    check_warranty = models.BooleanField(
        default=True,
        verbose_name=_('Garantie prüfen'),
        help_text=_('Geräte mit abgelaufener Garantie identifizieren')
    )

    check_support = models.BooleanField(
        default=True,
        verbose_name=_('Support-Verträge prüfen'),
        help_text=_('Support-Verträge auf Ablauf prüfen')
    )

    check_os_updates = models.BooleanField(
        default=True,
        verbose_name=_('OS-Updates prüfen'),
        help_text=_('Betriebssystem-Update-Status prüfen')
    )

    check_licenses = models.BooleanField(
        default=False,
        verbose_name=_('Lizenzen prüfen'),
        help_text=_('Software-Lizenzen auf Gültigkeit prüfen')
    )

    # Ergebnisse der IT-spezifischen Prüfungen
    warranty_expired_found = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Garantie abgelaufen'),
        help_text=_('Anzahl Geräte mit abgelaufener Garantie')
    )

    support_expired_found = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Support abgelaufen'),
        help_text=_('Anzahl Geräte mit abgelaufenem Support')
    )

    os_outdated_found = models.PositiveIntegerField(
        default=0,
        verbose_name=_('OS veraltet'),
        help_text=_('Anzahl Geräte mit veraltetem OS')
    )

    defective_devices_found = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Defekte Geräte'),
        help_text=_('Anzahl defekter Geräte gefunden')
    )

    class Meta:
        verbose_name = _('IT-Hardware Inventur')
        verbose_name_plural = _('IT-Hardware Inventuren')
        ordering = ['-created_at']
        permissions = [
            ('approve_ithardwareinventorycheck', _('Kann IT-Hardware-Inventur genehmigen')),
        ]

    def get_number_prefix(self):
        """Präfix für Inventur-Nummern"""
        return 'IT-INV'

    def update_progress(self):
        """IT-spezifische Fortschritts-Berechnung"""
        from django.utils import timezone

        self.total_items = self.items.count()
        self.counted_items = self.items.filter(is_counted=True).count()
        self.items_with_discrepancies = self.items.filter(has_discrepancy=True).count()

        # Zähle defekte Geräte
        self.defective_devices_found = self.items.filter(is_defective=True).count()

        # Zähle abgelaufene Garantien
        if self.check_warranty:
            self.warranty_expired_found = self.items.filter(
                warranty_expired=True
            ).count()

        # Zähle abgelaufene Support-Verträge
        if self.check_support:
            self.support_expired_found = self.items.filter(
                support_expired=True
            ).count()

        # Zähle veraltete OS
        if self.check_os_updates:
            self.os_outdated_found = self.items.filter(
                os_outdated=True
            ).count()

        self.save(update_fields=[
            'total_items',
            'counted_items',
            'items_with_discrepancies',
            'defective_devices_found',
            'warranty_expired_found',
            'support_expired_found',
            'os_outdated_found'
        ])


class ITHardwareInventoryCheckItem(AbstractInventoryCheckItem):
    """
    Einzelner Artikel in einer IT-Hardware-Inventur
    Erweitert AbstractInventoryCheckItem mit IT-spezifischen Feldern
    """

    # Verknüpfung zur Inventur
    inventory_check = models.ForeignKey(
        ITHardwareInventoryCheck,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_('Inventur')
    )

    # Verknüpfung zum IT-Gerät
    it_device = models.ForeignKey(
        'ITHardwareDeviceInstance',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='inventory_items',
        verbose_name=_('IT-Gerät')
    )

    # IT-Hardware-spezifische Felder
    asset_tag = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Asset-Tag')
    )

    serial_number = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Seriennummer')
    )

    hardware_type = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_('Hardware-Typ')
    )

    it_status = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_('IT-Status')
    )

    # Garantie & Support
    warranty_end_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Garantieende')
    )

    warranty_expired = models.BooleanField(
        default=False,
        verbose_name=_('Garantie abgelaufen')
    )

    support_end_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Support-Ende')
    )

    support_expired = models.BooleanField(
        default=False,
        verbose_name=_('Support abgelaufen')
    )

    # OS-Status
    operating_system = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Betriebssystem')
    )

    os_version = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('OS-Version')
    )

    last_os_update = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Letztes OS-Update')
    )

    os_outdated = models.BooleanField(
        default=False,
        verbose_name=_('OS veraltet'),
        help_text=_('Letztes Update > 6 Monate')
    )

    # Netzwerk
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name=_('IP-Adresse')
    )

    mac_address = models.CharField(
        max_length=17,
        blank=True,
        verbose_name=_('MAC-Adresse')
    )

    # Zustand
    is_defective = models.BooleanField(
        default=False,
        verbose_name=_('Defekt')
    )

    assigned_to_name = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Zugewiesen an')
    )

    class Meta:
        verbose_name = _('IT-Hardware Inventur-Position')
        verbose_name_plural = _('IT-Hardware Inventur-Positionen')
        ordering = ['item_name', 'asset_tag']
