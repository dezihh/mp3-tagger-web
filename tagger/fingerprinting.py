"""
Audio Fingerprinting Module
Modul für Audio-Fingerprinting Funktionalitäten
"""

import logging
import subprocess
import json
import os
import tempfile
import requests
import hashlib
import struct
from mutagen.mp3 import MP3

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class AlbumRecognitionService:
    """Service für Album-basierte Erkennung mittels DiscID und AcoustID"""
    
    def __init__(self):
        self.acoustid_api_key = "8XaBELgH"  # Öffentlicher API-Key
        self.musicbrainz_base_url = "https://musicbrainz.org/ws/2"
        self.acoustid_base_url = "https://api.acoustid.org/v2"
        
    def recognize_album_from_directory(self, directory_path):
        """
        Erkennt Album-Informationen basierend auf allen MP3-Dateien in einem Verzeichnis
        
        Args:
            directory_path (str): Pfad zum Verzeichnis mit MP3-Dateien
            
        Returns:
            dict: Album-Erkennungsergebnisse mit möglichen Kandidaten
        """
        try:
            logging.info(f"🎼 Starte Album-Erkennung für Verzeichnis: {directory_path}")
            
            # Sammle alle MP3-Dateien
            mp3_files = []
            for file in os.listdir(directory_path):
                if file.lower().endswith('.mp3'):
                    file_path = os.path.join(directory_path, file)
                    mp3_files.append(file_path)
            
            if len(mp3_files) < 2:
                return {
                    'success': False,
                    'error': 'Zu wenige MP3-Dateien für Album-Erkennung (mindestens 2 benötigt)',
                    'candidates': []
                }
            
            logging.info(f"📁 Gefunden: {len(mp3_files)} MP3-Dateien")
            
            # Extrahiere Track-Informationen (Längen)
            track_durations = []
            for file_path in sorted(mp3_files):
                try:
                    audio = MP3(file_path)
                    duration_ms = int(audio.info.length * 1000) if audio.info.length else 0
                    track_durations.append({
                        'file': os.path.basename(file_path),
                        'path': file_path,
                        'duration_ms': duration_ms
                    })
                    logging.debug(f"📊 Track: {os.path.basename(file_path)} - {duration_ms}ms")
                except Exception as e:
                    logging.warning(f"Konnte Länge für {file_path} nicht ermitteln: {e}")
                    continue
            
            logging.info(f"📊 Extrahierte Tracks: {len(track_durations)}")
            
            # Versuche verschiedene Erkennungsmethoden
            candidates = []
            
            # Methode 1: Einfacher Verzeichnisname-basierter Ansatz
            simple_candidates = self._try_simple_directory_recognition(directory_path, track_durations)
            if simple_candidates:
                candidates.extend(simple_candidates)
                logging.info(f"🔍 Einfache Erkennung: {len(simple_candidates)} Kandidaten")
            
            # Methode 2: AcoustID Album-Lookup (nur bei wenigen Dateien)
            if len(track_durations) <= 20:  # Begrenze AcoustID auf kleinere Alben
                acoustid_candidates = self._try_acoustid_album_recognition(track_durations)
                if acoustid_candidates:
                    candidates.extend(acoustid_candidates)
                    logging.info(f"🎵 AcoustID: {len(acoustid_candidates)} Kandidaten")
            
            # Methode 3: MusicBrainz Track-Längen-Matching
            duration_candidates = self._try_duration_matching(track_durations)
            if duration_candidates:
                candidates.extend(duration_candidates)
                logging.info(f"⏱️ Duration-Matching: {len(duration_candidates)} Kandidaten")
            
            # Entferne Duplikate und bewerte Kandidaten
            unique_candidates = self._deduplicate_and_score_candidates(candidates)
            
            logging.info(f"✅ Album-Erkennung abgeschlossen: {len(unique_candidates)} finale Kandidaten")
            
            return {
                'success': True,
                'directory': directory_path,
                'track_count': len(track_durations),
                'candidates': unique_candidates[:5],  # Top 5 Kandidaten
                'method_used': 'combined_album_recognition',
                'debug_info': {
                    'simple_count': len(simple_candidates) if simple_candidates else 0,
                    'acoustid_count': len(acoustid_candidates) if len(track_durations) <= 20 and 'acoustid_candidates' in locals() else 0,
                    'duration_count': len(duration_candidates) if duration_candidates else 0
                }
            }
            
        except Exception as e:
            logging.error(f"Album-Erkennung fehlgeschlagen: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'candidates': []
            }
    
    def _try_simple_directory_recognition(self, directory_path, track_durations):
        """Versucht Album-Erkennung basierend auf Verzeichnisname"""
        candidates = []
        
        try:
            # Extrahiere Artist und Album aus Verzeichnisname
            dir_name = os.path.basename(directory_path)
            logging.info(f"🔍 Analysiere Verzeichnisname: '{dir_name}'")
            
            # Verschiedene Verzeichnisname-Patterns
            patterns = [
                r'^(.+?)\s*-\s*(.+)$',  # "Artist - Album"
                r'^(.+?)\s*/\s*(.+)$',  # "Artist / Album"  
                r'^(.+?)\s*_\s*(.+)$',  # "Artist _ Album"
            ]
            
            artist, album = None, None
            for pattern in patterns:
                import re
                match = re.match(pattern, dir_name)
                if match:
                    artist = match.group(1).strip()
                    album = match.group(2).strip()
                    logging.info(f"📝 Pattern erkannt: Artist='{artist}', Album='{album}'")
                    break
            
            if not artist or not album:
                # Fallback: Verwende ganzen Verzeichnisnamen als Album
                album = dir_name
                artist = "Unbekannt"
                logging.info(f"📝 Fallback: Album='{album}'")
            
            # Erstelle Kandidat basierend auf Verzeichnisname
            candidate = {
                'source': 'directory_name',
                'album': album,
                'artist': artist,
                'track_count': len(track_durations),
                'total_duration_ms': sum(t['duration_ms'] for t in track_durations),
                'match_score': 0.8,  # Hoher Score für Verzeichnisname-Match
                'confidence': 'high',
                'method': 'directory_parsing'
            }
            
            candidates.append(candidate)
            logging.info(f"✅ Verzeichnisname-Kandidat erstellt: {album} von {artist}")
            
            # Versuche MusicBrainz-Suche basierend auf extrahierten Daten
            if artist != "Unbekannt":
                mb_candidates = self._search_musicbrainz_by_artist_album(artist, album, len(track_durations))
                if mb_candidates:
                    candidates.extend(mb_candidates)
                    logging.info(f"🎵 MusicBrainz Zusatz-Kandidaten: {len(mb_candidates)}")
            
        except Exception as e:
            logging.warning(f"Einfache Verzeichnis-Erkennung fehlgeschlagen: {e}")
        
        return candidates
    
    def _search_musicbrainz_by_artist_album(self, artist, album, track_count):
        """Sucht in MusicBrainz nach Artist+Album Kombination"""
        candidates = []
        
        try:
            # Bereite Suchstring vor
            query = f'artist:"{artist}" AND release:"{album}"'
            
            params = {
                'query': query,
                'limit': 5,
                'fmt': 'json'
            }
            
            logging.info(f"🔍 MusicBrainz Suche: {query}")
            
            response = requests.get(f"{self.musicbrainz_base_url}/release", params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                
                for release in data.get('releases', []):
                    candidate = self._parse_musicbrainz_release(release)
                    if candidate:
                        # Bonus für Track-Count-Match
                        if candidate.get('track_count') == track_count:
                            candidate['match_score'] += 0.2
                        
                        candidate['method'] = 'musicbrainz_search'
                        candidates.append(candidate)
                        logging.info(f"🎵 MusicBrainz Kandidat: {candidate.get('album')} von {candidate.get('artist')}")
                        
        except Exception as e:
            logging.warning(f"MusicBrainz Artist/Album-Suche fehlgeschlagen: {e}")
        
        return candidates

    def _try_acoustid_album_recognition(self, track_durations):
        """Versucht Album-Erkennung über AcoustID"""
        candidates = []
        
        try:
            logging.info(f"🎵 Starte AcoustID Album-Erkennung für {len(track_durations)} Tracks")
            
            # Fingerprinte ersten und letzten Track für Album-Kontext
            test_tracks = []
            if len(track_durations) >= 2:
                test_tracks = [track_durations[0], track_durations[-1]]
            elif len(track_durations) == 1:
                test_tracks = [track_durations[0]]
            
            for i, track in enumerate(test_tracks):
                try:
                    logging.info(f"🔍 Fingerprinting Track {i+1}: {track['file']}")
                    fingerprint = self._get_acoustid_fingerprint(track['path'])
                    
                    if fingerprint:
                        logging.info(f"✅ Fingerprint erstellt für {track['file']}")
                        result = self._query_acoustid_with_album_info(fingerprint, track['duration_ms'])
                        if result:
                            candidates.extend(result)
                            logging.info(f"🎵 AcoustID Ergebnisse: {len(result)} für {track['file']}")
                    else:
                        logging.warning(f"❌ Kein Fingerprint für {track['file']}")
                        
                except Exception as e:
                    logging.warning(f"AcoustID Fehler für {track['file']}: {e}")
                    continue
                    
        except Exception as e:
            logging.warning(f"AcoustID Album-Erkennung fehlgeschlagen: {e}")
        
        logging.info(f"🎵 AcoustID Album-Erkennung abgeschlossen: {len(candidates)} Kandidaten")
        return candidates
    
    def _try_duration_matching(self, track_durations):
        """Versucht Album-Erkennung über Track-Längen-Matching"""
        candidates = []
        
        try:
            # Erstelle "Signatur" aus Track-Längen
            duration_signature = [t['duration_ms'] for t in track_durations]
            total_duration = sum(duration_signature)
            track_count = len(track_durations)
            
            logging.info(f"⏱️ Duration-Matching: {track_count} Tracks, {total_duration//1000}s total")
            
            # Suche in MusicBrainz nach Alben mit ähnlicher Track-Anzahl und Gesamtlänge
            # Erweitere Suchbereich für bessere Treffer
            duration_tolerance = 60000  # ±60 Sekunden
            track_tolerance = 2  # ±2 Tracks
            
            queries = [
                f'tracks:{track_count}',  # Exakte Track-Anzahl
                f'tracks:[{max(1, track_count-track_tolerance)} TO {track_count+track_tolerance}]'  # Track-Bereich
            ]
            
            for query in queries:
                try:
                    params = {
                        'query': query,
                        'limit': 10,
                        'fmt': 'json'
                    }
                    
                    logging.debug(f"🔍 MusicBrainz Query: {query}")
                    
                    response = requests.get(f"{self.musicbrainz_base_url}/release", params=params, timeout=15)
                    if response.status_code == 200:
                        data = response.json()
                        
                        for release in data.get('releases', []):
                            candidate = self._parse_musicbrainz_release(release)
                            if candidate:
                                # Bewerte Übereinstimmung mit Track-Längen (falls verfügbar)
                                candidate['match_score'] = 0.6  # Base score für Duration-Matching
                                candidate['method'] = 'duration_matching'
                                candidates.append(candidate)
                                logging.debug(f"⏱️ Duration Kandidat: {candidate.get('album')} ({candidate.get('track_count')} tracks)")
                    else:
                        logging.warning(f"❌ MusicBrainz HTTP {response.status_code} für Query: {query}")
                        
                except requests.exceptions.Timeout:
                    logging.warning(f"⏰ MusicBrainz Timeout für Query: {query}")
                except Exception as e:
                    logging.warning(f"❌ MusicBrainz Query-Fehler für '{query}': {e}")
                    continue
                        
        except Exception as e:
            logging.warning(f"Duration-Matching fehlgeschlagen: {e}")
        
        logging.info(f"⏱️ Duration-Matching abgeschlossen: {len(candidates)} Kandidaten")
        return candidates
    
    def _get_acoustid_fingerprint(self, file_path):
        """Erstellt AcoustID Fingerprint für eine Datei"""
        try:
            logging.debug(f"🔍 Erstelle Fingerprint für: {os.path.basename(file_path)}")
            
            # Verwende fpcalc für Fingerprint-Erstellung
            cmd = ['fpcalc', '-json', file_path]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                fingerprint = data.get('fingerprint')
                if fingerprint:
                    logging.debug(f"✅ Fingerprint erstellt: {len(fingerprint)} Zeichen")
                    return fingerprint
                else:
                    logging.warning(f"❌ Leerer Fingerprint für {file_path}")
            else:
                logging.warning(f"❌ fpcalc Fehler für {file_path}: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            logging.error(f"⏰ fpcalc Timeout für {file_path}")
        except json.JSONDecodeError as e:
            logging.error(f"📄 JSON Parse-Fehler für {file_path}: {e}")
        except Exception as e:
            logging.warning(f"Fingerprint-Erstellung fehlgeschlagen für {file_path}: {e}")
        
        return None
    
    def _query_acoustid_with_album_info(self, fingerprint, duration):
        """Fragt AcoustID nach Album-Informationen"""
        try:
            params = {
                'client': self.acoustid_api_key,
                'fingerprint': fingerprint,
                'duration': duration // 1000,  # Sekunden
                'meta': 'releases+recordings+releasegroups'
            }
            
            logging.debug(f"🌐 AcoustID Query: duration={duration//1000}s")
            
            response = requests.get(f"{self.acoustid_base_url}/lookup", params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('status') != 'ok':
                    logging.warning(f"❌ AcoustID API Status: {data.get('status')}")
                    return []
                
                candidates = []
                results = data.get('results', [])
                logging.info(f"🎵 AcoustID Response: {len(results)} Ergebnisse")
                
                for result in results:
                    try:
                        recordings = result.get('recordings', [])
                        for recording in recordings:
                            releases = recording.get('releases', [])
                            for release in releases:
                                candidate = self._parse_acoustid_release(release, recording)
                                if candidate:
                                    candidates.append(candidate)
                                    logging.debug(f"🎵 AcoustID Kandidat: {candidate.get('album')} von {candidate.get('artist')}")
                    except Exception as e:
                        logging.warning(f"Fehler beim Parsen von AcoustID Ergebnis: {e}")
                        continue
                
                return candidates
            else:
                logging.warning(f"❌ AcoustID API Fehler: HTTP {response.status_code}")
                
        except requests.exceptions.Timeout:
            logging.error(f"⏰ AcoustID API Timeout")
        except requests.exceptions.RequestException as e:
            logging.warning(f"❌ AcoustID API Request-Fehler: {e}")
        except Exception as e:
            logging.warning(f"AcoustID Query fehlgeschlagen: {e}")
        
        return []
    
    def _parse_musicbrainz_release(self, release):
        """Parst MusicBrainz Release-Daten"""
        try:
            artist = self._extract_artist_from_release(release)
            album = release.get('title', 'Unbekanntes Album')
            
            return {
                'source': 'musicbrainz',
                'release_id': release.get('id'),
                'album': album,
                'artist': artist,
                'date': release.get('date'),
                'track_count': release.get('track-count'),
                'country': release.get('country'),
                'barcode': release.get('barcode'),
                'match_score': 0.5,  # Standard-Score für MusicBrainz
                'confidence': 'medium'
            }
        except Exception as e:
            logging.debug(f"Fehler beim Parsen von MusicBrainz Release: {e}")
            return None
    
    def _parse_acoustid_release(self, release, recording):
        """Parst AcoustID Release-Daten"""
        try:
            artist = self._extract_artist_from_acoustid(recording)
            album = release.get('title', 'Unbekanntes Album')
            
            return {
                'source': 'acoustid',
                'release_id': release.get('id'),
                'album': album,
                'artist': artist,
                'date': release.get('date'),
                'track_count': release.get('track-count'),
                'country': release.get('country'),
                'match_score': 0.7,  # Höherer Score für AcoustID (Audio-basiert)
                'confidence': 'high'
            }
        except Exception as e:
            logging.debug(f"Fehler beim Parsen von AcoustID Release: {e}")
            return None
    
    def _extract_artist_from_release(self, release):
        """Extrahiert Artist-Namen aus MusicBrainz Release"""
        try:
            if 'artist-credit' in release:
                artists = []
                for credit in release['artist-credit']:
                    if isinstance(credit, dict) and 'artist' in credit:
                        artists.append(credit['artist']['name'])
                return ', '.join(artists)
        except Exception:
            pass
        return "Unbekannt"
    
    def _extract_artist_from_acoustid(self, recording):
        """Extrahiert Artist-Namen aus AcoustID Recording"""
        try:
            if 'artists' in recording:
                return ', '.join([artist.get('name', 'Unbekannt') for artist in recording['artists']])
        except Exception:
            pass
        return "Unbekannt"
    
    def _calculate_duration_match_score(self, signature1, signature2):
        """Berechnet Übereinstimmungs-Score für Track-Längen"""
        if not signature1 or not signature2 or len(signature1) != len(signature2):
            return 0.0
        
        total_diff = 0
        for d1, d2 in zip(signature1, signature2):
            diff = abs(d1 - d2)
            total_diff += diff
        
        # Score basierend auf durchschnittlicher Abweichung
        avg_diff = total_diff / len(signature1)
        max_acceptable_diff = 10000  # 10 Sekunden
        
        if avg_diff <= max_acceptable_diff:
            return 1.0 - (avg_diff / max_acceptable_diff)
        else:
            return 0.0
    
    def _deduplicate_and_score_candidates(self, candidates):
        """Entfernt Duplikate und sortiert nach Score"""
        # Gruppiere nach Album+Artist
        seen = {}
        for candidate in candidates:
            key = f"{candidate.get('album', '')}-{candidate.get('artist', '')}"
            if key not in seen or candidate.get('match_score', 0) > seen[key].get('match_score', 0):
                seen[key] = candidate
        
        # Sortiere nach Score
        unique_candidates = list(seen.values())
        unique_candidates.sort(key=lambda x: x.get('match_score', 0), reverse=True)
        
        return unique_candidates

class AudioFingerprintService:
    """Service für Audio-Fingerprinting und verwandte Funktionen"""
    
    def __init__(self):
        # Lazy import um zirkuläre Abhängigkeiten zu vermeiden
        self._audio_recognition = None
        self.min_confidence = 0.6
        
    @property
    def audio_recognition(self):
        """Lazy loading für AudioRecognitionService"""
        if self._audio_recognition is None:
            from .audio_recognition import AudioRecognitionService
            self._audio_recognition = AudioRecognitionService()
        return self._audio_recognition
        
    def get_audio_fingerprint_metadata(self, file_path):
        """
        Holt Metadaten über Audio-Fingerprinting
        
        Args:
            file_path (str): Pfad zur Audio-Datei
            
        Returns:
            dict: Gefundene Metadaten oder None
        """
        try:
            # Verwende Audio-Recognition Service
            result = self.audio_recognition.recognize_audio_file(file_path)
            
            if result and result.get('confidence', 0) >= self.min_confidence:
                logging.info(f"✅ Audio-Fingerprinting erfolgreich mit {result.get('service')}")
                return result
            
            logging.warning(f"❌ Audio-Fingerprinting fehlgeschlagen für {file_path}")
            return None
            
        except Exception as e:
            logging.error(f"Fehler bei Audio-Fingerprinting: {str(e)}")
            return None
    
    def create_audio_fingerprint(self, file_path):
        """
        Erstellt einen Audio-Fingerprint für eine Datei
        
        Args:
            file_path (str): Pfad zur Audio-Datei
            
        Returns:
            dict: Fingerprint-Daten oder None
        """
        try:
            # Verwende fpcalc für Fingerprint-Erstellung
            cmd = ['fpcalc', '-json', file_path]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                return {
                    'fingerprint': data.get('fingerprint'),
                    'duration': data.get('duration'),
                    'file_path': file_path
                }
            else:
                logging.error(f"fpcalc Fehler: {result.stderr}")
                return None
                
        except subprocess.TimeoutExpired:
            logging.error(f"fpcalc Timeout für {file_path}")
            return None
        except Exception as e:
            logging.error(f"Fingerprint-Erstellung fehlgeschlagen: {str(e)}")
            return None
    
    def compare_audio_fingerprints(self, file_path1, file_path2):
        """
        Vergleicht Audio-Fingerprints von zwei Dateien
        
        Args:
            file_path1 (str): Pfad zur ersten Audio-Datei
            file_path2 (str): Pfad zur zweiten Audio-Datei
            
        Returns:
            dict: Vergleichsergebnis mit Similarity-Score
        """
        try:
            fp1 = self.create_audio_fingerprint(file_path1)
            fp2 = self.create_audio_fingerprint(file_path2)
            
            if not fp1 or not fp2:
                return None
            
            # Einfacher Fingerprint-Vergleich (vereinfacht)
            similarity = self._calculate_fingerprint_similarity(
                fp1['fingerprint'], 
                fp2['fingerprint']
            )
            
            return {
                'file1': file_path1,
                'file2': file_path2,
                'similarity': similarity,
                'duration1': fp1['duration'],
                'duration2': fp2['duration'],
                'is_similar': similarity > 0.8
            }
            
        except Exception as e:
            logging.error(f"Fingerprint-Vergleich fehlgeschlagen: {str(e)}")
            return None
    
    def _calculate_fingerprint_similarity(self, fp1, fp2):
        """Berechnet Ähnlichkeit zwischen zwei Fingerprints (vereinfacht)"""
        try:
            # Vereinfachter Vergleich basierend auf String-Ähnlichkeit
            from difflib import SequenceMatcher
            
            matcher = SequenceMatcher(None, fp1, fp2)
            return matcher.ratio()
            
        except Exception:
            return 0.0
    
    def extract_audio_features(self, file_path):
        """
        Extrahiert Audio-Features aus einer Datei
        
        Args:
            file_path (str): Pfad zur Audio-Datei
            
        Returns:
            dict: Audio-Features oder None
        """
        try:
            # Verwende ffprobe für Audio-Analyse
            cmd = [
                'ffprobe', '-v', 'quiet', '-print_format', 'json',
                '-show_format', '-show_streams', file_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                
                # Extrahiere Audio-Stream Informationen
                audio_stream = None
                for stream in data.get('streams', []):
                    if stream.get('codec_type') == 'audio':
                        audio_stream = stream
                        break
                
                if audio_stream:
                    format_info = data.get('format', {})
                    
                    return {
                        'duration': float(format_info.get('duration', 0)),
                        'bitrate': int(format_info.get('bit_rate', 0)),
                        'sample_rate': int(audio_stream.get('sample_rate', 0)),
                        'channels': int(audio_stream.get('channels', 0)),
                        'codec': audio_stream.get('codec_name'),
                        'file_size': int(format_info.get('size', 0)),
                        'format_name': format_info.get('format_name'),
                        'file_path': file_path
                    }
            
            return None
            
        except Exception as e:
            logging.error(f"Audio-Feature-Extraktion fehlgeschlagen: {str(e)}")
            return None
    
    def create_audio_segment(self, file_path, start_seconds=30, duration_seconds=30):
        """
        Erstellt einen Audio-Segment für bessere Erkennung
        
        Args:
            file_path (str): Pfad zur Audio-Datei
            start_seconds (int): Start-Zeit in Sekunden
            duration_seconds (int): Dauer des Segments in Sekunden
            
        Returns:
            str: Pfad zum temporären Segment oder None
        """
        try:
            # Erstelle temporäre Datei
            temp_fd, temp_path = tempfile.mkstemp(suffix='.mp3', prefix='audio_segment_')
            os.close(temp_fd)
            
            # Verwende ffmpeg für Segment-Erstellung
            cmd = [
                'ffmpeg', '-i', file_path,
                '-ss', str(start_seconds),
                '-t', str(duration_seconds),
                '-acodec', 'copy',
                '-y', temp_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0 and os.path.exists(temp_path):
                return temp_path
            else:
                # Aufräumen bei Fehler
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                return None
                
        except Exception as e:
            logging.error(f"Audio-Segment-Erstellung fehlgeschlagen: {str(e)}")
            return None
    
    def cleanup_temp_file(self, temp_path):
        """Räumt temporäre Datei auf"""
        try:
            if temp_path and os.path.exists(temp_path):
                os.unlink(temp_path)
                logging.debug(f"Temporäre Datei gelöscht: {temp_path}")
        except Exception as e:
            logging.error(f"Fehler beim Löschen der temporären Datei: {str(e)}")


def get_audio_fingerprint_metadata(file_path):
    """
    Standalone-Funktion für Audio-Fingerprinting Metadaten
    
    Args:
        file_path (str): Pfad zur Audio-Datei
        
    Returns:
        dict: Gefundene Metadaten oder None
    """
    service = AudioFingerprintService()
    return service.get_audio_fingerprint_metadata(file_path)


def create_audio_fingerprint(file_path):
    """
    Standalone-Funktion für Fingerprint-Erstellung
    
    Args:
        file_path (str): Pfad zur Audio-Datei
        
    Returns:
        dict: Fingerprint-Daten oder None
    """
    service = AudioFingerprintService()
    return service.create_audio_fingerprint(file_path)


def compare_audio_files(file_path1, file_path2):
    """
    Standalone-Funktion für Audio-Datei-Vergleich
    
    Args:
        file_path1 (str): Pfad zur ersten Audio-Datei
        file_path2 (str): Pfad zur zweiten Audio-Datei
        
    Returns:
        dict: Vergleichsergebnis oder None
    """
    service = AudioFingerprintService()
    return service.compare_audio_fingerprints(file_path1, file_path2)


def extract_audio_features(file_path):
    """
    Standalone-Funktion für Audio-Feature-Extraktion
    
    Args:
        file_path (str): Pfad zur Audio-Datei
        
    Returns:
        dict: Audio-Features oder None
    """
    service = AudioFingerprintService()
    return service.extract_audio_features(file_path)
