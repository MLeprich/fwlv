# Permission System - Implementation Status

**Datum:** 22. Oktober 2025
**Status:** ✅ Foundation Phase abgeschlossen
**Nächste Phase:** User Management UI + Modul-Integration

---

## 📋 Was wurde heute implementiert

### ✅ Phase 1: Permission Foundation (ABGESCHLOSSEN)

#### 1. Core Components
- ✅ **permissions/constants.py** (730 Zeilen)
  - Zentrale SSOT für alle Berechtigungen
  - 17 Rollen definiert (Roles class)
  - Alle Module und Actions
  - Custom Permissions für BTM, Bestellfreigaben, etc.
  - Approval Limits (1.000€, 5.000€, unbegrenzt)
  - Audit Actions für Logging
  - Utility Functions

- ✅ **permissions/models.py** (461 Zeilen)
  - `TimeBasedPermission` - Zeitbasierte Zugriffsbeschränkungen
    - Datum-Bereich (valid_from_date, valid_to_date)
    - Uhrzeit-Fenster (valid_from_time, valid_to_time)
    - Wochentage (JSON Array)
    - Vollständige Validation

  - `Delegation` - Vertretungsregelungen
    - Delegator/Delegate Beziehungen
    - Zeitbasiert (valid_from, valid_to)
    - Alle Permissions oder spezifisch
    - Genehmigungsworkflow
    - Vorzeitiges Beenden möglich

  - `ObjectPermission` - Object-Level Permissions
    - Ergänzt django-guardian
    - Ablaufdatum möglich
    - Generic Object-Referenz

- ✅ **permissions/backends.py** (570 Zeilen)
  - `CombinedPermissionBackend` (AKTIV in settings.py)
    - Vereint Standard + Zeitbasiert + Delegation
    - Optimiert für Production
  - `TimeBasedPermissionBackend`
  - `DelegationPermissionBackend`
  - `ObjectLevelPermissionBackend`
  - Helper Functions:
    - `check_delegation_active(user)`
    - `get_active_delegations(user)`
    - `cleanup_expired_delegations()` (für Cron)

#### 2. View Protection

- ✅ **permissions/decorators.py** (318 Zeilen)
  - Bestehende erweitert:
    - `@module_permission_required(module)`
    - `@role_required(*roles)`
    - `@btm_permission_required`

  - Neu implementiert:
    - `@require_2fa` - 2FA-Pflicht
    - `@require_witness(permission)` - Vier-Augen-Prinzip für BTM
    - `@audit_action(type, get_info)` - Auto-Logging
    - `@time_based_access_required` - Zeitprüfung
    - `@delegation_allowed` - Zeigt Delegation in UI
    - `@permission_required_with_fallback(perm, fallbacks)` - Alternative Permissions

- ✅ **permissions/mixins.py** (300 Zeilen)
  - Bestehende erweitert:
    - `ModulePermissionMixin`
    - `ObjectPermissionMixin`
    - `BTMPermissionMixin`
    - `RoleRequiredMixin`

  - Neu implementiert:
    - `BTMSecurityMixin` - BTM mit 2FA + IP-Logging + Audit
    - `TimeBasedAccessMixin` - Zeitprüfung
    - `DelegationAwareMixin` - Delegation-Info im Context
    - `AuditMixin` - Auto-Logging bei CRUD
    - `OwnershipMixin` - Nur eigene Objekte bearbeiten
    - `ApprovalRequiredMixin` - Freigabe-Workflows

#### 3. Template Integration

- ✅ **permissions/templatetags/permission_tags.py** (343 Zeilen)
  - Bestehende:
    - `has_module_permission`, `has_role`, `is_btm_authorized`
    - `can_add`, `can_change`, `can_delete`

  - Neu: 20+ Template Tags
    - `can_edit_object`, `can_delete_object` - Object-Level
    - `has_delegation` - Prüft Delegationen
    - `get_delegator_names` - Namen der Vertretenen
    - `has_time_based_access` - Zeitprüfung
    - `user_roles` - Alle Rollen
    - `user_has_any_role` - Mehrere Rollen prüfen
    - `is_owner` - Besitzer-Check
    - `permission_debug_info` - Debug-Info (DEV only)
    - `show_user_roles` - Rollen als Badges
    - `show_delegation_info` - Delegation-Widget
    - `get_permission_display` - Lesbare Namen
    - `check_approval_permission` - Freigabe-Check

#### 4. Management & Utilities

- ✅ **management/commands/setup_permissions.py** (590 Zeilen)
  - Erstellt automatisch alle 17 Gruppen
  - Weist korrekte Permissions zu
  - Optionen:
    - `--reset` - Löscht alle Gruppen vorher
    - `--dry-run` - Simulation ohne Änderungen
  - Detaillierte Zusammenfassung
  - ✅ **Erfolgreich ausgeführt:** 17 Gruppen erstellt

- ✅ **permissions/utils.py** (650 Zeilen)
  - `PermissionHelper` Class mit Methoden:
    - `assign_role(user, role)` - Rolle zuweisen
    - `remove_role(user, role)` - Rolle entfernen
    - `assign_module_responsibility(user, module)` - Modulverantwortlich machen
    - `assign_location_management(user, location)` - Lagerort-Rechte
    - `get_user_modules(user)` - Module des Users
    - `check_btm_clearance(user)` - Umfassender BTM-Check
    - `get_approval_limit(user)` - Freigabelimit ermitteln
    - `can_approve_order(user, amount)` - Freigabe-Check
    - `get_user_permission_summary(user)` - Komplette Übersicht
    - `create_delegation(...)` - Vertretung erstellen
    - `end_delegation(delegation)` - Vertretung beenden

  - Standalone Functions:
    - `get_users_by_role(role)`
    - `get_btm_authorized_users()`
    - `get_module_responsible_users(module)`
    - `get_approvers_for_amount(amount)`
    - `has_any_inventory_permission(user)`
    - `get_permission_conflicts(user)` - Konflikt-Erkennung

#### 5. Database & Configuration

- ✅ **Migrations**
  - `permissions/migrations/0001_initial.py` erstellt
  - ✅ Erfolgreich migriert (3 Tabellen)

- ✅ **Settings aktualisiert**
  - `flvs_project/settings/base.py`:
    ```python
    AUTHENTICATION_BACKENDS = (
        'permissions.backends.CombinedPermissionBackend',  # AKTIV
        'guardian.backends.ObjectPermissionBackend',
        'django.contrib.auth.backends.ModelBackend',
    )
    ```

---

## 📊 Erstellte Gruppen/Rollen

| Gruppe | Permissions | User | Status |
|--------|-------------|------|--------|
| Administrator | 667 | 0 | ✅ |
| BTM-Beauftragter | 34 | 0 | ✅ |
| Werkstattmeister | 38 | 0 | ✅ |
| Modulverantwortlicher Medical | 34 | 0 | ✅ |
| Modulverantwortlicher Clothing | 25 | 0 | ✅ |
| Modulverantwortlicher Magazine | 21 | 0 | ✅ |
| Modulverantwortlicher Workshop | 33 | 0 | ✅ |
| Modulverantwortlicher Disinfection | 20 | 0 | ✅ |
| Modulverantwortlicher Height Rescue | 53 | 0 | ✅ |
| Modulverantwortlicher Diving | 53 | 0 | ✅ |
| Modulverantwortlicher Equipment | 53 | 0 | ✅ |
| Modulverantwortlicher IT Hardware | 25 | 0 | ✅ |
| Lagerverwalter | 17 | 0 | ✅ |
| Wachleiter | 81 | 0 | ✅ |
| Sachbearbeiter | 166 | 0 | ✅ |
| Standard-Nutzer | 14 | 0 | ✅ |

**Gesamt:** 17 Gruppen | 1.334 Permission-Zuweisungen

---

## 🎯 Nächste Schritte (Priorisiert)

### Phase 2A: User Management UI (Höchste Priorität)

#### Ziel: Admins können Rollen zuweisen und Permissions verwalten

**Zu erstellen:**

1. **Admin Views (core/views/user_management.py)**
   ```python
   # URLs: /admin/users/
   - UserListView          # Liste aller User
   - UserDetailView        # User-Details + Rollen + Permissions
   - UserRoleAssignView    # Rollen zuweisen/entfernen
   - DelegationListView    # Vertretungen verwalten
   - DelegationCreateView  # Neue Vertretung
   - PermissionAuditView   # Permission-Log
   ```

2. **Forms (core/forms/permission_forms.py)**
   ```python
   - RoleAssignmentForm    # Multi-Select für Rollen
   - DelegationForm        # Vertretung erstellen
   - TimePermissionForm    # Zeitbasierte Permission
   ```

3. **Templates (templates/core/user_management/)**
   ```
   - user_list.html        # User-Übersicht mit Rollen
   - user_detail.html      # Detail mit Permission-Cards
   - role_assignment.html  # HTMX Modal für Rollen
   - delegation_list.html  # Vertretungen
   - delegation_form.html  # Vertretungs-Modal
   ```

4. **URLs (core/urls.py)**
   ```python
   path('admin/users/', include([
       path('', UserListView, name='user_list'),
       path('<int:pk>/', UserDetailView, name='user_detail'),
       path('<int:pk>/roles/', UserRoleAssignView, name='assign_roles'),
       # ...
   ]))
   ```

**Permissions benötigt:**
- `core.manage_users` - User verwalten
- `core.assign_roles` - Rollen zuweisen
- `core.view_audit_log` - Audit-Log sehen

**Schätzung:** 2-3 Tage

---

### Phase 2B: Delegation Management UI

**Zu erstellen:**

1. **Views**
   - Delegation-Übersicht (aktive, abgelaufene)
   - Delegation erstellen (mit Datum-Picker)
   - Delegation genehmigen (für Vorgesetzte)
   - Delegation vorzeitig beenden

2. **Features**
   - Kalender-View für Delegationen
   - Email-Benachrichtigungen (wenn Delegation startet/endet)
   - Automatische Deaktivierung abgelaufener Delegationen (Celery-Task)

**Schätzung:** 1-2 Tage

---

### Phase 3: Modul-Integration (Iterativ)

**Pro Modul (z.B. Medical):**

1. **Custom Permissions in models.py definieren**
   ```python
   class Medication(models.Model):
       class Meta:
           permissions = [
               ('dispense_medication', 'Kann Medikamente ausgeben'),
               ('view_btm_medication', 'Kann BTM einsehen'),
               # ...
           ]
   ```

2. **Views schützen**
   ```python
   @permission_required('medical.view_medication')
   @time_based_access_required
   def medication_list(request):
       ...
   ```

3. **Templates anpassen**
   ```django
   {% if request.user|has_module_permission:'medical' %}
     <a href="...">Medikamente</a>
   {% endif %}
   ```

4. **Tests schreiben**
   ```python
   def test_btm_access_requires_permission(self):
       # User ohne BTM-Rolle
       response = self.client.get('/medical/btm/')
       self.assertEqual(response.status_code, 403)
   ```

**Reihenfolge:**
1. Locations (simpel, brauchen alle)
2. Personnel (für Audit-Trail)
3. Magazine (einfachstes Lager-Modul)
4. Medical (komplex wegen BTM)
5. Weitere Module...

**Schätzung pro Modul:** 0.5-1 Tag

---

### Phase 4: BTM Vier-Augen-Prinzip (Kritisch)

**Zu implementieren:**

1. **Witness-Validation UI**
   - Modal für Witness-PIN-Eingabe
   - User-Auswahl (nur BTM-Berechtigte)
   - QR-Code für schnelle Bestätigung (optional)

2. **BTM-Transaction Model**
   ```python
   class BTMTransaction(models.Model):
       medication = ForeignKey(Medication)
       transaction_type = CharField(choices=TYPES)  # dispensed, disposed
       quantity = DecimalField()
       primary_user = ForeignKey(User, related_name='btm_primary')
       witness_user = ForeignKey(User, related_name='btm_witness')
       witness_confirmed_at = DateTimeField()
       reason = TextField()
       ip_address = GenericIPAddressField()
   ```

3. **Audit-Trail UI**
   - BTM-Log anzeigen
   - Export zu PDF
   - Filter nach Zeitraum, User, Medikament

**Schätzung:** 2-3 Tage

---

### Phase 5: Testing & Documentation

1. **Unit Tests**
   - `permissions/tests/test_backends.py`
   - `permissions/tests/test_decorators.py`
   - `permissions/tests/test_utils.py`
   - `permissions/tests/test_models.py`

2. **Integration Tests**
   - Permission-Flows testen
   - Delegation-Szenarien
   - BTM-Vier-Augen-Prinzip

3. **Documentation**
   - User-Handbuch für Admins
   - Entwickler-Doku für Modul-Integration
   - API-Dokumentation

**Schätzung:** 2-3 Tage

---

## 📝 Verwendungsbeispiele

### Rollen zuweisen (Python)

```python
from permissions.utils import PermissionHelper

# User zum Administrator machen
PermissionHelper.assign_role(user, 'Administrator')

# User zum Modulverantwortlichen machen
PermissionHelper.assign_module_responsibility(user, 'medical')

# BTM-Berechtigung prüfen
if PermissionHelper.check_btm_clearance(user):
    print(f"{user} ist BTM-berechtigt")

# Freigabelimit prüfen
limit = PermissionHelper.get_approval_limit(user)
print(f"Kann Bestellungen bis {limit}€ freigeben")

# Permission-Summary
summary = PermissionHelper.get_user_permission_summary(user)
print(f"User: {summary['user']}")
print(f"Rollen: {summary['roles']}")
print(f"Module: {summary['modules']}")
print(f"BTM-Clearance: {summary['btm_clearance']}")
```

### Delegation erstellen

```python
from permissions.utils import PermissionHelper
from datetime import datetime, timedelta

# Vertretung für 2 Wochen Urlaub
delegation = PermissionHelper.create_delegation(
    delegator=user_in_urlaub,
    delegate=vertreter,
    valid_from=datetime.now(),
    valid_to=datetime.now() + timedelta(days=14),
    delegate_all=True,  # Alle Rechte
    reason="Urlaub vom 01.11. bis 15.11."
)

# Vertretung vorzeitig beenden
if delegation:
    PermissionHelper.end_delegation(delegation)
```

### Views schützen

```python
from permissions.decorators import (
    require_2fa, require_witness,
    audit_action, delegation_allowed
)
from permissions.constants import AuditActions

# Einfache Permission
@permission_required('medical.view_medication')
def medication_list(request):
    medications = Medication.objects.all()
    return render(request, 'medical/list.html', {'medications': medications})

# BTM mit Vier-Augen-Prinzip
@permission_required('medical.dispose_btm_medication')
@require_2fa
@require_witness('medical.approve_btm_action')
@audit_action(AuditActions.BTM_DISPOSED)
def dispose_btm_medication(request, medication_id):
    medication = get_object_or_404(Medication, id=medication_id, is_btm=True)

    # Witness ist verfügbar nach Validation
    witness = request.witness_user

    # BTM-Transaction erstellen
    BTMTransaction.objects.create(
        medication=medication,
        transaction_type='disposal',
        quantity=request.POST['quantity'],
        primary_user=request.user,
        witness_user=witness,
        witness_confirmed_at=timezone.now(),
        reason=request.POST['reason'],
        ip_address=request.META['REMOTE_ADDR']
    )

    messages.success(request, 'BTM erfolgreich entsorgt')
    return redirect('medical:btm_list')

# Mit Delegation-Support
@permission_required('procurement.approve_order_low')
@delegation_allowed
def approve_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    # Prüfe ob User den Betrag freigeben darf
    if not PermissionHelper.can_approve_order(request.user, order.total_amount):
        messages.error(request, 'Betrag zu hoch für Ihre Freigabestufe')
        return redirect('procurement:order_detail', order_id)

    order.approve(request.user)

    # Wenn Delegation aktiv: Info wurde bereits von Decorator hinzugefügt
    if hasattr(request, 'is_delegated'):
        messages.info(request, f'Freigabe als Vertretung durchgeführt')

    return redirect('procurement:order_list')
```

### Class-Based Views

```python
from permissions.mixins import (
    ModulePermissionMixin,
    BTMSecurityMixin,
    AuditMixin,
    OwnershipMixin
)

# Standard Modul-View
class MedicationListView(ModulePermissionMixin, ListView):
    model = Medication
    required_module = 'medical'
    template_name = 'medical/medication_list.html'

# BTM-View mit Security
class BTMMedicationListView(BTMSecurityMixin, ListView):
    model = Medication
    template_name = 'medical/btm_list.html'

    def get_queryset(self):
        return super().get_queryset().filter(is_btm=True)

# Mit automatischem Audit
class MedicationCreateView(ModulePermissionMixin, AuditMixin, CreateView):
    model = Medication
    required_module = 'medical'
    form_class = MedicationForm

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        return super().form_valid(form)  # Audit wird automatisch geloggt

# Nur eigene Objekte bearbeiten
class OrderUpdateView(OwnershipMixin, UpdateView):
    model = Order
    form_class = OrderForm
    ownership_field = 'created_by'  # User kann nur eigene Orders bearbeiten
```

### Templates

```django
{% load permission_tags %}

{# Modul-Zugriff prüfen #}
{% if request.user|has_module_permission:'medical' %}
  <a href="{% url 'medical:medication_list' %}" class="nav-link">
    Medikamente
  </a>
{% endif %}

{# BTM-Berechtigung #}
{% if request.user|is_btm_authorized %}
  <a href="{% url 'medical:btm_list' %}" class="nav-link text-red-600">
    <i class="fas fa-lock"></i> BTM-Verwaltung
  </a>
{% endif %}

{# Object-Level Permissions #}
{% if request.user|can_edit_object:medication %}
  <button hx-get="{% url 'medical:medication_edit' medication.id %}"
          class="btn btn-primary">
    Bearbeiten
  </button>
{% endif %}

{# Delegation-Info anzeigen #}
{% has_delegation as is_delegated %}
{% if is_delegated %}
  <div class="alert alert-info">
    <i class="fas fa-user-friends"></i>
    Sie agieren als Vertretung für: {% get_delegator_names %}
  </div>
{% endif %}

{# Rollen anzeigen #}
{% show_user_roles request.user %}

{# Freigabe-Permission prüfen #}
{% check_approval_permission request.user order as can_approve %}
{% if can_approve %}
  <button hx-post="{% url 'procurement:approve_order' order.id %}"
          class="btn btn-success">
    Bestellung freigeben ({{ order.total_amount }}€)
  </button>
{% endif %}

{# Besitzer-Check #}
{% if request.user|is_owner:order %}
  <span class="badge badge-primary">Ihre Bestellung</span>
{% endif %}
```

---

## 🔧 Offene Punkte / Known Issues

### Minor Issues

1. **django-axes Warning**
   ```
   ?: (axes.W003) You do not have 'axes.backends.AxesStandaloneBackend'
   or a subclass in your settings.AUTHENTICATION_BACKENDS.
   ```
   **Fix:** Optional - Axes Backend hinzufügen wenn Brute-Force-Protection gewünscht
   ```python
   AUTHENTICATION_BACKENDS = (
       'axes.backends.AxesStandaloneBackend',  # HINZUFÜGEN
       'permissions.backends.CombinedPermissionBackend',
       'guardian.backends.ObjectPermissionBackend',
       'django.contrib.auth.backends.ModelBackend',
   )
   ```

2. **2FA-Integration noch nicht vollständig**
   - `@require_2fa` prüft auf `user.totp_device`
   - django-otp ist installiert aber noch nicht konfiguriert
   - **TODO:** 2FA Setup-Views erstellen (Phase 2)

3. **Template-Includes fehlen**
   - `permissions/tags/permission_badge.html` - für `{% show_user_roles %}`
   - `permissions/tags/delegation_info.html` - für `{% show_delegation_info %}`
   - **TODO:** Templates erstellen (Phase 2)

4. **Audit-Log Model fehlt noch**
   - `@audit_action` loggt momentan nur via Python logging
   - **TODO:** `audit.models.AuditLog` erstellen (Phase 3)

### Features noch nicht implementiert

- [ ] Email-Benachrichtigungen bei Delegation-Start/Ende
- [ ] Celery-Task für automatisches Cleanup abgelaufener Delegationen
- [ ] BTMTransaction Model (für Vier-Augen-Prinzip)
- [ ] Permission-Konflikt-Warnung in Admin-UI
- [ ] Export von Permission-Reports zu PDF
- [ ] IP-Whitelisting für BTM-Zugriff (optional)

---

## 🚀 Wie geht's morgen weiter?

### Empfohlener Start:

**Option A: User Management UI (Pragmatisch)**
```bash
# 1. Erstelle Admin-Views für Rollen-Zuweisung
# Datei: core/views/user_management.py

# 2. Erstelle Templates
# templates/core/user_management/user_list.html
# templates/core/user_management/user_detail.html

# 3. URLs hinzufügen
# core/urls.py

# 4. Teste Rollen-Zuweisung im Browser
# URL: /admin/users/
```

**Option B: Modul-Integration starten (Fokussiert)**
```bash
# 1. Magazine-Modul integrieren (einfachstes Modul)
# - Custom Permissions definieren
# - Views mit Decorators schützen
# - Templates anpassen

# 2. Testen
python manage.py test magazine.tests

# 3. Nächstes Modul (Medical)
```

**Option C: BTM-System vervollständigen (Kritisch)**
```bash
# 1. BTMTransaction Model erstellen
# medical/models.py

# 2. Vier-Augen-Prinzip UI
# templates/medical/btm_witness_modal.html

# 3. BTM-Audit-Log View
# medical/views.py
```

### Empfehlung: **Option A** (User Management UI)

**Warum?**
- Du kannst sofort Rollen testen
- Sichtbare Ergebnisse
- Basis für alle weiteren Schritte
- Kann parallel zu Modul-Integration laufen

---

## 📚 Relevante Dateien für morgen

### Zu bearbeiten:
```
core/views/user_management.py        # NEU ERSTELLEN
core/forms/permission_forms.py       # NEU ERSTELLEN
core/urls.py                          # ERWEITERN
templates/core/user_management/       # ORDNER ERSTELLEN
```

### Als Referenz:
```
permissions/constants.py              # Alle Rollen hier
permissions/utils.py                  # PermissionHelper nutzen
permissions/decorators.py             # Für View-Protection
permissions/templatetags/permission_tags.py  # Template-Tags
PERMISSIONS.md                        # Vollständige Spezifikation
```

### Testen mit:
```bash
# Permissions-Setup erneut ausführen
/var/www/lager.resqware.de/venv/bin/python manage.py setup_permissions

# Django Shell zum Testen
/var/www/lager.resqware.de/venv/bin/python manage.py shell

# Beispiel:
from permissions.utils import PermissionHelper
from core.models import User

user = User.objects.first()
PermissionHelper.assign_role(user, 'Administrator')
print(PermissionHelper.get_user_permission_summary(user))
```

---

## 🎓 Wichtige Konzepte zum Merken

1. **CombinedPermissionBackend ist aktiv**
   - Prüft Standard-Permissions
   - Dann zeitbasierte Einschränkungen
   - Dann Delegationen
   - Alles transparent für Views

2. **Drei Permission-Ebenen:**
   - **Global:** Django Permissions (via Groups)
   - **Zeitbasiert:** TimeBasedPermission Model
   - **Object-Level:** django-guardian + ObjectPermission

3. **Rollen vs. Permissions:**
   - Rollen = Groups (z.B. "Administrator")
   - Permissions = Atomare Rechte (z.B. "medical.view_medication")
   - User bekommen Rollen → Rollen haben Permissions

4. **BTM-Sicherheit:**
   - Separate Gruppe "BTM-Beauftragter"
   - 2FA-Pflicht (in User.requires_2fa())
   - Vier-Augen-Prinzip via `@require_witness`
   - Vollständiges Audit-Logging

5. **Delegationen:**
   - Zeitbasiert (von-bis)
   - Alle oder spezifische Permissions
   - Genehmigungsworkflow möglich
   - Automatisches Cleanup nötig (Celery)

---

## ✅ Checkliste für morgen

- [ ] User Management UI Views erstellen
- [ ] Rollen-Zuweisung Form implementieren
- [ ] User-Liste Template mit HTMX
- [ ] Ersten Test-User Rollen zuweisen
- [ ] Permission-Übersicht Dashboard
- [ ] Optional: Delegation-UI starten

---

**Bei Fragen oder Problemen:**
- Siehe `PERMISSIONS.md` für vollständige Spezifikation
- Siehe `permissions/constants.py` für alle Rollen/Permissions
- Siehe `permissions/utils.py` für alle Helper-Funktionen
- Nutze `PermissionHelper` für alle Permission-Operationen

**Viel Erfolg morgen! 🚀**
