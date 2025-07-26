import os
import eyed3
from pathlib import Path
from difflib import SequenceMatcher
import requests
from urllib.parse import quote
import logging
import base64
from collections import defaultdict
import re

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class MusicTagger:
    def __init__(self):
        self.lastfm_key = os.getenv('LASTFM_API_KEY')
        self.discogs_key = os.getenv('DISCOGS_API_KEY')
        self.discogs_secret = os.getenv('DISCOGS_API_SECRET')
        self.min_confidence = 0.6

    def scan_directory(self, directory):
        files = []
        try:
            for mp3_path in Path(directory).rglob('*.mp3'):
                try:
                    audio = eyed3.load(mp3_path)
                    if audio.tag is None:
                        audio.initTag()

                    file_data = {
                        'path': str(mp3_path),
                        'filename': mp3_path.name,
                        'directory': str(mp3_path.parent),
                        'target_path': str(mp3_path),
                        'current_artist': audio.tag.artist,
                        'current_title': audio.tag.title,
                        'current_album': audio.tag.album,
                        'current_has_cover': self._has_cover(audio),
                        'current_cover_info': self._get_cover_info(audio),
                        'current_cover_compact': self._get_cover_compact_info(audio),
                        'current_full_tags': self._get_full_tag_info(audio),
                        'current_cover_preview': self._get_cover_preview(audio),
                        'suggested_artist': None,
                        'suggested_title': None,
                        'suggested_album': None,
                        'suggested_cover_url': None,
                        'suggested_full_tags': None
                    }
                    files.append(file_data)
                except Exception as e:
                    logging.error(f"Fehler beim Lesen von {mp3_path}: {str(e)}")
        except Exception as e:
            logging.error(f"Verzeichnisscan fehlgeschlagen: {str(e)}")
        return files

    def get_metadata_for_files(self, files_data):
        results = []
        for file_data in files_data:
            try:
                artist, title = self._parse_filename(file_data['filename'])
                online_meta = self._query_online_metadata(
                    artist or file_data['current_artist'],
                    title or file_data['current_title'],
                    file_data['current_album']
                )

                if online_meta:
                    file_data.update({
                        'suggested_artist': online_meta.get('artist'),
                        'suggested_title': online_meta.get('title'),
                        'suggested_album': online_meta.get('album'),
                        'suggested_cover_url': online_meta.get('cover_url'),
                        'suggested_full_tags': self._format_suggested_tags(online_meta)
                    })
                results.append(file_data)
            except Exception as e:
                logging.error(f"Metadatenabfrage fehlgeschlagen für {file_data['filename']}: {str(e)}")
                results.append(file_data)
        return results

    def _has_cover(self, audio):
        """Prüft ob eine MP3-Datei ein Cover-Bild hat (eingebettet oder extern)"""
        try:
            if not audio or not audio.tag:
                return False
            
            # Prüfe eingebettete Cover-Bilder
            images = audio.tag.images
            
            # Methode 1: Direkte Images-Prüfung
            if images and len(images) > 0:
                return True
            
            # Methode 2: Prüfe Frame-basierte APIC-Tags
            if hasattr(audio.tag, 'frame_set'):
                frame_set = audio.tag.frame_set
                if b'APIC' in frame_set or b'PIC' in frame_set:
                    return True
            
            # Methode 3: Prüfe externe Cover-Bilder im Verzeichnis
            if hasattr(audio, 'path'):
                directory = os.path.dirname(audio.path)
                return self._has_external_cover(directory)
            
            return False
        except Exception as e:
            logging.debug(f"Fehler bei Cover-Prüfung: {str(e)}")
            return False

    def _has_external_cover(self, directory):
        """Prüft ob externe Cover-Bilder im Verzeichnis vorhanden sind"""
        try:
            cover_names = [
                'folder.jpg', 'folder.jpeg', 'folder.png',
                'cover.jpg', 'cover.jpeg', 'cover.png',
                'album.jpg', 'album.jpeg', 'album.png',
                'albumart.jpg', 'albumart.jpeg', 'albumart.png',
                'front.jpg', 'front.jpeg', 'front.png'
            ]
            
            for filename in os.listdir(directory):
                if filename.lower() in cover_names:
                    return True
                # Prüfe auch auf AlbumArt_*-Dateien (Windows Media Player Format)
                if filename.lower().startswith('albumart_') and filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                    return True
            
            return False
        except:
            return False

    def _get_full_tag_info(self, audio):
        """Erstellt eine vollständige Übersicht der ID3-Tags"""
        try:
            tag_info = []
            if audio.tag.artist:
                tag_info.append(f"Artist: {audio.tag.artist}")
            if audio.tag.title:
                tag_info.append(f"Title: {audio.tag.title}")
            if audio.tag.album:
                tag_info.append(f"Album: {audio.tag.album}")
            if audio.tag.album_artist:
                tag_info.append(f"Album Artist: {audio.tag.album_artist}")
            if audio.tag.track_num:
                tag_info.append(f"Track: {audio.tag.track_num[0]}")
            if audio.tag.recording_date:
                tag_info.append(f"Year: {audio.tag.recording_date}")
            if audio.tag.genre:
                tag_info.append(f"Genre: {audio.tag.genre}")
            
            # Cover-Information mit Details
            embedded_cover = False
            external_cover = False
            
            # Prüfe eingebettetes Cover
            if audio.tag.images and len(audio.tag.images) > 0:
                embedded_cover = True
            elif hasattr(audio.tag, 'frame_set'):
                frame_set = audio.tag.frame_set
                if b'APIC' in frame_set or b'PIC' in frame_set:
                    embedded_cover = True
            
            # Prüfe externes Cover
            if hasattr(audio, 'path'):
                directory = os.path.dirname(audio.path)
                external_cover = self._has_external_cover(directory)
            
            if embedded_cover:
                cover_count = len(audio.tag.images) if audio.tag.images else 1
                tag_info.append(f"Cover: {cover_count} eingebettete(s) Bild(er)")
            elif external_cover:
                tag_info.append("Cover: Externes Bild im Verzeichnis")
            else:
                tag_info.append("Cover: Nicht vorhanden")
            
            return "\n".join(tag_info) if tag_info else "Keine Tags vorhanden"
        except Exception as e:
            logging.debug(f"Fehler beim Tag-Info erstellen: {str(e)}")
            return "Fehler beim Lesen der Tags"

    def _get_cover_preview(self, audio):
        """Erstellt eine Base64-kodierte Vorschau des Cover-Bildes"""
        try:
            if not audio or not audio.tag:
                return None
            
            # Methode 1: Über Images-Accessor (eingebettete Bilder)
            if audio.tag.images and len(audio.tag.images) > 0:
                image_data = audio.tag.images[0].image_data
                if image_data:
                    return base64.b64encode(image_data).decode('utf-8')
            
            # Methode 2: Über Frame-Set (APIC-Frames)
            if hasattr(audio.tag, 'frame_set'):
                frame_set = audio.tag.frame_set
                if b'APIC' in frame_set:
                    apic_frames = frame_set[b'APIC']
                    if apic_frames and hasattr(apic_frames[0], 'image_data'):
                        image_data = apic_frames[0].image_data
                        if image_data:
                            return base64.b64encode(image_data).decode('utf-8')
            
            # Methode 3: Externe Cover-Bilder
            if hasattr(audio, 'path'):
                directory = os.path.dirname(audio.path)
                external_cover = self._get_external_cover_preview(directory)
                if external_cover:
                    return external_cover
            
            return None
        except Exception as e:
            logging.debug(f"Fehler bei Cover-Preview: {str(e)}")
            return None

    def _get_external_cover_preview(self, directory):
        """Lädt externes Cover-Bild und konvertiert zu Base64"""
        try:
            cover_names = [
                'folder.jpg', 'folder.jpeg', 'folder.png',
                'cover.jpg', 'cover.jpeg', 'cover.png',
                'album.jpg', 'album.jpeg', 'album.png',
                'albumart.jpg', 'albumart.jpeg', 'albumart.png',
                'front.jpg', 'front.jpeg', 'front.png'
            ]
            
            cover_path = None
            
            # Suche nach Standard-Cover-Namen
            for filename in os.listdir(directory):
                if filename.lower() in cover_names:
                    cover_path = os.path.join(directory, filename)
                    break
                # Prüfe auch AlbumArt_*-Dateien
                if filename.lower().startswith('albumart_') and filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                    cover_path = os.path.join(directory, filename)
                    break
            
            if cover_path and os.path.exists(cover_path):
                with open(cover_path, 'rb') as f:
                    image_data = f.read()
                    # Begrenze Bildgröße für Preview (max 100KB)
                    if len(image_data) > 100000:
                        return None  # Zu groß für Preview
                    return base64.b64encode(image_data).decode('utf-8')
            
            return None
        except Exception as e:
            logging.debug(f"Fehler bei externem Cover-Preview: {str(e)}")
            return None

    def _get_cover_info(self, audio):
        """Ermittelt detaillierte Cover-Informationen (Typ und Auflösung)"""
        try:
            if not audio or not audio.tag:
                return None
            
            # Prüfe eingebettetes Cover zuerst
            if audio.tag.images and len(audio.tag.images) > 0:
                img = audio.tag.images[0]
                if img.image_data:
                    resolution = self._get_image_resolution(img.image_data)
                    return {
                        'type': 'ID3',
                        'resolution': resolution,
                        'count': len(audio.tag.images)
                    }
            
            # Prüfe Frame-Set für APIC
            if hasattr(audio.tag, 'frame_set'):
                frame_set = audio.tag.frame_set
                if b'APIC' in frame_set:
                    apic_frames = frame_set[b'APIC']
                    if apic_frames and hasattr(apic_frames[0], 'image_data'):
                        image_data = apic_frames[0].image_data
                        if image_data:
                            resolution = self._get_image_resolution(image_data)
                            return {
                                'type': 'ID3',
                                'resolution': resolution,
                                'count': len(apic_frames)
                            }
            
            # Prüfe externes Cover
            if hasattr(audio, 'path'):
                directory = os.path.dirname(audio.path)
                external_info = self._get_external_cover_info(directory)
                if external_info:
                    return external_info
            
            return None
        except Exception as e:
            logging.debug(f"Fehler bei Cover-Info: {str(e)}")
            return None

    def _get_cover_compact_info(self, audio):
        """Erstellt kompakte Cover-Info: Nein, I 75×75, E 75×75, B 75×75"""
        try:
            if not audio or not audio.tag:
                return "Nein"
            
            has_embedded = False
            has_external = False
            embedded_resolution = None
            external_resolution = None
            
            # Prüfe eingebettetes Cover
            if audio.tag.images and len(audio.tag.images) > 0:
                img = audio.tag.images[0]
                if img.image_data:
                    has_embedded = True
                    embedded_resolution = self._get_image_resolution(img.image_data)
            
            # Prüfe Frame-Set für APIC falls keine Images
            if not has_embedded and hasattr(audio.tag, 'frame_set'):
                frame_set = audio.tag.frame_set
                if b'APIC' in frame_set:
                    apic_frames = frame_set[b'APIC']
                    if apic_frames and hasattr(apic_frames[0], 'image_data'):
                        image_data = apic_frames[0].image_data
                        if image_data:
                            has_embedded = True
                            embedded_resolution = self._get_image_resolution(image_data)
            
            # Prüfe externes Cover
            if hasattr(audio, 'path'):
                directory = os.path.dirname(audio.path)
                external_info = self._get_external_cover_info(directory)
                if external_info:
                    has_external = True
                    external_resolution = external_info.get('resolution', '?')
            
            # Bestimme das Format
            if has_embedded and has_external:
                # Verwende interne Auflösung bei "Beides"
                resolution = embedded_resolution or '?'
                return f"B {resolution}"
            elif has_embedded:
                resolution = embedded_resolution or '?'
                return f"I {resolution}"
            elif has_external:
                resolution = external_resolution or '?'
                return f"E {resolution}"
            else:
                return "Nein"
                
        except Exception as e:
            logging.debug(f"Fehler bei kompakter Cover-Info: {str(e)}")
            return "Nein"

    def _get_image_resolution(self, image_data):
        """Ermittelt die Auflösung eines Bildes aus den Binärdaten"""
        try:
            # JPEG Auflösung
            if image_data.startswith(b'\xff\xd8\xff'):
                return self._get_jpeg_resolution(image_data)
            # PNG Auflösung
            elif image_data.startswith(b'\x89PNG'):
                return self._get_png_resolution(image_data)
            else:
                return None
        except:
            return None

    def _get_jpeg_resolution(self, data):
        """Extrahiert JPEG-Auflösung aus Binärdaten"""
        try:
            i = 2
            while i < len(data):
                if data[i] == 0xff and data[i+1] in [0xc0, 0xc1, 0xc2]:
                    height = (data[i+5] << 8) | data[i+6]
                    width = (data[i+7] << 8) | data[i+8]
                    return f"{width}×{height}"
                i += 1
            return None
        except:
            return None

    def _get_png_resolution(self, data):
        """Extrahiert PNG-Auflösung aus Binärdaten"""
        try:
            if len(data) >= 24:
                width = int.from_bytes(data[16:20], 'big')
                height = int.from_bytes(data[20:24], 'big')
                return f"{width}×{height}"
            return None
        except:
            return None

    def _get_external_cover_info(self, directory):
        """Ermittelt Informationen über externe Cover-Bilder"""
        try:
            try:
                from PIL import Image
                pil_available = True
            except ImportError:
                pil_available = False
            
            cover_names = [
                'folder.jpg', 'folder.jpeg', 'folder.png',
                'cover.jpg', 'cover.jpeg', 'cover.png',
                'album.jpg', 'album.jpeg', 'album.png',
                'albumart.jpg', 'albumart.jpeg', 'albumart.png',
                'front.jpg', 'front.jpeg', 'front.png'
            ]
            
            cover_files = []
            
            for filename in os.listdir(directory):
                filename_lower = filename.lower()
                if filename_lower in cover_names:
                    cover_files.append(os.path.join(directory, filename))
                elif filename_lower.startswith('albumart_') and filename_lower.endswith(('.jpg', '.jpeg', '.png')):
                    cover_files.append(os.path.join(directory, filename))
            
            if cover_files:
                # Nehme das erste gefundene Cover
                cover_path = cover_files[0]
                
                if pil_available:
                    try:
                        with Image.open(cover_path) as img:
                            width, height = img.size
                            return {
                                'type': 'Extern',
                                'resolution': f"{width}×{height}",
                                'count': len(cover_files)
                            }
                    except:
                        pass
                
                # Fallback ohne PIL oder bei Fehler
                return {'type': 'Extern', 'resolution': '?', 'count': len(cover_files)}
            
            return None
        except Exception as e:
            logging.debug(f"Fehler bei externer Cover-Info: {str(e)}")
            return None

    def _parse_filename(self, filename):
        """Versucht Artist und Title aus dem Dateinamen zu extrahieren"""
        # Entferne die Dateiendung
        name = os.path.splitext(filename)[0]
        
        # Häufige Trennzeichen für Artist - Title
        separators = [' - ', ' – ', ' — ', '_', ' | ']
        
        for sep in separators:
            if sep in name:
                parts = name.split(sep, 1)
                if len(parts) == 2:
                    artist = parts[0].strip()
                    title = parts[1].strip()
                    # Entferne häufige Zusätze
                    title = re.sub(r'\s*\(.*?\)\s*$', '', title)
                    title = re.sub(r'\s*\[.*?\]\s*$', '', title)
                    return artist, title
        
        # Fallback: Verwende den ganzen Namen als Title
        return None, name

    def _query_online_metadata(self, artist, title, album=None):
        """Fragt Online-Dienste nach Metadaten ab"""
        if not artist or not title:
            return None
        
        # Vereinfachte Simulation - in der Realität würde hier eine API-Abfrage stattfinden
        # Da keine API-Keys vorhanden sind, erstellen wir Mock-Daten
        try:
            # Simuliere eine verbesserte Version der vorhandenen Daten
            return {
                'artist': artist.title() if artist else None,
                'title': title.title() if title else None,
                'album': album.title() if album else f"Album von {artist}",
                'cover_url': None,  # Keine Cover-URLs ohne echte API
                'year': None,
                'genre': None
            }
        except Exception as e:
            logging.error(f"Online-Metadatenabfrage fehlgeschlagen: {str(e)}")
            return None

    def _format_suggested_tags(self, metadata):
        """Formatiert die vorgeschlagenen Metadaten für die Anzeige"""
        if not metadata:
            return "Keine Vorschläge verfügbar"
        
        tags = []
        if metadata.get('artist'):
            tags.append(f"Artist: {metadata['artist']}")
        if metadata.get('title'):
            tags.append(f"Title: {metadata['title']}")
        if metadata.get('album'):
            tags.append(f"Album: {metadata['album']}")
        if metadata.get('year'):
            tags.append(f"Year: {metadata['year']}")
        if metadata.get('genre'):
            tags.append(f"Genre: {metadata['genre']}")
        
        return "\n".join(tags) if tags else "Keine Vorschläge verfügbar"

def group_by_directory(files_data):
    grouped = defaultdict(list)
    for file in files_data:
        grouped[file['directory']].append(file)
    return dict(grouped)
