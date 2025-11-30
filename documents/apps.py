from django.apps import AppConfig


class DocumentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'documents'
    verbose_name = 'Dokumentenmanagement'

    def ready(self):
        """Importiere Signals beim App-Start"""
        import documents.signals
