# MP3-Tagger Modulare Architektur - Dokumentation

## Überblick

Die MP3-Tagger Anwendung wurde erfolgreich in modulare, wiederverwendbare Komponenten aufgeteilt. Jedes Modul kann unabhängig verwendet werden und bietet sowohl Klassen-basierte als auch Standalone-Funktionen.

## Module-Struktur

### 1. `tagger/metadata_enrichment.py`
**Zweck**: Intelligente Anreicherung von MP3-Metadaten mit Online-Services

**Klassen**:
- `MetadataEnrichmentService`: Hauptservice für Metadaten-Anreicherung

**Standalone-Funktionen**:
```python
from tagger.metadata_enrichment import enrich_file_metadata, enrich_multiple_files

# Einzelne Datei anreichern
result = enrich_file_metadata(file_data)

# Mehrere Dateien anreichern
results = enrich_multiple_files(files_data)
```

**Features**:
- Intelligente Fallback-Hierarchie (Pfad-Analyse → Online-Suche → Audio-Fingerprinting)
- Automatische Erkennung aussagekräftiger Dateinamen
- Erweiterte Cover-Suche für alle Dateitypen
- Cover-URL-Erhaltung von Audio-Services

### 2. `tagger/audio_recognition.py`
**Zweck**: Audio-Erkennung über ShazamIO und AcoustID

**Klassen**:
- `AudioRecognitionService`: Dual-Service Audio-Erkennung

**Standalone-Funktionen**:
```python
from tagger.audio_recognition import (
    recognize_audio_file, 
    recognize_with_shazam, 
    recognize_with_acoustid
)

# Vollständige Audio-Erkennung (ShazamIO + AcoustID Fallback)
result = recognize_audio_file('/path/to/audio.mp3')

# Nur ShazamIO
result = recognize_with_shazam('/path/to/audio.mp3')

# Nur AcoustID
result = recognize_with_acoustid('/path/to/audio.mp3')
```

**Features**:
- Primärer Service: ShazamIO (hohe Konfidenz, Cover-URLs, Streaming-Links)
- Fallback-Service: AcoustID (MusicBrainz-Integration)
- Async/Await-Support für optimale Performance
- Confidence-basierte Service-Auswahl
- Streaming-Platform-Integration (Spotify, YouTube, Deezer)

### 3. `tagger/fingerprinting.py`
**Zweck**: Audio-Fingerprinting und Feature-Extraktion

**Klassen**:
- `AudioFingerprintService`: Audio-Fingerprinting Funktionalitäten

**Standalone-Funktionen**:
```python
from tagger.fingerprinting import (
    get_audio_fingerprint_metadata,
    create_audio_fingerprint,
    extract_audio_features,
    compare_audio_files
)

# Metadaten über Fingerprinting
meta = get_audio_fingerprint_metadata('/path/to/audio.mp3')

# Reinen Fingerprint erstellen
fp = create_audio_fingerprint('/path/to/audio.mp3')

# Audio-Features extrahieren
features = extract_audio_features('/path/to/audio.mp3')

# Zwei Audio-Dateien vergleichen
similarity = compare_audio_files('/path/file1.mp3', '/path/file2.mp3')
```

**Features**:
- AcoustID-Fingerprint-Erstellung (fpcalc)
- Audio-Feature-Extraktion (ffprobe)
- Audio-Segment-Erstellung für bessere Erkennung
- Fingerprint-Vergleich zwischen Dateien
- Temporäre Datei-Verwaltung

### 4. `tagger/core.py` (Refactored)
**Zweck**: Hauptanwendungslogik und MP3-Verarbeitung

**Klassen**:
- `MusicTagger`: Hauptklasse mit vereinfachter Architektur

**Features**:
- Verzeichnis-Scanning für MP3-Dateien
- Integration der modularen Services
- ID3-Tag-Verarbeitung und -Anwendung
- Cover-Art-Verarbeitung
- Metadaten-Formatierung für UI

## Verwendungsbeispiele

### Einfache Metadaten-Anreicherung
```python
from tagger.metadata_enrichment import enrich_file_metadata

file_data = {
    'path': '/path/to/song.mp3',
    'filename': 'song.mp3',
    'current_artist': 'Artist',
    'current_title': 'Title'
}

enriched = enrich_file_metadata(file_data)
print(f"Gefunden: {enriched['suggested_artist']} - {enriched['suggested_title']}")
```

### Audio-Erkennung ohne Metadaten
```python
from tagger.audio_recognition import recognize_audio_file

result = recognize_audio_file('/path/to/unknown.mp3')
if result:
    print(f"Erkannt: {result['artist']} - {result['title']}")
    print(f"Service: {result['service']}")
    print(f"Confidence: {result['confidence']}")
```

### Audio-Features extrahieren
```python
from tagger.fingerprinting import extract_audio_features

features = extract_audio_features('/path/to/audio.mp3')
print(f"Dauer: {features['duration']} Sekunden")
print(f"Bitrate: {features['bitrate']} bps")
print(f"Sample Rate: {features['sample_rate']} Hz")
```

## Flask-Integration

Die modularen Services sind nahtlos in die Flask-Anwendung integriert:

```python
# app.py
from tagger.core import MusicTagger
from tagger.metadata_enrichment import enrich_multiple_files
from tagger.audio_recognition import recognize_audio_file

# Hauptanwendung verwendet die refactored MusicTagger Klasse
tagger = MusicTagger()
enhanced_files = tagger.get_metadata_for_files(files_data)

# Module können auch direkt verwendet werden
enriched = enrich_multiple_files(files_data)
audio_result = recognize_audio_file('/path/to/audio.mp3')
```

## Intelligente Fallback-Hierarchie

Die Metadaten-Anreicherung verwendet eine optimierte Fallback-Kette:

1. **Pfad-Analyse**: Erkennt "Artist - Album" Struktur in Verzeichnispfaden
2. **Aussagekräftige Dateinamen**: Extrahiert "Artist - Title" aus Dateinamen
3. **Online-Metadaten-Suche**: MusicBrainz + Last.fm für ID3-getaggte Dateien
4. **Audio-Fingerprinting**: ShazamIO + AcoustID für unbekannte Dateien
5. **Erweiterte Cover-Suche**: Audio-Services wenn MusicBrainz keine Cover hat

## Vorteile der Modularisierung

### ✅ **Flexibilität**
- Jedes Modul kann unabhängig verwendet werden
- Einfache Integration in andere Projekte
- Standalone-Funktionen für schnelle Verwendung

### ✅ **Wartbarkeit**
- Klare Trennung der Verantwortlichkeiten
- Einfache Erweiterung und Debugging
- Unabhängige Tests für jedes Modul

### ✅ **Wiederverwendbarkeit**
- Module können in anderen Audio-Anwendungen verwendet werden
- Konsistente API-Design
- Gut dokumentierte Funktionen

### ✅ **Performance**
- Lazy Loading um zirkuläre Abhängigkeiten zu vermeiden
- Optimierte Fallback-Strategien
- Async/Await-Support wo sinnvoll

## Test-Skripte

### `test_modular_functions.py`
Umfassende Tests aller modularen Funktionen mit echten Audio-Dateien.

### `examples_modular_usage.py`
Praktische Verwendungsbeispiele für jedes Modul.

## Konfiguration

Alle Module verwenden die gleichen Umgebungsvariablen aus `config.env`:
- `ACOUSTID_API_KEY`: AcoustID API-Schlüssel
- `LASTFM_API_KEY`: Last.fm API-Schlüssel
- `MUSICBRAINZ_USERAGENT`: MusicBrainz User Agent

## Web-Service

Der Flask-Server ist verfügbar unter: **http://127.0.0.1:5000**

Die Web-Anwendung nutzt automatisch alle modularen Services und bietet:
- Verzeichnis-basierte MP3-Verarbeitung
- Intelligente Metadaten-Anreicherung
- Audio-Fingerprinting für unbekannte Dateien
- Cover-Art-Integration
- Streaming-Platform-Links

---

## Fazit

Die Modularisierung des MP3-Taggers ist erfolgreich abgeschlossen. Das System bietet jetzt:

1. **Separierte, wiederverwendbare Module** für verschiedene Funktionalitäten
2. **Standalone-Funktionen** für einfache Integration
3. **Intelligente Fallback-Strategien** für optimale Ergebnisse
4. **Vollständige Flask-Integration** mit allen Features
5. **Umfassende Tests und Beispiele** für die Verwendung

Die Module können flexibel einzeln oder zusammen verwendet werden und bieten eine solide Grundlage für erweiterte Audio-Metadaten-Verarbeitung.
