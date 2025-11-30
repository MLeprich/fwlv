"""
Permissions Constants - Single Source of Truth für Berechtigungen
Definiert alle Rollen, Permission-Codes und Limits zentral
"""

# ============================================================================
# ROLLEN (Django Groups)
# ============================================================================

class Roles:
    """Zentrale Definition aller Rollen im System"""

    # Haupt-Rollen
    SUPERUSER = 'Superuser'  # Django Superuser (technisch)
    ADMINISTRATOR = 'Administrator'

    # Spezial-Rollen
    BTM_BEAUFTRAGTER = 'BTM-Beauftragter'
    WERKSTATTMEISTER = 'Werkstattmeister'

    # Modul-Verantwortliche
    MODUL_MEDICAL = 'Modulverantwortlicher Medical'
    MODUL_CLOTHING = 'Modulverantwortlicher Clothing'
    MODUL_MAGAZINE = 'Modulverantwortlicher Magazine'
    MODUL_WORKSHOP = 'Modulverantwortlicher Workshop'
    MODUL_DISINFECTION = 'Modulverantwortlicher Disinfection'
    MODUL_HEIGHT_RESCUE = 'Modulverantwortlicher Height Rescue'
    MODUL_DIVING = 'Modulverantwortlicher Diving'
    MODUL_EQUIPMENT = 'Modulverantwortlicher Equipment'
    MODUL_IT_HARDWARE = 'Modulverantwortlicher IT Hardware'
    MODUL_WIKI = 'Modulverantwortlicher Wiki'
    MODUL_INFO_MONITORS = 'Modulverantwortlicher Info Monitors'

    # Operative Rollen
    BEREICHSLEITUNG = 'Bereichsleitung'
    LAGERVERWALTER = 'Lagerverwalter'
    WACHLEITER = 'Wachleiter'
    SACHBEARBEITER = 'Sachbearbeiter'
    STANDARD_USER = 'Standard-Nutzer'

    @classmethod
    def get_all_roles(cls):
        """Gibt alle definierten Rollen zurück"""
        return [
            cls.ADMINISTRATOR,
            cls.BTM_BEAUFTRAGTER,
            cls.WERKSTATTMEISTER,
            cls.MODUL_MEDICAL,
            cls.MODUL_CLOTHING,
            cls.MODUL_MAGAZINE,
            cls.MODUL_WORKSHOP,
            cls.MODUL_DISINFECTION,
            cls.MODUL_HEIGHT_RESCUE,
            cls.MODUL_DIVING,
            cls.MODUL_EQUIPMENT,
            cls.MODUL_IT_HARDWARE,
            cls.MODUL_WIKI,
            cls.MODUL_INFO_MONITORS,
            cls.BEREICHSLEITUNG,
            cls.LAGERVERWALTER,
            cls.WACHLEITER,
            cls.SACHBEARBEITER,
            cls.STANDARD_USER,
        ]

    @classmethod
    def get_module_roles(cls):
        """Gibt alle Modulverantwortlichen-Rollen zurück"""
        return [
            cls.MODUL_MEDICAL,
            cls.MODUL_CLOTHING,
            cls.MODUL_MAGAZINE,
            cls.MODUL_WORKSHOP,
            cls.MODUL_DISINFECTION,
            cls.MODUL_HEIGHT_RESCUE,
            cls.MODUL_DIVING,
            cls.MODUL_EQUIPMENT,
            cls.MODUL_IT_HARDWARE,
            cls.MODUL_WIKI,
            cls.MODUL_INFO_MONITORS,
        ]

    @classmethod
    def get_privileged_roles(cls):
        """Rollen mit erhöhten Rechten (erfordern 2FA)"""
        return [
            cls.ADMINISTRATOR,
            cls.BTM_BEAUFTRAGTER,
        ]


# ============================================================================
# MODUL-NAMEN (App Labels)
# ============================================================================

class Modules:
    """Zentrale Definition aller Module im System"""

    CORE = 'core'
    PERMISSIONS = 'permissions'
    LOCATIONS = 'locations'
    PERSONNEL = 'personnel'
    VEHICLES = 'vehicles'

    # Lager-Module
    CLOTHING = 'clothing'
    MAGAZINE = 'magazine'
    MEDICAL = 'medical'
    WORKSHOP = 'workshop'
    DISINFECTION = 'disinfection'
    HEIGHT_RESCUE = 'height_rescue'
    DIVING = 'diving'
    EQUIPMENT = 'equipment'
    IT_HARDWARE = 'it_hardware'

    # Prozess-Module
    VEHICLE_HANDOVER = 'vehicle_handover'
    PROCUREMENT = 'procurement'
    INVENTORY_CHECK = 'inventory_check'
    DOCUMENTS = 'documents'
    NOTIFICATIONS = 'notifications'
    AUDIT = 'audit'
    REPORTING = 'reporting'

    # Information-Module
    WIKI = 'wiki'
    INFO_MONITORS = 'info_monitors'

    @classmethod
    def get_all_modules(cls):
        """Alle Module"""
        return [
            cls.CORE,
            cls.PERMISSIONS,
            cls.LOCATIONS,
            cls.PERSONNEL,
            cls.VEHICLES,
            cls.CLOTHING,
            cls.MAGAZINE,
            cls.MEDICAL,
            cls.WORKSHOP,
            cls.DISINFECTION,
            cls.HEIGHT_RESCUE,
            cls.DIVING,
            cls.EQUIPMENT,
            cls.IT_HARDWARE,
            cls.VEHICLE_HANDOVER,
            cls.PROCUREMENT,
            cls.INVENTORY_CHECK,
            cls.DOCUMENTS,
            cls.NOTIFICATIONS,
            cls.AUDIT,
            cls.REPORTING,
            cls.WIKI,
            cls.INFO_MONITORS,
        ]

    @classmethod
    def get_inventory_modules(cls):
        """Nur Lager-Module"""
        return [
            cls.CLOTHING,
            cls.MAGAZINE,
            cls.MEDICAL,
            cls.WORKSHOP,
            cls.DISINFECTION,
            cls.HEIGHT_RESCUE,
            cls.DIVING,
            cls.EQUIPMENT,
            cls.IT_HARDWARE,
        ]


# ============================================================================
# PERMISSION ACTIONS
# ============================================================================

class Actions:
    """Standard CRUD Actions"""

    VIEW = 'view'
    ADD = 'add'
    CHANGE = 'change'
    DELETE = 'delete'

    @classmethod
    def get_all_actions(cls):
        return [cls.VIEW, cls.ADD, cls.CHANGE, cls.DELETE]


# ============================================================================
# CUSTOM PERMISSIONS
# ============================================================================

class CustomPermissions:
    """Custom Permissions über Standard-CRUD hinaus"""

    # Core / System
    MANAGE_USERS = 'core.manage_users'
    ASSIGN_ROLES = 'core.assign_roles'
    VIEW_AUDIT_LOG = 'core.view_audit_log'
    SYSTEM_CONFIGURATION = 'core.system_configuration'

    # BTM (Betäubungsmittel)
    VIEW_BTM_MEDICATION = 'medical.view_btm_medication'
    ADD_BTM_MEDICATION = 'medical.add_btm_medication'
    CHANGE_BTM_MEDICATION = 'medical.change_btm_medication'
    DISPENSE_BTM_MEDICATION = 'medical.dispense_btm_medication'
    DISPOSE_BTM_MEDICATION = 'medical.dispose_btm_medication'
    APPROVE_BTM_ACTION = 'medical.approve_btm_action'
    VIEW_BTM_TRANSACTION = 'medical.view_btm_transaction'

    # Medical (allgemein)
    DISPENSE_MEDICATION = 'medical.dispense_medication'
    DISPOSE_MEDICATION = 'medical.dispose_medication'
    RECEIVE_SHIPMENT = 'medical.receive_shipment'

    # Vehicles
    SCHEDULE_MAINTENANCE = 'vehicles.schedule_maintenance'
    VIEW_VEHICLE_HISTORY = 'vehicles.view_vehicle_history'

    # Vehicle Handover
    COMPLETE_HANDOVER = 'vehicle_handover.complete_handover'

    # Procurement (Bestellwesen)
    CREATE_ORDER_REQUEST = 'procurement.create_order_request'
    VIEW_OWN_ORDERS = 'procurement.view_own_orders'
    APPROVE_ORDER_LOW = 'procurement.approve_order_low'  # bis 1.000€
    APPROVE_ORDER_MEDIUM = 'procurement.approve_order_medium'  # bis 5.000€
    APPROVE_ORDER_HIGH = 'procurement.approve_order_high'  # über 5.000€
    CANCEL_ORDER = 'procurement.cancel_order'

    # Inventory Check
    PERFORM_COUNT = 'inventory_check.perform_count'
    APPROVE_INVENTORY = 'inventory_check.approve_inventory'

    # Documents
    CHANGE_OWN_DOCUMENT = 'documents.change_own_document'

    # Locations
    MANAGE_LOCATION = 'locations.manage_location'

    # Personnel
    VIEW_OWN_PROFILE = 'personnel.view_own_profile'
    VIEW_OWN_QUALIFICATIONS = 'personnel.view_own_qualifications'

    # Clothing
    VIEW_OWN_ASSIGNMENTS = 'clothing.view_own_assignments'

    # Notifications
    VIEW_OWN_NOTIFICATIONS = 'notifications.view_own_notifications'
    CONFIGURE_MODULE_ALERTS = 'notifications.configure_module_alerts'

    # Reporting
    VIEW_ALL_REPORTS = 'reporting.view_all_reports'
    VIEW_MODULE_REPORTS = 'reporting.view_module_reports'
    VIEW_BTM_REPORTS = 'reporting.view_btm_reports'
    EXPORT_REPORTS = 'reporting.export_reports'

    # Wiki
    PUBLISH_WIKI_PAGE = 'wiki.publish_wiki_page'
    APPROVE_WIKI_PAGE = 'wiki.approve_wiki_page'
    DELETE_ANY_WIKI_PAGE = 'wiki.delete_any_wiki_page'
    MANAGE_WIKI_CATEGORIES = 'wiki.manage_wiki_categories'
    VIEW_DRAFT_PAGES = 'wiki.view_draft_pages'
    VIEW_INTERNAL_PAGES = 'wiki.view_internal_pages'

    # Info Monitors
    CREATE_DASHBOARD = 'info_monitors.create_dashboard'
    PUBLISH_DASHBOARD = 'info_monitors.publish_dashboard'
    MANAGE_ACCESS_TOKENS = 'info_monitors.manage_access_tokens'
    CREATE_ACCESS_TOKEN = 'info_monitors.create_access_token'
    DELETE_ACCESS_TOKEN = 'info_monitors.delete_access_token'
    MANAGE_PLAYLISTS = 'info_monitors.manage_playlists'
    VIEW_ALL_DASHBOARDS = 'info_monitors.view_all_dashboards'
    EDIT_ALL_DASHBOARDS = 'info_monitors.edit_all_dashboards'

    @classmethod
    def get_btm_permissions(cls):
        """Alle BTM-spezifischen Permissions"""
        return [
            cls.VIEW_BTM_MEDICATION,
            cls.ADD_BTM_MEDICATION,
            cls.CHANGE_BTM_MEDICATION,
            cls.DISPENSE_BTM_MEDICATION,
            cls.DISPOSE_BTM_MEDICATION,
            cls.APPROVE_BTM_ACTION,
            cls.VIEW_BTM_TRANSACTION,
            cls.VIEW_BTM_REPORTS,
        ]

    @classmethod
    def get_admin_permissions(cls):
        """Alle Admin-spezifischen Permissions"""
        return [
            cls.MANAGE_USERS,
            cls.ASSIGN_ROLES,
            cls.VIEW_AUDIT_LOG,
            cls.SYSTEM_CONFIGURATION,
            cls.VIEW_ALL_REPORTS,
            cls.EXPORT_REPORTS,
        ]


# ============================================================================
# APPROVAL LIMITS (Freigabe-Limits für Bestellungen)
# ============================================================================

class ApprovalLimits:
    """Freigabe-Limits für Bestellungen in Euro"""

    LOW = 1000  # bis 1.000€ - Modulverantwortlicher
    MEDIUM = 5000  # bis 5.000€ - Abteilungsleiter
    HIGH = float('inf')  # über 5.000€ - Administrator

    @classmethod
    def get_required_permission(cls, amount):
        """
        Ermittelt erforderliche Permission basierend auf Betrag

        Args:
            amount (Decimal): Bestellbetrag in Euro

        Returns:
            str: Permission-Code
        """
        if amount <= cls.LOW:
            return CustomPermissions.APPROVE_ORDER_LOW
        elif amount <= cls.MEDIUM:
            return CustomPermissions.APPROVE_ORDER_MEDIUM
        else:
            return CustomPermissions.APPROVE_ORDER_HIGH


# ============================================================================
# PERMISSION GROUPS MAPPING
# ============================================================================

class RolePermissions:
    """
    Mapping von Rollen zu Permissions
    Wird von setup_permissions.py verwendet
    """

    # Administrator - Vollzugriff
    ADMINISTRATOR = {
        'description': 'Vollzugriff auf alle Module und System-Konfiguration',
        'custom_permissions': CustomPermissions.get_admin_permissions() + [
            CustomPermissions.APPROVE_ORDER_HIGH,
            CustomPermissions.CANCEL_ORDER,
        ],
        'modules': Modules.get_all_modules(),  # Voller CRUD für alle Module
        'is_superuser_equivalent': True,
    }

    # BTM-Beauftragter
    BTM_BEAUFTRAGTER = {
        'description': 'Verwaltung von Betäubungsmitteln',
        'custom_permissions': CustomPermissions.get_btm_permissions(),
        'modules': [Modules.MEDICAL],  # Nur Medical-Modul
        'requires_2fa': True,
        'requires_audit': True,
    }

    # Werkstattmeister
    WERKSTATTMEISTER = {
        'description': 'Verwaltung der KFZ-Werkstatt',
        'custom_permissions': [
            CustomPermissions.SCHEDULE_MAINTENANCE,
            CustomPermissions.VIEW_VEHICLE_HISTORY,
            CustomPermissions.APPROVE_ORDER_LOW,
            CustomPermissions.CREATE_ORDER_REQUEST,
        ],
        'modules': [Modules.WORKSHOP, Modules.VEHICLES],
        'crud_actions': {
            Modules.WORKSHOP: [Actions.VIEW, Actions.ADD, Actions.CHANGE, Actions.DELETE],
            Modules.VEHICLES: [Actions.VIEW, Actions.CHANGE],  # Nur View + Change
        }
    }

    # Lagerverwalter
    LAGERVERWALTER = {
        'description': 'Verwaltung von Lagerbeständen',
        'custom_permissions': [
            CustomPermissions.PERFORM_COUNT,
            CustomPermissions.CREATE_ORDER_REQUEST,
            CustomPermissions.VIEW_OWN_ORDERS,
        ],
        'modules': Modules.get_inventory_modules(),
        'crud_actions': {
            # Für alle Lager-Module: View + Add (Update/Delete nur eigene)
            module: [Actions.VIEW, Actions.ADD]
            for module in Modules.get_inventory_modules()
        }
    }

    # Wachleiter
    WACHLEITER = {
        'description': 'Schichtleitung mit Fahrzeugübernahme',
        'custom_permissions': [
            CustomPermissions.COMPLETE_HANDOVER,
            CustomPermissions.CREATE_ORDER_REQUEST,
            CustomPermissions.VIEW_OWN_PROFILE,
            CustomPermissions.VIEW_OWN_QUALIFICATIONS,
        ],
        'modules': [
            Modules.VEHICLE_HANDOVER,
            Modules.VEHICLES,
            Modules.PERSONNEL,
            Modules.MAGAZINE,
            Modules.MEDICAL,
            Modules.EQUIPMENT,
        ],
        'crud_actions': {
            Modules.VEHICLE_HANDOVER: [Actions.VIEW, Actions.ADD, Actions.CHANGE],
            # Restliche nur View
        }
    }

    # Bereichsleitung
    BEREICHSLEITUNG = {
        'description': 'Bereichsleitung mit Leseberechtigung für alle aktiven Module',
        'custom_permissions': [
            CustomPermissions.VIEW_MODULE_REPORTS,
        ],
        'modules': Modules.get_all_modules(),
        'crud_actions': {
            # View-Rechte für alle Module
            module: [Actions.VIEW]
            for module in Modules.get_all_modules()
        }
    }

    # Sachbearbeiter
    SACHBEARBEITER = {
        'description': 'Verwaltungsmitarbeiter mit Read-Zugriff',
        'custom_permissions': [
            CustomPermissions.CREATE_ORDER_REQUEST,
            CustomPermissions.CHANGE_OWN_DOCUMENT,
        ],
        'modules': Modules.get_all_modules(),
        'crud_actions': {
            # Hauptsächlich View für alle
            module: [Actions.VIEW]
            for module in Modules.get_all_modules()
        }
    }

    # Standard-Nutzer
    STANDARD_USER = {
        'description': 'Basis-Mitarbeiter mit eingeschränktem Zugriff',
        'custom_permissions': [
            CustomPermissions.VIEW_OWN_PROFILE,
            CustomPermissions.VIEW_OWN_QUALIFICATIONS,
            CustomPermissions.VIEW_OWN_ASSIGNMENTS,
            CustomPermissions.VIEW_OWN_NOTIFICATIONS,
        ],
        'modules': [Modules.PERSONNEL, Modules.CLOTHING, Modules.VEHICLES],
        'crud_actions': {}  # Nur Custom Permissions
    }


# ============================================================================
# AUDIT ACTIONS (für Audit-Log)
# ============================================================================

class AuditActions:
    """Actions die im Audit-Log protokolliert werden"""

    # User Management
    USER_CREATED = 'user_created'
    USER_UPDATED = 'user_updated'
    USER_DELETED = 'user_deleted'
    USER_LOGIN = 'user_login'
    USER_LOGOUT = 'user_logout'
    USER_LOGIN_FAILED = 'user_login_failed'

    # Role Management
    ROLE_ASSIGNED = 'role_assigned'
    ROLE_REMOVED = 'role_removed'

    # BTM
    BTM_ACCESS = 'btm_access'
    BTM_DISPENSED = 'btm_dispensed'
    BTM_DISPOSED = 'btm_disposed'
    BTM_APPROVED = 'btm_approved'

    # Permissions
    PERMISSION_GRANTED = 'permission_granted'
    PERMISSION_REVOKED = 'permission_revoked'
    DELEGATION_CREATED = 'delegation_created'
    DELEGATION_ENDED = 'delegation_ended'

    # Inventory
    INVENTORY_CREATED = 'inventory_created'
    INVENTORY_UPDATED = 'inventory_updated'
    INVENTORY_DELETED = 'inventory_deleted'
    STOCK_ADJUSTED = 'stock_adjusted'

    # Orders
    ORDER_CREATED = 'order_created'
    ORDER_APPROVED = 'order_approved'
    ORDER_REJECTED = 'order_rejected'
    ORDER_CANCELLED = 'order_cancelled'

    # System
    SYSTEM_CONFIG_CHANGED = 'system_config_changed'
    BACKUP_CREATED = 'backup_created'

    @classmethod
    def get_critical_actions(cls):
        """Kritische Actions die besonders überwacht werden"""
        return [
            cls.BTM_ACCESS,
            cls.BTM_DISPENSED,
            cls.BTM_DISPOSED,
            cls.ROLE_ASSIGNED,
            cls.PERMISSION_GRANTED,
            cls.SYSTEM_CONFIG_CHANGED,
        ]


# ============================================================================
# SESSION SETTINGS
# ============================================================================

class SessionSettings:
    """Session- und Security-Settings"""

    # Session Timeouts (in Sekunden)
    SESSION_TIMEOUT_DEFAULT = 12 * 60 * 60  # 12 Stunden
    SESSION_TIMEOUT_BTM = 2 * 60 * 60  # 2 Stunden für BTM-Nutzer
    SESSION_TIMEOUT_ADMIN = 4 * 60 * 60  # 4 Stunden für Admins

    # Login Attempts
    MAX_LOGIN_ATTEMPTS = 5
    LOCKOUT_DURATION = 30 * 60  # 30 Minuten

    # Password Requirements
    PASSWORD_MIN_LENGTH = 12
    PASSWORD_REQUIRE_UPPERCASE = True
    PASSWORD_REQUIRE_LOWERCASE = True
    PASSWORD_REQUIRE_DIGITS = True
    PASSWORD_REQUIRE_SPECIAL = True

    # 2FA Settings
    TOTP_VALIDITY_WINDOW = 1  # ±30 Sekunden
    BACKUP_CODES_COUNT = 10


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_permission_code(app_label, action, model_name=None):
    """
    Generiert Permission-Code nach Django-Standard

    Args:
        app_label (str): App-Name (z.B. 'medical')
        action (str): Action (z.B. 'view', 'add', 'change', 'delete')
        model_name (str): Model-Name (z.B. 'medication') - optional

    Returns:
        str: Permission-Code (z.B. 'medical.view_medication')
    """
    if model_name:
        return f"{app_label}.{action}_{model_name}"
    return f"{app_label}.{action}"


def is_privileged_role(role_name):
    """
    Prüft ob Rolle erhöhte Rechte hat (2FA erforderlich)

    Args:
        role_name (str): Name der Rolle

    Returns:
        bool: True wenn erhöhte Rechte
    """
    return role_name in Roles.get_privileged_roles()


def get_module_from_role(role_name):
    """
    Extrahiert Modul-Namen aus Modulverantwortlicher-Rolle

    Args:
        role_name (str): Rollen-Name (z.B. 'Modulverantwortlicher Medical')

    Returns:
        str: Modul-Name (z.B. 'medical') oder None
    """
    if role_name.startswith('Modulverantwortlicher '):
        module_display = role_name.replace('Modulverantwortlicher ', '')
        # Map Display-Name zu App-Label
        mapping = {
            'Medical': Modules.MEDICAL,
            'Clothing': Modules.CLOTHING,
            'Magazine': Modules.MAGAZINE,
            'Workshop': Modules.WORKSHOP,
            'Disinfection': Modules.DISINFECTION,
            'Height Rescue': Modules.HEIGHT_RESCUE,
            'Diving': Modules.DIVING,
            'Equipment': Modules.EQUIPMENT,
            'IT Hardware': Modules.IT_HARDWARE,
            'Wiki': Modules.WIKI,
            'Info Monitors': Modules.INFO_MONITORS,
        }
        return mapping.get(module_display)
    return None
