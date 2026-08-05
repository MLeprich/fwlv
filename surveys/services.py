"""
Umfragen Services
Auswertungslogik – bewusst aus den Views herausgehalten, damit sie testbar bleibt.

ANONYMITÄT IN DER AUSWERTUNG
----------------------------
Freitextantworten werden alphabetisch sortiert ausgegeben, NICHT nach Primärschlüssel.
Die pk-Reihenfolge entspricht der Einreichungsreihenfolge – zusammen mit den (tagesgenauen)
Teilnahmevermerken wäre das ein Ansatzpunkt für Rückschlüsse.
"""

from collections import Counter
from decimal import Decimal

from .models import QuestionType, SurveyAnswer


def build_question_statistics(survey):
    """
    Wertet alle Fragen einer Umfrage aus.

    Liefert eine Liste von Dicts mit:
        question, answer_count, kind ('chart' | 'text' | 'value'),
        categories/counts/percentages (chart), texts (text), stats (value)
    """
    answers = (
        SurveyAnswer.objects
        .filter(response__survey=survey, response__is_complete=True)
        .select_related('question')
    )

    # Antworten einmal einsammeln und pro Frage gruppieren (statt N Queries)
    by_question = {}
    for answer in answers:
        by_question.setdefault(answer.question_id, []).append(answer)

    threshold = survey.min_responses_for_results

    statistics = []
    for question in survey.questions.select_related('condition_question'):
        question_answers = by_question.get(question.pk, [])

        if question.is_chartable:
            entry = _chart_statistics(question, question_answers)
        elif question.question_type in (QuestionType.NUMBER, QuestionType.DATE):
            entry = _value_statistics(question, question_answers)
        else:
            entry = _text_statistics(question, question_answers)

        # Bedingte Fragen bekommen naturgemäß weniger Antworten als die Umfrage
        # insgesamt. Die globale Mindest-Fallzahl greift dort nicht – deshalb hier
        # zusätzlich je Frage prüfen. Sonst wäre z.B. eine Folgefrage, die nur zwei
        # Personen gesehen haben, faktisch nicht mehr anonym.
        if threshold and entry['answer_count'] < threshold:
            entry = _suppress(entry, threshold)

        statistics.append(entry)

    return statistics


def _suppress(entry, threshold):
    """Einzelergebnisse einer Frage verbergen, aber die Frage selbst weiter anzeigen"""
    entry['suppressed'] = True
    entry['threshold'] = threshold
    entry['texts'] = []
    entry['values'] = []
    entry['rows'] = []
    entry['counts'] = []
    entry['percentages'] = []
    entry['stats'] = {}
    entry['average'] = None
    return entry


def _chart_statistics(question, answers):
    """Häufigkeitsauszählung für Auswahl-, Skalen- und Ja/Nein-Fragen"""
    counter = Counter()
    for answer in answers:
        counter.update(answer.chart_values)

    categories = question.chart_categories()
    # Werte, die nicht mehr in den Optionen stehen (Option nachträglich umbenannt),
    # dürfen nicht verloren gehen – sonst stimmt die Summe nicht.
    for value in counter:
        if value not in categories:
            categories.append(value)

    counts = [counter.get(category, 0) for category in categories]
    total = sum(counts)
    percentages = [round(count * 100 / total, 1) if total else 0.0 for count in counts]

    average = None
    if question.question_type == QuestionType.SCALE and total:
        weighted = sum(int(cat) * cnt for cat, cnt in zip(categories, counts) if cat.isdigit())
        average = round(weighted / total, 2)

    return {
        'question': question,
        'kind': 'chart',
        'suppressed': False,
        'answer_count': len(answers),
        'categories': categories,
        'counts': counts,
        'percentages': percentages,
        'rows': list(zip(categories, counts, percentages)),
        'average': average,
    }


def _text_statistics(question, answers):
    """Freitextantworten – alphabetisch sortiert, siehe Modul-Docstring"""
    texts = sorted(
        (answer.display_value for answer in answers if answer.display_value),
        key=str.casefold,
    )
    return {
        'question': question,
        'kind': 'text',
        'suppressed': False,
        'answer_count': len(answers),
        'texts': texts,
    }


def _value_statistics(question, answers):
    """Kennzahlen für Zahlen- und Datumsfragen"""
    stats = {}
    if question.question_type == QuestionType.NUMBER:
        values = [a.value_number for a in answers if a.value_number is not None]
        if values:
            stats = {
                'min': min(values),
                'max': max(values),
                'avg': round(sum(values) / Decimal(len(values)), 2),
            }
    else:
        values = [a.value_date for a in answers if a.value_date]
        if values:
            stats = {'min': min(values), 'max': max(values), 'avg': None}

    return {
        'question': question,
        'kind': 'value',
        'suppressed': False,
        'answer_count': len(answers),
        'stats': stats,
        'values': sorted(str(v) for v in values) if values else [],
    }


def build_export_rows(survey):
    """
    Baut die Zeilen für den Excel-Export: eine Zeile je abgegebenem Fragebogen.

    Bei anonymen Umfragen werden die Zeilen nach ihrem Inhalt sortiert und enthalten
    keine Personenspalte. Die Reihenfolge gibt damit nichts über den Einreichungs-
    zeitpunkt preis.
    """
    questions = list(survey.questions.all())
    header = ['Abgesendet am']
    if not survey.is_anonymous:
        header.append('Teilnehmer')
    header += [q.text for q in questions]

    responses = (
        survey.responses
        .filter(is_complete=True)
        .select_related('user')
        .prefetch_related('answers__question')
    )

    rows = []
    for response in responses:
        answers = {a.question_id: a.display_value for a in response.answers.all()}
        if survey.is_anonymous:
            # Nur das Datum – die Uhrzeit ist bewusst nicht gespeichert
            row = [response.submitted_at.strftime('%d.%m.%Y')]
        else:
            row = [response.submitted_at.strftime('%d.%m.%Y %H:%M')]
            row.append(response.user.get_full_name() if response.user else '(gelöscht)')
        row += [answers.get(q.pk, '') for q in questions]
        rows.append(row)

    if survey.is_anonymous:
        rows.sort(key=lambda r: [str(cell).casefold() for cell in r])

    return header, rows


def get_missing_participants(survey):
    """
    Wer aus der Zielgruppe hat noch nicht teilgenommen?

    Funktioniert auch bei anonymen Umfragen, weil die Teilnahme getrennt von den
    Antworten vermerkt wird.
    """
    from django.contrib.auth import get_user_model

    User = get_user_model()
    users = User.objects.filter(is_active=True)

    group_ids = list(survey.target_groups.values_list('pk', flat=True))
    if group_ids:
        users = users.filter(groups__pk__in=group_ids).distinct()

    participated = survey.participations.values_list('user_id', flat=True)
    return users.exclude(pk__in=participated).order_by('last_name', 'first_name')
