# 📊 Benutzerdefinierte Messfelder für Prüfungen

## Übersicht

Mit den benutzerdefinierten Messfeldern können Sie für jede Prüfungsart individuelle Felder definieren, die bei jeder Prüfung ausgefüllt werden müssen. Die Werte werden gespeichert und können über die Jahre verglichen werden.

**Perfekt für:**
- Leiter-Durchbiegungsprüfungen (Messen der Durchbiegung Jahr für Jahr)
- Messungen von Abständen, Gewichten, Drücken
- Beliebige wiederkehrende Messwerte

---

## 🎯 Anwendungsfall: Leiter-Durchbiegungsprüfung

### Hintergrund
Bei der jährlichen Prüfung von Leitern wird diese horizontal auf zwei Stützen gelegt und in der Mitte mit einem definierten Gewicht belastet. Der Abstand vom tiefsten Punkt der Leiter zum Boden wird gemessen. Diese Messung muss jedes Jahr wiederholt und mit den Vorjahreswerten verglichen werden, um Materialermüdung zu erkennen.

### Schritt-für-Schritt Anleitung

#### 1. Prüfungsart mit Messfeldern erstellen

**Navigation:**
```
Equipment Dashboard → Verwaltung → Prüfungsarten → Neue Prüfungsart
```

**URL:** https://lager.resqware.de/equipment/inspection-types/create/

**Ausfüllen:**
- **Name:** Belastungsprüfung Leiter horizontal
- **Beschreibung:** Die Leiter wird horizontal auf zwei Stützen gelegt und in der Mitte mit definiertem Gewicht belastet. Der Abstand vom tiefsten Punkt zum Boden wird gemessen.
- **Prüfnorm:** DIN 14811
- **Intervall:** 12 Monate

**Benutzerdefinierte Messfelder (JSON):**
```json
[
  {
    "name": "Durchbiegung Mitte",
    "type": "number",
    "unit": "mm",
    "required": true,
    "min": 0,
    "max": 100,
    "help_text": "Abstand vom tiefsten Punkt der Leiter zum Boden"
  },
  {
    "name": "Abstand Boden vorher",
    "type": "number",
    "unit": "mm",
    "required": false,
    "min": 0,
    "help_text": "Abstand vor Belastung (optional)"
  },
  {
    "name": "Testgewicht",
    "type": "number",
    "unit": "kg",
    "required": true,
    "min": 50,
    "max": 200,
    "help_text": "Verwendetes Prüfgewicht"
  },
  {
    "name": "Temperatur",
    "type": "number",
    "unit": "°C",
    "required": false,
    "help_text": "Umgebungstemperatur während der Prüfung"
  },
  {
    "name": "Bemerkungen",
    "type": "text",
    "required": false,
    "placeholder": "Besondere Beobachtungen..."
  }
]
```

#### 2. Prüfung einer Leiter zuweisen

**Navigation:**
```
Equipment Dashboard → Verwaltung → Zuweisungen → Neue Zuweisung
```

**URL:** https://lager.resqware.de/equipment/inspection-assignments/create/

**Ausfüllen:**
- **Gerät:** Wählen Sie die Leiter (z.B. "Steckleiter 4-teilig")
- **Prüfungsart:** "Belastungsprüfung Leiter horizontal"
- **Nächste Prüfung:** Setzen Sie das Datum für die erste Prüfung

#### 3. Prüfung durchführen

**Navigation:**
```
Equipment Dashboard → Verwaltung → Prüfung durchführen
```

**URL:** https://lager.resqware.de/equipment/inspection-records/create/

**Das System zeigt automatisch:**
- Alle Standard-Felder (Datum, Prüfer, Ergebnis, etc.)
- **Automatisch generierte Messfelder:**
  - Durchbiegung Mitte (mm) - mit Validierung 0-100mm
  - Abstand Boden vorher (mm) - optional
  - Testgewicht (kg) - mit Validierung 50-200kg
  - Temperatur (°C) - optional
  - Bemerkungen - Textfeld

**Beispielhafte Eingabe (Jahr 2025):**
- Durchbiegung Mitte: **12.5 mm**
- Testgewicht: **150 kg**
- Temperatur: **18 °C**
- Ergebnis: Bestanden

**Im Folgejahr (2026):**
- Durchbiegung Mitte: **12.8 mm** (leichte Zunahme)
- Testgewicht: **150 kg**
- Temperatur: **20 °C**
- Ergebnis: Bestanden

➡️ Durch den Vergleich der Werte über die Jahre können Sie Trends erkennen!

---

## 📋 Feldtypen und Optionen

### 1. Number (Zahlenwerte)

**Verwendung:** Messungen, Gewichte, Abstände, Temperaturen, Drücke

**Beispiel:**
```json
{
  "name": "Durchbiegung Mitte",
  "type": "number",
  "unit": "mm",
  "required": true,
  "min": 0,
  "max": 100,
  "placeholder": "Wert in mm",
  "help_text": "Gemessener Abstand zum Boden"
}
```

**Attribute:**
- `min`: Minimalwert (z.B. 0)
- `max`: Maximalwert (z.B. 100)
- `unit`: Einheit (mm, kg, °C, bar, etc.)

**Darstellung im Formular:**
```
Durchbiegung Mitte (mm) *
[_______________] Wert in mm
Gemessener Abstand zum Boden
```

---

### 2. Text (Freitext)

**Verwendung:** Bemerkungen, Beschreibungen, Notizen

**Beispiel:**
```json
{
  "name": "Bemerkungen",
  "type": "text",
  "required": false,
  "placeholder": "Besondere Beobachtungen...",
  "help_text": "Zusätzliche Anmerkungen zur Prüfung"
}
```

**Darstellung im Formular:**
```
Bemerkungen
[_______________] Besondere Beobachtungen...
Zusätzliche Anmerkungen zur Prüfung
```

---

### 3. Date (Datum)

**Verwendung:** Zusätzliche Datumsangaben (z.B. Datum der letzten Reparatur)

**Beispiel:**
```json
{
  "name": "Letzte Reparatur",
  "type": "date",
  "required": false,
  "help_text": "Datum der letzten Instandsetzung"
}
```

**Darstellung im Formular:**
```
Letzte Reparatur
[DD.MM.YYYY] 📅
Datum der letzten Instandsetzung
```

---

### 4. Boolean (Ja/Nein)

**Verwendung:** Checkboxen für Ja/Nein-Fragen

**Beispiel:**
```json
{
  "name": "Rost vorhanden",
  "type": "boolean",
  "required": false,
  "help_text": "Wurde Rostbildung festgestellt?"
}
```

**Darstellung im Formular:**
```
☐ Rost vorhanden
  Wurde Rostbildung festgestellt?
```

---

## 🔧 Weitere Anwendungsbeispiele

### Beispiel 1: Druckprüfung Schläuche

```json
[
  {
    "name": "Prüfdruck",
    "type": "number",
    "unit": "bar",
    "required": true,
    "min": 0,
    "max": 50
  },
  {
    "name": "Haltedauer",
    "type": "number",
    "unit": "min",
    "required": true,
    "min": 1,
    "max": 30
  },
  {
    "name": "Druckabfall",
    "type": "number",
    "unit": "bar",
    "required": true,
    "min": 0
  },
  {
    "name": "Undichtigkeit festgestellt",
    "type": "boolean",
    "required": false
  }
]
```

### Beispiel 2: Gewichtsprüfung Atemschutzgeräte

```json
[
  {
    "name": "Gesamtgewicht",
    "type": "number",
    "unit": "kg",
    "required": true,
    "min": 10,
    "max": 20
  },
  {
    "name": "Flaschendruck",
    "type": "number",
    "unit": "bar",
    "required": true,
    "min": 0,
    "max": 300
  },
  {
    "name": "Maskenprüfung bestanden",
    "type": "boolean",
    "required": true
  }
]
```

### Beispiel 3: Funktionsprüfung Generator

```json
[
  {
    "name": "Leerlaufdrehzahl",
    "type": "number",
    "unit": "U/min",
    "required": true,
    "min": 0,
    "max": 5000
  },
  {
    "name": "Ausgangsspannung",
    "type": "number",
    "unit": "V",
    "required": true,
    "min": 200,
    "max": 240
  },
  {
    "name": "Ölstand OK",
    "type": "boolean",
    "required": true
  },
  {
    "name": "Betriebsstunden",
    "type": "number",
    "unit": "h",
    "required": false
  },
  {
    "name": "Nächster Ölwechsel",
    "type": "date",
    "required": false
  }
]
```

---

## ⚙️ Technische Details

### JSON-Struktur

Jedes Messfeld ist ein JSON-Objekt in einer Liste:

```json
[
  {
    "name": "Feldname",           // Erforderlich: Name des Feldes
    "type": "number",              // Erforderlich: number, text, date, boolean
    "unit": "mm",                  // Optional: Einheit
    "required": true,              // Optional: Pflichtfeld (true/false)
    "min": 0,                      // Optional: Minimalwert (nur bei number)
    "max": 100,                    // Optional: Maximalwert (nur bei number)
    "placeholder": "Text",         // Optional: Platzhalter
    "help_text": "Hilfetext"      // Optional: Erklärung
  }
]
```

### Validierung

Das System validiert automatisch:
- ✅ Pflichtfelder müssen ausgefüllt werden
- ✅ Zahlenwerte müssen im definierten min/max Bereich liegen
- ✅ Feldtypen werden geprüft (Zahl, Datum, etc.)
- ✅ JSON-Syntax wird beim Speichern der Prüfungsart validiert

### Datenspeicherung

Die Messwerte werden als JSON im Feld `custom_field_values` gespeichert:

```json
{
  "Durchbiegung Mitte": "12.5",
  "Testgewicht": "150",
  "Temperatur": "18"
}
```

---

## 📊 Datenauswertung und Verlauf

### Anzeige der historischen Werte

Im Prüfprotokoll (InspectionRecord Detail) werden alle Messwerte angezeigt.

### Vergleich über die Jahre

**Manueller Vergleich:**
1. Öffnen Sie die Liste der Prüfprotokolle für ein Gerät
2. Vergleichen Sie die Werte der verschiedenen Jahre
3. Achten Sie auf Trends (z.B. zunehmende Durchbiegung)

**Beispiel Leiter-Prüfung:**
```
Jahr 2023: Durchbiegung 11.2 mm
Jahr 2024: Durchbiegung 12.0 mm (+0.8mm)
Jahr 2025: Durchbiegung 12.5 mm (+0.5mm)
Jahr 2026: Durchbiegung 13.8 mm (+1.3mm) ⚠️ Trend beachten!
```

➡️ **Bei deutlich zunehmendem Trend sollte die Leiter genauer untersucht oder ausgemustert werden!**

---

## ❓ Häufig gestellte Fragen (FAQ)

### Kann ich Messfelder nachträglich hinzufügen?
**Ja!** Sie können die Prüfungsart bearbeiten und weitere Felder hinzufügen. Bestehende Prüfprotokolle bleiben unverändert, neue Prüfungen haben dann die zusätzlichen Felder.

### Kann ich Messfelder entfernen?
**Ja, aber Vorsicht!** Wenn Sie Felder entfernen, gehen die bereits erfassten Werte in alten Prüfprotokollen nicht verloren (sie sind weiterhin in der Datenbank), werden aber nicht mehr im Formular angezeigt.

### Kann ich verschiedene Geräte mit unterschiedlichen Messfeldern prüfen?
**Ja!** Erstellen Sie einfach verschiedene Prüfungsarten mit unterschiedlichen Messfeldern und weisen Sie diese den entsprechenden Geräten zu.

### Wie viele Messfelder kann ich definieren?
**Unbegrenzt!** Es gibt keine technische Begrenzung. Aus Usability-Gründen empfehlen wir jedoch maximal 10-15 Felder pro Prüfung.

### Kann ich Berechnungen durchführen?
**Aktuell nicht automatisch.** Sie können jedoch berechnete Werte manuell eingeben (z.B. Differenz zum Vorjahr).

---

## 🎓 Best Practices

### 1. Sprechende Feldnamen verwenden
✅ "Durchbiegung Mitte"
❌ "Feld1"

### 2. Einheiten immer angeben
✅ `"unit": "mm"`
❌ Einheit im Feldnamen: "Durchbiegung in mm"

### 3. Hilfetext für komplexe Messungen
```json
{
  "name": "Durchbiegung Mitte",
  "help_text": "Abstand vom tiefsten Punkt der belasteten Leiter zum Boden"
}
```

### 4. Min/Max sinnvoll setzen
Verhindert Eingabefehler:
```json
{
  "name": "Durchbiegung Mitte",
  "min": 0,
  "max": 100,  // Verhindert Tippfehler wie 125 statt 12.5
}
```

### 5. Nicht zu viele Pflichtfelder
Nur wirklich wichtige Werte als `"required": true` markieren.

---

## 🔗 Weiterführende Links

- **Prüfungsarten verwalten:** https://lager.resqware.de/equipment/inspection-types/
- **Neue Prüfungsart erstellen:** https://lager.resqware.de/equipment/inspection-types/create/
- **Prüfungen zuweisen:** https://lager.resqware.de/equipment/inspection-assignments/
- **Prüfung durchführen:** https://lager.resqware.de/equipment/inspection-records/create/
- **Verwaltungs-Dashboard:** https://lager.resqware.de/equipment/maintenance/management/

---

## 📞 Support

Bei Fragen oder Problemen wenden Sie sich an:
- **System-Administrator:** [Name]
- **Technischer Support:** [E-Mail/Telefon]

---

**Letzte Aktualisierung:** 05.10.2025
**Version:** 1.0
