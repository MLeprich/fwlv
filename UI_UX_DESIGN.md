# FLVS UI/UX Design System

## 🎨 Design-Prinzipien

### 1. Klarheit vor Schönheit
- Funktion > Form
- Schnelle Orientierung unter Stress (Einsatzsituation!)
- Kontraste für gute Lesbarkeit
- Große Touch-Targets (min. 44x44px)

### 2. Konsistenz
- Einheitliche Icon-Sprache
- Gleiches Pattern für ähnliche Aktionen
- Vorhersehbare Navigation

### 3. Effizienz
- Minimal Clicks to Action
- Keyboard-Shortcuts
- Bulk-Actions
- Quick-Filters

### 4. Fehlertoleranz
- Confirmation für destruktive Aktionen
- Undo-Möglichkeiten wo sinnvoll
- Klare Fehlermeldungen

---

## 🎨 Farbpalette

### Primary (Feuerwehr-Rot)
```css
--primary-50:  #FEF2F2;
--primary-100: #FEE2E2;
--primary-200: #FECACA;
--primary-300: #FCA5A5;
--primary-400: #F87171;
--primary-500: #EF4444;  /* Haupt-Rot */
--primary-600: #DC2626;  /* Akzent-Rot */
--primary-700: #B91C1C;
--primary-800: #991B1B;
--primary-900: #7F1D1D;
```

### Status-Farben
```css
/* Success (Grün) */
--success: #10B981;

/* Warning (Gelb) */
--warning: #F59E0B;

/* Critical (Orange) */
--critical: #F97316;

/* Danger (Rot) */
--danger: #DC2626;

/* Info (Blau) */
--info: #3B82F6;
```

### Neutrals
```css
--gray-50:  #F9FAFB;  /* Hintergründe */
--gray-100: #F3F4F6;
--gray-200: #E5E7EB;  /* Borders */
--gray-300: #D1D5DB;
--gray-400: #9CA3AF;
--gray-500: #6B7280;
--gray-600: #4B5563;
--gray-700: #374151;
--gray-800: #1F2937;  /* Haupt-Text */
--gray-900: #111827;  /* Überschriften */
```

---

## 📐 Layout-Struktur

```
┌─────────────────────────────────────────────────────────────────┐
│  Header (64px fixed)                                             │
│  ┌──────┐ ┌─────────────────────┐  ┌─────┐ ┌──────┐ ┌────────┐│
│  │ Logo │ │  Global Search      │  │  🔔 │ │  ⚙️  │ │ Avatar ││
│  └──────┘ └─────────────────────┘  └─────┘ └──────┘ └────────┘│
├──────┬──────────────────────────────────────────────────────────┤
│      │  Breadcrumb Navigation                                   │
│      ├──────────────────────────────────────────────────────────┤
│      │  Context Actions (wenn vorhanden)                        │
│      │  [+ Neues Item] [📥 Import] [📤 Export] [🗑️ Bulk]      │
│  S   ├──────────────────────────────────────────────────────────┤
│  i   │                                                          │
│  d   │                                                          │
│  e   │              Main Content Area                           │
│  b   │                                                          │
│  a   │                                                          │
│  r   │                                                          │
│      │                                                          │
│  64  │                                                          │
│  px  │                                                          │
│      │                                                          │
│      │                                                          │
│      │                                                          │
└──────┴──────────────────────────────────────────────────────────┘
```

### Responsive Breakpoints
```css
/* Mobile First */
sm:  640px   /* Tablets */
md:  768px   /* Small Laptops */
lg:  1024px  /* Laptops */
xl:  1280px  /* Desktop */
2xl: 1536px  /* Large Desktop */
```

---

## 🧩 Sidebar-Konzept

### Zwei-State-Sidebar

**Minimiert (Default):**
- 64px breit
- Nur Icons (24x24px)
- Tooltips on hover
- Fixed position

**Erweitert (on hover/click):**
- 280px breit
- Icons + Labels + Badges
- Kategorien aufklappbar
- Smooth transition

### Modul-Kategorien

```
📦 Lager & Inventar
  ├─ 💊 Rettungsdienst
  ├─ 👕 Kleiderkammer
  ├─ 📦 Magazin
  ├─ 🧰 Ausrüstung
  └─ 💻 IT-Hardware

🚒 Fahrzeuge
  ├─ 🚙 Fahrzeugverwaltung
  ├─ 🔧 KFZ-Werkstatt
  ├─ 🧼 Desinfektion
  └─ ✅ Fahrzeugübernahme

👥 Personal & Verwaltung
  ├─ 👤 Personal
  ├─ 📋 Bestellwesen
  ├─ 📊 Inventur
  └─ 📄 Dokumente

🎯 Spezial-Bereiche
  ├─ 🧗 Höhenrettung
  └─ 🤿 Taucher

📈 Berichte & System
  ├─ 📊 Reports & KPIs
  ├─ 📺 Info-Monitore
  └─ ⚙️ System
```

---

## 🎯 Kachel-Layout für Module

### Dashboard-Kacheln (Startseite)

**Standard-Kachel:**
- 300x200px (min)
- Icon (48x48px) + Titel + Kurzbeschreibung
- Badge für Status/Anzahl
- Hover-Effect: Lift + Shadow

**Kachel-Typen:**

1. **Modul-Kachel** (Einstieg in Modul)
2. **Action-Kachel** (Quick-Action)
3. **Stat-Kachel** (KPI-Anzeige)
4. **Alert-Kachel** (Warnung/Hinweis)

### Modul-Übersicht Kacheln

**Innerhalb eines Moduls:**
- Untermenü als Kacheln
- z.B. in Rettungsdienst: "Medikamente", "Medizintechnik", "BTM"

---

## 📱 Component Library

### 1. Buttons

**Primary Button (Haupt-Aktion)**
```html
<button class="btn-primary">
  Speichern
</button>
```
- Feuerwehr-Rot Hintergrund
- Weiße Schrift
- Rounded corners (6px)
- Shadow on hover

**Secondary Button**
```html
<button class="btn-secondary">
  Abbrechen
</button>
```
- Grauer Border
- Grauer Text
- Transparent Background

**Danger Button**
```html
<button class="btn-danger">
  Löschen
</button>
```
- Dunkelrot
- Nur für destruktive Aktionen

### 2. Cards

**Standard Card**
```html
<div class="card">
  <div class="card-header">
    <h3>Titel</h3>
    <button>⋮</button>
  </div>
  <div class="card-body">
    Content
  </div>
  <div class="card-footer">
    Actions
  </div>
</div>
```
- Weißer Hintergrund
- Subtle shadow
- 12px border-radius
- 24px padding

### 3. Tables

**Responsive Table**
- Sticky Header
- Zebra-Striping
- Row-Hover
- Sort-Icons
- Action-Column (right)
- Bulk-Selection (Checkboxes)

### 4. Forms

**Form-Layout:**
- Labels oben (nicht links)
- Helper-Text unter Input
- Inline-Validation
- Error-States klar erkennbar (rot border)
- Success-States (grüner Haken)

### 5. Badges & Labels

**Status-Badges:**
```html
<span class="badge badge-success">Aktiv</span>
<span class="badge badge-warning">Niedrig</span>
<span class="badge badge-critical">Kritisch</span>
<span class="badge badge-danger">Abgelaufen</span>
```

### 6. Notifications/Toasts

**Toast-Position:** Top-Right
**Typen:**
- Success (Grün)
- Error (Rot)
- Warning (Gelb)
- Info (Blau)

**Auto-Dismiss:** 5 Sekunden (außer Errors)

---

## 🔍 Navigation Patterns

### Breadcrumb

```
Dashboard > Rettungsdienst > Medikamente > Aspirin 500mg
```

- Klickbar bis vorletztes Element
- Aktuelles Element in Grau (nicht klickbar)
- "/" oder ">" als Separator

### Context Actions Bar

**Nur anzeigen wenn relevant:**
- Bei Listen: "Neu", "Import", "Export", "Filter"
- Bei Detail-Seite: "Bearbeiten", "Löschen", "Duplizieren"
- Bei Bearbeitung: "Speichern", "Abbrechen"

**Position:** Direkt unter Breadcrumb, vor Main-Content

---

## 🎨 Icon-System

### Unicode Icons (Empfohlen für Module)

```
📦 Lager/Inventar
🚒 Feuerwehr
🚙 Fahrzeuge
💊 Medikamente
👕 Kleidung
🔧 Werkzeug
🧰 Ausrüstung
💻 IT-Hardware
🧼 Reinigung
🧗 Höhenrettung
🤿 Tauchen
👤 Person
📋 Dokumente
📊 Statistiken
⚙️ Einstellungen
🔔 Benachrichtigungen
🔍 Suche
✅ Bestätigt
⚠️ Warnung
❌ Fehler
➕ Hinzufügen
✏️ Bearbeiten
🗑️ Löschen
📥 Download/Import
📤 Upload/Export
🔄 Synchronisieren
🔒 Gesperrt
🔓 Entsperrt
📅 Kalender
🕐 Zeit
📍 Standort
```

**Vorteile Unicode:**
- Keine Icon-Library nötig
- Konsistent über alle Systeme
- Schnell ladend
- Gut erkennbar

**Für komplexere UI-Elemente: Heroicons**
- Ergänzend für kleinere Icons (16x16, 20x20)
- Pfeile, Menüs, etc.

---

## 📋 Layout-Vorlagen (Template-Typen)

### 1. Dashboard (Startseite)
- Personalisierte Kacheln basierend auf Rolle
- "Heute wichtig"-Bereich
- Quick-Stats
- Letzte Aktivitäten

### 2. Modul-Übersicht
- Kachel-Layout für Untermenüs
- z.B. Rettungsdienst: 3 Kacheln (Medikamente, Medizintechnik, BTM)

### 3. Listen-Ansicht
- Filter-Sidebar (links oder ausklappbar)
- Tabelle mit Pagination
- Bulk-Actions
- Quick-Search

### 4. Detail-Ansicht
- 2-Spalten Layout (Info + Sidebar mit Actions)
- Tabs für verschiedene Bereiche
- Timeline für Änderungshistorie

### 5. Formular-Ansicht
- Single-Column für einfache Formulare
- Multi-Column für komplexe Formulare
- Wizard-Style für mehrstufige Prozesse

### 6. Einstellungs-Ansicht (Section-basiert)
- **Pattern:** Sidebar-Navigation + Section-Content
- **Modularisierung:** Sub-Templates für jede Section
- **Alpine.js:** Client-side Section-Switching ohne Page-Reload
- **Struktur:**
  ```
  templates/<app>/<page>/
  ├── <page>.html          # Haupt-Template (Layout & Navigation)
  ├── section1.html        # Sub-Template für Section 1
  ├── section2.html        # Sub-Template für Section 2
  └── section3.html        # Sub-Template für Section 3
  ```
- **Beispiel:** Einstellungen-Seite mit 6 Sections (Account, Notifications, Appearance, Security, Privacy, System)

### 7. Kalender-Ansicht
- Für Prüfungen, Wartungen, Schichten
- Monats-, Wochen-, Tagesansicht

---

## 🧩 Template-Modularisierung Best Practices

### Wann Sub-Templates verwenden?

**✅ VERWENDEN bei:**
- Seiten mit 3+ Sections/Tabs
- Formularen mit >200 Zeilen Code
- Wiederverwendbaren Content-Blöcken
- Team-Entwicklung (paralleles Arbeiten)
- HTMX-Partial-Updates

**❌ NICHT VERWENDEN bei:**
- Einfachen Formularen (<100 Zeilen)
- Einmalig verwendeten Komponenten
- Performance-kritischen Bereichen (zu viele includes = overhead)

### Sub-Template Pattern

**Haupt-Template Verantwortung:**
- Layout-Struktur (Breadcrumb, Sidebar, Content-Area)
- Navigation (Tabs, Section-Buttons)
- Alpine.js State-Management
- CSS-Includes

**Sub-Template Verantwortung:**
- Section-spezifischer Content
- Forms mit Validierung
- x-show/x-cloak für Visibility
- Submit-Actions

**Naming Convention:**
```
Haupt: settings.html
Subs:  settings/account.html
       settings/notifications.html
```

### Vorteile der Modularisierung

1. **Wartbarkeit:** Änderungen nur in einer Datei
2. **Wiederverwendbarkeit:** Sections via HTMX nachladen
3. **Übersichtlichkeit:** Kleine, fokussierte Templates
4. **Team-Arbeit:** Keine Merge-Konflikte
5. **Testing:** Unit-Tests pro Section
6. **Performance:** Lazy-Loading möglich (HTMX)

---

## 🎯 Spezifische UX-Verbesserungen

### Schnelle Bestandsänderung
```
In Listen-Ansicht:
[Item-Name] [Bestand: 50] [➖ ➕]
```
- +/- Buttons für schnelle Anpassung
- Click öffnet Modal für Details

### Smart-Notifications
- Gruppiert nach Priorität
- Badge mit Anzahl
- Quick-Actions direkt in Notification
- "Alle als gelesen markieren"

### Quick-Add
- FAB (Floating Action Button) rechts unten
- Kontextsensitiv (je nach aktuellem Modul)
- Öffnet Slide-in Panel statt neuer Seite

### Keyboard-Shortcuts
```
Strg + K:     Globale Suche
Strg + N:     Neuer Eintrag
Strg + S:     Speichern
Strg + Z:     Rückgängig
ESC:          Modal schließen
```

### Bulk-Operations
- Checkbox-Spalte in Listen
- "Alle auswählen" in Header
- Bulk-Actions-Bar erscheint bei Auswahl
- Preview vor destruktiven Aktionen

---

## 📱 Mobile Considerations

### Responsive Sidebar
- Mobile: Bottom Navigation Bar (5 Haupt-Items)
- Drawer für vollständiges Menü

### Touch-Optimierung
- Min. 44x44px Touch-Targets
- Swipe-Gesten (z.B. Swipe-to-Delete in Listen)
- Pull-to-Refresh

### Offline-Fähigkeit
- Service Worker für Offline-Nutzung
- Fahrzeugübernahme muss offline funktionieren
- Sync wenn wieder online

---

## 🎨 Animation & Transitions

**Grundprinzip:** Smooth but not slow

### Empfohlene Transitions
```css
/* Hover-Effects */
transition: all 0.15s ease;

/* Page-Transitions */
transition: all 0.3s ease;

/* Sidebar-Expand */
transition: width 0.2s ease;

/* Modal Fade-in */
transition: opacity 0.2s ease;
```

### Micro-Interactions
- Button-Click: Leichtes "Drücken"
- Card-Hover: Subtle lift + shadow
- Success-Action: Grüner Checkmark erscheint
- Delete: Fade-out Animation

---

## ♿ Accessibility (A11Y)

### Pflicht-Kriterien
- WCAG 2.1 Level AA
- Keyboard-Navigation
- Screen-Reader kompatibel
- Farbkontrast mind. 4.5:1
- Focus-States klar erkennbar
- ARIA-Labels für Icons

### Focus-Management
- Sichtbarer Focus-Ring
- Logische Tab-Order
- Focus-Trap in Modals

---

## 🎯 Modul-spezifische Anpassungen

### BTM-Bereich (Extra-Sicherheit)
- **Dunklerer Rot-Ton** (#991B1B)
- **Warnung-Banner** "Betäubungsmittel-Bereich"
- **Session-Timer** sichtbar
- **Vier-Augen-Bestätigung** prominent

### Fahrzeugübernahme
- **Große Checkboxen** (Touch-optimiert)
- **Foto-Upload** prominent
- **Unterschrift-Feld** direkt sichtbar
- **Status-Ampel** (Rot/Gelb/Grün)

### Medikamente mit Ablaufdatum
- **Farbcodierung:**
  - Grün: >3 Monate
  - Gelb: <3 Monate
  - Orange: <1 Monat
  - Rot: Abgelaufen

---

## 🎨 Tailwind CSS Configuration

### Custom Colors (tailwind.config.js)

```javascript
module.exports = {
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#FEF2F2',
          100: '#FEE2E2',
          200: '#FECACA',
          300: '#FCA5A5',
          400: '#F87171',
          500: '#EF4444',
          600: '#DC2626',
          700: '#B91C1C',
          800: '#991B1B',
          900: '#7F1D1D',
        },
      },
    },
  },
}
```

---

## 📋 Template-Implementierungs-Status

### ✅ Implementiert
- **Dashboard** (`templates/dashboard.html`) - KPI-Cards, Module-Tiles, Activity Timeline
- **Profil** (`templates/core/profile.html`) - 320px Sidebar + 4 Tabs
- **Einstellungen** (`templates/core/settings.html`) - **Modularisiert mit 6 Sub-Templates**
  - ✅ `templates/core/settings/account.html`
  - ✅ `templates/core/settings/notifications.html`
  - ✅ `templates/core/settings/appearance.html`
  - ✅ `templates/core/settings/security.html`
  - ✅ `templates/core/settings/privacy.html`
  - ✅ `templates/core/settings/system.html`

### 🔜 Geplant mit Sub-Templates
- **Personal-Detail** - 6 Tabs (Übersicht, Daten, Quali, Prüfungen, Kleidung, Pflichtstunden)
- **Fahrzeugverwaltung** - Multi-Step-Forms
- **Dashboard-Builder** - Widget-Typen als Sub-Templates
- **Medikamente-Detail** - 5 Tabs (Basis, Bestand, Chargen, Historie, Dokumente)

---

*Diese Datei ist Teil der SSOT (Single Source of Truth) für das FLVS-Projekt.*
*Letzte Aktualisierung: 2025-10-04*
