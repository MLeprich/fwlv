# UI/UX Implementation Guide - FLVS

## 📋 Übersicht

Diese Datei beschreibt die konkrete Umsetzung des UI/UX-Designs für das FLVS mit Django, HTMX und Tailwind CSS.

---

## 🎨 Design-Tokens

### Tailwind Config (bereits in base.html eingebunden)

```javascript
// Feuerwehr-Rot als Primary Color
primary: {
    50: '#FEF2F2',
    100: '#FEE2E2',
    200: '#FECACA',
    300: '#FCA5A5',
    400: '#F87171',
    500: '#EF4444',
    600: '#DC2626',  // Haupt-Akzentfarbe
    700: '#B91C1C',
    800: '#991B1B',
    900: '#7F1D1D',
}
```

### Spacing-System
- **Container-Padding:** px-6 py-4
- **Card-Padding:** p-5
- **Gap zwischen Elementen:** gap-4 (Standard), gap-6 (großzügig)
- **Margins:** mb-4 (Standard), mb-6 (Section-Trennung)

### Typography
- **Headings:** font-semibold text-gray-900
- **Body Text:** text-gray-700
- **Small Text:** text-sm text-gray-500
- **Labels:** text-sm font-medium text-gray-700

---

## 📁 Template-Struktur

### Ordner-Organisation

```
templates/
├── base.html                    # Haupt-Layout
├── dashboard.html               # Dashboard
├── includes/
│   ├── sidebar_nav.html        # Navigation
│   ├── notifications.html      # Notification Dropdown
│   ├── modals/
│   │   ├── modal_base.html     # Modal-Basis
│   │   └── confirm_modal.html  # Bestätigungs-Modal
│   └── components/
│       ├── card.html           # Card-Component
│       ├── badge.html          # Badge-Component
│       ├── button.html         # Button-Component
│       └── table.html          # Table-Component
│
├── medical/                     # Modul-Templates
│   ├── dashboard.html          # Modul-Übersicht (Kacheln)
│   ├── medication_list.html    # Listen-Ansicht
│   ├── medication_detail.html  # Detail-Ansicht
│   ├── medication_form.html    # Formular
│   └── partials/               # HTMX-Partials
│       ├── medication_row.html
│       ├── medication_card.html
│       └── medication_form_fields.html
│
├── vehicles/
├── personnel/
└── ...
```

---

## 🧩 Component Library

### 1. Buttons

**Primary Button**
```html
<button class="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors shadow-sm font-medium">
    Speichern
</button>
```

**Secondary Button**
```html
<button class="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors font-medium">
    Abbrechen
</button>
```

**Danger Button**
```html
<button class="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors shadow-sm font-medium">
    Löschen
</button>
```

**Icon Button**
```html
<button class="p-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors">
    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/>
    </svg>
</button>
```

### 2. Cards

**Standard Card**
```html
<div class="bg-white rounded-lg shadow overflow-hidden">
    <div class="px-5 py-4 border-b border-gray-200">
        <h3 class="font-semibold text-gray-900">Titel</h3>
    </div>
    <div class="p-5">
        <!-- Content -->
    </div>
    <div class="px-5 py-4 bg-gray-50 border-t border-gray-200">
        <!-- Footer Actions -->
    </div>
</div>
```

**Modul-Kachel (Dashboard)**
```html
<a href="{% url 'module:dashboard' %}" 
   class="group bg-white rounded-lg shadow hover:shadow-lg transition-all p-6 border-2 border-transparent hover:border-primary-200">
    <div class="flex items-start justify-between mb-3">
        <span class="text-4xl">💊</span>
        <span class="bg-red-100 text-red-700 text-xs px-2 py-1 rounded-full font-semibold">
            5
        </span>
    </div>
    <h3 class="font-semibold text-gray-900 mb-1 group-hover:text-primary-600">
        Rettungsdienst
    </h3>
    <p class="text-sm text-gray-500">
        Medikamente & Medizintechnik
    </p>
</a>
```

### 3. Badges

**Status Badges**
```html
<!-- Success -->
<span class="px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800">
    Aktiv
</span>

<!-- Warning -->
<span class="px-2 py-1 text-xs font-semibold rounded-full bg-yellow-100 text-yellow-800">
    Niedrig
</span>

<!-- Critical -->
<span class="px-2 py-1 text-xs font-semibold rounded-full bg-orange-100 text-orange-800">
    Kritisch
</span>

<!-- Danger -->
<span class="px-2 py-1 text-xs font-semibold rounded-full bg-red-100 text-red-800">
    Abgelaufen
</span>

<!-- Info -->
<span class="px-2 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-800">
    Info
</span>
```

### 4. Forms

**Input Field**
```html
<div>
    <label class="block text-sm font-medium text-gray-700 mb-1">
        Bezeichnung
    </label>
    <input 
        type="text"
        name="name"
        class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
        required
    />
    <p class="mt-1 text-sm text-gray-500">
        Helper-Text hier
    </p>
</div>
```

**Error State**
```html
<div>
    <label class="block text-sm font-medium text-gray-700 mb-1">
        Bezeichnung
    </label>
    <input 
        type="text"
        class="w-full px-3 py-2 border-2 border-red-300 rounded-lg focus:ring-2 focus:ring-red-500"
    />
    <p class="mt-1 text-sm text-red-600">
        Dieses Feld ist erforderlich
    </p>
</div>
```

**Select**
```html
<select class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500">
    <option value="">Bitte wählen</option>
    <option value="1">Option 1</option>
    <option value="2">Option 2</option>
</select>
```

### 5. Tables

**Responsive Table (siehe list_view.html)**

### 6. Modals

**Modal Base**
```html
<!-- Modal Overlay -->
<div 
    class="fixed inset-0 bg-gray-500 bg-opacity-75 z-50 flex items-center justify-center p-4"
    x-data="{ show: true }"
    x-show="show"
    x-transition
    @click.self="show = false"
>
    <!-- Modal Content -->
    <div class="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-hidden">
        
        <!-- Header -->
        <div class="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
            <h3 class="text-lg font-semibold text-gray-900">
                Modal Titel
            </h3>
            <button 
                @click="show = false"
                class="text-gray-400 hover:text-gray-600"
            >
                <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                </svg>
            </button>
        </div>

        <!-- Body (scrollable) -->
        <div class="px-6 py-4 overflow-y-auto max-h-[60vh]">
            <!-- Content -->
        </div>

        <!-- Footer -->
        <div class="px-6 py-4 bg-gray-50 border-t border-gray-200 flex items-center justify-end gap-3">
            <button 
                @click="show = false"
                class="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
            >
                Abbrechen
            </button>
            <button class="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700">
                Speichern
            </button>
        </div>
    </div>
</div>
```

### 7. Toasts/Notifications

**Toast**
```html
<div 
    class="max-w-sm w-full bg-white shadow-lg rounded-lg pointer-events-auto ring-1 ring-black ring-opacity-5"
    x-data="{ show: true }"
    x-show="show"
    x-init="setTimeout(() => show = false, 5000)"
    x-transition
>
    <div class="p-4">
        <div class="flex items-start">
            <div class="flex-shrink-0">
                <!-- Success Icon -->
                <svg class="h-6 w-6 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                </svg>
            </div>
            <div class="ml-3 w-0 flex-1">
                <p class="text-sm font-medium text-gray-900">
                    Erfolgreich gespeichert
                </p>
                <p class="mt-1 text-sm text-gray-500">
                    Die Änderungen wurden übernommen.
                </p>
            </div>
            <div class="ml-4 flex-shrink-0 flex">
                <button 
                    @click="show = false"
                    class="rounded-md inline-flex text-gray-400 hover:text-gray-500"
                >
                    <svg class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                        <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"/>
                    </svg>
                </button>
            </div>
        </div>
    </div>
</div>
```

---

## 🎯 HTMX-Patterns

### 1. Inline Editing

```html
<!-- Display Mode -->
<div 
    id="item-quantity-{{ item.id }}"
    hx-get="{% url 'edit_quantity' item.id %}"
    hx-target="#item-quantity-{{ item.id }}"
    hx-swap="outerHTML"
    class="cursor-pointer hover:bg-gray-50 p-2 rounded"
>
    <span>{{ item.quantity }} {{ item.unit }}</span>
    <span class="text-gray-400 ml-2">✏️</span>
</div>

<!-- Edit Mode (returned by HTMX) -->
<form 
    id="item-quantity-{{ item.id }}"
    hx-post="{% url 'update_quantity' item.id %}"
    hx-target="#item-quantity-{{ item.id }}"
    hx-swap="outerHTML"
    class="flex items-center gap-2"
>
    {% csrf_token %}
    <input 
        type="number" 
        name="quantity" 
        value="{{ item.quantity }}"
        class="w-20 px-2 py-1 border border-gray-300 rounded"
        autofocus
    />
    <button type="submit" class="text-green-600 hover:text-green-700">✓</button>
    <button 
        type="button"
        hx-get="{% url 'cancel_edit_quantity' item.id %}"
        hx-target="#item-quantity-{{ item.id }}"
        class="text-red-600 hover:text-red-700"
    >✗</button>
</form>
```

### 2. Modal Forms

```html
<!-- Trigger Button -->
<button 
    hx-get="{% url 'medication:create' %}"
    hx-target="#modal-container"
    hx-swap="innerHTML"
    class="btn-primary"
>
    Neues Medikament
</button>

<!-- Modal Container (in base.html) -->
<div id="modal-container"></div>

<!-- Modal Template (returned by view) -->
<div class="fixed inset-0 bg-gray-500 bg-opacity-75 z-50 flex items-center justify-center">
    <div class="bg-white rounded-lg shadow-xl max-w-2xl w-full">
        <form 
            hx-post="{% url 'medication:create' %}"
            hx-target="#modal-container"
            hx-swap="outerHTML"
        >
            {% csrf_token %}
            <!-- Form Fields -->
            
            <div class="px-6 py-4 bg-gray-50 border-t flex justify-end gap-3">
                <button 
                    type="button"
                    onclick="document.getElementById('modal-container').innerHTML = ''"
                    class="btn-secondary"
                >
                    Abbrechen
                </button>
                <button type="submit" class="btn-primary">
                    Speichern
                </button>
            </div>
        </form>
    </div>
</div>
```

### 3. Infinite Scroll

```html
<div id="items-container">
    {% for item in items %}
        {% include 'partials/item_card.html' %}
    {% endfor %}
</div>

<!-- Load More Trigger -->
{% if has_more %}
<div 
    hx-get="{% url 'items' %}?page={{ page|add:1 }}"
    hx-trigger="revealed"
    hx-swap="afterend"
    class="text-center py-4"
>
    <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mx-auto"></div>
</div>
{% endif %}
```

### 4. Live Search

```html
<input 
    type="search"
    name="q"
    placeholder="Suchen..."
    hx-get="{% url 'search' %}"
    hx-trigger="keyup changed delay:300ms"
    hx-target="#search-results"
    hx-indicator="#search-loading"
    class="w-full px-4 py-2 border border-gray-300 rounded-lg"
/>

<div id="search-loading" class="htmx-indicator">
    Suche läuft...
</div>

<div id="search-results"></div>
```

### 5. Dependent Selects

```html
<!-- Standort Select -->
<select 
    name="site"
    hx-get="{% url 'get_buildings' %}"
    hx-target="#building-select"
    hx-trigger="change"
>
    <option value="">Standort wählen</option>
    {% for site in sites %}
    <option value="{{ site.id }}">{{ site.name }}</option>
    {% endfor %}
</select>

<!-- Building Select (wird dynamisch geladen) -->
<div id="building-select">
    <select name="building" disabled>
        <option value="">Erst Standort wählen</option>
    </select>
</div>
```

### 6. Optimistic UI Updates

```html
<button 
    hx-post="{% url 'toggle_favorite' item.id %}"
    hx-swap="outerHTML"
    class="text-gray-400 hover:text-yellow-500"
>
    {% if item.is_favorite %}
    <span class="text-yellow-500">⭐</span>
    {% else %}
    <span>☆</span>
    {% endif %}
</button>
```

---

## 📱 Responsive Design

### Breakpoints verwenden

```html
<!-- Mobile: Stack, Desktop: Grid -->
<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
    <!-- Items -->
</div>

<!-- Mobile: Hidden, Desktop: Visible -->
<div class="hidden lg:block">
    <!-- Sidebar -->
</div>

<!-- Mobile: Visible, Desktop: Hidden -->
<div class="lg:hidden">
    <!-- Mobile Menu -->
</div>
```

### Mobile Navigation

```html
<!-- Mobile Hamburger Menu -->
<button 
    @click="mobileMenuOpen = true"
    class="lg:hidden p-2 rounded-lg hover:bg-gray-100"
>
    <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"/>
    </svg>
</button>

<!-- Mobile Sidebar (Drawer) -->
<div 
    x-show="mobileMenuOpen"
    x-transition
    @click.away="mobileMenuOpen = false"
    class="fixed inset-0 z-50 lg:hidden"
>
    <div class="fixed inset-0 bg-gray-600 bg-opacity-75"></div>
    <div class="fixed inset-y-0 left-0 w-64 bg-white shadow-xl">
        <!-- Navigation -->
    </div>
</div>
```

---

## 🎨 Context-Specific Styling

### BTM-Bereich (Extra Sicherheit)

```html
<!-- BTM Warning Banner -->
<div class="bg-red-900 text-white px-6 py-3 flex items-center justify-between">
    <div class="flex items-center gap-3">
        <span class="text-2xl">⚠️</span>
        <div>
            <p class="font-semibold">Betäubungsmittel-Bereich</p>
            <p class="text-sm text-red-200">Alle Aktionen werden protokolliert</p>
        </div>
    </div>
    <div class="text-sm">
        Session: <span id="session-timer" class="font-mono">15:00</span>
    </div>
</div>

<!-- BTM Card mit dunklerem Rot -->
<div class="bg-white rounded-lg shadow border-l-4 border-red-800">
    <!-- Content -->
</div>
```

### Ablaufdatum-Farbcodierung

```html
{% if item.days_until_expiry < 0 %}
    <span class="px-2 py-1 text-xs font-semibold rounded-full bg-red-100 text-red-800">
        Abgelaufen
    </span>
{% elif item.days_until_expiry <= 30 %}
    <span class="px-2 py-1 text-xs font-semibold rounded-full bg-orange-100 text-orange-800">
        {{ item.days_until_expiry }} Tage
    </span>
{% elif item.days_until_expiry <= 90 %}
    <span class="px-2 py-1 text-xs font-semibold rounded-full bg-yellow-100 text-yellow-800">
        {{ item.days_until_expiry }} Tage
    </span>
{% else %}
    <span class="px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800">
        OK
    </span>
{% endif %}
```

### Fahrzeugübernahme Touch-Optimiert

```html
<!-- Große Checkboxes -->
<label class="flex items-center gap-4 p-4 bg-white rounded-lg border-2 border-gray-200 hover:border-primary-300 cursor-pointer">
    <input 
        type="checkbox" 
        class="w-6 h-6 rounded border-gray-300 text-primary-600"
    />
    <div class="flex-1">
        <p class="font-medium text-gray-900">Fach 1 - Vorne Links</p>
        <p class="text-sm text-gray-500">Verbandskasten, Warnweste</p>
    </div>
    <span class="text-2xl">✅</span>
</label>
```

---

## 🚀 Performance-Optimierungen

### Lazy Loading für Bilder

```html
<img 
    src="{{ item.photo.url }}"
    loading="lazy"
    class="w-full h-48 object-cover rounded-lg"
    alt="{{ item.name }}"
/>
```

### HTMX Caching

```html
<!-- Cache GET Requests -->
<button 
    hx-get="{% url 'item_details' item.id %}"
    hx-target="#details"
    hx-swap="innerHTML"
    hx-push-url="true"
    hx-cache="true"
>
    Details
</button>
```

### Conditional Loading

```html
<!-- Nur laden wenn sichtbar -->
<div 
    hx-get="{% url 'expensive_data' %}"
    hx-trigger="revealed"
    hx-swap="innerHTML"
>
    <div class="animate-pulse">Lädt...</div>
</div>
```

---

## ♿ Accessibility

### Screen Reader Support

```html
<!-- ARIA Labels für Icons -->
<button aria-label="Löschen">
    <svg>...</svg>
</button>

<!-- SR-Only Text -->
<span class="sr-only">Nur für Screen Reader</span>

<!-- Live Regions -->
<div aria-live="polite" aria-atomic="true">
    {{ status_message }}
</div>
```

### Keyboard Navigation

```html
<!-- Tab-Index für Custom-Controls -->
<div 
    role="button"
    tabindex="0"
    @keydown.enter="handleClick"
    @keydown.space.prevent="handleClick"
>
    Custom Button
</div>

<!-- Skip Links -->
<a href="#main-content" class="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 bg-white px-4 py-2 rounded">
    Zum Hauptinhalt springen
</a>
```

### Focus Management

```html
<!-- Sichtbarer Focus Ring -->
<style>
*:focus {
    outline: 2px solid #DC2626;
    outline-offset: 2px;
}
</style>

<!-- Focus Trap in Modals -->
<div 
    x-data="{ trapFocus: true }"
    @keydown.tab="trapFocus && handleTab($event)"
>
    <!-- Modal Content -->
</div>
```

---

## 🎯 View-Context für Templates

### Context Processor erstellen

```python
# core/context_processors.py
def flvs_context(request):
    """Globaler Context für alle Templates"""
    context = {
        'today': timezone.now().date(),
        'current_module': request.resolver_match.app_name if request.resolver_match else None,
    }
    
    if request.user.is_authenticated:
        # Notification Count
        context['notification_count'] = Notification.objects.filter(
            recipient=request.user,
            is_read=False
        ).count()
        
        # Critical Alerts
        context['critical_alerts'] = get_critical_alerts(request.user)
        
        # Module Badges
        context['critical_medications_count'] = get_critical_medications_count()
        context['pending_inspections'] = get_pending_inspections_count()
        context['pending_approvals'] = get_pending_approvals_count(request.user)
        
    return context

# settings.py
TEMPLATES = [{
    'OPTIONS': {
        'context_processors': [
            # ...
            'core.context_processors.flvs_context',
        ],
    },
}]
```

### View mit Context für Dashboard

```python
# core/views.py
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        user = self.request.user
        
        # Quick Stats
        context['critical_stock_count'] = InventoryItem.objects.filter(
            quantity__lte=F('threshold_critical')
        ).count()
        
        context['upcoming_inspections'] = Inspection.objects.filter(
            scheduled_date__lte=timezone.now().date() + timedelta(days=30),
            status='pending'
        ).count()
        
        context['pending_orders'] = Order.objects.filter(
            status__in=['pending_approval', 'approved_l1']
        ).count()
        
        context['operational_vehicles'] = Vehicle.objects.filter(
            status='active'
        ).count()
        
        context['total_vehicles'] = Vehicle.objects.count()
        
        # Heute Wichtig
        context['my_tasks'] = Task.objects.filter(
            assigned_to=user,
            status='pending',
            due_date__lte=timezone.now().date() + timedelta(days=7)
        ).order_by('due_date')[:5]
        
        context['recent_notifications'] = Notification.objects.filter(
            recipient=user
        ).order_by('-created_at')[:5]
        
        # Module-spezifische Counts
        if user.has_perm('medical.view_medication'):
            context['critical_medications_count'] = Medication.objects.filter(
                quantity__lte=F('threshold_critical')
            ).count()
        
        if user.has_perm('vehicles.view_vehicle'):
            context['vehicles_in_maintenance'] = Vehicle.objects.filter(
                status__in=['maintenance', 'repair']
            ).count()
        
        # Letzte Aktivitäten
        context['recent_activities'] = AuditLog.objects.filter(
            user__in=User.objects.filter(is_active=True)
        ).select_related('user').order_by('-timestamp')[:8]
        
        return context
```

---

## 📋 Checkliste für neue Module

Beim Erstellen eines neuen Moduls:

- [ ] **Dashboard-Template** mit Kacheln für Untermenüs
- [ ] **Listen-Ansicht** mit Filtern, Suche, Pagination
- [ ] **Detail-Ansicht** mit Tabs für verschiedene Bereiche
- [ ] **Formular** (Create/Update) als Modal oder eigene Seite
- [ ] **HTMX-Partials** für dynamische Updates
- [ ] **Sidebar-Eintrag** in `sidebar_nav.html`
- [ ] **Breadcrumb** in allen Templates
- [ ] **Context Actions** für häufige Aktionen
- [ ] **Permissions-Checks** in Templates (`{% if perms.app.action %}`)
- [ ] **Icons** (Unicode) für Modul
- [ ] **Badges** für Counts/Status in Sidebar
- [ ] **Mobile-Optimierung** testen
- [ ] **Accessibility** prüfen (Keyboard, Screen Reader)

---

## 🎨 Beispiel: Neues Modul komplett

### 1. URLs definieren

```python
# mymodule/urls.py
from django.urls import path
from . import views

app_name = 'mymodule'

urlpatterns = [
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('items/', views.ItemListView.as_view(), name='item_list'),
    path('items/<int:pk>/', views.ItemDetailView.as_view(), name='item_detail'),
    path('items/create/', views.ItemCreateView.as_view(), name='item_create'),
    path('items/<int:pk>/edit/', views.ItemUpdateView.as_view(), name='item_update'),
    path('items/<int:pk>/delete/', views.ItemDeleteView.as_view(), name='item_delete'),
]
```

### 2. Views erstellen

```python
# mymodule/views.py
from django.views.generic import TemplateView, ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from .models import MyItem
from .forms import MyItemForm

class DashboardView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    template_name = 'mymodule/dashboard.html'
    permission_required = 'mymodule.view_myitem'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_module'] = 'mymodule'
        context['total_items'] = MyItem.objects.count()
        context['critical_items'] = MyItem.objects.filter(
            quantity__lte=F('threshold_critical')
        ).count()
        return context

class ItemListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = MyItem
    template_name = 'mymodule/item_list.html'
    permission_required = 'mymodule.view_myitem'
    context_object_name = 'items'
    paginate_by = 25
    
    def get_queryset(self):
        qs = super().get_queryset()
        
        # Suche
        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(name__icontains=q)
        
        # Filter
        status = self.request.GET.get('status')
        if status:
            qs = qs.filter(status=status)
        
        return qs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_module'] = 'mymodule'
        context['module_name'] = 'Mein Modul'
        context['can_add'] = self.request.user.has_perm('mymodule.add_myitem')
        context['can_edit'] = self.request.user.has_perm('mymodule.change_myitem')
        context['can_delete'] = self.request.user.has_perm('mymodule.delete_myitem')
        return context
```

### 3. Templates erstellen

```
mymodule/
├── dashboard.html
├── item_list.html
├── item_detail.html
├── item_form.html
└── partials/
    ├── item_card.html
    └── item_row.html
```

### 4. Sidebar-Eintrag hinzufügen

```html
<!-- In sidebar_nav.html -->
{% if perms.mymodule.view_myitem %}
<a 
    href="{% url 'mymodule:dashboard' %}"
    class="flex items-center gap-3 px-3 py-2 mx-2 rounded-lg transition-colors
           {% if current_module == 'mymodule' %}bg-primary-50 text-primary-700{% else %}text-gray-700 hover:bg-gray-100{% endif %}"
>
    <span class="text-xl flex-shrink-0">🎯</span>
    <span class="text-sm truncate">Mein Modul</span>
</a>
{% endif %}
```

---

## 🔧 Django Template Tags für UI

### Custom Template Tags erstellen

```python
# mymodule/templatetags/mymodule_tags.py
from django import template
from django.utils.html import format_html

register = template.Library()

@register.simple_tag
def status_badge(status):
    """Rendert einen Status-Badge"""
    colors = {
        'active': 'green',
        'low_stock': 'yellow',
        'critical': 'orange',
        'expired': 'red',
    }
    labels = {
        'active': 'Aktiv',
        'low_stock': 'Niedrig',
        'critical': 'Kritisch',
        'expired': 'Abgelaufen',
    }
    
    color = colors.get(status, 'gray')
    label = labels.get(status, status)
    
    return format_html(
        '<span class="px-2 py-1 text-xs font-semibold rounded-full bg-{}-100 text-{}-800">{}</span>',
        color, color, label
    )

@register.inclusion_tag('components/card.html')
def card(title, icon=None):
    """Rendert eine Card-Komponente"""
    return {'title': title, 'icon': icon}

@register.filter
def days_until(date):
    """Berechnet Tage bis zu einem Datum"""
    from datetime import date as dt
    if not date:
        return None
    delta = date - dt.today()
    return delta.days
```

**Verwendung:**
```html
{% load mymodule_tags %}

{{ item.status|status_badge }}
{{ item.expiry_date|days_until }} Tage
```

---

## 📱 Progressive Web App (PWA) Features

### Service Worker für Offline-Nutzung

```javascript
// static/js/sw.js
const CACHE_NAME = 'flvs-v1';
const urlsToCache = [
    '/',
    '/static/css/main.css',
    '/static/js/main.js',
];

self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => cache.addAll(urlsToCache))
    );
});

self.addEventListener('fetch', event => {
    event.respondWith(
        caches.match(event.request)
            .then(response => response || fetch(event.request))
    );
});
```

### Web App Manifest

```json
{
    "name": "FLVS - Feuerwehr Lagerverwaltung",
    "short_name": "FLVS",
    "start_url": "/",
    "display": "standalone",
    "background_color": "#ffffff",
    "theme_color": "#DC2626",
    "icons": [
        {
            "src": "/static/icons/icon-192.png",
            "sizes": "192x192",
            "type": "image/png"
        },
        {
            "src": "/static/icons/icon-512.png",
            "sizes": "512x512",
            "type": "image/png"
        }
    ]
}
```

---

## ✅ Zusammenfassung

### Claude Code Prompt für UI-Erstellung

```
Ich möchte das UI für Modul X implementieren. Verwende:
- Das Layout aus base.html
- Tailwind CSS für Styling (Feuerwehr-Rot: primary-600)
- HTMX für Interaktionen
- Alpine.js für Client-Side State
- Unicode Icons
- Die Component-Patterns aus UI_IMPLEMENTATION.md

Erstelle:
1. Dashboard mit Kacheln (mymodule/dashboard.html)
2. Listen-Ansicht mit Filtern (mymodule/item_list.html)
3. Detail-Ansicht (mymodule/item_detail.html)
4. Modal-Formular (mymodule/item_form.html)
5. HTMX-Partials für dynamische Updates
6. Context Processor für Sidebar-Badges

Beachte:
- Responsive Design (Mobile First)
- Accessibility (ARIA, Keyboard)
- Permission-Checks in Templates
- Breadcrumb-Navigation
- Context Actions Bar
```

---

*Version: 1.0*  
*Letzte Aktualisierung: [Datum]*
