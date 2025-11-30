Feuerwehr-Lagerverwaltungssystem - Projektübersicht
Technologie-Stack

Backend: Python (Flask/Django)
Frontend: HTMX für dynamische Interaktionen
Datenbank: PostgreSQL (empfohlen für Compliance & Audit-Trail)


Kern-Module (Lagerverwaltung)
1. Kleiderkammer

Ausgabe von Schutz- und Dienstkleidung an Personal
Größenverwaltung und Passform-Historie
Reinigungszyklen-Tracking
Rückgabe-Workflow bei Personalwechsel
Budget pro Person/Abteilung
Integration mit Stammdatenverwaltung

2. Magazin

Verbrauchsmaterial des täglichen Bedarfs (Waschmittel, Batterien, Handschuhe, Schrauben, Werkzeuge)
Mindesthaltbarkeitsdatum-Verwaltung
Automatische Bestellvorschläge basierend auf Verbrauch
Lieferanten-Verwaltung mit Preisvergleich

3. Rettungsdienst

Medizintechnik: Corpus C3, Sonographie-Geräte, Defibrillatoren
Medikamente:

BTM (Betäubungsmittel) mit besonderem Sicherheitsbereich und digitaler Signatur
Standard-Medikamente


Chargenrückverfolgung
Ablaufdatum-Überwachung
Temperatur-Logging für kühlpflichtige Medikamente
Integration mit Einsatzprotokollen
Rezeptverwaltung

4. KFZ-Werkstatt

Ersatzteile (Schrauben, Luftfilter, Öle, etc.)
Prüfungsverwaltung (TÜV, HU, Bremsenprüfung, individuelle Prüfungen)
Kalenderübersicht für geplante Werkstattaufenthalte
Wartungshistorie als "Fahrzeug-Lebenslauf"
Tankbuch (Kraftstoffverbrauch, CO2-Bilanz)
Schadensmanagement mit Fotodokumentation
Reifenverwaltung (Sommer/Winter, Profiltiefe)

5. Desinfektion

Lagerverwaltung Desinfektionsmittel
Desinfektionspläne und Intervalle für Fahrzeuge
Integration mit Fahrzeugverwaltung
Desinfektionskalender
Nachweis-Protokolle für Hygienekontrollen
Verbrauchsstatistiken
Priorisierung nach Einsatzart (Infektionstransporte)

6. Höhenrettung

Karabiner, Seile, Gurte, PSA
Individuell anlegbare Intervallprüfungen
Persönliche Zuordnung von Ausrüstung
Einsatzstatistiken
Wartungsanleitungen im System

7. Taucher

Tauchgeräte und Ausrüstung
Sauerstoffflaschen-Verwaltung
Einsatzdokumentation
Prüfintervalle (TÜV für Flaschen, etc.)
Pflichtstunden-Tracking

8. Ausrüstung & Geräte (oder "Einsatzmittel"/"Technik")
Alternative Bezeichnungen: "Technisches Gerät", "Einsatzausrüstung", "Gerätewesen"

Generatoren, Aggregate, Pumpen
Schläuche (Druck-, Saug-, Spezialschläuche)
Kettensägen und motorgetriebene Geräte
Leitern (tragbare und Steckleitern)
Spezielle Prüfungen:

Leitern: Sicht- und Belastungsprüfungen mit Jahresvergleich (Durchbiegungsmessung)
Tragkraftspritzen: Leistungsprüfungen
Kettensägen: Sicherheitsprüfungen


Katastrophenschutz-Material (Zelte, Feldbetten, Notstromaggregate)
Beleuchtungsgeräte
Hebezeuge und Rettungsgeräte

9. IT-Hardware

Verwaltung von Computern, Laptops, Tablets, Smartphones, Druckern
Zuordnung zu:

Benutzern (Personal)
Räumen/Standorten
Fahrzeugen (z.B. Tablets in Einsatzfahrzeugen)


Technische Details:

Hostname
IP-Adresse (statisch/DHCP)
MAC-Adresse (Ethernet + WLAN)
Seriennummer
Garantie/Leasing-Ende
Betriebssystem und Software-Lizenzen


Wartungsverträge und Support-Tickets
Lifecycle-Management (Anschaffung → Nutzung → Aussonderung)


Zentrale Verwaltungs-Module
10. Stammdatenverwaltung (Personal)

Personalstammdaten
Qualifikationen und Ausbildungen
Prüfungen (z.B. Atemschutz, Maschinisten)
Pflichtstunden (Tauchen, Höhenrettung, Rettungsdienst)
Benachrichtigungen für anstehende Prüfungen/Schulungen
Berechtigungen für verschiedene System-Module
Persönliche Schutzausrüstung-Zuordnung
Schulungshistorie

11. Fahrzeugverwaltung

Fahrzeugstammdaten:

Hersteller, Modell, Baujahr
Fahrzeugtyp (Drehleiter, LF, RTW, etc.)
Funkkennung
Fahrgestellnummer


Mobile Lager:

Hierarchische Struktur: Fahrzeug → Fächer/Schubladen → Lagerorte
Beladungspläne (Soll-Zustand)
Inventar-Zuordnung


Integration mit allen relevanten Modulen (KFZ-Werkstatt, Desinfektion, Fahrzeugübernahme)

12. Lagerorte

Hierarchische Struktur:

Ebene 1: Standorte (Hauptwache, Nebenwache A, etc.)
Ebene 2: Gebäude/Stellflächen (Hauptgebäude, Halle, Außenbereich)
Ebene 3: Räume/Stellplätze (Werkstatt, Magazin, Parkplatz 3)
Ebene 4: Lagerorte (Regal A, Schrank 2, Fach 5)


QR-Code/Barcode für jeden Lagerort
Kapazitätsverwaltung
Zugriff für alle Lager-Module


Prozess-Module
13. Fahrzeugübernahme

Checklisten für Wachmannschaft
Kilometerstand-Erfassung
Soll-Ist-Vergleich mobile Lager
Tankstand, Schäden, Sauberkeit
Sphärische 360°-Fotos:

Innenansicht des Fahrzeugs
Interaktive Hotspots für Fächer/Schubladen
Foto-Upload für Ist-Zustand
Referenzbilder für Besatzung


Digitale Unterschrift
Übergabeprotokoll (PDF-Export)

14. Info-Monitore (Dashboard-Builder)

Canvas-basierter Dashboard-Designer
Widgets:

Kritische Bestände
Anstehende Prüfungen
Überfällige Wartungen
KPI-Kennzahlen
Kalenderansichten
Benachrichtigungen


Individuelle Monitore pro Bereich (Werkstatt, Höhenrettung, etc.)
Vollbild-Modus für Displays
Auto-Refresh

15. Bestellwesen

Zentrale Bestellverwaltung für alle Module
Workflow:

Anfrage → Genehmigung → Bestellung → Wareneingang → Buchung


Budget-Kontrolle und Kostenstellen
Lieferanten-Verwaltung
Preisvergleich und Bestellhistorie
Automatische Bestellvorschläge bei Unterschreitung Schwellwerte

16. Inventur

Stichtagsinventuren planen
Mobile Erfassung (Barcode/QR-Scanner)
Differenzen-Analyse
Mehrere Zähler parallel
Inventur-Protokolle

17. Einsatzdokumentation (Light)

Grundlegende Verknüpfung zu Einsätzen
Material-Verbrauch bei Einsätzen
Automatische Nachbestellung nach Großschadenslagen
Integration mit Rettungsdienst-Modul (Medikamentenverbrauch)

18. Schulungsmodul

Schulungsplanung und -dokumentation
Einweisungen für neue Geräte
Verknüpfung mit Personal (wer darf was bedienen?)
Qualifikations-Nachweis
Schulungsbedarfsermittlung

19. Dokumentenmanagement

Zentrale Ablage für:

Prüfprotokolle
Zertifikate
Handbücher und Bedienungsanleitungen
Sicherheitsdatenblätter
Wartungsverträge


Automatische Verknüpfung mit Artikeln, Fahrzeugen, Personal
Ablaufdaten-Überwachung
Versionierung
Volltextsuche


Übergreifende System-Features
Berechtigungssystem (CRUD + Rollenbasiert)

Rollen: Administrator, Lagerverwalter, Werkstattmeister, Wachleiter, Standard-Nutzer, Gast
CRUD-Berechtigungen pro Modul:

Create (Anlegen)
Read (Lesen)
Update (Bearbeiten)
Delete (Löschen)


Erweiterte Berechtigungen:

Vier-Augen-Prinzip für kritische Aktionen (BTM-Entsorgung, teure Artikel)
Zeitbasierte Berechtigungen (nur während Dienstzeit)
Vertretungsregelungen
Freigabe-Workflows für Bestellungen
Modul-spezifische Berechtigungen



Schwellwert-Management

Pro Artikel konfigurierbar:

Mindestbestand (Warnung)
Kritischer Bestand (Alarm)
Optimaler Bestand
Maximaler Bestand


Automatische Benachrichtigungen
Eskalationsstufen

Barcode/QR-Code System

Eindeutige Identifikation aller Assets
Schnelles Ein-/Ausbuchen per Scanner
Mobile App für Inventur
Etiketten-Druck direkt aus System

Audit-Trail (Änderungshistorie)

Vollständige Nachverfolgbarkeit:

Wer hat was wann geändert?
Vorher/Nachher-Werte
IP-Adresse und Gerät


Unveränderbare Logs
Besonders wichtig für BTM und sicherheitskritische Ausrüstung
Export-Funktion für Audits

Benachrichtigungssystem

Multi-Channel:

E-Mail
Push-Benachrichtigungen (Web/Mobile)
In-App-Notifications
Optional: SMS für kritische Meldungen


Benachrichtigungs-Typen:

Ablaufende Prüfungen/Zertifikate
Kritische Bestände
Anstehende Wartungen
Bestellfreigaben
System-Meldungen


Eskalationsstufen (Erinnerung → Mahnung → Eskalation)
Persönliche und rollenbasierte Benachrichtigungen
Konfigurierbare Vorlaufzeiten

KPI & Controlling

Dashboard für Leitungsebene
KPIs pro Modul:

Lagerumschlag
Durchschnittliche Lagerdauer
Bestandswert
Verbrauch pro Zeitraum
Kosten pro Einsatz/Fahrzeug/Abteilung
Prüfquoten (fristgerecht/überfällig)
Inventurdifferenzen


Kostenstellen-Zuordnung
Budget-Überwachung
Export für externe Controlling-Software
Trend-Analysen und Prognosen

Reporting & Statistiken

Vorgefertigte Reports:

Bestandslisten
Verbrauchsauswertungen
Prüfprotokolle
Kostenauswertungen
Inventurberichte


Custom-Reports (parametrisierbar)
Export-Formate: PDF, Excel, CSV
Automatische Report-Versendung (z.B. monatlich)
Grafische Auswertungen (Charts, Diagramme)

API & Schnittstellen

RESTful API für externe Systeme
Import von Lieferanten-Katalogen
Export für Controlling-Software
Integration mit Einsatzleitsystem (optional)
Schnittstelle zu Buchhaltungssoftware
Webhook-Support für Automatisierungen

Backup & Archivierung

Automatische tägliche Backups
Gesetzliche Aufbewahrungsfristen beachten
Gelöschte Datensätze werden archiviert, nicht physisch gelöscht
Point-in-Time-Recovery
Verschlüsselte Backups

Offline-Fähigkeit

Progressive Web App (PWA)
Offline-Modus für Fahrzeugübernahmen
Lokale Daten-Speicherung (Browser)
Automatische Synchronisation bei Verbindung

Mehrsprachigkeit

Deutsch als Hauptsprache
Optional: Englisch, weitere Sprachen
Übersetzbare UI-Elemente
Sprachauswahl pro Benutzer


Compliance & Sicherheit
Rechtliche Anforderungen

DSGVO-Konformität bei Personaldaten
Betäubungsmittelgesetz (BtMG): Besonderer Schutz für BTM-Bereich
Arzneimittelgesetz (AMG): Dokumentation Medikamente
Medizinproduktegesetz (MPG): Nachweis Medizintechnik
DGUV-Vorschriften: PSA und Prüffristen

Sicherheitsmaßnahmen

Verschlüsselte Datenübertragung (HTTPS/TLS)
Verschlüsselte Datenspeicherung (at rest)
Zwei-Faktor-Authentifizierung (2FA)
Session-Management
Regelmäßige Security-Audits
Penetration-Tests
Sichere Passwort-Richtlinien
Automatische Logout bei Inaktivität


Technische Architektur-Empfehlungen
Backend-Framework
Option A: Django (empfohlen für dieses Projekt)

Umfangreiches Admin-Interface out-of-the-box
Starkes ORM für komplexe Datenbeziehungen
Integriertes User-Management
Viele Erweiterungen verfügbar

Option B: Flask

Leichtgewichtiger
Mehr Flexibilität
Erfordert mehr manuelle Konfiguration

Frontend mit HTMX

Server-Side Rendering
Minimaler JavaScript-Code
Schnelle Ladezeiten
SEO-freundlich
Kombinierbar mit Alpine.js für Client-seitige Interaktivität

Datenbank

PostgreSQL (dringend empfohlen)

Robust und skalierbar
Hervorragende JSON-Unterstützung
Audit-Trail via Trigger
Point-in-Time-Recovery



Zusätzliche Technologien

Redis: Caching, Session-Storage
Celery: Background-Tasks (Benachrichtigungen, Reports)
Docker: Containerisierung für einfaches Deployment
Nginx: Reverse Proxy
MinIO/S3: Objektspeicher für Fotos, Dokumente


Empfohlene Umsetzungsphasen
Phase 1: Fundament (MVP)

User-Management & Berechtigungssystem
Stammdatenverwaltung (Personal)
Lagerorte-Verwaltung
Ein Basis-Lagermodul (z.B. Magazin)
Grundlegendes Dashboard

Phase 2: Kern-Lager

Kleiderkammer
Rettungsdienst (ohne BTM)
Ausrüstung & Geräte
IT-Hardware
Bestellwesen (Basis)

Phase 3: Fahrzeuge & Spezial-Lager

Fahrzeugverwaltung
KFZ-Werkstatt
Desinfektion
Fahrzeugübernahme (ohne 360°-Fotos)

Phase 4: Spezial-Bereiche

BTM-Verwaltung (Rettungsdienst)
Höhenrettung
Taucher
Dokumentenmanagement

Phase 5: Erweiterte Features

360°-Fotos bei Fahrzeugübernahme
Info-Monitore (Dashboard-Builder)
Inventur-Modul
Erweiterte Reports und KPIs

Phase 6: Optimierung

Mobile App
Barcode-Scanner-Integration
API für Drittsysteme
Einsatzdokumentation (Light)
Schulungsmodul
