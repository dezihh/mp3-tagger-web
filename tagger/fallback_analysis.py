#!/usr/bin/env python3
"""
Fallback-Analysemethoden für MP3-Dateien ohne ID3-Tags
- Verzeichnisstruktur-Analyse
- Dateiname-Pattern-Erkennung  
- Audio-Fingerprinting (ShazamIO/AcoustID/Chromaprint)
"""

import os
import re
from pathlib import Path
import logging
from typing import Dict, List, Optional, Tuple
import subprocess
import json
import requests
import eyed3
import asyncio

logger = logging.getLogger(__name__)

class FallbackAnalyzer:
    def __init__(self):
        # Audio-Fingerprinting Services (nach Qualität sortiert)
        self.acoustid_api_key = os.getenv('ACOUSTID_API_KEY')  # Völlig kostenlos, sekundär
        self.acrcloud_key = os.getenv('ACRCLOUD_KEY')  # 2000 free requests/month
        self.acrcloud_secret = os.getenv('ACRCLOUD_SECRET')
        self.acrcloud_host = os.getenv('ACRCLOUD_HOST')
        
        # ShazamIO - primärer Service (beste Ergebnisse)
        self.use_shazam = True
        
        # Backup: Offline-Fingerprinting für lokale Datenbanken
        self.use_local_fingerprinting = True
        
        # Häufige Verzeichnisstruktur-Pattern
        self.directory_patterns = [
            # Artist/Album/Track
            r'^(.+)[/\\](.+)[/\\](.+)\.mp3$',
            # Artist - Album/Track
            r'^(.+)\s*-\s*(.+)[/\\](.+)\.mp3$',
            # Music/Artist/Album/Track
            r'^[Mm]usic[/\\](.+)[/\\](.+)[/\\](.+)\.mp3$',
            # Genre/Artist/Album/Track  
            r'^(.+)[/\\](.+)[/\\](.+)[/\\](.+)\.mp3$'
        ]
        
        # Dateiname-Pattern für Artist - Title
        self.filename_patterns = [
            # "01 - Artist - Title.mp3" (Track-Nummer gefolgt von Artist - Title)
            r'^\d+[\.\-\s]+(.+?)\s*-\s*(.+?)\.mp3$',
            # "Artist - Title.mp3" (aber handle AC-DC, etc. smart)
            r'^(.+?)\s*-\s*(.+?)\.mp3$',
            # "Track01 Artist Title.mp3" (komplizierter - letztes Wort ist wahrscheinlich Title)
            r'^[Tt]rack\d+\s+(.+)\s+(\w+)\.mp3$',
            # "Artist_Title.mp3" (Underscore)
            r'^(.+?)_(.+?)\.mp3$'
        ]

    def analyze_path_structure(self, file_path: str) -> Dict[str, Optional[str]]:
        """
        Analysiert Verzeichnisstruktur und Dateiname für Artist/Album/Title-Informationen
        """
        result = {
            'artist': None,
            'album': None, 
            'title': None,
            'confidence': 0.0,
            'method': 'path_analysis'
        }
        
        try:
            # Normalisiere Pfad für Pattern-Matching
            normalized_path = file_path.replace('\\', '/')
            path_obj = Path(file_path)
            
            # 1. Versuche Verzeichnisstruktur-Pattern
            directory_info = self._analyze_directory_structure(normalized_path)
            if directory_info['confidence'] > 0:
                result.update(directory_info)
                logger.info(f"Verzeichnisstruktur erkannt: {directory_info}")
                
            # 2. Versuche Dateiname-Pattern (überschreibt nur fehlende Werte)
            filename_info = self._analyze_filename(path_obj.name)
            if filename_info['confidence'] > 0:
                # Kombiniere Ergebnisse - Dateiname für Artist/Title, Verzeichnis für Album
                if not result['artist'] and filename_info['artist']:
                    result['artist'] = filename_info['artist']
                if not result['title'] and filename_info['title']:
                    result['title'] = filename_info['title']
                    
                # Aktualisiere Confidence wenn Dateiname bessere Infos liefert
                if filename_info['confidence'] > result['confidence']:
                    result['confidence'] = filename_info['confidence']
                    
                logger.info(f"Dateiname analysiert: {filename_info}")
            
            # 3. Bereinige Ergebnisse
            result = self._clean_extracted_data(result)
            
        except Exception as e:
            logger.error(f"Fehler bei Pfad-Analyse für {file_path}: {e}")
            
        return result

    def _analyze_directory_structure(self, file_path: str) -> Dict[str, Optional[str]]:
        """Analysiert Verzeichnisstruktur für Artist/Album-Informationen"""
        result = {'artist': None, 'album': None, 'title': None, 'confidence': 0.0}
        
        try:
            # Extrahiere relevante Pfad-Teile (die letzten 3-4 Verzeichnisse)
            path_parts = file_path.split('/')
            if len(path_parts) >= 3:  # Mindestens Verzeichnis/Datei
                filename = path_parts[-1]
                parent_dir = path_parts[-2] if len(path_parts) >= 2 else None
                grandparent_dir = path_parts[-3] if len(path_parts) >= 3 else None
                great_grandparent_dir = path_parts[-4] if len(path_parts) >= 4 else None
                
                # Pattern: Artist/Album/Song.mp3
                if parent_dir and grandparent_dir:
                    # Prüfe ob Parent-Dir wie Album aussieht (enthält Jahr, Album-Keywords)
                    if self._looks_like_album(parent_dir) and not self._looks_like_generic_folder(grandparent_dir):
                        result['artist'] = self._clean_name(grandparent_dir)
                        result['album'] = self._clean_name(parent_dir)
                        result['confidence'] = 0.7
                        
                # Pattern: Artist - Album/Song.mp3  
                elif parent_dir and ' - ' in parent_dir:
                    parts = parent_dir.split(' - ', 1)
                    if len(parts) == 2:
                        result['artist'] = self._clean_name(parts[0])
                        result['album'] = self._clean_name(parts[1])
                        result['confidence'] = 0.8
                        
                # Pattern: Music/Artist/Album/Song.mp3
                elif great_grandparent_dir and parent_dir and grandparent_dir:
                    if (self._looks_like_generic_folder(great_grandparent_dir) and 
                        not self._looks_like_generic_folder(grandparent_dir) and
                        self._looks_like_album(parent_dir)):
                        result['artist'] = self._clean_name(grandparent_dir)
                        result['album'] = self._clean_name(parent_dir)
                        result['confidence'] = 0.6
                        
                # Fallback: Parent-Verzeichnis als Album (nur wenn es nicht generisch ist)
                elif parent_dir and not self._looks_like_generic_folder(parent_dir):
                    result['album'] = self._clean_name(parent_dir)
                    result['confidence'] = 0.4
                    
        except Exception as e:
            logger.error(f"Fehler bei Verzeichnisstruktur-Analyse: {e}")
            
        return result

    def _analyze_filename(self, filename: str) -> Dict[str, Optional[str]]:
        """Analysiert Dateiname für Artist/Title-Informationen"""
        result = {'artist': None, 'title': None, 'confidence': 0.0}
        
        try:
            for pattern in self.filename_patterns:
                match = re.match(pattern, filename, re.IGNORECASE)
                if match:
                    groups = match.groups()
                    if len(groups) >= 2:
                        artist_raw = self._clean_name(groups[0])
                        title_raw = self._clean_name(groups[1])
                        
                        # Spezialbehandlung für Bandnamen mit Bindestrichen (AC-DC, etc.)
                        if ' - ' in filename and not self._looks_like_band_with_dash(artist_raw):
                            # Normale Artist - Title Struktur
                            artist = artist_raw
                            title = title_raw
                        else:
                            # Könnte ein Band-Name mit Bindestrich sein
                            # Versuche intelligentere Trennung
                            artist, title = self._smart_split_artist_title(filename)
                            if not artist or not title:
                                artist = artist_raw
                                title = title_raw
                        
                        # Validiere Ergebnisse - prüfe auf sinnvolle Werte
                        if (artist and title and len(artist) > 1 and len(title) > 1 and
                            not self._looks_like_nonsense(artist, title)):
                            result['artist'] = artist
                            result['title'] = title
                            result['confidence'] = 0.8 if ' - ' in filename else 0.6
                            logger.info(f"Pattern erkannt: '{pattern}' -> Artist: {artist}, Title: {title}")
                            break
                            
        except Exception as e:
            logger.error(f"Fehler bei Dateiname-Analyse: {e}")
            
        return result

    def _looks_like_band_with_dash(self, name: str) -> bool:
        """Prüft ob der Name wie eine Band mit Bindestrich aussieht"""
        band_indicators = [
            r'^[A-Z]{2,4}-[A-Z]{2,4}$',  # AC-DC, DC-AC, etc.
            r'^.+-\w{1,3}$',  # Something-X
            r'^\w{1,3}-.+$',  # X-Something
        ]
        
        # Bekannte Bands mit Bindestrichen
        known_bands = ['ac-dc', 'dc-ac', 'x-ray', 'k-pop']
        
        return (any(re.match(pattern, name, re.IGNORECASE) for pattern in band_indicators) or
                name.lower() in known_bands)

    def _smart_split_artist_title(self, filename: str) -> Tuple[str, str]:
        """Intelligente Trennung von Artist und Title bei komplexen Namen"""
        filename_clean = filename.replace('.mp3', '')
        
        # Entferne Track-Nummern am Anfang
        filename_clean = re.sub(r'^\d+[\.\-\s]*', '', filename_clean)
        
        if ' - ' in filename_clean:
            parts = filename_clean.split(' - ')
            if len(parts) == 2:
                artist_candidate = parts[0]
                title_candidate = parts[1]
                
                # Prüfe auf bekannte Band-Pattern
                if self._looks_like_band_with_dash(artist_candidate):
                    return self._clean_name(artist_candidate), self._clean_name(title_candidate)
                    
                # Standard-Fall: Erste Teil ist Artist
                return self._clean_name(artist_candidate), self._clean_name(title_candidate)
                
            elif len(parts) > 2:
                # Mehr als 2 Teile - intelligente Kombination
                first_two = parts[0] + ' - ' + parts[1]
                if self._looks_like_band_with_dash(first_two):
                    # Kombiniere erste zwei Teile als Artist
                    artist = first_two
                    title = ' - '.join(parts[2:])
                    return self._clean_name(artist), self._clean_name(title)
                else:
                    # Standard: Erstes Teil = Artist, Rest = Title
                    artist = parts[0]
                    title = ' - '.join(parts[1:])
                    return self._clean_name(artist), self._clean_name(title)
        
        return '', ''

    def _looks_like_album(self, dirname: str) -> bool:
        """Prüft ob Verzeichnisname wie ein Album aussieht"""
        album_indicators = [
            r'\b(19|20)\d{2}\b',  # Jahr
            r'\b(album|ep|lp|single|compilation|greatest\s+hits)\b',
            r'\[.*\]',  # Eckige Klammern
            r'\(.*\)',  # Runde Klammern
        ]
        
        dirname_lower = dirname.lower()
        return any(re.search(pattern, dirname_lower) for pattern in album_indicators)

    def _looks_like_generic_folder(self, dirname: str) -> bool:
        """Prüft ob Verzeichnisname generisch ist"""
        generic_names = [
            'music', 'mp3', 'audio', 'songs', 'tracks', 'downloads', 
            'new folder', 'untitled', 'misc', 'various', 'unknown',
            'mixed', 'temp', 'tmp', 'test'
        ]
        return dirname.lower().strip() in generic_names

    def _looks_like_nonsense(self, artist: str, title: str) -> bool:
        """Prüft ob Artist/Title-Kombination unsinnig ist"""
        # Nonsense-Pattern
        nonsense_combinations = [
            ('ohne', 'id3'),
            ('test', 'mp3'),
            ('audio', 'file'),
            ('track', 'number'),
            ('unknown', 'title'),
            ('noname', 'mp3'),
            ('untitled', 'song')
        ]
        
        artist_lower = artist.lower().strip()
        title_lower = title.lower().strip()
        
        # Prüfe bekannte unsinnige Kombinationen
        if (artist_lower, title_lower) in nonsense_combinations:
            return True
            
        # Prüfe auf sehr kurze oder generische Namen
        if len(artist_lower) <= 2 or len(title_lower) <= 2:
            return True
            
        # Prüfe auf Zahlen-nur Pattern
        if artist_lower.isdigit() or title_lower.isdigit():
            return True
            
        # Prüfe auf identische Werte
        if artist_lower == title_lower:
            return True
            
        return False

    def _clean_name(self, name: str) -> str:
        """Bereinigt extrahierte Namen von unnötigen Zeichen"""
        if not name:
            return ''
            
        # Entferne häufige Prefixe/Suffixe
        name = re.sub(r'^\d+[\.\-\s]*', '', name)  # Track-Nummern
        name = re.sub(r'\s*\[.*?\]\s*', '', name)  # Eckige Klammern
        name = re.sub(r'\s*\(.*?\)\s*', '', name)  # Runde Klammern (optional)
        name = re.sub(r'[_]+', ' ', name)  # Underscores zu Leerzeichen
        name = re.sub(r'\s+', ' ', name)  # Multiple Leerzeichen
        
        return name.strip()

    def _clean_extracted_data(self, data: Dict) -> Dict:
        """Finale Bereinigung der extrahierten Daten"""
        for key in ['artist', 'album', 'title']:
            if data.get(key):
                cleaned = self._clean_name(data[key])
                data[key] = cleaned if len(cleaned) > 1 else None
                
        return data

    def analyze_audio_fingerprint(self, file_path: str) -> Dict[str, Optional[str]]:
        """
        Analysiert MP3 mit kostenlosen Audio-Fingerprinting Services
        """
        result = {
            'artist': None,
            'album': None,
            'title': None,
            'confidence': 0.0,
            'method': 'audio_fingerprint',
            'service': None,
            'acoustid': None,
            'musicbrainz_id': None,
            'cover_url': None,
            'genre': None,
            'year': None,
            'spotify_url': None,
            'youtube_url': None,
            'shazam_track_id': None
        }
        
        # Versuche Services in Reihenfolge der Qualität
        services_to_try = []
        
        # 1. ShazamIO (primär - beste Ergebnisse mit umfangreichen Metadaten)
        if self.use_shazam:
            services_to_try.append(('shazam', self._try_shazam))
        
        # 2. AcoustID (sekundär - kostenlos, gut)
        if self.acoustid_api_key:
            services_to_try.append(('acoustid', self._try_acoustid))
        
        # 3. ACRCloud (2000 free requests/month)
        if self.acrcloud_key and self.acrcloud_secret:
            services_to_try.append(('acrcloud', self._try_acrcloud))
            
        # 3. Lokales Fingerprinting (immer verfügbar)
        if self.use_local_fingerprinting:
            services_to_try.append(('local_fingerprint', self._try_local_fingerprint))
            
        for service_name, service_func in services_to_try:
            try:
                logger.info(f"🎵 Versuche Audio-Fingerprinting mit {service_name}")
                service_result = service_func(file_path)
                
                if service_result and service_result.get('confidence', 0) > result['confidence']:
                    result.update(service_result)
                    result['service'] = service_name
                    logger.info(f"✅ {service_name} erfolgreich: {service_result.get('artist')} - {service_result.get('title')}")
                    
                    # Bei hoher Confidence: stoppe hier
                    if result['confidence'] > 0.8:
                        break
                        
            except Exception as e:
                logger.error(f"❌ {service_name} Fehler: {e}")
                continue
                
        return result

    def _try_shazam(self, file_path: str) -> Optional[Dict]:
        """ShazamIO - primärer Service mit umfangreichen Metadaten"""
        try:
            # Dynamischer Import von ShazamIO (falls nicht verfügbar: skip)
            try:
                from shazamio import Shazam
            except ImportError:
                logger.warning("ShazamIO nicht installiert - überspringe Shazam-Service")
                return None
                
            # Asynchrone Shazam-Erkennung mit verbesserter Fehlerbehandlung
            async def recognize_with_shazam():
                shazam = Shazam()
                
                # Mehrere Versuche mit unterschiedlichen Segmenten
                attempts = [
                    {"name": "Standard", "offset": 0},
                    {"name": "Mitte", "offset": 30},
                    {"name": "Späte Mitte", "offset": 60}
                ]
                
                for attempt in attempts:
                    try:
                        logger.info(f"🎵 Shazam-Versuch '{attempt['name']}' für {os.path.basename(file_path)}")
                        
                        # Versuche mit unterschiedlichen Offsets
                        if attempt["offset"] > 0:
                            # Für längere Offsets: verwende standard recognize
                            result = await shazam.recognize(file_path)
                        else:
                            result = await shazam.recognize(file_path)
                        
                        if result and 'track' in result and result['track']:
                            track_title = result.get('track', {}).get('title', 'Unknown')
                            track_artist = result.get('track', {}).get('subtitle', 'Unknown')
                            logger.info(f"✅ Shazam '{attempt['name']}' erfolgreich: {track_artist} - {track_title}")
                            return result
                        else:
                            logger.info(f"🔍 Shazam '{attempt['name']}': Kein verwertbares Ergebnis")
                            
                    except Exception as e:
                        logger.info(f"⚠️  Shazam '{attempt['name']}' Fehler: {e}")
                        continue
                
                logger.info("🔍 Alle Shazam-Versuche erschöpft")
                return None
            
            # Führe asynchrone Funktion aus mit robustem Event-Loop-Handling
            try:
                # Versuche, vorhandenen Event-Loop zu verwenden
                loop = asyncio.get_running_loop()
                # Event-Loop läuft bereits - verwende Thread
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, recognize_with_shazam())
                    shazam_result = future.result(timeout=45)  # Längerer Timeout
            except RuntimeError:
                # Kein Event-Loop läuft - erstelle neuen
                shazam_result = asyncio.run(recognize_with_shazam())
            
            if shazam_result and 'track' in shazam_result:
                return self._extract_shazam_metadata(shazam_result)
            else:
                logger.info("🔍 Shazam: Keine verwertbare Übereinstimmung gefunden")
                return None
                
        except Exception as e:
            logger.error(f"❌ ShazamIO Fehler: {e}")
            return None

    def _try_acoustid(self, file_path: str) -> Optional[Dict]:
        """AcoustID - sekundärer Service (kostenlos)"""
        try:
            fingerprint_data = self._generate_fingerprint(file_path)
            if not fingerprint_data:
                return None
                
            return self._lookup_acoustid(fingerprint_data)
        except Exception as e:
            logger.error(f"AcoustID Fehler: {e}")
            return None

    def _try_acrcloud(self, file_path: str) -> Optional[Dict]:
        """ACRCloud - 2000 kostenlose Anfragen/Monat"""
        try:
            import hmac
            import hashlib
            import base64
            import time
            
            # ACRCloud Audio-Fingerprint generieren
            fingerprint_data = self._generate_acrcloud_fingerprint(file_path)
            if not fingerprint_data:
                return None
                
            # API Request
            timestamp = str(int(time.time()))
            string_to_sign = f"POST\n/v1/identify\n{self.acrcloud_key}\naudio\n1\n{timestamp}"
            signature = base64.b64encode(
                hmac.new(
                    self.acrcloud_secret.encode('utf-8'),
                    string_to_sign.encode('utf-8'),
                    hashlib.sha1
                ).digest()
            ).decode('utf-8')
            
            headers = {
                'X-Signature': signature,
                'X-Timestamp': timestamp,
                'X-API-Key': self.acrcloud_key
            }
            
            files = {'sample': open(file_path, 'rb')}
            
            response = requests.post(
                f"https://{self.acrcloud_host}/v1/identify",
                files=files,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return self._parse_acrcloud_response(data)
                
        except Exception as e:
            logger.error(f"ACRCloud Fehler: {e}")
            
        return None

    def _try_local_fingerprint(self, file_path: str) -> Optional[Dict]:
        """Lokales Fingerprinting ohne externe API"""
        try:
            # Generiere lokalen Audio-Fingerprint
            fingerprint_data = self._generate_fingerprint(file_path)
            if not fingerprint_data:
                return None
                
            # Einfache lokale Analyse basierend auf Audio-Eigenschaften
            duration = fingerprint_data.get('duration', 0)
            fingerprint = fingerprint_data.get('fingerprint', '')
            
            # Basis-Metadata aus Audio-Eigenschaften ableiten
            if duration > 0:
                # Grobe Schätzungen basierend auf typischen Musiklängen
                if 120 < duration < 300:  # 2-5 Minuten = typischer Song
                    confidence = 0.3
                elif 180 < duration < 420:  # 3-7 Minuten = sehr typisch
                    confidence = 0.4
                else:
                    confidence = 0.2
                    
                return {
                    'artist': None,  # Lokal nicht ermittelbar
                    'title': None,   # Lokal nicht ermittelbar
                    'album': None,
                    'confidence': confidence,
                    'duration': duration,
                    'local_fingerprint': fingerprint[:50],  # Kurzer Hash für Vergleiche
                    'estimated_type': 'music' if 120 < duration < 600 else 'unknown'
                }
                
        except Exception as e:
            logger.error(f"Lokales Fingerprinting Fehler: {e}")
            
        return None

    def _generate_acrcloud_fingerprint(self, file_path: str) -> Optional[Dict]:
        """Generiert ACRCloud-kompatiblen Fingerprint"""
        # ACRCloud nutzt eigenes Format, aber wir können Standard-Audio-Features nutzen
        return self._generate_fingerprint(file_path)

    def _parse_acrcloud_response(self, data: Dict) -> Optional[Dict]:
        """Parst ACRCloud API Response"""
        try:
            if data.get('status', {}).get('code') == 0:  # Erfolg
                music = data.get('metadata', {}).get('music', [])
                if music:
                    track = music[0]  # Beste Übereinstimmung
                    return {
                        'artist': track.get('artists', [{}])[0].get('name'),
                        'title': track.get('title'),
                        'album': track.get('album', {}).get('name'),
                        'confidence': min(track.get('score', 0) / 100.0, 1.0),
                        'release_date': track.get('release_date'),
                        'genres': [genre.get('name') for genre in track.get('genres', [])]
                    }
        except Exception as e:
            logger.error(f"ACRCloud Response Parse Fehler: {e}")
            
        return None

    def _generate_fingerprint(self, file_path: str) -> Optional[Dict]:
        """Generiert Audio-Fingerprint mit fpcalc"""
        try:
            # Prüfe ob fpcalc verfügbar ist
            result = subprocess.run(['fpcalc', '-version'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode != 0:
                logger.warning("fpcalc nicht gefunden - installiere chromaprint-tools")
                return None
                
            # Generiere Fingerprint
            result = subprocess.run([
                'fpcalc', '-json', '-length', '120', file_path
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                return {
                    'duration': data.get('duration'),
                    'fingerprint': data.get('fingerprint')
                }
            else:
                logger.error(f"fpcalc Fehler: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            logger.error(f"fpcalc Timeout für {file_path}")
        except FileNotFoundError:
            logger.warning("fpcalc nicht installiert - Audio-Fingerprinting nicht verfügbar")
        except Exception as e:
            logger.error(f"Fehler bei Fingerprint-Generierung: {e}")
            
        return None

    def _lookup_acoustid(self, fingerprint_data: Dict) -> Optional[Dict]:
        """Lookup bei AcoustID API mit korrigierten Parametern"""
        try:
            url = "https://api.acoustid.org/v2/lookup"
            params = {
                'client': self.acoustid_api_key,
                'meta': 'recordings',  # Korrigiert: nur recordings funktioniert stabil
                'duration': int(fingerprint_data['duration']),  # Konvertiere zu int
                'fingerprint': fingerprint_data['fingerprint']
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if data.get('status') == 'ok' and data.get('results'):
                # Nimm das beste Ergebnis (höchste Score)
                best_result = max(data['results'], key=lambda x: x.get('score', 0))
                
                if best_result.get('score', 0) > 0.8:  # Hohe Konfidenz erforderlich
                    return self._extract_acoustid_metadata(best_result)
                    
        except Exception as e:
            logger.error(f"AcoustID Lookup Fehler: {e}")
            
        return None

    def _extract_acoustid_metadata(self, acoustid_result: Dict) -> Dict:
        """Extrahiert Metadaten aus AcoustID-Ergebnis"""
        result = {
            'artist': None,
            'album': None,
            'title': None,
            'confidence': acoustid_result.get('score', 0),
            'acoustid': acoustid_result.get('id'),
            'musicbrainz_id': None
        }
        
        try:
            recordings = acoustid_result.get('recordings', [])
            if recordings:
                # Nimm die erste/beste Aufnahme
                recording = recordings[0]
                result['title'] = recording.get('title')
                result['musicbrainz_id'] = recording.get('id')
                
                # Extrahiere Artist-Info
                artists = recording.get('artists', [])
                if artists:
                    result['artist'] = artists[0].get('name')
                
                # Extrahiere Album-Info aus Releases
                releases = recording.get('releases', [])
                if releases:
                    result['album'] = releases[0].get('title')
                    
        except Exception as e:
            logger.error(f"Fehler bei AcoustID Metadaten-Extraktion: {e}")
            
        return result

    def _extract_shazam_metadata(self, shazam_result: Dict) -> Dict:
        """Extrahiert Metadaten aus ShazamIO-Ergebnis"""
        result = {
            'artist': None,
            'album': None,
            'title': None,
            'confidence': 0.95,  # Shazam hat sehr hohe Genauigkeit
            'cover_url': None,
            'genre': None,
            'year': None,
            'spotify_url': None,
            'youtube_url': None,
            'shazam_track_id': None
        }
        
        try:
            track = shazam_result.get('track', {})
            
            # Basis-Metadaten
            result['title'] = track.get('title')
            result['artist'] = track.get('subtitle')  # Bei Shazam ist subtitle der Artist
            result['shazam_track_id'] = track.get('key')
            
            # Cover-Art
            images = track.get('images', {})
            if images:
                # Nimm das größte verfügbare Cover
                cover_url = images.get('coverarthq') or images.get('coverart') or images.get('background')
                if cover_url:
                    result['cover_url'] = cover_url
            
            # Album und erweiterte Metadaten
            sections = track.get('sections', [])
            for section in sections:
                if section.get('type') == 'SONG':
                    metadata = section.get('metadata', [])
                    for meta in metadata:
                        if meta.get('title') == 'Album':
                            result['album'] = meta.get('text')
                        elif meta.get('title') == 'Released':
                            result['year'] = meta.get('text')
                        elif meta.get('title') == 'Genre':
                            result['genre'] = meta.get('text')
            
            # Streaming-Links
            hub = track.get('hub', {})
            providers = hub.get('providers', [])
            for provider in providers:
                if 'spotify' in provider.get('type', '').lower():
                    result['spotify_url'] = provider.get('actions', [{}])[0].get('uri')
                elif 'youtube' in provider.get('type', '').lower():
                    result['youtube_url'] = provider.get('actions', [{}])[0].get('uri')
                    
            # Fallback für Streaming-Links aus options
            options = hub.get('options', [])
            for option in options:
                if 'spotify' in option.get('caption', '').lower():
                    actions = option.get('actions', [])
                    if actions:
                        result['spotify_url'] = actions[0].get('uri')
                elif 'youtube' in option.get('caption', '').lower():
                    actions = option.get('actions', [])
                    if actions:
                        result['youtube_url'] = actions[0].get('uri')
                        
        except Exception as e:
            logger.error(f"Fehler bei Shazam Metadaten-Extraktion: {e}")
            
        return result

    def get_fallback_suggestions(self, file_path: str) -> List[Dict]:
        """
        OPTIMIERTE Fallback-Strategien - Audio-Fingerprinting nur als letzter Fallback
        
        Hierarchie:
        1. Pfad/Dateiname-Analyse (schnell, kostenlos)
        2. Erweiterte Dateiname-Heuristiken (schnell, kostenlos)  
        3. Audio-Eigenschaften-Analyse (schnell, kostenlos)
        4. Audio-Fingerprinting (rechenintensiv, nur bei Bedarf)
        """
        suggestions = []
        
        logger.info(f"🔍 Starte optimierte Fallback-Kette für: {Path(file_path).name}")
        
        # 1. PFAD/DATEINAME-ANALYSE (Priorität 1 - schnell und oft erfolgreich)
        try:
            path_result = self.analyze_path_structure(file_path)
            if path_result and path_result['confidence'] > 0.0:
                suggestions.append(path_result)
                logger.info(f"📁 Pfad-Analyse: {path_result['artist']} - {path_result['title']} "
                           f"(Confidence: {path_result['confidence']:.2f})")
        except Exception as e:
            logger.warning(f"Pfad-Analyse fehlgeschlagen: {e}")
            
        # 2. ERWEITERTE DATEINAME-HEURISTIKEN (Priorität 2 - bessere Pattern)
        try:
            enhanced_filename_result = self._analyze_filename_enhanced(file_path)
            if enhanced_filename_result and enhanced_filename_result['confidence'] > 0.0:
                suggestions.append(enhanced_filename_result)
                logger.info(f"📝 Erweiterte Dateiname-Analyse: {enhanced_filename_result['artist']} - {enhanced_filename_result['title']} "
                           f"(Confidence: {enhanced_filename_result['confidence']:.2f})")
        except Exception as e:
            logger.warning(f"Erweiterte Dateiname-Analyse fehlgeschlagen: {e}")
            
        # 3. AUDIO-EIGENSCHAFTEN (Priorität 3 - partielle Tag-Wiederherstellung)
        try:
            audio_analysis_result = self._analyze_audio_properties(file_path)
            if audio_analysis_result and audio_analysis_result['confidence'] > 0.0:
                suggestions.append(audio_analysis_result)
                logger.info(f"🎵 Audio-Eigenschaften: {audio_analysis_result['artist']} - {audio_analysis_result['title']} "
                           f"(Confidence: {audio_analysis_result['confidence']:.2f})")
        except Exception as e:
            logger.warning(f"Audio-Eigenschaften-Analyse fehlgeschlagen: {e}")
        
        # Prüfe ob bereits gute Ergebnisse vorliegen
        if suggestions:
            best_confidence = max(s['confidence'] for s in suggestions)
            logger.info(f"Bisherige beste Confidence: {best_confidence:.2f}")
            
            # 4. AUDIO-FINGERPRINTING (Nur wenn andere Methoden unzureichend)
            if best_confidence < 0.6:  # Nur bei unzureichenden Ergebnissen
                logger.info(f"🎯 Audio-Fingerprinting aktiviert (beste bisherige Confidence: {best_confidence:.2f})")
                
                try:
                    fingerprint_result = self.analyze_audio_fingerprint(file_path)
                    if fingerprint_result and fingerprint_result['confidence'] > 0.0:
                        suggestions.append(fingerprint_result)
                        logger.info(f"🎯 Audio-Fingerprinting: {fingerprint_result['artist']} - {fingerprint_result['title']} "
                                   f"(Confidence: {fingerprint_result['confidence']:.2f})")
                except Exception as e:
                    logger.warning(f"Audio-Fingerprinting fehlgeschlagen: {e}")
            else:
                logger.info(f"✅ Audio-Fingerprinting übersprungen - ausreichende Confidence ({best_confidence:.2f})")
        else:
            # Keine anderen Methoden erfolgreich - Audio-Fingerprinting als letzter Versuch
            logger.info(f"🎯 Audio-Fingerprinting als letzter Fallback")
            try:
                fingerprint_result = self.analyze_audio_fingerprint(file_path)
                if fingerprint_result and fingerprint_result['confidence'] > 0.0:
                    suggestions.append(fingerprint_result)
                    logger.info(f"🎯 Audio-Fingerprinting (letzter Fallback): {fingerprint_result['artist']} - {fingerprint_result['title']} "
                               f"(Confidence: {fingerprint_result['confidence']:.2f})")
            except Exception as e:
                logger.warning(f"Audio-Fingerprinting (letzter Fallback) fehlgeschlagen: {e}")
        
        # Sortiere nach Confidence (höchste zuerst)
        suggestions.sort(key=lambda x: x['confidence'], reverse=True)
        
        if suggestions:
            logger.info(f"✅ Fallback-Ergebnisse für {Path(file_path).name}: "
                        f"{len(suggestions)} Vorschläge, beste Confidence: {suggestions[0]['confidence']:.2f} "
                        f"(Methode: {suggestions[0].get('method', 'unknown')})")
        else:
            logger.warning(f"❌ Keine Fallback-Ergebnisse für {Path(file_path).name}")
        
        return suggestions

    def _analyze_filename_enhanced(self, file_path: str) -> Dict[str, Optional[str]]:
        """Erweiterte Dateiname-Analyse mit mehr Heuristiken"""
        result = {'artist': None, 'title': None, 'album': None, 'confidence': 0.0, 'method': 'enhanced_filename'}
        
        try:
            filename = os.path.basename(file_path).replace('.mp3', '')
            
            # Erweiterte Pattern für schwierige Fälle
            enhanced_patterns = [
                # "Band Name feat. Other Artist - Song Title"
                r'^(.+?)\s+feat\.\s+.+?\s*-\s*(.+?)$',
                # "Song Title by Artist Name"
                r'^(.+?)\s+by\s+(.+?)$',
                # "Artist - Album - Track"
                r'^(.+?)\s*-\s*(.+?)\s*-\s*(.+?)$',
                # Numbers and special chars
                r'^\d+\s*[\.\-]\s*(.+?)\s*[\.\-]\s*(.+?)$',
            ]
            
            for pattern in enhanced_patterns:
                match = re.match(pattern, filename, re.IGNORECASE)
                if match:
                    groups = match.groups()
                    
                    if len(groups) == 2:
                        # Standard Artist - Title
                        candidate_artist = self._clean_name(groups[0]) 
                        candidate_title = self._clean_name(groups[1])
                        
                        # Swap wenn "by Artist" Pattern
                        if 'by' in pattern:
                            candidate_artist, candidate_title = candidate_title, candidate_artist
                            
                    elif len(groups) == 3:
                        # Artist - Album - Title
                        candidate_artist = self._clean_name(groups[0])
                        result['album'] = self._clean_name(groups[1])
                        candidate_title = self._clean_name(groups[2])
                    else:
                        continue
                        
                    if (candidate_artist and candidate_title and 
                        not self._looks_like_nonsense(candidate_artist, candidate_title)):
                        result['artist'] = candidate_artist
                        result['title'] = candidate_title  
                        result['confidence'] = 0.7
                        logger.info(f"Enhanced Pattern erkannt: {candidate_artist} - {candidate_title}")
                        break
                        
        except Exception as e:
            logger.error(f"Enhanced Filename Analysis Fehler: {e}")
            
        return result

    def _analyze_audio_properties(self, file_path: str) -> Dict[str, Optional[str]]:
        """Analysiert Audio-Eigenschaften ohne externe Services"""
        result = {'artist': None, 'title': None, 'album': None, 'confidence': 0.0, 'method': 'audio_properties'}
        
        try:
            # Lade Audio-Datei für Basis-Analyse
            audio = eyed3.load(file_path)
            if not audio:
                return result
                
            # Extrahiere verfügbare Informationen auch aus beschädigten/partiellen Tags
            partial_info = {}
            
            if audio.info:
                partial_info['duration'] = audio.info.time_secs
                partial_info['bitrate'] = audio.info.bit_rate[1] if audio.info.bit_rate else None
                partial_info['sample_rate'] = audio.info.sample_freq
                
            # Versuche auch beschädigte Tags zu lesen
            if audio.tag:
                # Manchmal sind nur Teile der Tags lesbar
                try:
                    if hasattr(audio.tag, '_raw_data'):
                        # Versuche rohe Tag-Daten zu parsen
                        raw_artist = getattr(audio.tag, 'artist', None)
                        raw_title = getattr(audio.tag, 'title', None)
                        
                        if raw_artist and len(str(raw_artist).strip()) > 1:
                            partial_info['artist'] = str(raw_artist).strip()
                        if raw_title and len(str(raw_title).strip()) > 1:
                            partial_info['title'] = str(raw_title).strip()
                            
                except Exception:
                    pass
                    
            # Bewerte gefundene Informationen
            confidence = 0.0
            if partial_info.get('artist') and partial_info.get('title'):
                confidence = 0.5  # Partielle Tag-Wiederherstellung
            elif partial_info.get('duration'):
                # Audio ist gültig, auch wenn Tags fehlen
                duration = partial_info['duration']
                if 60 < duration < 600:  # 1-10 Minuten = wahrscheinlich Musik
                    confidence = 0.2
                    
            if confidence > 0:
                result.update({
                    'artist': partial_info.get('artist'),
                    'title': partial_info.get('title'),
                    'confidence': confidence,
                    'audio_duration': partial_info.get('duration'),
                    'audio_bitrate': partial_info.get('bitrate'),
                    'audio_sample_rate': partial_info.get('sample_rate')
                })
                
        except Exception as e:
            logger.error(f"Audio Properties Analysis Fehler: {e}")
            
        return result
