"""
Bedingte Anzeige von Fragen (Sprunglogik).

WARUM DIE LOGIK ZWEIMAL LÄUFT
-----------------------------
Im Browser blendet Alpine.js Fragen live ein und aus – das ist reine Bequemlichkeit.
Verbindlich ist ausschließlich die serverseitige Auswertung in `visible_questions()`:

  1. Eine ausgeblendete Pflichtfrage darf das Absenden nicht blockieren. Ohne
     Serverprüfung wäre das Formular unabsendbar, sobald eine versteckte Pflichtfrage
     existiert.
  2. Ein manipulierter oder veralteter POST könnte Antworten auf Fragen enthalten, die
     gar nicht sichtbar waren. Die werden verworfen, sonst stünden in der Auswertung
     Antworten, die nie hätten gegeben werden dürfen.

Damit beide Seiten identisch entscheiden, erzeugt `build_client_config()` die Regeln
für den Browser aus denselben Daten, die `is_visible()` verwendet.
"""

from .models import CONDITION_SOURCE_TYPES, QuestionType

OPERATOR_ANY_OF = 'any_of'
OPERATOR_NONE_OF = 'none_of'


def condition_choices(question):
    """
    Auswählbare Antwortwerte einer Bezugsfrage als [(wert, beschriftung), ...].

    Wichtig: Der Wert muss dem entsprechen, was das Formularfeld später absendet –
    bei Ja/Nein also '1'/'0' und nicht 'Ja'/'Nein'. Sonst würde die Bedingung nie
    zutreffen.
    """
    if question.question_type == QuestionType.YESNO:
        return [('1', 'Ja'), ('0', 'Nein')]
    if question.question_type == QuestionType.SCALE:
        return [(str(value), str(value)) for value in question.scale_range]
    return [(option, option) for option in question.options]


def normalize_answer(value):
    """Antwortwert auf eine Liste von Strings bringen (Mehrfachauswahl liefert mehrere)"""
    if value is None or value == '':
        return []
    if isinstance(value, (list, tuple, set)):
        return [str(item) for item in value if item not in (None, '')]
    return [str(value)]


def is_visible(question, answers):
    """
    Ist `question` sichtbar, gegeben die bisherigen Antworten?

    `answers` bildet Frage-ID -> Antwortwert ab (Einzelwert oder Liste).
    """
    if not question.condition_question_id or not question.condition_values:
        return True

    source = question.condition_question
    # Sicherheitsnetz: Steht die Bezugsfrage nicht davor, ist die Bedingung nicht
    # auswertbar. Dann lieber anzeigen als eine Frage stillschweigend verschlucken.
    if source is None or source.order >= question.order:
        return True

    given = set(normalize_answer(answers.get(question.condition_question_id)))
    expected = {str(value) for value in question.condition_values}

    if not given:
        # Bezugsfrage unbeantwortet (oder selbst ausgeblendet): Folgefrage bleibt weg.
        return False

    matched = bool(given & expected)
    if question.condition_operator == OPERATOR_NONE_OF:
        return not matched
    return matched


def visible_questions(questions, answers):
    """
    Sichtbare Fragen in Reihenfolge bestimmen – inklusive Ketten.

    Fragen werden der Reihe nach geprüft. Wird eine Frage ausgeblendet, verschwindet
    ihre Antwort aus `answers`; dadurch fallen automatisch auch alle Fragen weg, die
    sich auf sie beziehen.
    """
    resolved = dict(answers)
    visible = []

    for question in questions:
        if is_visible(question, resolved):
            visible.append(question)
        else:
            # Antwort verwerfen, damit Folgebedingungen sie nicht mehr sehen
            resolved.pop(question.pk, None)

    return visible


def build_client_config(questions, field_name_for):
    """
    Regeln für Alpine.js aufbereiten.

    Rückgabe: {feldname: {'source': feldname, 'operator': ..., 'values': [...]}}
    Nur Fragen mit gültiger Bedingung tauchen auf; alles andere ist immer sichtbar.
    """
    by_pk = {question.pk: question for question in questions}
    config = {}

    for question in questions:
        if not question.condition_question_id or not question.condition_values:
            continue
        source = by_pk.get(question.condition_question_id)
        if source is None or source.order >= question.order:
            continue

        config[field_name_for(question)] = {
            'source': field_name_for(source),
            'operator': question.condition_operator or OPERATOR_ANY_OF,
            'values': [str(value) for value in question.condition_values],
        }

    return config


def describe_condition(question):
    """Bedingung als lesbarer Satz – für den Fragen-Builder"""
    if not question.condition_question_id or not question.condition_values:
        return ''

    source = question.condition_question
    labels = dict(condition_choices(source)) if source else {}
    values = ', '.join(
        labels.get(str(value), str(value)) for value in question.condition_values
    )
    position = (source.order + 1) if source else '?'

    if question.condition_operator == OPERATOR_NONE_OF:
        return f'Nur anzeigen, wenn Frage {position} NICHT mit "{values}" beantwortet wurde'
    return f'Nur anzeigen, wenn Frage {position} mit "{values}" beantwortet wurde'


def eligible_sources(survey, question=None):
    """
    Fragen, die als Bezugsfrage in Frage kommen.

    Nur Fragen mit festen Antwortmöglichkeiten und nur solche, die VOR der
    bearbeiteten Frage stehen.
    """
    queryset = survey.questions.filter(question_type__in=CONDITION_SOURCE_TYPES)
    if question is not None and question.pk:
        queryset = queryset.filter(order__lt=question.order).exclude(pk=question.pk)
    return queryset
