"""
MP3 Tagger Web Application - Optimized Utility Functions

Zentrale Hilfsfunktionen für MP3-Verarbeitung und Metadaten-Management.
Alle häufig verwendeten Operationen sind hier zusammengefasst.
"""

import os
import base64
from typing import List, Dict, Any, Optional, Tuple
from mutagen.mp3 import MP3
from mutagen.id3 import ID3NoHeaderError
from PIL import Image
from io import BytesIO


# === DATEI-SYSTEM FUNKTIONEN ===

def is_mp3_file(filename: str) -> bool:
    """Prüft, ob eine Datei eine MP3-Datei ist."""
    return filename.lower().endswith('.mp3')


def find_mp3_files_in_directory(directory: str) -> List[str]:
    """
    Findet alle MP3-Dateien in einem Verzeichnis (rekursiv).
    
    Args:
        directory: Pfad zum zu durchsuchenden Verzeichnis
        
    Returns:
        Liste der vollständigen Pfade zu allen gefundenen MP3-Dateien
    """
    if not os.path.isdir(directory):
        return []
        
    mp3_files = []
    for root, dirs, files in os.walk(directory):
        for filename in files:
            if is_mp3_file(filename):
                mp3_files.append(os.path.join(root, filename))
    
    return mp3_files


def count_mp3_files_in_directory(directory: str) -> int:
    """Zählt die Anzahl der MP3-Dateien in einem Verzeichnis (rekursiv)."""
    return len(find_mp3_files_in_directory(directory))


def has_mp3_files(directory: str) -> bool:
    """
    Prüft, ob ein Verzeichnis MP3-Dateien enthält (rekursiv).
    Optimiert - stoppt bei der ersten gefundenen MP3-Datei.
    """
    if not os.path.isdir(directory):
        return False
        
    for root, dirs, files in os.walk(directory):
        for filename in files:
            if is_mp3_file(filename):
                return True
    return False


# === MP3 METADATEN FUNKTIONEN ===


def get_detailed_mp3_info(file_path: str) -> Dict[str, Any]:
    """
    Sammelt detaillierte ID3-Informationen einer MP3-Datei für Tooltip-Anzeige.
    
    Args:
        file_path: Pfad zur MP3-Datei
        
    Returns:
        Dictionary mit strukturierten MP3-Metadaten (basic, extended, technical, cover)
    """
    info = {
        'basic': {},
        'extended': {},
        'technical': {},
        'cover': None,
        'error': None
    }
    
    try:
        # Grundlegende Datei-Validierung
        if not os.path.isfile(file_path) or not is_mp3_file(file_path):
            info['error'] = 'Datei ist keine gültige MP3-Datei'
            return info
            
        # Datei-Metadaten sammeln
        _collect_file_info(file_path, info)
        
        # MP3-Datei laden und verarbeiten
        audio = MP3(file_path)
        _collect_technical_info(audio, info)
        _collect_id3_tags(audio, info)
        _collect_cover_info(audio, info)
        
    except Exception as e:
        info['error'] = f'Fehler beim Lesen der Datei: {str(e)}'
    
    return info


def _collect_file_info(file_path: str, info: Dict[str, Any]) -> None:
    """Sammelt Datei-System Informationen."""
    file_size = os.path.getsize(file_path)
    info['technical']['file_size'] = f"{file_size / (1024*1024):.1f} MB"
    info['technical']['file_path'] = os.path.basename(file_path)


def _collect_technical_info(audio: MP3, info: Dict[str, Any]) -> None:
    """Sammelt technische Audio-Informationen."""
    if hasattr(audio, 'info') and audio.info:
        duration_sec = audio.info.length
        info['technical']['duration'] = f"{int(duration_sec // 60)}:{int(duration_sec % 60):02d} min"
        info['technical']['bitrate'] = f"{audio.info.bitrate} kbps"
        info['technical']['sample_rate'] = f"{audio.info.sample_rate} Hz"
        info['technical']['channels'] = "Stereo" if audio.info.channels == 2 else "Mono"


def _collect_id3_tags(audio: MP3, info: Dict[str, Any]) -> None:
    """Sammelt und organisiert ID3-Tags in basic und extended Kategorien."""
    if not hasattr(audio, 'tags') or not audio.tags:
        info['error'] = 'Keine ID3-Tags gefunden'
        return
        
    tags = audio.tags
    
    # Basis-Tags (häufig verwendet)
    basic_tag_mapping = {
        'TIT2': 'Titel', 'TPE1': 'Artist', 'TALB': 'Album',
        'TDRC': 'Jahr', 'TRCK': 'Track', 'TPOS': 'Disc', 'TCON': 'Genre'
    }
    
    for tag_id, tag_name in basic_tag_mapping.items():
        if tag_id in tags:
            value = str(tags[tag_id][0])
            # Spezielle Formatierung für Track-Nummern
            if tag_id == 'TRCK' and '/' in value:
                track_parts = value.split('/')
                value = f"{track_parts[0]}/{track_parts[1]}" if len(track_parts) > 1 else track_parts[0]
            info['basic'][tag_name] = value
    
    # Erweiterte Tags (seltener verwendet)
    extended_tag_mapping = {
        'TPE2': 'Album Artist', 'TPE3': 'Dirigent', 'TCOM': 'Komponist',
        'TYER': 'Jahr (alt)', 'TBPM': 'BPM', 'TKEY': 'Tonart',
        'TLAN': 'Sprache', 'TPUB': 'Label', 'TCOP': 'Copyright'
    }
    
    for tag_id, tag_name in extended_tag_mapping.items():
        if tag_id in tags:
            info['extended'][tag_name] = str(tags[tag_id][0])


def _collect_cover_info(audio: MP3, info: Dict[str, Any]) -> None:
    """Sammelt Cover-Informationen und erstellt Thumbnail."""
    if not hasattr(audio, 'tags') or not audio.tags:
        return
        
    tags = audio.tags
    apic_frames = [tag for tag in tags.values() if hasattr(tag, 'type') and hasattr(tag, 'data')]
    
    if not apic_frames:
        return
    
    try:
        # Erstes verfügbares Cover verwenden
        cover_frame = apic_frames[0]
        cover_data = cover_frame.data
        
        # Cover-Informationen via PIL analysieren
        with Image.open(BytesIO(cover_data)) as img:
            width, height = img.size
            cover_format = img.format or 'Unknown'
            
            # Thumbnail für Tooltip erstellen (max 150x150)
            thumbnail_size = (150, 150)
            img.thumbnail(thumbnail_size, Image.Resampling.LANCZOS)
            
            # Thumbnail zu Base64 konvertieren
            thumbnail_buffer = BytesIO()
            img.save(thumbnail_buffer, format='JPEG', quality=85)
            thumbnail_data = base64.b64encode(thumbnail_buffer.getvalue()).decode('utf-8')
            
            info['cover'] = {
                'width': width,
                'height': height,
                'size': f"{len(cover_data) / 1024:.1f} KB",
                'format': cover_format,
                'data': thumbnail_data
            }
            
    except Exception as e:
        info['cover'] = {'error': f'Fehler beim Lesen des Covers: {str(e)}'}


# === TAG-SPEICHER FUNKTIONEN ===

def save_mp3_tags(file_path: str, tags_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Speichert ID3-Tags in eine MP3-Datei mit optimierter Fehlerbehandlung.
    
    Args:
        file_path: Pfad zur MP3-Datei
        tags_data: Dictionary mit den zu speichernden Tags
        
    Returns:
        Dictionary mit Erfolgs/Fehlerstatus
    """
    result = {
        'success': False,
        'message': '',
        'file': os.path.basename(file_path)
    }
    
    try:
        # Datei-Validierung
        if not _validate_mp3_file(file_path):
            result['message'] = 'Datei ist keine gültige MP3-Datei'
            return result
            
        # MP3-Datei laden und Tags initialisieren
        audio = MP3(file_path)
        _ensure_id3_tags(audio)
        
        # Tags aktualisieren
        updated_count = _update_id3_tags(audio.tags, tags_data)
        
        # Nur speichern wenn Änderungen vorgenommen wurden
        if updated_count > 0:
            audio.save()
            result['success'] = True
            result['message'] = f'{updated_count} Tags erfolgreich gespeichert'
        else:
            result['success'] = True
            result['message'] = 'Keine Änderungen erforderlich'
        
    except Exception as e:
        result['message'] = f'Fehler beim Speichern: {str(e)}'
    
    return result


def _validate_mp3_file(file_path: str) -> bool:
    """Validiert, ob die Datei eine gültige MP3-Datei ist."""
    return os.path.isfile(file_path) and is_mp3_file(file_path)


def _ensure_id3_tags(audio: MP3) -> None:
    """Stellt sicher, dass ID3-Tags in der MP3-Datei existieren."""
    if not hasattr(audio, 'tags') or not audio.tags:
        audio.add_tags()


def _update_id3_tags(tags, tags_data: Dict[str, Any]) -> int:
    """
    Aktualisiert ID3-Tags und gibt die Anzahl der Änderungen zurück.
    
    Returns:
        int: Anzahl der aktualisierten Tags
    """
    # Optimierte Tag-Mappings mit Frame-Klassen
    from mutagen.id3 import TIT2, TPE1, TALB, TDRC, TRCK, TCON
    
    tag_mappings = {
        'title': ('TIT2', TIT2),
        'artist': ('TPE1', TPE1),
        'album': ('TALB', TALB),
        'year': ('TDRC', TDRC),
        'track': ('TRCK', TRCK),
        'genre': ('TCON', TCON)
    }
    
    updated_count = 0
    
    for field, (tag_id, frame_class) in tag_mappings.items():
        if field in tags_data and tags_data[field] is not None:
            value = str(tags_data[field]).strip()
            
            # Nur nicht-leere Werte setzen
            if value:
                # Prüfen ob sich der Wert geändert hat
                current_value = ''
                if tag_id in tags:
                    current_value = str(tags[tag_id][0]) if tags[tag_id] else ''
                
                if current_value != value:
                    tags[tag_id] = frame_class(encoding=3, text=[value])
                    updated_count += 1
    
    return updated_count
