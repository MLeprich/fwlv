"""
Audit Admin Configuration
Read-Only Admin-Interface für Audit-Logs
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.utils.safestring import mark_safe

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """
    Read-Only Admin für Audit-Logs
    Keine Add/Change/Delete-Optionen
    """

    list_display = [
        'timestamp',
        'user_display',
        'action_badge',
        'severity_badge',
        'object_display',
        'description_short',
        'ip_address',
    ]

    list_filter = [
        'action',
        'severity',
        'app_label',
        'timestamp',
    ]

    search_fields = [
        'description',
        'object_repr',
        'user__username',
        'user__first_name',
        'user__last_name',
        'ip_address',
    ]

    readonly_fields = [
        'timestamp',
        'user',
        'ip_address',
        'user_agent',
        'action',
        'severity',
        'content_type',
        'object_id',
        'object_repr',
        'app_label',
        'model_name',
        'description',
        'changes_display',
        'extra_data',
        'request_path',
        'http_method',
    ]

    fieldsets = (
        (_('Zeitstempel & Benutzer'), {
            'fields': (
                'timestamp',
                'user',
                'ip_address',
                'user_agent',
            )
        }),
        (_('Aktion'), {
            'fields': (
                'action',
                'severity',
                'description',
            )
        }),
        (_('Betroffenes Objekt'), {
            'fields': (
                'content_type',
                'object_id',
                'object_repr',
                'app_label',
                'model_name',
            )
        }),
        (_('Änderungen'), {
            'fields': (
                'changes_display',
            ),
            'classes': ('collapse',),
        }),
        (_('Request-Details'), {
            'fields': (
                'request_path',
                'http_method',
                'extra_data',
            ),
            'classes': ('collapse',),
        }),
    )

    date_hierarchy = 'timestamp'

    ordering = ['-timestamp']

    def has_add_permission(self, request):
        """Kein Hinzufügen erlaubt"""
        return False

    def has_change_permission(self, request, obj=None):
        """Keine Änderung erlaubt"""
        return False

    def has_delete_permission(self, request, obj=None):
        """Kein Löschen erlaubt"""
        return False

    def user_display(self, obj):
        """Benutzer mit Link"""
        if obj.user:
            return format_html(
                '<a href="{}">{}</a>',
                reverse('admin:core_user_change', args=[obj.user.pk]),
                obj.user
            )
        return format_html('<span style="color: gray;">System</span>')
    user_display.short_description = _('Benutzer')

    def action_badge(self, obj):
        """Farbcodierter Aktions-Badge"""
        color_map = {
            'create': 'green',
            'update': 'blue',
            'delete': 'red',
            'view': 'gray',
            'login': 'purple',
            'logout': 'purple',
            'export': 'orange',
            'import': 'orange',
            'approve': 'green',
            'reject': 'red',
            'custom': 'gray',
        }
        color = color_map.get(obj.action, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_action_display()
        )
    action_badge.short_description = _('Aktion')

    def severity_badge(self, obj):
        """Farbcodierter Schweregrad-Badge"""
        color_map = {
            'info': 'gray',
            'warning': 'orange',
            'error': 'red',
            'critical': 'darkred',
            'security': 'purple',
        }
        icon_map = {
            'info': 'ℹ️',
            'warning': '⚠️',
            'error': '❌',
            'critical': '🚨',
            'security': '🔒',
        }
        color = color_map.get(obj.severity, 'gray')
        icon = icon_map.get(obj.severity, '')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} {}</span>',
            color,
            icon,
            obj.get_severity_display()
        )
    severity_badge.short_description = _('Schweregrad')

    def object_display(self, obj):
        """Objekt-Anzeige mit Link (falls vorhanden)"""
        if obj.content_type and obj.object_id:
            try:
                # Versuche Link zum Objekt zu generieren
                model_class = obj.content_type.model_class()
                admin_url = reverse(
                    f'admin:{obj.app_label}_{obj.model_name}_change',
                    args=[obj.object_id]
                )
                return format_html(
                    '<a href="{}">{}</a>',
                    admin_url,
                    obj.object_repr
                )
            except:
                return obj.object_repr
        return format_html('<span style="color: gray;">—</span>')
    object_display.short_description = _('Objekt')

    def description_short(self, obj):
        """Gekürzte Beschreibung"""
        if len(obj.description) > 100:
            return obj.description[:100] + '...'
        return obj.description
    description_short.short_description = _('Beschreibung')

    def changes_display(self, obj):
        """Änderungen formatiert anzeigen"""
        if obj.changes:
            html = '<table style="width: 100%; border-collapse: collapse;">'
            html += '<tr><th style="border: 1px solid #ddd; padding: 8px; background-color: #f2f2f2;">Feld</th>'
            html += '<th style="border: 1px solid #ddd; padding: 8px; background-color: #f2f2f2;">Alt</th>'
            html += '<th style="border: 1px solid #ddd; padding: 8px; background-color: #f2f2f2;">Neu</th></tr>'

            for field, values in obj.changes.items():
                old_value = values.get('old', '—')
                new_value = values.get('new', '—')
                html += f'<tr>'
                html += f'<td style="border: 1px solid #ddd; padding: 8px;"><strong>{field}</strong></td>'
                html += f'<td style="border: 1px solid #ddd; padding: 8px; color: red;">{old_value}</td>'
                html += f'<td style="border: 1px solid #ddd; padding: 8px; color: green;">{new_value}</td>'
                html += f'</tr>'

            html += '</table>'
            return mark_safe(html)
        return format_html('<span style="color: gray;">Keine Änderungen</span>')
    changes_display.short_description = _('Änderungen')
