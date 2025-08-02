"""
Audio Recognition Module für MP3 Tagger Web Application

Implementiert Titelerkennung mit AcoustID (primär) und Shazam (Fallback).
Ergebnisse werden für spätere Verarbeitung zwischengespeichert.
"""

import os
import asyncio
import aiohttp
import hashlib
from typing import Dict, Any, Optional, List, Tuple
from shazamio import Shazam
import acoustid


class AudioRecognitionService:
    """Service für Audio-Erkennung mit mehreren Providern."""
    
    def __init__(self, acoustid_api_key: str, config: Dict[str, Any] = None):
        """
        Initialisiert den Audio-Recognition Service.
        
        Args:
            acoustid_api_key: API-Key für AcoustID
            config: Zusätzliche Konfiguration
        """
        self.acoustid_api_key = acoustid_api_key
        self.config = config or {}
        self.recognition_cache = {}  # Cache für erkannte Titel
        
    async def recognize_audio(self, file_path: str) -> Dict[str, Any]:
        """
        Hauptfunktion für Audio-Erkennung mit Fallback-Strategie.
        
        Args:
            file_path: Pfad zur MP3-Datei
            
        Returns:
            Dictionary mit Erkennungsergebnissen
        """
        result = {
            'success': False,
            'source': None,
            'title': None,
            'artist': None,
            'confidence': 0.0,
            'error': None,
            'metadata': {}
        }
        
        # Cache-Check
        cache_key = self._get_cache_key(file_path)
        if cache_key in self.recognition_cache:
            return self.recognition_cache[cache_key]
        
        try:
            # Schritt 1: AcoustID versuchen (primär)
            print(f"🔍 Versuche AcoustID-Erkennung für: {os.path.basename(file_path)}")
            acoustid_result = await self._recognize_with_acoustid(file_path)
            
            if acoustid_result['success']:
                result = acoustid_result
                result['source'] = 'AcoustID'
                print(f"✅ AcoustID erfolgreich: {result['artist']} - {result['title']}")
            else:
                # Schritt 2: Shazam als Fallback
                print(f"⚠️ AcoustID fehlgeschlagen, versuche Shazam...")
                shazam_result = await self._recognize_with_shazam(file_path)
                
                if shazam_result['success']:
                    result = shazam_result
                    result['source'] = 'Shazam'
                    print(f"✅ Shazam erfolgreich: {result['artist']} - {result['title']}")
                else:
                    result['error'] = f"Beide Services fehlgeschlagen: AcoustID ({acoustid_result['error']}), Shazam ({shazam_result['error']})"
                    print(f"❌ Beide Services fehlgeschlagen für: {os.path.basename(file_path)}")
        
        except Exception as e:
            result['error'] = f"Unerwarteter Fehler: {str(e)}"
            print(f"💥 Unerwarteter Fehler bei: {os.path.basename(file_path)} - {str(e)}")
        
        # Ergebnis cachen
        self.recognition_cache[cache_key] = result
        return result
    
    async def _recognize_with_acoustid(self, file_path: str) -> Dict[str, Any]:
        """
        Audio-Erkennung mit AcoustID.
        
        Args:
            file_path: Pfad zur MP3-Datei
            
        Returns:
            Dictionary mit AcoustID-Ergebnissen
        """
        result = {
            'success': False,
            'title': None,
            'artist': None,
            'confidence': 0.0,
            'error': None,
            'metadata': {}
        }
        
        try:
            # Audio-Fingerprint generieren mit Warnung-Unterdrückung
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", DeprecationWarning)
                duration, fingerprint = acoustid.fingerprint_file(file_path)
            
            if not fingerprint:
                result['error'] = 'Konnte keinen Fingerprint generieren'
                return result
            
            # AcoustID API abfragen mit besserer Fehlerbehandlung
            try:
                matches = acoustid.lookup(
                    apikey=self.acoustid_api_key,
                    fingerprint=fingerprint,
                    duration=duration,
                    meta='recordings+releasegroups+releases+tracks'
                )
            except Exception as api_error:
                result['error'] = f'AcoustID API Fehler: {str(api_error)}'
                return result
            
            # Beste Übereinstimmung suchen
            best_match = self._find_best_acoustid_match(matches)
            
            if best_match:
                result['success'] = True
                result['title'] = best_match['title']
                result['artist'] = best_match['artist']
                result['confidence'] = best_match['confidence']
                result['metadata'] = {
                    'duration': duration,
                    'fingerprint_length': len(fingerprint),
                    'acoustid_score': best_match['score'],
                    'release_group': best_match.get('release_group'),
                    'release': best_match.get('release')
                }
            else:
                result['error'] = 'Keine ausreichenden Übereinstimmungen gefunden'
        
        except Exception as e:
            result['error'] = f'AcoustID Fehler: {str(e)}'
        
        return result
    
    async def _recognize_with_shazam(self, file_path: str) -> Dict[str, Any]:
        """
        Audio-Erkennung mit Shazam.
        
        Args:
            file_path: Pfad zur MP3-Datei
            
        Returns:
            Dictionary mit Shazam-Ergebnissen
        """
        result = {
            'success': False,
            'title': None,
            'artist': None,
            'confidence': 0.0,
            'error': None,
            'metadata': {}
        }
        
        try:
            shazam = Shazam()
            
            # Shazam-Erkennung durchführen
            recognition_result = await shazam.recognize_song(file_path)
            
            if recognition_result and 'track' in recognition_result:
                track = recognition_result['track']
                
                result['success'] = True
                result['title'] = track.get('title', '').strip()
                result['artist'] = track.get('subtitle', '').strip()  # Subtitle ist meist der Artist
                result['confidence'] = 0.8  # Shazam gibt keine Confidence zurück, nehmen wir 0.8 an
                
                result['metadata'] = {
                    'shazam_key': track.get('key'),
                    'genre': track.get('genres', {}).get('primary') if track.get('genres') else None,
                    'release_date': track.get('releasedate'),
                    'label': track.get('label'),
                    'isrc': track.get('isrc')
                }
                
                # Zusätzliche Künstler-Informationen falls verfügbar
                if 'artists' in track and track['artists']:
                    primary_artist = track['artists'][0]
                    result['artist'] = primary_artist.get('alias', result['artist'])
            else:
                result['error'] = 'Keine Übereinstimmung bei Shazam gefunden'
        
        except Exception as e:
            result['error'] = f'Shazam Fehler: {str(e)}'
        
        return result
    
    def _find_best_acoustid_match(self, matches) -> Optional[Dict[str, Any]]:
        """
        Findet die beste Übereinstimmung aus AcoustID-Ergebnissen.
        
        Args:
            matches: AcoustID API Ergebnisse
            
        Returns:
            Dictionary mit dem besten Match oder None
        """
        best_match = None
        best_score = 0.0
        
        for match in matches:
            score = match.get('score', 0.0)
            
            # Nur Matches mit ausreichender Score berücksichtigen
            if score < 0.7:
                continue
            
            if 'recordings' in match:
                for recording in match['recordings']:
                    title = recording.get('title', '').strip()
                    
                    # Artist aus verschiedenen Quellen extrahieren
                    artist = ''
                    if 'artists' in recording and recording['artists']:
                        artist = recording['artists'][0].get('name', '').strip()
                    
                    if title and artist and score > best_score:
                        best_score = score
                        best_match = {
                            'title': title,
                            'artist': artist,
                            'confidence': score,
                            'score': score,
                            'release_group': recording.get('releasegroups', [{}])[0].get('title') if recording.get('releasegroups') else None,
                            'release': recording.get('releases', [{}])[0].get('title') if recording.get('releases') else None
                        }
        
        return best_match
    
    def _get_cache_key(self, file_path: str) -> str:
        """
        Generiert einen Cache-Key für eine Datei.
        
        Args:
            file_path: Pfad zur Datei
            
        Returns:
            MD5-Hash als Cache-Key
        """
        # Kombiniere Dateipfad und Größe für eindeutigen Key
        file_stat = os.stat(file_path)
        key_string = f"{file_path}_{file_stat.st_size}_{file_stat.st_mtime}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def get_recognition_stats(self) -> Dict[str, Any]:
        """
        Gibt Statistiken über durchgeführte Erkennungen zurück.
        
        Returns:
            Dictionary mit Statistiken
        """
        total = len(self.recognition_cache)
        successful = sum(1 for r in self.recognition_cache.values() if r['success'])
        
        sources = {}
        for r in self.recognition_cache.values():
            if r['success'] and r['source']:
                sources[r['source']] = sources.get(r['source'], 0) + 1
        
        return {
            'total_processed': total,
            'successful': successful,
            'success_rate': successful / total if total > 0 else 0,
            'sources': sources,
            'cached_results': total
        }


class AudioRecognitionBatch:
    """Batch-Verarbeitung für mehrere Audio-Dateien."""
    
    def __init__(self, recognition_service: AudioRecognitionService):
        """
        Initialisiert Batch-Verarbeitung.
        
        Args:
            recognition_service: AudioRecognitionService Instanz
        """
        self.recognition_service = recognition_service
        self.results = {}
        self.progress_callback = None
    
    def set_progress_callback(self, callback):
        """Setzt Callback-Funktion für Progress-Updates."""
        self.progress_callback = callback
    
    async def process_files(self, file_paths: List[str]) -> Dict[str, Any]:
        """
        Verarbeitet mehrere Audio-Dateien.
        
        Args:
            file_paths: Liste der zu verarbeitenden Dateipfade
            
        Returns:
            Dictionary mit allen Ergebnissen
        """
        total_files = len(file_paths)
        processed = 0
        
        for file_path in file_paths:
            try:
                if self.progress_callback:
                    self.progress_callback(processed, total_files, os.path.basename(file_path))
                
                result = await self.recognition_service.recognize_audio(file_path)
                self.results[file_path] = result
                
                processed += 1
                
            except Exception as e:
                self.results[file_path] = {
                    'success': False,
                    'error': f'Batch-Verarbeitungsfehler: {str(e)}',
                    'title': None,
                    'artist': None,
                    'source': None
                }
                processed += 1
        
        if self.progress_callback:
            self.progress_callback(processed, total_files, "Abgeschlossen")
        
        return self.results


def create_recognition_service(config_path: str = 'config.env') -> AudioRecognitionService:
    """
    Factory-Funktion zur Erstellung eines AudioRecognitionService.
    
    Args:
        config_path: Pfad zur Konfigurationsdatei
        
    Returns:
        Initialisierte AudioRecognitionService Instanz
    """
    import os
    from dotenv import load_dotenv
    
    # .env Datei laden (unterstützt KEY=VALUE Format ohne Sections)
    load_dotenv(config_path)
    
    acoustid_api_key = os.getenv('ACOUSTID_API_KEY')
    
    if not acoustid_api_key:
        raise ValueError("ACOUSTID_API_KEY nicht in config.env gefunden")
    
    config = {
        'lastfm_api_key': os.getenv('LASTFM_API_KEY'),
        'musicbrainz_useragent': os.getenv('MUSICBRAINZ_USERAGENT'),
        'discogs_api': os.getenv('DISCOGS_API')
    }
    
    return AudioRecognitionService(
        acoustid_api_key=acoustid_api_key,
        config=config
    )
