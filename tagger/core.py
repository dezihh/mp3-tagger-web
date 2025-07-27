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
import asyncio
from .metadata_enrichment import MetadataEnrichmentService

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
        # Initialisiere Metadata-Enrichment-Service
        self.metadata_service = MetadataEnrichmentService()

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
                        'current_genre': audio.tag.genre.name if audio.tag.genre else None,
                        'current_has_cover': self._has_cover(audio),
                        'current_cover_info': self._get_cover_info(audio),
                        'current_cover_compact': self._get_cover_compact_info(audio),
                        'current_full_tags': self._get_full_tag_info(audio),
                        'current_cover_preview': self._get_cover_preview(audio),
                        'suggested_artist': None,
                        'suggested_title': None,
                        'suggested_album': None,
                        'suggested_genre': None,
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
        """Erweiterte Metadatenabfrage mit modularen Services"""
        # Verwende den neuen Metadata-Enrichment-Service
        return self.metadata_service.enrich_multiple_files(files_data)

    def update_id3_tags(self, file_path, artist=None, title=None, album=None, track=None):
        """Update ID3-Tags einer MP3-Datei"""
        try:
            import eyed3
            
            audio = eyed3.load(file_path)
            if audio.tag is None:
                audio.initTag()
            
            # Update Tags wenn Werte vorhanden
            if artist:
                audio.tag.artist = artist
            if title:
                audio.tag.title = title
            if album:
                audio.tag.album = album
            if track:
                try:
                    audio.tag.track_num = int(track)
                except (ValueError, TypeError):
                    pass  # Ignoriere ungültige Track-Nummern
            
            # Speichere Änderungen
            audio.tag.save()
            logging.info(f"ID3-Tags aktualisiert: {file_path}")
            return True
            
        except Exception as e:
            logging.error(f"Fehler beim Update der ID3-Tags für {file_path}: {str(e)}")
            return False

    def _format_enhanced_suggested_tags(self, online_meta):
        """Formatiert erweiterte Online-Metadaten für die Anzeige"""
        tags = []
        
        # Basis-Informationen
        if online_meta.get('artist'):
            tags.append(f"Artist: {online_meta['artist']}")
        if online_meta.get('title'):
            tags.append(f"Title: {online_meta['title']}")
        if online_meta.get('album'):
            tags.append(f"Album: {online_meta['album']}")
        if online_meta.get('genre'):
            tags.append(f"Genre: {online_meta['genre']}")
        if online_meta.get('year'):
            tags.append(f"Year: {online_meta['year']}")
        
        # Metadaten-Quelle
        if online_meta.get('source'):
            tags.append(f"Source: {online_meta['source']}")
        
        # Konfidenz
        if online_meta.get('confidence'):
            tags.append(f"Confidence: {online_meta['confidence']:.2f}")
        
        # Cover-URL
        if online_meta.get('cover_url'):
            tags.append(f"Cover: Available")
        
        # Zusätzliche IDs für Debugging
        if online_meta.get('musicbrainz_id'):
            tags.append(f"MusicBrainz ID: {online_meta['musicbrainz_id']}")
        if online_meta.get('lastfm_mbid'):
            tags.append(f"Last.fm MBID: {online_meta['lastfm_mbid']}")
        
        # Fallback-Methode anzeigen
        if online_meta.get('fallback_method'):
            tags.append(f"Fallback Method: {online_meta['fallback_method']}")
        
        # Service-spezifische IDs
        if online_meta.get('acoustid'):
            tags.append(f"AcoustID: {online_meta['acoustid']}")
        if online_meta.get('shazam_track_id'):
            tags.append(f"Shazam ID: {online_meta['shazam_track_id']}")
        
        # Streaming-URLs
        if online_meta.get('spotify_url'):
            tags.append(f"Spotify: Available")
        if online_meta.get('youtube_url'):
            tags.append(f"YouTube: Available")
        
        return tags

    def _has_cover(self, audio):
        """Prüft ob Audio-Datei ein eingebettetes Cover hat"""
        try:
            return audio.tag and len(audio.tag.images) > 0
        except:
            return False

    def _get_cover_info(self, audio):
        """Extrahiert Cover-Informationen"""
        try:
            if audio.tag and audio.tag.images:
                image = audio.tag.images[0]
                return {
                    'type': image.picture_type,
                    'mime_type': image.mime_type,
                    'size': len(image.image_data) if image.image_data else 0,
                    'description': image.description
                }
        except:
            pass
        return None

    def _get_cover_compact_info(self, audio):
        """Kompakte Cover-Info für Anzeige"""
        cover_info = self._get_cover_info(audio)
        if cover_info:
            size_kb = cover_info['size'] // 1024
            return f"{cover_info['mime_type']} ({size_kb} KB)"
        return "None"

    def _get_cover_preview(self, audio):
        """Base64-encoded Cover-Preview"""
        try:
            if audio.tag and audio.tag.images:
                image_data = audio.tag.images[0].image_data
                if image_data:
                    return base64.b64encode(image_data).decode('utf-8')
        except:
            pass
        return None

    def _get_full_tag_info(self, audio):
        """Extrahiert alle verfügbaren Tag-Informationen"""
        try:
            if not audio.tag:
                return {}
            
            tag_info = {
                'artist': audio.tag.artist,
                'title': audio.tag.title,
                'album': audio.tag.album,
                'album_artist': audio.tag.album_artist,
                'genre': audio.tag.genre.name if audio.tag.genre else None,
                'year': audio.tag.getBestDate(),
                'track_num': audio.tag.track_num[0] if audio.tag.track_num[0] else None,
                'track_total': audio.tag.track_num[1] if audio.tag.track_num[1] else None,
                'disc_num': audio.tag.disc_num[0] if audio.tag.disc_num[0] else None,
                'disc_total': audio.tag.disc_num[1] if audio.tag.disc_num[1] else None,
                'publisher': audio.tag.publisher,
                'comments': [str(c) for c in audio.tag.comments] if audio.tag.comments else [],
                'has_cover': self._has_cover(audio),
                'cover_count': len(audio.tag.images) if audio.tag.images else 0
            }
            
            # Audio-Info
            if audio.info:
                tag_info.update({
                    'duration': audio.info.time_secs,
                    'bitrate': audio.info.bit_rate[1] if audio.info.bit_rate else None,
                    'sample_freq': audio.info.sample_freq,
                    'mode': audio.info.mode
                })
            
            return tag_info
        except Exception as e:
            logging.error(f"Fehler beim Extrahieren der Tag-Info: {str(e)}")
            return {}

    def apply_metadata(self, file_data, dry_run=True):
        """Wendet Metadaten auf eine Datei an"""
        try:
            if not file_data.get('suggested_artist') or not file_data.get('suggested_title'):
                return False, "Keine verwertbaren Metadaten verfügbar"
            
            if dry_run:
                return True, f"[DRY RUN] Würde setzen: {file_data['suggested_artist']} - {file_data['suggested_title']}"
            
            # Lade Audio-Datei
            audio = eyed3.load(file_data['path'])
            if audio.tag is None:
                audio.initTag()
            
            # Setze Metadaten
            audio.tag.artist = file_data['suggested_artist']
            audio.tag.title = file_data['suggested_title']
            if file_data.get('suggested_album'):
                audio.tag.album = file_data['suggested_album']
            if file_data.get('suggested_genre'):
                audio.tag.genre = file_data['suggested_genre']
            
            # Speichere Änderungen
            audio.tag.save()
            
            return True, f"Metadaten erfolgreich gesetzt: {file_data['suggested_artist']} - {file_data['suggested_title']}"
            
        except Exception as e:
            return False, f"Fehler beim Setzen der Metadaten: {str(e)}"

    def bulk_apply_metadata(self, files_data, dry_run=True):
        """Wendet Metadaten auf mehrere Dateien an"""
        results = []
        
        for file_data in files_data:
            success, message = self.apply_metadata(file_data, dry_run)
            results.append({
                'file': file_data['filename'],
                'success': success,
                'message': message
            })
        
        return results

    def embed_cover_art(self, file_path, cover_data):
        """
        Bettet Cover-Art in MP3-Datei ein
        
        Args:
            file_path (str): Pfad zur MP3-Datei
            cover_data (bytes): Cover-Bilddaten
            
        Returns:
            bool: True wenn erfolgreich, False sonst
        """
        try:
            audio = eyed3.load(file_path)
            if audio.tag is None:
                audio.initTag()
            
            # Entferne vorhandene Cover-Bilder
            for img in list(audio.tag.images):
                if img.picture_type == eyed3.id3.frames.ImageFrame.FRONT_COVER:
                    audio.tag.images.remove(img.description)
            
            # Füge neues Cover hinzu
            audio.tag.images.set(
                eyed3.id3.frames.ImageFrame.FRONT_COVER,
                cover_data,
                'image/jpeg'
            )
            
            # Speichere Änderungen
            audio.tag.save()
            logging.info(f"✅ Cover erfolgreich eingebettet in: {os.path.basename(file_path)}")
            return True
            
        except Exception as e:
            logging.error(f"❌ Cover-Einbettung fehlgeschlagen für {file_path}: {str(e)}")
            return False

    def remove_cover_art(self, file_path):
        """
        Entfernt alle Cover-Bilder aus MP3-Datei
        
        Args:
            file_path (str): Pfad zur MP3-Datei
            
        Returns:
            bool: True wenn erfolgreich, False sonst
        """
        try:
            audio = eyed3.load(file_path)
            if audio.tag is None:
                logging.info(f"Keine Tags in {os.path.basename(file_path)} vorhanden")
                return True
            
            # Zähle vorhandene Cover
            initial_count = len(audio.tag.images) if audio.tag.images else 0
            
            if initial_count == 0:
                logging.info(f"Keine Cover in {os.path.basename(file_path)} zum Entfernen")
                return True
            
            # Entferne alle Cover-Bilder - verwende bewährte Methode aus embed_cover_art
            images_to_remove = []
            for img in list(audio.tag.images):
                images_to_remove.append(img.description)
            
            # Entferne alle gefundenen Bilder
            for description in images_to_remove:
                try:
                    audio.tag.images.remove(description)
                    logging.info(f"Cover mit Description '{description}' entfernt")
                except Exception as e:
                    logging.warning(f"Konnte Cover mit Description '{description}' nicht entfernen: {e}")
            
            # Speichere Änderungen
            audio.tag.save()
            
            # Verifikation
            audio_verify = eyed3.load(file_path)
            final_count = len(audio_verify.tag.images) if audio_verify.tag and audio_verify.tag.images else 0
            
            if final_count == 0:
                logging.info(f"✅ Alle {initial_count} Cover erfolgreich entfernt aus: {os.path.basename(file_path)}")
                return True
            else:
                logging.warning(f"⚠️ Nur {initial_count - final_count} von {initial_count} Cover entfernt aus: {os.path.basename(file_path)}")
                return False
            
        except Exception as e:
            logging.error(f"❌ Cover-Entfernung fehlgeschlagen für {file_path}: {str(e)}")
            return False
            
            # Verifikation
            audio_verify = eyed3.load(file_path)
            final_count = len(audio_verify.tag.images) if audio_verify.tag and audio_verify.tag.images else 0
            
            if final_count == 0:
                logging.info(f"✅ Alle {initial_count} Cover erfolgreich entfernt aus: {os.path.basename(file_path)}")
                return True
            else:
                logging.warning(f"⚠️ Nur {initial_count - final_count} von {initial_count} Cover entfernt aus: {os.path.basename(file_path)}")
                return False
            
        except Exception as e:
            logging.error(f"❌ Cover-Entfernung fehlgeschlagen für {file_path}: {str(e)}")
            return False


def group_by_directory(files_data):
    """Gruppiert Dateien nach Verzeichnis"""
    grouped = defaultdict(list)
    
    for file_data in files_data:
        directory = file_data['directory']
        grouped[directory].append(file_data)
    
    # Sortiere Dateien in jedem Verzeichnis
    for directory in grouped:
        grouped[directory].sort(key=lambda x: x['filename'])
    
    return dict(grouped)


def calculate_similarity(str1, str2):
    """Berechnet Ähnlichkeit zwischen zwei Strings"""
    if not str1 or not str2:
        return 0.0
    return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()


def format_duration(seconds):
    """Formatiert Dauer in MM:SS Format"""
    if not seconds:
        return "0:00"
    
    minutes = int(seconds // 60)
    seconds = int(seconds % 60)
    return f"{minutes}:{seconds:02d}"


def clean_filename(filename):
    """Bereinigt Dateiname von problematischen Zeichen"""
    # Entferne/ersetze problematische Zeichen
    cleaned = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Entferne mehrfache Unterstriche
    cleaned = re.sub(r'_{2,}', '_', cleaned)
    # Entferne führende/abschließende Unterstriche
    cleaned = cleaned.strip('_')
    
    return cleaned


def is_valid_mp3(file_path):
    """Prüft ob Datei eine gültige MP3-Datei ist"""
    try:
        audio = eyed3.load(file_path)
        return audio is not None and audio.info is not None
    except:
        return False


def get_file_info(file_path):
    """Holt grundlegende Datei-Informationen"""
    try:
        file_path = Path(file_path)
        stat = file_path.stat()
        
        return {
            'size': stat.st_size,
            'modified': stat.st_mtime,
            'created': stat.st_ctime,
            'extension': file_path.suffix.lower(),
            'basename': file_path.stem
        }
    except:
        return None
