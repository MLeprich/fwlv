# UI-Strukturen - Visuelle Beschreibungen (SSOT für Template-Gestaltung)

> **Stand:** 2025-10-03
> **Version:** 1.1
> **Zweck:** Single Source of Truth für alle UI-Template-Strukturen in FLVS

---

## 🎨 CSS Layout-Implementation

### Custom CSS für Zwei-Spalten-Layouts

Für konsistente Zwei-Spalten-Layouts wird **Custom CSS** verwendet (nicht Tailwind Grid):

**Datei:** `/static/css/custom.css`

```css
/* Settings Layout: Sidebar 280px + Content flex */
@media (min-width: 1024px) {
    .settings-layout {
        display: flex;
        flex-direction: row;
        gap: 1.5rem;
    }
    .settings-layout .sidebar-nav {
        width: 280px;
        flex-shrink: 0;
    }
    .settings-layout .content-area {
        flex: 1;
        min-width: 0;
    }
}

/* Profile Layout: Sidebar 320px + Content flex */
@media (min-width: 1024px) {
    .profile-layout {
        display: flex;
        flex-direction: row;
        gap: 1.5rem;
    }
    .profile-layout .sidebar-profile {
        width: 320px;
        flex-shrink: 0;
    }
    .profile-layout .content-main {
        flex: 1;
        min-width: 0;
    }
}

/* Mobile: Stack vertikal */
@media (max-width: 1023px) {
    .settings-layout,
    .profile-layout {
        display: flex;
        flex-direction: column;
        gap: 1.5rem;
    }
    /* Alle Container volle Breite auf Mobile */
    .settings-layout .sidebar-nav,
    .settings-layout .content-area,
    .profile-layout .sidebar-profile,
    .profile-layout .content-main {
        width: 100%;
    }
}
```

**Template-Verwendung:**
```django
<div class="settings-layout">
    <div class="sidebar-nav">...</div>
    <div class="content-area">...</div>
</div>
```

**Wichtig:**
- ❌ **NICHT** verwenden: `grid-cols-[280px_1fr]` (Tailwind unterstützt diese Syntax nicht zuverlässig)
- ❌ **NICHT** verwenden: `lg:w-64 lg:flex-1` (funktioniert nicht konsistent)
- ✅ **VERWENDEN**: Custom CSS-Klassen mit festen Pixel-Breiten
- ✅ Custom CSS in `base.html` einbinden: `<link rel="stylesheet" href="{% static 'css/custom.css' %}">`

---

## 📐 Grundlegende Layout-Patterns

### Pattern 1: Zwei-Spalten Layout (70/30)
```
┌─────────────────────────────────────────────────────┐
│ Header (Breadcrumb, Titel, Actions)                 │
├─────────────────────────────────────────────────────┤
│                                                     │
│ ┌───────────────────────────┐  ┌────────────────┐ │
│ │                           │  │                │ │
│ │   Haupt-Content (70%)     │  │ Sidebar (30%)  │ │
│ │                           │  │                │ │
│ │                           │  │                │ │
│ └───────────────────────────┘  └────────────────┘ │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### Pattern 2: Mit Filter-Sidebar (20/80)
```
┌─────────────────────────────────────────────────────┐
│ Header + Toolbar                                     │
├─────────────────────────────────────────────────────┤
│ ┌────────┐ ┌──────────────────────────────────────┐│
│ │        │ │                                      ││
│ │ Filter │ │   Content (Liste, Tabelle, Grid)    ││
│ │ (20%)  │ │                                      ││
│ │        │ │                                      ││
│ └────────┘ └──────────────────────────────────────┘│
└─────────────────────────────────────────────────────┘
```

### Pattern 3: Vollbreite mit Tabs
```
┌─────────────────────────────────────────────────────┐
│ Header                                               │
├─────────────────────────────────────────────────────┤
│ [Tab 1] [Tab 2] [Tab 3] [Tab 4]                    │
├─────────────────────────────────────────────────────┤
│                                                     │
│            Tab-Content (Vollbreite)                 │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## 🏠 MODUL-DASHBOARD

### Struktur
```
┌─────────────────────────────────────────────────────┐
│ Breadcrumb: Dashboard > Modul-Name                  │
├─────────────────────────────────────────────────────┤
│                                                     │
│ ┌─────────────────────────────────────────────────┐│
│ │ 🎯 Modul-Header (Gradient-Hintergrund)         ││
│ │ Icon (groß) + Titel + Beschreibung             ││
│ └─────────────────────────────────────────────────┘│
│                                                     │
│ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐      │
│ │Stat 1  │ │Stat 2  │ │Stat 3  │ │Stat 4  │      │
│ │Zahl    │ │Zahl    │ │Zahl    │ │Zahl    │      │
│ │Label   │ │Label   │ │Label   │ │Label   │      │
│ └────────┘ └────────┘ └────────┘ └────────┘      │
│                                                     │
│ Bereiche (Hauptmenü-Kacheln):                      │
│ ┌──────────┐ ┌──────────┐ ┌──────────┐            │
│ │ 💊       │ │ 🏥       │ │ 🔒       │            │
│ │ Icon     │ │ Icon     │ │ Icon     │            │
│ │          │ │          │ │          │            │
│ │ Titel    │ │ Titel    │ │ Titel    │            │
│ │ Beschr.  │ │ Beschr.  │ │ Beschr.  │            │
│ │ Badge    │ │ Badge    │ │ Badge    │            │
│ │ → Link   │ │ → Link   │ │ → Link   │            │
│ └──────────┘ └──────────┘ └──────────┘            │
│                                                     │
│ ⚠️ Kritische Meldungen (wenn vorhanden):           │
│ ┌─────────────────────────────────────────────────┐│
│ │ • Meldung 1 mit Link                           ││
│ │ • Meldung 2 mit Link                           ││
│ └─────────────────────────────────────────────────┘│
│                                                     │
│ Quick Actions (optional):                          │
│ ┌────────┐ ┌────────┐ ┌────────┐                 │
│ │Action 1│ │Action 2│ │Action 3│                 │
│ └────────┘ └────────┘ └────────┘                 │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### Elemente-Details:

**Modul-Header:**
- Gradient-Hintergrund (modulspezifische Farbe)
- Großes Icon (60px)
- Titel (h1, fett)
- Beschreibung (Untertitel, helle Farbe)

**Quick-Stats (4 Cards):**
- Gleiche Breite
- Weißer Hintergrund, Schatten
- Große Zahl (Metrik)
- Label darunter
- Optional: Farbiger Border-Left bei kritischen Werten
- Optional: Link "Ansehen →"

**Bereichs-Kacheln:**
- 3er Grid (Desktop), 1er Stack (Mobile)
- Hover-Effekt: Shadow erhöhen, Border erscheint
- Icon oben links, Badge oben rechts
- Titel fett, Beschreibung klein
- Pfeil-Icon am Ende für "mehr"

**Kritische Meldungen:**
- Gelber/Roter Hintergrund
- Liste mit Punkten
- Jeweils mit Link zu Details

---

## 📋 LISTEN-ANSICHT

### Struktur
```
┌─────────────────────────────────────────────────────┐
│ Breadcrumb: Dashboard > Modul > Liste               │
├─────────────────────────────────────────────────────┤
│ Context Actions Bar:                                 │
│ [➕ Neu] [📥 Import] [📤 Export] [Sort ▾]          │
├─────────────────────────────────────────────────────┤
│                                                     │
│ ┌────────┐ ┌──────────────────────────────────────┐│
│ │        │ │ Toolbar: Results Count | Sort | Per  ││
│ │ Filter │ │         Page                         ││
│ │ ────── │ ├──────────────────────────────────────┤│
│ │        │ │                                      ││
│ │ 🔍Suche│ │ ┌──┬──────┬────────┬──────┬──────┐  ││
│ │        │ │ │□│ Name │ Bestand│ Ort  │Status│  ││
│ │ Status │ │ ├──┼──────┼────────┼──────┼──────┤  ││
│ │ □ Alle │ │ │□│ Item1│  50 St.│ R1   │ 🟢  │  ││
│ │ □ Aktiv│ │ │□│ Item2│   5 St.│ R2   │ 🟡  │  ││
│ │ □ Kritisch│ │ Item3│   1 St.│ R1   │ 🔴  │  ││
│ │        │ │ └──┴──────┴────────┴──────┴──────┘  ││
│ │ Ort    │ │                                      ││
│ │ ▾      │ │ ◀ 1 2 3 4 5 ▶  Pagination           ││
│ │        │ │                                      ││
│ │ Datum  │ │                                      ││
│ │ Von-Bis│ │                                      ││
│ │        │ │                                      ││
│ │[Apply] │ │                                      ││
│ │[Reset] │ │                                      ││
│ └────────┘ └──────────────────────────────────────┘│
└─────────────────────────────────────────────────────┘
```

### Elemente-Details:

**Context Actions Bar:**
- Sticky oben (bleibt beim Scrollen)
- Links: Haupt-Actions (Neu, Import, Export)
- Rechts: View-Optionen, Sort
- Höhe: ~60px

**Filter-Sidebar:**
- Feste Breite: 250-280px
- Sticky (scrollt mit)
- Sections mit Labels
- Suche ganz oben
- Collapse-Icon zum Ausblenden
- Apply/Reset Buttons unten

**Toolbar über Tabelle:**
- Result Count links
- Sort Dropdown rechts
- Items-per-Page Dropdown rechts

**Tabelle:**
- Checkbox-Spalte (Bulk-Selection)
- Sticky Header
- Zebra-Striping (optional)
- Row-Hover Effekt
- Status als farbige Badges
- Aktions-Spalte ganz rechts (⋮ Menü)
- Quick-Edit Buttons (➖/➕) für Mengen

**Bulk-Actions Bar (erscheint bei Selection):**
```
┌─────────────────────────────────────────────────────┐
│ ✓ 5 ausgewählt  [🗑️ Löschen] [📤 Export] [✕]      │
└─────────────────────────────────────────────────────┘
```

**Responsive (Mobile):**
- Filter-Sidebar wird zu Dropdown
- Tabelle wird zu Card-Liste
- Aktionen in Slide-in Panel

---

## 👁️ DETAIL-ANSICHT

### Struktur
```
┌─────────────────────────────────────────────────────┐
│ Breadcrumb + Actions (Edit, Delete, Print)          │
├─────────────────────────────────────────────────────┤
│                                                     │
│ ┌──────────────────────────┐  ┌─────────────────┐ │
│ │ Header-Section:          │  │   Sidebar       │ │
│ │ ┌──────┐                 │  │                 │ │
│ │ │ Icon │ Titel           │  │ Quick Actions:  │ │
│ │ │/Foto │ Status-Badge    │  │ • 📤 Ausgeben   │ │
│ │ └──────┘                 │  │ • ✏️ Bearbeiten │ │
│ └──────────────────────────┘  │ • 🗑️ Löschen    │ │
│                                │                 │ │
│ [Tab 1] [Tab 2] [Tab 3] [Tab 4]│              │ │
│ ──────                         │  QR-Code:       │ │
│ ┌──────────────────────────┐  │  ┌───────────┐ │ │
│ │ Tab-Content              │  │  │    QR     │ │ │
│ │                          │  │  │   Code    │ │ │
│ │ Label:   Wert            │  │  └───────────┘ │ │
│ │ Label:   Wert            │  │                 │ │
│ │ Label:   Wert            │  │  Status:        │ │
│ │                          │  │  ✅ Verfügbar   │ │
│ │ Sections mit Titel:      │  │                 │ │
│ │ ─────────────────        │  │  Wert:          │ │
│ │ Content...               │  │  1.234,56 €     │ │
│ │                          │  │                 │ │
│ └──────────────────────────┘  └─────────────────┘ │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### Elemente-Details:

**Header-Section:**
- Foto/Icon links (groß, 120x120px)
- Titel rechts daneben (h1)
- Status-Badge unter Titel
- Optional: Weitere Meta-Infos (ID, erstellt am, etc.)

**Tabs:**
- Horizontal scrollbar bei vielen Tabs
- Aktiver Tab: Unterstrich/Hintergrund
- Tab-Count in Badge wenn relevant

**Tab-Content:**
- Label-Value Pairs in Grid (2 Spalten auf Desktop)
- Sections mit Titeln und Border-Top
- Collapsible Sections für optionale Infos
- Listen für Historie/Transaktionen

**Sidebar (Sticky):**
- Quick-Actions als Button-Liste
- QR-Code wenn vorhanden
- Status-Anzeige (groß, farbig)
- Key-Metrics
- Breite: 280-320px

**Tab-Inhalte modulspezifisch:**

**Medical - Medikament:**
- Tab 1: Basis-Info (Name, Wirkstoff, Dosierung, etc.)
- Tab 2: Bestand (Menge, Ort, Schwellwerte, Preis)
- Tab 3: Chargen (Liste mit Ablaufdaten)
- Tab 4: Historie (Transaktions-Timeline)
- Tab 5: Dokumente (Anhänge)

**Equipment - Gerät:**
- Tab 1: Basis-Info (Name, Kategorie, Seriennummer)
- Tab 2: Prüfungen (Timeline mit Status)
- Tab 3: Wartung (Intervalle, Protokolle)
- Tab 4: Standort (Aktuell + Historie)
- Tab 5: Dokumente (Handbücher, Berichte)

**Workshop - Fahrzeug:**
- Tab 1: Basis-Info (Kennzeichen, Typ, Baujahr)
- Tab 2: Prüfungen (TÜV, HU, etc.)
- Tab 3: Wartungshistorie
- Tab 4: Tankbuch
- Tab 5: Schäden

---

## 📝 FORMULAR (Modal)

### Struktur
```
┌─────────────────────────────────────────────────────┐
│ Overlay (dunkel, transparent)                        │
│  ┌─────────────────────────────────────────────────┐│
│  │ Header: Icon + Titel            [✕ Schließen]  ││
│  ├─────────────────────────────────────────────────┤│
│  │ Scrollbereich (max-height):                     ││
│  │                                                  ││
│  │ 📋 Section 1: Titel                             ││
│  │ ─────────────────────                           ││
│  │ [Label] [Input]  [Label] [Input]                ││
│  │ [Label] [Input]  [Label] [Select]               ││
│  │                                                  ││
│  │ 📦 Section 2: Titel                             ││
│  │ ─────────────────────                           ││
│  │ [Label] [Input]  [Label] [Input]                ││
│  │ □ Checkbox mit Beschreibung                     ││
│  │                                                  ││
│  │ 🌡️ Section 3 (Collapsible):                    ││
│  │ ─────────────────────────── [▼]                ││
│  │ (Content ausgeblendet)                          ││
│  │                                                  ││
│  ├─────────────────────────────────────────────────┤│
│  │ Footer (Fixed):                                 ││
│  │            [Abbrechen] [Speichern]             ││
│  └─────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────┘
```

### Elemente-Details:

**Modal-Größen:**
- Small: max-width 500px (einfache Forms)
- Medium: max-width 768px (Standard)
- Large: max-width 1024px (komplexe Forms)

**Header:**
- Icon + Titel (linksbündig)
- Close-Button (rechtsbündig)
- Optional: Grauer Hintergrund
- Höhe: ~60px

**Body (Scrollbar):**
- Padding: 24px
- Max-Height: 70vh
- Sections mit Icons + Titeln
- Border-Top zwischen Sections
- Grid für Inputs (1 oder 2 Spalten)

**Input-Typen:**
- Text: Fullwidth mit Label oben
- Select: Dropdown mit Placeholder
- Checkbox: Mit Icon und Beschreibung (mehrzeilig)
- Date: Datepicker
- Number: Mit Step-Buttons
- Textarea: Für längere Texte

**Collapsible Sections:**
- Header clickbar
- Pfeil-Icon (▼/▶) für State
- Smooth Transition beim Öffnen

**Footer:**
- Sticky unten
- Grauer Hintergrund
- Buttons rechtsbündig
- Abbrechen (Secondary), Speichern (Primary)

**Validation:**
- Pflichtfelder mit * markiert
- Error-State: Roter Border + Text unter Input
- Success-State: Grüner Border + Checkmark

---

## 🎯 PROFIL-SEITE

### Struktur
```
┌─────────────────────────────────────────────────────┐
│ Breadcrumb                                           │
├─────────────────────────────────────────────────────┤
│ ┌──────────────┐  ┌────────────────────────────────┐│
│ │ Sidebar:     │  │ Tabs:                          ││
│ │              │  │ [Übersicht] [Daten] [Qual] ... ││
│ │  ┌────────┐  │  │ ──────────                     ││
│ │  │ Avatar │  │  │                                ││
│ │  │        │  │  │ Tab-Content:                   ││
│ │  └────────┘  │  │                                ││
│ │  Name        │  │ ⚠️ Anstehende Prüfungen:       ││
│ │  Position    │  │ • Prüfung 1 - Datum            ││
│ │  Abteilung   │  │ • Prüfung 2 - Datum            ││
│ │  [Badges]    │  │                                ││
│ │              │  │ Statistiken:                   ││
│ │ Stats:       │  │ ┌──────┐ ┌──────┐ ┌──────┐   ││
│ │ Quali: 12    │  │ │Stat 1│ │Stat 2│ │Stat 3│   ││
│ │ [Progress]   │  │ └──────┘ └──────┘ └──────┘   ││
│ │              │  │                                ││
│ │ Std: 45/60   │  │ Letzte Aktivitäten:            ││
│ │ [Progress]   │  │ • Aktivität 1                  ││
│ │              │  │ • Aktivität 2                  ││
│ │ Actions:     │  │ • Aktivität 3                  ││
│ │ [Bearbeiten] │  │                                ││
│ │ [Passwort]   │  │                                ││
│ └──────────────┘  └────────────────────────────────┘│
└─────────────────────────────────────────────────────┘
```

### Elemente-Details:

**Sidebar:**
- Sticky
- Breite: 320px
- Avatar zentriert (groß, rund)
- Edit-Button als Overlay auf Avatar
- Name/Position/Abteilung zentriert
- Badges (Status, Typ)
- Quick-Stats mit Progress-Bars
- Action-Buttons (Stack)

**Tabs:**
- Horizontal
- Content-Bereich vollbreite
- Je nach Tab unterschiedlicher Content

**Tab: Übersicht**
- Alert-Box für anstehende Aufgaben
- 3er Grid mit Stats
- Liste letzte Aktivitäten

**Tab: Persönliche Daten**
- Label-Value Grid (2 Spalten)
- Sections mit Titeln
- Nicht editierbar (nur ansehen)

**Tab: Qualifikationen**
- Card-Liste
- Jede Card: Titel, Datum, Status-Badge
- Farbcodiert nach Ablauf-Status

---

## ⚙️ EINSTELLUNGEN-SEITE

### Struktur
```
┌─────────────────────────────────────────────────────┐
│ Breadcrumb                                           │
├─────────────────────────────────────────────────────┤
│ ┌──────────┐  ┌──────────────────────────────────┐ │
│ │ Sidebar: │  │ Content (je nach Section):        │ │
│ │          │  │                                   │ │
│ │ 👤Account│  │ Section-Titel                     │ │
│ │ 🔔Notifi │  │ ─────────────                     │ │
│ │ 🎨Darst. │  │                                   │ │
│ │ 🔒Sicher │  │ Form-Elemente                     │ │
│ │ 🛡️Daten  │  │                                   │ │
│ │ ─────────│  │ [Input]                           │ │
│ │ ⚙️System │  │ [Select]                          │ │
│ │          │  │ □ Checkbox                        │ │
│ │          │  │                                   │ │
│ │          │  │ ─────────────                     │ │
│ │          │  │                                   │ │
│ │          │  │ [Speichern]                       │ │
│ └──────────┘  └──────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
```

### Template-Struktur (Modularisiert mit Sub-Templates)

**Haupt-Template:** `templates/core/settings.html`
- Breadcrumb
- 2-Spalten Layout (settings-layout)
- Sidebar-Navigation (Alpine.js Section-Switching)
- Content-Area mit {% include %} für alle Sections

**Sub-Templates (je Section):**
```
templates/core/settings/
├── account.html         # Account-Einstellungen
├── notifications.html   # Benachrichtigungen
├── appearance.html      # Darstellung
├── security.html        # Sicherheit
├── privacy.html         # Datenschutz
└── system.html          # System (nur Admins)
```

**Vorteile:**
- ✅ Wartbarkeit: Jede Section in eigener Datei
- ✅ Wiederverwendbarkeit: Sections können einzeln via HTMX geladen werden
- ✅ Übersichtlichkeit: Haupt-Template nur ~120 Zeilen (statt 570+)
- ✅ Team-Arbeit: Paralleles Arbeiten an verschiedenen Sections
- ✅ Testing: Einfachere Unit-Tests pro Section

### Sections-Inhalt:

**Account** (`account.html`):
- E-Mail-Adresse ändern
- Sprache & Zeitzone (vorbereitet)
- Form-Integration mit Django Forms

**Benachrichtigungen** (`notifications.html`):
- E-Mail-Benachrichtigungen (3 Optionen)
- Push-Benachrichtigungen mit Browser-Permission
- Benachrichtigungs-Kategorien (Bestände, Prüfungen, Bestellungen, etc.)

**Darstellung** (`appearance.html`):
- Theme-Auswahl (Hell/Dunkel/Auto) mit visuellen Karten
- Sidebar-Verhalten (ausgeklappt/eingeklappt/auto)
- Listen-Darstellung (Items/Page, Tabellen-Dichte)
- Ansichts-Präferenzen (Tooltips, Breadcrumbs, Kompakt-Modus)

**Sicherheit** (`security.html`):
- Passwort ändern (mit letzter Änderung)
- 2FA-Verwaltung (Status, Aktivierung, Backup-Codes)
- Aktive Sitzungen (Session-Liste)
- Anmelde-Aktivitäten & Sicherheits-Empfehlungen

**Datenschutz** (`privacy.html`):
- Datenerfassung (Analytics, Error-Reporting)
- Datenspeicherung (DSGVO-Hinweis, EU-Server)
- Meine Daten (Download, Datenschutzerklärung)
- Account löschen (mit Aufbewahrungspflichten BTM/Audit)

**System** (`system.html` - nur Admins):
- System-Status (Django, Python, PostgreSQL, Redis)
- Quick-Links (Admin, Backup, Cache, Logs)
- Wartungsmodus-Toggle
- System-Informationen

---

## 🚗 FAHRZEUGÜBERNAHME (Spezial)

### Struktur
```
┌─────────────────────────────────────────────────────┐
│ Progress-Steps: [1✓] [2✓] [3] [4] [5]              │
├─────────────────────────────────────────────────────┤
│                                                     │
│ Step-Content (je nach aktuellem Step):              │
│                                                     │
│ Step 1: Fahrzeug wählen                             │
│ ┌───────┐ ┌───────┐ ┌───────┐                     │
│ │ FZ 1  │ │ FZ 2  │ │ FZ 3  │                     │
│ └───────┘ └───────┘ └───────┘                     │
│                                                     │
│ Step 2: Basis-Check                                 │
│ □ Fahrzeug sauber                                   │
│ □ Fahrzeug einsatzbereit                           │
│ [Kilometerstand]  [Tankfüllung %]                  │
│                                                     │
│ Step 3: Fächer-Check                                │
│ ┌─────────────────────────────────────────────────┐│
│ │ Fach 1 - Vorne Links         [□ Vollständig]   ││
│ │ Soll: Item A, Item B, Item C                    ││
│ │ [Foto] [Notizen]                                ││
│ └─────────────────────────────────────────────────┘│
│                                                     │
│ [◀ Zurück]                    [Weiter ▶]           │
└─────────────────────────────────────────────────────┘
```

### Besonderheiten:
- Große Touch-Targets (min. 44px)
- Foto-Upload prominent
- Check-Listen mit großen Checkboxen
- Unterschriften-Feld am Ende
- Status-Ampel (Rot/Gelb/Grün)

---

## 📊 BTM-BEREICH (Spezial)

### Struktur
```
┌─────────────────────────────────────────────────────┐
│ ⚠️ BTM-Warning-Header (Dunkelrot):                 │
│ 🔒 Betäubungsmittel-Bereich                        │
│ Alle Aktionen protokolliert • 4-Augen-Prinzip      │
│ Session-Zeit: [14:58]                               │
├─────────────────────────────────────────────────────┤
│                                                     │
│ [Standard Listen/Detail-Ansicht]                    │
│                                                     │
│ Bei Aktion (Ausgabe/Entsorgung):                    │
│ ┌─────────────────────────────────────────────────┐│
│ │ Vier-Augen-Bestätigung Modal:                   ││
│ │                                                  ││
│ │ Hauptnutzer: [Name] (automatisch)               ││
│ │                                                  ││
│ │ Zeuge auswählen:                                 ││
│ │ [Select: Benutzer mit BTM-Berechtigung]         ││
│ │                                                  ││
│ │ Zeugen-PIN:                                      ││
│ │ [••••] [Eingabe]                                ││
│ │                                                  ││
│ │ Grund:                                           ││
│ │ [Textarea]                                       ││
│ │                                                  ││
│ │ [Abbrechen] [Bestätigen]                        ││
│ └─────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────┘
```

### Besonderheiten:
- Dunklerer Rot-Ton überall
- Warning-Banner immer sichtbar
- Session-Timer prominent
- Alle Aktionen benötigen Vier-Augen-Bestätigung
- Extra Audit-Spalten in Listen

---

Möchtest du noch spezifische Strukturen für:
1. **Kalender-Ansichten** (Prüfungen, Wartungen)
2. **Reports/Dashboards** (KPIs, Charts)
3. **Wizard-Formulare** (mehrstufig)
4. **Mobile-Ansichten** (spezielle Layouts)
5. **Info-Monitore** (Dashboard-Builder)

---

## 👥 PERSONAL-VERWALTUNG

### Dashboard-Struktur
```
┌─────────────────────────────────────────────────────┐
│ Breadcrumb: Dashboard > Personal                     │
├─────────────────────────────────────────────────────┤
│                                                     │
│ ┌─────────────────────────────────────────────────┐│
│ │ 👥 Personal-Header (Blauer Gradient)            ││
│ │ Icon + Titel + Beschreibung                     ││
│ └─────────────────────────────────────────────────┘│
│                                                     │
│ Quick-Stats:                                        │
│ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐      │
│ │ 245    │ │  12    │ │  28    │ │  8     │      │
│ │Personal│ │Prüfungen│ │Qualif. │ │Ablauf │      │
│ │Gesamt  │ │fällig  │ │erworben│ │bald    │      │
│ └────────┘ └────────┘ └────────┘ └────────┘      │
│                                                     │
│ Bereiche (Kacheln):                                 │
│ ┌──────────┐ ┌──────────┐ ┌──────────┐            │
│ │ 👤       │ │ 📜       │ │ 🎓       │            │
│ │Personal- │ │Qualifi-  │ │Schulungen│            │
│ │übersicht │ │kationen  │ │          │            │
│ │245 Pers. │ │125 aktiv │ │15 geplant│            │
│ │→ Ansehen │ │→ Ansehen │ │→ Ansehen │            │
│ └──────────┘ └──────────┘ └──────────┘            │
│                                                     │
│ ⚠️ Wichtige Hinweise:                              │
│ • 12 Personen: Prüfungen fällig in 30 Tagen       │
│ • 8 Qualifikationen laufen ab                      │
│ • 5 Personen: Pflichtstunden nicht erreicht        │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

### Personal-Liste
```
┌─────────────────────────────────────────────────────┐
│ Breadcrumb + Context Actions                        │
│ [➕ Neue Person] [📥 Import] [📤 Export]           │
├─────────────────────────────────────────────────────┤
│ ┌────────┐ ┌──────────────────────────────────────┐│
│ │Filter: │ │ Toolbar + Tabelle                    ││
│ │        │ │                                      ││
│ │🔍Suche │ │ ┌──┬────────┬────────┬──────┬──────┐││
│ │        │ │ │□│Name    │Pers-Nr │Abtlg.│Status│││
│ │Status: │ │ ├──┼────────┼────────┼──────┼──────┤││
│ │□ Aktiv │ │ │□│Müller,│P12345 │Wache1│🟢    │││
│ │□ Inakt.│ │ │ │Max     │        │      │Aktiv │││
│ │□ Aus-  │ │ │ │        │        │      │      │││
│ │  bildung│ │ │        │        │      │      │││
│ │        │ │ │□│Schmidt │P12346 │Wache2│🟢    │││
│ │Abtlg.: │ │ │ │Anna    │        │      │Aktiv │││
│ │▾ Alle  │ │ │ │        │        │      │      │││
│ │        │ │ │□│Weber   │P12347 │Werkst│⚠️    │││
│ │Position│ │ │ │Tom     │        │      │Prüfng│││
│ │▾ Alle  │ │ └──┴────────┴────────┴──────┴──────┘││
│ │        │ │                                      ││
│ │[Apply] │ │ Pagination                           ││
│ │[Reset] │ │                                      ││
│ └────────┘ └──────────────────────────────────────┘│
└─────────────────────────────────────────────────────┘
```

**Tabellen-Spalten (Desktop):**
- Checkbox
- Foto (klein, rund) + Name
- Personalnummer
- Position
- Abteilung
- Qualifikationen (Count + Badge)
- Prüfungen (Status-Icon)
- Status (Badge)
- Aktionen (⋮)

**Card-View (Mobile):**
```
┌─────────────────────────────┐
│ ┌──────┐ Max Müller        │
│ │ Foto │ P12345             │
│ └──────┘ Brandmeister       │
│          Wache 1            │
│                             │
│ Quali: 8  Prüfungen: ⚠️ 2  │
│ Status: 🟢 Aktiv            │
│                             │
│ [Details] [Bearbeiten]      │
└─────────────────────────────┘
```

---

### Person Detail-Ansicht
```
┌─────────────────────────────────────────────────────┐
│ Breadcrumb: Dashboard > Personal > Max Müller       │
│ [✏️ Bearbeiten] [🗑️ Löschen] [🖨️ Drucken]         │
├─────────────────────────────────────────────────────┤
│                                                     │
│ ┌──────────────────────────┐  ┌─────────────────┐ │
│ │ Header:                  │  │   Sidebar       │ │
│ │ ┌────────┐               │  │                 │ │
│ │ │        │ Max Müller    │  │ Quick Actions:  │ │
│ │ │  Foto  │ P12345        │  │ • 👕 Kleidung   │ │
│ │ │  140x  │ Brandmeister  │  │   ausgeben      │ │
│ │ │  140   │ Wache 1       │  │ • 📋 Schulung   │ │
│ │ │        │               │  │   planen        │ │
│ │ └────────┘ 🟢 Aktiv      │  │ • 📄 Dokument   │ │
│ │            🏢 Vollzeit   │  │   hochladen     │ │
│ └──────────────────────────┘  │                 │ │
│                                │ Status:         │ │
│ [Übersicht][Daten][Quali][Prüf][Kleidung][Std.] │ │
│ ────────                       │ ✅ Alle Prüf.   │ │
│ ┌──────────────────────────┐  │    aktuell      │ │
│ │ Tab-Content              │  │ ⚠️ Pflicht-     │ │
│ │                          │  │    stunden:     │ │
│ │ (je nach Tab)            │  │    45/60        │ │
│ │                          │  │                 │ │
│ └──────────────────────────┘  │ Kontakt:        │ │
│                                │ 📧 max@fw.de    │ │
│                                │ 📱 0123/456789  │ │
│                                │                 │ │
│                                │ Einstellung:    │ │
│                                │ 01.01.2015      │ │
│                                │ (9 Jahre)       │ │
│                                └─────────────────┘ │
└─────────────────────────────────────────────────────┘
```

**Tab: Übersicht**
```
┌─────────────────────────────────────────────────────┐
│ ⚠️ Anstehende Aufgaben:                            │
│ • Atemschutz-Prüfung in 14 Tagen                   │
│ • Erste-Hilfe-Kurs in 45 Tagen                     │
│                                                     │
│ Statistiken (3er Grid):                             │
│ ┌───────┐ ┌───────┐ ┌───────┐                     │
│ │ 28    │ │ 156   │ │ 12    │                     │
│ │Quali  │ │Schich-│ │Schulun│                     │
│ │       │ │ten '24│ │gen '24│                     │
│ └───────┘ └───────┘ └───────┘                     │
│                                                     │
│ Letzte Aktivitäten (Timeline):                     │
│ ────●──── 15.03.2024 - Atemschutz erneuert        │
│     │                                               │
│ ────●──── 10.03.2024 - Schulung Höhenrettung      │
│     │                                               │
│ ────●──── 01.03.2024 - Kleidung ausgegeben        │
│                                                     │
└─────────────────────────────────────────────────────┘
```

**Tab: Persönliche Daten**
```
┌─────────────────────────────────────────────────────┐
│ Basis-Informationen:                                │
│ ┌──────────────────┬──────────────────┐            │
│ │ Personalnr: P12345│ Geb.datum: ...  │            │
│ │ Position: ...     │ Abteilung: ...  │            │
│ │ Eintritt: ...     │ Beschäft.: ...  │            │
│ └──────────────────┴──────────────────┘            │
│                                                     │
│ Kontaktdaten:                                       │
│ ┌──────────────────┬──────────────────┐            │
│ │ E-Mail: ...       │ Telefon: ...    │            │
│ │ Mobil: ...        │ Notfall: ...    │            │
│ └──────────────────┴──────────────────┘            │
│                                                     │
│ Adresse:                                            │
│ ┌───────────────────────────────────────┐          │
│ │ Straße, PLZ Ort                       │          │
│ └───────────────────────────────────────┘          │
│                                                     │
└─────────────────────────────────────────────────────┘
```

**Tab: Qualifikationen**
```
┌─────────────────────────────────────────────────────┐
│ Qualifikationen (8) [+ Hinzufügen]                  │
│                                                     │
│ ┌─────────────────────────────────────────────────┐│
│ │ 🎓 Atemschutzgeräteträger                       ││
│ │ Code: AGT • Unbefristet                         ││
│ │ Erworben: 15.03.2015                            ││
│ │ Zertifikat: AGT-12345                           ││
│ │ Status: ✅ Gültig                               ││
│ └─────────────────────────────────────────────────┘│
│                                                     │
│ ┌─────────────────────────────────────────────────┐│
│ │ 🎓 Maschinist                                   ││
│ │ Code: MASCH • Gültig bis: 31.12.2024           ││
│ │ Erworben: 01.06.2018                            ││
│ │ Zertifikat: MASCH-67890                         ││
│ │ Status: ⚠️ Läuft in 90 Tagen ab                ││
│ └─────────────────────────────────────────────────┘│
│                                                     │
│ ┌─────────────────────────────────────────────────┐│
│ │ 🎓 Erste Hilfe                                  ││
│ │ Code: EH • Gültig bis: 15.01.2024              ││
│ │ Erworben: 15.01.2022                            ││
│ │ Status: 🔴 Abgelaufen                          ││
│ └─────────────────────────────────────────────────┘│
│                                                     │
└─────────────────────────────────────────────────────┘
```

**Tab: Prüfungen**
```
┌─────────────────────────────────────────────────────┐
│ Anstehende Prüfungen (2) | Absolvierte (45)        │
│                                                     │
│ Anstehend:                                          │
│ ┌─────────────────────────────────────────────────┐│
│ │ ⚠️ Atemschutz-Belastungsübung                   ││
│ │ Fällig: 28.03.2024 (in 14 Tagen)               ││
│ │ Intervall: Jährlich                             ││
│ │ Letzte Prüfung: 28.03.2023                      ││
│ │ [Als erledigt markieren] [Verschieben]          ││
│ └─────────────────────────────────────────────────┘│
│                                                     │
│ ┌─────────────────────────────────────────────────┐│
│ │ ℹ️ Erste-Hilfe-Auffrischung                     ││
│ │ Fällig: 15.04.2024 (in 45 Tagen)               ││
│ │ Intervall: 2 Jahre                              ││
│ │ Letzte Prüfung: 15.04.2022                      ││
│ │ [Als erledigt markieren] [Verschieben]          ││
│ └─────────────────────────────────────────────────┘│
│                                                     │
│ Absolviert (Timeline):                              │
│ ────●──── 28.03.2023 - Atemschutz ✅              │
│ ────●──── 15.01.2023 - Maschinisten-Prüfung ✅    │
│ ────●──── 10.12.2022 - Höhenrettung ✅            │
│                                                     │
└─────────────────────────────────────────────────────┘
```

**Tab: Kleidung**
```
┌─────────────────────────────────────────────────────┐
│ Ausgegebene Kleidung (12 Teile)                     │
│ Gesamtwert: 2.450,00 €                              │
│                                                     │
│ Tabelle:                                            │
│ ┌──────────┬──────┬────────────┬─────────┬────────┐│
│ │ Artikel  │Größe │Ausgegeben  │Zustand  │Wert   ││
│ ├──────────┼──────┼────────────┼─────────┼────────┤│
│ │Einsatz-  │  52  │01.01.2023  │🟢 Gut   │450€   ││
│ │jacke     │      │            │         │       ││
│ ├──────────┼──────┼────────────┼─────────┼────────┤│
│ │Einsatz-  │  48  │01.01.2023  │🟢 Gut   │380€   ││
│ │hose      │      │            │         │       ││
│ ├──────────┼──────┼────────────┼─────────┼────────┤│
│ │Helm      │  M   │01.01.2020  │🟡 Prüfen│250€   ││
│ │          │      │            │         │       ││
│ ├──────────┼──────┼────────────┼─────────┼────────┤│
│ │Stiefel   │  44  │15.06.2023  │🟢 Gut   │180€   ││
│ └──────────┴──────┴────────────┴─────────┴────────┘│
│                                                     │
│ [Neue Ausgabe] [Rücknahme erfassen]                │
│                                                     │
└─────────────────────────────────────────────────────┘
```

**Tab: Pflichtstunden**
```
┌─────────────────────────────────────────────────────┐
│ Pflichtstunden 2024                                 │
│                                                     │
│ Übersicht:                                          │
│ ┌─────────────────────────────────────────────────┐│
│ │ 🤿 Tauchen                                       ││
│ │ 18 / 30 Stunden (60%)                           ││
│ │ [████████████░░░░░░░░░] ⚠️ Noch 12 Std.        ││
│ │ Frist: 31.12.2024 (270 Tage)                    ││
│ └─────────────────────────────────────────────────┘│
│                                                     │
│ ┌─────────────────────────────────────────────────┐│
│ │ 🧗 Höhenrettung                                  ││
│ │ 20 / 20 Stunden (100%)                          ││
│ │ [████████████████████] ✅ Erfüllt              ││
│ │ Frist: 31.12.2024                               ││
│ └─────────────────────────────────────────────────┘│
│                                                     │
│ ┌─────────────────────────────────────────────────┐│
│ │ 🏥 Medizinische Fortbildung                     ││
│ │ 8 / 30 Stunden (27%)                            ││
│ │ [█████░░░░░░░░░░░░░░░] 🔴 Dringend 22 Std.     ││
│ │ Frist: 31.12.2024 (270 Tage)                    ││
│ └─────────────────────────────────────────────────┘│
│                                                     │
│ Historie (Liste):                                   │
│ • 15.03.2024 - Tauchgang (2h) - Trainer: Schmidt  │
│ • 10.03.2024 - Höhenrettung (4h) - Übung am Turm  │
│ • 05.03.2024 - Med. Fortbildung (2h) - EKG-Kurs   │
│                                                     │
│ [Stunden erfassen]                                  │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

### Person anlegen/bearbeiten (Modal)
```
┌─────────────────────────────────────────────────────┐
│ Overlay (transparent, dunkel)                        │
│  ┌─────────────────────────────────────────────────┐│
│  │ 👤 Neue Person anlegen              [✕]        ││
│  ├─────────────────────────────────────────────────┤│
│  │ Scrollbereich:                                  ││
│  │                                                  ││
│  │ 📋 Basis-Informationen                          ││
│  │ ───────────────────                             ││
│  │ [Vorname]              [Nachname]               ││
│  │ [Personalnummer]       [Geburtsdatum]           ││
│  │ [Position]             [Abteilung ▾]            ││
│  │ [Eintrittsdatum]       [Beschäftigungsart ▾]    ││
│  │                                                  ││
│  │ 📞 Kontaktdaten                                 ││
│  │ ───────────────                                 ││
│  │ [E-Mail]               [Telefon]                ││
│  │ [Mobil]                [Notfallkontakt]         ││
│  │                                                  ││
│  │ 📍 Adresse (Optional) ────── [▼]               ││
│  │ (Collapsed)                                     ││
│  │                                                  ││
│  │ 📸 Foto (Optional) ────────── [▼]              ││
│  │ (Collapsed)                                     ││
│  │                                                  ││
│  │ ⚙️ Systemzugang (Optional) ─── [▼]             ││
│  │ (Collapsed - für Benutzer-Account)             ││
│  │                                                  ││
│  ├─────────────────────────────────────────────────┤│
│  │ Footer:                                         ││
│  │              [Abbrechen] [Person anlegen]      ││
│  └─────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────┘
```

---

### Qualifikation hinzufügen (Slide-in Panel)
```
┌─────────────────────────────────────────────────────┐
│                                      ┌──────────────┐│
│                                      │ Slide-in:    ││
│                                      │              ││
│                                      │ Qualifikation││
│ (Hauptinhalt abgedunkelt)            │ hinzufügen   ││
│                                      │         [✕]  ││
│                                      ├──────────────┤│
│                                      │              ││
│                                      │ Qualifikation││
│                                      │ ▾ wählen     ││
│                                      │              ││
│                                      │ oder neu:    ││
│                                      │ [Name]       ││
│                                      │ [Code]       ││
│                                      │              ││
│                                      │ Erworben am: ││
│                                      │ [Datum]      ││
│                                      │              ││
│                                      │ Gültig bis:  ││
│                                      │ [Datum]      ││
│                                      │ □ Unbefr.    ││
│                                      │              ││
│                                      │ Zertifikat:  ││
│                                      │ [Nr.]        ││
│                                      │              ││
│                                      │ Dokument:    ││
│                                      │ [Upload]     ││
│                                      │              ││
│                                      ├──────────────┤│
│                                      │ [Abbrechen]  ││
│                                      │ [Hinzufügen] ││
│                                      └──────────────┘│
└─────────────────────────────────────────────────────┘
```

---

### Qualifikations-Verwaltung (Separate Ansicht)
```
┌─────────────────────────────────────────────────────┐
│ Breadcrumb: Dashboard > Personal > Qualifikationen  │
│ [➕ Neue Qualifikation] [📥 Import]                │
├─────────────────────────────────────────────────────┤
│                                                     │
│ 📊 Übersicht:                                       │
│ ┌────────┐ ┌────────┐ ┌────────┐                  │
│ │  125   │ │   8    │ │  342   │                  │
│ │Quali-  │ │Laufen  │ │Gesamt  │                  │
│ │fikatio-│ │bald ab │ │zugeord-│                  │
│ │nen     │ │        │ │net     │                  │
│ └────────┘ └────────┘ └────────┘                  │
│                                                     │
│ Liste aller Qualifikationen:                        │
│ ┌──────────────┬──────┬────────────┬──────┬───────┐│
│ │ Name         │Code  │Intervall   │Zuordn│Status ││
│ ├──────────────┼──────┼────────────┼──────┼───────┤│
│ │Atemschutz-   │AGT   │Unbefristet │  45  │Aktiv  ││
│ │geräteträger  │      │            │      │       ││
│ ├──────────────┼──────┼────────────┼──────┼───────┤│
│ │Maschinist    │MASCH │2 Jahre     │  28  │Aktiv  ││
│ │              │      │            │      │       ││
│ ├──────────────┼──────┼────────────┼──────┼───────┤│
│ │Erste Hilfe   │EH    │2 Jahre     │ 120  │Aktiv  ││
│ │              │      │            │      │       ││
│ └──────────────┴──────┴────────────┴──────┴───────┘│
│                                                     │
│ [Detail-Ansicht bei Click]                          │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

### Prüfungskalender
```
┌─────────────────────────────────────────────────────┐
│ Breadcrumb: Dashboard > Personal > Prüfungskalender │
│ [Filter: Alle Personen ▾] [Alle Prüfungen ▾]       │
├─────────────────────────────────────────────────────┤
│                                                     │
│ ◀ März 2024 ▶                [Monat][Woche][Liste]│
│                                                     │
│ ┌─────────────────────────────────────────────────┐│
│ │ Mo   Di   Mi   Do   Fr   Sa   So               ││
│ ├─────┬─────┬─────┬─────┬─────┬─────┬─────┐      ││
│ │     │     │     │     │  1  │  2  │  3  │      ││
│ │     │     │     │     │     │     │     │      ││
│ ├─────┼─────┼─────┼─────┼─────┼─────┼─────┤      ││
│ │  4  │  5  │  6  │  7  │  8  │  9  │ 10  │      ││
│ │     │     │     │     │ AGT │     │     │      ││
│ │     │     │     │     │🟡2x│     │     │      ││
│ ├─────┼─────┼─────┼─────┼─────┼─────┼─────┤      ││
│ │ 11  │ 12  │ 13  │ 14  │ 15  │ 16  │ 17  │      ││
│ │     │ EH  │     │     │MASCH│     │     │      ││
│ │     │🔴5x │     │     │🟢1x│     │     │      ││
│ ├─────┼─────┼─────┼─────┼─────┼─────┼─────┤      ││
│ │ 18  │ 19  │ 20  │ 21  │ 22  │ 23  │ 24  │      ││
│ │     │     │     │     │     │     │     │      ││
│ └─────┴─────┴─────┴─────┴─────┴─────┴─────┘      ││
│                                                     │
│ Legende:                                            │
│ 🔴 Überfällig  🟡 Fällig  🟢 Geplant              │
│                                                     │
│ Detail bei Click auf Tag:                           │
│ ┌─────────────────────────────────────────────────┐│
│ │ 08.03.2024 - Atemschutz (2 Prüfungen)          ││
│ │ • Müller, Max - Fällig (🟡)                     ││
│ │ • Schmidt, Anna - Fällig (🟡)                   ││
│ │ [Alle als erledigt] [Details]                   ││
│ └─────────────────────────────────────────────────┘│
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

### Schulungsverwaltung
```
┌─────────────────────────────────────────────────────┐
│ Breadcrumb: Dashboard > Personal > Schulungen       │
│ [➕ Neue Schulung] [📅 Kalender]                   │
├─────────────────────────────────────────────────────┤
│                                                     │
│ Anstehende Schulungen:                              │
│ ┌─────────────────────────────────────────────────┐│
│ │ 🎓 Erste-Hilfe-Kurs                             ││
│ │ Datum: 15.04.2024, 09:00-17:00 Uhr             ││
│ │ Ort: Schulungsraum 1                            ││
│ │ Trainer: Dr. Schmidt                            ││
│ │ Teilnehmer: 12 / 15 (3 Plätze frei)            ││
│ │ Status: 🟢 Bestätigt                            ││
│ │ [Details] [Teilnehmer] [Absagen]               ││
│ └─────────────────────────────────────────────────┘│
│                                                     │
│ ┌─────────────────────────────────────────────────┐│
│ │ 🎓 Atemschutz-Fortbildung                       ││
│ │ Datum: 22.04.2024, 14:00-18:00 Uhr             ││
│ │ Ort: Atemschutzwerkstatt                        ││
│ │ Trainer: Hauptbrandmeister Weber               ││
│ │ Teilnehmer: 8 / 10 (2 Plätze frei)             ││
│ │ Status: 🟡 Anmeldung läuft                      ││
│ │ [Details] [Anmelden] [Bearbeiten]              ││
│ └─────────────────────────────────────────────────┘│
│                                                     │
│ Vergangene Schulungen (Liste):                      │
│ • 15.03.2024 - Höhenrettung (12 Teilnehmer) ✅    │
│ • 10.03.2024 - Maschinisten-Lehrgang (8 TN) ✅    │
│ • 05.03.2024 - Funk-Schulung (15 TN) ✅           │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

### Bulk-Import (Modal)
```
┌─────────────────────────────────────────────────────┐
│ Overlay                                              │
│  ┌─────────────────────────────────────────────────┐│
│  │ 📥 Personal importieren              [✕]       ││
│  ├─────────────────────────────────────────────────┤│
│  │                                                  ││
│  │ Schritt 1: Vorlage herunterladen                ││
│  │ ┌────────────────────────────────────────────┐  ││
│  │ │ 📄 Excel-Vorlage                           │  ││
│  │ │ personal_import_vorlage.xlsx              │  ││
│  │ │ [Download]                                 │  ││
│  │ └────────────────────────────────────────────┘  ││
│  │                                                  ││
│  │ Schritt 2: Datei hochladen                      ││
│  │ ┌────────────────────────────────────────────┐  ││
│  │ │ Datei hierhin ziehen oder [Browse]        │  ││
│  │ │                                            │  ││
│  │ │ Unterstützte Formate: .xlsx, .csv         │  ││
│  │ └────────────────────────────────────────────┘  ││
│  │                                                  ││
│  │ Schritt 3: Überprüfung                          ││
│  │ ┌────────────────────────────────────────────┐  ││
│  │ │ ✅ 45 Einträge gefunden                    │  ││
│  │ │ ⚠️ 3 Warnungen (Duplikate)                │  ││
│  │ │ ❌ 2 Fehler (Pflichtfelder fehlen)        │  ││
│  │ │                                            │  ││
│  │ │ [Fehler anzeigen] [Vorschau]              │  ││
│  │ └────────────────────────────────────────────┘  ││
│  │                                                  ││
│  ├─────────────────────────────────────────────────┤│
│  │        [Abbrechen] [Import starten]            ││
│  └─────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────┘
```

---

Perfekt! Jetzt hast du auch die **komplette Struktur für die Personal-Verwaltung**! 👥

Die Personal-Templates beinhalten:
- ✅ Dashboard mit Stats
- ✅ Listen-Ansicht mit Filtern
- ✅ Detail-Ansicht mit 6 Tabs
- ✅ Formulare (Modal & Slide-in)
- ✅ Qualifikations-Verwaltung
- ✅ Prüfungskalender
- ✅ Schulungsverwaltung
- ✅ Bulk-Import



---

## 📚 Implementierte Templates (Stand 2025-10-03)

### ✅ Core Templates

#### 1. Dashboard (`templates/dashboard.html`)
- **Layout:** Vollbreite, Grid-basiert
- **Features:** KPI-Cards (4er Grid), Module-Tiles (3er Grid), Activity Timeline
- **Status:** ✅ Implementiert

#### 2. Profil-Seite (`templates/core/profile.html`)
- **Layout:** `profile-layout` (320px Sidebar + flex Content)
- **Custom CSS Klassen:**
  - Container: `profile-layout`
  - Sidebar: `sidebar-profile` (320px fest, sticky)
  - Content: `content-main` (flex: 1)
- **Features:**
  - Sidebar: Avatar mit Edit-Overlay, Name/Position, Stats (Progress-Bars), Action-Buttons
  - Content: 4 Tabs (Übersicht, Persönliche Daten, Qualifikationen, Aktivitäten)
  - Alpine.js Tab-Navigation
- **Status:** ✅ Implementiert und getestet

#### 3. Einstellungen (`templates/core/settings.html`)
- **Layout:** `settings-layout` (280px Sidebar + flex Content)
- **Custom CSS Klassen:**
  - Container: `settings-layout`
  - Sidebar: `sidebar-nav` (280px fest)
  - Content: `content-area` (flex: 1)
- **Features:**
  - Sidebar: 6 Sections (Account, Benachrichtigungen, Darstellung, Sicherheit, Datenschutz, System)
  - Content: Section-basierte Formulare mit Alpine.js Section-Switching
  - Theme-Auswahl mit visuellen Cards
  - 2FA-Status Anzeige
  - Aktive Sitzungen Liste
- **Status:** ✅ Implementiert und getestet

---

## 🛠️ Technische Hinweise

### Alpine.js Integration

**Tab-Navigation (Profil):**
```django
<nav x-data="{ activeTab: 'overview' }">
    <button @click="activeTab = 'overview'" :class="activeTab === 'overview' ? 'active' : ''">
        Übersicht
    </button>
</nav>

<div x-show="activeTab === 'overview'" x-cloak>
    <!-- Tab Content -->
</div>
```

**Section-Navigation (Einstellungen mit Sub-Templates):**

**Haupt-Template:**
```django
<div x-data="{ activeSection: 'account' }">
    <button @click="activeSection = 'account'">Account</button>
    <button @click="activeSection = 'notifications'">Benachrichtigungen</button>

    <!-- Include Sub-Templates -->
    {% include 'core/settings/account.html' %}
    {% include 'core/settings/notifications.html' %}
</div>
```

**Sub-Template (z.B. `account.html`):**
```django
<div x-show="activeSection === 'account'" x-cloak class="p-6">
    <h2 class="text-2xl font-bold text-gray-900 mb-6">Account-Einstellungen</h2>
    <form method="post">
        {% csrf_token %}
        <!-- Form-Felder -->
    </form>
</div>
```

**Wichtig:** `x-cloak` CSS hinzufügen:
```css
[x-cloak] { display: none !important; }
```

**Best Practice für große Formulare:**
- **Haupt-Template** enthält nur Layout & Navigation
- **Sub-Templates** enthalten die Section-spezifischen Inhalte
- Jede Section = eigene Datei in `templates/<app>/<page>/`
- Vorteile: Wartbarkeit, Wiederverwendbarkeit, Team-Arbeit

### Form-Integration

**Django Forms in Templates:**
```django
<form method="post">
    {% csrf_token %}
    <label>{{ form.email.label }}</label>
    {{ form.email }}
    {% if form.email.errors %}
        <p class="error">{{ form.email.errors.0 }}</p>
    {% endif %}
</form>
```

**Tailwind Form Styling (in forms.py):**
```python
widgets = {
    'email': forms.EmailInput(attrs={
        'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500',
        'placeholder': 'email@example.com'
    })
}
```

---

## 🔄 Update-Historie

### Version 1.2 (2025-10-04)
- ✅ Sub-Template Pattern für Einstellungen-Seite implementiert
- ✅ 6 modulare Sub-Templates erstellt (Account, Notifications, Appearance, Security, Privacy, System)
- ✅ Best-Practice-Dokumentation für Template-Modularisierung
- ✅ Code-Reduktion: Haupt-Template von 573 auf 119 Zeilen
- ✅ Erweiterte Features: Benachrichtigungs-Kategorien, Sicherheits-Empfehlungen, DSGVO-Compliance

### Version 1.1 (2025-10-03)
- ✅ Custom CSS Layout-System dokumentiert
- ✅ Profil-Template implementiert
- ✅ Einstellungen-Template implementiert
- ✅ Alpine.js Integration dokumentiert
- ✅ Technische Hinweise hinzugefügt

### Version 1.0 (2025-10-03)
- Initial: Visuelle Strukturbeschreibungen für alle Module
- Personal-Verwaltung Templates definiert
- BTM-Bereich Spezifikationen

---

## 📝 Offene Template-Implementierungen

**Noch zu implementieren:**
- [ ] Personal-Verwaltung (Dashboard, Liste, Detail, Qualifikationen)
- [ ] Medizinische Verwaltung (Medikamente, BTM-Bereich, Chargen)
- [ ] Fahrzeugverwaltung (Liste, Detail, Fahrzeugübernahme)
- [ ] Ausrüstung (Equipment-Liste, Prüfungen)
- [ ] Kleiderkammer (Ausgabe, Rücknahme)
- [ ] Reports & KPIs (Dashboard-Builder, Charts)

---

**Letzte Aktualisierung:** 2025-10-04 (Version 1.2 - Settings Sub-Templates)
**Verantwortlich:** Claude Code
**Nächste Review:** Bei neuer Template-Implementation

---

## 📊 Template-Implementierungs-Roadmap

### Phase 1: Core Templates ✅ ABGESCHLOSSEN
- ✅ Dashboard (KPI-Cards, Module-Tiles)
- ✅ Profil (4 Tabs mit 320px Sidebar)
- ✅ **Einstellungen (6 Sub-Templates - MODULARISIERT)**

### Phase 2: Personal-Verwaltung 🔜 NÄCHSTE
- Personal-Dashboard
- Personal-Liste (mit Filter-Sidebar)
- **Personal-Detail (6 Tabs) → Sub-Templates verwenden**
- Qualifikations-Verwaltung
- Prüfungskalender
- Schulungsverwaltung

### Phase 3: Inventar-Module 🔜
- **Medikamente-Detail (5 Tabs) → Sub-Templates verwenden**
- Fahrzeugverwaltung (Multi-Step Forms)
- Ausrüstungs-Listen
- BTM-Bereich (Sicherheits-UI)

### Phase 4: Advanced Features 🔜
- **Dashboard-Builder (Widget-Typen als Sub-Templates)**
- Fahrzeugübernahme (Multi-Step Wizard)
- Reports & KPIs
- Info-Monitore

