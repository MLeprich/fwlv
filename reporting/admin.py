"""
Django Admin Configuration für Reporting App

Registriert alle Models mit umfangreichen Admin-Features:
- Report-Templates mit Verwendungsstatistiken
- Generierte Reports mit Status-Tracking
- Scheduled Reports mit Frequenz-Management
- KPIs mit Ampel-System
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from .models import (
    ReportTemplate,
    Report,
    ReportSchedule,
    KPI,
    ReportType,
    ReportStatus,
    ReportFormat,
    ScheduleFrequency,
    KPICategory,
    KPIType
)


# =============================================================================
# REPORT TEMPLATES ADMIN
# =============================================================================

@admin.register(ReportTemplate)
class ReportTemplateAdmin(admin.ModelAdmin):
    """Admin für Report-Templates"""

    list_display = [
        'name',
        'type_badge',
        'usage_badge',
        'public_badge',
        'active_badge',
        'created_at'
    ]

    list_filter = ['report_type', 'is_public', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['usage_count', 'created_at', 'created_by', 'updated_at', 'updated_by']

    fieldsets = (
        (_('Basis-Informationen'), {
            'fields': ('name', 'description', 'report_type')
        }),
        (_('Query & Template'), {
            'fields': ('query', 'template_file', 'parameters', 'available_formats')
        }),
        (_('Berechtigungen'), {
            'fields': ('is_public', 'allowed_users', 'is_active')
        }),
        (_('Statistiken'), {
            'fields': ('usage_count',),
            'classes': ('collapse',)
        }),
        (_('Audit-Trail'), {
            'fields': ('created_at', 'created_by', 'updated_at', 'updated_by'),
            'classes': ('collapse',)
        }),
    )

    filter_horizontal = ['allowed_users']

    @admin.display(description=_('Typ'))
    def type_badge(self, obj):
        """Farbiger Typ-Badge"""
        colors = {
            ReportType.INVENTORY: '#3b82f6',     # blue-500
            ReportType.EXPIRING: '#ef4444',      # red-500
            ReportType.LOW_STOCK: '#f59e0b',     # orange-500
            ReportType.PROCUREMENT: '#8b5cf6',   # purple-500
            ReportType.VEHICLE: '#06b6d4',       # cyan-500
            ReportType.INSPECTION: '#14b8a6',    # teal-500
            ReportType.PERSONNEL: '#10b981',     # green-500
            ReportType.DOCUMENT: '#6366f1',      # indigo-500
            ReportType.AUDIT: '#f43f5e',         # rose-500
            ReportType.CUSTOM: '#9ca3af',        # gray-400
        }
        color = colors.get(obj.report_type, '#9ca3af')

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 10px; font-size: 10px; font-weight: bold;">{}</span>',
            color, obj.get_report_type_display()
        )

    @admin.display(description=_('Verwendungen'))
    def usage_badge(self, obj):
        """Badge mit Verwendungszähler"""
        if obj.usage_count == 0:
            color = '#9ca3af'  # gray-400
        elif obj.usage_count < 10:
            color = '#3b82f6'  # blue-500
        elif obj.usage_count < 50:
            color = '#10b981'  # green-500
        else:
            color = '#f59e0b'  # orange-500

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 12px; font-size: 12px; font-weight: bold;">{}</span>',
            color, obj.usage_count
        )

    @admin.display(description=_('Öffentlich'))
    def public_badge(self, obj):
        """Öffentlich-Badge"""
        if obj.is_public:
            return format_html(
                '<span style="background-color: #10b981; color: white; padding: 3px 8px; '
                'border-radius: 10px; font-size: 10px; font-weight: bold;">✓ Ja</span>'
            )
        else:
            return format_html(
                '<span style="background-color: #6b7280; color: white; padding: 3px 8px; '
                'border-radius: 10px; font-size: 10px; font-weight: bold;">✗ Nein</span>'
            )

    @admin.display(description=_('Aktiv'))
    def active_badge(self, obj):
        """Aktiv-Badge"""
        if obj.is_active:
            return format_html(
                '<span style="background-color: #10b981; color: white; padding: 3px 8px; '
                'border-radius: 10px; font-size: 10px; font-weight: bold;">✓ Aktiv</span>'
            )
        else:
            return format_html(
                '<span style="background-color: #ef4444; color: white; padding: 3px 8px; '
                'border-radius: 10px; font-size: 10px; font-weight: bold;">✗ Inaktiv</span>'
            )


# =============================================================================
# REPORTS ADMIN
# =============================================================================

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    """Admin für generierte Reports"""

    list_display = [
        'title',
        'type_badge',
        'status_badge',
        'format_badge',
        'period_display',
        'duration_display',
        'file_size_display',
        'download_badge',
        'created_by',
        'created_at'
    ]

    list_filter = [
        'report_type',
        'status',
        'file_format',
        'created_at',
        'expires_at'
    ]

    search_fields = ['title', 'description', 'created_by__username']
    readonly_fields = [
        'file_size',
        'generation_started_at',
        'generation_completed_at',
        'generation_duration',
        'download_count',
        'last_downloaded_at',
        'created_at',
        'created_by',
        'updated_at',
        'updated_by'
    ]

    fieldsets = (
        (_('Basis-Informationen'), {
            'fields': ('template', 'title', 'description', 'report_type', 'status')
        }),
        (_('Zeitraum'), {
            'fields': ('date_from', 'date_to')
        }),
        (_('Parameter'), {
            'fields': ('parameters',),
            'classes': ('collapse',)
        }),
        (_('Generierte Datei'), {
            'fields': ('file', 'file_format', 'file_size')
        }),
        (_('Generierungs-Metadaten'), {
            'fields': ('generation_started_at', 'generation_completed_at', 'generation_duration', 'error_message'),
            'classes': ('collapse',)
        }),
        (_('Ablauf & Statistiken'), {
            'fields': ('expires_at', 'download_count', 'last_downloaded_at')
        }),
        (_('Verknüpfung'), {
            'fields': ('related_content_type', 'related_object_id'),
            'classes': ('collapse',)
        }),
        (_('Audit-Trail'), {
            'fields': ('created_at', 'created_by', 'updated_at', 'updated_by'),
            'classes': ('collapse',)
        }),
    )

    actions = ['mark_as_expired', 'delete_files']

    @admin.display(description=_('Typ'))
    def type_badge(self, obj):
        """Farbiger Typ-Badge"""
        colors = {
            ReportType.INVENTORY: '#3b82f6',
            ReportType.EXPIRING: '#ef4444',
            ReportType.LOW_STOCK: '#f59e0b',
            ReportType.PROCUREMENT: '#8b5cf6',
            ReportType.VEHICLE: '#06b6d4',
            ReportType.INSPECTION: '#14b8a6',
            ReportType.PERSONNEL: '#10b981',
            ReportType.DOCUMENT: '#6366f1',
            ReportType.AUDIT: '#f43f5e',
            ReportType.CUSTOM: '#9ca3af',
        }
        color = colors.get(obj.report_type, '#9ca3af')

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 10px; font-size: 10px; font-weight: bold;">{}</span>',
            color, obj.get_report_type_display()
        )

    @admin.display(description=_('Status'))
    def status_badge(self, obj):
        """Farbiger Status-Badge"""
        colors = {
            ReportStatus.PENDING: '#6b7280',      # gray-500
            ReportStatus.GENERATING: '#3b82f6',   # blue-500
            ReportStatus.COMPLETED: '#10b981',    # green-500
            ReportStatus.FAILED: '#ef4444',       # red-500
            ReportStatus.EXPIRED: '#9ca3af',      # gray-400
        }
        color = colors.get(obj.status, '#9ca3af')

        icon = ''
        if obj.status == ReportStatus.GENERATING:
            icon = '⏳ '
        elif obj.status == ReportStatus.COMPLETED:
            icon = '✓ '
        elif obj.status == ReportStatus.FAILED:
            icon = '✗ '

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 12px; font-size: 11px; font-weight: bold;">{}{}</span>',
            color, icon, obj.get_status_display()
        )

    @admin.display(description=_('Format'))
    def format_badge(self, obj):
        """Farbiger Format-Badge"""
        colors = {
            ReportFormat.PDF: '#ef4444',      # red-500
            ReportFormat.EXCEL: '#10b981',    # green-500
            ReportFormat.CSV: '#3b82f6',      # blue-500
            ReportFormat.HTML: '#f59e0b',     # orange-500
            ReportFormat.JSON: '#8b5cf6',     # purple-500
        }
        color = colors.get(obj.file_format, '#9ca3af')

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 10px; font-size: 10px; font-weight: bold;">{}</span>',
            color, obj.get_file_format_display()
        )

    @admin.display(description=_('Zeitraum'))
    def period_display(self, obj):
        """Zeigt Zeitraum"""
        if obj.date_from and obj.date_to:
            return f"{obj.date_from.strftime('%d.%m.%Y')} - {obj.date_to.strftime('%d.%m.%Y')}"
        elif obj.date_from:
            return f"Ab {obj.date_from.strftime('%d.%m.%Y')}"
        elif obj.date_to:
            return f"Bis {obj.date_to.strftime('%d.%m.%Y')}"
        return '-'

    @admin.display(description=_('Dauer'))
    def duration_display(self, obj):
        """Zeigt Generierungsdauer"""
        if obj.generation_duration:
            if obj.generation_duration < 60:
                return f"{obj.generation_duration}s"
            else:
                minutes = obj.generation_duration // 60
                seconds = obj.generation_duration % 60
                return f"{minutes}m {seconds}s"
        return '-'

    @admin.display(description=_('Dateigröße'))
    def file_size_display(self, obj):
        """Formatierte Dateigröße"""
        return obj.get_file_size_display() if obj.file_size else '-'

    @admin.display(description=_('Downloads'))
    def download_badge(self, obj):
        """Download-Badge"""
        if obj.download_count == 0:
            color = '#9ca3af'  # gray-400
        elif obj.download_count < 5:
            color = '#3b82f6'  # blue-500
        elif obj.download_count < 20:
            color = '#10b981'  # green-500
        else:
            color = '#f59e0b'  # orange-500

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 12px; font-size: 11px; font-weight: bold;">⬇ {}</span>',
            color, obj.download_count
        )

    @admin.action(description=_('Markiere als abgelaufen'))
    def mark_as_expired(self, request, queryset):
        """Bulk-Action: Als abgelaufen markieren"""
        updated = queryset.update(status=ReportStatus.EXPIRED)
        self.message_user(request, _(f'{updated} Report(s) als abgelaufen markiert.'))

    @admin.action(description=_('Dateien löschen'))
    def delete_files(self, request, queryset):
        """Bulk-Action: Dateien löschen"""
        count = 0
        for report in queryset:
            if report.file:
                report.file.delete()
                count += 1
        self.message_user(request, _(f'{count} Datei(en) gelöscht.'))


# =============================================================================
# REPORT SCHEDULES ADMIN
# =============================================================================

@admin.register(ReportSchedule)
class ReportScheduleAdmin(admin.ModelAdmin):
    """Admin für Report-Zeitpläne"""

    list_display = [
        'name',
        'template',
        'frequency_badge',
        'format_badge',
        'next_run_display',
        'run_count_badge',
        'active_badge',
        'email_badge'
    ]

    list_filter = ['frequency', 'file_format', 'is_active', 'send_email']
    search_fields = ['name', 'description', 'template__name']
    readonly_fields = ['last_run_at', 'run_count', 'created_at', 'created_by', 'updated_at', 'updated_by']

    fieldsets = (
        (_('Basis-Informationen'), {
            'fields': ('template', 'name', 'description')
        }),
        (_('Zeitplan'), {
            'fields': ('frequency', 'cron_expression', 'run_at_time', 'day_of_week', 'day_of_month')
        }),
        (_('Parameter & Format'), {
            'fields': ('parameters', 'file_format')
        }),
        (_('E-Mail'), {
            'fields': ('send_email', 'recipients')
        }),
        (_('Ablauf & Status'), {
            'fields': ('retention_days', 'is_active')
        }),
        (_('Ausführung'), {
            'fields': ('last_run_at', 'next_run_at', 'run_count'),
            'classes': ('collapse',)
        }),
        (_('Audit-Trail'), {
            'fields': ('created_at', 'created_by', 'updated_at', 'updated_by'),
            'classes': ('collapse',)
        }),
    )

    filter_horizontal = ['recipients']

    @admin.display(description=_('Frequenz'))
    def frequency_badge(self, obj):
        """Farbiger Frequenz-Badge"""
        colors = {
            ScheduleFrequency.DAILY: '#10b981',      # green-500
            ScheduleFrequency.WEEKLY: '#3b82f6',     # blue-500
            ScheduleFrequency.MONTHLY: '#f59e0b',    # orange-500
            ScheduleFrequency.QUARTERLY: '#8b5cf6',  # purple-500
            ScheduleFrequency.YEARLY: '#ef4444',     # red-500
            ScheduleFrequency.CUSTOM: '#6b7280',     # gray-500
        }
        color = colors.get(obj.frequency, '#9ca3af')

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 12px; font-size: 11px; font-weight: bold;">{}</span>',
            color, obj.get_frequency_display()
        )

    @admin.display(description=_('Format'))
    def format_badge(self, obj):
        """Farbiger Format-Badge"""
        colors = {
            ReportFormat.PDF: '#ef4444',
            ReportFormat.EXCEL: '#10b981',
            ReportFormat.CSV: '#3b82f6',
            ReportFormat.HTML: '#f59e0b',
            ReportFormat.JSON: '#8b5cf6',
        }
        color = colors.get(obj.file_format, '#9ca3af')

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 10px; font-size: 10px; font-weight: bold;">{}</span>',
            color, obj.get_file_format_display()
        )

    @admin.display(description=_('Nächste Ausführung'))
    def next_run_display(self, obj):
        """Zeigt nächste Ausführung mit Warnung"""
        if not obj.next_run_at:
            return '-'

        now = timezone.now()
        if obj.next_run_at < now:
            return format_html(
                '<span style="color: #ef4444; font-weight: bold;">⚠ {}</span>',
                obj.next_run_at.strftime('%d.%m.%Y %H:%M')
            )

        return obj.next_run_at.strftime('%d.%m.%Y %H:%M')

    @admin.display(description=_('Ausführungen'))
    def run_count_badge(self, obj):
        """Badge mit Ausführungszähler"""
        if obj.run_count == 0:
            color = '#9ca3af'  # gray-400
        elif obj.run_count < 10:
            color = '#3b82f6'  # blue-500
        elif obj.run_count < 50:
            color = '#10b981'  # green-500
        else:
            color = '#f59e0b'  # orange-500

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 12px; font-size: 12px; font-weight: bold;">{}</span>',
            color, obj.run_count
        )

    @admin.display(description=_('Aktiv'))
    def active_badge(self, obj):
        """Aktiv-Badge"""
        if obj.is_active:
            return format_html(
                '<span style="background-color: #10b981; color: white; padding: 3px 8px; '
                'border-radius: 10px; font-size: 10px; font-weight: bold;">✓</span>'
            )
        else:
            return format_html(
                '<span style="background-color: #ef4444; color: white; padding: 3px 8px; '
                'border-radius: 10px; font-size: 10px; font-weight: bold;">✗</span>'
            )

    @admin.display(description=_('E-Mail'))
    def email_badge(self, obj):
        """E-Mail-Badge"""
        if obj.send_email:
            return format_html(
                '<span style="background-color: #10b981; color: white; padding: 3px 8px; '
                'border-radius: 10px; font-size: 10px; font-weight: bold;">📧</span>'
            )
        else:
            return format_html(
                '<span style="background-color: #6b7280; color: white; padding: 3px 8px; '
                'border-radius: 10px; font-size: 10px; font-weight: bold;">✗</span>'
            )


# =============================================================================
# KPI ADMIN
# =============================================================================

@admin.register(KPI)
class KPIAdmin(admin.ModelAdmin):
    """Admin für KPIs"""

    list_display = [
        'name',
        'category_badge',
        'type_badge',
        'value_display',
        'status_indicator',
        'refresh_display',
        'active_badge',
        'display_order'
    ]

    list_filter = ['category', 'kpi_type', 'is_active']
    search_fields = ['name', 'description']
    readonly_fields = ['last_calculated_at', 'last_value', 'created_at', 'created_by', 'updated_at', 'updated_by']

    fieldsets = (
        (_('Basis-Informationen'), {
            'fields': ('name', 'description', 'category', 'kpi_type')
        }),
        (_('Query'), {
            'fields': ('query',)
        }),
        (_('Zielwerte & Schwellwerte'), {
            'fields': ('target_value', 'threshold_good', 'threshold_warning', 'unit')
        }),
        (_('Darstellung'), {
            'fields': ('icon', 'color', 'display_order', 'is_active')
        }),
        (_('Aktualisierung'), {
            'fields': ('refresh_interval', 'last_calculated_at', 'last_value')
        }),
        (_('Audit-Trail'), {
            'fields': ('created_at', 'created_by', 'updated_at', 'updated_by'),
            'classes': ('collapse',)
        }),
    )

    @admin.display(description=_('Kategorie'))
    def category_badge(self, obj):
        """Farbiger Kategorie-Badge"""
        colors = {
            KPICategory.INVENTORY: '#3b82f6',    # blue-500
            KPICategory.FINANCIAL: '#10b981',    # green-500
            KPICategory.OPERATIONAL: '#f59e0b',  # orange-500
            KPICategory.QUALITY: '#8b5cf6',      # purple-500
            KPICategory.COMPLIANCE: '#ef4444',   # red-500
        }
        color = colors.get(obj.category, '#9ca3af')

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 12px; font-size: 11px; font-weight: bold;">{}</span>',
            color, obj.get_category_display()
        )

    @admin.display(description=_('Typ'))
    def type_badge(self, obj):
        """Farbiger Typ-Badge"""
        colors = {
            KPIType.COUNT: '#3b82f6',      # blue-500
            KPIType.SUM: '#10b981',        # green-500
            KPIType.AVERAGE: '#f59e0b',    # orange-500
            KPIType.PERCENTAGE: '#8b5cf6', # purple-500
            KPIType.RATIO: '#06b6d4',      # cyan-500
            KPIType.TREND: '#ec4899',      # pink-500
        }
        color = colors.get(obj.kpi_type, '#9ca3af')

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 10px; font-size: 10px; font-weight: bold;">{}</span>',
            color, obj.get_kpi_type_display()
        )

    @admin.display(description=_('Wert'))
    def value_display(self, obj):
        """Zeigt letzten Wert"""
        if obj.last_value is None:
            return '-'
        return f"{obj.last_value} {obj.unit}".strip()

    @admin.display(description=_('Status'))
    def status_indicator(self, obj):
        """Ampel-System"""
        status_color = obj.get_status_color()

        colors = {
            'green': '#10b981',
            'yellow': '#f59e0b',
            'red': '#ef4444',
            'gray': '#9ca3af'
        }
        color = colors.get(status_color, '#9ca3af')

        return format_html(
            '<span style="background-color: {}; width: 16px; height: 16px; '
            'border-radius: 50%; display: inline-block;"></span>',
            color
        )

    @admin.display(description=_('Aktualisierung'))
    def refresh_display(self, obj):
        """Zeigt Aktualisierungsintervall"""
        if obj.refresh_interval < 60:
            return f"{obj.refresh_interval} min"
        else:
            hours = obj.refresh_interval // 60
            return f"{hours}h"

    @admin.display(description=_('Aktiv'))
    def active_badge(self, obj):
        """Aktiv-Badge"""
        if obj.is_active:
            return format_html(
                '<span style="background-color: #10b981; color: white; padding: 3px 8px; '
                'border-radius: 10px; font-size: 10px; font-weight: bold;">✓</span>'
            )
        else:
            return format_html(
                '<span style="background-color: #ef4444; color: white; padding: 3px 8px; '
                'border-radius: 10px; font-size: 10px; font-weight: bold;">✗</span>'
            )
