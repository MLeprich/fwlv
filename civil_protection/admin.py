"""
Civil Protection Admin
Admin-Registrierung für das Bevölkerungsschutz-Modul
"""

from django.contrib import admin
from .models import (
    KatSEquipmentMaster, KatSEquipmentInstance, KatSVehicle,
    KatSMedicationMaster, KatSMedicationBatch, KatSStockMovement,
    KatSInventoryCheck, KatSInventoryCheckItem,
    KatSLending, KatSLendingItem,
)


@admin.register(KatSEquipmentMaster)
class KatSEquipmentMasterAdmin(admin.ModelAdmin):
    list_display = ['master_number', 'name', 'bereich', 'equipment_type', 'is_active']
    list_filter = ['bereich', 'equipment_type', 'is_active', 'requires_maintenance']
    search_fields = ['master_number', 'name', 'manufacturer']


@admin.register(KatSEquipmentInstance)
class KatSEquipmentInstanceAdmin(admin.ModelAdmin):
    list_display = ['inventory_number', 'master', 'bereich', 'location', 'condition', 'is_operational']
    list_filter = ['bereich', 'condition', 'is_operational', 'is_active']
    search_fields = ['inventory_number', 'serial_number', 'master__name']


@admin.register(KatSVehicle)
class KatSVehicleAdmin(admin.ModelAdmin):
    list_display = ['name', 'license_plate', 'bereich', 'vehicle_type', 'status', 'is_active']
    list_filter = ['bereich', 'vehicle_type', 'status', 'is_active']
    search_fields = ['name', 'license_plate', 'call_sign', 'vin']


@admin.register(KatSMedicationMaster)
class KatSMedicationMasterAdmin(admin.ModelAdmin):
    list_display = ['master_number', 'name', 'bereich', 'medication_type', 'is_active']
    list_filter = ['bereich', 'medication_type', 'storage_condition', 'is_active']
    search_fields = ['master_number', 'name', 'active_ingredient', 'pzn']


@admin.register(KatSMedicationBatch)
class KatSMedicationBatchAdmin(admin.ModelAdmin):
    list_display = ['master', 'batch_number', 'bereich', 'expiry_date', 'quantity_remaining', 'is_recalled']
    list_filter = ['bereich', 'is_recalled']
    search_fields = ['batch_number', 'master__name', 'supplier_batch_number']


@admin.register(KatSStockMovement)
class KatSStockMovementAdmin(admin.ModelAdmin):
    list_display = ['movement_type', 'bereich', 'equipment_master', 'medication_master', 'quantity', 'movement_date']
    list_filter = ['bereich', 'movement_type']
    search_fields = ['reference_number', 'notes']


@admin.register(KatSInventoryCheck)
class KatSInventoryCheckAdmin(admin.ModelAdmin):
    list_display = ['check_number', 'title', 'bereich', 'status', 'scheduled_start_date']
    list_filter = ['bereich', 'status', 'check_type']
    search_fields = ['check_number', 'title']


@admin.register(KatSInventoryCheckItem)
class KatSInventoryCheckItemAdmin(admin.ModelAdmin):
    list_display = ['inventory_check', 'item_name', 'expected_quantity', 'actual_quantity', 'has_discrepancy']
    list_filter = ['is_counted', 'has_discrepancy']
    search_fields = ['item_name', 'item_number']


class KatSLendingItemInline(admin.TabularInline):
    model = KatSLendingItem
    extra = 1


@admin.register(KatSLending)
class KatSLendingAdmin(admin.ModelAdmin):
    list_display = ['lending_number', 'borrower_name', 'bereich', 'status', 'lending_date', 'expected_return_date']
    list_filter = ['bereich', 'status']
    search_fields = ['lending_number', 'borrower_name', 'borrower_organization']
    inlines = [KatSLendingItemInline]
