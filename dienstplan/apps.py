from django.apps import AppConfig
from django.db.models.signals import post_migrate


def _seed_codes(sender, **kwargs):
    if sender.name != 'dienstplan':
        return
    from .defaults import ensure_default_codes
    from .models import DutyCode
    ensure_default_codes(DutyCode)


class DienstplanConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'dienstplan'
    verbose_name = 'Dienstplan'

    def ready(self):
        # Standardcodes auch ohne Migrationen (Tests mit --no-migrations) bereitstellen
        post_migrate.connect(_seed_codes, dispatch_uid='dienstplan_seed_codes')
