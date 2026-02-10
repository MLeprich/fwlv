"""
Vehicles Models
Fahrzeugverwaltung mit Prüfungen, Dokumenten und Mobile Lager-Funktion
"""

from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator
from django.utils import timezone

from core.models.base import AuditedModel
from inventory_base.models import Supplier


# VehicleManufacturer wurde entfernt - verwende jetzt Supplier aus inventory_base


class VehicleModel(models.Model):
    """
    Fahrzeugmodell
    """
    manufacturer = models.ForeignKey(
        Supplier,
        on_delete=models.CASCADE,
        related_name='vehicle_models',
        verbose_name=_('Hersteller'),
        limit_choices_to={'is_active': True}
    )

    name = models.CharField(
        max_length=100,
        verbose_name=_('Modellname')
    )

    vehicle_type = models.ForeignKey(
        'VehicleType',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='vehicle_models',
        verbose_name=_('Standardtyp'),
        help_text=_('Standard-Fahrzeugtyp für dieses Modell'),
        limit_choices_to={'is_active': True}
    )

    year_from = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Baujahr von'),
        help_text=_('Erster Produktionsjahr')
    )

    year_to = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Baujahr bis'),
        help_text=_('Letztes Produktionsjahr (leer = aktuell)')
    )

    notes = models.TextField(
        blank=True,
        verbose_name=_('Notizen')
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Aktiv')
    )

    class Meta:
        verbose_name = _('Fahrzeugmodell')
        verbose_name_plural = _('Fahrzeugmodelle')
        ordering = ['manufacturer__name', 'name']
        unique_together = [['manufacturer', 'name']]

    def __str__(self):
        return f"{self.manufacturer.name} {self.name}"


class LegacyVehicleType(models.TextChoices):
    """Fahrzeugtypen (Legacy - nur für Migration)"""
    FIRE_TRUCK = 'fire_truck', _('Löschfahrzeug')
    COMMAND_VEHICLE = 'command', _('Kommandowagen')
    AMBULANCE = 'ambulance', _('Rettungswagen')
    LADDER_TRUCK = 'ladder', _('Drehleiter')
    SPECIAL_VEHICLE = 'special', _('Sonderfahrzeug')
    TRAILER = 'trailer', _('Anhänger')
    BOAT = 'boat', _('Boot')
    UTILITY_VEHICLE = 'utility', _('Mannschaftstransporter')
    OTHER = 'other', _('Sonstiges')


class VehicleType(models.Model):
    """Fahrzeugtyp - vom Benutzer verwaltbar"""
    name = models.CharField(max_length=100, unique=True, verbose_name=_('Bezeichnung'))
    code = models.SlugField(max_length=30, unique=True, verbose_name=_('Code'),
                            help_text=_('Interner Code (z.B. hlf20, dlk)'))
    description = models.TextField(blank=True, verbose_name=_('Beschreibung'))
    icon = models.CharField(max_length=10, blank=True, default='🚒', verbose_name=_('Icon'))
    order = models.PositiveIntegerField(default=0, verbose_name=_('Reihenfolge'))
    is_active = models.BooleanField(default=True, verbose_name=_('Aktiv'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'name']
        verbose_name = _('Fahrzeugtyp')
        verbose_name_plural = _('Fahrzeugtypen')

    def __str__(self):
        return self.name


class VehicleStatus(models.TextChoices):
    """Fahrzeugstatus"""
    OPERATIONAL = 'operational', _('Einsatzbereit')
    IN_USE = 'in_use', _('Im Einsatz')
    MAINTENANCE = 'maintenance', _('In Wartung')
    REPAIR = 'repair', _('In Reparatur')
    OUT_OF_SERVICE = 'out_of_service', _('Außer Dienst')
    RESERVED = 'reserved', _('Reserviert')


class Vehicle(AuditedModel):
    """
    Fahrzeug-Stammdaten
    Kann als Mobile Location fungieren (für Fahrzeug-gebundenes Inventar)
    """

    # Basis-Informationen
    name = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Fahrzeugname'),
        help_text=_('z.B. LF 10/6, RTW 1')
    )

    vehicle_type = models.ForeignKey(
        VehicleType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='vehicles',
        verbose_name=_('Fahrzeugtyp'),
        limit_choices_to={'is_active': True}
    )

    call_sign = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        verbose_name=_('Funkrufname'),
        help_text=_('z.B. Florian Musterstadt 10/1')
    )

    # Kennzeichen
    license_plate = models.CharField(
        max_length=20,
        unique=True,
        verbose_name=_('Kennzeichen'),
        validators=[
            RegexValidator(
                regex=r'^[A-ZÄÖÜ]{1,3}-[A-Z]{1,2}\s?\d{1,4}[EH]?$',
                message=_('Ungültiges deutsches Kennzeichen-Format'),
            )
        ]
    )

    # Fahrzeugdaten
    manufacturer = models.ForeignKey(
        Supplier,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='vehicles',
        verbose_name=_('Hersteller'),
        limit_choices_to={'is_active': True}
    )

    model = models.ForeignKey(
        VehicleModel,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='vehicles',
        verbose_name=_('Modell')
    )

    year_of_manufacture = models.PositiveIntegerField(
        null=True, blank=True,
        verbose_name=_('Baujahr')
    )

    vin = models.CharField(
        max_length=17,
        blank=True,
        verbose_name=_('Fahrzeug-Identifikationsnummer (FIN/VIN)'),
        help_text=_('17-stellige FIN')
    )

    # Motor & Kraftstoff
    engine_number = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_('Motornummer')
    )

    fuel_type = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_('Kraftstoffart'),
        help_text=_('z.B. Diesel, Benzin, Elektro')
    )

    # Kilometerstand & Betriebsstunden
    current_mileage = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Aktueller Kilometerstand')
    )

    engine_hours = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Betriebsstunden')
    )

    # Status
    status = models.CharField(
        max_length=20,
        choices=VehicleStatus.choices,
        default=VehicleStatus.OPERATIONAL,
        verbose_name=_('Status')
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Aktiv'),
        help_text=_('Ist das Fahrzeug im aktiven Bestand?')
    )

    # Standort
    home_location = models.ForeignKey(
        'locations.Location',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='stationed_vehicles',
        verbose_name=_('Heimatstandort'),
        help_text=_('Feste Wache/Gerätehaus')
    )

    # Mobile Lager
    is_mobile_storage = models.BooleanField(
        default=False,
        verbose_name=_('Als Mobiles Lager nutzen'),
        help_text=_('Fahrzeug kann Inventar-Items zugeordnet bekommen')
    )

    mobile_storage_location = models.OneToOneField(
        'locations.Location',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='mobile_vehicle',
        verbose_name=_('Mobile Location'),
        help_text=_('Automatisch erstellte Location für Fahrzeug-Inventar')
    )

    # Prüfungen & Dokumente
    next_inspection_date = models.DateField(
        null=True, blank=True,
        verbose_name=_('Nächste Hauptuntersuchung (HU)')
    )

    next_safety_check_date = models.DateField(
        null=True, blank=True,
        verbose_name=_('Nächste Sicherheitsprüfung (UVV)')
    )

    insurance_policy_number = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Versicherungspolice')
    )

    insurance_expires = models.DateField(
        null=True, blank=True,
        verbose_name=_('Versicherung gültig bis')
    )

    # Zuständigkeit
    responsible_person = models.ForeignKey(
        'personnel.Person',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='responsible_vehicles',
        verbose_name=_('Verantwortliche Person'),
        help_text=_('Fahrzeugwart/Gerätewart')
    )

    # Fotos & Dokumente
    photo = models.ImageField(
        upload_to='vehicles/photos/',
        null=True, blank=True,
        verbose_name=_('Fahrzeugfoto')
    )

    vehicle_documents = models.FileField(
        upload_to='vehicles/documents/',
        null=True, blank=True,
        verbose_name=_('Fahrzeugdokumente'),
        help_text=_('Fahrzeugschein, Bedienungsanleitung, etc.')
    )

    # Notizen
    notes = models.TextField(blank=True, verbose_name=_('Notizen'))

    # Lifecycle Management
    commissioning_date = models.DateField(
        null=True, blank=True,
        verbose_name=_('Indienststellung'),
        help_text=_('Datum der Indienststellung')
    )

    planned_retirement_date = models.DateField(
        null=True, blank=True,
        verbose_name=_('Geplante Außerdienststellung'),
        help_text=_('Geplantes Datum der Außerdienststellung')
    )

    actual_retirement_date = models.DateField(
        null=True, blank=True,
        verbose_name=_('Tatsächliche Außerdienststellung'),
        help_text=_('Tatsächliches Datum der Außerdienststellung')
    )

    replacement_vehicle = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='replaced_vehicles',
        verbose_name=_('Nachfolgefahrzeug'),
        help_text=_('Fahrzeug das dieses ersetzt')
    )

    retirement_reason = models.TextField(
        blank=True,
        verbose_name=_('Grund der Außerdienststellung'),
        help_text=_('z.B. Alter, Wirtschaftlichkeit, Beschädigung')
    )

    class Meta:
        verbose_name = _('Fahrzeug')
        verbose_name_plural = _('Fahrzeuge')
        ordering = ['call_sign']
        indexes = [
            models.Index(fields=['call_sign']),
            models.Index(fields=['license_plate']),
            models.Index(fields=['status']),
            models.Index(fields=['is_active']),
            models.Index(fields=['next_inspection_date']),
        ]

    def __str__(self):
        return f"{self.call_sign} - {self.name}"

    def get_absolute_url(self):
        return reverse('vehicles:detail', kwargs={'pk': self.pk})

    def get_full_description(self):
        """Vollständige Beschreibung"""
        parts = [self.name]
        if self.manufacturer and self.model:
            parts.append(f"{self.manufacturer.name} {self.model.name}")
        elif self.manufacturer:
            parts.append(self.manufacturer.name)
        if self.year_of_manufacture:
            parts.append(f"({self.year_of_manufacture})")
        return ' - '.join(parts)

    def is_inspection_due(self, days=30):
        """Prüft ob HU bald fällig ist"""
        if not self.next_inspection_date:
            return False
        from datetime import timedelta
        return self.next_inspection_date <= timezone.now().date() + timedelta(days=days)

    def is_safety_check_due(self, days=30):
        """Prüft ob UVV bald fällig ist"""
        if not self.next_safety_check_date:
            return False
        from datetime import timedelta
        return self.next_safety_check_date <= timezone.now().date() + timedelta(days=days)

    def is_insurance_expiring(self, days=30):
        """Prüft ob Versicherung bald ausläuft"""
        if not self.insurance_expires:
            return False
        from datetime import timedelta
        return self.insurance_expires <= timezone.now().date() + timedelta(days=days)

    def get_recent_inspections(self, limit=5):
        """Letzte Prüfungen"""
        return self.inspections.all().order_by('-inspection_date')[:limit]

    def is_retirement_approaching(self, days=90):
        """Prüft ob Außerdienststellung bald ansteht"""
        if not self.planned_retirement_date:
            return False
        from datetime import timedelta
        return self.planned_retirement_date <= timezone.now().date() + timedelta(days=days)

    def is_retired(self):
        """Prüft ob Fahrzeug bereits außer Dienst ist"""
        return self.actual_retirement_date is not None

    def get_service_years(self):
        """Berechnet Dienstjahre"""
        if not self.commissioning_date:
            return None
        end_date = self.actual_retirement_date or timezone.now().date()
        delta = end_date - self.commissioning_date
        return round(delta.days / 365.25, 1)


class InspectionType(models.TextChoices):
    """Prüfungstypen"""
    HU = 'hu', _('Hauptuntersuchung (HU)')
    UVV = 'uvv', _('Unfallverhütungsvorschrift (UVV)')
    MAINTENANCE = 'maintenance', _('Wartung')
    REPAIR = 'repair', _('Reparatur')
    DAMAGE = 'damage', _('Schadenserfassung')
    OTHER = 'other', _('Sonstiges')


class InspectionStatus(models.TextChoices):
    """Prüfungsstatus"""
    PASSED = 'passed', _('Bestanden')
    PASSED_WITH_DEFECTS = 'passed_defects', _('Bestanden mit Mängeln')
    FAILED = 'failed', _('Nicht bestanden')
    IN_PROGRESS = 'in_progress', _('In Bearbeitung')
    SCHEDULED = 'scheduled', _('Geplant')


class VehicleInspection(AuditedModel):
    """
    Fahrzeugprüfungen und Wartungshistorie
    """

    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.CASCADE,
        related_name='inspections',
        verbose_name=_('Fahrzeug')
    )

    inspection_type = models.CharField(
        max_length=20,
        choices=InspectionType.choices,
        verbose_name=_('Prüfungstyp')
    )

    inspection_date = models.DateField(
        verbose_name=_('Prüfungsdatum')
    )

    next_inspection_date = models.DateField(
        null=True, blank=True,
        verbose_name=_('Nächste Prüfung fällig am')
    )

    status = models.CharField(
        max_length=20,
        choices=InspectionStatus.choices,
        default=InspectionStatus.IN_PROGRESS,
        verbose_name=_('Status')
    )

    inspector = models.ForeignKey(
        'personnel.Person',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='vehicle_inspections',
        verbose_name=_('Prüfer/Techniker')
    )

    organization = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Prüforganisation'),
        help_text=_('z.B. TÜV, DEKRA, Werkstatt')
    )

    mileage_at_inspection = models.PositiveIntegerField(
        null=True, blank=True,
        verbose_name=_('Kilometerstand bei Prüfung')
    )

    # Ergebnis
    findings = models.TextField(
        blank=True,
        verbose_name=_('Feststellungen/Mängel')
    )

    repairs_needed = models.TextField(
        blank=True,
        verbose_name=_('Erforderliche Reparaturen')
    )

    repairs_completed = models.BooleanField(
        default=False,
        verbose_name=_('Reparaturen durchgeführt')
    )

    # Kosten
    cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True, blank=True,
        verbose_name=_('Kosten (EUR)')
    )

    # Dokumente
    inspection_report = models.FileField(
        upload_to='vehicles/inspections/',
        null=True, blank=True,
        verbose_name=_('Prüfbericht')
    )

    notes = models.TextField(blank=True, verbose_name=_('Notizen'))

    class Meta:
        verbose_name = _('Fahrzeugprüfung')
        verbose_name_plural = _('Fahrzeugprüfungen')
        ordering = ['-inspection_date']
        indexes = [
            models.Index(fields=['vehicle', 'inspection_type']),
            models.Index(fields=['inspection_date']),
            models.Index(fields=['next_inspection_date']),
        ]

    def __str__(self):
        return f"{self.vehicle.call_sign} - {self.get_inspection_type_display()} ({self.inspection_date})"

    def is_passed(self):
        """Hat Prüfung bestanden?"""
        return self.status in [InspectionStatus.PASSED, InspectionStatus.PASSED_WITH_DEFECTS]


