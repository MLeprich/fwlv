"""
Django Admin Configuration für Info Monitors App

Registriert alle Models mit umfangreichen Admin-Features:
- Monitor-Profile für verschiedene Einsatzzwecke
- Dashboards mit Layout-Konfiguration
- Widgets mit Position & Größe
- Widget-Alerts mit Bedingungen
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from .models import (
    MonitorProfile,
    Dashboard,
    Widget,
    WidgetAlert,
    MonitorAccessToken,
    MonitorPlaylist,
    PlaylistItem,
    WidgetType,
    DashboardTheme,
    WidgetSize,
    ChartType
)


# =============================================================================
# INLINE ADMINS
# =============================================================================

class WidgetInline(admin.TabularInline):
    """Inline für Widgets"""
    model = Widget
    extra = 0
    fields = ['title', 'widget_type', 'row', 'column', 'width', 'height', 'is_active', 'display_order']
    readonly_fields = []


class WidgetAlertInline(admin.TabularInline):
    """Inline für Widget-Alerts"""
    model = WidgetAlert
    extra = 0
    fields = ['name', 'condition', 'threshold_value', 'severity', 'is_active']
    readonly_fields = []


class MonitorAccessTokenInline(admin.TabularInline):
    """Inline für Monitor-Zugriffs-Tokens"""
    model = MonitorAccessToken
    extra = 0
    fields = ['name', 'token', 'expires_at', 'is_active', 'use_count']
    readonly_fields = ['token', 'use_count']


class PlaylistItemInline(admin.TabularInline):
    """Inline für Playlist-Einträge"""
    model = PlaylistItem
    extra = 0
    fields = ['dashboard', 'order', 'duration']
    readonly_fields = []


# =============================================================================
# MONITOR PROFILE ADMIN
# =============================================================================

@admin.register(MonitorProfile)
class MonitorProfileAdmin(admin.ModelAdmin):
    """Admin für Monitor-Profile"""

    list_display = [
        'name',
        'dashboard_count',
        'default_badge',
        'active_badge',
        'display_order',
        'created_at'
    ]

    list_filter = ['is_active', 'is_default', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'created_by', 'updated_at', 'updated_by']

    fieldsets = (
        (_('Basis-Informationen'), {
            'fields': ('name', 'description')
        }),
        (_('Darstellung'), {
            'fields': ('icon', 'color', 'display_order')
        }),
        (_('Status'), {
            'fields': ('is_active', 'is_default')
        }),
        (_('Audit-Trail'), {
            'fields': ('created_at', 'created_by', 'updated_at', 'updated_by'),
            'classes': ('collapse',)
        }),
    )

    @admin.display(description=_('Dashboards'))
    def dashboard_count(self, obj):
        """Zeigt Anzahl Dashboards"""
        count = obj.dashboards.count()
        if count == 0:
            color = '#9ca3af'
        elif count < 3:
            color = '#3b82f6'
        else:
            color = '#10b981'

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 12px; font-size: 12px; font-weight: bold;">{}</span>',
            color, count
        )

    @admin.display(description=_('Standard'))
    def default_badge(self, obj):
        """Standard-Badge"""
        if obj.is_default:
            return format_html(
                '<span style="background-color: #10b981; color: white; padding: 3px 8px; '
                'border-radius: 10px; font-size: 10px; font-weight: bold;">✓ Standard</span>'
            )
        return format_html(
            '<span style="color: #9ca3af; font-size: 11px;">-</span>'
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


# =============================================================================
# DASHBOARD ADMIN
# =============================================================================

@admin.register(Dashboard)
class DashboardAdmin(admin.ModelAdmin):
    """Admin für Dashboards"""

    list_display = [
        'name',
        'profile',
        'theme_badge',
        'widget_count',
        'view_count_badge',
        'refresh_badge',
        'public_badge',
        'active_badge',
        'created_at'
    ]

    list_filter = ['profile', 'theme', 'is_public', 'is_active', 'use_canvas_layout', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['view_count', 'last_viewed_at', 'created_at', 'created_by', 'updated_at', 'updated_by']

    inlines = [WidgetInline, MonitorAccessTokenInline]

    fieldsets = (
        (_('Basis-Informationen'), {
            'fields': ('profile', 'name', 'description')
        }),
        (_('Layout'), {
            'fields': ('theme', 'use_canvas_layout', 'canvas_width', 'canvas_height', 'columns')
        }),
        (_('Auto-Refresh'), {
            'fields': ('auto_refresh', 'refresh_interval')
        }),
        (_('Vollbild-Modus'), {
            'fields': ('fullscreen_default', 'hide_header', 'hide_sidebar')
        }),
        (_('Berechtigungen'), {
            'fields': ('is_public', 'allowed_users')
        }),
        (_('Status'), {
            'fields': ('is_active', 'display_order')
        }),
        (_('Statistiken'), {
            'fields': ('view_count', 'last_viewed_at'),
            'classes': ('collapse',)
        }),
        (_('Audit-Trail'), {
            'fields': ('created_at', 'created_by', 'updated_at', 'updated_by'),
            'classes': ('collapse',)
        }),
    )

    filter_horizontal = ['allowed_users']

    @admin.display(description=_('Theme'))
    def theme_badge(self, obj):
        """Farbiger Theme-Badge"""
        colors = {
            DashboardTheme.LIGHT: '#f59e0b',    # orange-500
            DashboardTheme.DARK: '#6b7280',     # gray-500
            DashboardTheme.AUTO: '#3b82f6',     # blue-500
        }
        color = colors.get(obj.theme, '#9ca3af')

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 10px; font-size: 10px; font-weight: bold;">{}</span>',
            color, obj.get_theme_display()
        )

    @admin.display(description=_('Widgets'))
    def widget_count(self, obj):
        """Zeigt Anzahl Widgets"""
        count = obj.widgets.count()
        if count == 0:
            color = '#9ca3af'
        elif count < 5:
            color = '#3b82f6'
        elif count < 10:
            color = '#10b981'
        else:
            color = '#f59e0b'

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 12px; font-size: 12px; font-weight: bold;">{}</span>',
            color, count
        )

    @admin.display(description=_('Aufrufe'))
    def view_count_badge(self, obj):
        """View-Count-Badge"""
        if obj.view_count == 0:
            color = '#9ca3af'
        elif obj.view_count < 50:
            color = '#3b82f6'
        elif obj.view_count < 200:
            color = '#10b981'
        else:
            color = '#f59e0b'

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 12px; font-size: 11px; font-weight: bold;">👁 {}</span>',
            color, obj.view_count
        )

    @admin.display(description=_('Refresh'))
    def refresh_badge(self, obj):
        """Refresh-Intervall-Badge"""
        if obj.auto_refresh:
            return format_html(
                '<span style="background-color: #10b981; color: white; padding: 3px 8px; '
                'border-radius: 10px; font-size: 10px; font-weight: bold;">{}s</span>',
                obj.refresh_interval
            )
        else:
            return format_html(
                '<span style="background-color: #6b7280; color: white; padding: 3px 8px; '
                'border-radius: 10px; font-size: 10px; font-weight: bold;">✗</span>'
            )

    @admin.display(description=_('Öffentlich'))
    def public_badge(self, obj):
        """Öffentlich-Badge"""
        if obj.is_public:
            return format_html(
                '<span style="background-color: #10b981; color: white; padding: 3px 8px; '
                'border-radius: 10px; font-size: 10px; font-weight: bold;">✓</span>'
            )
        else:
            return format_html(
                '<span style="background-color: #6b7280; color: white; padding: 3px 8px; '
                'border-radius: 10px; font-size: 10px; font-weight: bold;">✗</span>'
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


# =============================================================================
# WIDGET ADMIN
# =============================================================================

@admin.register(Widget)
class WidgetAdmin(admin.ModelAdmin):
    """Admin für Widgets"""

    list_display = [
        'title',
        'dashboard',
        'type_badge',
        'size_badge',
        'position_display',
        'kpi',
        'refresh_badge',
        'active_badge',
        'display_order'
    ]

    list_filter = ['dashboard__profile', 'dashboard', 'widget_type', 'is_active']
    search_fields = ['title', 'description', 'dashboard__name']
    readonly_fields = ['last_updated_at', 'created_at', 'created_by', 'updated_at', 'updated_by']

    inlines = [WidgetAlertInline]

    fieldsets = (
        (_('Basis-Informationen'), {
            'fields': ('dashboard', 'title', 'description', 'widget_type')
        }),
        (_('Position & Größe (Grid-Modus)'), {
            'fields': ('row', 'column', 'width'),
            'classes': ('collapse',)
        }),
        (_('Position & Größe (Canvas-Modus)'), {
            'fields': ('x_position', 'y_position', 'canvas_width', 'height')
        }),
        (_('Datenquelle'), {
            'fields': ('kpi', 'data_source', 'config')
        }),
        (_('Chart-Einstellungen'), {
            'fields': ('chart_type',),
            'classes': ('collapse',)
        }),
        (_('Styling'), {
            'fields': ('background_color', 'text_color', 'border_color'),
            'classes': ('collapse',)
        }),
        (_('Refresh'), {
            'fields': ('auto_refresh', 'refresh_interval')
        }),
        (_('Status'), {
            'fields': ('is_active', 'display_order')
        }),
        (_('Cache'), {
            'fields': ('cached_data', 'last_updated_at'),
            'classes': ('collapse',)
        }),
        (_('Audit-Trail'), {
            'fields': ('created_at', 'created_by', 'updated_at', 'updated_by'),
            'classes': ('collapse',)
        }),
    )

    @admin.display(description=_('Typ'))
    def type_badge(self, obj):
        """Farbiger Typ-Badge"""
        colors = {
            WidgetType.KPI: '#3b82f6',        # blue-500
            WidgetType.CHART: '#10b981',      # green-500
            WidgetType.TABLE: '#f59e0b',      # orange-500
            WidgetType.LIST: '#8b5cf6',       # purple-500
            WidgetType.MAP: '#06b6d4',        # cyan-500
            WidgetType.GAUGE: '#14b8a6',      # teal-500
            WidgetType.PROGRESS: '#6366f1',   # indigo-500
            WidgetType.COUNTER: '#ec4899',    # pink-500
            WidgetType.ALERT: '#ef4444',      # red-500
            WidgetType.CLOCK: '#84cc16',      # lime-500
            WidgetType.WEATHER: '#0ea5e9',    # sky-500
            WidgetType.TEXT: '#64748b',       # slate-500
            WidgetType.PDF: '#dc2626',        # red-600
            WidgetType.ANNOUNCEMENTS: '#f97316',  # orange-600
            WidgetType.EVENTS: '#a855f7',     # purple-600
            WidgetType.CUSTOM: '#9ca3af',     # gray-400
        }
        color = colors.get(obj.widget_type, '#9ca3af')

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 10px; font-size: 10px; font-weight: bold;">{}</span>',
            color, obj.get_widget_type_display()
        )

    @admin.display(description=_('Größe'))
    def size_badge(self, obj):
        """Größen-Badge"""
        colors = {
            WidgetSize.SMALL: '#9ca3af',     # gray-400
            WidgetSize.MEDIUM: '#3b82f6',    # blue-500
            WidgetSize.LARGE: '#10b981',     # green-500
            WidgetSize.XLARGE: '#f59e0b',    # orange-500
            WidgetSize.FULL: '#ef4444',      # red-500
        }
        color = colors.get(obj.width, '#9ca3af')

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 10px; font-size: 10px; font-weight: bold;">{}</span>',
            color, obj.get_width_display()
        )

    @admin.display(description=_('Position'))
    def position_display(self, obj):
        """Zeigt Position im Grid"""
        return f"R{obj.row} C{obj.column}"

    @admin.display(description=_('Refresh'))
    def refresh_badge(self, obj):
        """Refresh-Intervall-Badge"""
        if obj.auto_refresh:
            return format_html(
                '<span style="background-color: #10b981; color: white; padding: 3px 8px; '
                'border-radius: 10px; font-size: 10px; font-weight: bold;">{}s</span>',
                obj.refresh_interval
            )
        else:
            return format_html(
                '<span style="background-color: #6b7280; color: white; padding: 3px 8px; '
                'border-radius: 10px; font-size: 10px; font-weight: bold;">✗</span>'
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


# =============================================================================
# WIDGET ALERT ADMIN
# =============================================================================

@admin.register(WidgetAlert)
class WidgetAlertAdmin(admin.ModelAdmin):
    """Admin für Widget-Alerts"""

    list_display = [
        'name',
        'widget',
        'severity_badge',
        'condition_display',
        'trigger_count_badge',
        'active_badge',
        'last_triggered_at'
    ]

    list_filter = ['severity', 'condition', 'is_active', 'widget__dashboard']
    search_fields = ['name', 'message', 'widget__title']
    readonly_fields = ['last_triggered_at', 'trigger_count', 'created_at', 'updated_at']

    fieldsets = (
        (_('Basis-Informationen'), {
            'fields': ('widget', 'name')
        }),
        (_('Bedingung'), {
            'fields': ('condition', 'threshold_value', 'threshold_value_max')
        }),
        (_('Alert'), {
            'fields': ('severity', 'message')
        }),
        (_('Benachrichtigung'), {
            'fields': ('send_notification', 'notification_users')
        }),
        (_('Status'), {
            'fields': ('is_active', 'last_triggered_at', 'trigger_count')
        }),
    )

    filter_horizontal = ['notification_users']

    @admin.display(description=_('Schweregrad'))
    def severity_badge(self, obj):
        """Farbiger Schweregrad-Badge"""
        colors = {
            'info': '#3b82f6',      # blue-500
            'warning': '#f59e0b',   # orange-500
            'error': '#ef4444',     # red-500
            'critical': '#7f1d1d',  # red-900
        }
        color = colors.get(obj.severity, '#9ca3af')

        icon = ''
        if obj.severity == 'critical':
            icon = '⚠ '

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 12px; font-size: 11px; font-weight: bold;">{}{}</span>',
            color, icon, obj.get_severity_display()
        )

    @admin.display(description=_('Bedingung'))
    def condition_display(self, obj):
        """Zeigt Bedingung"""
        if obj.condition == 'between' and obj.threshold_value_max:
            return f"{obj.threshold_value} - {obj.threshold_value_max}"
        return f"{obj.get_condition_display()} {obj.threshold_value}"

    @admin.display(description=_('Auslösungen'))
    def trigger_count_badge(self, obj):
        """Trigger-Count-Badge"""
        if obj.trigger_count == 0:
            color = '#9ca3af'
        elif obj.trigger_count < 10:
            color = '#3b82f6'
        elif obj.trigger_count < 50:
            color = '#f59e0b'
        else:
            color = '#ef4444'

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 12px; font-size: 12px; font-weight: bold;">{}</span>',
            color, obj.trigger_count
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


# =============================================================================
# MONITOR ACCESS TOKEN ADMIN
# =============================================================================

@admin.register(MonitorAccessToken)
class MonitorAccessTokenAdmin(admin.ModelAdmin):
    """Admin für Monitor-Zugriffs-Tokens"""

    list_display = [
        'name',
        'dashboard',
        'token_display',
        'expires_badge',
        'use_count_badge',
        'access_active_badge',
        'created_at'
    ]

    list_filter = ['dashboard__profile', 'dashboard', 'is_active', 'expires_at', 'created_at']
    search_fields = ['name', 'token', 'dashboard__name']
    readonly_fields = ['token', 'use_count', 'last_used_at', 'last_used_ip', 'created_at']

    fieldsets = (
        (_('Basis-Informationen'), {
            'fields': ('dashboard', 'name', 'token')
        }),
        (_('Gültigkeit'), {
            'fields': ('expires_at', 'max_uses', 'ip_whitelist')
        }),
        (_('Status'), {
            'fields': ('is_active', 'created_by')
        }),
        (_('Statistiken'), {
            'fields': ('use_count', 'last_used_at', 'last_used_ip'),
            'classes': ('collapse',)
        }),
    )

    @admin.display(description=_('Token'))
    def token_display(self, obj):
        """Zeigt Token gekürzt"""
        if obj.token:
            return f"{obj.token[:8]}...{obj.token[-8:]}"
        return '-'

    @admin.display(description=_('Gültig bis'))
    def expires_badge(self, obj):
        """Ablaufdatum-Badge"""
        if not obj.expires_at:
            return format_html(
                '<span style="background-color: #10b981; color: white; padding: 3px 8px; '
                'border-radius: 10px; font-size: 10px; font-weight: bold;">∞ Unbegrenzt</span>'
            )

        from django.utils import timezone
        if timezone.now() > obj.expires_at:
            return format_html(
                '<span style="background-color: #ef4444; color: white; padding: 3px 8px; '
                'border-radius: 10px; font-size: 10px; font-weight: bold;">⚠ Abgelaufen</span>'
            )
        else:
            return format_html(
                '<span style="color: #3b82f6; font-size: 11px;">{}</span>',
                obj.expires_at.strftime('%d.%m.%Y')
            )

    @admin.display(description=_('Verwendungen'))
    def use_count_badge(self, obj):
        """Verwendungs-Badge"""
        if obj.max_uses:
            percentage = (obj.use_count / obj.max_uses) * 100
            if percentage >= 90:
                color = '#ef4444'  # red
            elif percentage >= 70:
                color = '#f59e0b'  # orange
            else:
                color = '#10b981'  # green

            return format_html(
                '<span style="background-color: {}; color: white; padding: 3px 8px; '
                'border-radius: 10px; font-size: 10px; font-weight: bold;">{}/{}</span>',
                color, obj.use_count, obj.max_uses
            )
        else:
            color = '#3b82f6' if obj.use_count > 0 else '#9ca3af'
            return format_html(
                '<span style="background-color: {}; color: white; padding: 3px 8px; '
                'border-radius: 10px; font-size: 10px; font-weight: bold;">{}</span>',
                color, obj.use_count
            )

    @admin.display(description=_('Aktiv'))
    def access_active_badge(self, obj):
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

    def save_model(self, request, obj, form, change):
        """Generiert Token wenn leer"""
        if not obj.token:
            obj.generate_token()
        if not obj.created_by:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


# =============================================================================
# PLAYLIST ADMIN
# =============================================================================

@admin.register(MonitorPlaylist)
class MonitorPlaylistAdmin(admin.ModelAdmin):
    """Admin für Monitor-Playlists"""

    list_display = [
        'name',
        'dashboard_count_badge',
        'duration_badge',
        'play_count_badge',
        'playlist_active_badge',
        'created_at'
    ]

    list_filter = ['is_active', 'auto_rotate', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['play_count', 'last_played_at', 'created_at', 'created_by', 'updated_at', 'updated_by']

    inlines = [PlaylistItemInline]

    fieldsets = (
        (_('Basis-Informationen'), {
            'fields': ('name', 'description')
        }),
        (_('Rotations-Einstellungen'), {
            'fields': ('auto_rotate', 'default_duration')
        }),
        (_('Status'), {
            'fields': ('is_active',)
        }),
        (_('Statistiken'), {
            'fields': ('play_count', 'last_played_at'),
            'classes': ('collapse',)
        }),
        (_('Audit-Trail'), {
            'fields': ('created_at', 'created_by', 'updated_at', 'updated_by'),
            'classes': ('collapse',)
        }),
    )

    @admin.display(description=_('Dashboards'))
    def dashboard_count_badge(self, obj):
        """Dashboard-Anzahl-Badge"""
        count = obj.items.count()
        if count == 0:
            color = '#9ca3af'
        elif count < 3:
            color = '#3b82f6'
        elif count < 5:
            color = '#10b981'
        else:
            color = '#f59e0b'

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 12px; font-size: 12px; font-weight: bold;">{}</span>',
            color, count
        )

    @admin.display(description=_('Standard-Dauer'))
    def duration_badge(self, obj):
        """Dauer-Badge"""
        return format_html(
            '<span style="background-color: #3b82f6; color: white; padding: 3px 8px; '
            'border-radius: 10px; font-size: 10px; font-weight: bold;">{}s</span>',
            obj.default_duration
        )

    @admin.display(description=_('Abspielungen'))
    def play_count_badge(self, obj):
        """Abspielzähler-Badge"""
        if obj.play_count == 0:
            color = '#9ca3af'
        elif obj.play_count < 100:
            color = '#3b82f6'
        elif obj.play_count < 500:
            color = '#10b981'
        else:
            color = '#f59e0b'

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 12px; font-size: 12px; font-weight: bold;">{}</span>',
            color, obj.play_count
        )

    @admin.display(description=_('Aktiv'))
    def playlist_active_badge(self, obj):
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
