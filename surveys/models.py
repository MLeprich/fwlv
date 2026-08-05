"""
Umfragen Models
Formularbasiertes Umfrage-Modul mit wahlweise anonymer oder personalisierter Teilnahme.

WICHTIG ZUR ANONYMITÄT
----------------------
Bei `Survey.is_anonymous = True` darf zwischen einer Antwort und der Person, die sie
abgegeben hat, KEINE Verbindung existieren – auch nicht auf Datenbankebene. Deshalb:

1. `SurveyResponse` erbt bewusst NICHT von `AuditedModel`/`TimeStampedModel`.
   `AuditedModel` würde ein Pflichtfeld `created_by` erzwingen und die Anonymität
   sofort aushebeln.
2. Die Teilnahme wird getrennt in `SurveyParticipation` festgehalten. Diese Tabelle
   hat keinerlei Bezug zu `SurveyResponse`.
3. Zeitstempel sind bei anonymen Umfragen bewusst nur tagesgenau (siehe
   `SurveyResponse.submitted_at` und `SurveyParticipation.participated_on`).
   Sekundengenaue Zeitstempel in beiden Tabellen ließen sich sonst zu einer
   Zuordnung Person -> Antwort joinen.
4. In den Views darf für Antworten kein `audit.utils.log_create()` aufgerufen und
   keine IP-Adresse gespeichert werden.
"""

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone

from core.models.base import AuditedModel


class SurveyStatus(models.TextChoices):
    """Lebenszyklus einer Umfrage"""
    DRAFT = 'draft', 'Entwurf'
    ACTIVE = 'active', 'Aktiv'
    CLOSED = 'closed', 'Geschlossen'


class SurveyAccessMode(models.TextChoices):
    """
    Wie gelangen Teilnehmende zur Umfrage?

    LOGIN: ein gemeinsamer Link, Identität kommt aus dem Benutzerkonto. Doppelte
           Teilnahme verhindert `SurveyParticipation`. Nur so ist auswertbar, wer
           noch fehlt.
    TOKEN: N Einmal-Links, die als QR-Zettel verteilt werden. Funktioniert ohne
           Benutzerkonto. Bei anonymen Umfragen sind die Tokens bewusst KEINER
           Person zugeordnet – damit entfällt die Übersicht über Fehlende.
    """
    LOGIN = 'login', 'Über Login (Zielgruppe)'
    TOKEN = 'token', 'Über Einmal-Links (QR-Zettel)'


class QuestionType(models.TextChoices):
    """Verfügbare Fragetypen"""
    TEXT = 'text', 'Kurztext'
    TEXTAREA = 'textarea', 'Langtext'
    RADIO = 'radio', 'Einzelauswahl'
    CHECKBOX = 'checkbox', 'Mehrfachauswahl'
    SELECT = 'select', 'Dropdown'
    SCALE = 'scale', 'Skala'
    YESNO = 'yesno', 'Ja/Nein'
    NUMBER = 'number', 'Zahl'
    DATE = 'date', 'Datum'


#: Fragetypen, die eine Optionsliste in `config['options']` benötigen
CHOICE_TYPES = {QuestionType.RADIO, QuestionType.CHECKBOX, QuestionType.SELECT}

#: Fragetypen, die sich sinnvoll als Diagramm auswerten lassen
CHARTABLE_TYPES = CHOICE_TYPES | {QuestionType.SCALE, QuestionType.YESNO}

#: Fragetypen, die als Bezugsfrage einer Bedingung taugen (feste Antwortmöglichkeiten)
CONDITION_SOURCE_TYPES = CHARTABLE_TYPES


class Survey(AuditedModel):
    """
    Eine Umfrage mit beliebig vielen Fragen.

    Der Modus (anonym / personalisiert) wird pro Umfrage festgelegt und ist nach der
    ersten Antwort nicht mehr änderbar – sonst wäre die Zusage der Anonymität
    rückwirkend gebrochen.
    """

    title = models.CharField(
        max_length=200,
        verbose_name="Titel",
    )
    description = models.TextField(
        blank=True,
        verbose_name="Beschreibung",
        help_text="Einleitungstext, der den Teilnehmenden vor der ersten Frage angezeigt wird",
    )
    status = models.CharField(
        max_length=20,
        choices=SurveyStatus.choices,
        default=SurveyStatus.DRAFT,
        verbose_name="Status",
    )

    # ------------------------------------------------------------------
    # Anonymität
    # ------------------------------------------------------------------
    is_anonymous = models.BooleanField(
        default=True,
        verbose_name="Anonyme Umfrage",
        help_text=(
            "Ja: Die Antworten werden ohne Personenbezug gespeichert. Es wird lediglich "
            "getrennt vermerkt, WER teilgenommen hat – nicht WAS er geantwortet hat. "
            "Nein: Die Antworten sind der Person zugeordnet und in der Auswertung sichtbar."
        ),
    )
    min_responses_for_results = models.PositiveIntegerField(
        default=5,
        verbose_name="Auswertung erst ab X Antworten",
        help_text=(
            "Schutz vor Rückschlüssen bei kleinen Gruppen. Solange weniger Antworten "
            "vorliegen, bleibt die Auswertung gesperrt. 0 = keine Sperre."
        ),
    )

    # ------------------------------------------------------------------
    # Laufzeit & Teilnahme
    # ------------------------------------------------------------------
    start_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Startzeitpunkt",
        help_text="Leer = ab Freischaltung",
    )
    end_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Endzeitpunkt",
        help_text="Leer = kein automatisches Ende",
    )
    access_mode = models.CharField(
        max_length=20,
        choices=SurveyAccessMode.choices,
        default=SurveyAccessMode.LOGIN,
        verbose_name="Zugang",
        help_text=(
            "Login: gemeinsamer Link, Teilnahme über das Benutzerkonto – zeigt an, wer "
            "noch fehlt. Einmal-Links: QR-Zettel zum Verteilen, funktioniert ohne Konto."
        ),
    )
    pdf_intro_text = models.TextField(
        blank=True,
        verbose_name="Anschreiben für die QR-Zettel",
        help_text="Freier Text, der auf jedem ausgedruckten Zettel über dem QR-Code steht",
    )
    target_groups = models.ManyToManyField(
        'auth.Group',
        blank=True,
        related_name='surveys',
        verbose_name="Zielgruppe",
        help_text="Nur Mitglieder dieser Rollen dürfen teilnehmen. Leer = alle Benutzer.",
    )
    allow_multiple_responses = models.BooleanField(
        default=False,
        verbose_name="Mehrfachteilnahme erlauben",
        help_text="Erlaubt es, die Umfrage mehrfach auszufüllen (z.B. für wiederkehrende Meldungen)",
    )
    show_results_to_participants = models.BooleanField(
        default=False,
        verbose_name="Ergebnisse für Teilnehmende sichtbar",
        help_text="Teilnehmende sehen nach dem Absenden die (aggregierte) Auswertung",
    )

    class Meta:
        verbose_name = "Umfrage"
        verbose_name_plural = "Umfragen"
        ordering = ['-created_at']
        permissions = [
            ('conduct_survey', 'Kann Umfragen erstellen und auswerten'),
            ('participate_survey', 'Kann an Umfragen teilnehmen'),
        ]
        indexes = [
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('surveys:detail', kwargs={'pk': self.pk})

    # ------------------------------------------------------------------
    # Zustand
    # ------------------------------------------------------------------
    @property
    def is_open(self):
        """Läuft die Umfrage aktuell (Status + Zeitfenster)?"""
        if self.status != SurveyStatus.ACTIVE:
            return False
        now = timezone.now()
        if self.start_date and now < self.start_date:
            return False
        if self.end_date and now > self.end_date:
            return False
        return True

    @property
    def is_locked(self):
        """
        Sind die Grundeinstellungen gesperrt?

        Sobald die erste Antwort vorliegt, dürfen Anonymitätsmodus und Fragen nicht
        mehr geändert werden – sonst passen Antworten und Fragen nicht mehr zusammen.
        """
        return self.responses.exists()

    @property
    def response_count(self):
        return self.responses.filter(is_complete=True).count()

    @property
    def results_unlocked(self):
        """Ist die Mindest-Fallzahl für die Auswertung erreicht?"""
        if not self.min_responses_for_results:
            return True
        return self.response_count >= self.min_responses_for_results

    # ------------------------------------------------------------------
    # Teilnahme-Prüfungen
    # ------------------------------------------------------------------
    def is_in_target_group(self, user):
        """Gehört der User zur Zielgruppe? Keine Zielgruppe = alle."""
        if not self.target_groups.exists():
            return True
        return self.target_groups.filter(
            pk__in=user.groups.values_list('pk', flat=True)
        ).exists()

    def has_participated(self, user):
        """
        Hat der User bereits teilgenommen?

        Wird IMMER über `SurveyParticipation` beantwortet – auch bei personalisierten
        Umfragen –, damit es nur einen Code-Pfad gibt.
        """
        if not user.is_authenticated:
            return False
        return self.participations.filter(user=user).exists()

    @property
    def is_token_mode(self):
        return self.access_mode == SurveyAccessMode.TOKEN

    def can_participate(self, user):
        """
        Darf der User über den regulären Login-Weg teilnehmen?
        Gibt (bool, Begründung) zurück.
        """
        if self.is_token_mode:
            # Sonst ließe sich der Einmal-Link umgehen und mehrfach abstimmen.
            return False, "Für diese Umfrage ist ein persönlicher Zugangs-Link nötig."
        if not user.is_authenticated:
            return False, "Bitte melden Sie sich an."
        if not user.has_perm('surveys.participate_survey') and not user.has_perm('surveys.conduct_survey'):
            return False, "Sie haben keine Berechtigung, an Umfragen teilzunehmen."
        if not self.is_open:
            return False, "Diese Umfrage ist derzeit nicht geöffnet."
        if not self.questions.exists():
            return False, "Diese Umfrage enthält noch keine Fragen."
        if not self.is_in_target_group(user):
            return False, "Diese Umfrage richtet sich an eine andere Zielgruppe."
        if self.has_participated(user) and not self.allow_multiple_responses:
            return False, "Sie haben an dieser Umfrage bereits teilgenommen."
        return True, ""

    def can_view_results(self, user):
        """Darf der User die Auswertung sehen?"""
        if user.has_perm('surveys.conduct_survey'):
            return True
        return self.show_results_to_participants and self.has_participated(user)


class SurveyQuestion(models.Model):
    """
    Eine einzelne Frage innerhalb einer Umfrage.

    Typspezifische Einstellungen liegen in `config`:
      - Auswahltypen: {"options": ["A", "B", "C"]}
      - Skala:        {"min": 1, "max": 5, "min_label": "trifft nicht zu",
                       "max_label": "trifft voll zu"}
      - Zahl:         {"min": 0, "max": 100}
    """

    survey = models.ForeignKey(
        Survey,
        on_delete=models.CASCADE,
        related_name='questions',
        verbose_name="Umfrage",
    )
    order = models.PositiveIntegerField(
        default=0,
        verbose_name="Reihenfolge",
    )
    question_type = models.CharField(
        max_length=20,
        choices=QuestionType.choices,
        default=QuestionType.TEXT,
        verbose_name="Fragetyp",
    )
    text = models.CharField(
        max_length=500,
        verbose_name="Frage",
    )
    help_text = models.CharField(
        max_length=300,
        blank=True,
        verbose_name="Hilfetext",
        help_text="Optionale Erläuterung unterhalb der Frage",
    )
    is_required = models.BooleanField(
        default=True,
        verbose_name="Pflichtfrage",
    )
    config = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Konfiguration",
        help_text="Typspezifische Einstellungen (Optionen, Skalenbereich, ...)",
    )

    # ------------------------------------------------------------------
    # Bedingte Anzeige (Sprunglogik)
    # ------------------------------------------------------------------
    # Die Bezugsfrage muss VOR dieser Frage stehen – sonst wäre sie beim Auswerten
    # der Bedingung noch unbeantwortet. Das erzwingt zugleich, dass keine Zyklen
    # entstehen können.
    condition_question = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='dependent_questions',
        verbose_name="Bezugsfrage",
        help_text="Diese Frage nur anzeigen, wenn die Bezugsfrage passend beantwortet wurde",
    )
    condition_operator = models.CharField(
        max_length=10,
        choices=[
            ('any_of', 'eine der gewählten Antworten'),
            ('none_of', 'keine der gewählten Antworten'),
        ],
        default='any_of',
        blank=True,
        verbose_name="Bedingung",
    )
    condition_values = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Auslösende Antworten",
        help_text="Bei welchen Antworten der Bezugsfrage soll diese Frage erscheinen?",
    )

    class Meta:
        verbose_name = "Frage"
        verbose_name_plural = "Fragen"
        ordering = ['order', 'pk']

    def __str__(self):
        return f"{self.order + 1}. {self.text}"

    # ------------------------------------------------------------------
    # Konfigurations-Zugriff (immer über diese Properties, nie direkt auf config)
    # ------------------------------------------------------------------
    @property
    def options(self):
        """Antwortoptionen für Auswahltypen"""
        options = self.config.get('options') or []
        return [str(o) for o in options if str(o).strip()]

    @property
    def scale_min(self):
        try:
            return int(self.config.get('min', 1))
        except (TypeError, ValueError):
            return 1

    @property
    def scale_max(self):
        try:
            return int(self.config.get('max', 5))
        except (TypeError, ValueError):
            return 5

    @property
    def scale_range(self):
        """Werte der Skala als Liste – für Template und Auswertung"""
        low, high = self.scale_min, self.scale_max
        if high <= low:
            high = low + 1
        # Sicherheitsnetz gegen absurd große Skalen aus manipulierten Daten
        high = min(high, low + 20)
        return list(range(low, high + 1))

    @property
    def min_label(self):
        return self.config.get('min_label', '')

    @property
    def max_label(self):
        return self.config.get('max_label', '')

    @property
    def needs_options(self):
        return self.question_type in CHOICE_TYPES

    @property
    def has_condition(self):
        return bool(self.condition_question_id and self.condition_values)

    @property
    def condition_description(self):
        """Bedingung als lesbarer Satz – für den Builder"""
        from .conditions import describe_condition

        return describe_condition(self)

    @property
    def can_be_condition_source(self):
        """
        Taugt diese Frage als Bezugsfrage?

        Nur Fragen mit festen Antwortmöglichkeiten – bei Freitext oder Zahlen gäbe es
        keine sinnvoll auswählbare Bedingung.
        """
        return self.question_type in CONDITION_SOURCE_TYPES

    @property
    def is_chartable(self):
        """Lässt sich die Frage als Diagramm darstellen?"""
        return self.question_type in CHARTABLE_TYPES

    def chart_categories(self):
        """Alle möglichen Antwortkategorien in fester Reihenfolge"""
        if self.question_type in CHOICE_TYPES:
            return self.options
        if self.question_type == QuestionType.SCALE:
            return [str(v) for v in self.scale_range]
        if self.question_type == QuestionType.YESNO:
            return ['Ja', 'Nein']
        return []


class SurveyResponse(models.Model):
    """
    Ein ausgefüllter Fragebogen.

    ACHTUNG: Erbt bewusst NICHT von TimeStampedModel/AuditedModel – siehe Modul-Docstring.
    `user` bleibt bei anonymen Umfragen zwingend leer.
    """

    survey = models.ForeignKey(
        Survey,
        on_delete=models.CASCADE,
        related_name='responses',
        verbose_name="Umfrage",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='survey_responses',
        verbose_name="Teilnehmer",
        help_text="Bleibt bei anonymen Umfragen leer",
    )
    submitted_at = models.DateTimeField(
        verbose_name="Abgesendet am",
        help_text=(
            "Bei anonymen Umfragen bewusst nur tagesgenau gespeichert, damit sich "
            "Antworten nicht über den Zeitpunkt einer Person zuordnen lassen."
        ),
    )
    is_complete = models.BooleanField(
        default=True,
        verbose_name="Vollständig",
    )

    class Meta:
        verbose_name = "Antwort"
        verbose_name_plural = "Antworten"
        ordering = ['pk']
        indexes = [
            models.Index(fields=['survey', 'is_complete']),
        ]

    def __str__(self):
        if self.user_id:
            return f"Antwort von {self.user} zu '{self.survey}'"
        return f"Anonyme Antwort zu '{self.survey}'"

    def save(self, *args, **kwargs):
        # Doppelte Absicherung: Bei anonymen Umfragen niemals einen Personenbezug
        # speichern, egal was der aufrufende Code übergibt.
        is_anonymous = self.survey_id and self.survey.is_anonymous
        if is_anonymous:
            self.user = None
        if not self.submitted_at:
            self.submitted_at = timezone.now()
        if is_anonymous:
            self.submitted_at = self._truncate_to_day(self.submitted_at)
        super().save(*args, **kwargs)

    @staticmethod
    def _truncate_to_day(value):
        """Zeitstempel auf Tagesbeginn zurückschneiden (lokale Zeitzone)"""
        local = timezone.localtime(value) if timezone.is_aware(value) else value
        return local.replace(hour=0, minute=0, second=0, microsecond=0)


class SurveyAnswer(models.Model):
    """
    Die Antwort auf genau eine Frage.

    Bewusst eigene Zeilen statt eines JSON-Blobs pro Fragebogen: Auswertung und Export
    funktionieren so per ORM-Aggregation identisch auf SQLite (dev) und PostgreSQL (prod).
    """

    response = models.ForeignKey(
        SurveyResponse,
        on_delete=models.CASCADE,
        related_name='answers',
        verbose_name="Fragebogen",
    )
    question = models.ForeignKey(
        SurveyQuestion,
        on_delete=models.CASCADE,
        related_name='answers',
        verbose_name="Frage",
    )

    value_text = models.TextField(
        blank=True,
        verbose_name="Textantwort",
    )
    value_number = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Zahlenantwort",
    )
    value_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Datumsantwort",
    )
    value_json = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Mehrfachauswahl",
    )

    class Meta:
        verbose_name = "Einzelantwort"
        verbose_name_plural = "Einzelantworten"
        ordering = ['question__order', 'pk']
        constraints = [
            models.UniqueConstraint(
                fields=['response', 'question'],
                name='unique_answer_per_question',
            ),
        ]

    def __str__(self):
        return f"{self.question.text}: {self.display_value}"

    @property
    def display_value(self):
        """Menschenlesbare Darstellung – für Detailansicht und Export"""
        qtype = self.question.question_type
        if qtype == QuestionType.CHECKBOX:
            return ', '.join(str(v) for v in (self.value_json or []))
        if qtype == QuestionType.YESNO:
            if self.value_number is None:
                return ''
            return 'Ja' if int(self.value_number) == 1 else 'Nein'
        if qtype in (QuestionType.SCALE, QuestionType.NUMBER):
            if self.value_number is None:
                return ''
            # Ganzzahlen ohne Nachkommastellen ausgeben
            as_int = int(self.value_number)
            return str(as_int) if self.value_number == as_int else str(self.value_number)
        if qtype == QuestionType.DATE:
            return self.value_date.strftime('%d.%m.%Y') if self.value_date else ''
        return self.value_text

    @property
    def chart_values(self):
        """
        Werte dieser Antwort für die Häufigkeitsauszählung.
        Mehrfachauswahl liefert mehrere Werte, alles andere genau einen (oder keinen).
        """
        if self.question.question_type == QuestionType.CHECKBOX:
            return [str(v) for v in (self.value_json or [])]
        value = self.display_value
        return [value] if value else []


class SurveyInvitation(models.Model):
    """
    Ein Einmal-Zugang zu einer Umfrage – als QR-Zettel gedacht.

    ANONYMITÄT
    ----------
    Bei anonymen Umfragen bleibt `user` zwingend leer. Eine gespeicherte Zuordnung
    Token -> Person würde das Ergebnis von „anonym" zu „pseudonym" machen: jeder mit
    Datenbankzugriff könnte die Antwort einer Person zuordnen. Die AUSGABE der Zettel
    darf persönlich erfolgen, die gespeicherte Verknüpfung nicht.

    `used_on` ist – wie bei `SurveyParticipation` – bewusst nur tagesgenau.
    """

    survey = models.ForeignKey(
        Survey,
        on_delete=models.CASCADE,
        related_name='invitations',
        verbose_name="Umfrage",
    )
    token = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
        verbose_name="Zugangs-Token",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='survey_invitations',
        verbose_name="Zugeordnete Person",
        help_text="Nur bei personalisierten Umfragen erlaubt – siehe Klassen-Docstring",
    )
    label = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Aufdruck",
        help_text=(
            "Optionaler Text auf dem Zettel, z.B. 'Zug 1'. Bei anonymen Umfragen hier "
            "KEINE Namen eintragen – der Aufdruck wird mit dem Token gespeichert."
        ),
    )
    is_used = models.BooleanField(
        default=False,
        verbose_name="Bereits verwendet",
    )
    used_on = models.DateField(
        null=True,
        blank=True,
        verbose_name="Verwendet am",
        help_text="Bewusst nur das Datum, nicht die Uhrzeit",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Erstellt am",
    )

    class Meta:
        verbose_name = "Zugangs-Link"
        verbose_name_plural = "Zugangs-Links"
        ordering = ['pk']
        indexes = [
            models.Index(fields=['survey', 'is_used']),
        ]

    def __str__(self):
        state = 'verwendet' if self.is_used else 'offen'
        return f"Zugang {self.token[:8]}… ({state})"

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = self.generate_token()
        # Doppelte Absicherung gegen einen versehentlichen Personenbezug
        if self.survey_id and self.survey.is_anonymous:
            self.user = None
        super().save(*args, **kwargs)

    @staticmethod
    def generate_token():
        """
        Kryptografisch zufälliges Token.

        Muss lang genug sein, dass Raten im Stadtnetz aussichtslos ist – der Link
        ist bewusst ohne Login erreichbar.
        """
        import secrets

        return secrets.token_urlsafe(24)

    def get_absolute_url(self):
        return reverse('surveys:token_fill', kwargs={'token': self.token})

    def mark_used(self):
        """
        Token entwerten – rennsicher.

        Das bedingte UPDATE stellt sicher, dass bei zwei gleichzeitigen Absendungen
        (Doppelklick, zwei Geräte) nur genau eine durchkommt. Rückgabe: True, wenn
        DIESER Aufruf das Token entwertet hat.
        """
        updated = SurveyInvitation.objects.filter(pk=self.pk, is_used=False).update(
            is_used=True,
            used_on=timezone.localdate(),
        )
        return updated == 1


class SurveyParticipation(models.Model):
    """
    Vermerk, DASS eine Person teilgenommen hat – ohne jeden Bezug zu ihren Antworten.

    Diese Trennung ist der Kern des Anonymitätskonzepts: sie verhindert Doppelteilnahmen
    und erlaubt Erinnerungen an Fehlende, ohne die Antworten zuordenbar zu machen.

    `participated_on` ist bewusst ein DateField (nur Datum). Ein sekundengenauer
    Zeitstempel ließe sich mit dem Zeitstempel der Antwort korrelieren.
    """

    survey = models.ForeignKey(
        Survey,
        on_delete=models.CASCADE,
        related_name='participations',
        verbose_name="Umfrage",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='survey_participations',
        verbose_name="Benutzer",
    )
    participated_on = models.DateField(
        default=timezone.localdate,
        verbose_name="Teilgenommen am",
        help_text="Bewusst nur das Datum, nicht die Uhrzeit",
    )

    class Meta:
        verbose_name = "Teilnahme"
        verbose_name_plural = "Teilnahmen"
        ordering = ['user__last_name', 'user__first_name']
        constraints = [
            models.UniqueConstraint(
                fields=['survey', 'user'],
                name='unique_participation_per_survey',
            ),
        ]

    def __str__(self):
        return f"{self.user} hat an '{self.survey}' teilgenommen"
