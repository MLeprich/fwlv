# 🚒 Fahrzeugübernahme Modul - Entwicklungs-Roadmap

**Projekt:** FLVS - Fahrzeugübernahme mit digitaler Dokumentation
**Status:** Backend fertig, Frontend zu implementieren
**Geschätzte Gesamtdauer:** 12-15 Arbeitstage
**Erstellt:** 21. Oktober 2025

---

## 📋 Übersicht

Das Fahrzeugübernahme-Modul ermöglicht die digitale Dokumentation von Fahrzeugübergaben mit:
- Flexiblen JSON-basierten Checklisten-Vorlagen
- 360° Foto-Dokumentation
- Mängelerfassung und -tracking
- Digitalen Bestätigungen
- Verschiedenen Übergabetypen (Wachablösung, Einsatz, Werkstatt, etc.)

---

## 🎯 Entwicklungsphasen

### **Phase 1: Grundlagen & Checklisten-Verwaltung** (3-4 Tage)

#### 1.1 Checklisten-Template System (Tag 1-2)
**Priorität:** 🔴 HOCH (Grundlage für alles andere)

**Datenmodell erweitern:**
```python
# vehicle_handover/models.py - NEU hinzufügen

class ChecklistTemplate(TimeStampedModel):
    """
    Wiederverwendbare Checklisten-Vorlage (JSON-basiert)
    """
    name = models.CharField(max_length=200, verbose_name='Template-Name')
    description = models.TextField(blank=True)

    # Zuordnung zu Fahrzeugtypen
    vehicle_types = models.JSONField(
        default=list,
        help_text='Liste von vehicle_type codes, z.B. ["lf", "dlk", "hlf"]'
    )

    # JSON-Struktur der Checkliste
    checklist_items = models.JSONField(
        default=dict,
        help_text='JSON mit Kategorien und Items'
    )

    # Beispiel-Struktur:
    # {
    #   "categories": [
    #     {
    #       "name": "Fahrzeugpapiere",
    #       "order": 1,
    #       "items": [
    #         {
    #           "name": "Fahrzeugschein",
    #           "requires_serial": false,
    #           "order": 1
    #         },
    #         {
    #           "name": "Prüfplaketten",
    #           "requires_serial": false,
    #           "order": 2
    #         }
    #       ]
    #     },
    #     {
    #       "name": "Beladung",
    #       "order": 2,
    #       "items": [
    #         {
    #           "name": "Atemschutzgeräte",
    #           "requires_serial": true,
    #           "quantity": 4,
    #           "order": 1
    #         }
    #       ]
    #     }
    #   ]
    # }

    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)

    # Verwendungsstatistik
    usage_count = models.PositiveIntegerField(default=0)
    last_used = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'vehicle_handover_checklist_template'
        verbose_name = 'Checklisten-Vorlage'
        verbose_name_plural = 'Checklisten-Vorlagen'
        ordering = ['name']
```

**To-Do:**
- [x] Datenmodell `ChecklistTemplate` erstellen
- [ ] Migration erstellen und ausführen
- [ ] Admin-Interface für Templates
- [ ] JSON-Schema-Validierung implementieren

**Dateien zu erstellen:**
- `vehicle_handover/models.py` (erweitern)
- `vehicle_handover/migrations/000X_add_checklist_template.py`
- `vehicle_handover/validators.py` (JSON-Schema Validierung)

---

#### 1.2 Checklisten-Verwaltungs-UI (Tag 2-3)

**Frontend-Seiten:**

1. **Template-Liste** (`/vehicle_handover/templates/`)
   - Übersicht aller Vorlagen
   - Filter nach Fahrzeugtyp
   - Verwendungsstatistik anzeigen
   - Aktiv/Inaktiv Toggle

2. **Template-Editor** (`/vehicle_handover/templates/create/` & `/edit/<id>/`)
   - JSON-Editor mit Syntax-Highlighting
   - Live-Vorschau der Checkliste
   - Drag & Drop für Kategorien/Items
   - Fahrzeugtyp-Zuordnung (Multi-Select)

**Technologie:**
- **JSON-Editor:** Monaco Editor (wie VS Code) ODER CodeMirror
- **Alternative:** Formular-basierter Editor (Kategorie hinzufügen → Items hinzufügen)

**To-Do:**
- [ ] Views erstellen (`ChecklistTemplateListView`, `CreateView`, `UpdateView`, `DeleteView`)
- [ ] Forms erstellen (`ChecklistTemplateForm`)
- [ ] Templates erstellen:
  - `vehicle_handover/template_list.html`
  - `vehicle_handover/template_form.html`
  - `vehicle_handover/template_preview_partial.html`
- [ ] JSON-Editor integrieren (Monaco oder Formular)
- [ ] AJAX-Preview-Endpoint für Live-Vorschau

**Dateien zu erstellen:**
- `vehicle_handover/views.py` (neu)
- `vehicle_handover/forms.py` (neu)
- `templates/vehicle_handover/template_list.html`
- `templates/vehicle_handover/template_form.html`
- `templates/vehicle_handover/template_detail.html`
- `static/js/checklist_editor.js` (optional, für erweiterte Features)

---

#### 1.3 URLs & Navigation (Tag 3)

**URL-Struktur:**
```python
# vehicle_handover/urls.py

urlpatterns = [
    # Dashboard
    path('', views.HandoverDashboardView.as_view(), name='dashboard'),

    # Checklisten-Templates
    path('templates/', views.ChecklistTemplateListView.as_view(), name='template_list'),
    path('templates/create/', views.ChecklistTemplateCreateView.as_view(), name='template_create'),
    path('templates/<int:pk>/', views.ChecklistTemplateDetailView.as_view(), name='template_detail'),
    path('templates/<int:pk>/edit/', views.ChecklistTemplateUpdateView.as_view(), name='template_update'),
    path('templates/<int:pk>/delete/', views.ChecklistTemplateDeleteView.as_view(), name='template_delete'),
    path('templates/<int:pk>/preview/', views.template_preview_ajax, name='template_preview'),
    path('templates/<int:pk>/duplicate/', views.duplicate_template, name='template_duplicate'),

    # Übergaben (später)
    path('handovers/', views.HandoverListView.as_view(), name='handover_list'),
    path('handovers/create/', views.HandoverCreateView.as_view(), name='handover_create'),
    # ... weitere URLs
]
```

**To-Do:**
- [ ] URLs definieren
- [ ] Sidebar-Link aktualisieren (von `#` zu `vehicle_handover:dashboard`)
- [ ] Breadcrumb-Navigation
- [ ] Berechtigungen definieren

---

### **Phase 2: Übergabe-Workflow** (4-5 Tage)

#### 2.1 Dashboard & Übersicht (Tag 4)

**Dashboard-Features:**
- Letzte Übergaben (Timeline)
- Offene Übergaben (noch nicht abgeschlossen)
- Fahrzeuge mit ausstehenden Mängeln
- Statistiken (Übergaben pro Monat, Mängel-Verteilung)
- Quick-Actions (Neue Übergabe starten)

**To-Do:**
- [ ] Dashboard-View mit Context-Daten
- [ ] Dashboard-Template mit KPI-Karten
- [ ] Statistik-Queries optimieren

**Dateien:**
- `templates/vehicle_handover/dashboard.html`
- `vehicle_handover/views.py` (HandoverDashboardView)

---

#### 2.2 Übergabe erstellen - Wizard (Tag 4-5)

**Multi-Step Wizard:**

**Schritt 1: Grunddaten**
- Fahrzeug auswählen (durchsuchbar mit Alpine.js)
- Übergabeart wählen
- Übergeber/Empfänger
- Standort
- Datum/Uhrzeit

**Schritt 2: Fahrzeugdaten**
- KM-Stand
- Tankfüllung (Slider 0-100%)
- Sauberkeit Innen/Außen (Star-Rating)

**Schritt 3: Checkliste**
- Template auswählen (basierend auf Fahrzeugtyp)
- Items abhaken
- Seriennummern erfassen (wenn erforderlich)
- Fehlende/defekte Items markieren

**Schritt 4: Fotos (optional)**
- 360°-Fotos hochladen
- Drag & Drop
- Auto-Kategorisierung nach Foto-Typ

**Schritt 5: Mängel (wenn vorhanden)**
- Mängel erfassen
- Schweregrad festlegen
- Fotos zuordnen

**Schritt 6: Bestätigung**
- Zusammenfassung anzeigen
- Digitale Bestätigungen (Checkboxen)
- PDF-Export-Option

**Implementierung:**
- **Option A:** Session-basierter Wizard (Django FormWizard)
- **Option B:** Single-Page mit Alpine.js Tabs/Steps
- **Empfehlung:** Option B (bessere UX, weniger Server-Requests)

**To-Do:**
- [ ] Wizard-View implementieren
- [ ] Forms für jeden Schritt
- [ ] Template mit Tab-Navigation
- [ ] Auto-Save in Session (bei Seitenwechsel)
- [ ] Foto-Upload mit Preview
- [ ] PDF-Export-Funktion

**Dateien:**
- `vehicle_handover/views.py` (HandoverCreateView)
- `vehicle_handover/forms.py` (HandoverForm, ChecklistItemFormSet, DefectFormSet)
- `templates/vehicle_handover/handover_create.html`
- `templates/vehicle_handover/partials/handover_step_*.html`

---

#### 2.3 Übergabe-Liste & Detail (Tag 5-6)

**Listen-View:**
- Filterung (Fahrzeug, Datum, Status, Übergeber/Empfänger)
- Sortierung
- Status-Badges
- Quick-Actions (Anzeigen, Bearbeiten, PDF)

**Detail-View:**
- Alle Übergabe-Daten
- Checkliste mit Status
- Foto-Galerie (mit Lightbox)
- Mängel-Liste mit Status
- Timeline (Erstellung, Bestätigungen, Änderungen)
- PDF-Export-Button

**To-Do:**
- [ ] ListView mit Filterform
- [ ] DetailView mit Tabs
- [ ] PDF-Template erstellen (WeasyPrint)
- [ ] Foto-Lightbox (z.B. PhotoSwipe)

**Dateien:**
- `vehicle_handover/views.py` (HandoverListView, HandoverDetailView)
- `templates/vehicle_handover/handover_list.html`
- `templates/vehicle_handover/handover_detail.html`
- `templates/vehicle_handover/handover_pdf.html`

---

### **Phase 3: Mängel-Management** (2-3 Tage)

#### 3.1 Mängel-Verwaltung (Tag 7)

**Features:**
- Mängel-Übersicht (alle offenen/geschlossenen)
- Nach Fahrzeug/Schweregrad filtern
- Mangel bearbeiten/beheben
- Reparatur-Notizen
- Kosten erfassen
- Verknüpfung zu Werkstatt-Aufträgen (später)

**To-Do:**
- [ ] DefectListView (mit Filter)
- [ ] DefectUpdateView (Mangel als behoben markieren)
- [ ] Dashboard-Integration (offene Mängel)

**Dateien:**
- `vehicle_handover/views.py` (DefectListView, DefectUpdateView)
- `templates/vehicle_handover/defect_list.html`
- `templates/vehicle_handover/defect_form.html`

---

### **Phase 4: Erweiterte Features** (2-3 Tage)

#### 4.1 Foto-Upload & Verwaltung (Tag 8)

**Features:**
- Multi-Upload (Drag & Drop)
- Automatische Komprimierung (Pillow)
- 360°-Ansicht erstellen
- EXIF-Daten auslesen (GPS, Datum)
- Foto-Kategorien zuordnen

**To-Do:**
- [ ] FileUpload-Handler
- [ ] Image-Processing (Resize, Compress)
- [ ] EXIF-Extraktion
- [ ] 360°-Viewer (z.B. Three.js oder einfacher Carousel)

**Dateien:**
- `vehicle_handover/utils.py` (Image-Processing)
- `vehicle_handover/views.py` (PhotoUploadView)
- `templates/vehicle_handover/photo_gallery.html`
- `static/js/photo_uploader.js`

---

#### 4.2 Benachrichtigungen & Erinnerungen (Tag 9)

**Features:**
- Benachrichtigung bei neuer Übergabe (Empfänger)
- Erinnerung bei offenen Übergaben (nicht bestätigt)
- Warnung bei kritischen Mängeln
- E-Mail-Benachrichtigungen (optional)

**To-Do:**
- [ ] Signal-Handler für Benachrichtigungen
- [ ] Integration in bestehendes Notification-System
- [ ] E-Mail-Templates (optional)

**Dateien:**
- `vehicle_handover/signals.py` (neu)
- `templates/emails/handover_notification.html` (optional)

---

#### 4.3 Berichte & Statistiken (Tag 10)

**Features:**
- Monatsbericht (Anzahl Übergaben, Mängel)
- Fahrzeug-Historie (alle Übergaben)
- Mängel-Statistik (nach Kategorie, Schweregrad)
- Export (Excel, CSV)

**To-Do:**
- [ ] Report-Views
- [ ] Chart-Integration (Chart.js)
- [ ] Excel-Export (openpyxl)

**Dateien:**
- `vehicle_handover/views.py` (ReportView)
- `templates/vehicle_handover/reports.html`

---

### **Phase 5: Testing & Polishing** (2 Tage)

#### 5.1 Testing (Tag 11)

**Test-Coverage:**
- [ ] Model-Tests (Validierung, Save-Logic)
- [ ] View-Tests (Permissions, GET/POST)
- [ ] Form-Tests (Validierung)
- [ ] Integration-Tests (Wizard-Flow)

**Dateien:**
- `vehicle_handover/tests/test_models.py`
- `vehicle_handover/tests/test_views.py`
- `vehicle_handover/tests/test_forms.py`

---

#### 5.2 UI/UX Polishing (Tag 12)

**To-Do:**
- [ ] Responsive Design testen (Mobile)
- [ ] Loading-Spinner bei langen Operationen
- [ ] Error-Handling verbessern
- [ ] Tooltips/Hilfetexte ergänzen
- [ ] Keyboard-Navigation
- [ ] Accessibility-Check (ARIA-Labels)

---

### **Phase 6: Dokumentation & Deployment** (1 Tag)

#### 6.1 Dokumentation (Tag 12)

**To-Do:**
- [ ] User-Guide (Markdown)
- [ ] Admin-Anleitung
- [ ] API-Dokumentation (falls REST-Endpoints)
- [ ] CLAUDE.md aktualisieren

**Dateien:**
- `docs/VEHICLE_HANDOVER_USER_GUIDE.md`
- `docs/VEHICLE_HANDOVER_ADMIN_GUIDE.md`

---

#### 6.2 Deployment (Tag 12)

**To-Do:**
- [ ] Migrations auf Produktion ausführen
- [ ] Static-Files sammeln
- [ ] Server neu starten
- [ ] Smoke-Tests (Alle Seiten aufrufen)
- [ ] Backup vor Deployment

---

## 📊 Detaillierte Aufgabenliste

### 🔴 Priorität HOCH (MVP - Minimum Viable Product)

1. **Checklisten-Template System**
   - [ ] Model `ChecklistTemplate` (1h)
   - [ ] Migration (15min)
   - [ ] Admin-Interface (30min)
   - [ ] JSON-Schema-Validator (1h)

2. **Template-Verwaltung UI**
   - [ ] ListView (1h)
   - [ ] CreateView mit JSON-Editor (3h)
   - [ ] UpdateView (2h)
   - [ ] DeleteView (30min)
   - [ ] Preview-Funktion (1h)

3. **Übergabe-Workflow**
   - [ ] Dashboard (2h)
   - [ ] CreateView - Grunddaten (2h)
   - [ ] CreateView - Fahrzeugdaten (1h)
   - [ ] CreateView - Checkliste (3h)
   - [ ] CreateView - Zusammenfassung & Save (2h)
   - [ ] ListView (2h)
   - [ ] DetailView (2h)

4. **Mängel-Basis**
   - [ ] Mängel erfassen im Wizard (2h)
   - [ ] DefectListView (1h)

**Gesamt MVP: ~8 Tage**

---

### 🟡 Priorität MITTEL (Nice to have)

5. **Foto-Upload**
   - [ ] Multi-Upload (2h)
   - [ ] Image-Processing (1h)
   - [ ] Galerie-View (2h)

6. **PDF-Export**
   - [ ] Template erstellen (2h)
   - [ ] WeasyPrint-Integration (1h)

7. **Benachrichtigungen**
   - [ ] Signal-Handler (1h)
   - [ ] Integration (1h)

**Gesamt Mittel: ~3 Tage**

---

### 🟢 Priorität NIEDRIG (Später)

8. **Erweiterte Features**
   - [ ] 360°-Viewer (4h)
   - [ ] E-Mail-Benachrichtigungen (2h)
   - [ ] Excel-Export (2h)
   - [ ] Statistiken/Charts (3h)

9. **Mobile-App** (separates Projekt)
   - [ ] Native App für Foto-Upload
   - [ ] Offline-Fähigkeit

**Gesamt Niedrig: ~2 Tage**

---

## 🛠️ Technologie-Stack

### Backend
- **Framework:** Django 5.x
- **Models:** Bereits vorhanden
- **Forms:** Django Forms + Formsets
- **PDF:** WeasyPrint
- **Image-Processing:** Pillow

### Frontend
- **CSS:** Tailwind CSS (bereits vorhanden)
- **JS-Framework:** Alpine.js (bereits vorhanden)
- **JSON-Editor:** Monaco Editor ODER CodeMirror
- **Foto-Upload:** Dropzone.js oder natives Drag & Drop
- **Lightbox:** PhotoSwipe
- **Charts:** Chart.js (optional)

### Storage
- **Fotos:** Media-Files (lokales Filesystem oder S3)
- **Datenbank:** PostgreSQL

---

## 📅 Zeitplan (Beispiel)

### Sprint 1: Checklisten-System (Woche 1)
- **Tag 1-2:** Datenmodell + Migration
- **Tag 3-4:** Template-Verwaltung UI
- **Tag 5:** URLs, Navigation, Testing

### Sprint 2: Übergabe-Workflow (Woche 2)
- **Tag 6:** Dashboard
- **Tag 7-8:** Übergabe-Wizard
- **Tag 9-10:** Listen & Detail-Views

### Sprint 3: Erweiterte Features (Woche 3)
- **Tag 11:** Mängel-Verwaltung
- **Tag 12:** Foto-Upload
- **Tag 13:** PDF-Export
- **Tag 14:** Benachrichtigungen
- **Tag 15:** Testing & Deployment

---

## 🎨 UI/UX Mockup-Ideen

### Checklisten-Template Editor

**Option A: JSON-Editor (für Power-User)**
```
┌─────────────────────────────────────────────────────┐
│ Template: LF 10/6 Standardbeladung                  │
├─────────────────────────────────────────────────────┤
│ [Tab: JSON Editor] [Tab: Vorschau]                  │
│                                                      │
│ {                                                    │
│   "categories": [                                    │
│     {                                                │
│       "name": "Fahrzeugpapiere",                     │
│       "order": 1,                                    │
│       "items": [...]                                 │
│     }                                                │
│   ]                                                  │
│ }                                                    │
│                                                      │
│ [✓ Validierung OK]                                   │
│                                                      │
│ [Abbrechen] [Speichern]                             │
└─────────────────────────────────────────────────────┘
```

**Option B: Formular-Editor (für normale User)**
```
┌─────────────────────────────────────────────────────┐
│ Template: LF 10/6 Standardbeladung                  │
├─────────────────────────────────────────────────────┤
│                                                      │
│ ┌─ Kategorie: Fahrzeugpapiere ───────────────────┐ │
│ │ ☰ [Kategorie nach oben]                         │ │
│ │                                                  │ │
│ │ Items:                                           │ │
│ │  ☐ Fahrzeugschein         [Bearbeiten] [×]      │ │
│ │  ☐ Prüfplaketten          [Bearbeiten] [×]      │ │
│ │  [+ Neues Item]                                  │ │
│ │                                                  │ │
│ │ [Kategorie löschen]                              │ │
│ └──────────────────────────────────────────────────┘ │
│                                                      │
│ [+ Neue Kategorie]                                   │
│                                                      │
│ [Abbrechen] [Speichern]                             │
└─────────────────────────────────────────────────────┘
```

**Empfehlung:** Option B für bessere Usability

---

### Übergabe-Wizard

```
┌─────────────────────────────────────────────────────┐
│ Neue Fahrzeugübergabe                                │
├─────────────────────────────────────────────────────┤
│                                                      │
│ [1 Grunddaten] → [2 Fahrzeugdaten] → [3 Checkliste] │
│    → [4 Fotos] → [5 Mängel] → [6 Bestätigung]       │
│                                                      │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                      │
│ Schritt 1: Grunddaten                                │
│                                                      │
│ Fahrzeug: [Durchsuchbares Dropdown ▾]               │
│           🔍 Funkrufname, Kennzeichen...            │
│                                                      │
│ Übergabeart: [Wachablösung ▾]                       │
│                                                      │
│ Von: [Person auswählen ▾]                            │
│ An:  [Person auswählen ▾]                            │
│                                                      │
│ Datum/Zeit: [21.10.2025 14:30]                      │
│                                                      │
│                             [Abbrechen] [Weiter →]   │
└─────────────────────────────────────────────────────┘
```

---

## 🔒 Berechtigungen

### Permission-Matrix

| Aktion | Wachleiter | Fahrzeugverwalter | Admin |
|--------|-----------|-------------------|-------|
| Übergabe durchführen | ✅ | ✅ | ✅ |
| Übergabe anzeigen | ✅ (eigene) | ✅ (alle) | ✅ |
| Übergabe bearbeiten | ❌ | ✅ (24h) | ✅ |
| Übergabe löschen | ❌ | ❌ | ✅ |
| Template anzeigen | ✅ | ✅ | ✅ |
| Template erstellen | ❌ | ✅ | ✅ |
| Template bearbeiten | ❌ | ✅ | ✅ |
| Template löschen | ❌ | ❌ | ✅ |
| Mängel anzeigen | ✅ | ✅ | ✅ |
| Mängel als behoben markieren | ❌ | ✅ | ✅ |

**Django Permissions:**
```python
# vehicle_handover/models.py

class Meta:
    permissions = [
        ('manage_templates', 'Can manage checklist templates'),
        ('view_all_handovers', 'Can view all handovers'),
        ('edit_handover', 'Can edit handovers within 24h'),
        ('resolve_defects', 'Can mark defects as resolved'),
    ]
```

---

## 📝 Offene Fragen / Entscheidungen

1. **JSON-Editor vs. Formular-Editor für Templates?**
   - ✅ **Empfehlung:** Formular-Editor (bessere UX)
   - Alternative: Beide Optionen anbieten (Tab-Switch)

2. **Session-Wizard vs. Single-Page-Wizard?**
   - ✅ **Empfehlung:** Single-Page mit Alpine.js (moderne UX)

3. **Foto-Upload: Sofort oder am Ende?**
   - ✅ **Empfehlung:** Optional in Schritt 4 (flexibler)

4. **PDF-Export: On-demand oder automatisch bei Abschluss?**
   - ✅ **Empfehlung:** On-demand (spart Speicherplatz)

5. **E-Mail-Benachrichtigungen aktiv oder opt-in?**
   - ✅ **Empfehlung:** Opt-in (User-Einstellungen)

6. **Mobile-App notwendig?**
   - ⏸️ **Entscheidung:** Später (Phase 2), zunächst Responsive Web

---

## 🚀 Quick Start für Entwicklung

### Schritt 1: Migration erstellen
```bash
cd /var/www/lager.resqware.de
source venv/bin/activate
python manage.py makemigrations vehicle_handover
python manage.py migrate
```

### Schritt 2: Beispiel-Template erstellen (via Django Shell)
```python
python manage.py shell

from vehicle_handover.models import ChecklistTemplate

template = ChecklistTemplate.objects.create(
    name="LF 10/6 Standard",
    description="Standard-Checkliste für LF 10/6",
    vehicle_types=["lf"],
    checklist_items={
        "categories": [
            {
                "name": "Fahrzeugpapiere",
                "order": 1,
                "items": [
                    {"name": "Fahrzeugschein", "requires_serial": False, "order": 1},
                    {"name": "Prüfplaketten", "requires_serial": False, "order": 2}
                ]
            },
            {
                "name": "Beladung",
                "order": 2,
                "items": [
                    {"name": "Atemschutzgeräte", "requires_serial": True, "quantity": 4, "order": 1}
                ]
            }
        ]
    }
)
```

### Schritt 3: Erste View erstellen
```bash
# vehicle_handover/views.py bearbeiten
nano vehicle_handover/views.py
```

---

## 📚 Referenzen & Inspiration

### Ähnliche Systeme
- **Fahrzeug-Checklisten Apps:** Fleetio, Samsara
- **Übergabeprotokolle:** DGUV V3 Prüfprotokolle
- **JSON-Editoren:** JSONForms.io, React JSON Schema Form

### Django-Packages
- `django-formtools` - Wizard-Views
- `weasyprint` - PDF-Generation
- `pillow` - Image-Processing
- `django-cleanup` - Auto-Delete orphaned files

---

## ✅ Definition of Done

Eine Feature ist "Done" wenn:
- [ ] Code geschrieben und funktioniert
- [ ] Tests geschrieben (min. 80% Coverage)
- [ ] UI responsive (Mobile/Tablet/Desktop)
- [ ] Berechtigungen implementiert
- [ ] Dokumentation aktualisiert
- [ ] Code-Review durchgeführt
- [ ] Auf Staging getestet
- [ ] User-Feedback eingeholt (bei UI)

---

## 🎯 Success Metrics

### MVP (Phase 1-2)
- ✅ 5 Checklisten-Templates erstellt
- ✅ 10 erfolgreiche Übergaben durchgeführt
- ✅ 0 kritische Bugs
- ✅ Ladezeit < 2s

### Full Release
- ✅ 50+ Übergaben pro Monat
- ✅ 95%+ User-Zufriedenheit
- ✅ Mängel-Tracking funktioniert
- ✅ PDF-Export genutzt (>30%)

---

**Erstellt am:** 21. Oktober 2025
**Autor:** Claude Code
**Nächster Review:** Nach Phase 1 (Checklisten-System)

