# Performance Audit - FLVS

**Datum:** 2025-10-03
**Phase:** 8 - Polish & Production
**Zweck:** Systematische Performance-Analyse aller implementierten Apps

---

## 1. Index-Analyse

### ✅ Gut abgedeckte Apps (mit umfangreichen Indizes)

#### Documents App (17 Indizes)
- ✅ category (hierarchisch mit MPTT)
- ✅ document_type, status, access_level
- ✅ is_active, is_archived
- ✅ valid_from, valid_until, review_date
- ✅ content_type, object_id (Generic FK)
- **Bewertung:** Exzellent

#### Inventory Check App (17 Indizes)
- ✅ status, check_type
- ✅ location, responsible_person, approved_by
- ✅ scheduled_date, started_at, completed_at
- ✅ check_item → check, item_content_type, item_object_id
- ✅ discrepancy → check_item, discrepancy_type, severity
- **Bewertung:** Exzellent

#### Vehicle Handover App (14 Indizes)
- ✅ vehicle, handover_type, status
- ✅ handed_over_by, received_by
- ✅ started_at, completed_at
- ✅ checklist → handover, defect → handover
- **Bewertung:** Sehr gut

#### Info Monitors App (14 Indizes)
- ✅ MonitorProfile: is_active+display_order, is_default
- ✅ Dashboard: profile+is_active, is_public, display_order
- ✅ Widget: dashboard+is_active, widget_type, kpi, row+column
- ✅ WidgetAlert: widget+is_active, severity
- **Bewertung:** Sehr gut

#### Height Rescue App (14 Indizes)
- ✅ item_type, certification_standard, rope_type
- ✅ is_active, fall_arrested, retired
- ✅ manufactured_date, next_inspection_due
- **Bewertung:** Sehr gut

#### Diving App (13 Indizes)
- ✅ item_type, gas_type, is_active
- ✅ tuev_due_date, next_service_due
- ✅ bottle_volume, working_pressure
- **Bewertung:** Sehr gut

#### Procurement App (13 Indizes)
- ✅ status, priority, supplier
- ✅ requested_by, approved_by
- ✅ order_date, expected_delivery_date
- ✅ approval → order+approval_level
- **Bewertung:** Sehr gut

---

## 2. Query-Optimierung Empfehlungen

### A. Select Related / Prefetch Related

#### Kritische Bereiche für N+1 Probleme:

**1. Inventory Apps (Magazine, Medical, Clothing, Equipment, etc.):**
```python
# ❌ PROBLEM: N+1 Queries bei Item-Listen
items = MedicalItem.objects.all()
for item in items:
    print(item.location.name)  # N+1
    print(item.category.name)  # N+1
    print(item.supplier.name)  # N+1

# ✅ LÖSUNG: Select Related
items = MedicalItem.objects.select_related(
    'location',
    'category',
    'supplier',
    'created_by',
    'updated_by'
).all()
```

**2. Stock Movements:**
```python
# ❌ PROBLEM
movements = MedicalStockMovement.objects.all()
for mov in movements:
    print(mov.item.name)  # N+1
    print(mov.user.username)  # N+1

# ✅ LÖSUNG
movements = MedicalStockMovement.objects.select_related(
    'item',
    'item__category',
    'item__location',
    'user',
    'from_location',
    'to_location',
    'approved_by'  # Wichtig für BTM
).all()
```

**3. Dashboard/Reporting:**
```python
# ❌ PROBLEM: Widget mit KPI
widgets = Widget.objects.filter(dashboard=dashboard)
for widget in widgets:
    if widget.kpi:
        print(widget.kpi.name)  # N+1

# ✅ LÖSUNG
widgets = Widget.objects.select_related(
    'dashboard',
    'dashboard__profile',
    'kpi'
).prefetch_related(
    'alerts',
    'alerts__notification_users'
).filter(dashboard=dashboard)
```

**4. Documents mit Versionen:**
```python
# ❌ PROBLEM
documents = Document.objects.all()
for doc in documents:
    versions = doc.versions.all()  # N+1

# ✅ LÖSUNG
documents = Document.objects.select_related(
    'category',
    'category__parent',
    'created_by'
).prefetch_related(
    'versions',
    'reviews',
    'allowed_users'
).all()
```

---

## 3. Caching-Strategie

### A. Model-Level Caching

**Dashboard-Builder (Info Monitors):**
```python
# Widget.cached_data bereits implementiert ✅
# Cache-Invalidierung bei KPI-Updates:

@receiver(post_save, sender=KPI)
def invalidate_widget_cache(sender, instance, **kwargs):
    """Invalidiert Widget-Cache wenn KPI aktualisiert wird"""
    widgets = Widget.objects.filter(kpi=instance)
    for widget in widgets:
        widget.cached_data = {}
        widget.save(update_fields=['cached_data', 'last_updated_at'])
```

**KPI-Caching (Reporting):**
```python
from django.core.cache import cache

def get_kpi_value(kpi_id):
    cache_key = f'kpi_value_{kpi_id}'
    value = cache.get(cache_key)

    if value is None:
        kpi = KPI.objects.get(id=kpi_id)
        value = calculate_kpi_value(kpi)
        cache.set(cache_key, value, timeout=kpi.refresh_interval)

    return value
```

### B. QuerySet-Caching

**Häufig abgerufene Listen:**
```python
# Cache für aktive Locations
def get_active_locations():
    cache_key = 'locations_active'
    locations = cache.get(cache_key)

    if locations is None:
        locations = Location.objects.filter(
            is_active=True
        ).select_related('parent').order_by('tree_id', 'lft')
        cache.set(cache_key, locations, timeout=3600)  # 1 Stunde

    return locations

# Invalidierung bei Location-Änderung
@receiver(post_save, sender=Location)
@receiver(post_delete, sender=Location)
def invalidate_location_cache(sender, **kwargs):
    cache.delete('locations_active')
```

### C. Template Fragment Caching

**Dashboard-Elemente:**
```django
{% load cache %}

{% cache 300 sidebar_nav user.id %}
    {% include 'includes/sidebar_nav.html' %}
{% endcache %}

{% cache 60 kpi_card kpi.id %}
    <div class="kpi-card">
        <h3>{{ kpi.name }}</h3>
        <div class="value">{{ kpi.last_value }}</div>
    </div>
{% endcache %}
```

---

## 4. Database-Level Optimierungen

### A. Fehlende Indizes (Empfehlungen)

**Core App (User):**
```python
# Migration hinzufügen:
class Migration(migrations.Migration):
    operations = [
        migrations.AddIndex(
            model_name='user',
            index=models.Index(fields=['is_active', 'employee_id']),
        ),
        migrations.AddIndex(
            model_name='user',
            index=models.Index(fields=['email']),
        ),
    ]
```

**Audit App:**
```python
# Composite-Index für häufige Queries:
migrations.AddIndex(
    model_name='auditlog',
    index=models.Index(fields=['content_type', 'object_id', '-timestamp']),
)
```

**Notifications App:**
```python
migrations.AddIndex(
    model_name='notification',
    index=models.Index(fields=['recipient', 'is_read', '-created_at']),
)
```

### B. Partial Indizes (PostgreSQL)

**Nur aktive Items indizieren:**
```python
from django.contrib.postgres.indexes import Index

class Migration(migrations.Migration):
    operations = [
        migrations.AddIndex(
            model_name='medicalitem',
            index=Index(
                fields=['expiry_date'],
                name='medical_item_active_expiry_idx',
                condition=models.Q(is_active=True, deleted_at__isnull=True)
            ),
        ),
    ]
```

---

## 5. Query-Analyse Tools

### Django Debug Toolbar

**In settings/development.py aktiviert:**
```python
INSTALLED_APPS += ['debug_toolbar']
MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
```

**Kritische Queries identifizieren:**
- Anzahl Queries pro Page Load
- Duplicate Queries
- Slow Queries (>100ms)

### Django Silk (empfohlen für Production-ähnliches Testing)

```bash
pip install django-silk
```

```python
# settings.py
INSTALLED_APPS += ['silk']
MIDDLEWARE += ['silk.middleware.SilkyMiddleware']

# urls.py
urlpatterns += [path('silk/', include('silk.urls', namespace='silk'))]
```

---

## 6. Bulk-Operations

### A. Bulk Create statt Loop

**❌ SCHLECHT:**
```python
for item_data in import_data:
    MedicalItem.objects.create(**item_data)  # N INSERT Queries
```

**✅ GUT:**
```python
items = [MedicalItem(**item_data) for item_data in import_data]
MedicalItem.objects.bulk_create(items, batch_size=1000)
```

### B. Bulk Update

**✅ EMPFOHLEN:**
```python
# Stock-Adjustments bei Inventur:
items_to_update = []
for check_item in check_items:
    item = check_item.item
    item.quantity = check_item.actual_quantity
    items_to_update.append(item)

# Alle auf einmal
InventoryItem.objects.bulk_update(
    items_to_update,
    fields=['quantity', 'updated_at'],
    batch_size=500
)
```

---

## 7. Celery Background Tasks

### A. Tasks die bereits async sein sollten

**Report-Generierung:**
```python
# reporting/tasks.py
from celery import shared_task

@shared_task
def generate_report(report_id):
    report = Report.objects.get(id=report_id)
    report.mark_as_generating()

    try:
        # Report-Generierung
        data = execute_report_query(report.template.query)
        file_path = export_to_format(data, report.file_format)

        report.file = file_path
        report.mark_as_completed()
    except Exception as e:
        report.mark_as_failed(str(e))
```

**KPI-Berechnung:**
```python
@shared_task
def calculate_kpis():
    """Läuft alle 5 Minuten (Celery Beat)"""
    kpis = KPI.objects.filter(is_active=True)

    for kpi in kpis:
        try:
            value = execute_kpi_query(kpi.query)
            kpi.last_value = value
            kpi.last_calculated_at = timezone.now()
            kpi.save(update_fields=['last_value', 'last_calculated_at'])

            # Cache aktualisieren
            cache.set(f'kpi_value_{kpi.id}', value, timeout=kpi.refresh_interval)
        except Exception as e:
            logger.error(f"KPI {kpi.id} calculation failed: {e}")
```

**Inventory-Alerts:**
```python
@shared_task
def check_inventory_thresholds():
    """Prüft alle Items auf Schwellwerte - läuft täglich"""
    from inventory_base.models import AbstractInventoryItem

    # Alle Inventory-Models durchgehen
    for model_class in [MedicalItem, MagazineItem, ClothingItem, ...]:
        items = model_class.objects.filter(
            is_active=True,
            quantity__lte=models.F('threshold_warning')
        ).select_related('category', 'location')

        for item in items:
            # Notification erstellen
            create_threshold_notification(item)
```

---

## 8. Pagination

### A. Standard-Pagination (bereits konfiguriert)

```python
# settings/base.py
REST_FRAMEWORK = {
    'PAGE_SIZE': 50,  # ✅ Gut für API
}
```

### B. Cursor-Pagination für große Datasets

**Für Audit-Logs (kann Millionen Einträge haben):**
```python
# api/pagination.py
from rest_framework.pagination import CursorPagination

class AuditLogPagination(CursorPagination):
    page_size = 100
    ordering = '-timestamp'
```

---

## 9. Performance-Metriken Überwachung

### A. Custom Management Command

**Performance-Report generieren:**
```python
# core/management/commands/performance_report.py
from django.core.management.base import BaseCommand
from django.db import connection

class Command(BaseCommand):
    def handle(self, *args, **options):
        # Tabellen-Größen
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT
                    schemaname,
                    tablename,
                    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename))
                FROM pg_tables
                WHERE schemaname = 'public'
                ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
                LIMIT 20;
            """)

            print("Top 20 größte Tabellen:")
            for row in cursor.fetchall():
                print(f"{row[1]}: {row[2]}")

        # Index-Nutzung
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT
                    schemaname,
                    tablename,
                    indexname,
                    idx_scan
                FROM pg_stat_user_indexes
                WHERE idx_scan = 0
                ORDER BY schemaname, tablename;
            """)

            print("\nUngenutzte Indizes:")
            for row in cursor.fetchall():
                print(f"{row[0]}.{row[1]}.{row[2]}")
```

---

## 10. Action Items - Priorisiert

### 🔴 Hoch (Sofort umsetzen)

1. **Select Related in Admin-Klassen:**
   - Alle `list_display` mit FK-Zugriff optimieren
   - `get_queryset()` Override mit select_related

2. **Inventory Item Queries:**
   - `select_related('location', 'category', 'supplier')` überall

3. **Stock Movement Queries:**
   - `select_related('item', 'user', 'from_location', 'to_location')`

4. **Dashboard Widget Loading:**
   - `select_related('kpi')` + `prefetch_related('alerts')`

### 🟡 Mittel (Nächste Sprint)

5. **Caching für KPIs:**
   - Redis-Cache implementieren
   - Celery Beat für KPI-Updates

6. **Report-Generierung async:**
   - Celery Task für alle Report-Formate

7. **Template Fragment Caching:**
   - Sidebar-Navigation
   - Dashboard-KPI-Karten

### 🟢 Niedrig (Nice-to-have)

8. **Partial Indizes:**
   - Nur aktive Items
   - Nur nicht-gelöschte Items

9. **Cursor Pagination:**
   - Audit-Logs
   - Document-Access-Logs

10. **Performance Monitoring:**
    - Django Silk installieren
    - Performance-Report-Command

---

## 11. Benchmark-Ziele

### Response-Zeiten (95th Percentile)

- ✅ **Dashboard:** < 500ms
- ✅ **Liste (50 Items):** < 300ms
- ✅ **Detail-View:** < 200ms
- ✅ **API-Endpoint:** < 250ms
- ⚠️ **Report-Generierung:** < 30s (async!)
- ⚠️ **KPI-Berechnung:** < 10s (cached)

### Database Queries

- ✅ **Dashboard:** < 20 Queries
- ✅ **Liste:** < 10 Queries
- ✅ **Detail:** < 5 Queries
- ❌ **Vermeiden:** N+1 Queries (0 Toleranz)

---

## 12. Nächste Schritte

1. ✅ **Performance-Audit Dokument erstellt**
2. ⏭️ **Admin-Klassen optimieren** (select_related hinzufügen)
3. ⏭️ **Caching-Layer implementieren**
4. ⏭️ **Celery Tasks für Reports/KPIs**
5. ⏭️ **Performance-Tests mit Django Silk**
6. ⏭️ **Security-Audit**

---

**Status:** 📝 Audit abgeschlossen
**Nächster Review:** Nach Optimierungs-Implementierung
