# MP3 Tagger Web Application

Eine webbasierte Anwendung zur Verwaltung und Bearbeitung von MP3-Metadaten mit erweiterten Erkennungsfunktionen, basisierend auf python3.Wird mit einer vnv betrieben.

## 🎯 Funktionsbeschreibung (System Design)

### 📋 Vierstufiger Workflow

#### **Stufe 1: Grunddaten-Erfassung (automatisch)**
**Verzeichnis-Auswahl:**
- Quellverzeichnis manuell eingeben oder per Explorer auswählen
- Automatisches Scannen aller MP3-Dateien im Verzeichnis
- Ergebnisse werden verzeichnisweise sortiert in Stufe 2 angezeigt

#### **Stufe 2: Grunddaten-Erfassung (automatisch)**
Beim Laden eines Verzeichnisses werden **automatisch** alle verfügbaren Informationen gesammelt:

1. **ID3-Tags auslesen**: Vorhandene Metadaten (Artist, Titel, Album, Track, Genre)
2. **Cover-Status ermitteln**: Internes Cover, externes Cover im Verzeichnis  
3. **Dateiname-Parsing**: Falls keine ID3-Tags vorhanden → Automatische Erkennung aus Dateinamen
   - **Artist/Titel-Muster**: `"Artist - Title.mp3"`, `"Track Artist - Title.mp3"`
   - **Track-Nummern-Muster**: `"01 - Title.mp3"`, `"001 Track.mp3"`, `"05. Song.mp3"`
   - **Kombinierte Muster**: `"Artist - 02 - Title.mp3"`, `"Album/03-Song.mp3"`
   - **Visuelle Kennzeichnung**: Beige Hintergrund für erkannte Daten
   - **Track-Formatierung**: Automatische Anpassung an konfigurierte Stellenzahl (mit führender 0)

#### **Stufe 3: Audio-Erkennung (auf Knopfdruck)**
Für Dateien ohne ausreichende Metadaten → **Audio-Fingerprinting**:

1. **Shazam-Erkennung** (Primär): Beste Ergebnisse mit Cover-URLs und Streaming-Links
2. **AcoustID-Erkennung** (Fallback): MusicBrainz-basierte Metadaten
3. **Intelligente Segmentierung**: Verschiedene Audio-Abschnitte für bessere Trefferquote

**Button pro Datei**: "🎵 Erkennen" startet Audio-Fingerprinting
Die Felder Track#, Artist, Titel sowie Album sollen manuell editierbar bleiben

#### **Stufe 4: Metadaten-Anreicherung (selektiv)**
Für markierte Dateien → **Erweiterte Anreicherung**:

1. **Online-Metadaten**: MusicBrainz + Last.fm für zusätzliche Informationen
2. **Cover-Suche**: Hochauflösende Cover-Art von verschiedenen Quellen  
3. **Erweiterte Tags**: Genre-Details, Mood, Era, MusicBrainz-IDs
4. **Album-Kontext**: Intelligente Album-Erkennung für ganze Verzeichnisse

**Button für markierte Dateien**: "🌐 Metadaten anreichern"

---

### 1. Grundfunktionalität


**Datenanzeige:**
- Tabellensicht mit einer Zeile pro MP3-Datei
- Spalten: Dateiname, Track-Nummer, Artist, Titel, Album, Genre, Cover-Status
- Aktuelles Verzeichnis wird über der Tabelle angezeigt
- Hover-Details zeigen erweiterte ID3-Informationen
- Checkbox vor jeder MP3 Datei, für jedes Verzeichnis, für alle Dateien zur Auswahl

### 2. Cover-System

**Cover-Status-Anzeige:**
- `I<px>` - Cover in MP3 Abgespeichert - Intern mit Auflösung (z.B. I500 = 500x500px)
- `E<px>` - Cover liegt im aktuellen Verzeichnis der MP3 - Externes Logo im Verzeichnis (z.B. E300 = 300x300px) 
- `Nein` - Kein Cover vorhanden
- `B<px>` - Beide (intern + extern, px = interne Auflösung)

**Cover-Verwaltung:**
- **Anzeige**: Hover über Cover-Status zeigt Vorschau
- **Behalten**: Vorhandene Cover beibehalten (Standard)
- **Ersetzen**: Neue Cover aus Online-Quellen einbetten
- **Löschen**: Cover komplett aus MP3-Datei entfernen
- **Priorität**: Interne Cover haben Vorrang vor externen Dateien

**Cover-Quellen für Anreicherung:**
- **Shazam**: Hochauflösende Cover (primäre Quelle)
- **MusicBrainz**: Cover Art Archive
- **Last.fm**: Album-Artwork
- **Discogs**: Release-Cover

### 3. Bearbeitungsmodus

**Editierbare Felder:**
- Artist, Titel, Album, Track-Nummer
- Inline-Bearbeitung direkt in der Tabelle
- Visuelle Kennzeichnung geänderter Felder

**Track-Nummer-Verwaltung:**
- **Flexible Stellenzahl**: 1, 2 oder 3 Stellig konfigurierbar
- **Führende Nullen**: Automatische Formatierung (01, 001, etc.)
- **Live-Formatierung**: Eingabe wird sofort formatiert angezeigt
- **Bulk-Update**: Stellenzahl-Änderung aktualisiert alle Track-Nummern
- **Intelligente Erkennung**: Aus Dateinamen extrahierte Track-Nummern

**Track-Konfiguration:**
- Dropdown-Auswahl für Stellenzahl (1-3 Stellen)
- Sofortige Anwendung auf alle sichtbaren Tracks
- Beibehaltung der numerischen Werte bei Format-Änderung

**Auswahl-System:**
- Checkboxen für einzelne Dateien
- "Alle markieren" / "Alle abwählen" Buttons
- Verarbeitung nur für markierte Dateien

### 4. Erweiterte Funktionen

**Audio-Erkennung:**
- Button pro Datei für Audio-Fingerprinting
- Verwendet Shazam/AcoustID für Metadaten-Erkennung
- Ersetzt/ergänzt fehlende ID3-Tags

**Dateiname-Parsing:**
- Automatische Erkennung bei fehlenden ID3-Tags
- Beige Hintergrund für erkannte Daten
- **Track-Erkennung**: Intelligente Extraktion aus Dateinamen
  - Muster: `"01 - Title.mp3"`, `"001 Track.mp3"`, `"Artist - 05 - Title.mp3"`
  - Führende Nullen werden erkannt und beibehalten
  - Track-Position am Dateianfang oder nach Artist-Namen
- **Weitere Muster**: `"Artist - Title.mp3"`, `"Album/01 - Title.mp3"`

**Audio-Player:**
- Play-Button pro Datei
- Einfacher Inline-Player zum Vorhören
- Keine komplexe Playlist-Funktionalität

### 5. Speicher-Workflow

**Einfacher Speicher-Prozess:**
1. Dateien markieren
2. "Speichern" Button
3. Bestätigung zeigen
4. Metadaten in MP3-Dateien schreiben
5. Cover-Operationen durchführen (falls gewünscht)
6. Erfolgs-/Fehlermeldung anzeigen

**Cover-Verwaltung beim Speichern:**
- **Automatisch**: Neue Cover werden eingebettet wenn keine vorhanden
- **Benutzer-Auswahl**: Cover behalten/ersetzen/löschen bei vorhandenen Covern
- **Qualitäts-Prüfung**: Höhere Auflösung wird bevorzugt
- **Format-Unterstützung**: JPEG, PNG (wird zu JPEG konvertiert für MP3)

**Vereinfachte Cover-Operationen:**
- Fokus auf Metadaten-Bearbeitung
- Cover als Zusatz-Feature, nicht Hauptfunktion
- Keine komplexen Cover-Auswahl-Dialoge

## 🎨 UI/UX Philosophie

### Einfachheit vor Features
- Klare, übersichtliche Tabelle als Hauptansicht
- Minimale Modal-Dialoge
- Direktes Feedback bei Aktionen
- Keine verschachtelten Menüs oder komplexe Workflows

### Benutzerfreundlichkeit
- Intuitive Bedienung ohne Anleitung
- Schnelle Bearbeitung vieler Dateien
- Fehlertolerante Eingabe
- Klare visuelle Rückmeldungen

### Performance
- Schnelles Laden von Verzeichnissen
- Responsive Tabelle auch bei vielen Dateien
- Asynchrone Audio-Erkennung
- Batch-Operationen für markierte Dateien

## 🔧 Technische Anforderungen

### API-Services und Konfiguration

**Verwendete Dienste für Metadaten-Anreicherung:**
- **ShazamIO**: Audio-Fingerprinting (primärer Service, keine API-Key nötig)
- **AcoustID**: Audio-Fingerprinting Fallback (kostenlos, API-Key erforderlich)
- **MusicBrainz**: Metadaten-Datenbank (kostenlos, User-Agent erforderlich)
- **Last.fm**: Genre und Artist-Informationen (API-Key erforderlich)
- **Discogs**: Release-Informationen und Cover (API-Key erforderlich)

**Konfiguration in `config.env`:**
```bash
# Audio-Fingerprinting
ACOUSTID_API_KEY=your_acoustid_key_here

# Metadaten-Services  
LASTFM_API_KEY=your_lastfm_key_here
MUSICBRAINZ_USERAGENT=YourAppName/1.0 (your@email.com)

# Cover und Release-Daten
DISCOGS_CONSUMER_KEY=your_discogs_key_here
DISCOGS_CONSUMER_SECRET=your_discogs_secret_here

# Betrieb
MP3_SOURCE_DIR=~/tmp/mp3ren/mp3s
DRY_RUN=True
LOG_FILE=~/tmp/mp3ren/processing.log
```

**API-Key Beschaffung:**
- **AcoustID**: Registrierung auf https://acoustid.org/
- **Last.fm**: API-Key auf https://www.last.fm/api
- **Discogs**: Developer Account auf https://www.discogs.com/developers/
- **MusicBrainz**: Keine Registrierung, nur User-Agent erforderlich
- **Shazam**: Keine API-Keys nötig (verwendet ShazamIO Python-Library)

**Kern-Features (Priorität 1):**
- ✅ Verzeichnis scannen und MP3s anzeigen
- ✅ ID3-Metadaten bearbeiten
- ✅ Cover-Status anzeigen
- ✅ Speichern-Funktionalität
- ✅ Dateiname-Parsing

**Erweiterte Features (Priorität 2):**
- ✅ Audio-Erkennung (Shazam/AcoustID)
- ✅ Audio-Player
- ✅ Hover-Details
- ✅ Batch-Operationen

**Nice-to-have (Priorität 3):**
- ⭕ Erweiterte Genre-Anzeige
- ⭕ Undo-Funktionalität
- Rename der Zieldatei nach Muster

## 🚫 Bewusst ausgelassene Komplexität

- Kein komplexes Cover-Management
- Keine Playlist-Funktionen
- Keine Datei-Organisation/Umbenennung
- Keine Benutzer-Accounts oder Sessions
- Keine Datenbank für Metadaten-Cache

---

## Current Implementation Status

Das aktuelle System ist überkomplex geworden. Diese Spezifikation dient als Grundlage für eine **Neuimplementierung** mit Fokus auf:
1. **Einfachheit** - Weniger Features, bessere UX
2. **Stabilität** - Robuste Kern-Funktionen
3. **Wartbarkeit** - Sauberer, verständlicher Code

---

## 📁 Empfohlene Projektstruktur

Für eine wartbare, moderne Flask-Webanwendung mit den dokumentierten Features empfiehlt sich folgende Struktur:

```
mp3-tagger-web/
│
├── app.py                # Haupt-Flask-App (Entry Point)
├── requirements.txt      # Python-Abhängigkeiten
├── config.env            # Konfiguration & API-Keys
│
├── static/               # Statische Dateien (JS, CSS, Bilder)
│   ├── js/
│   ├── css/
│   └── img/
│
├── templates/            # HTML-Templates (Jinja2)
│   └── index.html
│
├── tagger/               # Backend-Logik (MP3-Tagging, Enrichment)
│   ├── __init__.py
│   ├── scanner.py        # Verzeichnis-Scan & Dateiname-Parsing
│   ├── id3.py            # ID3-Tag-Lesen/Schreiben
│   ├── cover.py          # Cover-Handling
│   ├── enrich.py         # Metadaten-Anreicherung (API-Services)
│   └── audio.py          # Audio-Fingerprinting (Shazam/AcoustID)
│
├── tests/                # (Optional) Unit- und Integrationstests
│   └── test_tagger.py
│
└── README.md             # Dokumentation & Workflow
```

**Vorteile:**
- Klare Trennung von Backend-Logik (`tagger/`), Web-UI (`templates/`, `static/`), und Konfiguration.
- Erweiterbar für neue Features.
- Einfaches Deployment und Testing.

Optional für größere Projekte:
- `instance/` für lokale Einstellungen
- `migrations/` für Datenbankmigrationen (falls später benötigt)




