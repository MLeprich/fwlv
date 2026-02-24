"""
Reporting & KPI Models für FLVS

Implementiert ein umfassendes Reporting-System mit:
- Vordefinierte Report-Templates
- Automatische Report-Generierung (Celery)
- KPI-Dashboards
- Export-Funktionen (PDF, Excel, CSV)
- Scheduled Reports
"""

from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from core.models import User, AuditedModel, TimeStampedModel
import json


# =============================================================================
# CHOICES & ENUMS
# =============================================================================

class ReportType(models.TextChoices):
    """Report-Typen"""
    INVENTORY = 'inventory', _('Bestandsübersicht')
    EXPIRING = 'expiring', _('Ablaufende Items')
    LOW_STOCK = 'low_stock', _('Niedrige Bestände')
    PROCUREMENT = 'procurement', _('Bestellübersicht')
    VEHICLE = 'vehicle', _('Fahrzeugübersicht')
    INSPECTION = 'inspection', _('Prüfungen & Wartungen')
    PERSONNEL = 'personnel', _('Personalübersicht')
    DOCUMENT = 'document', _('Dokumentenübersicht')
    AUDIT = 'audit', _('Audit-Trail')
    CUSTOM = 'custom', _('Benutzerdefiniert')


class ReportFormat(models.TextChoices):
    """Export-Formate"""
    PDF = 'pdf', _('PDF')
    EXCEL = 'excel', _('Excel (XLSX)')
    CSV = 'csv', _('CSV')
    HTML = 'html', _('HTML')
    JSON = 'json', _('JSON')


class ReportStatus(models.TextChoices):
    """Report-Status"""
    PENDING = 'pending', _('Ausstehend')
    GENERATING = 'generating', _('Wird erstellt')
    COMPLETED = 'completed', _('Abgeschlossen')
    FAILED = 'failed', _('Fehlgeschlagen')
    EXPIRED = 'expired', _('Abgelaufen')


class ScheduleFrequency(models.TextChoices):
    """Zeitplan-Frequenz"""
    DAILY = 'daily', _('Täglich')
    WEEKLY = 'weekly', _('Wöchentlich')
    MONTHLY = 'monthly', _('Monatlich')
    QUARTERLY = 'quarterly', _('Vierteljährlich')
    YEARLY = 'yearly', _('Jährlich')
    CUSTOM = 'custom', _('Benutzerdefiniert')


class KPIType(models.TextChoices):
    """KPI-Typen"""
    COUNT = 'count', _('Anzahl')
    SUM = 'sum', _('Summe')
    AVERAGE = 'average', _('Durchschnitt')
    PERCENTAGE = 'percentage', _('Prozentsatz')
    RATIO = 'ratio', _('Verhältnis')
    TREND = 'trend', _('Trend')


class KPICategory(models.TextChoices):
    """KPI-Kategorien"""
    INVENTORY = 'inventory', _('Lagerbestand')
    FINANCIAL = 'financial', _('Finanzen')
    OPERATIONAL = 'operational', _('Betrieb')
    QUALITY = 'quality', _('Qualität')
    COMPLIANCE = 'compliance', _('Compliance')


# =============================================================================
# REPORT TEMPLATES
# =============================================================================

class ReportTemplate(AuditedModel):
    """
    Vordefinierte Report-Templates

    Definiert Struktur und Parameter für wiederverwendbare Reports
    """

    name = models.CharField(
        _('Name'),
        max_length=200
    )

    description = models.TextField(
        _('Beschreibung'),
        blank=True
    )

    report_type = models.CharField(
        _('Report-Typ'),
        max_length=20,
        choices=ReportType.choices
    )

    # SQL-Query oder Python-Code für Report-Generierung
    query = models.TextField(
        _('Query / Code'),
        help_text=_('SQL-Query oder Python-Code für Datenabfrage')
    )

    # Template-Parameter (JSON)
    parameters = models.JSONField(
        _('Parameter'),
        default=dict,
        blank=True,
        help_text=_('JSON-Objekt mit Template-Parametern')
    )

    # Template-Datei für Rendering
    template_file = models.CharField(
        _('Template-Datei'),
        max_length=255,
        blank=True,
        help_text=_('Django-Template für HTML/PDF-Rendering')
    )

    # Verfügbare Export-Formate
    available_formats = models.JSONField(
        _('Verfügbare Formate'),
        default=list,
        help_text=_('Liste der unterstützten Export-Formate')
    )

    # Berechtigungen
    is_public = models.BooleanField(
        _('Öffentlich'),
        default=False,
        help_text=_('Für alle Benutzer sichtbar')
    )

    allowed_users = models.ManyToManyField(
        User,
        blank=True,
        related_name='report_templates',
        verbose_name=_('Berechtigte Benutzer')
    )

    is_active = models.BooleanField(
        _('Aktiv'),
        default=True
    )

    # Statistiken
    usage_count = models.PositiveIntegerField(
        _('Verwendungen'),
        default=0
    )

    class Meta:
        verbose_name = _('Report-Template')
        verbose_name_plural = _('Report-Templates')
        ordering = ['name']
        indexes = [
            models.Index(fields=['report_type', 'is_active']),
            models.Index(fields=['is_public']),
        ]
        permissions = [
            ('view_reporting_dashboard', 'Kann Reports & KPIs Dashboard sehen'),
            ('view_module_reports', 'Kann Modul-Reports sehen'),
            ('generate_reports', 'Kann Reports generieren'),
            ('schedule_reports', 'Kann Reports planen'),
            ('export_reports', 'Kann Reports exportieren'),
            ('view_inventory_dashboard', 'Kann Lager-Dashboard sehen'),
        ]

    def __str__(self):
        return self.name

    def increment_usage(self):
        """Erhöht Verwendungszähler"""
        self.usage_count += 1
        self.save(update_fields=['usage_count'])


# =============================================================================
# REPORTS
# =============================================================================

class Report(AuditedModel):
    """
    Generierte Reports

    Speichert generierte Reports mit Metadaten und Datei-Link
    """

    template = models.ForeignKey(
        ReportTemplate,
        on_delete=models.PROTECT,
        related_name='reports',
        verbose_name=_('Template'),
        null=True,
        blank=True
    )

    title = models.CharField(
        _('Titel'),
        max_length=255
    )

    description = models.TextField(
        _('Beschreibung'),
        blank=True
    )

    report_type = models.CharField(
        _('Report-Typ'),
        max_length=20,
        choices=ReportType.choices
    )

    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=ReportStatus.choices,
        default=ReportStatus.PENDING
    )

    # Zeitraum
    date_from = models.DateField(
        _('Von'),
        null=True,
        blank=True
    )

    date_to = models.DateField(
        _('Bis'),
        null=True,
        blank=True
    )

    # Parameter für Report-Generierung
    parameters = models.JSONField(
        _('Parameter'),
        default=dict,
        blank=True
    )

    # Generierte Datei
    file = models.FileField(
        _('Datei'),
        upload_to='reports/%Y/%m/',
        blank=True
    )

    file_format = models.CharField(
        _('Format'),
        max_length=10,
        choices=ReportFormat.choices,
        default=ReportFormat.PDF
    )

    file_size = models.PositiveIntegerField(
        _('Dateigröße (Bytes)'),
        null=True,
        blank=True
    )

    # Generierungs-Metadaten
    generation_started_at = models.DateTimeField(
        _('Generierung gestartet'),
        null=True,
        blank=True
    )

    generation_completed_at = models.DateTimeField(
        _('Generierung abgeschlossen'),
        null=True,
        blank=True
    )

    generation_duration = models.PositiveIntegerField(
        _('Generierungsdauer (Sekunden)'),
        null=True,
        blank=True
    )

    # Fehlerbehandlung
    error_message = models.TextField(
        _('Fehlermeldung'),
        blank=True
    )

    # Ablauf
    expires_at = models.DateTimeField(
        _('Läuft ab am'),
        null=True,
        blank=True,
        help_text=_('Reports werden nach Ablauf automatisch gelöscht')
    )

    # Statistiken
    download_count = models.PositiveIntegerField(
        _('Downloads'),
        default=0
    )

    last_downloaded_at = models.DateTimeField(
        _('Zuletzt heruntergeladen'),
        null=True,
        blank=True
    )

    # Verknüpfung zu Objekt (optional)
    related_content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_('Verknüpfter Typ')
    )

    related_object_id = models.PositiveIntegerField(
        _('Verknüpftes Objekt ID'),
        null=True,
        blank=True
    )

    related_object = GenericForeignKey('related_content_type', 'related_object_id')

    class Meta:
        verbose_name = _('Report')
        verbose_name_plural = _('Reports')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['template', '-created_at']),
            models.Index(fields=['report_type', 'status']),
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['created_by', '-created_at']),
            models.Index(fields=['expires_at']),
        ]

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"

    def is_expired(self):
        """Prüft ob Report abgelaufen ist"""
        if not self.expires_at:
            return False
        return timezone.now() > self.expires_at

    def get_file_size_display(self):
        """Formatierte Dateigröße"""
        if not self.file_size:
            return ''

        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"

    def increment_download_count(self):
        """Erhöht Download-Zähler"""
        self.download_count += 1
        self.last_downloaded_at = timezone.now()
        self.save(update_fields=['download_count', 'last_downloaded_at'])

    def mark_as_generating(self):
        """Markiert Report als in Generierung"""
        self.status = ReportStatus.GENERATING
        self.generation_started_at = timezone.now()
        self.save(update_fields=['status', 'generation_started_at'])

    def mark_as_completed(self):
        """Markiert Report als abgeschlossen"""
        self.status = ReportStatus.COMPLETED
        self.generation_completed_at = timezone.now()
        if self.generation_started_at:
            duration = (self.generation_completed_at - self.generation_started_at).total_seconds()
            self.generation_duration = int(duration)
        if self.file:
            self.file_size = self.file.size
        self.save(update_fields=['status', 'generation_completed_at', 'generation_duration', 'file_size'])

    def mark_as_failed(self, error_message):
        """Markiert Report als fehlgeschlagen"""
        self.status = ReportStatus.FAILED
        self.error_message = error_message
        self.generation_completed_at = timezone.now()
        self.save(update_fields=['status', 'error_message', 'generation_completed_at'])


# =============================================================================
# SCHEDULED REPORTS
# =============================================================================

class ReportSchedule(AuditedModel):
    """
    Zeitgesteuerte Report-Generierung

    Ermöglicht automatische Report-Generierung via Celery Beat
    """

    template = models.ForeignKey(
        ReportTemplate,
        on_delete=models.CASCADE,
        related_name='schedules',
        verbose_name=_('Template')
    )

    name = models.CharField(
        _('Name'),
        max_length=200
    )

    description = models.TextField(
        _('Beschreibung'),
        blank=True
    )

    # Zeitplan
    frequency = models.CharField(
        _('Frequenz'),
        max_length=20,
        choices=ScheduleFrequency.choices,
        default=ScheduleFrequency.MONTHLY
    )

    # Cron-Expression für CUSTOM-Frequenz
    cron_expression = models.CharField(
        _('Cron-Ausdruck'),
        max_length=100,
        blank=True,
        help_text=_('Nur für benutzerdefinierte Frequenz')
    )

    # Zeitpunkt
    run_at_time = models.TimeField(
        _('Ausführungszeit'),
        null=True,
        blank=True,
        help_text=_('Uhrzeit für tägliche/wöchentliche Reports')
    )

    # Wochentag (1=Montag, 7=Sonntag)
    day_of_week = models.PositiveSmallIntegerField(
        _('Wochentag'),
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(7)],
        help_text=_('Für wöchentliche Reports')
    )

    # Tag des Monats
    day_of_month = models.PositiveSmallIntegerField(
        _('Tag des Monats'),
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(31)],
        help_text=_('Für monatliche Reports')
    )

    # Parameter
    parameters = models.JSONField(
        _('Parameter'),
        default=dict,
        blank=True
    )

    # Export-Format
    file_format = models.CharField(
        _('Export-Format'),
        max_length=10,
        choices=ReportFormat.choices,
        default=ReportFormat.PDF
    )

    # Empfänger
    recipients = models.ManyToManyField(
        User,
        related_name='scheduled_reports',
        verbose_name=_('Empfänger'),
        help_text=_('Benutzer, die Report per E-Mail erhalten')
    )

    send_email = models.BooleanField(
        _('Per E-Mail senden'),
        default=True
    )

    # Ablauf
    retention_days = models.PositiveIntegerField(
        _('Aufbewahrung (Tage)'),
        default=30,
        help_text=_('Reports werden nach X Tagen gelöscht')
    )

    # Status
    is_active = models.BooleanField(
        _('Aktiv'),
        default=True
    )

    last_run_at = models.DateTimeField(
        _('Zuletzt ausgeführt'),
        null=True,
        blank=True
    )

    next_run_at = models.DateTimeField(
        _('Nächste Ausführung'),
        null=True,
        blank=True
    )

    run_count = models.PositiveIntegerField(
        _('Ausführungen'),
        default=0
    )

    class Meta:
        verbose_name = _('Report-Zeitplan')
        verbose_name_plural = _('Report-Zeitpläne')
        ordering = ['name']
        indexes = [
            models.Index(fields=['template', 'is_active']),
            models.Index(fields=['is_active', 'next_run_at']),
            models.Index(fields=['frequency']),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_frequency_display()})"


# =============================================================================
# KPIs (Key Performance Indicators)
# =============================================================================

class KPI(AuditedModel):
    """
    Key Performance Indicators

    Definiert KPIs die auf Dashboards angezeigt werden
    """

    name = models.CharField(
        _('Name'),
        max_length=200
    )

    description = models.TextField(
        _('Beschreibung'),
        blank=True
    )

    category = models.CharField(
        _('Kategorie'),
        max_length=20,
        choices=KPICategory.choices
    )

    kpi_type = models.CharField(
        _('KPI-Typ'),
        max_length=20,
        choices=KPIType.choices
    )

    # Query für KPI-Berechnung
    query = models.TextField(
        _('Query / Code'),
        help_text=_('SQL-Query oder Python-Code für KPI-Berechnung')
    )

    # Zielwert
    target_value = models.DecimalField(
        _('Zielwert'),
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )

    # Schwellwerte für Ampel-System
    threshold_good = models.DecimalField(
        _('Schwellwert Gut'),
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_('Grüne Ampel ab diesem Wert')
    )

    threshold_warning = models.DecimalField(
        _('Schwellwert Warnung'),
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_('Gelbe Ampel ab diesem Wert')
    )

    # Einheit
    unit = models.CharField(
        _('Einheit'),
        max_length=20,
        blank=True,
        help_text=_('z.B. €, %, Stück')
    )

    # Display-Optionen
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

    # Aktualisierung
    refresh_interval = models.PositiveIntegerField(
        _('Aktualisierungsintervall (Minuten)'),
        default=60,
        help_text=_('Wie oft KPI neu berechnet wird')
    )

    last_calculated_at = models.DateTimeField(
        _('Zuletzt berechnet'),
        null=True,
        blank=True
    )

    last_value = models.DecimalField(
        _('Letzter Wert'),
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )

    # Sortierung & Anzeige
    display_order = models.PositiveIntegerField(
        _('Anzeigereihenfolge'),
        default=0
    )

    is_active = models.BooleanField(
        _('Aktiv'),
        default=True
    )

    class Meta:
        verbose_name = _('KPI')
        verbose_name_plural = _('KPIs')
        ordering = ['category', 'display_order', 'name']
        indexes = [
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['kpi_type']),
            models.Index(fields=['is_active', 'display_order']),
        ]

    def __str__(self):
        return self.name

    def get_status_color(self):
        """Gibt Ampel-Farbe basierend auf letztem Wert zurück"""
        if not self.last_value or not self.threshold_good or not self.threshold_warning:
            return 'gray'

        if self.last_value >= self.threshold_good:
            return 'green'
        elif self.last_value >= self.threshold_warning:
            return 'yellow'
        else:
            return 'red'
