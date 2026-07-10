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

    vehicle_handover_enabled = models.BooleanField(
        default=True,
        verbose_name="Fahrzeugübernahme",
        help_text="Fahrzeugübernahme-Protokolle bei Schichtwechsel"
    )

    driving_license_enabled = models.BooleanField(
        default=True,
        verbose_name="Führerscheinüberprüfung",
        help_text="Führerscheinüberprüfung und -verwaltung"
    )

    height_rescue_enabled = models.BooleanField(
        default=True,
        verbose_name="Höhenrettung",
        help_text="Höhenrettungsausrüstung (PSA) Verwaltung"
    )

    diving_enabled = models.BooleanField(
        default=True,
        verbose_name="Taucher",
        help_text="Tauchausrüstung Verwaltung"
    )

    workshop_enabled = models.BooleanField(
        default=True,
        verbose_name="KFZ-Werkstatt",
        help_text="KFZ-Werkstatt und Werkzeugverwaltung"
    )

    phonebook_enabled = models.BooleanField(
        default=True,
        verbose_name="Telefonbuch",
        help_text="Internes Telefonbuch mit Kontaktdaten"
    )

    defect_management_enabled = models.BooleanField(
        default=True,
        verbose_name="Mängelwesen",
        help_text="Mängelerfassung und -verwaltung für Räume, Fahrzeuge und Ausrüstung"
    )

    civil_protection_enabled = models.BooleanField(
        default=False,
        verbose_name="Bevölkerungsschutz",
        help_text="Bevölkerungsschutz-Modul (Bund, Land & Kommune)"
    )

    objektverwaltung_enabled = models.BooleanField(
        default=True,
        verbose_name="Objektverwaltung",
        help_text="Verwaltung öffentlicher Gebäude (Etagen, Fluchtwege, Laufkarten)"
    )

    accident_report_enabled = models.BooleanField(
        default=True,
        verbose_name="Unfallberichte",
        help_text="Erfassung und Verwaltung von Unfall-/Verletzungsmeldungen im Dienst"
    )

    # ============================================================================
    # PERSONAL - TAB VISIBILITY
    # ============================================================================

    person_tab_duty_hours_visible = models.BooleanField(
        default=True,
        verbose_name="Pflichtstunden-Tab",
        help_text="Pflichtstunden-Tab auf der Personaldetailseite anzeigen"
    )

    person_tab_qualifications_visible = models.BooleanField(
        default=True,
        verbose_name="Qualifikationen-Tab",
        help_text="Qualifikationen-Tab auf der Personaldetailseite anzeigen"
    )

    person_tab_inspections_visible = models.BooleanField(
        default=True,
        verbose_name="Prüfungen-Tab",
        help_text="Prüfungen-Tab auf der Personaldetailseite anzeigen"
    )

    person_tab_clothing_visible = models.BooleanField(
        default=True,
        verbose_name="Kleidung & PSA-Tab",
        help_text="Kleidung & PSA-Tab auf der Personaldetailseite anzeigen"
    )

    # ============================================================================
    # SECURITY
    # ============================================================================

    two_factor_auth_enabled = models.BooleanField(
        default=False,
        verbose_name="Zwei-Faktor-Authentifizierung",
        help_text="2FA systemweit aktivieren (erfordert zusätzliche Konfiguration)"
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
    # DSGVO - SETTINGS TAB VISIBILITY
    # ============================================================================

    privacy_tab_visible = models.BooleanField(
        default=False,
        verbose_name="Datenschutz-Tab",
        help_text="Datenschutz-Tab in den Benutzer-Einstellungen anzeigen"
    )

    # ============================================================================
    # DSGVO - PERSON FORM SECTION VISIBILITY
    # ============================================================================

    person_section_work_contact_visible = models.BooleanField(
        default=True,
        verbose_name="Dienstliche Kontaktdaten",
        help_text="Standort, Raum, dienstliche Telefonnummern im Personalformular anzeigen"
    )

    person_section_private_contact_visible = models.BooleanField(
        default=True,
        verbose_name="Private Kontaktdaten",
        help_text="E-Mail, Telefon, Adresse im Personalformular anzeigen"
    )

    person_section_emergency_contact_visible = models.BooleanField(
        default=True,
        verbose_name="Notfallkontakt",
        help_text="Notfallkontakt-Bereich im Personalformular anzeigen"
    )

    person_section_organization_visible = models.BooleanField(
        default=True,
        verbose_name="Organisationszugehörigkeit",
        help_text="JF, FF, BF-Zugehörigkeit im Personalformular anzeigen"
    )

    person_section_user_photo_visible = models.BooleanField(
        default=True,
        verbose_name="Benutzer & Foto",
        help_text="Benutzer-Account und Profilfoto im Personalformular anzeigen"
    )

    person_section_driving_license_visible = models.BooleanField(
        default=True,
        verbose_name="Führerscheindaten",
        help_text="Führerscheinklassen im Personalformular anzeigen"
    )

    person_section_fire_department_visible = models.BooleanField(
        default=True,
        verbose_name="Feuerwehr-Daten",
        help_text="Feuerwehr-Daten (Abteilung, Dienstgrad, Funktion) im Personalformular anzeigen"
    )

    person_section_notes_visible = models.BooleanField(
        default=True,
        verbose_name="Notizen",
        help_text="Interne Anmerkungen im Personalformular anzeigen"
    )

    # ============================================================================
    # SYSTEM INFORMATION
    # ============================================================================

    organization_name = models.CharField(
        max_length=200,
        default="Feuerwehr",
        verbose_name="Organisationsname"
    )

    site_title = models.CharField(
        max_length=200,
        default="Feuerwehr Lagerverwaltungssystem",
        verbose_name="Titel auf der Startseite",
        help_text="Wird auf der öffentlichen Startseite als Überschrift angezeigt "
                  "(z.B. 'Feuerwehr Oberhausen Lagerverwaltung')."
    )

    organization_logo = models.ImageField(
        upload_to='system/logos/',
        null=True,
        blank=True,
        verbose_name="Organisations-Logo",
        help_text="Wird auf der Startseite angezeigt (empfohlen: PNG mit transparentem Hintergrund)."
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
        if self.vehicle_handover_enabled:
            modules.append('vehicle_handover')
        if self.driving_license_enabled:
            modules.append('driving_license')
        if self.height_rescue_enabled:
            modules.append('height_rescue')
        if self.diving_enabled:
            modules.append('diving')
        if self.workshop_enabled:
            modules.append('workshop')
        if self.phonebook_enabled:
            modules.append('phonebook')
        if self.defect_management_enabled:
            modules.append('defect_management')
        if self.civil_protection_enabled:
            modules.append('civil_protection')
        if self.objektverwaltung_enabled:
            modules.append('objektverwaltung')
        if self.accident_report_enabled:
            modules.append('accident_report')
        return modules
