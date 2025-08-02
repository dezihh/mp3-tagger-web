# Extended Metadata Setup - Spotify Web API

## Spotify Web API Konfiguration

Um die erweiterten Metadaten-Features (BPM, Energy, Danceability, etc.) zu nutzen, benötigen Sie Spotify Web API Credentials.

### 1. Spotify Developer Account erstellen

1. Gehen Sie zu: https://developer.spotify.com/dashboard
2. Loggen Sie sich mit Ihrem Spotify-Account ein
3. Klicken Sie auf "Create an App"
4. Geben Sie folgende Informationen ein:
   - **App Name**: MP3 Tagger Web Extended
   - **App Description**: Extended metadata collection for MP3 files
   - **Website**: http://localhost:5000
   - **Redirect URI**: http://localhost:5000/callback

### 2. API-Credentials erhalten

Nach dem Erstellen der App finden Sie:
- **Client ID**: Ihre eindeutige Client-ID
- **Client Secret**: Ihr geheimer Schlüssel (Show Client Secret klicken)

### 3. Konfiguration in config.env

Fügen Sie diese Zeilen zu Ihrer `config.env` hinzu:

```
SPOTIFY_CLIENT_ID=Ihre_Client_ID_hier
SPOTIFY_CLIENT_SECRET=Ihr_Client_Secret_hier
```

### 4. Verfügbare Extended Metadata

Mit aktivierter Spotify-Integration sammelt das System:

#### Von Spotify Web API:
- **BPM (Tempo)**: Beats per Minute
- **Energy**: Energie-Level (0.0-1.0)
- **Danceability**: Tanzbarkeit (0.0-1.0)
- **Valence**: Positivität/Fröhlichkeit (0.0-1.0)
- **Acousticness**: Akustik-Anteil (0.0-1.0)
- **Instrumentalness**: Instrumental-Anteil (0.0-1.0)
- **Liveness**: Live-Performance-Wahrscheinlichkeit (0.0-1.0)
- **Speechiness**: Sprach-Anteil (0.0-1.0)
- **Loudness**: Lautheit in dB
- **Key**: Tonart (0-11)
- **Mode**: Dur/Moll (0/1)
- **Time Signature**: Taktart

#### Von Last.fm API (bereits konfiguriert):
- **Genres**: Erweiterte Genre-Informationen
- **Mood/Tags**: Stimmungs-Tags
- **Ähnliche Künstler**: Top 5 ähnliche Künstler
- **Release-Datum**: Veröffentlichungsdatum

### 5. Testen der Funktionalität

1. Starten Sie die Anwendung: `./venv/bin/python app.py`
2. Laden Sie ein Verzeichnis mit MP3-Dateien
3. Wählen Sie einige Dateien aus
4. Klicken Sie auf "🎯 Erweiterte Metadaten"
5. Die gesammelten Metadaten werden in einem Dialog angezeigt

### 6. Fehlerbehebung

**Keine Spotify-Daten:**
- Prüfen Sie die Client ID und Secret
- Stellen Sie sicher, dass die MP3-Dateien Artist und Titel haben
- Spotify kann nicht alle Tracks finden (besonders lokale/seltene Musik)

**Nur Last.fm-Daten:**
- Last.fm funktioniert auch ohne Spotify-Konfiguration
- Weniger detaillierte Audio-Features, aber Genre und Mood-Informationen

**API-Rate-Limits:**
- Spotify: 100 Requests pro Sekunde
- Last.fm: 5 Requests pro Sekunde
- Bei großen Sammlungen kann es einige Zeit dauern

### 7. Datenschutz

- Keine persönlichen Spotify-Daten werden gespeichert
- Nur Track-bezogene Metadaten werden abgerufen
- Alle API-Calls erfolgen über die offizielle Spotify Web API
- Ihre Credentials bleiben lokal in der config.env
