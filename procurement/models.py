"""
Models für Procurement App (Bestellwesen)

Dieses Modul verwaltet den kompletten Bestellprozess:
- Bestellanforderungen
- Bestellungen (Purchase Orders)
- Freigabe-Workflow (Approval Workflow)
- Lieferantenmanagement
- Wareneingang
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from django.db.models import Sum, F
from decimal import Decimal
from core.models.base import TimeStampedModel, AuditedModel


class OrderPriority(models.TextChoices):
    """Priorität einer Bestellung"""
    LOW = 'low', _('Niedrig')
    NORMAL = 'normal', _('Normal')
    HIGH = 'high', _('Hoch')
    URGENT = 'urgent', _('Dringend')


class OrderStatus(models.TextChoices):
    """Status einer Bestellung"""
    DRAFT = 'draft', _('Entwurf')
    SUBMITTED = 'submitted', _('Eingereicht')
    PENDING_APPROVAL = 'pending_approval', _('Wartet auf Freigabe')
    APPROVED = 'approved', _('Freigegeben')
    REJECTED = 'rejected', _('Abgelehnt')
    ORDERED = 'ordered', _('Bestellt')
    PARTIALLY_RECEIVED = 'partially_received', _('Teilweise geliefert')
    RECEIVED = 'received', _('Vollständig geliefert')
    CANCELLED = 'cancelled', _('Storniert')
    CLOSED = 'closed', _('Abgeschlossen')


class ApprovalStatus(models.TextChoices):
    """Status einer Freigabe"""
    PENDING = 'pending', _('Ausstehend')
    APPROVED = 'approved', _('Freigegeben')
    REJECTED = 'rejected', _('Abgelehnt')
    EXPIRED = 'expired', _('Abgelaufen')


class DeliveryStatus(models.TextChoices):
    """Lieferstatus"""
    NOT_SHIPPED = 'not_shipped', _('Noch nicht versandt')
    SHIPPED = 'shipped', _('Versandt')
    IN_TRANSIT = 'in_transit', _('Unterwegs')
    DELIVERED = 'delivered', _('Geliefert')
    DELAYED = 'delayed', _('Verspätet')


class PurchaseOrder(AuditedModel):
    """
    Bestellung (Purchase Order)

    Hauptmodell für alle Bestellungen mit mehrstufigem Approval-Workflow
    """

    # Bestellnummer
    order_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_('Bestellnummer'),
        help_text=_('Automatisch generiert, z.B. PO-2025-0001')
    )

    # Titel & Beschreibung
    title = models.CharField(
        max_length=200,
        verbose_name=_('Titel')
    )

    description = models.TextField(
        blank=True,
        verbose_name=_('Beschreibung'),
        help_text=_('Zweck und Details der Bestellung')
    )

    # Status & Priorität
    status = models.CharField(
        max_length=30,
        choices=OrderStatus.choices,
        default=OrderStatus.DRAFT,
        verbose_name=_('Status')
    )

    priority = models.CharField(
        max_length=20,
        choices=OrderPriority.choices,
        default=OrderPriority.NORMAL,
        verbose_name=_('Priorität')
    )

    # Lieferant
    supplier = models.ForeignKey(
        'inventory_base.Supplier',
        on_delete=models.PROTECT,
        related_name='purchase_orders',
        verbose_name=_('Lieferant')
    )

    # Anforderung & Genehmigung
    requested_by = models.ForeignKey(
        'personnel.Person',
        on_delete=models.PROTECT,
        related_name='purchase_orders_requested',
        verbose_name=_('Angefordert von')
    )

    requested_date = models.DateField(
        verbose_name=_('Anforderungsdatum')
    )

    approved_by = models.ForeignKey(
        'personnel.Person',
        on_delete=models.PROTECT,
        related_name='purchase_orders_approved',
        null=True,
        blank=True,
        verbose_name=_('Genehmigt von')
    )

    approved_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Genehmigungsdatum')
    )

    # Bestellung
    ordered_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Bestelldatum'),
        help_text=_('Datum der tatsächlichen Bestellung beim Lieferanten')
    )

    # Lieferung
    expected_delivery_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Erwartetes Lieferdatum')
    )

    actual_delivery_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Tatsächliches Lieferdatum')
    )

    delivery_status = models.CharField(
        max_length=20,
        choices=DeliveryStatus.choices,
        default=DeliveryStatus.NOT_SHIPPED,
        verbose_name=_('Lieferstatus')
    )

    # Lieferadresse
    delivery_location = models.ForeignKey(
        'locations.Location',
        on_delete=models.PROTECT,
        related_name='purchase_orders',
        verbose_name=_('Lieferadresse')
    )

    # Kosten
    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name=_('Zwischensumme (€)')
    )

    tax_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=19.00,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name=_('Steuersatz (%)')
    )

    tax_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name=_('Steuerbetrag (€)')
    )

    shipping_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name=_('Versandkosten (€)')
    )

    total_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name=_('Gesamtkosten (€)')
    )

    # Budget
    budget_code = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_('Budgetcode'),
        help_text=_('Interner Budgetcode für Kostenstelle')
    )

    # Dokumente
    invoice_number = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Rechnungsnummer')
    )

    invoice_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Rechnungsdatum')
    )

    invoice_file = models.FileField(
        upload_to='procurement/invoices/%Y/%m/',
        blank=True,
        null=True,
        verbose_name=_('Rechnungsdatei')
    )

    order_confirmation_file = models.FileField(
        upload_to='procurement/confirmations/%Y/%m/',
        blank=True,
        null=True,
        verbose_name=_('Auftragsbestätigung')
    )

    # Notizen
    notes = models.TextField(
        blank=True,
        verbose_name=_('Interne Notizen')
    )

    rejection_reason = models.TextField(
        blank=True,
        verbose_name=_('Ablehnungsgrund')
    )

    # Tracking
    tracking_number = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Tracking-Nummer')
    )

    class Meta:
        db_table = 'procurement_purchase_order'
        verbose_name = _('Bestellung')
        verbose_name_plural = _('Bestellungen')
        ordering = ['-requested_date', '-order_number']
        indexes = [
            models.Index(fields=['order_number']),
            models.Index(fields=['status']),
            models.Index(fields=['-requested_date']),
            models.Index(fields=['supplier', '-requested_date']),
            models.Index(fields=['requested_by', '-requested_date']),
            models.Index(fields=['priority', 'status']),
        ]

    def __str__(self):
        return f"{self.order_number} - {self.title}"

    def save(self, *args, **kwargs):
        # Auto-generate order_number if not set
        if not self.order_number:
            from django.utils import timezone
            year = timezone.now().year
            # Get last order number for this year
            last_order = PurchaseOrder.objects.filter(
                order_number__startswith=f'PO-{year}-'
            ).order_by('-order_number').first()

            if last_order:
                last_num = int(last_order.order_number.split('-')[-1])
                new_num = last_num + 1
            else:
                new_num = 1

            self.order_number = f'PO-{year}-{new_num:04d}'

        # Calculate totals
        self.calculate_totals()

        super().save(*args, **kwargs)

    def calculate_totals(self):
        """Berechnet Zwischen-, Steuer- und Gesamtsumme"""
        # Subtotal aus OrderItems berechnen
        items_total = self.items.aggregate(
            total=Sum(F('quantity') * F('unit_price'))
        )['total'] or Decimal('0.00')

        self.subtotal = items_total
        self.tax_amount = (self.subtotal * self.tax_rate) / Decimal('100')
        self.total_cost = self.subtotal + self.tax_amount + self.shipping_cost

    def get_approval_progress(self):
        """Gibt Freigabe-Fortschritt zurück (Anzahl approved / total)"""
        total = self.approvals.count()
        if total == 0:
            return 0
        approved = self.approvals.filter(status=ApprovalStatus.APPROVED).count()
        return int((approved / total) * 100)

    def is_fully_approved(self):
        """Prüft ob alle erforderlichen Freigaben erteilt wurden"""
        total = self.approvals.count()
        if total == 0:
            return False
        approved = self.approvals.filter(status=ApprovalStatus.APPROVED).count()
        rejected = self.approvals.filter(status=ApprovalStatus.REJECTED).count()

        if rejected > 0:
            return False
        return approved == total

    def get_received_percentage(self):
        """Berechnet Lieferfortschritt in Prozent"""
        total_items = self.items.count()
        if total_items == 0:
            return 0

        received_items = self.items.filter(
            quantity_received__gte=F('quantity')
        ).count()

        return int((received_items / total_items) * 100)


class OrderItem(TimeStampedModel):
    """
    Bestellposition

    Einzelne Artikel in einer Bestellung
    """

    purchase_order = models.ForeignKey(
        PurchaseOrder,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_('Bestellung')
    )

    # Artikel-Details
    item_name = models.CharField(
        max_length=200,
        verbose_name=_('Artikelbezeichnung')
    )

    description = models.TextField(
        blank=True,
        verbose_name=_('Beschreibung')
    )

    # Optional: Verknüpfung zu Inventory Item (wenn Nachbestellung)
    # Generic FK für alle Inventory-Typen
    inventory_content_type = models.ForeignKey(
        'contenttypes.ContentType',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('Lager-Artikeltyp'),
        help_text=_('z.B. MagazineItem, MedicalItem, etc.')
    )

    inventory_object_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Lager-Artikel-ID')
    )

    # Menge & Preis
    quantity = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name=_('Menge')
    )

    unit = models.CharField(
        max_length=50,
        default='Stück',
        verbose_name=_('Einheit')
    )

    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name=_('Einzelpreis (€)')
    )

    # Lieferung
    quantity_received = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name=_('Erhaltene Menge')
    )

    # Kategorie (für Budget-Zuordnung)
    category = models.ForeignKey(
        'inventory_base.Category',
        on_delete=models.PROTECT,
        related_name='order_items',
        null=True,
        blank=True,
        verbose_name=_('Kategorie')
    )

    # Ziel-Lagerort
    target_location = models.ForeignKey(
        'locations.Location',
        on_delete=models.PROTECT,
        related_name='order_items',
        null=True,
        blank=True,
        verbose_name=_('Ziel-Lagerort')
    )

    # Artikelnummer des Lieferanten
    supplier_item_number = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Lieferanten-Artikelnummer')
    )

    # Notizen
    notes = models.TextField(
        blank=True,
        verbose_name=_('Notizen')
    )

    class Meta:
        db_table = 'procurement_order_item'
        verbose_name = _('Bestellposition')
        verbose_name_plural = _('Bestellpositionen')
        ordering = ['id']

    def __str__(self):
        return f"{self.item_name} ({self.quantity} {self.unit})"

    def get_total_price(self):
        """Berechnet Gesamtpreis der Position"""
        return self.quantity * self.unit_price

    def is_fully_received(self):
        """Prüft ob vollständig geliefert"""
        return self.quantity_received >= self.quantity

    def get_received_percentage(self):
        """Lieferfortschritt in Prozent"""
        if self.quantity == 0:
            return 0
        return int((self.quantity_received / self.quantity) * 100)


class OrderApproval(AuditedModel):
    """
    Freigabe-Stufe für Bestellungen

    Mehrstufiger Approval-Workflow
    """

    purchase_order = models.ForeignKey(
        PurchaseOrder,
        on_delete=models.CASCADE,
        related_name='approvals',
        verbose_name=_('Bestellung')
    )

    # Freigabe-Stufe
    approval_level = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name=_('Freigabestufe'),
        help_text=_('1 = Erste Stufe (z.B. Teamleiter), 2 = Zweite Stufe (z.B. Abteilungsleiter), etc.')
    )

    # Genehmiger
    approver = models.ForeignKey(
        'personnel.Person',
        on_delete=models.PROTECT,
        related_name='order_approvals',
        verbose_name=_('Genehmiger')
    )

    # Status
    status = models.CharField(
        max_length=20,
        choices=ApprovalStatus.choices,
        default=ApprovalStatus.PENDING,
        verbose_name=_('Status')
    )

    # Datum & Zeit
    requested_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Angefordert am')
    )

    decision_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Entschieden am')
    )

    # Kommentar
    comment = models.TextField(
        blank=True,
        verbose_name=_('Kommentar')
    )

    # Deadline
    deadline = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Frist'),
        help_text=_('Bis wann muss die Freigabe erfolgen?')
    )

    class Meta:
        db_table = 'procurement_order_approval'
        verbose_name = _('Freigabe')
        verbose_name_plural = _('Freigaben')
        ordering = ['approval_level', 'requested_date']
        unique_together = [['purchase_order', 'approval_level']]
        indexes = [
            models.Index(fields=['purchase_order', 'approval_level']),
            models.Index(fields=['approver', 'status']),
            models.Index(fields=['status', 'deadline']),
        ]

    def __str__(self):
        return f"{self.purchase_order.order_number} - Stufe {self.approval_level} - {self.approver}"

    def is_overdue(self):
        """Prüft ob Freigabe überfällig ist"""
        if not self.deadline:
            return False
        if self.status != ApprovalStatus.PENDING:
            return False
        from django.utils import timezone
        return timezone.now() > self.deadline


class GoodsReceipt(AuditedModel):
    """
    Wareneingang

    Dokumentiert den Erhalt von bestellten Waren
    """

    purchase_order = models.ForeignKey(
        PurchaseOrder,
        on_delete=models.PROTECT,
        related_name='goods_receipts',
        verbose_name=_('Bestellung')
    )

    # Wareneingangs-Details
    receipt_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_('Wareneingangs-Nummer'),
        help_text=_('Automatisch generiert, z.B. GR-2025-0001')
    )

    receipt_date = models.DateTimeField(
        verbose_name=_('Wareneingangsdatum')
    )

    received_by = models.ForeignKey(
        'personnel.Person',
        on_delete=models.PROTECT,
        related_name='goods_receipts',
        verbose_name=_('Empfangen von')
    )

    # Lieferung
    delivery_note_number = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Lieferschein-Nummer')
    )

    carrier = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Spediteur/Kurier')
    )

    # Qualitätsprüfung
    quality_check_passed = models.BooleanField(
        default=True,
        verbose_name=_('Qualitätsprüfung bestanden')
    )

    quality_check_notes = models.TextField(
        blank=True,
        verbose_name=_('Qualitätsprüfungs-Notizen')
    )

    # Abweichungen
    has_discrepancies = models.BooleanField(
        default=False,
        verbose_name=_('Abweichungen festgestellt')
    )

    discrepancy_notes = models.TextField(
        blank=True,
        verbose_name=_('Abweichungs-Notizen'),
        help_text=_('z.B. falsche Menge, beschädigte Ware, etc.')
    )

    # Dokumente
    delivery_note_file = models.FileField(
        upload_to='procurement/delivery_notes/%Y/%m/',
        blank=True,
        null=True,
        verbose_name=_('Lieferschein-Datei')
    )

    photos = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_('Fotos'),
        help_text=_('Liste von Foto-URLs (z.B. bei Schäden)')
    )

    # Notizen
    notes = models.TextField(
        blank=True,
        verbose_name=_('Notizen')
    )

    class Meta:
        db_table = 'procurement_goods_receipt'
        verbose_name = _('Wareneingang')
        verbose_name_plural = _('Wareneingänge')
        ordering = ['-receipt_date']
        indexes = [
            models.Index(fields=['receipt_number']),
            models.Index(fields=['purchase_order', '-receipt_date']),
            models.Index(fields=['received_by', '-receipt_date']),
        ]

    def __str__(self):
        return f"{self.receipt_number} - {self.purchase_order.order_number}"

    def save(self, *args, **kwargs):
        # Auto-generate receipt_number if not set
        if not self.receipt_number:
            from django.utils import timezone
            year = timezone.now().year
            # Get last receipt number for this year
            last_receipt = GoodsReceipt.objects.filter(
                receipt_number__startswith=f'GR-{year}-'
            ).order_by('-receipt_number').first()

            if last_receipt:
                last_num = int(last_receipt.receipt_number.split('-')[-1])
                new_num = last_num + 1
            else:
                new_num = 1

            self.receipt_number = f'GR-{year}-{new_num:04d}'

        super().save(*args, **kwargs)


class GoodsReceiptItem(TimeStampedModel):
    """
    Wareneingangs-Position

    Einzelne empfangene Artikel im Wareneingang
    """

    goods_receipt = models.ForeignKey(
        GoodsReceipt,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_('Wareneingang')
    )

    order_item = models.ForeignKey(
        OrderItem,
        on_delete=models.PROTECT,
        related_name='receipt_items',
        verbose_name=_('Bestellposition')
    )

    # Empfangene Menge
    quantity_received = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name=_('Erhaltene Menge')
    )

    # Eingelagert
    location = models.ForeignKey(
        'locations.Location',
        on_delete=models.PROTECT,
        related_name='receipt_items',
        verbose_name=_('Eingelagert in')
    )

    # Zustand
    condition = models.CharField(
        max_length=20,
        choices=[
            ('good', _('Gut')),
            ('acceptable', _('Akzeptabel')),
            ('damaged', _('Beschädigt')),
            ('defective', _('Defekt')),
        ],
        default='good',
        verbose_name=_('Zustand')
    )

    # Chargeninformationen (falls relevant)
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

    # Notizen
    notes = models.TextField(
        blank=True,
        verbose_name=_('Notizen')
    )

    class Meta:
        db_table = 'procurement_goods_receipt_item'
        verbose_name = _('Wareneingangs-Position')
        verbose_name_plural = _('Wareneingangs-Positionen')
        ordering = ['id']

    def __str__(self):
        return f"{self.order_item.item_name} - {self.quantity_received} {self.order_item.unit}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        # Update quantity_received in OrderItem
        self.order_item.quantity_received = self.order_item.receipt_items.aggregate(
            total=Sum('quantity_received')
        )['total'] or 0
        self.order_item.save()
