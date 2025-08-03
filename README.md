# MP3 Tagger Web Application

Eine moderne, webbasierte Anwendung zur Verwaltung und Bearbeitung von MP3-Metadaten mit erweiterten Features wie Hover-Tooltips, Batch-Bearbeitung und automatischen Checkbox-Aktivierung.

## ✨ Haupt-Features

- **🔍 Hover-Tooltips**: Detaillierte MP3-Informationen bei Dateiname-Hover
- **📝 Batch-Bearbeitung**: Mehrere Dateien gleichzeitig bearbeiten
- **✅ Smart Checkboxes**: Automatische Aktivierung bei Feldänderungen  
- **📊 Progress-Bar**: Visuelles Feedback beim Speichern ohne störende Dialoge
- **🎵 Audio-Preview**: Integrierte MP3-Wiedergabe
- **🖼️ Cover-Anzeige**: Pixelauflösung und Thumbnail-Vorschau
- **📱 Responsive Design**: Optimiert für verschiedene Bildschirmgrößen
- **🎯 Audio-Erkennung**: Automatische Titel- und Künstler-Erkennung via AcoustID/Shazam

## 🎼 Audio-Erkennung System

### **Zwei-Stufen-Erkennung**
1. **AcoustID (Primär)**: Hochgenaue Fingerprint-basierte Erkennung
2. **Shazam (Fallback)**: Zusätzliche Erkennung wenn AcoustID fehlschlägt

### **Intelligente Verarbeitung**
- **Bedarfserkennung**: Nur Dateien ohne Titel oder Künstler werden verarbeitet
- **Visuelle Kennzeichnung**: Erkannte Tags werden kursiv und grün markiert dargestellt
- **Nicht-destruktiv**: Erkannte Werte werden erst bei manuellem Speichern übernommen
- **Caching**: Bereits erkannte Dateien werden zwischengespeichert

## 🚀 Schnellstart

1. **Verzeichnis auswählen**: MP3-Verzeichnis auf der Startseite eingeben
2. **Dateien scannen**: Automatischer Scan aller MP3-Dateien mit Metadaten-Extraktion
3. **Audio-Erkennung** (optional): Button "� Audio-Erkennung" für fehlende Tags
4. **Tags bearbeiten**: Direkte Bearbeitung in der Tabelle (Auto-Checkbox-Aktivierung)
5. **Batch-Speichern**: Ausgewählte Änderungen mit Progress-Bar speichern

### **Audio-Erkennung verwenden**
- **Automatische Erkennung**: Dateien ohne Titel/Künstler werden automatisch identifiziert
- **Ein-Klick-Start**: Button "🎵 Audio-Erkennung" startet Batch-Verarbeitung
- **Erkannte Tags**: Werden kursiv und grün markiert angezeigt
- **Speichern**: Erkannte Werte werden erst beim manuellen Speichern übernommen

## 🏗️ Architektur & Module

### **Frontend (HTML/CSS/JavaScript)**
- **`templates/index.html`**: Hauptseite mit Verzeichnisauswahl
- **`templates/results.html`**: Optimierte Ergebnisansicht mit modularem JavaScript und Progress-Tracking
- **`static/styles.css`**: Moderne CSS-Datei mit Responsive Design
- **`static/utils.js`**: JavaScript-Utilities für UI-Interaktionen

### **Backend (Python/Flask)**
- **`app.py`**: Flask-Anwendung mit API-Endpoints und Workflow-Orchestrierung
- **`tagger/mp3_processor.py`**: Kern-MP3-Verarbeitung und Metadaten-Extraktion
- **`tagger/utils.py`**: Grundlegende Utilities für MP3-Tag-Operationen
- **`tagger/extended_metadata.py`**: Erweiterte Metadaten-Anreicherung (Spotify, Last.fm)
- **`tagger/audio_recognition.py`**: Audio-Fingerprinting (AcoustID/Shazam)
- **`tagger/album_recognition.py`**: Album-Erkennung mit Progress-Tracking
- **`tagger/http_client.py`**: Zentralisierte HTTP-Client-Utilities mit Rate-Limiting
- **`tagger/directory_history.py`**: Verzeichnis-Verlauf Management
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

### **Entwicklungsumgebung**
```bash
# Virtuelles Environment erstellen und aktivieren
python -m venv venv
source venv/bin/activate  # Linux/Mac
# oder: venv\Scripts\activate  # Windows

# Abhängigkeiten installieren
pip install -r requirements.txt

# Server starten (Standard Port 5000)
python app.py
```

### **API-Services und Konfiguration**

**Verwendete Dienste für Metadaten-Anreicherung:**
- **AcoustID**: Audio-Fingerprinting (kostenlos, API-Key erforderlich)
- **Shazam**: Audio-Fingerprinting Alternative (über ShazamIO, kein API-Key nötig)
- **MusicBrainz**: Metadaten-Datenbank (kostenlos, User-Agent erforderlich)
- **Discogs**: Release-Informationen und Cover (API-Key erforderlich)
- **Spotify**: Metadaten und Cover-Art (API-Key erforderlich)
- **Last.fm**: Genre und Zusatz-Informationen (API-Key erforderlich)

**Konfiguration in `config.env`:**
```bash
# Audio-Fingerprinting
ACOUSTID_API_KEY=your_acoustid_key_here

# Metadaten-Services  
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
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
- **Spotify**: App registrieren auf https://developer.spotify.com/
- **Last.fm**: API-Key auf https://www.last.fm/api
- **Discogs**: Developer Account auf https://www.discogs.com/developers/
- **MusicBrainz**: Keine Registrierung, nur User-Agent erforderlich
- **Shazam**: Keine API-Keys nötig (verwendet ShazamIO Python-Library)

### **Aktueller Implementierungsstand**

**Kern-Features (✅ Vollständig implementiert):**
- ✅ Verzeichnis scannen und MP3s anzeigen
- ✅ ID3-Metadaten bearbeiten mit automatischer Checkbox-Aktivierung
- ✅ Cover-Status anzeigen (intern/extern/beide/keine)
- ✅ Robuste Speichern-Funktionalität mit Fehlerbehandlung
- ✅ Intelligentes Dateiname-Parsing für Track-Nummern
- ✅ Progress-Tracking für alle Operationen

**Erweiterte Features (✅ Vollständig implementiert):**
- ✅ Audio-Erkennung (AcoustID/Shazam) mit Progress-Feedback
- ✅ Album-Erkennung (MusicBrainz/Discogs) mit detailliertem Progress
- ✅ Erweiterte Metadaten-Anreicherung (Spotify, Last.fm)
- ✅ Hover-Details für MP3-Informationen
- ✅ Batch-Operationen für markierte Dateien
- ✅ HTTP-Client mit Rate-Limiting für alle API-Services

**Code-Qualität (✅ Optimiert):**
- ✅ Konsolidierte HTTP-Client-Utilities
- ✅ Entfernung von orphaned Code und redundanten Dateien
- ✅ Verbesserte Fehlerbehandlung und Logging
- ✅ Modulare Architektur für bessere Wartbarkeit

## 🚫 Bewusst einfach gehalten

- Keine komplexen Cover-Management-Dialoge
- Keine Playlist-Funktionen im Audio-Player
- Keine automatische Datei-Organisation/Umbenennung
- Keine Benutzer-Accounts oder Sessions
- Keine persistente Datenbank (Filesystem-basiert)

---

## 🎯 Projektphilosophie

Das System wurde bewusst als **schlanke, fokussierte MP3-Tagging-Lösung** entwickelt mit Priorität auf:

1. **Einfachheit** - Intuitive Bedienung ohne steile Lernkurve
2. **Stabilität** - Robuste Kern-Funktionen mit umfassendem Error-Handling  
3. **Wartbarkeit** - Saubere, modulare Architektur für einfache Erweiterung
4. **Performance** - Effiziente Batch-Operationen mit Progress-Feedback

---

## 📁 Aktuelle Projektstruktur

```
mp3-tagger-web/
│
├── app.py                       # Flask-Hauptanwendung mit API-Endpoints
├── requirements.txt             # Python-Abhängigkeiten
├── config.env                   # Konfiguration & API-Keys
├── directory_history.json       # Verzeichnis-Verlauf (auto-generiert)
│
├── static/                      # Frontend-Assets
│   ├── styles.css              # Moderne CSS mit Responsive Design
│   ├── utils.js                # JavaScript-Utilities
│   ├── drag-drop-icon.svg      # UI-Icons
│   └── fallback-icon.png       # Fallback-Grafiken
│
├── templates/                   # Jinja2-Templates
│   ├── index.html              # Startseite mit Verzeichnisauswahl
│   └── results.html            # Hauptansicht mit MP3-Tabelle
│
├── tagger/                      # Backend-Kern-Module
│   ├── __init__.py             # Package-Initialisierung
│   ├── mp3_processor.py        # MP3-Verarbeitung & Metadaten-Extraktion
│   ├── utils.py                # Grundlegende MP3-Tag-Operationen
│   ├── audio_recognition.py    # Audio-Fingerprinting (AcoustID/Shazam)
│   ├── album_recognition.py    # Album-Erkennung mit Progress-Tracking
│   ├── extended_metadata.py    # Metadaten-Anreicherung (Spotify/Last.fm)
│   ├── http_client.py          # HTTP-Client mit Rate-Limiting
│   └── directory_history.py    # Verzeichnis-Verlauf Management
│
└── test_music/                  # Test-MP3-Dateien (für Development)
```

**Architektur-Vorteile:**
- **Modulare Trennung**: Klare Separation zwischen Web-UI, Business-Logic und API-Services
- **Skalierbar**: Neue Features können als separate Module hinzugefügt werden  
- **Testbar**: Isolierte Module ermöglichen einfaches Unit-Testing
- **Deployment-ready**: Alle Abhängigkeiten klar definiert und containerisierbar




