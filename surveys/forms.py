"""
Umfragen Forms

Enthält zwei getrennte Dinge:
  1. Formulare zum BAUEN einer Umfrage (SurveyForm, SurveyQuestionForm)
  2. Die Factory `build_response_form()`, die zur Laufzeit aus den Fragen einer
     Umfrage ein normales Django-Form erzeugt. Dadurch bekommen wir Validierung,
     CSRF-Schutz und Fehlerdarstellung geschenkt – ohne zusätzliche Abhängigkeit.
"""

from decimal import Decimal

from django import forms
from django.contrib.auth.models import Group

from .conditions import (
    OPERATOR_ANY_OF,
    OPERATOR_NONE_OF,
    condition_choices,
    eligible_sources,
    visible_questions,
)
from .models import CHOICE_TYPES, QuestionType, Survey, SurveyAnswer, SurveyQuestion

# Einheitliche Tailwind-Klassen (das CSS ist vorkompiliert – nur bestehende Klassen nutzen)
INPUT_CLASS = (
    'w-full rounded-lg border-gray-300 shadow-sm '
    'focus:border-primary-500 focus:ring-primary-500'
)
CHECKBOX_CLASS = 'rounded border-gray-300 text-primary-600 focus:ring-primary-500'
RADIO_CLASS = 'border-gray-300 text-primary-600 focus:ring-primary-500'


class SurveyForm(forms.ModelForm):
    """Grunddaten einer Umfrage"""

    class Meta:
        model = Survey
        fields = [
            'title', 'description', 'is_anonymous', 'access_mode', 'pdf_intro_text',
            'target_groups', 'start_date', 'end_date', 'allow_multiple_responses',
            'min_responses_for_results', 'show_results_to_participants',
        ]
        widgets = {
            'access_mode': forms.RadioSelect(),
            'pdf_intro_text': forms.Textarea(attrs={
                'class': INPUT_CLASS,
                'rows': 3,
                'placeholder': 'z.B. Bitte nehmen Sie bis zum 15.08. an der Umfrage teil.',
            }),
            'title': forms.TextInput(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'z.B. Zufriedenheit mit der neuen Einsatzkleidung',
            }),
            'description': forms.Textarea(attrs={'class': INPUT_CLASS, 'rows': 4}),
            'is_anonymous': forms.RadioSelect(choices=[
                (True, 'Anonym – Antworten ohne Personenbezug'),
                (False, 'Personalisiert – Antworten sind der Person zugeordnet'),
            ]),
            # format='%Y-%m-%dT%H:%M' ist bei datetime-local zwingend, sonst bleibt
            # das Feld beim Bearbeiten leer.
            'start_date': forms.DateTimeInput(
                format='%Y-%m-%dT%H:%M',
                attrs={'type': 'datetime-local', 'class': INPUT_CLASS},
            ),
            'end_date': forms.DateTimeInput(
                format='%Y-%m-%dT%H:%M',
                attrs={'type': 'datetime-local', 'class': INPUT_CLASS},
            ),
            'target_groups': forms.CheckboxSelectMultiple(),
            'allow_multiple_responses': forms.CheckboxInput(attrs={'class': CHECKBOX_CLASS}),
            'show_results_to_participants': forms.CheckboxInput(attrs={'class': CHECKBOX_CLASS}),
            'min_responses_for_results': forms.NumberInput(attrs={'class': INPUT_CLASS, 'min': 0}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['target_groups'].queryset = Group.objects.order_by('name')
        self.fields['target_groups'].required = False

        # Der Anonymitätsmodus ist eine Zusage an die Teilnehmenden. Sobald die erste
        # Antwort vorliegt, darf er nicht mehr umgestellt werden.
        if self.instance.pk and self.instance.is_locked:
            self.fields['is_anonymous'].disabled = True
            self.fields['is_anonymous'].help_text = (
                "Gesperrt: Es liegen bereits Antworten vor. Der Anonymitätsmodus kann "
                "nicht mehr geändert werden."
            )
            # Ein Wechsel des Zugangswegs würde die bereits verteilten Zettel entwerten
            # bzw. den Zettel-Zwang nachträglich aushebeln.
            self.fields['access_mode'].disabled = True

    def clean(self):
        cleaned = super().clean()
        start, end = cleaned.get('start_date'), cleaned.get('end_date')
        if start and end and end <= start:
            self.add_error('end_date', 'Das Ende muss nach dem Start liegen.')
        return cleaned

    def clean_is_anonymous(self):
        # disabled-Felder liefern den Initialwert; das explizit absichern, damit ein
        # manipulierter POST den Modus nicht doch umstellt.
        if self.instance.pk and self.instance.is_locked:
            return self.instance.is_anonymous
        return self.cleaned_data['is_anonymous']

    def clean_access_mode(self):
        if self.instance.pk and self.instance.is_locked:
            return self.instance.access_mode
        return self.cleaned_data['access_mode']


class LateValidatedMultipleChoiceField(forms.MultipleChoiceField):
    """
    Mehrfachauswahl, deren gültige Werte erst zur Laufzeit feststehen.

    Welche Werte erlaubt sind, hängt von der gewählten Bezugsfrage ab – das weiß das
    Feld beim Aufbau des Formulars noch nicht. Die Prüfung passiert deshalb in
    `SurveyQuestionForm.clean()`.
    """

    def validate(self, value):
        if self.required and not value:
            raise forms.ValidationError(self.error_messages['required'], code='required')


class SurveyQuestionForm(forms.ModelForm):
    """
    Eine Frage im Builder.

    Die typspezifische Konfiguration wird über eigene Felder erfasst und beim Speichern
    nach `config` (JSONField) überführt – so bleibt das JSON im Formular unsichtbar.
    """

    options_text = forms.CharField(
        label="Antwortoptionen",
        required=False,
        widget=forms.Textarea(attrs={
            'class': INPUT_CLASS,
            'rows': 5,
            'placeholder': 'Eine Option pro Zeile',
        }),
        help_text="Eine Option pro Zeile. Nur für Einzelauswahl, Mehrfachauswahl und Dropdown.",
    )
    scale_min = forms.IntegerField(
        label="Skala von", required=False, min_value=0, max_value=100, initial=1,
        widget=forms.NumberInput(attrs={'class': INPUT_CLASS}),
    )
    scale_max = forms.IntegerField(
        label="Skala bis", required=False, min_value=1, max_value=100, initial=5,
        widget=forms.NumberInput(attrs={'class': INPUT_CLASS}),
    )
    min_label = forms.CharField(
        label="Beschriftung unterer Wert", required=False, max_length=50,
        widget=forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'z.B. trifft nicht zu'}),
    )
    max_label = forms.CharField(
        label="Beschriftung oberer Wert", required=False, max_length=50,
        widget=forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'z.B. trifft voll zu'}),
    )

    condition_values = LateValidatedMultipleChoiceField(
        label="Auslösende Antworten",
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={'class': CHECKBOX_CLASS}),
    )

    class Meta:
        model = SurveyQuestion
        fields = [
            'text', 'question_type', 'help_text', 'is_required',
            'condition_question', 'condition_operator',
        ]
        widgets = {
            'text': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'question_type': forms.Select(attrs={'class': INPUT_CLASS, 'x-model': 'questionType'}),
            'help_text': forms.TextInput(attrs={'class': INPUT_CLASS}),
            'is_required': forms.CheckboxInput(attrs={'class': CHECKBOX_CLASS}),
            'condition_question': forms.Select(attrs={
                'class': INPUT_CLASS,
                'x-model': 'conditionSource',
            }),
            'condition_operator': forms.Select(attrs={'class': INPUT_CLASS}),
        }

    def __init__(self, *args, survey=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.survey = survey or getattr(self.instance, 'survey', None)

        # Bestehende config in die Einzelfelder zurückschreiben
        if self.instance.pk:
            self.fields['options_text'].initial = '\n'.join(self.instance.options)
            self.fields['scale_min'].initial = self.instance.scale_min
            self.fields['scale_max'].initial = self.instance.scale_max
            self.fields['min_label'].initial = self.instance.min_label
            self.fields['max_label'].initial = self.instance.max_label
            self.fields['condition_values'].initial = [
                str(value) for value in (self.instance.condition_values or [])
            ]

        # Als Bezugsfrage kommen nur vorausgehende Fragen mit festen Antwortmöglich-
        # keiten in Frage – sonst wäre die Bedingung beim Ausfüllen nicht auswertbar.
        source_field = self.fields['condition_question']
        if self.survey is not None:
            source_field.queryset = eligible_sources(self.survey, self.instance)
        else:
            source_field.queryset = SurveyQuestion.objects.none()
        source_field.required = False
        source_field.empty_label = 'Immer anzeigen (keine Bedingung)'
        source_field.label_from_instance = (
            lambda question: f'Frage {question.order + 1}: {question.text[:60]}'
        )

    @property
    def condition_source_options(self):
        """
        Antwortmöglichkeiten je Bezugsfrage – als JSON für die Live-Anzeige im Builder.

        Der Builder weiß erst nach Auswahl der Bezugsfrage, welche Häkchen er anbieten
        muss; die Zuordnung kommt deshalb komplett mit ins Template.
        """
        return {
            str(question.pk): [
                {'value': value, 'label': label}
                for value, label in condition_choices(question)
            ]
            for question in self.fields['condition_question'].queryset
        }

    def clean(self):
        cleaned = super().clean()
        qtype = cleaned.get('question_type')

        if qtype in CHOICE_TYPES:
            options = [
                line.strip()
                for line in (cleaned.get('options_text') or '').splitlines()
                if line.strip()
            ]
            if len(options) < 2:
                self.add_error(
                    'options_text',
                    'Bitte mindestens zwei Antwortoptionen angeben (eine pro Zeile).',
                )
            elif len(set(options)) != len(options):
                # Doppelte Optionen würden die Auswertung verfälschen: die Häufigkeiten
                # werden pro Optionstext gezählt.
                self.add_error('options_text', 'Die Antwortoptionen müssen eindeutig sein.')
            cleaned['_options'] = options

        if qtype == QuestionType.SCALE:
            low = cleaned.get('scale_min')
            high = cleaned.get('scale_max')
            low = 1 if low is None else low
            high = 5 if high is None else high
            if high <= low:
                self.add_error('scale_max', 'Der obere Wert muss größer als der untere sein.')
            elif high - low > 20:
                self.add_error('scale_max', 'Die Skala darf höchstens 21 Stufen umfassen.')
            cleaned['scale_min'], cleaned['scale_max'] = low, high

        self._clean_condition(cleaned)
        return cleaned

    def _clean_condition(self, cleaned):
        """
        Bedingung prüfen.

        Die erlaubten Werte hängen von der Bezugsfrage ab und werden deshalb erst hier
        geprüft (siehe LateValidatedMultipleChoiceField).
        """
        source = cleaned.get('condition_question')
        values = cleaned.get('condition_values') or []

        if source is None:
            # Ohne Bezugsfrage keine Bedingung – Reste verwerfen
            cleaned['condition_values'] = []
            cleaned['condition_operator'] = OPERATOR_ANY_OF
            return

        if self.survey is not None and source.survey_id != self.survey.pk:
            self.add_error('condition_question', 'Die Bezugsfrage gehört zu einer anderen Umfrage.')
            return

        if self.instance.pk and source.pk == self.instance.pk:
            self.add_error('condition_question', 'Eine Frage kann sich nicht auf sich selbst beziehen.')
            return

        # Die Bezugsfrage muss vorher kommen, sonst ist sie beim Ausfüllen noch
        # unbeantwortet. Bei einer neuen Frage ist das automatisch erfüllt, weil sie
        # ans Ende gehängt wird.
        if self.instance.pk and source.order >= self.instance.order:
            self.add_error(
                'condition_question',
                'Die Bezugsfrage muss vor dieser Frage stehen.',
            )
            return

        if not values:
            self.add_error(
                'condition_values',
                'Bitte mindestens eine auslösende Antwort auswählen.',
            )
            return

        allowed = {value for value, _ in condition_choices(source)}
        invalid = [value for value in values if value not in allowed]
        if invalid:
            self.add_error(
                'condition_values',
                f'Unbekannte Antwortmöglichkeit: {", ".join(invalid)}',
            )
            return

        if cleaned.get('condition_operator') not in (OPERATOR_ANY_OF, OPERATOR_NONE_OF):
            cleaned['condition_operator'] = OPERATOR_ANY_OF

    def save(self, commit=True):
        question = super().save(commit=False)
        qtype = self.cleaned_data['question_type']

        # config typabhängig neu aufbauen – alte Reste anderer Typen fallen dabei weg
        config = {}
        if qtype in CHOICE_TYPES:
            config['options'] = self.cleaned_data.get('_options', [])
        elif qtype == QuestionType.SCALE:
            config['min'] = self.cleaned_data['scale_min']
            config['max'] = self.cleaned_data['scale_max']
            if self.cleaned_data.get('min_label'):
                config['min_label'] = self.cleaned_data['min_label']
            if self.cleaned_data.get('max_label'):
                config['max_label'] = self.cleaned_data['max_label']
        question.config = config
        question.condition_values = self.cleaned_data.get('condition_values') or []

        if commit:
            question.save()
        return question


# ======================================================================
# Laufzeit-Factory für den Fragebogen
# ======================================================================

def field_name_for(question):
    """Feldname einer Frage im generierten Formular"""
    return f'question_{question.pk}'


def _build_field(question):
    """Erzeugt das passende Form-Field für eine Frage"""
    # required=False ist Absicht: die Pflicht prüft SurveyResponseFormBase.clean(),
    # weil eine ausgeblendete Pflichtfrage sonst das Absenden blockieren würde.
    common = {
        'label': question.text,
        'required': False,
        'help_text': question.help_text,
    }
    qtype = question.question_type

    if qtype == QuestionType.TEXT:
        return forms.CharField(
            max_length=500,
            widget=forms.TextInput(attrs={'class': INPUT_CLASS}),
            **common,
        )

    if qtype == QuestionType.TEXTAREA:
        return forms.CharField(
            widget=forms.Textarea(attrs={'class': INPUT_CLASS, 'rows': 4}),
            **common,
        )

    if qtype == QuestionType.RADIO:
        return forms.ChoiceField(
            choices=[(o, o) for o in question.options],
            widget=forms.RadioSelect(attrs={'class': RADIO_CLASS}),
            **common,
        )

    if qtype == QuestionType.SELECT:
        return forms.ChoiceField(
            choices=[('', '--- Bitte wählen ---')] + [(o, o) for o in question.options],
            widget=forms.Select(attrs={'class': INPUT_CLASS}),
            **common,
        )

    if qtype == QuestionType.CHECKBOX:
        return forms.MultipleChoiceField(
            choices=[(o, o) for o in question.options],
            widget=forms.CheckboxSelectMultiple(attrs={'class': CHECKBOX_CLASS}),
            **common,
        )

    if qtype == QuestionType.SCALE:
        return forms.ChoiceField(
            choices=[(str(v), str(v)) for v in question.scale_range],
            widget=forms.RadioSelect(attrs={'class': RADIO_CLASS}),
            **common,
        )

    if qtype == QuestionType.YESNO:
        return forms.ChoiceField(
            choices=[('1', 'Ja'), ('0', 'Nein')],
            widget=forms.RadioSelect(attrs={'class': RADIO_CLASS}),
            **common,
        )

    if qtype == QuestionType.NUMBER:
        return forms.DecimalField(
            max_digits=12,
            decimal_places=2,
            widget=forms.NumberInput(attrs={'class': INPUT_CLASS, 'step': 'any'}),
            **common,
        )

    if qtype == QuestionType.DATE:
        # format='%Y-%m-%d' ist bei type='date' zwingend, sonst bleibt das Feld leer
        return forms.DateField(
            widget=forms.DateInput(
                format='%Y-%m-%d',
                attrs={'type': 'date', 'class': INPUT_CLASS},
            ),
            **common,
        )

    # Unbekannter Typ (z.B. nach einem Downgrade): als Freitext behandeln, damit die
    # Umfrage nicht komplett unbenutzbar wird.
    return forms.CharField(
        widget=forms.TextInput(attrs={'class': INPUT_CLASS}),
        **common,
    )


class SurveyResponseFormBase(forms.Form):
    """
    Basis des generierten Fragebogens.

    Alle Felder werden mit `required=False` erzeugt; die Pflicht wird erst in `clean()`
    geprüft – und zwar nur für Fragen, die nach den gegebenen Antworten überhaupt
    sichtbar sind. Andernfalls würde eine ausgeblendete Pflichtfrage das Absenden
    dauerhaft blockieren.
    """

    #: wird von build_response_form() gesetzt
    question_map = {}
    ordered_questions = []

    def clean(self):
        cleaned = super().clean()

        # Antworten nach Frage-ID sammeln, um die Bedingungen auswerten zu können
        answers = {
            question.pk: cleaned.get(name)
            for name, question in self.question_map.items()
        }
        visible = visible_questions(self.ordered_questions, answers)
        visible_pks = {question.pk for question in visible}

        for name, question in self.question_map.items():
            if question.pk not in visible_pks:
                # Nicht sichtbar: Wert verwerfen und etwaige Fehler entfernen.
                # Ein manipulierter POST soll keine Antwort auf eine Frage
                # hinterlassen, die nie angezeigt wurde.
                cleaned[name] = None
                self.errors.pop(name, None)
                continue

            if question.is_required and self._is_empty(cleaned.get(name)):
                self.add_error(name, 'Diese Frage ist eine Pflichtfrage.')

        self.visible_questions = visible
        return cleaned

    @staticmethod
    def _is_empty(value):
        return value in (None, '', [], ())


def build_response_form(survey, data=None):
    """
    Baut zur Laufzeit ein Django-Form aus den Fragen einer Umfrage.

    Rückgabe ist eine fertige Form-INSTANZ. Die Fragen hängen als `question_map` am
    Formular, damit die View die Antworten wieder zuordnen kann.
    """
    questions = list(survey.questions.all().select_related('condition_question'))
    fields = {field_name_for(q): _build_field(q) for q in questions}

    form_class = type('SurveyResponseForm', (SurveyResponseFormBase,), fields)
    form = form_class(data) if data is not None else form_class()
    form.question_map = {field_name_for(q): q for q in questions}
    form.ordered_questions = questions
    return form


def save_answers(response, form):
    """
    Schreibt die validierten Formulardaten als `SurveyAnswer`-Zeilen.

    Bewusst ohne Personenbezug und ohne Audit-Log – der Bezug hängt allein an
    `response.user`, das bei anonymen Umfragen leer ist.
    """
    answers = []
    for field_name, question in form.question_map.items():
        value = form.cleaned_data.get(field_name)
        if value in (None, '', []):
            continue

        answer = SurveyAnswer(response=response, question=question)
        qtype = question.question_type

        if qtype == QuestionType.CHECKBOX:
            answer.value_json = list(value)
        elif qtype in (QuestionType.SCALE, QuestionType.YESNO):
            answer.value_number = Decimal(str(value))
        elif qtype == QuestionType.NUMBER:
            answer.value_number = value
        elif qtype == QuestionType.DATE:
            answer.value_date = value
        else:
            answer.value_text = str(value)

        answers.append(answer)

    SurveyAnswer.objects.bulk_create(answers)
    return answers
