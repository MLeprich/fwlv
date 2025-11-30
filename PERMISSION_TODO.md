# Permission System - Todo Liste

**Stand:** 22. Oktober 2025
**Aktualisiert:** Heute, 23:45 Uhr

---

## ✅ Phase 1: Foundation (ABGESCHLOSSEN) - 100%

### Core Components
- [x] permissions/constants.py (730 Zeilen) - Alle Rollen, Module, Permissions
- [x] permissions/models.py (461 Zeilen) - TimeBasedPermission, Delegation, ObjectPermission
- [x] permissions/backends.py (570 Zeilen) - CombinedPermissionBackend (AKTIV)
- [x] permissions/decorators.py (318 Zeilen) - @require_2fa, @require_witness, @audit_action
- [x] permissions/mixins.py (300 Zeilen) - BTMSecurityMixin, AuditMixin, OwnershipMixin
- [x] permissions/templatetags/permission_tags.py (343 Zeilen) - 20+ Template Tags
- [x] management/commands/setup_permissions.py (590 Zeilen) - Auto-Setup aller Gruppen
- [x] permissions/utils.py (650 Zeilen) - PermissionHelper Class
- [x] Migrations erstellt und ausgeführt
- [x] settings.py aktualisiert
- [x] 17 Gruppen erfolgreich erstellt (1.334 Permission-Zuweisungen)

**Ergebnis:** ✅ Produktionsreifes Permission-System

---

## 🔄 Phase 2: User Management UI - 0%

**Priorität:** HOCH
**Geschätzte Zeit:** 2-3 Tage
**Start:** Morgen

### 2A: Basis User Management

- [ ] **Views erstellen** (core/views/user_management.py)
  - [ ] UserListView - Liste aller User mit Rollen
  - [ ] UserDetailView - User-Details mit Permission-Summary
  - [ ] UserRoleAssignView - Rollen zuweisen/entfernen (HTMX)
  - [ ] UserCreateView - Neuen User anlegen
  - [ ] UserUpdateView - User bearbeiten

- [ ] **Forms erstellen** (core/forms/permission_forms.py)
  - [ ] RoleAssignmentForm - Multi-Select für Rollen
  - [ ] UserCreationFormExtended - Mit Abteilung, Position
  - [ ] TimePermissionForm - Zeitbasierte Permissions

- [ ] **Templates erstellen**
  - [ ] templates/core/user_management/user_list.html
  - [ ] templates/core/user_management/user_detail.html
  - [ ] templates/core/user_management/user_form.html
  - [ ] templates/core/user_management/role_assignment_modal.html

- [ ] **URLs konfigurieren** (core/urls.py)
  - [ ] /admin/users/ - Liste
  - [ ] /admin/users/<pk>/ - Detail
  - [ ] /admin/users/<pk>/roles/ - Rollen-Management
  - [ ] /admin/users/create/ - User erstellen

- [ ] **Navigation erweitern**
  - [ ] Link in sidebar_nav.html (nur für Admins)
  - [ ] Breadcrumbs

- [ ] **Tests schreiben**
  - [ ] test_user_list_view.py
  - [ ] test_role_assignment.py
  - [ ] test_permissions_on_user_management.py

### 2B: Delegation Management UI

- [ ] **Views**
  - [ ] DelegationListView - Aktive & abgelaufene Delegationen
  - [ ] DelegationCreateView - Neue Vertretung erstellen
  - [ ] DelegationUpdateView - Delegation bearbeiten
  - [ ] DelegationApproveView - Genehmigung durch Vorgesetzten
  - [ ] DelegationEndView - Vorzeitig beenden

- [ ] **Forms**
  - [ ] DelegationForm - Mit DateTime-Picker
  - [ ] DelegationApprovalForm

- [ ] **Templates**
  - [ ] templates/permissions/delegation_list.html
  - [ ] templates/permissions/delegation_form.html
  - [ ] templates/permissions/delegation_calendar.html
  - [ ] templates/permissions/delegation_approval_modal.html

- [ ] **Features**
  - [ ] Kalender-View für Delegationen (Optional: FullCalendar.js)
  - [ ] Filter: Aktiv/Abgelaufen/Alle
  - [ ] Sortierung nach Datum

### 2C: 2FA Setup

- [ ] **Views**
  - [ ] Enable2FAView - 2FA aktivieren
  - [ ] Confirm2FAView - QR-Code scannen + bestätigen
  - [ ] Disable2FAView - 2FA deaktivieren
  - [ ] BackupCodesView - Backup-Codes anzeigen/regenerieren

- [ ] **Templates**
  - [ ] templates/core/2fa/enable.html
  - [ ] templates/core/2fa/confirm.html
  - [ ] templates/core/2fa/backup_codes.html

- [ ] **Integration**
  - [ ] django-otp konfigurieren
  - [ ] QR-Code Generator einbinden
  - [ ] Backup-Codes System

**Erfolgskriterien Phase 2:**
- Admin kann User anlegen und Rollen zuweisen
- User-Detail zeigt vollständige Permission-Übersicht
- Delegationen können erstellt und verwaltet werden
- 2FA kann aktiviert werden

---

## 🔄 Phase 3: Modul-Integration - 0%

**Priorität:** MITTEL
**Geschätzte Zeit:** 5-7 Tage (0.5-1 Tag pro Modul)
**Start:** Nach Phase 2

### Locations (SIMPEL - Start hier)

- [ ] Custom Permissions definieren
  ```python
  class Meta:
      permissions = [
          ('manage_location', 'Kann Lagerort verwalten'),
      ]
  ```
- [ ] Views mit @permission_required schützen
- [ ] Templates: {% if user|has_module_permission:'locations' %}
- [ ] Tests schreiben

### Personnel

- [ ] Custom Permissions
  ```python
  ('view_own_profile', 'Kann eigenes Profil sehen'),
  ('view_own_qualifications', 'Kann eigene Qualifikationen sehen'),
  ('manage_qualifications', 'Kann Qualifikationen verwalten'),
  ```
- [ ] OwnershipMixin für eigene Daten
- [ ] Views schützen
- [ ] Templates anpassen
- [ ] Tests

### Magazine (EINFACHSTES LAGER-MODUL)

- [ ] Custom Permissions
  ```python
  ('dispense_item', 'Kann Artikel ausgeben'),
  ('receive_shipment', 'Kann Wareneingang buchen'),
  ('adjust_stock', 'Kann Bestand korrigieren'),
  ```
- [ ] Views mit Decorators
- [ ] Templates
- [ ] Tests

### Medical (KOMPLEX - BTM!)

- [ ] Custom Permissions (siehe PERMISSIONS.md)
  ```python
  ('view_btm_medication', ...),
  ('dispense_btm_medication', ...),
  ('dispose_btm_medication', ...),
  ('approve_btm_action', ...),
  ```
- [ ] BTMTransaction Model erstellen
- [ ] @require_witness für BTM-Aktionen
- [ ] BTMSecurityMixin in Views
- [ ] Witness-Modal Template
- [ ] BTM-Audit-Log View
- [ ] Tests (inkl. Vier-Augen-Prinzip)

### Weitere Module (je 0.5-1 Tag)

- [ ] Clothing
- [ ] Workshop
- [ ] Equipment
- [ ] Disinfection
- [ ] Height Rescue
- [ ] Diving
- [ ] IT Hardware
- [ ] Vehicle Handover
- [ ] Procurement
- [ ] Inventory Check
- [ ] Documents

**Erfolgskriterien Phase 3:**
- Jedes Modul hat Custom Permissions
- Alle Views sind permission-geschützt
- Templates prüfen Permissions
- Tests für Permission-Flows vorhanden

---

## 🔄 Phase 4: BTM Vier-Augen-Prinzip - 0%

**Priorität:** HOCH (Kritisch für Medical)
**Geschätzte Zeit:** 2-3 Tage
**Start:** Parallel zu Medical-Integration

### Models

- [ ] **BTMTransaction Model erstellen**
  ```python
  # medical/models.py
  class BTMTransaction(AuditedModel):
      medication = ForeignKey(Medication)
      transaction_type = CharField(choices=[
          ('dispensed', 'Ausgegeben'),
          ('disposed', 'Entsorgt'),
          ('received', 'Wareneingang'),
          ('corrected', 'Korrektur'),
      ])
      quantity = DecimalField()
      unit = CharField()

      # Vier-Augen-Prinzip
      primary_user = ForeignKey(User, related_name='btm_primary')
      witness_user = ForeignKey(User, related_name='btm_witness')
      witness_confirmed_at = DateTimeField()

      # Details
      reason = TextField()
      patient_reference = CharField(blank=True)  # Optional

      # Security
      ip_address = GenericIPAddressField()
      user_agent = TextField()

      # Audit
      is_reversed = BooleanField(default=False)
      reversed_by = ForeignKey(User, null=True)
      reversed_at = DateTimeField(null=True)
      reversal_reason = TextField(blank=True)
  ```

- [ ] Migration erstellen und ausführen

### Views

- [ ] **BTMMedicationDispenseView**
  - @require_2fa
  - @require_witness('medical.approve_btm_action')
  - Erstellt BTMTransaction
  - Aktualisiert Stock

- [ ] **BTMMedicationDisposeView**
  - @require_2fa
  - @require_witness('medical.approve_btm_action')
  - Disposal-Grund erforderlich
  - Photos optional

- [ ] **BTMTransactionListView**
  - Alle BTM-Transaktionen
  - Filter: Typ, Datum, User, Medikament
  - Export zu PDF

- [ ] **BTMAuditLogView**
  - Vollständiger Audit-Trail
  - Unveränderbar
  - Mit Witness-Info

### Templates

- [ ] **btm_witness_modal.html**
  ```html
  <div id="witness-modal">
      <h3>Vier-Augen-Prinzip</h3>
      <p>Diese Aktion erfordert Bestätigung durch einen zweiten BTM-Beauftragten</p>

      <select name="witness_user_id">
          <!-- BTM-berechtigte User außer aktuellem User -->
      </select>

      <input type="password" name="witness_pin" placeholder="PIN des Zeugen">

      <button>Bestätigen</button>
  </div>
  ```

- [ ] **btm_transaction_list.html**
  - Tabelle mit allen Transaktionen
  - Witness-Spalte
  - Export-Button

- [ ] **btm_audit_log.html**
  - Detaillierter Log
  - Timeline-View
  - PDF-Export

### Features

- [ ] QR-Code für schnelle Witness-Bestätigung (Optional)
- [ ] Email-Benachrichtigung bei BTM-Transaktion
- [ ] Automatische Alerts bei ungewöhnlichen Transaktionen
- [ ] Dashboard-Widget mit BTM-Statistiken

### Tests

- [ ] test_btm_dispense_requires_witness.py
- [ ] test_btm_witness_validation.py
- [ ] test_btm_transaction_logging.py
- [ ] test_btm_audit_trail_immutable.py

**Erfolgskriterien Phase 4:**
- BTM-Transaktion benötigt Witness
- Witness muss anderer User sein
- Witness braucht approve_btm_action Permission
- Vollständiger Audit-Trail
- Export zu PDF funktioniert

---

## 🔄 Phase 5: Background Tasks & Automation - 0%

**Priorität:** MITTEL
**Geschätzte Zeit:** 1-2 Tage

### Celery Tasks

- [ ] **Cleanup abgelaufene Delegationen** (täglich)
  ```python
  @shared_task
  def cleanup_expired_delegations():
      from permissions.backends import cleanup_expired_delegations
      count = cleanup_expired_delegations()
      logger.info(f"Cleaned up {count} expired delegations")
  ```

- [ ] **Cleanup abgelaufene TimePermissions** (täglich)
  ```python
  @shared_task
  def cleanup_expired_time_permissions():
      from permissions.backends import cleanup_expired_time_permissions
      count = cleanup_expired_time_permissions()
      logger.info(f"Cleaned up {count} expired time permissions")
  ```

- [ ] **Email-Benachrichtigungen**
  - Delegation startet morgen → Email an Delegate
  - Delegation endet heute → Email an Delegator
  - BTM-Transaktion → Email an Admin
  - Permission-Konflikt → Email an Admin

- [ ] **Celery Beat Schedule konfigurieren**
  ```python
  CELERY_BEAT_SCHEDULE = {
      'cleanup-delegations': {
          'task': 'permissions.tasks.cleanup_expired_delegations',
          'schedule': crontab(hour=2, minute=0),  # 02:00 Uhr
      },
      'send-delegation-reminders': {
          'task': 'permissions.tasks.send_delegation_reminders',
          'schedule': crontab(hour=8, minute=0),  # 08:00 Uhr
      },
  }
  ```

**Erfolgskriterien Phase 5:**
- Delegationen werden automatisch deaktiviert
- Email-Benachrichtigungen funktionieren
- Celery Beat läuft stabil

---

## 🔄 Phase 6: Testing & QA - 0%

**Priorität:** HOCH
**Geschätzte Zeit:** 2-3 Tage

### Unit Tests

- [ ] **permissions/tests/test_backends.py**
  - CombinedPermissionBackend
  - Zeitbasierte Permissions
  - Delegationen

- [ ] **permissions/tests/test_decorators.py**
  - @require_2fa
  - @require_witness
  - @audit_action

- [ ] **permissions/tests/test_utils.py**
  - PermissionHelper
  - get_users_by_role
  - get_approval_limit

- [ ] **permissions/tests/test_models.py**
  - TimeBasedPermission.is_currently_valid()
  - Delegation.is_currently_valid()

### Integration Tests

- [ ] **Test Permission-Flows**
  - User bekommt Rolle → Hat Permissions
  - User verliert Rolle → Permissions weg
  - Delegation erstellen → Permissions temporär

- [ ] **Test BTM-Vier-Augen-Prinzip**
  - Ohne Witness → Fehler
  - Mit Witness ohne Permission → Fehler
  - Mit richtigem Witness → Erfolg

- [ ] **Test Zeitbasierte Permissions**
  - Außerhalb Zeit → Kein Zugriff
  - Innerhalb Zeit → Zugriff
  - Nur Mo-Fr → Sa/So kein Zugriff

### End-to-End Tests (Optional: Playwright/Selenium)

- [ ] User-Login
- [ ] Rolle zuweisen
- [ ] Permission prüfen
- [ ] BTM-Transaktion mit Witness

### Coverage-Ziel

- [ ] Gesamt: >80%
- [ ] permissions App: >90%
- [ ] BTM-Bereich: 100%

**Erfolgskriterien Phase 6:**
- Alle Tests grün
- Coverage-Ziele erreicht
- Keine bekannten Bugs

---

## 🔄 Phase 7: Documentation - 0%

**Priorität:** MITTEL
**Geschätzte Zeit:** 1-2 Tage

### User-Dokumentation

- [ ] **Admin-Handbuch** (PDF)
  - Rollen-Verwaltung
  - User anlegen
  - Delegationen erstellen
  - Troubleshooting

- [ ] **BTM-Handbuch** (PDF)
  - Vier-Augen-Prinzip
  - BTM-Transaktionen
  - Audit-Log

- [ ] **Video-Tutorials** (Optional)
  - User anlegen und Rollen zuweisen
  - Delegation erstellen
  - BTM-Ausgabe mit Witness

### Entwickler-Dokumentation

- [ ] **API-Dokumentation**
  - PermissionHelper Class
  - Decorators
  - Mixins
  - Backends

- [ ] **Integration-Guide**
  - Modul in Permission-System integrieren
  - Custom Permissions definieren
  - Views schützen
  - Tests schreiben

- [ ] **Architecture Decision Records (ADRs)**
  - Warum CombinedPermissionBackend?
  - Warum zeitbasierte Permissions?
  - BTM-Vier-Augen-Prinzip Design

**Erfolgskriterien Phase 7:**
- Admin-Handbuch fertig
- Entwickler-Doku vollständig
- Alle Use-Cases dokumentiert

---

## 📊 Fortschritt Übersicht

| Phase | Status | Fortschritt | Geschätzte Zeit | Priorität |
|-------|--------|-------------|-----------------|-----------|
| Phase 1: Foundation | ✅ Abgeschlossen | 100% | - | - |
| Phase 2: User Management UI | ⏳ Ausstehend | 0% | 2-3 Tage | HOCH |
| Phase 3: Modul-Integration | ⏳ Ausstehend | 0% | 5-7 Tage | MITTEL |
| Phase 4: BTM Vier-Augen | ⏳ Ausstehend | 0% | 2-3 Tage | HOCH |
| Phase 5: Background Tasks | ⏳ Ausstehend | 0% | 1-2 Tage | MITTEL |
| Phase 6: Testing & QA | ⏳ Ausstehend | 0% | 2-3 Tage | HOCH |
| Phase 7: Documentation | ⏳ Ausstehend | 0% | 1-2 Tage | MITTEL |

**Gesamt:** 1/7 Phasen abgeschlossen (14%)
**Verbleibend:** ca. 15-20 Arbeitstage

---

## 🎯 Prioritäten für nächste Woche

### Diese Woche (KW 43)
1. ✅ Phase 1: Foundation (ERLEDIGT)
2. 🔄 Phase 2: User Management UI (START MORGEN)

### Nächste Woche (KW 44)
3. Phase 2: Fertigstellung User Management
4. Phase 4: BTM Vier-Augen-Prinzip (parallel starten)
5. Phase 3: Erste Module integrieren (Locations, Magazine)

### Übernächste Woche (KW 45)
6. Phase 3: Weitere Module (Medical, Clothing, etc.)
7. Phase 5: Background Tasks
8. Phase 6: Testing starten

---

## 📝 Quick Links

- **Status:** [PERMISSION_IMPLEMENTATION_STATUS.md](./PERMISSION_IMPLEMENTATION_STATUS.md)
- **Quick Start:** [NEXT_STEPS_QUICKSTART.md](./NEXT_STEPS_QUICKSTART.md)
- **Spezifikation:** [PERMISSIONS.md](./PERMISSIONS.md)
- **Constants:** [permissions/constants.py](./permissions/constants.py)
- **Utils:** [permissions/utils.py](./permissions/utils.py)

---

**Zuletzt aktualisiert:** 22. Oktober 2025, 23:45 Uhr
**Nächstes Update:** Nach Abschluss Phase 2
