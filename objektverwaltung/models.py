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


class ObjectStatus(models.TextChoices):
    """Lebenszyklus-Status eines Objekts"""
    ACTIVE = 'active', 'Aktiv'
    PLANNED = 'planned', 'In Planung'
    INACTIVE = 'inactive', 'Inaktiv'
    FOR_DELETION = 'for_deletion', 'Zum Löschen vorgemerkt'

    @property
    def badge_class(self):
        return {
            'active': 'bg-green-100 text-green-800',
            'planned': 'bg-blue-100 text-blue-800',
            'inactive': 'bg-gray-100 text-gray-800',
            'for_deletion': 'bg-red-100 text-red-800',
        }[self.value]


class UsageCategory(models.Model):
    """
    Nutzungsart eines Objekts (z.B. Schule, Krankenhaus, Versammlungsstätte).

    Wird im Modul selbst unter „Nutzungsarten“ gepflegt. Nutzungsarten, die
    von Objekten verwendet werden, lassen sich nicht löschen, aber deaktivieren.
    """

    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Bezeichnung",
        help_text="Wird in Listen und Auswahlfeldern angezeigt"
    )
    sort_order = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="Reihenfolge",
        help_text="Kleinere Werte stehen weiter oben"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Aktiv",
        help_text="Inaktive Nutzungsarten stehen für neue Objekte nicht mehr zur Auswahl; "
                  "bestehende Objekte behalten sie"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Erstellt am")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Aktualisiert am")

    class Meta:
        verbose_name = "Nutzungsart"
        verbose_name_plural = "Nutzungsarten"
        ordering = ['sort_order', 'name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('objektverwaltung:usage_category_list')

    @property
    def usage_count(self):
        return self.buildings.count()

    @property
    def is_in_use(self):
        return self.buildings.exists()


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
    usage_type = models.ForeignKey(
        UsageCategory,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='buildings',
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

    status = models.CharField(
        max_length=20,
        choices=ObjectStatus.choices,
        default=ObjectStatus.ACTIVE,
        verbose_name="Status"
    )

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

    def get_usage_type_display(self):
        """Wie bei einem Choice-Feld: Bezeichnung der Nutzungsart oder '–'."""
        return self.usage_type.name if self.usage_type_id else '–'

    @property
    def is_active(self):
        return self.status == ObjectStatus.ACTIVE

    @property
    def status_badge_class(self):
        return ObjectStatus(self.status).badge_class

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


# ============================================================================
# BRANDVERHÜTUNGSSCHAU (BVS)
#
# Fristen der Prüfsachverständigen (PSV), zentral gepflegte Mustersätze und
# die Niederschrift über die Brandverhütungsschau nach § 26 BHKG.
#
# Eigene Rechte (bvs_view / bvs_edit / bvs_manage) statt der Modellrechte:
# alle BVS-Modelle haben ``default_permissions = ()``, damit die Gruppen der
# Objektverwaltung (view_*/add_* bzw. „alle Rechte der App“) nicht automatisch
# Zugriff auf die Brandverhütungsschau bekommen.
# ============================================================================

class PSVInspectionType(models.Model):
    """Art einer Prüfung durch Prüfsachverständige (frei pflegbar, z.B. RWA, BMA)."""

    name = models.CharField(max_length=150, unique=True, verbose_name="Bezeichnung")
    interval_months = models.PositiveSmallIntegerField(
        default=36, verbose_name="Prüfintervall (Monate)",
        help_text="Vorschlag für „gültig bis“ beim Eintragen einer neuen Prüfung"
    )
    warning_days = models.PositiveSmallIntegerField(
        default=90, verbose_name="Vorwarnzeit (Tage)",
        help_text="So viele Tage vor Ablauf wird die Frist gelb markiert"
    )
    sort_order = models.PositiveSmallIntegerField(default=0, verbose_name="Reihenfolge")
    is_active = models.BooleanField(
        default=True, verbose_name="Aktiv",
        help_text="Inaktive Prüfarten stehen für neue Prüfpflichten nicht mehr zur Auswahl"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Erstellt am")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Aktualisiert am")

    class Meta:
        verbose_name = "PSV-Prüfart"
        verbose_name_plural = "PSV-Prüfarten"
        ordering = ['sort_order', 'name']
        default_permissions = ()

    def __str__(self):
        return self.name

    @property
    def is_in_use(self):
        return self.requirements.exists()


class PSVStatus(models.TextChoices):
    """Ampelstatus einer PSV-Frist"""
    EXPIRED = 'expired', 'Abgelaufen'
    MISSING = 'missing', 'Kein Nachweis'
    EXPIRING = 'expiring', 'Läuft bald ab'
    VALID = 'valid', 'Gültig'
    INACTIVE = 'inactive', 'Nicht mehr erforderlich'

    @property
    def badge_class(self):
        return {
            'expired': 'bg-red-100 text-red-800',
            'missing': 'bg-red-100 text-red-800',
            'expiring': 'bg-yellow-100 text-yellow-800',
            'valid': 'bg-green-100 text-green-800',
            'inactive': 'bg-gray-100 text-gray-600',
        }[self.value]

    @property
    def dot_class(self):
        return {
            'expired': 'bg-red-500',
            'missing': 'bg-red-500',
            'expiring': 'bg-yellow-400',
            'valid': 'bg-green-500',
            'inactive': 'bg-gray-300',
        }[self.value]


class PSVRequirement(TimeStampedModel):
    """
    Prüfpflicht eines Objekts: welche Prüfung durch Prüfsachverständige
    erforderlich ist. Der aktuelle Stand (letzte Prüfung, gültig bis) wird
    aus der jüngsten Prüfbescheinigung übernommen.
    """
    building = models.ForeignKey(
        BuildingObject, on_delete=models.CASCADE,
        related_name='psv_requirements', verbose_name="Objekt"
    )
    inspection_type = models.ForeignKey(
        PSVInspectionType, on_delete=models.PROTECT,
        related_name='requirements', verbose_name="Prüfart"
    )
    designation = models.CharField(
        max_length=200, blank=True, verbose_name="Anlage / Bereich",
        help_text="z.B. „RWA Treppenraum A“ – leer lassen, wenn es nur eine Anlage dieser Art gibt"
    )
    notes = models.TextField(blank=True, verbose_name="Hinweise")
    is_active = models.BooleanField(
        default=True, verbose_name="Erforderlich",
        help_text="Nicht mehr erforderliche Prüfpflichten bleiben mit ihrer Historie erhalten"
    )
    last_inspection = models.DateField(null=True, blank=True, verbose_name="Letzte Prüfung")
    valid_until = models.DateField(null=True, blank=True, verbose_name="Gültig bis")

    class Meta:
        verbose_name = "PSV-Prüfpflicht"
        verbose_name_plural = "PSV-Prüfpflichten"
        ordering = ['building', 'inspection_type__sort_order', 'inspection_type__name', 'designation']
        default_permissions = ()

    def __str__(self):
        return self.display_name

    def get_absolute_url(self):
        return reverse('objektverwaltung:psv_detail', kwargs={'pk': self.pk})

    @property
    def display_name(self):
        if self.designation:
            return f"{self.inspection_type.name} – {self.designation}"
        return self.inspection_type.name

    def sync_from_certificates(self):
        """Stand aus der jüngsten Prüfbescheinigung übernehmen und speichern."""
        latest = self.certificates.order_by('-inspection_date', '-valid_until', '-pk').first()
        self.last_inspection = latest.inspection_date if latest else None
        self.valid_until = latest.valid_until if latest else None
        self.save(update_fields=['last_inspection', 'valid_until', 'updated_at'])

    @property
    def latest_certificate(self):
        return self.certificates.order_by('-inspection_date', '-valid_until', '-pk').first()

    @property
    def days_left(self):
        if not self.valid_until:
            return None
        from django.utils import timezone
        return (self.valid_until - timezone.localdate()).days

    @property
    def remaining_display(self):
        """z.B. „noch 45 Tage“, „seit 3 Tagen abgelaufen“, „läuft heute ab“."""
        days = self.days_left
        if days is None:
            return ''
        if days == 0:
            return 'läuft heute ab'
        if days > 0:
            return f'noch {days} Tag{"e" if days != 1 else ""}'
        return f'seit {-days} Tag{"en" if days != -1 else ""} abgelaufen'

    @property
    def status(self):
        if not self.is_active:
            return PSVStatus.INACTIVE
        days = self.days_left
        if days is None:
            return PSVStatus.MISSING
        if days < 0:
            return PSVStatus.EXPIRED
        if days <= self.inspection_type.warning_days:
            return PSVStatus.EXPIRING
        return PSVStatus.VALID

    @property
    def status_display(self):
        return self.status.label

    @property
    def status_badge_class(self):
        return self.status.badge_class

    @property
    def status_dot_class(self):
        return self.status.dot_class

    @property
    def needs_action(self):
        return self.status in (PSVStatus.EXPIRED, PSVStatus.MISSING, PSVStatus.EXPIRING)


class PSVResult(models.TextChoices):
    OK = 'ok', 'Ohne Mängel'
    MINOR = 'minor', 'Geringfügige Mängel'
    MAJOR = 'major', 'Wesentliche Mängel'


def psv_certificate_upload_path(instance, filename):
    return f"objektverwaltung/psv/{instance.requirement.building_id}/{filename}"


class PSVCertificate(AuditedModel):
    """Prüfbescheinigung eines Prüfsachverständigen zu einer Prüfpflicht."""
    requirement = models.ForeignKey(
        PSVRequirement, on_delete=models.CASCADE,
        related_name='certificates', verbose_name="Prüfpflicht"
    )
    inspection_date = models.DateField(verbose_name="Prüfdatum")
    valid_until = models.DateField(verbose_name="Gültig bis")
    expert_name = models.CharField(max_length=150, blank=True, verbose_name="Prüfsachverständige/r")
    expert_company = models.CharField(max_length=150, blank=True, verbose_name="Firma / Büro")
    result = models.CharField(
        max_length=10, choices=PSVResult.choices, default=PSVResult.OK, verbose_name="Ergebnis"
    )
    document = models.FileField(
        upload_to=psv_certificate_upload_path, blank=True, verbose_name="Bescheinigung (Datei)"
    )
    notes = models.TextField(blank=True, verbose_name="Hinweise")

    class Meta:
        verbose_name = "PSV-Prüfbescheinigung"
        verbose_name_plural = "PSV-Prüfbescheinigungen"
        ordering = ['-inspection_date', '-pk']
        default_permissions = ()

    def __str__(self):
        return f"{self.requirement.display_name}: geprüft {self.inspection_date:%d.%m.%Y}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.requirement.sync_from_certificates()


class BVSPhraseCategory(models.Model):
    """Kapitel bzw. Abschnitt der Mustersätze (z.B. „2 Flächen für die Feuerwehr“, „2.1 Zugänge“)."""
    number = models.CharField(max_length=10, unique=True, verbose_name="Nummer")
    title = models.CharField(max_length=200, verbose_name="Bezeichnung")
    parent = models.ForeignKey(
        'self', on_delete=models.CASCADE, null=True, blank=True,
        related_name='children', verbose_name="Kapitel",
        help_text="Leer lassen für ein Kapitel; bei einem Abschnitt das übergeordnete Kapitel"
    )
    sort_order = models.PositiveIntegerField(default=0, verbose_name="Reihenfolge")

    class Meta:
        verbose_name = "Mustersatz-Kapitel"
        verbose_name_plural = "Mustersatz-Kapitel"
        ordering = ['sort_order', 'number']
        default_permissions = ()

    def __str__(self):
        return f"{self.number} {self.title}"

    @staticmethod
    def sort_key_for(number):
        """„2.10“ → 2010: Kapitel und Abschnitte numerisch sortieren."""
        parts = [int(p) if p.isdigit() else 0 for p in number.split('.')][:2]
        return parts[0] * 1000 + (parts[1] if len(parts) > 1 else 0)


class BVSPhrase(models.Model):
    """Mustersatz / Textbaustein für Mängel in der Niederschrift."""
    category = models.ForeignKey(
        BVSPhraseCategory, on_delete=models.PROTECT,
        related_name='phrases', verbose_name="Kapitel / Abschnitt"
    )
    code = models.CharField(max_length=10, unique=True, verbose_name="Nr.")
    title = models.CharField(max_length=200, verbose_name="Titel")
    text = models.TextField(
        blank=True, verbose_name="Text",
        help_text="„…“ markiert Stellen, die vor Ort ergänzt werden"
    )
    review_note = models.TextField(
        blank=True, verbose_name="Prüfhinweis",
        help_text="Hinweise aus dem Import (z.B. Randkommentare der Vorlage) – nach Durchsicht leeren"
    )
    is_active = models.BooleanField(
        default=True, verbose_name="Aktiv",
        help_text="Nur aktive Mustersätze stehen bei der Brandverhütungsschau zur Auswahl"
    )
    sort_order = models.PositiveIntegerField(default=0, verbose_name="Reihenfolge")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Erstellt am")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Aktualisiert am")

    class Meta:
        verbose_name = "Mustersatz"
        verbose_name_plural = "Mustersätze"
        ordering = ['sort_order', 'code']
        default_permissions = ()

    def __str__(self):
        return f"{self.code} {self.title}"


class BVSStatus(models.TextChoices):
    DRAFT = 'draft', 'In Bearbeitung'
    COMPLETED = 'completed', 'Abgeschlossen'


class FireSafetyInspection(AuditedModel):
    """
    Brandverhütungsschau nach § 26 BHKG mit Niederschrift, Mängelliste und
    den Angaben des Erfassungsblatts für die Gebührenabrechnung.
    """
    building = models.ForeignKey(
        BuildingObject, on_delete=models.CASCADE,
        related_name='fire_safety_inspections', verbose_name="Objekt"
    )
    status = models.CharField(
        max_length=10, choices=BVSStatus.choices, default=BVSStatus.DRAFT, verbose_name="Status"
    )
    inspection_date = models.DateField(verbose_name="Datum der Brandverhütungsschau")
    report_number = models.CharField(max_length=50, blank=True, verbose_name="Berichtnummer")
    object_key = models.CharField(max_length=50, blank=True, verbose_name="Objekt-Kennziffer laut Satzung")
    cost_bearer = models.CharField(max_length=200, blank=True, verbose_name="Kostenträger (Firma)")

    participant_operator = models.CharField(max_length=300, blank=True, verbose_name="Teilnehmer Betrieb")
    participant_fire_dept = models.CharField(max_length=300, blank=True, verbose_name="Teilnehmer Feuerwehr")
    participant_other = models.CharField(max_length=300, blank=True, verbose_name="Teilnehmer Sonstige")

    # Zeitaufwand (Erfassungsblatt)
    departure_station = models.TimeField(null=True, blank=True, verbose_name="Abfahrt Feuerwache")
    arrival_object = models.TimeField(null=True, blank=True, verbose_name="Ankunft Objekt")
    departure_object = models.TimeField(null=True, blank=True, verbose_name="Abfahrt Objekt")
    arrival_station = models.TimeField(null=True, blank=True, verbose_name="Ankunft Feuerwache")
    prep_minutes = models.PositiveSmallIntegerField(
        null=True, blank=True, verbose_name="Vor- und Nachbearbeitung (Minuten)"
    )

    # Ergebnis
    defect_deadline = models.DateField(
        null=True, blank=True, verbose_name="Frist zur Mängelbeseitigung",
        help_text="Danach erfolgt eine Nachschau"
    )
    next_inspection = models.DateField(
        null=True, blank=True, verbose_name="Nächste Brandverhütungsschau (voraussichtlich)",
        help_text="Es zählt nur Monat und Jahr"
    )
    is_fee_required = models.BooleanField(
        default=True, verbose_name="Gebührenpflichtig",
        help_text="Niederschrift mit Hinweis auf den Gebührenbescheid"
    )

    # Briefkopf der Niederschrift
    recipient_address = models.TextField(
        blank=True, verbose_name="Anschrift Empfänger",
        help_text="Erscheint im Adressfeld der Niederschrift"
    )
    clerk_name = models.CharField(max_length=150, blank=True, verbose_name="Bearbeiter/in")
    clerk_phone = models.CharField(max_length=30, blank=True, verbose_name="Durchwahl")
    clerk_room = models.CharField(max_length=30, blank=True, verbose_name="Zimmer-Nr.")
    clerk_email = models.CharField(max_length=150, blank=True, verbose_name="E-Mail")
    our_reference = models.CharField(max_length=50, blank=True, verbose_name="Mein Zeichen")

    notes = models.TextField(blank=True, verbose_name="Interne Notizen",
                             help_text="Erscheint nicht in der Niederschrift")

    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="Abgeschlossen am")
    completed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='+', verbose_name="Abgeschlossen von"
    )

    class Meta:
        verbose_name = "Brandverhütungsschau"
        verbose_name_plural = "Brandverhütungsschauen"
        ordering = ['-inspection_date', '-created_at']
        default_permissions = ()
        permissions = [
            ('bvs_view', 'Brandverhütungsschau: Niederschriften und PSV-Fristen ansehen'),
            ('bvs_edit', 'Brandverhütungsschau: durchführen, Niederschriften und PSV-Fristen bearbeiten'),
            ('bvs_manage', 'Brandverhütungsschau: Mustersätze und PSV-Prüfarten verwalten'),
        ]

    def __str__(self):
        return f"Brandverhütungsschau {self.inspection_date:%d.%m.%Y} – {self.building.name}"

    def get_absolute_url(self):
        return reverse('objektverwaltung:bvs_detail', kwargs={'pk': self.pk})

    @property
    def is_completed(self):
        return self.status == BVSStatus.COMPLETED

    @property
    def status_badge_class(self):
        return 'bg-green-100 text-green-800' if self.is_completed else 'bg-blue-100 text-blue-800'

    @property
    def open_defects(self):
        return [d for d in self.defects.all() if not d.resolved_on]

    @property
    def follow_up_status(self):
        """Nachschau: 'overdue' | 'open' | '' (keine offenen Mängel mit Frist)."""
        if not self.is_completed or not self.defect_deadline or not self.open_defects:
            return ''
        from django.utils import timezone
        return 'overdue' if self.defect_deadline < timezone.localdate() else 'open'


class FireSafetyDefect(TimeStampedModel):
    """Mangel aus der Brandverhütungsschau (Zeile der Mängelliste)."""
    inspection = models.ForeignKey(
        FireSafetyInspection, on_delete=models.CASCADE,
        related_name='defects', verbose_name="Brandverhütungsschau"
    )
    position = models.PositiveIntegerField(default=0, verbose_name="Reihenfolge")
    number = models.CharField(max_length=20, blank=True, verbose_name="Punkt")
    location = models.CharField(max_length=200, blank=True, verbose_name="Ort / Bereich")
    text = models.TextField(blank=True, verbose_name="Art des Mangels und notwendige Maßnahme")
    phrase = models.ForeignKey(
        BVSPhrase, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='defects', verbose_name="Mustersatz"
    )
    resolved_on = models.DateField(null=True, blank=True, verbose_name="Behoben am")

    class Meta:
        verbose_name = "Mangel"
        verbose_name_plural = "Mängel"
        ordering = ['position', 'pk']
        default_permissions = ()

    def __str__(self):
        return f"Punkt {self.number}" if self.number else f"Mangel {self.pk}"

    #: Platzhalter der Mustersätze, die vor Ort ausgefüllt werden
    GAP_MARKERS = ('…', '...')

    @property
    def has_gap(self):
        return any(marker in self.text for marker in self.GAP_MARKERS)
