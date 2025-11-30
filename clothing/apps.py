from django.apps import AppConfig


class ClothingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'clothing'
    verbose_name = 'Kleiderkammer'

    def ready(self):
        """Importiere Signals beim App-Start"""
        import clothing.signals
