from django.apps import AppConfig
from django.db.models.signals import post_migrate


def _seed_categories(sender, **kwargs):
    if sender.name != 'termine':
        return
    from .defaults import ensure_default_categories
    from .models import EventCategory
    ensure_default_categories(EventCategory)


class TermineConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'termine'
    verbose_name = 'Termine'

    def ready(self):
        post_migrate.connect(_seed_categories, dispatch_uid='termine_seed_categories')
