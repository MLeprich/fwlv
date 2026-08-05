"""
Tests für das Umfrage-Modul.

Der Schwerpunkt liegt auf der Anonymität: dass bei `is_anonymous=True` wirklich kein
Personenbezug gespeichert wird, ist die zentrale Zusage des Moduls und muss abgesichert
sein – auch gegen versehentliche Änderungen im Aufrufer.
"""

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .forms import SurveyForm, SurveyQuestionForm, build_response_form, save_answers
from .models import (
    QuestionType,
    Survey,
    SurveyAccessMode,
    SurveyAnswer,
    SurveyInvitation,
    SurveyParticipation,
    SurveyQuestion,
    SurveyResponse,
    SurveyStatus,
)
from .services import build_export_rows, build_question_statistics

User = get_user_model()


def make_user(username, *codenames):
    user = User.objects.create_user(username=username, password='pw12345')
    for codename in codenames:
        user.user_permissions.add(Permission.objects.get(codename=codename))
    # Frisch laden, damit der Permission-Cache die neuen Rechte kennt
    return User.objects.get(pk=user.pk)


class SurveyTestMixin:
    def setUp(self):
        self.conductor = make_user('leiter', 'conduct_survey', 'add_survey', 'delete_survey')
        self.participant = make_user('mitglied', 'participate_survey')

    def make_survey(self, is_anonymous=True, **kwargs):
        defaults = dict(
            title='Zufriedenheit Einsatzkleidung',
            status=SurveyStatus.ACTIVE,
            is_anonymous=is_anonymous,
            min_responses_for_results=0,
            created_by=self.conductor,
            updated_by=self.conductor,
        )
        defaults.update(kwargs)
        survey = Survey.objects.create(**defaults)
        SurveyQuestion.objects.create(
            survey=survey,
            order=0,
            question_type=QuestionType.RADIO,
            text='Wie zufrieden sind Sie?',
            config={'options': ['Sehr', 'Mittel', 'Gar nicht']},
        )
        return survey

    def fill(self, survey, user, **answers):
        """Fragebogen über die View absenden"""
        self.client.force_login(user)
        question = survey.questions.first()
        data = {f'question_{question.pk}': 'Sehr'}
        data.update(answers)
        return self.client.post(reverse('surveys:fill', args=[survey.pk]), data)


class AnonymityTests(SurveyTestMixin, TestCase):
    """Die zentrale Zusage: bei anonymen Umfragen existiert kein Personenbezug."""

    def test_anonymous_response_has_no_user(self):
        survey = self.make_survey(is_anonymous=True)
        self.fill(survey, self.participant)

        self.assertIsNone(SurveyResponse.objects.get().user_id)

    def test_model_strips_user_even_if_caller_sets_it(self):
        """Auch ein fehlerhafter Aufrufer darf die Anonymität nicht brechen."""
        survey = self.make_survey(is_anonymous=True)

        response = SurveyResponse.objects.create(survey=survey, user=self.participant)

        response.refresh_from_db()
        self.assertIsNone(response.user_id)

    def test_anonymous_timestamp_is_truncated_to_day(self):
        """Sekundengenaue Zeitstempel ließen sich mit den Teilnahmevermerken korrelieren."""
        survey = self.make_survey(is_anonymous=True)
        self.fill(survey, self.participant)

        submitted = timezone.localtime(SurveyResponse.objects.get().submitted_at)
        self.assertEqual((submitted.hour, submitted.minute, submitted.second), (0, 0, 0))

    def test_participation_is_recorded_separately(self):
        """Teilnahme ist bekannt, die Antwort bleibt trotzdem unzuordenbar."""
        survey = self.make_survey(is_anonymous=True)
        self.fill(survey, self.participant)

        self.assertTrue(survey.has_participated(self.participant))
        self.assertIsNone(SurveyResponse.objects.get().user_id)
        # Es gibt keinen Weg von der Teilnahme zur Antwort
        participation = SurveyParticipation.objects.get()
        self.assertFalse(hasattr(participation, 'response'))

    def test_participation_stores_date_only(self):
        survey = self.make_survey(is_anonymous=True)
        self.fill(survey, self.participant)

        participation = SurveyParticipation.objects.get()
        self.assertEqual(participation.participated_on, timezone.localdate())
        # DateField, kein DateTimeField – sonst wäre eine Korrelation möglich
        self.assertFalse(hasattr(participation.participated_on, 'hour'))

    def test_personalized_response_keeps_user(self):
        survey = self.make_survey(is_anonymous=False)
        self.fill(survey, self.participant)

        self.assertEqual(SurveyResponse.objects.get().user, self.participant)

    def test_response_model_has_no_audit_fields(self):
        """
        `AuditedModel` würde ein Pflichtfeld `created_by` mitbringen und die
        Anonymität aushebeln.
        """
        field_names = {f.name for f in SurveyResponse._meta.get_fields()}
        self.assertNotIn('created_by', field_names)
        self.assertNotIn('updated_by', field_names)

    def test_anonymity_mode_locked_after_first_response(self):
        survey = self.make_survey(is_anonymous=True)
        self.fill(survey, self.participant)

        self.assertTrue(SurveyForm(instance=survey).fields['is_anonymous'].disabled)

    def test_anonymity_mode_cannot_be_flipped_by_post(self):
        """Ein manipulierter POST darf den Modus nicht rückwirkend umstellen."""
        survey = self.make_survey(is_anonymous=True)
        self.fill(survey, self.participant)

        form = SurveyForm(
            data={
                'title': survey.title,
                'description': '',
                'is_anonymous': 'False',
                'min_responses_for_results': 0,
            },
            instance=survey,
        )
        self.assertTrue(form.is_valid(), form.errors)
        self.assertTrue(form.save().is_anonymous)


class ParticipationTests(SurveyTestMixin, TestCase):
    def test_double_participation_is_blocked(self):
        survey = self.make_survey()
        self.fill(survey, self.participant)
        self.fill(survey, self.participant)

        self.assertEqual(SurveyResponse.objects.count(), 1)
        self.assertEqual(SurveyParticipation.objects.count(), 1)

    def test_multiple_responses_when_allowed(self):
        survey = self.make_survey(allow_multiple_responses=True)
        self.fill(survey, self.participant)
        self.fill(survey, self.participant)

        self.assertEqual(SurveyResponse.objects.count(), 2)
        self.assertEqual(SurveyParticipation.objects.count(), 1)

    def test_closed_survey_rejects_participation(self):
        survey = self.make_survey(status=SurveyStatus.CLOSED)
        self.fill(survey, self.participant)

        self.assertEqual(SurveyResponse.objects.count(), 0)

    def test_expired_survey_rejects_participation(self):
        survey = self.make_survey(end_date=timezone.now() - timedelta(hours=1))
        self.fill(survey, self.participant)

        self.assertEqual(SurveyResponse.objects.count(), 0)

    def test_target_group_restricts_participation(self):
        survey = self.make_survey()
        group = Group.objects.create(name='Tauchgruppe')
        survey.target_groups.add(group)

        self.fill(survey, self.participant)
        self.assertEqual(SurveyResponse.objects.count(), 0)

        self.participant.groups.add(group)
        self.fill(survey, self.participant)
        self.assertEqual(SurveyResponse.objects.count(), 1)

    def test_user_without_permission_cannot_participate(self):
        survey = self.make_survey()

        self.fill(survey, make_user('fremd'))
        self.assertEqual(SurveyResponse.objects.count(), 0)

    def test_required_question_blocks_submission(self):
        survey = self.make_survey()
        question = survey.questions.first()

        self.client.force_login(self.participant)
        self.client.post(reverse('surveys:fill', args=[survey.pk]), {f'question_{question.pk}': ''})

        self.assertEqual(SurveyResponse.objects.count(), 0)
        # Kein Teilnahmevermerk ohne Antwort – sonst wäre der Nutzer fälschlich gesperrt
        self.assertEqual(SurveyParticipation.objects.count(), 0)


class ResultsTests(SurveyTestMixin, TestCase):
    def test_results_locked_below_minimum(self):
        survey = self.make_survey(min_responses_for_results=5)
        self.fill(survey, self.participant)

        self.client.force_login(self.conductor)
        response = self.client.get(reverse('surveys:results', args=[survey.pk]))

        self.assertFalse(response.context['results_unlocked'])
        self.assertEqual(response.context['missing_for_unlock'], 4)

    def test_export_blocked_below_minimum(self):
        survey = self.make_survey(min_responses_for_results=5)
        self.fill(survey, self.participant)

        self.client.force_login(self.conductor)
        response = self.client.get(reverse('surveys:export', args=[survey.pk]))

        self.assertEqual(response.status_code, 302)

    def test_chart_statistics_count_options(self):
        survey = self.make_survey()
        for index in range(3):
            self.fill(survey, make_user(f'user{index}', 'participate_survey'))

        entry = build_question_statistics(survey)[0]
        self.assertEqual(entry['kind'], 'chart')
        self.assertEqual(entry['categories'], ['Sehr', 'Mittel', 'Gar nicht'])
        self.assertEqual(entry['counts'], [3, 0, 0])
        self.assertEqual(entry['percentages'], [100.0, 0.0, 0.0])

    def test_export_has_no_person_column_when_anonymous(self):
        survey = self.make_survey(is_anonymous=True)
        self.fill(survey, self.participant)

        header, rows = build_export_rows(survey)
        self.assertNotIn('Teilnehmer', header)
        self.assertEqual(len(rows), 1)

    def test_export_has_person_column_when_personalized(self):
        survey = self.make_survey(is_anonymous=False)
        self.fill(survey, self.participant)

        header, _ = build_export_rows(survey)
        self.assertIn('Teilnehmer', header)

    def test_participant_cannot_view_results_by_default(self):
        survey = self.make_survey()
        self.fill(survey, self.participant)

        self.client.force_login(self.participant)
        response = self.client.get(reverse('surveys:results', args=[survey.pk]))
        self.assertEqual(response.status_code, 302)


class QuestionTypeTests(SurveyTestMixin, TestCase):
    """Die Formular-Factory muss jeden Fragetyp korrekt speichern."""

    def _single_question_survey(self, question_type, **config):
        survey = self.make_survey()
        survey.questions.all().delete()
        SurveyQuestion.objects.create(
            survey=survey,
            order=0,
            question_type=question_type,
            text='Testfrage',
            config=config,
        )
        return survey

    def _submit(self, survey, value):
        question = survey.questions.first()
        form = build_response_form(survey, data={f'question_{question.pk}': value})
        self.assertTrue(form.is_valid(), form.errors)
        response = SurveyResponse.objects.create(survey=survey)
        save_answers(response, form)
        return SurveyAnswer.objects.get(response=response)

    def test_text_answer(self):
        survey = self._single_question_survey(QuestionType.TEXTAREA)
        self.assertEqual(self._submit(survey, 'Alles gut').value_text, 'Alles gut')

    def test_number_answer(self):
        survey = self._single_question_survey(QuestionType.NUMBER)
        self.assertEqual(self._submit(survey, '42.5').display_value, '42.50')

    def test_scale_answer(self):
        survey = self._single_question_survey(QuestionType.SCALE, min=1, max=5)
        self.assertEqual(self._submit(survey, '4').display_value, '4')

    def test_yesno_answer(self):
        survey = self._single_question_survey(QuestionType.YESNO)
        self.assertEqual(self._submit(survey, '1').display_value, 'Ja')
        SurveyResponse.objects.all().delete()
        self.assertEqual(self._submit(survey, '0').display_value, 'Nein')

    def test_date_answer(self):
        survey = self._single_question_survey(QuestionType.DATE)
        self.assertEqual(self._submit(survey, '2026-08-04').display_value, '04.08.2026')

    def test_checkbox_answer_stores_all_selections(self):
        survey = self._single_question_survey(QuestionType.CHECKBOX, options=['A', 'B', 'C'])
        question = survey.questions.first()
        form = build_response_form(survey, data={f'question_{question.pk}': ['A', 'C']})
        self.assertTrue(form.is_valid(), form.errors)

        response = SurveyResponse.objects.create(survey=survey)
        save_answers(response, form)

        answer = SurveyAnswer.objects.get(response=response)
        self.assertEqual(answer.value_json, ['A', 'C'])
        self.assertEqual(answer.display_value, 'A, C')

    def test_invalid_choice_is_rejected(self):
        survey = self._single_question_survey(QuestionType.RADIO, options=['A', 'B'])
        question = survey.questions.first()
        form = build_response_form(survey, data={f'question_{question.pk}': 'Manipuliert'})
        self.assertFalse(form.is_valid())


class TokenAccessTests(SurveyTestMixin, TestCase):
    """Einmal-Links (QR-Zettel): jeder Zettel genau eine Stimme."""

    def make_token_survey(self, is_anonymous=True, count=3):
        survey = self.make_survey(
            is_anonymous=is_anonymous, access_mode=SurveyAccessMode.TOKEN
        )
        invitations = SurveyInvitation.objects.bulk_create([
            SurveyInvitation(survey=survey, token=SurveyInvitation.generate_token())
            for _ in range(count)
        ])
        return survey, invitations

    def submit(self, survey, invitation):
        question = survey.questions.first()
        return self.client.post(
            reverse('surveys:token_fill', args=[invitation.token]),
            {f'question_{question.pk}': 'Sehr'},
        )

    def test_token_works_without_login(self):
        survey, invitations = self.make_token_survey()

        response = self.client.get(reverse('surveys:token_fill', args=[invitations[0].token]))
        self.assertEqual(response.status_code, 200)

    def test_token_is_burned_after_use(self):
        survey, invitations = self.make_token_survey()
        invitation = invitations[0]

        self.submit(survey, invitation)
        invitation.refresh_from_db()

        self.assertTrue(invitation.is_used)
        self.assertEqual(invitation.used_on, timezone.localdate())
        self.assertEqual(SurveyResponse.objects.count(), 1)

    def test_used_token_is_rejected(self):
        survey, invitations = self.make_token_survey()
        invitation = invitations[0]

        self.submit(survey, invitation)
        second = self.submit(survey, invitation)

        self.assertEqual(second.status_code, 410)
        self.assertEqual(SurveyResponse.objects.count(), 1)

    def test_each_token_counts_once(self):
        survey, invitations = self.make_token_survey(count=3)
        for invitation in invitations:
            self.submit(survey, invitation)

        self.assertEqual(SurveyResponse.objects.count(), 3)

    def test_unknown_token_returns_404(self):
        self.make_token_survey()
        response = self.client.get(reverse('surveys:token_fill', args=['gibtesnicht']))
        self.assertEqual(response.status_code, 404)

    def test_token_response_stays_anonymous(self):
        survey, invitations = self.make_token_survey(is_anonymous=True)
        invitation = invitations[0]
        # Selbst wenn dem Zettel versehentlich eine Person zugeordnet würde:
        SurveyInvitation.objects.filter(pk=invitation.pk).update(user=self.participant)

        self.submit(survey, SurveyInvitation.objects.get(pk=invitation.pk))

        self.assertIsNone(SurveyResponse.objects.get().user_id)

    def test_invitation_model_strips_user_when_anonymous(self):
        survey, _ = self.make_token_survey(is_anonymous=True)

        invitation = SurveyInvitation.objects.create(survey=survey, user=self.participant)

        invitation.refresh_from_db()
        self.assertIsNone(invitation.user_id)

    def test_login_route_blocked_in_token_mode(self):
        """Sonst ließen sich die Zettel umgehen."""
        survey, _ = self.make_token_survey()

        self.fill(survey, self.participant)
        self.assertEqual(SurveyResponse.objects.count(), 0)

    def test_closed_survey_rejects_token(self):
        survey, invitations = self.make_token_survey()
        survey.status = SurveyStatus.CLOSED
        survey.save(update_fields=['status'])

        response = self.submit(survey, invitations[0])

        self.assertEqual(response.status_code, 403)
        self.assertEqual(SurveyResponse.objects.count(), 0)

    def test_invalid_form_does_not_burn_token(self):
        """Ein Pflichtfeld-Fehler darf den Zettel nicht wertlos machen."""
        survey, invitations = self.make_token_survey()
        invitation = invitations[0]
        question = survey.questions.first()

        self.client.post(
            reverse('surveys:token_fill', args=[invitation.token]),
            {f'question_{question.pk}': ''},
        )

        invitation.refresh_from_db()
        self.assertFalse(invitation.is_used)
        self.assertEqual(SurveyResponse.objects.count(), 0)

    def test_tokens_are_unique_and_long(self):
        _, invitations = self.make_token_survey(count=25)
        tokens = [invitation.token for invitation in invitations]

        self.assertEqual(len(set(tokens)), 25)
        self.assertTrue(all(len(token) >= 30 for token in tokens))

    def test_generate_view_creates_requested_count(self):
        survey = self.make_survey(access_mode=SurveyAccessMode.TOKEN)

        self.client.force_login(self.conductor)
        self.client.post(
            reverse('surveys:invitation_generate', args=[survey.pk]),
            {'count': '50', 'label': 'Leitstelle'},
        )

        self.assertEqual(survey.invitations.count(), 50)

    def test_generate_view_rejects_absurd_count(self):
        survey = self.make_survey(access_mode=SurveyAccessMode.TOKEN)

        self.client.force_login(self.conductor)
        self.client.post(
            reverse('surveys:invitation_generate', args=[survey.pk]), {'count': '500000'}
        )

        self.assertEqual(survey.invitations.count(), 0)

    def test_pdf_download(self):
        survey, _ = self.make_token_survey(count=9)

        self.client.force_login(self.conductor)
        response = self.client.get(reverse('surveys:invitation_pdf', args=[survey.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertTrue(response.content.startswith(b'%PDF'))

    def test_invitation_url_is_the_token_route(self):
        """Der QR-Code muss auf den Einmal-Link zeigen, nicht auf die Umfrage."""
        _, invitations = self.make_token_survey(count=1)
        invitation = invitations[0]

        self.assertEqual(
            invitation.get_absolute_url(), f'/umfragen/t/{invitation.token}/'
        )

    def test_pdf_requires_permission(self):
        survey, _ = self.make_token_survey()

        self.client.force_login(self.participant)
        response = self.client.get(reverse('surveys:invitation_pdf', args=[survey.pk]))

        self.assertEqual(response.status_code, 302)


class ConditionTests(SurveyTestMixin, TestCase):
    """
    Bedingte Anzeige. Schwerpunkt: der Server entscheidet, nicht der Browser.
    """

    def build(self, is_anonymous=True):
        """Umfrage mit Ja/Nein-Frage + bedingter Folgefrage"""
        survey = self.make_survey(is_anonymous=is_anonymous)
        survey.questions.all().delete()

        self.q1 = SurveyQuestion.objects.create(
            survey=survey, order=0, question_type=QuestionType.YESNO,
            text='Waren Sie im Einsatz?', is_required=True,
        )
        self.q2 = SurveyQuestion.objects.create(
            survey=survey, order=1, question_type=QuestionType.TEXTAREA,
            text='Was lief gut?', is_required=True,
            condition_question=self.q1,
            condition_operator='any_of',
            condition_values=['1'],
        )
        return survey

    def submit(self, survey, answers, user=None):
        """`answers` bildet Frage-Objekt -> Wert ab"""
        self.client.force_login(user or self.participant)
        data = {f'question_{question.pk}': value for question, value in answers.items()}
        return self.client.post(reverse('surveys:fill', args=[survey.pk]), data)

    # -- Kernverhalten ---------------------------------------------------

    def test_hidden_required_question_does_not_block_submission(self):
        """
        Der wichtigste Fall: eine ausgeblendete Pflichtfrage darf das Absenden
        nicht verhindern.
        """
        survey = self.build()

        self.submit(survey, {self.q1: '0'})  # "Nein" -> Folgefrage entfällt

        self.assertEqual(SurveyResponse.objects.count(), 1)

    def test_visible_required_question_is_still_enforced(self):
        survey = self.build()

        self.submit(survey, {self.q1: '1'})  # "Ja" -> Folgefrage ist Pflicht

        self.assertEqual(SurveyResponse.objects.count(), 0)

    def test_visible_question_is_saved(self):
        survey = self.build()

        self.submit(survey, {self.q1: '1', self.q2: 'Die Absprache'})

        answers = SurveyAnswer.objects.filter(response__survey=survey)
        self.assertEqual(answers.count(), 2)
        self.assertEqual(answers.get(question=self.q2).value_text, 'Die Absprache')

    def test_answer_to_hidden_question_is_discarded(self):
        """
        Ein manipulierter POST darf keine Antwort auf eine Frage hinterlassen, die
        gar nicht sichtbar war – sonst stünde sie in der Auswertung.
        """
        survey = self.build()

        self.submit(survey, {self.q1: '0', self.q2: 'geschmuggelt'})

        answers = SurveyAnswer.objects.filter(response__survey=survey)
        self.assertEqual(answers.count(), 1)
        self.assertFalse(answers.filter(question=self.q2).exists())

    def test_none_of_operator(self):
        survey = self.build()
        self.q2.condition_operator = 'none_of'
        self.q2.save(update_fields=['condition_operator'])

        # "Ja" -> Bedingung trifft NICHT zu -> Frage verborgen
        self.submit(survey, {self.q1: '1'})
        self.assertEqual(SurveyResponse.objects.count(), 1)
        self.assertEqual(SurveyAnswer.objects.count(), 1)

    def test_unanswered_source_hides_follow_up(self):
        survey = self.build()
        self.q1.is_required = False
        self.q1.save(update_fields=['is_required'])

        self.submit(survey, {})  # gar nichts beantwortet

        self.assertEqual(SurveyResponse.objects.count(), 1)
        self.assertEqual(SurveyAnswer.objects.count(), 0)

    def test_chained_conditions_cascade(self):
        """Wird B ausgeblendet, muss auch das von B abhängige C verschwinden."""
        survey = self.build()
        q3 = SurveyQuestion.objects.create(
            survey=survey, order=2, question_type=QuestionType.TEXT,
            text='Und warum?', is_required=True,
            condition_question=self.q2,
            condition_operator='any_of',
            condition_values=['egal'],
        )

        self.submit(survey, {self.q1: '0', self.q2: 'x', q3: 'y'})

        self.assertEqual(SurveyResponse.objects.count(), 1)
        self.assertEqual(SurveyAnswer.objects.filter(question=q3).count(), 0)

    def test_checkbox_source_matches_single_selection(self):
        survey = self.make_survey()
        survey.questions.all().delete()
        source = SurveyQuestion.objects.create(
            survey=survey, order=0, question_type=QuestionType.CHECKBOX,
            text='Welche Module nutzen Sie?', is_required=False,
            config={'options': ['Kleiderkammer', 'Atemschutz', 'Fahrzeuge']},
        )
        follow_up = SurveyQuestion.objects.create(
            survey=survey, order=1, question_type=QuestionType.TEXT,
            text='Wie oft?', is_required=True,
            condition_question=source, condition_operator='any_of',
            condition_values=['Atemschutz'],
        )

        self.client.force_login(self.participant)
        self.client.post(reverse('surveys:fill', args=[survey.pk]), {
            f'question_{source.pk}': ['Kleiderkammer', 'Atemschutz'],
            f'question_{follow_up.pk}': 'täglich',
        })

        self.assertEqual(SurveyAnswer.objects.filter(question=follow_up).count(), 1)

    def test_condition_on_later_question_falls_back_to_visible(self):
        """
        Sicherheitsnetz: Zeigt eine Bedingung auf eine spätere Frage, wird die Frage
        angezeigt statt stillschweigend verschluckt.
        """
        survey = self.build()
        self.q2.condition_question = self.q1
        SurveyQuestion.objects.filter(pk=self.q1.pk).update(order=5)

        from .conditions import is_visible

        self.q2.refresh_from_db()
        self.assertTrue(is_visible(self.q2, {}))

    # -- Builder ---------------------------------------------------------

    def test_form_rejects_values_not_in_source(self):
        survey = self.build()
        form = SurveyQuestionForm(
            data={
                'text': 'Neue Frage',
                'question_type': QuestionType.TEXT,
                'condition_question': self.q1.pk,
                'condition_operator': 'any_of',
                'condition_values': ['gibtesnicht'],
            },
            survey=survey,
        )
        self.assertFalse(form.is_valid())
        self.assertIn('condition_values', form.errors)

    def test_form_requires_values_when_source_set(self):
        survey = self.build()
        form = SurveyQuestionForm(
            data={
                'text': 'Neue Frage',
                'question_type': QuestionType.TEXT,
                'condition_question': self.q1.pk,
                'condition_operator': 'any_of',
            },
            survey=survey,
        )
        self.assertFalse(form.is_valid())
        self.assertIn('condition_values', form.errors)

    def test_form_rejects_self_reference(self):
        survey = self.build()
        form = SurveyQuestionForm(
            data={
                'text': self.q1.text,
                'question_type': QuestionType.YESNO,
                'condition_question': self.q1.pk,
                'condition_operator': 'any_of',
                'condition_values': ['1'],
            },
            instance=self.q1,
            survey=survey,
        )
        self.assertFalse(form.is_valid())
        self.assertIn('condition_question', form.errors)

    def test_free_text_question_is_no_valid_source(self):
        """Freitext hat keine auswählbaren Antworten – taugt nicht als Bedingung."""
        survey = self.make_survey()
        survey.questions.all().delete()
        text_question = SurveyQuestion.objects.create(
            survey=survey, order=0, question_type=QuestionType.TEXT, text='Name?'
        )
        later = SurveyQuestion.objects.create(
            survey=survey, order=1, question_type=QuestionType.TEXT, text='Weiter?'
        )

        form = SurveyQuestionForm(instance=later, survey=survey)
        self.assertNotIn(
            text_question, form.fields['condition_question'].queryset
        )

    def test_move_is_blocked_when_it_would_break_a_condition(self):
        survey = self.build()

        self.client.force_login(self.conductor)
        # q2 (abhängig) nach oben schieben würde q1 dahinter bringen
        self.client.post(
            reverse('surveys:question_move', args=[self.q2.pk]), {'direction': 'up'}
        )

        self.q1.refresh_from_db()
        self.q2.refresh_from_db()
        self.assertEqual(self.q1.order, 0)
        self.assertEqual(self.q2.order, 1)

    def test_deleting_source_clears_condition(self):
        survey = self.build()

        self.client.force_login(self.conductor)
        self.client.post(reverse('surveys:question_delete', args=[self.q1.pk]))

        self.q2.refresh_from_db()
        self.assertIsNone(self.q2.condition_question_id)
        # Fail-open: die Frage wird jetzt immer angezeigt
        from .conditions import is_visible
        self.assertTrue(is_visible(self.q2, {}))

    # -- Auswertung ------------------------------------------------------

    def test_sparse_conditional_question_is_suppressed(self):
        """
        Eine Folgefrage, die nur wenige gesehen haben, darf nicht einzeln
        ausgewertet werden – sonst ist sie faktisch nicht mehr anonym.
        """
        survey = self.build()
        survey.min_responses_for_results = 3
        survey.save(update_fields=['min_responses_for_results'])

        # Drei Antworten insgesamt, aber nur eine sieht die Folgefrage
        self.submit(survey, {self.q1: '1', self.q2: 'geheim'})
        for index in range(2):
            user = make_user(f'nein{index}', 'participate_survey')
            self.submit(survey, {self.q1: '0'}, user=user)

        stats = {entry['question'].pk: entry for entry in build_question_statistics(survey)}

        self.assertFalse(stats[self.q1.pk]['suppressed'])
        self.assertTrue(stats[self.q2.pk]['suppressed'])
        self.assertEqual(stats[self.q2.pk]['texts'], [])


class BuilderTests(SurveyTestMixin, TestCase):
    def test_questions_locked_after_first_response(self):
        survey = self.make_survey()
        self.fill(survey, self.participant)

        self.client.force_login(self.conductor)
        self.client.post(reverse('surveys:question_delete', args=[survey.questions.first().pk]))

        self.assertEqual(survey.questions.count(), 1)

    def test_question_move_reorders(self):
        survey = self.make_survey()
        second = SurveyQuestion.objects.create(
            survey=survey, order=1, question_type=QuestionType.TEXT, text='Zweite'
        )

        self.client.force_login(self.conductor)
        self.client.post(reverse('surveys:question_move', args=[second.pk]), {'direction': 'up'})

        self.assertEqual(list(survey.questions.values_list('text', flat=True))[0], 'Zweite')

    def test_choice_question_requires_two_options(self):
        form = SurveyQuestionForm(data={
            'text': 'Frage',
            'question_type': QuestionType.RADIO,
            'options_text': 'Nur eine',
            'is_required': True,
        })
        self.assertFalse(form.is_valid())
        self.assertIn('options_text', form.errors)

    def test_duplicate_options_are_rejected(self):
        form = SurveyQuestionForm(data={
            'text': 'Frage',
            'question_type': QuestionType.RADIO,
            'options_text': 'A\nB\nA',
            'is_required': True,
        })
        self.assertFalse(form.is_valid())

    def test_survey_without_questions_cannot_be_activated(self):
        survey = self.make_survey(status=SurveyStatus.DRAFT)
        survey.questions.all().delete()

        self.client.force_login(self.conductor)
        self.client.post(reverse('surveys:set_status', args=[survey.pk]), {'status': 'active'})

        survey.refresh_from_db()
        self.assertEqual(survey.status, SurveyStatus.DRAFT)

    def test_detail_requires_conduct_permission(self):
        survey = self.make_survey()
        self.client.force_login(self.participant)

        response = self.client.get(reverse('surveys:detail', args=[survey.pk]))
        self.assertEqual(response.status_code, 403)
