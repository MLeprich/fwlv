# FLVS Berechtigungssystem

Diese Dokumentation beschreibt das komplette Berechtigungssystem des Feuerwehr Lagerverwaltungssystems (FLVS).

## Übersicht

Das System verwendet Django's integriertes Permission-System mit gruppenbasierten Rollen. Jede Rolle (Gruppe) hat spezifische Berechtigungen zugewiesen.

## Management Commands

### Berechtigungen einrichten/aktualisieren

```bash
# Alle Gruppen und Berechtigungen einrichten
python manage.py setup_permissions

# Mit Reset (löscht alle Gruppen vorher)
python manage.py setup_permissions --reset

# Trockenlauf (zeigt Änderungen ohne Anwendung)
python manage.py setup_permissions --dry-run
```

**WICHTIG:** Nach dem Hinzufügen neuer Models muss `setup_permissions` erneut ausgeführt werden!

## Rollen-Hierarchie

### Haupt-Rollen

| Rolle | Beschreibung | Permissions |
|-------|--------------|-------------|
| **Administrator** | Vollzugriff auf alle Module und System-Konfiguration | Alle (~770) |
| **BTM-Beauftragter** | Verwaltung von Betäubungsmitteln (Medical-Modul) | 34 |
| **Werkstattmeister** | Verwaltung der KFZ-Werkstatt und Fahrzeuge | 38 |

### Modulverantwortliche

Für jedes Lager-Modul gibt es eine spezielle Rolle mit vollem CRUD-Zugriff:

| Rolle | Permissions | Modul |
|-------|-------------|-------|
| Modulverantwortlicher Equipment | 61 | equipment |
| Modulverantwortlicher Height Rescue | 57 | height_rescue |
| Modulverantwortlicher Diving | 53 | diving |
| Modulverantwortlicher Clothing | 37 | clothing |
| Modulverantwortlicher Info Monitors | 35 | info_monitors |
| Modulverantwortlicher Medical | 34 | medical |
| Modulverantwortlicher Workshop | 33 | workshop |
| Modulverantwortlicher Magazine | 25 | magazine |
| Modulverantwortlicher IT Hardware | 25 | it_hardware |
| Modulverantwortlicher Wiki | 22 | wiki |
| Modulverantwortlicher Disinfection | 20 | disinfection |

### Operative Rollen

| Rolle | Beschreibung | Permissions |
|-------|--------------|-------------|
| **Sachbearbeiter** | View-Rechte für alle Module | 191 |
| **Lagerverwalter** | View + Add für alle Lager-Module | 186 |
| **Wachleiter** | Fahrzeugübernahme + View auf wichtige Module | 86 |
| **Personalverwalter** | Vollzugriff auf Personalverwaltung | 67 |
| **Dokumentenverwalter** | Dokumentenverwaltung | 20 |
| **Standard-Nutzer** | Basis-Zugriff (eigenes Profil, Fahrzeuge) | 16 |

## Berechtigungs-Matrix

### Equipment-Modul (61 Permissions)

| Berechtigung | Modulverantwortlicher | Lagerverwalter | Wachleiter | Sachbearbeiter |
|--------------|----------------------|----------------|------------|----------------|
| view_* | ✓ | ✓ | ✓ | ✓ |
| add_* | ✓ | ✓ | ✗ | ✗ |
| change_* | ✓ | ✗ | ✗ | ✗ |
| delete_* | ✓ | ✗ | ✗ | ✗ |

#### Wartungs-Berechtigungen (Maintenance)

| Permission | Beschreibung |
|------------|--------------|
| `equipment.add_maintenancetype` | Wartungsarten erstellen |
| `equipment.change_maintenancetype` | Wartungsarten bearbeiten |
| `equipment.delete_maintenancetype` | Wartungsarten löschen |
| `equipment.view_maintenancetype` | Wartungsarten ansehen |
| `equipment.add_mastermaintenanceassignment` | Stammdaten-Wartungszuweisungen erstellen |
| `equipment.change_mastermaintenanceassignment` | Stammdaten-Wartungszuweisungen bearbeiten |
| `equipment.delete_mastermaintenanceassignment` | Stammdaten-Wartungszuweisungen löschen |
| `equipment.view_mastermaintenanceassignment` | Stammdaten-Wartungszuweisungen ansehen |
| `equipment.add_maintenancerecord` | Wartungsprotokolle erstellen |
| `equipment.change_maintenancerecord` | Wartungsprotokolle bearbeiten |
| `equipment.delete_maintenancerecord` | Wartungsprotokolle löschen |
| `equipment.view_maintenancerecord` | Wartungsprotokolle ansehen |
| `equipment.add_equipmentmaintenanceassignment` | Geräte-Wartungszuweisungen erstellen |
| `equipment.change_equipmentmaintenanceassignment` | Geräte-Wartungszuweisungen bearbeiten |
| `equipment.delete_equipmentmaintenanceassignment` | Geräte-Wartungszuweisungen löschen |
| `equipment.view_equipmentmaintenanceassignment` | Geräte-Wartungszuweisungen ansehen |

#### Gerätetypen-Berechtigungen

| Permission | Beschreibung |
|------------|--------------|
| `equipment.add_devicetypecategory` | Gerätetypen-Kategorien erstellen |
| `equipment.change_devicetypecategory` | Gerätetypen-Kategorien bearbeiten |
| `equipment.delete_devicetypecategory` | Gerätetypen-Kategorien löschen |
| `equipment.view_devicetypecategory` | Gerätetypen-Kategorien ansehen |

## Permission-Prüfung in Views

### Mit PermissionRequiredMixin (empfohlen)

```python
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin

class MaintenanceTypeCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    permission_required = 'equipment.add_maintenancetype'
    # ...
```

### Mit Decorator

```python
from django.contrib.auth.decorators import permission_required

@permission_required('equipment.add_maintenancetype')
def maintenance_type_create(request):
    # ...
```

### In Templates

```django
{% if perms.equipment.add_maintenancetype %}
    <a href="{% url 'equipment:maintenance_type_create' %}">Neue Wartungsart</a>
{% endif %}

{% if perms.equipment.change_maintenancetype %}
    <a href="{% url 'equipment:maintenance_type_edit' pk=obj.pk %}">Bearbeiten</a>
{% endif %}
```

## Zentrale Konfiguration

Die Berechtigungen werden zentral in folgenden Dateien definiert:

- `permissions/constants.py` - Rollen, Module, Custom Permissions
- `permissions/management/commands/setup_permissions.py` - Setup-Logik

### Custom Permissions (über Standard-CRUD hinaus)

| Permission | Beschreibung |
|------------|--------------|
| `core.manage_users` | Benutzerverwaltung |
| `core.assign_roles` | Rollenzuweisung |
| `core.view_audit_log` | Audit-Log einsehen |
| `medical.dispense_btm_medication` | BTM-Medikamente ausgeben |
| `medical.approve_btm_action` | BTM-Aktionen freigeben |
| `procurement.approve_order_low` | Bestellungen bis 1.000€ freigeben |
| `procurement.approve_order_medium` | Bestellungen bis 5.000€ freigeben |
| `procurement.approve_order_high` | Bestellungen über 5.000€ freigeben |

## Troubleshooting

### Benutzer kann Funktion nicht nutzen

1. Prüfen Sie die Gruppenzugehörigkeit des Benutzers
2. Führen Sie `setup_permissions` aus, um sicherzustellen, dass alle Permissions zugewiesen sind
3. Prüfen Sie die View auf `PermissionRequiredMixin` oder `@permission_required`

### Berechtigungen prüfen (Django Shell)

```python
python manage.py shell

# Benutzer-Berechtigungen prüfen
user = User.objects.get(username='example')
user.has_perm('equipment.add_maintenancetype')  # True/False
user.get_all_permissions()  # Alle Permissions

# Gruppen-Berechtigungen prüfen
from django.contrib.auth.models import Group
group = Group.objects.get(name='Modulverantwortlicher Equipment')
group.permissions.all()  # Alle Permissions der Gruppe
group.permissions.filter(codename__contains='maintenance')  # Maintenance-Permissions
```

### Nach neuen Models

Wenn neue Django-Models hinzugefügt wurden, müssen die Permissions aktualisiert werden:

```bash
# Zuerst Migrations erstellen und anwenden
python manage.py makemigrations
python manage.py migrate

# Dann Permissions aktualisieren
python manage.py setup_permissions
```

## View-Schutz Status pro Modul

| Modul | CRUD-Views geschützt | List/Detail-Views |
|-------|---------------------|-------------------|
| clothing | ✓ Alle mit PermissionRequiredMixin | LoginRequired |
| magazine | ✓ Alle mit PermissionRequiredMixin | LoginRequired |
| workshop | ✓ Alle mit PermissionRequiredMixin | LoginRequired |
| height_rescue | ✓ Alle mit PermissionRequiredMixin | LoginRequired |
| diving | ✓ Alle mit PermissionRequiredMixin | LoginRequired |
| equipment | ✓ Alle mit PermissionRequiredMixin | LoginRequired |
| it_hardware | ✓ Alle mit PermissionRequiredMixin | LoginRequired |
| medical | ✓ Alle mit PermissionRequiredMixin | LoginRequired |
| disinfection | ✓ Alle mit @permission_required | LoginRequired |

**Hinweis:** List- und Detail-Views verwenden nur `LoginRequiredMixin`. Dies ist by-design, da Leserechte für alle authentifizierten Benutzer gelten. CRUD-Operationen (Create, Update, Delete) sind mit spezifischen Permissions geschützt.

## Alle Module mit Permissions

| Modul | App-Label | Permissions |
|-------|-----------|-------------|
| Equipment | equipment | 61 |
| Height Rescue | height_rescue | 57 |
| Diving | diving | 53 |
| Personnel | personnel | 52 |
| Vehicle Handover | vehicle_handover | 40 |
| Clothing | clothing | 37 |
| Info Monitors | info_monitors | 35 |
| Medical | medical | 34 |
| Workshop | workshop | 33 |
| Magazine | magazine | 25 |
| IT Hardware | it_hardware | 25 |
| Wiki | wiki | 22 |
| Tickets | tickets | 22 |
| Disinfection | disinfection | 20 |
| Documents | documents | 20 |
| Procurement | procurement | 20 |
| Reporting | reporting | 20 |
| Inventory Check | inventory_check | 16 |
| Core | core | 16 |
| Organization | organization | 16 |
| Vehicles | vehicles | 12 |
| Permissions | permissions | 12 |
| Notifications | notifications | 8 |
| Inventory Base | inventory_base | 8 |
| Locations | locations | 4 |
| Driving License | driving_license | 4 |

---

*Letzte Aktualisierung: 2026-01-13*
