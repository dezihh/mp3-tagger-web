# MP## ✨ Haupt-Features

- **📁 Verzeichnis-Scanner**: Automatisches Erkennen aller MP3-Dateien
- **🎵 Audio-Vorhören**: Integrierter Audio-Player mit Play/Pause/Stop-Funktionen
- **📝 Inline-Editing**: Direkte Bearbeitung in der Tabelle
- **✅ Smart Checkboxes**: Automatische Auswahl bei Feldänderungen  
- **📊 Batch-Operationen**: Mehrere Dateien gleichzeitig bearbeiten
- **🎤 Audio-Erkennung**: Automatische Titel/Künstler-Erkennung via AcoustID/Shazam
- **🖼️ Cover-Management**: Cover anzeigen, laden und verwalten
- **🎯 Metadaten-Anreicherung**: Last.fm und MusicBrainz Integration
- **💾 Robuste Speicher-Funktionen**: Sichere Tag- und Cover-Speicherungesktop Application

Eine moderne Python-Desktop-Anwendung (tkinter) zur Verwaltung und Bearbeitung von MP3-Metadaten mit erweiterten Features wie Audio-Erkennung, Cover-Management und Metadaten-Anreicherung.

## ✨ Haupt-Features

- **� Verzeichnis-Scanner**: Automatisches Erkennen aller MP3-Dateien
- **📝 Inline-Editing**: Direkte Bearbeitung in der Tabelle
- **✅ Smart Checkboxes**: Automatische Auswahl bei Feldänderungen  
- **📊 Batch-Operationen**: Mehrere Dateien gleichzeitig bearbeiten
- **🎵 Audio-Erkennung**: Automatische Titel/Künstler-Erkennung via AcoustID/Shazam
- **🖼️ Cover-Management**: Cover anzeigen, laden und verwalten
- **🎯 Metadaten-Anreicherung**: Last.fm und MusicBrainz Integration
- **💾 Robuste Speicher-Funktionen**: Sichere Tag- und Cover-Speicherung

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

1. **Virtual Environment aktivieren**: `source venv/bin/activate`
2. **Anwendung starten**: `python start_desktop.py`
3. **Verzeichnis auswählen**: MP3-Verzeichnis über "Durchsuchen" Button wählen
4. **Dateien scannen**: Automatischer Scan aller MP3-Dateien mit Metadaten-Extraktion
5. **Audio-Vorhören**: MP3-Dateien über Rechtsklick → "🎵 Vorhören" oder Leertaste abspielen
6. **Audio-Erkennung** (optional): Buttons "Shazam" oder "AcoustID" für fehlende Tags
7. **Tags bearbeiten**: Direkte Bearbeitung in der Tabelle (Auto-Checkbox-Aktivierung)
8. **Batch-Speichern**: Ausgewählte Änderungen über "Speichern" Button sichern

## 🎵 Audio-Vorhören System

### **Integrierter Audio-Player**
- **Unterstützte Formate**: MP3-Dateien (pygame-basiert)
- **Steuerung**: Play/Pause/Stop-Buttons im Player-Widget
- **Position**: Fortschrittsbalken mit Seek-Funktionalität
- **Lautstärke**: Einstellbare Lautstärke von 0-100%
- **Echtzeitinfo**: Anzeige von aktueller Position und Gesamtdauer

### **Bedienung**
- **Rechtsklick-Menü**: "🎵 Vorhören" für ausgewählte Datei (startet automatisch)
- **Keyboard-Shortcuts**: 
  - `Leertaste`: Datei laden und automatisch abspielen
  - `Enter`: Play/Pause umschalten
- **Player-Widget**: Vollständige Kontrolle über Wiedergabe
- **Status-Anzeige**: Aktuelle Datei und Wiedergabe-Status in der Statusleiste

### **Desktop-spezifische Features**
- **Cover-Dialog**: Button "Cover anzeigen" öffnet Auswahl-Dialog mit Vorschau
- **Inline-Editing**: Doppelklick auf Zellen zur direkten Bearbeitung
- **Batch-Metadata-Editor**: Dialog für gemeinsame Änderungen an mehreren Dateien
- **Threading**: Alle zeitaufwändigen Operationen laufen im Hintergrund

## 🏗️ Architektur & Module

### **Desktop-Anwendung (Python/tkinter)**
- **`mp3_tagger_gui.py`**: Haupt-GUI mit tkinter-Interface und Event-Handling
- **`start_desktop.py`**: Startskript mit Dependency-Prüfung und Umgebungs-Setup

### **Backend-Module (Python)**
- **`tagger/audio_player.py`**: Audio-Player-Engine mit pygame für MP3-Wiedergabe
- **`tagger/audio_player_widget.py`**: GUI-Widget für Audio-Player-Steuerung
- **`tagger/desktop_mp3_processor.py`**: Desktop-spezifische MP3-Verarbeitung
- **`tagger/mp3_processor.py`**: Kern-MP3-Verarbeitung und Metadaten-Extraktion
- **`tagger/audio_recognition.py`**: Audio-Fingerprinting (AcoustID/Shazam)
- **`tagger/extended_metadata.py`**: Erweiterte Metadaten-Anreicherung (Last.fm, MusicBrainz)
- **`tagger/cover_manager.py`**: Cover-Erkennung, -Analyse und -Management
- **`tagger/metadata_editor.py`**: Batch-Metadata-Editor-Dialoge
- **`tagger/desktop_config.py`**: Desktop-spezifische Konfiguration
- **`tagger/utils.py`**: Grundlegende Utilities für MP3-Tag-Operationen
- **`tagger/http_client.py`**: Zentralisierte HTTP-Client-Utilities mit Rate-Limiting
- **`tagger/directory_history.py`**: Verzeichnis-Verlauf Management
### **Desktop-Workflow**
- **Verzeichnis-Auswahl**: File-Dialog oder manuelle Eingabe
- **Tabellen-Ansicht**: Eine Zeile pro MP3-Datei mit editierbaren Feldern
- **Checkbox-System**: Datei-Auswahl für Batch-Operationen
- **Threading**: Asynchrone Verarbeitung für Audio-Erkennung und Metadaten-Anreicherung
- **Dialoge**: Modal-Dialoge für Cover-Auswahl und Batch-Metadaten-Bearbeitung

### **Audio-Erkennung**
1. **Shazam-Integration**: Hochgenaue Musik-Erkennung über ShazamIO
2. **AcoustID-Erkennung**: MusicBrainz-basierte Metadaten-Zuordnung
3. **Asynchrone Verarbeitung**: Keine Blockierung der GUI
4. **Visuelle Kennzeichnung**: Erkannte Tags werden markiert dargestellt

**Bedienung**: Buttons "Shazam" oder "AcoustID" für ausgewählte Dateien

### **Metadaten-Anreicherung**
1. **Last.fm-Integration**: Zusätzliche Metadaten und Künstler-Informationen
2. **MusicBrainz-Abfrage**: Standardisierte Musik-Datenbank
3. **Batch-Verarbeitung**: Mehrere Dateien gleichzeitig verarbeiten
4. **Smart-Caching**: Vermeidung redundanter API-Calls

**Bedienung**: Buttons "Last.fm" oder "MusicBrainz" für ausgewählte Dateien

### **Cover-Management**
1. **Cover-Erkennung**: Automatische Detektion interner und externer Cover
2. **Cover-Dialog**: Vorschau und Auswahl verfügbarer Cover mit Thumbnail-Ansicht
3. **Cover-Operationen**: Laden, Entfernen, Ersetzen von Cover-Art
4. **Prioritäts-System**: Intelligente Auswahl zwischen internen und externen Covern

**Bedienung**: Buttons "Cover anzeigen", "Cover laden", "Cover entfernen"

### **Album-Erkennung**
1. **MusicBrainz-Integration**: Kostenlose, umfassende Musikdatenbank
2. **Discogs-Fallback**: Kommerzielle Musikdatenbank für erweiterte Informationen
3. **Konfidenz-Bewertung**: Nur Übereinstimmungen >70% werden automatisch angewendet
4. **Intelligente Zuordnung**: Automatische Track-Nummer-Extraktion aus Album-Informationen

**Bedienung**: Button "Album erkennen" für ausgewählte Dateien

### **Erweiterte Batch-Funktionen**
1. **Auto-Track-Nummerierung**: Automatische Vergabe von Track-Nummern (01, 02, 03...)
2. **Sortierung**: Alphabetische Reihenfolge basierend auf Dateinamen
3. **Format-Konsistenz**: Führende Nullen für einheitliche Darstellung
4. **Batch-Metadaten-Editor**: Gemeinsame Änderungen an mehreren Dateien

**Bedienung**: Button "Track-Nr." für automatische Nummerierung

---

### 1. Grundfunktionalität (Desktop)

**Tabellen-Interface:**
- Eine Zeile pro MP3-Datei mit editierbaren Spalten
- Spalten: Checkbox, Dateiname, Track-Nummer, Artist, Titel, Album, Genre, Cover-Status
- Doppelklick auf Zellen für Inline-Editing
- Aktuelles Verzeichnis wird in der Titelleiste angezeigt
- Intelligente Checkbox-Aktivierung bei Feldänderungen

**Datei-Auswahl:**
- Checkbox vor jeder MP3-Datei für individuelle Auswahl
- "Alle auswählen" / "Alle abwählen" Buttons
- Status-Anzeige für Anzahl ausgewählter Dateien

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

### 3. Bearbeitungsmodus (Desktop)

**Inline-Editing:**
- Doppelklick auf Zellen für direkte Bearbeitung
- Editierbare Felder: Artist, Titel, Album, Track-Nummer, Genre
- Enter zum Bestätigen, Escape zum Abbrechen
- Automatische Checkbox-Aktivierung bei Änderungen

**Batch-Metadaten-Editor:**
- Modal-Dialog für gemeinsame Änderungen an mehreren Dateien
- Auswahl der zu ändernden Felder über Checkboxes
- Vorschau der Änderungen vor Anwendung

**Track-Nummer-Management:**
- Automatische Formatierung mit führenden Nullen
- Intelligente Extraktion aus Dateinamen
- Konsistente Darstellung in der Tabelle

### 4. Erweiterte Funktionen (Desktop)

**Audio-Erkennung:**
- Separate Buttons für Shazam und AcoustID
- Asynchrone Verarbeitung im Hintergrund
- Progress-Feedback über Status-Bar
- Automatische Markierung erkannter Dateien

**Metadaten-Anreicherung:**
- Last.fm Integration für erweiterte Metadaten
- MusicBrainz für standardisierte Musikdatenbank-Informationen
- Batch-Verarbeitung für ausgewählte Dateien
- Intelligentes Caching zur Performance-Optimierung

**Cover-Management:**
- Cover-Auswahl-Dialog mit Thumbnail-Vorschau
- Unterstützung für interne und externe Cover
- Cover-Status-Anzeige: `I<px>`, `E<px>`, `B<px>`, `Nein`
- Cover-Operationen: Laden, Anzeigen, Entfernen

### 5. Speicher-Workflow (Desktop)

**Desktop-Speicher-Prozess:**
1. Dateien über Checkboxes markieren
2. "Speichern" Button in der Funktions-Toolbar
3. Asynchrone Verarbeitung mit Threading
4. Status-Updates über Status-Bar
5. Erfolgs-/Fehlermeldung über Message-Box

**Robuste Operationen:**
- Atomare Speicher-Operationen pro Datei
- Umfassende Fehlerbehandlung und Logging
- Backup-Mechanismen für kritische Operationen
- Thread-sichere GUI-Updates

## 🎨 UI/UX Philosophie (Desktop)

### Native Desktop-Experience
- Native tkinter-Widgets für plattformspezifisches Look-and-Feel
- Responsive Layout mit Grid- und Pack-Managern
- Modal-Dialoge für komplexe Interaktionen
- Keyboard-Shortcuts für häufige Aktionen

### Threading und Performance
- Asynchrone Verarbeitung für zeitaufwändige Operationen
- Non-blocking GUI für bessere Benutzererfahrung
- Intelligentes Caching zur Performance-Optimierung
- Effiziente Batch-Operationen

### Benutzerfreundlichkeit
- Intuitive Bedienung ohne Einarbeitung
- Klare visuelle Rückmeldungen über Status-Bar
- Fehlertolerante Eingabe mit Validierung
- Automatische Checkbox-Aktivierung bei Änderungen

## 🔧 Technische Anforderungen

### **Desktop-Entwicklungsumgebung**
```bash
# Virtuelles Environment erstellen und aktivieren
python -m venv venv
source venv/bin/activate  # Linux/Mac
# oder: venv\Scripts\activate  # Windows

# Abhängigkeiten installieren
pip install -r requirements.txt

# Desktop-Anwendung starten
python start_desktop.py
```

### **Abhängigkeiten**
- **Python 3.8+**: Basis-Interpreter
- **tkinter**: GUI-Framework (meist mit Python vorinstalliert)
- **mutagen**: MP3-Metadaten-Bearbeitung
- **Pillow (PIL)**: Bildverarbeitung für Cover
- **requests**: HTTP-Client für API-Calls
- **asyncio**: Asynchrone Verarbeitung
- **threading**: GUI-Threading für Non-blocking Operations

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
LASTFM_API_KEY=your_lastfm_key_here
MUSICBRAINZ_USERAGENT=YourAppName/1.0 (your@email.com)

# Optional: Erweiterte Services
DISCOGS_CONSUMER_KEY=your_discogs_key_here
DISCOGS_CONSUMER_SECRET=your_discogs_secret_here

# Desktop-spezifische Einstellungen
LOG_LEVEL=INFO
CACHE_DIR=./cache
BACKUP_ENABLED=True
```

**API-Key Beschaffung:**
- **AcoustID**: Registrierung auf https://acoustid.org/
- **Last.fm**: API-Key auf https://www.last.fm/api
- **MusicBrainz**: Keine Registrierung, nur User-Agent erforderlich
- **Shazam**: Keine API-Keys nötig (verwendet ShazamIO Python-Library)
- **Discogs**: Optional - Developer Account auf https://www.discogs.com/developers/

### **Desktop-Implementierungsstand**

**Kern-Features (✅ Vollständig implementiert):**
- ✅ Desktop-GUI mit tkinter
- ✅ Verzeichnis-Scanner mit File-Dialog
- ✅ MP3-Tabelle mit Inline-Editing
- ✅ Checkbox-System für Datei-Auswahl
- ✅ Cover-Status-Anzeige (intern/extern/beide/keine)
- ✅ Robuste Speicher-Funktionalität mit Threading
- ✅ Intelligentes Dateiname-Parsing für Track-Nummern

**Audio-Erkennung (✅ Vollständig implementiert):**
- ✅ Shazam-Integration mit ShazamIO
- ✅ AcoustID-Integration mit MusicBrainz
- ✅ Asynchrone Verarbeitung ohne GUI-Blocking
- ✅ Progress-Feedback über Status-Bar

**Metadaten-Anreicherung (✅ Vollständig implementiert):**
- ✅ Last.fm-Integration für erweiterte Metadaten
- ✅ MusicBrainz-Abfrage für standardisierte Informationen
- ✅ Batch-Verarbeitung für markierte Dateien
- ✅ HTTP-Client mit Rate-Limiting

**Cover-Management (✅ Vollständig implementiert):**
- ✅ Cover-Erkennung und Analyse
- ✅ Cover-Auswahl-Dialog mit Vorschau
- ✅ Cover-Operationen (Laden, Entfernen, Anzeigen)
- ✅ Unterstützung für interne und externe Cover

**Album-Erkennung (✅ NEU implementiert):**
- ✅ MusicBrainz und Discogs Integration
- ✅ Intelligente Album-Kandidaten-Suche
- ✅ Konfidenz-basierte Auswahl (>70% Übereinstimmung)
- ✅ Automatische Album-Metadaten-Zuordnung

**Erweiterte Features (✅ Vollständig implementiert):**
- ✅ Batch-Metadaten-Editor-Dialog
- ✅ Automatische Track-Nummerierung für ausgewählte Dateien
- ✅ Automatische Checkbox-Aktivierung bei Änderungen
- ✅ Thread-sichere GUI-Updates
- ✅ Umfassende Fehlerbehandlung und Logging

## 🚫 Bewusst einfach gehalten

- Keine komplexen Playlist-Funktionen oder Audio-Player
- Keine automatische Datei-Organisation/Umbenennung
- Keine persistente Datenbank (Filesystem-basiert)
- Keine Netzwerk-Features oder Multi-User-Support
- Fokus auf MP3-Metadaten-Bearbeitung als Kern-Funktionalität

---

## 🎯 Projektphilosophie

Das System wurde als **native Desktop-MP3-Tagging-Lösung** entwickelt mit Priorität auf:

1. **Native Desktop-Experience** - tkinter für plattformspezifisches Look-and-Feel
2. **Performance** - Asynchrone Verarbeitung und Thread-sichere GUI-Updates  
3. **Stabilität** - Robuste Kern-Funktionen mit umfassendem Error-Handling
4. **Wartbarkeit** - Saubere, modulare Architektur für einfache Erweiterung

---

## 📁 Aktuelle Projektstruktur

```
mp3-tagger-web/
│
├── mp3_tagger_gui.py            # Haupt-Desktop-GUI-Anwendung
├── start_desktop.py             # Startskript mit Dependency-Checks
├── requirements.txt             # Python-Abhängigkeiten
├── config.env                   # Konfiguration & API-Keys
├── directory_history.json       # Verzeichnis-Verlauf (auto-generiert)
│
├── tagger/                      # Backend-Kern-Module
│   ├── __init__.py             # Package-Initialisierung
│   ├── desktop_mp3_processor.py # Desktop-spezifische MP3-Verarbeitung
│   ├── mp3_processor.py        # Kern-MP3-Verarbeitung & Metadaten
│   ├── cover_manager.py        # Cover-Erkennung und -Management
│   ├── audio_recognition.py    # Audio-Fingerprinting (AcoustID/Shazam)
│   ├── extended_metadata.py    # Metadaten-Anreicherung (Last.fm/MusicBrainz)
│   ├── metadata_editor.py      # Batch-Metadaten-Editor-Dialoge
│   ├── desktop_config.py       # Desktop-spezifische Konfiguration
│   ├── utils.py                # Grundlegende MP3-Tag-Operationen
│   ├── http_client.py          # HTTP-Client mit Rate-Limiting
│   └── directory_history.py    # Verzeichnis-Verlauf Management
│
└── test_music/                  # Test-MP3-Dateien (für Development)
```

**Desktop-Architektur-Vorteile:**
- **Native GUI**: Plattformspezifisches Look-and-Feel mit tkinter
- **Thread-sicher**: Asynchrone Verarbeitung ohne GUI-Blocking  
- **Modulare Struktur**: Klare Trennung zwischen GUI und Business-Logic
- **Deployment-ready**: Alle Abhängigkeiten klar definiert, keine Web-Server nötig




