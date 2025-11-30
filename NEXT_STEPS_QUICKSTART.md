# Quick Start für morgen

## ⚡ Sofort starten

### 1. Server starten
```bash
cd /var/www/lager.resqware.de
source venv/bin/activate
python manage.py runserver 0.0.0.0:8000
```

### 2. Ersten Admin-User erstellen (falls noch nicht vorhanden)
```bash
python manage.py createsuperuser
# Username: admin
# Email: admin@example.com
# Password: [sicheres Passwort]
```

### 3. Admin Rolle zuweisen
```bash
python manage.py shell
```
```python
from core.models import User
from permissions.utils import PermissionHelper

# Admin-User holen
user = User.objects.get(username='admin')

# Administrator-Rolle zuweisen
PermissionHelper.assign_role(user, 'Administrator')

# Prüfen
print(PermissionHelper.get_user_permission_summary(user))
# Sollte zeigen: roles: ['Administrator'], approval_limit: inf

exit()
```

### 4. Testen im Browser
```
http://lager.resqware.de/admin/
oder
http://localhost:8000/admin/

Login mit dem erstellten User
```

---

## 📋 Empfohlene Arbeitsreihenfolge für morgen

### Morgen Session 1: User Management Views (2-3h)

#### Schritt 1: View-Datei erstellen
```bash
touch core/views/user_management.py
```

**Inhalt (Starter-Template):**
```python
from django.views.generic import ListView, DetailView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import redirect
from django.http import JsonResponse

from core.models import User
from permissions.mixins import RoleRequiredMixin
from permissions.constants import Roles
from permissions.utils import PermissionHelper


class UserListView(LoginRequiredMixin, RoleRequiredMixin, ListView):
    """Liste aller User für Admin"""
    model = User
    template_name = 'core/user_management/user_list.html'
    required_roles = [Roles.ADMINISTRATOR]
    context_object_name = 'users'
    paginate_by = 50

    def get_queryset(self):
        return User.objects.all().prefetch_related('groups').order_by('last_name', 'first_name')


class UserDetailView(LoginRequiredMixin, RoleRequiredMixin, DetailView):
    """User-Details mit Rollen und Permissions"""
    model = User
    template_name = 'core/user_management/user_detail.html'
    required_roles = [Roles.ADMINISTRATOR]
    context_object_name = 'user_obj'  # Nicht 'user' wegen request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_obj = self.object

        # Permission-Summary holen
        context['permission_summary'] = PermissionHelper.get_user_permission_summary(user_obj)

        # Alle verfügbaren Rollen
        from django.contrib.auth.models import Group
        context['available_roles'] = Group.objects.all().order_by('name')

        # Aktive Delegationen
        from permissions.backends import get_active_delegations
        context['active_delegations'] = get_active_delegations(user_obj)

        return context


class UserRoleAssignView(LoginRequiredMixin, RoleRequiredMixin, DetailView):
    """HTMX Endpoint für Rollen-Zuweisung"""
    model = User
    required_roles = [Roles.ADMINISTRATOR]

    def post(self, request, *args, **kwargs):
        user_obj = self.get_object()
        action = request.POST.get('action')  # 'add' oder 'remove'
        role_name = request.POST.get('role')

        if action == 'add':
            success = PermissionHelper.assign_role(user_obj, role_name, assigned_by=request.user)
            if success:
                messages.success(request, f'Rolle "{role_name}" zugewiesen')
            else:
                messages.error(request, f'Fehler beim Zuweisen der Rolle')

        elif action == 'remove':
            success = PermissionHelper.remove_role(user_obj, role_name, removed_by=request.user)
            if success:
                messages.success(request, f'Rolle "{role_name}" entfernt')
            else:
                messages.error(request, f'Fehler beim Entfernen der Rolle')

        # Redirect zurück zu User-Detail
        return redirect('core:user_detail', pk=user_obj.pk)
```

#### Schritt 2: URLs hinzufügen
**Datei:** `core/urls.py`

**Hinzufügen:**
```python
from core.views.user_management import (
    UserListView,
    UserDetailView,
    UserRoleAssignView,
)

# Im urlpatterns ergänzen:
path('admin/users/', UserListView.as_view(), name='user_list'),
path('admin/users/<int:pk>/', UserDetailView.as_view(), name='user_detail'),
path('admin/users/<int:pk>/roles/', UserRoleAssignView.as_view(), name='assign_roles'),
```

#### Schritt 3: Template erstellen
```bash
mkdir -p templates/core/user_management
touch templates/core/user_management/user_list.html
touch templates/core/user_management/user_detail.html
```

**user_list.html (Minimal):**
```django
{% extends 'base.html' %}
{% load permission_tags %}

{% block content %}
<div class="container mx-auto px-4 py-8">
    <div class="flex justify-between items-center mb-6">
        <h1 class="text-3xl font-bold">Benutzerverwaltung</h1>
    </div>

    <div class="bg-white shadow-md rounded-lg overflow-hidden">
        <table class="min-w-full">
            <thead class="bg-gray-50">
                <tr>
                    <th class="px-6 py-3 text-left">Name</th>
                    <th class="px-6 py-3 text-left">Username</th>
                    <th class="px-6 py-3 text-left">Email</th>
                    <th class="px-6 py-3 text-left">Rollen</th>
                    <th class="px-6 py-3 text-left">Status</th>
                    <th class="px-6 py-3 text-left">Aktionen</th>
                </tr>
            </thead>
            <tbody class="divide-y divide-gray-200">
                {% for user_obj in users %}
                <tr>
                    <td class="px-6 py-4">{{ user_obj.get_full_name }}</td>
                    <td class="px-6 py-4">{{ user_obj.username }}</td>
                    <td class="px-6 py-4">{{ user_obj.email }}</td>
                    <td class="px-6 py-4">
                        {% for group in user_obj.groups.all %}
                            <span class="badge badge-sm badge-primary mr-1">{{ group.name }}</span>
                        {% empty %}
                            <span class="text-gray-400">Keine Rollen</span>
                        {% endfor %}
                    </td>
                    <td class="px-6 py-4">
                        {% if user_obj.is_active %}
                            <span class="badge badge-success">Aktiv</span>
                        {% else %}
                            <span class="badge badge-error">Inaktiv</span>
                        {% endif %}
                    </td>
                    <td class="px-6 py-4">
                        <a href="{% url 'core:user_detail' user_obj.pk %}"
                           class="btn btn-sm btn-primary">
                            Details
                        </a>
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</div>
{% endblock %}
```

#### Schritt 4: Navigation hinzufügen
**In sidebar_nav.html ergänzen (nur für Admins):**
```django
{% if request.user|has_role:'Administrator' %}
<li>
    <a href="{% url 'core:user_list' %}" class="menu-item">
        <i class="fas fa-users"></i>
        <span>Benutzerverwaltung</span>
    </a>
</li>
{% endif %}
```

#### Schritt 5: Testen
```bash
# Server starten
python manage.py runserver

# Browser öffnen:
http://lager.resqware.de/admin/users/

# Sollte User-Liste zeigen
# Klick auf "Details" -> User-Detail mit Rollen
```

---

### Session 2: User Detail & Rollen-Zuweisung (2h)

**user_detail.html (Erweitert):**
```django
{% extends 'base.html' %}
{% load permission_tags %}

{% block content %}
<div class="container mx-auto px-4 py-8">
    <div class="mb-6">
        <a href="{% url 'core:user_list' %}" class="btn btn-sm btn-ghost">
            <i class="fas fa-arrow-left"></i> Zurück zur Liste
        </a>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <!-- User Info -->
        <div class="lg:col-span-1">
            <div class="card bg-white shadow-lg">
                <div class="card-body">
                    <h2 class="card-title">{{ user_obj.get_full_name }}</h2>
                    <p class="text-gray-600">@{{ user_obj.username }}</p>

                    <div class="divider"></div>

                    <dl class="space-y-2">
                        <div>
                            <dt class="font-semibold">Email:</dt>
                            <dd>{{ user_obj.email }}</dd>
                        </div>
                        <div>
                            <dt class="font-semibold">Personalnummer:</dt>
                            <dd>{{ user_obj.personnel_number|default:"—" }}</dd>
                        </div>
                        <div>
                            <dt class="font-semibold">Abteilung:</dt>
                            <dd>{{ user_obj.department|default:"—" }}</dd>
                        </div>
                        <div>
                            <dt class="font-semibold">Status:</dt>
                            <dd>
                                {% if user_obj.is_active %}
                                    <span class="badge badge-success">Aktiv</span>
                                {% else %}
                                    <span class="badge badge-error">Inaktiv</span>
                                {% endif %}
                            </dd>
                        </div>
                    </dl>
                </div>
            </div>
        </div>

        <!-- Rollen & Permissions -->
        <div class="lg:col-span-2">
            <!-- Rollen -->
            <div class="card bg-white shadow-lg mb-6">
                <div class="card-body">
                    <h3 class="card-title">Rollen</h3>

                    <div class="flex flex-wrap gap-2 mb-4">
                        {% for group in user_obj.groups.all %}
                            <div class="badge badge-lg badge-primary gap-2">
                                {{ group.name }}
                                <form method="post" action="{% url 'core:assign_roles' user_obj.pk %}" class="inline">
                                    {% csrf_token %}
                                    <input type="hidden" name="action" value="remove">
                                    <input type="hidden" name="role" value="{{ group.name }}">
                                    <button type="submit" class="btn btn-xs btn-ghost btn-circle">
                                        <i class="fas fa-times"></i>
                                    </button>
                                </form>
                            </div>
                        {% empty %}
                            <p class="text-gray-500">Keine Rollen zugewiesen</p>
                        {% endfor %}
                    </div>

                    <!-- Rolle hinzufügen -->
                    <form method="post" action="{% url 'core:assign_roles' user_obj.pk %}" class="flex gap-2">
                        {% csrf_token %}
                        <input type="hidden" name="action" value="add">
                        <select name="role" class="select select-bordered flex-1">
                            <option disabled selected>Rolle auswählen...</option>
                            {% for role in available_roles %}
                                {% if role not in user_obj.groups.all %}
                                    <option value="{{ role.name }}">{{ role.name }}</option>
                                {% endif %}
                            {% endfor %}
                        </select>
                        <button type="submit" class="btn btn-primary">
                            <i class="fas fa-plus"></i> Hinzufügen
                        </button>
                    </form>
                </div>
            </div>

            <!-- Permission Summary -->
            <div class="card bg-white shadow-lg">
                <div class="card-body">
                    <h3 class="card-title">Berechtigungen</h3>

                    <dl class="grid grid-cols-2 gap-4">
                        <div>
                            <dt class="font-semibold">Superuser:</dt>
                            <dd>
                                {% if permission_summary.is_superuser %}
                                    <span class="badge badge-error">Ja</span>
                                {% else %}
                                    <span class="badge badge-ghost">Nein</span>
                                {% endif %}
                            </dd>
                        </div>
                        <div>
                            <dt class="font-semibold">Freigabelimit:</dt>
                            <dd class="font-mono">
                                {% if permission_summary.approval_limit == float('inf') %}
                                    ∞ (unbegrenzt)
                                {% else %}
                                    {{ permission_summary.approval_limit|floatformat:0 }}€
                                {% endif %}
                            </dd>
                        </div>
                        <div>
                            <dt class="font-semibold">BTM-Berechtigung:</dt>
                            <dd>
                                {% if permission_summary.btm_clearance %}
                                    <span class="badge badge-warning">Ja</span>
                                {% else %}
                                    <span class="badge badge-ghost">Nein</span>
                                {% endif %}
                            </dd>
                        </div>
                        <div>
                            <dt class="font-semibold">Zeitbasierter Zugriff:</dt>
                            <dd>
                                {% if permission_summary.has_time_access %}
                                    <span class="badge badge-success">Aktiv</span>
                                {% else %}
                                    <span class="badge badge-error">Gesperrt</span>
                                {% endif %}
                            </dd>
                        </div>
                    </dl>

                    {% if permission_summary.modules %}
                    <div class="mt-4">
                        <dt class="font-semibold mb-2">Verantwortliche Module:</dt>
                        <div class="flex flex-wrap gap-2">
                            {% for module in permission_summary.modules %}
                                <span class="badge badge-accent">{{ module }}</span>
                            {% endfor %}
                        </div>
                    </div>
                    {% endif %}
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

---

## 🧪 Testing Commands

```bash
# Django Shell öffnen
python manage.py shell

# Befehle zum Testen:
from core.models import User
from permissions.utils import PermissionHelper
from permissions.constants import Roles

# Alle User anzeigen
for u in User.objects.all():
    print(f"{u.username}: {[g.name for g in u.groups.all()]}")

# Rolle zuweisen
user = User.objects.get(username='admin')
PermissionHelper.assign_role(user, Roles.ADMINISTRATOR)

# Prüfen
summary = PermissionHelper.get_user_permission_summary(user)
print(summary)

# BTM-User finden
from permissions.utils import get_btm_authorized_users
btm_users = get_btm_authorized_users()
print(f"BTM-berechtigte User: {btm_users.count()}")

# Alle Rollen auflisten
from django.contrib.auth.models import Group
for g in Group.objects.all():
    print(f"{g.name}: {g.permissions.count()} Permissions, {g.user_set.count()} User")
```

---

## 🐛 Troubleshooting

### Problem: "Permission denied" beim Zugriff auf /admin/users/
**Lösung:**
```python
# Shell:
user = User.objects.get(username='dein_username')
PermissionHelper.assign_role(user, 'Administrator')
```

### Problem: Gruppen sind leer
**Lösung:**
```bash
python manage.py setup_permissions
```

### Problem: Templates werden nicht gefunden
**Lösung:**
```bash
# Prüfe Template-Pfad
ls -la templates/core/user_management/

# Falls Ordner fehlt:
mkdir -p templates/core/user_management
```

### Problem: HTMX funktioniert nicht
**Lösung:**
```html
<!-- In base.html prüfen ob HTMX eingebunden ist: -->
<script src="https://unpkg.com/htmx.org@1.9.10"></script>
```

---

## 📦 Wichtige Imports für morgen

```python
# In Views:
from permissions.utils import PermissionHelper
from permissions.constants import Roles, Modules
from permissions.decorators import require_2fa, require_witness
from permissions.mixins import RoleRequiredMixin, BTMSecurityMixin

# In Templates:
{% load permission_tags %}

# Permission-Checks:
PermissionHelper.assign_role(user, role_name)
PermissionHelper.check_btm_clearance(user)
PermissionHelper.get_approval_limit(user)
PermissionHelper.get_user_permission_summary(user)
```

---

## ✅ Erfolgskriterien für morgen

- [ ] User-Liste lädt und zeigt alle User
- [ ] User-Detail zeigt Rollen und Permissions
- [ ] Rolle kann zugewiesen werden (+ Button funktioniert)
- [ ] Rolle kann entfernt werden (X Button funktioniert)
- [ ] Permission-Summary wird korrekt angezeigt
- [ ] Navigation zeigt "Benutzerverwaltung" nur für Admins

---

**Viel Erfolg morgen! Bei Fragen einfach nach `PERMISSION_IMPLEMENTATION_STATUS.md` schauen.**
