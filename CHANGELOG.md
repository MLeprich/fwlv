# Changelog - FLVS Entwicklung

Alle wichtigen Änderungen am Projekt werden in dieser Datei dokumentiert.

---

## [Unreleased]

### 2025-10-04 - Medical Module (Rettungsdienst) - Vollständig implementiert

#### ✅ Rettungsdienst-Modul abgeschlossen

**Kern-Funktionalität:**
- Vollständiges CRUD für medizinische Artikel (Medikamente, Medizintechnik, Verbrauchsmaterial)
- Chargen-Verwaltung mit Verfallsdatum-Tracking
- Lagerbewegungen (Eingang, Ausgang, Umbuchung, Entsorgung)
- BTM-Bereich (Betäubungsmittel) mit Vier-Augen-Prinzip
- Schwellwert-Management und Low-Stock-Alerts
- Ablaufende Chargen mit mehrstufigen Warnungen (7/14/30/90 Tage)
- Kühlketten-Management mit Temperatur-Logging
- Wartungs-/Prüfungs-Tracking für Medizintechnik

**QR-Code & Barcode-Integration:**
- QR-Code-Generierung für Artikel (Name, Artikelnummer, PZN) und Chargen (inkl. Verfallsdatum, Lagerort)
- Optionale Barcode-Generierung (Code128) für PZN und Chargennummern
- SVG-Format für skalierbare Ausgabe
- Download-Funktion für beide Code-Typen
- Implementiert in: `medical/models.py` (generate_qr_code, generate_barcode)

**Templates & UI:**
- Dashboard mit KPI-Kacheln und Quick-Actions
- Item-Detail mit Chargen-Übersicht und QR/Barcode-Tab
- Batch-Detail mit vollständiger Historie und Codes
- Lagerbewegungen-Formulare mit dynamischer Chargen-Auswahl
- Statistik-Kacheln für ablaufende Chargen (korrigiert: expiring_7days, expiring_14days, etc.)
- Import/Export-Funktionalität (Excel)

**Sidebar-Navigation:**
- Icon-Alignment im collapsed State korrigiert
- Dashboard und Kategorie-Icons perfekt zentriert
- Einheitliche Klassen: `px-3 mx-2 justify-center` im collapsed State
- Dynamisches Verhalten mit Alpine.js `:class` Binding

**Technische Details:**
- Models: MedicalItem, MedicalBatch, MedicalStockMovement, MedicalCategory
- Views: 30+ Class-based und Function-based Views
- Forms: Dynamische Formulare mit HTMX-Integration
- URLs: Vollständiges URL-Schema mit app_name='medical'
- Permissions: Granulare Berechtigungen inkl. custom BTM-Permissions

### 2025-10-04 - UI Templates: Settings Page Modularization

#### ✅ Template-Modularisierung implementiert

**Einstellungen-Seite refactored:**
- Haupt-Template `templates/core/settings.html` von 573 auf 119 Zeilen reduziert (-79%)
- 6 modulare Sub-Templates erstellt:
  - `templates/core/settings/account.html` - Account-Einstellungen
  - `templates/core/settings/notifications.html` - Benachrichtigungs-Präferenzen
  - `templates/core/settings/appearance.html` - Darstellungs-Optionen
  - `templates/core/settings/security.html` - Sicherheits-Einstellungen
  - `templates/core/settings/privacy.html` - Datenschutz & DSGVO
  - `templates/core/settings/system.html` - System-Administration (nur Admins)

**Erweiterte Features implementiert:**
- **Benachrichtigungen:** 5 Kategorien (Kritische Bestände, Ablaufende Artikel, Prüfungen, Bestellungen, Fahrzeugübernahme)
- **Darstellung:** Theme-Auswahl, Sidebar-Verhalten, Tabellen-Dichte, Ansichts-Präferenzen
- **Sicherheit:** 2FA-Verwaltung, Backup-Codes, Anmelde-Aktivitäten, Sicherheits-Empfehlungen
- **Datenschutz:** DSGVO-konforme Datenerfassung, Account-Löschung mit Aufbewahrungspflichten (BTM, Audit)
- **System:** Status-Dashboard, Quick-Links, Wartungsmodus

**Technische Verbesserungen:**
- Alpine.js Section-Switching ohne Page-Reload
- Modulare Struktur für bessere Wartbarkeit
- Wiederverwendbare Sub-Templates (HTMX-ready)
- Team-fähig (paralleles Arbeiten ohne Merge-Konflikte)

#### ✅ Dokumentation aktualisiert

**UI_STRUCTURE_VISUAL.md (Version 1.2):**
- Sub-Template Pattern für Einstellungen dokumentiert
- Template-Struktur-Diagramm hinzugefügt
- Vorteile der Modularisierung beschrieben
- Code-Beispiele für Haupt- und Sub-Templates

**UI_UX_DESIGN.md:**
- Neuer Section: "Template-Modularisierung Best Practices"
- Wann Sub-Templates verwenden (Entscheidungshilfe)
- Naming Conventions dokumentiert
- 6 Vorteile der Modularisierung aufgelistet
- Layout-Vorlage "Einstellungs-Ansicht" hinzugefügt

**Auswirkung auf zukünftige Module:**
- Pattern kann für andere komplexe Seiten wiederverwendet werden
- Personal-Detail-Seite (6 Tabs) → Sub-Templates
- Fahrzeugverwaltung (Multi-Step-Forms) → Sub-Templates
- Dashboard-Builder → Sub-Templates für Widget-Typen

---

### 2025-10-03 - Phase 8: Production Readiness (Performance & Security)

#### ✅ Performance-Optimierung

**Dokumentation erstellt:**
- `docs/PERFORMANCE_AUDIT.md` - Umfassende Performance-Analyse
  - Index-Analyse aller Apps (14-17 Indizes pro kritischer App)
  - N+1 Query-Probleme identifiziert
  - select_related/prefetch_related Strategien
  - Caching-Strategie (Redis, QuerySet, Template-Fragment)
  - Bulk-Operations Best-Practices
  - Celery Background Tasks (Reports, KPIs, Alerts)
  - Pagination-Strategien
  - Performance-Benchmark-Ziele definiert

- `docs/ADMIN_OPTIMIZATION_GUIDE.md` - Admin Query-Optimierung
  - get_queryset() Override für alle Admin-Klassen
  - Geschätzter Performance-Gewinn: **95-98% weniger Queries**
  - 15 Apps mit detaillierten Optimierungsvorschlägen
  - Test-Strategie mit Django Debug Toolbar
  - Code-Review-Checklist

**Optimierungen dokumentiert:**
- **Medical Admin:** select_related (category, location, supplier, approved_by)
- **Equipment Admin:** select_related (assigned_vehicle, location)
- **Documents Admin:** prefetch_related (versions, reviews, allowed_users)
- **Procurement Admin:** prefetch_related (items, approvals, goods_receipts)
- **Info Monitors Admin:** select_related (dashboard__profile, kpi)

#### ✅ Security-Audit

**Dokumentation erstellt:**
- `docs/SECURITY_AUDIT.md` - Umfassender Security-Review
  - Django Settings Security (17 Punkte)
  - HTTPS/SSL-Enforcement (HSTS, Secure Cookies)
  - Authentication & Authorization (2FA, Brute-Force-Protection)
  - SQL-Injection-Prävention (ORM-Validierung)
  - XSS-Protection (Template-Escaping)
  - CSRF-Protection (HTMX-Integration)
  - File-Upload-Security (MIME-Type-Validierung)
  - BTM-Bereich-Security (Vier-Augen-Prinzip, Audit-Logging)
  - API-Security (JWT, Rate-Limiting)
  - Dependency-Security (safety check)
  - Environment-Variablen-Management
  - Backup & Disaster Recovery

**BTM-Security geprüft:**
- ✅ Vier-Augen-Prinzip implementiert (approved_by != user)
- ✅ BTM-Permission existiert (`medical.approve_btm_movement`)
- ✅ Approval-Status-Tracking (PENDING/APPROVED/REJECTED)
- ⚠️ TODO: 2FA-Pflicht für BTM-Beauftragte (Infrastructure vorhanden)
- ⚠️ TODO: IP-Tracking für BTM-Zugriffe
- ✅ Admin-Interface zeigt BTM-Status mit Badges

#### ✅ Production-Settings

**File erstellt:** `flvs_project/settings/production.py`

**Security-Features:**
- DEBUG = False (mit Runtime-Validation)
- SECRET_KEY aus Environment (Pflicht)
- ALLOWED_HOSTS Validation
- HTTPS/SSL-Enforcement (SECURE_SSL_REDIRECT, HSTS)
- Cookie-Security (Secure, HttpOnly, SameSite='Strict')
- File-Upload-Limits (20 MB)
- Admin-URL aus Environment (geheimer Pfad)
- Database Connection Pooling (CONN_MAX_AGE=600)
- Redis-Caching optimiert (max_connections=50)
- Celery-Compression (gzip)
- Template-Caching aktiviert
- Debug-Toolbar deaktiviert
- BTM-2FA-Pflicht konfigurierbar
- Sentry-Integration vorbereitet

**Logging-Strategie:**
- `logs/flvs.log` - Application-Logs (10 MB, 10 Backups)
- `logs/audit.log` - Audit-Trail (50 MB, 20 Backups)
- `logs/btm_audit.log` - BTM-Zugriffe (100 MB, 50 Backups)
- `logs/security.log` - Security-Events (50 MB, 20 Backups)
- Admin-Email bei Errors (ERROR-Level)

**API-Security:**
- Rate-Limiting (100/hour anonym, 1000/hour authentifiziert)
- Nur JSON-Renderer (kein Browsable API)
- JWT-Authentifizierung
- CORS vorbereitet (optional)

**Production-Validation:**
- Runtime-Checks für DEBUG, SECRET_KEY, ALLOWED_HOSTS
- Fehler-Meldungen bei unsicherer Konfiguration

#### ✅ Deployment-Guide

**Dokumentation erstellt:** `docs/DEPLOYMENT_GUIDE.md`

**Deployment-Architektur:**
```
Internet → Nginx (SSL) → Gunicorn → Django
           ↓              ↓
       PostgreSQL     Celery (Worker + Beat) + Redis
```

**Umfang:**
- Server-Vorbereitung (Ubuntu 20.04+, Firewall, Pakete)
- PostgreSQL Setup (Database, User, Backup-Script)
- Redis-Konfiguration
- FLVS-Installation (Virtual Env, Dependencies, Migrations)
- Gunicorn-Setup (Systemd Service, Konfiguration)
- Celery-Setup (Worker + Beat Services)
- Nginx-Konfiguration (SSL, Security-Headers, Static-Files)
- SSL-Zertifikat (Let's Encrypt, Auto-Renewal)
- Monitoring & Logging (Log-Rotation, Fail2Ban)
- Final Checks (Deployment-Checklist)
- Updates & Wartung (Code-Updates, Backups)
- Troubleshooting (häufige Probleme + Lösungen)

**Systemd Services:**
- `flvs.service` - Gunicorn Application Server
- `flvs-celery.service` - Celery Worker
- `flvs-celery-beat.service` - Celery Scheduler

**Security-Features:**
- SSL/TLS (TLS 1.2+, Modern Ciphers)
- Security-Headers (HSTS, X-Frame-Options, CSP-Ready)
- File-Upload-Limits (20 MB)
- Fail2Ban-Integration
- Log-Rotation (täglich, 30 Tage Retention)

#### 📊 Performance-Metriken (Ziele)

**Response-Zeiten (95th Percentile):**
- Dashboard: < 500ms
- Liste (50 Items): < 300ms
- Detail-View: < 200ms
- API-Endpoint: < 250ms
- Report-Generierung: < 30s (async)
- KPI-Berechnung: < 10s (cached)

**Database-Queries:**
- Dashboard: < 20 Queries
- Liste: < 10 Queries
- Detail: < 5 Queries
- N+1 Queries: 0 Toleranz (100% vermeidbar)

#### 🔒 Security-Checkliste (Production)

**Kritisch (vor Production):**
- [x] DEBUG = False
- [x] SECRET_KEY aus Environment
- [x] ALLOWED_HOSTS konfiguriert
- [x] HTTPS/SSL-Enforcement
- [x] Cookie-Security (Secure, HttpOnly)
- [x] HSTS aktiviert (1 Jahr)
- [x] CSRF/XSS-Protection verifiziert
- [x] File-Upload-Validierung dokumentiert
- [x] BTM-Vier-Augen-Prinzip geprüft
- [x] API Rate-Limiting konfiguriert
- [x] Brute-Force-Protection (Axes)
- [x] Logging-Strategie implementiert
- [ ] 2FA für BTM-Beauftragte aktivieren
- [ ] SSL-Zertifikat installieren
- [ ] Backups testen

**Nice-to-have:**
- [ ] Sentry-Integration
- [ ] Penetration-Test
- [ ] Security-Headers erweitern (CSP)
- [ ] WAF (Web Application Firewall)

#### 🎯 Nächste Schritte

1. **Admin-Optimierungen implementieren** (select_related in allen Admin-Klassen)
2. **Celery Tasks implementieren** (Reports, KPIs, Alerts)
3. **2FA-Setup** für BTM-Beauftragte
4. **Production-Deployment** durchführen
5. **User-Testing** mit Feuerwehr
6. **Performance-Tests** mit Django Silk
7. **Security-Scan** (SSL Labs, Security Headers)

---

### 2025-10-03 - Info Monitors App vollständig implementiert (Dashboard-Builder für Info-Monitore)

#### ✅ Hinzugefügt
- **Info Monitors Models (586 Zeilen, 4 Modelle):**
  - `WidgetType` - 12 Widget-Typen (KPI, CHART, TABLE, LIST, MAP, GAUGE, PROGRESS, COUNTER, ALERT, CLOCK, WEATHER, CUSTOM)
  - `ChartType` - 7 Diagramm-Typen (LINE, BAR, PIE, DOUGHNUT, AREA, RADAR, SCATTER)
  - `DashboardTheme` - 3 Themes (LIGHT, DARK, AUTO)
  - `WidgetSize` - 5 Größen (SMALL=1, MEDIUM=2, LARGE=3, XLARGE=4, FULL=12 Spalten)
  - **MonitorProfile** - Monitor-Profile für verschiedene Einsatzzwecke
    - **Basis:** name, description, icon, color
    - **Status:** is_active, is_default (Standard-Profil)
    - **Display:** display_order
  - **Dashboard** - Dashboard-Konfiguration
    - **Verknüpfung:** profile (FK), name, description
    - **Layout:** theme, columns (1-12, Standard 12), fullscreen_default
    - **Optionen:** hide_header, hide_sidebar
    - **Auto-Refresh:** auto_refresh, refresh_interval (min. 5 Sekunden)
    - **Berechtigungen:** is_public, allowed_users (M2M), is_active
    - **Display:** display_order
    - **Statistiken:** view_count, last_viewed_at
    - **Helper:** increment_view_count()
  - **Widget** - Dashboard-Widget (Flexible Datenvisualisierung)
    - **Verknüpfung:** dashboard (FK), title, description, widget_type
    - **Position & Größe:** row, column (0-11), width (WidgetSize), height (px, min. 100)
    - **Datenquelle Option 1:** kpi (FK zu reporting.KPI)
    - **Datenquelle Option 2:** data_source (SQL/API-Endpoint), config (JSON)
    - **Chart-Settings:** chart_type (nur für CHART-Widgets)
    - **Styling:** background_color, text_color, border_color
    - **Refresh:** auto_refresh, refresh_interval (min. 5 Sekunden)
    - **Status:** is_active, display_order
    - **Cache:** cached_data (JSON), last_updated_at
    - **Helper:** get_width_class() (Bootstrap col-1 bis col-12), update_cached_data()
  - **WidgetAlert** - Alert-Konfiguration für Widgets
    - **Verknüpfung:** widget (FK), name
    - **Bedingung:** condition (greater/less/equal/not_equal/between), threshold_value, threshold_value_max
    - **Alert-Eigenschaften:** severity (info/warning/error/critical), message
    - **Benachrichtigung:** send_notification, notification_users (M2M)
    - **Status:** is_active, last_triggered_at, trigger_count
    - **Helper:** check_condition(value), trigger()

- **Info Monitors Admin (520 Zeilen, 4 Admin-Klassen + 2 Inlines):**
  - **MonitorProfileAdmin:**
    - List-Display: name, dashboard_count (farbcodiert 0=grau, <3=blau, ≥3=grün), default_badge, active_badge, display_order
    - Filterable: is_active, is_default
    - Search: name, description
    - Fields: (Basis-Info, Icon & Farbe, Status & Display)
  - **DashboardAdmin:**
    - List-Display: name, profile, theme_badge (Light=orange, Dark=grau, Auto=blau), widget_count (farbcodiert), view_count_badge (👁 Emoji)
    - List-Display: refresh_badge (Auto-Refresh ON/OFF), public_badge, active_badge
    - Filterable: profile, theme, is_public, is_active, auto_refresh
    - Search: name, description
    - Inlines: WidgetInline (tabular, 10 extra)
    - Filter-Horizontal: allowed_users
    - Fields: (Dashboard-Info, Profil, Layout-Einstellungen, Auto-Refresh, Vollbild-Modus, Berechtigungen, Status, Statistiken)
  - **WidgetAdmin:**
    - List-Display: title, dashboard, type_badge (12 Farben je Widget-Typ), size_badge (Small bis Full), position_display (R0 C0 Format)
    - List-Display: kpi, refresh_badge, active_badge, display_order
    - Filterable: dashboard, widget_type, chart_type, auto_refresh, is_active
    - Search: title, description
    - Inlines: WidgetAlertInline (tabular, 5 extra)
    - Fields: (Widget-Info, Dashboard, Widget-Typ & Chart, Position & Größe, Datenquelle, Konfiguration, Styling, Refresh, Status, Cache)
  - **WidgetAlertAdmin:**
    - List-Display: name, widget, severity_badge (Info=blau, Warning=orange, Error=rot, Critical=dunkelrot mit ⚠), condition_display (Wert oder Min-Max)
    - List-Display: trigger_count_badge (mit 🚨 Emoji), active_badge, last_triggered_at
    - Filterable: widget__dashboard, severity, condition, is_active
    - Search: name, message
    - Filter-Horizontal: notification_users
    - Fields: (Alert-Info, Widget, Bedingung, Schwellwerte, Alert-Eigenschaften, Benachrichtigung, Status, Statistiken)

- **URL-Konfiguration:**
  - `info_monitors/urls.py` - URL-Namespace 'info_monitors' (Views in späteren Phasen)
  - Integration in `flvs_project/urls.py` - Pfad 'monitors/'

- **Migrations:**
  - `0001_initial.py` - Erstellt alle 4 Modelle (MonitorProfile, Dashboard, Widget, WidgetAlert)
  - **Indizes:** 14 Indizes für optimierte Abfragen
    - MonitorProfile: is_active+display_order, is_default
    - Dashboard: profile+is_active, is_public, display_order
    - Widget: dashboard+is_active, widget_type, kpi, row+column
    - WidgetAlert: widget+is_active, severity

#### 📊 Statistiken
- **Models:** 4 Modelle (MonitorProfile, Dashboard, Widget, WidgetAlert)
- **Codezeilen:** 586 (models.py) + 520 (admin.py) = 1106 Zeilen
- **Choices/Enums:** 4 (WidgetType mit 12 Werten, ChartType mit 7, DashboardTheme mit 3, WidgetSize mit 5)
- **Foreign Keys:** 3 (Dashboard→MonitorProfile, Widget→Dashboard+KPI, WidgetAlert→Widget)
- **M2M-Relationen:** 3 (Dashboard.allowed_users, Widget, WidgetAlert.notification_users)
- **Admin-Klassen:** 4 (MonitorProfileAdmin, DashboardAdmin, WidgetAdmin, WidgetAlertAdmin)
- **Inlines:** 2 (WidgetInline, WidgetAlertInline)
- **Indizes:** 14

#### 🎯 Use-Cases
- **Leitstelle:** Aktive Einsätze (Counter), Verfügbare Fahrzeuge (Gauge), Wetter (Weather-Widget)
- **Werkstatt:** Überfällige Wartungen (Alert), Ersatzteil-Bestand (KPI), Service-Historie (Chart)
- **Lager:** Niedrige Bestände (Alert), Ablaufende Items (List), Bestellstatus (Progress)
- **Management:** KPI-Dashboards (KPIs aus Reporting App), Compliance-Status (Gauge)

#### 🔗 Integration
- **Reporting App:** Widget kann KPI (FK) als Datenquelle nutzen
- **Custom Queries:** data_source-Feld für flexible SQL/API-Abfragen
- **Notifications App:** WidgetAlert kann Benachrichtigungen triggern
- **Permissions:** Dashboard.allowed_users für Zugriffskontrolle

#### ⚙️ Besonderheiten
- **12 Widget-Typen:** Flexibilität für alle Anwendungsfälle
- **Bootstrap 12-Spalten-Grid:** Standard-Layout-System
- **Dual-Datenquellen:** KPI-FK oder Custom Query
- **Widget-Level Caching:** cached_data für Performance
- **Alert-System:** 5 Bedingungstypen mit Schweregrad-Stufen
- **Auto-Refresh:** Dashboard & Widget-Level konfigurierbar
- **3 Themes:** Light, Dark, Auto für verschiedene Monitore
- **Vollbild-Modus:** Header/Sidebar ausblendbar

---

### 2025-10-03 - Reporting & KPI App vollständig implementiert (Reporting-System mit KPI-Dashboards & Scheduled Reports)

#### ✅ Hinzugefügt
- **Reporting Models (681 Zeilen, 4 Modelle):**
  - `ReportType` - 10 Report-Typen (INVENTORY, EXPIRING, LOW_STOCK, PROCUREMENT, VEHICLE, INSPECTION, PERSONNEL, DOCUMENT, AUDIT, CUSTOM)
  - `ReportFormat` - 5 Export-Formate (PDF, EXCEL, CSV, HTML, JSON)
  - `ReportStatus` - 5 Status (PENDING, GENERATING, COMPLETED, FAILED, EXPIRED)
  - `ScheduleFrequency` - 6 Frequenzen (DAILY, WEEKLY, MONTHLY, QUARTERLY, YEARLY, CUSTOM)
  - `KPIType` - 6 KPI-Typen (COUNT, SUM, AVERAGE, PERCENTAGE, RATIO, TREND)
  - `KPICategory` - 5 Kategorien (INVENTORY, FINANCIAL, OPERATIONAL, QUALITY, COMPLIANCE)
  - **ReportTemplate** - Wiederverwendbare Report-Definitionen
    - **Basis:** name, description, report_type
    - **Query:** query (SQL/Python-Code), parameters (JSON), template_file
    - **Formate:** available_formats (JSON-Array)
    - **Berechtigungen:** is_public, allowed_users (M2M), is_active
    - **Statistiken:** usage_count mit increment_usage()
  - **Report** - Generierte Reports
    - **Template:** template (FK), title, description, report_type, status
    - **Zeitraum:** date_from, date_to
    - **Parameter:** parameters (JSON)
    - **Datei:** file, file_format, file_size (auto)
    - **Generierung:** generation_started_at, generation_completed_at, generation_duration (auto-berechnet)
    - **Fehler:** error_message
    - **Ablauf:** expires_at (Auto-Löschung)
    - **Statistiken:** download_count, last_downloaded_at
    - **Verknüpfung:** Generic FK (related_content_type, related_object_id)
    - **Helper-Methoden:** is_expired(), get_file_size_display(), increment_download_count(), mark_as_generating(), mark_as_completed(), mark_as_failed()
  - **ReportSchedule** - Zeitgesteuerte Report-Generierung (Celery Beat)
    - **Template:** template (FK), name, description
    - **Zeitplan:** frequency, cron_expression, run_at_time, day_of_week, day_of_month
    - **Parameter:** parameters (JSON), file_format
    - **E-Mail:** send_email, recipients (M2M)
    - **Ablauf:** retention_days (Aufbewahrung)
    - **Status:** is_active, last_run_at, next_run_at, run_count
  - **KPI** - Key Performance Indicators
    - **Basis:** name, description, category, kpi_type
    - **Query:** query (SQL/Python-Code)
    - **Zielwerte:** target_value, threshold_good, threshold_warning, unit
    - **Darstellung:** icon, color, display_order, is_active
    - **Aktualisierung:** refresh_interval, last_calculated_at, last_value
    - **Helper:** get_status_color() - Ampel-Farbe (green/yellow/red/gray)

- **Reporting Admin (628 Zeilen, 4 Admin-Klassen):**
  - **ReportTemplateAdmin**
    - **type_badge:** 10 Report-Typ-Farben (Inventory Blau, Expiring Rot, Low Stock Orange, etc.)
    - **usage_badge:** Verwendungszähler mit Farbcodierung (0: Grau, <10: Blau, <50: Grün, ≥50: Orange)
    - **public_badge:** ✓ Ja (Grün) / ✗ Nein (Grau)
    - **active_badge:** ✓ Aktiv (Grün) / ✗ Inaktiv (Rot)
  - **ReportAdmin**
    - **type_badge:** 10 Report-Typ-Farben
    - **status_badge:** 5 Status-Farben mit Icons (⏳ Generating Blau, ✓ Completed Grün, ✗ Failed Rot)
    - **format_badge:** 5 Format-Farben (PDF Rot, Excel Grün, CSV Blau, HTML Orange, JSON Lila)
    - **period_display:** Zeitraum-Formatierung (Von-Bis)
    - **duration_display:** Generierungsdauer (Sekunden/Minuten)
    - **file_size_display:** Formatierte Dateigröße (B/KB/MB/GB)
    - **download_badge:** Download-Counter mit Farbcodierung (⬇ X)
    - Bulk Actions: mark_as_expired, delete_files
  - **ReportScheduleAdmin**
    - **frequency_badge:** 6 Frequenz-Farben (Daily Grün, Weekly Blau, Monthly Orange, etc.)
    - **format_badge:** 5 Format-Farben
    - **next_run_display:** Nächste Ausführung mit ⚠ Warnung bei Überfälligkeit
    - **run_count_badge:** Ausführungszähler mit Farbcodierung
    - **active_badge:** ✓/✗ Aktiv-Status
    - **email_badge:** 📧 (Grün) / ✗ (Grau)
  - **KPIAdmin**
    - **category_badge:** 5 Kategorie-Farben (Inventory Blau, Financial Grün, Operational Orange, etc.)
    - **type_badge:** 6 Typ-Farben (Count Blau, Sum Grün, Average Orange, Percentage Lila, Ratio Cyan, Trend Pink)
    - **value_display:** Letzter Wert mit Einheit
    - **status_indicator:** Ampel-System (●) in Grün/Gelb/Rot/Grau basierend auf Schwellwerten
    - **refresh_display:** Aktualisierungsintervall (Minuten/Stunden)
    - **active_badge:** ✓/✗ Aktiv-Status

- **URL Configuration:**
  - `/reporting/` - Hauptseite (Placeholder)
  - Integration in flvs_project/urls.py

- **Migrations:**
  - `0001_initial.py` - 4 Modelle, 10 Indizes
    - ReportTemplate-Indizes: report_type+is_active, is_public
    - Report-Indizes: template+created_at, report_type+status, status+created_at, created_by+created_at, expires_at
    - ReportSchedule-Indizes: template+is_active, is_active+next_run_at, frequency
    - KPI-Indizes: category+is_active, kpi_type, is_active+display_order

#### 📝 Notizen
- **Report-Templates:** Wiederverwendbare Report-Definitionen mit Query/Code-Feld für flexible Datenabfragen
- **Celery-Integration:** ReportSchedule vorbereitet für automatische Generierung via Celery Beat
- **Export-Formate:** Unterstützt PDF, Excel, CSV, HTML, JSON (Template-basiert)
- **KPI-Ampel-System:** Automatische Farbcodierung basierend auf Schwellwerten (threshold_good/warning)
- **Generic FK:** Reports können an beliebige Objekte gehängt werden (z.B. Fahrzeug-spezifische Reports)
- **Auto-Expiry:** Reports mit expires_at werden automatisch gelöscht nach Ablauf
- **Phase 7.2 abgeschlossen:** Reporting & KPI-System voll funktionsfähig

---

### 2025-10-03 - Documents App vollständig implementiert (Dokumentenmanagement mit Versionierung & Zugriffsprotokollierung)

#### ✅ Hinzugefügt
- **Documents Models (668 Zeilen, 5 Modelle):**
  - `DocumentType` - 12 Dokumententypen (MANUAL, CERTIFICATE, INVOICE, CONTRACT, PROTOCOL, REPORT, FORM, PHOTO, DRAWING, SPECIFICATION, POLICY, OTHER)
  - `DocumentStatus` - 7 Status (DRAFT, REVIEW, APPROVED, ACTIVE, SUPERSEDED, EXPIRED, ARCHIVED)
  - `AccessLevel` - 5 Zugriffslevel (PUBLIC, INTERNAL, CONFIDENTIAL, RESTRICTED, SECRET)
  - `VersionChangeType` - 4 Änderungstypen (MAJOR, MINOR, PATCH, REVISION)
  - **DocumentCategory** - Hierarchische Kategorisierung (MPTT-Baum)
    - **Hierarchie:** parent (TreeForeignKey für verschachtelte Kategorien)
    - **Darstellung:** icon, color (Tailwind-Classes)
    - **Methoden:** get_full_path() (Vollständiger Pfad), get_document_count() (Dokumente in Kategorie + Unterkategorien)
  - **Document** - Hauptmodell für Dokumente
    - **Auto-Generierung:** document_number (DOC-2025-0001 Format)
    - **Kategorisierung:** category (FK), document_type, status
    - **Datei:** file (mit FileExtensionValidator), file_size (auto), mime_type, version_number
    - **Metadaten:** title, description, tags, author
    - **Gültigkeit:** valid_from, valid_until (auto-expiry bei Ablauf), review_date
    - **Archivierung:** archived_at, archived_by, archive(user) Methode
    - **Verknüpfung:** Generic FK (related_content_type, related_object_id) zu beliebigen Objekten
    - **Sicherheit:** access_level, allowed_users (M2M)
    - **Versionierung:** superseded_by (FK zu neuerer Version)
    - **Statistiken:** view_count, download_count, last_accessed_at
    - **Helper-Methoden:** get_file_extension(), get_file_size_display(), is_expired(), is_review_due(), increment_view_count(), increment_download_count()
  - **DocumentVersion** - Versionshistorie für Dokumente
    - **Version:** version_number, change_type
    - **Datei:** file (in versions/), file_size (auto)
    - **Änderungen:** change_summary, change_details
    - **Unique Constraint:** (document, version_number)
  - **DocumentAccess** - Zugriffsprotokolle (Audit-Trail)
    - **Zugriff:** document (FK), user (FK), access_type (view/download/edit/delete/share)
    - **Details:** ip_address, user_agent, notes
    - **Read-Only:** Nur Lesezugriff im Admin
  - **DocumentReview** - Prüfungs- und Freigabe-Workflow
    - **Prüfung:** reviewer (FK), review_status (pending/approved/rejected/revision)
    - **Termine:** review_date, deadline
    - **Methoden:** is_overdue() - Prüft Frist-Überschreitung

- **Documents Admin (602 Zeilen, 5 Admin-Klassen):**
  - **DocumentCategoryAdmin** (MPTT-Admin)
    - **get_full_path_display:** Zeigt vollständigen Kategorie-Pfad (z.B. "Fahrzeuge > KFZ-Scheine > HU/AU")
    - **document_count_badge:** Anzahl Dokumente mit Farbcodierung (0: Grau, <10: Blau, <50: Grün, ≥50: Orange)
  - **DocumentAdmin** (Haupt-Admin mit 3 Inlines)
    - **status_badge:** 7 Status-Farben (Entwurf Grau, Prüfung Blau, Aktiv Grün, Abgelaufen Rot, etc.)
    - **type_badge:** 12 Typ-Farben (Handbuch Blau, Zertifikat Grün, Rechnung Orange, etc.)
    - **access_level_badge:** 5 Zugriffslevel-Farben mit 🔒 Icon für Vertraulich/Eingeschränkt/Geheim
    - **expiry_badge:** Ablaufdatum mit Warnung (⚠ ABGELAUFEN Rot, <30 Tage Orange, >30 Tage Grün)
    - **review_badge:** Prüfdatum mit Warnung (⚠ FÄLLIG Rot, <14 Tage Orange, sonst Grün)
    - **file_size_display:** Formatiert als B/KB/MB/GB
    - **stats_display:** 👁 Views | ⬇ Downloads
    - Inlines: DocumentVersionInline, DocumentReviewInline, DocumentAccessInline (Read-Only, max 10)
    - Bulk Actions: mark_as_active, mark_as_archived, mark_as_expired, reset_statistics
  - **DocumentVersionAdmin**
    - **change_type_badge:** 4 Änderungstyp-Farben (Major Rot, Minor Orange, Patch Blau, Revision Grün)
    - **file_size_display:** Formatierte Dateigröße
  - **DocumentAccessAdmin** (Read-Only)
    - **access_type_badge:** 5 Zugriffstyp-Farben (View Blau, Download Grün, Edit Orange, Delete Rot, Share Lila)
    - Keine Add/Change/Delete-Rechte
  - **DocumentReviewAdmin**
    - **status_badge:** 4 Prüfstatus-Farben (Ausstehend Orange, Freigegeben Grün, Abgelehnt Rot, Überarbeitung Blau)
    - **deadline_display:** Frist mit ⚠ Warnung bei Überschreitung
    - Bulk Actions: approve_reviews, reject_reviews

- **URL Configuration:**
  - `/documents/` - Hauptseite (Placeholder)
  - Integration in flvs_project/urls.py

- **Migrations:**
  - `0001_initial.py` - 5 Modelle, 17 Indizes
    - DocumentCategory-Indizes: parent+name, is_active, tree_id+lft (MPTT)
    - Document-Indizes: document_number, category+created_at, status+created_at, document_type, valid_until, review_date, related_content_type+related_object_id, access_level
    - DocumentVersion-Indizes: document+created_at, change_type
    - DocumentReview-Indizes: document+review_status, reviewer+review_status, deadline
    - DocumentAccess-Indizes: document+created_at, user+created_at, access_type+created_at

#### 📝 Notizen
- **MPTT-Hierarchie:** Kategorien beliebig verschachtelt (z.B. Fahrzeuge > Prüfberichte > UVV-Prüfungen)
- **Generic FK:** Dokumente können an beliebige Objekte gehängt werden (Fahrzeuge, Personal, Equipment, etc.)
- **Auto-Expiry:** Status wird automatisch auf EXPIRED gesetzt wenn valid_until < heute
- **Versionierung:** Vollständige Historie aller Dokumentversionen mit Änderungstyp
- **Audit-Trail:** Alle Zugriffe (View, Download, Edit, Delete, Share) werden protokolliert
- **Zugriffskontrolle:** 5 Sicherheitsstufen + M2M-Berechtigung für eingeschränkten Zugriff
- **Phase 6 abgeschlossen:** Alle Prozess-Apps (Vehicle Handover, Procurement, Inventory Check, Documents) implementiert

---

### 2025-10-03 - Inventory Check App vollständig implementiert (Inventur mit Soll-Ist-Vergleich & Korrektur-Buchungen)

#### ✅ Hinzugefügt
- **Inventory Check Models (667 Zeilen, 4 Modelle):**
  - `InventoryCheckType` - 4 Inventur-Typen (FULL, SAMPLE, CYCLE, AD_HOC)
  - `InventoryCheckStatus` - 6 Status (PLANNED, IN_PROGRESS, PAUSED, COMPLETED, CANCELLED, VERIFIED)
  - `DiscrepancyType` - 6 Diskrepanz-Typen (SHORTAGE, SURPLUS, DAMAGED, EXPIRED, WRONG_LOCATION, UNIDENTIFIED)
  - `DiscrepancySeverity` - 4 Schweregrad-Stufen (MINOR, MODERATE, MAJOR, CRITICAL)
  - `ItemCondition` - 7 Zustands-Bewertungen (NEW, EXCELLENT, GOOD, FAIR, WORN, DAMAGED, DEFECTIVE)
  - `AdjustmentType` - 4 Anpassungs-Typen (CORRECTION, WRITE_OFF, TRANSFER, OTHER)
  - **InventoryCheck** - Hauptmodell für Inventur-Durchführung
    - **Auto-Generierung:** check_number (INV-2025-0001 Format)
    - **Planung:** scheduled_start_date, scheduled_end_date, responsible_person, assigned_team (M2M)
    - **Durchführung:** actual_start_date, actual_end_date, status
    - **Tracking:** total_items, counted_items, items_with_discrepancies
    - **Ort & Typ:** location, check_type, inventory_category
    - **Fortschritts-Methoden:** get_progress_percentage(), get_discrepancy_percentage(), update_progress()
    - **Validierung:** Prüft ob scheduled_end_date >= scheduled_start_date
  - **InventoryCheckItem** - Einzelne gezählte Items mit Soll-Ist-Vergleich
    - **Soll-Ist:** expected_quantity, actual_quantity, variance_quantity (auto-berechnet)
    - **Status:** is_counted, has_discrepancy (auto-gesetzt bei Abweichung)
    - **Details:** item_name, item_number, location, condition
    - **Dokumentation:** serial_number, batch_number, counted_by, counted_at
    - **Auto-Berechnungen:** variance_quantity & has_discrepancy im save(), ruft update_progress() auf
  - **InventoryDiscrepancy** - Detaillierte Diskrepanz-Dokumentation
    - **Diskrepanz:** discrepancy_type, severity, quantity_discrepancy
    - **Wert:** estimated_value (Finanzieller Impact)
    - **Dokumentation:** found_by, found_date, description, photo
    - **Korrektur:** corrective_action, correction_applied, corrected_at
  - **InventoryAdjustment** - Korrektur-Buchungen nach Inventur
    - **Auto-Generierung:** adjustment_number (ADJ-2025-0001 Format)
    - **Referenz:** inventory_check (FK), check_item (FK), discrepancy (FK, optional)
    - **Buchung:** adjustment_date, adjustment_type, quantity_adjustment
    - **Genehmigung:** approved, approved_by, approved_at
    - **Anwendung:** applied, applied_at
    - **Wiederholung:** recount_required, recount_completed_at
    - **Auto-Generierung:** adjustment_number im save()

- **Inventory Check Admin (740 Zeilen, 4 Admin-Klassen):**
  - **InventoryCheckAdmin** (Haupt-Admin mit InventoryCheckItemInline)
    - **progress_bar:** Fortschrittsbalken 0-100% (Rot <50%, Orange 50-99%, Grün 100%)
      - Anzeige: "45/100 (45%)" mit farbiger Balken-Visualisierung
    - **status_badge:** 6 farbige Status-Badges (Geplant Blau, Laufend Grün, Pausiert Orange, etc.)
    - **type_badge:** 4 Typ-Badges (Vollständig Blau, Stichprobe Grün, Zyklisch Orange, Ad-hoc Rot)
    - **discrepancy_rate:** Abweichungsquote als farbiger Badge (0% Grün, <10% Orange, ≥10% Rot)
    - **overdue_badge:** ⚠ ÜBERFÄLLIG (Rot) wenn Inventur über scheduled_end_date hinaus läuft
    - Bulk Actions: mark_as_in_progress, mark_as_completed, mark_as_verified, mark_as_cancelled
  - **InventoryCheckItemAdmin**
    - **variance_display:** Varianz mit Farbcodierung
      - Grün für Überbestand (+X), Rot für Fehlbestand (-X), Grau für Übereinstimmung (0)
    - **discrepancy_badge:** ⚠ Ja (Rot) / ✓ Nein (Grün)
    - **counted_badge:** ✓ Gezählt (Grün) / ⧖ Ausstehend (Orange)
    - **condition_badge:** 7 Zustand-Farben (Neuwertig Grün, Defekt Rot)
    - Bulk Actions: mark_as_counted, mark_as_having_discrepancy
  - **InventoryDiscrepancyAdmin**
    - **type_badge:** 6 Diskrepanz-Typ-Farben (Fehlbestand Rot, Überbestand Grün, Beschädigt Orange, etc.)
    - **severity_badge:** 4 Schweregrad-Farben (Geringfügig Grau, Kritisch Rot)
    - **value_display:** Formatierter Wert (1.234,56 €)
    - **correction_badge:** ✓ Korrigiert (Grün) / ⧖ Ausstehend (Orange)
    - Bulk Actions: mark_as_corrected
  - **InventoryAdjustmentAdmin**
    - **type_badge:** 4 Anpassungs-Typ-Farben (Korrektur Blau, Abschreibung Rot, Umbuchung Grün)
    - **approval_badge:** ✓ Genehmigt (Grün) / ⧖ Ausstehend (Orange)
    - **applied_badge:** ✓ Angewendet (Grün) / ⧖ Ausstehend (Orange)
    - **recount_badge:** ⚠ Nachzählung erforderlich (Orange) / ✓ Nachgezählt (Grün)
    - Bulk Actions: approve_adjustments, apply_adjustments, mark_as_recounted

- **URL Configuration:**
  - `/inventory_check/` - Hauptseite (Placeholder)
  - Integration in flvs_project/urls.py

- **Migrations:**
  - `0001_initial.py` - 4 Modelle, 17 Indizes
    - InventoryCheck-Indizes: check_number, status, scheduled_start_date, responsible_person+scheduled_start_date, location
    - InventoryCheckItem-Indizes: inventory_check+is_counted, inventory_check+has_discrepancy, location, counted_by
    - InventoryDiscrepancy-Indizes: check_item, discrepancy_type, correction_applied, found_by+found_date
    - InventoryAdjustment-Indizes: adjustment_number, inventory_check+adjustment_date, applied, approved_by

#### 📝 Notizen
- **Soll-Ist-Vergleich:** Automatische variance_quantity-Berechnung bei Zählung (actual_quantity - expected_quantity)
- **Fortschritts-Tracking:** Echtzeit-Update von total_items, counted_items, items_with_discrepancies
- **Abweichungsrate:** Diskrepanzquote = (items_with_discrepancies / counted_items) × 100%
- **Korrektur-Workflow:** InventoryAdjustment mit Genehmigung → Anwendung → optional Nachzählung
- **Wiederholungszählungen:** recount_required-Flag für kritische Abweichungen
- **Phase 6.3 abgeschlossen:** Inventur-System voll funktionsfähig

---

### 2025-10-03 - Procurement App vollständig implementiert (Bestellwesen mit Approval-Workflow & Wareneingang)

#### ✅ Hinzugefügt
- **Procurement Models (772 Zeilen, 5 Modelle):**
  - `OrderPriority` - 4 Prioritäts-Stufen (LOW, NORMAL, HIGH, URGENT)
  - `OrderStatus` - 10 Status (DRAFT, SUBMITTED, PENDING_APPROVAL, APPROVED, REJECTED, ORDERED, PARTIALLY_RECEIVED, RECEIVED, CANCELLED, CLOSED)
  - `ApprovalStatus` - 4 Freigabe-Status (PENDING, APPROVED, REJECTED, EXPIRED)
  - `DeliveryStatus` - 5 Lieferstatus (NOT_SHIPPED, SHIPPED, IN_TRANSIT, DELIVERED, DELAYED)
  - **PurchaseOrder** - Hauptmodell für Bestellungen mit Approval-Workflow
    - **Auto-Generierung:** order_number (PO-2025-0001 Format)
    - **Lieferant & Lieferung:** supplier, delivery_location, delivery_status, expected/actual_delivery_date, tracking_number
    - **Anforderung:** requested_by, requested_date, approved_by, approved_date, ordered_date
    - **Kosten:** subtotal, tax_rate, tax_amount, shipping_cost, total_cost (auto-berechnet)
    - **Dokumente:** invoice_file, order_confirmation_file, invoice_number/date
    - **Helper-Methoden:** calculate_totals(), get_approval_progress(), is_fully_approved(), get_received_percentage()
  - **OrderItem** - Bestellpositionen mit Generic FK zu Inventory-Items
    - **Generic FK:** inventory_content_type + inventory_object_id (für alle Inventory-Typen)
    - **Menge & Preis:** quantity, unit, unit_price, quantity_received (auto-update)
    - **Ziel:** category, target_location, supplier_item_number
    - **Helper-Methoden:** get_total_price(), is_fully_received(), get_received_percentage()
  - **OrderApproval** - Mehrstufiger Freigabe-Workflow
    - **Stufen:** approval_level (1, 2, 3, ...), approver, deadline
    - **Status-Tracking:** requested_date, decision_date, comment
    - **Helper:** is_overdue() - Prüft Frist-Überschreitung
    - **Unique Constraint:** (purchase_order, approval_level)
  - **GoodsReceipt** - Wareneingang mit Qualitätsprüfung
    - **Auto-Generierung:** receipt_number (GR-2025-0001 Format)
    - **Empfang:** receipt_date, received_by, delivery_note_number, carrier
    - **Qualität:** quality_check_passed, quality_check_notes
    - **Abweichungen:** has_discrepancies, discrepancy_notes
    - **Dokumente:** delivery_note_file, photos (JSONField)
  - **GoodsReceiptItem** - Wareneingangs-Positionen
    - **Empfang:** quantity_received, location, condition (good/acceptable/damaged/defective)
    - **Chargen:** batch_number, expiry_date
    - **Auto-Update:** Aktualisiert order_item.quantity_received im save()

- **Procurement Admin (719 Zeilen, 5 Admin-Klassen):**
  - **PurchaseOrderAdmin** (Haupt-Admin mit 2 Inlines)
    - **status_badge:** 10 farbige Status-Badges (Entwurf Grau, Eingereicht Blau, Freigabe Orange, Freigegeben Grün, etc.)
    - **priority_badge:** 4 Prioritäts-Farben (Niedrig Grau, Normal Blau, Hoch Orange, Dringend Rot)
    - **approval_progress:** Freigabe-Fortschritt als % (✓ 100% Grün, X% Orange, 0% Grau)
    - **delivery_progress:** Lieferfortschritt als %
    - **approval_progress_bar:** Fortschrittsbalken 0-100% für Freigaben (Rot <50%, Orange 50-99%, Grün 100%)
    - **delivery_progress_bar:** Fortschrittsbalken für Lieferungen
    - **total_cost_display:** Formatierte Gesamtkosten (1.234,56 €)
    - Inlines: OrderItemInline, OrderApprovalInline
    - Bulk Actions: mark_as_approved, mark_as_ordered, mark_as_received, mark_as_cancelled
  - **OrderItemAdmin**
    - **quantity_display:** Menge mit Einheit (z.B. "100 Stück")
    - **total_price_display:** Gesamtpreis der Position (Menge × Einzelpreis)
    - **received_progress:** Lieferfortschritt (✓ 100/100 Stück Grün, 50/100 Stück (50%) Orange)
  - **OrderApprovalAdmin**
    - **status_badge:** 4 Freigabe-Status-Farben (Ausstehend Orange, Freigegeben Grün, Abgelehnt Rot)
    - **deadline_display:** Frist mit Überfällig-Warnung (⚠ Datum Rot wenn überfällig)
    - Bulk Actions: approve_requests, reject_requests
  - **GoodsReceiptAdmin** (mit GoodsReceiptItemInline)
    - **quality_check_badge:** ✓ Bestanden (Grün) / ✗ Nicht bestanden (Rot)
    - **discrepancies_badge:** ⚠ Ja (Rot) / ✓ Keine (Grün)
  - **GoodsReceiptItemAdmin**
    - **condition_badge:** 4 Zustand-Farben (Gut Grün, Akzeptabel Orange, Beschädigt Rot, Defekt Dunkelrot)

- **URL Configuration:**
  - `/procurement/` - Hauptseite (Placeholder)
  - Integration in flvs_project/urls.py

- **Migrations:**
  - `0001_initial.py` - 5 Modelle, 13 Indizes
    - PurchaseOrder-Indizes: order_number, status, requested_date, supplier+requested_date, requested_by+requested_date, priority+status
    - OrderApproval-Indizes: purchase_order+approval_level, approver+status, status+deadline
    - GoodsReceipt-Indizes: receipt_number, purchase_order+receipt_date, received_by+receipt_date

#### 📝 Notizen
- **Approval-Workflow:** Unterstützt mehrstufige Freigaben (z.B. Teamleiter → Abteilungsleiter → Geschäftsführer)
- **Generic FK:** OrderItem kann auf alle Inventory-Typen verweisen (MagazineItem, MedicalItem, etc.) für Nachbestellungen
- **Auto-Berechnungen:** Kosten (Subtotal, Tax, Total) und Lieferfortschritt werden automatisch berechnet
- **Phase 6.2 abgeschlossen:** Bestellwesen voll funktionsfähig

---

### 2025-10-03 - Vehicle Handover App vollständig implementiert (Fahrzeugübernahme mit 360°-Fotos & Mängeldokumentation)

#### ✅ Hinzugefügt
- **Vehicle Handover Models (537 Zeilen, 4 Modelle):**
  - `HandoverType` - 8 Übergabe-Arten
    - shift_change: Wachablösung
    - deployment_start/end: Einsatzbeginn/ende
    - maintenance_in/out: Werkstatteingang/ausgang
    - rental/return: Ausleihe/Rückgabe
    - inspection: Kontrolle/Inspektion
  - `HandoverStatus` - 4 Status (In Bearbeitung, Abgeschlossen, Mit Mängeln abgeschlossen, Abgebrochen)
  - `DefectSeverity` - 5 Schweregrad-Stufen
    - info: Information (kein Mangel)
    - minor: Geringer Mangel (einsatzbereit)
    - moderate: Mittlerer Mangel (eingeschränkt einsatzbereit)
    - major: Erheblicher Mangel (nicht einsatzbereit)
    - critical: Kritischer Mangel (Verkehrssicherheit gefährdet)
  - **VehicleHandover** - Hauptmodell für Fahrzeugübergabe
    - **Personen:** handover_from (nullable), handover_to, location
    - **Fahrzeugzustand:** odometer_reading, fuel_level (%), cleanliness_interior/exterior (1-5)
    - **Vollständigkeit:** completeness_check_done, all_items_present
    - **Mängel:** has_defects, defects_count (auto-berechnet)
    - **Bestätigung:** confirmed_by_giver, confirmed_by_receiver (digitale Unterschriften)
    - **Helper-Methoden:** get_checklist_completion(), get_photo_count(), is_complete()
    - **Auto-Status:** Setzt automatisch status='defects_noted' bei has_defects=True
  - **HandoverChecklist** - Flexible Checklisten je Fahrzeugtyp
    - **Prüfstatus:** checked (geprüft), present (vorhanden), functional (funktionsfähig)
    - **Kategorisierung:** category (z.B. "Fahrzeugpapiere", "Beladung", "Sicherheitsausrüstung")
    - **Sortierung:** order (Reihenfolge), serial_number (optional)
  - **HandoverPhoto** - 360°-Foto-Dokumentation & Schadensfotos
    - **15 Foto-Typen:**
      - 360°: front, front_right, right, rear_right, rear, rear_left, left, front_left
      - Innenraum: interior_front, interior_rear, cargo_area, dashboard
      - Sonstige: defect, equipment, other
    - **GPS-Daten:** gps_latitude, gps_longitude (optional)
    - **Verknüpfung:** related_defect (FK zu HandoverDefect)
    - **Upload:** image (ImageField), upload_to='vehicle_handovers/%Y/%m/%d/'
  - **HandoverDefect** - Mängel-Dokumentation mit Reparatur-Tracking
    - **11 Mangel-Kategorien:** Karosserie, Verglasung, Beleuchtung, Reifen, Innenraum, Ausrüstung, Motor, Bremsen, Elektronik, Reinigung, Sonstiges
    - **Auswirkungen:** requires_immediate_action, affects_operational_readiness
    - **Reparatur:** repaired (Boolean), repair_date, repaired_by, repair_notes
    - **Kosten:** estimated_repair_cost, actual_repair_cost
    - **Automatik im save():** Setzt handover.has_defects=True bei neuem Mangel
    - **TODO-Feld:** workshop_order (FK zu workshop.WorkshopOrder) - auskommentiert bis WorkshopOrder existiert

- **Vehicle Handover Admin (681 Zeilen, 4 Admin-Klassen):**
  - **VehicleHandoverAdmin** (Haupt-Admin mit 3 Inlines)
    - **handover_type_badge:** 8 farbige Badges (Wachablösung Blau, Einsatz Grün, Werkstatt Rot, etc.)
    - **status_badge:** 4 Status-Farben (In Bearbeitung Orange, Abgeschlossen Grün, Mit Mängeln Rot)
    - **odometer_reading_display:** Formatiert als "123,456 km"
    - **fuel_level_display:** Farbcodiert (>75% Grün, >50% Orange, >25% Rot, <25% Dunkelrot)
    - **defects_badge:** ✓ Keine / ⚠ X Mangel/Mängel (Rot)
    - **checklist_progress:** Fortschrittsbalken 0-100% (Rot <50%, Orange 50-99%, Grün 100%)
    - **photo_count_display:** 📷 X Foto(s) (Blau) / 0 Fotos (Grau)
    - **completeness_badge:** ✓ Vollständig (Grün) / ⚠ Unvollständig (Orange)
    - **completeness_status:** Detaillierte Checkliste (Vollständigkeitsprüfung, Bestätigungen, Checklisten-%)
    - Inlines: HandoverChecklistInline, HandoverPhotoInline, HandoverDefectInline
    - Bulk Actions: mark_as_completed, mark_as_defects_noted, mark_as_cancelled
    - **get_queryset:** Optimiert mit select_related + prefetch_related + annotate (Checklist-Items, Photos)
  - **HandoverChecklistAdmin**
    - **status_icon:** ✓ Geprüft (Grün) / ○ Nicht geprüft (Grau)
    - **present_icon:** ✓ Vorhanden (Grün) / ✗ Fehlt (Rot)
    - **functional_icon:** ✓ Funktionsfähig (Grün) / ✗ Defekt (Rot)
    - **list_editable:** order (Reihenfolge direkt bearbeitbar)
  - **HandoverPhotoAdmin**
    - **image_thumbnail:** 60x60px Vorschau-Bild (list_display)
    - **image_preview:** Große Vorschau (max 600x600px) in Detailansicht
    - **photo_type_badge:** Farbcodierung (360° Blau, Innenraum Lila, Defekt Rot)
    - **has_gps:** Boolean-Icon für GPS-Koordinaten
    - **list_editable:** order (Reihenfolge)
  - **HandoverDefectAdmin**
    - **severity_badge:** 5 Schweregrad-Farben (Info Blau, Gering Grün, Mittel Orange, Erheblich Rot, Kritisch Dunkelrot)
    - **category_badge:** Kategorie-Badge (Grau)
    - **operational_readiness_icon:** Boolean-Icon (✓ Einsatzbereit / ✗ Nicht einsatzbereit)
    - **repair_status_badge:** ✓ Behoben (Grün) / ⚠ SOFORT! (Dunkelrot bei requires_immediate_action) / ✗ Offen (Orange)
    - **cost_display:** Tatsächliche Kosten (Fett) / ~Geschätzte Kosten (Grau) / - (Keine Angabe)
    - Bulk Actions: mark_as_repaired, mark_as_critical

- **URL Configuration:**
  - `/vehicle_handover/` - Hauptseite (Placeholder)
  - Integration in flvs_project/urls.py

- **Migrations:**
  - `0001_initial.py` - 4 Modelle, 14 Indizes
    - Indizes: handover_date, vehicle+handover_date, handover_to+handover_date, status, handover_type
    - Photo-Indizes: handover+order, photo_type
    - Defect-Indizes: handover, severity, repaired, affects_operational_readiness
    - Checklist-Indizes: handover+order, category

#### 📝 Notizen
- **workshop_order Feld temporär auskommentiert:** FK zu `workshop.WorkshopOrder` existiert noch nicht. Wird aktiviert sobald WorkshopOrder-Model in Workshop-App implementiert ist.
- **Phase 6 gestartet:** Erste App der Prozess-Phase (Fahrzeugübernahme, Bestellwesen, Inventur, Dokumente)

---

### 2025-10-03 - IT Hardware App vollständig implementiert (IT-Asset-Management mit Abschreibung & Lizenz-Tracking)

#### ✅ Hinzugefügt
- **IT Hardware Models (550 Zeilen, 2 Modelle):**
  - `ITHardwareType` - 43 Hardware-Typen
    - Computer: Desktop-PC, Laptop, Tablet, Thin Client, All-in-One
    - Server & Netzwerk: Server, NAS, Router, Switch, Firewall, Access Point, Modem
    - Peripherie: Monitor, Tastatur, Maus, Drucker, Scanner, Multifunktion, Webcam, Headset, Lautsprecher
    - Mobilgeräte: Smartphone, Mobiltelefon, Funkgerät, GPS-Gerät
    - Speicher & Komponenten: Externe HDD, USB-Stick, SSD, HDD, RAM, CPU, GPU, Netzteil, Mainboard
    - Zubehör: Kabel, Adapter, Dockingstation, USV, KVM-Switch, Rack
    - Software: Softwarelizenz
  - `ITStatus` - 7 Status (In Betrieb, Auf Lager, Reserviert, Defekt, In Reparatur, Ausgemustert, Bestellt)
  - `OperatingSystem` - 10 Betriebssysteme (Windows 11/10/Server, Linux Ubuntu/Debian/CentOS, macOS, Android, iOS)
  - **ITHardwareItem** - IT-Hardware mit Asset-Tracking & Lebenszyklus
    - **Asset-Tracking:** asset_tag (unique), serial_number, mac_address, ip_address, hostname
    - **Technische Specs:** operating_system, os_version, cpu_model, ram_gb, storage_gb, gpu_model, screen_size_inch
    - **Benutzer-Zuordnung:** assigned_to, assignment_date
    - **Garantie & Support:** purchase_date, purchase_price, warranty_end_date, support_contract, support_end_date
    - **Lebenszyklus:** depreciation_years (Standard 5), expected_replacement_date, get_current_value()
    - **Wartung & Updates:** last_maintenance_date, next_maintenance_date, last_os_update, antivirus_software, antivirus_last_update
    - **Lizenzen:** license_key, license_seats, license_expiry_date
    - **Helper-Methoden:** is_warranty_valid(), is_warranty_expiring_soon(), is_support_valid(), get_age_years(), get_current_value()
  - **ITHardwareStockMovement** - Lagerbewegung mit Benutzer-Zuordnung & Updates
    - **Zuweisung:** assigned_to, assignment_reason (Neueinstellung/Ersatz/Upgrade)
    - **Wartung:** maintenance_performed, maintenance_type, maintenance_notes, parts_replaced, maintenance_cost
    - **Software-Updates:** os_updated, new_os_version, software_installed
    - **Automatik im save():** Benutzer-Zuweisung Update, Wartungsdatum Update, OS-Version Update

- **IT Hardware Admin (320 Zeilen, 2 Admin-Klassen):**
  - **ITHardwareItemAdmin**
    - **it_status_badge:** 7 farbige Status (In Betrieb Grün, Auf Lager Blau, Defekt Rot, etc.)
    - **warranty_badge:** ✓ Gültig / ⚠ Läuft bald ab / ✗ Abgelaufen
    - **support_badge:** ✓ Gültig / ✗ Abgelaufen / Kein Vertrag
    - **current_value_display:** Aktueller Wert nach linearer Abschreibung
    - **age_display:** Alter in Jahren
    - Bulk Actions: mark_in_use, mark_in_stock, mark_defect, mark_retired
  - **ITHardwareStockMovementAdmin**
    - **assigned_to_badge:** 👤 Benutzer
    - **maintenance_badge:** 🔧 Wartungsart (Kosten)
    - **os_update_badge:** ⬆ OS-Version

- **Integration:**
  - URLs: path('it_hardware/', include('it_hardware.urls'))
  - settings/base.py: it_hardware.apps.ItHardwareConfig in LOCAL_APPS
  - Migrations: 0001_initial.py mit 10 Indizes

#### 🎯 Hauptfeatures
- **Asset-Tracking** - Eindeutige Asset-Tags, Seriennummern, MAC/IP-Adressen
- **Garantie & Support-Tracking** - Automatische Warnung bei Ablauf (30 Tage Vorwarnung)
- **Abschreibungsberechnung** - Linearer Wertverlust über 5 Jahre (konfigurierbar)
- **Benutzer-Zuordnung** - Tracking wer welche Hardware nutzt
- **Lizenz-Management** - Lizenzschlüssel, Anzahl Seats, Ablaufdaten
- **OS & Software-Tracking** - Betriebssystem-Versionen, Update-Historie, Antivirus-Status
- **Netzwerk-Informationen** - Hostname, IP, MAC für IT-Asset-Inventar

#### 🎉 Phase 5 ABGESCHLOSSEN
Alle 7 Lager-Module vollständig implementiert:
1. ✅ Clothing App (Kleiderkammer)
2. ✅ Equipment App (Ausrüstung & Geräte)
3. ✅ Workshop App (KFZ-Werkstatt)
4. ✅ Disinfection App (Desinfektion)
5. ✅ Height Rescue App (Höhenrettung)
6. ✅ Diving App (Taucher)
7. ✅ IT Hardware App (IT-Hardware)

---

### 2025-10-03 - Diving App vollständig implementiert (Tauch-Management mit TÜV & Gasverwaltung)

#### ✅ Hinzugefügt
- **Diving Models (674 Zeilen, 3 Modelle):**
  - `DivingItemType` - 29 Ausrüstungstypen
    - Atemausrüstung: Tauchflasche, Atemregler, Oktopus, Tarierjacket (BCD)
    - Schutzausrüstung: Nass-/Trockenanzug, Maske, Schnorchel, Flossen, Schuhe, Handschuhe, Haube
    - Instrumente: Tauchcomputer, Tiefenmesser, Kompass, Finimeter
    - Sicherheit: Tauchmesser, Tauchlampe, Signalboje (SMB), Signalpfeife, Sicherheitsleine
    - Gewichte: Bleigurt, Bleigewichte, Netztasche
    - Kompressor: Tauchkompressor, Füllstation, Wartungskit
  - `TankType` - 3 Flaschentypen (Stahl, Aluminium, Komposit)
  - `GasType` - 6 Atemgase (Pressluft, Nitrox 32/36, Trimix, Heliox, O2)
  - `InspectionStatus` - 6 TÜV-Status (Nicht fällig, Demnächst, Überfällig, Bestanden, Nicht bestanden, Ausgemustert)
  - **DivingItem** - Tauchausrüstung mit TÜV & Gasverwaltung
    - **Flaschen-Spezifikationen:** tank_type, volume_liters, working_pressure_bar, test_pressure_bar, current_gas_type
    - **TÜV-Prüfung (2.5 Jahre):** manufacturing_date, last_tuv_inspection, next_tuv_inspection, tuv_certificate_number, inspection_status
    - **Regelmäßige Wartung:** last_service_date, next_service_date, service_interval_months (Standard 12), last_service_technician
    - **Technische Daten:** max_depth_m, weight_kg, size, material
    - **Nutzungshistorie:** total_dives, total_hours, last_use_date
    - **Dokumentation:** service_manual, tuv_certificate, service_log, photos
    - **Helper-Methoden:** is_tuv_due(), is_tuv_due_soon(), is_service_due(), is_service_due_soon(), is_condemned(), get_age_years()
  - **DivingStockMovement** - Lagerbewegung mit Gasfüllung & Tauchgangsdokumentation
    - **Gasfüllung:** gas_filled, gas_type, fill_pressure_bar, oxygen_percentage (21-100%)
    - **Tauchgang:** dive_date, dive_location, max_depth_m, dive_duration_minutes, dive_purpose
    - **Service:** service_performed, service_type, service_technician, service_notes, parts_replaced
    - **Automatik im save():** Gas-Typ Update, Service-Datum Update, Tauchgangs-Statistik Update (total_dives, total_hours)
  - **DivingServiceLog** - Wartungsprotokoll mit Kostenerfassung
    - **Service:** service_date, service_type (Jahresservice/TÜV/Reparatur/Prüfung/Reinigung), technician, passed
    - **Prüfwerte (Atemregler):** cracking_pressure_mbar (18-25), flow_rate_l_min, leak_test_passed
    - **Kosten:** labor_cost, parts_cost, total_cost()
    - **Dokumentation:** service_report (PDF), photos, next_service_due

- **Diving Admin (428 Zeilen, 3 Admin-Klassen):**
  - **DivingItemAdmin**
    - **current_gas_badge:** Farbige Gas-Badges (Luft Blau, Nitrox Grün, Trimix Lila, Heliox Orange, O2 Rot)
    - **tuv_status_badge:** ✓ Bestanden / ✗ Nicht bestanden / ⚠️ Überfällig / 🚫 Ausgemustert (nur für Flaschen)
    - **service_status_badge:** ⚠️ Überfällig / Demnächst fällig / ✓ OK
    - **age_display:** Alter in Jahren
    - Bulk Actions: mark_tuv_overdue, mark_service_due, mark_condemned
  - **DivingStockMovementAdmin**
    - **gas_filled_badge:** ✓ Nitrox 32 (200 bar)
    - **dive_badge:** 🤿 25m / 45min
    - **service_badge:** 🔧 Jahresservice
  - **DivingServiceLogAdmin**
    - **passed_badge:** ✓ Bestanden / ✗ Nicht bestanden
    - **cost_display:** Gesamtkosten (Arbeit + Material)

- **Integration:**
  - URLs: path('diving/', include('diving.urls'))
  - settings/base.py: diving.apps.DivingConfig in LOCAL_APPS
  - Migrations: 0001_initial.py mit 13 Indizes

#### 🎯 Hauptfeatures
- **TÜV-Prüfung für Tauchflaschen** - Alle 2.5 Jahre mit Status-Tracking
- **6 Atemgastypen** - Pressluft, Nitrox 32/36, Trimix, Heliox, reiner Sauerstoff
- **Gasfüll-Tracking** - Gas-Typ, Druck, Sauerstoffanteil
- **Jährliche Wartung** - Atemregler & BCD mit Prüfwerten (Ansprechdruck 18-25 mbar)
- **Tauchgangs-Statistik** - Automatische Zählung (total_dives, total_hours)
- **Kostenerfassung** - Arbeits- und Materialkosten bei Service

---

### 2025-10-03 - Height Rescue App vollständig implementiert (Höhenrettungs-Management mit DGUV-konformer Prüfung)

#### ✅ Hinzugefügt
- **Height Rescue Models (579 Zeilen, 3 Modelle):**
  - `HeightRescueItemType` - 20 Ausrüstungstypen
    - Seile & Schlingen: Seil, Bandschlinge, Sicherheitsleine
    - Gurte: Auffanggurt, Brustgurt, Sitzgurt
    - Verbindungselemente: Karabiner, Seilrolle, Steigklemme
    - Sicherungsgeräte: Abseilgerät, Sicherungsgerät, Falldämpfer, Höhensicherungsgerät
    - Spezialausrüstung: Rettungsgerät, Dreibein, Rettungstrage
    - Zubehör: Kantenschutz, Kantenrolle, Anschlagpunkt, Positionierungsmittel, Helm
  - `RopeType` - 5 Seiltypen nach EN 1891 (Typ A Statisch, Typ B Halbstatisch, Dynamisch, Kernmantel, Stahlseil)
  - `CertificationStandard` - 22 EN-Normen + GS/CE/DGUV
    - PSAgA-Normen: EN 361 (Gurte), EN 362 (Verbindungselemente), EN 363 (Auffangsysteme)
    - Seile: EN 892 (Dynamisch), EN 1891 (Statisch), EN 12275 (Karabiner), EN 12278 (Rollen)
    - Spezial: EN 341 (Abseilgeräte), EN 353 (Auffanggerät), EN 355 (Falldämpfer), EN 360 (Höhensicherung)
  - `InspectionStatus` - 6 Prüfstatus (Nicht fällig, Demnächst fällig, Überfällig, Bestanden, Nicht bestanden, Ausgemustert)
  - **HeightRescueItem** - Höhenrettungsausrüstung mit EN-Zertifizierung
    - **Zertifizierung:** certifications (JSONField), certification_number
    - **Belastungsdaten:** max_load_kg, breaking_strength_kn, working_load_limit_kg (WLL)
    - **Seil-Spezifikationen:** rope_type, rope_length_m, rope_diameter_mm
    - **Lebensdauer:** manufacturing_date, max_service_life_years, retirement_date, retirement_reason
    - **DGUV Prüfungen:** last_inspection_date, next_inspection_date, inspection_interval_months (Standard 12), inspection_status, last_inspector
    - **Nutzungshistorie:** **total_falls_arrested** (⚠️ KRITISCH), total_uses, last_use_date
    - **Dokumentation:** inspection_report, manual_file, test_certificate, photos, condition_notes
    - **Fahrzeuge:** assigned_vehicles (M2M)
    - **Helper-Methoden:**
      - is_inspection_due() / is_inspection_due_soon()
      - is_retired() - Prüft Aussonderungsstatus
      - has_certification(standard) - Zertifizierungscheck
      - get_age_years() - Altersberechnung
      - **should_be_retired()** - Automatische Aussonderungsprüfung (nach Sturz oder Alter)
  - **HeightRescueStockMovement** - Lagerbewegung mit Einsatz- & Sturzdokumentation
    - **Einsatz:** mission_date, mission_type (Rettung/Training/etc.)
    - **⚠️ STURZ-KRITISCH:** fall_arrested (Boolean), fall_height_m, fall_description
    - **Prüfung:** inspection_performed, inspection_passed, inspection_notes, inspector
    - **Zustand:** condition_before, condition_after, photos
    - **Automatik im save():**
      - Bei Sturz: Item wird SOFORT ausgemustert (inspection_status=RETIRED, retirement_date gesetzt)
      - Bei Prüfung: next_inspection_date wird automatisch berechnet, inspection_status aktualisiert
  - **HeightRescueInspectionLog** - Vollständige Prüfhistorie (DGUV Vorschrift 3)
    - **Prüfung:** inspection_date, inspection_type (Jährlich/Nach Einsatz/Nach Sturz/Sicht/Detail), inspector, passed
    - **Prüfpunkte:** visual_check, functionality_check, marking_legible, no_damage, no_wear, no_corrosion
    - **Ergebnis:** findings, actions_taken
    - **Dokumentation:** protocol_file (PDF), photos, next_inspection_due

- **Height Rescue Admin (399 Zeilen, 3 Admin-Klassen):**
  - **HeightRescueItemAdmin**
    - **certification_badge:** Farbige EN-Badges (EN 361 grün, EN 1891 blau, EN 362 orange, EN 12275 lila, DGUV rot)
    - **inspection_status_badge:** ✓ Bestanden / ✗ Nicht bestanden / ⚠️ Überfällig / 🚫 Ausgemustert
    - **age_display:** Alterungsanzeige mit Ampel-Farben (Grün/Orange/Rot basierend auf max_service_life_years)
    - **should_retire_display:** ⚠️ JA / ✓ Nein - Aussonderungswarnung
    - Bulk Actions: mark_inspection_overdue, mark_for_retirement, reset_inspection_status
  - **HeightRescueStockMovementAdmin**
    - **fall_arrested_badge:** ⚠️ STURZ (Rot) oder -
    - **inspection_badge:** ✓ Bestanden / ✗ Nicht bestanden
  - **HeightRescueInspectionLogAdmin**
    - **passed_badge:** ✓ Bestanden / ✗ Nicht bestanden
    - Filter für alle Prüfpunkte

- **Integration:**
  - URLs: path('height_rescue/', include('height_rescue.urls'))
  - settings/base.py: height_rescue.apps.HeightRescueConfig in LOCAL_APPS
  - Migrations: 0001_initial.py mit 14 Indizes

#### 🎯 Hauptfeatures
- **DGUV Vorschrift 3 konform** - Mindestens jährliche Prüfung, vollständige Protokollierung
- **EN-Zertifizierungen** - 22 europäische Normen (PSAgA, Seile, Karabiner, etc.)
- **Automatische Aussonderung nach Sturz** - fall_arrested=True löst sofortige Ausm usterung
- **Alterungsberechnung** - Automatische Warnung bei Überschreitung max_service_life_years
- **Belastungsgrenzen** - max_load_kg, breaking_strength_kn, working_load_limit_kg (WLL)
- **Vollständige Prüfhistorie** - HeightRescueInspectionLog mit 6 Prüfpunkten
- **Seilspezifikationen** - Länge, Durchmesser, Typ nach EN 1891

---

### 2025-10-03 - Disinfection App vollständig implementiert (Desinfektions-Management mit Protokollierung)

#### ✅ Hinzugefügt
- **Disinfection Models (562 Zeilen, 3 Modelle):**
  - `DisinfectionItemType` - 27 Typen (Flächen-, Hände-, Instrumenten-, Wäsche-, Fahrzeugdesinfektion, UV/Ozon-Geräte, Schutzausrüstung, Zubehör)
  - `DisinfectionSpectrum` - 7 Wirkungsspektren (Bakterizid, Viruzid, Fungizid, Sporizid, Tuberkulozid, Vollspektrum)
  - `DisinfectionStatus` - 6 Status (In Stock, Low Stock, Out of Stock, On Order, Expired, Quarantine)
  - `ApplicationMethod` - 7 Anwendungsmethoden (Spray, Wipe, Immersion, Nebulization, UV-Light, Ozone)
  - **DisinfectionItem** - Desinfektionsmittel & -geräte
    - Wirkungsspektrum (JSONField Multi-Select), Anwendungsmethode, Einwirkzeit, Verdünnungsverhältnis
    - **Compliance:** VAH/DGHM/RKI-Listung, Zulassungsnummer
    - Gefahrstoff-Management: is_hazardous, GHS-Symbole, Sicherheitsdatenblatt
    - Lagerung: Temperatur, Lichtschutz, Haltbarkeit (normal & geöffnet)
    - Fahrzeug-Zuordnung (M2M), Wirkstoff, Konzentration, Anwendungsbereiche (JSONField)
    - Helper: has_spectrum(), is_full_spectrum()
  - **DisinfectionStockMovement** - Lagerbewegung mit Chargen-Tracking
    - Fahrzeug, performed_by, batch_number, production_date, expiry_date, **opened_date**
    - used_for, disinfection_protocol - Verwendungsdokumentation
  - **DisinfectionLog** - Desinfektions-Protokolle (unabhängig von Lager)
    - object_type, vehicle, object_description - Was wurde desinfiziert
    - disinfection_date, performed_by, **verified_by** - Vier-Augen-Prinzip
    - disinfection_item, stock_movement, dilution_used, contact_time, method
    - protocol, reason, photos (JSONField), notes

- **Disinfection Admin (558 Zeilen, 3 Admin-Klassen):**
  - **DisinfectionItemAdmin**
    - **status_badge**: 6 farbcodierte Status
    - **spectrum_badge**: ✓ Vollspektrum oder Icons (🦠B, 🧬V, 🍄F, ⚪S, 🔬T)
    - **compliance_badge**: VAH/DGHM/RKI-Badges
    - **hazard_badge**: ⚠ GEFAHRSTOFF-Warnung
    - Bulk Actions: mark_as_in_stock, mark_as_low_stock, mark_as_expired
  - **DisinfectionStockMovementAdmin**
    - expiry_badge mit 30-Tage-Vorwarnung
  - **DisinfectionLogAdmin**
    - **verified_badge**: ✓ Verifiziert oder ⚠ Ungeprüft (Vier-Augen-Kontrolle)

- **Integration:**
  - URLs: path('disinfection/', include('disinfection.urls'))
  - Migrations: 0001_initial.py mit 14 Indizes

#### 🎯 Hauptfeatures
- **VAH/DGHM/RKI-Compliance** - Hygiene-Standards-Konformität
- **Wirkungsspektrum-Tracking** - Multi-Select für Bakterizid/Viruzid/Fungizid etc.
- **Anbruch-Tracking** - opened_date für Haltbarkeit nach Öffnung
- **Desinfektions-Protokolle** - Unabhängige Dokumentation mit Vier-Augen-Prinzip
- **Gefahrstoff-Management** - GHS-Symbole & Sicherheitsdatenblätter
- **Chargen-Rückverfolgung** - Batch-Nummer, Produktions- & Verfallsdatum

---

### 2025-10-03 - Workshop App vollständig implementiert (KFZ-Werkstatt mit Fahrzeug-Service-Management)

#### ✅ Hinzugefügt
- **Workshop Models (619 Zeilen, 3 Modelle):**
  - `WorkshopItemType` Choices - 80+ Werkstatt-Artikel-Typen
    - Betriebsstoffe (11 Typen): Motoröl, Getriebeöl, Hydrauliköl, Bremsflüssigkeit, Kühlflüssigkeit, AdBlue
    - Verschleißteile (11 Typen): Ölfilter, Luftfilter, Kraftstofffilter, Bremsbeläge, Bremsscheiben, Zündkerzen, Zahnriemen
    - Reifen & Räder (6 Typen): Sommerreifen, Winterreifen, Ganzjahresreifen, Felgen
    - Beleuchtung (4 Typen): Scheinwerferbirnen, Rücklichtbirnen, Blinkerbirnen, LED-Einheiten
    - Batterie & Elektrik (6 Typen): Batterie, Lichtmaschine, Anlasser, Sicherungen, Relais, Kabel
    - Karosserie & Lack (5 Typen): Lack, Grundierung, Klarlack, Spachtelmasse, Rostschutz
    - Werkzeug (10 Typen): Schraubenschlüssel, Steckschlüssel, Drehmomentschlüssel, Wagenheber, Diagnosegerät
    - Reinigung & Pflege (7 Typen): Autowaschmittel, Autowachs, Bremsenreiniger, Entfetter, Glasreiniger
  - `WorkshopItemStatus` Choices - 7 Status (In Stock, Low Stock, Out of Stock, On Order, Reserved, Expired, Defective)
  - `VehicleServiceType` Choices - 15 Service-Typen (Ölwechsel, Inspektion, HU, AU, Reifenwechsel, Bremsenwartung, Reparatur, Lackierung, etc.)
  - `ServiceStatus` Choices - 6 Service-Status (Scheduled, In Progress, Waiting Parts, Waiting Approval, Completed, Cancelled)
  - `WorkshopItem` Model - Erbt von AbstractInventoryItem
    - **Typ & Status:** workshop_item_type, workshop_status
    - **Fahrzeug-Kompatibilität:** compatible_vehicles (M2M) - Zeigt welche Teile für welche Fahrzeuge passen
    - **Spezifikationen:** manufacturer_part_number, oem_number, viscosity (z.B. 5W-30), specification (z.B. API SN/CF)
    - **Lagerung:** shelf_life_months, production_date, storage_temperature_min/max
    - **Gefahrstoff:** is_hazardous, hazard_symbols (GHS), safety_data_sheet (FileField für SDB)
    - **Wartungsintervalle:** recommended_change_interval_km, recommended_change_interval_months
    - **Kosten & Pfand:** purchase_price, core_charge (Pfandbetrag für Altteilrückgabe)
    - Helper-Methoden: is_expired(), is_low_stock()
  - `WorkshopStockMovement` Model - Erbt von AbstractStockMovement
    - vehicle FK - Fahrzeug für das der Artikel verwendet wurde
    - service_record FK - Verknüpfung zum Fahrzeug-Serviceeintrag
    - vehicle_mileage - Kilometerstand bei Verwendung
    - batch_number, expiry_date - Chargen-Tracking
    - **Pfandrückgabe:** core_returned, core_return_date - Altteil-Management
    - Kosten: unit_cost, total_cost (auto-berechnet)
    - Dokumente: delivery_note
    - **save() überschrieben:** Auto-Berechnung total_cost, Bestandsaktualisierung
  - `VehicleServiceRecord` Model - **Fahrzeug-Service-Dokumentation**
    - vehicle FK, service_type, service_status
    - **Zeitplanung:** scheduled_date, started_date, completed_date
    - **Fahrzeugdaten:** mileage_at_service, operating_hours_at_service
    - **Durchführung:** description (TextField), technician (FK Person), labor_hours
    - **Kosten:** labor_cost, parts_cost (auto-berechnet), external_cost, total_cost (auto-berechnet)
    - **Freigabe:** approved_by (FK User), approval_date
    - **Dokumentation:** invoice_number, invoice_file (FileField), photos (JSONField), notes
    - **Audit:** created_by, created_at, updated_at
    - **save() überschrieben:** Auto-Berechnung total_cost = labor_cost + parts_cost + external_cost
    - Helper-Methoden: calculate_parts_cost() (aggregiert aus used_items), is_overdue()

- **Workshop Admin-Interface (636 Zeilen, 3 Admin-Klassen) mit Service-Management:**
  - WorkshopItemAdmin - Werkstatt-Artikel-Verwaltung
    - **workshop_status_badge:** 7 farbcodierte Status (In Stock=Grün, Low Stock=Amber, Out of Stock=Rot, On Order=Blau, Reserved=Lila, Expired=Grau, Defective=Dunkelrot)
    - **hazard_badge:** ⚠ GEFAHRSTOFF Warnung (Rot) für is_hazardous=True
    - **expiry_badge:** Ablaufdatum mit 30-Tage-Vorwarnung (Rot=Abgelaufen, Amber=<30 Tage, Grün=OK)
    - **stock_badge:** ⚠ Niedrig für low_stock
    - Fahrzeug-Kompatibilität als filter_horizontal widget
    - **Bulk-Actions:** mark_as_in_stock, mark_as_low_stock, mark_as_out_of_stock, mark_as_on_order
  - WorkshopStockMovementAdmin - Lagerbewegungen
    - **movement_type_badge:** Farbcodiert (Incoming=Grün, Outgoing=Amber, Return=Blau, Correction=Lila, Disposal=Rot)
    - **vehicle_badge:** Zeigt zugeordnetes Fahrzeug
    - **service_record_link:** Klickbarer Link zum zugehörigen Service-Eintrag
    - **core_returned_badge:** ✓ Pfand zurückgegeben (Grün) mit Datum
    - Automatische created_by Zuweisung
  - VehicleServiceRecordAdmin - **Fahrzeug-Service-Verwaltung**
    - **service_status_badge:** 6 farbcodierte Status (Scheduled=Grau, In Progress=Blau, Waiting Parts=Amber, Waiting Approval=Lila, Completed=Grün, Cancelled=Rot)
    - **overdue_badge:** ⚠ X Tage überfällig (Rot) oder ✓ Pünktlich (Grün)
    - **Inline:** WorkshopStockMovementInline - Verwendete Artikel direkt im Service-Eintrag
    - **Bulk-Actions:**
      - mark_as_in_progress - Setzt started_date=heute, status=IN_PROGRESS
      - mark_as_completed - Setzt started_date + completed_date=heute, status=COMPLETED
      - calculate_parts_costs - Berechnet parts_cost aus allen used_items neu
    - Automatische created_by Zuweisung

- **Workshop Views (443 Zeilen, 19 Views):**
  - **Item-Management (5 Views):** List, Detail, Create, Update, Delete
  - **Stock Movement (3 Views):** List, Detail, Create
  - **Vehicle Service (5 Views):** List, Detail, Create, Update, Delete
  - **Special Views (6 Views):**
    - HazardousItemsListView - Alle Gefahrstoffe
    - LowStockItemsListView - Artikel mit niedrigem Bestand
    - ExpiredItemsListView - Abgelaufene Artikel
    - UpcomingServicesView - **Anstehende Services (nächste 30 Tage)**
    - OverdueServicesView - **Überfällige Services**
    - VehicleServicesView - **Service-Historie pro Fahrzeug**
  - Filter: type, status, hazardous, vehicle, service_type, technician
  - Search: item_number, name, manufacturer_part_number, oem_number, vehicle__license_plate

- **Workshop URLs (21 URL-Patterns):**
  - workshop/ - Item-Liste
  - workshop/item/<pk>/ - Item-Detail, Update, Delete
  - workshop/item/create/ - Item anlegen
  - workshop/movement/ - Lagerbewegungen Liste, Detail, Create
  - workshop/service/ - **Service-Liste, Detail, Create, Update, Delete**
  - workshop/hazardous/ - Gefahrstoffe
  - workshop/low-stock/ - Niedrige Bestände
  - workshop/expired/ - Abgelaufene Artikel
  - workshop/services/upcoming/ - **Anstehende Services**
  - workshop/services/overdue/ - **Überfällige Services**
  - workshop/vehicle/<vehicle_id>/services/ - **Fahrzeug-Service-Historie**

- **Workshop Migrations:**
  - 0001_initial.py - Alle Modelle, Indizes
  - **Indizes auf:** workshop_item_type, workshop_status, manufacturer_part_number, oem_number, is_hazardous
  - **Indizes Stock Movement:** item+movement_date, vehicle+movement_date, service_record, movement_type+movement_date
  - **Indizes Service Record:** vehicle+scheduled_date, service_type+service_status, technician+scheduled_date, service_status+scheduled_date

- **Integration:**
  - App zu INSTALLED_APPS hinzugefügt (workshop.apps.WorkshopConfig)
  - URLs in flvs_project/urls.py unter path('workshop/', include('workshop.urls'))
  - Verknüpfung mit vehicles.Vehicle (compatible_vehicles M2M, service vehicle FK)
  - Verknüpfung mit personnel.Person (technician FK)

#### 🎯 Hauptfeatures
- **Umfassende Werkstatt-Artikel-Verwaltung** - 80+ Artikel-Typen (Betriebsstoffe, Verschleißteile, Werkzeug)
- **Gefahrstoff-Management** - Kennzeichnung, GHS-Symbole, Sicherheitsdatenblätter
- **Fahrzeug-Kompatibilität** - M2M-Beziehung zeigt welche Teile für welche Fahrzeuge passen
- **Pfand-Rückgabe-System** - Tracking von Altteilrückgaben (core_charge, core_returned)
- **Fahrzeug-Service-Management** - Vollständige Dokumentation aller Wartungs- und Reparaturarbeiten
- **Automatische Kostenberechnung** - parts_cost aus used_items, total_cost = labor + parts + external
- **Überfälligkeits-Tracking** - is_overdue() für verspätete Services
- **Service-Historie pro Fahrzeug** - Komplette Wartungshistorie
- **Kilometerstand-Tracking** - vehicle_mileage bei jedem Artikel-Einsatz
- **Service-Status-Workflow** - 6 Status von Scheduled bis Completed

---

### 2025-10-03 - Equipment App vollständig implementiert (Ausrüstung & Geräte mit Wartungsmanagement)

#### ✅ Hinzugefügt
- **Equipment Models (499 Zeilen):**
  - `EquipmentType` Choices - 35+ Gerätetypen (Atemschutz, Werkzeuge, Messgeräte, Pumpen, Leiter, Schläuche, Beleuchtung, etc.)
  - `EquipmentStatus` Choices - 5 Betriebszustände (Operational, Maintenance, Defective, Testing, Decommissioned)
  - `PowerSource` Choices - 9 Antriebsarten (Manual, Electric, Gasoline, Diesel, Hydraulic, Pneumatic, Gas)
  - `CertificationStatus` Choices - 4 Zertifizierungsstatus (Valid, Expiring Soon, Expired, Not Required)
  - `EquipmentItem` Model - Erbt von AbstractInventoryItem
    - **Geräte-Details:** equipment_type, equipment_status, model_year, serial_number, power_source, weight_kg, dimensions
    - **Zertifizierung:** requires_certification, certification_number, certification_expires, certification_status
    - **Wartung:** requires_maintenance, maintenance_interval_months, last/next_maintenance_date, maintenance_notes
    - **Prüfung (UVV/TÜV):** requires_inspection, inspection_interval_months, last/next_inspection_date, inspection_notes
    - **Lebensdauer & Betriebsstunden:** max_operating_hours, current_operating_hours, max_usage_years, replacement_due_date
    - **Fahrzeug-Zuordnung:** assigned_vehicle (FK Vehicle)
    - **QR-Code:** has_qr_code, qr_code_data
    - **Tech-Specs:** technical_specs (JSONField für zusätzliche Daten)
    - Helper-Methoden: is_maintenance_due(), is_inspection_due(), is_certification_expired(), is_replacement_due(), is_operating_hours_exceeded()
  - `EquipmentStockMovement` Model - Erbt von AbstractStockMovement **mit automatischer Fahrzeugzuordnung**
    - vehicle FK - Fahrzeug bei Aus-/Einlagerung
    - person FK - Person die Gerät entnimmt/zurückgibt
    - **Zustandsdokumentation:** condition_before, condition_after
    - **Defektmeldung:** is_defective, defect_description
    - **Betriebsstunden:** operating_hours_delta (automatische Aktualisierung)
    - Kosten: unit_cost, total_cost (auto-berechnet)
    - Dokumente: delivery_note
    - **save() überschrieben:**
      - Auto-Zuweisung bei OUTGOING: assigned_vehicle = vehicle
      - Auto-Entfernung bei RETURN: assigned_vehicle = None
      - Betriebsstunden-Update: current_operating_hours += operating_hours_delta
      - Automatische Bestandsaktualisierung via update_item_stock()

- **Equipment Admin-Interface (602 Zeilen) mit Wartungs- & Prüfmanagement:**
  - EquipmentItemAdmin - Umfangreiches Geräte-Management
    - **equipment_status_badge:** Farbcodiert nach Status (Operational=Grün, Maintenance=Amber, Defective=Rot, Testing=Blau, Decommissioned=Grau)
    - **vehicle_badge:** Zeigt zugeordnetes Fahrzeug (Blau=Fahrzeug, Grau=Lager)
    - **maintenance_status_badge:** Rot=Fällig, Orange=<30 Tage, Grün=OK
    - **inspection_status_badge:** UVV/TÜV-Prüfstatus mit Fälligkeitsanzeige
    - **certification_badge:** Zertifizierung mit Ablaufdatum-Warnungen
    - **operating_hours_badge:** Fortschrittsbalken mit Farbwechsel (75%/90%/100%)
    - Inline: EquipmentStockMovementInline
    - **Bulk-Actions:**
      - mark_as_operational - Als einsatzbereit markieren
      - mark_as_defective - Als defekt markieren
      - mark_maintenance_complete - Wartung abgeschlossen (berechnet next_maintenance_date)
      - mark_inspection_complete - Prüfung abgeschlossen (berechnet next_inspection_date)
    - Fieldsets: Basis, Geräte-Details, Zertifizierung, Wartung, Prüfung, Lebensdauer & Betriebsstunden, Fahrzeug-Zuordnung, QR-Code, Tech-Specs, Bestand, Einkauf, Notizen
  - EquipmentStockMovementAdmin - Lagerbewegungen mit Fahrzeug- & Defekttracking
    - **movement_type_badge:** Farbcodiert mit Icons
    - **vehicle_badge:** Grün bei Ausgang, Blau bei Rückgabe
    - **person_badge:** Lila mit Personenicon
    - **defect_badge:** Rot=Defekt gemeldet
    - operating_hours_delta in list_display
    - Fieldsets: Bewegung, Zuordnung, Referenz, Zustand, Betriebsstunden, Kosten, Notizen, System

- **Equipment Views (317 Zeilen) mit Wartungs- & Fahrzeugverwaltung:**
  - **Item-Verwaltung:**
    - EquipmentItemListView - Alle Geräte mit Filtern (type, status, vehicle)
    - EquipmentItemDetailView - Detail mit letzten 10 Bewegungen
    - EquipmentItemCreateView, EquipmentItemUpdateView, EquipmentItemDeleteView
  - **Lagerbewegungen:**
    - EquipmentStockMovementListView - Bewegungen mit Typ-, Fahrzeug-, Defekt-Filter
    - EquipmentStockMovementDetailView - Bewegungs-Details
    - EquipmentStockMovementCreateView - Neue Bewegung (created_by = request.user)
  - **Wartung & Prüfung:**
    - MaintenanceListView - Alle wartungspflichtigen Geräte
    - MaintenanceDueView - Fällige Wartungen (next_maintenance_date <= heute)
    - InspectionListView - Alle prüfpflichtigen Geräte
    - InspectionDueView - Fällige Prüfungen (next_inspection_date <= heute)
  - **Fahrzeug-Ausrüstung:**
    - VehicleEquipmentListView - Ausrüstung eines bestimmten Fahrzeugs
  - **Defekte Geräte:**
    - DefectiveEquipmentListView - Alle defekten Geräte

- **Equipment URLs:**
  - 16 URL-Patterns mit Namespace 'equipment'
  - Wartung & Prüfung: maintenance/, maintenance/due/, inspection/, inspection/due/
  - Fahrzeug-Spezifisch: vehicle/<id>/
  - Defekte: defective/
  - Integration in Haupt-URLs (flvs_project/urls.py)

#### 🔧 Geändert
- `flvs_project/settings/base.py`:
  - equipment.apps.EquipmentConfig zu LOCAL_APPS hinzugefügt
- `flvs_project/urls.py`:
  - equipment URLs aktiviert (path('equipment/', include('equipment.urls')))

#### 📝 Migrations
- `equipment/migrations/0001_initial.py`:
  - EquipmentItem, EquipmentStockMovement Models
  - Indizes: equipment_type, equipment_status, serial_number, next_maintenance_date, next_inspection_date, assigned_vehicle
  - Indizes für Bewegungen: item+movement_date, vehicle+movement_date, person+movement_date, movement_type+movement_date

#### 🎯 Features
- **Wartungsmanagement:** Automatische Berechnung der nächsten Wartung (Intervall in Monaten)
- **Prüfmanagement:** UVV/TÜV-Prüfungen mit Fälligkeitsverfolgung
- **Betriebsstunden-Tracking:** Automatische Aktualisierung bei Bewegungen
- **Fahrzeugzuordnung:** Automatisch bei Ausgabe/Rückgabe
- **Defektmanagement:** Defektmeldung mit Beschreibung
- **QR-Code-Support:** QR-Code-Kennzeichnung für schnelle Inventur

---

### 2025-10-03 - Clothing App vollständig implementiert (Kleiderkammer mit PSA-Verwaltung)

#### ✅ Hinzugefügt
- **Clothing Models (485 Zeilen):**
  - `ClothingType` Choices - 15 Kleidungstypen (Jacket, Pants, Overall, Shirt, Underwear, Shoes, Boots, Gloves, Helmet, Vest, Coat, Hat, Protective, Uniform, Other)
  - `ClothingSize` Choices - 40+ Größen (XXS-XXXXL, numerisch 36-60, Schuhgrößen 36-48)
  - `Gender` Choices - 3 Schnitte (Unisex, Male, Female)
  - `ProtectionLevel` Choices - 5 PSA-Stufen (None, Basic, Enhanced, High, Specialist)
  - `ClothingItem` Model - Erbt von AbstractInventoryItem
    - **Kleidungs-Details:** clothing_type, size, gender, color, material
    - **PSA-Informationen:** is_psa, protection_level, norm_standard (z.B. EN 469)
    - **Zertifizierung:** certification_number, certification_date, certification_expires
    - **Prüfung & Wartung:** requires_inspection, inspection_interval_months, last/next_inspection_date, max_usage_years
    - **Reinigung & Pflege:** washing_instructions, max_washing_cycles, current_washing_cycles
    - **Personenzuordnung:** assigned_to (FK Person), assignment_date, is_personal_issue
    - **Besondere Merkmale:** has_name_tag, reflective_strips, special_features
    - Helper-Methoden: is_inspection_due(), is_certification_expired(), is_washing_limit_reached()
  - `ClothingStockMovement` Model - Erbt von AbstractStockMovement **mit automatischer Personenzuordnung**
    - person FK - Person die Kleidung erhält/zurückgibt
    - **Rückgabe:** return_reason, return_condition_notes, cleaned_before_return
    - Kosten: unit_cost, total_cost (auto-berechnet)
    - Dokumente: delivery_note
    - **save() überschrieben:**
      - Auto-Zuweisung bei OUTGOING: assigned_to = person, is_personal_issue = True
      - Auto-Entfernung bei RETURN: assigned_to = None, is_personal_issue = False
      - Automatische Bestandsaktualisierung via update_item_stock()
  - `ClothingSizeAssignment` Model - Größenzuordnung pro Person
    - person FK, clothing_type, size, notes
    - unique_together: [person, clothing_type] (eine Größe pro Typ pro Person)
    - Automatisches updated_at Feld

- **Clothing Admin-Interface (593 Zeilen) mit PSA & Personenzuordnung:**
  - ClothingItemAdmin - Umfangreiches Kleidungs-Management
    - **PSA-Badge:** Farbcodiert nach Schutzlevel (Basic=Blau, Enhanced=Gelb, High=Orange, Specialist=Rot)
    - **assigned_person_badge:** Grün für persönliche Ausgabe, Blau für Pool
    - **inspection_status_badge:** Rot=Fällig, Orange=<30 Tage, Grün=OK
    - **certification_status_badge:** Rot=Abgelaufen, Orange=<90 Tage, Grün=Gültig
    - **washing_status_badge:** Fortschrittsbalken mit Farbwechsel (75%/90%/100%)
    - Inline: ClothingStockMovementInline
    - **Bulk-Actions:**
      - mark_for_inspection - Als prüfpflichtig markieren
      - mark_inspection_complete - Prüfung abgeschlossen (setzt next_inspection_date)
      - increment_washing_cycles - Waschzyklus +1
      - unassign_from_person - Personenzuordnung aufheben
    - Fieldsets: Basis, Kleidungs-Details, PSA & Sicherheit, Prüfung & Wartung, Reinigung & Pflege, Personenzuordnung, Besondere Merkmale, Bestand & Einheit, Einkauf, Notizen
  - ClothingStockMovementAdmin - Lagerbewegungen mit Personenzuordnung
    - **movement_type_badge:** Farbcodiert mit Icons (Eingang=Grün 📥, Ausgang=Rot 📤, Rückgabe=Blau ↩️)
    - **person_badge:** Grün bei Ausgang, Blau bei Rückgabe
    - **cleaned_badge:** Grün=Gereinigt, Orange=Nicht gereinigt (nur bei Rückgabe)
    - Fieldsets: Bewegung, Personenzuordnung, Referenz, Rückgabe, Kosten, Notizen, System
  - ClothingSizeAssignmentAdmin - Größenverwaltung
    - Liste: person, clothing_type, size, updated_at
    - list_select_related für Performance

- **Clothing Views (363 Zeilen) mit PSA & Personenzuordnung:**
  - **Item-Verwaltung:**
    - ClothingItemListView - Alle Kleidungsstücke mit Filtern (type, size, is_psa, assignment)
    - ClothingItemDetailView - Detail mit letzten 10 Bewegungen
    - ClothingItemCreateView, ClothingItemUpdateView, ClothingItemDeleteView (Soft-Delete)
  - **Lagerbewegungen:**
    - ClothingStockMovementListView - Bewegungen mit Typ- & Personen-Filter
    - ClothingStockMovementDetailView - Bewegungs-Details
    - ClothingStockMovementCreateView - Neue Bewegung (created_by = request.user)
  - **PSA-Übersicht:**
    - PSAOverviewView - Alle PSA-Kleidung mit Statistiken (total, expired_cert, inspection_due)
    - PSAExpiringView - PSA mit Zertifikaten die in 90 Tagen ablaufen
  - **Prüfungen:**
    - InspectionListView - Alle prüfpflichtigen Kleidungsstücke
    - InspectionDueView - Fällige Prüfungen (next_inspection_date <= heute)
  - **Personenzuordnungen:**
    - PersonAssignmentListView - Alle zugeordneten Items mit Personen-Statistik
    - PersonSizeManagementView - Größenverwaltung für eine Person (assigned_items + size_assignments)

- **Clothing URLs:**
  - 17 URL-Patterns mit Namespace 'clothing'
  - PSA-Übersicht: psa/, psa/expiring/
  - Prüfungen: inspections/, inspections/due/
  - Personenzuordnung: assignments/, person/<id>/sizes/
  - Integration in Haupt-URLs (flvs_project/urls.py)

#### 🔧 Geändert
- `flvs_project/settings/base.py`:
  - clothing.apps.ClothingConfig zu LOCAL_APPS hinzugefügt
- `flvs_project/urls.py`:
  - clothing URLs aktiviert (path('clothing/', include('clothing.urls')))

#### 📝 Migrations
- `clothing/migrations/0001_initial.py`:
  - ClothingItem, ClothingStockMovement, ClothingSizeAssignment Models
  - Indizes: clothing_type+size, is_psa, assigned_to, next_inspection_date
  - Indizes für Bewegungen: item+movement_date, person+movement_date, movement_type+movement_date
  - unique_together für ClothingSizeAssignment (person, clothing_type)

#### 🎯 Features
- **PSA-Compliance:** Zertifizierungsverfolgung mit Ablaufdatum-Warnungen
- **Prüfmanagement:** Automatische Berechnung der nächsten Prüfung (Intervall in Monaten)
- **Waschzyklen-Tracking:** Max-Limit mit Fortschrittsanzeige
- **Personenzuordnung:** Automatisch bei Ausgabe/Rückgabe
- **Größenverwaltung:** Hinterlegt Größen pro Person & Kleidungstyp

---

### 2025-10-03 - Medical App vollständig implementiert (mit BTM-Sicherheit)

#### ✅ Hinzugefügt
- **Medical Models (601 Zeilen):**
  - `MedicalItemType` Choices - 11 Artikeltypen (Medication, BTM, Infusion, Injection, Bandage, Diagnostic, Device, Disinfectant, Oxygen, Disposable, Other)
  - `AdministrationRoute` Choices - 9 Verabreichungswege (Oral, IV, IM, SC, Inhalation, Topical, Rectal, Sublingual, Other)
  - `StorageCondition` Choices - 6 Lagerungsbedingungen (Room Temp, Refrigerated, Frozen, Dark, Dry, Special)
  - `BTMApprovalStatus` Choices - 3 Status (Pending, Approved, Rejected)
  - `MedicalItem` Model - Erbt von AbstractInventoryItem
    - **BTM-Kennzeichnung:** is_btm (boolean)
    - Pharmazeutische Informationen: active_ingredient, dosage, pharmaceutical_form, administration_route
    - Zulassung: pzn (Pharmazentralnummer), atc_code, approval_number
    - Lagerung: storage_condition, requires_cold_chain, expiry_warning_days
    - Verschreibung: is_prescription_required, package_insert (FileField), spc_document (FileField)
    - Medizinprodukte: is_medical_device, medical_device_class, udi
    - Wartung: requires_maintenance, maintenance_interval_months, last/next_maintenance_date
    - Medizinische Informationen: indications, contraindications, side_effects
    - Helper-Methode: is_maintenance_due()
  - `MedicalStockMovement` Model - Erbt von AbstractStockMovement **mit BTM-Vier-Augen-Prinzip**
    - item FK zu MedicalItem
    - Chargen-Information: batch_number, expiry_date
    - Medizinischer Kontext: patient_id (anonymisiert), diagnosis, administered_by
    - **BTM-Freigabe (Vier-Augen-Prinzip):**
      - requires_approval (boolean, automatisch gesetzt wenn BTM + Outgoing/Disposal)
      - approval_status (Pending/Approved/Rejected)
      - approved_by, approved_at, rejection_reason
    - Dokumente: prescription_number, delivery_note
    - Kosten: unit_cost, total_cost (auto-berechnet)
    - **save() überschrieben:** BTM-Check, Berechnung, Bestandsaktualisierung nur bei Freigabe
    - **approve(user):** Freigabe erteilen mit Vier-Augen-Check (ValueError wenn gleicher User)
    - **reject(user, reason):** Freigabe ablehnen mit Begründung
    - **update_item_stock():** Bestand aktualisieren (nur wenn freigegeben)
  - `MedicalBatch` Model - Chargen-/Lot-Tracking mit Compliance
    - batch_number, supplier_batch_number
    - quantity_received, quantity_remaining
    - received_date, expiry_date
    - **Temperatur-Logging:** temperature_log (JSONField), cold_chain_break (boolean)
    - **Qualitätskontrolle:** quality_check_passed, quality_check_date, quality_check_notes
    - **Rückruf-Management:** is_recalled, recall_date, recall_reason
    - Helper-Methoden: is_expired(), is_expiring_soon(days), is_depleted()

- **Medical Admin-Interface (877 Zeilen) mit BTM-Sicherheit:**
  - MedicalItemAdmin - Umfangreiches Item-Management
    - **BTM-Badge:** Rot hervorgehoben mit ☢️ Emoji
    - **BTM-Kennzeichnung Fieldset:** Prominent an erster Stelle mit Warnhinweis
    - Inline-Admins: MedicalBatchInline, MedicalStockMovementInline
    - Farbcodierte Badges: stock_status, storage_badge (Kühlkette), maintenance_status
    - Statistiken: pending_btm_approvals_count (zeigt ausstehende Freigaben)
    - Bulk-Actions: mark_as_active, mark_as_inactive, check_expiring_batches
    - Filter: item_type, is_btm, category, location, storage_condition, requires_cold_chain, is_medical_device, requires_maintenance
  - MedicalStockMovementAdmin - Lagerbewegungen mit BTM-Freigabe-Workflow
    - **BTM-Freigabe Fieldset:** Prominent mit Status, Approved By, Timestamp
    - **btm_approval_badge:** Farbcodiert (Amber=Pending, Green=Approved, Red=Rejected)
    - **Bulk-Actions für BTM-Freigaben:**
      - approve_btm_movements - Prüft Vier-Augen-Prinzip, zeigt Fehler bei Selbst-Freigabe
      - reject_btm_movements - Lehnt BTM-Bewegungen ab
    - Filter: movement_type, requires_approval, approval_status
  - MedicalBatchAdmin - Chargen mit Rückruf-Management
    - **Rückruf-Fieldset:** Prominent an erster Stelle
    - **recall_badge:** Rot hervorgehoben mit 🚨 Emoji
    - Fortschrittsbalken für quantity_remaining
    - Status-Badges: Aufgebraucht, Abgelaufen, Läuft ab, OK
    - quality_badge, cold_chain_break Anzeige
    - Bulk-Action: mark_as_recalled

- **Medical Views (435 Zeilen) mit BTM-Sicherheit:**
  - MedicalItemListView - Alle Artikel mit erweiterten Filtern (inkl. BTM-Filter)
  - MedicalItemDetailView - Detail mit recent_movements, active_batches, pending_approvals (BTM)
  - **BTM-Bereich:**
    - BTMItemListView - Alle BTM-Artikel (besondere Sicherheitsansicht)
    - BTMApprovalListView - Ausstehende BTM-Freigaben
    - approve_btm_movement(request, pk) - Freigabe erteilen mit Vier-Augen-Prüfung
    - reject_btm_movement(request, pk) - Freigabe ablehnen mit Begründung
  - LowStockListView - Artikel unter min_quantity
  - ExpiringBatchesListView - Chargen die in 90 Tagen ablaufen (ohne zurückgerufene)
  - ColdChainItemsListView - Artikel mit Kühlketten-Anforderung + Chargen mit Unterbrechung
  - MaintenanceDueListView - Medizingeräte mit fälliger Wartung
  - StockMovementListView - Alle Lagerbewegungen mit BTM-Filter & approval_status-Filter
  - StockMovementDetailView - Bewegungs-Details
  - BatchListView - Alle Chargen (optional ohne aufgebrauchte/zurückgerufene)
  - RecalledBatchesListView - Nur zurückgerufene Chargen

- **Medical URLs:**
  - 17 URL-Patterns mit Namespace 'medical'
  - BTM-spezifische URLs: btm/, btm/approvals/, btm/movement/<pk>/approve/, btm/movement/<pk>/reject/
  - Integration in Haupt-URLs (flvs_project/urls.py)

#### 🔧 Geändert
- `flvs_project/settings/base.py`:
  - medical.apps.MedicalConfig zu LOCAL_APPS hinzugefügt
- `flvs_project/urls.py`:
  - medical URLs aktiviert (path('medical/', include('medical.urls')))

#### 🗄️ Datenbank
- Migration 0001_initial für medical erstellt und angewendet
- MedicalItem Tabelle mit allen Feldern von AbstractInventoryItem + medical-spezifische Felder
- MedicalStockMovement Tabelle mit BTM-Freigabe-Feldern
- MedicalBatch Tabelle mit Temperatur-Logging, Qualitätskontrolle, Rückruf-Management
- 9 Indizes erstellt (item_type/category, is_btm, pzn, atc_code, next_maintenance_date, item/expiry_date, batch_number, is_recalled, expiry_date, approval_status)

#### 🔒 Sicherheit (BTM-Bereich)
- **Vier-Augen-Prinzip:** BTM-Bewegungen (Outgoing/Disposal) erfordern Freigabe durch anderen Benutzer
- **Automatische BTM-Erkennung:** requires_approval wird automatisch gesetzt bei BTM-Items
- **Bestandsschutz:** Keine Bestandsänderung bis approval_status = APPROVED
- **Fehlerprüfung:** ValueError bei Selbst-Freigabe (created_by == approved_by)
- **Audit-Trail:** approved_by, approved_at, rejection_reason vollständig dokumentiert
- **BTM-Badge:** Rot hervorgehoben in allen Listen und Detail-Ansichten
- **IP-Logging:** Vorbereitet durch AuditedModel (created_by/updated_by)

#### 📝 Hinweise
- **BTM-Compliance:** Vollständig BtMG-konform mit Vier-Augen-Prinzip
- **Kühlketten-Überwachung:** Temperatur-Logging (JSONField) für lückenlose Dokumentation
- **Rückruf-Management:** Chargen können als zurückgerufen markiert werden
- **Wartungs-Management:** Automatische Wartungserinnerungen für Medizingeräte
- **Chargen-Rückverfolgbarkeit:** Vollständig für Compliance und Rückrufe
- Templates müssen noch erstellt werden (13 Views + 2 BTM-Functions warten auf Templates)
- Permissions für medical.* und BTM-spezifische Permissions müssen in permissions App hinzugefügt werden
- **WICHTIG:** BTM-Bereich erfordert zusätzliche Schulung der Benutzer zum Vier-Augen-Prinzip

---

### 2025-10-03 - Magazine App vollständig implementiert

#### ✅ Hinzugefügt
- **Magazine Models (438 Zeilen):**
  - `MagazineItemType` Choices - 10 Artikeltypen (Hose, Fitting, Tool, Consumable, Chemical, Cleaning, Spare Part, Fastener, Electrical, Other)
  - `HazardClass` Choices - 9 Gefahrenklassen (Keine, Explosiv, Entzündbar, Oxidierend, Druckgas, Ätzend, Giftig, Gesundheitsschädlich, Umweltgefährlich)
  - `MagazineItem` Model - Erbt von AbstractInventoryItem
    - Magazin-spezifische Felder: item_type, size, material, color
    - Gewicht & Volumen: weight_per_unit, volume_per_unit
    - Gefahrgut: is_hazardous, hazard_class, safety_data_sheet (FileField)
    - Haltbarkeit: has_expiry_date, shelf_life_months
    - Lagerung: storage_temperature_min/max, storage_instructions
    - Bestellung: reorder_point, standard_order_quantity, last_ordered_date
    - Zusatzinformationen: technical_specifications, usage_instructions
    - Helper-Methoden: is_reorder_needed(), get_total_weight(), get_total_volume()
  - `MagazineStockMovement` Model - Erbt von AbstractStockMovement
    - item FK zu MagazineItem
    - Chargen-Tracking: batch_number, expiry_date
    - Kosten: unit_cost, total_cost (auto-berechnet)
    - Verwendung: purpose, recipient_name
    - Dokumente: delivery_note, invoice_number
    - save() überschrieben: Berechnet total_cost, übernimmt unit von item, ruft update_item_stock()
    - update_item_stock() - Aktualisiert Bestand basierend auf movement_type
  - `MagazineBatch` Model - Chargen-/Lot-Tracking
    - batch_number, supplier_batch_number
    - quantity_received, quantity_remaining
    - received_date, expiry_date
    - location FK
    - Helper-Methoden: is_expired(), is_depleted()
    - unique_together: item + batch_number

- **Magazine Admin-Interface (633 Zeilen):**
  - MagazineItemAdmin - Umfangreiches Item-Management
    - Inline-Admins: MagazineBatchInline, MagazineStockMovementInline
    - Farbcodierte Badges: stock_status, hazard_badge, reorder_status
    - Berechnete Felder: total_stock_value, total_weight_display, total_volume_display
    - Statistiken: stock_movements_count, batches_count
    - Bulk-Actions: mark_as_active, mark_as_inactive, check_reorder_needed
    - Filter: item_type, category, location, is_hazardous, has_expiry_date, supplier
  - MagazineStockMovementAdmin - Lagerbewegungen verwalten
    - Farbcodierte Bewegungstyp-Badges mit Emojis
    - Berechnete Gesamtkosten-Anzeige
    - Filter: movement_type, movement_date, from_location, to_location
    - date_hierarchy auf movement_date
  - MagazineBatchAdmin - Chargen verwalten
    - Fortschrittsbalken für quantity_remaining
    - Status-Badges: Aufgebraucht, Abgelaufen, OK
    - date_hierarchy auf expiry_date

- **Magazine Views (255 Zeilen):**
  - MagazineItemListView - Alle Artikel mit Suche & Filtern
  - MagazineItemDetailView - Detail mit recent_movements & active_batches
  - LowStockListView - Artikel unter min_quantity
  - ReorderNeededListView - Artikel unter reorder_point
  - HazardousItemsListView - Alle Gefahrgut-Artikel
  - StockMovementListView - Alle Lagerbewegungen mit Filtern
  - StockMovementDetailView - Bewegungs-Details
  - BatchListView - Alle Chargen (optional mit aufgebrauchten)
  - ExpiringBatchesListView - Chargen die in 90 Tagen ablaufen

- **Magazine URLs:**
  - 10 URL-Patterns mit Namespace 'magazine'
  - Integration in Haupt-URLs (flvs_project/urls.py)

#### 🔧 Geändert
- `flvs_project/settings/base.py`:
  - magazine.apps.MagazineConfig zu LOCAL_APPS hinzugefügt
- `flvs_project/urls.py`:
  - magazine URLs aktiviert (path('magazine/', include('magazine.urls')))

#### 🗄️ Datenbank
- Migration 0001_initial für magazine erstellt und angewendet
- MagazineItem Tabelle mit allen Feldern von AbstractInventoryItem + magazin-spezifische Felder
- MagazineStockMovement Tabelle mit Chargen-Tracking
- MagazineBatch Tabelle für Lot-Tracking
- 7 Indizes erstellt (item_type/category, is_hazardous, has_expiry_date, item/expiry_date, batch_number, item/movement_date, movement_type/movement_date)

#### 📝 Hinweise
- Erste konkrete Implementierung basierend auf inventory_base Abstract Base Classes
- Automatische Bestandsaktualisierung bei Lagerbewegungen über save() Signal
- Chargen-Rückverfolgbarkeit für Compliance
- Gefahrgut-Management mit Sicherheitsdatenblatt-Upload
- Reorder-Management für automatische Bestellvorschläge
- Templates müssen noch erstellt werden (10 Views warten auf Templates)
- Permissions für magazine.* müssen in permissions App hinzugefügt werden

---

### 2025-10-03 - Inventory Base App vollständig implementiert

#### ✅ Hinzugefügt
- **Inventory Base Models (418 Zeilen):**
  - `StockMovementType` Choices - 7 Bewegungstypen (Incoming, Outgoing, Transfer, Inventory, Damage, Return, Disposal)
  - `ItemCondition` Choices - 6 Zustände (New, Good, Used, Worn, Damaged, Defect)
  - `Category` Model - Hierarchische Kategorien mit django-mptt
    - TreeForeignKey für Parent-Beziehung
    - Eindeutiger Code pro Kategorie
    - `get_full_path()` Methode für vollständigen Pfad
  - `Supplier` Model - Lieferanten/Hersteller-Verwaltung
    - Vollständige Kontaktdaten (Name, E-Mail, Telefon, Website)
    - Vollständige Adresse (Straße, PLZ, Stadt, Land)
    - Zahlungsbedingungen und Steuernummer
  - `AbstractInventoryItem` - Abstract Base Class für alle Inventar-Items
    - Basis-Felder: name, item_number, description
    - Kategorisierung: category, supplier, manufacturer
    - Lagerort: location (FK zu locations.Location)
    - Bestandsmanagement: quantity, unit, min_quantity, max_quantity
    - Zustand: condition (mit ItemCondition Choices)
    - Identifikation: barcode, qr_code
    - Preise: unit_price
    - Bilder: image (ImageField)
    - Helper-Methoden: is_low_stock(), is_out_of_stock(), get_stock_percentage(), calculate_total_value()
    - Dynamic related_name: '%(app_label)s_%(class)s_items' für Verwendung in mehreren Apps
  - `AbstractStockMovement` - Abstract Base Class für Lagerbewegungen
    - movement_type mit StockMovementType Choices
    - quantity und unit
    - from_location und to_location (beide FK zu locations.Location)
    - reference_number für Lieferschein/Bestellung
    - movement_date (auto_now_add)
    - Dynamic related_name für from/to Locations

- **Inventory Base Admin-Interface (274 Zeilen):**
  - CategoryAdmin - DraggableMPTTAdmin für Drag & Drop-Hierarchie
    - Hierarchische Anzeige mit Einrückung
    - Vollständiger Pfad in Liste
    - Item-Count Spalte (vorbereitet für konkrete Apps)
    - Status-Badge (Aktiv/Inaktiv)
    - Filteroptionen (Aktiv, Erstellt)
  - SupplierAdmin - Lieferanten-Verwaltung
    - Übersichtliche Darstellung mit Kontaktdaten
    - Status-Badge (Aktiv/Inaktiv)
    - Item-Count Spalte (vorbereitet für konkrete Apps)
    - Filteroptionen (Aktiv, Land, Erstellt)
    - Bulk-Actions: activate_suppliers, deactivate_suppliers
    - Suchfunktion (Name, Nummer, Kontakt, E-Mail, Stadt)

#### 🔧 Geändert
- `flvs_project/settings/base.py`:
  - inventory_base.apps.InventoryBaseConfig zu LOCAL_APPS hinzugefügt

#### 🗄️ Datenbank
- Migration 0001_initial für inventory_base erstellt und angewendet
- Category Tabelle mit MPTT-Feldern (lft, rght, tree_id, level)
- Supplier Tabelle mit allen Kontakt- und Adressfeldern

#### 📝 Hinweise
- AbstractInventoryItem und AbstractStockMovement sind abstrakt und erzeugen keine eigenen DB-Tabellen
- Werden von konkreten Apps geerbt (magazine, medical, clothing, etc.)
- Category und Supplier sind shared models - werden von allen Inventory-Apps verwendet
- Item-Count in Admin ist vorbereitet, funktioniert wenn erste konkrete App (z.B. magazine) implementiert ist
- Für Barcode/QR-Code Scanning: Integration mit django-qr-code oder python-barcode geplant

---

### 2025-10-03 - Notifications App vollständig implementiert

#### ✅ Hinzugefügt
- **Notifications Models (342 Zeilen):**
  - `Notification` Model - Benachrichtigungen für Benutzer
  - `NotificationPreference` Model - Benutzer-Einstellungen für Benachrichtigungen
  - `NotificationType` Choices - 8 Typen (Info, Warning, Error, Success, Reminder, Expiry, Approval, System)
  - `NotificationCategory` Choices - 8 Kategorien (General, Inventory, Vehicle, Personnel, Inspection, Qualification, Order, System)
  - Generic Foreign Key - Verlinkung zu beliebigen Objekten
  - Status-Tracking (is_read, is_archived, read_at)
  - Prioritäts-System für wichtige Benachrichtigungen
  - Ablaufdatum für automatische Archivierung
  - Custom Manager mit QuerySet (unread, read, archived, active, by_type, by_category, high_priority)
  - Model-Methoden (mark_as_read, mark_as_unread, archive, is_expired)

- **Notification Utility-Funktionen (utils.py - 235 Zeilen):**
  - `create_notification()` - Benachrichtigung erstellen
  - `notify_user()`, `notify_users()`, `notify_all_users()` - Benutzer benachrichtigen
  - `notify_by_role()` - Rollenbasierte Benachrichtigungen
  - Spezifische Helper: `notify_vehicle_inspection_due()`, `notify_qualification_expiring()`, `notify_low_stock()`, `notify_approval_needed()`
  - Bulk-Operationen: `mark_all_as_read()`, `archive_old_notifications()`, `delete_expired_notifications()`

- **Notifications Admin-Interface (230 Zeilen):**
  - NotificationAdmin mit farbcodierten Typ-Badges und Emojis
  - NotificationPreferenceAdmin für Einstellungen
  - Bulk-Actions: mark_as_read, mark_as_unread, archive_notifications
  - Filteroptionen (Typ, Kategorie, Gelesen, Archiviert)
  - Suchfunktion (Titel, Nachricht, Empfänger)

- **Notifications Views (228 Zeilen):**
  - NotificationListView - Alle Benachrichtigungen mit Filtern
  - NotificationPreferenceView - Einstellungen bearbeiten
  - AJAX-Endpoints: mark_as_read, mark_as_unread, archive_notification, mark_all_as_read
  - API-Endpoints: unread_count (für Badge), notification_dropdown (für Header)
  - HTMX-Support für dynamische Updates

- **Notifications URLs:**
  - 8 URL-Patterns mit Namespace 'notifications'
  - Integration in Haupt-URLs (flvs_project/urls.py)

#### 🔧 Geändert
- `flvs_project/settings/base.py`:
  - notifications.apps.NotificationsConfig zu LOCAL_APPS hinzugefügt
- `flvs_project/urls.py`:
  - notifications URLs aktiviert

#### 🗄️ Datenbank
- Migration 0001_initial für notifications erstellt und angewendet
- 5 Indizes erstellt (recipient/created_at, recipient/is_read, notification_type/created_at, category/created_at, expires_at)

#### 📝 Hinweise
- Für E-Mail-Benachrichtigungen: Celery-Tasks für async Versand einrichten
- Für Cleanup: Celery Periodic Task für `archive_old_notifications()` und `delete_expired_notifications()`
- HTMX-Partials in Templates erstellen für dynamische Updates
- Integration in Header-Template für Benachrichtigungs-Badge

---

### 2025-10-03 - Audit App vollständig implementiert

#### ✅ Hinzugefügt
- **Audit Models (305 Zeilen):**
  - `AuditLog` Model - Unveränderbare Änderungshistorie für alle Operationen
  - `AuditAction` Choices - 11 Aktionstypen (Create, Update, Delete, View, Login, Logout, Export, Import, Approve, Reject, Custom)
  - `AuditSeverity` Choices - 5 Schweregrade (Info, Warning, Error, Critical, Security)
  - Generic Foreign Key - Unterstützung für beliebige Objekte
  - JSON-Felder für Änderungen und Extra-Daten
  - IP-Adresse und User-Agent Tracking
  - Verhindert Updates/Deletes in save() und delete() Methoden
  - Custom Manager mit QuerySet (for_user, for_object, for_model, by_action, security_relevant, critical_logs)
  - log_action() Class-Method für einfaches Logging

- **Audit Utility-Funktionen (utils.py - 260 Zeilen):**
  - `get_client_ip()` - Ermittelt Client-IP mit Proxy-Support
  - `log_create()`, `log_update()`, `log_delete()` - CRUD-Logging
  - `log_view()` - View-Tracking (wichtig für BTM-Bereich)
  - `log_login()`, `log_logout()` - Auth-Logging
  - `log_export()`, `log_import()` - Daten-Transfer-Logging
  - `log_custom()` - Benutzerdefiniertes Logging
  - `compare_model_instances()` - Automatischer Änderungsvergleich

- **Audit Admin-Interface (232 Zeilen):**
  - Read-Only Admin (kein Add/Change/Delete)
  - Farbcodierte Action- und Severity-Badges mit Emojis
  - Objekt-Links zu Admin-Detail-Seiten
  - Änderungs-Tabelle mit Alt/Neu-Vergleich
  - Filteroptionen (Action, Severity, App, Zeitstempel)
  - Suchfunktion (Beschreibung, Objekt, User, IP)

- **Audit Views (166 Zeilen):**
  - AuditLogListView - Alle Logs (mit Permission)
  - AuditLogDetailView - Log-Detail
  - MyAuditLogsView - Eigene Logs (ohne Permission)
  - ObjectAuditLogsView - Logs für spezifisches Objekt
  - SecurityLogsView - Nur Security/Critical Logs
  - Filter: Action, Severity, User, App, Zeitraum (today/week/month)

- **Audit URLs:**
  - 5 URL-Patterns mit Namespace 'audit'
  - Integration in Haupt-URLs (flvs_project/urls.py)

#### 🔧 Geändert
- `flvs_project/settings/base.py`:
  - audit.apps.AuditConfig zu LOCAL_APPS hinzugefügt
- `flvs_project/urls.py`:
  - audit URLs aktiviert

#### 🗄️ Datenbank
- Migration 0001_initial für audit erstellt und angewendet
- 6 Indizes erstellt (timestamp, user/timestamp, action/timestamp, severity/timestamp, app_label/model_name/timestamp, content_type/object_id)
- Custom Permissions: view_all_logs, export_logs

#### 📝 Hinweise
- Audit-Logs sind unveränderbar (save() wirft ValueError bei Update, delete() wirft ValueError)
- Für BTM-Bereich: log_view() mit severity=AuditSeverity.SECURITY nutzen
- Integration in Views via Utility-Funktionen aus audit.utils

---

### 2025-10-03 - Vehicles App vollständig implementiert

#### ✅ Hinzugefügt
- **Vehicles Models (388 Zeilen):**
  - `Vehicle` Model - Fahrzeug-Stammdaten mit vollständigen technischen Daten
  - `VehicleInspection` Model - Prüfhistorie (HU, UVV, Wartung, Reparatur)
  - `VehicleType` Choices - 9 Fahrzeugtypen (Löschfahrzeug, RTW, Drehleiter, etc.)
  - `VehicleStatus` Choices - 6 Status (Einsatzbereit, Im Einsatz, Wartung, etc.)
  - `InspectionType` Choices - 6 Prüfungstypen
  - `InspectionStatus` Choices - 5 Prüfungsstatus
  - Mobile Lager-Funktion - Fahrzeuge als Location für Inventar
  - Kennzeichen-Validierung (deutsches Format)
  - Prüfdaten-Tracking (HU, UVV, Versicherung) mit Ablaufwarnungen
  - 4 Model-Methoden (is_inspection_due, is_safety_check_due, is_insurance_expiring, get_recent_inspections)

- **Vehicles Admin-Interface (277 Zeilen):**
  - VehicleAdmin mit VehicleInspectionInline
  - Farbcodierte Status-Badges (Einsatzbereit/Wartung/Reparatur)
  - HU-Status-Warnung (Überfällig/Bald fällig/OK) mit Tagesberechnung
  - VehicleInspectionAdmin mit Prüfstatus-Anzeige
  - Filteroptionen (Fahrzeugtyp, Status, Kraftstoff, Mobile Lager)
  - Suchfunktion (Funkrufname, Kennzeichen, FIN, Hersteller)

- **Vehicles Views (287 Zeilen):**
  - VehicleListView mit Such- und Filterfunktion
  - VehicleDetailView mit Prüfhistorie und Warnungen
  - VehicleCreateView, VehicleUpdateView, VehicleDeleteView
  - VehicleInspectionCreateView mit Auto-Update der Fahrzeug-Prüfdaten
  - VehicleInspectionUpdateView, VehicleInspectionDeleteView
  - Audit-Trail in allen Create/Update-Views

- **Vehicles Forms (295 Zeilen):**
  - VehicleForm mit Tailwind CSS Styling
  - VehicleInspectionForm mit Tailwind CSS Styling
  - Custom Validierung: Funkrufname eindeutig
  - Custom Validierung: Kennzeichen eindeutig
  - Custom Validierung: Nächste Prüfung nach aktueller Prüfung

- **Vehicles URLs:**
  - 8 URL-Patterns mit Namespace 'vehicles'
  - Integration in Haupt-URLs (flvs_project/urls.py)

#### 🔧 Geändert
- `flvs_project/settings/base.py`:
  - vehicles.apps.VehiclesConfig zu LOCAL_APPS hinzugefügt
- `flvs_project/urls.py`:
  - vehicles URLs aktiviert

#### 🗄️ Datenbank
- Migration 0001_initial für vehicles erstellt und angewendet
- 8 Indizes erstellt (call_sign, license_plate, status, is_active, next_inspection_date, vehicle/inspection_type)

---

### 2025-10-03 - Personnel App vollständig implementiert

#### ✅ Hinzugefügt
- **Personnel Models (255 Zeilen):**
  - `Person` Model - Personal-Stammdaten mit vollständiger Adress- und Kontaktverwaltung
  - `Qualification` Model - Qualifikationen/Zertifikate/Lehrgänge mit Ablaufdaten
  - `QualificationType` Choices - 6 Typen (Lehrgang, Zertifikat, Führerschein, Medizinische Untersuchung, Sicherheitsunterweisung, Sonstiges)
  - Person-User-Verknüpfung (optional) - nicht jedes Personal braucht Account
  - Foto-Upload für Personal
  - 3 Model-Methoden (get_qualifications, get_expired_qualifications, get_address)

- **Personnel Admin-Interface (249 Zeilen):**
  - PersonAdmin mit QualificationInline
  - Farbcodierte Qualifikations-Anzahl und Account-Status
  - QualificationAdmin mit Ablauf-Status-Indikator (Gültig/Läuft bald ab/Abgelaufen)
  - Filteroptionen (Abteilung, Dienstgrad, Aktiv, Qualifikationstyp)
  - Suchfunktion (Name, Personalnummer, Zertifikatsnummer)

- **Personnel Views (244 Zeilen):**
  - PersonListView mit Such- und Filterfunktion
  - PersonDetailView mit aktiven/abgelaufenen Qualifikationen
  - PersonCreateView, PersonUpdateView, PersonDeleteView
  - QualificationCreateView mit Person-Vorauswahl
  - QualificationUpdateView, QualificationDeleteView
  - Audit-Trail in allen Create/Update-Views

- **Personnel Forms (268 Zeilen):**
  - PersonForm mit Tailwind CSS Styling
  - QualificationForm mit Tailwind CSS Styling
  - Custom Validierung: Personalnummer eindeutig
  - Custom Validierung: Austritt nach Eintritt
  - Custom Validierung: Ablaufdatum nach Ausstellungsdatum

- **Personnel URLs:**
  - 8 URL-Patterns mit Namespace 'personnel'
  - Integration in Haupt-URLs (flvs_project/urls.py)

#### 🔧 Geändert
- `flvs_project/urls.py`:
  - personnel URLs aktiviert

#### 🗄️ Datenbank
- Migration 0001_initial für personnel erstellt und angewendet
- 7 Indizes erstellt (personnel_number, last_name/first_name, is_active, person/is_active, expiry_date)

---

### 2025-10-03 - Permissions App implementiert

#### ✅ Hinzugefügt
- **Permission Mixins (4 Mixins, 75 Zeilen):**
  - `ModulePermissionMixin` - Prüft Modul-Zugriff
  - `ObjectPermissionMixin` - Object-Level Permissions
  - `BTMPermissionMixin` - BTM-Bereich Zugriff
  - `RoleRequiredMixin` - Rollen-basierter Zugriff

- **Permission Decorators (66 Zeilen):**
  - `@module_permission_required` - Modul-Zugriff für FBVs
  - `@role_required` - Rollen-Zugriff für FBVs
  - `@btm_permission_required` - BTM-Zugriff für FBVs

- **Template Tags (75 Zeilen):**
  - `has_module_permission` - Filter für Modul-Check
  - `has_role` - Filter für Rollen-Check
  - `can_add/change/delete` - Simple Tags für CRUD-Permissions
  - `is_btm_authorized` - Filter für BTM-Check

- **Management Command:**
  - `setup_roles` - Erstellt 7 Standard-Rollen
  - Rollen: Administrator, Modulverantwortlicher, Lagerverwalter, Werkstattmeister, BTM-Beauftragter, Wachleiter, Standard-Nutzer

#### 🔧 Geändert
- `flvs_project/settings/base.py`:
  - permissions.apps.PermissionsConfig zu LOCAL_APPS hinzugefügt

#### 🗄️ Datenbank
- 7 Standard-Rollen (Groups) erstellt via Management Command

---

### 2025-10-03 - Locations App vollständig implementiert

#### ✅ Hinzugefügt
- **Location Model (293 Zeilen):**
  - Hierarchisches Model mit django-mppt
  - 9 Location-Typen (Gebäude, Raum, Regal, Shelf, Box, Fahrzeug, Container, Outdoor, Sonstiges)
  - Vollständige Adressverwaltung
  - Kapazitäts- und Klimadaten (Temperatur-Bereich)
  - Zugriffskontrolle (restricted, access_instructions)
  - QR-Code Support für mobile Zugriffe
  - 14 Model-Methoden (get_full_path, get_address, can_be_deleted, etc.)

- **Admin-Interface (99 Zeilen):**
  - DraggableMPTTAdmin mit Drag & Drop Tree-Darstellung
  - Hierarchische Ansicht mit Einrückung
  - Filteroptionen (Typ, Aktiv, Klimatisiert, Zugriffsbeschränkung)
  - Suchfunktion (Name, Code, Beschreibung, Adresse)
  - Item-Count Display

- **Views (113 Zeilen):**
  - LocationListView (mit Suche und Filterung)
  - LocationDetailView (mit Hierarchie-Navigation)
  - LocationCreateView
  - LocationUpdateView
  - LocationDeleteView (mit can_be_deleted Check)

- **Forms (45 Zeilen):**
  - LocationForm mit TreeNodeChoiceField für Parent-Auswahl
  - Tailwind CSS Styling für alle Felder

- **URLs:**
  - 5 URL-Patterns mit Namespace 'locations'
  - Integration in Haupt-URLs

#### 🔧 Geändert
- `flvs_project/settings/base.py`:
  - django-mptt zu THIRD_PARTY_APPS hinzugefügt
  - locations.apps.LocationsConfig zu LOCAL_APPS hinzugefügt

#### 📦 Dependencies
- django-mptt==0.18.0 installiert
- django-js-asset==3.1.2 (Dependency von django-mptt)

#### 🗄️ Datenbank
- Migration 0001_initial für locations erstellt und angewendet

---

### 2025-10-03 - Core App vollständig implementiert

#### ✅ Hinzugefügt
- **Core Views:**
  - `DashboardView` - Haupt-Dashboard mit KPI-Übersicht
  - `ProfileView` - Benutzerprofil bearbeiten
  - `SettingsView` - Benutzereinstellungen
  - `global_search_view` - Globale Suche (HTMX)
  - `notifications_dropdown_view` - Benachrichtigungen-Dropdown (HTMX)
  - `notifications_list_view` - Vollständige Benachrichtigungsliste
  - `alerts_view` - Kritische Alerts/Warnungen
  - `inventory_critical_view` - Kritische Bestände Übersicht
  - `inspections_upcoming_view` - Anstehende Prüfungen
  - `activity_log_view` - Aktivitäts-Log
  - `tasks_toggle_view` - Tasks als erledigt markieren (HTMX)

- **Core Forms:**
  - `UserProfileForm` - Formular für Profil-Bearbeitung mit Tailwind CSS Styling
  - `UserSettingsForm` - Formular für Benutzer-Einstellungen
  - `PasswordChangeCustomForm` - Custom Passwort-Änderung

- **Core URLs:**
  - URL-Konfiguration mit Namespace 'core'
  - Integration von Django Authentication Views (Login, Logout, Password Reset)
  - HTMX-Endpoints für Search und Notifications

- **Context Processors:**
  - `notification_count` - Anzahl ungelesener Benachrichtigungen
  - `app_settings` - Projekt-Einstellungen für Templates
  - `user_permissions` - Benutzer-Berechtigungen für Template-Zugriff
  - `module_badges` - Badge-Counts für Module (Sidebar)

- **HTMX-Partials:**
  - `templates/core/partials/search_results.html` - Suchergebnisse
  - `templates/core/partials/notifications_dropdown.html` - Benachrichtigungen-Dropdown

- **Haupt-URLs:**
  - Integration von Core URLs in `flvs_project/urls.py`
  - Vorbereitung für zukünftige App-URLs (kommentiert)

#### 🔧 Geändert
- `flvs_project/settings/base.py`:
  - Context Processors registriert
  - Template-Konfiguration erweitert

#### 📝 Dokumentation
- `README.md` aktualisiert mit aktuellem Projektstatus
- `CLAUDE.md` aktualisiert mit Phase 1 Fortschritt
- `CHANGELOG.md` erstellt für Projekt-Historie

---

## 2025-10-03 - Basis-Templates erstellt

#### ✅ Hinzugefügt
- **Templates:**
  - `templates/base.html` - Haupt-Layout mit Header, Sidebar, Footer
  - `templates/dashboard.html` - Dashboard-Vorlage mit KPI-Karten
  - `templates/includes/sidebar_nav.html` - Hierarchische Navigation

- **Frontend-Integration:**
  - Tailwind CSS via CDN
  - HTMX 1.9.10 via CDN
  - Alpine.js 3.x via CDN
  - Custom Tailwind Config (Feuerwehr-rot als Primary Color)

---

## 2025-10-02 - Projekt-Setup

#### ✅ Hinzugefügt
- Django 5.x Projekt initialisiert
- PostgreSQL Datenbank konfiguriert
- Docker Compose Setup (web, db, redis)
- Core App erstellt mit:
  - Custom User Model (mit Feuerwehr-spezifischen Feldern)
  - Base Models (TimeStampedModel, AuditedModel, SoftDeleteModel)
  - Admin-Konfiguration

- **Dokumentation:**
  - README.md
  - CLAUDE.md
  - ARCHITECTURE.md
  - DATA_MODEL.md
  - PERMISSIONS.md

---

## Nächste Schritte

### Phase 1 (noch ausstehend):
- [ ] Permissions App vervollständigen
- [ ] Locations App erstellen
- [ ] Notifications App erstellen

### Phase 2:
- [ ] Personnel App
- [ ] Vehicles App
- [ ] Audit App

### Phase 3:
- [ ] Inventory Base Models
- [ ] Magazine App (erstes Lager-Modul)

---

*Format basierend auf [Keep a Changelog](https://keepachangelog.com/de/1.0.0/)*
