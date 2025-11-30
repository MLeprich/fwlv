"""
Admin Interface für Procurement App (Bestellwesen)
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.db.models import Sum, F, Q
from django.utils import timezone
from .models import (
    PurchaseOrder,
    OrderItem,
    OrderApproval,
    GoodsReceipt,
    GoodsReceiptItem,
    OrderStatus,
    OrderPriority,
    ApprovalStatus,
    DeliveryStatus
)


class OrderItemInline(admin.TabularInline):
    """Inline Admin für Bestellpositionen"""
    model = OrderItem
    extra = 1
    fields = ('item_name', 'quantity', 'unit', 'unit_price', 'quantity_received', 'target_location', 'supplier_item_number')
    readonly_fields = ('quantity_received',)


class OrderApprovalInline(admin.TabularInline):
    """Inline Admin für Freigaben"""
    model = OrderApproval
    extra = 0
    fields = ('approval_level', 'approver', 'status', 'decision_date', 'comment', 'deadline')
    readonly_fields = ('requested_date',)


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    """Admin für Bestellungen"""

    list_display = (
        'order_number',
        'title',
        'status_badge',
        'priority_badge',
        'supplier',
        'requested_by',
        'requested_date',
        'approval_progress',
        'delivery_progress',
        'total_cost_display',
        'expected_delivery_date',
    )

    list_filter = (
        'status',
        'priority',
        'delivery_status',
        'requested_date',
        'supplier',
    )

    search_fields = (
        'order_number',
        'title',
        'description',
        'supplier__name',
        'requested_by__first_name',
        'requested_by__last_name',
        'invoice_number',
    )

    readonly_fields = (
        'order_number',
        'created_at',
        'updated_at',
        'created_by',
        'updated_by',
        'subtotal',
        'tax_amount',
        'total_cost',
        'approval_progress_bar',
        'delivery_progress_bar',
    )

    fieldsets = (
        (_('Bestellung'), {
            'fields': (
                'order_number',
                'title',
                'description',
                'status',
                'priority',
            )
        }),
        (_('Lieferant & Lieferung'), {
            'fields': (
                'supplier',
                'delivery_location',
                'delivery_status',
                'expected_delivery_date',
                'actual_delivery_date',
                'tracking_number',
            )
        }),
        (_('Anforderung & Genehmigung'), {
            'fields': (
                'requested_by',
                'requested_date',
                'approved_by',
                'approved_date',
                'ordered_date',
            )
        }),
        (_('Kosten'), {
            'fields': (
                'subtotal',
                'tax_rate',
                'tax_amount',
                'shipping_cost',
                'total_cost',
                'budget_code',
            )
        }),
        (_('Dokumente'), {
            'fields': (
                'invoice_number',
                'invoice_date',
                'invoice_file',
                'order_confirmation_file',
            )
        }),
        (_('Notizen'), {
            'fields': (
                'notes',
                'rejection_reason',
            )
        }),
        (_('Fortschritt'), {
            'fields': (
                'approval_progress_bar',
                'delivery_progress_bar',
            ),
            'classes': ('collapse',)
        }),
        (_('Metadaten'), {
            'fields': (
                'created_at',
                'updated_at',
                'created_by',
                'updated_by',
            ),
            'classes': ('collapse',)
        }),
    )

    inlines = [OrderItemInline, OrderApprovalInline]

    date_hierarchy = 'requested_date'

    actions = ['mark_as_approved', 'mark_as_ordered', 'mark_as_received', 'mark_as_cancelled']

    def get_queryset(self, request):
        """Optimiere Queries"""
        qs = super().get_queryset(request)
        return qs.select_related(
            'supplier',
            'requested_by',
            'approved_by',
            'delivery_location',
            'created_by',
            'updated_by'
        ).prefetch_related(
            'items',
            'approvals',
            'goods_receipts'
        )

    @admin.display(description=_('Status'))
    def status_badge(self, obj):
        """Farbiger Badge für Status"""
        status_colors = {
            OrderStatus.DRAFT: '#9ca3af',
            OrderStatus.SUBMITTED: '#3b82f6',
            OrderStatus.PENDING_APPROVAL: '#f59e0b',
            OrderStatus.APPROVED: '#10b981',
            OrderStatus.REJECTED: '#ef4444',
            OrderStatus.ORDERED: '#8b5cf6',
            OrderStatus.PARTIALLY_RECEIVED: '#06b6d4',
            OrderStatus.RECEIVED: '#22c55e',
            OrderStatus.CANCELLED: '#9ca3af',
            OrderStatus.CLOSED: '#6b7280',
        }
        color = status_colors.get(obj.status, '#9ca3af')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )

    @admin.display(description=_('Priorität'))
    def priority_badge(self, obj):
        """Badge für Priorität"""
        priority_colors = {
            OrderPriority.LOW: '#9ca3af',
            OrderPriority.NORMAL: '#3b82f6',
            OrderPriority.HIGH: '#f59e0b',
            OrderPriority.URGENT: '#ef4444',
        }
        color = priority_colors.get(obj.priority, '#9ca3af')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color, obj.get_priority_display()
        )

    @admin.display(description=_('Freigabe'))
    def approval_progress(self, obj):
        """Freigabe-Fortschritt"""
        progress = obj.get_approval_progress()
        if progress == 100:
            return format_html('<span style="color: #10b981; font-weight: bold;">✓ 100%</span>')
        elif progress > 0:
            return format_html('<span style="color: #f59e0b;">{} %</span>', progress)
        else:
            return format_html('<span style="color: #9ca3af;">0 %</span>')

    @admin.display(description=_('Lieferung'))
    def delivery_progress(self, obj):
        """Lieferfortschritt"""
        progress = obj.get_received_percentage()
        if progress == 100:
            return format_html('<span style="color: #10b981; font-weight: bold;">✓ 100%</span>')
        elif progress > 0:
            return format_html('<span style="color: #f59e0b;">{} %</span>', progress)
        else:
            return format_html('<span style="color: #9ca3af;">0 %</span>')

    @admin.display(description=_('Gesamtkosten'))
    def total_cost_display(self, obj):
        """Formatierte Gesamtkosten"""
        return format_html('<span style="font-weight: bold;">{:,.2f} €</span>', obj.total_cost)

    @admin.display(description=_('Freigabe-Fortschritt'))
    def approval_progress_bar(self, obj):
        """Fortschrittsbalken für Freigaben"""
        progress = obj.get_approval_progress()
        if progress == 100:
            color = '#10b981'
        elif progress >= 50:
            color = '#f59e0b'
        else:
            color = '#ef4444'

        return format_html(
            '<div style="width: 200px; background-color: #e5e7eb; border-radius: 3px; height: 20px; position: relative;">'
            '<div style="width: {}%; background-color: {}; border-radius: 3px; height: 20px;"></div>'
            '<span style="position: absolute; top: 0; left: 0; width: 100%; text-align: center; '
            'font-size: 12px; line-height: 20px; font-weight: bold; color: #1f2937;">{} %</span>'
            '</div>',
            progress, color, progress
        )

    @admin.display(description=_('Lieferfortschritt'))
    def delivery_progress_bar(self, obj):
        """Fortschrittsbalken für Lieferungen"""
        progress = obj.get_received_percentage()
        if progress == 100:
            color = '#10b981'
        elif progress >= 50:
            color = '#f59e0b'
        else:
            color = '#ef4444'

        return format_html(
            '<div style="width: 200px; background-color: #e5e7eb; border-radius: 3px; height: 20px; position: relative;">'
            '<div style="width: {}%; background-color: {}; border-radius: 3px; height: 20px;"></div>'
            '<span style="position: absolute; top: 0; left: 0; width: 100%; text-align: center; '
            'font-size: 12px; line-height: 20px; font-weight: bold; color: #1f2937;">{} %</span>'
            '</div>',
            progress, color, progress
        )

    @admin.action(description=_('Als freigegeben markieren'))
    def mark_as_approved(self, request, queryset):
        """Markiere Bestellungen als freigegeben"""
        updated = queryset.update(
            status=OrderStatus.APPROVED,
            approved_by=request.user.person if hasattr(request.user, 'person') else None,
            approved_date=timezone.now()
        )
        self.message_user(request, _(f'{updated} Bestellung(en) als freigegeben markiert.'))

    @admin.action(description=_('Als bestellt markieren'))
    def mark_as_ordered(self, request, queryset):
        """Markiere als bestellt"""
        from django.utils import timezone
        updated = queryset.update(
            status=OrderStatus.ORDERED,
            ordered_date=timezone.now().date(),
            delivery_status=DeliveryStatus.NOT_SHIPPED
        )
        self.message_user(request, _(f'{updated} Bestellung(en) als bestellt markiert.'))

    @admin.action(description=_('Als vollständig geliefert markieren'))
    def mark_as_received(self, request, queryset):
        """Markiere als vollständig geliefert"""
        from django.utils import timezone
        updated = queryset.update(
            status=OrderStatus.RECEIVED,
            actual_delivery_date=timezone.now().date(),
            delivery_status=DeliveryStatus.DELIVERED
        )
        self.message_user(request, _(f'{updated} Bestellung(en) als geliefert markiert.'))

    @admin.action(description=_('Als storniert markieren'))
    def mark_as_cancelled(self, request, queryset):
        """Markiere als storniert"""
        updated = queryset.update(status=OrderStatus.CANCELLED)
        self.message_user(request, _(f'{updated} Bestellung(en) storniert.'))

    def save_model(self, request, obj, form, change):
        """Setze created_by/updated_by"""
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    """Admin für Bestellpositionen"""

    list_display = (
        'purchase_order',
        'item_name',
        'quantity_display',
        'unit_price_display',
        'total_price_display',
        'received_progress',
        'target_location',
    )

    list_filter = (
        'purchase_order__status',
        'category',
        'target_location',
    )

    search_fields = (
        'item_name',
        'description',
        'supplier_item_number',
        'purchase_order__order_number',
    )

    readonly_fields = ('quantity_received',)

    fieldsets = (
        (_('Bestellung'), {
            'fields': ('purchase_order',)
        }),
        (_('Artikel'), {
            'fields': (
                'item_name',
                'description',
                'supplier_item_number',
                'category',
            )
        }),
        (_('Menge & Preis'), {
            'fields': (
                'quantity',
                'unit',
                'unit_price',
                'quantity_received',
            )
        }),
        (_('Lagerort'), {
            'fields': ('target_location',)
        }),
        (_('Notizen'), {
            'fields': ('notes',)
        }),
    )

    @admin.display(description=_('Menge'))
    def quantity_display(self, obj):
        """Formatierte Menge"""
        return f"{obj.quantity} {obj.unit}"

    @admin.display(description=_('Einzelpreis'))
    def unit_price_display(self, obj):
        """Formatierter Einzelpreis"""
        return format_html('<span>{:.2f} €</span>', obj.unit_price)

    @admin.display(description=_('Gesamtpreis'))
    def total_price_display(self, obj):
        """Gesamtpreis der Position"""
        total = obj.get_total_price()
        return format_html('<span style="font-weight: bold;">{:.2f} €</span>', total)

    @admin.display(description=_('Lieferung'))
    def received_progress(self, obj):
        """Lieferfortschritt"""
        progress = obj.get_received_percentage()
        if obj.is_fully_received():
            return format_html('<span style="color: #10b981; font-weight: bold;">✓ {}/{} {}</span>',
                             obj.quantity_received, obj.quantity, obj.unit)
        elif obj.quantity_received > 0:
            return format_html('<span style="color: #f59e0b;">{}/{} {} ({}%)</span>',
                             obj.quantity_received, obj.quantity, obj.unit, progress)
        else:
            return format_html('<span style="color: #9ca3af;">0/{} {}</span>',
                             obj.quantity, obj.unit)


@admin.register(OrderApproval)
class OrderApprovalAdmin(admin.ModelAdmin):
    """Admin für Freigaben"""

    list_display = (
        'purchase_order',
        'approval_level',
        'approver',
        'status_badge',
        'requested_date',
        'decision_date',
        'deadline_display',
    )

    list_filter = (
        'status',
        'approval_level',
        'requested_date',
        'deadline',
    )

    search_fields = (
        'purchase_order__order_number',
        'approver__first_name',
        'approver__last_name',
        'comment',
    )

    readonly_fields = ('requested_date', 'created_at', 'updated_at', 'created_by', 'updated_by')

    fieldsets = (
        (_('Bestellung'), {
            'fields': ('purchase_order', 'approval_level')
        }),
        (_('Genehmiger'), {
            'fields': ('approver',)
        }),
        (_('Status'), {
            'fields': (
                'status',
                'decision_date',
                'comment',
            )
        }),
        (_('Frist'), {
            'fields': ('deadline',)
        }),
        (_('Metadaten'), {
            'fields': (
                'requested_date',
                'created_at',
                'updated_at',
                'created_by',
                'updated_by',
            ),
            'classes': ('collapse',)
        }),
    )

    actions = ['approve_requests', 'reject_requests']

    @admin.display(description=_('Status'))
    def status_badge(self, obj):
        """Status-Badge"""
        status_colors = {
            ApprovalStatus.PENDING: '#f59e0b',
            ApprovalStatus.APPROVED: '#10b981',
            ApprovalStatus.REJECTED: '#ef4444',
            ApprovalStatus.EXPIRED: '#9ca3af',
        }
        color = status_colors.get(obj.status, '#9ca3af')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )

    @admin.display(description=_('Frist'))
    def deadline_display(self, obj):
        """Frist-Anzeige mit Überfällig-Warnung"""
        if not obj.deadline:
            return '-'
        if obj.is_overdue():
            return format_html(
                '<span style="color: #ef4444; font-weight: bold;">⚠ {} (Überfällig)</span>',
                obj.deadline.strftime('%d.%m.%Y %H:%M')
            )
        return obj.deadline.strftime('%d.%m.%Y %H:%M')

    @admin.action(description=_('Freigaben genehmigen'))
    def approve_requests(self, request, queryset):
        """Genehmige ausgewählte Freigaben"""
        updated = queryset.filter(status=ApprovalStatus.PENDING).update(
            status=ApprovalStatus.APPROVED,
            decision_date=timezone.now()
        )
        self.message_user(request, _(f'{updated} Freigabe(n) genehmigt.'))

    @admin.action(description=_('Freigaben ablehnen'))
    def reject_requests(self, request, queryset):
        """Lehne Freigaben ab"""
        updated = queryset.filter(status=ApprovalStatus.PENDING).update(
            status=ApprovalStatus.REJECTED,
            decision_date=timezone.now()
        )
        self.message_user(request, _(f'{updated} Freigabe(n) abgelehnt.'))

    def save_model(self, request, obj, form, change):
        """Setze created_by/updated_by"""
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


class GoodsReceiptItemInline(admin.TabularInline):
    """Inline Admin für Wareneingangs-Positionen"""
    model = GoodsReceiptItem
    extra = 0
    fields = ('order_item', 'quantity_received', 'location', 'condition', 'batch_number', 'expiry_date')


@admin.register(GoodsReceipt)
class GoodsReceiptAdmin(admin.ModelAdmin):
    """Admin für Wareneingänge"""

    list_display = (
        'receipt_number',
        'purchase_order',
        'receipt_date',
        'received_by',
        'quality_check_badge',
        'discrepancies_badge',
        'carrier',
    )

    list_filter = (
        'receipt_date',
        'quality_check_passed',
        'has_discrepancies',
    )

    search_fields = (
        'receipt_number',
        'purchase_order__order_number',
        'delivery_note_number',
        'carrier',
        'received_by__first_name',
        'received_by__last_name',
    )

    readonly_fields = ('receipt_number', 'created_at', 'updated_at', 'created_by', 'updated_by')

    fieldsets = (
        (_('Wareneingang'), {
            'fields': (
                'receipt_number',
                'purchase_order',
                'receipt_date',
                'received_by',
            )
        }),
        (_('Lieferung'), {
            'fields': (
                'delivery_note_number',
                'carrier',
                'delivery_note_file',
            )
        }),
        (_('Qualitätsprüfung'), {
            'fields': (
                'quality_check_passed',
                'quality_check_notes',
            )
        }),
        (_('Abweichungen'), {
            'fields': (
                'has_discrepancies',
                'discrepancy_notes',
            )
        }),
        (_('Notizen'), {
            'fields': ('notes',)
        }),
        (_('Metadaten'), {
            'fields': (
                'created_at',
                'updated_at',
                'created_by',
                'updated_by',
            ),
            'classes': ('collapse',)
        }),
    )

    inlines = [GoodsReceiptItemInline]

    date_hierarchy = 'receipt_date'

    def get_queryset(self, request):
        """Optimiere Queries"""
        qs = super().get_queryset(request)
        return qs.select_related(
            'purchase_order',
            'received_by',
            'created_by',
            'updated_by'
        ).prefetch_related('items')

    @admin.display(description=_('Qualitätsprüfung'))
    def quality_check_badge(self, obj):
        """Qualitätsprüfungs-Badge"""
        if obj.quality_check_passed:
            return format_html('<span style="color: #10b981; font-weight: bold;">✓ Bestanden</span>')
        return format_html('<span style="color: #ef4444; font-weight: bold;">✗ Nicht bestanden</span>')

    @admin.display(description=_('Abweichungen'))
    def discrepancies_badge(self, obj):
        """Abweichungs-Badge"""
        if obj.has_discrepancies:
            return format_html('<span style="color: #ef4444; font-weight: bold;">⚠ Ja</span>')
        return format_html('<span style="color: #10b981;">✓ Keine</span>')

    def save_model(self, request, obj, form, change):
        """Setze created_by/updated_by"""
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(GoodsReceiptItem)
class GoodsReceiptItemAdmin(admin.ModelAdmin):
    """Admin für Wareneingangs-Positionen"""

    list_display = (
        'goods_receipt',
        'order_item',
        'quantity_received_display',
        'condition_badge',
        'location',
        'batch_number',
        'expiry_date',
    )

    list_filter = (
        'condition',
        'goods_receipt__receipt_date',
        'location',
    )

    search_fields = (
        'goods_receipt__receipt_number',
        'order_item__item_name',
        'batch_number',
    )

    fieldsets = (
        (_('Wareneingang'), {
            'fields': ('goods_receipt', 'order_item')
        }),
        (_('Empfangen'), {
            'fields': (
                'quantity_received',
                'location',
                'condition',
            )
        }),
        (_('Chargeninformationen'), {
            'fields': (
                'batch_number',
                'expiry_date',
            )
        }),
        (_('Notizen'), {
            'fields': ('notes',)
        }),
    )

    @admin.display(description=_('Menge'))
    def quantity_received_display(self, obj):
        """Empfangene Menge"""
        return f"{obj.quantity_received} {obj.order_item.unit}"

    @admin.display(description=_('Zustand'))
    def condition_badge(self, obj):
        """Zustand-Badge"""
        condition_colors = {
            'good': '#10b981',
            'acceptable': '#f59e0b',
            'damaged': '#ef4444',
            'defective': '#dc2626',
        }
        color = condition_colors.get(obj.condition, '#9ca3af')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color, obj.get_condition_display()
        )
