# MP3 Tagger Desktop-Anwendung

Eine grafische Desktop-Anwendung zum Verwalten und Bearbeiten von MP3-Metadaten, basierend auf der Web-Version.

## 🚀 Schnellstart

### 1. Abhängigkeiten installieren
```bash
pip install mutagen Pillow requests
```

### 2. Anwendung starten
```bash
python start_desktop.py
```

Oder direkt:
```bash
python mp3_tagger_gui.py
```

## 📋 Features

### ✅ Grundfunktionen
- **Verzeichnis-Scan**: Automatisches Erkennen und Analysieren von MP3-Dateien
- **Metadaten-Anzeige**: Übersichtliche Tabellenansicht aller Dateien mit ID3-Tags
- **Einzeldatei-Editor**: Detaillierte Bearbeitung einzelner MP3-Dateien
- **Batch-Editor**: Gleichzeitige Bearbeitung mehrerer ausgewählter Dateien
- **Cover-Management**: Anzeige und Verwaltung von Album-Covern

### 🎛️ Benutzeroberfläche
- **Tab-basierte Navigation**: Übersichtliche Aufteilung in verschiedene Bereiche
- **Responsive Design**: Anpassbare Fenstergröße und Spaltenbreiten
- **Fortschrittsanzeigen**: Echzeit-Feedback bei längeren Operationen
- **Statusleiste**: Kontinuierliche Information über den aktuellen Zustand

### 📁 Dateiverwaltung
- **Flexible Auswahl**: Einzelne oder mehrere Dateien markieren
- **Sofortige Speicherung**: Direkte Anwendung von Änderungen
- **Fehlerbehandlung**: Robuste Verarbeitung problematischer Dateien

## 🏗️ Architektur

### Hauptkomponenten

#### `mp3_tagger_gui.py`
- Haupt-GUI-Klasse mit tkinter
- Tab-basierte Benutzeroberfläche
- Event-Handling und Threading

#### `tagger/desktop_mp3_processor.py`
- Desktop-spezifische Erweiterung des MP3Processors
- Fortschritts-Callbacks
- Batch-Verarbeitung

#### `tagger/metadata_editor.py`
- Dialog für Einzeldatei-Bearbeitung
- Batch-Editor für mehrere Dateien
- Validierung und Fehlerbehandlung

#### `tagger/desktop_config.py`
- Konfigurationsverwaltung
- API-Schlüssel aus config.env
- Persistente Einstellungen

### Datenfluss

1. **Verzeichnis-Auswahl** → Benutzer wählt Ordner mit MP3s
2. **Scanning** → Analyse aller MP3-Dateien im Hintergrund
3. **Anzeige** → Tabellarische Darstellung mit allen Metadaten
4. **Bearbeitung** → Einzeln oder als Batch über Dialoge
5. **Speicherung** → Direkte Anwendung auf die MP3-Dateien

## 🎨 Benutzeroberfläche

### Tab 1: MP3 Dateien
- **Dateitabelle**: Alle MP3s mit Metadaten
- **Toolbar**: Auswahl-Funktionen und Batch-Operationen
- **Doppelklick**: Öffnet Einzeldatei-Editor
- **Checkboxen**: Für Mehrfachauswahl

### Tab 2: Cover Management
- **Cover-Analyse**: Erkennung vorhandener Cover
- **Batch-Operationen**: Anwenden/Entfernen für ausgewählte Dateien
- **Cover-Quellen**: Liste aller gefundenen Cover mit Details

### Tab 3: Audio Recognition (Geplant)
- Integration von Shazam/AcoustID APIs
- Automatische Metadaten-Erkennung

### Tab 4: Metadata Enrichment (Geplant)
- MusicBrainz/Last.fm Integration
- Automatische Anreicherung

## 🔧 Konfiguration

### Einstellungen
Die Anwendung speichert Einstellungen in `~/.mp3tagger/`:
- `config.json`: Benutzereinstellungen
- `directory_history.json`: Verzeichnis-Verlauf
- `cache/`: Temporäre Dateien

### API-Konfiguration
Erstellen Sie `config.env` im Projektverzeichnis:
```env
# Shazam/RapidAPI
RAPIDAPI_KEY=your_rapidapi_key

# AcoustID
ACOUSTID_API_KEY=your_acoustid_key

# Last.fm
LASTFM_API_KEY=your_lastfm_key

# Discogs
DISCOGS_TOKEN=your_discogs_token

# Spotify
SPOTIFY_CLIENT_ID=your_spotify_id
SPOTIFY_CLIENT_SECRET=your_spotify_secret
```

## 💻 Entwicklung

### Code-Struktur
```
mp3-tagger-web/
├── mp3_tagger_gui.py          # Haupt-GUI
├── start_desktop.py           # Startskript
├── tagger/
│   ├── desktop_mp3_processor.py   # Desktop MP3-Verarbeitung
│   ├── metadata_editor.py         # Editor-Dialoge
│   ├── desktop_config.py          # Konfiguration
│   ├── cover_manager.py           # Cover-Verwaltung
│   ├── audio_recognition.py       # Audio-Erkennung
│   └── extended_metadata.py       # Metadaten-Anreicherung
└── config.env                # API-Konfiguration
```

### Threading-Konzept
- **Main Thread**: GUI und Benutzerinteraktion
- **Worker Threads**: Datei-Verarbeitung und API-Aufrufe
- **Callbacks**: Fortschritts-Updates zurück an GUI

### Fehlerbehandlung
- Robuste Verarbeitung defekter MP3-Dateien
- Detaillierte Fehlermeldungen für Benutzer
- Logging für Debugging

## 🔄 Migration von Web zu Desktop

### Vorteile der Desktop-Version
- **Keine Server-Abhängigkeit**: Läuft lokal ohne Browser
- **Bessere Performance**: Direkter Dateizugriff ohne HTTP
- **Native UI**: Plattform-spezifische Benutzeroberfläche
- **Offline-Fähig**: Funktioniert ohne Internetverbindung

### Übergangsphase
- Web-Version bleibt erhalten
- Schrittweise Migration der Features
- Gemeinsame `tagger/`-Module nutzen beide Versionen

## 📦 Ausführbare Datei erstellen (Optional)

Für eine standalone .exe/.app-Datei:

```bash
pip install pyinstaller
pyinstaller --onefile --windowed start_desktop.py
```

## 🐛 Bekannte Einschränkungen

- Cover-Management noch nicht vollständig implementiert
- Audio Recognition noch in Entwicklung
- Metadaten-Anreicherung in Planung
- Keine Undo/Redo-Funktion

## 🎯 Roadmap

### Version 1.1
- [ ] Vollständiges Cover-Management
- [ ] Audio Recognition Integration
- [ ] Erweiterte Metadaten-Validierung

### Version 1.2
- [ ] Metadaten-Anreicherung
- [ ] Plugin-System für Erweiterungen
- [ ] Erweiterte Batch-Operationen

### Version 2.0
- [ ] Multi-Format-Unterstützung (FLAC, M4A)
- [ ] Cloud-Synchronisation
- [ ] Erweiterte Audio-Analyse

## 📞 Support

Bei Problemen oder Fragen:
1. Prüfen Sie die Konsolen-Ausgaben
2. Überprüfen Sie die Log-Dateien in `~/.mp3tagger/`
3. Stellen Sie sicher, dass alle Abhängigkeiten installiert sind
