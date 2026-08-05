from django.contrib import admin

from .models import (
    Survey,
    SurveyAnswer,
    SurveyInvitation,
    SurveyParticipation,
    SurveyQuestion,
    SurveyResponse,
)


class SurveyQuestionInline(admin.TabularInline):
    model = SurveyQuestion
    extra = 0
    fields = ['order', 'question_type', 'text', 'is_required']
    ordering = ['order']


@admin.register(Survey)
class SurveyAdmin(admin.ModelAdmin):
    list_display = ['title', 'status', 'is_anonymous', 'access_mode', 'response_count', 'created_at']
    list_filter = ['status', 'is_anonymous', 'access_mode', 'created_at']
    search_fields = ['title', 'description']
    filter_horizontal = ['target_groups']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']
    inlines = [SurveyQuestionInline]

    fieldsets = (
        ('Grunddaten', {
            'fields': ('title', 'description', 'status')
        }),
        ('Anonymität', {
            'fields': ('is_anonymous', 'min_responses_for_results'),
            'description': (
                'Der Anonymitätsmodus ist eine Zusage an die Teilnehmenden. Er sollte '
                'nach der ersten Antwort nicht mehr geändert werden.'
            ),
        }),
        ('Zugang', {
            'fields': ('access_mode', 'pdf_intro_text'),
        }),
        ('Laufzeit & Teilnahme', {
            'fields': (
                'start_date', 'end_date', 'target_groups',
                'allow_multiple_responses', 'show_results_to_participants',
            )
        }),
        ('Metadaten', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',),
        }),
    )

    @admin.display(description='Antworten')
    def response_count(self, obj):
        return obj.response_count

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


class SurveyAnswerInline(admin.TabularInline):
    model = SurveyAnswer
    extra = 0
    fields = ['question', 'value_text', 'value_number', 'value_date', 'value_json']
    readonly_fields = fields
    can_delete = False


@admin.register(SurveyResponse)
class SurveyResponseAdmin(admin.ModelAdmin):
    """
    Nur lesend. Antworten werden ausschließlich über das Frontend erzeugt – ein
    manuelles Anlegen im Admin könnte bei anonymen Umfragen versehentlich einen
    Personenbezug herstellen.
    """
    list_display = ['__str__', 'survey', 'submitted_at', 'is_complete']
    list_filter = ['survey', 'is_complete']
    readonly_fields = ['survey', 'user', 'submitted_at', 'is_complete']
    inlines = [SurveyAnswerInline]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(SurveyParticipation)
class SurveyParticipationAdmin(admin.ModelAdmin):
    list_display = ['survey', 'user', 'participated_on']
    list_filter = ['survey', 'participated_on']
    search_fields = ['user__username', 'user__first_name', 'user__last_name']
    readonly_fields = ['participated_on']


@admin.register(SurveyInvitation)
class SurveyInvitationAdmin(admin.ModelAdmin):
    """
    Nur lesend. Tokens werden über die Umfrage-Oberfläche erzeugt; ein manuelles
    Setzen von `user` könnte bei anonymen Umfragen einen Personenbezug herstellen.
    """
    list_display = ['token', 'survey', 'label', 'is_used', 'used_on']
    list_filter = ['survey', 'is_used']
    search_fields = ['token', 'label']
    readonly_fields = ['survey', 'token', 'user', 'label', 'is_used', 'used_on', 'created_at']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
