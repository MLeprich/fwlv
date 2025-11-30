"""
Models für Inventory Check App (Inventur)

Dieses Modul verwaltet die physische Bestandsaufnahme:
- Inventur-Durchführung
- Zählungen (Counting)
- Abweichungen (Discrepancies)
- Korrekturbuchungen
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from django.db.models import Count, Q, F, Sum
from decimal import Decimal
from core.models.base import TimeStampedModel, AuditedModel


class InventoryCheckType(models.TextChoices):
    """Art der Inventur"""
    FULL = 'full', _('Vollinventur')
    PARTIAL = 'partial', _('Teilinventur')
    SPOT_CHECK = 'spot_check', _('Stichprobe')
    CYCLE_COUNT = 'cycle_count', _('Zykluszählung')
    ANNUAL = 'annual', _('Jahresinventur')


class InventoryCheckStatus(models.TextChoices):
    """Status der Inventur"""
    PLANNED = 'planned', _('Geplant')
    IN_PROGRESS = 'in_progress', _('In Bearbeitung')
    COUNTING_COMPLETE = 'counting_complete', _('Zählung abgeschlossen')
    REVIEW = 'review', _('In Prüfung')
    ADJUSTMENTS_PENDING = 'adjustments_pending', _('Korrekturen ausstehend')
    COMPLETED = 'completed', _('Abgeschlossen')
    CANCELLED = 'cancelled', _('Abgebrochen')


class DiscrepancyType(models.TextChoices):
    """Art der Abweichung"""
    SURPLUS = 'surplus', _('Überschuss')
    SHORTAGE = 'shortage', _('Fehlbestand')
    DAMAGED = 'damaged', _('Beschädigt')
    EXPIRED = 'expired', _('Abgelaufen')
    MISLABELED = 'mislabeled', _('Falsch gekennzeichnet')
    MISLOCATED = 'mislocated', _('Falsch eingelagert')


class InventoryCheck(AuditedModel):
    """
    Inventur-Durchführung

    Hauptmodell für eine Inventur mit Fortschritts-Tracking
    """

    # Inventur-Nummer
    check_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_('Inventur-Nummer'),
        help_text=_('Automatisch generiert, z.B. INV-2025-0001')
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
        related_name='inventory_checks_responsible',
        verbose_name=_('Verantwortliche Person')
    )

    team_members = models.ManyToManyField(
        'personnel.Person',
        related_name='inventory_checks_team',
        blank=True,
        verbose_name=_('Team-Mitglieder')
    )

    # Zeitplanung
    scheduled_start_date = models.DateField(
        verbose_name=_('Geplanter Starttermin')
    )

    scheduled_end_date = models.DateField(
        verbose_name=_('Geplanter Endtermin')
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
        related_name='inventory_checks',
        null=True,
        blank=True,
        verbose_name=_('Lagerort'),
        help_text=_('Leer = Alle Lagerorte')
    )

    module_filter = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_('Modul-Filter'),
        help_text=_('z.B. "medical", "magazine" - Leer = Alle Module')
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
        related_name='inventory_checks_approved',
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
        db_table = 'inventory_check'
        verbose_name = _('Inventur')
        verbose_name_plural = _('Inventuren')
        ordering = ['-scheduled_start_date', '-check_number']
        indexes = [
            models.Index(fields=['check_number']),
            models.Index(fields=['status']),
            models.Index(fields=['-scheduled_start_date']),
            models.Index(fields=['responsible_person', '-scheduled_start_date']),
            models.Index(fields=['location']),
        ]

    def __str__(self):
        return f"{self.check_number} - {self.title}"

    def save(self, *args, **kwargs):
        # Auto-generate check_number if not set
        if not self.check_number:
            from django.utils import timezone
            year = timezone.now().year
            # Get last check number for this year
            last_check = InventoryCheck.objects.filter(
                check_number__startswith=f'INV-{year}-'
            ).order_by('-check_number').first()

            if last_check:
                last_num = int(last_check.check_number.split('-')[-1])
                new_num = last_num + 1
            else:
                new_num = 1

            self.check_number = f'INV-{year}-{new_num:04d}'

        super().save(*args, **kwargs)

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

    def update_progress(self):
        """Aktualisiert Fortschritts-Zähler"""
        self.total_items = self.items.count()
        self.counted_items = self.items.filter(is_counted=True).count()
        self.items_with_discrepancies = self.items.filter(has_discrepancy=True).count()
        self.save()


class InventoryCheckItem(AuditedModel):
    """
    Inventur-Position

    Einzelner Artikel in einer Inventur mit Soll/Ist-Vergleich
    """

    inventory_check = models.ForeignKey(
        InventoryCheck,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_('Inventur')
    )

    # Generic FK zu Inventory-Items (alle Typen)
    inventory_content_type = models.ForeignKey(
        'contenttypes.ContentType',
        on_delete=models.PROTECT,
        verbose_name=_('Lager-Artikeltyp'),
        help_text=_('z.B. MagazineItem, MedicalItem, etc.')
    )

    inventory_object_id = models.PositiveIntegerField(
        verbose_name=_('Lager-Artikel-ID')
    )

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
        related_name='check_items',
        verbose_name=_('Lagerort')
    )

    # Sollbestand (aus System)
    expected_quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name=_('Sollbestand'),
        help_text=_('Bestand laut System')
    )

    unit = models.CharField(
        max_length=50,
        default='Stück',
        verbose_name=_('Einheit')
    )

    # Istbestand (gezählt)
    actual_quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name=_('Istbestand'),
        help_text=_('Tatsächlich gezählter Bestand')
    )

    # Zählung
    is_counted = models.BooleanField(
        default=False,
        verbose_name=_('Gezählt')
    )

    counted_by = models.ForeignKey(
        'personnel.Person',
        on_delete=models.PROTECT,
        related_name='inventory_items_counted',
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
        verbose_name=_('Abweichung vorhanden')
    )

    variance_quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name=_('Abweichungsmenge'),
        help_text=_('Positiv = Überschuss, Negativ = Fehlbestand')
    )

    # Notizen
    notes = models.TextField(
        blank=True,
        verbose_name=_('Notizen')
    )

    # Verifikation (Nachzählung)
    requires_recount = models.BooleanField(
        default=False,
        verbose_name=_('Nachzählung erforderlich')
    )

    recount_done = models.BooleanField(
        default=False,
        verbose_name=_('Nachzählung durchgeführt')
    )

    recounted_by = models.ForeignKey(
        'personnel.Person',
        on_delete=models.PROTECT,
        related_name='inventory_items_recounted',
        null=True,
        blank=True,
        verbose_name=_('Nachgezählt von')
    )

    class Meta:
        db_table = 'inventory_check_item'
        verbose_name = _('Inventur-Position')
        verbose_name_plural = _('Inventur-Positionen')
        ordering = ['location', 'item_name']
        indexes = [
            models.Index(fields=['inventory_check', 'is_counted']),
            models.Index(fields=['inventory_check', 'has_discrepancy']),
            models.Index(fields=['location']),
            models.Index(fields=['counted_by']),
        ]

    def __str__(self):
        return f"{self.item_name} - {self.location}"

    def save(self, *args, **kwargs):
        # Berechne Abweichung wenn gezählt
        if self.is_counted and self.actual_quantity is not None:
            self.variance_quantity = self.actual_quantity - self.expected_quantity
            self.has_discrepancy = abs(self.variance_quantity) > Decimal('0.01')

        super().save(*args, **kwargs)

        # Update progress in parent InventoryCheck
        if self.inventory_check_id:
            self.inventory_check.update_progress()

    def get_variance_percentage(self):
        """Berechnet Abweichung in Prozent"""
        if self.expected_quantity == 0:
            return 0 if self.variance_quantity == 0 else 100
        return float((self.variance_quantity / self.expected_quantity) * 100)


class InventoryDiscrepancy(AuditedModel):
    """
    Inventur-Abweichung

    Detaillierte Dokumentation von Abweichungen mit Ursachen
    """

    check_item = models.ForeignKey(
        InventoryCheckItem,
        on_delete=models.CASCADE,
        related_name='discrepancies',
        verbose_name=_('Inventur-Position')
    )

    # Art der Abweichung
    discrepancy_type = models.CharField(
        max_length=20,
        choices=DiscrepancyType.choices,
        verbose_name=_('Abweichungsart')
    )

    # Menge
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name=_('Abweichungsmenge')
    )

    # Ursache
    cause = models.TextField(
        verbose_name=_('Ursache'),
        help_text=_('Beschreibung der vermuteten oder festgestellten Ursache')
    )

    # Verantwortlich
    found_by = models.ForeignKey(
        'personnel.Person',
        on_delete=models.PROTECT,
        related_name='discrepancies_found',
        verbose_name=_('Festgestellt von')
    )

    found_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Feststellungsdatum')
    )

    # Wert
    unit_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_('Wert pro Einheit (€)')
    )

    total_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_('Gesamtwert der Abweichung (€)')
    )

    # Korrektur
    corrective_action = models.TextField(
        blank=True,
        verbose_name=_('Korrekturmaßnahme'),
        help_text=_('Geplante oder durchgeführte Maßnahme')
    )

    correction_applied = models.BooleanField(
        default=False,
        verbose_name=_('Korrektur durchgeführt')
    )

    correction_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Korrekturdatum')
    )

    corrected_by = models.ForeignKey(
        'personnel.Person',
        on_delete=models.PROTECT,
        related_name='discrepancies_corrected',
        null=True,
        blank=True,
        verbose_name=_('Korrigiert von')
    )

    # Fotos
    photos = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_('Fotos'),
        help_text=_('Liste von Foto-URLs')
    )

    class Meta:
        db_table = 'inventory_discrepancy'
        verbose_name = _('Inventur-Abweichung')
        verbose_name_plural = _('Inventur-Abweichungen')
        ordering = ['-found_date']
        indexes = [
            models.Index(fields=['check_item']),
            models.Index(fields=['discrepancy_type']),
            models.Index(fields=['correction_applied']),
            models.Index(fields=['found_by', '-found_date']),
        ]

    def __str__(self):
        return f"{self.get_discrepancy_type_display()} - {self.quantity} {self.check_item.unit}"

    def save(self, *args, **kwargs):
        # Berechne Gesamtwert
        if self.unit_value is not None:
            self.total_value = self.quantity * self.unit_value

        super().save(*args, **kwargs)


class InventoryAdjustment(AuditedModel):
    """
    Inventur-Korrekturbuchung

    Buchungssatz zur Korrektur von Bestandsabweichungen
    """

    inventory_check = models.ForeignKey(
        InventoryCheck,
        on_delete=models.PROTECT,
        related_name='adjustments',
        verbose_name=_('Inventur')
    )

    check_item = models.ForeignKey(
        InventoryCheckItem,
        on_delete=models.PROTECT,
        related_name='adjustments',
        verbose_name=_('Inventur-Position')
    )

    discrepancy = models.ForeignKey(
        InventoryDiscrepancy,
        on_delete=models.PROTECT,
        related_name='adjustments',
        null=True,
        blank=True,
        verbose_name=_('Zugehörige Abweichung')
    )

    # Buchung
    adjustment_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_('Korrekturnummer'),
        help_text=_('Automatisch generiert, z.B. ADJ-2025-0001')
    )

    adjustment_date = models.DateTimeField(
        verbose_name=_('Buchungsdatum')
    )

    # Mengen
    old_quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_('Alter Bestand')
    )

    new_quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_('Neuer Bestand')
    )

    adjustment_quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_('Korrekturbetrag'),
        help_text=_('Positiv = Zugang, Negativ = Abgang')
    )

    # Begründung
    reason = models.TextField(
        verbose_name=_('Begründung')
    )

    # Genehmigung
    approved_by = models.ForeignKey(
        'personnel.Person',
        on_delete=models.PROTECT,
        related_name='adjustments_approved',
        null=True,
        blank=True,
        verbose_name=_('Genehmigt von')
    )

    approved_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Genehmigungsdatum')
    )

    # Durchführung
    applied = models.BooleanField(
        default=False,
        verbose_name=_('Angewendet'),
        help_text=_('Wurde die Korrektur im Lagersystem gebucht?')
    )

    applied_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Anwendungsdatum')
    )

    class Meta:
        db_table = 'inventory_adjustment'
        verbose_name = _('Korrekturbuchung')
        verbose_name_plural = _('Korrekturbuchungen')
        ordering = ['-adjustment_date']
        indexes = [
            models.Index(fields=['adjustment_number']),
            models.Index(fields=['inventory_check', '-adjustment_date']),
            models.Index(fields=['applied']),
            models.Index(fields=['approved_by']),
        ]

    def __str__(self):
        return f"{self.adjustment_number} - {self.check_item.item_name}"

    def save(self, *args, **kwargs):
        # Auto-generate adjustment_number if not set
        if not self.adjustment_number:
            from django.utils import timezone
            year = timezone.now().year
            # Get last adjustment number for this year
            last_adjustment = InventoryAdjustment.objects.filter(
                adjustment_number__startswith=f'ADJ-{year}-'
            ).order_by('-adjustment_number').first()

            if last_adjustment:
                last_num = int(last_adjustment.adjustment_number.split('-')[-1])
                new_num = last_num + 1
            else:
                new_num = 1

            self.adjustment_number = f'ADJ-{year}-{new_num:04d}'

        # Berechne adjustment_quantity
        self.adjustment_quantity = self.new_quantity - self.old_quantity

        super().save(*args, **kwargs)
