"""
Disinfection Models
Datenmodelle für Desinfektions-Management
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from decimal import Decimal

from inventory_base.models import (
    AbstractInventoryItem,
    AbstractStockMovement,
)


# ============================================================================
# CHOICE CLASSES
# ============================================================================

class DisinfectionItemType(models.TextChoices):
    """Desinfektionsmittel-Typen"""
    # Flächendesinfektion
    SURFACE_SPRAY = 'surface_spray', _('Flächendesinfektionsspray')
    SURFACE_WIPES = 'surface_wipes', _('Desinfektionstücher')
    SURFACE_CONCENTRATE = 'surface_concentrate', _('Flächendesinfektions-Konzentrat')
    SURFACE_READY_TO_USE = 'surface_ready_to_use', _('Flächendesinfektion gebrauchsfertig')

    # Händedesinfektion
    HAND_DISINFECTION = 'hand_disinfection', _('Händedesinfektionsmittel')
    HAND_SANITIZER_GEL = 'hand_sanitizer_gel', _('Händedesinfektionsgel')
    HAND_SANITIZER_FOAM = 'hand_sanitizer_foam', _('Händedesinfektionsschaum')

    # Instrumentendesinfektion
    INSTRUMENT_DISINFECTION = 'instrument_disinfection', _('Instrumentendesinfektion')
    INSTRUMENT_CONCENTRATE = 'instrument_concentrate', _('Instrumentendesinfektions-Konzentrat')

    # Wäschedesinfektion
    LAUNDRY_DISINFECTION = 'laundry_disinfection', _('Wäschedesinfektionsmittel')

    # Spezialdesinfektion
    VEHICLE_DISINFECTION = 'vehicle_disinfection', _('Fahrzeugdesinfektion')
    ROOM_DISINFECTION = 'room_disinfection', _('Raumdesinfektion')
    NEBULIZER_SOLUTION = 'nebulizer_solution', _('Verneblerlösung')
    UV_DISINFECTION = 'uv_disinfection', _('UV-Desinfektion (Gerät)')
    OZONE_GENERATOR = 'ozone_generator', _('Ozongenerator (Gerät)')

    # Schutzausrüstung für Desinfektion
    PROTECTIVE_GLOVES = 'protective_gloves', _('Schutzhandschuhe')
    PROTECTIVE_SUIT = 'protective_suit', _('Schutzanzug')
    FACE_SHIELD = 'face_shield', _('Gesichtsschutz')
    RESPIRATOR = 'respirator', _('Atemschutzmaske')

    # Zubehör
    SPRAY_BOTTLE = 'spray_bottle', _('Sprühflasche')
    DISPENSER = 'dispenser', _('Spender')
    DOSING_PUMP = 'dosing_pump', _('Dosierpumpe')
    MEASURING_CUP = 'measuring_cup', _('Messbecher')

    # Sonstiges
    OTHER = 'other', _('Sonstiges')


class DisinfectionSpectrum(models.TextChoices):
    """Wirkungsspektrum"""
    BACTERICIDAL = 'bactericidal', _('Bakterizid')
    VIRUCIDAL = 'virucidal', _('Viruzid')
    LIMITED_VIRUCIDAL = 'limited_virucidal', _('Begrenzt viruzid')
    FUNGICIDAL = 'fungicidal', _('Fungizid')
    SPORICIDAL = 'sporicidal', _('Sporizid')
    TUBERCULOCIDAL = 'tuberculocidal', _('Tuberkulozid')
    FULL_SPECTRUM = 'full_spectrum', _('Vollspektrum (alle)')


class DisinfectionStatus(models.TextChoices):
    """Desinfektionsmittel-Status"""
    IN_STOCK = 'in_stock', _('Auf Lager')
    LOW_STOCK = 'low_stock', _('Niedriger Bestand')
    OUT_OF_STOCK = 'out_of_stock', _('Nicht vorrätig')
    ON_ORDER = 'on_order', _('Bestellt')
    EXPIRED = 'expired', _('Abgelaufen')
    QUARANTINE = 'quarantine', _('Quarantäne')


class ApplicationMethod(models.TextChoices):
    """Anwendungsmethode"""
    SPRAY = 'spray', _('Sprühen')
    WIPE = 'wipe', _('Wischen')
    IMMERSION = 'immersion', _('Tauchen/Einlegen')
    NEBULIZATION = 'nebulization', _('Vernebeln')
    UV_LIGHT = 'uv_light', _('UV-Licht')
    OZONE = 'ozone', _('Ozon')
    MANUAL = 'manual', _('Manuelle Anwendung')


# ============================================================================
# DISINFECTION ITEM MODEL
# ============================================================================

class DisinfectionItem(AbstractInventoryItem):
    """
    Desinfektionsmittel & -geräte
    Erweitert AbstractInventoryItem um desinfektionsspezifische Felder
    """

    # Typ & Status
    disinfection_type = models.CharField(
        max_length=50,
        choices=DisinfectionItemType.choices,
        verbose_name=_('Desinfektionsmittel-Typ')
    )

    disinfection_status = models.CharField(
        max_length=20,
        choices=DisinfectionStatus.choices,
        default=DisinfectionStatus.IN_STOCK,
        verbose_name=_('Status')
    )

    category = models.ForeignKey(
        'DisinfectionCategory',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='items',
        verbose_name=_('Kategorie')
    )

    # Wirkungsspektrum (Multi-Select via JSONField)
    spectrum = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_('Wirkungsspektrum'),
        help_text=_('Liste der Wirkungsspektren (z.B. ["bactericidal", "virucidal"])')
    )

    # Anwendung
    application_method = models.CharField(
        max_length=20,
        choices=ApplicationMethod.choices,
        blank=True,
        verbose_name=_('Anwendungsmethode')
    )

    contact_time_minutes = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Einwirkzeit (Minuten)'),
        help_text=_('Erforderliche Kontaktzeit für volle Wirkung')
    )

    dilution_ratio = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_('Verdünnungsverhältnis'),
        help_text=_('z.B. 1:100, 2%')
    )

    # Zulassung & Compliance
    registration_number = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Zulassungsnummer'),
        help_text=_('z.B. BAuA-Nummer, VAH-Listung')
    )

    vah_listed = models.BooleanField(
        default=False,
        verbose_name=_('VAH-gelistet'),
        help_text=_('Verbund für Angewandte Hygiene')
    )

    dghm_listed = models.BooleanField(
        default=False,
        verbose_name=_('DGHM-gelistet'),
        help_text=_('Deutsche Gesellschaft für Hygiene und Mikrobiologie')
    )

    rki_listed = models.BooleanField(
        default=False,
        verbose_name=_('RKI-gelistet'),
        help_text=_('Robert Koch-Institut')
    )

    # Gefahrstoff
    is_hazardous = models.BooleanField(
        default=False,
        verbose_name=_('Gefahrstoff')
    )

    hazard_symbols = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Gefahrensymbole'),
        help_text=_('GHS-Symbole: GHS02, GHS05, GHS07, etc.')
    )

    safety_data_sheet = models.FileField(
        upload_to='disinfection/sds/',
        null=True,
        blank=True,
        verbose_name=_('Sicherheitsdatenblatt')
    )

    # Lagerung
    storage_temperature_min = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        null=True,
        blank=True,
        verbose_name=_('Min. Lagertemperatur (°C)')
    )

    storage_temperature_max = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        null=True,
        blank=True,
        verbose_name=_('Max. Lagertemperatur (°C)')
    )

    protect_from_light = models.BooleanField(
        default=False,
        verbose_name=_('Vor Licht schützen')
    )

    shelf_life_months = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Haltbarkeit (Monate)'),
        help_text=_('Haltbarkeit ab Herstellungsdatum')
    )

    shelf_life_opened_months = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Haltbarkeit geöffnet (Monate)'),
        help_text=_('Haltbarkeit nach Anbruch')
    )

    # Fahrzeug-Zuordnung
    assigned_vehicles = models.ManyToManyField(
        'vehicles.Vehicle',
        related_name='disinfection_items',
        blank=True,
        verbose_name=_('Zugeordnete Fahrzeuge'),
        help_text=_('Fahrzeuge, in denen dieses Mittel vorhanden ist')
    )

    # Wirkstoff
    active_ingredient = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Wirkstoff'),
        help_text=_('z.B. Ethanol, Isopropanol, Natriumhypochlorit')
    )

    concentration = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_('Konzentration'),
        help_text=_('z.B. 70%, 0.5%')
    )

    # Anwendungsbereiche (JSONField für Flexibilität)
    application_areas = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_('Anwendungsbereiche'),
        help_text=_('z.B. ["Fahrzeuge", "Tragen", "Instrumente", "Hände"]')
    )

    class Meta:
        verbose_name = _('Desinfektionsmittel')
        verbose_name_plural = _('Desinfektionsmittel')
        ordering = ['disinfection_type', 'name']
        indexes = [
            models.Index(fields=['disinfection_type']),
            models.Index(fields=['disinfection_status']),
            models.Index(fields=['vah_listed']),
            models.Index(fields=['is_hazardous']),
            models.Index(fields=['registration_number']),
        ]

    def __str__(self):
        return f"{self.item_number} - {self.name} ({self.get_disinfection_type_display()})"

    def has_spectrum(self, spectrum_type):
        """Prüft ob ein bestimmtes Wirkungsspektrum vorhanden ist"""
        return spectrum_type in self.spectrum if self.spectrum else False

    def is_full_spectrum(self):
        """Prüft ob Vollspektrum-Desinfektion"""
        return 'full_spectrum' in self.spectrum if self.spectrum else False


# ============================================================================
# DISINFECTION STOCK MOVEMENT MODEL
# ============================================================================

class DisinfectionStockMovement(AbstractStockMovement):
    """
    Desinfektionsmittel-Lagerbewegung
    Erweitert AbstractStockMovement um desinfektionsspezifische Felder
    """

    item = models.ForeignKey(
        DisinfectionItem,
        on_delete=models.PROTECT,
        related_name='stock_movements',
        verbose_name=_('Desinfektionsmittel')
    )

    # Fahrzeug-/Standort-Bezug
    vehicle = models.ForeignKey(
        'vehicles.Vehicle',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='disinfection_movements',
        verbose_name=_('Fahrzeug'),
        help_text=_('Fahrzeug, dem das Mittel zugeordnet wurde')
    )

    # Chargen-Info
    batch_number = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Chargen-/Batch-Nummer')
    )

    production_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Produktionsdatum')
    )

    expiry_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Verfallsdatum')
    )

    opened_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Anbruchdatum'),
        help_text=_('Datum, an dem die Flasche/Packung geöffnet wurde')
    )

    # Verwendungsdokumentation
    used_for = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Verwendet für'),
        help_text=_('z.B. "Fahrzeug XY nach Einsatz", "Trage", "Instrumente"')
    )

    disinfection_protocol = models.TextField(
        blank=True,
        verbose_name=_('Desinfektionsprotokoll'),
        help_text=_('Beschreibung der durchgeführten Desinfektion')
    )

    performed_by = models.ForeignKey(
        'personnel.Person',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='performed_disinfections',
        verbose_name=_('Durchgeführt von')
    )

    # Kosten
    unit_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name=_('Stückkosten (EUR)')
    )

    total_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name=_('Gesamtkosten (EUR)')
    )

    # Dokumente
    delivery_note = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Lieferschein-Nr.')
    )

    class Meta:
        verbose_name = _('Desinfektionsmittel-Lagerbewegung')
        verbose_name_plural = _('Desinfektionsmittel-Lagerbewegungen')
        ordering = ['-movement_date', '-created_at']
        indexes = [
            models.Index(fields=['item', 'movement_date']),
            models.Index(fields=['vehicle', 'movement_date']),
            models.Index(fields=['batch_number']),
            models.Index(fields=['expiry_date']),
            models.Index(fields=['movement_type', 'movement_date']),
        ]

    def __str__(self):
        return f"{self.get_movement_type_display()} - {self.item.name} ({self.movement_date})"

    def save(self, *args, **kwargs):
        # Kosten berechnen
        if self.unit_cost and not self.total_cost:
            self.total_cost = self.unit_cost * self.quantity

        super().save(*args, **kwargs)

        # Bestand aktualisieren
        self.update_item_stock()


# ============================================================================
# DISINFECTION LOG MODEL
# ============================================================================

class DisinfectionLog(models.Model):
    """
    Desinfektions-Dokumentation
    Protokolliert durchgeführte Desinfektionen (unabhängig von Lagerbewegungen)
    """

    # Was wurde desinfiziert
    object_type = models.CharField(
        max_length=50,
        verbose_name=_('Objekt-Typ'),
        help_text=_('z.B. Fahrzeug, Trage, Raum, Instrumente')
    )

    vehicle = models.ForeignKey(
        'vehicles.Vehicle',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='disinfection_logs',
        verbose_name=_('Fahrzeug')
    )

    object_description = models.CharField(
        max_length=200,
        verbose_name=_('Objekt-Beschreibung'),
        help_text=_('Genauere Beschreibung des desinfizierten Objekts')
    )

    # Wann & Wer
    disinfection_date = models.DateTimeField(
        verbose_name=_('Desinfektionsdatum')
    )

    performed_by = models.ForeignKey(
        'personnel.Person',
        on_delete=models.PROTECT,
        related_name='disinfection_logs',
        verbose_name=_('Durchgeführt von')
    )

    verified_by = models.ForeignKey(
        'personnel.Person',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_disinfections',
        verbose_name=_('Kontrolliert von')
    )

    # Verwendete Mittel
    disinfection_item = models.ForeignKey(
        DisinfectionItem,
        on_delete=models.PROTECT,
        related_name='disinfection_logs',
        verbose_name=_('Verwendetes Desinfektionsmittel')
    )

    stock_movement = models.ForeignKey(
        DisinfectionStockMovement,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='disinfection_logs',
        verbose_name=_('Zugehörige Lagerbewegung')
    )

    disinfection_plan = models.ForeignKey(
        'DisinfectionPlan',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='disinfection_logs',
        verbose_name=_('Zugehöriger Desinfektionsplan'),
        help_text=_('Falls diese Desinfektion Teil eines Plans ist')
    )

    # Durchführung
    dilution_used = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_('Verwendete Verdünnung')
    )

    contact_time_minutes = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Einwirkzeit (Minuten)')
    )

    method = models.CharField(
        max_length=20,
        choices=ApplicationMethod.choices,
        verbose_name=_('Methode')
    )

    # Dokumentation
    protocol = models.TextField(
        verbose_name=_('Protokoll'),
        help_text=_('Detaillierte Beschreibung der Durchführung')
    )

    reason = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Grund/Anlass'),
        help_text=_('z.B. "Nach Infektionstransport", "Routinedesinfektion"')
    )

    photos = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_('Fotos'),
        help_text=_('Liste von Foto-URLs als Nachweis')
    )

    notes = models.TextField(
        blank=True,
        verbose_name=_('Notizen')
    )

    # Audit
    created_by = models.ForeignKey(
        'core.User',
        on_delete=models.PROTECT,
        related_name='created_disinfection_logs',
        verbose_name=_('Erstellt von')
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Erstellt am')
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Aktualisiert am')
    )

    class Meta:
        verbose_name = _('Desinfektions-Protokoll')
        verbose_name_plural = _('Desinfektions-Protokolle')
        ordering = ['-disinfection_date']
        indexes = [
            models.Index(fields=['vehicle', 'disinfection_date']),
            models.Index(fields=['object_type', 'disinfection_date']),
            models.Index(fields=['performed_by', 'disinfection_date']),
            models.Index(fields=['disinfection_item', 'disinfection_date']),
        ]

    def __str__(self):
        return f"{self.object_type} - {self.object_description} ({self.disinfection_date.strftime('%Y-%m-%d %H:%M')})"


# ============================================================================
# DISINFECTION CATEGORIES
# ============================================================================

class DisinfectionCategory(models.Model):
    """
    Kategorien für Desinfektionsmittel
    Für die Organisation und Gruppierung von Desinfektionsmitteln
    """

    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_('Kategorie-Name')
    )

    description = models.TextField(
        blank=True,
        verbose_name=_('Beschreibung')
    )

    icon = models.CharField(
        max_length=10,
        blank=True,
        verbose_name=_('Icon'),
        help_text=_('Emoji oder Icon-Symbol')
    )

    color = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_('Farbe'),
        help_text=_('Tailwind Color-Class (z.B. blue-500)')
    )

    sort_order = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Sortierreihenfolge')
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Aktiv')
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Desinfektions-Kategorie')
        verbose_name_plural = _('Desinfektions-Kategorien')
        ordering = ['sort_order', 'name']

    def __str__(self):
        return self.name


# ============================================================================
# DISINFECTION PLANS (Schedules)
# ============================================================================

class DisinfectionPlanFrequency(models.TextChoices):
    """Häufigkeit der Desinfektion"""
    DAILY = 'daily', _('Täglich')
    AFTER_EACH_USE = 'after_each_use', _('Nach jeder Benutzung')
    WEEKLY = 'weekly', _('Wöchentlich')
    BIWEEKLY = 'biweekly', _('Alle 2 Wochen')
    MONTHLY = 'monthly', _('Monatlich')
    QUARTERLY = 'quarterly', _('Vierteljährlich')
    BIANNUALLY = 'biannually', _('Halbjährlich')
    ANNUALLY = 'annually', _('Jährlich')
    CUSTOM = 'custom', _('Individuell')


class DisinfectionPlan(models.Model):
    """
    Desinfektionsplan für Fahrzeuge und andere Objekte
    Definiert wann und wie oft etwas desinfiziert werden muss
    """

    # Was soll desinfiziert werden
    name = models.CharField(
        max_length=200,
        verbose_name=_('Plan-Name'),
        help_text=_('z.B. "RTW 1 - Wöchentliche Desinfektion"')
    )

    vehicle = models.ForeignKey(
        'vehicles.Vehicle',
        on_delete=models.CASCADE,
        related_name='disinfection_plans',
        verbose_name=_('Fahrzeug'),
        null=True,
        blank=True
    )

    object_type = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_('Objekt-Typ'),
        help_text=_('Falls nicht Fahrzeug: z.B. Raum, Trage, etc.')
    )

    object_description = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Objekt-Beschreibung')
    )

    # Häufigkeit & Timing
    frequency = models.CharField(
        max_length=20,
        choices=DisinfectionPlanFrequency.choices,
        default=DisinfectionPlanFrequency.WEEKLY,
        verbose_name=_('Häufigkeit')
    )

    custom_interval_days = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Benutzerdefiniertes Intervall (Tage)'),
        help_text=_('Nur bei Häufigkeit "Individuell"')
    )

    start_date = models.DateField(
        verbose_name=_('Start-Datum'),
        help_text=_('Ab wann gilt dieser Plan')
    )

    end_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('End-Datum'),
        help_text=_('Optional: Bis wann gilt dieser Plan')
    )

    next_due_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Nächste fällige Desinfektion'),
        help_text=_('Automatisch berechnet basierend auf letzter Durchführung')
    )

    # Anweisungen
    description = models.TextField(
        blank=True,
        verbose_name=_('Beschreibung / Anweisungen'),
        help_text=_('Spezielle Hinweise oder Anweisungen für die Desinfektion')
    )

    required_items = models.ManyToManyField(
        DisinfectionItem,
        blank=True,
        related_name='required_for_plans',
        verbose_name=_('Benötigte Desinfektionsmittel')
    )

    contact_time_minutes = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Einwirkzeit (Minuten)')
    )

    # Verantwortlichkeiten
    responsible_person = models.ForeignKey(
        'personnel.Person',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='responsible_for_disinfection_plans',
        verbose_name=_('Verantwortliche Person')
    )

    responsible_department = models.ForeignKey(
        'organization.Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='disinfection_plans',
        verbose_name=_('Verantwortliche Abteilung')
    )

    # Status
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Aktiv')
    )

    # Erinnerungen
    reminder_days_before = models.PositiveIntegerField(
        default=3,
        verbose_name=_('Erinnerung (Tage vorher)'),
        help_text=_('Wie viele Tage vorher soll erinnert werden')
    )

    send_email_reminder = models.BooleanField(
        default=True,
        verbose_name=_('E-Mail-Erinnerung senden')
    )

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        'core.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_disinfection_plans',
        verbose_name=_('Erstellt von')
    )
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        'core.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='updated_disinfection_plans',
        verbose_name=_('Aktualisiert von')
    )

    class Meta:
        verbose_name = _('Desinfektionsplan')
        verbose_name_plural = _('Desinfektionspläne')
        ordering = ['next_due_date', 'name']
        indexes = [
            models.Index(fields=['vehicle', 'is_active']),
            models.Index(fields=['next_due_date', 'is_active']),
            models.Index(fields=['frequency']),
        ]

    def __str__(self):
        return self.name

    def calculate_next_due_date(self):
        """
        Berechnet das nächste Fälligkeitsdatum basierend auf Frequenz
        """
        from datetime import timedelta
        from django.utils import timezone

        # Letzten Log finden
        last_log = self.disinfection_logs.order_by('-disinfection_date').first()
        base_date = last_log.disinfection_date.date() if last_log else self.start_date

        frequency_map = {
            'daily': 1,
            'after_each_use': 1,  # Wird manuell getriggert
            'weekly': 7,
            'biweekly': 14,
            'monthly': 30,
            'quarterly': 90,
            'biannually': 180,
            'annually': 365,
        }

        if self.frequency == 'custom' and self.custom_interval_days:
            days = self.custom_interval_days
        else:
            days = frequency_map.get(self.frequency, 7)

        return base_date + timedelta(days=days)

    def is_overdue(self):
        """Prüft ob Desinfektion überfällig ist"""
        from django.utils import timezone
        if not self.next_due_date:
            return False
        return self.next_due_date < timezone.now().date()

    def is_due_soon(self):
        """Prüft ob Desinfektion bald fällig ist"""
        from datetime import timedelta
        from django.utils import timezone
        if not self.next_due_date:
            return False
        warning_date = timezone.now().date() + timedelta(days=self.reminder_days_before)
        return self.next_due_date <= warning_date
