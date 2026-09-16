"""
Termine-Modul: zentraler Kalender der Feuerwehr.

Termine mit Kategorie, optionaler Uhrzeit, Ort und Wiederholung. Sie sind
für alle angemeldeten Benutzer sichtbar und erscheinen über das Widget
„Kalender“ auf den Info-Monitoren. Optional lassen sich Termine Wachen
zuordnen, damit Listen und Monitore danach filtern können.
"""
from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse

from core.models import AuditedModel


class EventColor(models.TextChoices):
    GRAY = 'gray', 'Grau'
    BLUE = 'blue', 'Blau'
    GREEN = 'green', 'Grün'
    YELLOW = 'yellow', 'Gelb'
    ORANGE = 'orange', 'Orange'
    RED = 'red', 'Rot'
    PURPLE = 'purple', 'Lila'


class EventCategory(models.Model):
    name = models.CharField('Name', max_length=100, unique=True)
    color = models.CharField('Farbe', max_length=10, choices=EventColor.choices, default=EventColor.GRAY)
    icon = models.CharField('Symbol', max_length=8, blank=True, help_text='Emoji, z.B. 🚒')
    sort_order = models.PositiveSmallIntegerField('Reihenfolge', default=100)
    is_active = models.BooleanField('Aktiv', default=True)

    class Meta:
        verbose_name = 'Terminkategorie'
        verbose_name_plural = 'Terminkategorien'
        ordering = ['sort_order', 'name']

    def __str__(self):
        return self.name


class Recurrence(models.TextChoices):
    NONE = 'none', 'Einmalig'
    WEEKLY = 'weekly', 'Wöchentlich'
    BIWEEKLY = 'biweekly', 'Alle zwei Wochen'
    MONTHLY = 'monthly', 'Monatlich (gleicher Tag)'
    YEARLY = 'yearly', 'Jährlich'


class Event(AuditedModel):
    title = models.CharField('Titel', max_length=200)
    category = models.ForeignKey(EventCategory, on_delete=models.PROTECT, related_name='events', verbose_name='Kategorie')
    start_date = models.DateField('Beginn (Datum)', db_index=True)
    end_date = models.DateField('Ende (Datum)', null=True, blank=True, help_text='Leer = eintägig')
    all_day = models.BooleanField('Ganztägig', default=True)
    start_time = models.TimeField('Beginn (Uhrzeit)', null=True, blank=True)
    end_time = models.TimeField('Ende (Uhrzeit)', null=True, blank=True)
    location = models.CharField('Ort', max_length=200, blank=True)
    description = models.TextField('Beschreibung', blank=True)
    sites = models.ManyToManyField(
        'locations.Location', blank=True, related_name='termine', verbose_name='Wachen',
        limit_choices_to={'location_type': 'site'},
        help_text='Optional: nur für bestimmte Wachen relevant (Filter für Listen und Monitore)'
    )
    recurrence = models.CharField('Wiederholung', max_length=10, choices=Recurrence.choices, default=Recurrence.NONE)
    recurrence_until = models.DateField('Wiederholen bis', null=True, blank=True,
                                        help_text='Leer = bis zu zwei Jahre ab Beginn')
    show_on_monitor = models.BooleanField('Auf Info-Monitoren anzeigen', default=True)
    is_public = models.BooleanField(
        'Auch auf öffentlichen Monitoren', default=False,
        help_text='Öffentliche Info-Monitore sind ohne Anmeldung abrufbar'
    )
    uid = models.CharField('ICS-UID', max_length=255, blank=True, db_index=True,
                           help_text='Kennung aus einem ICS-Import (für erneuten Import)')

    class Meta:
        verbose_name = 'Termin'
        verbose_name_plural = 'Termine'
        ordering = ['start_date', 'start_time', 'title']
        permissions = [
            ('termine_view', 'Termine: Kalender ansehen'),
            ('termine_edit', 'Termine: anlegen und bearbeiten'),
            ('termine_manage', 'Termine: löschen, Kategorien und Import verwalten'),
        ]

    def __str__(self):
        return f'{self.start_date:%d.%m.%Y} {self.title}'

    def clean(self):
        if self.end_date and self.end_date < self.start_date:
            raise ValidationError({'end_date': 'Das Ende liegt vor dem Beginn.'})
        if not self.all_day and not self.start_time:
            raise ValidationError({'start_time': 'Bitte eine Uhrzeit angeben oder „Ganztägig“ wählen.'})
        if self.recurrence_until and self.recurrence_until < self.start_date:
            raise ValidationError({'recurrence_until': 'Das Wiederholungsende liegt vor dem Beginn.'})

    def save(self, *args, **kwargs):
        if self.all_day:
            self.start_time = None
            self.end_time = None
        if self.end_date == self.start_date:
            self.end_date = None
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('termine:event_detail', kwargs={'pk': self.pk})

    @property
    def duration_days(self):
        return ((self.end_date or self.start_date) - self.start_date).days + 1

    @property
    def last_date(self):
        return self.end_date or self.start_date

    @property
    def time_display(self):
        if self.all_day:
            return 'ganztägig'
        if self.end_time:
            return f'{self.start_time:%H:%M}–{self.end_time:%H:%M} Uhr'
        return f'{self.start_time:%H:%M} Uhr'

    @property
    def is_recurring(self):
        return self.recurrence != Recurrence.NONE

    def recurrence_end(self):
        return self.recurrence_until or (self.start_date + timedelta(days=730))
