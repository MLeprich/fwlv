"""
Ticket-Kategorie "IT Datenversorgung" bereitstellen.

Kategorien liegen in der Datenbank (pro Deployment). Damit die Kategorie auch
auf der Stadt-VM nach `git pull` + migrate vorhanden ist, wird sie hier angelegt.
Eine bereits manuell angelegte Kategorie "Datenversorgung" wird umbenannt,
damit verknüpfte Tickets erhalten bleiben und kein Duplikat entsteht.
"""

from django.db import migrations


NAME = 'IT Datenversorgung'


def add_category(apps, schema_editor):
    TicketCategory = apps.get_model('tickets', 'TicketCategory')

    if TicketCategory.objects.filter(name__iexact=NAME).exists():
        return

    existing = TicketCategory.objects.filter(name__iexact='Datenversorgung').first()
    if existing:
        existing.name = NAME
        existing.save(update_fields=['name'])
        return

    slug = 'it-datenversorgung'
    counter = 1
    while TicketCategory.objects.filter(slug=slug).exists():
        slug = f'it-datenversorgung-{counter}'
        counter += 1

    # Direkt hinter "IT & Technik" einsortieren, falls vorhanden
    it_cat = TicketCategory.objects.filter(slug='it').first()
    order = it_cat.order + 1 if it_cat else 3

    TicketCategory.objects.create(
        name=NAME,
        slug=slug,
        icon='🗄️',
        color='#0EA5E9',
        description='Datenversorgung durch die IT (z.B. Stammdaten, Schnittstellen, Datenbestände)',
        is_active=True,
        order=order,
    )


def noop(apps, schema_editor):
    # Kategorie bewusst nicht löschen – es könnten Tickets daran hängen.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('tickets', '0041_ff_stammfahrzeug'),
    ]

    operations = [
        migrations.RunPython(add_category, noop),
    ]
