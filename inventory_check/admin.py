"""
Admin Interface für Inventory Check App (Inventur)
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.utils import timezone
from .models import (
    InventoryCheck,
    InventoryCheckItem,
    InventoryDiscrepancy,
    InventoryAdjustment,
    InventoryCheckStatus,
    InventoryCheckType,
    DiscrepancyType
)


class InventoryCheckItemInline(admin.TabularInline):
    """Inline Admin für Inventur-Positionen"""
    model = InventoryCheckItem
    extra = 0
    fields = ('item_name', 'location', 'expected_quantity', 'actual_quantity', 'variance_quantity', 'is_counted', 'has_discrepancy')
    readonly_fields = ('variance_quantity', 'has_discrepancy')


class InventoryDiscrepancyInline(admin.TabularInline):
    """Inline Admin für Abweichungen"""
    model = InventoryDiscrepancy
    extra = 0
    fields = ('discrepancy_type', 'quantity', 'cause', 'correction_applied')
    readonly_fields = ('found_date',)


@admin.register(InventoryCheck)
class InventoryCheckAdmin(admin.ModelAdmin):
    """Admin für Inventuren"""

    list_display = (
        'check_number',
        'title',
        'check_type_badge',
        'status_badge',
        'responsible_person',
        'scheduled_start_date',
        'scheduled_end_date',
        'progress_bar',
        'discrepancy_rate',
        'overdue_badge',
    )

    list_filter = (
        'status',
        'check_type',
        'scheduled_start_date',
        'location',
        'responsible_person',
    )

    search_fields = (
        'check_number',
        'title',
        'description',
        'responsible_person__first_name',
        'responsible_person__last_name',
    )

    readonly_fields = (
        'check_number',
        'total_items',
        'counted_items',
        'items_with_discrepancies',
        'created_at',
        'updated_at',
        'created_by',
        'updated_by',
        'progress_display',
        'discrepancy_display',
    )

    fieldsets = (
        (_('Inventur'), {
            'fields': (
                'check_number',
                'title',
                'description',
                'check_type',
                'status',
            )
        }),
        (_('Verantwortung'), {
            'fields': (
                'responsible_person',
                'team_members',
            )
        }),
        (_('Zeitplanung'), {
            'fields': (
                'scheduled_start_date',
                'scheduled_end_date',
                'actual_start_date',
                'actual_end_date',
            )
        }),
        (_('Umfang'), {
            'fields': (
                'location',
                'module_filter',
            )
        }),
        (_('Fortschritt'), {
            'fields': (
                'total_items',
                'counted_items',
                'items_with_discrepancies',
                'progress_display',
                'discrepancy_display',
            )
        }),
        (_('Genehmigung'), {
            'fields': (
                'approved_by',
                'approved_date',
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

    filter_horizontal = ('team_members',)

    date_hierarchy = 'scheduled_start_date'

    actions = ['mark_as_in_progress', 'mark_as_counting_complete', 'mark_as_completed', 'update_all_progress']

    def get_queryset(self, request):
        """Optimiere Queries"""
        qs = super().get_queryset(request)
        return qs.select_related(
            'responsible_person',
            'location',
            'approved_by',
            'created_by',
            'updated_by'
        ).prefetch_related(
            'team_members',
            'items',
            'adjustments'
        )

    @admin.display(description=_('Art'))
    def check_type_badge(self, obj):
        """Badge für Inventurart"""
        type_colors = {
            InventoryCheckType.FULL: '#8b5cf6',
            InventoryCheckType.PARTIAL: '#3b82f6',
            InventoryCheckType.SPOT_CHECK: '#f59e0b',
            InventoryCheckType.CYCLE_COUNT: '#10b981',
            InventoryCheckType.ANNUAL: '#ef4444',
        }
        color = type_colors.get(obj.check_type, '#9ca3af')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            color, obj.get_check_type_display()
        )

    @admin.display(description=_('Status'))
    def status_badge(self, obj):
        """Farbiger Badge für Status"""
        status_colors = {
            InventoryCheckStatus.PLANNED: '#9ca3af',
            InventoryCheckStatus.IN_PROGRESS: '#3b82f6',
            InventoryCheckStatus.COUNTING_COMPLETE: '#f59e0b',
            InventoryCheckStatus.REVIEW: '#8b5cf6',
            InventoryCheckStatus.ADJUSTMENTS_PENDING: '#ef4444',
            InventoryCheckStatus.COMPLETED: '#10b981',
            InventoryCheckStatus.CANCELLED: '#6b7280',
        }
        color = status_colors.get(obj.status, '#9ca3af')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )

    @admin.display(description=_('Fortschritt'))
    def progress_bar(self, obj):
        """Fortschrittsbalken"""
        progress = obj.get_progress_percentage()
        if progress == 100:
            color = '#10b981'
        elif progress >= 50:
            color = '#f59e0b'
        else:
            color = '#ef4444'

        return format_html(
            '<div style="width: 120px; background-color: #e5e7eb; border-radius: 3px; height: 18px; position: relative;">'
            '<div style="width: {}%; background-color: {}; border-radius: 3px; height: 18px;"></div>'
            '<span style="position: absolute; top: 0; left: 0; width: 100%; text-align: center; '
            'font-size: 11px; line-height: 18px; font-weight: bold; color: #1f2937;">{}/{} ({}%)</span>'
            '</div>',
            progress, color, obj.counted_items, obj.total_items, progress
        )

    @admin.display(description=_('Abweichungsquote'))
    def discrepancy_rate(self, obj):
        """Abweichungsquote"""
        rate = obj.get_discrepancy_percentage()
        if rate == 0:
            return format_html('<span style="color: #10b981; font-weight: bold;">✓ 0%</span>')
        elif rate <= 5:
            return format_html('<span style="color: #f59e0b;">{} %</span>', rate)
        else:
            return format_html('<span style="color: #ef4444; font-weight: bold;">⚠ {} %</span>', rate)

    @admin.display(description=_('Frist'))
    def overdue_badge(self, obj):
        """Überfällig-Anzeige"""
        if obj.is_overdue():
            return format_html('<span style="color: #ef4444; font-weight: bold;">⚠ Überfällig</span>')
        return format_html('<span style="color: #10b981;">✓ Im Plan</span>')

    @admin.display(description=_('Fortschritts-Details'))
    def progress_display(self, obj):
        """Detaillierte Fortschritts-Anzeige"""
        progress = obj.get_progress_percentage()
        return format_html(
            '<div style="margin-bottom: 10px;">'
            '<div style="width: 300px; background-color: #e5e7eb; border-radius: 3px; height: 24px; position: relative;">'
            '<div style="width: {}%; background-color: #3b82f6; border-radius: 3px; height: 24px;"></div>'
            '<span style="position: absolute; top: 0; left: 0; width: 100%; text-align: center; '
            'font-size: 13px; line-height: 24px; font-weight: bold; color: #1f2937;">{} von {} Artikeln ({}%)</span>'
            '</div>'
            '</div>',
            progress, obj.counted_items, obj.total_items, progress
        )

    @admin.display(description=_('Abweichungs-Details'))
    def discrepancy_display(self, obj):
        """Detaillierte Abweichungs-Anzeige"""
        rate = obj.get_discrepancy_percentage()
        if obj.counted_items == 0:
            return format_html('<span style="color: #9ca3af;">Noch keine Zählungen</span>')

        if rate == 0:
            color = '#10b981'
            icon = '✓'
        elif rate <= 5:
            color = '#f59e0b'
            icon = '⚠'
        else:
            color = '#ef4444'
            icon = '⚠'

        return format_html(
            '<div style="color: {}; font-weight: bold;">{} {} von {} gezählten Artikeln ({} %)</div>',
            color, icon, obj.items_with_discrepancies, obj.counted_items, rate
        )

    @admin.action(description=_('Als "In Bearbeitung" markieren'))
    def mark_as_in_progress(self, request, queryset):
        """Markiere als in Bearbeitung"""
        updated = queryset.update(
            status=InventoryCheckStatus.IN_PROGRESS,
            actual_start_date=timezone.now()
        )
        self.message_user(request, _(f'{updated} Inventur(en) als in Bearbeitung markiert.'))

    @admin.action(description=_('Als "Zählung abgeschlossen" markieren'))
    def mark_as_counting_complete(self, request, queryset):
        """Markiere Zählung als abgeschlossen"""
        updated = queryset.update(status=InventoryCheckStatus.COUNTING_COMPLETE)
        self.message_user(request, _(f'{updated} Inventur(en) - Zählung abgeschlossen.'))

    @admin.action(description=_('Als abgeschlossen markieren'))
    def mark_as_completed(self, request, queryset):
        """Markiere als abgeschlossen"""
        updated = queryset.update(
            status=InventoryCheckStatus.COMPLETED,
            actual_end_date=timezone.now(),
            approved_by=request.user.person if hasattr(request.user, 'person') else None,
            approved_date=timezone.now()
        )
        self.message_user(request, _(f'{updated} Inventur(en) abgeschlossen.'))

    @admin.action(description=_('Fortschritt aktualisieren'))
    def update_all_progress(self, request, queryset):
        """Aktualisiere Fortschritt für alle ausgewählten Inventuren"""
        for inventory_check in queryset:
            inventory_check.update_progress()
        self.message_user(request, _(f'Fortschritt für {queryset.count()} Inventur(en) aktualisiert.'))

    def save_model(self, request, obj, form, change):
        """Setze created_by/updated_by"""
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(InventoryCheckItem)
class InventoryCheckItemAdmin(admin.ModelAdmin):
    """Admin für Inventur-Positionen"""

    list_display = (
        'inventory_check',
        'item_name',
        'location',
        'expected_quantity_display',
        'actual_quantity_display',
        'variance_display',
        'counted_badge',
        'discrepancy_badge',
        'counted_by',
    )

    list_filter = (
        'is_counted',
        'has_discrepancy',
        'requires_recount',
        'inventory_check__status',
        'location',
        'counted_by',
    )

    search_fields = (
        'item_name',
        'item_number',
        'inventory_check__check_number',
        'notes',
    )

    readonly_fields = ('variance_quantity', 'has_discrepancy', 'created_at', 'updated_at', 'created_by', 'updated_by')

    fieldsets = (
        (_('Inventur'), {
            'fields': ('inventory_check',)
        }),
        (_('Artikel'), {
            'fields': (
                'item_name',
                'item_number',
                'location',
                'unit',
            )
        }),
        (_('Bestand'), {
            'fields': (
                'expected_quantity',
                'actual_quantity',
                'variance_quantity',
                'has_discrepancy',
            )
        }),
        (_('Zählung'), {
            'fields': (
                'is_counted',
                'counted_by',
                'counted_date',
            )
        }),
        (_('Nachzählung'), {
            'fields': (
                'requires_recount',
                'recount_done',
                'recounted_by',
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

    inlines = [InventoryDiscrepancyInline]

    actions = ['mark_as_counted', 'mark_requires_recount']

    @admin.display(description=_('Soll'))
    def expected_quantity_display(self, obj):
        """Formatierter Sollbestand"""
        return f"{obj.expected_quantity} {obj.unit}"

    @admin.display(description=_('Ist'))
    def actual_quantity_display(self, obj):
        """Formatierter Istbestand"""
        if obj.actual_quantity is None:
            return format_html('<span style="color: #9ca3af;">-</span>')
        return f"{obj.actual_quantity} {obj.unit}"

    @admin.display(description=_('Abweichung'))
    def variance_display(self, obj):
        """Abweichungs-Anzeige"""
        if not obj.is_counted:
            return format_html('<span style="color: #9ca3af;">-</span>')

        variance_pct = obj.get_variance_percentage()

        if obj.variance_quantity > 0:
            return format_html(
                '<span style="color: #10b981; font-weight: bold;">+{} {} (+{:.1f}%)</span>',
                obj.variance_quantity, obj.unit, variance_pct
            )
        elif obj.variance_quantity < 0:
            return format_html(
                '<span style="color: #ef4444; font-weight: bold;">{} {} ({:.1f}%)</span>',
                obj.variance_quantity, obj.unit, variance_pct
            )
        else:
            return format_html('<span style="color: #10b981;">✓ 0</span>')

    @admin.display(description=_('Gezählt'))
    def counted_badge(self, obj):
        """Gezählt-Badge"""
        if obj.is_counted:
            return format_html('<span style="color: #10b981; font-weight: bold;">✓</span>')
        return format_html('<span style="color: #9ca3af;">○</span>')

    @admin.display(description=_('Abweichung'))
    def discrepancy_badge(self, obj):
        """Abweichungs-Badge"""
        if not obj.is_counted:
            return format_html('<span style="color: #9ca3af;">-</span>')
        if obj.has_discrepancy:
            return format_html('<span style="color: #ef4444; font-weight: bold;">⚠</span>')
        return format_html('<span style="color: #10b981;">✓</span>')

    @admin.action(description=_('Als gezählt markieren'))
    def mark_as_counted(self, request, queryset):
        """Markiere als gezählt"""
        updated = queryset.update(
            is_counted=True,
            counted_by=request.user.person if hasattr(request.user, 'person') else None,
            counted_date=timezone.now()
        )
        self.message_user(request, _(f'{updated} Position(en) als gezählt markiert.'))

    @admin.action(description=_('Nachzählung erforderlich'))
    def mark_requires_recount(self, request, queryset):
        """Markiere als nachzählungs-pflichtig"""
        updated = queryset.update(requires_recount=True)
        self.message_user(request, _(f'{updated} Position(en) erfordern Nachzählung.'))

    def save_model(self, request, obj, form, change):
        """Setze created_by/updated_by"""
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(InventoryDiscrepancy)
class InventoryDiscrepancyAdmin(admin.ModelAdmin):
    """Admin für Inventur-Abweichungen"""

    list_display = (
        'check_item',
        'discrepancy_type_badge',
        'quantity_display',
        'value_display',
        'found_by',
        'found_date',
        'correction_badge',
    )

    list_filter = (
        'discrepancy_type',
        'correction_applied',
        'found_date',
        'found_by',
    )

    search_fields = (
        'check_item__item_name',
        'check_item__inventory_check__check_number',
        'cause',
        'corrective_action',
    )

    readonly_fields = ('found_date', 'total_value', 'created_at', 'updated_at', 'created_by', 'updated_by')

    fieldsets = (
        (_('Inventur-Position'), {
            'fields': ('check_item',)
        }),
        (_('Abweichung'), {
            'fields': (
                'discrepancy_type',
                'quantity',
                'cause',
            )
        }),
        (_('Feststellung'), {
            'fields': (
                'found_by',
                'found_date',
            )
        }),
        (_('Wert'), {
            'fields': (
                'unit_value',
                'total_value',
            )
        }),
        (_('Korrektur'), {
            'fields': (
                'corrective_action',
                'correction_applied',
                'correction_date',
                'corrected_by',
            )
        }),
        (_('Notizen'), {
            'fields': ('photos',)
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

    date_hierarchy = 'found_date'

    actions = ['mark_as_corrected']

    @admin.display(description=_('Art'))
    def discrepancy_type_badge(self, obj):
        """Badge für Abweichungsart"""
        type_colors = {
            DiscrepancyType.SURPLUS: '#10b981',
            DiscrepancyType.SHORTAGE: '#ef4444',
            DiscrepancyType.DAMAGED: '#f59e0b',
            DiscrepancyType.EXPIRED: '#dc2626',
            DiscrepancyType.MISLABELED: '#8b5cf6',
            DiscrepancyType.MISLOCATED: '#3b82f6',
        }
        color = type_colors.get(obj.discrepancy_type, '#9ca3af')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            color, obj.get_discrepancy_type_display()
        )

    @admin.display(description=_('Menge'))
    def quantity_display(self, obj):
        """Formatierte Menge"""
        return f"{obj.quantity} {obj.check_item.unit}"

    @admin.display(description=_('Wert'))
    def value_display(self, obj):
        """Formatierter Wert"""
        if obj.total_value is None:
            return '-'
        return format_html('<span style="font-weight: bold;">{:,.2f} €</span>', obj.total_value)

    @admin.display(description=_('Korrektur'))
    def correction_badge(self, obj):
        """Korrektur-Status"""
        if obj.correction_applied:
            return format_html('<span style="color: #10b981; font-weight: bold;">✓ Korrigiert</span>')
        return format_html('<span style="color: #ef4444;">✗ Offen</span>')

    @admin.action(description=_('Als korrigiert markieren'))
    def mark_as_corrected(self, request, queryset):
        """Markiere als korrigiert"""
        updated = queryset.update(
            correction_applied=True,
            correction_date=timezone.now(),
            corrected_by=request.user.person if hasattr(request.user, 'person') else None
        )
        self.message_user(request, _(f'{updated} Abweichung(en) als korrigiert markiert.'))

    def save_model(self, request, obj, form, change):
        """Setze created_by/updated_by"""
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(InventoryAdjustment)
class InventoryAdjustmentAdmin(admin.ModelAdmin):
    """Admin für Korrekturbuchungen"""

    list_display = (
        'adjustment_number',
        'inventory_check',
        'check_item',
        'adjustment_quantity_display',
        'adjustment_date',
        'approved_badge',
        'applied_badge',
    )

    list_filter = (
        'applied',
        'adjustment_date',
        'inventory_check__status',
        'approved_by',
    )

    search_fields = (
        'adjustment_number',
        'check_item__item_name',
        'inventory_check__check_number',
        'reason',
    )

    readonly_fields = ('adjustment_number', 'adjustment_quantity', 'created_at', 'updated_at', 'created_by', 'updated_by')

    fieldsets = (
        (_('Korrekturbuchung'), {
            'fields': (
                'adjustment_number',
                'inventory_check',
                'check_item',
                'discrepancy',
            )
        }),
        (_('Buchung'), {
            'fields': (
                'adjustment_date',
                'old_quantity',
                'new_quantity',
                'adjustment_quantity',
                'reason',
            )
        }),
        (_('Genehmigung'), {
            'fields': (
                'approved_by',
                'approved_date',
            )
        }),
        (_('Durchführung'), {
            'fields': (
                'applied',
                'applied_date',
            )
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

    date_hierarchy = 'adjustment_date'

    actions = ['approve_adjustments', 'apply_adjustments']

    @admin.display(description=_('Korrekturbetrag'))
    def adjustment_quantity_display(self, obj):
        """Formatierter Korrekturbetrag"""
        if obj.adjustment_quantity > 0:
            return format_html(
                '<span style="color: #10b981; font-weight: bold;">+{} {}</span>',
                obj.adjustment_quantity, obj.check_item.unit
            )
        elif obj.adjustment_quantity < 0:
            return format_html(
                '<span style="color: #ef4444; font-weight: bold;">{} {}</span>',
                obj.adjustment_quantity, obj.check_item.unit
            )
        else:
            return format_html('<span>0 {}</span>', obj.check_item.unit)

    @admin.display(description=_('Genehmigt'))
    def approved_badge(self, obj):
        """Genehmigungs-Badge"""
        if obj.approved_by:
            return format_html('<span style="color: #10b981; font-weight: bold;">✓</span>')
        return format_html('<span style="color: #9ca3af;">○</span>')

    @admin.display(description=_('Angewendet'))
    def applied_badge(self, obj):
        """Anwendungs-Badge"""
        if obj.applied:
            return format_html('<span style="color: #10b981; font-weight: bold;">✓</span>')
        return format_html('<span style="color: #9ca3af;">○</span>')

    @admin.action(description=_('Korrekturen genehmigen'))
    def approve_adjustments(self, request, queryset):
        """Genehmige Korrekturen"""
        updated = queryset.update(
            approved_by=request.user.person if hasattr(request.user, 'person') else None,
            approved_date=timezone.now()
        )
        self.message_user(request, _(f'{updated} Korrektur(en) genehmigt.'))

    @admin.action(description=_('Korrekturen anwenden'))
    def apply_adjustments(self, request, queryset):
        """Wende Korrekturen an"""
        updated = queryset.filter(approved_by__isnull=False).update(
            applied=True,
            applied_date=timezone.now()
        )
        not_approved = queryset.filter(approved_by__isnull=True).count()

        self.message_user(request, _(f'{updated} Korrektur(en) angewendet.'))
        if not_approved > 0:
            self.message_user(request, _(f'{not_approved} Korrektur(en) konnten nicht angewendet werden (nicht genehmigt).'), level='WARNING')

    def save_model(self, request, obj, form, change):
        """Setze created_by/updated_by"""
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
