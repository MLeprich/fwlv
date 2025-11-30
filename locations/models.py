"""
Locations Models
Hierarchische Lagerorte-Verwaltung mit MPTT
"""

from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from mptt.models import MPTTModel, TreeForeignKey

from core.models.base import TimeStampedModel, AuditedModel


class LocationType(models.TextChoices):
    """
    Typen von Lagerorten - Hierarchisch organisiert

    Hierarchie-Empfehlung:
    1. SITE (Standort) - Hauptstandort/Wache
    2. BUILDING (Gebäude) - Gebäude auf dem Standort
    3. AREA (Stellfläche) - Außenbereich, Parkfläche
    4. ROOM (Raum/Stellplatz) - Raum in Gebäude oder nummerierter Stellplatz
    5. RACK (Regal) - Regal/Schrank im Raum
    6. SHELF (Regalboden) - Fach/Ablage im Regal
    7. BOX (Box) - Kiste/Container im Fach
    8. VEHICLE (Fahrzeug) - Mobiler Lagerort
    9. CONTAINER (Container) - Stationärer oder mobiler Container
    """
    # Ebene 1: Standorte
    SITE = 'site', _('Standort/Wache')

    # Ebene 2: Gebäude & Großstrukturen
    BUILDING = 'building', _('Gebäude')

    # Ebene 3: Bereiche
    AREA = 'area', _('Stellfläche/Außenbereich')

    # Ebene 4: Räume & Stellplätze
    ROOM = 'room', _('Raum')
    PARKING_SPOT = 'parking_spot', _('Stellplatz')

    # Ebene 5: Lagerstrukturen
    RACK = 'rack', _('Regal/Schrank')
    CABINET = 'cabinet', _('Schrank')

    # Ebene 6: Fächer & Ablagen
    SHELF = 'shelf', _('Regalboden/Fach')
    DRAWER = 'drawer', _('Schublade')

    # Ebene 7: Kleinbehälter
    BOX = 'box', _('Kiste/Box')

    # Mobile & Spezial
    VEHICLE = 'vehicle', _('Fahrzeug (mobil)')
    CONTAINER = 'container', _('Container')

    # Sonstiges
    OTHER = 'other', _('Sonstiges')


class Location(MPTTModel, AuditedModel):
    """
    Hierarchischer Lagerort

    Verwendet django-mptt für effiziente hierarchische Queries.
    Beispiel-Hierarchie:
    - Feuerwache Nord (Gebäude)
      - Gerätehalle (Raum)
        - Regal 1 (Regal)
          - Fach A (Regalboden)
      - Rettungswagen 1 (Fahrzeug)
        - Fach 1 (Box)
    """

    # Hierarchie
    parent = TreeForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        verbose_name=_('Übergeordneter Standort'),
        help_text=_('Übergeordneter Lagerort in der Hierarchie')
    )

    # Basis-Informationen
    name = models.CharField(
        max_length=200,
        verbose_name=_('Name'),
        help_text=_('Bezeichnung des Lagerorts')
    )

    code = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_('Kennzeichen/Code'),
        help_text=_('Eindeutiger Code (z.B. FWN-GH-R1-FA)')
    )

    location_type = models.CharField(
        max_length=20,
        choices=LocationType.choices,
        default=LocationType.ROOM,
        verbose_name=_('Typ'),
        help_text=_('Art des Lagerorts')
    )

    # Adresse (nur für Haupt-Standorte)
    street = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Straße'),
    )

    house_number = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_('Hausnummer'),
    )

    postal_code = models.CharField(
        max_length=10,
        blank=True,
        verbose_name=_('PLZ'),
    )

    city = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Stadt'),
    )

    # Zusätzliche Informationen
    description = models.TextField(
        blank=True,
        verbose_name=_('Beschreibung'),
        help_text=_('Zusätzliche Informationen zum Lagerort')
    )

    capacity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_('Kapazität'),
        help_text=_('Maximale Kapazität (z.B. Volumen in m³, Gewicht in kg)')
    )

    capacity_unit = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_('Einheit'),
        help_text=_('Einheit der Kapazität (z.B. m³, kg, Stück)')
    )

    # Zugriffskontrolle
    access_restricted = models.BooleanField(
        default=False,
        verbose_name=_('Zugriff beschränkt'),
        help_text=_('Ist der Zugriff auf diesen Lagerort beschränkt?')
    )

    access_instructions = models.TextField(
        blank=True,
        verbose_name=_('Zugangshinweise'),
        help_text=_('Informationen zum Zugang (z.B. Schlüsselnummer, Türcode)')
    )

    # Klima/Lagerung
    climate_controlled = models.BooleanField(
        default=False,
        verbose_name=_('Klimatisiert'),
        help_text=_('Ist der Lagerort klimatisiert?')
    )

    temperature_min = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        null=True,
        blank=True,
        verbose_name=_('Min. Temperatur (°C)'),
    )

    temperature_max = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        null=True,
        blank=True,
        verbose_name=_('Max. Temperatur (°C)'),
    )

    # QR-Code für einfachen Zugriff
    qr_code = models.ImageField(
        upload_to='locations/qr_codes/',
        null=True,
        blank=True,
        verbose_name=_('QR-Code'),
        help_text=_('QR-Code für mobilen Zugriff')
    )

    # Status
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Aktiv'),
        help_text=_('Ist der Lagerort aktiv und nutzbar?')
    )

    # Technische Ausstattung (z.B. für Räume)
    technical_equipment = models.TextField(
        blank=True,
        verbose_name=_('Technische Ausstattung'),
        help_text=_('Vorhandene Technik (z.B. Beamer, Prowise-Board, Soundsystem)')
    )

    # Notizen
    notes = models.TextField(
        blank=True,
        verbose_name=_('Notizen'),
        help_text=_('Interne Notizen')
    )

    class MPTTMeta:
        order_insertion_by = ['name']

    class Meta:
        verbose_name = _('Lagerort')
        verbose_name_plural = _('Lagerorte')
        ordering = ['tree_id', 'lft']  # MPTT ordering
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['location_type']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"

    def get_absolute_url(self):
        """URL zur Detailansicht"""
        return reverse('locations:detail', kwargs={'pk': self.pk})

    def get_full_path(self):
        """
        Vollständiger Pfad in der Hierarchie
        z.B. "Feuerwache Nord > Gerätehalle > Regal 1"
        """
        ancestors = self.get_ancestors(include_self=True)
        return ' > '.join([loc.name for loc in ancestors])

    def get_full_code(self):
        """
        Vollständiger Code-Pfad
        z.B. "FWN-GH-R1"
        """
        ancestors = self.get_ancestors(include_self=True)
        return '-'.join([loc.code for loc in ancestors])

    def get_address(self):
        """
        Vollständige Adresse (falls vorhanden)
        """
        if not (self.street and self.city):
            # Versuche Adresse vom Parent zu holen
            if self.parent:
                return self.parent.get_address()
            return None

        parts = []
        if self.street:
            parts.append(f"{self.street} {self.house_number}".strip())
        if self.postal_code and self.city:
            parts.append(f"{self.postal_code} {self.city}")

        return ', '.join(parts) if parts else None

    def get_item_count(self):
        """
        Anzahl der Artikel an diesem Lagerort
        TODO: Später implementieren wenn inventory_base vorhanden
        """
        # from inventory_base.models import InventoryItem
        # return InventoryItem.objects.filter(location=self).count()
        return 0

    def get_total_item_count(self):
        """
        Gesamtanzahl der Artikel (inkl. Unter-Lagerorte)
        """
        # TODO: Später implementieren
        return 0

    def is_available(self):
        """
        Prüft ob der Lagerort verfügbar ist
        """
        return self.is_active

    def has_children_items(self):
        """
        Prüft ob dieser Lagerort Unter-Lagerorte hat
        """
        return self.get_children().exists()

    def can_be_deleted(self):
        """
        Prüft ob der Lagerort gelöscht werden kann
        (Keine Artikel, keine Unter-Lagerorte)
        """
        # TODO: Später auch Artikel-Check
        return not self.has_children_items()

    def generate_qr_code(self):
        """
        Generiert QR-Code für diesen Lagerort
        TODO: Später implementieren mit qrcode library
        """
        pass

    @classmethod
    def get_root_locations(cls):
        """
        Gibt alle Haupt-Standorte zurück (ohne Parent)
        """
        return cls.objects.filter(parent__isnull=True, is_active=True)

    @classmethod
    def get_by_type(cls, location_type):
        """
        Gibt alle Lagerorte eines bestimmten Typs zurück
        """
        return cls.objects.filter(location_type=location_type, is_active=True)
