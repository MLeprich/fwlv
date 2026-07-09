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


class FireAlarmPanel(TimeStampedModel):
    """Brandmeldezentrale (BMZ) eines Objekts"""
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


class FireSuppressionSystem(TimeStampedModel):
    """Lösch-/Sprinkleranlage eines Objekts"""
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
    last_inspection = models.DateField(null=True, blank=True, verbose_name="Letzte Prüfung")
    next_inspection = models.DateField(null=True, blank=True, verbose_name="Nächste Prüfung")
    is_operational = models.BooleanField(default=True, verbose_name="Funktionsfähig / in Betrieb")
    notes = models.TextField(blank=True, verbose_name="Hinweise")

    class Meta:
        verbose_name = "Löschanlage"
        verbose_name_plural = "Löschanlagen"
        ordering = ['building', 'designation']

    def __str__(self):
        return f"{self.get_system_type_display()}: {self.designation}"


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
