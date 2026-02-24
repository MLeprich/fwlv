"""
Medical Inventory Views

Views für die Inventur-Funktionalität im Medical-Modul
"""

from django.views.generic import ListView, DetailView, CreateView, UpdateView, View
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from django.db.models import Q, Sum, F, DecimalField, Value
from django.db.models.functions import Coalesce
from django.template.loader import render_to_string
from decimal import Decimal
import csv
from io import BytesIO

from .models import (
    MedicalInventoryCheck,
    MedicalInventoryCheckItem,
    MedicalItemMaster,
    MedicalBatch,
    MedicalDeviceInstance
)
from personnel.models import Person


class MedicalInventoryListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """Liste aller Medical-Inventuren"""
    model = MedicalInventoryCheck
    template_name = 'medical/inventory/check_list.html'
    context_object_name = 'checks'
    permission_required = 'medical.view_medicalinventorycheck'
    paginate_by = 20

    def get_queryset(self):
        queryset = MedicalInventoryCheck.objects.select_related(
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
            'module_name': 'Rettungsdienst',
            'module_icon': '💊',
            'module_color_from': 'from-red-600',
            'module_color_to': 'to-red-800',
            'module_dashboard_url': 'medical:dashboard',
            'inventory_list_url': 'medical:inventory_list',
            'inventory_create_url': 'medical:inventory_create',
            'inventory_detail_url': 'medical:inventory_detail',
            'inventory_start_url': 'medical:inventory_start',
            'inventory_count_url': 'medical:inventory_count',
            'inventory_complete_url': 'medical:inventory_complete',
            'current_module': 'medical',

            # Stats
            'stats': {
                'in_progress': MedicalInventoryCheck.objects.filter(status='in_progress').count(),
                'planned': MedicalInventoryCheck.objects.filter(status='planned').count(),
                'completed_this_year': MedicalInventoryCheck.objects.filter(
                    status='completed',
                    actual_end_date__year=timezone.now().year
                ).count(),
            }
        })

        # === Finanz-Kennzahlen (Buchwert) ===

        # Buchwert Verbrauchsmaterial: Summe(Restmenge * Einkaufspreis) aller aktiven Chargen
        batch_value = MedicalBatch.objects.filter(
            quantity_remaining__gt=0,
            unit_price__isnull=False,
            is_recalled=False,
        ).aggregate(
            total=Coalesce(
                Sum(F('quantity_remaining') * F('unit_price'), output_field=DecimalField()),
                Value(Decimal('0.00'))
            )
        )['total']

        # Buchwert Medizintechnik: Summe(Anschaffungspreis) aller aktiven Geraete
        device_value = MedicalDeviceInstance.objects.filter(
            is_active=True,
            purchase_price__isnull=False,
        ).aggregate(
            total=Coalesce(
                Sum('purchase_price'),
                Value(Decimal('0.00'))
            )
        )['total']

        total_value = batch_value + device_value

        # Anzahl Artikel-Stammdaten und Chargen
        active_masters = MedicalItemMaster.objects.filter(is_active=True).count()
        active_batches = MedicalBatch.objects.filter(
            quantity_remaining__gt=0, is_recalled=False
        ).count()
        active_devices = MedicalDeviceInstance.objects.filter(is_active=True).count()

        # Chargen ohne Preis (zur Info)
        batches_without_price = MedicalBatch.objects.filter(
            quantity_remaining__gt=0,
            unit_price__isnull=True,
            is_recalled=False,
        ).count()

        context['financials'] = {
            'batch_value': batch_value,
            'device_value': device_value,
            'total_value': total_value,
            'active_masters': active_masters,
            'active_batches': active_batches,
            'active_devices': active_devices,
            'batches_without_price': batches_without_price,
        }

        return context


class MedicalInventoryCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """Neue Medical-Inventur erstellen"""
    model = MedicalInventoryCheck
    template_name = 'medical/inventory/check_form.html'
    permission_required = 'medical.add_medicalinventorycheck'
    fields = [
        'title',
        'description',
        'check_type',
        'responsible_person',
        'team_members',
        'scheduled_start_date',
        'scheduled_end_date',
        'location',
        'include_btm',
        'check_expiry_dates',
        'notes'
    ]

    def get_success_url(self):
        return reverse('medical:inventory_detail', kwargs={'pk': self.object.pk})

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
        context['current_module'] = 'medical'
        context['module_name'] = 'Rettungsdienst'
        context['action'] = 'create'
        return context


class MedicalInventoryDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """Detail-Ansicht einer Medical-Inventur"""
    model = MedicalInventoryCheck
    template_name = 'medical/inventory/check_detail.html'
    context_object_name = 'check'
    permission_required = 'medical.view_medicalinventorycheck'

    def get_queryset(self):
        return MedicalInventoryCheck.objects.select_related(
            'responsible_person',
            'location',
            'approved_by',
            'btm_verified_by',
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

        # BTM-spezifisch
        if check.include_btm:
            context['btm_items_total'] = check.items.filter(is_btm=True).count()
            context['btm_items_verified'] = check.items.filter(is_btm=True, btm_verified=True).count()

        context['current_module'] = 'medical'
        context['module_name'] = 'Rettungsdienst'

        return context


class MedicalInventoryStartView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Startet eine geplante Inventur"""
    permission_required = 'medical.change_medicalinventorycheck'

    def post(self, request, pk):
        check = get_object_or_404(MedicalInventoryCheck, pk=pk)

        if not check.can_start():
            messages.error(request, 'Diese Inventur kann nicht gestartet werden.')
            return redirect('medical:inventory_detail', pk=pk)

        # Starte Inventur
        if check.start_counting(request.user):
            # Generiere Inventur-Items aus aktuellem Bestand
            items_created = 0

            # 1. Erstelle Items aus MedicalBatch (Verbrauchsmaterial)
            batches_query = MedicalBatch.objects.filter(
                quantity_remaining__gt=0
            ).select_related('master', 'location')

            # Filter nach Location falls angegeben
            if check.location:
                batches_query = batches_query.filter(location=check.location)

            # Filter nach BTM falls nicht inkludiert
            if not check.include_btm:
                batches_query = batches_query.exclude(master__is_btm=True)

            for batch in batches_query:
                # Sichere Null-Checks
                if not batch.master:
                    continue  # Überspringe Batches ohne Master-Daten

                try:
                    MedicalInventoryCheckItem.objects.create(
                        inventory_check=check,
                        medical_item=batch.master,
                        batch_number=batch.batch_number or '',
                        expiry_date=batch.expiry_date,
                        location=batch.location,  # Kann NULL sein
                        item_name=batch.master.name or 'Unbenannt',
                        item_number=batch.master.master_number or '',
                        expected_quantity=batch.quantity_remaining,
                        counted_quantity=0,
                        is_btm=batch.master.is_btm,
                        notes=f'Charge: {batch.batch_number or "N/A"}'
                    )
                    items_created += 1
                except Exception as e:
                    # Logge Fehler aber fahre fort
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f'Fehler beim Erstellen von Inventur-Item für Batch {batch.pk}: {str(e)}')
                    continue

            # 2. Erstelle Items aus MedicalDeviceInstance (Medizintechnik)
            devices_query = MedicalDeviceInstance.objects.filter(
                is_operational=True,
                is_active=True
            ).select_related('master', 'location')

            # Filter nach Location falls angegeben
            if check.location:
                devices_query = devices_query.filter(location=check.location)

            for device in devices_query:
                # Sichere Null-Checks
                if not device.master:
                    continue  # Überspringe Devices ohne Master-Daten

                try:
                    MedicalInventoryCheckItem.objects.create(
                        inventory_check=check,
                        medical_device=device,
                        location=device.location,  # Kann NULL sein
                        item_name=f'{device.master.name or "Unbenannt"} - {device.inventory_number or "N/A"}',
                        item_number=device.inventory_number or '',
                        expected_quantity=1,
                        counted_quantity=0,
                        is_btm=False,
                        notes=f'Seriennummer: {device.serial_number}' if device.serial_number else 'Keine Seriennummer'
                    )
                    items_created += 1
                except Exception as e:
                    # Logge Fehler aber fahre fort
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f'Fehler beim Erstellen von Inventur-Item für Device {device.pk}: {str(e)}')
                    continue

            # Update progress
            check.update_progress()

            if items_created == 0:
                messages.warning(
                    request,
                    f'Inventur "{check.title}" wurde gestartet, aber es wurden keine Artikel gefunden. '
                    f'Bitte legen Sie zuerst Medikamente (Batches) oder Geräte (Devices) an.'
                )
            else:
                messages.success(
                    request,
                    f'Inventur "{check.title}" wurde gestartet. '
                    f'{items_created} Artikel wurden automatisch angelegt.'
                )
        else:
            messages.error(request, 'Fehler beim Starten der Inventur.')

        return redirect('medical:inventory_detail', pk=pk)


class MedicalInventoryCountingView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """Zähl-Interface für Inventur"""
    model = MedicalInventoryCheck
    template_name = 'medical/inventory/counting_interface.html'
    context_object_name = 'check'
    permission_required = 'medical.view_medicalinventorycheck'

    def get_queryset(self):
        return MedicalInventoryCheck.objects.select_related(
            'responsible_person',
            'location'
        ).prefetch_related(
            'items__location',
            'items__medical_item',
            'items__medical_device'
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
        elif show_filter == 'btm':
            items = items.filter(is_btm=True)

        # Gruppiere nach Lagerort für bessere UX
        items = items.select_related('location', 'medical_item', 'medical_device').order_by('location', 'item_name')

        context['items'] = items
        context['current_filter'] = show_filter
        context['current_module'] = 'medical'
        context['module_name'] = 'Rettungsdienst'

        return context


class MedicalInventoryCompleteView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Schließt eine Inventur ab"""
    permission_required = 'medical.change_medicalinventorycheck'

    def post(self, request, pk):
        check = get_object_or_404(MedicalInventoryCheck, pk=pk)

        # Prüfe ob alle Items gezählt wurden
        if check.counted_items < check.total_items:
            messages.error(
                request,
                f'Nicht alle Artikel wurden gezählt. '
                f'({check.counted_items}/{check.total_items})'
            )
            return redirect('medical:inventory_count', pk=pk)

        # Schließe Zählung ab
        if check.complete_counting(request.user):
            messages.success(
                request,
                f'Inventur "{check.title}" wurde abgeschlossen. '
                f'Bitte prüfen und genehmigen.'
            )
        else:
            messages.error(request, 'Fehler beim Abschließen der Inventur.')

        return redirect('medical:inventory_detail', pk=pk)


class MedicalInventoryApproveView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Genehmigt und finalisiert eine Inventur"""
    permission_required = 'medical.approve_medicalinventorycheck'

    def post(self, request, pk):
        check = get_object_or_404(MedicalInventoryCheck, pk=pk)

        if not check.can_complete():
            messages.error(request, 'Diese Inventur kann noch nicht genehmigt werden.')
            return redirect('medical:inventory_detail', pk=pk)

        # Genehmige und schließe ab
        if check.approve_and_complete(request.user):
            # Erstelle Korrekturbuchungen für Abweichungen
            adjustments_made = 0
            from decimal import Decimal

            # Hole alle Items mit Abweichungen
            items_with_discrepancies = check.items.filter(has_discrepancy=True)

            for item in items_with_discrepancies:
                discrepancy = item.get_discrepancy()

                # 1. Update MedicalBatch wenn es ein Batch-Item ist
                if item.batch_number and item.medical_item:
                    try:
                        batch = MedicalBatch.objects.get(
                            master=item.medical_item,
                            batch_number=item.batch_number,
                            location=item.location
                        )

                        # Aktualisiere Restmenge basierend auf gezählter Menge
                        old_quantity = batch.quantity_remaining
                        batch.quantity_remaining = item.counted_quantity
                        batch.save()

                        # Logge die Korrektur in den Notizen
                        item.notes += f'\n[Inventur-Korrektur] Bestand angepasst: {old_quantity} → {item.counted_quantity}'
                        item.save()

                        adjustments_made += 1

                    except MedicalBatch.DoesNotExist:
                        # Batch nicht gefunden - nur Notiz
                        item.notes += f'\n[Warnung] Charge nicht gefunden für Korrektur'
                        item.save()

                    except MedicalBatch.MultipleObjectsReturned:
                        # Mehrere Batches gefunden - nur Notiz
                        item.notes += f'\n[Warnung] Mehrere Chargen gefunden - manuelle Korrektur erforderlich'
                        item.save()

                # 2. Für Devices: Notiz hinzufügen (keine automatische Korrektur)
                if item.medical_device:
                    if item.counted_quantity == 0:
                        item.notes += f'\n[Inventur] Gerät nicht gefunden - Überprüfung erforderlich'
                        # Optional: Setze Gerät auf "nicht operational"
                        # item.medical_device.is_operational = False
                        # item.medical_device.save()
                    else:
                        item.notes += f'\n[Inventur] Gerät gefunden und verifiziert'
                    item.save()

            # Aktualisiere Inventur-Check
            if check.include_btm and items_with_discrepancies.filter(is_btm=True).exists():
                # BTM-Abweichungen erfordern zusätzliche Dokumentation
                check.notes += f'\n[Genehmigung] {adjustments_made} Korrekturen durchgeführt. BTM-Abweichungen dokumentiert am {timezone.now().strftime("%d.%m.%Y %H:%M")}'
            else:
                check.notes += f'\n[Genehmigung] {adjustments_made} Korrekturen automatisch durchgeführt'
            check.save()

            messages.success(
                request,
                f'Inventur "{check.title}" wurde genehmigt und abgeschlossen. '
                f'{adjustments_made} Bestandskorrekturen wurden durchgeführt.'
            )
        else:
            messages.error(request, 'Fehler beim Genehmigen der Inventur.')

        return redirect('medical:inventory_detail', pk=pk)


class MedicalInventoryItemUpdateView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """HTMX Endpoint: Aktualisiert einzelnes Inventur-Item"""
    permission_required = 'medical.change_medicalinventorycheck'

    def post(self, request, pk):
        item = get_object_or_404(MedicalInventoryCheckItem, pk=pk)

        # Prüfe ob Inventur noch in Bearbeitung
        if item.inventory_check.status != 'in_progress':
            return render(request, 'medical/inventory/partials/item_row.html', {
                'item': item,
                'error': 'Inventur ist nicht mehr in Bearbeitung'
            })

        # Hole gezählte Menge
        try:
            counted_quantity = request.POST.get('counted_quantity', '')
            if counted_quantity:
                item.counted_quantity = float(counted_quantity)
                item.is_counted = True
                item.counted_at = timezone.now()
                item.counted_by = request.user

                # Berechne Abweichung
                item.calculate_discrepancy()

                item.save()

                # Update Check-Progress
                item.inventory_check.update_progress()
            else:
                item.is_counted = False
                item.save()

        except (ValueError, TypeError):
            return render(request, 'medical/inventory/partials/item_row.html', {
                'item': item,
                'error': 'Ungültige Mengeneingabe'
            })

        # Returniere aktualisierte Zeile
        return render(request, 'medical/inventory/partials/item_row.html', {
            'item': item
        })


class MedicalInventoryProgressView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """HTMX Endpoint: Liefert aktualisierte Progress-Anzeige"""
    permission_required = 'medical.view_medicalinventorycheck'

    def get(self, request, pk):
        check = get_object_or_404(MedicalInventoryCheck, pk=pk)

        return render(request, 'medical/inventory/partials/progress_display.html', {
            'check': check
        })


class MedicalInventoryExportView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Export Inventur als Excel oder PDF"""
    permission_required = 'medical.view_medicalinventorycheck'

    def get(self, request, pk):
        check = get_object_or_404(MedicalInventoryCheck, pk=pk)
        export_format = request.GET.get('format', 'excel')

        if export_format == 'excel':
            return self.export_excel(check)
        elif export_format == 'pdf':
            return self.export_pdf(check)
        else:
            messages.error(request, 'Ungültiges Export-Format')
            return redirect('medical:inventory_detail', pk=pk)

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
            'Artikel-Nr.',
            'Artikelname',
            'Lagerort',
            'Charge',
            'MHD',
            'Erwartet',
            'Gezählt',
            'Abweichung',
            'Status',
            'BTM',
            'Notizen'
        ])

        # Artikel-Daten
        items = check.items.all().order_by('location__name', 'item_name')
        for item in items:
            writer.writerow([
                item.item_number,
                item.item_name,
                item.location.name if item.location else '',
                item.batch_number or '',
                item.expiry_date.strftime('%d.%m.%Y') if item.expiry_date else '',
                str(item.expected_quantity).replace('.', ','),
                str(item.counted_quantity).replace('.', ',') if item.is_counted else '',
                str(item.get_discrepancy()).replace('.', ',') if item.is_counted else '',
                'Gezählt' if item.is_counted else 'Ausstehend',
                'Ja' if item.is_btm else 'Nein',
                item.notes.replace('\n', ' ') if item.notes else ''
            ])

        # Zusammenfassung
        writer.writerow([])
        writer.writerow([])
        writer.writerow(['Zusammenfassung'])
        writer.writerow(['Gesamt Artikel:', check.total_items])
        writer.writerow(['Gezählte Artikel:', check.counted_items])
        writer.writerow(['Ausstehende Artikel:', check.total_items - check.counted_items])
        writer.writerow(['Artikel mit Abweichungen:', check.items_with_discrepancies])

        if check.include_btm:
            btm_items = check.items.filter(is_btm=True)
            writer.writerow([])
            writer.writerow(['BTM-Artikel:', btm_items.count()])
            writer.writerow(['BTM Gezählt:', btm_items.filter(is_counted=True).count()])

        writer.writerow([])
        writer.writerow(['Exportiert am:', timezone.now().strftime('%d.%m.%Y %H:%M')])

        return response

    def export_pdf(self, check):
        """Exportiert Inventur als PDF"""
        try:
            from weasyprint import HTML, CSS
            from django.template.loader import render_to_string

            # Render HTML template
            html_string = render_to_string('medical/inventory/export_pdf.html', {
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
            return redirect('medical:inventory_detail', pk=check.pk)
