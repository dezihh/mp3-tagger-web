"""
MP3 Tagger Web Application - Optimized Utility Functions

Zentrale Hilfsfunktionen für die MP3 Tagger Web Application.
Stellt wiederverwendbare, optimierte Funktionen für häufige Operationen bereit:

Funktionsgruppen:
- Datei-System: MP3-Validierung, Pfad-Normalisierung
- Image-Processing: Cover-Art-Extraktion, Base64-Konvertierung, Größenanalyse  
- String-Processing: Name-Normalisierung, Format-Validierung
- ID3-Tag-Utilities: Tag-Extraktion, Validierung, Metadaten-Bereinigung

Verwendung:
    from tagger.utils import is_mp3_file, normalize_name, get_cover_art_base64
    
    # MP3-Validierung
    if is_mp3_file(filename):
        # Cover-Art extrahieren
        cover_data = get_cover_art_base64(mp3_file)
        
        # Namen normalisieren
        clean_name = normalize_name(artist_name)

Diese Module ist optimiert für Performance und Wiederverwendbarkeit.
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
        'TDRC': 'Erscheinungsdatum', 'TRCK': 'Track', 'TPOS': 'Disc', 'TCON': 'Genre'
    }
    
    for tag_id, tag_name in basic_tag_mapping.items():
        if tag_id in tags:
            value = str(tags[tag_id][0])
            # Spezielle Formatierung für Track-Nummern
            if tag_id == 'TRCK' and '/' in value:
                track_parts = value.split('/')
                value = f"{track_parts[0]}/{track_parts[1]}" if len(track_parts) > 1 else track_parts[0]
            info['basic'][tag_name] = value
    
    # Erweiterte Standard-Tags (seltener verwendet)
    extended_tag_mapping = {
        'TPE2': 'Album Artist', 'TPE3': 'Dirigent', 'TCOM': 'Komponist',
        'TYER': 'Jahr (alt)', 'TBPM': 'BPM', 'TKEY': 'Tonart',
        'TLAN': 'Sprache', 'TPUB': 'Label', 'TCOP': 'Copyright'
    }
    
    for tag_id, tag_name in extended_tag_mapping.items():
        if tag_id in tags:
            info['extended'][tag_name] = str(tags[tag_id][0])
    
    # Erweiterte Metadaten aus TXXX-Tags sammeln
    extended_metadata_mapping = {
        'EXTENDED_GENRES': '🎪 Genres (erweitert)',
        'MOOD': '🎭 Mood',
        'SIMILAR_ARTISTS': '👥 Ähnliche Künstler',
        'AUDIO_FEATURES': '🎵 Audio Features',
        'TAGS': '🏷️ Tags',
        'RELEASE_DATE': '📅 Release Datum',
        'POPULARITY': '⭐ Beliebtheit'
    }
    
    # TXXX (User-defined) Tags durchsuchen
    for tag_key, tag_value in tags.items():
        if tag_key.startswith('TXXX:') and hasattr(tag_value, 'desc'):
            desc = tag_value.desc
            value = str(tag_value.text[0]) if tag_value.text else ''
            
            if desc in extended_metadata_mapping and value:
                label = extended_metadata_mapping[desc]
                
                # Spezielle Formatierung für verschiedene Datentypen
                if desc == 'AUDIO_FEATURES':
                    # Parse "energy:0.825, danceability:0.742" zu lesbar
                    features = []
                    for feature in value.split(','):
                        if ':' in feature:
                            name, val = feature.strip().split(':', 1)
                            try:
                                # Namen übersetzen
                                feature_names = {
                                    'energy': 'Energy', 'danceability': 'Danceability',
                                    'valence': 'Valence', 'acousticness': 'Acousticness'
                                }
                                display_name = feature_names.get(name, name.title())
                                features.append(f"{display_name}: {float(val):.2f}")
                            except ValueError:
                                features.append(f"{name}: {val}")
                    value = ', '.join(features) if features else value
                
                elif desc == 'POPULARITY':
                    try:
                        pop_val = int(value)
                        value = f"{pop_val}/100"
                    except ValueError:
                        pass
                        
                elif desc in ['SIMILAR_ARTISTS', 'EXTENDED_GENRES', 'TAGS']:
                    # Limitiere die Anzahl der angezeigten Items für bessere Lesbarkeit
                    items = [item.strip() for item in value.split(',')]
                    if len(items) > 5:
                        value = ', '.join(items[:5]) + f' (+{len(items)-5} weitere)'
                    else:
                        value = ', '.join(items)
                
                info['extended'][label] = value


def _collect_cover_info(audio: MP3, info: Dict[str, Any]) -> None:
    """Sammelt Cover-Informationen und erstellt Thumbnail."""
    file_path = audio.filename
    cover_data = None
    cover_source = None
    
    # Erst nach eingebetteten Covern suchen
    if hasattr(audio, 'tags') and audio.tags:
        tags = audio.tags
        apic_frames = [tag for tag in tags.values() if hasattr(tag, 'type') and hasattr(tag, 'data')]
        
        if apic_frames:
            cover_frame = apic_frames[0]
            cover_data = cover_frame.data
            cover_source = "embedded"
    
    # Wenn kein eingebettetes Cover gefunden, nach externen Covern suchen
    if not cover_data:
        directory = os.path.dirname(file_path)
        cover_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp']
        cover_names = ['cover', 'folder', 'albumart', 'front']
        
        try:
            for file in os.listdir(directory):
                file_lower = file.lower()
                if any(file_lower.endswith(ext) for ext in cover_extensions):
                    if any(name in file_lower for name in cover_names):
                        external_cover_path = os.path.join(directory, file)
                        try:
                            with open(external_cover_path, 'rb') as f:
                                cover_data = f.read()
                                cover_source = "external"
                                break
                        except Exception:
                            continue
        except OSError:
            pass
    
    if not cover_data:
        return
    
    try:
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
                'source': cover_source,
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
    if not hasattr(audio, 'tags') or audio.tags is None:
        try:
            audio.add_tags()
        except Exception as e:
            # Ignoriere den Fehler falls Tags bereits existieren
            if "tag already exists" not in str(e).lower():
                raise e


def _update_id3_tags(tags, tags_data: Dict[str, Any]) -> int:
    """
    Aktualisiert ID3-Tags und gibt die Anzahl der Änderungen zurück.
    
    Returns:
        int: Anzahl der aktualisierten Tags
    """
    # Optimierte Tag-Mappings mit Frame-Klassen
    from mutagen.id3 import TIT2, TPE1, TALB, TDRC, TRCK, TCON, TBPM, COMM, TXXX
    
    # Standard-Tags
    tag_mappings = {
        'title': ('TIT2', TIT2),
        'artist': ('TPE1', TPE1),
        'album': ('TALB', TALB),
        'year': ('TDRC', TDRC),
        'track': ('TRCK', TRCK),
        'genre': ('TCON', TCON)
    }
    
    updated_count = 0
    
    # Standard-Tags aktualisieren
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
    
    # Erweiterte Metadaten verarbeiten
    if 'extended_metadata' in tags_data and tags_data['extended_metadata']:
        extended = tags_data['extended_metadata']
        
        # BPM speichern
        if extended.get('bpm') and extended['bpm']:
            try:
                bpm_value = int(float(extended['bpm']))
                current_bpm = ''
                if 'TBPM' in tags:
                    current_bpm = str(tags['TBPM'][0]) if tags['TBPM'] else ''
                
                if current_bpm != str(bpm_value):
                    tags['TBPM'] = TBPM(encoding=3, text=[str(bpm_value)])
                    updated_count += 1
            except (ValueError, TypeError):
                pass
        
        # Erweiterte Genres als TXXX speichern
        if extended.get('genres') and extended['genres']:
            genres_text = ', '.join(extended['genres'])
            if _update_txxx_tag(tags, 'EXTENDED_GENRES', genres_text):
                updated_count += 1
        
        # Mood als TXXX speichern
        if extended.get('mood') and extended['mood']:
            mood_text = ', '.join(extended['mood']) if isinstance(extended['mood'], list) else str(extended['mood'])
            if _update_txxx_tag(tags, 'MOOD', mood_text):
                updated_count += 1
        
        # Ähnliche Künstler als TXXX speichern
        if extended.get('similar_artists') and extended['similar_artists']:
            artists_text = ', '.join(extended['similar_artists'][:5])  # Max 5 Künstler
            if _update_txxx_tag(tags, 'SIMILAR_ARTISTS', artists_text):
                updated_count += 1
        
        # Audio Features als TXXX speichern
        audio_features = []
        for feature in ['energy', 'danceability', 'valence', 'acousticness']:
            if extended.get(feature) and extended[feature] is not None:
                audio_features.append(f"{feature}:{extended[feature]:.3f}")
        
        if audio_features:
            if _update_txxx_tag(tags, 'AUDIO_FEATURES', ', '.join(audio_features)):
                updated_count += 1
        
        # Tags als TXXX speichern
        if extended.get('tags') and extended['tags']:
            tags_text = ', '.join(extended['tags'][:10])  # Max 10 Tags
            if _update_txxx_tag(tags, 'TAGS', tags_text):
                updated_count += 1
        
        # Release Date als TXXX speichern
        if extended.get('release_date') and extended['release_date']:
            if _update_txxx_tag(tags, 'RELEASE_DATE', str(extended['release_date'])):
                updated_count += 1
        
        # Popularity als TXXX speichern
        if extended.get('popularity') and extended['popularity'] is not None:
            if _update_txxx_tag(tags, 'POPULARITY', str(extended['popularity'])):
                updated_count += 1
    
    return updated_count


def _update_txxx_tag(tags, desc: str, value: str) -> bool:
    """
    Aktualisiert einen TXXX (User-defined text) Tag.
    
    Returns:
        bool: True wenn der Tag aktualisiert wurde
    """
    from mutagen.id3 import TXXX
    
    # Aktuellen Wert prüfen
    current_value = ''
    for tag in tags.values():
        if hasattr(tag, 'desc') and tag.desc == desc:
            current_value = str(tag.text[0]) if tag.text else ''
            break
    
    # Nur aktualisieren wenn sich der Wert geändert hat
    if current_value != value:
        # Entferne alten Tag falls vorhanden
        for key in list(tags.keys()):
            if key.startswith('TXXX:') and hasattr(tags[key], 'desc') and tags[key].desc == desc:
                del tags[key]
        
        # Neuen Tag hinzufügen
        tags[f'TXXX:{desc}'] = TXXX(encoding=3, desc=desc, text=[value])
        return True
    
    return False
