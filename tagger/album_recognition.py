"""
Album-Erkennungsmodul für MP3 Tagger Web Application

Dieses Modul bietet umfassende Album-Erkennungsfunktionen unter Verwendung von:
- MusicBrainz (primär): Kostenlose, umfassende Musikdatenbank ohne Rate-Limits
- Discogs (Fallback): Kommerzielle Musikdatenbank mit Rate-Limiting

Hauptfunktionen:
- Automatische Album-Erkennung basierend auf vorhandenen MP3-Metadaten
- Intelligente Konfidenz-Bewertung mit Fuzzy-Matching
- Caching-System für bereits erkannte Alben
- Rate-Limiting für externe API-Aufrufe
- Graceful Degradation bei API-Fehlern

Verwendung:
    service = create_album_recognition_service()
    candidates, confidence = await service.recognize_album(files_info)

Konfiguration:
    Benötigt MUSICBRAINZ_USERAGENT und DISCOGS_API in config.env
"""

import os
import asyncio
import warnings
import logging
import time
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import musicbrainzngs
import discogs_client
from dotenv import load_dotenv

# Konfiguration laden
load_dotenv('config.env')

logger = logging.getLogger(__name__)

@dataclass
class AlbumCandidate:
    """Repräsentiert einen Album-Kandidaten"""
    title: str
    artist: str
    year: Optional[str]
    track_count: int
    tracks: List[Dict[str, Any]]
    confidence: float
    source: str  # 'musicbrainz' oder 'discogs'
    external_id: str  # MB-ID oder Discogs-ID
    
class AlbumRecognitionService:
    """Service für Album-Erkennung mit MusicBrainz und Discogs"""
    
    def __init__(self):
        self.mb_client = None
        self.discogs_client = None
        self.cache = {}
        self.last_discogs_request = 0  # Rate Limiting für Discogs
        self.discogs_delay = 1.0  # Mindestens 1 Sekunde zwischen Discogs-Requests
        self._setup_clients()
        
    def _setup_clients(self):
        """Initialisiert die API-Clients"""
        try:
            # MusicBrainz Setup
            user_agent = os.getenv('MUSICBRAINZ_USERAGENT', 'MP3Tagger/1.0 (contact@example.com)')
            musicbrainzngs.set_useragent(*user_agent.split('/', 1))
            self.mb_client = musicbrainzngs
            logger.info("MusicBrainz Client initialisiert")
            
            # Discogs Setup
            discogs_token = os.getenv('DISCOGS_API')
            if discogs_token:
                self.discogs_client = discogs_client.Client('MP3Tagger/1.0', user_token=discogs_token)
                logger.info("Discogs Client initialisiert")
            else:
                logger.warning("Discogs API Token fehlt")
                
        except Exception as e:
            logger.error(f"Fehler beim Setup der API-Clients: {e}")
    
    async def recognize_album(self, files_info: List[Dict]) -> Tuple[List[AlbumCandidate], float]:
        """
        Erkennt das wahrscheinlichste Album basierend auf den MP3-Dateien
        
        Args:
            files_info: Liste von Datei-Informationen mit title, artist, etc.
            
        Returns:
            Tuple von (Album-Kandidaten, Konfidenz-Score)
        """
        if not files_info:
            return [], 0.0
            
        cache_key = self._generate_cache_key(files_info)
        if cache_key in self.cache:
            logger.info("Album-Erkennung aus Cache geladen")
            return self.cache[cache_key]
        
        candidates = []
        
        # Zuerst MusicBrainz versuchen (kostenlos, kein Rate Limit)
        try:
            mb_candidates = await self._search_musicbrainz(files_info)
            candidates.extend(mb_candidates)
            logger.info(f"MusicBrainz: {len(mb_candidates)} Kandidaten gefunden")
        except Exception as e:
            logger.error(f"MusicBrainz Suche fehlgeschlagen: {e}")
        
        # Discogs nur als letzter Ausweg (Rate Limit beachten!)
        # Nur verwenden wenn MusicBrainz weniger als 2 Kandidaten oder sehr niedrige Konfidenz liefert
        best_mb_confidence = max((c.confidence for c in candidates), default=0) if candidates else 0
        
        if len(candidates) < 2 or best_mb_confidence < 0.6:
            logger.info(f"MusicBrainz unzureichend (Kandidaten: {len(candidates)}, Konfidenz: {best_mb_confidence:.2f}), verwende Discogs als Fallback")
            try:
                discogs_candidates = await self._search_discogs(files_info)
                candidates.extend(discogs_candidates)
                logger.info(f"Discogs: {len(discogs_candidates)} zusätzliche Kandidaten gefunden")
            except Exception as e:
                logger.error(f"Discogs Suche fehlgeschlagen (Rate Limit?): {e}")
        else:
            logger.info(f"MusicBrainz lieferte ausreichende Ergebnisse, Discogs wird übersprungen (Rate Limit schonen)")
        
        # Kandidaten nach Konfidenz sortieren
        candidates.sort(key=lambda x: x.confidence, reverse=True)
        
        # Nur die besten 5 Kandidaten behalten
        candidates = candidates[:5]
        
        # Ergebnis cachen
        max_confidence = max((c.confidence for c in candidates), default=0.0)
        result = (candidates, max_confidence)
        self.cache[cache_key] = result
        
        return result
    
    async def _search_musicbrainz(self, files_info: List[Dict]) -> List[AlbumCandidate]:
        """Sucht nach Album-Kandidaten in MusicBrainz"""
        candidates = []
        
        try:
            # Sammle Artist und Track-Namen
            artists = [f.get('artist', '').strip() for f in files_info if f.get('artist')]
            titles = [f.get('title', '').strip() for f in files_info if f.get('title')]
            
            if not artists or not titles:
                return candidates
            
            # Häufigster Artist
            main_artist = max(set(artists), key=artists.count) if artists else ""
            
            # Suche nach Releases des Artists mit erweiterten Parametern
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                
                # Erste Suche: Genauer Artist-Name
                search_results = self.mb_client.search_releases(
                    artist=main_artist,
                    limit=25  # Erhöht von 50 für bessere Performance
                )
                
                processed_releases = set()  # Vermeidet Duplikate
                
                for release in search_results.get('release-list', []):
                    release_id = release['id']
                    if release_id in processed_releases:
                        continue
                    processed_releases.add(release_id)
                    
                    candidate = await self._evaluate_mb_release(release, files_info)
                    if candidate and candidate.confidence > 0.2:  # Niedrigere Schwelle für MusicBrainz
                        candidates.append(candidate)
                
                # Falls nicht genug Ergebnisse: Fuzzy-Suche nach Tracks
                if len(candidates) < 3 and titles:
                    logger.info("Erweitere MusicBrainz-Suche mit Track-Namen...")
                    for title in titles[:3]:  # Nur die ersten 3 Tracks probieren
                        try:
                            track_search = self.mb_client.search_releases(
                                recording=title,
                                artist=main_artist,
                                limit=10
                            )
                            
                            for release in track_search.get('release-list', []):
                                release_id = release['id']
                                if release_id in processed_releases:
                                    continue
                                processed_releases.add(release_id)
                                
                                candidate = await self._evaluate_mb_release(release, files_info)
                                if candidate and candidate.confidence > 0.2:
                                    candidates.append(candidate)
                        except Exception as e:
                            logger.warning(f"Track-basierte Suche fehlgeschlagen für '{title}': {e}")
                            continue
                        
        except Exception as e:
            logger.error(f"MusicBrainz Suchfehler: {e}")
        
        return candidates
    
    async def _evaluate_mb_release(self, release: Dict, files_info: List[Dict]) -> Optional[AlbumCandidate]:
        """Bewertet einen MusicBrainz Release als Album-Kandidaten"""
        try:
            release_id = release['id']
            
            # Detaillierte Release-Informationen abrufen
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                
                detailed_release = self.mb_client.get_release_by_id(
                    release_id, 
                    includes=['recordings', 'artist-credits']
                )
                
            release_info = detailed_release['release']
            
            # Track-Liste extrahieren
            tracks = []
            if 'medium-list' in release_info:
                for medium in release_info['medium-list']:
                    if 'track-list' in medium:
                        for i, track in enumerate(medium['track-list'], 1):
                            tracks.append({
                                'number': i,
                                'title': track['recording']['title'],
                                'artist': release_info.get('artist-credit', [{}])[0].get('name', ''),
                                'duration': track['recording'].get('length')
                            })
            
            # Konfidenz berechnen
            confidence = self._calculate_confidence(files_info, tracks)
            
            # Artist-Name sicher extrahieren - verschiedene Varianten probieren
            artist_name = ''
            if 'artist-credit' in release_info and release_info['artist-credit']:
                # Erste Variante: artist-credit ist eine Liste
                if isinstance(release_info['artist-credit'], list) and len(release_info['artist-credit']) > 0:
                    first_credit = release_info['artist-credit'][0]
                    if isinstance(first_credit, dict):
                        artist_name = first_credit.get('artist', {}).get('name', '') or first_credit.get('name', '')
                    else:
                        artist_name = str(first_credit)
            
            # Fallback: versuche andere Felder
            if not artist_name and 'artist-credit-phrase' in release_info:
                artist_name = release_info['artist-credit-phrase']
            
            print(f"DEBUG MusicBrainz: Release '{release_info.get('title', 'UNBEKANNT')}', Artist: '{artist_name}', Konfidenz: {confidence}")
            print(f"DEBUG MusicBrainz: Full artist-credit: {release_info.get('artist-credit')}")
            
            return AlbumCandidate(
                title=release_info['title'],
                artist=artist_name,
                year=release_info.get('date', '')[:4] if release_info.get('date') else None,
                track_count=len(tracks),
                tracks=tracks,
                confidence=confidence,
                source='musicbrainz',
                external_id=release_id
            )
            
        except Exception as e:
            logger.error(f"Fehler bei MusicBrainz Release-Bewertung: {e}")
            return None
    
    async def _search_discogs(self, files_info: List[Dict]) -> List[AlbumCandidate]:
        """Sucht nach Album-Kandidaten in Discogs"""
        candidates = []
        
        if not self.discogs_client:
            return candidates
        
        try:
            # Rate Limiting für Discogs respektieren
            time_since_last = time.time() - self.last_discogs_request
            if time_since_last < self.discogs_delay:
                sleep_time = self.discogs_delay - time_since_last
                logger.info(f"Discogs Rate Limiting: warte {sleep_time:.1f}s...")
                await asyncio.sleep(sleep_time)
            
            # Sammle Artist und Track-Namen
            artists = [f.get('artist', '').strip() for f in files_info if f.get('artist')]
            
            if not artists:
                return candidates
            
            main_artist = max(set(artists), key=artists.count)
            
            # Suche nach Releases (nicht Masters)
            self.last_discogs_request = time.time()  # Rate Limiting markieren
            search_results = self.discogs_client.search(
                artist=main_artist,
                type_='release',  # Nur Releases, nicht Masters
                per_page=15  # Reduziert für Rate Limiting
            )
            
            processed_count = 0
            for release in search_results:
                # Begrenze die Anzahl der verarbeiteten Releases
                if processed_count >= 15:
                    break
                
                # Skip Masters und ungültige Releases
                if hasattr(release, 'type') and release.type == 'master':
                    continue
                
                # Skip Releases ohne Titel
                if not hasattr(release, 'title') or not release.title:
                    continue
                    
                try:
                    candidate = await self._evaluate_discogs_release(release, files_info)
                    if candidate and candidate.confidence > 0.3:
                        candidates.append(candidate)
                        processed_count += 1
                except Exception as e:
                    logger.warning(f"Überspringe Discogs Release wegen Fehler: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Discogs Suchfehler: {e}")
        
        return candidates
    
    async def _evaluate_discogs_release(self, release, files_info: List[Dict]) -> Optional[AlbumCandidate]:
        """Bewertet einen Discogs Release als Album-Kandidaten"""
        try:
            # Sichere Extraktion der Release-Daten
            release_title = getattr(release, 'title', 'Unbekannt')
            
            # Artist-Information sicher extrahieren - mehrere Varianten probieren
            artist_name = 'Unbekannt'
            if hasattr(release, 'artists') and release.artists:
                try:
                    artist_name = release.artists[0].name
                except (AttributeError, IndexError):
                    pass
            elif hasattr(release, 'artist') and release.artist:
                artist_name = str(release.artist)
            
            # Falls immer noch leer, versuche main_release
            if artist_name == 'Unbekannt' and hasattr(release, 'main_release'):
                try:
                    if hasattr(release.main_release, 'artists') and release.main_release.artists:
                        artist_name = release.main_release.artists[0].name
                except:
                    pass
            
            # Jahr sicher extrahieren
            release_year = None
            if hasattr(release, 'year') and release.year:
                release_year = str(release.year)
            elif hasattr(release, 'date') and release.date:
                release_year = str(release.date)[:4] if len(str(release.date)) >= 4 else None
            
            # Track-Liste extrahieren (falls verfügbar)
            tracks = []
            if hasattr(release, 'tracklist') and release.tracklist:
                for i, track in enumerate(release.tracklist, 1):
                    track_title = getattr(track, 'title', f'Track {i}')
                    track_artist = artist_name  # Default zum Release-Artist
                    
                    # Versuche track-spezifischen Artist zu finden
                    if hasattr(track, 'artists') and track.artists:
                        track_artist = track.artists[0].name
                    elif hasattr(track, 'artist') and track.artist:
                        track_artist = track.artist
                    
                    tracks.append({
                        'number': i,
                        'title': track_title,
                        'artist': track_artist,
                        'duration': getattr(track, 'duration', None)
                    })
            
            # Wenn keine Tracks verfügbar, erstelle leere Liste
            if not tracks:
                # Versuche mindestens die Anzahl aus dem Release zu schätzen
                track_count = len(files_info) if files_info else 1
                for i in range(1, track_count + 1):
                    tracks.append({
                        'number': i,
                        'title': f'Track {i}',
                        'artist': artist_name,
                        'duration': None
                    })
            
            # Konfidenz berechnen
            confidence = self._calculate_confidence(files_info, tracks)
            
            print(f"DEBUG Discogs: Release '{release_title}', Artist: '{artist_name}', Konfidenz: {confidence}")
            print(f"DEBUG Discogs: Release object attributes: {[attr for attr in dir(release) if not attr.startswith('_')]}")
            
            # Release-ID sicher extrahieren
            release_id = getattr(release, 'id', 'unknown')
            
            return AlbumCandidate(
                title=release_title,
                artist=artist_name,
                year=release_year,
                track_count=len(tracks),
                tracks=tracks,
                confidence=confidence,
                source='discogs',
                external_id=str(release_id)
            )
            
        except Exception as e:
            logger.error(f"Fehler bei Discogs Release-Bewertung: {e}")
            return None
    
    def _calculate_confidence(self, files_info: List[Dict], album_tracks: List[Dict]) -> float:
        """Berechnet die Konfidenz eines Album-Kandidaten"""
        if not files_info or not album_tracks:
            return 0.0
        
        file_titles = [f.get('title', '').lower().strip() for f in files_info if f.get('title')]
        album_titles = [t.get('title', '').lower().strip() for t in album_tracks]
        
        if not file_titles or not album_titles:
            return 0.0
        
        # Exact matches zählen
        exact_matches = sum(1 for ft in file_titles if ft in album_titles)
        
        # Ähnlichkeits-Matches (vereinfachte Fuzzy-Matching)
        fuzzy_matches = 0
        for ft in file_titles:
            for at in album_titles:
                if ft and at and (ft in at or at in ft or self._fuzzy_match(ft, at)):
                    fuzzy_matches += 1
                    break
        
        # Konfidenz berechnen
        total_files = len(file_titles)
        confidence = (exact_matches * 1.0 + fuzzy_matches * 0.7) / total_files
        
        # Bonus für passende Track-Anzahl
        if abs(len(album_tracks) - total_files) <= 2:
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _fuzzy_match(self, str1: str, str2: str, threshold: float = 0.8) -> bool:
        """Einfaches Fuzzy-Matching für Strings"""
        if not str1 or not str2:
            return False
        
        # Vereinfachte Ähnlichkeitsprüfung
        longer = str1 if len(str1) > len(str2) else str2
        shorter = str2 if len(str1) > len(str2) else str1
        
        if len(longer) == 0:
            return True
        
        # Anteil der übereinstimmenden Zeichen
        matches = sum(1 for c in shorter if c in longer)
        similarity = matches / len(longer)
        
        return similarity >= threshold
    
    def _generate_cache_key(self, files_info: List[Dict]) -> str:
        """Generiert einen Cache-Schlüssel für die Datei-Liste"""
        titles = sorted([f.get('title', '') for f in files_info if f.get('title')])
        artists = sorted([f.get('artist', '') for f in files_info if f.get('artist')])
        return f"album_{hash(tuple(titles + artists))}"

# Factory-Funktion
def create_album_recognition_service() -> AlbumRecognitionService:
    """Erstellt eine neue Instanz des Album-Erkennungsservices"""
    return AlbumRecognitionService()
