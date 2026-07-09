"""
Mängelwesen Models
Verwaltung von Mängeln an Räumen, Fahrzeugen und Ausrüstung
"""

from django.db import models
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse

from core.models.base import AuditedModel, TimeStampedModel


class DefectStatus(models.TextChoices):
    OPEN = 'open', 'Offen'
    IN_PROGRESS = 'in_progress', 'In Bearbeitung'
    RESOLVED = 'resolved', 'Behoben'
    CLOSED = 'closed', 'Geschlossen'


class DefectCategoryModel(TimeStampedModel):
    """Dynamische Mangel-Kategorie"""

    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Name",
    )
    icon = models.CharField(
        max_length=10,
        default='⚠️',
        verbose_name="Icon",
    )
    color = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Farbe",
        help_text="Tailwind-Farbklasse, z.B. 'red', 'blue'",
    )
    description = models.TextField(
        blank=True,
        verbose_name="Beschreibung",
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Aktiv",
    )
    sort_order = models.IntegerField(
        default=0,
        verbose_name="Sortierung",
    )
    app_label = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="App-Label",
        help_text="Django App-Label für Objekt-Lookup, z.B. 'vehicles'",
    )
    model_name = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Model-Name",
        help_text="Django Model-Name für Objekt-Lookup, z.B. 'vehicle'",
    )
    responsible_users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name='responsible_defect_categories',
        verbose_name="Zuständige Bearbeiter",
        help_text="Sachbearbeiter, die Mängel dieser Kategorie sehen/bearbeiten dürfen. "
                  "Leer = für alle Bearbeiter sichtbar (keine Einschränkung).",
    )

    class Meta:
        ordering = ['sort_order', 'name']
        verbose_name = 'Mangel-Kategorie'
        verbose_name_plural = 'Mangel-Kategorien'

    def __str__(self):
        return self.name


class Defect(AuditedModel):
    """Mangel-Meldung"""

    # Override AuditedModel fields to allow anonymous submissions
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='defect_management_defect_created',
        verbose_name="Erstellt von",
        null=True,
        blank=True,
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='defect_management_defect_updated',
        verbose_name="Aktualisiert von",
        null=True,
        blank=True,
    )

    # Anonyme Melder-Felder
    reporter_first_name = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Melder (Vorname)",
    )
    reporter_last_name = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Melder (Nachname)",
    )

    title = models.CharField(
        max_length=200,
        verbose_name="Titel",
    )
    description = models.TextField(
        verbose_name="Beschreibung",
    )
    category = models.ForeignKey(
        DefectCategoryModel,
        on_delete=models.PROTECT,
        verbose_name="Kategorie",
        related_name='defects',
    )

    # GenericForeignKey für Referenz auf beliebiges Objekt
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Objekttyp",
    )
    object_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Objekt-ID",
    )
    related_object = GenericForeignKey('content_type', 'object_id')

    status = models.CharField(
        max_length=20,
        choices=DefectStatus.choices,
        default=DefectStatus.OPEN,
        verbose_name="Status",
    )
    reported_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Gemeldet am",
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_defects',
        verbose_name="Zugewiesen an",
    )
    resolved_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Behoben am",
    )
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_defects',
        verbose_name="Behoben von",
    )
    resolution_notes = models.TextField(
        blank=True,
        verbose_name="Behebungsnotiz",
    )

    class Meta:
        verbose_name = 'Mangel'
        verbose_name_plural = 'Mängel'
        ordering = ['-reported_date']
        permissions = [
            ('assign_defect', 'Kann Mängel zuweisen'),
        ]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('defect_management:detail', kwargs={'pk': self.pk})

    def get_related_object_display(self):
        """Anzeigename des verknüpften Objekts"""
        if self.related_object:
            return str(self.related_object)
        return '-'

    def get_status_color(self):
        """CSS-Farbe für Status-Badge"""
        colors = {
            DefectStatus.OPEN: 'red',
            DefectStatus.IN_PROGRESS: 'yellow',
            DefectStatus.RESOLVED: 'green',
            DefectStatus.CLOSED: 'gray',
        }
        return colors.get(self.status, 'gray')


class DefectPhoto(TimeStampedModel):
    """Foto zu einem Mangel"""

    defect = models.ForeignKey(
        Defect,
        on_delete=models.CASCADE,
        related_name='photos',
        verbose_name="Mangel",
    )
    image = models.ImageField(
        upload_to='defect_management/%Y/%m/',
        verbose_name="Foto",
    )
    description = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Beschreibung",
    )

    class Meta:
        verbose_name = 'Mangel-Foto'
        verbose_name_plural = 'Mangel-Fotos'

    def __str__(self):
        return f"Foto zu {self.defect.title}"


class DefectComment(AuditedModel):
    """Kommentar zu einem Mangel"""

    defect = models.ForeignKey(
        Defect,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name="Mangel",
    )
    text = models.TextField(
        verbose_name="Kommentar",
    )
    is_status_change = models.BooleanField(
        default=False,
        verbose_name="Status-Änderung",
        help_text="Automatischer Eintrag bei Status-Änderung",
    )

    class Meta:
        verbose_name = 'Mangel-Kommentar'
        verbose_name_plural = 'Mangel-Kommentare'
        ordering = ['created_at']

    def __str__(self):
        return f"Kommentar zu {self.defect.title}"
