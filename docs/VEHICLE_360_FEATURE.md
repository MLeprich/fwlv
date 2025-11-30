# 360° Sphärische Foto-Verwaltung für Fahrzeuginnenräume

**Version:** 1.0.0
**Stand:** 21. Oktober 2025
**Modul:** `vehicle_handover`

---

## 📋 Übersicht

Das 360° Feature ermöglicht die Verwaltung sphärischer Panorama-Fotos von Fahrzeuginnenräumen mit interaktiven Hotspots. Benutzer können:

- **360° Fotos hochladen** von Fahrerkabine und Laderaum/Mannschaftsraum
- **Hotspots setzen** für Schubladen, Fächer, Schränke etc.
- **Detailbilder hinterlegen** für jeden Hotspot
- **Checklisten verknüpfen** zur Inventurprüfung
- **Interaktiv navigieren** im 360° Viewer

---

## 🎯 Hauptfunktionen

### 1. 360° Foto-Verwaltung

**Pfad:** `/vehicle_handover/360/`

- Hochladen von equirectangular/sphärischen Fotos
- Unterstützt Fotos von Insta360 V2 und anderen 360°-Kameras
- Separate Bereiche: Vorne (Fahrerkabine) und Hinten (Laderaum)
- Versionierung: Mehrere Fotos pro Fahrzeug möglich
- Aktiv/Inaktiv Status für zeitliche Verwaltung

### 2. Interaktiver 360° Viewer

**Pfad:** `/vehicle_handover/360/<id>/`

- Vollständige 360° Navigation (Maus, Touch, Tastatur)
- Zoom-Funktion
- Vollbild-Modus
- Hotspots als interaktive Marker
- Click-to-Focus auf Hotspots

### 3. Hotspot-Editor

**Pfad:** `/vehicle_handover/360/<id>/editor/`

- **Click-to-Add:** Klick ins Foto platziert Hotspot
- **Drag-to-Rotate:** Ansicht durch Ziehen drehen
- **Echtzeitkoordinaten:** Pitch/Yaw-Anzeige
- **Visueller Feedback:** Bearbeitungsmodus mit Hilfe-Overlay

### 4. Hotspot-Management

Jeder Hotspot kann enthalten:

- **Titel & Beschreibung**
- **Typ:**
  - 📋 Checkliste (verknüpft mit ChecklistTemplate)
  - 🖼️ Bildergalerie (Detailfotos)
  - ℹ️ Information (nur Text)
  - 📝 Gemischt (Bilder + Checkliste)
- **Visuelle Anpassung:**
  - 9 Icons (📦 Schublade, 🗄️ Schrank, 🔧 Werkzeug, etc.)
  - 7 Farben (Blau, Rot, Grün, Gelb, Lila, Orange, Grau)
- **Detailbilder:** Bis zu unbegrenzt viele Fotos mit Bildunterschriften
- **Reihenfolge:** Sortierung konfigurierbar

---

## 🏗️ Datenmodell

### Vehicle360Photo

```python
class Vehicle360Photo(AuditedModel):
    vehicle = ForeignKey(Vehicle)           # Zugeordnetes Fahrzeug
    photo_type = CharField                  # 'front' oder 'rear'
    image = ImageField                      # Equirectangular Image
    title = CharField                       # z.B. "HLF 1 - Mannschaftsraum 2024"
    description = TextField                 # Optional
    resolution_width = IntegerField         # Auto-ermittelt
    resolution_height = IntegerField        # Auto-ermittelt
    captured_date = DateField               # Aufnahmedatum
    is_active = BooleanField                # Für Versionierung
```

**Unique Constraint:** Ein Fahrzeug kann nur ein aktives Foto pro Typ haben.

### Vehicle360Hotspot

```python
class Vehicle360Hotspot(AuditedModel):
    photo_360 = ForeignKey(Vehicle360Photo)
    title = CharField                       # z.B. "Schublade links oben"
    description = TextField                 # Optional
    pitch = FloatField                      # -90° bis +90° (vertikal)
    yaw = FloatField                        # -180° bis +180° (horizontal)
    hotspot_type = CharField                # checklist/images/info/mixed
    checklist_template = ForeignKey         # Optional
    icon = CharField                        # drawer/cabinet/tool/etc.
    color = CharField                       # blue/red/green/etc.
    order = IntegerField                    # Sortierung
    is_active = BooleanField
```

### HotspotImage

```python
class HotspotImage(TimeStampedModel):
    hotspot = ForeignKey(Vehicle360Hotspot)
    image = ImageField
    caption = CharField                     # Optional
    order = IntegerField                    # Sortierung
```

---

## 🚀 Verwendung

### Schritt 1: 360° Foto hochladen

1. Navigation: **Fahrzeugübernahme → 360° Ansichten → Neues 360° Foto**
2. Fahrzeug auswählen
3. Bereich wählen (Vorne/Hinten)
4. Titel eingeben (z.B. "HLF 1 - Fahrerkabine 2024")
5. Equirectangular-Foto von Insta360 V2 hochladen
6. Aufnahmedatum eingeben
7. **Speichern**

**Tipp:** Fotos von Insta360 V2 sind bereits im richtigen Format (equirectangular).

### Schritt 2: Hotspots hinzufügen

1. Auf dem 360° Foto: **Bearbeiten** klicken
2. **Bearbeitungsmodus aktivieren** (obere rechte Ecke)
3. **Im Foto klicken** an der gewünschten Position
4. Im Modal eingeben:
   - Titel (z.B. "Medizinschrank links")
   - Typ (Checkliste/Bilder/Info/Gemischt)
   - Icon & Farbe auswählen
5. **Hotspot erstellen**
6. Optional: Hotspot bearbeiten und Detailbilder hinzufügen

### Schritt 3: Detailbilder hinzufügen

1. In der Hotspot-Liste: **Bearbeiten** klicken
2. Unter "Detailbilder" bis zu 3+ Bilder hochladen
3. Bildunterschriften eingeben
4. Reihenfolge festlegen
5. **Speichern**

### Schritt 4: Checkliste verknüpfen

1. Hotspot bearbeiten
2. Typ: "Checkliste" oder "Gemischt" wählen
3. Im Dropdown eine Checklisten-Vorlage auswählen
4. **Speichern**

Jetzt ist der Hotspot mit der Checkliste verknüpft und zeigt bei Fahrzeugübergaben den Prüfstatus an.

---

## 🔗 Integration in Fahrzeugübergabe

### Automatische Anzeige

Wenn ein Fahrzeug 360° Fotos hat, werden diese automatisch in der **Fahrzeugübergabe-Detailansicht** angezeigt:

- **Bereich:** "360° Innenraum-Ansichten"
- **Anzeige:** Karten mit Vorschau, Hotspot-Anzahl, Datum
- **Klick:** Öffnet interaktiven 360° Viewer

### Use Case: Fahrzeugübernahme-Protokoll

1. Wachleiter öffnet Übergabe für Fahrzeug
2. Sieht 360° Fotos des Fahrzeuginnenraums
3. Klickt auf Hotspot "Medizinschrank"
4. Sieht Detailbilder des Inhalts
5. Prüft gegen hinterlegte Checkliste
6. Dokumentiert Vollzähligkeit oder Mängel

---

## 📱 Bedienung

### Desktop (Maus)

- **Linke Maustaste + Ziehen:** Ansicht drehen
- **Mausrad:** Zoomen
- **Klick auf Hotspot:** Details anzeigen
- **Rechtsklick:** Kontext-Menü (Browser)

### Mobile (Touch)

- **Finger ziehen:** Ansicht drehen
- **Pinch:** Zoomen
- **Tap auf Hotspot:** Details anzeigen
- **Zwei Finger:** Zoom

### Tastatur

- **Pfeiltasten:** Ansicht drehen
- **+/-:** Zoomen
- **F:** Fullscreen
- **ESC:** Fullscreen verlassen

---

## ⚙️ Technische Details

### Frontend Libraries

- **Photo Sphere Viewer:** v5.x (MIT License)
  - Core: 360° Panorama-Darstellung
  - Markers Plugin: Interaktive Hotspots
- **Three.js:** WebGL 3D Engine (automatisch geladen)

### Performance-Optimierung

```python
# Effiziente Queries mit select_related/prefetch_related
Vehicle360Photo.objects.select_related(
    'vehicle',
    'created_by',
    'updated_by'
).prefetch_related(
    'hotspots',
    'hotspots__images',
    'hotspots__checklist_template'
)
```

### Bildanforderungen

- **Format:** JPEG, PNG
- **Projektion:** Equirectangular (360° × 180°)
- **Empfohlene Auflösung:** 5376×2688 (Insta360 V2 Standard)
- **Minimale Auflösung:** 4000×2000
- **Maximale Dateigröße:** 20 MB (konfigurierbar)

### Koordinatensystem

- **Pitch (Vertikal):**
  - -90° = nach unten schauen
  - 0° = geradeaus
  - +90° = nach oben schauen
- **Yaw (Horizontal):**
  - 0° = Vorne (Center)
  - +90° = Rechts
  - +180° / -180° = Hinten
  - -90° = Links

---

## 🔐 Berechtigungen

### Erforderliche Permissions

- `vehicle_handover.view_vehicle360photo` - Fotos ansehen
- `vehicle_handover.add_vehicle360photo` - Fotos hochladen
- `vehicle_handover.change_vehicle360photo` - Fotos bearbeiten
- `vehicle_handover.delete_vehicle360photo` - Fotos löschen
- `vehicle_handover.add_vehicle360hotspot` - Hotspots erstellen
- `vehicle_handover.change_vehicle360hotspot` - Hotspots bearbeiten
- `vehicle_handover.delete_vehicle360hotspot` - Hotspots löschen

### Rollenkonzept

- **Wachleiter:** Nur Ansicht (view)
- **Lagerverwalter:** Ansicht + Erstellen (view, add)
- **Modulverantwortlicher:** Volle Rechte (view, add, change, delete)
- **Administrator:** Volle Rechte + Admin-Interface

---

## 📊 Admin-Interface

### Zugriff

**URL:** `/admin/vehicle_handover/vehicle360photo/`

### Features

- Inline-Bearbeitung von Hotspots
- Inline-Bearbeitung von Hotspot-Bildern
- Thumbnail-Vorschau
- Farbige Badges für Status
- Position-Anzeige (Pitch/Yaw)
- Filterung nach Fahrzeug, Typ, Status
- Suche nach Titel, Beschreibung

### List Display

- Thumbnail
- Fahrzeug
- Typ-Badge (Vorne/Hinten)
- Titel
- Hotspot-Anzahl
- Aktiv-Badge
- Erstellungsdatum

---

## 🐛 Troubleshooting

### Problem: Foto wird nicht korrekt angezeigt

**Lösung:**
- Prüfen, ob Foto im equirectangular Format vorliegt
- Aspect Ratio sollte 2:1 sein (Breite : Höhe)
- Browser-Konsole auf Fehler prüfen

### Problem: Hotspots werden nicht angezeigt

**Lösung:**
- Prüfen, ob Hotspots auf `is_active=True` gesetzt sind
- Browser-Cache leeren
- JavaScript-Konsole auf Fehler prüfen
- Koordinaten prüfen (Pitch: -90 bis +90, Yaw: -180 bis +180)

### Problem: Performance-Probleme

**Lösung:**
- Bilder komprimieren (max. 5376×2688 für Insta360 V2)
- Nicht mehr benötigte Fotos auf `is_active=False` setzen
- Browser-Cache nutzen (automatisch aktiv)

### Problem: Click-to-Add funktioniert nicht

**Lösung:**
- "Bearbeitungsmodus aktivieren" klicken
- Prüfen, ob JavaScript aktiviert ist
- Browser aktualisieren (Chrome 90+, Firefox 88+, Safari 14+)

---

## 📈 Best Practices

### 1. Foto-Management

- **Naming Convention:** `[Fahrzeug] - [Bereich] [Jahr]`
  - Beispiel: "HLF 1 - Mannschaftsraum 2024"
- **Regelmäßige Updates:** Jährlich oder nach größeren Umbauten
- **Alte Fotos archivieren:** Auf `is_active=False` setzen statt löschen
- **Konsistente Aufnahmeposition:** Immer von gleicher Stelle fotografieren

### 2. Hotspot-Verwaltung

- **Aussagekräftige Titel:** "Medizinschrank links oben" statt "Schrank 1"
- **Farbcodierung nutzen:**
  - 🔴 Rot: Kritische/wichtige Bereiche (BTM, Notfallausrüstung)
  - 🟢 Grün: Standard-Ausstattung
  - 🟡 Gelb: Prüfbedürftige Bereiche
- **Icons passend wählen:**
  - 📦 Schublade für Schubladen
  - 🗄️ Schrank für Schränke
  - ⚕️ Medizin für Sanitätsmaterial
  - 🔧 Werkzeug für Werkzeugfächer

### 3. Checklisten-Integration

- **Granularität:** Ein Hotspot pro logischem Bereich
- **Hierarchie:** Hauptfächer als Hotspots, Inhalte in Checkliste
- **Synchronisation:** Checklisten aktuell halten bei Änderungen

### 4. Detailbilder

- **Qualität:** Ausreichend hochauflösend für Erkennbarkeit
- **Anzahl:** 2-5 Bilder pro Hotspot (Übersicht + Details)
- **Bildunterschriften:** Kurz und beschreibend
- **Aktualität:** Bei Änderungen Bilder aktualisieren

---

## 🔄 Workflow-Beispiel: Neues Fahrzeug

1. **Fahrzeug fotografieren:**
   - Insta360 V2 in Fahrzeugmitte positionieren
   - Vorne (Fahrerkabine) fotografieren
   - Hinten (Laderaum/Mannschaftsraum) fotografieren
   - Fotos auf Computer übertragen

2. **Fotos hochladen:**
   - Beide Fotos im System hochladen
   - Titel vergeben
   - Aufnahmedatum setzen
   - Aktiv setzen

3. **Hotspots platzieren:**
   - Vorne: Handschuhfach, Funkgerät, Seitenfächer
   - Hinten: Alle Schubladen, Schränke, Fächer einzeln markieren
   - Icons und Farben zuweisen

4. **Detailbilder hinzufügen:**
   - Jeden Hotspot öffnen
   - Fotos des Inhalts hochladen (geöffnete Schublade)
   - Bildunterschriften ergänzen

5. **Checklisten verknüpfen:**
   - Für wichtige Bereiche Checklisten erstellen
   - Mit Hotspots verknüpfen
   - Testlauf mit Fahrzeugübergabe

6. **Qualitätsprüfung:**
   - Alle Hotspots im Viewer testen
   - Positionen nachkorrigieren falls nötig
   - Vollständigkeit prüfen

---

## 📚 API-Endpunkte

### REST API (für zukünftige Integration)

```
GET    /api/v1/vehicle-handover/360-photos/              # Liste aller 360° Fotos
POST   /api/v1/vehicle-handover/360-photos/              # Neues Foto erstellen
GET    /api/v1/vehicle-handover/360-photos/{id}/         # Foto-Details
PUT    /api/v1/vehicle-handover/360-photos/{id}/         # Foto aktualisieren
DELETE /api/v1/vehicle-handover/360-photos/{id}/         # Foto löschen

GET    /api/v1/vehicle-handover/360-photos/{id}/hotspots/   # Hotspots eines Fotos
POST   /api/v1/vehicle-handover/hotspots/                   # Hotspot erstellen
PUT    /api/v1/vehicle-handover/hotspots/{id}/              # Hotspot aktualisieren
DELETE /api/v1/vehicle-handover/hotspots/{id}/              # Hotspot löschen
```

---

## 🎓 Schulungsmaterial

### Video-Tutorial-Themen (empfohlen)

1. **Grundlagen:** 360° Fotos mit Insta360 V2 aufnehmen (5 Min)
2. **Upload:** Fotos ins System hochladen und verwalten (3 Min)
3. **Hotspots:** Interaktive Hotspots platzieren (7 Min)
4. **Checklisten:** Hotspots mit Checklisten verknüpfen (5 Min)
5. **Fahrzeugübergabe:** 360° Fotos bei Übergabe nutzen (4 Min)

### Schulungsplan

- **Zielgruppe:** Lagerverwalter, Modulverantwortliche
- **Dauer:** 30 Minuten
- **Inhalt:**
  - Theoretischer Überblick (5 Min)
  - Praktische Demo (15 Min)
  - Hands-On-Übung (10 Min)

---

## 📞 Support

**Technischer Support:** [Tech Lead Name]
**Fachlicher Support:** [Modulverantwortlicher Name]
**Dokumentation:** `/docs/VEHICLE_360_FEATURE.md`
**Issue-Tracker:** [URL zum Issue-Tracker]

---

## 📜 Changelog

### Version 1.0.0 (21. Oktober 2025)

- ✅ Initiale Implementierung
- ✅ 360° Foto-Upload und Verwaltung
- ✅ Interaktiver Viewer mit Photo Sphere Viewer
- ✅ Click-to-Add Hotspot-Editor
- ✅ Hotspot-Management mit Detailbildern
- ✅ Checklisten-Integration
- ✅ Integration in Fahrzeugübergabe
- ✅ Admin-Interface
- ✅ Responsive Design
- ✅ Error Handling & Loading States
- ✅ Performance-Optimierung

---

**Letztes Update:** 21. Oktober 2025
**Autor:** Claude (Anthropic)
**Status:** Produktionsreif ✅
