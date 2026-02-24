"""
Civil Protection Models (Bevölkerungsschutz)
Modelle für Bund, Land und Kommune
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from django.utils import timezone
from decimal import Decimal

from core.models.base import AuditedModel
from inventory_base.models import (
    AbstractStockMovement,
    AbstractInventoryCheck,
    AbstractInventoryCheckItem,
    ItemCondition,
    ItemUnit,
)


# ============================================================================
# ENUMS & CHOICES
# ============================================================================

class Bereich(models.TextChoices):
    BUND = 'bund', _('Bund')
    LAND = 'land', _('Land')
    KOMMUNE = 'kommune', _('Kommune')


class EquipmentType(models.TextChoices):
    GENERATOR = 'generator', _('Generator')
    SANDSACK = 'sandsack', _('Sandsack')
    PUMPE = 'pumpe', _('Pumpe')
    ZELT = 'zelt', _('Zelt')
    BELEUCHTUNG = 'beleuchtung', _('Beleuchtung')
    KOMMUNIKATION = 'kommunikation', _('Kommunikation')
    STROMVERSORGUNG = 'stromversorgung', _('Stromversorgung')
    WASSERAUFBEREITUNG = 'wasseraufbereitung', _('Wasseraufbereitung')
    HEIZUNG = 'heizung', _('Heizung')
    UNTERKUNFT = 'unterkunft', _('Unterkunft')
    SONSTIGES = 'sonstiges', _('Sonstiges')


class VehicleType(models.TextChoices):
    GW_SAN = 'gw_san', _('GW-San')
    MTW = 'mtw', _('MTW')
    GKW = 'gkw', _('GKW')
    LKW = 'lkw', _('LKW')
    ANH_LOGISTIK = 'anh_logistik', _('Anh Logistik')
    ANH_MZ = 'anh_mz', _('Anh MZ')
    FELDKUECHE = 'feldkueche', _('Feldküche')
    BTP = 'btp', _('BTP')
    SONSTIGES = 'sonstiges', _('Sonstiges')


class VehicleStatus(models.TextChoices):
    EINSATZBEREIT = 'einsatzbereit', _('Einsatzbereit')
    WARTUNG = 'wartung', _('In Wartung')
    DEFEKT = 'defekt', _('Defekt')
    AUSSER_DIENST = 'ausser_dienst', _('Außer Dienst')


class MedicationType(models.TextChoices):
    JODTABLETTE = 'jodtablette', _('Jodtablette')
    VERBANDMATERIAL = 'verbandmaterial', _('Verbandmaterial')
    INFUSION = 'infusion', _('Infusion')
    DESINFEKTIONSMITTEL = 'desinfektionsmittel', _('Desinfektionsmittel')
    ANTIDOT = 'antidot', _('Antidot')
    ERSTE_HILFE = 'erste_hilfe', _('Erste Hilfe')
    SONSTIGES = 'sonstiges', _('Sonstiges')


class StorageCondition(models.TextChoices):
    RAUMTEMPERATUR = 'raumtemperatur', _('Raumtemperatur')
    GEKUEHLT = 'gekuehlt', _('Gekühlt')
    GEFROREN = 'gefroren', _('Gefroren')
    TROCKEN = 'trocken', _('Trocken')
    DUNKEL = 'dunkel', _('Dunkel')


class NIPStatus(models.TextChoices):
    AKTIV = 'aktiv', _('Aktiv')
    INAKTIV = 'inaktiv', _('Inaktiv')
    GEPLANT = 'geplant', _('Geplant')
    VORUEBERGEHEND_GESCHLOSSEN = 'voruebergehend_geschlossen', _('Vorübergehend geschlossen')


# ============================================================================
# 1. KatSEquipmentMaster - Ausrüstungs-Stammdaten
# ============================================================================

class KatSEquipmentMaster(AuditedModel):
    """Stammdaten für KatS-Ausrüstung (Generatoren, Sandsäcke, Pumpen etc.)"""

    master_number = models.CharField(
        max_length=50, unique=True,
        verbose_name=_('Artikelnummer')
    )
    name = models.CharField(max_length=200, verbose_name=_('Bezeichnung'))
    description = models.TextField(blank=True, verbose_name=_('Beschreibung'))
    bereich = models.CharField(
        max_length=30, choices=Bereich.choices,
        verbose_name=_('Bereich')
    )
    equipment_type = models.CharField(
        max_length=30, choices=EquipmentType.choices,
        default=EquipmentType.SONSTIGES,
        verbose_name=_('Gerätetyp')
    )
    manufacturer = models.CharField(max_length=200, blank=True, verbose_name=_('Hersteller'))
    supplier = models.ForeignKey(
        'inventory_base.Supplier', on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='kats_equipment_masters',
        verbose_name=_('Lieferant')
    )
    unit = models.CharField(
        max_length=50, choices=ItemUnit.choices,
        default=ItemUnit.PIECE, verbose_name=_('Einheit')
    )
    min_quantity = models.DecimalField(
        max_digits=10, decimal_places=2,
        null=True, blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name=_('Mindestbestand')
    )
    max_quantity = models.DecimalField(
        max_digits=10, decimal_places=2,
        null=True, blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name=_('Maximalbestand')
    )
    unit_price = models.DecimalField(
        max_digits=10, decimal_places=2,
        null=True, blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name=_('Stückpreis (EUR)')
    )
    image = models.ImageField(
        upload_to='civil_protection/equipment/',
        null=True, blank=True, verbose_name=_('Bild')
    )
    requires_maintenance = models.BooleanField(
        default=False, verbose_name=_('Wartungspflichtig')
    )
    maintenance_interval_months = models.PositiveIntegerField(
        null=True, blank=True,
        verbose_name=_('Wartungsintervall (Monate)')
    )
    is_active = models.BooleanField(default=True, verbose_name=_('Aktiv'))
    notes = models.TextField(blank=True, verbose_name=_('Notizen'))

    class Meta:
        verbose_name = _('KatS-Ausrüstung (Stammdaten)')
        verbose_name_plural = _('KatS-Ausrüstung (Stammdaten)')
        ordering = ['master_number']

    def __str__(self):
        return f"{self.master_number} - {self.name}"

    def get_instance_count(self):
        return self.instances.filter(is_active=True).count()

    def generate_qr_code(self):
        import qrcode
        import qrcode.image.svg
        from io import BytesIO
        qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
        qr.add_data(f'/civil_protection/equipment/{self.pk}/')
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white", image_factory=qrcode.image.svg.SvgPathImage)
        stream = BytesIO()
        img.save(stream)
        return stream.getvalue().decode('utf-8')

    def generate_barcode(self):
        import barcode
        from barcode.writer import SVGWriter
        from io import BytesIO
        code128 = barcode.get_barcode_class('code128')
        rv = BytesIO()
        code = code128(self.master_number, writer=SVGWriter())
        code.write(rv)
        return rv.getvalue().decode('utf-8')


# ============================================================================
# 2. KatSEquipmentInstance - Einzelne Geräte-Instanzen
# ============================================================================

class KatSEquipmentInstance(AuditedModel):
    """Einzelne Geräte-Instanzen mit Inventarnummern"""

    master = models.ForeignKey(
        KatSEquipmentMaster, on_delete=models.CASCADE,
        related_name='instances',
        verbose_name=_('Stammdaten')
    )
    inventory_number = models.CharField(
        max_length=50, unique=True,
        verbose_name=_('Inventarnummer')
    )
    serial_number = models.CharField(
        max_length=100, blank=True,
        verbose_name=_('Seriennummer')
    )
    bereich = models.CharField(
        max_length=30, choices=Bereich.choices,
        verbose_name=_('Bereich')
    )
    location = models.ForeignKey(
        'locations.Location', on_delete=models.PROTECT,
        null=True, blank=True,
        related_name='kats_equipment_instances',
        verbose_name=_('Standort')
    )
    condition = models.CharField(
        max_length=20, choices=ItemCondition.choices,
        default=ItemCondition.NEW,
        verbose_name=_('Zustand')
    )
    is_operational = models.BooleanField(
        default=True, verbose_name=_('Einsatzbereit')
    )
    purchase_date = models.DateField(
        null=True, blank=True, verbose_name=_('Kaufdatum')
    )
    purchase_price = models.DecimalField(
        max_digits=10, decimal_places=2,
        null=True, blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name=_('Kaufpreis (EUR)')
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
    is_active = models.BooleanField(default=True, verbose_name=_('Aktiv'))
    notes = models.TextField(blank=True, verbose_name=_('Notizen'))

    class Meta:
        verbose_name = _('KatS-Gerät (Instanz)')
        verbose_name_plural = _('KatS-Geräte (Instanzen)')
        ordering = ['inventory_number']

    def __str__(self):
        return f"{self.inventory_number} - {self.master.name}"

    def generate_qr_code(self):
        import qrcode
        import qrcode.image.svg
        from io import BytesIO
        qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
        qr.add_data(f'/civil_protection/equipment/instances/{self.pk}/')
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white", image_factory=qrcode.image.svg.SvgPathImage)
        stream = BytesIO()
        img.save(stream)
        return stream.getvalue().decode('utf-8')

    def generate_barcode(self):
        import barcode
        from barcode.writer import SVGWriter
        from io import BytesIO
        code128 = barcode.get_barcode_class('code128')
        rv = BytesIO()
        code = code128(self.inventory_number, writer=SVGWriter())
        code.write(rv)
        return rv.getvalue().decode('utf-8')

    def is_maintenance_due(self):
        if self.next_maintenance_date:
            return self.next_maintenance_date <= timezone.now().date()
        return False


# ============================================================================
# 3. KatSVehicle - KatS-Fahrzeuge
# ============================================================================

class KatSVehicle(AuditedModel):
    """KatS-Fahrzeuge (GW-San, MTW, GKW etc.)"""

    name = models.CharField(max_length=200, verbose_name=_('Bezeichnung'))
    bereich = models.CharField(
        max_length=30, choices=Bereich.choices,
        verbose_name=_('Bereich')
    )
    vehicle_type = models.CharField(
        max_length=30, choices=VehicleType.choices,
        default=VehicleType.SONSTIGES,
        verbose_name=_('Fahrzeugtyp')
    )
    license_plate = models.CharField(
        max_length=20, unique=True,
        verbose_name=_('Kennzeichen')
    )
    call_sign = models.CharField(
        max_length=50, blank=True,
        verbose_name=_('Funkrufname')
    )
    vin = models.CharField(
        max_length=17, blank=True,
        verbose_name=_('FIN (Fahrzeugidentnummer)')
    )
    manufacturer = models.CharField(
        max_length=200, blank=True, verbose_name=_('Hersteller')
    )
    model = models.CharField(
        max_length=200, blank=True, verbose_name=_('Modell')
    )
    year_of_manufacture = models.PositiveIntegerField(
        null=True, blank=True,
        verbose_name=_('Baujahr')
    )
    location = models.ForeignKey(
        'locations.Location', on_delete=models.PROTECT,
        null=True, blank=True,
        related_name='kats_vehicles',
        verbose_name=_('Standort')
    )
    status = models.CharField(
        max_length=20, choices=VehicleStatus.choices,
        default=VehicleStatus.EINSATZBEREIT,
        verbose_name=_('Status')
    )
    tuev_date = models.DateField(
        null=True, blank=True, verbose_name=_('TÜV bis')
    )
    sp_date = models.DateField(
        null=True, blank=True, verbose_name=_('SP bis')
    )
    last_maintenance_date = models.DateField(
        null=True, blank=True,
        verbose_name=_('Letzte Wartung')
    )
    next_maintenance_date = models.DateField(
        null=True, blank=True,
        verbose_name=_('Nächste Wartung')
    )
    mileage_km = models.PositiveIntegerField(
        default=0, verbose_name=_('Kilometerstand')
    )
    purchase_date = models.DateField(
        null=True, blank=True, verbose_name=_('Kaufdatum')
    )
    purchase_price = models.DecimalField(
        max_digits=12, decimal_places=2,
        null=True, blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name=_('Kaufpreis (EUR)')
    )
    image = models.ImageField(
        upload_to='civil_protection/vehicles/',
        null=True, blank=True, verbose_name=_('Bild')
    )
    is_active = models.BooleanField(default=True, verbose_name=_('Aktiv'))
    notes = models.TextField(blank=True, verbose_name=_('Notizen'))

    class Meta:
        verbose_name = _('KatS-Fahrzeug')
        verbose_name_plural = _('KatS-Fahrzeuge')
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.license_plate})"

    def generate_qr_code(self):
        import qrcode
        import qrcode.image.svg
        from io import BytesIO
        qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
        qr.add_data(f'/civil_protection/vehicles/{self.pk}/')
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white", image_factory=qrcode.image.svg.SvgPathImage)
        stream = BytesIO()
        img.save(stream)
        return stream.getvalue().decode('utf-8')

    def generate_barcode(self):
        import barcode
        from barcode.writer import SVGWriter
        from io import BytesIO
        code128 = barcode.get_barcode_class('code128')
        rv = BytesIO()
        code = code128(self.license_plate, writer=SVGWriter())
        code.write(rv)
        return rv.getvalue().decode('utf-8')


# ============================================================================
# 4. KatSMedicationMaster - Medikamenten-Stammdaten
# ============================================================================

class KatSMedicationMaster(AuditedModel):
    """Stammdaten für KatS-Medikamente (Jodtabletten etc.)"""

    master_number = models.CharField(
        max_length=50, unique=True,
        verbose_name=_('Artikelnummer')
    )
    name = models.CharField(max_length=200, verbose_name=_('Bezeichnung'))
    description = models.TextField(blank=True, verbose_name=_('Beschreibung'))
    bereich = models.CharField(
        max_length=30, choices=Bereich.choices,
        verbose_name=_('Bereich')
    )
    medication_type = models.CharField(
        max_length=30, choices=MedicationType.choices,
        default=MedicationType.SONSTIGES,
        verbose_name=_('Medikamententyp')
    )
    active_ingredient = models.CharField(
        max_length=200, blank=True,
        verbose_name=_('Wirkstoff')
    )
    dosage = models.CharField(
        max_length=100, blank=True,
        verbose_name=_('Dosierung')
    )
    pharmaceutical_form = models.CharField(
        max_length=100, blank=True,
        verbose_name=_('Darreichungsform')
    )
    manufacturer = models.CharField(
        max_length=200, blank=True, verbose_name=_('Hersteller')
    )
    supplier = models.ForeignKey(
        'inventory_base.Supplier', on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='kats_medication_masters',
        verbose_name=_('Lieferant')
    )
    pzn = models.CharField(
        max_length=20, blank=True,
        verbose_name=_('PZN'),
        help_text=_('Pharmazentralnummer')
    )
    unit = models.CharField(
        max_length=50, choices=ItemUnit.choices,
        default=ItemUnit.PIECE, verbose_name=_('Einheit')
    )
    storage_condition = models.CharField(
        max_length=30, choices=StorageCondition.choices,
        default=StorageCondition.RAUMTEMPERATUR,
        verbose_name=_('Lagerbedingung')
    )
    expiry_warning_days = models.PositiveIntegerField(
        default=90,
        verbose_name=_('Ablaufwarnung (Tage)'),
        help_text=_('Warnung X Tage vor Ablauf')
    )
    min_quantity = models.DecimalField(
        max_digits=10, decimal_places=2,
        null=True, blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name=_('Mindestbestand')
    )
    max_quantity = models.DecimalField(
        max_digits=10, decimal_places=2,
        null=True, blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name=_('Maximalbestand')
    )
    image = models.ImageField(
        upload_to='civil_protection/medications/',
        null=True, blank=True, verbose_name=_('Bild')
    )
    is_active = models.BooleanField(default=True, verbose_name=_('Aktiv'))
    notes = models.TextField(blank=True, verbose_name=_('Notizen'))

    class Meta:
        verbose_name = _('KatS-Medikament (Stammdaten)')
        verbose_name_plural = _('KatS-Medikamente (Stammdaten)')
        ordering = ['master_number']

    def __str__(self):
        return f"{self.master_number} - {self.name}"

    def generate_qr_code(self):
        import qrcode
        import qrcode.image.svg
        from io import BytesIO
        qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
        qr.add_data(f'/civil_protection/medications/{self.pk}/')
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white", image_factory=qrcode.image.svg.SvgPathImage)
        stream = BytesIO()
        img.save(stream)
        return stream.getvalue().decode('utf-8')

    def generate_barcode(self):
        import barcode
        from barcode.writer import SVGWriter
        from io import BytesIO
        code128 = barcode.get_barcode_class('code128')
        rv = BytesIO()
        code = code128(self.master_number, writer=SVGWriter())
        code.write(rv)
        return rv.getvalue().decode('utf-8')

    def get_total_stock(self):
        return sum(
            b.quantity_remaining
            for b in self.batches.filter(is_recalled=False)
        )

    def get_expiring_batches(self):
        warning_date = timezone.now().date() + timezone.timedelta(
            days=self.expiry_warning_days
        )
        return self.batches.filter(
            expiry_date__lte=warning_date,
            quantity_remaining__gt=0,
            is_recalled=False,
        )


# ============================================================================
# 5. KatSMedicationBatch - Chargen mit Verfallsdatum
# ============================================================================

class KatSMedicationBatch(AuditedModel):
    """Medikamenten-Chargen mit Verfallsdatum und Rückverfolgbarkeit"""

    master = models.ForeignKey(
        KatSMedicationMaster, on_delete=models.CASCADE,
        related_name='batches',
        verbose_name=_('Medikament')
    )
    batch_number = models.CharField(
        max_length=100, verbose_name=_('Chargennummer')
    )
    bereich = models.CharField(
        max_length=30, choices=Bereich.choices,
        verbose_name=_('Bereich')
    )
    received_date = models.DateField(
        verbose_name=_('Eingangsdatum')
    )
    expiry_date = models.DateField(
        verbose_name=_('Verfallsdatum')
    )
    quantity_received = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name=_('Eingegangene Menge')
    )
    quantity_remaining = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name=_('Restmenge')
    )
    location = models.ForeignKey(
        'locations.Location', on_delete=models.PROTECT,
        null=True, blank=True,
        related_name='kats_medication_batches',
        verbose_name=_('Lagerort')
    )
    supplier_batch_number = models.CharField(
        max_length=100, blank=True,
        verbose_name=_('Lieferanten-Chargennummer')
    )
    unit_price = models.DecimalField(
        max_digits=10, decimal_places=2,
        null=True, blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name=_('Stückpreis (EUR)')
    )
    is_recalled = models.BooleanField(
        default=False, verbose_name=_('Rückruf')
    )
    recall_date = models.DateField(
        null=True, blank=True, verbose_name=_('Rückrufdatum')
    )
    recall_reason = models.TextField(
        blank=True, verbose_name=_('Rückrufgrund')
    )
    notes = models.TextField(blank=True, verbose_name=_('Notizen'))

    class Meta:
        verbose_name = _('KatS-Medikamenten-Charge')
        verbose_name_plural = _('KatS-Medikamenten-Chargen')
        unique_together = ['master', 'batch_number']
        ordering = ['expiry_date']

    def __str__(self):
        return f"{self.master.name} - Charge {self.batch_number}"

    def generate_qr_code(self):
        import qrcode
        import qrcode.image.svg
        from io import BytesIO
        qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
        qr.add_data(f'/civil_protection/batches/{self.pk}/')
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white", image_factory=qrcode.image.svg.SvgPathImage)
        stream = BytesIO()
        img.save(stream)
        return stream.getvalue().decode('utf-8')

    def generate_barcode(self):
        import barcode
        from barcode.writer import SVGWriter
        from io import BytesIO
        code128 = barcode.get_barcode_class('code128')
        rv = BytesIO()
        code = code128(self.batch_number, writer=SVGWriter())
        code.write(rv)
        return rv.getvalue().decode('utf-8')

    def save(self, *args, **kwargs):
        if not self.bereich:
            self.bereich = self.master.bereich
        super().save(*args, **kwargs)

    def is_expired(self):
        return self.expiry_date < timezone.now().date()

    def is_expiring_soon(self):
        warning_date = timezone.now().date() + timezone.timedelta(
            days=self.master.expiry_warning_days
        )
        return not self.is_expired() and self.expiry_date <= warning_date

    def days_until_expiry(self):
        delta = self.expiry_date - timezone.now().date()
        return delta.days


# ============================================================================
# 6. KatSStockMovement - Lagerbewegungen
# ============================================================================

class KatSStockMovement(AbstractStockMovement):
    """Lagerbewegungen für KatS-Material"""

    bereich = models.CharField(
        max_length=30, choices=Bereich.choices,
        blank=True,
        verbose_name=_('Bereich')
    )
    equipment_master = models.ForeignKey(
        KatSEquipmentMaster, on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='stock_movements',
        verbose_name=_('Ausrüstung')
    )
    medication_master = models.ForeignKey(
        KatSMedicationMaster, on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='stock_movements',
        verbose_name=_('Medikament')
    )
    batch = models.ForeignKey(
        KatSMedicationBatch, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='stock_movements',
        verbose_name=_('Charge')
    )
    unit_cost = models.DecimalField(
        max_digits=10, decimal_places=2,
        null=True, blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name=_('Stückkosten (EUR)')
    )
    total_cost = models.DecimalField(
        max_digits=12, decimal_places=2,
        null=True, blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name=_('Gesamtkosten (EUR)')
    )

    class Meta:
        verbose_name = _('KatS-Lagerbewegung')
        verbose_name_plural = _('KatS-Lagerbewegungen')
        ordering = ['-movement_date']

    def __str__(self):
        item = self.equipment_master or self.medication_master
        return f"{self.get_movement_type_display()} - {item} - {self.quantity}"


# ============================================================================
# 7. KatSInventoryCheck - Inventur
# ============================================================================

class KatSInventoryCheck(AbstractInventoryCheck):
    """Inventur für KatS-Material"""

    bereich = models.CharField(
        max_length=30, choices=Bereich.choices,
        blank=True,
        verbose_name=_('Bereich'),
        help_text=_('Leer = alle Bereiche')
    )
    check_expiry_dates = models.BooleanField(
        default=True,
        verbose_name=_('Verfallsdaten prüfen')
    )
    expired_items_found = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Abgelaufene Artikel gefunden')
    )

    class Meta:
        verbose_name = _('KatS-Inventur')
        verbose_name_plural = _('KatS-Inventuren')
        ordering = ['-scheduled_start_date']

    def get_number_prefix(self):
        return 'KATS-INV'

    def update_progress(self):
        items = self.check_items.all()
        self.total_items = items.count()
        self.counted_items = items.filter(is_counted=True).count()
        self.items_with_discrepancies = items.filter(has_discrepancy=True).count()
        self.save(update_fields=[
            'total_items', 'counted_items', 'items_with_discrepancies'
        ])


# ============================================================================
# 8. KatSInventoryCheckItem - Inventur-Positionen
# ============================================================================

class KatSInventoryCheckItem(AbstractInventoryCheckItem):
    """Einzelne Positionen einer KatS-Inventur"""

    inventory_check = models.ForeignKey(
        KatSInventoryCheck, on_delete=models.CASCADE,
        related_name='check_items',
        verbose_name=_('Inventur')
    )
    equipment_master = models.ForeignKey(
        KatSEquipmentMaster, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='inventory_check_items',
        verbose_name=_('Ausrüstung')
    )
    medication_master = models.ForeignKey(
        KatSMedicationMaster, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='inventory_check_items',
        verbose_name=_('Medikament')
    )
    batch_number = models.CharField(
        max_length=100, blank=True,
        verbose_name=_('Chargennummer')
    )
    expiry_date = models.DateField(
        null=True, blank=True,
        verbose_name=_('Verfallsdatum')
    )

    class Meta:
        verbose_name = _('KatS-Inventur-Position')
        verbose_name_plural = _('KatS-Inventur-Positionen')
        ordering = ['location', 'item_name']


# ============================================================================
# 9. Notfallinformationspunkt (NIP) - Bevölkerungsschutz
# ============================================================================

class Notfallinformationspunkt(AuditedModel):
    """Notfallinformationspunkte (NIPs) im Bevölkerungsschutz"""

    name = models.CharField(max_length=200, verbose_name=_('Bezeichnung'))
    bereich = models.CharField(
        max_length=30, choices=Bereich.choices,
        default=Bereich.BUND,
        verbose_name=_('Bereich')
    )
    status = models.CharField(
        max_length=40, choices=NIPStatus.choices,
        default=NIPStatus.GEPLANT,
        verbose_name=_('Status')
    )

    # Adresse
    address_street = models.CharField(
        max_length=200, blank=True, verbose_name=_('Straße')
    )
    address_postal_code = models.CharField(
        max_length=10, blank=True, verbose_name=_('PLZ')
    )
    address_city = models.CharField(
        max_length=100, blank=True, verbose_name=_('Stadt')
    )

    # GPS
    latitude = models.DecimalField(
        max_digits=9, decimal_places=6,
        null=True, blank=True, verbose_name=_('Breitengrad')
    )
    longitude = models.DecimalField(
        max_digits=9, decimal_places=6,
        null=True, blank=True, verbose_name=_('Längengrad')
    )

    capacity_persons = models.PositiveIntegerField(
        null=True, blank=True,
        verbose_name=_('Kapazität (Personen)')
    )

    # Ansprechpartner
    contact_name = models.CharField(
        max_length=200, blank=True, verbose_name=_('Ansprechpartner')
    )
    contact_phone = models.CharField(
        max_length=50, blank=True, verbose_name=_('Telefon')
    )
    contact_email = models.EmailField(
        blank=True, verbose_name=_('E-Mail')
    )

    # Zugewiesene Ressourcen
    assigned_equipment = models.ManyToManyField(
        KatSEquipmentInstance, blank=True,
        related_name='assigned_nips',
        verbose_name=_('Zugewiesene Geräte')
    )
    assigned_vehicles = models.ManyToManyField(
        KatSVehicle, blank=True,
        related_name='assigned_nips',
        verbose_name=_('Zugewiesene Fahrzeuge')
    )

    description = models.TextField(blank=True, verbose_name=_('Beschreibung'))
    opening_hours = models.TextField(
        blank=True, verbose_name=_('Öffnungszeiten')
    )
    is_active = models.BooleanField(default=True, verbose_name=_('Aktiv'))
    notes = models.TextField(blank=True, verbose_name=_('Notizen'))

    class Meta:
        verbose_name = _('Notfallinformationspunkt')
        verbose_name_plural = _('Notfallinformationspunkte')
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_full_address(self):
        parts = [self.address_street, f"{self.address_postal_code} {self.address_city}".strip()]
        return ', '.join(p for p in parts if p)


# ============================================================================
# 10. Leuchtturmstandort - Bevölkerungsschutz
# ============================================================================

class Leuchtturmstandort(AuditedModel):
    """Leuchtturmstandorte im Bevölkerungsschutz"""

    name = models.CharField(max_length=200, verbose_name=_('Bezeichnung'))
    bereich = models.CharField(
        max_length=30, choices=Bereich.choices,
        default=Bereich.BUND,
        verbose_name=_('Bereich')
    )
    status = models.CharField(
        max_length=40, choices=NIPStatus.choices,
        default=NIPStatus.GEPLANT,
        verbose_name=_('Status')
    )

    # Adresse
    address_street = models.CharField(
        max_length=200, blank=True, verbose_name=_('Straße')
    )
    address_postal_code = models.CharField(
        max_length=10, blank=True, verbose_name=_('PLZ')
    )
    address_city = models.CharField(
        max_length=100, blank=True, verbose_name=_('Stadt')
    )

    # GPS
    latitude = models.DecimalField(
        max_digits=9, decimal_places=6,
        null=True, blank=True, verbose_name=_('Breitengrad')
    )
    longitude = models.DecimalField(
        max_digits=9, decimal_places=6,
        null=True, blank=True, verbose_name=_('Längengrad')
    )

    capacity_persons = models.PositiveIntegerField(
        null=True, blank=True,
        verbose_name=_('Kapazität (Personen)')
    )

    # Ansprechpartner
    contact_name = models.CharField(
        max_length=200, blank=True, verbose_name=_('Ansprechpartner')
    )
    contact_phone = models.CharField(
        max_length=50, blank=True, verbose_name=_('Telefon')
    )
    contact_email = models.EmailField(
        blank=True, verbose_name=_('E-Mail')
    )

    # Zugewiesene Ressourcen
    assigned_equipment = models.ManyToManyField(
        KatSEquipmentInstance, blank=True,
        related_name='assigned_leuchtturm',
        verbose_name=_('Zugewiesene Geräte')
    )
    assigned_vehicles = models.ManyToManyField(
        KatSVehicle, blank=True,
        related_name='assigned_leuchtturm',
        verbose_name=_('Zugewiesene Fahrzeuge')
    )

    description = models.TextField(blank=True, verbose_name=_('Beschreibung'))
    opening_hours = models.TextField(
        blank=True, verbose_name=_('Öffnungszeiten')
    )
    is_active = models.BooleanField(default=True, verbose_name=_('Aktiv'))
    notes = models.TextField(blank=True, verbose_name=_('Notizen'))

    # Leuchtturm-spezifisch
    power_supply_available = models.BooleanField(
        default=False, verbose_name=_('Stromversorgung vorhanden')
    )
    heating_available = models.BooleanField(
        default=False, verbose_name=_('Heizung vorhanden')
    )
    water_supply_available = models.BooleanField(
        default=False, verbose_name=_('Wasserversorgung vorhanden')
    )
    communication_available = models.BooleanField(
        default=False, verbose_name=_('Kommunikation vorhanden')
    )

    class Meta:
        verbose_name = _('Leuchtturmstandort')
        verbose_name_plural = _('Leuchtturmstandorte')
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_full_address(self):
        parts = [self.address_street, f"{self.address_postal_code} {self.address_city}".strip()]
        return ', '.join(p for p in parts if p)


# ============================================================================
# 11. KatSLending - Ausleihe
# ============================================================================

class LendingStatus(models.TextChoices):
    OFFEN = 'offen', _('Offen')
    AUSGEGEBEN = 'ausgegeben', _('Ausgegeben')
    ZURUECKGEGEBEN = 'zurueckgegeben', _('Zurückgegeben')
    UEBERFAELLIG = 'ueberfaellig', _('Überfällig')


class KatSLending(AuditedModel):
    """Ausleihe von KatS-Material (Bierzeltgarnituren, Kaffeemaschinen etc.)"""

    lending_number = models.CharField(
        max_length=50, unique=True, editable=False,
        verbose_name=_('Ausleihe-Nr.')
    )
    bereich = models.CharField(
        max_length=30, choices=Bereich.choices,
        verbose_name=_('Bereich')
    )

    # Ausleihender
    borrower = models.ForeignKey(
        'personnel.Person', on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='kats_lendings',
        verbose_name=_('Ausleihende Person (intern)')
    )
    borrower_name = models.CharField(
        max_length=200, blank=True,
        verbose_name=_('Name des Ausleihenden')
    )
    borrower_organization = models.CharField(
        max_length=200, blank=True,
        verbose_name=_('Organisation')
    )
    borrower_phone = models.CharField(
        max_length=50, blank=True,
        verbose_name=_('Telefon')
    )
    borrower_email = models.EmailField(
        blank=True,
        verbose_name=_('E-Mail')
    )

    # Daten
    lending_date = models.DateField(
        verbose_name=_('Ausgabedatum')
    )
    expected_return_date = models.DateField(
        verbose_name=_('Geplantes Rückgabedatum')
    )
    actual_return_date = models.DateField(
        null=True, blank=True,
        verbose_name=_('Tatsächliches Rückgabedatum')
    )

    status = models.CharField(
        max_length=20, choices=LendingStatus.choices,
        default=LendingStatus.OFFEN,
        verbose_name=_('Status')
    )
    purpose = models.TextField(
        blank=True,
        verbose_name=_('Verwendungszweck')
    )
    notes = models.TextField(
        blank=True,
        verbose_name=_('Notizen')
    )

    class Meta:
        verbose_name = _('KatS-Ausleihe')
        verbose_name_plural = _('KatS-Ausleihen')
        ordering = ['-lending_date']
        permissions = [
            ('manage_lending', _('Kann Ausleihen verwalten')),
        ]

    def __str__(self):
        name = self.borrower_name or (str(self.borrower) if self.borrower else '–')
        return f"{self.lending_number} - {name}"

    def save(self, *args, **kwargs):
        if not self.lending_number:
            self.lending_number = self._generate_lending_number()
        super().save(*args, **kwargs)

    def _generate_lending_number(self):
        year = timezone.now().year
        prefix = f"KATS-AL-{year}-"
        last = (
            KatSLending.objects
            .filter(lending_number__startswith=prefix)
            .order_by('-lending_number')
            .values_list('lending_number', flat=True)
            .first()
        )
        if last:
            try:
                seq = int(last.split('-')[-1]) + 1
            except (ValueError, IndexError):
                seq = 1
        else:
            seq = 1
        return f"{prefix}{seq:04d}"

    def get_borrower_display(self):
        if self.borrower:
            return str(self.borrower)
        return self.borrower_name or '–'

    def is_overdue(self):
        if self.status in (LendingStatus.ZURUECKGEGEBEN,):
            return False
        return self.expected_return_date < timezone.now().date()


class KatSLendingItem(models.Model):
    """Einzelne Positionen einer Ausleihe"""

    lending = models.ForeignKey(
        KatSLending, on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_('Ausleihe')
    )
    equipment_master = models.ForeignKey(
        KatSEquipmentMaster, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='lending_items',
        verbose_name=_('KatS-Ausrüstung')
    )
    item_name = models.CharField(
        max_length=200,
        verbose_name=_('Artikelbezeichnung'),
        help_text=_('z.B. Bierzeltgarnitur, Kaffeemaschine')
    )
    quantity = models.PositiveIntegerField(
        default=1,
        verbose_name=_('Menge')
    )
    quantity_returned = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Menge zurückgegeben')
    )
    condition_out = models.CharField(
        max_length=100, blank=True,
        verbose_name=_('Zustand bei Ausgabe')
    )
    condition_in = models.CharField(
        max_length=100, blank=True,
        verbose_name=_('Zustand bei Rückgabe')
    )
    notes = models.TextField(
        blank=True,
        verbose_name=_('Notizen')
    )

    class Meta:
        verbose_name = _('Ausleihe-Position')
        verbose_name_plural = _('Ausleihe-Positionen')

    def __str__(self):
        return f"{self.item_name} x{self.quantity}"

    def is_fully_returned(self):
        return self.quantity_returned >= self.quantity
