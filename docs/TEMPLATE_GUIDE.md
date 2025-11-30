# FLVS Template Development Guide

**Version:** 1.0
**Letzte Aktualisierung:** 2025-10-03
**Tech Stack:** Django Templates + HTMX + Alpine.js + Tailwind CSS

---

## 📚 Übersicht

Dieser Guide beschreibt die Template-Entwicklung für FLVS (Feuerwehr Lagerverwaltungssystem) basierend auf dem UI/UX Design System.

**Architektur:**
```
Django Templates (Backend-Rendering)
    ↓
HTMX (Partial Updates, AJAX ohne JavaScript)
    ↓
Alpine.js (Client-Side State Management)
    ↓
Tailwind CSS (Utility-First CSS Framework)
```

---

## 📁 Template-Struktur

```
templates/
├── base.html                       # Haupt-Layout (Header, Sidebar, Footer)
├── dashboard.html                  # Main Dashboard
├── includes/
│   ├── sidebar_nav.html           # Navigation (hierarchisch)
│   ├── notifications.html         # Notifications Dropdown
│   └── components/                # Wiederverwendbare Components
│       ├── card.html              # Card-Component ✅
│       ├── badge.html             # Badge-Component ✅
│       ├── button.html            # Button-Component ✅
│       ├── table.html             # Table-Component ✅
│       ├── modal.html             # Modal-Component
│       ├── form_field.html        # Form-Field-Component
│       └── pagination.html        # Pagination-Component
│
├── medical/                       # App-spezifische Templates
│   ├── medication_list.html       # Listen-Ansicht ✅
│   ├── medication_detail.html     # Detail-Ansicht
│   ├── medication_form.html       # Formular
│   └── partials/                  # HTMX-Partials
│       ├── medication_table.html  # Table-Partial ✅
│       ├── medication_row.html    # Single Row (für inline edit)
│       ├── medication_card.html   # Card-Ansicht
│       └── stock_modal.html       # Bestandsbewegung Modal
│
├── equipment/
├── vehicles/
└── ...
```

---

## 🧩 Component Library

### 1. Card Component

**File:** `templates/includes/components/card.html`

**Usage:**
```django
{% include 'includes/components/card.html' with
    title="Medikamente"
    subtitle="24 Artikel"
    icon="💊"
    badge="BTM"
    badge_color="critical"
%}
    <p>Card-Inhalt hier...</p>
{% endinclude %}
```

**Parameters:**
- `title` (optional): Card-Titel
- `subtitle` (optional): Card-Untertitel
- `icon` (optional): Icon (Emoji oder SVG)
- `badge` (optional): Badge-Text
- `badge_color` (optional): success, warning, danger, info, critical
- `actions` (optional): Action-Buttons HTML

**Output:**
```html
<div class="bg-white border rounded-lg shadow-sm">
    <div class="px-5 py-4 border-b">
        <!-- Header mit Title, Icon, Badge -->
    </div>
    <div class="p-5">
        <!-- Content -->
    </div>
</div>
```

---

### 2. Badge Component

**File:** `templates/includes/components/badge.html`

**Usage:**
```django
{% include 'includes/components/badge.html' with text="BTM" color="critical" icon="⚠️" %}
{% include 'includes/components/badge.html' with text="Verfügbar" color="success" %}
{% include 'includes/components/badge.html' with text="Niedrig" color="warning" size="lg" %}
```

**Parameters:**
- `text` (required): Badge-Text
- `color` (optional): success, warning, danger, critical, info, primary, gray (default)
- `icon` (optional): Icon vor Text
- `size` (optional): sm, md (default), lg

**Farben:**
- `success`: Grün (für Verfügbar, Aktiv, etc.)
- `warning`: Gelb (für Niedrig, Warnung, etc.)
- `danger`: Rot (für Leer, Fehler, etc.)
- `critical`: Dunkelrot mit weißem Text (für BTM, Kritisch)
- `info`: Blau (für Info, Hinweise)
- `primary`: Feuerwehr-Rot
- `gray`: Grau (für Inaktiv, Standard)

---

### 3. Button Component

**File:** `templates/includes/components/button.html`

**Usage:**
```django
{# Primary Button #}
{% include 'includes/components/button.html' with
    text="Speichern"
    type="primary"
    icon="💾"
%}

{# Link als Button #}
{% include 'includes/components/button.html' with
    text="Neues Medikament"
    type="primary"
    icon="➕"
    href="/medical/medications/create/"
%}

{# HTMX Button #}
{% include 'includes/components/button.html' with
    text="Löschen"
    type="danger"
    hx_delete="/medical/medications/123/delete/"
    hx_confirm="Wirklich löschen?"
    hx_target="#medication-row-123"
%}
```

**Parameters:**
- `text` (required): Button-Text
- `type` (optional): primary, secondary, danger, success, ghost
- `icon` (optional): Icon (Emoji oder SVG)
- `icon_position` (optional): left (default), right
- `size` (optional): sm, md (default), lg
- `href` (optional): Link-URL (macht <a> statt <button>)
- `hx_*` (optional): HTMX-Attribute (hx_get, hx_post, hx_target, etc.)
- `disabled` (optional): Boolean
- `classes` (optional): Zusätzliche CSS-Klassen

**Button-Typen:**
- `primary`: Feuerwehr-Rot, weiße Schrift (Hauptaktionen)
- `secondary`: Grauer Border, graue Schrift (Sekundär-Aktionen)
- `danger`: Rot (Destruktive Aktionen)
- `success`: Grün (Bestätigungen)
- `ghost`: Transparent, nur Hover (Tertiary-Aktionen)

---

### 4. Table Component

**File:** `templates/includes/components/table.html`

**Usage:**
```django
{% include 'includes/components/table.html' with
    headers=headers
    items=medications
    striped=True
    hover=True
%}
```

**In View:**
```python
headers = [
    {'text': 'Name', 'sortable': True},
    {'text': 'Bestand', 'sortable': True},
    {'text': 'Status', 'sortable': False},
]
```

**Parameters:**
- `headers` (required): Liste von Header-Dicts
- `items` (required): QuerySet oder Liste
- `striped` (optional): Zebra-Striping
- `hover` (optional): Hover-Effect (default: True)
- `compact` (optional): Kompaktere Darstellung

---

## 🔄 HTMX Integration

### Konzept

**HTMX ermöglicht AJAX ohne JavaScript:**
- `hx-get`: GET-Request
- `hx-post`: POST-Request
- `hx-target`: Ziel-Element für Response
- `hx-swap`: Swap-Strategie (innerHTML, outerHTML, etc.)
- `hx-trigger`: Event-Trigger (click, keyup, revealed, etc.)

### Beispiel 1: Live-Search

**Template:**
```django
<input
    type="search"
    name="search"
    placeholder="Suche..."
    hx-get="{% url 'medical:medication_list' %}"
    hx-trigger="keyup changed delay:300ms"
    hx-target="#medication-list"
    hx-include="[name='category'], [name='btm']"
/>
```

**View:**
```python
def medication_list(request):
    search = request.GET.get('search', '')
    medications = MedicalItem.objects.filter(name__icontains=search)

    # Nur Partial bei HTMX-Request
    if request.headers.get('HX-Request'):
        return render(request, 'medical/partials/medication_table.html', {
            'medications': medications
        })

    # Vollständige Seite bei normalem Request
    return render(request, 'medical/medication_list.html', {
        'medications': medications,
        'categories': Category.objects.all(),
    })
```

### Beispiel 2: Modal öffnen

**Button:**
```django
<button
    hx-get="{% url 'medical:medication_stock_modal' medication.pk %}"
    hx-target="#modal-container"
    class="...">
    Bestandsbewegung
</button>
```

**View:**
```python
def medication_stock_modal(request, pk):
    medication = get_object_or_404(MedicalItem, pk=pk)
    return render(request, 'medical/partials/stock_modal.html', {
        'medication': medication,
    })
```

**Modal-Partial:**
```django
{# medical/partials/stock_modal.html #}
<div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
     @click.self="$el.remove()">
    <div class="bg-white rounded-lg p-6 max-w-2xl w-full">
        <h2 class="text-2xl font-bold mb-4">Bestandsbewegung: {{ medication.name }}</h2>

        <form hx-post="{% url 'medical:medication_stock' medication.pk %}"
              hx-target="#modal-container">
            {% csrf_token %}
            <!-- Form-Fields -->

            <div class="flex justify-end gap-3 mt-6">
                <button @click="$el.closest('.fixed').remove()"
                        type="button" class="...">
                    Abbrechen
                </button>
                <button type="submit" class="...">
                    Speichern
                </button>
            </div>
        </form>
    </div>
</div>
```

### Beispiel 3: Inline-Editing

**Table-Row:**
```django
<tr id="medication-row-{{ medication.pk }}">
    <td>{{ medication.name }}</td>
    <td>
        <button
            hx-get="{% url 'medical:medication_edit_inline' medication.pk %}"
            hx-target="#medication-row-{{ medication.pk }}"
            hx-swap="outerHTML">
            Bearbeiten
        </button>
    </td>
</tr>
```

**Edit-Partial:**
```django
{# medication_row_edit.html #}
<tr id="medication-row-{{ medication.pk }}">
    <td>
        <input type="text" name="name" value="{{ medication.name }}" />
    </td>
    <td>
        <button
            hx-post="{% url 'medical:medication_update_inline' medication.pk %}"
            hx-target="#medication-row-{{ medication.pk }}"
            hx-swap="outerHTML">
            Speichern
        </button>
    </td>
</tr>
```

---

## 🎨 Tailwind CSS Patterns

### Spacing

**Container-Padding:**
```django
<div class="px-6 py-4">  {# Standard #}
<div class="p-5">        {# Card-Body #}
```

**Gaps:**
```django
<div class="gap-4">      {# Standard #}
<div class="gap-6">      {# Großzügig #}
```

**Margins:**
```django
<div class="mb-4">       {# Standard #}
<div class="mb-6">       {# Section-Trennung #}
<div class="mb-8">       {# Page-Section #}
```

### Typography

**Headings:**
```django
<h1 class="text-3xl font-bold text-gray-900">       {# Page Title #}
<h2 class="text-2xl font-bold text-gray-900">       {# Section Title #}
<h3 class="text-lg font-semibold text-gray-900">    {# Card Title #}
```

**Body Text:**
```django
<p class="text-gray-700">                           {# Normal Text #}
<p class="text-sm text-gray-500">                   {# Small Text #}
<p class="text-xs text-gray-400">                   {# Tiny Text #}
```

**Labels:**
```django
<label class="text-sm font-medium text-gray-700">  {# Form Label #}
```

### Colors

**Primary (Feuerwehr-Rot):**
```django
bg-primary-600 text-white        {# Buttons #}
bg-primary-50 text-primary-800   {# Badges #}
border-primary-500               {# Borders #}
```

**Status:**
```django
bg-green-100 text-green-800      {# Success #}
bg-yellow-100 text-yellow-800    {# Warning #}
bg-red-100 text-red-800          {# Danger #}
bg-blue-100 text-blue-800        {# Info #}
```

### Hover & Focus

**Hover:**
```django
hover:bg-gray-50                 {# Row Hover #}
hover:bg-primary-700             {# Button Hover #}
```

**Focus:**
```django
focus:ring-2 focus:ring-primary-500 focus:border-transparent
```

---

## 🔌 Alpine.js Integration

### State Management

**Sidebar Toggle:**
```django
<body x-data="{ sidebarExpanded: false }">
    <button @click="sidebarExpanded = !sidebarExpanded">
        Toggle
    </button>

    <aside x-show="sidebarExpanded">
        Sidebar
    </aside>
</body>
```

**Notifications Dropdown:**
```django
<div x-data="{ showNotifications: false }">
    <button @click="showNotifications = !showNotifications">
        🔔
    </button>

    <div x-show="showNotifications" @click.away="showNotifications = false">
        Notifications
    </div>
</div>
```

**Modal:**
```django
<div x-data="{ showModal: false }">
    <button @click="showModal = true">
        Öffnen
    </button>

    <div x-show="showModal" @click.self="showModal = false">
        <div>Modal-Content</div>
    </div>
</div>
```

---

## 📋 Template-Patterns für Apps

### Listen-Ansicht

**Struktur:**
1. Breadcrumb-Navigation
2. Page-Header (Titel + Action-Buttons)
3. Filter & Search
4. Liste/Table
5. Pagination

**Template:**
```django
{% extends "base.html" %}

{% block content %}
<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">

    <!-- Breadcrumb -->
    <nav class="flex mb-6">...</nav>

    <!-- Page Header -->
    <div class="mb-8">
        <h1 class="text-3xl font-bold">Medikamente</h1>
        <div class="flex gap-3 mt-4">
            {% include 'includes/components/button.html' with ... %}
        </div>
    </div>

    <!-- Filters -->
    <div class="bg-white border rounded-lg p-4 mb-6">
        <div class="grid grid-cols-4 gap-4">
            <input hx-get="..." hx-trigger="keyup changed delay:300ms" />
            <select hx-get="..." hx-trigger="change" />
        </div>
    </div>

    <!-- List -->
    <div id="list-container">
        {% include 'app/partials/list_table.html' %}
    </div>

</div>
{% endblock %}
```

### Detail-Ansicht

**Struktur:**
1. Breadcrumb
2. Header (Titel + Status-Badges + Actions)
3. Tab-Navigation (bei viel Content)
4. Content-Sections (Grid-Layout)
5. Related Items (Bewegungen, Batches, etc.)

### Formular

**Struktur:**
1. Breadcrumb
2. Page-Header
3. Form (2-Spalten-Grid)
4. Submit-Buttons (Save, Cancel)

**Template:**
```django
<form method="post" hx-post="{% url '...' %}" hx-target="#form-container">
    {% csrf_token %}

    <div class="grid grid-cols-2 gap-6">
        <div>
            <label class="text-sm font-medium text-gray-700">Name</label>
            <input type="text" name="name" class="w-full px-4 py-2 border rounded-lg" />
        </div>

        <div>
            <label class="text-sm font-medium text-gray-700">Kategorie</label>
            <select name="category" class="w-full px-4 py-2 border rounded-lg">
                <option>...</option>
            </select>
        </div>
    </div>

    <div class="flex justify-end gap-3 mt-6">
        {% include 'includes/components/button.html' with text="Abbrechen" type="secondary" %}
        {% include 'includes/components/button.html' with text="Speichern" type="primary" %}
    </div>
</form>
```

---

## ✅ Best Practices

### 1. Component-First

**DO:**
```django
{% include 'includes/components/badge.html' with text="BTM" color="critical" %}
```

**DON'T:**
```django
<span class="px-2 py-1 bg-red-800 text-white rounded-full text-xs">BTM</span>
```

### 2. HTMX-Partials

**Partial-Template-Namen:**
- `partials/` Unterordner
- Beschreibender Name (`medication_table.html`, nicht `table.html`)
- Inkludiert nur HTML-Fragment (kein `{% extends %}`)

### 3. Responsive Design

**Mobile-First:**
```django
<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
```

**Breakpoints:**
- `sm`: 640px
- `md`: 768px
- `lg`: 1024px
- `xl`: 1280px

### 4. Accessibility

**Labels:**
```django
<label for="search">Suche</label>
<input id="search" type="search" />
```

**ARIA:**
```django
<button aria-label="Menü öffnen">☰</button>
```

**Focus-Styles:**
- Immer sichtbare Focus-Styles (`:focus`)
- Tastatur-Navigation testen

### 5. Performance

**Lazy-Loading:**
```django
<div hx-get="{% url '...' %}" hx-trigger="revealed">
    <p class="text-gray-500">Lädt...</p>
</div>
```

**Pagination:**
- Max 50 Items pro Seite
- Pagination-Component verwenden

---

## 📦 Deployment-Checklist

**Template-Optimierung:**
- [ ] Alle Components erstellt
- [ ] HTMX-Partials für dynamische Bereiche
- [ ] Responsive Design getestet
- [ ] Accessibility geprüft
- [ ] Performance-Tests (< 300ms Page Load)
- [ ] Browser-Testing (Chrome, Firefox, Edge, Safari)

---

**Template-Entwicklung ready! 🚀**

Alle wiederverwendbaren Components sind erstellt und dokumentiert.
