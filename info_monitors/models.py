"""
Info Monitors Models für FLVS

Implementiert ein Dashboard-Builder-System mit:
- Konfigurierbare Dashboards für Info-Monitore
- Flexibles Widget-System (KPIs, Charts, Listen, Tabellen)
- Auto-Refresh & Vollbild-Modus
- Mehrere Monitor-Profile (Leitstelle, Werkstatt, Lager)
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from core.models import User, AuditedModel, TimeStampedModel
from reporting.models import KPI
import json


# =============================================================================
# CHOICES & ENUMS
# =============================================================================

class WidgetType(models.TextChoices):
    """Widget-Typen"""
    KPI = 'kpi', _('KPI-Anzeige')
    CHART = 'chart', _('Diagramm')
    TABLE = 'table', _('Tabelle')
    LIST = 'list', _('Liste')
    MAP = 'map', _('Karte')
    GAUGE = 'gauge', _('Tachometer')
    PROGRESS = 'progress', _('Fortschrittsbalken')
    COUNTER = 'counter', _('Zähler')
    ALERT = 'alert', _('Warnungen')
    CLOCK = 'clock', _('Uhr')
    WEATHER = 'weather', _('Wetter')
    TEXT = 'text', _('Text/Information')
    PDF = 'pdf', _('PDF-Dokument')
    ANNOUNCEMENTS = 'announcements', _('Bekanntmachungen')
    EVENTS = 'events', _('Termine/Kalender')
    CUSTOM = 'custom', _('Benutzerdefiniert')


class ChartType(models.TextChoices):
    """Diagramm-Typen"""
    LINE = 'line', _('Liniendiagramm')
    BAR = 'bar', _('Balkendiagramm')
    PIE = 'pie', _('Kreisdiagramm')
    DOUGHNUT = 'doughnut', _('Ring-Diagramm')
    AREA = 'area', _('Flächendiagramm')
    RADAR = 'radar', _('Radar-Diagramm')
    SCATTER = 'scatter', _('Streudiagramm')


class DashboardTheme(models.TextChoices):
    """Dashboard-Themes"""
    LIGHT = 'light', _('Hell')
    DARK = 'dark', _('Dunkel')
    AUTO = 'auto', _('Automatisch')


class WidgetSize(models.TextChoices):
    """Widget-Größen (Grid-Spalten)"""
    SMALL = '1', _('Klein (1/12)')
    MEDIUM = '2', _('Mittel (2/12)')
    LARGE = '3', _('Groß (3/12)')
    XLARGE = '4', _('Extra Groß (4/12)')
    FULL = '12', _('Vollbreite (12/12)')


# =============================================================================
# MONITOR PROFILE
# =============================================================================

class MonitorProfile(AuditedModel):
    """
    Monitor-Profile für verschiedene Einsatzzwecke

    Beispiele:
    - Leitstelle: Aktive Einsätze, Fahrzeugstatus, Wetter
    - Werkstatt: Wartungen, Reparaturen, Ersatzteile
    - Lager: Bestände, Ablaufdaten, Bestellungen
    """

    name = models.CharField(
        _('Name'),
        max_length=200
    )

    description = models.TextField(
        _('Beschreibung'),
        blank=True
    )

    icon = models.CharField(
        _('Icon'),
        max_length=50,
        blank=True
    )

    color = models.CharField(
        _('Farbe'),
        max_length=20,
        blank=True
    )

    is_active = models.BooleanField(
        _('Aktiv'),
        default=True
    )

    is_default = models.BooleanField(
        _('Standard-Profil'),
        default=False,
        help_text=_('Wird automatisch geladen wenn kein Profil ausgewählt')
    )

    # Display-Einstellungen
    display_order = models.PositiveIntegerField(
        _('Anzeigereihenfolge'),
        default=0
    )

    class Meta:
        verbose_name = _('Monitor-Profil')
        verbose_name_plural = _('Monitor-Profile')
        ordering = ['display_order', 'name']
        indexes = [
            models.Index(fields=['is_active', 'display_order']),
            models.Index(fields=['is_default']),
        ]

    def __str__(self):
        return self.name


# =============================================================================
# DASHBOARDS
# =============================================================================

class Dashboard(AuditedModel):
    """
    Dashboard-Konfiguration

    Enthält Layout und Einstellungen für ein Dashboard
    """

    profile = models.ForeignKey(
        MonitorProfile,
        on_delete=models.CASCADE,
        related_name='dashboards',
        verbose_name=_('Profil')
    )

    name = models.CharField(
        _('Name'),
        max_length=200
    )

    description = models.TextField(
        _('Beschreibung'),
        blank=True
    )

    # Layout-Einstellungen
    theme = models.CharField(
        _('Theme'),
        max_length=10,
        choices=DashboardTheme.choices,
        default=DashboardTheme.LIGHT
    )

    # Layout-Modus
    use_canvas_layout = models.BooleanField(
        _('Canvas-Layout verwenden'),
        default=True,
        help_text=_('Canvas = freie Positionierung, Grid = 12-Spalten-System')
    )

    canvas_width = models.PositiveIntegerField(
        _('Canvas-Breite (px)'),
        default=1920,
        validators=[MinValueValidator(800)],
        help_text=_('Breite des Canvas in Pixel (nur für Canvas-Modus)')
    )

    canvas_height = models.PositiveIntegerField(
        _('Canvas-Höhe (px)'),
        default=1080,
        validators=[MinValueValidator(600)],
        help_text=_('Höhe des Canvas in Pixel (nur für Canvas-Modus)')
    )

    columns = models.PositiveSmallIntegerField(
        _('Spalten'),
        default=12,
        validators=[MinValueValidator(1), MaxValueValidator(12)],
        help_text=_('Grid-Spalten (nur für Grid-Modus)')
    )

    # Auto-Refresh
    auto_refresh = models.BooleanField(
        _('Auto-Refresh'),
        default=True
    )

    refresh_interval = models.PositiveIntegerField(
        _('Refresh-Intervall (Sekunden)'),
        default=30,
        validators=[MinValueValidator(5)],
        help_text=_('Mindestens 5 Sekunden')
    )

    # Vollbild-Modus
    fullscreen_default = models.BooleanField(
        _('Vollbild als Standard'),
        default=False
    )

    hide_header = models.BooleanField(
        _('Header ausblenden'),
        default=False
    )

    hide_sidebar = models.BooleanField(
        _('Sidebar ausblenden'),
        default=False
    )

    # Berechtigungen
    is_public = models.BooleanField(
        _('Öffentlich'),
        default=False
    )

    allowed_users = models.ManyToManyField(
        User,
        blank=True,
        related_name='dashboards',
        verbose_name=_('Berechtigte Benutzer')
    )

    # Status
    is_active = models.BooleanField(
        _('Aktiv'),
        default=True
    )

    display_order = models.PositiveIntegerField(
        _('Anzeigereihenfolge'),
        default=0
    )

    # Statistiken
    view_count = models.PositiveIntegerField(
        _('Aufrufe'),
        default=0
    )

    last_viewed_at = models.DateTimeField(
        _('Zuletzt angesehen'),
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = _('Dashboard')
        verbose_name_plural = _('Dashboards')
        ordering = ['profile', 'display_order', 'name']
        indexes = [
            models.Index(fields=['profile', 'is_active']),
            models.Index(fields=['is_public']),
            models.Index(fields=['display_order']),
        ]
        permissions = [
            ('publish_dashboard', 'Kann Dashboards veröffentlichen'),
            ('view_all_dashboards', 'Kann alle Dashboards sehen'),
            ('edit_all_dashboards', 'Kann alle Dashboards bearbeiten'),
        ]

    def __str__(self):
        return f"{self.profile.name} - {self.name}"

    def increment_view_count(self):
        """Erhöht Aufrufzähler"""
        self.view_count += 1
        self.last_viewed_at = timezone.now()
        self.save(update_fields=['view_count', 'last_viewed_at'])


# =============================================================================
# WIDGETS
# =============================================================================

class Widget(AuditedModel):
    """
    Dashboard-Widget

    Flexible Widget-Komponente für verschiedene Datenvisualisierungen
    """

    dashboard = models.ForeignKey(
        Dashboard,
        on_delete=models.CASCADE,
        related_name='widgets',
        verbose_name=_('Dashboard')
    )

    title = models.CharField(
        _('Titel'),
        max_length=200
    )

    description = models.TextField(
        _('Beschreibung'),
        blank=True
    )

    # Widget-Typ
    widget_type = models.CharField(
        _('Widget-Typ'),
        max_length=20,
        choices=WidgetType.choices
    )

    # Position & Größe (unterstützt Grid UND Canvas-Modus)
    # Grid-Modus (optional)
    row = models.PositiveIntegerField(
        _('Zeile'),
        default=0,
        null=True,
        blank=True,
        help_text=_('Zeile im Grid (0 = erste Zeile) - nur für Grid-Modus')
    )

    column = models.PositiveIntegerField(
        _('Spalte'),
        default=0,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(11)],
        help_text=_('Spalte im Grid (0-11) - nur für Grid-Modus')
    )

    width = models.CharField(
        _('Breite'),
        max_length=2,
        choices=WidgetSize.choices,
        default=WidgetSize.LARGE,
        blank=True,
        help_text=_('Anzahl Spalten (12-Spalten-Grid) - nur für Grid-Modus')
    )

    # Canvas-Modus (freie Positionierung)
    x_position = models.PositiveIntegerField(
        _('X-Position (px)'),
        default=0,
        null=True,
        blank=True,
        help_text=_('X-Koordinate in Pixel - nur für Canvas-Modus')
    )

    y_position = models.PositiveIntegerField(
        _('Y-Position (px)'),
        default=0,
        null=True,
        blank=True,
        help_text=_('Y-Koordinate in Pixel - nur für Canvas-Modus')
    )

    canvas_width = models.PositiveIntegerField(
        _('Canvas-Breite (px)'),
        default=400,
        null=True,
        blank=True,
        validators=[MinValueValidator(100)],
        help_text=_('Breite in Pixel - nur für Canvas-Modus')
    )

    height = models.PositiveIntegerField(
        _('Höhe (px)'),
        default=300,
        validators=[MinValueValidator(100)],
        help_text=_('Höhe in Pixel (für beide Modi)')
    )

    # Datenquelle
    # Option 1: KPI-Verknüpfung
    kpi = models.ForeignKey(
        KPI,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='widgets',
        verbose_name=_('KPI')
    )

    # Option 2: Custom Query
    data_source = models.TextField(
        _('Datenquelle'),
        blank=True,
        help_text=_('SQL-Query oder API-Endpoint für Daten')
    )

    # Konfiguration (JSON)
    config = models.JSONField(
        _('Konfiguration'),
        default=dict,
        blank=True,
        help_text=_('Widget-spezifische Konfiguration (JSON)')
    )

    # PDF-Datei (für PDF-Widgets)
    pdf_file = models.FileField(
        _('PDF-Datei'),
        upload_to='info_monitors/pdfs/%Y/%m/',
        blank=True,
        null=True,
        help_text=_('PDF-Datei für PDF-Widgets')
    )

    # Chart-spezifisch
    chart_type = models.CharField(
        _('Diagramm-Typ'),
        max_length=20,
        choices=ChartType.choices,
        blank=True,
        help_text=_('Nur für Chart-Widgets')
    )

    # Styling
    background_color = models.CharField(
        _('Hintergrundfarbe'),
        max_length=20,
        blank=True
    )

    text_color = models.CharField(
        _('Textfarbe'),
        max_length=20,
        blank=True
    )

    border_color = models.CharField(
        _('Rahmenfarbe'),
        max_length=20,
        blank=True
    )

    # Refresh
    auto_refresh = models.BooleanField(
        _('Auto-Refresh'),
        default=True
    )

    refresh_interval = models.PositiveIntegerField(
        _('Refresh-Intervall (Sekunden)'),
        default=60,
        validators=[MinValueValidator(5)]
    )

    # Status
    is_active = models.BooleanField(
        _('Aktiv'),
        default=True
    )

    display_order = models.PositiveIntegerField(
        _('Anzeigereihenfolge'),
        default=0
    )

    # Cache
    cached_data = models.JSONField(
        _('Gecachte Daten'),
        default=dict,
        blank=True
    )

    last_updated_at = models.DateTimeField(
        _('Zuletzt aktualisiert'),
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = _('Widget')
        verbose_name_plural = _('Widgets')
        ordering = ['dashboard', 'row', 'column', 'display_order']
        indexes = [
            models.Index(fields=['dashboard', 'is_active']),
            models.Index(fields=['widget_type']),
            models.Index(fields=['kpi']),
            models.Index(fields=['row', 'column']),
        ]

    def __str__(self):
        return f"{self.dashboard.name} - {self.title}"

    def get_width_class(self):
        """Gibt Bootstrap-CSS-Klasse für Breite zurück"""
        width_map = {
            WidgetSize.SMALL: 'col-1',
            WidgetSize.MEDIUM: 'col-2',
            WidgetSize.LARGE: 'col-3',
            WidgetSize.XLARGE: 'col-4',
            WidgetSize.FULL: 'col-12',
        }
        return width_map.get(self.width, 'col-3')

    def update_cached_data(self, data):
        """Aktualisiert gecachte Daten"""
        self.cached_data = data
        self.last_updated_at = timezone.now()
        self.save(update_fields=['cached_data', 'last_updated_at'])


# =============================================================================
# WIDGET ALERTS
# =============================================================================

class WidgetAlert(TimeStampedModel):
    """
    Alert-Konfiguration für Widgets

    Definiert Schwellwerte und Benachrichtigungen
    """

    widget = models.ForeignKey(
        Widget,
        on_delete=models.CASCADE,
        related_name='alerts',
        verbose_name=_('Widget')
    )

    name = models.CharField(
        _('Name'),
        max_length=200
    )

    # Bedingung
    condition = models.CharField(
        _('Bedingung'),
        max_length=20,
        choices=[
            ('greater', _('Größer als')),
            ('less', _('Kleiner als')),
            ('equal', _('Gleich')),
            ('not_equal', _('Ungleich')),
            ('between', _('Zwischen')),
        ]
    )

    threshold_value = models.DecimalField(
        _('Schwellwert'),
        max_digits=12,
        decimal_places=2
    )

    threshold_value_max = models.DecimalField(
        _('Max. Schwellwert'),
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_('Für "Zwischen"-Bedingung')
    )

    # Alert-Eigenschaften
    severity = models.CharField(
        _('Schweregrad'),
        max_length=20,
        choices=[
            ('info', _('Info')),
            ('warning', _('Warnung')),
            ('error', _('Fehler')),
            ('critical', _('Kritisch')),
        ],
        default='warning'
    )

    message = models.TextField(
        _('Nachricht'),
        help_text=_('Alert-Nachricht die angezeigt wird')
    )

    # Benachrichtigung
    send_notification = models.BooleanField(
        _('Benachrichtigung senden'),
        default=False
    )

    notification_users = models.ManyToManyField(
        User,
        blank=True,
        related_name='widget_alerts',
        verbose_name=_('Empfänger')
    )

    # Status
    is_active = models.BooleanField(
        _('Aktiv'),
        default=True
    )

    last_triggered_at = models.DateTimeField(
        _('Zuletzt ausgelöst'),
        null=True,
        blank=True
    )

    trigger_count = models.PositiveIntegerField(
        _('Anzahl Auslösungen'),
        default=0
    )

    class Meta:
        verbose_name = _('Widget-Alert')
        verbose_name_plural = _('Widget-Alerts')
        ordering = ['widget', '-severity']
        indexes = [
            models.Index(fields=['widget', 'is_active']),
            models.Index(fields=['severity']),
        ]

    def __str__(self):
        return f"{self.widget.title} - {self.name}"

    def check_condition(self, value):
        """Prüft ob Alert-Bedingung erfüllt ist"""
        try:
            value = float(value)
            threshold = float(self.threshold_value)

            if self.condition == 'greater':
                return value > threshold
            elif self.condition == 'less':
                return value < threshold
            elif self.condition == 'equal':
                return value == threshold
            elif self.condition == 'not_equal':
                return value != threshold
            elif self.condition == 'between' and self.threshold_value_max:
                threshold_max = float(self.threshold_value_max)
                return threshold <= value <= threshold_max

        except (ValueError, TypeError):
            return False

        return False

    def trigger(self):
        """Löst Alert aus"""
        self.last_triggered_at = timezone.now()
        self.trigger_count += 1
        self.save(update_fields=['last_triggered_at', 'trigger_count'])


# =============================================================================
# MONITOR ACCESS TOKENS
# =============================================================================

class MonitorAccessToken(TimeStampedModel):
    """
    Zugriffs-Token für öffentliche Monitor-Anzeige

    Ermöglicht Token-basierten Zugriff auf Dashboards ohne Login.
    Optional mit Ablaufdatum.
    """

    dashboard = models.ForeignKey(
        Dashboard,
        on_delete=models.CASCADE,
        related_name='access_tokens',
        verbose_name=_('Dashboard')
    )

    name = models.CharField(
        _('Name'),
        max_length=200,
        help_text=_('Beschreibender Name (z.B. "Monitor Leitstelle")')
    )

    token = models.CharField(
        _('Token'),
        max_length=64,
        unique=True,
        db_index=True,
        help_text=_('Eindeutiger Zugriffs-Token')
    )

    # Ablaufdatum
    expires_at = models.DateTimeField(
        _('Gültig bis'),
        null=True,
        blank=True,
        help_text=_('Optional: Ablaufdatum des Tokens')
    )

    # Zugriffsbeschränkungen
    ip_whitelist = models.TextField(
        _('IP-Whitelist'),
        blank=True,
        help_text=_('Komma-getrennte Liste erlaubter IP-Adressen (leer = alle)')
    )

    max_uses = models.PositiveIntegerField(
        _('Max. Verwendungen'),
        null=True,
        blank=True,
        help_text=_('Optional: Maximale Anzahl Zugriffe')
    )

    # Statistiken
    use_count = models.PositiveIntegerField(
        _('Verwendungen'),
        default=0
    )

    last_used_at = models.DateTimeField(
        _('Zuletzt verwendet'),
        null=True,
        blank=True
    )

    last_used_ip = models.GenericIPAddressField(
        _('Letzte IP'),
        null=True,
        blank=True
    )

    # Status
    is_active = models.BooleanField(
        _('Aktiv'),
        default=True
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_monitor_tokens',
        verbose_name=_('Erstellt von')
    )

    class Meta:
        verbose_name = _('Monitor-Zugriffs-Token')
        verbose_name_plural = _('Monitor-Zugriffs-Tokens')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['token', 'is_active']),
            models.Index(fields=['dashboard', 'is_active']),
            models.Index(fields=['expires_at']),
        ]
        permissions = [
            ('manage_access_tokens', 'Kann Zugriffs-Tokens verwalten'),
            ('create_access_token', 'Kann Zugriffs-Tokens erstellen'),
            ('delete_access_token', 'Kann Zugriffs-Tokens löschen'),
        ]

    def __str__(self):
        return f"{self.name} - {self.dashboard.name}"

    def is_valid(self, ip_address=None):
        """Prüft ob Token gültig ist"""
        if not self.is_active:
            return False

        # Ablaufdatum prüfen
        if self.expires_at and timezone.now() > self.expires_at:
            return False

        # Max. Verwendungen prüfen
        if self.max_uses and self.use_count >= self.max_uses:
            return False

        # IP-Whitelist prüfen
        if self.ip_whitelist and ip_address:
            allowed_ips = [ip.strip() for ip in self.ip_whitelist.split(',')]
            if ip_address not in allowed_ips:
                return False

        return True

    def increment_usage(self, ip_address=None):
        """Erhöht Verwendungszähler"""
        self.use_count += 1
        self.last_used_at = timezone.now()
        if ip_address:
            self.last_used_ip = ip_address
        self.save(update_fields=['use_count', 'last_used_at', 'last_used_ip'])

    def generate_token(self):
        """Generiert einen eindeutigen Token"""
        import secrets
        self.token = secrets.token_urlsafe(48)


# =============================================================================
# PLAYLISTS
# =============================================================================

class MonitorPlaylist(AuditedModel):
    """
    Playlist für automatische Rotation mehrerer Dashboards

    Ermöglicht sequenzielles Durchlaufen mehrerer Dashboards
    auf einem Monitor.
    """

    name = models.CharField(
        _('Name'),
        max_length=200
    )

    description = models.TextField(
        _('Beschreibung'),
        blank=True
    )

    # Dashboards in der Playlist
    dashboards = models.ManyToManyField(
        Dashboard,
        through='PlaylistItem',
        related_name='playlists',
        verbose_name=_('Dashboards')
    )

    # Rotations-Einstellungen
    auto_rotate = models.BooleanField(
        _('Auto-Rotation'),
        default=True
    )

    default_duration = models.PositiveIntegerField(
        _('Standard-Anzeigedauer (Sekunden)'),
        default=60,
        validators=[MinValueValidator(5)],
        help_text=_('Standard-Dauer pro Dashboard')
    )

    # Status
    is_active = models.BooleanField(
        _('Aktiv'),
        default=True
    )

    # Statistiken
    play_count = models.PositiveIntegerField(
        _('Abspielungen'),
        default=0
    )

    last_played_at = models.DateTimeField(
        _('Zuletzt abgespielt'),
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = _('Monitor-Playlist')
        verbose_name_plural = _('Monitor-Playlists')
        ordering = ['name']
        permissions = [
            ('manage_playlists', 'Kann Playlists verwalten'),
        ]

    def __str__(self):
        return self.name

    def increment_play_count(self):
        """Erhöht Abspiel-Zähler"""
        self.play_count += 1
        self.last_played_at = timezone.now()
        self.save(update_fields=['play_count', 'last_played_at'])


class PlaylistItem(models.Model):
    """
    Verknüpfung zwischen Playlist und Dashboard

    Ermöglicht Sortierung und individuelle Anzeigedauer pro Dashboard.
    """

    playlist = models.ForeignKey(
        MonitorPlaylist,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_('Playlist')
    )

    dashboard = models.ForeignKey(
        Dashboard,
        on_delete=models.CASCADE,
        related_name='playlist_items',
        verbose_name=_('Dashboard')
    )

    order = models.PositiveIntegerField(
        _('Reihenfolge'),
        default=0
    )

    duration = models.PositiveIntegerField(
        _('Anzeigedauer (Sekunden)'),
        null=True,
        blank=True,
        validators=[MinValueValidator(5)],
        help_text=_('Überschreibt Standard-Dauer der Playlist (optional)')
    )

    class Meta:
        verbose_name = _('Playlist-Eintrag')
        verbose_name_plural = _('Playlist-Einträge')
        ordering = ['playlist', 'order']
        unique_together = [['playlist', 'dashboard']]
        indexes = [
            models.Index(fields=['playlist', 'order']),
        ]

    def __str__(self):
        return f"{self.playlist.name} - {self.dashboard.name}"

    def get_duration(self):
        """Gibt Anzeigedauer zurück (eigene oder Standard)"""
        return self.duration if self.duration else self.playlist.default_duration
