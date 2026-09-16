"""
Dienstplan-Modul

Importiert Dienstplan-Exporte des Dienstplansystems (OC:Planner, CSV) und
hält je Person und Tag den Dienstcode vor. Die Bedeutung der Codes (A1-Dienst,
B-Dienst, Urlaub …) wird in einer pflegbaren Code-Tabelle hinterlegt, damit das
Info-Monitor-Widget daraus den Führungsdienst des Tages ableiten kann.
(Die Leitstellen-Anzeige bleibt vorerst manuell; Anbindung folgt später.)
"""
from django.conf import settings
from django.db import models
from django.utils import timezone


class DutyFunction(models.TextChoices):
    """Führungsdienst-Funktionen, auf die ein Dienstcode abgebildet werden kann"""
    A1 = 'a1', 'A1-Dienst'
    A2 = 'a2', 'A2-Dienst'
    B = 'b', 'B-Dienst'
    C = 'c', 'C-Dienst'
    LAGEDIENST = 'lagedienst', 'Lagedienst'
    LNA = 'lna', 'LNA'


class DutyKind(models.TextChoices):
    DUTY = 'duty', 'Dienst'
    OFFICE = 'office', 'Büro / Tagdienst'
    TRAINING = 'training', 'Lehrgang / Fortbildung'
    ABSENCE = 'absence', 'Abwesenheit'
    FREE = 'free', 'Frei'
    OTHER = 'other', 'Sonstiges'


class DutyColor(models.TextChoices):
    GRAY = 'gray', 'Grau'
    BLUE = 'blue', 'Blau'
    GREEN = 'green', 'Grün'
    YELLOW = 'yellow', 'Gelb'
    ORANGE = 'orange', 'Orange'
    RED = 'red', 'Rot'
    PURPLE = 'purple', 'Lila'


class DutyCode(models.Model):
    """Bedeutung eines Dienstcodes aus dem Dienstplan-Export"""
    code = models.CharField('Code', max_length=20, unique=True)
    label = models.CharField('Bezeichnung', max_length=100)
    kind = models.CharField('Art', max_length=20, choices=DutyKind.choices, default=DutyKind.OTHER)
    function = models.CharField(
        'Führungsdienst-Funktion', max_length=20, choices=DutyFunction.choices, blank=True, default='',
        help_text='Mit dieser Zuordnung wird der Code im Dienstplan-Widget der Info-Monitore '
                  'als Führungsdienst des Tages angezeigt'
    )
    color = models.CharField('Farbe', max_length=10, choices=DutyColor.choices, default=DutyColor.GRAY)
    show_on_monitor = models.BooleanField(
        'Auf Info-Monitor anzeigen', default=False,
        help_text='Im Dienstplan-Widget werden nur Codes mit diesem Haken aufgeführt'
    )
    verified = models.BooleanField(
        'Bedeutung geprüft', default=False,
        help_text='Vorbelegte Codes sind Vermutungen aus dem ersten Import; nach Prüfung Haken setzen'
    )
    sort_order = models.PositiveSmallIntegerField('Reihenfolge', default=100)

    class Meta:
        verbose_name = 'Dienstcode'
        verbose_name_plural = 'Dienstcodes'
        ordering = ['sort_order', 'code']

    def __str__(self):
        return f'{self.code} – {self.label}'

    @property
    def function_label(self):
        return DutyFunction(self.function).label if self.function else ''


class UploadStatus(models.TextChoices):
    PENDING = 'pending', 'Vorschau (noch nicht übernommen)'
    IMPORTED = 'imported', 'Aktueller Stand'
    REPLACED = 'replaced', 'Durch neueren Upload ersetzt'


def _upload_path(instance, filename):
    return f'dienstplan/{timezone.now():%Y/%m}/{filename}'


class RosterUpload(models.Model):
    """Ein hochgeladener Dienstplan-Export (CSV, optional mit PDF zur Anzeige)"""
    file = models.FileField('CSV-Datei', upload_to=_upload_path)
    pdf_file = models.FileField('PDF-Datei (optional)', upload_to=_upload_path, blank=True, null=True)
    original_name = models.CharField('Dateiname', max_length=255, blank=True)
    period_start = models.DateField('Zeitraum von')
    period_end = models.DateField('Zeitraum bis')
    month_label = models.CharField('Monat', max_length=50, blank=True)
    department = models.CharField('Fachabteilung', max_length=120, blank=True)
    plan_status = models.CharField('Zustand laut Export', max_length=50, blank=True,
                                   help_text='z.B. vorläufig oder genehmigt')
    status = models.CharField('Status', max_length=10, choices=UploadStatus.choices, default=UploadStatus.PENDING)
    person_count = models.PositiveIntegerField('Personen', default=0)
    warnings = models.TextField('Hinweise aus dem Import', blank=True)
    uploaded_at = models.DateTimeField('Hochgeladen am', auto_now_add=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='dienstplan_uploads', verbose_name='Hochgeladen von'
    )
    imported_at = models.DateTimeField('Übernommen am', null=True, blank=True)

    class Meta:
        verbose_name = 'Dienstplan-Upload'
        verbose_name_plural = 'Dienstplan-Uploads'
        ordering = ['-uploaded_at']
        indexes = [models.Index(fields=['status', 'period_start', 'period_end'])]

    def __str__(self):
        label = self.month_label or f'{self.period_start:%m/%Y}'
        return f'{label} ({self.get_status_display()})'

    @property
    def day_count(self):
        return (self.period_end - self.period_start).days + 1

    @property
    def warning_lines(self):
        return [line for line in self.warnings.splitlines() if line.strip()]


class RosterEntry(models.Model):
    """Dienstcode einer Person an einem Tag"""
    upload = models.ForeignKey(RosterUpload, on_delete=models.CASCADE, related_name='entries')
    date = models.DateField('Datum', db_index=True)
    person_name = models.CharField('Name', max_length=200)
    code = models.CharField('Code', max_length=20, blank=True)

    class Meta:
        verbose_name = 'Dienstplan-Eintrag'
        verbose_name_plural = 'Dienstplan-Einträge'
        ordering = ['date', 'person_name']
        constraints = [
            models.UniqueConstraint(fields=['upload', 'date', 'person_name'], name='dienstplan_entry_unique'),
        ]

    def __str__(self):
        return f'{self.date:%d.%m.%Y} {self.person_name}: {self.code or "–"}'
