"""
Organization Models
Verwaltung der Organisationsstruktur: Abteilungen, FF-Einheiten, Wachmannschaften
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.urls import reverse


class RelatedModule(models.TextChoices):
    """
    Module, zu denen Funktionen, Qualifikationen und Pflichtstunden zugeordnet werden können
    """
    EQUIPMENT = 'equipment', _('Ausrüstung')
    DIVING = 'diving', _('Taucher')
    HEIGHT_RESCUE = 'height_rescue', _('Höhenrettung')


class Department(models.Model):
    """
    Abteilungen der Feuerwehr
    z.B. Einsatzabteilung, Technik, Verwaltung, Ausbildung
    """
    name = models.CharField(
        max_length=200,
        unique=True,
        verbose_name=_('Name'),
        help_text=_('z.B. Einsatzabteilung, Technik, Verwaltung')
    )
    abbreviation = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_('Abkürzung'),
        help_text=_('z.B. EA, TEC, VW')
    )
    description = models.TextField(
        blank=True,
        verbose_name=_('Beschreibung')
    )

    # Leitung
    head = models.ForeignKey(
        'personnel.Person',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='headed_departments',
        verbose_name=_('Fachbereichsleiter'),
        help_text=_('Leiter/in dieser Abteilung')
    )
    deputy_head = models.ForeignKey(
        'personnel.Person',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='deputy_headed_departments',
        verbose_name=_('Stellv. Fachbereichsleiter'),
        help_text=_('Stellvertretende/r Leiter/in dieser Abteilung')
    )

    # Procurement-Felder (zusammengeführt aus ProcurementDepartment)
    budget_code = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_('Budgetcode'),
        help_text=_('Standard-Budgetcode für diesen Fachbereich')
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Aktiv')
    )
    sort_order = models.IntegerField(
        default=0,
        verbose_name=_('Sortierung'),
        help_text=_('Niedrigere Werte werden zuerst angezeigt')
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
        verbose_name = _('Abteilung')
        verbose_name_plural = _('Abteilungen')
        ordering = ['sort_order', 'name']
        indexes = [
            models.Index(fields=['is_active', 'sort_order']),
        ]

    def __str__(self):
        if self.abbreviation:
            return f"{self.name} ({self.abbreviation})"
        return self.name

    def get_absolute_url(self):
        return reverse('organization:department_detail', kwargs={'pk': self.pk})


class VolunteerUnit(models.Model):
    """
    Einheiten der Freiwilligen Feuerwehr
    z.B. Löschzug 1, Löschgruppe Musterort, Löschzug Stadtmitte
    """
    name = models.CharField(
        max_length=200,
        unique=True,
        verbose_name=_('Name'),
        help_text=_('z.B. Löschzug 1, Löschgruppe Musterort')
    )
    abbreviation = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_('Abkürzung'),
        help_text=_('z.B. LZ 1, LG Muster')
    )
    location = models.ForeignKey(
        'locations.Location',
        on_delete=models.PROTECT,
        related_name='volunteer_units',
        null=True,
        blank=True,
        verbose_name=_('Standort'),
        help_text=_('Feuerwehrhaus/Gerätehaus')
    )
    description = models.TextField(
        blank=True,
        verbose_name=_('Beschreibung')
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Aktiv')
    )
    sort_order = models.IntegerField(
        default=0,
        verbose_name=_('Sortierung'),
        help_text=_('Niedrigere Werte werden zuerst angezeigt')
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
        verbose_name = _('FF-Einheit')
        verbose_name_plural = _('FF-Einheiten')
        ordering = ['sort_order', 'name']
        indexes = [
            models.Index(fields=['is_active', 'sort_order']),
            models.Index(fields=['location']),
        ]

    def __str__(self):
        if self.abbreviation:
            return f"{self.name} ({self.abbreviation})"
        return self.name

    def get_absolute_url(self):
        return reverse('organization:volunteer_unit_detail', kwargs={'pk': self.pk})


class WatchCrew(models.Model):
    """
    Wachmannschaften der Berufsfeuerwehr
    z.B. 1. Wachmannschaft, 2. Wachmannschaft, 3. Wachmannschaft
    Es gibt je Wache 3 Wachmannschaften.
    """
    name = models.CharField(
        max_length=200,
        verbose_name=_('Name'),
        help_text=_('z.B. 1. Wachmannschaft, 2. Wachmannschaft')
    )
    abbreviation = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_('Kürzel'),
        help_text=_('z.B. WA1, WA2, WA3')
    )
    station = models.ForeignKey(
        'locations.Location',
        on_delete=models.PROTECT,
        related_name='watch_crews',
        verbose_name=_('Wachenstandort'),
        help_text=_('Feuerwache/Standort')
    )
    description = models.TextField(
        blank=True,
        verbose_name=_('Beschreibung')
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Aktiv')
    )
    sort_order = models.IntegerField(
        default=0,
        verbose_name=_('Sortierung'),
        help_text=_('Niedrigere Werte werden zuerst angezeigt')
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
        verbose_name = _('Wachmannschaft')
        verbose_name_plural = _('Wachmannschaften')
        ordering = ['station', 'sort_order', 'name']
        unique_together = [['name', 'station']]
        indexes = [
            models.Index(fields=['is_active', 'station']),
            models.Index(fields=['station']),
        ]

    def __str__(self):
        return f"{self.name} - {self.station.name}"

    def get_absolute_url(self):
        return reverse('organization:watch_crew_detail', kwargs={'pk': self.pk})


class Function(models.Model):
    """
    Funktionen bei der Feuerwehr
    z.B. Gruppenführer, Taucher, Höhenretter, Atemschutzgeräteträger, Maschinist
    """
    name = models.CharField(
        max_length=200,
        unique=True,
        verbose_name=_('Name'),
        help_text=_('z.B. Gruppenführer, Taucher, Höhenretter')
    )
    abbreviation = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_('Abkürzung'),
        help_text=_('z.B. GF, MA, AGT')
    )
    description = models.TextField(
        blank=True,
        verbose_name=_('Beschreibung')
    )
    related_module = models.CharField(
        max_length=50,
        choices=RelatedModule.choices,
        blank=True,
        null=True,
        verbose_name=_('Zugeordnetes Modul'),
        help_text=_('Modul, zu dem diese Funktion gehört (z.B. Taucher, Höhenrettung, Ausrüstung)')
    )
    requires_qualification = models.BooleanField(
        default=False,
        verbose_name=_('Qualifikation erforderlich'),
        help_text=_('Ist eine spezielle Qualifikation/Ausbildung erforderlich?')
    )
    required_qualifications = models.ManyToManyField(
        'personnel.QualificationTemplate',
        blank=True,
        related_name='required_for_functions',
        verbose_name=_('Erforderliche Qualifikationen'),
        help_text=_('Wählen Sie die Qualifikationen aus, die für diese Funktion erforderlich sind')
    )
    required_duty_hour_categories = models.ManyToManyField(
        'personnel.DutyHoursCategory',
        blank=True,
        related_name='required_for_functions',
        verbose_name=_('Erforderliche Pflichtstunden-Kategorien'),
        help_text=_('Wählen Sie die Pflichtstunden-Kategorien aus, die für diese Funktion erforderlich sind')
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Aktiv')
    )
    sort_order = models.IntegerField(
        default=0,
        verbose_name=_('Sortierung'),
        help_text=_('Niedrigere Werte werden zuerst angezeigt')
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
        verbose_name = _('Funktion')
        verbose_name_plural = _('Funktionen')
        ordering = ['sort_order', 'name']
        indexes = [
            models.Index(fields=['is_active', 'sort_order']),
        ]

    def __str__(self):
        if self.abbreviation:
            return f"{self.name} ({self.abbreviation})"
        return self.name

    def get_absolute_url(self):
        return reverse('organization:function_detail', kwargs={'pk': self.pk})
