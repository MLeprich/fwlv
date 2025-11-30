from django.apps import AppConfig


class MedicalConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'medical'
    verbose_name = 'Rettungsdienst (Medizin & BTM)'

    def ready(self):
        """Importiere Signals beim App-Start"""
        import medical.signals
