"""
Höhenrettung Admin Interface
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    HeightRescueItem, HeightRescueStockMovement, HeightRescueInspectionLog,
    InspectionStatus, HeightRescueInventoryCheck, HeightRescueInventoryCheckItem
)


@admin.register(HeightRescueItem)
class HeightRescueItemAdmin(admin.ModelAdmin):
    """Admin-Interface für Höhenrettungsausrüstung"""

    list_display = [
        'name', 'item_type', 'manufacturer', 'certification_badge',
        'inspection_status_badge', 'next_inspection_date', 'total_falls_arrested',
        'location'
    ]

    list_filter = [
        'item_type', 'inspection_status', 'rope_type',
        ('next_inspection_date', admin.DateFieldListFilter),
        ('last_inspection_date', admin.DateFieldListFilter),
        'location'
    ]

    search_fields = [
        'name', 'item_number', 'manufacturer',
        'certification_number', 'description'
    ]

    readonly_fields = [
        'created_at', 'updated_at', 'certification_badge',
        'inspection_status_badge', 'age_display', 'should_retire_display'
    ]

    fieldsets = (
        (_('Allgemeine Informationen'), {
            'fields': (
                'name', 'item_type', 'rope_type', 'item_number',
                'manufacturer', 'manufacturer_part_number', 'location',
                'description'
            )
        }),
        (_('Zertifizierung & Normen'), {
            'fields': (
                'certifications', 'certification_number', 'certification_badge'
            )
        }),
        (_('Technische Daten'), {
            'fields': (
                'max_load_kg', 'breaking_strength_kn', 'working_load_limit_kg',
                'rope_length_m', 'rope_diameter_mm'
            )
        }),
        (_('Lebensdauer & Alterung'), {
            'fields': (
                'manufacturing_date', 'max_service_life_years', 'age_display',
                'retirement_date', 'retirement_reason', 'should_retire_display'
            )
        }),
        (_('Prüfungen (DGUV)'), {
            'fields': (
                'last_inspection_date', 'next_inspection_date',
                'inspection_interval_months', 'inspection_status',
                'inspection_status_badge', 'last_inspector'
            ),
            'description': _('Mindestens jährliche Prüfung nach DGUV Vorschrift 3 erforderlich')
        }),
        (_('Nutzungshistorie'), {
            'fields': (
                'total_falls_arrested', 'total_uses', 'last_use_date'
            ),
            'description': _('⚠️ Ausrüstung nach Sturz aussondern!')
        }),
        (_('Dokumentation'), {
            'fields': (
                'inspection_report', 'manual_file', 'test_certificate',
                'photos', 'condition_notes'
            ),
            'classes': ('collapse',)
        }),
        (_('Fahrzeugzuordnung'), {
            'fields': ('assigned_vehicles',),
            'classes': ('collapse',)
        }),
        (_('System'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    filter_horizontal = ['assigned_vehicles']

    actions = [
        'mark_inspection_overdue',
        'mark_for_retirement',
        'reset_inspection_status'
    ]

    @admin.display(description=_('Zertifizierungen'))
    def certification_badge(self, obj):
        """Zeigt Zertifizierungen als Badges"""
        if not obj.certifications:
            return format_html(
                '<span style="background-color: #9ca3af; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-size: 11px;">Keine</span>'
            )

        cert_badges = []
        cert_colors = {
            'en_361': '#10b981',  # Auffanggurte
            'en_1891': '#3b82f6', # Statische Seile
            'en_362': '#f59e0b',  # Verbindungselemente
            'en_12275': '#8b5cf6', # Karabiner
            'dguv': '#ef4444',    # DGUV
            'ce': '#06b6d4',      # CE
        }

        for cert in obj.certifications[:5]:  # Max 5 Badges
            color = cert_colors.get(cert, '#6b7280')
            cert_label = cert.upper().replace('_', ' ')
            cert_badges.append(
                f'<span style="background-color: {color}; color: white; padding: 2px 6px; '
                f'border-radius: 3px; font-size: 10px; margin-right: 2px; '
                f'white-space: nowrap;">{cert_label}</span>'
            )

        if len(obj.certifications) > 5:
            cert_badges.append(
                f'<span style="background-color: #6b7280; color: white; padding: 2px 6px; '
                f'border-radius: 3px; font-size: 10px;">+{len(obj.certifications) - 5}</span>'
            )

        return format_html(''.join(cert_badges))

    @admin.display(description=_('Prüfstatus'))
    def inspection_status_badge(self, obj):
        """Zeigt Prüfstatus als farbiges Badge"""
        status_colors = {
            InspectionStatus.NOT_DUE: '#9ca3af',
            InspectionStatus.DUE_SOON: '#f59e0b',
            InspectionStatus.OVERDUE: '#ef4444',
            InspectionStatus.FAILED: '#dc2626',
            InspectionStatus.PASSED: '#10b981',
            InspectionStatus.RETIRED: '#6b7280',
        }

        color = status_colors.get(obj.inspection_status, '#9ca3af')
        icon = ''

        if obj.inspection_status == InspectionStatus.PASSED:
            icon = '✓ '
        elif obj.inspection_status == InspectionStatus.FAILED:
            icon = '✗ '
        elif obj.inspection_status == InspectionStatus.OVERDUE:
            icon = '⚠️ '
        elif obj.inspection_status == InspectionStatus.RETIRED:
            icon = '🚫 '

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">{}{}</span>',
            color, icon, obj.get_inspection_status_display()
        )

    @admin.display(description=_('Alter'))
    def age_display(self, obj):
        """Zeigt Alter in Jahren"""
        age = obj.get_age_years()
        if age is None:
            return _('Unbekannt')

        color = '#10b981'  # Grün
        if obj.max_service_life_years:
            if age >= obj.max_service_life_years:
                color = '#ef4444'  # Rot (überfällig)
            elif age >= obj.max_service_life_years * 0.8:
                color = '#f59e0b'  # Orange (bald fällig)

        return format_html(
            '<span style="color: {}; font-weight: bold;">{:.1f} Jahre</span>',
            color, age
        )

    @admin.display(description=_('Aussonderung fällig?'))
    def should_retire_display(self, obj):
        """Zeigt ob Aussonderung fällig ist"""
        if obj.should_be_retired():
            return format_html(
                '<span style="background-color: #ef4444; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-size: 11px; font-weight: bold;">⚠️ JA</span>'
            )
        return format_html(
            '<span style="color: #10b981; font-weight: bold;">✓ Nein</span>'
        )

    @admin.action(description=_('Prüfung als überfällig markieren'))
    def mark_inspection_overdue(self, request, queryset):
        """Markiert Ausrüstung als prüfüberfällig"""
        updated = queryset.update(inspection_status=InspectionStatus.OVERDUE)
        self.message_user(
            request,
            _(f'{updated} Ausrüstungsteile als prüfüberfällig markiert.')
        )

    @admin.action(description=_('Zur Aussonderung markieren'))
    def mark_for_retirement(self, request, queryset):
        """Markiert Ausrüstung zur Aussonderung"""
        from datetime import date
        updated = queryset.update(
            inspection_status=InspectionStatus.RETIRED,
            retirement_date=date.today()
        )
        self.message_user(
            request,
            _(f'{updated} Ausrüstungsteile zur Aussonderung markiert.')
        )

    @admin.action(description=_('Prüfstatus zurücksetzen'))
    def reset_inspection_status(self, request, queryset):
        """Setzt Prüfstatus zurück"""
        updated = queryset.update(inspection_status=InspectionStatus.NOT_DUE)
        self.message_user(
            request,
            _(f'Prüfstatus von {updated} Ausrüstungsteilen zurückgesetzt.')
        )


@admin.register(HeightRescueStockMovement)
class HeightRescueStockMovementAdmin(admin.ModelAdmin):
    """Admin-Interface für Lagerbewegungen"""

    list_display = [
        'movement_date', 'item', 'movement_type', 'quantity',
        'fall_arrested_badge', 'inspection_badge', 'created_by'
    ]

    list_filter = [
        'movement_type', 'fall_arrested', 'inspection_performed',
        'inspection_passed',
        ('movement_date', admin.DateFieldListFilter),
        ('mission_date', admin.DateFieldListFilter)
    ]

    search_fields = [
        'item__name', 'item__item_number', 'mission_type',
        'notes', 'fall_description', 'inspection_notes'
    ]

    readonly_fields = [
        'created_at', 'updated_at', 'fall_arrested_badge',
        'inspection_badge',
        # movement_date wird beim Buchen automatisch gesetzt (auto_now_add)
        # und ist daher nicht editierbar -> nur lesend anzeigen
        'movement_date'
    ]

    fieldsets = (
        (_('Bewegung'), {
            'fields': (
                'item', 'movement_type', 'movement_date', 'quantity', 'unit',
                'from_location', 'to_location', 'notes'
            )
        }),
        (_('Einsatzdokumentation'), {
            'fields': (
                'mission_date', 'mission_type', 'condition_before',
                'condition_after'
            ),
            'classes': ('collapse',)
        }),
        (_('Sturzinformation'), {
            'fields': (
                'fall_arrested', 'fall_arrested_badge', 'fall_height_m',
                'fall_description'
            ),
            'description': _('⚠️ Bei Sturz: Ausrüstung wird automatisch ausgemustert!')
        }),
        (_('Prüfung'), {
            'fields': (
                'inspection_performed', 'inspection_passed',
                'inspection_badge', 'inspector', 'inspection_notes'
            ),
            'classes': ('collapse',)
        }),
        (_('Dokumentation'), {
            'fields': ('photos',),
            'classes': ('collapse',)
        }),
        (_('System'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    @admin.display(description=_('Sturz'))
    def fall_arrested_badge(self, obj):
        """Zeigt Sturz-Status"""
        if obj.fall_arrested:
            return format_html(
                '<span style="background-color: #ef4444; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-size: 11px; font-weight: bold;">⚠️ STURZ</span>'
            )
        return format_html(
            '<span style="color: #9ca3af;">-</span>'
        )

    @admin.display(description=_('Prüfung'))
    def inspection_badge(self, obj):
        """Zeigt Prüfungsstatus"""
        if not obj.inspection_performed:
            return format_html('<span style="color: #9ca3af;">-</span>')

        if obj.inspection_passed:
            return format_html(
                '<span style="background-color: #10b981; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-size: 11px;">✓ Bestanden</span>'
            )
        else:
            return format_html(
                '<span style="background-color: #ef4444; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-size: 11px;">✗ Nicht bestanden</span>'
            )


@admin.register(HeightRescueInspectionLog)
class HeightRescueInspectionLogAdmin(admin.ModelAdmin):
    """Admin-Interface für Prüfprotokolle"""

    list_display = [
        'inspection_date', 'item', 'inspection_type', 'inspector',
        'passed_badge', 'next_inspection_due'
    ]

    list_filter = [
        'passed', 'inspection_type',
        ('inspection_date', admin.DateFieldListFilter),
        ('next_inspection_due', admin.DateFieldListFilter),
        'visual_check', 'functionality_check', 'no_damage'
    ]

    search_fields = [
        'item__name', 'item__item_number', 'inspector__first_name',
        'inspector__last_name', 'findings', 'actions_taken'
    ]

    readonly_fields = ['created_at', 'updated_at', 'passed_badge']

    fieldsets = (
        (_('Prüfung'), {
            'fields': (
                'item', 'inspection_date', 'inspection_type',
                'inspector', 'passed', 'passed_badge'
            )
        }),
        (_('Prüfpunkte'), {
            'fields': (
                'visual_check', 'functionality_check', 'marking_legible',
                'no_damage', 'no_wear', 'no_corrosion'
            )
        }),
        (_('Ergebnis'), {
            'fields': (
                'findings', 'actions_taken'
            )
        }),
        (_('Dokumentation'), {
            'fields': (
                'protocol_file', 'photos'
            ),
            'classes': ('collapse',)
        }),
        (_('Nächste Prüfung'), {
            'fields': ('next_inspection_due',)
        }),
        (_('System'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    @admin.display(description=_('Ergebnis'))
    def passed_badge(self, obj):
        """Zeigt Prüfungsergebnis"""
        if obj.passed:
            return format_html(
                '<span style="background-color: #10b981; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-size: 11px; font-weight: bold;">✓ Bestanden</span>'
            )
        else:
            return format_html(
                '<span style="background-color: #ef4444; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-size: 11px; font-weight: bold;">✗ Nicht bestanden</span>'
            )

# ========================================================================
# INVENTUR ADMIN
# ========================================================================

@admin.register(HeightRescueInventoryCheck)
class HeightRescueInventoryCheckAdmin(admin.ModelAdmin):
    """Admin-Interface für Höhenrettungs-Inventuren"""

    list_display = [
        'check_number',
        'title',
        'check_type',
        'status',
        'progress_display',
        'scheduled_start_date',
        'responsible_person',
        'created_at'
    ]

    list_filter = [
        'status',
        'check_type',
        ('scheduled_start_date', admin.DateFieldListFilter),
        ('actual_start_date', admin.DateFieldListFilter),
        'check_inspections',
        'check_age_limits',
        'check_rope_condition',
        'check_retirement',
        'responsible_person',
        'location'
    ]

    search_fields = [
        'check_number',
        'title',
        'description',
        'notes'
    ]

    readonly_fields = [
        'check_number',
        'actual_start_date',
        'actual_end_date',
        'total_items',
        'counted_items',
        'items_with_discrepancies',
        'inspection_overdue_found',
        'age_limit_exceeded_found',
        'rope_damage_found',
        'retirement_required_found',
        'approved_by',
        'approved_date',
        'created_at',
        'updated_at',
        'created_by',
        'updated_by'
    ]

    autocomplete_fields = ['responsible_person', 'team_members', 'location']

    fieldsets = (
        ('Basis-Informationen', {
            'fields': ('check_number', 'title', 'description', 'check_type', 'status')
        }),
        ('Zeitplanung', {
            'fields': ('scheduled_start_date', 'scheduled_end_date', 'actual_start_date', 'actual_end_date')
        }),
        ('Verantwortung', {
            'fields': ('responsible_person', 'team_members')
        }),
        ('Umfang', {
            'fields': ('location',)
        }),
        ('PSA-spezifische Prüfungen (DGUV)', {
            'fields': ('check_inspections', 'check_age_limits', 'check_rope_condition', 'check_retirement'),
            'description': _('⚠️ DGUV Vorschrift 3 - Jährliche Prüfpflicht für PSA!')
        }),
        ('Fortschritt & Ergebnisse', {
            'fields': ('total_items', 'counted_items', 'items_with_discrepancies',
                      'inspection_overdue_found', 'age_limit_exceeded_found', 'rope_damage_found',
                      'retirement_required_found')
        }),
        ('Genehmigung', {
            'fields': ('approved_by', 'approved_date')
        }),
        ('Notizen', {
            'fields': ('notes',)
        }),
        ('System', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )

    @admin.display(description=_('Fortschritt'))
    def progress_display(self, obj):
        """Zeigt Fortschritt als Badge"""
        percentage = obj.get_progress_percentage()
        if percentage == 100:
            color = '#10b981'
        elif percentage >= 50:
            color = '#f59e0b'
        else:
            color = '#6b7280'

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">{}/{} ({}%)</span>',
            color, obj.counted_items, obj.total_items, percentage
        )


@admin.register(HeightRescueInventoryCheckItem)
class HeightRescueInventoryCheckItemAdmin(admin.ModelAdmin):
    """Admin-Interface für Höhenrettungs-Inventur-Positionen"""

    list_display = [
        'inventory_check',
        'inventory_number',
        'item_name',
        'item_type',
        'inspection_status_badge',
        'age_badge',
        'rope_status_badge',
        'operational_status',
        'is_counted',
        'has_discrepancy'
    ]

    list_filter = [
        'inventory_check__status',
        'is_counted',
        'has_discrepancy',
        'inspection_overdue',
        'age_limit_exceeded',
        'rope_damage_found',
        'retirement_required',
        'operational_status',
        'inspection_status',
        'item_type'
    ]

    search_fields = [
        'inventory_number', 'item_name', 'serial_number', 'notes'
    ]

    autocomplete_fields = ['inventory_check', 'location']

    readonly_fields = [
        'variance_quantity', 'counted_date', 'counted_by',
        'inspection_status_badge', 'age_badge', 'rope_status_badge',
        # created_at/updated_at werden automatisch gesetzt (auto_now_add/auto_now)
        # und sind daher nicht editierbar -> nur lesend anzeigen
        'created_at', 'updated_at'
    ]

    fieldsets = (
        ('Basis-Info', {
            'fields': ('inventory_check', 'height_rescue_device', 'inventory_number', 
                      'item_name', 'item_number', 'item_type', 'location')
        }),
        ('Geräte-Details', {
            'fields': ('serial_number', 'operational_status')
        }),
        ('Prüfungen (DGUV)', {
            'fields': ('last_inspection_date', 'next_inspection_date', 'inspection_overdue',
                      'inspection_status', 'inspection_status_badge'),
            'description': _('⚠️ DGUV Vorschrift 3 - Jährliche Prüfpflicht!')
        }),
        ('Alterung & Nutzungsdauer', {
            'fields': ('manufacturing_date', 'first_use_date', 'age_in_years', 
                      'age_limit_exceeded', 'age_badge')
        }),
        ('Seil-spezifisch', {
            'fields': ('rope_length', 'rope_diameter', 'rope_damage_found', 'rope_status_badge'),
            'classes': ('collapse',)
        }),
        ('Aussonderung', {
            'fields': ('retirement_date', 'retirement_required', 'retirement_reason')
        }),
        ('Mengen', {
            'fields': ('expected_quantity', 'unit', 'actual_quantity', 'variance_quantity')
        }),
        ('Zählung', {
            'fields': ('is_counted', 'counted_date', 'counted_by', 'has_discrepancy', 'requires_recount')
        }),
        ('Notizen', {
            'fields': ('notes',)
        }),
        ('System', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )

    @admin.display(description=_('Prüfstatus'))
    def inspection_status_badge(self, obj):
        """Zeigt Prüfstatus als Badge"""
        if obj.inspection_overdue:
            return format_html(
                '<span style="background-color: #ef4444; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-size: 11px; font-weight: bold;">⚠️ Überfällig</span>'
            )
        elif obj.inspection_status:
            return format_html(
                '<span style="background-color: #10b981; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-size: 11px;">✓ {}</span>',
                obj.inspection_status
            )
        return format_html(
            '<span style="color: #6b7280;">-</span>'
        )

    @admin.display(description=_('Alter'))
    def age_badge(self, obj):
        """Zeigt Altersstatus als Badge"""
        if obj.age_limit_exceeded:
            return format_html(
                '<span style="background-color: #ef4444; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-size: 11px; font-weight: bold;">⚠️ {} Jahre</span>',
                obj.age_in_years or '?'
            )
        elif obj.age_in_years is not None:
            return format_html(
                '<span style="background-color: #10b981; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-size: 11px;">✓ {} Jahre</span>',
                obj.age_in_years
            )
        return format_html(
            '<span style="color: #6b7280;">-</span>'
        )

    @admin.display(description=_('Seil'))
    def rope_status_badge(self, obj):
        """Zeigt Seilstatus als Badge"""
        if obj.rope_damage_found:
            return format_html(
                '<span style="background-color: #ef4444; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-size: 11px; font-weight: bold;">⚠️ Schaden</span>'
            )
        elif obj.rope_length:
            return format_html(
                '<span style="background-color: #10b981; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-size: 11px;">✓ {}m/{}mm</span>',
                obj.rope_length, obj.rope_diameter or '?'
            )
        return format_html(
            '<span style="color: #6b7280;">-</span>'
        )
