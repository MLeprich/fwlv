# Feuerwehr Lagerverwaltungssystem (FLVS)

Ein umfassendes Lagerverwaltungssystem für Feuerwehr und Katastrophenschutz, entwickelt mit Django und HTMX.

---

## 📊 Aktueller Projektstatus

### ✅ Bereits implementiert:
- Django 5.x Projekt initialisiert
- PostgreSQL Datenbank konfiguriert
- Core App mit Base-Models (TimeStampedModel, AuditedModel, SoftDeleteModel)
- Custom User Model mit Feuerwehr-spezifischen Feldern
- Docker Compose Setup (web, db, redis)
- **Basis-Templates erstellt:**
  - `base.html` - Haupt-Layout mit Tailwind CSS, HTMX, Alpine.js
  - `dashboard.html` - Dashboard mit KPI-Karten und Modul-Kacheln
  - `sidebar_nav.html` - Hierarchische Navigation mit 5 Kategorien
- **Core App vollständig funktional:**
  - ✅ Views (Dashboard, Profile, Settings, Search, Notifications, etc.)
  - ✅ Forms (UserProfileForm, UserSettingsForm)
  - ✅ URLs mit Namespace 'core'
  - ✅ HTMX-Partials (Search Results, Notifications Dropdown)
  - ✅ Context Processors für globale Template-Variablen
  - ✅ Authentication Views (Login, Logout, Password Reset)
- **Locations App vollständig funktional:**
  - ✅ Location Model mit MPTT (hierarchische Struktur)
  - ✅ Admin-Interface mit Drag & Drop Tree-Darstellung
  - ✅ CRUD Views (List, Detail, Create, Update, Delete)
  - ✅ Forms mit Tailwind CSS Styling
  - ✅ URLs konfiguriert
  - ✅ Migrations erstellt und angewendet
- **Permissions App vollständig funktional:**
  - ✅ Permission Mixins (ModulePermissionMixin, BTMPermissionMixin, RoleRequiredMixin, ObjectPermissionMixin)
  - ✅ Permission Decorators (module_permission_required, role_required, btm_permission_required)
  - ✅ Template Tags (has_module_permission, has_role, can_add/change/delete, is_btm_authorized)
  - ✅ Management Command setup_roles
  - ✅ 7 Standard-Rollen erstellt (Administrator, Modulverantwortlicher, Lagerverwalter, Werkstattmeister, BTM-Beauftragter, Wachleiter, Standard-Nutzer)
- **Inventory Base App vollständig funktional:**
  - ✅ AbstractInventoryItem & AbstractStockMovement Models
  - ✅ Category Model mit MPTT (hierarchisch)
  - ✅ Supplier Model
  - ✅ Admin-Interface mit Drag & Drop für Kategorien
  - ✅ Migrations erstellt und angewendet
- **Magazine App vollständig funktional:**
  - ✅ MagazineItem Model (erbt von AbstractInventoryItem)
  - ✅ MagazineStockMovement & MagazineBatch Models
  - ✅ Admin-Interface mit Gefahrstoff-Badges
  - ✅ Views & URLs (10 URL-Patterns)
  - ✅ Migrations erstellt und angewendet
- **Medical App vollständig funktional (mit BTM-Sicherheit):**
  - ✅ MedicalItem Model mit BTM-Kennzeichnung
  - ✅ MedicalStockMovement mit Vier-Augen-Prinzip
  - ✅ MedicalBatch mit Temperatur-Logging & Rückrufverwaltung
  - ✅ Admin-Interface mit BTM-Freigabe-Workflow
  - ✅ Views mit BTM-Approval-Funktionen (17 URL-Patterns)
  - ✅ Migrations erstellt und angewendet
- **Clothing App vollständig funktional (Kleiderkammer):**
  - ✅ ClothingItem Model mit PSA-Verwaltung
  - ✅ ClothingStockMovement mit automatischer Personenzuordnung
  - ✅ ClothingSizeAssignment für Größenverwaltung
  - ✅ Admin-Interface mit PSA-Badges & Prüfstatus
  - ✅ Views für PSA-Übersicht & Prüfungen (17 URL-Patterns)
  - ✅ Migrations erstellt und angewendet
- **Equipment App vollständig funktional (Ausrüstung & Geräte):**
  - ✅ EquipmentItem Model mit Wartungs- & Prüfmanagement
  - ✅ EquipmentStockMovement mit automatischer Fahrzeugzuordnung
  - ✅ Admin-Interface mit Wartungs-/Prüf-/Betriebsstunden-Badges
  - ✅ Views für Wartung, Prüfung, Fahrzeug-Ausrüstung (16 URL-Patterns)
  - ✅ Migrations erstellt und angewendet
- **Workshop App vollständig funktional (KFZ-Werkstatt):**
  - ✅ WorkshopItem Model mit 80+ Artikel-Typen & Gefahrstoff-Management
  - ✅ WorkshopStockMovement mit Pfand-Rückgabe-System
  - ✅ VehicleServiceRecord Model für Fahrzeug-Wartungs-Dokumentation
  - ✅ Admin-Interface mit Service-Management & automatischer Kostenberechnung
  - ✅ Views für Service-Historie, Überfälligkeits-Tracking (21 URL-Patterns)
  - ✅ Migrations erstellt und angewendet
- **Disinfection App vollständig implementiert (Desinfektions-Management):**
  - ✅ DisinfectionItem Model mit VAH/DGHM/RKI-Compliance & Wirkungsspektrum
  - ✅ DisinfectionStockMovement mit Chargen- & Anbruch-Tracking
  - ✅ DisinfectionLog Model für Desinfektions-Protokolle
  - ✅ Admin-Interface mit Spektrum-Badges & Compliance-Kennzeichnung
  - ✅ Migrations erstellt und angewendet

- **Height Rescue App vollständig implementiert (Höhenrettungs-Management):**
  - ✅ HeightRescueItem Model mit EN-Zertifizierungen (EN 361, EN 1891, etc.)
  - ✅ 20 Ausrüstungstypen (Seile, Gurte, Karabiner, Abseilgeräte, etc.)
  - ✅ DGUV Vorschrift 3 konforme Prüfintervalle & Prüfprotokollierung
  - ✅ Automatische Aussonderung nach Sturz (fall_arrested)
  - ✅ Alterungsberechnung & max. Nutzungsdauer
  - ✅ HeightRescueStockMovement mit Einsatz- & Sturzdokumentation
  - ✅ HeightRescueInspectionLog für vollständige Prüfhistorie
  - ✅ Admin-Interface mit Zertifizierungs-Badges & Prüfstatus-Anzeige
  - ✅ Migrations erstellt und angewendet (14 Indizes)

- **Diving App vollständig implementiert (Tauch-Management):**
  - ✅ DivingItem Model mit 29 Ausrüstungstypen (Flaschen, Atemregler, Anzüge, Instrumente, Kompressor)
  - ✅ TÜV-Prüfung für Tauchflaschen (alle 2.5 Jahre) mit Prüfstatus-Tracking
  - ✅ Gasverwaltung (Pressluft, Nitrox 32/36, Trimix, Heliox, O2)
  - ✅ Jährliche Wartung für Atemregler & BCD mit Prüfwerten (Ansprechdruck, Durchfluss)
  - ✅ DivingStockMovement mit Gasfüll-Tracking, Tauchgangs- & Servicedokumentation
  - ✅ Automatische Statistik-Updates (total_dives, total_hours)
  - ✅ DivingServiceLog mit Kostenerfassung & Prüfprotokollen
  - ✅ Admin-Interface mit Gas-Badges, TÜV/Service-Status-Anzeige
  - ✅ Migrations erstellt und angewendet (13 Indizes)

- **IT Hardware App vollständig implementiert (IT-Asset-Management):**
  - ✅ ITHardwareItem Model mit 43 Hardware-Typen (PC, Server, Netzwerk, Peripherie, Komponenten, Lizenzen)
  - ✅ Asset-Tracking (Asset-Tag, Seriennummer, MAC/IP, Hostname)
  - ✅ Benutzer-Zuordnung & Netzwerk-Informationen
  - ✅ Garantie & Support-Verträge mit Ablauf-Tracking
  - ✅ Abschreibungsberechnung & aktueller Wert (5 Jahre Standard)
  - ✅ OS & Software-Management (10 Betriebssysteme, Antivirus-Tracking)
  - ✅ Lizenz-Management (Lizenzschlüssel, Anzahl Seats, Ablaufdatum)
  - ✅ ITHardwareStockMovement mit Benutzer-Zuweisungen, Wartung & OS-Updates
  - ✅ Admin-Interface mit IT-Status-Badges, Garantie/Support-Anzeige, Wert-Berechnung
  - ✅ Migrations erstellt und angewendet (10 Indizes)

### 📝 Phase 5 ABGESCHLOSSEN! ✅
Alle Lager-Module aus CLAUDE.md Phase 5 sind vollständig implementiert.

---

### 🚗 Phase 6 - Prozesse (IN ARBEIT)

- **Vehicle Handover App vollständig implementiert (Fahrzeugübernahme):**
  - ✅ VehicleHandover Model mit 8 Übergabe-Arten (Wachablösung, Einsatz, Werkstatt, Kontrolle)
  - ✅ 4 Status-Stufen (In Bearbeitung, Abgeschlossen, Mit Mängeln, Abgebrochen)
  - ✅ Fahrzeugzustand-Erfassung (KM-Stand, Tankfüllung, Sauberkeit Innen/Außen)
  - ✅ Vollständigkeitsprüfung mit digitaler Bestätigung (Übergeber & Empfänger)
  - ✅ HandoverChecklist Model für flexible, fahrzeugspezifische Checklisten
  - ✅ Prüfstatus (Geprüft, Vorhanden, Funktionsfähig) je Item
  - ✅ HandoverPhoto Model mit 360°-Foto-Unterstützung (8 Positionen)
  - ✅ 15 Foto-Typen (360°, Innenraum, Laderaum, Schäden, Ausrüstung)
  - ✅ GPS-Koordinaten-Erfassung bei Fotos
  - ✅ HandoverDefect Model für Mängel-Dokumentation
  - ✅ 5 Schweregrad-Stufen (Info, Gering, Mittel, Erheblich, Kritisch)
  - ✅ 11 Mangel-Kategorien (Karosserie, Verglasung, Beleuchtung, Reifen, etc.)
  - ✅ Einsatzbereitschafts-Kennzeichnung & Sofortmaßnahmen-Flag
  - ✅ Reparatur-Tracking (Datum, Person, Kosten geschätzt/tatsächlich)
  - ✅ Foto-Verknüpfung zu Mängeln
  - ✅ Admin-Interface mit:
    - Checklisten-Fortschrittsbalken & Foto-Galerie
    - Übergabe-Art & Status-Badges (8 Farben)
    - Mängel-Übersicht mit Schweregrad-Badges
    - KM-Stand & Tankfüllungs-Anzeige (farbcodiert)
    - Vollständigkeits-Status & Bestätigungs-Tracking
    - Bulk-Actions (Als abgeschlossen markieren, etc.)
  - ✅ Migrations erstellt und angewendet (14 Indizes)

- **Procurement App vollständig implementiert (Bestellwesen):**
  - ✅ PurchaseOrder Model mit 10 Status-Stufen (Entwurf → Bestellt → Geliefert)
  - ✅ 4 Prioritäts-Stufen (Niedrig, Normal, Hoch, Dringend)
  - ✅ Automatische Bestellnummern-Generierung (PO-2025-0001)
  - ✅ Mehrstufiger Approval-Workflow (OrderApproval)
  - ✅ Freigabe-Stufen mit Genehmiger, Frist & Deadline-Tracking
  - ✅ OrderItem Model für Bestellpositionen
  - ✅ Generic Foreign Key zu allen Inventory-Typen
  - ✅ Automatische Kostenberechnung (Subtotal, Tax, Shipping, Total)
  - ✅ GoodsReceipt Model für Wareneingänge
  - ✅ Automatische Wareneingangs-Nummern (GR-2025-0001)
  - ✅ Qualitätsprüfung & Abweichungs-Management
  - ✅ GoodsReceiptItem mit Zustandsbewertung (Gut, Akzeptabel, Beschädigt, Defekt)
  - ✅ Chargen- & Ablaufdatum-Tracking
  - ✅ Automatisches Update von quantity_received in OrderItem
  - ✅ Admin-Interface mit:
    - Status & Prioritäts-Badges (10 Farben)
    - Freigabe-Fortschrittsbalken (0-100%)
    - Lieferfortschritts-Anzeige
    - Kostenübersicht & Budget-Tracking
    - Approval-Workflow-Management
    - Bulk-Actions (Freigeben, Bestellen, Liefern, Stornieren)
  - ✅ Migrations erstellt und angewendet (13 Indizes)

- **Inventory Check App vollständig implementiert (Inventur):**
  - ✅ InventoryCheck Model mit 6 Status-Stufen (Geplant → Abgeschlossen)
  - ✅ 4 Inventur-Typen (Vollständig, Stichprobe, Zyklisch, Ad-hoc)
  - ✅ Automatische Inventur-Nummern-Generierung (INV-2025-0001)
  - ✅ Fortschritts-Tracking (gezählte Items / Gesamt-Items)
  - ✅ Abweichungsrate-Berechnung (Items mit Diskrepanzen)
  - ✅ InventoryCheckItem Model für Soll-Ist-Vergleich
  - ✅ Erwartete & tatsächliche Mengen mit Varianz-Berechnung
  - ✅ Automatische Diskrepanz-Erkennung bei Abweichungen
  - ✅ 7 Zustands-Bewertungen (Neuwertig → Defekt)
  - ✅ Seriennummer & Chargen-Tracking
  - ✅ InventoryDiscrepancy Model für detaillierte Dokumentation
  - ✅ 6 Diskrepanz-Typen (Fehlbestand, Überbestand, Beschädigt, etc.)
  - ✅ 4 Schweregrad-Stufen (Geringfügig → Kritisch)
  - ✅ Wert-Berechnung für Abweichungen
  - ✅ Korrekturmaßnahmen-Tracking
  - ✅ InventoryAdjustment Model für Korrektur-Buchungen
  - ✅ Automatische Anpassungs-Nummern (ADJ-2025-0001)
  - ✅ 4 Anpassungs-Typen (Korrektur, Abschreibung, Umbuchung, Sonstiges)
  - ✅ Genehmigungsworkflow (Approval-Management)
  - ✅ Wiederholungszählungen-Management
  - ✅ Admin-Interface mit:
    - Fortschrittsbalken (gezählt/gesamt Items)
    - Diskrepanzrate-Badges mit Farbcodierung
    - Varianz-Anzeige (grün für Überbestand, rot für Fehlbestand)
    - Überfälligkeits-Warnungen
    - Status & Typ-Badges (6 Farben)
    - Schweregrad-Badges für Diskrepanzen
    - Bulk-Actions (Starten, Abschließen, Genehmigen, etc.)
  - ✅ Migrations erstellt und angewendet (17 Indizes)

- **Documents App vollständig implementiert (Dokumentenmanagement):**
  - ✅ DocumentCategory Model mit MPTT-Hierarchie (Baum-Struktur)
  - ✅ Verschachtelbare Kategorien (z.B. Fahrzeuge > KFZ-Scheine > HU/AU)
  - ✅ get_full_path() & get_document_count() Methoden
  - ✅ Document Model mit umfangreichem Feature-Set
  - ✅ 12 Dokumententypen (Handbuch, Zertifikat, Rechnung, Vertrag, etc.)
  - ✅ 7 Status-Stufen (Entwurf → Archiviert)
  - ✅ 5 Zugriffslevel (Öffentlich → Geheim)
  - ✅ Automatische Dokumentennummern-Generierung (DOC-2025-0001)
  - ✅ Dateiupload mit Validierung (PDF, DOC, XLS, JPG, etc.)
  - ✅ Versionsnummer-Tracking (1.0, 1.2, 2.0)
  - ✅ Gültigkeitsdaten (valid_from/until) mit Auto-Expiry
  - ✅ Review-Datum für regelmäßige Prüfungen
  - ✅ Generic FK für Verknüpfung mit beliebigen Objekten
  - ✅ M2M-Berechtigungen für eingeschränkten Zugriff
  - ✅ Statistiken (view_count, download_count)
  - ✅ Archivierungs-Workflow
  - ✅ DocumentVersion Model für vollständige Versionshistorie
  - ✅ 4 Änderungstypen (Major, Minor, Patch, Revision)
  - ✅ Änderungszusammenfassung & Details
  - ✅ Unique Constraint (document, version_number)
  - ✅ DocumentAccess Model für Audit-Trail (Read-Only)
  - ✅ 5 Zugriffstypen (View, Download, Edit, Delete, Share)
  - ✅ IP-Adresse & User-Agent-Logging
  - ✅ DocumentReview Model für Freigabe-Workflow
  - ✅ 4 Prüfstatus (Ausstehend, Freigegeben, Abgelehnt, Überarbeitung)
  - ✅ Deadline-Tracking mit is_overdue()
  - ✅ Admin-Interface mit umfangreichen Features:
    - Hierarchische Kategorie-Verwaltung (MPTT)
    - Status, Typ & Zugriffslevel-Badges (29 Farben)
    - Ablaufdatum-Warnungen (⚠ ABGELAUFEN bei Überschreitung)
    - Review-Datum-Warnungen (⚠ FÄLLIG bei Fälligkeit)
    - Dateigröße-Formatierung (B, KB, MB, GB)
    - Statistik-Anzeige (👁 Views | ⬇ Downloads)
    - 3 Inlines (Versionen, Prüfungen, Zugriffe)
    - Bulk-Actions (Aktivieren, Archivieren, Ablaufen, Stats zurücksetzen)
  - ✅ Migrations erstellt und angewendet (17 Indizes)

- **Reporting & KPI App vollständig implementiert:**
  - ✅ ReportTemplate Model mit wiederverwendbaren Report-Definitionen
  - ✅ 10 Report-Typen (Bestand, Ablaufend, Niedrige Bestände, Bestellungen, etc.)
  - ✅ Query/Code-Feld für flexible Datenabfrage
  - ✅ JSON-Parameter für dynamische Reports
  - ✅ Berechtigungssystem (öffentlich/eingeschränkt)
  - ✅ Verwendungszähler-Tracking
  - ✅ Report Model für generierte Reports
  - ✅ 5 Report-Status (Ausstehend → Abgeschlossen)
  - ✅ 5 Export-Formate (PDF, Excel, CSV, HTML, JSON)
  - ✅ Zeitraum-Filter (date_from/to)
  - ✅ Generierungs-Metadaten (Dauer, Fehler)
  - ✅ Ablauf-Management mit Auto-Löschung
  - ✅ Download-Statistiken
  - ✅ Generic FK für Objekt-Verknüpfung
  - ✅ ReportSchedule Model für automatische Generierung
  - ✅ 6 Frequenzen (Täglich, Wöchentlich, Monatlich, Vierteljährlich, Jährlich, Custom)
  - ✅ Cron-Expression-Support
  - ✅ E-Mail-Versand an Empfänger
  - ✅ Retention-Management (Aufbewahrungsdauer)
  - ✅ Next-Run-Berechnung
  - ✅ KPI Model für Key Performance Indicators
  - ✅ 5 KPI-Kategorien (Inventory, Financial, Operational, Quality, Compliance)
  - ✅ 6 KPI-Typen (Count, Sum, Average, Percentage, Ratio, Trend)
  - ✅ Zielwert & Schwellwerte für Ampel-System
  - ✅ Auto-Refresh-Intervalle
  - ✅ Display-Order für Dashboard-Sortierung
  - ✅ Admin-Interface mit umfangreichen Features:
    - Report-Templates mit Verwendungs-Badges
    - Reports mit Status, Format & Download-Tracking
    - Generierungsdauer-Anzeige (Sekunden/Minuten)
    - Scheduled Reports mit Frequenz-Badges
    - Nächste Ausführung mit Überfälligkeits-Warnung
    - E-Mail & Aktiv-Badges
    - KPIs mit Ampel-System (Grün/Gelb/Rot/Grau)
    - Kategorie & Typ-Badges (11 Farben)
    - Bulk-Actions (Ablaufen, Dateien löschen)
  - ✅ Migrations erstellt und angewendet (10 Indizes)

### 📺 Phase 7 - Advanced Features (IN ARBEIT)

- **Info Monitors App vollständig implementiert (Dashboard-Builder):**
  - ✅ MonitorProfile Model für verschiedene Einsatzzwecke
  - ✅ 3 Standard-Profile (Leitstelle, Werkstatt, Lager)
  - ✅ Standard-Profil-Markierung & Display-Order
  - ✅ Dashboard Model mit flexiblem Layout-System
  - ✅ 3 Themes (Light, Dark, Auto)
  - ✅ Bootstrap 12-Spalten-Grid-System
  - ✅ Auto-Refresh mit konfigurierbarem Intervall (min. 5 Sekunden)
  - ✅ Vollbild-Modus (Header/Sidebar ausblendbar)
  - ✅ Berechtigungssystem (öffentlich/berechtigte Benutzer)
  - ✅ View-Count-Tracking & Last-Viewed-Zeitstempel
  - ✅ Widget Model für flexible Datenvisualisierung
  - ✅ 12 Widget-Typen (KPI, Chart, Table, List, Map, Gauge, Progress, Counter, Alert, Clock, Weather, Custom)
  - ✅ 7 Chart-Typen (Line, Bar, Pie, Doughnut, Area, Radar, Scatter)
  - ✅ Grid-Position (Row/Column) & 5 Größen (1-12 Spalten)
  - ✅ Duale Datenquellen (KPI-FK oder Custom Query)
  - ✅ JSON-Konfiguration für Widget-spezifische Settings
  - ✅ Styling (Hintergrund, Text, Rahmen)
  - ✅ Widget-Level Auto-Refresh & Caching
  - ✅ WidgetAlert Model für Schwellwert-Benachrichtigungen
  - ✅ 5 Alert-Bedingungen (Größer, Kleiner, Gleich, Ungleich, Zwischen)
  - ✅ 4 Schweregrade (Info, Warnung, Fehler, Kritisch)
  - ✅ Benachrichtigungs-System mit User-Zuordnung
  - ✅ Trigger-Tracking (Anzahl & Zeitstempel)
  - ✅ Admin-Interface mit umfangreichen Features:
    - Monitor-Profile mit Dashboard-Count-Badges
    - Dashboards mit Theme, Widget-Count, View-Count-Badges
    - Widget-Inline-Editor für schnelle Konfiguration
    - 12 Widget-Typ-Badges mit Farbcodierung
    - Chart-Typ-Anzeige für Chart-Widgets
    - Position-Display (Row/Column-Format)
    - Widget-Alerts mit Schweregrad-Badges (4 Farben)
    - Bedingungsanzeige mit Min/Max-Werten
    - Trigger-Count-Badges
    - 2 Inlines (Widgets, Alerts)
    - Bulk-Actions
  - ✅ Migrations erstellt und angewendet (14 Indizes)

### 🎯 Phase 8 - Polish & Production (IN ARBEIT)

**Performance-Optimierung:**
- ✅ Performance-Audit durchgeführt (`docs/PERFORMANCE_AUDIT.md`)
- ✅ Admin-Optimierungs-Guide erstellt (`docs/ADMIN_OPTIMIZATION_GUIDE.md`)
- ✅ Query-Analyse: select_related/prefetch_related Strategie dokumentiert
- ✅ Caching-Strategie definiert (Redis, QuerySet-Cache, Template-Fragment-Cache)
- ✅ Index-Review: 14-17 Indizes pro kritischer App
- ⏭️ Celery Tasks für Reports/KPIs (dokumentiert, noch nicht implementiert)
- ⏭️ Performance-Tests mit Django Silk

**Security-Audit:**
- ✅ Umfassender Security-Audit durchgeführt (`docs/SECURITY_AUDIT.md`)
- ✅ Production-Settings erstellt mit allen Security-Best-Practices
- ✅ HTTPS/SSL-Enforcement konfiguriert
- ✅ Cookie-Security (Secure, HttpOnly, SameSite)
- ✅ HSTS konfiguriert (1 Jahr)
- ✅ CSRF/XSS-Protection verifiziert
- ✅ File-Upload-Validierung dokumentiert
- ✅ BTM-Vier-Augen-Prinzip geprüft
- ✅ API Rate-Limiting konfiguriert
- ✅ Brute-Force-Protection (Django Axes)
- ✅ Logging-Strategie (btm_audit.log, security.log)
- ⏭️ 2FA für BTM-Beauftragte (Infrastructure vorhanden)

**Production-Readiness:**
- ✅ Production-Settings (`flvs_project/settings/production.py`) vollständig
- ✅ Security-Validation-Checks implementiert
- ✅ Sentry-Integration vorbereitet (optional)
- ✅ Template-Caching aktiviert
- ✅ Debug-Toolbar deaktiviert in Production
- ✅ Admin-Email-Benachrichtigungen bei Errors
- ⏭️ Deployment-Guide
- ⏭️ Backup-Automation

**Dokumentation:**
- ✅ `docs/PERFORMANCE_AUDIT.md` - Umfassende Performance-Analyse
- ✅ `docs/ADMIN_OPTIMIZATION_GUIDE.md` - Admin-Query-Optimierung
- ✅ `docs/SECURITY_AUDIT.md` - Security-Best-Practices & Action Items
- ⏭️ API-Dokumentation (OpenAPI/Swagger)
- ⏭️ Deployment-Anleitung

**Nächste Schritte:**
1. Admin-Optimierungen implementieren (select_related)
2. Celery Tasks für Reports/KPIs
3. 2FA-Setup für BTM
4. Deployment-Guide
5. User-Testing

---

## 🚀 Projekt-Start mit Claude Code

### Voraussetzungen

- **Ubuntu Server** (20.04 LTS oder neuer)
- **Python 3.11+**
- **PostgreSQL 15+**
- **Redis** (für Caching und Celery)
- **Claude Code** CLI-Tool installiert

### 1. Repository initialisieren

```bash
# Projektverzeichnis erstellen
mkdir flvs_project
cd flvs_project

# Git initialisieren
git init

# Diese SSOT-Dateien ins Repository kopieren:
# - CLAUDE.md
# - ARCHITECTURE.md
# - DATA_MODEL.md
# - PERMISSIONS.md
# - core/constants.py (Beispiel-Struktur)
```

### 2. Claude Code starten

```bash
# Claude Code im Projektverzeichnis ausführen
claude-code
```

### 3. Initialer Prompt für Claude Code

Sobald Claude Code läuft, gib folgenden Prompt ein:

```
Ich möchte das Feuerwehr Lagerverwaltungssystem (FLVS) entwickeln, wie in CLAUDE.md beschrieben.

Bitte beginne mit Phase 1 (Foundation):

1. Erstelle die Django-Projekt-Struktur mit folgenden Apps:
   - core (Basis-Funktionalität, User-Management, Base-Models)
   - permissions (Berechtigungssystem)
   - locations (Lagerorte-Hierarchie)
   - personnel (Stammdatenverwaltung Personal)
   - vehicles (Fahrzeugverwaltung)
   - inventory_base (Basis-Klassen für Lager-Module)

2. Setup:
   - Django 5.x Projekt initialisieren
   - PostgreSQL Datenbank-Konfiguration (settings.py mit django-environ)
   - Docker Compose Setup (web, db, redis)
   - Requirements.txt mit allen notwendigen Packages
   - .env.example Template

3. Implementiere die Basis-Models aus DATA_MODEL.md:
   - TimeStampedModel
   - AuditedModel
   - SoftDeleteModel
   - User-Model (erweitert Django's AbstractUser)

4. Erstelle die initiale Migration und Admin-Registrierung

Folge dabei strikt den Vorgaben in ARCHITECTURE.md und beachte die Konstanten in core/constants.py.
```

---

## 📋 Entwicklungs-Phasen

### Phase 1: Foundation ✅ IN PROGRESS
- ✅ Django-Projekt Setup
- ✅ Core App mit Base-Models
- 🔄 Permissions App - IN PROGRESS
- 🔄 Locations App (Lagerorte) - NEXT
- ✅ Docker Compose Setup
- ✅ Basis-Templates (base.html, dashboard.html, sidebar_nav.html)

### Phase 2: Personnel & Vehicles
- Personnel App (Stammdaten, Qualifikationen)
- Vehicles App (Fahrzeuge, Mobile Lager)
- Audit App
- Notifications App

### Phase 3: Inventory Base
- AbstractInventoryItem Model
- Magazine App (erstes Lager-Modul)
- Schwellwert-Management
- Barcode-Integration

### Phase 4: Medical & Critical
- Medical App
- BTM-Sicherheit
- Chargen-Rückverfolgung

### Phase 5-8: Siehe CLAUDE.md

---

## 🏗️ Projekt-Struktur

```
flvs_project/
├── CLAUDE.md                 # Haupt-Projektdokumentation
├── ARCHITECTURE.md           # System-Architektur
├── DATA_MODEL.md            # Datenmodell-Dokumentation
├── PERMISSIONS.md           # Berechtigungskonzept
├── README.md                # Diese Datei
├── requirements.txt         # Python Dependencies
├── .env.example            # Environment-Variablen Template
├── docker-compose.yml      # Docker Setup
├── Dockerfile             # Django Container
├── manage.py              # Django Management
│
├── templates/             # ✅ Basis-Templates
│   ├── base.html          # Haupt-Layout (Header, Sidebar, Footer)
│   ├── dashboard.html     # Dashboard-Vorlage
│   └── includes/
│       └── sidebar_nav.html  # Hierarchische Navigation
│
├── flvs_project/          # Django Projekt
│   ├── __init__.py
│   ├── settings/
│   │   ├── __init__.py
│   │   ├── base.py        # Basis-Settings
│   │   ├── development.py # Dev-Settings
│   │   └── production.py  # Prod-Settings
│   ├── urls.py
│   ├── wsgi.py
│   └── celery.py
│
├── core/                   # Kern-App
│   ├── models/
│   │   ├── __init__.py
│   │   ├── base.py        # TimeStampedModel, AuditedModel, etc.
│   │   └── user.py        # Custom User Model
│   ├── constants.py       # Zentrale Konstanten
│   ├── mixins.py          # Wiederverwendbare Mixins
│   ├── utils/
│   └── ...
│
├── permissions/            # Berechtigungssystem
├── locations/             # Lagerorte
├── personnel/             # Personal
├── vehicles/              # Fahrzeuge
├── inventory_base/        # Inventar-Basis
├── medical/               # Rettungsdienst
├── clothing/              # Kleiderkammer
├── magazine/              # Magazin
├── workshop/              # KFZ-Werkstatt
├── disinfection/          # Desinfektion
├── height_rescue/         # Höhenrettung
├── diving/                # Taucher
├── equipment/             # Ausrüstung
├── it_hardware/           # IT-Hardware
├── vehicle_handover/      # Fahrzeugübernahme
├── info_monitors/         # Dashboard-Builder
├── procurement/           # Bestellwesen
├── inventory_check/       # Inventur
├── documents/             # Dokumentenmanagement
├── notifications/         # Benachrichtigungen
├── audit/                 # Audit-Trail
├── reporting/             # Reports & KPIs
└── api/                   # REST API
```

---

## 🔧 Wichtige Befehle

### Entwicklung

```bash
# Django Development Server
python manage.py runserver

# Migrations erstellen
python manage.py makemigrations

# Migrations anwenden
python manage.py migrate

# Superuser erstellen
python manage.py createsuperuser

# Shell öffnen
python manage.py shell

# Tests ausführen
python manage.py test

# Permissions Setup
python manage.py setup_permissions
```

### Docker

```bash
# Container starten
docker-compose up -d

# Container stoppen
docker-compose down

# Logs ansehen
docker-compose logs -f web

# In Container einloggen
docker-compose exec web bash

# Datenbank-Backup
docker-compose exec db pg_dump -U flvs_user flvs > backup.sql
```

---

## 📚 Wichtige Dateien für Claude Code

Diese Dateien dienen als **Single Source of Truth (SSOT)** und sollten immer konsultiert werden:

1. **CLAUDE.md** - Vollständige Projektbeschreibung, Technologie-Stack, Module
2. **ARCHITECTURE.md** - System-Architektur, Layer-Beschreibung, Patterns
3. **DATA_MODEL.md** - Datenmodell, Entity-Relationships, Model-Definitionen
4. **PERMISSIONS.md** - Berechtigungskonzept, Rollen, Security
5. **core/constants.py** - Enums, Choices, Konstanten

---

## 🎯 Claude Code Workflow

### Typischer Entwicklungsablauf mit Claude:

```
1. Neues Feature planen
   └─> Claude: "Ich möchte Feature X implementieren. 
                Prüfe bitte CLAUDE.md und ARCHITECTURE.md 
                für Kontext und schlage eine Implementierung vor."

2. Models erstellen
   └─> Claude: "Erstelle die Models für Modul Y basierend auf 
                DATA_MODEL.md. Beachte die Vererbung von 
                AbstractInventoryItem."

3. Permissions hinzufügen
   └─> Claude: "Füge die Permissions für Modul Y hinzu, 
                gemäß PERMISSIONS.md Sektion 'Custom Permissions'."

4. Views implementieren
   └─> Claude: "Erstelle Class-Based Views für CRUD-Operationen 
                auf Modul Y. Verwende HTMX-Patterns aus ARCHITECTURE.md 
                und die Permission-Mixins aus PERMISSIONS.md."

5. Templates erstellen
   └─> Claude: "Erstelle Templates für Modul Y mit HTMX und 
                Tailwind CSS. Beachte die Template-Struktur 
                und Partials-Pattern."

6. Tests schreiben
   └─> Claude: "Schreibe Unit-Tests für die Models und Services 
                von Modul Y. Verwende Factory Boy für Test-Daten."

7. Migration erstellen und anwenden
   └─> Claude: "Erstelle und überprüfe die Migration für Modul Y."
```

### Best Practices für Prompts:

✅ **GUT:**
```
"Implementiere die Medication-Verwaltung gemäß DATA_MODEL.md. 
Beachte besonders:
1. Vererbung von AbstractInventoryItem
2. BTM-Sicherheit aus PERMISSIONS.md
3. Chargen-Rückverfolgung
4. Temperatur-Logging"
```

❌ **SCHLECHT:**
```
"Mach ein Medikamenten-Ding"
```

---

## 🔐 Sicherheits-Checkliste

Vor Production-Deployment prüfen:

- [ ] `DEBUG = False` in settings
- [ ] `SECRET_KEY` aus Environment-Variable
- [ ] `ALLOWED_HOSTS` konfiguriert
- [ ] Alle Security-Settings aus ARCHITECTURE.md aktiv
- [ ] 2FA für BTM-Beauftragte implementiert und getestet
- [ ] Audit-Logging für alle kritischen Operationen
- [ ] Backup-Strategie implementiert
- [ ] SSL/TLS-Zertifikate konfiguriert
- [ ] Firewall-Regeln gesetzt
- [ ] Datenbank-Credentials sicher
- [ ] BTM-Vier-Augen-Prinzip getestet
- [ ] Permission-Audit durchgeführt

---

## 📦 Dependencies

### Core Django Packages
```txt
Django>=5.0,<5.1
django-environ>=0.11.0
psycopg2-binary>=2.9.9
django-redis>=5.4.0
celery>=5.3.4
django-celery-beat>=2.5.0
django-celery-results>=2.5.1
```

### Security & Permissions
```txt
django-guardian>=2.4.0
django-axes>=6.1.1
django-otp>=1.3.0
qrcode>=7.4.2
```

### Forms & Admin
```txt
django-crispy-forms>=2.1
crispy-tailwind>=1.0.0
django-import-export>=3.3.0
```

### Files & Media
```txt
Pillow>=10.1.0
python-magic>=0.4.27
```

### API
```txt
djangorestframework>=3.14.0
django-filter>=23.5
drf-spectacular>=0.27.0
djangorestframework-simplejwt>=5.3.1
```

### Background Tasks
```txt
redis>=5.0.1
```

### Utilities
```txt
python-dateutil>=2.8.2
pytz>=2023.3
```

### Development & Testing
```txt
django-debug-toolbar>=4.2.0
factory-boy>=3.3.0
faker>=20.1.0
pytest>=7.4.3
pytest-django>=4.7.0
coverage>=7.3.2
```

---

## 🗄️ Datenbank-Setup

### PostgreSQL Installation (Ubuntu)

```bash
# PostgreSQL installieren
sudo apt update
sudo apt install postgresql postgresql-contrib

# PostgreSQL Service starten
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Datenbank und User erstellen
sudo -u postgres psql

CREATE DATABASE flvs;
CREATE USER flvs_user WITH PASSWORD 'your_secure_password';
ALTER ROLE flvs_user SET client_encoding TO 'utf8';
ALTER ROLE flvs_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE flvs_user SET timezone TO 'Europe/Berlin';
GRANT ALL PRIVILEGES ON DATABASE flvs TO flvs_user;
\q
```

### Redis Installation

```bash
# Redis installieren
sudo apt install redis-server

# Redis starten
sudo systemctl start redis
sudo systemctl enable redis

# Testen
redis-cli ping
# Sollte "PONG" zurückgeben
```

---

## 🐳 Docker Setup (Alternative)

### docker-compose.yml

```yaml
version: '3.8'

services:
  db:
    image: postgres:15-alpine
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_DB=flvs
      - POSTGRES_USER=flvs_user
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U flvs_user"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5

  web:
    build: .
    command: python manage.py runserver 0.0.0.0:8000
    volumes:
      - .:/app
      - media_volume:/app/media
      - static_volume:/app/static
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://flvs_user:${DB_PASSWORD}@db:5432/flvs
      - REDIS_URL=redis://redis:6379/0
      - DJANGO_SETTINGS_MODULE=flvs_project.settings.development
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy

  celery_worker:
    build: .
    command: celery -A flvs_project worker -l info
    volumes:
      - .:/app
    environment:
      - DATABASE_URL=postgresql://flvs_user:${DB_PASSWORD}@db:5432/flvs
      - REDIS_URL=redis://redis:6379/0
      - DJANGO_SETTINGS_MODULE=flvs_project.settings.development
    depends_on:
      - db
      - redis

  celery_beat:
    build: .
    command: celery -A flvs_project beat -l info
    volumes:
      - .:/app
    environment:
      - DATABASE_URL=postgresql://flvs_user:${DB_PASSWORD}@db:5432/flvs
      - REDIS_URL=redis://redis:6379/0
      - DJANGO_SETTINGS_MODULE=flvs_project.settings.development
    depends_on:
      - db
      - redis

volumes:
  postgres_data:
  redis_data:
  media_volume:
  static_volume:
```

### Dockerfile

```dockerfile
FROM python:3.11-slim

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Arbeitsverzeichnis
WORKDIR /app

# System-Dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    libpq-dev \
    gcc \
    python3-dev \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Python-Dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Projekt-Dateien
COPY . .

# Collectstatic (für Production)
# RUN python manage.py collectstatic --noinput

# Expose Port
EXPOSE 8000

# Startbefehl (wird von docker-compose überschrieben)
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "flvs_project.wsgi:application"]
```

### .env.example

```env
# Django
DEBUG=True
SECRET_KEY=your-secret-key-here-change-in-production
DJANGO_SETTINGS_MODULE=flvs_project.settings.development
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DB_NAME=flvs
DB_USER=flvs_user
DB_PASSWORD=your_secure_password_here
DB_HOST=localhost
DB_PORT=5432
DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_URL=redis://${REDIS_HOST}:${REDIS_PORT}/0

# Email (für Benachrichtigungen)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@example.com
EMAIL_HOST_PASSWORD=your-app-password

# Celery
CELERY_BROKER_URL=${REDIS_URL}
CELERY_RESULT_BACKEND=${REDIS_URL}

# Security
CSRF_COOKIE_SECURE=False  # True in Production
SESSION_COOKIE_SECURE=False  # True in Production
SECURE_SSL_REDIRECT=False  # True in Production

# Media & Static
MEDIA_ROOT=/app/media
STATIC_ROOT=/app/staticfiles

# Backup
BACKUP_DIR=/backups
BACKUP_ENCRYPTION_KEY=your-encryption-key-here

# Monitoring (optional)
SENTRY_DSN=
```

---

## 🧪 Testing

### Test-Struktur

```
app_name/
└── tests/
    ├── __init__.py
    ├── test_models.py       # Model-Tests
    ├── test_services.py     # Business-Logic-Tests
    ├── test_views.py        # View-Tests
    ├── test_api.py          # API-Tests
    ├── test_permissions.py  # Permission-Tests
    └── factories.py         # Factory Boy Factories
```

### Tests ausführen

```bash
# Alle Tests
python manage.py test

# Spezifische App
python manage.py test medical

# Mit Coverage
coverage run --source='.' manage.py test
coverage report
coverage html  # HTML-Report in htmlcov/

# Pytest (alternative)
pytest
pytest --cov=. --cov-report=html
```

### Beispiel Test

```python
# medical/tests/test_models.py
from django.test import TestCase
from django.contrib.auth import get_user_model
from decimal import Decimal
from medical.models import Medication
from .factories import MedicationFactory, UserFactory

User = get_user_model()

class MedicationModelTest(TestCase):
    
    def setUp(self):
        self.user = UserFactory()
        self.medication = MedicationFactory(
            quantity=100,
            threshold_warning=20,
            threshold_critical=10
        )
    
    def test_is_below_warning(self):
        """Test Warnschwelle-Check"""
        self.medication.quantity = 15
        self.assertTrue(self.medication.is_below_warning)
        
        self.medication.quantity = 25
        self.assertFalse(self.medication.is_below_warning)
    
    def test_is_below_critical(self):
        """Test kritische Schwelle"""
        self.medication.quantity = 5
        self.assertTrue(self.medication.is_below_critical)
    
    def test_adjust_quantity(self):
        """Test Bestandsanpassung"""
        old_quantity = self.medication.quantity
        self.medication.adjust_quantity(
            amount=-10,
            reason="Test-Ausgabe",
            user=self.user
        )
        
        self.assertEqual(
            self.medication.quantity,
            old_quantity - 10
        )
```

---

## 📊 Monitoring & Logging

### Logging-Konfiguration

```python
# settings/base.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
        'json': {
            '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': '%(asctime)s %(name)s %(levelname)s %(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/flvs.log',
            'maxBytes': 1024 * 1024 * 10,  # 10 MB
            'backupCount': 5,
            'formatter': 'json'
        },
        'audit_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/audit.log',
            'maxBytes': 1024 * 1024 * 50,  # 50 MB
            'backupCount': 10,
            'formatter': 'json'
        }
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
        },
        'flvs': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
        },
        'audit': {
            'handlers': ['audit_file'],
            'level': 'INFO',
            'propagate': False,
        }
    }
}
```

---

## 🔄 Backup & Recovery

### Automatisches Backup (Cronjob)

```bash
# /etc/cron.d/flvs-backup
0 2 * * * root /usr/local/bin/backup-flvs.sh

# /usr/local/bin/backup-flvs.sh
#!/bin/bash
BACKUP_DIR="/backups/flvs"
DATE=$(date +%Y%m%d_%H%M%S)

# Database Backup
docker-compose exec -T db pg_dump -U flvs_user flvs | \
  gzip > "${BACKUP_DIR}/db_${DATE}.sql.gz"

# Media Files Backup
tar -czf "${BACKUP_DIR}/media_${DATE}.tar.gz" /app/media

# Alte Backups löschen (älter als 30 Tage)
find ${BACKUP_DIR} -type f -mtime +30 -delete

echo "Backup completed: ${DATE}"
```

### Recovery

```bash
# Datenbank wiederherstellen
gunzip < backup.sql.gz | docker-compose exec -T db psql -U flvs_user flvs

# Media-Files wiederherstellen
tar -xzf media_backup.tar.gz -C /app/
```

---

## 🚀 Production-Deployment

### 1. Server vorbereiten

```bash
# System aktualisieren
sudo apt update && sudo apt upgrade -y

# Notwendige Pakete installieren
sudo apt install -y git python3-pip python3-venv \
  postgresql postgresql-contrib redis-server nginx

# Firewall konfigurieren
sudo ufw allow 22    # SSH
sudo ufw allow 80    # HTTP
sudo ufw allow 443   # HTTPS
sudo ufw enable
```

### 2. Projekt deployen

```bash
# Projektverzeichnis erstellen
sudo mkdir -p /var/www/flvs
sudo chown $USER:$USER /var/www/flvs

# Repository klonen
cd /var/www/flvs
git clone <your-repo-url> .

# Virtual Environment erstellen
python3 -m venv venv
source venv/bin/activate

# Dependencies installieren
pip install -r requirements.txt

# .env konfigurieren
cp .env.example .env
nano .env  # Anpassen für Production

# Migrations ausführen
python manage.py migrate

# Static-Files sammeln
python manage.py collectstatic --noinput

# Permissions setup
python manage.py setup_permissions

# Superuser erstellen
python manage.py createsuperuser
```

### 3. Gunicorn konfigurieren

```bash
# /etc/systemd/system/flvs.service
[Unit]
Description=FLVS Gunicorn daemon
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/flvs
EnvironmentFile=/var/www/flvs/.env
ExecStart=/var/www/flvs/venv/bin/gunicorn \
  --workers 3 \
  --bind unix:/var/www/flvs/flvs.sock \
  flvs_project.wsgi:application

[Install]
WantedBy=multi-user.target
```

```bash
# Service starten
sudo systemctl start flvs
sudo systemctl enable flvs
```

### 4. Nginx konfigurieren

```nginx
# /etc/nginx/sites-available/flvs
server {
    listen 80;
    server_name your-domain.com;

    client_max_body_size 20M;

    location = /favicon.ico { access_log off; log_not_found off; }
    
    location /static/ {
        alias /var/www/flvs/staticfiles/;
    }
    
    location /media/ {
        alias /var/www/flvs/media/;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/var/www/flvs/flvs.sock;
    }
}
```

```bash
# Nginx konfigurieren
sudo ln -s /etc/nginx/sites-available/flvs /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 5. SSL mit Let's Encrypt

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

### 6. Celery als Service

```bash
# /etc/systemd/system/celery.service
[Unit]
Description=Celery Service
After=network.target

[Service]
Type=forking
User=www-data
Group=www-data
WorkingDirectory=/var/www/flvs
EnvironmentFile=/var/www/flvs/.env
ExecStart=/var/www/flvs/venv/bin/celery -A flvs_project worker \
  --detach --loglevel=info

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl start celery
sudo systemctl enable celery
```

---

## 📞 Support & Kontakt

**Projekt-Repository:** [Git-URL]  
**Dokumentation:** [Wiki-URL]  
**Issue-Tracker:** [Issues-URL]

---

## 📝 Lizenz

[Lizenz hier einfügen]

---

## ✅ Quick-Start Checklist

- [ ] Ubuntu Server vorbereitet
- [ ] PostgreSQL installiert und konfiguriert
- [ ] Redis installiert
- [ ] Python 3.11+ installiert
- [ ] Virtual Environment erstellt
- [ ] Dependencies installiert (`pip install -r requirements.txt`)
- [ ] `.env` Datei konfiguriert
- [ ] Datenbank-Migrations ausgeführt (`python manage.py migrate`)
- [ ] Superuser erstellt (`python manage.py createsuperuser`)
- [ ] Permissions setup (`python manage.py setup_permissions`)
- [ ] Static-Files gesammelt (`python manage.py collectstatic`)
- [ ] Development-Server läuft (`python manage.py runserver`)
- [ ] Admin-Interface erreichbar (http://localhost:8000/admin/)
- [ ] SSOT-Dateien (CLAUDE.md, etc.) im Projekt vorhanden
- [ ] Claude Code bereit

---

**Viel Erfolg beim Entwickeln! 🚒🔥**
