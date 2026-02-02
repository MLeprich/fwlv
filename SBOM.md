# FLVS - Software Bill of Materials (SBOM)

**Projekt:** Feuerwehr Lagerverwaltungssystem (FLVS)
**Version:** 1.1.0
**Aktualisiert:** Februar 2025
**Format:** CycloneDX-kompatibel

---

## Systemkomponenten

| Komponente | Version | Beschreibung |
|------------|---------|--------------|
| Python | 3.12 | Programmiersprache |
| PostgreSQL | 16 | Datenbank |
| Redis | 7 | Cache & Message Broker |
| Nginx | 1.24+ | Reverse Proxy |

---

## Frontend-Bibliotheken (lokal/CDN)

| Bibliothek | Version | Lizenz | Beschreibung |
|------------|---------|--------|--------------|
| HTMX | 2.0.8 | BSD-2-Clause | HTML Extensions |
| Alpine.js | 3.14.8 | MIT | Reactive JavaScript |
| Tailwind CSS | 3.x | MIT | CSS Framework |
| Mermaid.js | 11.x (CDN) | MIT | Diagramme & Flowcharts |

---

## Python-Abhängigkeiten

### Framework & Core

| Paket | Version | Lizenz | Beschreibung |
|-------|---------|--------|--------------|
| Django | 5.0.14 | BSD-3-Clause | Web-Framework |
| gunicorn | 23.0.0 | MIT | WSGI HTTP Server |
| asgiref | 3.9.2 | BSD-3-Clause | ASGI-Spezifikation |
| whitenoise | 6.11.0 | MIT | Static Files Serving |

### Datenbank

| Paket | Version | Lizenz | Beschreibung |
|-------|---------|--------|--------------|
| psycopg2-binary | 2.9.10 | LGPL | PostgreSQL-Adapter |
| django-environ | 0.12.0 | MIT | Umgebungsvariablen |

### REST API

| Paket | Version | Lizenz | Beschreibung |
|-------|---------|--------|--------------|
| djangorestframework | 3.16.1 | BSD-3-Clause | REST API Framework |
| djangorestframework-simplejwt | 5.5.1 | MIT | JWT Authentication |
| drf-spectacular | 0.28.0 | BSD-3-Clause | OpenAPI Schema |
| django-filter | 25.1 | BSD-3-Clause | Queryset Filtering |

### Authentifizierung & Sicherheit

| Paket | Version | Lizenz | Beschreibung |
|-------|---------|--------|--------------|
| django-axes | 8.0.0 | MIT | Brute-Force Protection |
| django-guardian | 3.2.0 | BSD-3-Clause | Object Permissions |
| django-otp | 1.6.1 | BSD-2-Clause | 2FA Support |
| PyJWT | 2.10.1 | MIT | JSON Web Tokens |

### Background Tasks

| Paket | Version | Lizenz | Beschreibung |
|-------|---------|--------|--------------|
| celery | 5.5.3 | BSD-3-Clause | Task Queue |
| django-celery-beat | 2.8.1 | BSD-3-Clause | Periodic Tasks |
| django-celery-results | 2.6.0 | BSD-3-Clause | Task Results |
| redis | 6.4.0 | MIT | Redis Client |
| django-redis | 6.0.0 | BSD-3-Clause | Django Redis Cache |
| kombu | 5.5.4 | BSD-3-Clause | Messaging Library |
| amqp | 5.3.1 | BSD-3-Clause | AMQP Protocol |
| billiard | 4.2.2 | BSD-3-Clause | Process Pool |
| vine | 5.1.0 | BSD-3-Clause | Promise Library |

### Formulare & Admin

| Paket | Version | Lizenz | Beschreibung |
|-------|---------|--------|--------------|
| django-crispy-forms | 2.4 | MIT | Form Rendering |
| crispy-tailwind | 1.0.3 | MIT | Tailwind für Crispy |
| django-admin-interface | 0.30.1 | MIT | Admin UI |
| django-colorfield | 0.14.0 | MIT | Color Picker |
| django-import-export | 4.3.10 | BSD-2-Clause | Excel Import/Export |
| django-mptt | 0.18.0 | MIT | Tree Structures |

### Dateiverarbeitung

| Paket | Version | Lizenz | Beschreibung |
|-------|---------|--------|--------------|
| pillow | 11.3.0 | HPND | Bildverarbeitung |
| python-magic | 0.4.27 | MIT | MIME Detection |
| openpyxl | 3.1.5 | MIT | Excel-Dateien |
| python-docx | 1.2.0 | MIT | Word-Dokumente |
| pypdf | 6.6.0 | BSD-3-Clause | PDF-Verarbeitung |
| pdf2image | 1.17.0 | MIT | PDF zu Bild |
| weasyprint | 66.0 | BSD-3-Clause | HTML zu PDF |
| lxml | 6.0.2 | BSD-3-Clause | XML/HTML Parser |

### OCR & Barcodes

| Paket | Version | Lizenz | Beschreibung |
|-------|---------|--------|--------------|
| pytesseract | 0.3.13 | Apache-2.0 | OCR Engine |
| python-barcode | 0.16.1 | MIT | Barcode-Generator |
| qrcode | 8.2 | BSD-3-Clause | QR-Code Generator |

### Utilities

| Paket | Version | Lizenz | Beschreibung |
|-------|---------|--------|--------------|
| python-dateutil | 2.9.0 | Apache-2.0 | Datum-Utilities |
| python-slugify | 8.0.4 | MIT | Slug-Generierung |
| pytz | 2025.2 | MIT | Zeitzonen |
| click | 8.3.0 | BSD-3-Clause | CLI Framework |
| PyYAML | 6.0.3 | MIT | YAML Parser |
| Brotli | 1.1.0 | MIT | Kompression |
| zopfli | 0.2.3 | Apache-2.0 | Kompression |

### Testing & Development

| Paket | Version | Lizenz | Beschreibung |
|-------|---------|--------|--------------|
| pytest | 8.4.2 | MIT | Test Framework |
| pytest-django | 4.11.1 | BSD-3-Clause | Django Testing |
| coverage | 7.10.7 | Apache-2.0 | Code Coverage |
| factory-boy | 3.3.3 | MIT | Test Fixtures |
| Faker | 37.8.0 | MIT | Fake Data |
| django-debug-toolbar | 6.0.0 | BSD-3-Clause | Debug Toolbar |

---

## System-Abhängigkeiten (apt)

| Paket | Beschreibung |
|-------|--------------|
| libpq-dev | PostgreSQL Client |
| libpango-1.0-0 | Text Rendering (WeasyPrint) |
| libpangocairo-1.0-0 | Cairo Integration |
| libgdk-pixbuf2.0-0 | Bildverarbeitung |
| poppler-utils | PDF Tools |
| tesseract-ocr | OCR Engine |
| tesseract-ocr-deu | Deutsche Sprachdaten |
| libmagic1 | MIME Detection |

---

## Lizenzzusammenfassung

| Lizenz | Anzahl Pakete |
|--------|---------------|
| MIT | 31 |
| BSD-3-Clause | 24 |
| BSD-2-Clause | 4 |
| Apache-2.0 | 4 |
| LGPL | 1 |
| HPND | 1 |

**Alle Lizenzen sind Open-Source und kommerziell nutzbar.**

---

## Sicherheitshinweise

- Regelmäßige Updates: `pip install --upgrade -r requirements.txt`
- Sicherheitsprüfung: `pip-audit` oder `safety check`
- CVE-Monitoring empfohlen für alle Dependencies

---

*Aktualisiert: Februar 2025*
