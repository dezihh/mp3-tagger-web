"""
MP3 Metadaten-Verarbeitung für den MP3 Tagger Web Application

Dieses Modul stellt die Kernfunktionalität für die Verarbeitung von MP3-Dateien bereit:
- MP3-Datei-Scanning und Metadaten-Extraktion
- ID3-Tag-Management (Lesen, Schreiben, Validierung)
- Cover-Art-Verarbeitung mit Größenanalyse
- Audio-Erkennung-Integration (AcoustID, Shazam)
- Album-Erkennung-Integration (MusicBrainz, Discogs)

Hauptklassen:
- MP3FileInfo: Datenklasse für MP3-Metadaten mit Recognition-Features
- Utility-Funktionen für Batch-Verarbeitung und Dateisystem-Integration

Verwendung:
    from tagger.mp3_processor import scan_directory, save_mp3_tags
    
    # Verzeichnis scannen
    files = scan_directory('/path/to/mp3s')
    
    # Tags speichern
    results = save_mp3_tags(files_data)
"""

import os
import re
from io import BytesIO
from mutagen.mp3 import MP3
from PIL import Image
from mutagen.id3 import ID3NoHeaderError
from typing import Dict, List, Any, Optional, Tuple
from .utils import is_mp3_file


def get_image_dimensions_from_data(image_data: bytes) -> tuple:
    """
    Ermittelt die Abmessungen eines Bildes aus Binärdaten.
    
    Args:
        image_data: Binärdaten des Bildes
        
    Returns:
        Tuple (width, height) oder (0, 0) bei Fehlern
    """
    try:
        with Image.open(BytesIO(image_data)) as img:
            return img.size  # (width, height)
    except Exception:
        return (0, 0)


def get_image_dimensions_from_file(file_path: str) -> tuple:
    """
    Ermittelt die Abmessungen einer Bilddatei.
    
    Args:
        file_path: Pfad zur Bilddatei
        
    Returns:
        Tuple (width, height) oder (0, 0) bei Fehlern
    """
    try:
        with Image.open(file_path) as img:
            return img.size  # (width, height)
    except Exception:
        return (0, 0)


class MP3FileInfo:
    """Klasse zur Repräsentation einer MP3-Datei mit Metadaten und Audio-Erkennung."""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.filename = os.path.basename(file_path)
        self.directory = os.path.dirname(file_path)
        self.relative_directory = ""
        self.size = 0
        self.track_number = ""
        self.title = ""
        self.artist = ""
        self.album = ""
        self.year = ""
        self.genre = ""
        self.cover_status = "Nein"
        
        # Audio-Erkennungsergebnisse für fehlende Tags
        self.recognized_title = None
        self.recognized_artist = None
        self.recognition_source = None
        self.needs_recognition = False
        
        # Album-Erkennungsergebnisse
        self.album_recognized = False
        self.recognized_album = None
        self.recognized_year = None
        self.recognized_track_number = None
        
        # Erweiterte Metadaten (ID3v2.4 Tags)
        self.extended_metadata = {
            'release_date': None,           # TDRC - Release-Datum
            'bpm': None,                    # TBPM - BPM
            'genres': [],                   # TCON - Erweiterte Genres
            'mood': [],                     # TMOO - Stimmung/Mood
            'similar_artists': [],          # Ähnliche Künstler (custom)
            'energy': None,                 # Audio-Feature: Energy (0.0-1.0)
            'danceability': None,           # Audio-Feature: Danceability (0.0-1.0)
            'valence': None,                # Audio-Feature: Valence/Positivität (0.0-1.0)
            'acousticness': None,           # Audio-Feature: Acousticness (0.0-1.0)
            'instrumentalness': None,       # Audio-Feature: Instrumentalness (0.0-1.0)
            'liveness': None,               # Audio-Feature: Liveness (0.0-1.0)
            'speechiness': None,            # Audio-Feature: Speechiness (0.0-1.0)
            'loudness': None,               # Audio-Feature: Loudness (dB)
            'key': None,                    # Tonart (0-11)
            'mode': None,                   # Dur/Moll (0/1)
            'time_signature': None,         # Taktart
            'popularity': None,             # Popularity-Score
            'tags': [],                     # Last.fm Tags
            'has_extended_data': False      # Flag für erweiterte Daten
        }
        
        self._load_file_info()
        self._load_id3_tags()
        self._detect_cover()
        self._check_recognition_needed()
    
    def _check_recognition_needed(self):
        """Prüft, ob Audio-Erkennung für fehlende Tags benötigt wird."""
        self.needs_recognition = not self.title.strip() or not self.artist.strip()
    
    def _load_file_info(self):
        """Lädt grundlegende Dateiinformationen."""
        try:
            self.size = os.path.getsize(self.file_path)
        except OSError:
            self.size = 0
    
    def _load_id3_tags(self):
        """Lädt ID3-Tags aus der MP3-Datei, inklusive erweiterte Metadaten."""
        try:
            audio = MP3(self.file_path)
            
            # Basis-Tags
            # Track-Nummer
            if 'TRCK' in audio:
                track = str(audio['TRCK'][0])
                # Extrahiere nur die Tracknummer (vor dem '/')
                if '/' in track:
                    track = track.split('/')[0]
                self.track_number = track.zfill(2)  # Mit führender Null
            
            # Titel
            if 'TIT2' in audio:
                self.title = str(audio['TIT2'][0])
            
            # Künstler
            if 'TPE1' in audio:
                self.artist = str(audio['TPE1'][0])
            
            # Album
            if 'TALB' in audio:
                self.album = str(audio['TALB'][0])
            
            # Jahr
            if 'TDRC' in audio:  # ID3v2.4
                self.year = str(audio['TDRC'][0])
            elif 'TYER' in audio:  # ID3v2.3
                self.year = str(audio['TYER'][0])
            else:
                # Fallback: Jahr aus TXXX:RELEASE_DATE extrahieren
                for tag_name, tag_value in audio.items():
                    if tag_name.startswith('TXXX:') and 'RELEASE_DATE' in tag_name:
                        release_date = str(tag_value[0])
                        # Jahr aus Datum extrahieren (YYYY-MM-DD -> YYYY)
                        if len(release_date) >= 4 and release_date[:4].isdigit():
                            self.year = release_date[:4]
                            print(f"📅 Jahr aus {tag_name} extrahiert: {self.year}")
                            break
            
            # Genre
            if 'TCON' in audio:
                self.genre = str(audio['TCON'][0])
            
            # Erweiterte Metadaten laden
            self._load_extended_id3_tags(audio)
                
        except (ID3NoHeaderError, Exception):
            # Fallback: Versuche Informationen aus Dateinamen zu extrahieren
            self._parse_filename()
    
    def _load_extended_id3_tags(self, audio):
        """Lädt erweiterte ID3v2.4 Tags."""
        try:
            # Release-Datum
            if 'TDRC' in audio:
                self.extended_metadata['release_date'] = str(audio['TDRC'][0])
            
            # BPM
            if 'TBPM' in audio:
                try:
                    self.extended_metadata['bpm'] = float(audio['TBPM'][0])
                except ValueError:
                    pass
            
            # Mood (Legacy TMOO Tag)
            if 'TMOO' in audio:
                mood_str = str(audio['TMOO'][0])
                self.extended_metadata['mood'] = [m.strip() for m in mood_str.split(',')]
            
            # Erweiterte Genres (zusätzlich zu TCON)
            if 'TCON' in audio:
                genre_str = str(audio['TCON'][0])
                # Genres können durch '/' oder ';' getrennt sein
                genres = [g.strip() for g in genre_str.replace('/', ';').split(';')]
                self.extended_metadata['genres'] = [g for g in genres if g]
            
            # TXXX (User-defined) Tags für erweiterte Metadaten
            for tag_key, tag_value in audio.items():
                if tag_key.startswith('TXXX:') and hasattr(tag_value, 'desc'):
                    desc = tag_value.desc
                    value = str(tag_value.text[0]) if tag_value.text else ''
                    
                    if desc == 'EXTENDED_GENRES' and value:
                        extended_genres = [g.strip() for g in value.split(',')]
                        existing_genres = self.extended_metadata.get('genres', [])
                        # Kombiniere Standard-Genres mit erweiterten Genres
                        all_genres = list(set(existing_genres + extended_genres))
                        self.extended_metadata['genres'] = all_genres
                    
                    elif desc == 'MOOD' and value:
                        # Mood als String speichern (nicht als Liste)
                        self.extended_metadata['mood'] = value
                    
                    elif desc == 'SIMILAR_ARTISTS' and value:
                        self.extended_metadata['similar_artists'] = [a.strip() for a in value.split(',')]
                    
                    elif desc == 'SIMILAR_ARTIST' and value:  # GUI verwendet singular
                        self.extended_metadata['similar_artist'] = value
                    
                    elif desc == 'ENERGY' and value:
                        try:
                            self.extended_metadata['energy'] = float(value)
                        except ValueError:
                            self.extended_metadata['energy'] = value
                    
                    elif desc == 'DANCEABILITY' and value:
                        try:
                            self.extended_metadata['danceability'] = float(value)
                        except ValueError:
                            self.extended_metadata['danceability'] = value
                    
                    elif desc == 'URL' and value:
                        self.extended_metadata['url'] = value
                    
                    elif desc == 'ERA' and value:
                        self.extended_metadata['era'] = value
                    
                    elif desc == 'STYLE' and value:
                        self.extended_metadata['style'] = value
                    
                    elif desc == 'ENERGY_LEVEL' and value:
                        # Als String beibehalten für Konsistenz
                        self.extended_metadata['energy_level'] = value
                    
                    elif desc == 'AUDIO_FEATURES' and value:
                        # Parse Audio Features: "energy:0.825, danceability:0.742, valence:0.893"
                        for feature_str in value.split(','):
                            if ':' in feature_str:
                                feature_name, feature_value = feature_str.strip().split(':', 1)
                                try:
                                    self.extended_metadata[feature_name] = float(feature_value)
                                except ValueError:
                                    pass
                    
                    elif desc == 'TAGS' and value:
                        self.extended_metadata['tags'] = [t.strip() for t in value.split(',')]
                    
                    elif desc == 'RELEASE_DATE' and value:
                        self.extended_metadata['release_date'] = value
                    
                    elif desc == 'POPULARITY' and value:
                        try:
                            self.extended_metadata['popularity'] = int(value)
                        except ValueError:
                            pass
            
            # Legacy Custom Tags für Audio Features (Rückwärtskompatibilität)
            legacy_fields = [
                'TXXX:ENERGY', 'TXXX:DANCEABILITY', 'TXXX:VALENCE',
                'TXXX:ACOUSTICNESS', 'TXXX:INSTRUMENTALNESS', 'TXXX:LIVENESS',
                'TXXX:SPEECHINESS', 'TXXX:LOUDNESS', 'TXXX:KEY', 'TXXX:MODE',
                'TXXX:TIME_SIGNATURE', 'TXXX:POPULARITY', 'TXXX:SIMILAR_ARTISTS'
            ]
            
            for field in legacy_fields:
                if field in audio:
                    field_name = field.split(':')[1].lower()
                    value = str(audio[field][0])
                    
                    if field_name in ['energy', 'danceability', 'valence', 'acousticness', 
                                    'instrumentalness', 'liveness', 'speechiness']:
                        try:
                            self.extended_metadata[field_name] = float(value)
                        except ValueError:
                            pass
                    elif field_name in ['loudness']:
                        try:
                            self.extended_metadata[field_name] = float(value)
                        except ValueError:
                            pass
                    elif field_name in ['key', 'mode', 'time_signature', 'popularity']:
                        try:
                            self.extended_metadata[field_name] = int(value)
                        except ValueError:
                            pass
                    elif field_name == 'similar_artists':
                        self.extended_metadata['similar_artists'] = [a.strip() for a in value.split(',')]
            
            # Weitere Standard-Tags für Advanced Metadata
            # Rating (POPM)
            for key in audio.keys():
                if key.startswith('POPM'):
                    try:
                        rating = audio[key].rating
                        if rating > 0:
                            self.extended_metadata['rating'] = str(int(rating / 51))  # 0-255 -> 0-5
                        break
                    except:
                        pass
            
            # Comment (COMM)
            if 'COMM::eng' in audio:
                self.extended_metadata['comment'] = str(audio['COMM::eng'].text[0])
            elif 'COMM' in audio:
                # Fallback für COMM ohne spezifische Sprache
                for key in audio.keys():
                    if key.startswith('COMM:'):
                        self.extended_metadata['comment'] = str(audio[key].text[0])
                        break
            
            # Lyrics (USLT)
            if 'USLT::eng' in audio:
                self.extended_metadata['lyrics'] = str(audio['USLT::eng'].text)
            elif 'USLT' in audio:
                # Fallback für USLT ohne spezifische Sprache
                for key in audio.keys():
                    if key.startswith('USLT:'):
                        self.extended_metadata['lyrics'] = str(audio[key].text)
                        break
            
            # Release Year (TDRL)
            if 'TDRL' in audio:
                self.extended_metadata['release_year'] = str(audio['TDRL'][0])
            
            # Prüfen ob erweiterte Daten vorhanden sind
            self.extended_metadata['has_extended_data'] = any([
                self.extended_metadata.get('bpm'),
                self.extended_metadata.get('energy'),
                self.extended_metadata.get('mood'),
                len(self.extended_metadata.get('similar_artists', [])) > 0,
                len(self.extended_metadata.get('tags', [])) > 0,
                self.extended_metadata.get('popularity') is not None
            ])
            
        except Exception as e:
            pass  # Erweiterte Tags sind optional
            
        except Exception as e:
            pass  # Erweiterte Tags sind optional
    
    def _parse_filename(self):
        """Extrahiert Metadaten aus dem Dateinamen als Fallback."""
        filename_no_ext = os.path.splitext(self.filename)[0]
        
        # Verschiedene Muster für Dateinamen
        patterns = [
            r'^(\d+)[\s\-\.]+(.+?)\s*-\s*(.+)$',  # "01 - Artist - Title" oder "01. Artist - Title"
            r'^(.+?)\s*-\s*(.+)$',                 # "Artist - Title"
            r'^(\d+)[\s\-\.]+(.+)$',               # "01 - Title" oder "01. Title"
        ]
        
        for pattern in patterns:
            match = re.match(pattern, filename_no_ext)
            if match:
                groups = match.groups()
                if len(groups) == 3:  # Track, Artist, Title
                    self.track_number = groups[0].zfill(2) if groups[0].isdigit() else ""
                    self.artist = groups[1].strip()
                    self.title = groups[2].strip()
                elif len(groups) == 2:
                    if groups[0].isdigit():  # Track, Title
                        self.track_number = groups[0].zfill(2)
                        self.title = groups[1].strip()
                    else:  # Artist, Title
                        self.artist = groups[0].strip()
                        self.title = groups[1].strip()
                break
        
        # Wenn kein Titel gefunden wurde, verwende Dateinamen
        if not self.title:
            self.title = filename_no_ext
    
    def _detect_cover(self):
        """Erkennt Cover-Status der Datei mit Auflösungsangabe."""
        try:
            audio = MP3(self.file_path)
            embedded_dimensions = None
            
            # Prüfe auf eingebettete Cover
            if hasattr(audio, 'tags') and audio.tags:
                for key in audio.tags.keys():
                    if key.startswith('APIC'):
                        image_data = audio.tags[key].data
                        embedded_dimensions = get_image_dimensions_from_data(image_data)
                        break
            
            # Prüfe auf externe Cover-Dateien
            directory = os.path.dirname(self.file_path)
            external_cover_path = None
            external_dimensions = None
            cover_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp']
            cover_names = ['cover', 'folder', 'albumart', 'front']
            
            try:
                for file in os.listdir(directory):
                    file_lower = file.lower()
                    if any(file_lower.endswith(ext) for ext in cover_extensions):
                        if any(name in file_lower for name in cover_names):
                            external_cover_path = os.path.join(directory, file)
                            external_dimensions = get_image_dimensions_from_file(external_cover_path)
                            break
            except OSError:
                pass
            
            # Bestimme Cover-Status mit Auflösung
            has_embedded = embedded_dimensions and embedded_dimensions != (0, 0)
            has_external = external_dimensions and external_dimensions != (0, 0)
            
            if has_embedded and has_external:
                # Beide Cover vorhanden - zeige eingebettetes Cover
                width, height = embedded_dimensions
                self.cover_status = f"B {width}x{height}"  # Both
            elif has_embedded:
                # Nur eingebettetes Cover
                width, height = embedded_dimensions
                self.cover_status = f"I {width}x{height}"  # Internal
            elif has_external:
                # Nur externes Cover (Verzeichnis)
                width, height = external_dimensions
                self.cover_status = f"D {width}x{height}"  # Directory
            else:
                self.cover_status = "Nein"
                
        except Exception:
            self.cover_status = "Nein"
    
    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert das MP3FileInfo-Objekt zu einem Dictionary."""
        return {
            'filename': self.filename,
            'file_path': self.file_path,
            'directory': self.directory,
            'relative_directory': self.relative_directory,
            'size': self.size,
            'track_number': self.track_number,
            'title': self.title,
            'artist': self.artist,
            'album': self.album,
            'cover_status': self.cover_status
        }
    
    @property
    def full_path(self):
        """Vollständiger Pfad zur Datei."""
        return self.file_path
    
    @property 
    def display_album(self):
        """Album für Anzeige (erkannt oder original)."""
        if self.album_recognized and self.recognized_album:
            return self.recognized_album
        return self.album
    
    @property
    def display_year(self):
        """Jahr für Anzeige (erkannt oder original).""" 
        if self.album_recognized and self.recognized_year:
            return self.recognized_year
        return getattr(self, 'year', '')
    
    @property
    def display_track_number(self):
        """Track-Nummer für Anzeige (erkannt oder original)."""
        if self.album_recognized and self.recognized_track_number:
            return self.recognized_track_number
        return self.track_number
    
    @property
    def year_recognized(self):
        """Gibt zurück, ob das Jahr durch Album-Erkennung ermittelt wurde."""
        return self.album_recognized and self.recognized_year is not None


def scan_mp3_directory(root_directory: str, max_files: int = 5000, max_dirs: int = 200) -> Dict[str, List[MP3FileInfo]]:
    """
    Scannt ein Verzeichnis rekursiv nach MP3-Dateien und gruppiert sie nach Unterverzeichnissen.
    
    Args:
        root_directory: Pfad zum Stammverzeichnis
        max_files: Maximale Anzahl zu verarbeitender MP3-Dateien (Standard: 5000)
        max_dirs: Maximale Anzahl zu verarbeitender Verzeichnisse (Standard: 200)
        
    Returns:
        Dictionary mit relativen Verzeichnispfaden als Schlüssel und Listen von MP3FileInfo als Werte
    """
    grouped_files = {}
    total_files_processed = 0
    total_dirs_processed = 0
    
    print(f"🔍 Scanne Verzeichnis: {root_directory}")
    print(f"📊 Limits: {max_files} Dateien, {max_dirs} Verzeichnisse")
    
    for root, dirs, files in os.walk(root_directory):
        # Prüfe Verzeichnis-Limit
        if total_dirs_processed >= max_dirs:
            print(f"⚠️ Verzeichnis-Limit erreicht ({max_dirs}). Verarbeitung gestoppt.")
            break
            
        mp3_files_in_dir = []
        
        for file in files:
            if is_mp3_file(file):
                # Prüfe Datei-Limit
                if total_files_processed >= max_files:
                    print(f"⚠️ Datei-Limit erreicht ({max_files}). Verarbeitung gestoppt.")
                    break
                    
                file_path = os.path.join(root, file)
                mp3_info = MP3FileInfo(file_path)
                
                # Relativen Pfad berechnen
                relative_path = os.path.relpath(root, root_directory)
                if relative_path == '.':
                    relative_path = os.path.basename(root_directory)
                mp3_info.relative_directory = relative_path
                
                mp3_files_in_dir.append(mp3_info)
                total_files_processed += 1
        
        # Breche ab wenn Datei-Limit erreicht
        if total_files_processed >= max_files:
            break
        
        if mp3_files_in_dir:
            # Sortiere nach Track-Nummer und dann nach Dateinamen
            mp3_files_in_dir.sort(key=lambda x: (x.track_number.zfill(3) if x.track_number else '999', x.filename.lower()))
            
            relative_path = os.path.relpath(root, root_directory)
            if relative_path == '.':
                relative_path = os.path.basename(root_directory)
            
            grouped_files[relative_path] = mp3_files_in_dir
            total_dirs_processed += 1
    
    print(f"✅ Scan abgeschlossen: {total_files_processed} Dateien in {total_dirs_processed} Verzeichnissen")
    if total_files_processed >= max_files:
        print(f"⚠️ Hinweis: Nicht alle Dateien wurden geladen (Limit: {max_files})")
    if total_dirs_processed >= max_dirs:
        print(f"⚠️ Hinweis: Nicht alle Verzeichnisse wurden geladen (Limit: {max_dirs})")
    
    return grouped_files


def get_mp3_statistics(grouped_files: Dict[str, List[MP3FileInfo]]) -> Dict[str, int]:
    """
    Berechnet Statistiken über die gescannten MP3-Dateien.
    
    Args:
        grouped_files: Gruppierte MP3-Dateien
        
    Returns:
        Dictionary mit Statistiken
    """
    total_files = sum(len(files) for files in grouped_files.values())
    total_directories = len(grouped_files)
    total_size = sum(sum(f.size for f in files) for files in grouped_files.values())
    
    # Zusätzliche Statistiken für Audio-Erkennung
    needs_recognition = sum(sum(1 for f in files if f.needs_recognition) for files in grouped_files.values())
    has_recognition = sum(sum(1 for f in files if f.recognized_title or f.recognized_artist) for files in grouped_files.values())
    
    return {
        'total_files': total_files,
        'total_directories': total_directories,
        'total_size_mb': total_size / (1024 * 1024),
        'needs_recognition': needs_recognition,
        'has_recognition': has_recognition
    }


# === AUDIO RECOGNITION INTEGRATION ===

def set_recognition_result(mp3_file: MP3FileInfo, recognition_result: Dict[str, Any]) -> None:
    """
    Setzt Audio-Erkennungsergebnisse für eine MP3-Datei.
    
    Args:
        mp3_file: MP3FileInfo Instanz
        recognition_result: Erkennungsergebnis von AudioRecognitionService
    """
    if recognition_result.get('success'):
        mp3_file.recognized_title = recognition_result.get('title')
        mp3_file.recognized_artist = recognition_result.get('artist')
        mp3_file.recognition_source = recognition_result.get('source')
    else:
        mp3_file.recognized_title = None
        mp3_file.recognized_artist = None
        mp3_file.recognition_source = None


def get_files_needing_recognition(grouped_files: Dict[str, List[MP3FileInfo]]) -> List[MP3FileInfo]:
    """
    Sammelt alle Dateien, die Audio-Erkennung benötigen.
    
    Args:
        grouped_files: Gruppierte MP3-Dateien
        
    Returns:
        Liste der Dateien, die Erkennung benötigen
    """
    files_needing_recognition = []
    
    for files in grouped_files.values():
        for mp3_file in files:
            if mp3_file.needs_recognition:
                files_needing_recognition.append(mp3_file)
    
    return files_needing_recognition


def get_display_title(mp3_file: MP3FileInfo) -> Tuple[str, bool]:
    """
    Gibt den anzuzeigenden Titel zurück mit Information ob er erkannt wurde.
    
    Args:
        mp3_file: MP3FileInfo Instanz
        
    Returns:
        Tuple (title, is_recognized)
    """
    if mp3_file.title:
        return mp3_file.title, False
    elif mp3_file.recognized_title:
        return mp3_file.recognized_title, True
    else:
        return "", False


def get_display_artist(mp3_file: MP3FileInfo) -> Tuple[str, bool]:
    """
    Gibt den anzuzeigenden Künstler zurück mit Information ob er erkannt wurde.
    
    Args:
        mp3_file: MP3FileInfo Instanz
        
    Returns:
        Tuple (artist, is_recognized)
    """
    if mp3_file.artist:
        return mp3_file.artist, False
    elif mp3_file.recognized_artist:
        return mp3_file.recognized_artist, True
    else:
        return "", False
