"""
System Settings Model
System-weite Einstellungen für Module und Features
Singleton-Pattern: Es gibt nur eine Instanz mit ID=1
"""

from django.db import models
from django.core.cache import cache
from django.utils.translation import gettext_lazy as _


class SystemSettings(models.Model):
    """
    System-weite Einstellungen
    Singleton: Nur eine Instanz mit ID=1
    """

    # ============================================================================
    # MODULE ACTIVATION
    # ============================================================================

    # Information & Wissen
    wiki_enabled = models.BooleanField(
        default=False,
        verbose_name="Wiki-Modul",
        help_text="Interne Wissensdatenbank aktivieren"
    )

    # Weitere Module (für zukünftige Erweiterungen)
    procurement_enabled = models.BooleanField(
        default=True,
        verbose_name="Bestellwesen",
        help_text="Beschaffungs- und Bestellverwaltung"
    )

    inventory_check_enabled = models.BooleanField(
        default=True,
        verbose_name="Inventur",
        help_text="Inventur-Modul"
    )

    info_monitors_enabled = models.BooleanField(
        default=False,
        verbose_name="Info-Monitore",
        help_text="Dashboard-Builder für öffentliche Monitore"
    )

    it_hardware_enabled = models.BooleanField(
        default=True,
        verbose_name="IT-Hardware",
        help_text="IT-Hardware Verwaltung"
    )

    tickets_enabled = models.BooleanField(
        default=True,
        verbose_name="Ticketsystem",
        help_text="Internes Ticketsystem für Anfragen und Meldungen"
    )

    ff_dashboard_enabled = models.BooleanField(
        default=True,
        verbose_name="FF-Dashboard",
        help_text="Feuerwehr-Verwaltung (Dienstgrade, Jubiläen, Beförderungen)"
    )

    # ============================================================================
    # FEATURE FLAGS
    # ============================================================================

    barcode_scanning_enabled = models.BooleanField(
        default=True,
        verbose_name="Barcode-Scanner",
        help_text="Barcode/QR-Code Scanning aktivieren"
    )

    mobile_app_enabled = models.BooleanField(
        default=False,
        verbose_name="Mobile App",
        help_text="Mobile App Zugriff aktivieren"
    )

    api_enabled = models.BooleanField(
        default=False,
        verbose_name="REST API",
        help_text="REST API für externe Integrationen"
    )

    # ============================================================================
    # SYSTEM INFORMATION
    # ============================================================================

    organization_name = models.CharField(
        max_length=200,
        default="Feuerwehr",
        verbose_name="Organisationsname"
    )

    organization_logo = models.ImageField(
        upload_to='system/logos/',
        null=True,
        blank=True,
        verbose_name="Organisations-Logo"
    )

    system_email = models.EmailField(
        blank=True,
        verbose_name="System-E-Mail",
        help_text="E-Mail-Adresse für System-Benachrichtigungen"
    )

    # ============================================================================
    # TIMESTAMPS
    # ============================================================================

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Aktualisiert am"
    )

    updated_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='+',
        verbose_name="Aktualisiert von"
    )

    class Meta:
        verbose_name = "System-Einstellungen"
        verbose_name_plural = "System-Einstellungen"

    def __str__(self):
        return f"System-Einstellungen ({self.organization_name})"

    def save(self, *args, **kwargs):
        # Enforce Singleton: Immer ID=1
        self.pk = 1
        super().save(*args, **kwargs)
        # Cache invalidieren
        cache.delete('system_settings')

    @classmethod
    def load(cls):
        """
        Lädt die System-Einstellungen (Singleton)
        Cached für Performance
        """
        settings = cache.get('system_settings')
        if settings is None:
            settings, created = cls.objects.get_or_create(pk=1)
            cache.set('system_settings', settings, 60 * 15)  # 15 Minuten Cache
        return settings

    @classmethod
    def clear_cache(cls):
        """Cache manuell leeren"""
        cache.delete('system_settings')

    def get_enabled_modules(self):
        """
        Gibt eine Liste aller aktivierten Module zurück
        """
        modules = []
        if self.wiki_enabled:
            modules.append('wiki')
        if self.procurement_enabled:
            modules.append('procurement')
        if self.inventory_check_enabled:
            modules.append('inventory_check')
        if self.info_monitors_enabled:
            modules.append('info_monitors')
        if self.it_hardware_enabled:
            modules.append('it_hardware')
        if self.tickets_enabled:
            modules.append('tickets')
        if self.ff_dashboard_enabled:
            modules.append('ff_dashboard')
        return modules
