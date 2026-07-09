from django.apps import AppConfig


class ObjektverwaltungConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'objektverwaltung'
    verbose_name = 'Objektverwaltung'

    def ready(self):
        # Abo-Benachrichtigungen registrieren
        import objektverwaltung.signals  # noqa: F401
