from django.apps import AppConfig


class MagazineConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'magazine'
    verbose_name = 'Magazin (Verbrauchsmaterial)'

    def ready(self):
        """Importiere Signals beim App-Start"""
        import magazine.signals
