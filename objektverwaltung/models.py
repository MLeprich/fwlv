"""
Objektverwaltung - Modelle

Verwaltung öffentlicher Gebäude/Objekte mit Brandschutz-relevanten
Informationen (Etagen, Fluchtwege, Brandmeldezentralen), Laufkarten/Plänen
und Ansprechpartnern. Nutzer können einzelne Objekte abonnieren ("folgen")
und werden bei Änderungen über das interne Notification-System informiert.
"""

from django.conf import settings
from django.db import models
from django.urls import reverse

from core.models.base import FullAuditModel, AuditedModel, TimeStampedModel


class UsageType(models.TextChoices):
    """Nutzungsart des Objekts"""
    SCHOOL = 'school', 'Schule'
    KINDERGARTEN = 'kindergarten', 'Kindergarten / Kita'
    HOSPITAL = 'hospital', 'Krankenhaus / Pflege'
    ASSEMBLY = 'assembly', 'Versammlungsstätte'
    OFFICE = 'office', 'Verwaltung / Büro'
    INDUSTRY = 'industry', 'Industrie / Gewerbe'
    RESIDENTIAL = 'residential', 'Wohngebäude'
    OTHER = 'other', 'Sonstiges'


class BuildingObject(FullAuditModel):
    """
    Ein öffentliches Gebäude / Objekt mit allgemeinen
    Gebäude- und Brandschutzinformationen.
    """

    # Identifikation
    object_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Objektnummer",
        help_text="Eindeutige Kennung des Objekts"
    )
    name = models.CharField(
        max_length=200,
        verbose_name="Bezeichnung",
        help_text="Name des Objekts (z.B. 'Grundschule Musterstadt')"
    )
    usage_type = models.CharField(
        max_length=20,
        choices=UsageType.choices,
        default=UsageType.OTHER,
        verbose_name="Nutzungsart"
    )

    # Adresse
    street = models.CharField(max_length=200, blank=True, verbose_name="Straße")
    house_number = models.CharField(max_length=20, blank=True, verbose_name="Hausnummer")
    postal_code = models.CharField(max_length=10, blank=True, verbose_name="PLZ")
    city = models.CharField(max_length=100, blank=True, verbose_name="Ort")

    # Geokoordinaten (optional, ohne Kartendarstellung gespeichert)
    latitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True,
        verbose_name="Breitengrad",
        help_text="Geografische Breite (optional)"
    )
    longitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True,
        verbose_name="Längengrad",
        help_text="Geografische Länge (optional)"
    )

    # Gebäudeinformationen
    floor_count = models.PositiveSmallIntegerField(
        null=True, blank=True,
        verbose_name="Anzahl Obergeschosse"
    )
    basement_count = models.PositiveSmallIntegerField(
        null=True, blank=True,
        verbose_name="Anzahl Untergeschosse"
    )
    has_fire_alarm_system = models.BooleanField(
        default=False,
        verbose_name="Brandmeldeanlage vorhanden"
    )

    notes = models.TextField(blank=True, verbose_name="Allgemeine Hinweise")

    is_active = models.BooleanField(default=True, verbose_name="Aktiv")

    # Abonnement: Nutzer, die dieses Objekt "folgen" und bei Änderungen
    # benachrichtigt werden sollen.
    followers = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='followed_objects',
        blank=True,
        verbose_name="Abonnenten",
        help_text="Nutzer, die bei Änderungen an diesem Objekt benachrichtigt werden"
    )

    class Meta:
        verbose_name = "Objekt"
        verbose_name_plural = "Objekte"
        ordering = ['name']

    def __str__(self):
        return f"{self.object_number} – {self.name}"

    def get_absolute_url(self):
        return reverse('objektverwaltung:detail', kwargs={'pk': self.pk})

    def get_follow_url(self):
        return reverse('objektverwaltung:toggle_follow', kwargs={'pk': self.pk})

    def is_followed_by(self, user):
        if not user or not user.is_authenticated:
            return False
        return self.followers.filter(pk=user.pk).exists()

    @property
    def full_address(self):
        parts = [f"{self.street} {self.house_number}".strip()]
        city_line = f"{self.postal_code} {self.city}".strip()
        if city_line:
            parts.append(city_line)
        return ", ".join(p for p in parts if p)


class Floor(TimeStampedModel):
    """Etage/Geschoss eines Objekts"""
    building = models.ForeignKey(
        BuildingObject, on_delete=models.CASCADE,
        related_name='floors', verbose_name="Objekt"
    )
    level = models.IntegerField(
        verbose_name="Geschoss-Ebene",
        help_text="z.B. -1 = Keller, 0 = Erdgeschoss, 1 = 1. OG"
    )
    name = models.CharField(
        max_length=100, blank=True,
        verbose_name="Bezeichnung",
        help_text="z.B. 'Erdgeschoss', 'Dachgeschoss'"
    )
    description = models.TextField(blank=True, verbose_name="Beschreibung")

    class Meta:
        verbose_name = "Etage"
        verbose_name_plural = "Etagen"
        ordering = ['building', 'level']
        unique_together = ('building', 'level')

    def __str__(self):
        return self.name or f"Ebene {self.level}"


class EscapeRoute(TimeStampedModel):
    """Fluchtweg eines Objekts (optional einer Etage zugeordnet)"""
    building = models.ForeignKey(
        BuildingObject, on_delete=models.CASCADE,
        related_name='escape_routes', verbose_name="Objekt"
    )
    floor = models.ForeignKey(
        Floor, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='escape_routes', verbose_name="Etage"
    )
    name = models.CharField(max_length=200, verbose_name="Bezeichnung")
    description = models.TextField(blank=True, verbose_name="Beschreibung")

    class Meta:
        verbose_name = "Fluchtweg"
        verbose_name_plural = "Fluchtwege"
        ordering = ['building', 'name']

    def __str__(self):
        return self.name


def add_months(date_value, months):
    """Datum um n Monate verschieben (Monatsende wird abgeschnitten)."""
    import calendar
    month_index = date_value.month - 1 + months
    year = date_value.year + month_index // 12
    month = month_index % 12 + 1
    day = min(date_value.day, calendar.monthrange(year, month)[1])
    return date_value.replace(year=year, month=month, day=day)


class InspectionType(models.TextChoices):
    """Prüfungsarten der Objektverwaltung (je Anlagentyp)"""
    FSD = 'fsd', 'Feuerwehrschlüsseldepot'
    BMZ = 'bmz', 'Brandmeldezentrale'
    LOESCHANLAGE = 'loeschanlage', 'Löschanlage'


class InspectableMixin(models.Model):
    """
    Prüfbare Anlage eines Objekts: Prüfintervall, letzte/nächste Prüfung,
    Fälligkeitsstatus. Die nächste Prüfung wird aus letzter Prüfung
    (bzw. Einbaudatum) + Intervall berechnet; ohne beides bleibt ein manuell
    gesetzter Termin erhalten.
    """
    DUE_SOON_DAYS = 30
    inspection_type = None  # in Unterklassen: InspectionType.*

    inspection_interval_months = models.PositiveSmallIntegerField(
        default=12, verbose_name="Prüfintervall (Monate)"
    )
    last_inspection = models.DateField(null=True, blank=True, verbose_name="Letzte Prüfung")
    next_inspection = models.DateField(
        null=True, blank=True, verbose_name="Nächste Prüfung",
        help_text="Wird aus letzter Prüfung (bzw. Einbaudatum) und Intervall berechnet"
    )

    class Meta:
        abstract = True

    # --- Termine -----------------------------------------------------------
    def compute_next_inspection(self):
        base = self.last_inspection or getattr(self, 'installed_at', None)
        if base is not None and self.inspection_interval_months:
            return add_months(base, self.inspection_interval_months)
        return self.next_inspection if not self.last_inspection else None

    def save(self, *args, **kwargs):
        self.next_inspection = self.compute_next_inspection()
        super().save(*args, **kwargs)

    def sync_from_reports(self):
        """Letzte Prüfung aus den Prüfberichten übernehmen und speichern."""
        latest = self.inspection_reports.order_by('-inspection_date').first()
        self.last_inspection = latest.inspection_date if latest else None
        if latest is None:
            self.next_inspection = None  # kein Bericht mehr → kein berechneter Termin
        self.save(update_fields=['last_inspection', 'next_inspection', 'updated_at'])

    # --- Status ------------------------------------------------------------
    @property
    def days_until_inspection(self):
        if not self.next_inspection:
            return None
        from django.utils import timezone
        return (self.next_inspection - timezone.localdate()).days

    @property
    def inspection_status(self):
        """'overdue' | 'due_soon' | 'ok' | 'unknown'"""
        days = self.days_until_inspection
        if days is None:
            return 'unknown'
        if days < 0:
            return 'overdue'
        if days <= self.DUE_SOON_DAYS:
            return 'due_soon'
        return 'ok'

    @property
    def inspection_status_display(self):
        return {
            'overdue': 'Prüfung überfällig',
            'due_soon': 'Prüfung bald fällig',
            'ok': 'Prüfung aktuell',
            'unknown': 'Kein Prüftermin',
        }[self.inspection_status]

    @property
    def inspection_type_label(self):
        return InspectionType(self.inspection_type).label

    @property
    def inspection_active(self):
        """Nur aktive Anlagen werden als fällig gemeldet."""
        return getattr(self, 'is_active', True)

    @property
    def display_name(self):
        return self.designation

    def get_absolute_url(self):
        return reverse('objektverwaltung:asset_detail',
                       kwargs={'type': self.inspection_type, 'pk': self.pk})


class FireAlarmPanel(InspectableMixin, TimeStampedModel):
    """Brandmeldezentrale (BMZ) eines Objekts"""
    inspection_type = InspectionType.BMZ

    building = models.ForeignKey(
        BuildingObject, on_delete=models.CASCADE,
        related_name='fire_alarm_panels', verbose_name="Objekt"
    )
    designation = models.CharField(max_length=200, verbose_name="Bezeichnung")
    location_description = models.CharField(
        max_length=255, blank=True,
        verbose_name="Standort",
        help_text="Wo befindet sich die BMZ? (z.B. 'Haupteingang links')"
    )
    manufacturer = models.CharField(max_length=120, blank=True, verbose_name="Hersteller")
    model = models.CharField(max_length=120, blank=True, verbose_name="Typ/Modell")
    notes = models.TextField(blank=True, verbose_name="Hinweise")

    class Meta:
        verbose_name = "Brandmeldezentrale"
        verbose_name_plural = "Brandmeldezentralen"
        ordering = ['building', 'designation']

    def __str__(self):
        return self.designation


class SuppressionSystemType(models.TextChoices):
    """Art einer Lösch-/Sprinkleranlage"""
    SPRINKLER = 'sprinkler', 'Sprinkleranlage'
    GAS = 'gas', 'Gaslöschanlage'
    FOAM = 'foam', 'Schaumlöschanlage'
    WATER_MIST = 'water_mist', 'Wassernebel-Löschanlage'
    DRY_RISER = 'dry_riser', 'Steigleitung trocken'
    WET_RISER = 'wet_riser', 'Steigleitung nass'
    OTHER = 'other', 'Sonstige'


class FireSuppressionSystem(InspectableMixin, TimeStampedModel):
    """Lösch-/Sprinkleranlage eines Objekts"""
    inspection_type = InspectionType.LOESCHANLAGE

    building = models.ForeignKey(
        BuildingObject, on_delete=models.CASCADE,
        related_name='suppression_systems', verbose_name="Objekt"
    )
    system_type = models.CharField(
        max_length=20, choices=SuppressionSystemType.choices,
        default=SuppressionSystemType.SPRINKLER, verbose_name="Art"
    )
    designation = models.CharField(max_length=200, verbose_name="Bezeichnung")
    location_description = models.CharField(
        max_length=255, blank=True, verbose_name="Standort / abgedeckter Bereich"
    )
    manufacturer = models.CharField(max_length=120, blank=True, verbose_name="Hersteller")
    is_operational = models.BooleanField(default=True, verbose_name="Funktionsfähig / in Betrieb")
    notes = models.TextField(blank=True, verbose_name="Hinweise")

    class Meta:
        verbose_name = "Löschanlage"
        verbose_name_plural = "Löschanlagen"
        ordering = ['building', 'designation']

    def __str__(self):
        return f"{self.get_system_type_display()}: {self.designation}"


class FSDType(models.TextChoices):
    """Typ eines Feuerwehrschlüsseldepots nach DIN 14675"""
    FSD1 = 'fsd1', 'FSD 1'
    FSD2 = 'fsd2', 'FSD 2'
    FSD3 = 'fsd3', 'FSD 3'


class FireKeyDepot(InspectableMixin, TimeStampedModel):
    """Feuerwehrschlüsseldepot (FSD) eines Objekts mit Prüfintervall"""
    inspection_type = InspectionType.FSD

    building = models.ForeignKey(
        BuildingObject, on_delete=models.CASCADE,
        related_name='key_depots', verbose_name="Objekt"
    )
    depot_type = models.CharField(
        max_length=10, choices=FSDType.choices,
        default=FSDType.FSD3, verbose_name="Typ"
    )
    designation = models.CharField(
        max_length=200, verbose_name="Bezeichnung",
        help_text="z.B. 'FSD Haupteingang'"
    )
    location_description = models.CharField(
        max_length=255, blank=True, verbose_name="Standort",
        help_text="Wo befindet sich das Depot? (z.B. 'Rechts neben Haupteingang')"
    )
    manufacturer = models.CharField(max_length=120, blank=True, verbose_name="Hersteller")
    serial_number = models.CharField(max_length=100, blank=True, verbose_name="Serien-/Depot-Nr.")
    installed_at = models.DateField(null=True, blank=True, verbose_name="Einbaudatum")
    contents = models.TextField(
        blank=True, verbose_name="Depot-Inhalt",
        help_text="Hinterlegte Schlüssel; wird als Vorbelegung in neue Prüfberichte übernommen"
    )
    is_active = models.BooleanField(default=True, verbose_name="Aktiv")
    notes = models.TextField(blank=True, verbose_name="Hinweise")

    class Meta:
        verbose_name = "Feuerwehrschlüsseldepot"
        verbose_name_plural = "Feuerwehrschlüsseldepots"
        ordering = ['building', 'designation']

    def __str__(self):
        return f"{self.get_depot_type_display()}: {self.designation}"


class InspectionResult(models.TextChoices):
    OK = 'ok', 'Ohne Mängel'
    DEFECTS = 'defects', 'Mit Mängeln'


# Rückwärtskompatibler Name
FSDInspectionResult = InspectionResult


class InspectionReport(AuditedModel):
    """
    Prüfbericht zu einer prüfbaren Anlage (Schlüsseldepot, BMZ, Löschanlage).
    Genau eine der Anlagen-Referenzen ist gesetzt; ``building`` und
    ``inspection_type`` werden daraus beim Speichern abgeleitet.
    """
    ASSET_FIELDS = {
        InspectionType.FSD: 'depot',
        InspectionType.BMZ: 'fire_alarm_panel',
        InspectionType.LOESCHANLAGE: 'suppression_system',
    }

    building = models.ForeignKey(
        BuildingObject, on_delete=models.CASCADE,
        related_name='inspection_reports', verbose_name="Objekt"
    )
    inspection_type = models.CharField(
        max_length=20, choices=InspectionType.choices, verbose_name="Prüfungsart"
    )
    depot = models.ForeignKey(
        FireKeyDepot, on_delete=models.CASCADE, null=True, blank=True,
        related_name='inspection_reports', verbose_name="Schlüsseldepot"
    )
    fire_alarm_panel = models.ForeignKey(
        FireAlarmPanel, on_delete=models.CASCADE, null=True, blank=True,
        related_name='inspection_reports', verbose_name="Brandmeldezentrale"
    )
    suppression_system = models.ForeignKey(
        FireSuppressionSystem, on_delete=models.CASCADE, null=True, blank=True,
        related_name='inspection_reports', verbose_name="Löschanlage"
    )

    inspection_date = models.DateField(verbose_name="Überprüfungsdatum")
    participant_operator = models.CharField(
        max_length=200, blank=True, verbose_name="Teilnehmer Betrieb"
    )
    participant_fire_dept = models.CharField(
        max_length=200, blank=True, verbose_name="Teilnehmer Feuerwehr"
    )
    participant_other = models.CharField(
        max_length=200, blank=True, verbose_name="Teilnehmer Sonstige"
    )
    depot_contents = models.TextField(blank=True, verbose_name="Depot-Inhalt")
    condition_report = models.TextField(blank=True, verbose_name="Zustandsbericht")
    result = models.CharField(
        max_length=10, choices=InspectionResult.choices,
        default=InspectionResult.OK, verbose_name="Ergebnis"
    )
    keys_match = models.BooleanField(
        default=True, verbose_name="Schlüssel entsprechen der Schließanlage",
        help_text="Bescheinigung: Die deponierten Schlüssel entsprechen der General- bzw. "
                  "Torschließanlage und öffnen alle Toranlagen und Türen gewaltfrei."
    )

    class Meta:
        verbose_name = "Prüfbericht"
        verbose_name_plural = "Prüfberichte"
        ordering = ['-inspection_date', '-created_at']

    def __str__(self):
        return f"Prüfbericht {self.inspection_date:%d.%m.%Y} – {self.asset}"

    @property
    def asset(self):
        for field in self.ASSET_FIELDS.values():
            value = getattr(self, field)
            if value is not None:
                return value
        return None

    @asset.setter
    def asset(self, value):
        for type_key, field in self.ASSET_FIELDS.items():
            setattr(self, field, value if value is not None and value.inspection_type == type_key else None)
        if value is not None:
            self.inspection_type = value.inspection_type
            self.building = value.building

    def save(self, *args, **kwargs):
        asset = self.asset
        if asset is not None:
            self.inspection_type = asset.inspection_type
            self.building_id = asset.building_id
        super().save(*args, **kwargs)
        if asset is not None:
            asset.sync_from_reports()


# Rückwärtskompatibler Name
FSDInspectionReport = InspectionReport


class CompensationStatus(models.TextChoices):
    """Status einer Kompensationsmaßnahme"""
    PLANNED = 'planned', 'Geplant'
    ACTIVE = 'active', 'Aktiv'
    DONE = 'done', 'Erledigt'


class CompensationMeasure(TimeStampedModel):
    """
    Kompensationsmaßnahme zum Ausgleich eines Brandschutz-Mangels
    (z.B. gesperrter Fluchtweg, ausgefallene Sprinkleranlage).
    Optional einem konkreten Fluchtweg oder einer Löschanlage zugeordnet.
    """
    building = models.ForeignKey(
        BuildingObject, on_delete=models.CASCADE,
        related_name='compensation_measures', verbose_name="Objekt"
    )
    title = models.CharField(max_length=200, verbose_name="Bezeichnung")
    reason = models.TextField(
        blank=True, verbose_name="Grund / Mangel",
        help_text="Welcher Mangel wird kompensiert? (z.B. Fluchtweg gesperrt)"
    )
    description = models.TextField(
        blank=True, verbose_name="Maßnahme",
        help_text="Welche Kompensationsmaßnahme wurde getroffen? (z.B. Brandsicherheitswache)"
    )
    escape_route = models.ForeignKey(
        EscapeRoute, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='compensation_measures', verbose_name="Betroffener Fluchtweg"
    )
    suppression_system = models.ForeignKey(
        FireSuppressionSystem, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='compensation_measures', verbose_name="Betroffene Löschanlage"
    )
    status = models.CharField(
        max_length=10, choices=CompensationStatus.choices,
        default=CompensationStatus.ACTIVE, verbose_name="Status"
    )
    start_date = models.DateField(null=True, blank=True, verbose_name="Beginn")
    end_date = models.DateField(null=True, blank=True, verbose_name="Frist / Ende")
    responsible = models.CharField(max_length=150, blank=True, verbose_name="Verantwortlich")

    class Meta:
        verbose_name = "Kompensationsmaßnahme"
        verbose_name_plural = "Kompensationsmaßnahmen"
        ordering = ['building', 'status', '-start_date']

    def __str__(self):
        return self.title


class BuildingContact(TimeStampedModel):
    """Ansprechpartner eines Objekts (Freitext, z.B. Hausmeister/Betreiber)"""
    building = models.ForeignKey(
        BuildingObject, on_delete=models.CASCADE,
        related_name='contacts', verbose_name="Objekt"
    )
    name = models.CharField(max_length=150, verbose_name="Name")
    role = models.CharField(
        max_length=120, blank=True,
        verbose_name="Funktion",
        help_text="z.B. Hausmeister, Betreiber, Sicherheitsbeauftragter"
    )
    phone = models.CharField(max_length=50, blank=True, verbose_name="Telefon")
    mobile = models.CharField(max_length=50, blank=True, verbose_name="Mobil")
    email = models.EmailField(blank=True, verbose_name="E-Mail")
    notes = models.TextField(blank=True, verbose_name="Hinweise")
    is_primary = models.BooleanField(default=False, verbose_name="Hauptansprechpartner")

    class Meta:
        verbose_name = "Ansprechpartner"
        verbose_name_plural = "Ansprechpartner"
        ordering = ['building', '-is_primary', 'name']

    def __str__(self):
        return f"{self.name} ({self.role})" if self.role else self.name


class PlanType(models.TextChoices):
    """Art eines hochgeladenen Plans/Dokuments"""
    LAUFKARTE = 'laufkarte', 'Laufkarte'
    FIRE_DEPT_PLAN = 'feuerwehrplan', 'Feuerwehrplan'
    ESCAPE_PLAN = 'fluchtplan', 'Flucht- und Rettungsplan'
    FLOOR_PLAN = 'grundriss', 'Grundriss / Gebäudeplan'
    OTHER = 'other', 'Sonstiges'


def building_plan_upload_path(instance, filename):
    return f"objektverwaltung/plans/{instance.building_id}/{filename}"


class BuildingPlan(AuditedModel):
    """
    Hochgeladene Laufkarte / Plan zu einem Objekt.
    Eigenes Modell, damit Uploads gezielt Abo-Benachrichtigungen auslösen können.
    """
    building = models.ForeignKey(
        BuildingObject, on_delete=models.CASCADE,
        related_name='plans', verbose_name="Objekt"
    )
    plan_type = models.CharField(
        max_length=20, choices=PlanType.choices,
        default=PlanType.LAUFKARTE, verbose_name="Art"
    )
    title = models.CharField(max_length=200, verbose_name="Titel")
    file = models.FileField(
        upload_to=building_plan_upload_path,
        verbose_name="Datei"
    )
    floor = models.ForeignKey(
        Floor, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='plans', verbose_name="Etage"
    )
    notes = models.TextField(blank=True, verbose_name="Hinweise")

    class Meta:
        verbose_name = "Plan / Laufkarte"
        verbose_name_plural = "Pläne / Laufkarten"
        ordering = ['building', 'plan_type', '-created_at']

    def __str__(self):
        return f"{self.get_plan_type_display()}: {self.title}"
