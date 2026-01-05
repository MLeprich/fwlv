"""
Personnel Admin Configuration
Admin-Interface für Personal-Stammdaten und Qualifikationen
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from .models import (
    Person, Qualification, QualificationTemplate, Training, TrainingParticipant,
    Inspection, DutyHoursEntry, DutyHoursRequirement,
    Rank, PersonRank, ServiceInterruption, OrganizationType
)


class QualificationInline(admin.TabularInline):
    """
    Inline-Admin für Qualifikationen innerhalb der Person-Detailansicht
    """
    model = Qualification
    extra = 0
    fields = [
        'qualification_type',
        'name',
        'issue_date',
        'expiry_date',
        'is_active',
        'certificate_number',
    ]
    readonly_fields = []

    def get_readonly_fields(self, request, obj=None):
        """Audit-Felder sind nur lesbar"""
        if obj:  # Editing
            return ['created_at', 'created_by', 'updated_at', 'updated_by']
        return []


class PersonRankInline(admin.TabularInline):
    """
    Inline-Admin für Dienstgrade innerhalb der Person-Detailansicht
    """
    model = PersonRank
    extra = 0
    fields = [
        'rank',
        'since_date',
        'is_current',
        'promoted_by',
        'certificate_number',
    ]


class ServiceInterruptionInline(admin.TabularInline):
    """
    Inline-Admin für Dienstunterbrechungen innerhalb der Person-Detailansicht
    """
    model = ServiceInterruption
    extra = 0
    fields = [
        'organization_type',
        'interruption_type',
        'start_date',
        'end_date',
        'other_department_name',
        'reason',
    ]


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    """
    Admin-Interface für Person-Stammdaten
    """
    list_display = [
        'personnel_number',
        'get_full_name_display',
        'department',
        'rank',
        'is_active',
        'qualification_count',
        'has_user_account',
    ]

    list_filter = [
        'is_active',
        'department',
        'rank',
        'entry_date',
        'is_youth_fire_brigade',
        'is_volunteer_fire_brigade',
        'is_professional_fire_brigade',
    ]

    search_fields = [
        'personnel_number',
        'first_name',
        'last_name',
        'email',
        'department',
    ]

    fieldsets = (
        (_('Persönliche Daten'), {
            'fields': (
                'first_name',
                'last_name',
                'personnel_number',
                'date_of_birth',
                'photo',
            )
        }),
        (_('Kontaktdaten'), {
            'fields': (
                'email',
                'phone',
                'mobile',
            )
        }),
        (_('Adresse'), {
            'fields': (
                'street',
                'house_number',
                'postal_code',
                'city',
            ),
            'classes': ('collapse',),
        }),
        (_('Organisatorisch'), {
            'fields': (
                'department',
                'rank',
                'function',
                'entry_date',
                'exit_date',
            )
        }),
        (_('Feuerwehr-Organisationen'), {
            'fields': (
                'is_youth_fire_brigade',
                'youth_entry_date',
                'youth_exit_date',
                'is_volunteer_fire_brigade',
                'volunteer_entry_date',
                'volunteer_unit',
                'is_professional_fire_brigade',
                'professional_entry_date',
                'previous_fire_department',
                'previous_fire_department_entry_date',
                'previous_fire_department_exit_date',
            ),
            'classes': ('collapse',),
        }),
        (_('System'), {
            'fields': (
                'is_active',
                'user',
                'notes',
            )
        }),
    )

    readonly_fields = []

    inlines = [QualificationInline, PersonRankInline, ServiceInterruptionInline]

    date_hierarchy = 'entry_date'

    ordering = ['last_name', 'first_name']

    def get_full_name_display(self, obj):
        """Vollständiger Name für List-Display"""
        return obj.get_full_name()
    get_full_name_display.short_description = _('Name')
    get_full_name_display.admin_order_field = 'last_name'

    def qualification_count(self, obj):
        """Anzahl aktiver Qualifikationen"""
        count = obj.qualifications.filter(is_active=True).count()
        if count > 0:
            return format_html(
                '<span style="color: green; font-weight: bold;">{}</span>',
                count
            )
        return format_html('<span style="color: gray;">0</span>')
    qualification_count.short_description = _('Qualifikationen')

    def has_user_account(self, obj):
        """Zeigt an ob Person einen User-Account hat"""
        if obj.user:
            return format_html(
                '<span style="color: green;">✓</span>'
            )
        return format_html('<span style="color: gray;">—</span>')
    has_user_account.short_description = _('Account')
    has_user_account.boolean = True

    def get_readonly_fields(self, request, obj=None):
        """Audit-Felder sind nur lesbar"""
        if obj:  # Editing
            return ['created_at', 'created_by', 'updated_at', 'updated_by']
        return []


@admin.register(QualificationTemplate)
class QualificationTemplateAdmin(admin.ModelAdmin):
    """
    Admin-Interface für Qualifikations-Vorlagen
    """
    list_display = [
        'name',
        'qualification_type',
        'default_validity_days',
        'default_issuing_authority',
        'is_active',
        'usage_count',
    ]

    list_filter = [
        'qualification_type',
        'is_active',
    ]

    search_fields = [
        'name',
        'description',
        'default_issuing_authority',
    ]

    fieldsets = (
        (_('Qualifikation'), {
            'fields': (
                'name',
                'qualification_type',
                'description',
            )
        }),
        (_('Standard-Werte'), {
            'fields': (
                'default_validity_days',
                'default_issuing_authority',
            )
        }),
        (_('System'), {
            'fields': (
                'is_active',
                'notes',
            )
        }),
    )

    ordering = ['name']

    def usage_count(self, obj):
        """Anzahl der Verwendungen"""
        count = obj.qualifications.count()
        if count > 0:
            return format_html(
                '<span style="color: green; font-weight: bold;">{}</span>',
                count
            )
        return format_html('<span style="color: gray;">0</span>')
    usage_count.short_description = _('Verwendet')


@admin.register(Qualification)
class QualificationAdmin(admin.ModelAdmin):
    """
    Admin-Interface für Qualifikationen
    (Standalone-View, zusätzlich zum Inline)
    """
    list_display = [
        'person',
        'name',
        'qualification_type',
        'issue_date',
        'expiry_date',
        'is_active',
        'expiry_status',
    ]

    list_filter = [
        'qualification_type',
        'is_active',
        'issue_date',
        'expiry_date',
    ]

    search_fields = [
        'name',
        'description',
        'certificate_number',
        'person__first_name',
        'person__last_name',
        'person__personnel_number',
    ]

    fieldsets = (
        (_('Zuordnung'), {
            'fields': (
                'person',
                'qualification_type',
            )
        }),
        (_('Qualifikation'), {
            'fields': (
                'name',
                'description',
                'issuing_authority',
                'certificate_number',
            )
        }),
        (_('Gültigkeit'), {
            'fields': (
                'issue_date',
                'expiry_date',
                'is_active',
            )
        }),
        (_('Dokumente'), {
            'fields': (
                'certificate_file',
                'notes',
            ),
            'classes': ('collapse',),
        }),
    )

    readonly_fields = []

    date_hierarchy = 'issue_date'

    ordering = ['-issue_date']

    def expiry_status(self, obj):
        """Zeigt Ablauf-Status mit Farbe"""
        if not obj.expiry_date:
            return format_html(
                '<span style="color: gray;">Unbefristet</span>'
            )

        if obj.is_expired():
            return format_html(
                '<span style="color: red; font-weight: bold;">Abgelaufen</span>'
            )

        if obj.is_expiring_soon(days=30):
            return format_html(
                '<span style="color: orange; font-weight: bold;">Läuft bald ab</span>'
            )

        return format_html(
            '<span style="color: green;">Gültig</span>'
        )
    expiry_status.short_description = _('Status')

    def get_readonly_fields(self, request, obj=None):
        """Audit-Felder sind nur lesbar"""
        if obj:  # Editing
            return ['created_at', 'created_by', 'updated_at', 'updated_by']
        return []


class TrainingParticipantInline(admin.TabularInline):
    """
    Inline-Admin für Teilnehmer innerhalb der Training-Detailansicht
    """
    model = TrainingParticipant
    extra = 0
    fields = [
        'person',
        'status',
        'passed',
        'certificate_issued',
    ]
    autocomplete_fields = ['person']


@admin.register(Training)
class TrainingAdmin(admin.ModelAdmin):
    """
    Admin-Interface für Schulungen
    """
    list_display = [
        'title',
        'start_date',
        'end_date',
        'status',
        'location',
        'participant_count_display',
    ]

    list_filter = [
        'status',
        'training_type',
        'start_date',
    ]

    search_fields = [
        'title',
        'description',
        'location',
        'organizer',
        'instructor',
    ]

    fieldsets = (
        (_('Schulungsdetails'), {
            'fields': (
                'title',
                'description',
                'training_type',
                'status',
            )
        }),
        (_('Datum & Zeit'), {
            'fields': (
                'start_date',
                'start_time',
                'end_date',
                'end_time',
            )
        }),
        (_('Ort & Organisation'), {
            'fields': (
                'location',
                'organizer',
                'instructor',
            )
        }),
        (_('Teilnehmer'), {
            'fields': (
                'max_participants',
            )
        }),
        (_('Kosten & Dokumente'), {
            'fields': (
                'cost_per_participant',
                'training_materials',
                'notes',
            ),
            'classes': ('collapse',),
        }),
    )

    readonly_fields = []

    inlines = [TrainingParticipantInline]

    date_hierarchy = 'start_date'

    ordering = ['-start_date']

    def participant_count_display(self, obj):
        """Anzahl Teilnehmer anzeigen"""
        count = obj.get_participant_count()
        max_count = obj.max_participants
        if max_count:
            color = 'green' if count < max_count else 'red'
            return format_html(
                '<span style="color: {};">{} / {}</span>',
                color, count, max_count
            )
        return format_html('<span>{}</span>', count)
    participant_count_display.short_description = _('Teilnehmer')

    def get_readonly_fields(self, request, obj=None):
        """Audit-Felder sind nur lesbar"""
        if obj:  # Editing
            return ['created_at', 'created_by', 'updated_at', 'updated_by']
        return []


@admin.register(TrainingParticipant)
class TrainingParticipantAdmin(admin.ModelAdmin):
    """
    Admin-Interface für Schulungsteilnahmen
    """
    list_display = [
        'person',
        'training',
        'status',
        'registration_date',
        'passed',
        'certificate_issued',
    ]

    list_filter = [
        'status',
        'passed',
        'certificate_issued',
        'registration_date',
    ]

    search_fields = [
        'person__first_name',
        'person__last_name',
        'person__personnel_number',
        'training__title',
    ]

    fieldsets = (
        (_('Zuordnung'), {
            'fields': (
                'training',
                'person',
                'status',
            )
        }),
        (_('Ergebnis'), {
            'fields': (
                'passed',
                'certificate_issued',
                'notes',
            )
        }),
    )

    readonly_fields = ['registration_date']

    date_hierarchy = 'registration_date'

    ordering = ['-registration_date']

    autocomplete_fields = ['person', 'training']

    def get_readonly_fields(self, request, obj=None):
        """Audit-Felder sind nur lesbar"""
        readonly = ['registration_date']
        if obj:  # Editing
            readonly.extend(['created_at', 'created_by', 'updated_at', 'updated_by'])
        return readonly


@admin.register(Inspection)
class InspectionAdmin(admin.ModelAdmin):
    """
    Admin-Interface für Prüfungen
    """
    list_display = [
        'person',
        'title',
        'inspection_type',
        'scheduled_date',
        'status',
        'passed',
        'completed_date',
    ]

    list_filter = [
        'inspection_type',
        'status',
        'passed',
        'scheduled_date',
    ]

    search_fields = [
        'title',
        'description',
        'person__first_name',
        'person__last_name',
        'person__personnel_number',
        'examiner',
    ]

    fieldsets = (
        (_('Zuordnung'), {
            'fields': (
                'person',
                'inspection_type',
            )
        }),
        (_('Prüfungsdetails'), {
            'fields': (
                'title',
                'description',
                'examiner',
            )
        }),
        (_('Termine'), {
            'fields': (
                'scheduled_date',
                'completed_date',
                'next_inspection_date',
                'interval_months',
            )
        }),
        (_('Status & Ergebnis'), {
            'fields': (
                'status',
                'passed',
                'result_notes',
            )
        }),
        (_('Dokumente'), {
            'fields': (
                'certificate_file',
                'notes',
            ),
            'classes': ('collapse',),
        }),
    )

    readonly_fields = []

    date_hierarchy = 'scheduled_date'

    ordering = ['-scheduled_date']

    autocomplete_fields = ['person']

    def get_readonly_fields(self, request, obj=None):
        """Audit-Felder sind nur lesbar"""
        if obj:  # Editing
            return ['created_at', 'created_by', 'updated_at', 'updated_by']
        return []


@admin.register(DutyHoursEntry)
class DutyHoursEntryAdmin(admin.ModelAdmin):
    """
    Admin-Interface für Pflichtstunden-Einträge
    """
    list_display = [
        'person',
        'title',
        'category',
        'date',
        'hours',
        'year',
        'confirmed',
        'supervisor',
    ]

    list_filter = [
        'category',
        'confirmed',
        'year',
        'date',
    ]

    search_fields = [
        'title',
        'description',
        'person__first_name',
        'person__last_name',
        'person__personnel_number',
        'supervisor',
    ]

    fieldsets = (
        (_('Zuordnung'), {
            'fields': (
                'person',
                'category',
            )
        }),
        (_('Details'), {
            'fields': (
                'title',
                'description',
                'date',
                'hours',
                'supervisor',
            )
        }),
        (_('Bestätigung'), {
            'fields': (
                'confirmed',
                'confirmed_date',
            )
        }),
        (_('Dokumente'), {
            'fields': (
                'certificate_file',
                'notes',
            ),
            'classes': ('collapse',),
        }),
    )

    readonly_fields = ['year', 'confirmed_date']

    date_hierarchy = 'date'

    ordering = ['-date']

    autocomplete_fields = ['person']

    def get_readonly_fields(self, request, obj=None):
        """Audit-Felder sind nur lesbar"""
        readonly = ['year', 'confirmed_date']
        if obj:  # Editing
            readonly.extend(['created_at', 'created_by', 'updated_at', 'updated_by'])
        return readonly


@admin.register(DutyHoursRequirement)
class DutyHoursRequirementAdmin(admin.ModelAdmin):
    """
    Admin-Interface für Pflichtstunden-Anforderungen
    """
    list_display = [
        'category',
        'year',
        'required_hours',
        'is_active',
    ]

    list_filter = [
        'category',
        'year',
        'is_active',
    ]

    search_fields = [
        'category',
        'description',
    ]

    fieldsets = (
        (_('Anforderung'), {
            'fields': (
                'category',
                'year',
                'required_hours',
                'description',
            )
        }),
        (_('Status'), {
            'fields': (
                'is_active',
            )
        }),
    )

    ordering = ['-year', 'category']

    list_editable = ['is_active']


@admin.register(Rank)
class RankAdmin(admin.ModelAdmin):
    """
    Admin-Interface für Dienstgrade
    """
    list_display = [
        'name',
        'abbreviation',
        'organization_type',
        'sort_order',
        'min_years_in_previous',
        'min_total_years',
        'is_functional_rank',
        'is_active',
    ]

    list_filter = [
        'organization_type',
        'is_functional_rank',
        'is_active',
    ]

    search_fields = [
        'name',
        'abbreviation',
        'description',
        'requires_course',
    ]

    fieldsets = (
        (_('Dienstgrad'), {
            'fields': (
                'name',
                'abbreviation',
                'organization_type',
                'sort_order',
            )
        }),
        (_('Beförderungsvoraussetzungen'), {
            'fields': (
                'min_years_in_previous',
                'min_total_years',
                'requires_course',
            )
        }),
        (_('Details'), {
            'fields': (
                'is_functional_rank',
                'description',
            )
        }),
        (_('Status'), {
            'fields': (
                'is_active',
            )
        }),
    )

    ordering = ['organization_type', 'sort_order']

    list_editable = ['sort_order', 'is_active']


@admin.register(PersonRank)
class PersonRankAdmin(admin.ModelAdmin):
    """
    Admin-Interface für Dienstgrade von Personen
    """
    list_display = [
        'person',
        'rank',
        'since_date',
        'is_current',
        'promoted_by',
    ]

    list_filter = [
        'rank__organization_type',
        'rank',
        'is_current',
        'since_date',
    ]

    search_fields = [
        'person__first_name',
        'person__last_name',
        'person__personnel_number',
        'rank__name',
        'promoted_by',
        'certificate_number',
    ]

    fieldsets = (
        (_('Zuordnung'), {
            'fields': (
                'person',
                'rank',
                'since_date',
                'is_current',
            )
        }),
        (_('Details'), {
            'fields': (
                'promoted_by',
                'certificate_number',
                'certificate_file',
            )
        }),
        (_('Notizen'), {
            'fields': (
                'notes',
            ),
            'classes': ('collapse',),
        }),
    )

    readonly_fields = []

    date_hierarchy = 'since_date'

    ordering = ['-since_date']

    autocomplete_fields = ['person', 'rank']

    def get_readonly_fields(self, request, obj=None):
        """Audit-Felder sind nur lesbar"""
        if obj:  # Editing
            return ['created_at', 'created_by', 'updated_at', 'updated_by']
        return []


@admin.register(ServiceInterruption)
class ServiceInterruptionAdmin(admin.ModelAdmin):
    """
    Admin-Interface für Dienstunterbrechungen
    """
    list_display = [
        'person',
        'organization_type',
        'interruption_type',
        'start_date',
        'end_date',
        'duration_display',
        'is_active_display',
    ]

    list_filter = [
        'organization_type',
        'interruption_type',
        'start_date',
    ]

    search_fields = [
        'person__first_name',
        'person__last_name',
        'person__personnel_number',
        'other_department_name',
        'reason',
    ]

    fieldsets = (
        (_('Zuordnung'), {
            'fields': (
                'person',
                'organization_type',
                'interruption_type',
            )
        }),
        (_('Zeitraum'), {
            'fields': (
                'start_date',
                'end_date',
            )
        }),
        (_('Details'), {
            'fields': (
                'other_department_name',
                'reason',
            )
        }),
        (_('Notizen'), {
            'fields': (
                'notes',
            ),
            'classes': ('collapse',),
        }),
    )

    readonly_fields = []

    date_hierarchy = 'start_date'

    ordering = ['-start_date']

    autocomplete_fields = ['person']

    def duration_display(self, obj):
        """Zeigt die Dauer der Unterbrechung"""
        days = obj.get_duration_days()
        years = days / 365.25
        if years >= 1:
            return f"{years:.1f} Jahre"
        months = days / 30.44
        if months >= 1:
            return f"{months:.1f} Monate"
        return f"{days} Tage"
    duration_display.short_description = _('Dauer')

    def is_active_display(self, obj):
        """Zeigt ob Unterbrechung noch aktiv ist"""
        if obj.is_active():
            return format_html('<span style="color: orange; font-weight: bold;">Aktiv</span>')
        return format_html('<span style="color: green;">Beendet</span>')
    is_active_display.short_description = _('Status')

    def get_readonly_fields(self, request, obj=None):
        """Audit-Felder sind nur lesbar"""
        if obj:  # Editing
            return ['created_at', 'created_by', 'updated_at', 'updated_by']
        return []
