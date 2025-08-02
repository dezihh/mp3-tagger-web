"""
MP3 Metadaten-Verarbeitung für den MP3 Tagger.

Dieses Modul bietet Funktionen zum Lesen und Verarbeiten von MP3-Dateien
und deren ID3-Tags.
"""

import os
import re
from mutagen.mp3 import MP3
from mutagen.id3 import ID3NoHeaderError
from typing import Dict, List, Any, Optional


class MP3FileInfo:
    """Klasse zur Repräsentation einer MP3-Datei mit Metadaten."""
    
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
        self.cover_status = "Nein"
        
        self._load_file_info()
        self._load_id3_tags()
        self._detect_cover()
    
    def _load_file_info(self):
        """Lädt grundlegende Dateiinformationen."""
        try:
            self.size = os.path.getsize(self.file_path)
        except OSError:
            self.size = 0
    
    def _load_id3_tags(self):
        """Lädt ID3-Tags aus der MP3-Datei."""
        try:
            audio = MP3(self.file_path)
            
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
                
        except (ID3NoHeaderError, Exception):
            # Fallback: Versuche Informationen aus Dateinamen zu extrahieren
            self._parse_filename()
    
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
        """Erkennt Cover-Status der Datei."""
        try:
            audio = MP3(self.file_path)
            has_embedded = False
            embedded_size = 0
            
            # Prüfe auf eingebettete Cover
            if hasattr(audio, 'tags') and audio.tags:
                for key in audio.tags.keys():
                    if key.startswith('APIC'):
                        has_embedded = True
                        embedded_size = len(audio.tags[key].data)
                        break
            
            # Prüfe auf externe Cover-Dateien
            directory = os.path.dirname(self.file_path)
            external_covers = []
            cover_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp']
            cover_names = ['cover', 'folder', 'albumart', 'front']
            
            try:
                for file in os.listdir(directory):
                    file_lower = file.lower()
                    if any(file_lower.endswith(ext) for ext in cover_extensions):
                        if any(name in file_lower for name in cover_names):
                            external_covers.append(file)
            except OSError:
                pass
            
            # Bestimme Cover-Status
            if has_embedded and external_covers:
                self.cover_status = f"B{embedded_size//1024}k"  # Both
            elif has_embedded:
                self.cover_status = f"I{embedded_size//1024}k"  # Internal
            elif external_covers:
                # Größe der ersten externen Cover-Datei
                try:
                    ext_path = os.path.join(directory, external_covers[0])
                    ext_size = os.path.getsize(ext_path)
                    self.cover_status = f"E{ext_size//1024}k"  # External
                except OSError:
                    self.cover_status = "E?k"
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


def scan_mp3_directory(root_directory: str) -> Dict[str, List[MP3FileInfo]]:
    """
    Scannt ein Verzeichnis rekursiv nach MP3-Dateien und gruppiert sie nach Unterverzeichnissen.
    
    Args:
        root_directory: Pfad zum Stammverzeichnis
        
    Returns:
        Dictionary mit relativen Verzeichnispfaden als Schlüssel und Listen von MP3FileInfo als Werte
    """
    grouped_files = {}
    
    for root, dirs, files in os.walk(root_directory):
        mp3_files_in_dir = []
        
        for file in files:
            if file.lower().endswith('.mp3'):
                file_path = os.path.join(root, file)
                mp3_info = MP3FileInfo(file_path)
                
                # Relativen Pfad berechnen
                relative_path = os.path.relpath(root, root_directory)
                if relative_path == '.':
                    relative_path = os.path.basename(root_directory)
                mp3_info.relative_directory = relative_path
                
                mp3_files_in_dir.append(mp3_info)
        
        if mp3_files_in_dir:
            # Sortiere nach Track-Nummer und dann nach Dateinamen
            mp3_files_in_dir.sort(key=lambda x: (x.track_number.zfill(3) if x.track_number else '999', x.filename.lower()))
            
            relative_path = os.path.relpath(root, root_directory)
            if relative_path == '.':
                relative_path = os.path.basename(root_directory)
            
            grouped_files[relative_path] = mp3_files_in_dir
    
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
    total_size = sum(file.size for files in grouped_files.values() for file in files)
    
    return {
        'total_files': total_files,
        'total_directories': total_directories,
        'total_size_mb': total_size / (1024 * 1024)
    }
