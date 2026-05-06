from django.contrib import admin

from .models import IdCard, IdCardAuditLog, IdCardTemplate


@admin.register(IdCardTemplate)
class IdCardTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_portrait', 'is_default', 'is_system', 'is_active', 'updated_at')
    list_filter = ('is_portrait', 'is_default', 'is_system', 'is_active')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by')


@admin.register(IdCard)
class IdCardAdmin(admin.ModelAdmin):
    list_display = ('card_number', 'person', 'type', 'status', 'issued_at', 'valid_until')
    list_filter = ('status', 'type', 'template')
    search_fields = ('card_number', 'person__first_name', 'person__last_name', 'person__personnel_number')
    raw_id_fields = ('person', 'template', 'replaced_by')
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by', 'revoked_at', 'revoked_by')


@admin.register(IdCardAuditLog)
class IdCardAuditLogAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'card', 'action', 'actor')
    list_filter = ('action',)
    search_fields = ('card__card_number',)
    readonly_fields = ('card', 'action', 'actor', 'metadata', 'created_at', 'updated_at')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
