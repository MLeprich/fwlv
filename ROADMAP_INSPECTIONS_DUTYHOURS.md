# Roadmap: Prüfungen & Pflichtstunden Module

**Status:** Models und Forms erstellt, Migrations ausgeführt
**Datum:** 2025-10-16
**Ziel:** Vollständige Integration von Inspections und DutyHours in das Personal-Modul

---

## 📋 Modul 1: Prüfungen (Inspections)

### Phase 1.1: Backend - Views & URLs (2-3 Stunden)

#### 1.1.1 CRUD Views erstellen
**Datei:** `/var/www/lager.resqware.de/personnel/views.py`

```python
# Hinzufügen am Ende der Datei:

# ============================================================================
# INSPECTION VIEWS
# ============================================================================

class InspectionCreateView(LoginRequiredMixin, CreateView):
    """Prüfung zu Person hinzufügen"""
    model = Inspection
    form_class = InspectionForm
    template_name = 'personnel/inspection_form.html'

    def get_template_names(self):
        if self.request.headers.get('HX-Request'):
            return ['personnel/inspection_form_modal.html']
        return [self.template_name]

    def get_initial(self):
        initial = super().get_initial()
        person_id = self.kwargs.get('person_pk')
        if person_id:
            initial['person'] = person_id
            # Status auf PENDING setzen
            initial['status'] = 'pending'
        return initial

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user

        messages.success(
            self.request,
            f'Prüfung "{form.instance.title}" wurde erfolgreich hinzugefügt.'
        )

        response = super().form_valid(form)

        if self.request.headers.get('HX-Request'):
            return HttpResponse(
                status=200,
                headers={'HX-Redirect': self.get_success_url()}
            )

        return response

    def get_success_url(self):
        return reverse('personnel:detail', kwargs={'pk': self.object.person.pk})


class InspectionUpdateView(LoginRequiredMixin, UpdateView):
    """Prüfung bearbeiten"""
    model = Inspection
    form_class = InspectionForm
    template_name = 'personnel/inspection_form.html'

    def get_template_names(self):
        if self.request.headers.get('HX-Request'):
            return ['personnel/inspection_form_modal.html']
        return [self.template_name]

    def form_valid(self, form):
        form.instance.updated_by = self.request.user

        # Wenn completed_date gesetzt, Status auf COMPLETED setzen
        if form.cleaned_data.get('completed_date'):
            form.instance.status = 'completed'

        messages.success(
            self.request,
            f'Prüfung "{form.instance.title}" wurde erfolgreich aktualisiert.'
        )

        response = super().form_valid(form)

        if self.request.headers.get('HX-Request'):
            return HttpResponse(
                status=200,
                headers={'HX-Redirect': self.get_success_url()}
            )

        return response

    def get_success_url(self):
        return reverse('personnel:detail', kwargs={'pk': self.object.person.pk})


class InspectionDeleteView(LoginRequiredMixin, DeleteView):
    """Prüfung löschen"""
    model = Inspection
    template_name = 'personnel/inspection_confirm_delete.html'

    def get_success_url(self):
        return reverse('personnel:detail', kwargs={'pk': self.object.person.pk})

    def delete(self, request, *args, **kwargs):
        inspection = self.get_object()
        messages.success(
            request,
            f'Prüfung "{inspection.title}" wurde erfolgreich gelöscht.'
        )
        return super().delete(request, *args, **kwargs)


@login_required
def inspection_complete(request, pk):
    """Prüfung als abgeschlossen markieren (Quick-Action)"""
    inspection = get_object_or_404(Inspection, pk=pk)

    if request.method == 'POST':
        inspection.status = 'completed'
        inspection.completed_date = timezone.now().date()
        inspection.passed = request.POST.get('passed') == 'true'
        inspection.updated_by = request.user
        inspection.save()

        messages.success(
            request,
            f'Prüfung "{inspection.title}" als abgeschlossen markiert.'
        )

        if request.headers.get('HX-Request'):
            return HttpResponse(
                status=200,
                headers={'HX-Redirect': reverse('personnel:detail', kwargs={'pk': inspection.person.pk})}
            )

    return redirect('personnel:detail', pk=inspection.person.pk)
```

**Zu ergänzende Imports:**
```python
from .models import Inspection, DutyHoursEntry, DutyHoursRequirement
from .forms import InspectionForm, DutyHoursEntryForm, DutyHoursRequirementForm
```

#### 1.1.2 URLs hinzufügen
**Datei:** `/var/www/lager.resqware.de/personnel/urls.py`

```python
# Hinzufügen in urlpatterns:

# Inspections
path('persons/<int:person_pk>/inspections/create/', views.InspectionCreateView.as_view(), name='inspection_create'),
path('inspections/<int:pk>/edit/', views.InspectionUpdateView.as_view(), name='inspection_update'),
path('inspections/<int:pk>/delete/', views.InspectionDeleteView.as_view(), name='inspection_delete'),
path('inspections/<int:pk>/complete/', views.inspection_complete, name='inspection_complete'),
```

---

### Phase 1.2: PersonDetailView erweitern (30 Min)

**Datei:** `/var/www/lager.resqware.de/personnel/views.py`

```python
# In PersonDetailView.get_context_data() ergänzen:

# Prüfungen laden
from datetime import date
now = timezone.now().date()

# Anstehende Prüfungen (nicht abgeschlossen, sortiert nach Datum)
pending_inspections = self.object.inspections.filter(
    status__in=['pending', 'due_soon', 'overdue']
).order_by('scheduled_date')

# Abgeschlossene Prüfungen (neueste zuerst)
completed_inspections = self.object.inspections.filter(
    status='completed'
).order_by('-completed_date')[:10]

context['pending_inspections'] = pending_inspections
context['completed_inspections'] = completed_inspections
context['inspection_stats'] = {
    'pending': pending_inspections.filter(status='pending').count(),
    'due_soon': pending_inspections.filter(status='due_soon').count(),
    'overdue': pending_inspections.filter(status='overdue').count(),
    'completed_this_year': self.object.inspections.filter(
        status='completed',
        completed_date__year=now.year
    ).count(),
}
```

---

### Phase 1.3: Frontend - Templates (2-3 Stunden)

#### 1.3.1 Inspection Form Modal
**Datei:** `/var/www/lager.resqware.de/templates/personnel/inspection_form_modal.html`

```html
<!-- Modal für Prüfung Create/Update -->
<div
    id="inspection-modal"
    class="fixed inset-0 bg-gray-900 bg-opacity-50 z-50 flex items-center justify-center p-4"
    @click.self="$el.remove()"
>
    <div class="bg-white rounded-lg shadow-xl max-w-3xl w-full max-h-[90vh] overflow-hidden" @click.stop>
        <!-- Header -->
        <div class="bg-gradient-to-r from-blue-600 to-blue-800 px-6 py-4 flex items-center justify-between">
            <h2 class="text-xl font-bold text-white">
                {% if object %}Prüfung bearbeiten{% else %}Neue Prüfung anlegen{% endif %}
            </h2>
            <button @click="$el.closest('#inspection-modal').remove()" class="text-white hover:text-gray-200">
                <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                </svg>
            </button>
        </div>

        <!-- Body -->
        <div class="overflow-y-auto p-6" style="max-height: calc(90vh - 140px);">
            <form
                method="post"
                hx-post="{% if object %}{% url 'personnel:inspection_update' object.pk %}{% else %}{% url 'personnel:inspection_create' person.pk %}{% endif %}"
                hx-target="#inspection-modal"
                hx-swap="outerHTML"
            >
                {% csrf_token %}

                {% if form.non_field_errors %}
                <div class="bg-red-50 border-l-4 border-red-400 p-4 mb-6 rounded-r-lg">
                    <h3 class="text-sm font-medium text-red-800">Fehler beim Speichern</h3>
                    <div class="mt-2 text-sm text-red-700">{{ form.non_field_errors }}</div>
                </div>
                {% endif %}

                <div class="space-y-6">
                    <!-- Basis-Daten -->
                    <div class="border-b border-gray-200 pb-6">
                        <h3 class="text-lg font-semibold text-gray-900 mb-4">Basis-Informationen</h3>

                        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <!-- Person (hidden wenn von Person-Seite) -->
                            {% if not person %}
                            <div class="md:col-span-2">
                                <label class="block text-sm font-medium text-gray-700 mb-2">{{ form.person.label }} *</label>
                                {{ form.person }}
                                {% if form.person.errors %}
                                <p class="mt-1 text-sm text-red-600">{{ form.person.errors.0 }}</p>
                                {% endif %}
                            </div>
                            {% else %}
                            <input type="hidden" name="person" value="{{ person.pk }}">
                            {% endif %}

                            <div class="md:col-span-2">
                                <label class="block text-sm font-medium text-gray-700 mb-2">{{ form.inspection_type.label }} *</label>
                                {{ form.inspection_type }}
                                {% if form.inspection_type.errors %}
                                <p class="mt-1 text-sm text-red-600">{{ form.inspection_type.errors.0 }}</p>
                                {% endif %}
                            </div>

                            <div class="md:col-span-2">
                                <label class="block text-sm font-medium text-gray-700 mb-2">{{ form.title.label }} *</label>
                                {{ form.title }}
                                {% if form.title.errors %}
                                <p class="mt-1 text-sm text-red-600">{{ form.title.errors.0 }}</p>
                                {% endif %}
                            </div>

                            <div class="md:col-span-2">
                                <label class="block text-sm font-medium text-gray-700 mb-2">{{ form.description.label }}</label>
                                {{ form.description }}
                                {% if form.description.errors %}
                                <p class="mt-1 text-sm text-red-600">{{ form.description.errors.0 }}</p>
                                {% endif %}
                            </div>
                        </div>
                    </div>

                    <!-- Termine -->
                    <div class="border-b border-gray-200 pb-6">
                        <h3 class="text-lg font-semibold text-gray-900 mb-4">Termine & Intervall</h3>

                        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                                <label class="block text-sm font-medium text-gray-700 mb-2">{{ form.scheduled_date.label }} *</label>
                                {{ form.scheduled_date }}
                                {% if form.scheduled_date.errors %}
                                <p class="mt-1 text-sm text-red-600">{{ form.scheduled_date.errors.0 }}</p>
                                {% endif %}
                            </div>

                            <div>
                                <label class="block text-sm font-medium text-gray-700 mb-2">{{ form.completed_date.label }}</label>
                                {{ form.completed_date }}
                                {% if form.completed_date.errors %}
                                <p class="mt-1 text-sm text-red-600">{{ form.completed_date.errors.0 }}</p>
                                {% endif %}
                            </div>

                            <div>
                                <label class="block text-sm font-medium text-gray-700 mb-2">{{ form.interval_months.label }}</label>
                                {{ form.interval_months }}
                                <p class="mt-1 text-sm text-gray-500">Für automatische Wiedervorlage</p>
                                {% if form.interval_months.errors %}
                                <p class="mt-1 text-sm text-red-600">{{ form.interval_months.errors.0 }}</p>
                                {% endif %}
                            </div>

                            <div>
                                <label class="block text-sm font-medium text-gray-700 mb-2">{{ form.next_inspection_date.label }}</label>
                                {{ form.next_inspection_date }}
                                {% if form.next_inspection_date.errors %}
                                <p class="mt-1 text-sm text-red-600">{{ form.next_inspection_date.errors.0 }}</p>
                                {% endif %}
                            </div>
                        </div>
                    </div>

                    <!-- Ergebnis -->
                    <div class="border-b border-gray-200 pb-6">
                        <h3 class="text-lg font-semibold text-gray-900 mb-4">Ergebnis & Prüfer</h3>

                        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                                <label class="block text-sm font-medium text-gray-700 mb-2">{{ form.status.label }}</label>
                                {{ form.status }}
                                {% if form.status.errors %}
                                <p class="mt-1 text-sm text-red-600">{{ form.status.errors.0 }}</p>
                                {% endif %}
                            </div>

                            <div>
                                <label class="block text-sm font-medium text-gray-700 mb-2">{{ form.passed.label }}</label>
                                {{ form.passed }}
                                {% if form.passed.errors %}
                                <p class="mt-1 text-sm text-red-600">{{ form.passed.errors.0 }}</p>
                                {% endif %}
                            </div>

                            <div class="md:col-span-2">
                                <label class="block text-sm font-medium text-gray-700 mb-2">{{ form.examiner.label }}</label>
                                {{ form.examiner }}
                                {% if form.examiner.errors %}
                                <p class="mt-1 text-sm text-red-600">{{ form.examiner.errors.0 }}</p>
                                {% endif %}
                            </div>

                            <div class="md:col-span-2">
                                <label class="block text-sm font-medium text-gray-700 mb-2">{{ form.result_notes.label }}</label>
                                {{ form.result_notes }}
                                {% if form.result_notes.errors %}
                                <p class="mt-1 text-sm text-red-600">{{ form.result_notes.errors.0 }}</p>
                                {% endif %}
                            </div>
                        </div>
                    </div>

                    <!-- Dokumente & Notizen -->
                    <div>
                        <h3 class="text-lg font-semibold text-gray-900 mb-4">Dokumente & Notizen</h3>

                        <div class="space-y-4">
                            <div>
                                <label class="block text-sm font-medium text-gray-700 mb-2">{{ form.certificate_file.label }}</label>
                                {{ form.certificate_file }}
                                {% if form.certificate_file.errors %}
                                <p class="mt-1 text-sm text-red-600">{{ form.certificate_file.errors.0 }}</p>
                                {% endif %}
                            </div>

                            <div>
                                <label class="block text-sm font-medium text-gray-700 mb-2">{{ form.notes.label }}</label>
                                {{ form.notes }}
                                {% if form.notes.errors %}
                                <p class="mt-1 text-sm text-red-600">{{ form.notes.errors.0 }}</p>
                                {% endif %}
                            </div>
                        </div>
                    </div>
                </div>
            </form>
        </div>

        <!-- Footer -->
        <div class="bg-gray-50 px-6 py-4 flex items-center justify-end gap-3 border-t border-gray-200">
            <button
                type="button"
                @click="$el.closest('#inspection-modal').remove()"
                class="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors font-medium text-sm"
            >
                Abbrechen
            </button>
            <button
                type="submit"
                form="inspection-form"
                class="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium text-sm"
            >
                {% if object %}Änderungen speichern{% else %}Prüfung anlegen{% endif %}
            </button>
        </div>
    </div>
</div>

<script>
document.querySelector('#inspection-modal form').setAttribute('id', 'inspection-form');
</script>
```

#### 1.3.2 Inspections Tab Template aktualisieren
**Datei:** `/var/www/lager.resqware.de/templates/personnel/tabs/inspections.html`

```html
<!-- Tab: Prüfungen -->
<div x-show="activeTab === 'inspections'" x-cloak>

    <!-- Header mit Button -->
    <div class="flex items-center justify-between mb-6">
        <h3 class="text-lg font-semibold text-gray-900">
            Prüfungen & Untersuchungen
        </h3>
        <button
            hx-get="{% url 'personnel:inspection_create' person.pk %}"
            hx-target="body"
            hx-swap="beforeend"
            class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium text-sm"
        >
            ➕ Prüfung hinzufügen
        </button>
    </div>

    <!-- Statistiken -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div class="bg-red-50 rounded-lg p-4 border border-red-200">
            <div class="flex items-center justify-between mb-2">
                <span class="text-sm font-medium text-red-900">Überfällig</span>
                <span class="text-2xl">⚠️</span>
            </div>
            <p class="text-3xl font-bold text-red-900">{{ inspection_stats.overdue }}</p>
        </div>

        <div class="bg-yellow-50 rounded-lg p-4 border border-yellow-200">
            <div class="flex items-center justify-between mb-2">
                <span class="text-sm font-medium text-yellow-900">Bald fällig</span>
                <span class="text-2xl">⏰</span>
            </div>
            <p class="text-3xl font-bold text-yellow-900">{{ inspection_stats.due_soon }}</p>
        </div>

        <div class="bg-blue-50 rounded-lg p-4 border border-blue-200">
            <div class="flex items-center justify-between mb-2">
                <span class="text-sm font-medium text-blue-900">Anstehend</span>
                <span class="text-2xl">📅</span>
            </div>
            <p class="text-3xl font-bold text-blue-900">{{ inspection_stats.pending }}</p>
        </div>

        <div class="bg-green-50 rounded-lg p-4 border border-green-200">
            <div class="flex items-center justify-between mb-2">
                <span class="text-sm font-medium text-green-900">Dieses Jahr</span>
                <span class="text-2xl">✅</span>
            </div>
            <p class="text-3xl font-bold text-green-900">{{ inspection_stats.completed_this_year }}</p>
        </div>
    </div>

    <!-- Anstehende Prüfungen -->
    {% if pending_inspections %}
    <div class="mb-6">
        <h4 class="font-semibold text-gray-900 mb-4">Anstehende Prüfungen ({{ pending_inspections.count }})</h4>

        <div class="space-y-4">
            {% for inspection in pending_inspections %}
            <div class="p-4 rounded-lg border-l-4
                {% if inspection.status == 'overdue' %}bg-red-50 border-red-400
                {% elif inspection.status == 'due_soon' %}bg-yellow-50 border-yellow-400
                {% else %}bg-blue-50 border-blue-400{% endif %}">

                <div class="flex items-start justify-between">
                    <div class="flex-1">
                        <div class="flex items-center gap-2 mb-2">
                            <span class="text-2xl">
                                {% if inspection.status == 'overdue' %}⚠️
                                {% elif inspection.status == 'due_soon' %}⏰
                                {% else %}📅{% endif %}
                            </span>
                            <h5 class="font-semibold text-gray-900">{{ inspection.title }}</h5>
                            <span class="px-2 py-1 text-xs font-semibold rounded-full
                                {% if inspection.status == 'overdue' %}bg-red-100 text-red-700
                                {% elif inspection.status == 'due_soon' %}bg-yellow-100 text-yellow-700
                                {% else %}bg-blue-100 text-blue-700{% endif %}">
                                {{ inspection.get_status_display }}
                            </span>
                        </div>

                        <div class="text-sm text-gray-700 space-y-1">
                            <p><strong>Typ:</strong> {{ inspection.get_inspection_type_display }}</p>
                            <p><strong>Geplant:</strong> {{ inspection.scheduled_date|date:"d.m.Y" }}
                                {% if inspection.is_overdue %}
                                <span class="text-red-600 font-semibold">(Überfällig!)</span>
                                {% elif inspection.is_due_soon %}
                                <span class="text-yellow-600 font-semibold">(Bald fällig)</span>
                                {% endif %}
                            </p>
                            {% if inspection.interval_months %}
                            <p><strong>Intervall:</strong> Alle {{ inspection.interval_months }} Monate</p>
                            {% endif %}
                            {% if inspection.examiner %}
                            <p><strong>Prüfer:</strong> {{ inspection.examiner }}</p>
                            {% endif %}
                        </div>
                    </div>

                    <div class="flex gap-2">
                        <button
                            hx-post="{% url 'personnel:inspection_complete' inspection.pk %}"
                            hx-confirm="Prüfung als abgeschlossen markieren?"
                            hx-target="body"
                            class="px-3 py-1.5 bg-green-600 text-white rounded text-sm hover:bg-green-700"
                        >
                            ✓ Erledigt
                        </button>
                        <button
                            hx-get="{% url 'personnel:inspection_update' inspection.pk %}"
                            hx-target="body"
                            hx-swap="beforeend"
                            class="px-3 py-1.5 bg-gray-100 text-gray-700 rounded text-sm hover:bg-gray-200"
                        >
                            ✏️ Bearbeiten
                        </button>
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>
    </div>
    {% endif %}

    <!-- Absolvierte Prüfungen (Timeline) -->
    {% if completed_inspections %}
    <div>
        <h4 class="font-semibold text-gray-900 mb-4">Absolvierte Prüfungen (Letzte 10)</h4>

        <div class="relative">
            <div class="absolute left-2 top-2 bottom-2 w-0.5 bg-gray-200"></div>

            <div class="space-y-4">
                {% for inspection in completed_inspections %}
                <div class="relative pl-8">
                    <div class="absolute left-0 top-1 w-4 h-4 rounded-full border-2 border-white
                        {% if inspection.passed %}bg-green-600{% else %}bg-red-600{% endif %}">
                    </div>

                    <div class="bg-gray-50 rounded-lg p-4">
                        <div class="flex items-start justify-between">
                            <div class="flex-1">
                                <p class="font-medium text-gray-900">{{ inspection.title }}</p>
                                <p class="text-sm text-gray-600 mt-1">
                                    {% if inspection.passed %}
                                    <span class="text-green-600 font-semibold">✓ Bestanden</span>
                                    {% elif inspection.passed == False %}
                                    <span class="text-red-600 font-semibold">✗ Nicht bestanden</span>
                                    {% else %}
                                    <span class="text-gray-600">Abgeschlossen</span>
                                    {% endif %}
                                    {% if inspection.examiner %}• Prüfer: {{ inspection.examiner }}{% endif %}
                                </p>
                                {% if inspection.result_notes %}
                                <p class="text-sm text-gray-600 mt-2">{{ inspection.result_notes }}</p>
                                {% endif %}
                            </div>
                            <div class="flex flex-col items-end gap-2">
                                <span class="text-xs text-gray-500 whitespace-nowrap">{{ inspection.completed_date|date:"d.m.Y" }}</span>
                                <button
                                    hx-get="{% url 'personnel:inspection_update' inspection.pk %}"
                                    hx-target="body"
                                    hx-swap="beforeend"
                                    class="text-sm text-blue-600 hover:text-blue-800"
                                >
                                    Details →
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>
    </div>
    {% endif %}

    <!-- Keine Prüfungen -->
    {% if not pending_inspections and not completed_inspections %}
    <div class="bg-gray-50 rounded-lg p-8 text-center border border-gray-200">
        <div class="text-5xl mb-4">📅</div>
        <h3 class="text-lg font-bold text-gray-900 mb-2">Keine Prüfungen erfasst</h3>
        <p class="text-gray-600 mb-6">
            Für diese Person wurden noch keine Prüfungen angelegt.
        </p>
        <button
            hx-get="{% url 'personnel:inspection_create' person.pk %}"
            hx-target="body"
            hx-swap="beforeend"
            class="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium text-sm"
        >
            ➕ Erste Prüfung hinzufügen
        </button>
    </div>
    {% endif %}

</div>
```

---

### Phase 1.4: Testing & Refinement (1 Stunde)

**Checkliste:**
- [ ] Prüfung erstellen funktioniert
- [ ] Prüfung bearbeiten funktioniert
- [ ] Quick-Action "Erledigt" funktioniert
- [ ] Status-Updates automatisch (overdue/due_soon)
- [ ] Statistiken werden korrekt angezeigt
- [ ] Timeline zeigt abgeschlossene Prüfungen
- [ ] HTMX-Modals öffnen und schließen korrekt

---

## ⏱️ Modul 2: Pflichtstunden (DutyHours)

### Phase 2.1: Backend - Views & URLs (3-4 Stunden)

#### 2.1.1 CRUD Views für DutyHoursEntry
**Datei:** `/var/www/lager.resqware.de/personnel/views.py`

```python
# ============================================================================
# DUTY HOURS VIEWS
# ============================================================================

class DutyHoursEntryCreateView(LoginRequiredMixin, CreateView):
    """Pflichtstunden-Eintrag hinzufügen"""
    model = DutyHoursEntry
    form_class = DutyHoursEntryForm
    template_name = 'personnel/dutyhours_form.html'

    def get_template_names(self):
        if self.request.headers.get('HX-Request'):
            return ['personnel/dutyhours_form_modal.html']
        return [self.template_name]

    def get_initial(self):
        initial = super().get_initial()
        person_id = self.kwargs.get('person_pk')
        if person_id:
            initial['person'] = person_id
            # Heutiges Datum als Standard
            initial['date'] = timezone.now().date()
        return initial

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user

        messages.success(
            self.request,
            f'Pflichtstunden "{form.instance.title}" ({form.instance.hours}h) wurden erfolgreich erfasst.'
        )

        response = super().form_valid(form)

        if self.request.headers.get('HX-Request'):
            return HttpResponse(
                status=200,
                headers={'HX-Redirect': self.get_success_url()}
            )

        return response

    def get_success_url(self):
        return reverse('personnel:detail', kwargs={'pk': self.object.person.pk})


class DutyHoursEntryUpdateView(LoginRequiredMixin, UpdateView):
    """Pflichtstunden-Eintrag bearbeiten"""
    model = DutyHoursEntry
    form_class = DutyHoursEntryForm
    template_name = 'personnel/dutyhours_form.html'

    def get_template_names(self):
        if self.request.headers.get('HX-Request'):
            return ['personnel/dutyhours_form_modal.html']
        return [self.template_name]

    def form_valid(self, form):
        form.instance.updated_by = self.request.user

        messages.success(
            self.request,
            f'Pflichtstunden-Eintrag wurde erfolgreich aktualisiert.'
        )

        response = super().form_valid(form)

        if self.request.headers.get('HX-Request'):
            return HttpResponse(
                status=200,
                headers={'HX-Redirect': self.get_success_url()}
            )

        return response

    def get_success_url(self):
        return reverse('personnel:detail', kwargs={'pk': self.object.person.pk})


class DutyHoursEntryDeleteView(LoginRequiredMixin, DeleteView):
    """Pflichtstunden-Eintrag löschen"""
    model = DutyHoursEntry
    template_name = 'personnel/dutyhours_confirm_delete.html'

    def get_success_url(self):
        return reverse('personnel:detail', kwargs={'pk': self.object.person.pk})

    def delete(self, request, *args, **kwargs):
        entry = self.get_object()
        messages.success(
            request,
            f'Pflichtstunden-Eintrag "{entry.title}" wurde erfolgreich gelöscht.'
        )
        return super().delete(request, *args, **kwargs)


@login_required
def dutyhours_overview(request, person_pk):
    """Pflichtstunden-Übersicht für eine Person mit Jahr-Filter"""
    person = get_object_or_404(Person, pk=person_pk)

    # Jahr aus Query-Parameter oder aktuelles Jahr
    year = request.GET.get('year')
    if year:
        try:
            year = int(year)
        except:
            year = timezone.now().year
    else:
        year = timezone.now().year

    # Alle Kategorien mit Anforderungen für dieses Jahr
    requirements = DutyHoursRequirement.objects.filter(
        year=year,
        is_active=True
    ).order_by('category')

    # Erfasste Stunden für diese Person und Jahr
    entries = DutyHoursEntry.objects.filter(
        person=person,
        year=year
    ).select_related('created_by')

    # Pro Kategorie: Anforderung, erfasste Stunden, Prozent
    category_stats = []

    for req in requirements:
        # Summe der Stunden für diese Kategorie
        hours_sum = entries.filter(
            category=req.category,
            confirmed=True
        ).aggregate(total=models.Sum('hours'))['total'] or 0

        # Prozent berechnen
        if req.required_hours > 0:
            percentage = min(100, (hours_sum / req.required_hours) * 100)
        else:
            percentage = 0

        # Status ermitteln
        if percentage >= 100:
            status = 'complete'
        elif percentage >= 75:
            status = 'warning'
        else:
            status = 'danger'

        category_stats.append({
            'category': req.category,
            'category_display': req.get_category_display(),
            'required_hours': req.required_hours,
            'completed_hours': hours_sum,
            'remaining_hours': max(0, req.required_hours - hours_sum),
            'percentage': round(percentage, 1),
            'status': status,
            'entries_count': entries.filter(category=req.category).count()
        })

    # Letzte Einträge (alle Kategorien)
    recent_entries = entries.order_by('-date')[:10]

    # Verfügbare Jahre für Dropdown
    years_with_data = DutyHoursEntry.objects.filter(
        person=person
    ).values_list('year', flat=True).distinct().order_by('-year')

    # Kombiniere mit Jahren die Anforderungen haben
    years_with_requirements = DutyHoursRequirement.objects.filter(
        is_active=True
    ).values_list('year', flat=True).distinct().order_by('-year')

    available_years = sorted(set(list(years_with_data) + list(years_with_requirements)), reverse=True)

    context = {
        'person': person,
        'year': year,
        'available_years': available_years,
        'category_stats': category_stats,
        'recent_entries': recent_entries,
        'total_entries': entries.count(),
        'total_hours': entries.aggregate(total=models.Sum('hours'))['total'] or 0,
    }

    return render(request, 'personnel/dutyhours_overview.html', context)
```

#### 2.1.2 URLs hinzufügen
**Datei:** `/var/www/lager.resqware.de/personnel/urls.py`

```python
# Duty Hours
path('persons/<int:person_pk>/dutyhours/', views.dutyhours_overview, name='dutyhours_overview'),
path('persons/<int:person_pk>/dutyhours/create/', views.DutyHoursEntryCreateView.as_view(), name='dutyhours_create'),
path('dutyhours/<int:pk>/edit/', views.DutyHoursEntryUpdateView.as_view(), name='dutyhours_update'),
path('dutyhours/<int:pk>/delete/', views.DutyHoursEntryDeleteView.as_view(), name='dutyhours_delete'),
```

---

### Phase 2.2: PersonDetailView erweitern (30 Min)

**Datei:** `/var/www/lager.resqware.de/personnel/views.py`

```python
# In PersonDetailView.get_context_data() ergänzen:

# Pflichtstunden laden (aktuelles Jahr)
current_year = timezone.now().year

# Anforderungen für aktuelles Jahr
requirements = DutyHoursRequirement.objects.filter(
    year=current_year,
    is_active=True
)

# Erfasste Stunden
entries = self.object.duty_hours.filter(year=current_year)

# Statistiken pro Kategorie
duty_hours_stats = []
for req in requirements:
    hours_sum = entries.filter(
        category=req.category,
        confirmed=True
    ).aggregate(total=models.Sum('hours'))['total'] or 0

    percentage = (hours_sum / req.required_hours * 100) if req.required_hours > 0 else 0

    duty_hours_stats.append({
        'category': req.get_category_display(),
        'required': req.required_hours,
        'completed': hours_sum,
        'remaining': max(0, req.required_hours - hours_sum),
        'percentage': round(percentage, 1),
        'status': 'complete' if percentage >= 100 else ('warning' if percentage >= 75 else 'danger')
    })

context['duty_hours_stats'] = duty_hours_stats
context['duty_hours_entries'] = entries.order_by('-date')[:5]
context['duty_hours_year'] = current_year
```

---

### Phase 2.3: Frontend - Templates (3-4 Stunden)

#### 2.3.1 DutyHours Tab Template aktualisieren
**Datei:** `/var/www/lager.resqware.de/templates/personnel/tabs/dutyhours.html`

```html
<!-- Tab: Pflichtstunden -->
<div x-show="activeTab === 'dutyhours'" x-cloak>

    <div class="flex items-center justify-between mb-6">
        <h3 class="text-lg font-semibold text-gray-900">Pflichtstunden {{ duty_hours_year }}</h3>
        <div class="flex gap-2">
            <a
                href="{% url 'personnel:dutyhours_overview' person.pk %}"
                class="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors font-medium text-sm"
            >
                📊 Vollständige Übersicht
            </a>
            <button
                hx-get="{% url 'personnel:dutyhours_create' person.pk %}"
                hx-target="body"
                hx-swap="beforeend"
                class="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors font-medium text-sm"
            >
                ➕ Stunden erfassen
            </button>
        </div>
    </div>

    <!-- Übersicht mit Progress-Bars -->
    {% if duty_hours_stats %}
    <div class="space-y-6 mb-8">
        {% for stat in duty_hours_stats %}
        <div class="bg-white border border-gray-200 rounded-lg p-6">
            <div class="flex items-center gap-3 mb-3">
                <span class="text-3xl">
                    {% if '🤿' in stat.category %}🤿
                    {% elif '🧗' in stat.category or 'Höhen' in stat.category %}🧗
                    {% elif '🏥' in stat.category or 'Medizin' in stat.category %}🏥
                    {% elif 'Atem' in stat.category %}😷
                    {% elif 'Fahrzeug' in stat.category %}🚒
                    {% elif 'Technisch' in stat.category %}🔧
                    {% else %}📝{% endif %}
                </span>
                <div class="flex-1">
                    <h4 class="font-semibold text-gray-900">{{ stat.category }}</h4>
                    <p class="text-sm text-gray-600">{{ stat.completed }} / {{ stat.required }} Stunden ({{ stat.percentage }}%)</p>
                </div>
                <span class="px-3 py-1 text-sm rounded-full font-semibold
                    {% if stat.status == 'complete' %}bg-green-100 text-green-700
                    {% elif stat.status == 'warning' %}bg-yellow-100 text-yellow-700
                    {% else %}bg-red-100 text-red-700{% endif %}">
                    {% if stat.status == 'complete' %}✅ Erfüllt
                    {% elif stat.status == 'warning' %}⚠️ Noch {{ stat.remaining }} Std.
                    {% else %}🔴 Dringend {{ stat.remaining }} Std.{% endif %}
                </span>
            </div>

            <!-- Progress Bar -->
            <div class="w-full bg-gray-200 rounded-full h-4 mb-2">
                <div class="h-4 rounded-full flex items-center justify-end pr-2
                    {% if stat.status == 'complete' %}bg-green-500
                    {% elif stat.status == 'warning' %}bg-yellow-500
                    {% else %}bg-red-500{% endif %}"
                    style="width: {{ stat.percentage }}%">
                    {% if stat.percentage > 15 %}
                    <span class="text-xs font-bold text-white">{{ stat.percentage }}%</span>
                    {% endif %}
                </div>
            </div>

            <div class="flex items-center justify-between text-xs text-gray-500">
                <span>Frist: 31.12.{{ duty_hours_year }}</span>
                <span>
                    {% now "z" as day_of_year %}
                    {% with days_left=365|add:"-"|add:day_of_year %}
                    {{ days_left }} Tage verbleibend
                    {% endwith %}
                </span>
            </div>
        </div>
        {% endfor %}
    </div>
    {% else %}
    <div class="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
        <p class="text-sm text-blue-800">
            <strong>Hinweis:</strong> Für das Jahr {{ duty_hours_year }} sind noch keine Anforderungen definiert.
            Erfasste Stunden werden trotzdem gespeichert.
        </p>
    </div>
    {% endif %}

    <!-- Letzte Einträge -->
    {% if duty_hours_entries %}
    <div>
        <div class="flex items-center justify-between mb-4">
            <h4 class="font-semibold text-gray-900">Letzte Einträge</h4>
        </div>

        <div class="space-y-2">
            {% for entry in duty_hours_entries %}
            <div class="bg-gray-50 rounded-lg p-4 flex items-center justify-between">
                <div class="flex items-center gap-4">
                    <span class="text-2xl">
                        {% if entry.category == 'diving' %}🤿
                        {% elif entry.category == 'height_rescue' %}🧗
                        {% elif entry.category == 'medical' %}🏥
                        {% elif entry.category == 'breathing' %}😷
                        {% elif entry.category == 'vehicle' %}🚒
                        {% elif entry.category == 'technical' %}🔧
                        {% else %}📝{% endif %}
                    </span>
                    <div>
                        <p class="font-medium text-gray-900">{{ entry.title }}</p>
                        <p class="text-sm text-gray-600">
                            {{ entry.hours }} Stunden
                            {% if entry.supervisor %} • {{ entry.supervisor }}{% endif %}
                            {% if entry.confirmed %}
                            <span class="text-green-600 font-semibold">✓ Bestätigt</span>
                            {% else %}
                            <span class="text-gray-500">⏳ Nicht bestätigt</span>
                            {% endif %}
                        </p>
                    </div>
                </div>
                <div class="flex items-center gap-3">
                    <span class="text-sm text-gray-500">{{ entry.date|date:"d.m.Y" }}</span>
                    <button
                        hx-get="{% url 'personnel:dutyhours_update' entry.pk %}"
                        hx-target="body"
                        hx-swap="beforeend"
                        class="text-sm text-blue-600 hover:text-blue-800"
                    >
                        ✏️
                    </button>
                </div>
            </div>
            {% endfor %}
        </div>

        <div class="mt-4 text-center">
            <a
                href="{% url 'personnel:dutyhours_overview' person.pk %}"
                class="text-sm text-blue-600 hover:text-blue-800 font-medium"
            >
                Alle Einträge anzeigen →
            </a>
        </div>
    </div>
    {% else %}
    <div class="bg-gray-50 rounded-lg p-8 text-center border border-gray-200">
        <div class="text-5xl mb-4">⏱️</div>
        <h3 class="text-lg font-bold text-gray-900 mb-2">Keine Pflichtstunden erfasst</h3>
        <p class="text-gray-600 mb-6">
            Für diese Person wurden noch keine Pflichtstunden für {{ duty_hours_year }} erfasst.
        </p>
        <button
            hx-get="{% url 'personnel:dutyhours_create' person.pk %}"
            hx-target="body"
            hx-swap="beforeend"
            class="inline-flex items-center px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors font-medium text-sm"
        >
            ➕ Erste Stunden erfassen
        </button>
    </div>
    {% endif %}

</div>
```

#### 2.3.2 DutyHours Form Modal (Analog zu Inspection Form)
**Datei:** `/var/www/lager.resqware.de/templates/personnel/dutyhours_form_modal.html`

*(Struktur ähnlich wie inspection_form_modal.html, mit lila/purple Farbschema statt blau)*

---

### Phase 2.4: Anforderungen-Verwaltung (2 Stunden)

#### 2.4.1 Admin-Interface für DutyHoursRequirement
**Datei:** `/var/www/lager.resqware.de/personnel/admin.py`

```python
from django.contrib import admin
from .models import (
    Person, Qualification, QualificationTemplate,
    Training, TrainingParticipant,
    Inspection, DutyHoursEntry, DutyHoursRequirement
)

# ... existing admin registrations ...

@admin.register(DutyHoursRequirement)
class DutyHoursRequirementAdmin(admin.ModelAdmin):
    list_display = ['category', 'year', 'required_hours', 'is_active']
    list_filter = ['year', 'category', 'is_active']
    search_fields = ['category', 'description']
    ordering = ['-year', 'category']

@admin.register(Inspection)
class InspectionAdmin(admin.ModelAdmin):
    list_display = ['person', 'title', 'inspection_type', 'scheduled_date', 'status']
    list_filter = ['status', 'inspection_type', 'scheduled_date']
    search_fields = ['person__first_name', 'person__last_name', 'title']
    date_hierarchy = 'scheduled_date'
    ordering = ['-scheduled_date']

@admin.register(DutyHoursEntry)
class DutyHoursEntryAdmin(admin.ModelAdmin):
    list_display = ['person', 'category', 'title', 'hours', 'date', 'confirmed']
    list_filter = ['category', 'year', 'confirmed', 'date']
    search_fields = ['person__first_name', 'person__last_name', 'title']
    date_hierarchy = 'date'
    ordering = ['-date']
```

---

### Phase 2.5: Testing & Refinement (1-2 Stunden)

**Checkliste:**
- [ ] Pflichtstunden erfassen funktioniert
- [ ] Pflichtstunden bearbeiten funktioniert
- [ ] Progress-Bars zeigen korrekte Prozente
- [ ] Jahr-Filter in Übersicht funktioniert
- [ ] Anforderungen können im Admin definiert werden
- [ ] Bestätigung von Stunden funktioniert
- [ ] Statistiken werden korrekt berechnet

---

## 🔗 Phase 3: Integration & Polish (2-3 Stunden)

### 3.1 Dashboard-Integration

**Datei:** `/var/www/lager.resqware.de/personnel/views.py`

In `personnel_dashboard()` aktualisieren:

```python
# Fällige Prüfungen (nächste 30 Tage) ersetzen mit:
from .models import Inspection
due_inspections = Inspection.objects.filter(
    status__in=['pending', 'due_soon', 'overdue'],
    scheduled_date__lte=timezone.now().date() + timedelta(days=30)
).count()

# Personal unter Pflichtstunden ersetzen mit:
current_year = timezone.now().year
requirements = DutyHoursRequirement.objects.filter(
    year=current_year,
    is_active=True
)

personnel_below_duty_hours = 0
for person in Person.objects.filter(is_active=True):
    for req in requirements:
        hours_sum = person.duty_hours.filter(
            category=req.category,
            year=current_year,
            confirmed=True
        ).aggregate(total=models.Sum('hours'))['total'] or 0

        if hours_sum < req.required_hours:
            personnel_below_duty_hours += 1
            break  # Person nur einmal zählen
```

### 3.2 Navigation & Links aktualisieren

**Überall wo "coming soon" oder Platzhalter sind:**
- Dashboard-Links aktivieren
- Sidebar-Navigation aktualisieren
- Breadcrumbs korrigieren

### 3.3 Permissions & Security

**Optional aber empfohlen:**
```python
# In views.py für alle neuen Views:
from django.contrib.auth.mixins import PermissionRequiredMixin

class InspectionCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    permission_required = 'personnel.add_inspection'
    # ...

class DutyHoursEntryCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    permission_required = 'personnel.add_dutyhoursentry'
    # ...
```

---

## 📊 Zeitschätzung Gesamt

| Phase | Modul | Geschätzte Zeit |
|-------|-------|-----------------|
| 1.1 | Inspections Backend | 2-3h |
| 1.2 | Inspections PersonView | 0.5h |
| 1.3 | Inspections Templates | 2-3h |
| 1.4 | Inspections Testing | 1h |
| **Summe Inspections** | | **5.5-7.5h** |
| 2.1 | DutyHours Backend | 3-4h |
| 2.2 | DutyHours PersonView | 0.5h |
| 2.3 | DutyHours Templates | 3-4h |
| 2.4 | DutyHours Requirements | 2h |
| 2.5 | DutyHours Testing | 1-2h |
| **Summe DutyHours** | | **9.5-12.5h** |
| 3 | Integration & Polish | 2-3h |
| **GESAMT** | | **17-23h** |

---

## 🎯 Erfolgs-Kriterien

### Inspections (Prüfungen)
- [ ] Prüfungen können CRUD durchgeführt werden
- [ ] Status-Updates erfolgen automatisch
- [ ] Quick-Actions (Erledigt-Button) funktioniert
- [ ] Statistiken im Tab sind korrekt
- [ ] Timeline zeigt vergangene Prüfungen
- [ ] Benachrichtigungen bei überfälligen Prüfungen

### DutyHours (Pflichtstunden)
- [ ] Stunden können erfasst werden
- [ ] Progress-Bars zeigen korrekten Fortschritt
- [ ] Jahr-Filter funktioniert
- [ ] Anforderungen können definiert werden
- [ ] Bestätigung von Stunden funktioniert
- [ ] Dashboard zeigt Personal unter Sollstunden

---

## 🚀 Quick Start

### Für Inspections:
```bash
# 1. Backend implementieren (Phase 1.1-1.2)
# 2. Templates erstellen (Phase 1.3)
# 3. Testen und verfeinern (Phase 1.4)
# 4. Commit & Deploy
```

### Für DutyHours:
```bash
# 1. Backend implementieren (Phase 2.1-2.2)
# 2. Templates erstellen (Phase 2.3)
# 3. Admin-Interface konfigurieren (Phase 2.4)
# 4. Anforderungen definieren über Admin
# 5. Testen und verfeinern (Phase 2.5)
# 6. Commit & Deploy
```

---

## 📝 Notizen & Best Practices

### Code-Struktur
- Folge dem bestehenden Pattern (Qualifications als Vorlage)
- Verwende HTMX für Modals
- Tailwind CSS für Styling
- Alpine.js für client-side Interaktivität

### Testing
- Teste mit echten Daten
- Prüfe Edge-Cases (leere Listen, überfällige Prüfungen, 100%+ Pflichtstunden)
- Mobile Responsiveness checken

### Performance
- Select_related() für Person Foreign Keys
- Aggregate() für Summen-Berechnungen
- Pagination bei langen Listen

### Security
- LoginRequiredMixin auf allen Views
- Permission-Checks hinzufügen
- Audit-Felder (created_by, updated_by) nutzen

---

**Autor:** Claude Code
**Version:** 1.0
**Stand:** 2025-10-16
