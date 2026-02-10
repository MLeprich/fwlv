"""
Disinfection Views
Views für Desinfektions-Management
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.db.models import Q, Count, Sum
from django.utils import timezone
from datetime import datetime, timedelta
from calendar import monthcalendar
import json

from .models import (
    DisinfectionItem,
    DisinfectionCategory,
    DisinfectionPlan,
    DisinfectionLog,
    DisinfectionStockMovement,
    DisinfectionItemType,
    DisinfectionStatus,
    DisinfectionPlanFrequency,
)
from vehicles.models import Vehicle


@login_required
def disinfection_dashboard(request):
    """
    Desinfektions-Dashboard
    Übersicht über Desinfektionsmittel, Pläne und anstehende Desinfektionen
    """
    # Statistiken
    total_items = DisinfectionItem.objects.filter(is_active=True).count()
    total_plans = DisinfectionPlan.objects.filter(is_active=True).count()

    # Überfällige Pläne
    overdue_plans = DisinfectionPlan.objects.filter(
        is_active=True,
        next_due_date__lt=timezone.now().date()
    ).select_related('vehicle')

    # Bald fällige Pläne (nächste 7 Tage)
    upcoming_plans = DisinfectionPlan.objects.filter(
        is_active=True,
        next_due_date__gte=timezone.now().date(),
        next_due_date__lte=timezone.now().date() + timedelta(days=7)
    ).select_related('vehicle').order_by('next_due_date')

    # Niedrige Bestände
    low_stock_items = DisinfectionItem.objects.filter(
        is_active=True,
        disinfection_status='low_stock'
    )

    # Letzte Desinfektionen
    recent_logs = DisinfectionLog.objects.select_related(
        'vehicle',
        'performed_by',
        'disinfection_item'
    ).order_by('-disinfection_date')[:10]

    context = {
        'total_items': total_items,
        'total_plans': total_plans,
        'overdue_count': overdue_plans.count(),
        'upcoming_count': upcoming_plans.count(),
        'low_stock_count': low_stock_items.count(),
        'overdue_plans': overdue_plans[:5],
        'upcoming_plans': upcoming_plans[:5],
        'low_stock_items': low_stock_items[:5],
        'recent_logs': recent_logs,
    }

    return render(request, 'disinfection/dashboard.html', context)


@login_required
def disinfection_calendar(request):
    """
    Kalenderansicht für Desinfektionspläne
    Zeigt wann welches Fahrzeug desinfiziert werden muss
    """
    # Monat und Jahr aus Request oder aktuell
    year = int(request.GET.get('year', timezone.now().year))
    month = int(request.GET.get('month', timezone.now().month))
    selected_day = request.GET.get('day')

    # Kalender generieren
    cal = monthcalendar(year, month)

    # Alle Pläne für diesen Monat
    month_start = datetime(year, month, 1).date()
    if month == 12:
        month_end = datetime(year + 1, 1, 1).date()
    else:
        month_end = datetime(year, month + 1, 1).date()

    plans_in_month = DisinfectionPlan.objects.filter(
        is_active=True,
        next_due_date__gte=month_start,
        next_due_date__lt=month_end
    ).select_related('vehicle')

    # Gruppiere Pläne nach Tag
    plans_by_day = {}
    for plan in plans_in_month:
        day = plan.next_due_date.day
        if day not in plans_by_day:
            plans_by_day[day] = []
        plans_by_day[day].append(plan)

    # Ausgewählter Tag - Standard ist heute (falls im aktuellen Monat)
    if selected_day:
        selected_day = int(selected_day)
    else:
        today = timezone.now().date()
        if today.year == year and today.month == month:
            selected_day = today.day
        else:
            # Oder den ersten Tag mit Plänen
            selected_day = min(plans_by_day.keys()) if plans_by_day else 1

    # Pläne für den ausgewählten Tag
    selected_date = datetime(year, month, selected_day).date()
    selected_plans = plans_by_day.get(selected_day, [])

    # Navigation
    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1

    context = {
        'calendar': cal,
        'year': year,
        'month': month,
        'month_name': datetime(year, month, 1).strftime('%B'),
        'plans_by_day': plans_by_day,
        'selected_day': selected_day,
        'selected_date': selected_date,
        'selected_plans': selected_plans,
        'prev_month': prev_month,
        'prev_year': prev_year,
        'next_month': next_month,
        'next_year': next_year,
    }

    # HTMX Request - nur die Tagesdetails zurückgeben
    if request.headers.get('HX-Request'):
        return render(request, 'disinfection/partials/calendar_day_detail.html', context)

    return render(request, 'disinfection/calendar.html', context)


@login_required
def item_list(request):
    """
    Liste aller Desinfektionsmittel
    Tabellen-Ansicht mit umfangreichen Filtermöglichkeiten
    """
    # Basis-Queryset
    items = DisinfectionItem.objects.select_related('category')

    # Filter nach Kategorie
    category_filter = request.GET.get('category')
    if category_filter:
        items = items.filter(category_id=category_filter)

    # Filter nach Suche
    search_query = request.GET.get('search')
    if search_query:
        items = items.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(manufacturer__icontains=search_query) |
            Q(item_number__icontains=search_query) |
            Q(active_ingredient__icontains=search_query)
        )

    # Filter nach Typ
    type_filter = request.GET.get('disinfection_type')
    if type_filter:
        items = items.filter(disinfection_type=type_filter)

    # Filter nach Status
    status_filter = request.GET.get('status')
    if status_filter:
        items = items.filter(disinfection_status=status_filter)

    # Filter nach Zulassungen
    if request.GET.get('vah_listed'):
        items = items.filter(vah_listed=True)
    if request.GET.get('dghm_listed'):
        items = items.filter(dghm_listed=True)
    if request.GET.get('rki_listed'):
        items = items.filter(rki_listed=True)

    # Filter nach Gefahrstoff
    is_hazardous_filter = request.GET.get('is_hazardous')
    if is_hazardous_filter == 'true':
        items = items.filter(is_hazardous=True)

    # Filter nach Aktiv/Inaktiv
    is_active_filter = request.GET.get('is_active')
    if is_active_filter == 'true':
        items = items.filter(is_active=True)
    elif is_active_filter == 'false':
        items = items.filter(is_active=False)
    else:
        # Standard: Nur aktive Items zeigen
        items = items.filter(is_active=True)

    # Sortierung
    sort = request.GET.get('sort')
    if sort:
        items = items.order_by(sort)
    else:
        items = items.order_by('name')

    # Alle Kategorien für Filter
    categories = DisinfectionCategory.objects.filter(is_active=True).order_by('name')

    context = {
        'items': items,
        'categories': categories,
        'disinfection_types': DisinfectionItemType.choices,
        'statuses': DisinfectionStatus.choices,
        'category_filter': category_filter,
        'type_filter': type_filter,
        'status_filter': status_filter,
        'is_hazardous_filter': is_hazardous_filter,
        'is_active_filter': is_active_filter,
        'search_query': search_query,
    }

    return render(request, 'disinfection/item_list.html', context)


@login_required
@permission_required('disinfection.add_disinfectionitem', raise_exception=True)
def item_create(request):
    """Neues Desinfektionsmittel erstellen"""
    from .forms import DisinfectionItemForm

    if request.method == 'POST':
        form = DisinfectionItemForm(request.POST, request.FILES)
        if form.is_valid():
            item = form.save(commit=False)
            item.created_by = request.user
            item.updated_by = request.user
            item.save()
            form.save_m2m()  # Für ManyToMany Felder (assigned_vehicles)

            messages.success(request, f'Desinfektionsmittel "{item.name}" wurde erfolgreich erstellt.')
            return redirect('disinfection:item_list')
    else:
        form = DisinfectionItemForm()

    context = {
        'form': form,
        'title': 'Neues Desinfektionsmittel',
    }

    return render(request, 'disinfection/item_form.html', context)


@login_required
@permission_required('disinfection.change_disinfectionitem', raise_exception=True)
def item_update(request, pk):
    """Desinfektionsmittel bearbeiten"""
    from .forms import DisinfectionItemForm

    item = get_object_or_404(DisinfectionItem, pk=pk)

    if request.method == 'POST':
        form = DisinfectionItemForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            item = form.save(commit=False)
            item.updated_by = request.user
            item.save()
            form.save_m2m()

            messages.success(request, f'Desinfektionsmittel "{item.name}" wurde erfolgreich aktualisiert.')
            return redirect('disinfection:item_list')
    else:
        form = DisinfectionItemForm(instance=item)

    context = {
        'form': form,
        'item': item,
        'title': 'Desinfektionsmittel bearbeiten',
    }

    return render(request, 'disinfection/item_form.html', context)


@login_required
@permission_required('disinfection.delete_disinfectionitem', raise_exception=True)
def item_delete(request, pk):
    """Desinfektionsmittel löschen (soft delete)"""
    item = get_object_or_404(DisinfectionItem, pk=pk)

    if request.method == 'POST':
        item.is_active = False
        item.updated_by = request.user
        item.save()

        messages.success(request, f'Desinfektionsmittel "{item.name}" wurde erfolgreich deaktiviert.')
        return redirect('disinfection:item_list')

    context = {
        'item': item,
    }

    return render(request, 'disinfection/item_confirm_delete.html', context)


@login_required
def plan_list(request):
    """Liste aller Desinfektionspläne"""
    plans = DisinfectionPlan.objects.filter(is_active=True).select_related(
        'vehicle',
        'responsible_person'
    ).order_by('next_due_date')

    # Filter nach Fahrzeug
    vehicle_id = request.GET.get('vehicle')
    if vehicle_id:
        plans = plans.filter(vehicle_id=vehicle_id)

    # Filter nach Status
    status = request.GET.get('status')
    if status == 'overdue':
        plans = plans.filter(next_due_date__lt=timezone.now().date())
    elif status == 'upcoming':
        plans = plans.filter(
            next_due_date__gte=timezone.now().date(),
            next_due_date__lte=timezone.now().date() + timedelta(days=7)
        )

    vehicles = Vehicle.objects.filter(is_active=True)

    context = {
        'plans': plans,
        'vehicles': vehicles,
        'vehicle_filter': vehicle_id,
        'status_filter': status,
    }

    return render(request, 'disinfection/plan_list.html', context)


@login_required
@permission_required('disinfection.add_disinfectionplan', raise_exception=True)
def plan_create(request):
    """Neuen Desinfektionsplan erstellen"""
    from .forms import DisinfectionPlanForm

    if request.method == 'POST':
        form = DisinfectionPlanForm(request.POST)
        if form.is_valid():
            plan = form.save(commit=False)
            plan.created_by = request.user
            plan.updated_by = request.user

            # Berechne next_due_date basierend auf start_date
            plan.next_due_date = plan.start_date

            plan.save()
            form.save_m2m()  # Für ManyToMany Felder

            messages.success(request, f'Desinfektionsplan "{plan.name}" wurde erfolgreich erstellt.')
            return redirect('disinfection:plan_list')
    else:
        form = DisinfectionPlanForm()

    context = {
        'form': form,
        'title': 'Neuer Desinfektionsplan',
    }

    return render(request, 'disinfection/plan_form.html', context)


@login_required
@permission_required('disinfection.change_disinfectionplan', raise_exception=True)
def plan_update(request, pk):
    """Desinfektionsplan bearbeiten"""
    from .forms import DisinfectionPlanForm

    plan = get_object_or_404(DisinfectionPlan, pk=pk)

    if request.method == 'POST':
        form = DisinfectionPlanForm(request.POST, instance=plan)
        if form.is_valid():
            plan = form.save(commit=False)
            plan.updated_by = request.user
            plan.save()
            form.save_m2m()

            messages.success(request, f'Desinfektionsplan "{plan.name}" wurde erfolgreich aktualisiert.')
            return redirect('disinfection:plan_list')
    else:
        form = DisinfectionPlanForm(instance=plan)

    context = {
        'form': form,
        'plan': plan,
        'title': 'Desinfektionsplan bearbeiten',
    }

    return render(request, 'disinfection/plan_form.html', context)


@login_required
@permission_required('disinfection.delete_disinfectionplan', raise_exception=True)
def plan_delete(request, pk):
    """Desinfektionsplan löschen (soft delete)"""
    plan = get_object_or_404(DisinfectionPlan, pk=pk)

    if request.method == 'POST':
        plan.is_active = False
        plan.updated_by = request.user
        plan.save()

        messages.success(request, f'Desinfektionsplan "{plan.name}" wurde erfolgreich deaktiviert.')
        return redirect('disinfection:plan_list')

    context = {
        'plan': plan,
    }

    return render(request, 'disinfection/plan_confirm_delete.html', context)


@login_required
def category_list(request):
    """Liste aller Kategorien"""
    categories = DisinfectionCategory.objects.filter(is_active=True).annotate(
        item_count=Count('items')
    )

    context = {
        'categories': categories,
    }

    return render(request, 'disinfection/category_list.html', context)


@login_required
def log_list(request):
    """Liste aller Desinfektionsprotokolle"""
    logs = DisinfectionLog.objects.select_related(
        'vehicle',
        'performed_by',
        'disinfection_item',
        'disinfection_plan'
    ).order_by('-disinfection_date')

    # Filter
    vehicle_id = request.GET.get('vehicle')
    if vehicle_id:
        logs = logs.filter(vehicle_id=vehicle_id)

    date_from = request.GET.get('date_from')
    if date_from:
        logs = logs.filter(disinfection_date__gte=date_from)

    date_to = request.GET.get('date_to')
    if date_to:
        logs = logs.filter(disinfection_date__lte=date_to)

    vehicles = Vehicle.objects.filter(is_active=True)

    context = {
        'logs': logs,
        'vehicles': vehicles,
        'vehicle_filter': vehicle_id,
        'date_from': date_from,
        'date_to': date_to,
    }

    return render(request, 'disinfection/log_list.html', context)


@login_required
@permission_required('disinfection.add_disinfectionlog', raise_exception=True)
def log_create(request):
    """Neues Desinfektionsprotokoll erstellen"""
    from .forms import DisinfectionLogForm

    if request.method == 'POST':
        form = DisinfectionLogForm(request.POST)
        if form.is_valid():
            log = form.save(commit=False)
            log.created_by = request.user
            log.save()

            # Optional: Desinfektionsplan aktualisieren (next_due_date neu berechnen)
            if log.disinfection_plan:
                plan = log.disinfection_plan
                plan.next_due_date = plan.calculate_next_due_date()
                plan.save()

            messages.success(request, 'Desinfektionsprotokoll wurde erfolgreich erstellt.')
            return redirect('disinfection:log_list')
    else:
        # Initialisiere mit aktuellem Datum/Uhrzeit
        initial_date = timezone.now()

        # Wenn Datum in URL übergeben wurde (z.B. aus Kalender)
        date_str = request.GET.get('date')
        if date_str:
            try:
                from datetime import datetime as dt
                parsed = dt.strptime(date_str, '%Y-%m-%d')
                initial_date = timezone.make_aware(
                    dt.combine(parsed.date(), timezone.now().time())
                )
            except (ValueError, TypeError):
                pass

        initial_data = {
            'disinfection_date': initial_date,
        }

        # Wenn Fahrzeug-ID in URL übergeben wurde, vorausfüllen
        vehicle_id = request.GET.get('vehicle')
        if vehicle_id:
            try:
                vehicle = Vehicle.objects.get(id=vehicle_id)
                initial_data['vehicle'] = vehicle
                initial_data['object_type'] = 'Fahrzeug'
                initial_data['object_description'] = f'{vehicle.call_sign} - {vehicle.name}'
            except Vehicle.DoesNotExist:
                pass

        # Wenn Plan-ID in URL übergeben wurde, vorausfüllen
        plan_id = request.GET.get('plan')
        if plan_id:
            try:
                plan = DisinfectionPlan.objects.get(id=plan_id)
                initial_data['disinfection_plan'] = plan
                initial_data['vehicle'] = plan.vehicle
                initial_data['object_type'] = plan.object_type or 'Fahrzeug'
                initial_data['object_description'] = plan.object_description or (f'{plan.vehicle.call_sign}' if plan.vehicle else '')
            except DisinfectionPlan.DoesNotExist:
                pass

        form = DisinfectionLogForm(initial=initial_data)

    context = {
        'form': form,
        'title': 'Neues Desinfektionsprotokoll',
    }

    return render(request, 'disinfection/log_form.html', context)
