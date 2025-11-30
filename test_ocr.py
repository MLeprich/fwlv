#!/usr/bin/env python
"""
Testet die OCR-Funktionalität
"""

import os
import sys
import django

# Django Setup
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'flvs_project.settings.development')
django.setup()

from documents.utils import extract_text_from_file

# Test mit existierenden Dateien
media_root = os.path.join(os.path.dirname(__file__), 'media')
documents_dir = os.path.join(media_root, 'documents')

if os.path.exists(documents_dir):
    print(f"📁 Suche nach Dokumenten in: {documents_dir}\n")

    # Alle PDF-Dateien finden
    pdf_files = []
    for root, dirs, files in os.walk(documents_dir):
        for file in files:
            if file.lower().endswith(('.pdf', '.jpg', '.jpeg', '.png')):
                pdf_files.append(os.path.join(root, file))

    if pdf_files:
        print(f"✅ Gefundene Dateien: {len(pdf_files)}\n")

        # Teste erste 3 Dateien
        for i, file_path in enumerate(pdf_files[:3], 1):
            print(f"{'='*60}")
            print(f"Test {i}/{min(3, len(pdf_files))}: {os.path.basename(file_path)}")
            print(f"{'='*60}")

            text = extract_text_from_file(file_path)

            if text:
                print(f"✅ Text extrahiert: {len(text)} Zeichen")
                print(f"\nErste 200 Zeichen:")
                print(f"{'-'*60}")
                print(text[:200])
                print(f"{'-'*60}\n")
            else:
                print(f"❌ Keine Text-Extraktion möglich\n")
    else:
        print(f"⚠️  Keine PDF/Bild-Dateien gefunden")
        print(f"\nBitte lade über die Web-Oberfläche ein Dokument hoch")
        print(f"oder platziere Test-PDFs in: {documents_dir}")
else:
    print(f"⚠️  Dokumenten-Verzeichnis nicht gefunden: {documents_dir}")
    print(f"\nBitte starte den Server und lade ein Dokument hoch")

print("\n" + "="*60)
print("Tesseract-Version:")
print("="*60)
os.system("tesseract --version | head -1")
