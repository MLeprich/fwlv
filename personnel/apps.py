from django.apps import AppConfig


class PersonnelConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'personnel'
    verbose_name = 'Personal'

    def ready(self):
        """Import signals when app is ready"""
        import personnel.signals
