"""
Management Command: OCR-Verarbeitung für bestehende Dokumente

Verwendung:
    python manage.py process_document_ocr                    # Alle unverarbeiteten Dokumente
    python manage.py process_document_ocr --all              # Alle Dokumente (auch bereits verarbeitete)
    python manage.py process_document_ocr --id 123           # Einzelnes Dokument
    python manage.py process_document_ocr --type manual      # Nur Handbücher
"""

from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone
from documents.models import Document
from documents.utils import extract_text_from_file
import os


class Command(BaseCommand):
    help = 'Verarbeitet Dokumente mit OCR und extrahiert Text'

    def add_arguments(self, parser):
        parser.add_argument(
            '--all',
            action='store_true',
            help='Verarbeite alle Dokumente (auch bereits verarbeitete)',
        )
        parser.add_argument(
            '--id',
            type=int,
            help='Verarbeite nur Dokument mit dieser ID',
        )
        parser.add_argument(
            '--type',
            type=str,
            help='Verarbeite nur Dokumente dieses Typs (z.B. manual, certificate)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Zeige nur an, welche Dokumente verarbeitet würden',
        )

    def handle(self, *args, **options):
        # Query-Builder
        queryset = Document.objects.all()

        # Filter nach ID
        if options['id']:
            queryset = queryset.filter(id=options['id'])
            self.stdout.write(f"🎯 Filtere nach ID: {options['id']}")

        # Filter nach Typ
        elif options['type']:
            queryset = queryset.filter(document_type=options['type'])
            self.stdout.write(f"🎯 Filtere nach Typ: {options['type']}")

        # Filter nach unverarbeiteten
        elif not options['all']:
            queryset = queryset.filter(ocr_processed=False)
            self.stdout.write("🎯 Filtere nach unverarbeiteten Dokumenten")

        # Zähle Dokumente
        total = queryset.count()

        if total == 0:
            self.stdout.write(self.style.WARNING("⚠️  Keine Dokumente gefunden"))
            return

        self.stdout.write(f"\n📄 Gefundene Dokumente: {total}\n")
        self.stdout.write("=" * 70)

        # Dry-Run?
        if options['dry_run']:
            self.stdout.write(self.style.WARNING("\n🔍 DRY-RUN Modus (keine Änderungen)\n"))
            for doc in queryset:
                self.stdout.write(f"  • [{doc.id}] {doc.title}")
                self.stdout.write(f"    Datei: {doc.file.name}")
            return

        # Verarbeitung
        success_count = 0
        error_count = 0
        skip_count = 0

        for i, doc in enumerate(queryset, 1):
            self.stdout.write(f"\n[{i}/{total}] {doc.title}")
            self.stdout.write(f"  Datei: {doc.file.name}")

            # Prüfe ob Datei existiert
            if not doc.file:
                self.stdout.write(self.style.WARNING("  ⚠️  Keine Datei vorhanden"))
                skip_count += 1
                continue

            file_path = doc.file.path

            if not os.path.exists(file_path):
                self.stdout.write(self.style.ERROR(f"  ❌ Datei nicht gefunden: {file_path}"))
                error_count += 1
                continue

            # Text extrahieren
            try:
                text = extract_text_from_file(file_path)

                if text:
                    # Text speichern
                    doc.ocr_text = text
                    doc.ocr_processed = True
                    doc.ocr_processed_at = timezone.now()
                    doc.save(update_fields=['ocr_text', 'ocr_processed', 'ocr_processed_at', 'updated_at'])

                    char_count = len(text)
                    word_count = len(text.split())

                    self.stdout.write(self.style.SUCCESS(
                        f"  ✅ Erfolgreich: {char_count} Zeichen, {word_count} Wörter"
                    ))
                    success_count += 1
                else:
                    self.stdout.write(self.style.WARNING(
                        "  ⚠️  Keine Text-Extraktion möglich (nicht unterstützter Dateityp)"
                    ))
                    skip_count += 1

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  ❌ Fehler: {e}"))
                error_count += 1

        # Zusammenfassung
        self.stdout.write("\n" + "=" * 70)
        self.stdout.write("\n📊 Zusammenfassung:")
        self.stdout.write(f"  ✅ Erfolgreich: {success_count}")
        self.stdout.write(f"  ⚠️  Übersprungen: {skip_count}")
        self.stdout.write(f"  ❌ Fehler: {error_count}")
        self.stdout.write(f"  📄 Gesamt: {total}\n")

        if success_count > 0:
            self.stdout.write(self.style.SUCCESS(
                f"\n✨ {success_count} Dokumente erfolgreich verarbeitet!"
            ))
