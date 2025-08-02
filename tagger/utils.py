"""
Utility-Funktionen für MP3 Tagger Web Application

Gemeinsame Hilfsfunktionen für verschiedene Module.
"""

import os
import base64
from typing import List, Dict, Any, Optional
from mutagen.mp3 import MP3
from mutagen.id3 import ID3NoHeaderError
from PIL import Image
from io import BytesIO


def is_mp3_file(filename: str) -> bool:
    """
    Prüft, ob eine Datei eine MP3-Datei ist.
    
    Args:
        filename: Name der zu prüfenden Datei
        
    Returns:
        bool: True wenn die Datei eine .mp3 Endung hat
    """
    return filename.lower().endswith('.mp3')


def find_mp3_files_in_directory(directory: str) -> List[str]:
    """
    Findet alle MP3-Dateien in einem Verzeichnis (rekursiv).
    
    Args:
        directory: Pfad zum zu durchsuchenden Verzeichnis
        
    Returns:
        Liste der vollständigen Pfade zu allen gefundenen MP3-Dateien
    """
    mp3_files = []
    
    if not os.path.isdir(directory):
        return mp3_files
        
    for root, dirs, files in os.walk(directory):
        for filename in files:
            if is_mp3_file(filename):
                mp3_files.append(os.path.join(root, filename))
    
    return mp3_files


def count_mp3_files_in_directory(directory: str) -> int:
    """
    Zählt die Anzahl der MP3-Dateien in einem Verzeichnis (rekursiv).
    
    Args:
        directory: Pfad zum Verzeichnis
        
    Returns:
        int: Anzahl der gefundenen MP3-Dateien
    """
    return len(find_mp3_files_in_directory(directory))


def has_mp3_files(directory: str) -> bool:
    """
    Prüft, ob ein Verzeichnis MP3-Dateien enthält (rekursiv).
    
    Args:
        directory: Pfad zum zu prüfenden Verzeichnis
        
    Returns:
        bool: True wenn MP3-Dateien gefunden wurden
    """
    if not os.path.isdir(directory):
        return False
        
    # Optimierte Suche - stoppt bei der ersten gefundenen MP3-Datei
    for root, dirs, files in os.walk(directory):
        for filename in files:
            if is_mp3_file(filename):
                return True
    return False


def get_detailed_mp3_info(file_path: str) -> Dict[str, Any]:
    """
    Sammelt detaillierte ID3-Informationen einer MP3-Datei für Hover-Anzeige.
    
    Args:
        file_path: Pfad zur MP3-Datei
        
    Returns:
        Dictionary mit allen verfügbaren ID3-Tags und Metadaten
    """
    info = {
        'basic': {},
        'extended': {},
        'technical': {},
        'cover': None,
        'error': None
    }
    
    try:
        if not os.path.isfile(file_path) or not is_mp3_file(file_path):
            info['error'] = 'Datei ist keine gültige MP3-Datei'
            return info
            
        # Datei-Informationen
        file_size = os.path.getsize(file_path)
        info['technical']['file_size'] = f"{file_size / (1024*1024):.1f} MB"
        info['technical']['file_path'] = os.path.basename(file_path)
        
        # MP3-Datei laden
        audio = MP3(file_path)
        
        # Technische Informationen
        if hasattr(audio, 'info'):
            info['technical']['duration'] = f"{int(audio.info.length // 60)}:{int(audio.info.length % 60):02d} min"
            info['technical']['bitrate'] = f"{audio.info.bitrate} kbps"
            info['technical']['sample_rate'] = f"{audio.info.sample_rate} Hz"
            info['technical']['channels'] = "Stereo" if audio.info.channels == 2 else "Mono"
        
        # ID3-Tags prüfen
        if not hasattr(audio, 'tags') or not audio.tags:
            info['error'] = 'Keine ID3-Tags gefunden'
            return info
            
        tags = audio.tags
        
        # Basis-Tags (häufig verwendet)
        basic_tags = {
            'TIT2': 'Titel',
            'TPE1': 'Artist', 
            'TALB': 'Album',
            'TDRC': 'Jahr',
            'TRCK': 'Track',
            'TPOS': 'Disc',
            'TCON': 'Genre'
        }
        
        for tag_id, tag_name in basic_tags.items():
            if tag_id in tags:
                value = str(tags[tag_id][0])
                if tag_id == 'TRCK' and '/' in value:
                    # Track-Nummer formatieren
                    track_parts = value.split('/')
                    value = f"{track_parts[0]}/{track_parts[1]}" if len(track_parts) > 1 else track_parts[0]
                info['basic'][tag_name] = value
        
        # Erweiterte Tags
        extended_tags = {
            'TPE2': 'Album Artist',
            'TPE3': 'Dirigent',
            'TPE4': 'Remixer',
            'TCOM': 'Komponist',
            'TPUB': 'Label',
            'TCOP': 'Copyright',
            'TENC': 'Encoded by',
            'TBPM': 'BPM',
            'TKEY': 'Tonart',
            'TMOO': 'Mood',
            'COMM': 'Kommentar'
        }
        
        for tag_id, tag_name in extended_tags.items():
            if tag_id in tags:
                if tag_id == 'COMM':
                    # Kommentare haben spezielle Struktur
                    comments = []
                    for comm in tags.getall(tag_id):
                        if comm.text and comm.text[0]:
                            comments.append(str(comm.text[0]))
                    if comments:
                        info['extended'][tag_name] = '; '.join(comments)
                else:
                    info['extended'][tag_name] = str(tags[tag_id][0])
        
        # Cover-Informationen
        cover_info = _extract_cover_info(tags)
        if cover_info:
            info['cover'] = cover_info
            
    except ID3NoHeaderError:
        info['error'] = 'Keine ID3-Tags gefunden'
    except Exception as e:
        info['error'] = f'Fehler beim Lesen: {str(e)}'
    
    return info


def _extract_cover_info(tags) -> Optional[Dict[str, Any]]:
    """
    Extrahiert Cover-Informationen aus ID3-Tags.
    
    Args:
        tags: ID3-Tags der MP3-Datei
        
    Returns:
        Dictionary mit Cover-Informationen oder None
    """
    for key in tags.keys():
        if key.startswith('APIC'):
            apic = tags[key]
            try:
                # Bild-Informationen ermitteln
                img = Image.open(BytesIO(apic.data))
                width, height = img.size
                
                # Bild als Base64 für Vorschau (kleine Version)
                img.thumbnail((200, 200), Image.Resampling.LANCZOS)
                buffer = BytesIO()
                img.save(buffer, format='JPEG', quality=85)
                img_data = base64.b64encode(buffer.getvalue()).decode()
                
                # APIC-Typ ermitteln
                picture_types = {
                    0: 'Andere',
                    1: 'Icon',
                    2: 'Anderes Icon', 
                    3: 'Cover (Front)',
                    4: 'Cover (Back)',
                    5: 'Leaflet',
                    6: 'Media',
                    7: 'Lead Artist',
                    8: 'Artist/Performer',
                    9: 'Dirigent',
                    10: 'Band/Orchestra',
                    11: 'Komponist',
                    12: 'Texter',
                    13: 'Aufnahmeort',
                    14: 'Während Aufnahme',
                    15: 'Während Performance',
                    16: 'Video Screenshot',
                    17: 'Heller farbiger Fisch',
                    18: 'Illustration',
                    19: 'Band/Artist Logo',
                    20: 'Publisher/Studio Logo'
                }
                
                return {
                    'width': width,
                    'height': height,
                    'size': f"{len(apic.data) / 1024:.0f} KB",
                    'format': apic.mime.split('/')[-1].upper() if apic.mime else 'Unknown',
                    'type': picture_types.get(apic.type, f'Type {apic.type}'),
                    'description': apic.desc if apic.desc else '',
                    'data': img_data  # Base64 für Vorschau
                }
            except Exception:
                return {
                    'error': 'Cover nicht lesbar',
                    'size': f"{len(apic.data) / 1024:.0f} KB"
                }
    
    return None
