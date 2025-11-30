"""
Notifications Admin Configuration
Admin-Interface für Benachrichtigungen
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .models import Notification, NotificationPreference


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """
    Admin-Interface für Benachrichtigungen
    """

    list_display = [
        'created_at',
        'recipient',
        'title_short',
        'type_badge',
        'category',
        'is_read',
        'priority',
    ]

    list_filter = [
        'notification_type',
        'category',
        'is_read',
        'is_archived',
        'created_at',
    ]

    search_fields = [
        'title',
        'message',
        'recipient__username',
        'recipient__first_name',
        'recipient__last_name',
    ]

    readonly_fields = [
        'created_at',
        'read_at',
        'content_type',
        'object_id',
    ]

    fieldsets = (
        (_('Empfänger'), {
            'fields': (
                'recipient',
            )
        }),
        (_('Inhalt'), {
            'fields': (
                'notification_type',
                'category',
                'title',
                'message',
            )
        }),
        (_('Verlinktes Objekt'), {
            'fields': (
                'content_type',
                'object_id',
                'action_url',
            ),
            'classes': ('collapse',),
        }),
        (_('Status'), {
            'fields': (
                'is_read',
                'read_at',
                'is_archived',
                'priority',
            )
        }),
        (_('Zeitstempel'), {
            'fields': (
                'created_at',
                'expires_at',
            )
        }),
    )

    date_hierarchy = 'created_at'

    ordering = ['-created_at']

    actions = ['mark_as_read', 'mark_as_unread', 'archive_notifications']

    def title_short(self, obj):
        """Gekürzter Titel"""
        if len(obj.title) > 50:
            return obj.title[:50] + '...'
        return obj.title
    title_short.short_description = _('Titel')

    def type_badge(self, obj):
        """Farbcodierter Typ-Badge"""
        color_map = {
            'info': 'blue',
            'warning': 'orange',
            'error': 'red',
            'success': 'green',
            'reminder': 'purple',
            'expiry': 'orange',
            'approval': 'darkred',
            'system': 'gray',
        }
        icon_map = {
            'info': 'ℹ️',
            'warning': '⚠️',
            'error': '❌',
            'success': '✅',
            'reminder': '🔔',
            'expiry': '⏰',
            'approval': '✋',
            'system': '⚙️',
        }
        color = color_map.get(obj.notification_type, 'gray')
        icon = icon_map.get(obj.notification_type, '')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} {}</span>',
            color,
            icon,
            obj.get_notification_type_display()
        )
    type_badge.short_description = _('Typ')

    def mark_as_read(self, request, queryset):
        """Aktion: Als gelesen markieren"""
        updated = 0
        for notification in queryset:
            notification.mark_as_read()
            updated += 1
        self.message_user(request, f'{updated} Benachrichtigung(en) als gelesen markiert.')
    mark_as_read.short_description = _('Als gelesen markieren')

    def mark_as_unread(self, request, queryset):
        """Aktion: Als ungelesen markieren"""
        updated = 0
        for notification in queryset:
            notification.mark_as_unread()
            updated += 1
        self.message_user(request, f'{updated} Benachrichtigung(en) als ungelesen markiert.')
    mark_as_unread.short_description = _('Als ungelesen markieren')

    def archive_notifications(self, request, queryset):
        """Aktion: Archivieren"""
        updated = 0
        for notification in queryset:
            notification.archive()
            updated += 1
        self.message_user(request, f'{updated} Benachrichtigung(en) archiviert.')
    archive_notifications.short_description = _('Archivieren')


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    """
    Admin-Interface für Benachrichtigungs-Einstellungen
    """

    list_display = [
        'user',
        'email_enabled',
        'inapp_enabled',
        'daily_summary',
        'weekly_summary',
    ]

    list_filter = [
        'email_enabled',
        'inapp_enabled',
        'daily_summary',
        'weekly_summary',
    ]

    search_fields = [
        'user__username',
        'user__first_name',
        'user__last_name',
        'user__email',
    ]

    fieldsets = (
        (_('Benutzer'), {
            'fields': (
                'user',
            )
        }),
        (_('E-Mail-Benachrichtigungen'), {
            'fields': (
                'email_enabled',
                'email_on_expiry',
                'email_on_low_stock',
                'email_on_approval_needed',
            )
        }),
        (_('In-App-Benachrichtigungen'), {
            'fields': (
                'inapp_enabled',
            )
        }),
        (_('Kategorien'), {
            'fields': (
                'notify_inventory',
                'notify_vehicles',
                'notify_personnel',
                'notify_inspections',
                'notify_qualifications',
                'notify_orders',
                'notify_system',
            )
        }),
        (_('Zusammenfassungen'), {
            'fields': (
                'daily_summary',
                'weekly_summary',
            )
        }),
    )

    ordering = ['user__username']
