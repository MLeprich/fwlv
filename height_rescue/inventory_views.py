"""
Höhenrettung Inventory Views

Views für die Inventur-Funktionalität im Höhenrettung-Modul
"""

from django.views.generic import ListView, DetailView, CreateView, UpdateView, View
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from django.db.models import Q
from django.template.loader import render_to_string
import csv
from io import BytesIO
from datetime import timedelta

from .models import (
    HeightRescueInventoryCheck,
    HeightRescueInventoryCheckItem,
    HeightRescueDeviceInstance
)
from personnel.models import Person


class HeightRescueInventoryListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """Liste aller Höhenrettung-Inventuren"""
    model = HeightRescueInventoryCheck
    template_name = 'height_rescue/inventory/check_list.html'
    context_object_name = 'checks'
    permission_required = 'height_rescue.view_heightrescueinventorycheck'
    paginate_by = 20

    def get_queryset(self):
        queryset = HeightRescueInventoryCheck.objects.select_related(
            'responsible_person',
            'location',
            'created_by'
        ).prefetch_related('team_members')

        # Filter by status
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)

        # Filter by type
        check_type = self.request.GET.get('type')
        if check_type:
            queryset = queryset.filter(check_type=check_type)

        # Search
        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(
                Q(check_number__icontains=search_query) |
                Q(title__icontains=search_query) |
                Q(description__icontains=search_query)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Basis-Kontext für Template
        context.update({
            'module_name': 'Höhenrettung',
            'module_icon': '⛰️',
            'module_color_from': 'from-amber-600',
            'module_color_to': 'to-amber-800',
            'module_dashboard_url': 'height_rescue:dashboard',
            'inventory_list_url': 'height_rescue:inventory_list',
            'inventory_create_url': 'height_rescue:inventory_create',
            'inventory_detail_url': 'height_rescue:inventory_detail',
            'inventory_start_url': 'height_rescue:inventory_start',
            'inventory_count_url': 'height_rescue:inventory_count',
            'inventory_complete_url': 'height_rescue:inventory_complete',
            'current_module': 'height_rescue',

            # Stats
            'stats': {
                'in_progress': HeightRescueInventoryCheck.objects.filter(status='in_progress').count(),
                'planned': HeightRescueInventoryCheck.objects.filter(status='planned').count(),
                'completed_this_year': HeightRescueInventoryCheck.objects.filter(
                    status='completed',
                    actual_end_date__year=timezone.now().year
                ).count(),
            }
        })

        return context


class HeightRescueInventoryCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """Neue Höhenrettung-Inventur erstellen"""
    model = HeightRescueInventoryCheck
    template_name = 'height_rescue/inventory/check_form.html'
    permission_required = 'height_rescue.add_heightrescueinventorycheck'
    fields = [
        'title',
        'description',
        'check_type',
        'responsible_person',
        'team_members',
        'scheduled_start_date',
        'scheduled_end_date',
        'location',
        'check_inspections',
        'check_age_limits',
        'check_rope_condition',
        'check_retirement',
        'notes'
    ]

    def get_success_url(self):
        return reverse('height_rescue:inventory_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        messages.success(
            self.request,
            f'Inventur "{form.instance.title}" wurde erfolgreich erstellt.'
        )
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_module'] = 'it_hardware'
        context['module_name'] = 'Höhenrettung'
        context['action'] = 'create'
        return context


class HeightRescueInventoryDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """Detail-Ansicht einer Höhenrettung-Inventur"""
    model = HeightRescueInventoryCheck
    template_name = 'height_rescue/inventory/check_detail.html'
    context_object_name = 'check'
    permission_required = 'height_rescue.view_heightrescueinventorycheck'

    def get_queryset(self):
        return HeightRescueInventoryCheck.objects.select_related(
            'responsible_person',
            'location',
            'approved_by',
            'created_by',
            'updated_by'
        ).prefetch_related('team_members', 'items')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        check = self.object

        # Gruppiere Items nach Status
        context['pending_items'] = check.items.filter(is_counted=False).count()
        context['counted_items'] = check.items.filter(is_counted=True).count()
        context['items_with_discrepancies'] = check.items.filter(has_discrepancy=True).count()

        # Höhenrettung-spezifisch
        if check.check_inspections:
            context['inspection_overdue_total'] = check.items.filter(
                inspection_overdue=True
            ).count()

        if check.check_age_limits:
            context['age_limit_exceeded_total'] = check.items.filter(
                age_limit_exceeded=True
            ).count()

        if check.check_rope_condition:
            context['rope_damage_total'] = check.items.filter(
                rope_damage_found=True
            ).count()

        if check.check_retirement:
            context['retirement_required_total'] = check.items.filter(
                retirement_required=True
            ).count()

        context['current_module'] = 'height_rescue'
        context['module_name'] = 'Höhenrettung'

        return context


class HeightRescueInventoryStartView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Startet eine geplante Inventur"""
    permission_required = 'height_rescue.change_heightrescueinventorycheck'

    def post(self, request, pk):
        check = get_object_or_404(HeightRescueInventoryCheck, pk=pk)

        if not check.can_start():
            messages.error(request, 'Diese Inventur kann nicht gestartet werden.')
            return redirect('height_rescue:inventory_detail', pk=pk)

        # Starte Inventur
        if check.start_counting(request.user):
            # Generiere Inventur-Items aus aktuellem Höhenrettungs-Bestand
            items_created = 0

            # Erstelle Items aus HeightRescueDeviceInstance (PSA-Geräte)
            from dateutil.relativedelta import relativedelta

            devices = HeightRescueDeviceInstance.objects.filter(
                is_active=True
            ).select_related('master', 'location')

            if check.location:
                devices = devices.filter(location=check.location)

            for device in devices:
                try:
                    # Prüfe Prüffristen (DGUV Vorschrift 3)
                    inspection_overdue = False
                    if device.next_inspection_date:
                        inspection_overdue = device.next_inspection_date < timezone.now().date()

                    # Berechne Alter
                    age_in_years = None
                    age_limit_exceeded = False
                    if device.first_use_date:
                        age_in_years = relativedelta(timezone.now().date(), device.first_use_date).years
                        # PSA hat typischerweise Altersgrenzen (z.B. 10 Jahre für Seile)
                        if hasattr(device.master, 'max_age_years') and device.master.max_age_years:
                            age_limit_exceeded = age_in_years >= device.master.max_age_years

                    # Seilspezifische Prüfung
                    rope_damage_found = False
                    rope_length = None
                    rope_diameter = None
                    if hasattr(device.master, 'item_type') and device.master.item_type == 'rope':
                        rope_length = getattr(device.master, 'rope_length', None)
                        rope_diameter = getattr(device.master, 'rope_diameter', None)
                        # Schäden werden in Prüfprotokollen dokumentiert
                        rope_damage_found = not device.is_operational or device.inspection_status in ['failed', 'defect']

                    # Aussonderung prüfen
                    retirement_required = False
                    retirement_reason = device.retirement_reason or ''
                    if device.retirement_date:
                        retirement_required = True

                    HeightRescueInventoryCheckItem.objects.create(
                        inventory_check=check,
                        height_rescue_device=device,
                        location=device.location,
                        item_name=device.master.name if device.master else 'PSA-Gerät',
                        item_number=device.master.master_number if device.master else '',
                        expected_quantity=1,
                        actual_quantity=None,
                        inventory_number=device.inventory_number or '',
                        serial_number=device.serial_number or '',
                        item_type=device.master.item_type if hasattr(device.master, 'item_type') else '',
                        last_inspection_date=device.last_inspection_date,
                        next_inspection_date=device.next_inspection_date,
                        inspection_overdue=inspection_overdue,
                        inspection_status=device.inspection_status,
                        manufacturing_date=device.manufacturing_date,
                        first_use_date=device.first_use_date,
                        age_in_years=age_in_years,
                        age_limit_exceeded=age_limit_exceeded,
                        rope_length=rope_length,
                        rope_diameter=rope_diameter,
                        rope_damage_found=rope_damage_found,
                        retirement_date=device.retirement_date,
                        retirement_required=retirement_required,
                        retirement_reason=retirement_reason,
                        is_operational=device.is_operational,
                        notes=f'Inv: {device.inventory_number or "N/A"} | S/N: {device.serial_number or "N/A"} | Prüfung: {device.next_inspection_date or "N/A"}'
                    )
                    items_created += 1
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f'Fehler beim Erstellen von Inventur-Item für HR-Device {device.pk}: {str(e)}')
                    continue

            # Update progress
            check.update_progress()

            if items_created == 0:
                messages.warning(
                    request,
                    f'Inventur "{check.title}" wurde gestartet, aber es wurden keine Artikel gefunden. '
                    f'Bitte legen Sie zuerst Höhenrettung-Artikel an.'
                )
            else:
                messages.success(
                    request,
                    f'Inventur "{check.title}" wurde gestartet. '
                    f'{items_created} Artikel wurden automatisch angelegt.'
                )
        else:
            messages.error(request, 'Fehler beim Starten der Inventur.')

        return redirect('height_rescue:inventory_detail', pk=pk)


class HeightRescueInventoryCountingView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """Zähl-Interface für Inventur"""
    model = HeightRescueInventoryCheck
    template_name = 'height_rescue/inventory/counting_interface.html'
    context_object_name = 'check'
    permission_required = 'height_rescue.view_heightrescueinventorycheck'

    def get_queryset(self):
        return HeightRescueInventoryCheck.objects.select_related(
            'responsible_person',
            'location'
        ).prefetch_related(
            'items__location',
            'items__height_rescue_device'
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        check = self.object

        # Filter für Items
        show_filter = self.request.GET.get('filter', 'all')
        items = check.items.all()

        if show_filter == 'uncounted':
            items = items.filter(is_counted=False)
        elif show_filter == 'discrepancies':
            items = items.filter(has_discrepancy=True)
        elif show_filter == 'inspection_overdue':
            items = items.filter(inspection_overdue=True)
        elif show_filter == 'age_limit_exceeded':
            items = items.filter(age_limit_exceeded=True)
        elif show_filter == 'rope_damage':
            items = items.filter(rope_damage_found=True)
        elif show_filter == 'retirement_required':
            items = items.filter(retirement_required=True)

        # Gruppiere nach Lagerort für bessere UX
        items = items.select_related('location', 'height_rescue_device').order_by('location', 'item_name')

        context['items'] = items
        context['current_filter'] = show_filter
        context['current_module'] = 'height_rescue'
        context['module_name'] = 'Höhenrettung'

        return context


class HeightRescueInventoryCompleteView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Schließt eine Inventur ab"""
    permission_required = 'height_rescue.change_heightrescueinventorycheck'

    def post(self, request, pk):
        check = get_object_or_404(HeightRescueInventoryCheck, pk=pk)

        # Prüfe ob alle Items gezählt wurden
        if check.counted_items < check.total_items:
            messages.error(
                request,
                f'Nicht alle Artikel wurden gezählt. '
                f'({check.counted_items}/{check.total_items})'
            )
            return redirect('height_rescue:inventory_count', pk=pk)

        # Schließe Zählung ab
        if check.complete_counting(request.user):
            messages.success(
                request,
                f'Inventur "{check.title}" wurde abgeschlossen. '
                f'Bitte prüfen und genehmigen.'
            )
        else:
            messages.error(request, 'Fehler beim Abschließen der Inventur.')

        return redirect('height_rescue:inventory_detail', pk=pk)


class HeightRescueInventoryApproveView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Genehmigt und finalisiert eine Inventur"""
    permission_required = 'height_rescue.approve_heightrescueinventorycheck'

    def post(self, request, pk):
        check = get_object_or_404(HeightRescueInventoryCheck, pk=pk)

        if not check.can_complete():
            messages.error(request, 'Diese Inventur kann noch nicht genehmigt werden.')
            return redirect('height_rescue:inventory_detail', pk=pk)

        # Genehmige und schließe ab
        if check.approve_and_complete(request.user):
            # Erstelle Korrekturbuchungen für Abweichungen
            adjustments_made = 0
            from decimal import Decimal

            # Hole alle Items mit Abweichungen
            items_with_discrepancies = check.items.filter(has_discrepancy=True)

            for item in items_with_discrepancies:
                discrepancy = item.get_discrepancy()

                # Update HeightRescueDeviceInstance Bestand
                if item.equipment_item:
                    try:
                        equipment_item = item.equipment_item

                        # Aktualisiere Bestand basierend auf gezählter Menge
                        old_quantity = equipment_item.quantity
                        equipment_item.quantity = item.actual_quantity if item.actual_quantity is not None else item.expected_quantity
                        equipment_item.save()

                        # Logge die Korrektur in den Notizen
                        item.notes += f'\n[Inventur-Korrektur] Bestand angepasst: {old_quantity} → {item.actual_quantity}'
                        item.save()

                        adjustments_made += 1

                    except Exception as e:
                        # Logge Fehler
                        import logging
                        logger = logging.getLogger(__name__)
                        logger.error(f'Fehler bei Bestandskorrektur für Item {item.pk}: {str(e)}')
                        item.notes += f'\n[Warnung] Automatische Korrektur fehlgeschlagen - manuelle Prüfung erforderlich'
                        item.save()

            # Aktualisiere Inventur-Check
            check.notes += f'\n[Genehmigung] {adjustments_made} Korrekturen automatisch durchgeführt'
            if check.defective_items_found > 0:
                check.notes += f'\n[Warnung] {check.defective_items_found} defekte Geräte gefunden'
            if check.expired_certifications_found > 0:
                check.notes += f'\n[Warnung] {check.expired_certifications_found} abgelaufene Zertifizierungen gefunden'
            if check.maintenance_due_found > 0:
                check.notes += f'\n[Info] {check.maintenance_due_found} fällige Wartungen gefunden'
            check.save()

            messages.success(
                request,
                f'Inventur "{check.title}" wurde genehmigt und abgeschlossen. '
                f'{adjustments_made} Bestandskorrekturen wurden durchgeführt.'
            )
        else:
            messages.error(request, 'Fehler beim Genehmigen der Inventur.')

        return redirect('height_rescue:inventory_detail', pk=pk)


class HeightRescueInventoryItemUpdateView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """HTMX Endpoint: Aktualisiert einzelnes Inventur-Item"""
    permission_required = 'height_rescue.change_heightrescueinventorycheck'

    def post(self, request, pk):
        item = get_object_or_404(HeightRescueInventoryCheckItem, pk=pk)

        # Prüfe ob Inventur noch in Bearbeitung
        if item.inventory_check.status != 'in_progress':
            return render(request, 'it_hardware/inventory/partials/item_row.html', {
                'item': item,
                'error': 'Inventur ist nicht mehr in Bearbeitung'
            })

        # Hole gezählte Menge
        try:
            actual_quantity = request.POST.get('actual_quantity', '')
            if actual_quantity:
                item.actual_quantity = float(actual_quantity)
                item.is_counted = True
                item.counted_date = timezone.now()

                # Get person from user if exists
                if hasattr(request.user, 'person'):
                    item.counted_by = request.user.person

                # Berechne Abweichung
                item.has_discrepancy = (item.actual_quantity != item.expected_quantity)
                item.variance_quantity = item.actual_quantity - item.expected_quantity

                item.save()

                # Update Check-Progress
                item.inventory_check.update_progress()
            else:
                item.is_counted = False
                item.save()

        except (ValueError, TypeError):
            return render(request, 'it_hardware/inventory/partials/item_row.html', {
                'item': item,
                'error': 'Ungültige Mengeneingabe'
            })

        # Returniere aktualisierte Zeile
        return render(request, 'it_hardware/inventory/partials/item_row.html', {
            'item': item
        })


class HeightRescueInventoryProgressView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """HTMX Endpoint: Liefert aktualisierte Progress-Anzeige"""
    permission_required = 'height_rescue.view_heightrescueinventorycheck'

    def get(self, request, pk):
        check = get_object_or_404(HeightRescueInventoryCheck, pk=pk)

        return render(request, 'it_hardware/inventory/partials/progress_display.html', {
            'check': check
        })


class HeightRescueInventoryExportView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Export Inventur als Excel oder PDF"""
    permission_required = 'height_rescue.view_heightrescueinventorycheck'

    def get(self, request, pk):
        check = get_object_or_404(HeightRescueInventoryCheck, pk=pk)
        export_format = request.GET.get('format', 'excel')

        if export_format == 'excel':
            return self.export_excel(check)
        elif export_format == 'pdf':
            return self.export_pdf(check)
        else:
            messages.error(request, 'Ungültiges Export-Format')
            return redirect('height_rescue:inventory_detail', pk=pk)

    def export_excel(self, check):
        """Exportiert Inventur als Excel-CSV"""
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="inventur_{check.check_number}.csv"'

        # UTF-8 BOM für korrekte Umlaute in Excel
        response.write('\ufeff')

        writer = csv.writer(response, delimiter=';')

        # Header
        writer.writerow(['Inventur-Bericht'])
        writer.writerow([])
        writer.writerow(['Inventur-Nr.:', check.check_number])
        writer.writerow(['Titel:', check.title])
        writer.writerow(['Typ:', check.get_check_type_display()])
        writer.writerow(['Status:', check.get_status_display()])
        writer.writerow(['Geplanter Zeitraum:', f'{check.scheduled_start_date.strftime("%d.%m.%Y")} - {check.scheduled_end_date.strftime("%d.%m.%Y")}'])
        if check.actual_start_date:
            writer.writerow(['Tatsächlicher Start:', check.actual_start_date.strftime('%d.%m.%Y %H:%M')])
        if check.actual_end_date:
            writer.writerow(['Tatsächliches Ende:', check.actual_end_date.strftime('%d.%m.%Y %H:%M')])
        writer.writerow(['Verantwortlich:', check.responsible_person.get_full_name()])
        writer.writerow(['Lagerort:', check.location.name if check.location else 'Alle'])
        writer.writerow([])
        writer.writerow(['Fortschritt:', f'{check.counted_items}/{check.total_items} Artikel ({check.get_progress_percentage()}%)'])
        writer.writerow(['Abweichungen:', check.items_with_discrepancies])
        writer.writerow([])
        writer.writerow([])

        # Artikel-Details Header
        writer.writerow([
            'Inventar-Nr.',
            'Artikelname',
            'S/N',
            'Gerätetyp',
            'Lagerort',
            'Gezählt',
            'Prüfung überfällig',
            'Nächste Prüfung',
            'Alter (Jahre)',
            'Altersgrenze überschr.',
            'Seilschaden',
            'Seillänge (m)',
            'Seildurchm. (mm)',
            'Aussonderung erf.',
            'Einsatzstatus',
            'Notizen'
        ])

        # Artikel-Daten
        items = check.items.all().order_by('location__name', 'item_name')
        for item in items:
            writer.writerow([
                item.inventory_number or '',
                item.item_name,
                item.serial_number or '',
                item.item_type or '',
                item.location.name if item.location else '',
                'Ja' if item.is_counted else 'Nein',
                'Ja' if item.inspection_overdue else 'Nein',
                item.next_inspection_date.strftime('%d.%m.%Y') if item.next_inspection_date else '',
                str(item.age_in_years) if item.age_in_years else '',
                'Ja' if item.age_limit_exceeded else 'Nein',
                'Ja' if item.rope_damage_found else 'Nein',
                str(item.rope_length).replace('.', ',') if item.rope_length else '',
                str(item.rope_diameter).replace('.', ',') if item.rope_diameter else '',
                'Ja' if item.retirement_required else 'Nein',
                'Ja' if item.is_operational else 'Nein',
                item.notes.replace('\n', ' ') if item.notes else ''
            ])

        # Zusammenfassung
        writer.writerow([])
        writer.writerow([])
        writer.writerow(['Zusammenfassung'])
        writer.writerow(['Gesamt PSA-Geräte:', check.total_items])
        writer.writerow(['Gezählte Geräte:', check.counted_items])
        writer.writerow(['Ausstehende Geräte:', check.total_items - check.counted_items])
        writer.writerow(['Geräte mit Abweichungen:', check.items_with_discrepancies])

        writer.writerow([])
        writer.writerow(['Höhenrettung-spezifische Prüfungen:'])

        if check.check_inspections:
            writer.writerow(['Prüfungen überfällig:', check.inspection_overdue_found])

        if check.check_age_limits:
            writer.writerow(['Altersgrenze überschritten:', check.age_limit_exceeded_found])

        if check.check_rope_condition:
            writer.writerow(['Seilschäden gefunden:', check.rope_damage_found])

        if check.check_retirement:
            writer.writerow(['Aussonderung erforderlich:', check.retirement_required_found])

        writer.writerow([])
        writer.writerow(['Exportiert am:', timezone.now().strftime('%d.%m.%Y %H:%M')])

        return response

    def export_pdf(self, check):
        """Exportiert Inventur als PDF"""
        try:
            from weasyprint import HTML, CSS
            from django.template.loader import render_to_string

            # Render HTML template
            html_string = render_to_string('equipment/inventory/export_pdf.html', {
                'check': check,
                'items': check.items.all().order_by('location__name', 'item_name'),
                'export_date': timezone.now()
            })

            # Generate PDF
            html = HTML(string=html_string)
            pdf_file = html.write_pdf()

            # Create response
            response = HttpResponse(pdf_file, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="inventur_{check.check_number}.pdf"'

            return response

        except ImportError:
            # Fallback wenn WeasyPrint nicht installiert ist
            messages.error(
                self.request,
                'PDF-Export nicht verfügbar. Bitte verwenden Sie Excel-Export.'
            )
            return redirect('height_rescue:inventory_detail', pk=check.pk)
