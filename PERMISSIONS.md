# Berechtigungskonzept - FLVS

## Übersicht

Das FLVS verwendet ein mehrstufiges Berechtigungssystem mit CRUD-Rechten pro Modul, Rollen-basierter Zugriffskontrolle und Object-Level-Permissions.

---

## Berechtigungs-Hierarchie

```
┌─────────────────────────────────────────────────────────────┐
│                        Superuser                            │
│            (voller Zugriff auf alles)                       │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────┴───────────────────────────────────┐
│                     Administrator                           │
│         (Vollzugriff alle Module + System-Config)           │
└─────────────────────────┬───────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
┌───────▼────────┐ ┌──────▼───────┐ ┌──────▼────────┐
│ BTM-Beauftragter│ │ Modul-       │ │ Werkstatt-    │
│                 │ │ verantwortl. │ │ meister       │
└───────┬─────────┘ └──────┬───────┘ └──────┬────────┘
        │                  │                 │
┌───────▼──────────────────▼─────────────────▼────────┐
│              Lagerverwalter                         │
│        (CR für Lager, UD nach Freigabe)             │
└─────────────────────────┬───────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┬─────────┐
        │                 │                 │         │
┌───────▼────────┐ ┌──────▼───────┐ ┌──────▼────────┐ │
│ Bereichsleitung│ │  Wachleiter  │ │ Sachbearbeiter│ │
└────────────────┘ └──────────────┘ └───────────────┘ │
                                                       │
                                              ┌────────▼────────┐
                                              │ Standard-Nutzer │
                                              └─────────────────┘
```

---

## Rollen-Definition

### 1. Superuser (Django Admin)
**Technischer Administrator mit vollem System-Zugriff**

- Vollzugriff auf Django Admin Interface
- Kann andere Administratoren ernennen
- Zugriff auf Datenbank-Backups
- System-Konfiguration
- **Keine Business-Rolle** - nur für IT-Administration

**Permissions:**
- `*.*` (alle Permissions)

---

### 2. Administrator
**Fachlicher System-Administrator**

- Vollzugriff auf alle Module
- User-Management (Rollen zuweisen)
- System-Konfiguration (Lagerorte, Fahrzeugtypen, etc.)
- Zugriff auf alle Reports und KPIs
- Freigabe von kritischen Aktionen

**Permissions:**
```python
ADMIN_PERMISSIONS = [
    # Alle CRUD-Rechte für alle Module
    '*.add_*',
    '*.change_*',
    '*.delete_*',
    '*.view_*',
    
    # Spezielle Rechte
    'core.manage_users',
    'core.assign_roles',
    'core.view_audit_log',
    'core.system_configuration',
    
    # Reports
    'reporting.view_all_reports',
    'reporting.export_reports',
]
```

---

### 3. BTM-Beauftragter
**Spezialrolle für Betäubungsmittel-Verwaltung**

- Vollzugriff auf BTM-Bereich (medical.Medication mit is_btm=True)
- Vier-Augen-Prinzip: Benötigt zweiten BTM-Beauftragten für kritische Aktionen
- Zugriff auf BTM-spezifische Berichte
- Muss 2FA aktiviert haben
- Zeitbasierte Zugriffsbeschränkung möglich

**Permissions:**
```python
BTM_PERMISSIONS = [
    'medical.view_medication',
    'medical.view_btm_medication',
    'medical.add_btm_medication',
    'medical.change_btm_medication',
    'medical.dispense_btm_medication',
    'medical.dispose_btm_medication',
    'medical.view_btm_transaction',
    'medical.approve_btm_action',  # Für Vier-Augen-Prinzip
    'reporting.view_btm_reports',
]
```

**Spezielle Regeln:**
```python
# permissions/rules.py
@permission_required('medical.dispense_btm_medication')
@require_2fa
@require_witness(permission='medical.approve_btm_action')
def dispense_btm_medication(request, medication_id):
    # BTM-Ausgabe mit Vier-Augen-Prinzip
    pass
```

---

### 4. Modulverantwortlicher
**Verantwortlich für ein oder mehrere Module**

Beispiel-Varianten:
- **Kleiderkammer-Verantwortlicher**
- **Rettungsdienst-Leiter**
- **Höhenrettungs-Beauftragter**
- **IT-Administrator**

**Basis-Permissions pro Modul:**
```python
MODULE_RESPONSIBLE_PERMISSIONS = [
    # Vollzugriff auf zugewiesene(s) Modul(e)
    '<module>.add_*',
    '<module>.change_*',
    '<module>.delete_*',
    '<module>.view_*',
    
    # Kann Bestellungen für sein Modul freigeben
    'procurement.approve_order_<module>',
    
    # Zugriff auf Modul-spezifische Reports
    'reporting.view_<module>_reports',
    
    # Kann Benachrichtigungen für sein Modul konfigurieren
    'notifications.configure_<module>_alerts',
]
```

**Beispiel: Rettungsdienst-Leiter**
```python
MEDICAL_MODULE_LEAD_PERMISSIONS = [
    'medical.add_medication',
    'medical.change_medication',
    'medical.delete_medication',
    'medical.view_medication',
    'medical.add_medicalequipment',
    'medical.change_medicalequipment',
    'medical.delete_medicalequipment',
    'medical.view_medicalequipment',
    'medical.dispense_medication',  # (außer BTM)
    'medical.receive_shipment',
    'procurement.create_order_medical',
    'procurement.approve_order_medical',
    'reporting.view_medical_reports',
]
```

---

### 5. Werkstattmeister
**Spezialrolle für KFZ-Werkstatt**

- Vollzugriff auf Werkstatt-Modul
- Kann Fahrzeugprüfungen planen und durchführen
- Zugriff auf Fahrzeughistorie
- Kann Reparaturen dokumentieren
- Bestellrechte für Ersatzteile

**Permissions:**
```python
WORKSHOP_MASTER_PERMISSIONS = [
    # Werkstatt-Modul
    'workshop.*',
    
    # Fahrzeuge (eingeschränkt)
    'vehicles.view_vehicle',
    'vehicles.change_vehicle',  # Für Kilometerstand, etc.
    'vehicles.view_vehicleinspection',
    'vehicles.add_vehicleinspection',
    'vehicles.change_vehicleinspection',
    'vehicles.schedule_maintenance',
    
    # Bestellwesen
    'procurement.create_order_workshop',
    'procurement.approve_order_workshop',  # bis zu Limit
    
    # Reports
    'reporting.view_workshop_reports',
    'reporting.view_vehicle_history',
]
```

---

### 6. Lagerverwalter
**Standard-Rolle für Lagermitarbeiter**

- **Create & Read:** Kann neue Items anlegen und alle sehen
- **Update & Delete:** Nur eigene Einträge oder nach Freigabe
- Kann Bestandsänderungen vornehmen
- Kann Inventur durchführen
- Bestellvorschläge erstellen (Freigabe durch Vorgesetzten)

**Permissions:**
```python
WAREHOUSE_KEEPER_PERMISSIONS = [
    # Basis CRUD für zugewiesene Module
    '<module>.add_item',
    '<module>.view_item',
    '<module>.change_own_item',  # Custom Permission
    '<module>.delete_own_item',  # Custom Permission
    
    # Bestandsänderungen
    '<module>.adjust_stock',
    '<module>.transfer_item',
    '<module>.receive_shipment',
    
    # Inventur
    'inventory_check.view_inventorycheck',
    'inventory_check.add_inventorycheck',
    'inventory_check.perform_count',
    
    # Bestellwesen (eingeschränkt)
    'procurement.create_order_request',
    'procurement.view_own_orders',
    
    # Lagerorte
    'locations.view_location',
]
```

---

### 7. Bereichsleitung
**Führungskraft mit Lesezugriff auf alle Module**

- Read-Zugriff auf alle Module
- Kann Reports einsehen
- Übersicht über alle Lagerbestände
- Kann Bestandsinformationen exportieren (lesend)
- Keine Schreibrechte

**Permissions:**
```python
BEREICHSLEITUNG_PERMISSIONS = [
    # View-Rechte für alle Module
    '*.view_*',

    # Reports
    'reporting.view_module_reports',
]
```

---

### 8. Wachleiter
**Schichtleitung mit Übernahme-Rechten**

- Read-Zugriff auf die meisten Module
- Volle Rechte für Fahrzeugübernahmen
- Kann Mängel dokumentieren
- Kann Nachbestellungen anstoßen
- Einsicht in Personal-Qualifikationen

**Permissions:**
```python
SHIFT_LEADER_PERMISSIONS = [
    # Fahrzeugübernahme
    'vehicle_handover.add_vehiclehandover',
    'vehicle_handover.change_vehiclehandover',
    'vehicle_handover.view_vehiclehandover',
    'vehicle_handover.complete_handover',
    
    # Fahrzeuge (Read)
    'vehicles.view_vehicle',
    'vehicles.view_vehiclecompartment',
    
    # Lager (Read für Bestandsprüfung)
    'magazine.view_item',
    'medical.view_medication',
    'equipment.view_equipment',
    
    # Personal (Read für Qualifikationen)
    'personnel.view_person',
    'personnel.view_qualification',
    
    # Kann Nachbestellungen vorschlagen
    'procurement.create_order_request',
]
```

---

### 9. Sachbearbeiter
**Büro/Verwaltungsmitarbeiter**

- Read-Zugriff auf die meisten Daten
- Kann Bestellungen erfassen
- Kann Dokumente hochladen
- Reports ansehen (keine Export-Funktion)

**Permissions:**
```python
CLERK_PERMISSIONS = [
    # View-Only für meiste Module
    '*.view_*',
    
    # Dokumente
    'documents.add_document',
    'documents.view_document',
    'documents.change_own_document',
    
    # Bestellwesen
    'procurement.create_order_request',
    'procurement.view_order',
    
    # Reports (nur ansehen)
    'reporting.view_reports',
]
```

---

### 10. Standard-Nutzer
**Basis-Mitarbeiter**

- Eingeschränkter Read-Zugriff
- Kann eigene Kleiderkammer-Einträge sehen
- Kann eigene Qualifikationen einsehen
- Kann Benachrichtigungen empfangen

**Permissions:**
```python
STANDARD_USER_PERMISSIONS = [
    # Eigene Daten
    'personnel.view_own_profile',
    'personnel.view_own_qualifications',
    
    # Kleiderkammer (eigene Ausgaben)
    'clothing.view_own_assignments',
    
    # Fahrzeuge (basic info)
    'vehicles.view_vehicle',
    
    # Benachrichtigungen
    'notifications.view_own_notifications',
]
```

---

## CRUD-Permissions pro Modul

### Namenskonvention
```
<app_label>.<action>_<model>

Beispiele:
- medical.add_medication
- medical.change_medication
- medical.delete_medication
- medical.view_medication
```

### Standard CRUD-Matrix

| Rolle | Create | Read | Update | Delete |
|-------|--------|------|--------|--------|
| Administrator | ✓ | ✓ | ✓ | ✓ |
| Modulverantwortlicher | ✓ | ✓ | ✓ | ✓* |
| Lagerverwalter | ✓ | ✓ | eigene** | eigene** |
| Bereichsleitung | - | ✓ | - | - |
| Wachleiter | - | ✓ | - | - |
| Sachbearbeiter | - | ✓ | - | - |
| Standard-Nutzer | - | eingeschr. | - | - |

*mit Freigabe
**nur eigene Einträge oder nach Freigabe

---

## Custom Permissions

### Definition

```python
# medical/models.py
class Medication(AbstractInventoryItem):
    class Meta:
        permissions = [
            ('dispense_medication', 'Kann Medikamente ausgeben'),
            ('dispose_medication', 'Kann Medikamente entsorgen'),
            ('view_btm_medication', 'Kann BTM einsehen'),
            ('dispense_btm_medication', 'Kann BTM ausgeben'),
            ('dispose_btm_medication', 'Kann BTM entsorgen'),
            ('approve_btm_action', 'Kann BTM-Aktionen freigeben (Vier-Augen)'),
        ]

# procurement/models.py
class Order(models.Model):
    class Meta:
        permissions = [
            ('approve_order_low', 'Kann Bestellungen bis 1.000€ freigeben'),
            ('approve_order_medium', 'Kann Bestellungen bis 5.000€ freigeben'),
            ('approve_order_high', 'Kann Bestellungen über 5.000€ freigeben'),
            ('cancel_order', 'Kann Bestellungen stornieren'),
        ]

# core/models.py
class User(AbstractUser):
    class Meta:
        permissions = [
            ('manage_users', 'Kann Benutzer verwalten'),
            ('assign_roles', 'Kann Rollen zuweisen'),
            ('view_audit_log', 'Kann Audit-Log einsehen'),
            ('system_configuration', 'Kann System konfigurieren'),
        ]
```

---

## Object-Level Permissions (django-guardian)

### Use Cases

```python
# Beispiel 1: User kann nur eigene Bestellungen sehen
from guardian.shortcuts import assign_perm, get_objects_for_user

# Bei Erstellung
order = Order.objects.create(created_by=request.user, ...)
assign_perm('procurement.view_order', request.user, order)
assign_perm('procurement.change_order', request.user, order)

# Beim Abrufen
my_orders = get_objects_for_user(
    request.user,
    'procurement.view_order',
    Order
)

# Beispiel 2: Modulverantwortlicher für bestimmte Lagerorte
location = Location.objects.get(code='HW-G1-WS')
user = User.objects.get(username='werkstatt_mueller')
assign_perm('locations.manage_location', user, location)

# Prüfung
if user.has_perm('locations.manage_location', location):
    # User darf diesen Lagerort verwalten
    pass
```

---

## Vier-Augen-Prinzip (BTM & kritische Aktionen)

### Implementierung

```python
# medical/decorators.py
from functools import wraps
from django.core.exceptions import PermissionDenied

def require_witness(permission):
    """
    Decorator für Vier-Augen-Prinzip.
    Aktion benötigt Bestätigung durch zweiten User mit entsprechender Permission.
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Prüfe ob Witness-Confirmation vorhanden
            witness_id = request.POST.get('witness_user_id')
            witness_pin = request.POST.get('witness_pin')
            
            if not witness_id or not witness_pin:
                raise PermissionDenied("Vier-Augen-Prinzip: Zeuge erforderlich")
            
            witness = User.objects.get(id=witness_id)
            
            # Prüfe Witness-Permission
            if not witness.has_perm(permission):
                raise PermissionDenied("Zeuge hat keine Berechtigung")
            
            # Prüfe PIN/2FA
            if not witness.check_witness_pin(witness_pin):
                raise PermissionDenied("Ungültige Zeugen-PIN")
            
            # Witness darf nicht derselbe User sein
            if witness.id == request.user.id:
                raise PermissionDenied("Zeuge muss anderer Benutzer sein")
            
            # Füge Witness zum Request hinzu
            request.witness_user = witness
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

# Verwendung
@permission_required('medical.dispose_btm_medication')
@require_2fa
@require_witness('medical.approve_btm_action')
def dispose_btm_medication(request, medication_id):
    medication = get_object_or_404(Medication, id=medication_id, is_btm=True)
    
    # Erstelle BTM-Transaction mit Witness
    BTMTransaction.objects.create(
        medication=medication,
        transaction_type='disposal',
        quantity=request.POST['quantity'],
        primary_user=request.user,
        witness_user=request.witness_user,
        witness_confirmed_at=timezone.now(),
        reason=request.POST['reason'],
        ip_address=request.META['REMOTE_ADDR']
    )
    
    # ... weitere Logik
```

---

## Permission Mixins für Class-Based Views

```python
# core/mixins.py
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.exceptions import PermissionDenied

class ModulePermissionMixin(PermissionRequiredMixin):
    """Basis-Mixin für Modul-basierte Permissions"""
    module_name = None  # Muss von Subclass gesetzt werden
    
    def get_permission_required(self):
        if not self.module_name:
            raise ImproperlyConfigured("module_name must be set")
        
        # Leite Permission aus View-Typ ab
        if hasattr(self, 'object') and self.object:
            action = 'change'
        elif self.request.method == 'POST':
            action = 'add'
        else:
            action = 'view'
        
        return f"{self.module_name}.{action}_{self.model._meta.model_name}"

class BTMSecurityMixin:
    """Extra-Sicherheit für BTM-Bereich"""
    
    def dispatch(self, request, *args, **kwargs):
        # 2FA-Pflicht
        if not request.user.has_2fa_enabled():
            return redirect('enable_2fa')
        
        # IP-Whitelisting (optional)
        if not self.check_ip_whitelist(request):
            raise PermissionDenied("Zugriff nur von autorisierten IPs")
        
        # Log Zugriff
        AuditLog.objects.create(
            user=request.user,
            action='access_btm_area',
            module='medical',
            ip_address=request.META['REMOTE_ADDR'],
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        return super().dispatch(request, *args, **kwargs)
    
    def check_ip_whitelist(self, request):
        # Implementierung IP-Check
        allowed_ips = ['192.168.1.0/24', '10.0.0.0/8']
        client_ip = request.META['REMOTE_ADDR']
        # ... IP-Prüfung
        return True

# Verwendung
class BTMMedicationListView(BTMSecurityMixin, ModulePermissionMixin, ListView):
    model = Medication
    module_name = 'medical'
    template_name = 'medical/btm_list.html'
    
    def get_queryset(self):
        return super().get_queryset().filter(is_btm=True)
```

---

## Template-Tags für Permission-Checks

```python
# core/templatetags/permission_tags.py
from django import template

register = template.Library()

@register.simple_tag(takes_context=True)
def has_module_perm(context, module_name, action):
    """Check if user has permission for module action"""
    user = context['request'].user
    perm = f"{module_name}.{action}"
    return user.has_perm(perm)

@register.filter
def can_edit(user, obj):
    """Check if user can edit object"""
    model_name = obj._meta.model_name
    app_label = obj._meta.app_label
    
    # Prüfe globale Permission
    if user.has_perm(f'{app_label}.change_{model_name}'):
        return True
    
    # Prüfe Object-Level Permission
    from guardian.shortcuts import get_perms
    perms = get_perms(user, obj)
    return f'change_{model_name}' in perms

@register.simple_tag(takes_context=True)
def is_btm_authorized(context):
    """Check if user has BTM clearance"""
    user = context['request'].user
    return (
        user.has_perm('medical.view_btm_medication') and
        user.has_2fa_enabled()
    )
```

**Verwendung in Templates:**
```django
{% load permission_tags %}

{% has_module_perm 'medical' 'add_medication' as can_add %}
{% if can_add %}
  <a href="{% url 'medical:medication_create' %}">Neues Medikament</a>
{% endif %}

{% if object|can_edit:request.user %}
  <button hx-get="{% url 'medical:medication_edit' object.id %}">
    Bearbeiten
  </button>
{% endif %}

{% is_btm_authorized as btm_access %}
{% if btm_access %}
  <a href="{% url 'medical:btm_list' %}">BTM-Verwaltung</a>
{% endif %}
```

---

## Zeitbasierte Berechtigungen

### Implementierung

```python
# permissions/models.py
class TimeBasedPermission(models.Model):
    """Zeitbasierte Zugriffsbeschränkungen"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='time_permissions'
    )
    permission = models.CharField(max_length=255)
    
    # Zeitfenster
    valid_from_time = models.TimeField(
        null=True,
        blank=True,
        help_text="z.B. 08:00 für Start der Dienstzeit"
    )
    valid_to_time = models.TimeField(
        null=True,
        blank=True,
        help_text="z.B. 20:00 für Ende der Dienstzeit"
    )
    
    # Wochentage (JSON Array: [1,2,3,4,5] für Mo-Fr)
    valid_weekdays = models.JSONField(
        default=list,
        blank=True,
        help_text="1=Montag, 7=Sonntag"
    )
    
    # Datum-Bereich
    valid_from_date = models.DateField(null=True, blank=True)
    valid_to_date = models.DateField(null=True, blank=True)
    
    is_active = models.BooleanField(default=True)
    
    def is_currently_valid(self):
        """Prüft ob Permission aktuell gültig ist"""
        now = timezone.now()
        
        # Datum-Check
        if self.valid_from_date and now.date() < self.valid_from_date:
            return False
        if self.valid_to_date and now.date() > self.valid_to_date:
            return False
        
        # Wochentag-Check
        if self.valid_weekdays and now.isoweekday() not in self.valid_weekdays:
            return False
        
        # Zeit-Check
        current_time = now.time()
        if self.valid_from_time and current_time < self.valid_from_time:
            return False
        if self.valid_to_time and current_time > self.valid_to_time:
            return False
        
        return True

# permissions/backends.py
from django.contrib.auth.backends import ModelBackend

class TimeBasedPermissionBackend(ModelBackend):
    """Backend für zeitbasierte Permissions"""
    
    def has_perm(self, user_obj, perm, obj=None):
        # Erst Standard-Check
        if not super().has_perm(user_obj, perm, obj):
            return False
        
        # Dann prüfe zeitbasierte Einschränkungen
        time_perms = TimeBasedPermission.objects.filter(
            user=user_obj,
            permission=perm,
            is_active=True
        )
        
        # Wenn keine zeitbasierten Permissions existieren, erlaube
        if not time_perms.exists():
            return True
        
        # Mindestens eine muss aktuell gültig sein
        return any(tp.is_currently_valid() for tp in time_perms)

# settings.py
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'permissions.backends.TimeBasedPermissionBackend',
]
```

---

## Freigabe-Workflows

### Bestellfreigabe nach Wert

```python
# procurement/models.py
class Order(AuditedModel):
    APPROVAL_STATUS = [
        ('draft', 'Entwurf'),
        ('pending', 'Wartet auf Freigabe'),
        ('approved_l1', 'Freigabe Stufe 1'),
        ('approved_l2', 'Freigabe Stufe 2'),
        ('approved_final', 'Final freigegeben'),
        ('rejected', 'Abgelehnt'),
    ]
    
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    approval_status = models.CharField(
        max_length=20,
        choices=APPROVAL_STATUS,
        default='draft'
    )
    
    # Freigaben
    approved_by_l1 = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name='approved_orders_l1'
    )
    approved_at_l1 = models.DateTimeField(null=True, blank=True)
    
    approved_by_l2 = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name='approved_orders_l2'
    )
    approved_at_l2 = models.DateTimeField(null=True, blank=True)
    
    def get_required_approval_level(self):
        """Ermittle erforderliche Freigabestufe basierend auf Betrag"""
        if self.total_amount <= 1000:
            return 'l1'  # Modulverantwortlicher
        elif self.total_amount <= 5000:
            return 'l2'  # Abteilungsleiter
        else:
            return 'admin'  # Administrator
    
    def can_approve(self, user, level):
        """Prüft ob User auf dieser Stufe freigeben darf"""
        permission_map = {
            'l1': 'procurement.approve_order_low',
            'l2': 'procurement.approve_order_medium',
            'admin': 'procurement.approve_order_high',
        }
        return user.has_perm(permission_map.get(level, ''))
    
    def approve(self, user, level):
        """Freigabe durchführen"""
        if not self.can_approve(user, level):
            raise PermissionDenied("Keine Berechtigung für Freigabe")
        
        if level == 'l1':
            self.approved_by_l1 = user
            self.approved_at_l1 = timezone.now()
            self.approval_status = 'approved_l1'
            
            # Wenn L1 ausreicht, final freigeben
            if self.get_required_approval_level() == 'l1':
                self.approval_status = 'approved_final'
        
        elif level == 'l2':
            if self.approval_status != 'approved_l1':
                raise ValidationError("L1-Freigabe fehlt")
            
            self.approved_by_l2 = user
            self.approved_at_l2 = timezone.now()
            self.approval_status = 'approved_final'
        
        self.save()
        
        # Benachrichtigungen
        NotificationService.send_approval_notification(self, user)

# procurement/views.py
@require_http_methods(['POST'])
@permission_required('procurement.approve_order_low')
def approve_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    
    # Ermittle Freigabestufe des Users
    if request.user.has_perm('procurement.approve_order_high'):
        level = 'admin'
    elif request.user.has_perm('procurement.approve_order_medium'):
        level = 'l2'
    else:
        level = 'l1'
    
    try:
        order.approve(request.user, level)
        messages.success(request, 'Bestellung freigegeben')
    except (PermissionDenied, ValidationError) as e:
        messages.error(request, str(e))
    
    return redirect('procurement:order_detail', order_id)
```

---

## Vertretungsregelungen

```python
# core/models.py
class Delegation(TimeStampedModel):
    """Vertretungsregelungen bei Urlaub/Krankheit"""
    delegator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='delegations_given',
        verbose_name="Vertretener"
    )
    delegate = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='delegations_received',
        verbose_name="Vertreter"
    )
    
    # Zeitraum
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    
    # Welche Permissions werden delegiert?
    delegated_permissions = models.JSONField(
        default=list,
        help_text="Liste der delegierten Permissions"
    )
    
    # Oder: Alle Permissions?
    delegate_all_permissions = models.BooleanField(
        default=False,
        verbose_name="Alle Berechtigungen delegieren"
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # Grund
    reason = models.TextField(
        blank=True,
        help_text="z.B. Urlaub, Krankheit"
    )
    
    class Meta:
        verbose_name = "Vertretung"
        verbose_name_plural = "Vertretungen"
    
    def is_currently_valid(self):
        now = timezone.now()
        return (
            self.is_active and
            self.valid_from <= now <= self.valid_to
        )

# permissions/backends.py
class DelegationPermissionBackend(ModelBackend):
    """Backend für Vertretungs-Permissions"""
    
    def has_perm(self, user_obj, perm, obj=None):
        # Standard-Check
        if super().has_perm(user_obj, perm, obj):
            return True
        
        # Prüfe aktive Vertretungen
        active_delegations = Delegation.objects.filter(
            delegate=user_obj,
            is_active=True,
            valid_from__lte=timezone.now(),
            valid_to__gte=timezone.now()
        )
        
        for delegation in active_delegations:
            if delegation.delegate_all_permissions:
                # User hat alle Rechte des Vertretenen
                if delegation.delegator.has_perm(perm, obj):
                    return True
            else:
                # Nur explizit delegierte Permissions
                if perm in delegation.delegated_permissions:
                    return True
        
        return False
```

---

## Permission-Gruppen

### Vordefinierte Gruppen

```python
# core/management/commands/setup_permissions.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

class Command(BaseCommand):
    help = 'Erstellt Rollen-Gruppen und weist Permissions zu'
    
    def handle(self, *args, **options):
        self.setup_admin_group()
        self.setup_btm_group()
        self.setup_module_lead_groups()
        self.setup_warehouse_keeper_group()
        self.setup_bereichsleitung_group()
        self.setup_shift_leader_group()
        self.setup_clerk_group()
        self.setup_standard_user_group()

        self.stdout.write(self.style.SUCCESS('Gruppen erfolgreich erstellt'))
    
    def setup_admin_group(self):
        """Administrator-Gruppe"""
        group, created = Group.objects.get_or_create(name='Administrator')
        
        # Alle Permissions
        all_perms = Permission.objects.all()
        group.permissions.set(all_perms)
        
        # Custom Permissions
        self.add_custom_perms(group, [
            'core.manage_users',
            'core.assign_roles',
            'core.view_audit_log',
            'core.system_configuration',
        ])
    
    def setup_btm_group(self):
        """BTM-Beauftragte Gruppe"""
        group, created = Group.objects.get_or_create(name='BTM-Beauftragter')
        
        # Medical-Permissions
        medical_ct = ContentType.objects.get(app_label='medical', model='medication')
        btm_perms = Permission.objects.filter(
            content_type=medical_ct,
            codename__in=[
                'view_medication',
                'add_medication',
                'change_medication',
                'view_btm_medication',
                'dispense_btm_medication',
                'dispose_btm_medication',
                'approve_btm_action',
            ]
        )
        group.permissions.add(*btm_perms)
    
    def setup_module_lead_groups(self):
        """Modulverantwortliche (je Modul eine Gruppe)"""
        modules = [
            'medical', 'clothing', 'magazine', 'workshop',
            'disinfection', 'height_rescue', 'diving', 'equipment'
        ]
        
        for module in modules:
            group_name = f'Modulverantwortlicher {module.title()}'
            group, created = Group.objects.get_or_create(name=group_name)
            
            # Alle Permissions für dieses Modul
            module_perms = Permission.objects.filter(
                content_type__app_label=module
            )
            group.permissions.add(*module_perms)
            
            # Plus: Bestellfreigabe
            procurement_perms = Permission.objects.filter(
                content_type__app_label='procurement',
                codename__in=[
                    'create_order_request',
                    'approve_order_low',
                ]
            )
            group.permissions.add(*procurement_perms)
    
    def setup_warehouse_keeper_group(self):
        """Lagerverwalter"""
        group, created = Group.objects.get_or_create(name='Lagerverwalter')
        
        # View & Add für alle Lager-Module
        inventory_apps = [
            'medical', 'clothing', 'magazine', 'workshop',
            'disinfection', 'equipment'
        ]
        
        perms = []
        for app in inventory_apps:
            app_perms = Permission.objects.filter(
                content_type__app_label=app,
                codename__startswith=('view_', 'add_')
            )
            perms.extend(app_perms)
        
        group.permissions.add(*perms)

        # Inventur
        inventory_perms = Permission.objects.filter(
            content_type__app_label='inventory_check'
        )
        group.permissions.add(*inventory_perms)

    def setup_bereichsleitung_group(self):
        """Bereichsleitung"""
        group, created = Group.objects.get_or_create(name='Bereichsleitung')

        # View-Rechte für alle Module
        view_perms = Permission.objects.filter(codename__startswith='view_')
        group.permissions.add(*view_perms)

        # Reports
        reporting_perms = Permission.objects.filter(
            content_type__app_label='reporting',
            codename='view_module_reports'
        )
        group.permissions.add(*reporting_perms)

    def setup_shift_leader_group(self):
        """Wachleiter"""
        group, created = Group.objects.get_or_create(name='Wachleiter')
        
        # Fahrzeugübernahme
        handover_perms = Permission.objects.filter(
            content_type__app_label='vehicle_handover'
        )
        group.permissions.add(*handover_perms)
        
        # View-Rechte für viele Module
        view_perms = Permission.objects.filter(
            codename__startswith='view_',
            content_type__app_label__in=[
                'vehicles', 'personnel', 'medical', 
                'magazine', 'equipment'
            ]
        )
        group.permissions.add(*view_perms)
    
    def setup_clerk_group(self):
        """Sachbearbeiter"""
        group, created = Group.objects.get_or_create(name='Sachbearbeiter')
        
        # Hauptsächlich View-Rechte
        view_perms = Permission.objects.filter(codename__startswith='view_')
        group.permissions.add(*view_perms)
        
        # Plus: Dokumente und Bestellanfragen
        extra_perms = Permission.objects.filter(
            content_type__app_label__in=['documents', 'procurement'],
            codename__in=[
                'add_document', 'change_document',
                'create_order_request', 'view_order'
            ]
        )
        group.permissions.add(*extra_perms)
    
    def setup_standard_user_group(self):
        """Standard-Nutzer"""
        group, created = Group.objects.get_or_create(name='Standard-Nutzer')
        
        # Sehr eingeschränkt
        perms = Permission.objects.filter(
            content_type__app_label__in=['personnel', 'notifications'],
            codename__in=[
                'view_own_profile',
                'view_own_qualifications',
                'view_own_notifications'
            ]
        )
        group.permissions.add(*perms)
    
    def add_custom_perms(self, group, perm_codes):
        """Hilfsfunktion für Custom Permissions"""
        for perm_code in perm_codes:
            app_label, codename = perm_code.split('.')
            try:
                perm = Permission.objects.get(
                    content_type__app_label=app_label,
                    codename=codename
                )
                group.permissions.add(perm)
            except Permission.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(f'Permission {perm_code} nicht gefunden')
                )
```

**Ausführen:**
```bash
python manage.py setup_permissions
```

---

## Permission-Helpers & Utilities

```python
# core/utils/permissions.py
from django.contrib.auth.models import Group
from guardian.shortcuts import assign_perm, remove_perm

class PermissionHelper:
    """Helper-Klasse für Permission-Management"""
    
    @staticmethod
    def assign_role(user, role_name):
        """Weise User eine Rolle (Gruppe) zu"""
        try:
            group = Group.objects.get(name=role_name)
            user.groups.add(group)
            
            # Log
            AuditLog.objects.create(
                user=get_current_user(),
                action='assign_role',
                module='core',
                object_type='user',
                object_id=user.id,
                extra_data={'role': role_name}
            )
            
            return True
        except Group.DoesNotExist:
            return False
    
    @staticmethod
    def remove_role(user, role_name):
        """Entferne Rolle von User"""
        try:
            group = Group.objects.get(name=role_name)
            user.groups.remove(group)
            
            # Log
            AuditLog.objects.create(
                user=get_current_user(),
                action='remove_role',
                module='core',
                object_type='user',
                object_id=user.id,
                extra_data={'role': role_name}
            )
            
            return True
        except Group.DoesNotExist:
            return False
    
    @staticmethod
    def assign_module_responsibility(user, module_name):
        """Mache User zum Modulverantwortlichen"""
        group_name = f'Modulverantwortlicher {module_name.title()}'
        return PermissionHelper.assign_role(user, group_name)
    
    @staticmethod
    def assign_location_management(user, location):
        """Gebe User Verwaltungsrechte für Lagerort"""
        assign_perm('locations.manage_location', user, location)
        
        # Auch für Kind-Lagerorte
        for child in location.get_descendants():
            assign_perm('locations.manage_location', user, child)
    
    @staticmethod
    def get_user_modules(user):
        """Ermittle Module, für die User verantwortlich ist"""
        modules = []
        for group in user.groups.all():
            if group.name.startswith('Modulverantwortlicher '):
                module = group.name.replace('Modulverantwortlicher ', '').lower()
                modules.append(module)
        return modules
    
    @staticmethod
    def check_btm_clearance(user):
        """Umfassende BTM-Berechtigung-Prüfung"""
        return (
            user.has_perm('medical.view_btm_medication') and
            user.has_2fa_enabled() and
            user.is_active and
            not user.is_locked
        )
    
    @staticmethod
    def get_approval_limit(user):
        """Ermittle Freigabelimit für Bestellungen"""
        if user.has_perm('procurement.approve_order_high'):
            return float('inf')  # Unbegrenzt
        elif user.has_perm('procurement.approve_order_medium'):
            return 5000
        elif user.has_perm('procurement.approve_order_low'):
            return 1000
        else:
            return 0

# Verwendung
from core.utils.permissions import PermissionHelper

# User zum BTM-Beauftragten machen
PermissionHelper.assign_role(user, 'BTM-Beauftragter')

# User zum Modulverantwortlichen für Rettungsdienst machen
PermissionHelper.assign_module_responsibility(user, 'medical')

# Prüfe ob User BTM-berechtigt
if PermissionHelper.check_btm_clearance(request.user):
    # Zeige BTM-Bereich
    pass
```

---

## Security Best Practices

### 1. Principle of Least Privilege
- User bekommen nur minimal notwendige Rechte
- Standard-Rolle hat sehr eingeschränkte Rechte
- Erhöhte Rechte nur auf Antrag und nach Review

### 2. Defense in Depth
- Mehrere Sicherheits-Layer:
  - View-Level: @permission_required Decorator
  - Template-Level: {% if perms.app.action %}
  - Model-Level: Custom save() mit Permission-Check
  - API-Level: DRF Permission Classes

### 3. Audit Everything
- Alle Permission-Änderungen loggen
- BTM-Zugriffe vollständig protokollieren
- Regelmäßige Reviews der Audit-Logs

### 4. Secure Defaults
```python
# settings.py
# Sichere Defaults
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/login/'

# Session Security
SESSION_COOKIE_SECURE = True  # Nur HTTPS
SESSION_COOKIE_HTTPONLY = True  # Kein JS-Zugriff
SESSION_COOKIE_SAMESITE = 'Strict'
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_COOKIE_AGE = 43200  # 12 Stunden

# CSRF Protection
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Strict'

# Password Validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 12}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]
```

### 5. Regular Permission Audits
```python
# core/management/commands/audit_permissions.py
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = 'Audit-Report für User-Berechtigungen'
    
    def handle(self, *args, **options):
        User = get_user_model()
        
        # Finde User mit BTM-Zugriff ohne 2FA
        btm_users_no_2fa = User.objects.filter(
            groups__name='BTM-Beauftragter',
            has_2fa_enabled=False
        )
        
        if btm_users_no_2fa.exists():
            self.stdout.write(
                self.style.WARNING(
                    f'{btm_users_no_2fa.count()} BTM-User ohne 2FA!'
                )
            )
        
        # Finde inaktive User mit Permissions
        inactive_with_perms = User.objects.filter(
            is_active=False
        ).exclude(groups__isnull=True)
        
        if inactive_with_perms.exists():
            self.stdout.write(
                self.style.WARNING(
                    f'{inactive_with_perms.count()} inaktive User mit Rechten!'
                )
            )
        
        # Finde abgelaufene Vertretungen
        expired_delegations = Delegation.objects.filter(
            is_active=True,
            valid_to__lt=timezone.now()
        )
        
        if expired_delegations.exists():
            self.stdout.write(
                self.style.WARNING(
                    f'{expired_delegations.count()} abgelaufene Vertretungen!'
                )
            )
            # Deaktiviere automatisch
            expired_delegations.update(is_active=False)
```

---

## Checkliste: Permission-Implementation

- [ ] Alle Rollen-Gruppen erstellt (`setup_permissions`)
- [ ] Custom Permissions in Models definiert
- [ ] Permission-Backends konfiguriert (settings.py)
- [ ] View-Decorators für alle Views
- [ ] Template-Tags für Permission-Checks
- [ ] Object-Level Permissions für sensitive Daten
- [ ] Vier-Augen-Prinzip für BTM implementiert
- [ ] 2FA-Pflicht für BTM-Beauftragte
- [ ] Zeitbasierte Permissions konfiguriert (falls benötigt)
- [ ] Vertretungsregelungen implementiert
- [ ] Freigabe-Workflows für Bestellungen
- [ ] Audit-Logging für alle Permission-Änderungen
- [ ] Permission-Helper-Funktionen
- [ ] Tests für alle Permission-Szenarien
- [ ] Dokumentation für Admins

---

*Version: 1.0*  
*Letzte Aktualisierung: [Datum]*
