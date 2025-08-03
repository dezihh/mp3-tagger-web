"""
Extended Metadata Service für MP3 Tagger Web Application

Sammelt erweiterte ID3-Tags von Last.fm und Spotify:
- Veröffentlichungsdatum, BPM, Genre-Details
- Mood, Energy, Danceability, Valence
- Ähnliche Künstler, Audio-Features
- Erweiterte Genre-Informationen

APIs:
- Last.fm: Genre-Tags, ähnliche Künstler, Mood-Informationen
- Spotify Web API: Audio-Features (BPM, Energy, etc.)

Verwendung:
    from tagger.extended_metadata import ExtendedMetadataService
    
    service = ExtendedMetadataService()
    metadata = await service.get_track_metadata('Artist', 'Title', 'Album')
    
    # Ergebnis enthält alle verfügbaren erweiterten Metadaten
    if metadata.success:
        bpm = metadata.audio_features.get('tempo')
        genres = metadata.genres
        similar_artists = metadata.similar_artists
"""

import os
import asyncio
import aiohttp
import logging
import base64
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime

# Logging-Setup
logger = logging.getLogger(__name__)


@dataclass
class AudioFeatures:
    """Audio-Features von Spotify Web API"""
    tempo: Optional[float] = None  # BPM
    energy: Optional[float] = None  # 0.0-1.0
    danceability: Optional[float] = None  # 0.0-1.0
    valence: Optional[float] = None  # 0.0-1.0 (Positivität)
    acousticness: Optional[float] = None  # 0.0-1.0
    instrumentalness: Optional[float] = None  # 0.0-1.0
    liveness: Optional[float] = None  # 0.0-1.0
    speechiness: Optional[float] = None  # 0.0-1.0
    loudness: Optional[float] = None  # dB
    key: Optional[int] = None  # Tonart (0-11)
    mode: Optional[int] = None  # Dur/Moll (0/1)
    time_signature: Optional[int] = None  # Taktart


@dataclass
class ExtendedMetadata:
    """Sammlung aller erweiterten Metadaten"""
    success: bool = False
    source: str = ""
    
    # Basis-Informationen
    release_date: Optional[str] = None
    genres: List[str] = field(default_factory=list)
    extended_genres: List[str] = field(default_factory=list)
    
    # Mood und Charakteristika
    mood: List[str] = field(default_factory=list)
    similar_artists: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    
    # Audio-Features
    audio_features: AudioFeatures = field(default_factory=AudioFeatures)
    
    # Cover-Art Informationen
    cover_url: Optional[str] = None
    cover_urls: Dict[str, str] = field(default_factory=dict)  # verschiedene Größen
    
    # Zusätzliche Informationen
    popularity: Optional[int] = None
    explicit: Optional[bool] = None
    album_type: Optional[str] = None  # album, single, compilation
    
    # Metadaten
    collected_at: str = field(default_factory=lambda: datetime.now().isoformat())
    sources_used: List[str] = field(default_factory=list)
    collected_at: str = field(default_factory=lambda: datetime.now().isoformat())
    sources_used: List[str] = field(default_factory=list)


class SpotifyService:
    """Spotify Web API Service für Audio-Features"""
    
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None
        self.token_expires_at = None
        
    async def get_access_token(self) -> Optional[str]:
        """Holt neuen Access Token von Spotify"""
        if (self.access_token and self.token_expires_at and 
            datetime.now().timestamp() < self.token_expires_at):
            return self.access_token
            
        auth_string = base64.b64encode(
            f"{self.client_id}:{self.client_secret}".encode()
        ).decode()
        
        headers = {
            'Authorization': f'Basic {auth_string}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        data = {'grant_type': 'client_credentials'}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    'https://accounts.spotify.com/api/token',
                    headers=headers,
                    data=data
                ) as response:
                    if response.status == 200:
                        token_data = await response.json()
                        self.access_token = token_data['access_token']
                        self.token_expires_at = (
                            datetime.now().timestamp() + token_data['expires_in'] - 60
                        )
                        return self.access_token
        except Exception as e:
            logger.error(f"Spotify Token-Fehler: {e}")
            
        return None
    
    async def search_track(self, artist: str, title: str, album: str = None) -> Optional[str]:
        """Sucht Track bei Spotify und gibt Track-ID zurück"""
        token = await self.get_access_token()
        if not token:
            return None
            
        # Such-Query erstellen
        query_parts = [f'track:"{title}"', f'artist:"{artist}"']
        if album:
            query_parts.append(f'album:"{album}"')
        query = ' '.join(query_parts)
        
        headers = {'Authorization': f'Bearer {token}'}
        params = {
            'q': query,
            'type': 'track',
            'limit': 1
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    'https://api.spotify.com/v1/search',
                    headers=headers,
                    params=params
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        tracks = data.get('tracks', {}).get('items', [])
                        if tracks:
                            return tracks[0]['id']
        except Exception as e:
            logger.error(f"Spotify Suche-Fehler: {e}")
            
        return None
    
    async def get_track_details(self, track_id: str) -> Optional[Dict[str, Any]]:
        """Holt Track-Details inklusive Album-Cover von Spotify"""
        token = await self.get_access_token()
        if not token:
            return None
            
        headers = {'Authorization': f'Bearer {token}'}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f'https://api.spotify.com/v1/tracks/{track_id}',
                    headers=headers
                ) as response:
                    if response.status == 200:
                        return await response.json()
        except Exception as e:
            logger.error(f"Spotify Track-Details-Fehler: {e}")
            
        return None

    async def get_audio_features(self, track_id: str) -> Optional[AudioFeatures]:
        """Holt Audio-Features für einen Track"""
        token = await self.get_access_token()
        if not token:
            return None
            
        headers = {'Authorization': f'Bearer {token}'}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f'https://api.spotify.com/v1/audio-features/{track_id}',
                    headers=headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return AudioFeatures(
                            tempo=data.get('tempo'),
                            energy=data.get('energy'),
                            danceability=data.get('danceability'),
                            valence=data.get('valence'),
                            acousticness=data.get('acousticness'),
                            instrumentalness=data.get('instrumentalness'),
                            liveness=data.get('liveness'),
                            speechiness=data.get('speechiness'),
                            loudness=data.get('loudness'),
                            key=data.get('key'),
                            mode=data.get('mode'),
                            time_signature=data.get('time_signature')
                        )
        except Exception as e:
            logger.error(f"Spotify Audio-Features-Fehler: {e}")
            
        return None


class LastFmExtendedService:
    """Erweiterte Last.fm API für Metadaten"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "http://ws.audioscrobbler.com/2.0/"
    
    async def get_track_info(self, artist: str, title: str) -> Dict[str, Any]:
        """Holt erweiterte Track-Informationen von Last.fm"""
        params = {
            'method': 'track.getInfo',
            'api_key': self.api_key,
            'artist': artist,
            'track': title,
            'format': 'json'
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.base_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('track', {})
        except Exception as e:
            logger.error(f"Last.fm Track-Info-Fehler: {e}")
            
        return {}
    
    async def get_artist_similar(self, artist: str) -> List[str]:
        """Holt ähnliche Künstler von Last.fm"""
        params = {
            'method': 'artist.getSimilar',
            'api_key': self.api_key,
            'artist': artist,
            'limit': 10,
            'format': 'json'
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.base_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        similar = data.get('similarartists', {}).get('artist', [])
                        return [a['name'] for a in similar[:5]]  # Top 5
        except Exception as e:
            logger.error(f"Last.fm Similar-Artists-Fehler: {e}")
            
        return []
    
    async def get_album_info(self, artist: str, album: str) -> Dict[str, Any]:
        """Holt Album-Informationen von Last.fm"""
        params = {
            'method': 'album.getInfo',
            'api_key': self.api_key,
            'artist': artist,
            'album': album,
            'format': 'json'
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.base_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('album', {})
        except Exception as e:
            logger.error(f"Last.fm Album-Info-Fehler: {e}")
            
        return {}


class ExtendedMetadataService:
    """Hauptservice für erweiterte Metadaten-Sammlung"""
    
    def __init__(self):
        # Config aus config.env laden
        self._load_config()
        
        self.lastfm_key = os.getenv('LASTFM_API_KEY')
        self.spotify_client_id = os.getenv('SPOTIFY_CLIENT_ID')
        self.spotify_client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
        
        # Services initialisieren
        self.lastfm = LastFmExtendedService(self.lastfm_key) if self.lastfm_key else None
        self.spotify = SpotifyService(
            self.spotify_client_id, self.spotify_client_secret
        ) if self.spotify_client_id and self.spotify_client_secret else None
        
        # Cache für API-Anfragen
        self.cache = {}
    
    def _load_config(self):
        """Lädt Konfiguration aus config.env"""
        try:
            # Pfad zur config.env Datei
            config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.env')
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            os.environ[key.strip()] = value.strip()
                logger.info(f"Konfiguration geladen aus {config_path}")
            else:
                logger.warning(f"Config-Datei nicht gefunden: {config_path}")
        except Exception as e:
            logger.error(f"Fehler beim Laden der Konfiguration: {e}")
    
    async def get_track_metadata(self, artist: str, title: str, album: str = None) -> ExtendedMetadata:
        """
        Sammelt alle verfügbaren erweiterten Metadaten für einen Track
        
        Args:
            artist: Künstlername
            title: Track-Titel
            album: Album-Name (optional)
            
        Returns:
            ExtendedMetadata mit allen gesammelten Informationen
        """
        metadata = ExtendedMetadata()
        cache_key = f"{artist}|{title}|{album or ''}"
        
        # Cache prüfen
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # Parallel alle Services abfragen
        tasks = []
        
        if self.lastfm:
            tasks.append(self._collect_lastfm_data(metadata, artist, title, album))
            
        if self.spotify:
            tasks.append(self._collect_spotify_data(metadata, artist, title, album))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
            metadata.success = True
        
        # Ergebnis cachen
        self.cache[cache_key] = metadata
        return metadata
    
    async def _collect_lastfm_data(self, metadata: ExtendedMetadata, artist: str, title: str, album: str = None):
        """Sammelt Daten von Last.fm"""
        try:
            # Track-Informationen
            track_info = await self.lastfm.get_track_info(artist, title)
            if track_info:
                metadata.sources_used.append('lastfm')
                
                # Tags als Genres und Moods verwenden
                tags = track_info.get('toptags', {}).get('tag', [])
                if isinstance(tags, list):
                    tag_names = [tag['name'] for tag in tags]
                    
                    # Genre-Tags identifizieren
                    genre_keywords = ['rock', 'pop', 'jazz', 'blues', 'country', 'electronic', 'hip hop', 'rap', 'classical']
                    mood_keywords = ['chill', 'upbeat', 'melancholy', 'energetic', 'relaxing', 'dark', 'happy', 'sad']
                    
                    for tag in tag_names:
                        tag_lower = tag.lower()
                        if any(keyword in tag_lower for keyword in genre_keywords):
                            metadata.extended_genres.append(tag)
                        elif any(keyword in tag_lower for keyword in mood_keywords):
                            metadata.mood.append(tag)
                        else:
                            metadata.tags.append(tag)
            
            # Ähnliche Künstler
            similar = await self.lastfm.get_artist_similar(artist)
            metadata.similar_artists.extend(similar)
            
            # Album-Informationen (für Release-Datum)
            if album:
                album_info = await self.lastfm.get_album_info(artist, album)
                if album_info:
                    wiki = album_info.get('wiki', {})
                    if wiki.get('published'):
                        metadata.release_date = wiki['published']
                        
        except Exception as e:
            logger.error(f"Last.fm Datensammlung-Fehler: {e}")
    
    async def _collect_spotify_data(self, metadata: ExtendedMetadata, artist: str, title: str, album: str = None):
        """Sammelt Daten von Spotify inklusive Cover-URLs"""
        try:
            # Track suchen
            track_id = await self.spotify.search_track(artist, title, album)
            if track_id:
                metadata.sources_used.append('spotify')
                
                # Audio-Features holen
                audio_features = await self.spotify.get_audio_features(track_id)
                if audio_features:
                    metadata.audio_features = audio_features
                
                # Track-Details mit Cover-URLs holen
                track_details = await self.spotify.get_track_details(track_id)
                if track_details:
                    # Album-Cover URLs extrahieren
                    album_data = track_details.get('album', {})
                    images = album_data.get('images', [])
                    
                    if images:
                        # Verschiedene Cover-Größen speichern
                        for img in images:
                            size_key = f"{img['width']}x{img['height']}"
                            metadata.cover_urls[size_key] = img['url']
                        
                        # Beste Cover-URL als Standard setzen
                        metadata.cover_url = images[0]['url']  # Erste (meist größte)
                    
                    # Zusätzliche Album-Informationen
                    metadata.album_type = album_data.get('album_type')
                    
                    # Release-Datum von Spotify (falls nicht von Last.fm verfügbar)
                    if not metadata.release_date:
                        release_date = album_data.get('release_date')
                        if release_date:
                            metadata.release_date = release_date
                    
                    # Popularity
                    metadata.popularity = track_details.get('popularity')
                    metadata.explicit = track_details.get('explicit')
                    
        except Exception as e:
            logger.error(f"Spotify Datensammlung-Fehler: {e}")


def create_extended_metadata_service() -> ExtendedMetadataService:
    """Factory-Funktion für ExtendedMetadataService"""
    return ExtendedMetadataService()


# Async Wrapper für synchrone Verwendung
def get_extended_metadata_sync(artist: str, title: str, album: str = None) -> ExtendedMetadata:
    """Synchroner Wrapper für get_track_metadata"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        service = create_extended_metadata_service()
        return loop.run_until_complete(service.get_track_metadata(artist, title, album))
    finally:
        loop.close()
