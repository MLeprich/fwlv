"""
Inventory Base Models
Basis-Modelle für alle Lager-Module (Abstract Base Classes)
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.core.validators import MinValueValidator
from decimal import Decimal

from core.models.base import AuditedModel
from mptt.models import MPTTModel, TreeForeignKey


# ============================================================================
# ENUMS & CHOICES
# ============================================================================

class StockMovementType(models.TextChoices):
    """Lagerbewegungstypen"""
    INCOMING = 'incoming', _('Wareneingang')
    OUTGOING = 'outgoing', _('Warenausgang')
    TRANSFER = 'transfer', _('Umlagerung')
    INVENTORY = 'inventory', _('Inventur-Korrektur')
    DAMAGE = 'damage', _('Beschädigung/Schwund')
    RETURN = 'return', _('Rückgabe')
    DISPOSAL = 'disposal', _('Entsorgung')


class ItemCondition(models.TextChoices):
    """Artikelzustand"""
    NEW = 'new', _('Neu')
    GOOD = 'good', _('Gut')
    USED = 'used', _('Gebraucht')
    WORN = 'worn', _('Abgenutzt')
    DAMAGED = 'damaged', _('Beschädigt')
    DEFECT = 'defect', _('Defekt')


class ItemUnit(models.TextChoices):
    """Lagereinheiten für Inventar-Artikel"""
    PIECE = 'Stück', _('Stück')
    PACKAGE = 'Packung', _('Packung')
    BOX = 'Karton', _('Karton')
    PALLET = 'Palette', _('Palette')
    # Längenmaße
    METER = 'Meter', _('Meter')
    CENTIMETER = 'Zentimeter', _('Zentimeter')
    MILLIMETER = 'Millimeter', _('Millimeter')
    # Volumen
    LITER = 'Liter', _('Liter')
    MILLILITER = 'Milliliter', _('Milliliter')
    # Gewicht
    KILOGRAM = 'Kilogramm', _('Kilogramm')
    GRAM = 'Gramm', _('Gramm')
    # Fläche
    SQUARE_METER = 'Quadratmeter', _('Quadratmeter')
    # Paar
    PAIR = 'Paar', _('Paar')
    # Rollen
    ROLL = 'Rolle', _('Rolle')
    # Set
    SET = 'Set', _('Set')


# ============================================================================
# CATEGORY & SUPPLIER
# ============================================================================

class Category(MPTTModel, AuditedModel):
    """
    Hierarchische Kategorien für Inventar-Items
    Verwendet django-mptt für Baum-Struktur
    """

    name = models.CharField(
        max_length=200,
        verbose_name=_('Name')
    )

    parent = TreeForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='children',
        verbose_name=_('Übergeordnete Kategorie')
    )

    description = models.TextField(
        blank=True,
        verbose_name=_('Beschreibung')
    )

    code = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_('Code'),
        help_text=_('Eindeutiger Kategorie-Code')
    )

    MODULE_CHOICES = [
        ('magazine', _('Magazin')),
        ('equipment', _('Ausrüstung')),
        ('clothing', _('Kleiderkammer')),
        ('medical', _('Rettungsdienst')),
        ('workshop', _('KFZ-Werkstatt')),
        ('height_rescue', _('Höhenrettung')),
        ('diving', _('Taucher')),
        ('it_hardware', _('IT-Hardware')),
    ]

    module = models.CharField(
        max_length=50,
        choices=MODULE_CHOICES,
        default='magazine',
        verbose_name=_('Modul'),
        help_text=_('Zugehöriges Lager-Modul')
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Aktiv')
    )

    class MPTTMeta:
        order_insertion_by = ['name']

    class Meta:
        verbose_name = _('Kategorie')
        verbose_name_plural = _('Kategorien')
        ordering = ['tree_id', 'lft']

    def __str__(self):
        return self.name

    def get_full_path(self):
        """Vollständiger Pfad der Kategorie"""
        ancestors = self.get_ancestors(include_self=True)
        return ' > '.join([cat.name for cat in ancestors])


class Supplier(AuditedModel):
    """
    Lieferanten/Hersteller
    """

    name = models.CharField(
        max_length=200,
        verbose_name=_('Name')
    )

    supplier_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_('Lieferantennummer')
    )

    # Kontaktdaten
    contact_person = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Ansprechpartner')
    )

    email = models.EmailField(
        blank=True,
        verbose_name=_('E-Mail')
    )

    phone = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_('Telefon')
    )

    mobile = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_('Mobiltelefon'),
        help_text=_('Mobilnummer des Ansprechpartners')
    )

    website = models.URLField(
        blank=True,
        verbose_name=_('Website')
    )

    # Adresse
    street = models.CharField(max_length=200, blank=True, verbose_name=_('Straße'))
    postal_code = models.CharField(max_length=10, blank=True, verbose_name=_('PLZ'))
    city = models.CharField(max_length=100, blank=True, verbose_name=_('Stadt'))
    country = models.CharField(max_length=100, blank=True, default='Deutschland', verbose_name=_('Land'))

    # Fahrzeug-spezifische Felder (optional)
    support_hotline = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_('Support-Hotline'),
        help_text=_('Technischer Support / Notfall-Hotline')
    )

    parts_department_phone = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_('Ersatzteil-Abteilung'),
        help_text=_('Telefon Ersatzteilbestellung')
    )

    service_email = models.EmailField(
        blank=True,
        verbose_name=_('Service-E-Mail'),
        help_text=_('E-Mail für Service-Anfragen')
    )

    # Zusatzinformationen
    tax_id = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_('Steuernummer')
    )

    payment_terms = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Zahlungsbedingungen'),
        help_text=_('z.B. 30 Tage netto')
    )

    notes = models.TextField(blank=True, verbose_name=_('Notizen'))

    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Aktiv')
    )

    class Meta:
        verbose_name = _('Lieferant')
        verbose_name_plural = _('Lieferanten')
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.supplier_number})"


# ============================================================================
# ABSTRACT INVENTORY ITEM
# ============================================================================

class AbstractInventoryItem(AuditedModel):
    """
    Abstrakte Basis-Klasse für alle Inventar-Items
    Wird von konkreten Apps geerbt (magazine, clothing, medical, etc.)
    """

    # Basis-Informationen
    name = models.CharField(
        max_length=200,
        verbose_name=_('Bezeichnung')
    )

    description = models.TextField(
        blank=True,
        verbose_name=_('Beschreibung')
    )

    item_number = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_('Artikelnummer'),
        help_text=_('Eindeutige Artikelnummer')
    )

    # Kategorisierung
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(app_label)s_%(class)s_items',
        verbose_name=_('Kategorie')
    )

    # Lieferant
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='%(app_label)s_%(class)s_items',
        verbose_name=_('Lieferant')
    )

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

    # Lagerort
    location = models.ForeignKey(
        'locations.Location',
        on_delete=models.PROTECT,
        null=True, blank=True,
        related_name='%(app_label)s_%(class)s_items',
        verbose_name=_('Lagerort')
    )

    # Bestandsmanagement
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name=_('Bestand')
    )

    unit = models.CharField(
        max_length=50,
        choices=ItemUnit.choices,
        default=ItemUnit.PIECE,
        verbose_name=_('Einheit'),
        help_text=_('z.B. Stück, Liter, Meter, kg')
    )

    min_quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True, blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name=_('Mindestbestand'),
        help_text=_('Warnung bei Unterschreitung')
    )

    max_quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True, blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name=_('Maximalbestand')
    )

    # Zustand
    condition = models.CharField(
        max_length=20,
        choices=ItemCondition.choices,
        default=ItemCondition.NEW,
        verbose_name=_('Zustand')
    )

    # Barcode/QR-Code
    barcode = models.CharField(
        max_length=100,
        blank=True,
        unique=True,
        null=True,
        verbose_name=_('Barcode/EAN')
    )

    qr_code = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('QR-Code')
    )

    # Preise
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True, blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name=_('Stückpreis (EUR)')
    )

    # Bilder
    image = models.ImageField(
        upload_to='inventory/images/',
        null=True, blank=True,
        verbose_name=_('Bild')
    )

    # Status
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Aktiv')
    )

    notes = models.TextField(blank=True, verbose_name=_('Notizen'))

    class Meta:
        abstract = True
        ordering = ['item_number']

    def __str__(self):
        return f"{self.item_number} - {self.name}"

    def is_low_stock(self):
        """Prüft ob Mindestbestand unterschritten"""
        if self.min_quantity:
            return self.quantity < self.min_quantity
        return False

    def is_out_of_stock(self):
        """Prüft ob ausverkauft"""
        return self.quantity <= 0

    def get_stock_percentage(self):
        """Bestand in Prozent (bezogen auf max_quantity)"""
        if self.max_quantity and self.max_quantity > 0:
            return (self.quantity / self.max_quantity) * 100
        return None

    def calculate_total_value(self):
        """Gesamtwert des Bestands"""
        if self.unit_price:
            return self.quantity * self.unit_price
        return None


# ============================================================================
# STOCK MOVEMENT
# ============================================================================

class AbstractStockMovement(AuditedModel):
    """
    Abstrakte Basis-Klasse für Lagerbewegungen
    Wird von konkreten Apps geerbt
    """

    movement_type = models.CharField(
        max_length=20,
        choices=StockMovementType.choices,
        verbose_name=_('Bewegungstyp')
    )

    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_('Menge')
    )

    unit = models.CharField(
        max_length=50,
        verbose_name=_('Einheit')
    )

    # Lagerorte
    from_location = models.ForeignKey(
        'locations.Location',
        on_delete=models.PROTECT,
        null=True, blank=True,
        related_name='%(app_label)s_%(class)s_outgoing',
        verbose_name=_('Von Lagerort')
    )

    to_location = models.ForeignKey(
        'locations.Location',
        on_delete=models.PROTECT,
        null=True, blank=True,
        related_name='%(app_label)s_%(class)s_incoming',
        verbose_name=_('Nach Lagerort')
    )

    # Referenzen
    reference_number = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Referenznummer'),
        help_text=_('z.B. Lieferschein-Nr., Bestellnummer')
    )

    # Zeitstempel
    movement_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Bewegungsdatum')
    )

    notes = models.TextField(blank=True, verbose_name=_('Notizen'))

    class Meta:
        abstract = True
        ordering = ['-movement_date']

    def __str__(self):
        return f"{self.get_movement_type_display()} - {self.quantity} {self.unit}"


class Meta:
    app_label = 'inventory_base'
"""
Abstract Base Models für Inventur

Diese Models werden von allen Modul-Inventuren geerbt (Medical, Magazine, etc.)
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from decimal import Decimal
from core.models.base import AuditedModel


class InventoryCheckStatus(models.TextChoices):
    """Status-Definitionen (einheitlich für alle Module)"""
    PLANNED = 'planned', _('Geplant')
    IN_PROGRESS = 'in_progress', _('In Bearbeitung')
    COUNTING_COMPLETE = 'counting_complete', _('Zählung abgeschlossen')
    REVIEW = 'review', _('In Prüfung')
    ADJUSTMENTS_PENDING = 'adjustments_pending', _('Korrekturen ausstehend')
    COMPLETED = 'completed', _('Abgeschlossen')
    CANCELLED = 'cancelled', _('Abgebrochen')


class InventoryCheckType(models.TextChoices):
    """Inventurarten"""
    FULL = 'full', _('Vollinventur')
    PARTIAL = 'partial', _('Teilinventur')
    SPOT_CHECK = 'spot_check', _('Stichprobe')
    CYCLE_COUNT = 'cycle_count', _('Zykluszählung')
    ANNUAL = 'annual', _('Jahresinventur')


class AbstractInventoryCheck(AuditedModel):
    """
    Basis-Modell für alle Modul-Inventuren
    NICHT in Datenbank erstellt (abstract = True)

    Wird geerbt von:
    - MedicalInventoryCheck
    - MagazineInventoryCheck
    - EquipmentInventoryCheck
    - etc.
    """

    # Nummer (modul-spezifisches Präfix wird überschrieben)
    check_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_('Inventur-Nummer'),
        editable=False
    )

    # Titel & Beschreibung
    title = models.CharField(
        max_length=200,
        verbose_name=_('Titel')
    )

    description = models.TextField(
        blank=True,
        verbose_name=_('Beschreibung')
    )

    # Art & Status
    check_type = models.CharField(
        max_length=20,
        choices=InventoryCheckType.choices,
        default=InventoryCheckType.PARTIAL,
        verbose_name=_('Inventurart')
    )

    status = models.CharField(
        max_length=30,
        choices=InventoryCheckStatus.choices,
        default=InventoryCheckStatus.PLANNED,
        verbose_name=_('Status')
    )

    # Verantwortung
    responsible_person = models.ForeignKey(
        'personnel.Person',
        on_delete=models.PROTECT,
        related_name='%(app_label)s_%(class)s_responsible',
        verbose_name=_('Verantwortliche Person')
    )

    team_members = models.ManyToManyField(
        'personnel.Person',
        related_name='%(app_label)s_%(class)s_team',
        blank=True,
        verbose_name=_('Team-Mitglieder')
    )

    # Zeitplanung
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

    # Umfang
    location = models.ForeignKey(
        'locations.Location',
        on_delete=models.PROTECT,
        related_name='%(app_label)s_%(class)s_checks',
        null=True,
        blank=True,
        verbose_name=_('Lagerort'),
        help_text=_('Leer = Alle Lagerorte')
    )

    # Fortschritt
    total_items = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Gesamt-Anzahl Artikel')
    )

    counted_items = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Gezählte Artikel')
    )

    items_with_discrepancies = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Artikel mit Abweichungen')
    )

    # Genehmigung
    approved_by = models.ForeignKey(
        'personnel.Person',
        on_delete=models.PROTECT,
        related_name='%(app_label)s_%(class)s_approved',
        null=True,
        blank=True,
        verbose_name=_('Genehmigt von')
    )

    approved_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Genehmigungsdatum')
    )

    # Notizen
    notes = models.TextField(
        blank=True,
        verbose_name=_('Notizen')
    )

    class Meta:
        abstract = True  # WICHTIG: Nicht in DB erstellen
        ordering = ['-scheduled_start_date', '-check_number']
        indexes = [
            models.Index(fields=['check_number']),
            models.Index(fields=['status']),
            models.Index(fields=['-scheduled_start_date']),
        ]

    def __str__(self):
        return f"{self.check_number} - {self.title}"

    # === Business-Logik (einheitlich für alle Module) ===

    def get_progress_percentage(self):
        """Berechnet Fortschritt in Prozent"""
        if self.total_items == 0:
            return 0
        return int((self.counted_items / self.total_items) * 100)

    def get_discrepancy_percentage(self):
        """Berechnet Abweichungsquote"""
        if self.counted_items == 0:
            return 0
        return int((self.items_with_discrepancies / self.counted_items) * 100)

    def is_overdue(self):
        """Prüft ob Inventur überfällig ist"""
        if self.status in [InventoryCheckStatus.COMPLETED, InventoryCheckStatus.CANCELLED]:
            return False
        from django.utils import timezone
        return timezone.now().date() > self.scheduled_end_date

    def can_start(self):
        """Prüft ob Inventur gestartet werden kann"""
        return self.status == InventoryCheckStatus.PLANNED

    def can_complete(self):
        """Prüft ob Inventur abgeschlossen werden kann"""
        return (
            self.status in [
                InventoryCheckStatus.COUNTING_COMPLETE,
                InventoryCheckStatus.REVIEW,
                InventoryCheckStatus.ADJUSTMENTS_PENDING
            ] and
            self.counted_items == self.total_items
        )

    def start_counting(self, user):
        """Startet die Inventur"""
        from django.utils import timezone
        if self.can_start():
            self.status = InventoryCheckStatus.IN_PROGRESS
            self.actual_start_date = timezone.now()
            self.updated_by = user
            self.save()
            return True
        return False

    def complete_counting(self, user):
        """Schließt Zählung ab"""
        from django.utils import timezone
        if self.status == InventoryCheckStatus.IN_PROGRESS:
            self.status = InventoryCheckStatus.COUNTING_COMPLETE
            self.updated_by = user
            self.save()
            return True
        return False

    def approve_and_complete(self, user):
        """Genehmigt und schließt Inventur ab"""
        from django.utils import timezone
        if self.can_complete():
            self.status = InventoryCheckStatus.COMPLETED
            # Get person from user if exists
            if hasattr(user, 'person'):
                self.approved_by = user.person
            self.approved_date = timezone.now()
            self.actual_end_date = timezone.now()
            self.updated_by = user
            self.save()
            return True
        return False

    def update_progress(self):
        """Aktualisiert Fortschritts-Zähler - Muss in Subklasse implementiert werden"""
        raise NotImplementedError("Subclass must implement update_progress()")

    def get_number_prefix(self):
        """Gibt Präfix für Nummerierung zurück - Muss in Subklasse implementiert werden"""
        raise NotImplementedError("Subclass must implement get_number_prefix()")

    def save(self, *args, **kwargs):
        # Auto-generate check_number if not set
        if not self.check_number:
            from django.utils import timezone
            year = timezone.now().year
            prefix = self.get_number_prefix()

            # Get last check number for this year and type
            last_check = self.__class__.objects.filter(
                check_number__startswith=f'{prefix}-{year}-'
            ).order_by('-check_number').first()

            if last_check:
                last_num = int(last_check.check_number.split('-')[-1])
                new_num = last_num + 1
            else:
                new_num = 1

            self.check_number = f'{prefix}-{year}-{new_num:04d}'

        super().save(*args, **kwargs)


class AbstractInventoryCheckItem(AuditedModel):
    """
    Basis-Modell für Inventur-Positionen

    Wird geerbt von:
    - MedicalInventoryCheckItem
    - MagazineInventoryCheckItem
    - etc.
    """

    # Artikeldetails (kopiert zur Bestandswahrung)
    item_name = models.CharField(
        max_length=200,
        verbose_name=_('Artikelbezeichnung')
    )

    item_number = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Artikelnummer')
    )

    location = models.ForeignKey(
        'locations.Location',
        on_delete=models.PROTECT,
        related_name='%(app_label)s_%(class)s_items',
        verbose_name=_('Lagerort')
    )

    # Sollbestand
    expected_quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name=_('Sollbestand')
    )

    unit = models.CharField(
        max_length=50,
        default='Stück',
        verbose_name=_('Einheit')
    )

    # Istbestand
    actual_quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name=_('Istbestand')
    )

    # Zählung
    is_counted = models.BooleanField(
        default=False,
        verbose_name=_('Gezählt')
    )

    counted_by = models.ForeignKey(
        'personnel.Person',
        on_delete=models.PROTECT,
        related_name='%(app_label)s_%(class)s_counted',
        null=True,
        blank=True,
        verbose_name=_('Gezählt von')
    )

    counted_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Zähldatum')
    )

    # Abweichung
    has_discrepancy = models.BooleanField(
        default=False,
        verbose_name=_('Abweichung')
    )

    variance_quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name=_('Differenz')
    )

    # Notizen
    notes = models.TextField(
        blank=True,
        verbose_name=_('Notizen')
    )

    # Nachzählung
    requires_recount = models.BooleanField(
        default=False,
        verbose_name=_('Nachzählung erforderlich')
    )

    class Meta:
        abstract = True
        ordering = ['location', 'item_name']

    def __str__(self):
        return f"{self.item_name} - {self.location}"

    def save(self, *args, **kwargs):
        # Berechne Abweichung
        if self.is_counted and self.actual_quantity is not None:
            self.variance_quantity = self.actual_quantity - self.expected_quantity
            self.has_discrepancy = abs(self.variance_quantity) > Decimal('0.01')

        super().save(*args, **kwargs)

    def get_variance_percentage(self):
        """Berechnet Abweichung in Prozent"""
        if self.expected_quantity == 0:
            return 0 if self.variance_quantity == 0 else 100
        return float((self.variance_quantity / self.expected_quantity) * 100)
