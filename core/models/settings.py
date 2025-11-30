"""
User Settings Model
Speichert Benutzer-spezifische Einstellungen und Präferenzen
"""

from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class UserSettings(models.Model):
    """
    Benutzer-Einstellungen und Präferenzen
    """

    # Theme Choices
    THEME_LIGHT = 'light'
    THEME_DARK = 'dark'
    THEME_AUTO = 'auto'
    THEME_CHOICES = [
        (THEME_LIGHT, 'Hell'),
        (THEME_DARK, 'Dunkel'),
        (THEME_AUTO, 'Automatisch'),
    ]

    # Sidebar Choices
    SIDEBAR_EXPANDED = 'expanded'
    SIDEBAR_COLLAPSED = 'collapsed'
    SIDEBAR_AUTO = 'auto'
    SIDEBAR_CHOICES = [
        (SIDEBAR_EXPANDED, 'Standard ausgeklappt'),
        (SIDEBAR_COLLAPSED, 'Standard eingeklappt'),
        (SIDEBAR_AUTO, 'Automatisch'),
    ]

    # Table Density Choices
    DENSITY_COMPACT = 'compact'
    DENSITY_NORMAL = 'normal'
    DENSITY_COMFORTABLE = 'comfortable'
    DENSITY_CHOICES = [
        (DENSITY_COMPACT, 'Kompakt'),
        (DENSITY_NORMAL, 'Normal'),
        (DENSITY_COMFORTABLE, 'Komfortabel'),
    ]

    # Language Choices
    LANGUAGE_DE = 'de'
    LANGUAGE_EN = 'en'
    LANGUAGE_CHOICES = [
        (LANGUAGE_DE, 'Deutsch'),
        (LANGUAGE_EN, 'English'),
    ]

    # Relation
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='settings',
        verbose_name="Benutzer"
    )

    # Account Settings
    language = models.CharField(
        max_length=5,
        choices=LANGUAGE_CHOICES,
        default=LANGUAGE_DE,
        verbose_name="Sprache"
    )

    timezone = models.CharField(
        max_length=50,
        default='Europe/Berlin',
        verbose_name="Zeitzone"
    )

    # Notification Settings
    email_notifications = models.BooleanField(
        default=True,
        verbose_name="E-Mail-Benachrichtigungen"
    )

    email_critical_alerts = models.BooleanField(
        default=True,
        verbose_name="Kritische Alerts per E-Mail"
    )

    email_weekly_summary = models.BooleanField(
        default=False,
        verbose_name="Wöchentliche Zusammenfassung"
    )

    push_enabled = models.BooleanField(
        default=False,
        verbose_name="Push-Benachrichtigungen"
    )

    # Notification Categories
    notify_critical_stock = models.BooleanField(
        default=True,
        verbose_name="Kritische Bestände"
    )

    notify_expiring_items = models.BooleanField(
        default=True,
        verbose_name="Ablaufende Artikel"
    )

    notify_upcoming_inspections = models.BooleanField(
        default=True,
        verbose_name="Anstehende Prüfungen"
    )

    notify_orders = models.BooleanField(
        default=False,
        verbose_name="Bestellungen"
    )

    notify_vehicle_handover = models.BooleanField(
        default=False,
        verbose_name="Fahrzeugübernahme"
    )

    # Appearance Settings
    theme = models.CharField(
        max_length=10,
        choices=THEME_CHOICES,
        default=THEME_LIGHT,
        verbose_name="Theme"
    )

    sidebar_behavior = models.CharField(
        max_length=10,
        choices=SIDEBAR_CHOICES,
        default=SIDEBAR_EXPANDED,
        verbose_name="Sidebar-Verhalten"
    )

    items_per_page = models.IntegerField(
        default=25,
        choices=[(10, '10'), (25, '25'), (50, '50'), (100, '100')],
        verbose_name="Einträge pro Seite"
    )

    table_density = models.CharField(
        max_length=12,
        choices=DENSITY_CHOICES,
        default=DENSITY_NORMAL,
        verbose_name="Tabellen-Dichte"
    )

    show_hints = models.BooleanField(
        default=True,
        verbose_name="Hilfe-Tooltips anzeigen"
    )

    show_breadcrumbs = models.BooleanField(
        default=True,
        verbose_name="Breadcrumb-Navigation anzeigen"
    )

    compact_mode = models.BooleanField(
        default=False,
        verbose_name="Kompakt-Modus"
    )

    # Privacy Settings
    analytics_enabled = models.BooleanField(
        default=True,
        verbose_name="Nutzungsstatistiken"
    )

    error_reporting = models.BooleanField(
        default=True,
        verbose_name="Anonyme Fehlerberichte"
    )

    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Erstellt am"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Aktualisiert am"
    )

    class Meta:
        verbose_name = "Benutzer-Einstellungen"
        verbose_name_plural = "Benutzer-Einstellungen"

    def __str__(self):
        return f"Einstellungen für {self.user.get_full_name()}"

    @classmethod
    def get_or_create_for_user(cls, user):
        """
        Holt oder erstellt Einstellungen für einen Benutzer
        """
        settings, created = cls.objects.get_or_create(user=user)
        return settings
