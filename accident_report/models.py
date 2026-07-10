"""
Unfallbericht-Modelle (Accident Report)

Erfassung von Unfall-/Verletzungsmeldungen im Dienst (angelehnt an eine
Unfallanzeige an die Feuerwehr-Unfallkasse). Vorlage – kann bei Bedarf an
die konkrete Abfrage des Trägers angepasst werden.
"""

import os
from io import BytesIO
from PIL import Image
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from core.models.base import AuditedModel, TimeStampedModel


def accident_image_path(instance, filename):
    """Upload-Pfad für Bilder eines Unfallberichts."""
    number = getattr(instance.report, 'report_number', None) or 'misc'
    return f'accident_reports/{number}/{filename}'


def resize_image(image_file, max_size=(1920, 1080)):
    """Skaliert ein Bild auf eine maximale Größe (analog Ticketsystem)."""
    img = Image.open(image_file)
    if img.mode in ('RGBA', 'P'):
        img = img.convert('RGB')
    if img.width > max_size[0] or img.height > max_size[1]:
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
    output = BytesIO()
    img.save(output, format='JPEG', quality=85, optimize=True)
    output.seek(0)
    return output


class ActivityType(models.TextChoices):
    """Art der Tätigkeit zum Unfallzeitpunkt."""
    EINSATZ = 'einsatz', _('Einsatz')
    UEBUNG = 'uebung', _('Übung')
    AUSBILDUNG = 'ausbildung', _('Aus-/Fortbildung')
    DIENSTSPORT = 'dienstsport', _('Dienstsport')
    ARBEITSDIENST = 'arbeitsdienst', _('Arbeits-/Gerätedienst')
    VERANSTALTUNG = 'veranstaltung', _('Veranstaltung / Absicherung')
    ANFAHRT = 'anfahrt', _('An-/Rückfahrt zum Dienst')
    SONSTIGES = 'sonstiges', _('Sonstiges')


class Severity(models.TextChoices):
    """Schwere des Unfalls (Klassifizierung, kein Bearbeitungsstatus)."""
    LEICHT = 'leicht', _('Leichtverletzung')
    MELDEPFLICHTIG = 'meldepflichtig', _('Meldepflichtig (> 3 Tage AU)')
    SCHWER = 'schwer', _('Schwerer Unfall')
    TOD = 'tod', _('Tödlicher Unfall')


class AccidentReport(AuditedModel):
    """
    Ein einzelner Unfallbericht.

    Die verletzte Person kann entweder mit dem Personalstamm verknüpft
    (``injured_person``) **oder** als Freitext (``injured_name``) erfasst
    werden – so lassen sich auch externe/nicht im System geführte Personen
    dokumentieren.
    """

    # AuditedModel-Felder überschreiben: öffentliche (anonyme) Meldungen
    # haben keinen angemeldeten Benutzer.
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='accident_report_accidentreport_created',
        verbose_name=_('Erstellt von'),
        null=True,
        blank=True,
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='accident_report_accidentreport_updated',
        verbose_name=_('Aktualisiert von'),
        null=True,
        blank=True,
    )

    # -- Bericht ------------------------------------------------------------
    report_number = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
        verbose_name=_('Berichts-Nr.'),
    )
    severity = models.CharField(
        max_length=20,
        choices=Severity.choices,
        default=Severity.LEICHT,
        verbose_name=_('Schwere'),
    )

    # -- Melder (bei öffentlicher Meldung ohne Login) ----------------------
    reporter_first_name = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Melder – Vorname'),
    )
    reporter_last_name = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Melder – Nachname'),
    )
    reporter_contact = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Melder – Kontakt (Telefon / E-Mail)'),
    )

    # -- Verletzte / betroffene Person -------------------------------------
    injured_person = models.ForeignKey(
        'personnel.Person',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='accident_reports',
        verbose_name=_('Person (aus Personalstamm)'),
        help_text=_('Optional – bei Mitgliedern aus dem Personalstamm auswählen.'),
    )
    injured_name = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Name (falls extern / nicht im System)'),
    )
    injured_birthdate = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Geburtsdatum'),
    )
    injured_function = models.CharField(
        max_length=150,
        blank=True,
        verbose_name=_('Funktion / Dienstgrad'),
    )
    injured_contact = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Kontakt (Telefon / Anschrift)'),
    )

    # -- Unfalldaten --------------------------------------------------------
    accident_date = models.DateField(
        verbose_name=_('Unfalldatum'),
    )
    accident_time = models.TimeField(
        null=True,
        blank=True,
        verbose_name=_('Unfallzeit'),
    )
    location = models.CharField(
        max_length=250,
        verbose_name=_('Unfallort'),
    )
    activity_type = models.CharField(
        max_length=20,
        choices=ActivityType.choices,
        default=ActivityType.EINSATZ,
        verbose_name=_('Tätigkeit zum Unfallzeitpunkt'),
    )
    activity_detail = models.CharField(
        max_length=250,
        blank=True,
        verbose_name=_('Bezug (Einsatz-Nr. / Bezeichnung)'),
    )
    vehicle = models.ForeignKey(
        'vehicles.Vehicle',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='accident_reports',
        verbose_name=_('Beteiligtes Fahrzeug'),
    )

    # -- Hergang & Ursache --------------------------------------------------
    description = models.TextField(
        verbose_name=_('Unfallhergang'),
    )
    cause = models.TextField(
        blank=True,
        verbose_name=_('Unfallursache'),
    )

    # -- Verletzung ---------------------------------------------------------
    injury_type = models.CharField(
        max_length=250,
        blank=True,
        verbose_name=_('Art der Verletzung'),
    )
    body_part = models.CharField(
        max_length=250,
        blank=True,
        verbose_name=_('Betroffene Körperteile'),
    )
    first_aid_given = models.BooleanField(
        default=False,
        verbose_name=_('Erste Hilfe geleistet'),
    )
    first_aid_by = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Erste Hilfe durch'),
    )
    doctor_visited = models.BooleanField(
        default=False,
        verbose_name=_('Ärztliche Behandlung'),
    )
    doctor_hospital = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Arzt / Krankenhaus'),
    )
    incapacity_expected = models.BooleanField(
        default=False,
        verbose_name=_('Arbeitsunfähigkeit zu erwarten'),
    )

    # -- Zeugen & Meldung ---------------------------------------------------
    witnesses = models.TextField(
        blank=True,
        verbose_name=_('Zeugen (Name, Kontakt)'),
    )
    reported_to = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Gemeldet an'),
    )
    reported_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Meldedatum'),
    )
    notes = models.TextField(
        blank=True,
        verbose_name=_('Bemerkungen'),
    )

    class Meta:
        verbose_name = _('Unfallbericht')
        verbose_name_plural = _('Unfallberichte')
        ordering = ['-accident_date', '-created_at']
        indexes = [
            models.Index(fields=['report_number']),
            models.Index(fields=['accident_date']),
            models.Index(fields=['severity']),
        ]

    def __str__(self):
        return f'{self.report_number} – {self.injured_display}'

    def get_absolute_url(self):
        return reverse('accident_report:detail', kwargs={'pk': self.pk})

    def save(self, *args, **kwargs):
        if not self.report_number:
            self.report_number = self._generate_report_number()
        super().save(*args, **kwargs)

    @staticmethod
    def _generate_report_number():
        """Fortlaufende Nummer pro Jahr: UB-<Jahr>-<5-stellig>."""
        year = timezone.now().year
        prefix = f'UB-{year}-'
        last = (
            AccidentReport.objects
            .filter(report_number__startswith=prefix)
            .order_by('-report_number')
            .first()
        )
        if last:
            try:
                seq = int(last.report_number.rsplit('-', 1)[1]) + 1
            except (ValueError, IndexError):
                seq = 1
        else:
            seq = 1
        return f'{prefix}{seq:05d}'

    @property
    def injured_display(self):
        """Anzeigename der verletzten Person (Personalstamm oder Freitext)."""
        if self.injured_person:
            return self.injured_person.full_name
        return self.injured_name or _('Unbekannt')

    @property
    def reporter_display(self):
        """Name der meldenden Person (öffentliche Meldung) oder erfassender User."""
        name = f'{self.reporter_first_name} {self.reporter_last_name}'.strip()
        if name:
            return name
        if self.created_by:
            return self.created_by.get_full_name() or self.created_by.username
        return _('Unbekannt')

    @property
    def is_public_submission(self):
        """True, wenn der Bericht ohne angemeldeten Benutzer eingereicht wurde."""
        return self.created_by_id is None

    @property
    def severity_color(self):
        """Tailwind-Klassen für das Schwere-Badge."""
        return {
            Severity.LEICHT: 'bg-green-100 text-green-800',
            Severity.MELDEPFLICHTIG: 'bg-yellow-100 text-yellow-800',
            Severity.SCHWER: 'bg-orange-100 text-orange-800',
            Severity.TOD: 'bg-red-100 text-red-800',
        }.get(self.severity, 'bg-gray-100 text-gray-800')


class AccidentReportImage(TimeStampedModel):
    """Foto/Anhang zu einem Unfallbericht (Bild wird automatisch skaliert)."""

    report = models.ForeignKey(
        AccidentReport,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name=_('Unfallbericht'),
    )
    image = models.ImageField(
        upload_to=accident_image_path,
        verbose_name=_('Bild'),
    )
    caption = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Beschreibung'),
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='uploaded_accident_images',
        verbose_name=_('Hochgeladen von'),
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = _('Unfallbericht-Bild')
        verbose_name_plural = _('Unfallbericht-Bilder')
        ordering = ['created_at']

    def __str__(self):
        return f'Bild zu {self.report.report_number}'

    def save(self, *args, **kwargs):
        if self.image and hasattr(self.image.file, 'seek'):
            self.image.file.seek(0)
            resized = resize_image(self.image.file)
            new_name = os.path.splitext(self.image.name)[0] + '.jpg'
            self.image = InMemoryUploadedFile(
                resized, 'ImageField', new_name,
                'image/jpeg', resized.getbuffer().nbytes, None
            )
        super().save(*args, **kwargs)
