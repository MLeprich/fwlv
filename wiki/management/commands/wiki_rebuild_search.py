"""Volltext (search_text) aller Wiki-Seiten neu aufbauen – einmalig nach dem Update oder bei Bedarf."""
from django.core.management.base import BaseCommand

from wiki.models import WikiPage


class Command(BaseCommand):
    help = 'Suchindex (Volltext) aller Wiki-Seiten neu aufbauen'

    def handle(self, *args, **options):
        n = 0
        for page in WikiPage.objects.all():
            page.rebuild_search_text()
            n += 1
        self.stdout.write(self.style.SUCCESS(f'✓ {n} Seiten neu indexiert'))
