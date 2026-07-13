"""
Personenzuordnung für Mengen-Artikel (ClothingItem).

Ein Lagerartikel ist ein Mengenposten ("Weste XL, 39 Stück") und gehört niemandem.
Persönlich ausgegeben ist immer nur eine *Menge* daraus, und die steht in den
Lagerbewegungen. Offener Bestand bei einer Person:

    Ausgabe − Rückgabe − Beschädigung/Schwund

Einzelstücke mit Seriennummer werden dagegen über ClothingItemInstance.assigned_to
geführt und nicht hier.
"""
from decimal import Decimal

from django.db.models import (
    Case,
    DateTimeField,
    DecimalField,
    F,
    Max,
    Sum,
    Value,
    When,
)

from inventory_base.models import StockMovementType

# Vorzeichen einer Bewegung aus Sicht der Person: Ausgabe mehrt, Rückgabe und
# Beschädigung/Schwund mindern ihren offenen Bestand.
SIGNED_QUANTITY = Case(
    When(movement_type=StockMovementType.OUTGOING, then=F('quantity')),
    When(
        movement_type__in=[StockMovementType.RETURN, StockMovementType.DAMAGE],
        then=-F('quantity'),
    ),
    default=Value(Decimal('0')),
    output_field=DecimalField(max_digits=10, decimal_places=2),
)

LAST_ISSUE_DATE = Max(
    Case(
        When(movement_type=StockMovementType.OUTGOING, then=F('movement_date')),
        output_field=DateTimeField(),
    )
)


def open_issues(person=None, item=None, items=None):
    """
    Offene persönliche Ausgaben je (Person, Artikel), abgeleitet aus den Bewegungen.

    Liefert dicts mit person, item, quantity und last_issue – nur für Paare, bei
    denen noch etwas offen ist. `items` grenzt auf mehrere Artikel ein.
    """
    from clothing.models import ClothingStockMovement

    queryset = ClothingStockMovement.objects.filter(
        person__isnull=False,
        item__is_active=True,
    )
    if person is not None:
        queryset = queryset.filter(person=person)
    if item is not None:
        queryset = queryset.filter(item=item)
    if items is not None:
        queryset = queryset.filter(item__in=items)

    return (
        queryset
        .values('person', 'item')
        .annotate(quantity=Sum(SIGNED_QUANTITY), last_issue=LAST_ISSUE_DATE)
        .filter(quantity__gt=0)
    )


def annotate_issues(items):
    """
    Hängt an jedes ClothingItem die offenen Ausgaben als `issues` an.

    Jeder Eintrag ist ein dict mit person, quantity und issued_date. Artikel ohne
    offene Ausgabe bekommen eine leere Liste – dann liegt der Bestand im Pool.
    Reines Anzeige-Attribut, wird nicht gespeichert.
    """
    from personnel.models import Person

    items = list(items)
    if not items:
        return items

    rows = list(open_issues(items=items))
    persons = Person.objects.in_bulk({row['person'] for row in rows})

    je_artikel = {}
    for row in rows:
        person = persons.get(row['person'])
        if person is None:
            continue
        je_artikel.setdefault(row['item'], []).append({
            'person': person,
            'quantity': row['quantity'],
            'issued_date': row['last_issue'],
        })

    for item in items:
        item.issues = je_artikel.get(item.pk, [])

    return items


def issued_items_for_person(person):
    """
    Artikel, von denen die Person aktuell noch etwas hat.

    Die zurückgegebenen ClothingItem-Objekte tragen zusätzlich `issued_quantity`
    (ausgegebene Menge) und `issued_date` (letzte Ausgabe). Beides sind reine
    Anzeige-Attribute und werden nicht gespeichert.
    """
    from clothing.models import ClothingItem

    rows = {row['item']: row for row in open_issues(person=person)}
    items = ClothingItem.objects.filter(pk__in=rows).select_related('category', 'location')

    for item in items:
        item.issued_quantity = rows[item.pk]['quantity']
        item.issued_date = rows[item.pk]['last_issue']

    return sorted(items, key=lambda item: (item.clothing_type, item.size))


def issued_item_ids():
    """IDs aller Artikel, von denen aktuell etwas bei einer Person ist."""
    return {row['item'] for row in open_issues()}


def total_issued_quantity():
    """Gesamtzahl der aktuell persönlich ausgegebenen Teile."""
    return sum((row['quantity'] for row in open_issues()), Decimal('0'))
