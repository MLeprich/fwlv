"""
Core Views für FLVS
Haupt-Views wie Dashboard, Profile, Settings, Search, etc.
"""

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, UpdateView, View
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.db.models import Q, Count
from django.utils import timezone
from datetime import timedelta
from django.contrib import messages
from rest_framework.authtoken.models import Token

from core.models import User, UserSettings
from core.forms import (
    UserProfileForm,
    AccountSettingsForm,
    NotificationSettingsForm,
    AppearanceSettingsForm,
    PrivacySettingsForm,
)

# Imports für Profil-Ausrüstungsübersicht
try:
    from clothing.models import ClothingItem, ClothingStockMovement
    CLOTHING_AVAILABLE = True
except ImportError:
    CLOTHING_AVAILABLE = False

try:
    from magazine.models import MagazineStockMovement
    MAGAZINE_AVAILABLE = True
except ImportError:
    MAGAZINE_AVAILABLE = False


class DashboardView(LoginRequiredMixin, TemplateView):
    """
    Haupt-Dashboard mit Übersicht und KPIs
    """
    template_name = 'dashboard.html'

    def get(self, request, *args, **kwargs):
        # Prüfe ob ein QR-Code/Barcode gescannt wurde
        scanned_value = request.GET.get('q', '').strip()
        if scanned_value:
            from django.shortcuts import redirect
            # Wenn der gescannte Wert eine URL ist, direkt weiterleiten
            if scanned_value.startswith('/'):
                return redirect(scanned_value)

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Aktuelles Datum
        context['today'] = timezone.now()
        today_date = timezone.now().date()

        # KPI-Daten (Placeholder - werden später mit echten Daten gefüllt)
        context['critical_stock_count'] = 0
        context['stock_trend'] = 0
        context['stock_trend_direction'] = 'up'
        context['upcoming_inspections'] = 0
        context['pending_orders'] = 0
        context['operational_vehicles'] = 0
        context['total_vehicles'] = 0
        context['expired_qualifications'] = 0
        context['active_inventory_checks'] = 0
        context['inventory_progress'] = 0

        # Ablaufende Medikamente (90 Tage) - aus Medical Modul
        try:
            from medical.models import MedicalBatch
            threshold_90 = today_date + timedelta(days=90)
            context['expiring_medications'] = MedicalBatch.objects.filter(
                expiry_date__lte=threshold_90,
                expiry_date__gte=today_date,
                quantity_remaining__gt=0,
                is_recalled=False
            ).count()
        except ImportError:
            context['expiring_medications'] = 0

        # Kritische Alerts (Placeholder)
        context['critical_alerts'] = []

        # Meine Aufgaben (Placeholder)
        context['my_tasks'] = []

        # Benachrichtigungen (Placeholder)
        context['recent_notifications'] = []

        # Modul-spezifische Badges
        try:
            from medical.models import MedicalItem
            from django.db.models import F
            context['critical_medications_count'] = MedicalItem.objects.filter(
                is_active=True,
                min_quantity__isnull=False,
                quantity__lt=F('min_quantity')
            ).count()
        except ImportError:
            context['critical_medications_count'] = 0

        context['vehicles_in_maintenance'] = 0
        context['pending_inspections'] = 0
        context['pending_approvals'] = 0

        # Letzte Aktivitäten (Placeholder)
        context['recent_activities'] = []

        # Aktuelles Modul für Sidebar-Highlighting
        context['current_module'] = 'dashboard'

        return context


class ProfileView(LoginRequiredMixin, UpdateView):
    """
    Benutzer-Profil anzeigen und bearbeiten
    """
    model = User
    form_class = UserProfileForm
    template_name = 'core/profile.html'
    success_url = reverse_lazy('core:profile')

    def get_object(self, queryset=None):
        """Immer das Profil des aktuellen Benutzers"""
        return self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_module'] = 'profile'

        user = self.request.user

        # Prüfe ob User mit einer Person verknüpft ist
        person = getattr(user, 'person', None)
        context['has_person'] = person is not None

        if person:
            # Zugeordnete Kleidung
            if CLOTHING_AVAILABLE:
                assigned_clothing = ClothingItem.objects.filter(
                    assigned_to=person,
                    is_active=True
                ).select_related('location', 'category').order_by('-assignment_date')
                context['assigned_clothing'] = assigned_clothing
                context['assigned_clothing_count'] = assigned_clothing.count()

                # Berechne Gesamtwert der zugeordneten Kleidung
                total_value = sum(
                    item.unit_price or 0
                    for item in assigned_clothing
                )
                context['assigned_clothing_value'] = total_value

                # Letzte Kleidungs-Bewegungen (Ausgaben an diese Person)
                clothing_movements = ClothingStockMovement.objects.filter(
                    person=person
                ).select_related('item').order_by('-movement_date')[:10]
                context['clothing_movements'] = clothing_movements
            else:
                context['assigned_clothing'] = []
                context['assigned_clothing_count'] = 0
                context['assigned_clothing_value'] = 0
                context['clothing_movements'] = []

            # Letzte Magazin-Ausgaben
            if MAGAZINE_AVAILABLE:
                magazine_movements = MagazineStockMovement.objects.filter(
                    person=person
                ).select_related('item').order_by('-movement_date')[:10]
                context['magazine_movements'] = magazine_movements
            else:
                context['magazine_movements'] = []
        else:
            # Keine Person verknüpft
            context['assigned_clothing'] = []
            context['assigned_clothing_count'] = 0
            context['assigned_clothing_value'] = 0
            context['clothing_movements'] = []
            context['magazine_movements'] = []

        return context

    def form_valid(self, form):
        """Erfolgreiche Speicherung"""
        messages.success(self.request, 'Profil erfolgreich aktualisiert.')
        return super().form_valid(form)


class SettingsView(LoginRequiredMixin, View):
    """
    Benutzer-Einstellungen mit mehreren Sections
    """
    template_name = 'core/settings.html'

    def get(self, request, *args, **kwargs):
        """GET Request - Zeige Einstellungen"""
        user = request.user
        user_settings, created = UserSettings.objects.get_or_create(user=user)

        # Forms initialisieren
        account_form = AccountSettingsForm(instance=user, initial={
            'language': user_settings.language,
            'timezone': user_settings.timezone,
        })
        notification_form = NotificationSettingsForm(instance=user_settings)
        appearance_form = AppearanceSettingsForm(instance=user_settings)
        privacy_form = PrivacySettingsForm(instance=user_settings)

        # API Token Status
        try:
            api_token = Token.objects.get(user=user)
            has_api_token = True
            api_token_key = api_token.key
            api_token_created = api_token.created
        except Token.DoesNotExist:
            has_api_token = False
            api_token_key = None
            api_token_created = None

        # System-Einstellungen für Module-Tab laden
        from core.models import SystemSettings
        modules = SystemSettings.load()

        context = {
            'current_module': 'settings',
            'requires_2fa': user.requires_2fa(),
            'twofa_system_enabled': modules.two_factor_auth_enabled,
            'form': account_form,  # Default form für account.html
            'account_form': account_form,
            'notification_form': notification_form,
            'appearance_form': appearance_form,
            'privacy_form': privacy_form,
            'has_api_token': has_api_token,
            'api_token_key': api_token_key,
            'api_token_created': api_token_created,
            'modules': modules,  # SystemSettings für Module-Tab
        }

        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        """POST Request - Speichere Einstellungen"""
        user = request.user
        user_settings, created = UserSettings.objects.get_or_create(user=user)

        section = request.POST.get('section', 'account')

        if section == 'account':
            form = AccountSettingsForm(request.POST, instance=user)
            if form.is_valid():
                form.save()
                # Sprache und Zeitzone in UserSettings speichern
                user_settings.language = form.cleaned_data.get('language', user_settings.language)
                user_settings.timezone = form.cleaned_data.get('timezone', user_settings.timezone)
                user_settings.save()
                messages.success(request, 'Account-Einstellungen erfolgreich gespeichert.')
                return redirect('core:settings')

        elif section == 'notifications':
            form = NotificationSettingsForm(request.POST, instance=user_settings)
            if form.is_valid():
                form.save()
                messages.success(request, 'Benachrichtigungs-Einstellungen erfolgreich gespeichert.')
                return redirect('core:settings')

        elif section == 'appearance':
            form = AppearanceSettingsForm(request.POST, instance=user_settings)
            if form.is_valid():
                form.save()
                messages.success(request, 'Darstellungs-Einstellungen erfolgreich gespeichert.')
                return redirect('core:settings')

        elif section == 'privacy':
            form = PrivacySettingsForm(request.POST, instance=user_settings)
            if form.is_valid():
                form.save()
                messages.success(request, 'Datenschutz-Einstellungen erfolgreich gespeichert.')
                return redirect('core:settings')

        elif section == 'modules':
            # Nur Superuser dürfen Module aktivieren/deaktivieren
            if user.is_superuser:
                from core.models import SystemSettings

                sys_settings = SystemSettings.load()

                # Module-Status aktualisieren
                sys_settings.wiki_enabled = request.POST.get('wiki_enabled') == 'true'
                sys_settings.procurement_enabled = request.POST.get('procurement_enabled') == 'true'
                sys_settings.inventory_check_enabled = request.POST.get('inventory_check_enabled') == 'true'
                sys_settings.info_monitors_enabled = request.POST.get('info_monitors_enabled') == 'true'
                sys_settings.it_hardware_enabled = request.POST.get('it_hardware_enabled') == 'true'
                sys_settings.tickets_enabled = request.POST.get('tickets_enabled') == 'true'
                sys_settings.ff_dashboard_enabled = request.POST.get('ff_dashboard_enabled') == 'true'
                sys_settings.vehicle_handover_enabled = request.POST.get('vehicle_handover_enabled') == 'true'
                sys_settings.driving_license_enabled = request.POST.get('driving_license_enabled') == 'true'
                sys_settings.updated_by = user
                sys_settings.save()

                # Cache leeren damit Änderungen sofort sichtbar sind
                SystemSettings.clear_cache()

                messages.success(request, 'Modul-Einstellungen erfolgreich gespeichert. Änderungen sind sofort aktiv.')
                return redirect('core:settings')
            else:
                messages.error(request, 'Keine Berechtigung für diese Aktion.')
                return redirect('core:settings')

        elif section == 'security_system':
            # Nur Superuser dürfen Sicherheitseinstellungen ändern
            if user.is_superuser:
                from core.models import SystemSettings

                sys_settings = SystemSettings.load()

                # 2FA Status aktualisieren
                sys_settings.two_factor_auth_enabled = request.POST.get('two_factor_auth_enabled') == 'true'
                sys_settings.updated_by = user
                sys_settings.save()

                # Cache leeren damit Änderungen sofort sichtbar sind
                SystemSettings.clear_cache()

                status = 'aktiviert' if sys_settings.two_factor_auth_enabled else 'deaktiviert'
                messages.success(request, f'Zwei-Faktor-Authentifizierung wurde {status}.')
                return redirect('core:settings')
            else:
                messages.error(request, 'Keine Berechtigung für diese Aktion.')
                return redirect('core:settings')

        # Bei Fehler: Forms erneut anzeigen
        account_form = AccountSettingsForm(instance=user, initial={
            'language': user_settings.language,
            'timezone': user_settings.timezone,
        })
        notification_form = NotificationSettingsForm(instance=user_settings)
        appearance_form = AppearanceSettingsForm(instance=user_settings)
        privacy_form = PrivacySettingsForm(instance=user_settings)

        # Update das entsprechende Form mit Fehlern
        if section == 'account':
            account_form = form
        elif section == 'notifications':
            notification_form = form
        elif section == 'appearance':
            appearance_form = form
        elif section == 'privacy':
            privacy_form = form

        # System-Einstellungen für Module-Tab laden
        from core.models import SystemSettings
        modules = SystemSettings.load()

        context = {
            'current_module': 'settings',
            'requires_2fa': user.requires_2fa(),
            'twofa_system_enabled': modules.two_factor_auth_enabled,
            'form': account_form,
            'account_form': account_form,
            'notification_form': notification_form,
            'appearance_form': appearance_form,
            'privacy_form': privacy_form,
            'modules': modules,  # SystemSettings für Module-Tab
        }

        return render(request, self.template_name, context)


@login_required
def global_search_view(request):
    """
    Globale Suche über alle Module (HTMX)

    Robuste Suche mit individueller Fehlerbehandlung pro Modul
    """
    query = request.GET.get('q', '').strip()

    if not query or len(query) < 2:
        return render(request, 'core/partials/search_results.html', {
            'results': [],
            'query': query
        })

    results = []
    max_results_per_type = 5

    import logging
    logger = logging.getLogger(__name__)

    # 1. PERSONNEL - Personen durchsuchen
    try:
        from personnel.models import Person
        personnel = Person.objects.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(personnel_number__icontains=query) |
            Q(email__icontains=query)
        ).filter(is_active=True).select_related('department')[:max_results_per_type]

        for person in personnel:
            description_parts = []
            if hasattr(person, 'rank') and person.rank:
                description_parts.append(person.rank)
            if person.department:
                description_parts.append(person.department.name)

            results.append({
                'type': 'personnel',
                'title': f'{person.first_name} {person.last_name}',
                'description': 'Personal - ' + ' • '.join(description_parts) if description_parts else 'Personal',
                'url': f'/personnel/persons/{person.id}/',
                'icon': '👤'
            })
    except Exception as e:
        logger.error(f"Error searching personnel: {e}")

    # 2. MEDICAL ITEMS - Medizinische Artikel durchsuchen
    try:
        from medical.models import MedicalItem
        medical_items = MedicalItem.objects.filter(
            Q(name__icontains=query) |
            Q(item_number__icontains=query) |
            Q(pzn__icontains=query)
        ).filter(is_active=True)[:max_results_per_type]

        for item in medical_items:
            description_parts = []
            if hasattr(item, 'active_ingredient') and item.active_ingredient:
                description_parts.append(item.active_ingredient)
            if hasattr(item, 'pzn') and item.pzn:
                description_parts.append(f'PZN: {item.pzn}')

            results.append({
                'type': 'medical_item',
                'title': item.name,
                'description': 'Medizinischer Artikel - ' + ' • '.join(description_parts) if description_parts else 'Medizinischer Artikel',
                'url': f'/medical/items/{item.id}/',
                'icon': '💊'
            })
    except Exception as e:
        logger.error(f"Error searching medical items: {e}")

    # 2b. MEDICAL DEVICES - Medizintechnik Geräte-Instanzen durchsuchen (inkl. zusätzliche Inv.Nr.)
    try:
        from medical.models import MedicalDeviceInstance
        medical_devices = MedicalDeviceInstance.objects.filter(
            Q(inventory_number__icontains=query) |
            Q(serial_number__icontains=query) |
            Q(master__name__icontains=query) |
            Q(additional_inventory_numbers__icontains=query)  # Durchsucht auch zusätzliche Inventarnummern
        ).filter(is_active=True).select_related('master', 'location')[:max_results_per_type]

        for device in medical_devices:
            description_parts = [f'Inv: {device.inventory_number}']
            if device.serial_number:
                description_parts.append(f'SN: {device.serial_number}')
            if device.location:
                description_parts.append(device.location.name)
            # Prüfe ob Match in zusätzlichen Inventarnummern
            if device.additional_inventory_numbers:
                for add_inv in device.additional_inventory_numbers:
                    if query.lower() in add_inv.get('number', '').lower():
                        description_parts.append(f"+ {add_inv.get('number')}")
                        break

            results.append({
                'type': 'medical_device',
                'title': f'{device.master.name}',
                'description': 'Medizintechnik Gerät - ' + ' • '.join(description_parts),
                'url': f'/medical/devices/{device.id}/',
                'icon': '🏥'
            })
    except Exception as e:
        logger.error(f"Error searching medical devices: {e}")

    # 3. VEHICLES - Fahrzeuge durchsuchen
    try:
        from vehicles.models import Vehicle
        vehicles = Vehicle.objects.filter(
            Q(license_plate__icontains=query) |
            Q(call_sign__icontains=query) |
            Q(name__icontains=query)
        ).filter(is_active=True)[:max_results_per_type]

        for vehicle in vehicles:
            description_parts = []
            if hasattr(vehicle, 'call_sign') and vehicle.call_sign:
                description_parts.append(vehicle.call_sign)

            title = vehicle.license_plate if vehicle.license_plate else (vehicle.name if hasattr(vehicle, 'name') and vehicle.name else f'Fahrzeug {vehicle.id}')
            description = ' '.join(description_parts) if description_parts else 'Fahrzeug'

            results.append({
                'type': 'vehicle',
                'title': title,
                'description': f'Fahrzeug - {description}',
                'url': f'/vehicles/{vehicle.id}/',
                'icon': '🚒'
            })
    except Exception as e:
        logger.error(f"Error searching vehicles: {e}")

    # 4. LOCATIONS - Lagerorte durchsuchen
    try:
        from locations.models import Location
        locations = Location.objects.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query)
        ).filter(is_active=True)[:max_results_per_type]

        for location in locations:
            results.append({
                'type': 'location',
                'title': location.name,
                'description': f'Lagerort - {location.description}' if location.description else 'Lagerort',
                'url': f'/locations/{location.id}/',
                'icon': '📍'
            })
    except Exception as e:
        logger.error(f"Error searching locations: {e}")

    # 5. DOCUMENTS - Dokumente durchsuchen (inkl. OCR-Text aus PDFs)
    try:
        from documents.models import Document
        import re

        documents = Document.objects.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(tags__icontains=query) |
            Q(ocr_text__icontains=query) |  # Durchsucht OCR-Text aus PDFs
            Q(document_number__icontains=query)
        ).exclude(
            status='archived'
        ).select_related('category')[:max_results_per_type]

        def extract_snippet(text, query, context_length=100):
            """Extrahiere Textausschnitt mit Kontext um den Suchbegriff"""
            if not text or not query:
                return None

            # Finde erste Übereinstimmung (case-insensitive)
            pattern = re.compile(re.escape(query), re.IGNORECASE)
            match = pattern.search(text)

            if not match:
                return None

            start = match.start()
            end = match.end()

            # Kontext vor und nach dem Match
            snippet_start = max(0, start - context_length)
            snippet_end = min(len(text), end + context_length)

            snippet = text[snippet_start:snippet_end]

            # Ellipsen hinzufügen wenn gekürzt
            if snippet_start > 0:
                snippet = '...' + snippet
            if snippet_end < len(text):
                snippet = snippet + '...'

            return snippet

        def count_matches(text, query):
            """Zähle Anzahl der Übereinstimmungen im Text"""
            if not text or not query:
                return 0
            pattern = re.compile(re.escape(query), re.IGNORECASE)
            return len(pattern.findall(text))

        for doc in documents:
            # Beschreibung mit Dokumenttyp und Kategorie
            description_parts = []
            if doc.category:
                description_parts.append(doc.category.name)

            # Suche nach Snippet in verschiedenen Feldern
            snippet = None
            match_count = 0

            # Prüfe zuerst OCR-Text (wichtigster)
            if doc.ocr_text:
                snippet = extract_snippet(doc.ocr_text, query, context_length=80)
                match_count = count_matches(doc.ocr_text, query)

            # Falls kein Match in OCR, prüfe Beschreibung
            if not snippet and doc.description:
                snippet = extract_snippet(doc.description, query, context_length=80)
                match_count = count_matches(doc.description, query)

            # Falls kein Match, prüfe Tags
            if not snippet and doc.tags:
                snippet = extract_snippet(doc.tags, query, context_length=50)
                match_count = count_matches(doc.tags, query)

            # Beschreibung zusammenbauen
            if snippet:
                description_parts.append(f'"{snippet}"')
                if match_count > 1:
                    description_parts.append(f'({match_count} Treffer)')

            # URL zum Dokument
            doc_url = f'/documents/{doc.id}/'
            if match_count > 1:
                # Bei mehreren Treffern Parameter für Navigation hinzufügen
                doc_url = f'/documents/{doc.id}/?highlight={query}'

            results.append({
                'type': 'document',
                'title': doc.title,
                'description': 'Dokument - ' + ' • '.join(description_parts) if description_parts else 'Dokument',
                'url': doc_url,
                'icon': '📄',
                'match_count': match_count,
                'snippet': snippet
            })
    except Exception as e:
        logger.error(f"Error searching documents: {e}")

    # 6. MAGAZINE - Magazin-Artikel durchsuchen
    try:
        from magazine.models import MagazineItem
        magazine_items = MagazineItem.objects.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(item_number__icontains=query)
        ).filter(is_active=True)[:max_results_per_type]

        for item in magazine_items:
            description_parts = []
            if hasattr(item, 'category') and item.category:
                description_parts.append(item.category.name)
            if hasattr(item, 'current_stock'):
                description_parts.append(f'Bestand: {item.current_stock}')

            results.append({
                'type': 'magazine_item',
                'title': item.name,
                'description': 'Magazin - ' + ' • '.join(description_parts) if description_parts else 'Magazin',
                'url': f'/magazine/items/{item.id}/',
                'icon': '📦'
            })
    except Exception as e:
        logger.error(f"Error searching magazine items: {e}")

    # 7. CLOTHING - Kleiderkammer durchsuchen
    try:
        from clothing.models import ClothingItem
        clothing_items = ClothingItem.objects.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(item_number__icontains=query)
        ).filter(is_active=True)[:max_results_per_type]

        for item in clothing_items:
            description_parts = []
            if hasattr(item, 'category') and item.category:
                description_parts.append(item.category.name)
            if hasattr(item, 'clothing_type'):
                description_parts.append(item.get_clothing_type_display() if hasattr(item, 'get_clothing_type_display') else str(item.clothing_type))

            results.append({
                'type': 'clothing_item',
                'title': item.name,
                'description': 'Kleiderkammer - ' + ' • '.join(description_parts) if description_parts else 'Kleiderkammer',
                'url': f'/clothing/items/{item.id}/',
                'icon': '👕'
            })
    except Exception as e:
        logger.error(f"Error searching clothing items: {e}")

    # 8. EQUIPMENT - Ausrüstung durchsuchen
    try:
        from equipment.models import EquipmentItemMaster
        equipment_items = EquipmentItemMaster.objects.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(manufacturer__icontains=query) |
            Q(model_number__icontains=query)
        ).filter(is_active=True)[:max_results_per_type]

        for item in equipment_items:
            description_parts = []
            if hasattr(item, 'category') and item.category:
                description_parts.append(item.category.name)
            if hasattr(item, 'manufacturer') and item.manufacturer:
                description_parts.append(item.manufacturer)

            results.append({
                'type': 'equipment_item',
                'title': item.name,
                'description': 'Ausrüstung - ' + ' • '.join(description_parts) if description_parts else 'Ausrüstung',
                'url': f'/equipment/masters/{item.id}/',
                'icon': '🛠️'
            })
    except Exception as e:
        logger.error(f"Error searching equipment items: {e}")

    # 8b. EQUIPMENT DEVICES - Ausrüstung Geräte-Instanzen durchsuchen (inkl. zusätzliche Inv.Nr.)
    try:
        from equipment.models import EquipmentDeviceInstance
        equipment_devices = EquipmentDeviceInstance.objects.filter(
            Q(inventory_number__icontains=query) |
            Q(serial_number__icontains=query) |
            Q(master__name__icontains=query) |
            Q(additional_inventory_numbers__icontains=query)  # Durchsucht auch zusätzliche Inventarnummern
        ).filter(is_active=True).select_related('master', 'location')[:max_results_per_type]

        for device in equipment_devices:
            description_parts = [f'Inv: {device.inventory_number}']
            if device.serial_number:
                description_parts.append(f'SN: {device.serial_number}')
            if device.location:
                description_parts.append(device.location.name)
            # Prüfe ob Match in zusätzlichen Inventarnummern
            if device.additional_inventory_numbers:
                for add_inv in device.additional_inventory_numbers:
                    if query.lower() in add_inv.get('number', '').lower():
                        description_parts.append(f"+ {add_inv.get('number')}")
                        break

            results.append({
                'type': 'equipment_device',
                'title': f'{device.master.name}',
                'description': 'Ausrüstung Gerät - ' + ' • '.join(description_parts),
                'url': f'/equipment/device/{device.id}/',
                'icon': '🔧'
            })
    except Exception as e:
        logger.error(f"Error searching equipment devices: {e}")

    # 9. WORKSHOP - KFZ-Werkstatt durchsuchen
    try:
        from workshop.models import WorkshopItemMaster
        workshop_items = WorkshopItemMaster.objects.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(manufacturer__icontains=query) |
            Q(part_number__icontains=query)
        ).filter(is_active=True)[:max_results_per_type]

        for item in workshop_items:
            description_parts = []
            if hasattr(item, 'category') and item.category:
                description_parts.append(item.category.name)
            if hasattr(item, 'manufacturer') and item.manufacturer:
                description_parts.append(item.manufacturer)

            results.append({
                'type': 'workshop_item',
                'title': item.name,
                'description': 'KFZ-Werkstatt - ' + ' • '.join(description_parts) if description_parts else 'KFZ-Werkstatt',
                'url': f'/workshop/masters/{item.id}/',
                'icon': '🔧'
            })
    except Exception as e:
        logger.error(f"Error searching workshop items: {e}")

    # 10. DIVING - Taucher durchsuchen
    try:
        from diving.models import DivingItemMaster
        diving_items = DivingItemMaster.objects.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(manufacturer__icontains=query) |
            Q(model_number__icontains=query)
        ).filter(is_active=True)[:max_results_per_type]

        for item in diving_items:
            description_parts = []
            if hasattr(item, 'category') and item.category:
                description_parts.append(item.category.name)
            if hasattr(item, 'manufacturer') and item.manufacturer:
                description_parts.append(item.manufacturer)

            results.append({
                'type': 'diving_item',
                'title': item.name,
                'description': 'Taucher - ' + ' • '.join(description_parts) if description_parts else 'Taucher',
                'url': f'/diving/masters/{item.id}/',
                'icon': '🤿'
            })
    except Exception as e:
        logger.error(f"Error searching diving items: {e}")

    # 10b. DIVING DEVICES - Taucher Geräte-Instanzen durchsuchen (für Barcode-Scan)
    try:
        from diving.models import DivingDeviceInstance
        diving_devices = DivingDeviceInstance.objects.filter(
            Q(inventory_number__icontains=query) |
            Q(serial_number__icontains=query) |
            Q(master__name__icontains=query)
        ).filter(is_active=True).select_related('master', 'location')[:max_results_per_type]

        for device in diving_devices:
            description_parts = [f'Inv: {device.inventory_number}']
            if device.serial_number:
                description_parts.append(f'SN: {device.serial_number}')
            if device.location:
                description_parts.append(device.location.name)

            results.append({
                'type': 'diving_device',
                'title': f'{device.master.name}',
                'description': 'Taucher Gerät - ' + ' • '.join(description_parts),
                'url': f'/diving/device/{device.id}/',
                'icon': '🤿'
            })
    except Exception as e:
        logger.error(f"Error searching diving devices: {e}")

    # 11. HEIGHT RESCUE - Höhenrettung durchsuchen
    try:
        from height_rescue.models import HeightRescueItemMaster
        height_rescue_items = HeightRescueItemMaster.objects.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(manufacturer__icontains=query) |
            Q(model_number__icontains=query)
        ).filter(is_active=True)[:max_results_per_type]

        for item in height_rescue_items:
            description_parts = []
            if hasattr(item, 'category') and item.category:
                description_parts.append(item.category.name)
            if hasattr(item, 'manufacturer') and item.manufacturer:
                description_parts.append(item.manufacturer)

            results.append({
                'type': 'height_rescue_item',
                'title': item.name,
                'description': 'Höhenrettung - ' + ' • '.join(description_parts) if description_parts else 'Höhenrettung',
                'url': f'/height-rescue/masters/{item.id}/',
                'icon': '🧗'
            })
    except Exception as e:
        logger.error(f"Error searching height rescue items: {e}")

    # WIKI - Wiki-Seiten durchsuchen (nur wenn Modul aktiviert)
    try:
        from core.models import SystemSettings
        from wiki.models import WikiPage

        sys_settings = SystemSettings.load()

        if sys_settings.wiki_enabled:
            # Suche in Titel, Beschreibung und Tags
            # Zeige veröffentlichte Seiten + eigene Entwürfe
            wiki_pages = WikiPage.objects.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query) |
                Q(tags__icontains=query)
            ).filter(
                is_deleted=False
            ).filter(
                Q(status=WikiPage.STATUS_PUBLISHED) |  # Veröffentlichte für alle
                Q(created_by=request.user)  # Eigene Seiten (auch Entwürfe)
            ).select_related('category', 'created_by')[:max_results_per_type]

            for page in wiki_pages:
                # Prüfe ob User die Seite sehen darf
                if not page.can_user_view(request.user):
                    continue

                description_parts = []

                # Status-Badge hinzufügen (nur für Entwürfe/nicht-veröffentlichte)
                if page.status != WikiPage.STATUS_PUBLISHED:
                    status_labels = {
                        WikiPage.STATUS_DRAFT: '📝 Entwurf',
                        WikiPage.STATUS_REVIEW: '🔍 In Prüfung',
                        WikiPage.STATUS_ARCHIVED: '📦 Archiviert'
                    }
                    status_label = status_labels.get(page.status, page.status)
                    description_parts.append(status_label)

                if page.category:
                    description_parts.append(f'{page.category.icon} {page.category.name}')

                if page.description:
                    # Kurzer Ausschnitt der Beschreibung
                    desc_snippet = page.description[:100]
                    if len(page.description) > 100:
                        desc_snippet += '...'
                    description_parts.append(desc_snippet)

                # Tags hinzufügen wenn vorhanden
                if page.tags and isinstance(page.tags, list) and page.tags:
                    tags_str = ', '.join(page.tags[:3])
                    if len(page.tags) > 3:
                        tags_str += '...'
                    description_parts.append(f'Tags: {tags_str}')

                results.append({
                    'type': 'wiki_page',
                    'title': page.title,
                    'description': 'Wiki - ' + ' • '.join(description_parts) if description_parts else 'Wiki',
                    'url': page.get_absolute_url(),
                    'icon': '📖'
                })
    except Exception as e:
        logger.error(f"Error searching wiki pages: {e}")

    # Sortiere Ergebnisse nach Relevanz
    # Priorität: Exakte Übereinstimmung > Beginnt mit > Enthält
    def get_relevance_score(result):
        try:
            title_lower = result.get('title', '').lower()
            query_lower = query.lower()

            if title_lower == query_lower:
                return 3  # Exakt
            elif title_lower.startswith(query_lower):
                return 2  # Beginnt mit
            else:
                return 1  # Enthält
        except:
            return 0

    try:
        results.sort(key=get_relevance_score, reverse=True)
    except Exception as e:
        logger.error(f"Error sorting results: {e}")

    return render(request, 'core/partials/search_results.html', {
        'results': results[:20],  # Max 20 Ergebnisse insgesamt
        'query': query
    })


@login_required
def barcode_scan_view(request):
    """
    Barcode/QR-Code Scanner Endpoint

    Akzeptiert gescannte Werte und leitet direkt zur Artikel-/Geräte-Seite weiter.
    Unterstützt:
    - JSON aus QR-Codes (mit 'url' oder 'type' Feld)
    - Einfache IDs (item_number, inventory_number, etc.)
    """
    import json
    import logging
    from django.shortcuts import redirect
    from django.contrib import messages

    logger = logging.getLogger(__name__)
    scanned_value = request.GET.get('q', '').strip()

    if not scanned_value:
        messages.warning(request, 'Kein Scan-Wert übermittelt.')
        return redirect('core:dashboard')

    # 1. Versuche JSON zu parsen (QR-Code)
    try:
        data = json.loads(scanned_value)

        # Falls URL direkt enthalten -> Redirect
        if 'url' in data and data['url']:
            url = data['url']
            # Sicherheitscheck: nur relative URLs oder gleicher Host
            if url.startswith('/'):
                return redirect(url)
            elif request.get_host() in url:
                # Extrahiere relativen Pfad
                from urllib.parse import urlparse
                parsed = urlparse(url)
                return redirect(parsed.path)

        # Falls type und identifier -> Suche basierend auf type
        item_type = data.get('type', '')
        identifier = (
            data.get('inventory_number') or
            data.get('item_number') or
            data.get('master_number') or
            data.get('barcode') or
            data.get('serial_number')
        )

        if item_type and identifier:
            scanned_value = identifier
            # Weiter zur ID-Suche unten
        elif identifier:
            scanned_value = identifier

    except (json.JSONDecodeError, TypeError):
        # Kein JSON -> behandle als einfache ID
        pass

    # 2. Suche in allen Modulen nach der ID
    found_items = []

    # Medical Masters
    try:
        from medical.models import MedicalItemMaster
        items = MedicalItemMaster.objects.filter(
            Q(master_number__iexact=scanned_value) |
            Q(pzn__iexact=scanned_value)
        )[:1]
        for item in items:
            found_items.append({
                'url': f'/medical/masters/{item.pk}/',
                'name': item.name,
                'type': 'Medical Master'
            })
    except Exception as e:
        logger.debug(f"Medical Master search error: {e}")

    # Medical Devices (inkl. zusätzliche Inventarnummern)
    try:
        from medical.models import MedicalDeviceInstance
        # Erst nach Haupt-Inventarnummer und Seriennummer suchen
        items = MedicalDeviceInstance.objects.filter(
            Q(inventory_number__iexact=scanned_value) |
            Q(serial_number__iexact=scanned_value)
        )[:1]
        # Falls nicht gefunden, in zusätzlichen Inventarnummern suchen
        if not items.exists():
            items = MedicalDeviceInstance.objects.filter(
                additional_inventory_numbers__icontains=scanned_value
            )[:1]
        for item in items:
            found_items.append({
                'url': f'/medical/devices/{item.pk}/',
                'name': str(item),
                'type': 'Medical Device'
            })
    except Exception as e:
        logger.debug(f"Medical Device search error: {e}")

    # Clothing
    try:
        from clothing.models import ClothingItem
        items = ClothingItem.objects.filter(
            Q(item_number__iexact=scanned_value) |
            Q(barcode__iexact=scanned_value)
        )[:1]
        for item in items:
            found_items.append({
                'url': f'/clothing/items/{item.pk}/',
                'name': item.name,
                'type': 'Kleidung'
            })
    except Exception as e:
        logger.debug(f"Clothing search error: {e}")

    # Magazine
    try:
        from magazine.models import MagazineItem
        items = MagazineItem.objects.filter(
            Q(item_number__iexact=scanned_value) |
            Q(barcode__iexact=scanned_value)
        )[:1]
        for item in items:
            found_items.append({
                'url': f'/magazine/items/{item.pk}/',
                'name': item.name,
                'type': 'Magazin'
            })
    except Exception as e:
        logger.debug(f"Magazine search error: {e}")

    # Equipment Masters
    try:
        from equipment.models import EquipmentItemMaster
        items = EquipmentItemMaster.objects.filter(
            master_number__iexact=scanned_value
        )[:1]
        for item in items:
            found_items.append({
                'url': f'/equipment/masters/{item.pk}/',
                'name': item.name,
                'type': 'Equipment Master'
            })
    except Exception as e:
        logger.debug(f"Equipment Master search error: {e}")

    # Equipment Devices (inkl. zusätzliche Inventarnummern)
    try:
        from equipment.models import EquipmentDeviceInstance
        # Erst nach Haupt-Inventarnummer und Seriennummer suchen
        items = EquipmentDeviceInstance.objects.filter(
            Q(inventory_number__iexact=scanned_value) |
            Q(serial_number__iexact=scanned_value)
        )[:1]
        # Falls nicht gefunden, in zusätzlichen Inventarnummern suchen
        if not items.exists():
            items = EquipmentDeviceInstance.objects.filter(
                additional_inventory_numbers__icontains=scanned_value
            )[:1]
        for item in items:
            found_items.append({
                'url': f'/equipment/device/{item.pk}/',
                'name': str(item),
                'type': 'Equipment Device'
            })
    except Exception as e:
        logger.debug(f"Equipment Device search error: {e}")

    # Height Rescue Masters
    try:
        from height_rescue.models import HeightRescueItemMaster
        items = HeightRescueItemMaster.objects.filter(
            master_number__iexact=scanned_value
        )[:1]
        for item in items:
            found_items.append({
                'url': f'/height_rescue/masters/{item.pk}/',
                'name': item.name,
                'type': 'Höhenrettung Master'
            })
    except Exception as e:
        logger.debug(f"Height Rescue Master search error: {e}")

    # Height Rescue Devices
    try:
        from height_rescue.models import HeightRescueDeviceInstance
        items = HeightRescueDeviceInstance.objects.filter(
            Q(inventory_number__iexact=scanned_value) |
            Q(serial_number__iexact=scanned_value) |
            Q(custom_barcode__iexact=scanned_value)
        )[:1]
        for item in items:
            found_items.append({
                'url': f'/height_rescue/device/{item.pk}/',
                'name': str(item),
                'type': 'Höhenrettung Device'
            })
    except Exception as e:
        logger.debug(f"Height Rescue Device search error: {e}")

    # Diving Masters
    try:
        from diving.models import DivingItemMaster
        items = DivingItemMaster.objects.filter(
            master_number__iexact=scanned_value
        )[:1]
        for item in items:
            found_items.append({
                'url': f'/diving/masters/{item.pk}/',
                'name': item.name,
                'type': 'Taucher Master'
            })
    except Exception as e:
        logger.debug(f"Diving Master search error: {e}")

    # Diving Devices
    try:
        from diving.models import DivingDeviceInstance
        items = DivingDeviceInstance.objects.filter(
            Q(inventory_number__iexact=scanned_value) |
            Q(serial_number__iexact=scanned_value)
        )[:1]
        for item in items:
            found_items.append({
                'url': f'/diving/device/{item.pk}/',
                'name': str(item),
                'type': 'Taucher Device'
            })
    except Exception as e:
        logger.debug(f"Diving Device search error: {e}")

    # Workshop Masters
    try:
        from workshop.models import WorkshopItemMaster
        items = WorkshopItemMaster.objects.filter(
            Q(item_number__iexact=scanned_value)
        )[:1]
        for item in items:
            found_items.append({
                'url': f'/workshop/item/{item.pk}/',
                'name': item.name,
                'type': 'Werkstatt'
            })
    except Exception as e:
        logger.debug(f"Workshop search error: {e}")

    # Workshop Tool Instances
    try:
        from workshop.models import WorkshopToolInstance
        items = WorkshopToolInstance.objects.filter(
            Q(inventory_number__iexact=scanned_value) |
            Q(serial_number__iexact=scanned_value)
        )[:1]
        for item in items:
            found_items.append({
                'url': f'/workshop/tool/{item.pk}/',
                'name': str(item),
                'type': 'Werkstatt Tool'
            })
    except Exception as e:
        logger.debug(f"Workshop Tool search error: {e}")

    # 3. Ergebnis-Handling
    if len(found_items) == 1:
        # Eindeutiger Treffer -> direkt weiterleiten
        return redirect(found_items[0]['url'])
    elif len(found_items) > 1:
        # Mehrere Treffer -> Warnung und zur Suche
        messages.info(
            request,
            f'Mehrere Treffer für "{scanned_value}" gefunden. Bitte wählen Sie den gewünschten Artikel.'
        )
        return redirect(f'/core/search/?q={scanned_value}')
    else:
        # Kein Treffer
        messages.warning(request, f'Kein Artikel gefunden für: {scanned_value}')
        return redirect(f'/core/search/?q={scanned_value}')


@login_required
def notifications_dropdown_view(request):
    """
    Benachrichtigungen-Dropdown (HTMX)
    """
    # TODO: Später mit echten Benachrichtigungen aus notifications app
    notifications = []

    return render(request, 'core/partials/notifications_dropdown.html', {
        'notifications': notifications
    })


@login_required
def notifications_list_view(request):
    """
    Vollständige Benachrichtigungsliste
    """
    # TODO: Später mit echten Benachrichtigungen aus notifications app
    notifications = []

    return render(request, 'core/notifications_list.html', {
        'notifications': notifications,
        'current_module': 'notifications'
    })


@login_required
def alerts_view(request):
    """
    Kritische Alerts/Warnungen
    """
    # TODO: Später mit echten Alerts
    alerts = []

    return render(request, 'core/alerts.html', {
        'alerts': alerts,
        'current_module': 'alerts'
    })


@login_required
def inventory_critical_view(request):
    """
    Übersicht kritische Bestände (alle Module)
    """
    # TODO: Später aggregierte Daten aus allen Inventory-Modulen
    critical_items = []

    return render(request, 'core/inventory_critical.html', {
        'critical_items': critical_items,
        'current_module': 'inventory'
    })


@login_required
def inspections_upcoming_view(request):
    """
    Übersicht anstehende Prüfungen (alle Module)
    """
    # TODO: Später aggregierte Prüfungen aus equipment, workshop, etc.
    upcoming_inspections = []

    return render(request, 'core/inspections_upcoming.html', {
        'upcoming_inspections': upcoming_inspections,
        'current_module': 'inspections'
    })


@login_required
def activity_log_view(request):
    """
    Aktivitäts-Log (alle Aktionen)
    """
    # TODO: Später mit echten Daten aus audit app
    activities = []

    return render(request, 'core/activity_log.html', {
        'activities': activities,
        'current_module': 'activity'
    })


@login_required
def tasks_toggle_view(request, task_id):
    """
    Task als erledigt markieren (HTMX)
    """
    # TODO: Später mit echtem Task-System
    if request.method == 'POST':
        return JsonResponse({'status': 'success'})

    return JsonResponse({'status': 'error'}, status=400)


@login_required
def send_test_email_view(request):
    """
    Sendet eine Test-E-Mail an den aktuellen Benutzer
    """
    if request.method == 'POST':
        from notifications.tasks import send_test_email

        # Sende Test-E-Mail asynchron via Celery
        send_test_email.delay(request.user.id)

        messages.success(
            request,
            f'Test-E-Mail wird an {request.user.email} gesendet. Überprüfen Sie Ihr Postfach in wenigen Minuten.'
        )

        return redirect('core:settings')

    return redirect('core:settings')


@login_required
def force_password_change_view(request):
    """
    Erzwungene Passwortänderung für neue Benutzer
    """
    # Wenn Benutzer password_must_change nicht gesetzt hat, zurück zum Dashboard
    if not request.user.password_must_change:
        return redirect('core:dashboard')

    if request.method == 'POST':
        from django.contrib.auth.forms import PasswordChangeForm

        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            # Flag zurücksetzen
            user.password_must_change = False
            user.save()

            # Session aktualisieren, damit Benutzer eingeloggt bleibt
            from django.contrib.auth import update_session_auth_hash
            update_session_auth_hash(request, user)

            messages.success(
                request,
                'Ihr Passwort wurde erfolgreich geändert. Sie können jetzt das System nutzen.'
            )
            return redirect('core:dashboard')
    else:
        from django.contrib.auth.forms import PasswordChangeForm
        form = PasswordChangeForm(request.user)

    return render(request, 'core/force_password_change.html', {
        'form': form,
        'user': request.user
    })


# ============================================================================
# API TOKEN MANAGEMENT
# ============================================================================

@login_required
def generate_api_token(request):
    """
    Generiert oder regeneriert einen API-Token für den User
    Nur für Superuser zugänglich
    """
    if not request.user.is_superuser:
        messages.error(request, 'Keine Berechtigung für diese Aktion.')
        return redirect('core:settings')

    if request.method == 'POST':
        # Lösche alten Token falls vorhanden
        Token.objects.filter(user=request.user).delete()

        # Erstelle neuen Token
        token = Token.objects.create(user=request.user)

        messages.success(
            request,
            f'API-Token wurde erfolgreich generiert. Bewahren Sie ihn sicher auf!'
        )

        return redirect('core:settings')

    return redirect('core:settings')


@login_required
def revoke_api_token(request):
    """
    Widerruft den API-Token des Users
    Nur für Superuser zugänglich
    """
    if not request.user.is_superuser:
        messages.error(request, 'Keine Berechtigung für diese Aktion.')
        return redirect('core:settings')

    if request.method == 'POST':
        deleted_count, _ = Token.objects.filter(user=request.user).delete()

        if deleted_count > 0:
            messages.success(
                request,
                'API-Token wurde erfolgreich widerrufen.'
            )
        else:
            messages.info(
                request,
                'Sie hatten keinen aktiven API-Token.'
            )

        return redirect('core:settings')

    return redirect('core:settings')


# ============================================================================
# BACKUP / RESTORE
# ============================================================================

@login_required
def backup_export(request):
    """
    Exportiert die komplette Datenbank als JSON-Datei.
    Nur für Superuser zugänglich.
    """
    import json
    import subprocess
    import tempfile
    import os
    from django.http import HttpResponse
    from django.utils import timezone as django_timezone

    if not request.user.is_superuser:
        messages.error(request, 'Keine Berechtigung für diese Aktion.')
        return redirect('core:settings')

    if request.method != 'POST':
        return redirect('core:settings')

    try:
        # Django dumpdata über subprocess aufrufen
        # Wir nutzen das Management Command für maximale Kompatibilität
        from django.core.management import call_command
        from io import StringIO

        output = StringIO()

        # Alle Apps exportieren, außer contenttypes und auth.permission (werden beim Import neu erstellt)
        call_command(
            'dumpdata',
            '--natural-foreign',
            '--natural-primary',
            '--exclude=contenttypes',
            '--exclude=auth.permission',
            '--exclude=admin.logentry',
            '--exclude=sessions.session',
            '--indent=2',
            stdout=output
        )

        json_data = output.getvalue()

        # Dateiname mit Zeitstempel
        timestamp = django_timezone.now().strftime('%Y-%m-%d_%H-%M-%S')
        filename = f'flvs_backup_{timestamp}.json'

        # Response als Download
        response = HttpResponse(json_data, content_type='application/json')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        messages.success(request, f'Backup erfolgreich erstellt: {filename}')

        return response

    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Backup export failed: {e}")
        messages.error(request, f'Fehler beim Erstellen des Backups: {str(e)}')
        return redirect('core:settings')


@login_required
def backup_import(request):
    """
    Importiert eine Backup-Datei in die Datenbank.
    Nur für Superuser zugänglich.
    """
    import json
    import tempfile
    import os

    if not request.user.is_superuser:
        messages.error(request, 'Keine Berechtigung für diese Aktion.')
        return redirect('core:settings')

    if request.method != 'POST':
        return redirect('core:settings')

    # Prüfe Bestätigung
    if not request.POST.get('confirm_import'):
        messages.error(request, 'Bitte bestätigen Sie, dass Sie den Import durchführen möchten.')
        return redirect('core:settings')

    # Prüfe Datei
    backup_file = request.FILES.get('backup_file')
    if not backup_file:
        messages.error(request, 'Keine Backup-Datei ausgewählt.')
        return redirect('core:settings')

    if not backup_file.name.endswith('.json'):
        messages.error(request, 'Nur JSON-Dateien werden akzeptiert.')
        return redirect('core:settings')

    try:
        # Datei in temporäre Datei schreiben
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.json', delete=False) as tmp_file:
            for chunk in backup_file.chunks():
                tmp_file.write(chunk)
            tmp_path = tmp_file.name

        try:
            # Validieren dass es gültiges JSON ist
            with open(tmp_path, 'r', encoding='utf-8') as f:
                json.load(f)

            # Django loaddata aufrufen
            from django.core.management import call_command
            from io import StringIO

            output = StringIO()
            call_command('loaddata', tmp_path, stdout=output, verbosity=1)

            result = output.getvalue()

            messages.success(
                request,
                f'Backup erfolgreich importiert! Die Daten wurden wiederhergestellt.'
            )

        finally:
            # Temporäre Datei löschen
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    except json.JSONDecodeError as e:
        messages.error(request, f'Ungültige JSON-Datei: {str(e)}')
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Backup import failed: {e}")
        messages.error(request, f'Fehler beim Importieren des Backups: {str(e)}')

    return redirect('core:settings')
