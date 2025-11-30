# Admin Performance Optimization Guide

**Phase 8 - Production Readiness**

---

## Problem: N+1 Queries in Admin

Alle Admin-Klassen die Foreign Keys in `list_display` verwenden, erzeugen N+1 Queries ohne Optimierung.

### Beispiel (VORHER):

```python
@admin.register(MedicalItem)
class MedicalItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'location', 'supplier')
    # Problem: Für jedes Item wird category/location/supplier einzeln abgerufen
    # 1 Query für Items + N Queries für category + N für location + N für supplier
```

### Lösung: get_queryset() Override

```python
@admin.register(MedicalItem)
class MedicalItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'location', 'supplier')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related(
            'category',
            'location',
            'supplier',
            'created_by',
            'updated_by'
        )
    # Nur 1 Query mit JOINs - massiv schneller!
```

---

## Apps die optimiert werden müssen

### 1. Medical Admin (/medical/admin.py)

**MedicalItemAdmin:**
```python
def get_queryset(self, request):
    qs = super().get_queryset(request)
    return qs.select_related(
        'category',
        'location',
        'supplier',
        'created_by',
        'updated_by',
    ).prefetch_related(
        'batches',  # Für batches_count
    )
```

**MedicalStockMovementAdmin:**
```python
def get_queryset(self, request):
    qs = super().get_queryset(request)
    return qs.select_related(
        'item',
        'item__category',
        'from_location',
        'to_location',
        'user',
        'approved_by',  # BTM-Freigabe
        'created_by',
    )
```

**MedicalBatchAdmin:**
```python
def get_queryset(self, request):
    qs = super().get_queryset(request)
    return qs.select_related(
        'item',
        'item__category',
        'item__location',
        'created_by',
    )
```

---

### 2. Magazine Admin (/magazine/admin.py)

**MagazineItemAdmin:**
```python
def get_queryset(self, request):
    qs = super().get_queryset(request)
    return qs.select_related(
        'category',
        'location',
        'supplier',
        'created_by',
        'updated_by',
    )
```

**MagazineStockMovementAdmin:**
```python
def get_queryset(self, request):
    qs = super().get_queryset(request)
    return qs.select_related(
        'item',
        'from_location',
        'to_location',
        'user',
        'created_by',
    )
```

---

### 3. Clothing Admin (/clothing/admin.py)

**ClothingItemAdmin:**
```python
def get_queryset(self, request):
    qs = super().get_queryset(request)
    return qs.select_related(
        'category',
        'location',
        'supplier',
        'created_by',
        'updated_by',
    )
```

**ClothingStockMovementAdmin:**
```python
def get_queryset(self, request):
    qs = super().get_queryset(request)
    return qs.select_related(
        'item',
        'assigned_to',  # Personnel
        'from_location',
        'to_location',
        'user',
        'created_by',
    )
```

**ClothingSizeAssignmentAdmin:**
```python
def get_queryset(self, request):
    qs = super().get_queryset(request)
    return qs.select_related(
        'personnel',
        'personnel__rank',
        'personnel__department',
        'created_by',
    )
```

---

### 4. Equipment Admin (/equipment/admin.py)

**EquipmentItemAdmin:**
```python
def get_queryset(self, request):
    qs = super().get_queryset(request)
    return qs.select_related(
        'category',
        'location',
        'supplier',
        'assigned_vehicle',  # Wichtig!
        'created_by',
        'updated_by',
    )
```

**EquipmentStockMovementAdmin:**
```python
def get_queryset(self, request):
    qs = super().get_queryset(request)
    return qs.select_related(
        'item',
        'assigned_vehicle',
        'from_location',
        'to_location',
        'user',
        'created_by',
    )
```

---

### 5. Workshop Admin (/workshop/admin.py)

**WorkshopItemAdmin:**
```python
def get_queryset(self, request):
    qs = super().get_queryset(request)
    return qs.select_related(
        'category',
        'location',
        'supplier',
        'created_by',
        'updated_by',
    )
```

**VehicleServiceRecordAdmin:**
```python
def get_queryset(self, request):
    qs = super().get_queryset(request)
    return qs.select_related(
        'vehicle',
        'vehicle__location',
        'performed_by',
        'created_by',
    ).prefetch_related(
        'used_parts',  # M2M zu WorkshopItem
    )
```

---

### 6. Disinfection Admin (/disinfection/admin.py)

**DisinfectionItemAdmin:**
```python
def get_queryset(self, request):
    qs = super().get_queryset(request)
    return qs.select_related(
        'category',
        'location',
        'supplier',
        'created_by',
        'updated_by',
    )
```

**DisinfectionLogAdmin:**
```python
def get_queryset(self, request):
    qs = super().get_queryset(request)
    return qs.select_related(
        'item',
        'location',
        'performed_by',
        'created_by',
    )
```

---

### 7. Height Rescue Admin (/height_rescue/admin.py)

**HeightRescueItemAdmin:**
```python
def get_queryset(self, request):
    qs = super().get_queryset(request)
    return qs.select_related(
        'category',
        'location',
        'supplier',
        'created_by',
        'updated_by',
    )
```

**HeightRescueInspectionLogAdmin:**
```python
def get_queryset(self, request):
    qs = super().get_queryset(request)
    return qs.select_related(
        'item',
        'inspector',
        'created_by',
    )
```

---

### 8. Diving Admin (/diving/admin.py)

**DivingItemAdmin:**
```python
def get_queryset(self, request):
    qs = super().get_queryset(request)
    return qs.select_related(
        'category',
        'location',
        'supplier',
        'created_by',
        'updated_by',
    )
```

**DivingServiceLogAdmin:**
```python
def get_queryset(self, request):
    qs = super().get_queryset(request)
    return qs.select_related(
        'item',
        'performed_by',
        'created_by',
    )
```

---

### 9. IT Hardware Admin (/it_hardware/admin.py)

**ITHardwareItemAdmin:**
```python
def get_queryset(self, request):
    qs = super().get_queryset(request)
    return qs.select_related(
        'category',
        'location',
        'supplier',
        'assigned_to',  # User
        'created_by',
        'updated_by',
    )
```

---

### 10. Vehicle Handover Admin (/vehicle_handover/admin.py)

**VehicleHandoverAdmin:**
```python
def get_queryset(self, request):
    qs = super().get_queryset(request)
    return qs.select_related(
        'vehicle',
        'vehicle__location',
        'handed_over_by',
        'received_by',
        'created_by',
    ).prefetch_related(
        'checklist_items',
        'photos',
        'defects',
    )
```

**HandoverDefectAdmin:**
```python
def get_queryset(self, request):
    qs = super().get_queryset(request)
    return qs.select_related(
        'handover',
        'handover__vehicle',
        'reported_by',
        'repaired_by',
        'created_by',
    )
```

---

### 11. Procurement Admin (/procurement/admin.py)

**PurchaseOrderAdmin:**
```python
def get_queryset(self, request):
    qs = super().get_queryset(request)
    return qs.select_related(
        'supplier',
        'requested_by',
        'approved_by',
        'created_by',
    ).prefetch_related(
        'items',
        'approvals',
        'goods_receipts',
    )
```

**GoodsReceiptAdmin:**
```python
def get_queryset(self, request):
    qs = super().get_queryset(request)
    return qs.select_related(
        'order',
        'order__supplier',
        'received_by',
        'created_by',
    ).prefetch_related(
        'items',
    )
```

---

### 12. Inventory Check Admin (/inventory_check/admin.py)

**InventoryCheckAdmin:**
```python
def get_queryset(self, request):
    qs = super().get_queryset(request)
    return qs.select_related(
        'location',
        'responsible_person',
        'approved_by',
        'created_by',
    ).prefetch_related(
        'items',
        'discrepancies',
    )
```

**InventoryDiscrepancyAdmin:**
```python
def get_queryset(self, request):
    qs = super().get_queryset(request)
    return qs.select_related(
        'check_item',
        'check_item__check',
        'reported_by',
        'created_by',
    )
```

---

### 13. Documents Admin (/documents/admin.py)

**DocumentAdmin:**
```python
def get_queryset(self, request):
    qs = super().get_queryset(request)
    return qs.select_related(
        'category',
        'category__parent',
        'content_type',
        'created_by',
        'updated_by',
    ).prefetch_related(
        'versions',
        'allowed_users',
        'reviews',
    )
```

**DocumentVersionAdmin:**
```python
def get_queryset(self, request):
    qs = super().get_queryset(request)
    return qs.select_related(
        'document',
        'document__category',
        'created_by',
    )
```

---

### 14. Reporting Admin (/reporting/admin.py)

**ReportAdmin:**
```python
def get_queryset(self, request):
    qs = super().get_queryset(request)
    return qs.select_related(
        'template',
        'content_type',
        'generated_by',
        'created_by',
    )
```

**ReportScheduleAdmin:**
```python
def get_queryset(self, request):
    qs = super().get_queryset(request)
    return qs.select_related(
        'template',
        'created_by',
    ).prefetch_related(
        'recipients',
    )
```

**KPIAdmin:**
```python
def get_queryset(self, request):
    qs = super().get_queryset(request)
    return qs.select_related(
        'created_by',
        'updated_by',
    )
```

---

### 15. Info Monitors Admin (/info_monitors/admin.py)

**DashboardAdmin:**
```python
def get_queryset(self, request):
    qs = super().get_queryset(request)
    return qs.select_related(
        'profile',
        'created_by',
        'updated_by',
    ).prefetch_related(
        'widgets',
        'allowed_users',
    )
```

**WidgetAdmin:**
```python
def get_queryset(self, request):
    qs = super().get_queryset(request)
    return qs.select_related(
        'dashboard',
        'dashboard__profile',
        'kpi',
        'created_by',
        'updated_by',
    ).prefetch_related(
        'alerts',
    )
```

**WidgetAlertAdmin:**
```python
def get_queryset(self, request):
    qs = super().get_queryset(request)
    return qs.select_related(
        'widget',
        'widget__dashboard',
    ).prefetch_related(
        'notification_users',
    )
```

---

## Implementierungs-Reihenfolge

### Priorität 1 (Sofort):
1. ✅ Medical Admin (BTM-kritisch)
2. ✅ Equipment Admin (viele FK-Referenzen)
3. ✅ Vehicle Handover Admin (komplexe Relationen)
4. ✅ Procurement Admin (Order → Items → Receipts)

### Priorität 2 (Diese Woche):
5. ✅ Documents Admin (viele Prefetch-Relationen)
6. ✅ Inventory Check Admin
7. ✅ Info Monitors Admin
8. ✅ Reporting Admin

### Priorität 3 (Nächste Woche):
9. ✅ Alle Inventory Apps (Magazine, Clothing, Workshop, etc.)

---

## Testing

### Django Debug Toolbar

Nach Implementierung prüfen:

```python
# Vorher: ~100-200 Queries bei Item-Liste
# Nachher: ~5-10 Queries

# URLs mit Debug Toolbar besuchen:
/admin/medical/medicalitem/
/admin/equipment/equipmentitem/
/admin/procurement/purchaseorder/
```

### Query-Count Assert (Tests)

```python
from django.test import TestCase
from django.test.utils import override_settings
from django.db import connection
from django.test.utils import CaptureQueriesContext

class AdminPerformanceTest(TestCase):
    def test_medical_item_list_queries(self):
        """Admin-Liste sollte < 10 Queries haben"""
        # 50 Items erstellen
        items = [MedicalItemFactory() for _ in range(50)]

        with CaptureQueriesContext(connection) as context:
            response = self.client.get('/admin/medical/medicalitem/')

        # Max 10 Queries erlaubt
        self.assertLess(len(context), 10,
            f"Too many queries: {len(context)}")
```

---

## Performance-Gewinn Schätzung

| Admin                     | Vorher (Queries) | Nachher (Queries) | Verbesserung |
|---------------------------|------------------|-------------------|--------------|
| MedicalItem (50 Items)    | ~250             | ~5                | **98%**      |
| EquipmentItem (100 Items) | ~400             | ~7                | **98%**      |
| PurchaseOrder (20 Orders) | ~100             | ~8                | **92%**      |
| Document (50 Docs)        | ~200             | ~6                | **97%**      |

**Gesamt-Performance-Gewinn: ~95-98% weniger Database Queries**

---

## Wartung

Nach Hinzufügen neuer Foreign Keys zu `list_display`:
1. ✅ get_queryset() aktualisieren
2. ✅ select_related() für FK
3. ✅ prefetch_related() für M2M/Reverse-FK
4. ✅ Debug Toolbar prüfen

**Code-Review-Checklist:**
- [ ] Neue FK in list_display → get_queryset() erweitert?
- [ ] Neue M2M in list_display → prefetch_related() hinzugefügt?
- [ ] Query-Count < 10 für Standard-Listen?

---

**Status:** 📋 Guide erstellt - Ready für Implementierung
**Geschätzte Implementierungszeit:** 2-3 Stunden für alle Apps
**Erwarteter Performance-Gewinn:** 95-98% Query-Reduktion
