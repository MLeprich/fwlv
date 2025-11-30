"""
Personnel Models
Stammdatenverwaltung Personal mit Qualifikationen
"""

from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator

from core.models.base import AuditedModel


class Person(AuditedModel):
    """
    Personal-Stammdaten
    Separate von User-Accounts - nicht jedes Personal hat zwingend einen Account
    """

    # Persönliche Daten
    first_name = models.CharField(max_length=100, verbose_name=_('Vorname'))
    last_name = models.CharField(max_length=100, verbose_name=_('Nachname'))

    personnel_number = models.CharField(
        max_length=20,
        unique=True,
        verbose_name=_('Personalnummer'),
        help_text=_('Eindeutige Personalnummer')
    )

    date_of_birth = models.DateField(
        null=True, blank=True,
        verbose_name=_('Geburtsdatum')
    )

    # Kontaktdaten
    email = models.EmailField(blank=True, verbose_name=_('E-Mail'))

    phone = models.CharField(
        max_length=50, blank=True,
        verbose_name=_('Telefon')
    )

    mobile = models.CharField(
        max_length=50, blank=True,
        verbose_name=_('Mobil')
    )

    # Adresse
    street = models.CharField(max_length=200, blank=True, verbose_name=_('Straße'))
    house_number = models.CharField(max_length=20, blank=True, verbose_name=_('Hausnummer'))
    postal_code = models.CharField(max_length=10, blank=True, verbose_name=_('PLZ'))
    city = models.CharField(max_length=100, blank=True, verbose_name=_('Stadt'))

    # Organisatorisch
    department = models.ForeignKey(
        'organization.Department',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='personnel',
        verbose_name=_('Abteilung'),
        help_text=_('z.B. Einsatzabteilung, Jugendfeuerwehr')
    )

    rank = models.CharField(
        max_length=100, blank=True,
        verbose_name=_('Dienstgrad'),
        help_text=_('z.B. Feuerwehrmann, Hauptfeuerwehrmann, Oberlöschmeister')
    )

    ACTIVITY_CHOICES = [
        ('fire_protection', _('Brandschutz')),
        ('day_service', _('Tagesdienst')),
        ('command_service', _('Führungsdienst')),
        ('intern', _('Praktikant')),
    ]

    activity = models.CharField(
        max_length=50,
        choices=ACTIVITY_CHOICES,
        blank=True,
        verbose_name=_('Tätigkeit'),
        help_text=_('Art der Tätigkeit bei der Feuerwehr')
    )

    function = models.CharField(
        max_length=100, blank=True,
        verbose_name=_('Funktion (deprecated)'),
        help_text=_('Veraltet - bitte "Funktionen" verwenden')
    )

    # Neue ManyToMany-Beziehung zu Funktionen
    functions = models.ManyToManyField(
        'organization.Function',
        blank=True,
        related_name='personnel',
        verbose_name=_('Funktionen'),
        help_text=_('z.B. Gruppenführer, Taucher, Atemschutzgeräteträger')
    )

    # ManyToMany-Beziehung zu Qualifikations-Vorlagen
    qualification_templates = models.ManyToManyField(
        'QualificationTemplate',
        blank=True,
        related_name='personnel',
        verbose_name=_('Qualifikations-Vorlagen'),
        help_text=_('Welche Qualifikationen sollte diese Person haben?')
    )

    # Zeitraum
    entry_date = models.DateField(
        null=True, blank=True,
        verbose_name=_('Eintrittsdatum')
    )

    exit_date = models.DateField(
        null=True, blank=True,
        verbose_name=_('Austrittsdatum')
    )

    # Status
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Aktiv'),
        help_text=_('Ist die Person aktiv im Dienst?')
    )

    # User-Verknüpfung (optional)
    user = models.OneToOneField(
        'core.User',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='person',
        verbose_name=_('Benutzer-Account'),
        help_text=_('Verknüpfter Benutzer-Account (optional)')
    )

    # Foto
    photo = models.ImageField(
        upload_to='personnel/photos/',
        null=True, blank=True,
        verbose_name=_('Foto')
    )

    # Dienstausweis-Foto (automatisch generiert aus photo)
    id_card_photo = models.ImageField(
        upload_to='personnel/id_cards/',
        null=True, blank=True,
        verbose_name=_('Dienstausweis-Foto'),
        help_text=_('Automatisch generiert: 35x45mm, 300 DPI')
    )

    # Organisationszugehörigkeit
    is_youth_fire_brigade = models.BooleanField(
        default=False,
        verbose_name=_('Jugendfeuerwehr'),
        help_text=_('Ist/war die Person in der Jugendfeuerwehr?')
    )

    youth_entry_date = models.DateField(
        null=True, blank=True,
        verbose_name=_('Eintritt Jugendfeuerwehr')
    )

    youth_exit_date = models.DateField(
        null=True, blank=True,
        verbose_name=_('Austritt Jugendfeuerwehr')
    )

    is_volunteer_fire_brigade = models.BooleanField(
        default=False,
        verbose_name=_('Freiwillige Feuerwehr'),
        help_text=_('Ist/war die Person in der Freiwilligen Feuerwehr?')
    )

    volunteer_entry_date = models.DateField(
        null=True, blank=True,
        verbose_name=_('Eintritt Freiwillige Feuerwehr')
    )

    volunteer_unit = models.ForeignKey(
        'organization.VolunteerUnit',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='volunteers',
        verbose_name=_('Einheit FF'),
        help_text=_('z.B. Löschzug 1, Löschgruppe Musterort')
    )

    is_professional_fire_brigade = models.BooleanField(
        default=False,
        verbose_name=_('Berufsfeuerwehr'),
        help_text=_('Ist die Person bei der Berufsfeuerwehr?')
    )

    professional_entry_date = models.DateField(
        null=True, blank=True,
        verbose_name=_('Eintritt Berufsfeuerwehr')
    )

    watch_crew = models.ForeignKey(
        'organization.WatchCrew',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='crew_members',
        verbose_name=_('Wachmannschaft'),
        help_text=_('z.B. A-Schicht Wache 1')
    )

    previous_fire_department = models.CharField(
        max_length=200, blank=True,
        verbose_name=_('Vorherige Feuerwehr'),
        help_text=_('Von welcher Feuerwehr kam die Person? (z.B. BF München)')
    )

    previous_fire_department_entry_date = models.DateField(
        null=True, blank=True,
        verbose_name=_('Eintritt vorherige Feuerwehr')
    )

    previous_fire_department_exit_date = models.DateField(
        null=True, blank=True,
        verbose_name=_('Austritt vorherige Feuerwehr')
    )

    # Notizen
    notes = models.TextField(blank=True, verbose_name=_('Notizen'))

    # Dienstliche Kontaktdaten
    work_phone = models.CharField(
        max_length=50, blank=True,
        verbose_name=_('Dienstliche Telefonnummer'),
        help_text=_('Dienstliche Festnetznummer')
    )

    work_mobile = models.CharField(
        max_length=50, blank=True,
        verbose_name=_('Dienstliche Handynummer'),
        help_text=_('Dienstliches Mobiltelefon')
    )

    work_location = models.ForeignKey(
        'locations.Location',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='stationed_personnel',
        verbose_name=_('Dienstlicher Standort'),
        help_text=_('Standort/Wache der Person')
    )

    work_room = models.CharField(
        max_length=100, blank=True,
        verbose_name=_('Raum/Büro'),
        help_text=_('z.B. Raum 203, Büro Wachleitung')
    )

    # Privatsphäre-Einstellungen
    show_private_contact_data = models.BooleanField(
        default=False,
        verbose_name=_('Private Kontaktdaten öffentlich'),
        help_text=_('Sollen private Kontaktdaten (Telefon, Mobil, Adresse) im Telefonbuch angezeigt werden?')
    )

    # Notfallkontakt
    emergency_contact_name = models.CharField(
        max_length=200, blank=True,
        verbose_name=_('Notfallkontakt Name'),
        help_text=_('Vollständiger Name des Notfallkontakts')
    )

    emergency_contact_relationship = models.CharField(
        max_length=100, blank=True,
        verbose_name=_('Beziehung'),
        help_text=_('z.B. Ehepartner, Elternteil, Geschwister')
    )

    emergency_contact_phone = models.CharField(
        max_length=50, blank=True,
        verbose_name=_('Telefon'),
        help_text=_('Telefonnummer des Notfallkontakts')
    )

    emergency_contact_mobile = models.CharField(
        max_length=50, blank=True,
        verbose_name=_('Mobil'),
        help_text=_('Mobilnummer des Notfallkontakts')
    )

    emergency_contact_address = models.TextField(
        blank=True,
        verbose_name=_('Adresse'),
        help_text=_('Vollständige Adresse des Notfallkontakts')
    )

    class Meta:
        verbose_name = _('Person')
        verbose_name_plural = _('Personal')
        ordering = ['last_name', 'first_name']
        indexes = [
            models.Index(fields=['personnel_number']),
            models.Index(fields=['last_name', 'first_name']),
            models.Index(fields=['is_active']),
            models.Index(fields=['department']),  # For filtering by department
            models.Index(fields=['entry_date']),  # For date-based queries
        ]

    def __str__(self):
        return f"{self.last_name}, {self.first_name} ({self.personnel_number})"

    def get_absolute_url(self):
        return reverse('personnel:detail', kwargs={'pk': self.pk})

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

    def get_address(self):
        """Vollständige Adresse"""
        parts = []
        if self.street:
            parts.append(f"{self.street} {self.house_number}".strip())
        if self.postal_code and self.city:
            parts.append(f"{self.postal_code} {self.city}")
        return ', '.join(parts) if parts else None

    def get_qualifications(self):
        """Aktive Qualifikationen"""
        return self.qualifications.filter(is_active=True)

    def get_expired_qualifications(self):
        """Abgelaufene Qualifikationen"""
        from django.utils import timezone
        return self.qualifications.filter(
            expiry_date__lt=timezone.now().date(),
            is_active=True
        )

    def get_years_of_service(self):
        """Berechnet die Gesamtdienstjahre basierend auf allen Organisationen"""
        from django.utils import timezone
        from dateutil.relativedelta import relativedelta

        today = timezone.now().date()
        total_days = 0

        # Jugendfeuerwehr
        if self.youth_entry_date:
            exit_date = self.youth_exit_date or today
            if exit_date > self.youth_entry_date:
                delta = exit_date - self.youth_entry_date
                total_days += delta.days

        # Vorherige Feuerwehr
        if self.previous_fire_department_entry_date:
            exit_date = self.previous_fire_department_exit_date
            if exit_date and exit_date > self.previous_fire_department_entry_date:
                delta = exit_date - self.previous_fire_department_entry_date
                total_days += delta.days

        # Freiwillige Feuerwehr
        if self.volunteer_entry_date:
            delta = today - self.volunteer_entry_date
            total_days += delta.days

        # Berufsfeuerwehr
        if self.professional_entry_date:
            delta = today - self.professional_entry_date
            total_days += delta.days

        # In Jahre umrechnen (ungefähr)
        years = total_days / 365.25
        return round(years, 1)

    def get_service_start_date(self):
        """Ermittelt das früheste Eintrittsdatum aller Organisationen"""
        dates = []
        if self.youth_entry_date:
            dates.append(self.youth_entry_date)
        if self.previous_fire_department_entry_date:
            dates.append(self.previous_fire_department_entry_date)
        if self.volunteer_entry_date:
            dates.append(self.volunteer_entry_date)
        if self.professional_entry_date:
            dates.append(self.professional_entry_date)

        return min(dates) if dates else None

    def get_upcoming_anniversaries(self):
        """Berechnet anstehende Jubiläen (10, 25, 40 Jahre)"""
        from django.utils import timezone

        start_date = self.get_service_start_date()
        if not start_date:
            return []

        today = timezone.now().date()
        service_years = self.get_years_of_service()

        anniversaries = []
        milestones = [10, 25, 40, 50, 60]

        for milestone in milestones:
            if service_years < milestone:
                # Berechne Datum des Jubiläums
                from dateutil.relativedelta import relativedelta
                anniversary_date = start_date + relativedelta(years=milestone)

                # Nur zukünftige oder aktuelle Jubiläen (innerhalb der nächsten 2 Jahre)
                days_until = (anniversary_date - today).days
                if 0 <= days_until <= 730:  # Nächste 2 Jahre
                    anniversaries.append({
                        'years': milestone,
                        'date': anniversary_date,
                        'days_until': days_until,
                        'is_upcoming': days_until <= 365  # Nächstes Jahr
                    })

        return anniversaries

    def get_current_organizations(self):
        """Gibt eine Liste der aktuellen Organisationszugehörigkeiten zurück"""
        orgs = []

        if self.is_youth_fire_brigade and not self.youth_exit_date:
            orgs.append({
                'name': 'Jugendfeuerwehr',
                'entry_date': self.youth_entry_date,
                'unit': None
            })

        if self.is_volunteer_fire_brigade:
            orgs.append({
                'name': 'Freiwillige Feuerwehr',
                'entry_date': self.volunteer_entry_date,
                'unit': self.volunteer_unit
            })

        if self.is_professional_fire_brigade:
            orgs.append({
                'name': 'Berufsfeuerwehr',
                'entry_date': self.professional_entry_date,
                'unit': self.department
            })

        return orgs


class QualificationType(models.Model):
    """
    Typen von Qualifikationen (verwaltbar)
    z.B. Lehrgang, Zertifikat, Führerschein/Lizenz
    """
    name = models.CharField(
        max_length=200,
        unique=True,
        verbose_name=_('Name'),
        help_text=_('z.B. Lehrgang, Zertifikat, Führerschein/Lizenz')
    )
    abbreviation = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_('Abkürzung'),
        help_text=_('z.B. LG, CERT, FS')
    )
    description = models.TextField(
        blank=True,
        verbose_name=_('Beschreibung')
    )
    color = models.CharField(
        max_length=7,
        default='#6366F1',
        verbose_name=_('Farbe'),
        help_text=_('Hex-Farbcode für Darstellung (z.B. #6366F1)')
    )
    icon = models.CharField(
        max_length=10,
        default='🎓',
        verbose_name=_('Icon'),
        help_text=_('Emoji-Icon für Darstellung')
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
        verbose_name = _('Qualifikationstyp')
        verbose_name_plural = _('Qualifikationstypen')
        ordering = ['sort_order', 'name']
        indexes = [
            models.Index(fields=['is_active', 'sort_order']),
        ]

    def __str__(self):
        if self.abbreviation:
            return f"{self.name} ({self.abbreviation})"
        return self.name


class QualificationTemplate(models.Model):
    """
    Vorlagen für Qualifikationen (wiederverwendbar)
    """
    name = models.CharField(
        max_length=200,
        unique=True,
        verbose_name=_('Bezeichnung'),
        help_text=_('z.B. Atemschutzgeräteträger, Truppmannausbildung Teil 1')
    )

    qualification_type = models.ForeignKey(
        'QualificationType',
        on_delete=models.PROTECT,
        related_name='templates',
        verbose_name=_('Typ')
    )

    description = models.TextField(
        blank=True,
        verbose_name=_('Beschreibung')
    )

    related_module = models.CharField(
        max_length=50,
        choices=[
            ('equipment', _('Ausrüstung')),
            ('diving', _('Taucher')),
            ('height_rescue', _('Höhenrettung')),
        ],
        blank=True,
        null=True,
        verbose_name=_('Zugeordnetes Modul'),
        help_text=_('Modul, zu dem diese Qualifikation gehört (z.B. Taucher, Höhenrettung, Ausrüstung)')
    )

    default_validity_days = models.PositiveIntegerField(
        null=True, blank=True,
        verbose_name=_('Standard-Gültigkeit (Tage)'),
        help_text=_('Standard-Gültigkeitsdauer in Tagen (z.B. 1095 für 3 Jahre). Leer lassen wenn unbefristet.')
    )

    default_issuing_authority = models.CharField(
        max_length=200, blank=True,
        verbose_name=_('Standard-Ausstellende Stelle'),
        help_text=_('z.B. Feuerwehrschule, TÜV')
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Aktiv'),
        help_text=_('Ist diese Vorlage aktiv und kann ausgewählt werden?')
    )

    required_duty_hour_categories = models.ManyToManyField(
        'DutyHoursCategory',
        blank=True,
        related_name='required_for_qualifications',
        verbose_name=_('Erforderliche Pflichtstunden-Kategorien'),
        help_text=_('Wählen Sie die Pflichtstunden-Kategorien aus, die für diese Qualifikation erforderlich sind')
    )

    notes = models.TextField(blank=True, verbose_name=_('Notizen'))

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Qualifikations-Vorlage')
        verbose_name_plural = _('Qualifikations-Vorlagen')
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return self.name


class Qualification(AuditedModel):
    """
    Qualifikationen/Lehrgänge/Zertifikate
    """

    person = models.ForeignKey(
        Person,
        on_delete=models.CASCADE,
        related_name='qualifications',
        verbose_name=_('Person')
    )

    template = models.ForeignKey(
        QualificationTemplate,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='qualifications',
        verbose_name=_('Vorlage'),
        help_text=_('Optional: Vorlage auswählen um Felder automatisch auszufüllen')
    )

    qualification_type = models.ForeignKey(
        'QualificationType',
        on_delete=models.PROTECT,
        related_name='qualifications',
        verbose_name=_('Typ')
    )

    name = models.CharField(
        max_length=200,
        verbose_name=_('Bezeichnung'),
        help_text=_('z.B. Atemschutzgeräteträger, Truppmannausbildung Teil 1')
    )

    description = models.TextField(
        blank=True,
        verbose_name=_('Beschreibung')
    )

    issuing_authority = models.CharField(
        max_length=200, blank=True,
        verbose_name=_('Ausstellende Stelle'),
        help_text=_('z.B. Feuerwehrschule, TÜV')
    )

    certificate_number = models.CharField(
        max_length=100, blank=True,
        verbose_name=_('Zertifikatsnummer')
    )

    issue_date = models.DateField(
        verbose_name=_('Ausstellungsdatum')
    )

    expiry_date = models.DateField(
        null=True, blank=True,
        verbose_name=_('Ablaufdatum'),
        help_text=_('Leer lassen wenn unbefristet')
    )

    # Dokumente
    certificate_file = models.FileField(
        upload_to='personnel/certificates/',
        null=True, blank=True,
        verbose_name=_('Zertifikat-Datei'),
        help_text=_('PDF, JPG oder PNG')
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Aktiv')
    )

    notes = models.TextField(blank=True, verbose_name=_('Notizen'))

    class Meta:
        verbose_name = _('Qualifikation')
        verbose_name_plural = _('Qualifikationen')
        ordering = ['-issue_date']
        indexes = [
            models.Index(fields=['person', 'is_active']),
            models.Index(fields=['expiry_date']),
        ]

    def __str__(self):
        return f"{self.person.get_full_name()} - {self.name}"

    def is_expired(self):
        """Prüft ob Qualifikation abgelaufen ist"""
        if not self.expiry_date:
            return False
        from django.utils import timezone
        return self.expiry_date < timezone.now().date()

    def is_expiring_soon(self, days=30):
        """Prüft ob Qualifikation bald abläuft"""
        if not self.expiry_date:
            return False
        from django.utils import timezone
        from datetime import timedelta
        return self.expiry_date <= timezone.now().date() + timedelta(days=days)


class TrainingStatus(models.TextChoices):
    """Status von Schulungen"""
    PLANNED = 'planned', _('Geplant')
    CONFIRMED = 'confirmed', _('Bestätigt')
    IN_PROGRESS = 'in_progress', _('Läuft')
    COMPLETED = 'completed', _('Abgeschlossen')
    CANCELLED = 'cancelled', _('Abgesagt')


class Training(AuditedModel):
    """
    Schulungen und Ausbildungsveranstaltungen
    """

    title = models.CharField(
        max_length=200,
        verbose_name=_('Titel'),
        help_text=_('z.B. Atemschutzgeräteträgerlehrgang, G26.3-Untersuchung')
    )

    description = models.TextField(
        blank=True,
        verbose_name=_('Beschreibung')
    )

    training_type = models.ForeignKey(
        'QualificationType',
        on_delete=models.PROTECT,
        related_name='trainings',
        verbose_name=_('Schulungstyp')
    )

    status = models.CharField(
        max_length=20,
        choices=TrainingStatus.choices,
        default=TrainingStatus.PLANNED,
        verbose_name=_('Status')
    )

    # Datum & Zeit
    start_date = models.DateField(
        verbose_name=_('Startdatum')
    )

    start_time = models.TimeField(
        null=True, blank=True,
        verbose_name=_('Startzeit')
    )

    end_date = models.DateField(
        null=True, blank=True,
        verbose_name=_('Enddatum'),
        help_text=_('Bei mehrtägigen Schulungen')
    )

    end_time = models.TimeField(
        null=True, blank=True,
        verbose_name=_('Endzeit')
    )

    # Ort
    location = models.CharField(
        max_length=200, blank=True,
        verbose_name=_('Veranstaltungsort'),
        help_text=_('z.B. Feuerwehrschule, Feuerwehrhaus')
    )

    # Organisator
    organizer = models.CharField(
        max_length=200, blank=True,
        verbose_name=_('Veranstalter'),
        help_text=_('z.B. Kreisfeuerwehrverband')
    )

    instructor = models.CharField(
        max_length=200, blank=True,
        verbose_name=_('Ausbilder/Dozent')
    )

    # Teilnehmer
    participants = models.ManyToManyField(
        Person,
        through='TrainingParticipant',
        related_name='trainings',
        verbose_name=_('Teilnehmer')
    )

    max_participants = models.PositiveIntegerField(
        null=True, blank=True,
        verbose_name=_('Max. Teilnehmer'),
        help_text=_('Maximale Teilnehmerzahl')
    )

    # Kosten
    cost_per_participant = models.DecimalField(
        max_digits=10, decimal_places=2,
        null=True, blank=True,
        verbose_name=_('Kosten pro Teilnehmer'),
        help_text=_('In Euro')
    )

    # Dokumente
    training_materials = models.FileField(
        upload_to='personnel/training_materials/',
        null=True, blank=True,
        verbose_name=_('Schulungsunterlagen')
    )

    notes = models.TextField(blank=True, verbose_name=_('Notizen'))

    class Meta:
        verbose_name = _('Schulung')
        verbose_name_plural = _('Schulungen')
        ordering = ['-start_date', '-start_time']
        indexes = [
            models.Index(fields=['start_date']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.title} ({self.start_date})"

    def get_absolute_url(self):
        return reverse('personnel:training_detail', kwargs={'pk': self.pk})

    def is_upcoming(self):
        """Prüft ob Schulung in der Zukunft liegt"""
        from django.utils import timezone
        return self.start_date >= timezone.now().date()

    def is_past(self):
        """Prüft ob Schulung in der Vergangenheit liegt"""
        from django.utils import timezone
        end = self.end_date or self.start_date
        return end < timezone.now().date()

    def get_participant_count(self):
        """Anzahl bestätigter Teilnehmer"""
        return self.trainingparticipant_set.filter(status='confirmed').count()

    def has_free_slots(self):
        """Prüft ob noch Plätze frei sind"""
        if not self.max_participants:
            return True
        return self.get_participant_count() < self.max_participants


class ParticipantStatus(models.TextChoices):
    """Status der Teilnahme"""
    REGISTERED = 'registered', _('Angemeldet')
    CONFIRMED = 'confirmed', _('Bestätigt')
    ATTENDED = 'attended', _('Teilgenommen')
    ABSENT = 'absent', _('Abwesend')
    CANCELLED = 'cancelled', _('Abgemeldet')


class TrainingParticipant(AuditedModel):
    """
    Teilnahme an Schulungen (Through-Model für M2M)
    """

    training = models.ForeignKey(
        Training,
        on_delete=models.CASCADE,
        verbose_name=_('Schulung')
    )

    person = models.ForeignKey(
        Person,
        on_delete=models.CASCADE,
        verbose_name=_('Person')
    )

    status = models.CharField(
        max_length=20,
        choices=ParticipantStatus.choices,
        default=ParticipantStatus.REGISTERED,
        verbose_name=_('Status')
    )

    registration_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Anmeldedatum')
    )

    # Bei erfolgreichem Abschluss
    passed = models.BooleanField(
        null=True, blank=True,
        verbose_name=_('Bestanden'),
        help_text=_('Hat die Person die Schulung erfolgreich abgeschlossen?')
    )

    certificate_issued = models.BooleanField(
        default=False,
        verbose_name=_('Zertifikat ausgestellt')
    )

    notes = models.TextField(blank=True, verbose_name=_('Notizen'))

    class Meta:
        verbose_name = _('Schulungsteilnahme')
        verbose_name_plural = _('Schulungsteilnahmen')
        unique_together = [['training', 'person']]
        ordering = ['person__last_name', 'person__first_name']

    def __str__(self):
        return f"{self.person.get_full_name()} - {self.training.title}"


class InspectionType(models.TextChoices):
    """Typen von Prüfungen"""
    MEDICAL = 'medical', _('Medizinische Untersuchung')
    FITNESS = 'fitness', _('Belastungsübung')
    EQUIPMENT = 'equipment', _('Gerätewartung')
    SKILL = 'skill', _('Leistungsnachweis')
    SAFETY = 'safety', _('Sicherheitsunterweisung')
    OTHER = 'other', _('Sonstiges')


class InspectionStatus(models.TextChoices):
    """Status von Prüfungen"""
    PENDING = 'pending', _('Anstehend')
    DUE_SOON = 'due_soon', _('Bald fällig')
    OVERDUE = 'overdue', _('Überfällig')
    COMPLETED = 'completed', _('Abgeschlossen')
    CANCELLED = 'cancelled', _('Abgesagt')


class Inspection(AuditedModel):
    """
    Prüfungen und Untersuchungen für Personal
    (z.B. G26.3, Atemschutz-Belastungsübung, Leistungsnachweis)
    """

    person = models.ForeignKey(
        Person,
        on_delete=models.CASCADE,
        related_name='inspections',
        verbose_name=_('Person')
    )

    inspection_type = models.CharField(
        max_length=20,
        choices=InspectionType.choices,
        default=InspectionType.MEDICAL,
        verbose_name=_('Prüfungstyp')
    )

    title = models.CharField(
        max_length=200,
        verbose_name=_('Bezeichnung'),
        help_text=_('z.B. G26.3, Atemschutz-Belastungsübung, Leistungsnachweis')
    )

    description = models.TextField(
        blank=True,
        verbose_name=_('Beschreibung')
    )

    # Termine
    scheduled_date = models.DateField(
        verbose_name=_('Geplantes Datum'),
        help_text=_('Wann soll die Prüfung stattfinden?')
    )

    completed_date = models.DateField(
        null=True, blank=True,
        verbose_name=_('Durchgeführt am')
    )

    next_inspection_date = models.DateField(
        null=True, blank=True,
        verbose_name=_('Nächste Prüfung'),
        help_text=_('Wann ist die nächste Prüfung fällig?')
    )

    # Intervall für automatische Wiedervorlage
    interval_months = models.PositiveIntegerField(
        null=True, blank=True,
        verbose_name=_('Intervall (Monate)'),
        help_text=_('z.B. 12 für jährliche Prüfung')
    )

    # Status
    status = models.CharField(
        max_length=20,
        choices=InspectionStatus.choices,
        default=InspectionStatus.PENDING,
        verbose_name=_('Status')
    )

    # Ergebnis
    passed = models.BooleanField(
        null=True, blank=True,
        verbose_name=_('Bestanden'),
        help_text=_('Hat die Person die Prüfung bestanden?')
    )

    result_notes = models.TextField(
        blank=True,
        verbose_name=_('Ergebnisnotizen')
    )

    # Prüfer
    examiner = models.CharField(
        max_length=200, blank=True,
        verbose_name=_('Prüfer/Arzt'),
        help_text=_('Wer hat die Prüfung durchgeführt?')
    )

    # Dokumente
    certificate_file = models.FileField(
        upload_to='personnel/inspections/',
        null=True, blank=True,
        verbose_name=_('Prüfungsdokument'),
        help_text=_('PDF, JPG oder PNG')
    )

    notes = models.TextField(blank=True, verbose_name=_('Notizen'))

    class Meta:
        verbose_name = _('Prüfung')
        verbose_name_plural = _('Prüfungen')
        ordering = ['-scheduled_date']
        indexes = [
            models.Index(fields=['person', 'status']),
            models.Index(fields=['scheduled_date']),
            models.Index(fields=['next_inspection_date']),
        ]

    def __str__(self):
        return f"{self.person.get_full_name()} - {self.title} ({self.scheduled_date})"

    def get_absolute_url(self):
        return reverse('personnel:inspection_detail', kwargs={'pk': self.pk})

    def is_overdue(self):
        """Prüft ob Prüfung überfällig ist"""
        if self.status == InspectionStatus.COMPLETED:
            return False
        from django.utils import timezone
        return self.scheduled_date < timezone.now().date()

    def is_due_soon(self, days=30):
        """Prüft ob Prüfung bald fällig ist"""
        if self.status == InspectionStatus.COMPLETED:
            return False
        from django.utils import timezone
        from datetime import timedelta
        return self.scheduled_date <= timezone.now().date() + timedelta(days=days)

    def update_status(self):
        """Aktualisiert Status basierend auf Datum"""
        if self.status == InspectionStatus.COMPLETED:
            return

        from django.utils import timezone
        from datetime import timedelta

        today = timezone.now().date()

        if self.scheduled_date < today:
            self.status = InspectionStatus.OVERDUE
        elif self.scheduled_date <= today + timedelta(days=30):
            self.status = InspectionStatus.DUE_SOON
        else:
            self.status = InspectionStatus.PENDING

    def save(self, *args, **kwargs):
        """Auto-update status on save"""
        if not self.completed_date:
            self.update_status()
        super().save(*args, **kwargs)


class DutyHoursCategory(models.Model):
    """
    Kategorien für Pflichtstunden (verwaltbar)
    z.B. Tauchen, Höhenrettung, Medizinische Fortbildung
    """
    name = models.CharField(
        max_length=200,
        unique=True,
        verbose_name=_('Name'),
        help_text=_('z.B. Tauchen, Höhenrettung, Medizinische Fortbildung')
    )
    abbreviation = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_('Abkürzung'),
        help_text=_('z.B. TAU, HR, MED')
    )
    description = models.TextField(
        blank=True,
        verbose_name=_('Beschreibung')
    )
    related_module = models.CharField(
        max_length=50,
        choices=[
            ('equipment', _('Ausrüstung')),
            ('diving', _('Taucher')),
            ('height_rescue', _('Höhenrettung')),
        ],
        blank=True,
        null=True,
        verbose_name=_('Zugeordnetes Modul'),
        help_text=_('Modul, zu dem diese Pflichtstunden-Kategorie gehört (z.B. Taucher, Höhenrettung, Ausrüstung)')
    )
    color = models.CharField(
        max_length=7,
        default='#6B7280',
        verbose_name=_('Farbe'),
        help_text=_('Hex-Farbcode für Darstellung (z.B. #3B82F6)')
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
        verbose_name = _('Pflichtstunden-Kategorie')
        verbose_name_plural = _('Pflichtstunden-Kategorien')
        ordering = ['sort_order', 'name']
        indexes = [
            models.Index(fields=['is_active', 'sort_order']),
        ]

    def __str__(self):
        if self.abbreviation:
            return f"{self.name} ({self.abbreviation})"
        return self.name


class DutyHoursEntry(AuditedModel):
    """
    Pflichtstunden-Erfassung
    (z.B. Tauchstunden, Höhenrettungsstunden, medizinische Fortbildung)
    """

    person = models.ForeignKey(
        Person,
        on_delete=models.CASCADE,
        related_name='duty_hours',
        verbose_name=_('Person')
    )

    category = models.ForeignKey(
        'DutyHoursCategory',
        on_delete=models.PROTECT,
        related_name='entries',
        verbose_name=_('Kategorie')
    )

    title = models.CharField(
        max_length=200,
        verbose_name=_('Bezeichnung'),
        help_text=_('z.B. Tauchgang, Übung am Turm, EKG-Kurs')
    )

    description = models.TextField(
        blank=True,
        verbose_name=_('Beschreibung')
    )

    # Datum & Dauer
    date = models.DateField(
        verbose_name=_('Datum')
    )

    hours = models.DecimalField(
        max_digits=5, decimal_places=2,
        verbose_name=_('Stunden'),
        help_text=_('Anzahl der geleisteten Stunden (z.B. 2.5)')
    )

    # Jahr für Reporting
    year = models.PositiveIntegerField(
        verbose_name=_('Jahr'),
        help_text=_('Wird automatisch aus Datum gesetzt')
    )

    # Trainer/Bestätigung
    supervisor = models.CharField(
        max_length=200, blank=True,
        verbose_name=_('Trainer/Vorgesetzter'),
        help_text=_('Wer hat die Stunden bestätigt?')
    )

    confirmed = models.BooleanField(
        default=False,
        verbose_name=_('Bestätigt'),
        help_text=_('Wurden die Stunden offiziell bestätigt?')
    )

    confirmed_date = models.DateField(
        null=True, blank=True,
        verbose_name=_('Bestätigt am')
    )

    # Dokumente
    certificate_file = models.FileField(
        upload_to='personnel/duty_hours/',
        null=True, blank=True,
        verbose_name=_('Nachweis'),
        help_text=_('Teilnahmebescheinigung, Logbuch-Eintrag, etc.')
    )

    notes = models.TextField(blank=True, verbose_name=_('Notizen'))

    class Meta:
        verbose_name = _('Pflichtstunden-Eintrag')
        verbose_name_plural = _('Pflichtstunden-Einträge')
        ordering = ['-date']
        indexes = [
            models.Index(fields=['person', 'category', 'year']),
            models.Index(fields=['date']),
            models.Index(fields=['confirmed']),
        ]

    def __str__(self):
        return f"{self.person.get_full_name()} - {self.title} ({self.hours}h)"

    def save(self, *args, **kwargs):
        """Auto-set year from date"""
        if self.date:
            self.year = self.date.year
        super().save(*args, **kwargs)


class DutyHoursRequirement(models.Model):
    """
    Pflichtstunden-Anforderungen pro Kategorie und Jahr
    """

    category = models.ForeignKey(
        'DutyHoursCategory',
        on_delete=models.PROTECT,
        related_name='requirements',
        verbose_name=_('Kategorie')
    )

    year = models.PositiveIntegerField(
        verbose_name=_('Jahr')
    )

    required_hours = models.DecimalField(
        max_digits=5, decimal_places=2,
        verbose_name=_('Erforderliche Stunden'),
        help_text=_('Anzahl der erforderlichen Stunden pro Jahr')
    )

    description = models.TextField(
        blank=True,
        verbose_name=_('Beschreibung'),
        help_text=_('Zusätzliche Informationen zur Anforderung')
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Aktiv')
    )

    class Meta:
        verbose_name = _('Pflichtstunden-Anforderung')
        verbose_name_plural = _('Pflichtstunden-Anforderungen')
        unique_together = [['category', 'year']]
        ordering = ['-year', 'category']
        indexes = [
            models.Index(fields=['year', 'is_active']),
        ]

    def __str__(self):
        return f"{self.category.name} {self.year}: {self.required_hours}h"
