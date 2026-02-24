"""
Admin Interface für Fahrzeugübernahme App
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.db.models import Count, Q
from .models import (
    ChecklistTemplate,
    ChecklistTemplateCategory,
    ChecklistTemplateItem,
    VehicleHandover,
    HandoverChecklist,
    HandoverPhoto,
    HandoverDefect,
    HandoverStatus,
    DefectSeverity,
    Vehicle360Photo,
    Vehicle360Hotspot,
    HotspotImage,
)


# ===== Checklisten-Templates =====

class ChecklistTemplateItemInline(admin.TabularInline):
    """Inline Admin für Template-Items"""
    model = ChecklistTemplateItem
    extra = 1
    fields = ('order', 'name', 'expected_quantity', 'requires_serial', 'description')
    ordering = ['order', 'name']


class ChecklistTemplateCategoryInline(admin.TabularInline):
    """Inline Admin für Template-Kategorien"""
    model = ChecklistTemplateCategory
    extra = 1
    fields = ('order', 'name', 'description')
    ordering = ['order', 'name']
    show_change_link = True


@admin.register(ChecklistTemplate)
class ChecklistTemplateAdmin(admin.ModelAdmin):
    """Admin für Checklisten-Vorlagen"""

    list_display = (
        'name',
        'category_count',
        'item_count',
        'vehicle_types_display',
        'is_default_badge',
        'is_active_badge',
        'usage_count',
        'last_used',
    )

    list_filter = (
        'is_active',
        'is_default',
        'created_at',
    )

    search_fields = (
        'name',
        'description',
    )

    readonly_fields = (
        'usage_count',
        'last_used',
        'created_at',
        'updated_at',
        'created_by',
        'updated_by',
    )

    fieldsets = (
        (_('Grundinformationen'), {
            'fields': (
                'name',
                'description',
            )
        }),
        (_('Zuordnung'), {
            'fields': (
                'vehicle_types',
                'is_default',
                'is_active',
            )
        }),
        (_('Statistik'), {
            'fields': (
                'usage_count',
                'last_used',
            ),
            'classes': ('collapse',),
        }),
        (_('Audit-Informationen'), {
            'fields': (
                'created_at',
                'created_by',
                'updated_at',
                'updated_by',
            ),
            'classes': ('collapse',),
        }),
    )

    inlines = [ChecklistTemplateCategoryInline]

    actions = ['duplicate_templates', 'activate_templates', 'deactivate_templates']

    def category_count(self, obj):
        """Anzahl Kategorien"""
        return obj.get_category_count()
    category_count.short_description = _('Kategorien')

    def item_count(self, obj):
        """Anzahl Items"""
        return obj.get_item_count()
    item_count.short_description = _('Items')

    def vehicle_types_display(self, obj):
        """Fahrzeugtypen anzeigen"""
        if obj.vehicle_types:
            return ', '.join(obj.vehicle_types)
        return '-'
    vehicle_types_display.short_description = _('Fahrzeugtypen')

    def is_default_badge(self, obj):
        """Standard-Badge"""
        if obj.is_default:
            return format_html(
                '<span style="background-color: #10b981; color: white; padding: 3px 7px; '
                'border-radius: 3px; font-size: 11px;">✓ Standard</span>'
            )
        return '-'
    is_default_badge.short_description = _('Standard')

    def is_active_badge(self, obj):
        """Aktiv-Badge"""
        if obj.is_active:
            return format_html(
                '<span style="background-color: #10b981; color: white; padding: 3px 7px; '
                'border-radius: 3px; font-size: 11px;">✓ Aktiv</span>'
            )
        return format_html(
            '<span style="background-color: #6b7280; color: white; padding: 3px 7px; '
            'border-radius: 3px; font-size: 11px;">○ Inaktiv</span>'
        )
    is_active_badge.short_description = _('Status')

    def duplicate_templates(self, request, queryset):
        """Templates duplizieren"""
        count = 0
        for template in queryset:
            template.duplicate()
            count += 1
        self.message_user(request, _(f'{count} Template(s) wurden dupliziert.'))
    duplicate_templates.short_description = _('Ausgewählte Templates duplizieren')

    def activate_templates(self, request, queryset):
        """Templates aktivieren"""
        count = queryset.update(is_active=True)
        self.message_user(request, _(f'{count} Template(s) wurden aktiviert.'))
    activate_templates.short_description = _('Ausgewählte Templates aktivieren')

    def deactivate_templates(self, request, queryset):
        """Templates deaktivieren"""
        count = queryset.update(is_active=False)
        self.message_user(request, _(f'{count} Template(s) wurden deaktiviert.'))
    deactivate_templates.short_description = _('Ausgewählte Templates deaktivieren')


@admin.register(ChecklistTemplateCategory)
class ChecklistTemplateCategoryAdmin(admin.ModelAdmin):
    """Admin für Template-Kategorien"""

    list_display = (
        'name',
        'template',
        'order',
        'item_count',
    )

    list_filter = (
        'template',
    )

    search_fields = (
        'name',
        'description',
        'template__name',
    )

    fields = (
        'template',
        'name',
        'order',
        'description',
    )

    inlines = [ChecklistTemplateItemInline]

    def item_count(self, obj):
        """Anzahl Items"""
        return obj.items.count()
    item_count.short_description = _('Items')


@admin.register(ChecklistTemplateItem)
class ChecklistTemplateItemAdmin(admin.ModelAdmin):
    """Admin für Template-Items"""

    list_display = (
        'name',
        'category',
        'order',
        'expected_quantity',
        'requires_serial_badge',
    )

    list_filter = (
        'category__template',
        'category',
        'requires_serial',
    )

    search_fields = (
        'name',
        'description',
        'category__name',
    )

    fields = (
        'category',
        'name',
        'order',
        'expected_quantity',
        'requires_serial',
        'description',
    )

    def requires_serial_badge(self, obj):
        """Seriennummer-Badge"""
        if obj.requires_serial:
            return format_html(
                '<span style="background-color: #f59e0b; color: white; padding: 3px 7px; '
                'border-radius: 3px; font-size: 11px;">SN</span>'
            )
        return '-'
    requires_serial_badge.short_description = _('Seriennr.')


# ===== Fahrzeugübergaben =====

class HandoverChecklistInline(admin.TabularInline):
    """Inline Admin für Checklisten-Items"""
    model = HandoverChecklist
    extra = 0
    fields = ('order', 'category', 'item_name', 'checked', 'present', 'functional', 'serial_number', 'notes')
    ordering = ['order', 'category', 'item_name']


class HandoverPhotoInline(admin.TabularInline):
    """Inline Admin für Fotos"""
    model = HandoverPhoto
    extra = 0
    fields = ('order', 'photo_type', 'image', 'description', 'related_defect')
    readonly_fields = ('created_at',)
    ordering = ['order', 'photo_type']


class HandoverDefectInline(admin.TabularInline):
    """Inline Admin für Mängel"""
    model = HandoverDefect
    extra = 0
    fields = ('title', 'severity', 'category', 'affects_operational_readiness', 'repaired', 'repaired_by')
    readonly_fields = ('created_at',)
    ordering = ['-severity', '-created_at']


@admin.register(VehicleHandover)
class VehicleHandoverAdmin(admin.ModelAdmin):
    """Admin für Fahrzeugübergaben"""

    list_display = (
        'vehicle',
        'handover_type_badge',
        'handover_to',
        'handover_date',
        'status_badge',
        'odometer_reading_display',
        'fuel_level_display',
        'defects_badge',
        'checklist_progress',
        'photo_count_display',
        'completeness_badge',
    )

    list_filter = (
        'status',
        'handover_type',
        'has_defects',
        'completeness_check_done',
        'all_items_present',
        'handover_date',
        'vehicle__vehicle_type',
    )

    search_fields = (
        'vehicle__license_plate',
        'vehicle__radio_callsign',
        'handover_to__first_name',
        'handover_to__last_name',
        'notes',
    )

    readonly_fields = (
        'created_at',
        'updated_at',
        'created_by',
        'updated_by',
        'checklist_progress',
        'photo_count_display',
        'completeness_status',
    )

    fieldsets = (
        (_('Fahrzeug & Personen'), {
            'fields': (
                'vehicle',
                'handover_to',
                'location',
            )
        }),
        (_('Übergabe-Details'), {
            'fields': (
                'handover_type',
                'handover_date',
                'status',
                'odometer_reading',
                'fuel_level',
            )
        }),
        (_('Zustand'), {
            'fields': (
                'cleanliness_interior',
                'cleanliness_exterior',
                'completeness_check_done',
                'all_items_present',
            )
        }),
        (_('Mängel'), {
            'fields': (
                'has_defects',
                'defects_count',
            )
        }),
        (_('Bestätigung'), {
            'fields': (
                'confirmed_by_receiver',
            )
        }),
        (_('Bemerkungen'), {
            'fields': ('notes',)
        }),
        (_('Fortschritt'), {
            'fields': (
                'checklist_progress',
                'photo_count_display',
                'completeness_status',
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

    inlines = [HandoverChecklistInline, HandoverPhotoInline, HandoverDefectInline]

    date_hierarchy = 'handover_date'

    actions = ['mark_as_completed', 'mark_as_defects_noted', 'mark_as_cancelled']

    def get_queryset(self, request):
        """Optimiere Queries mit prefetch"""
        qs = super().get_queryset(request)
        return qs.select_related(
            'vehicle',
            'handover_to',
            'location',
            'created_by',
            'updated_by'
        ).prefetch_related(
            'checklist_items',
            'photos',
            'defects'
        ).annotate(
            total_checklist_items=Count('checklist_items'),
            checked_items=Count('checklist_items', filter=Q(checklist_items__checked=True)),
            photo_count=Count('photos'),
        )

    @admin.display(description=_('Art'))
    def handover_type_badge(self, obj):
        """Farbiger Badge für Übergabe-Art"""
        type_colors = {
            'shift_change': '#3b82f6',
            'deployment_start': '#10b981',
            'deployment_end': '#f59e0b',
            'maintenance_in': '#ef4444',
            'maintenance_out': '#22c55e',
            'rental': '#8b5cf6',
            'return': '#06b6d4',
            'inspection': '#6366f1',
        }
        color = type_colors.get(obj.handover_type, '#9ca3af')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            color, obj.get_handover_type_display()
        )

    @admin.display(description=_('Status'))
    def status_badge(self, obj):
        """Farbiger Badge für Status"""
        status_colors = {
            HandoverStatus.IN_PROGRESS: '#f59e0b',
            HandoverStatus.COMPLETED: '#10b981',
            HandoverStatus.DEFECTS_NOTED: '#ef4444',
            HandoverStatus.CANCELLED: '#9ca3af',
        }
        color = status_colors.get(obj.status, '#9ca3af')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )

    @admin.display(description=_('KM-Stand'))
    def odometer_reading_display(self, obj):
        """Formatierter KM-Stand"""
        return format_html('<span style="font-weight: bold;">{:,} km</span>', obj.odometer_reading)

    @admin.display(description=_('Tank'))
    def fuel_level_display(self, obj):
        """Tankfüllung mit Farbe"""
        if obj.fuel_level >= 75:
            color = '#10b981'
        elif obj.fuel_level >= 50:
            color = '#f59e0b'
        elif obj.fuel_level >= 25:
            color = '#ef4444'
        else:
            color = '#dc2626'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} %</span>',
            color, obj.fuel_level
        )

    @admin.display(description=_('Mängel'))
    def defects_badge(self, obj):
        """Mängel-Anzeige"""
        if not obj.has_defects:
            return format_html('<span style="color: #10b981;">✓ Keine</span>')
        return format_html(
            '<span style="color: #ef4444; font-weight: bold;">⚠ {} Mangel{}</span>',
            obj.defects_count,
            '' if obj.defects_count == 1 else 'ängel'
        )

    @admin.display(description=_('Checkliste'))
    def checklist_progress(self, obj):
        """Checklisten-Fortschritt in Prozent"""
        completion = obj.get_checklist_completion()
        if completion == 100:
            color = '#10b981'
        elif completion >= 50:
            color = '#f59e0b'
        else:
            color = '#ef4444'
        return format_html(
            '<div style="width: 100px; background-color: #e5e7eb; border-radius: 3px; height: 18px; position: relative;">'
            '<div style="width: {}%; background-color: {}; border-radius: 3px; height: 18px;"></div>'
            '<span style="position: absolute; top: 0; left: 0; width: 100%; text-align: center; '
            'font-size: 11px; line-height: 18px; font-weight: bold; color: #1f2937;">{} %</span>'
            '</div>',
            completion, color, completion
        )

    @admin.display(description=_('Fotos'))
    def photo_count_display(self, obj):
        """Anzahl Fotos"""
        count = obj.get_photo_count()
        if count == 0:
            return format_html('<span style="color: #9ca3af;">0 Fotos</span>')
        return format_html(
            '<span style="font-weight: bold; color: #3b82f6;">📷 {} Foto{}</span>',
            count,
            '' if count == 1 else 's'
        )

    @admin.display(description=_('Vollständigkeit'))
    def completeness_badge(self, obj):
        """Vollständigkeits-Badge"""
        if obj.is_complete():
            return format_html('<span style="color: #10b981; font-weight: bold;">✓ Vollständig</span>')
        return format_html('<span style="color: #f59e0b;">⚠ Unvollständig</span>')

    @admin.display(description=_('Vollständigkeits-Status'))
    def completeness_status(self, obj):
        """Detaillierter Vollständigkeits-Status"""
        checks = []

        if obj.completeness_check_done:
            checks.append('✓ Vollständigkeitsprüfung durchgeführt')
        else:
            checks.append('✗ Vollständigkeitsprüfung fehlt')

        if obj.confirmed_by_receiver:
            checks.append('✓ Bestätigt durch Übernehmenden')
        else:
            checks.append('✗ Bestätigung Übernehmender fehlt')

        completion = obj.get_checklist_completion()
        if completion == 100:
            checks.append('✓ Checkliste vollständig')
        else:
            checks.append(f'✗ Checkliste nur {completion}% vollständig')

        return format_html('<br>'.join(checks))

    @admin.action(description=_('Als abgeschlossen markieren'))
    def mark_as_completed(self, request, queryset):
        """Markiere ausgewählte Übergaben als abgeschlossen"""
        updated = queryset.update(status=HandoverStatus.COMPLETED)
        self.message_user(request, _(f'{updated} Übergabe(n) als abgeschlossen markiert.'))

    @admin.action(description=_('Als mit Mängeln abgeschlossen markieren'))
    def mark_as_defects_noted(self, request, queryset):
        """Markiere als mit Mängeln abgeschlossen"""
        updated = queryset.update(status=HandoverStatus.DEFECTS_NOTED, has_defects=True)
        self.message_user(request, _(f'{updated} Übergabe(n) als mit Mängeln abgeschlossen markiert.'))

    @admin.action(description=_('Als abgebrochen markieren'))
    def mark_as_cancelled(self, request, queryset):
        """Markiere als abgebrochen"""
        updated = queryset.update(status=HandoverStatus.CANCELLED)
        self.message_user(request, _(f'{updated} Übergabe(n) als abgebrochen markiert.'))

    def save_model(self, request, obj, form, change):
        """Setze created_by/updated_by"""
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(HandoverChecklist)
class HandoverChecklistAdmin(admin.ModelAdmin):
    """Admin für Checklisten-Items"""

    list_display = (
        'item_name',
        'handover',
        'category',
        'status_icon',
        'present_icon',
        'functional_icon',
        'order',
    )

    list_filter = (
        'category',
        'checked',
        'present',
        'functional',
        'handover__handover_type',
    )

    search_fields = (
        'item_name',
        'category',
        'notes',
        'serial_number',
        'handover__vehicle__license_plate',
    )

    list_editable = ('order',)

    fieldsets = (
        (_('Checklisten-Item'), {
            'fields': (
                'handover',
                'item_name',
                'category',
                'order',
            )
        }),
        (_('Status'), {
            'fields': (
                'checked',
                'present',
                'functional',
            )
        }),
        (_('Details'), {
            'fields': (
                'serial_number',
                'notes',
            )
        }),
    )

    @admin.display(description=_('Geprüft'))
    def status_icon(self, obj):
        """Icon für Geprüft-Status"""
        if obj.checked:
            return format_html('<span style="color: #10b981; font-weight: bold;">✓</span>')
        return format_html('<span style="color: #9ca3af;">○</span>')

    @admin.display(description=_('Vorhanden'))
    def present_icon(self, obj):
        """Icon für Vorhanden-Status"""
        if obj.present:
            return format_html('<span style="color: #10b981;">✓</span>')
        return format_html('<span style="color: #ef4444;">✗</span>')

    @admin.display(description=_('Funktionsfähig'))
    def functional_icon(self, obj):
        """Icon für Funktionsfähig-Status"""
        if obj.functional:
            return format_html('<span style="color: #10b981;">✓</span>')
        return format_html('<span style="color: #ef4444;">✗</span>')


@admin.register(HandoverPhoto)
class HandoverPhotoAdmin(admin.ModelAdmin):
    """Admin für Übergabe-Fotos"""

    list_display = (
        'image_thumbnail',
        'handover',
        'photo_type_badge',
        'description',
        'has_gps',
        'related_defect',
        'order',
        'created_at',
    )

    list_filter = (
        'photo_type',
        'created_at',
        'handover__handover_type',
    )

    search_fields = (
        'description',
        'handover__vehicle__license_plate',
    )

    list_editable = ('order',)

    readonly_fields = ('image_preview', 'created_at', 'updated_at')

    fieldsets = (
        (_('Foto'), {
            'fields': (
                'handover',
                'image',
                'image_preview',
                'photo_type',
                'description',
                'order',
            )
        }),
        (_('GPS-Daten'), {
            'fields': (
                'gps_latitude',
                'gps_longitude',
            ),
            'classes': ('collapse',)
        }),
        (_('Verknüpfung'), {
            'fields': ('related_defect',)
        }),
        (_('Metadaten'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    @admin.display(description=_('Vorschau'))
    def image_thumbnail(self, obj):
        """Kleine Vorschau des Bildes"""
        if obj.image:
            return format_html(
                '<img src="{}" style="width: 60px; height: 60px; object-fit: cover; border-radius: 3px;" />',
                obj.image.url
            )
        return '-'

    @admin.display(description=_('Foto-Typ'))
    def photo_type_badge(self, obj):
        """Badge für Foto-Typ"""
        if obj.photo_type.startswith('360_'):
            color = '#3b82f6'
        elif obj.photo_type.startswith('interior_'):
            color = '#8b5cf6'
        elif obj.photo_type == 'defect':
            color = '#ef4444'
        else:
            color = '#9ca3af'

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            color, obj.get_photo_type_display()
        )

    @admin.display(description=_('GPS'), boolean=True)
    def has_gps(self, obj):
        """Hat das Foto GPS-Koordinaten?"""
        return obj.gps_latitude is not None and obj.gps_longitude is not None

    def image_preview(self, obj):
        """Große Vorschau für Detailansicht"""
        if obj.image:
            return format_html(
                '<img src="{}" style="max-width: 600px; max-height: 600px; border-radius: 5px;" />',
                obj.image.url
            )
        return _('Kein Bild vorhanden')


@admin.register(HandoverDefect)
class HandoverDefectAdmin(admin.ModelAdmin):
    """Admin für Mängel"""

    list_display = (
        'title',
        'handover',
        'severity_badge',
        'category_badge',
        'operational_readiness_icon',
        'repair_status_badge',
        'cost_display',
        'created_at',
    )

    list_filter = (
        'severity',
        'category',
        'repaired',
        'requires_immediate_action',
        'affects_operational_readiness',
        'created_at',
    )

    search_fields = (
        'title',
        'description',
        'repair_notes',
        'handover__vehicle__license_plate',
    )

    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by')

    fieldsets = (
        (_('Mangel'), {
            'fields': (
                'handover',
                'title',
                'description',
                'severity',
                'category',
            )
        }),
        (_('Auswirkungen'), {
            'fields': (
                'requires_immediate_action',
                'affects_operational_readiness',
            )
        }),
        (_('Behebung'), {
            'fields': (
                'repaired',
                'repair_date',
                'repaired_by',
                'repair_notes',
                # 'workshop_order',  # TODO: Aktivieren sobald workshop.WorkshopOrder existiert
            )
        }),
        (_('Kosten'), {
            'fields': (
                'estimated_repair_cost',
                'actual_repair_cost',
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

    actions = ['mark_as_repaired', 'mark_as_critical']

    def get_queryset(self, request):
        """Optimiere Queries"""
        qs = super().get_queryset(request)
        return qs.select_related(
            'handover',
            'handover__vehicle',
            'repaired_by',
            # 'workshop_order',  # TODO: Aktivieren sobald workshop.WorkshopOrder existiert
            'created_by',
            'updated_by'
        )

    @admin.display(description=_('Schweregrad'))
    def severity_badge(self, obj):
        """Farbiger Badge für Schweregrad"""
        severity_colors = {
            DefectSeverity.INFO: '#3b82f6',
            DefectSeverity.MINOR: '#10b981',
            DefectSeverity.MODERATE: '#f59e0b',
            DefectSeverity.MAJOR: '#ef4444',
            DefectSeverity.CRITICAL: '#dc2626',
        }
        color = severity_colors.get(obj.severity, '#9ca3af')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            color, obj.get_severity_display()
        )

    @admin.display(description=_('Kategorie'))
    def category_badge(self, obj):
        """Badge für Kategorie"""
        return format_html(
            '<span style="background-color: #6b7280; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            obj.get_category_display()
        )

    @admin.display(description=_('Einsatzbereit'), boolean=True)
    def operational_readiness_icon(self, obj):
        """Beeinträchtigt Einsatzbereitschaft?"""
        return not obj.affects_operational_readiness

    @admin.display(description=_('Reparatur-Status'))
    def repair_status_badge(self, obj):
        """Status der Reparatur"""
        if obj.repaired:
            return format_html('<span style="color: #10b981; font-weight: bold;">✓ Behoben</span>')
        elif obj.requires_immediate_action:
            return format_html('<span style="color: #dc2626; font-weight: bold;">⚠ SOFORT!</span>')
        else:
            return format_html('<span style="color: #f59e0b;">✗ Offen</span>')

    @admin.display(description=_('Kosten'))
    def cost_display(self, obj):
        """Kosten-Anzeige"""
        if obj.actual_repair_cost:
            return format_html('<span style="font-weight: bold;">{:.2f} €</span>', obj.actual_repair_cost)
        elif obj.estimated_repair_cost:
            return format_html('<span style="color: #9ca3af;">~{:.2f} €</span>', obj.estimated_repair_cost)
        return '-'

    @admin.action(description=_('Als behoben markieren'))
    def mark_as_repaired(self, request, queryset):
        """Markiere Mängel als behoben"""
        from django.utils import timezone
        updated = queryset.update(repaired=True, repair_date=timezone.now())
        self.message_user(request, _(f'{updated} Mangel/Mängel als behoben markiert.'))

    @admin.action(description=_('Als kritisch markieren'))
    def mark_as_critical(self, request, queryset):
        """Markiere als kritisch"""
        updated = queryset.update(
            severity=DefectSeverity.CRITICAL,
            requires_immediate_action=True,
            affects_operational_readiness=True
        )
        self.message_user(request, _(f'{updated} Mangel/Mängel als kritisch markiert.'))

    def save_model(self, request, obj, form, change):
        """Setze created_by/updated_by"""
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


# ===== 360° Fahrzeuginnenraum-Verwaltung =====

class HotspotImageInline(admin.TabularInline):
    """Inline Admin für Hotspot-Bilder"""
    model = HotspotImage
    extra = 1
    fields = ('order', 'image', 'caption')
    readonly_fields = ('created_at',)
    ordering = ['order']


class Vehicle360HotspotInline(admin.TabularInline):
    """Inline Admin für Hotspots"""
    model = Vehicle360Hotspot
    extra = 0
    fields = ('order', 'title', 'pitch', 'yaw', 'hotspot_type', 'icon', 'color', 'is_active')
    ordering = ['order', 'title']
    show_change_link = True


@admin.register(Vehicle360Photo)
class Vehicle360PhotoAdmin(admin.ModelAdmin):
    """Admin für 360° Fahrzeug-Fotos"""

    list_display = (
        'image_thumbnail',
        'vehicle',
        'photo_type_badge',
        'title',
        'hotspot_count',
        'is_active_badge',
        'created_at',
    )

    list_filter = (
        'photo_type',
        'is_active',
        'created_at',
    )

    search_fields = (
        'title',
        'description',
        'vehicle__license_plate',
    )

    readonly_fields = (
        'image_preview',
        'created_at',
        'updated_at',
        'created_by',
        'updated_by',
    )

    inlines = [Vehicle360HotspotInline]

    @admin.display(description=_('Vorschau'))
    def image_thumbnail(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="width: 80px; height: 40px; object-fit: cover; border-radius: 3px;" />', obj.image.url)
        return '-'

    @admin.display(description=_('Foto-Typ'))
    def photo_type_badge(self, obj):
        colors = {'front': '#3b82f6', 'rear': '#8b5cf6'}
        color = colors.get(obj.photo_type, '#9ca3af')
        return format_html('<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>', color, obj.get_photo_type_display())

    @admin.display(description=_('Hotspots'))
    def hotspot_count(self, obj):
        count = obj.get_hotspot_count()
        return format_html('<span style="font-weight: bold; color: #3b82f6;">🎯 {}</span>', count) if count > 0 else format_html('<span style="color: #9ca3af;">0</span>')

    @admin.display(description=_('Status'))
    def is_active_badge(self, obj):
        if obj.is_active:
            return format_html('<span style="background-color: #10b981; color: white; padding: 3px 7px; border-radius: 3px; font-size: 11px;">✓ Aktiv</span>')
        return format_html('<span style="background-color: #6b7280; color: white; padding: 3px 7px; border-radius: 3px; font-size: 11px;">○ Inaktiv</span>')

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-width: 800px; max-height: 400px; border-radius: 5px;" />', obj.image.url)
        return _('Kein Bild vorhanden')


@admin.register(Vehicle360Hotspot)
class Vehicle360HotspotAdmin(admin.ModelAdmin):
    """Admin für 360° Hotspots"""

    list_display = (
        'title',
        'photo_360',
        'hotspot_type_badge',
        'position_display',
        'is_active_badge',
        'order',
    )

    list_filter = (
        'hotspot_type',
        'is_active',
        'photo_360__photo_type',
    )

    search_fields = (
        'title',
        'description',
        'photo_360__title',
    )

    list_editable = ('order',)

    inlines = [HotspotImageInline]

    @admin.display(description=_('Typ'))
    def hotspot_type_badge(self, obj):
        colors = {'checklist': '#10b981', 'images': '#3b82f6', 'info': '#f59e0b', 'mixed': '#8b5cf6'}
        color = colors.get(obj.hotspot_type, '#9ca3af')
        return format_html('<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>', color, obj.get_hotspot_type_display())

    @admin.display(description=_('Position'))
    def position_display(self, obj):
        return format_html('<span style="font-family: monospace; font-size: 10px;">P: {:.1f}° | Y: {:.1f}°</span>', obj.pitch, obj.yaw)

    @admin.display(description=_('Status'))
    def is_active_badge(self, obj):
        if obj.is_active:
            return format_html('<span style="background-color: #10b981; color: white; padding: 3px 7px; border-radius: 3px; font-size: 11px;">✓</span>')
        return format_html('<span style="background-color: #6b7280; color: white; padding: 3px 7px; border-radius: 3px; font-size: 11px;">○</span>')


@admin.register(HotspotImage)
class HotspotImageAdmin(admin.ModelAdmin):
    """Admin für Hotspot-Bilder"""

    list_display = (
        'image_thumbnail',
        'hotspot',
        'caption',
        'order',
        'created_at',
    )

    list_editable = ('order',)

    readonly_fields = ('image_preview', 'created_at', 'updated_at')

    @admin.display(description=_('Vorschau'))
    def image_thumbnail(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="width: 60px; height: 60px; object-fit: cover; border-radius: 3px;" />', obj.image.url)
        return '-'

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-width: 600px; max-height: 600px; border-radius: 5px;" />', obj.image.url)
        return _('Kein Bild vorhanden')
