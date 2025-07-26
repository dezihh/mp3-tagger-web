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
from .online_metadata import OnlineMetadataProvider
from .fallback_analysis import FallbackAnalyzer

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
        # Initialisiere Online-Metadata-Provider
        self.online_provider = OnlineMetadataProvider()
        # Initialisiere Fallback-Analyzer
        self.fallback_analyzer = FallbackAnalyzer()

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
        """Erweiterte Metadatenabfrage mit Online-Diensten"""
        results = []
        
        for file_data in files_data:
            try:
                # Prüfe ob Online-Suche sinnvoll ist
                has_basic_info = (
                    file_data['current_artist'] and 
                    file_data['current_title']
                )
                
                online_meta = None
                
                if has_basic_info:
                    logging.info(f"Suche erweiterte Online-Metadaten für: {file_data['filename']}")
                    
                    # Verwende neuen Online-Provider
                    online_meta = self.online_provider.search_metadata(
                        filename=file_data['filename'],
                        current_artist=file_data['current_artist'],
                        current_title=file_data['current_title'],
                        current_album=file_data['current_album']
                    )
                    
                    # 🎨 Erweiterte Cover-Suche: Wenn kein Cover gefunden, versuche Audio-Fingerprinting
                    if online_meta and not online_meta.get('cover_url'):
                        logging.info(f"🎨 Kein Cover in MusicBrainz/Last.fm - versuche Audio-Fingerprinting für Cover")
                        try:
                            # analyze_audio_fingerprint ist bereits sync und führt async intern aus
                            audio_result = self.fallback_analyzer.analyze_audio_fingerprint(file_data['path'])
                            if audio_result and audio_result.get('cover_url'):
                                online_meta['cover_url'] = audio_result['cover_url']
                                logging.info(f"🎨 Cover via Audio-Fingerprinting gefunden: {audio_result['cover_url'][:60]}...")
                                # Ergänze auch Streaming-Links
                                if audio_result.get('spotify_url'):
                                    online_meta['spotify_url'] = audio_result['spotify_url']
                                if audio_result.get('youtube_url'):
                                    online_meta['youtube_url'] = audio_result['youtube_url']
                                # Ergänze Service-Information für erweiterte Anzeige
                                if audio_result.get('service'):
                                    online_meta['cover_service'] = audio_result['service']
                        except Exception as e:
                            logging.warning(f"🎨 Audio-Fingerprinting für Cover fehlgeschlagen: {e}")
                else:
                    # Prüfe ob Fallback-Strategien nötig sind
                    logging.info(f"🔍 Keine ID3-Tags - aktiviere Fallback-Strategien für: {file_data['filename']}")
                    
                    # Prüfe ob Dateiname aussagekräftig ist
                    has_meaningful_filename = not any(bad_word in file_data['filename'].lower() 
                                                     for bad_word in ['ohne_id3', 'noname', 'track', 'unknown', 'untitled'])
                    
                    if has_meaningful_filename:
                        # Für aussagekräftige Dateinamen: Erst Pfad-Analyse, dann Audio-Fingerprinting
                        logging.info(f"📁 Dateiname aussagekräftig - versuche Pfad-Analyse")
                        fallback_suggestions = self.fallback_analyzer.get_fallback_suggestions(file_data['path'])
                    else:
                        # Für nichtssagende Dateinamen: Direkt Audio-Fingerprinting
                        logging.info(f"🎵 Dateiname nicht aussagekräftig - verwende Audio-Fingerprinting direkt")
                        try:
                            # analyze_audio_fingerprint ist bereits sync und führt async intern aus
                            audio_result = self.fallback_analyzer.analyze_audio_fingerprint(file_data['path'])
                            if audio_result and audio_result.get('confidence', 0) > 0:
                                fallback_suggestions = [audio_result]  # Als Liste formatieren
                            else:
                                fallback_suggestions = []
                        except Exception as e:
                            logging.warning(f"🎵 Audio-Fingerprinting fehlgeschlagen: {e}")
                            fallback_suggestions = []
                    
                    # Verarbeite Fallback-Ergebnisse
                    if fallback_suggestions:
                        best_fallback = fallback_suggestions[0]  # Höchste Confidence
                        logging.info(f"✅ Fallback gefunden via {best_fallback.get('method', 'unknown')}: "
                                   f"{best_fallback.get('artist')} - {best_fallback.get('title')} "
                                   f"(Confidence: {best_fallback.get('confidence', 0):.2f})")
                        
                        # Bei guter Confidence: Verwende für Online-Suche
                        if best_fallback.get('confidence', 0) > 0.6:
                            fallback_online_meta = self.online_provider.search_metadata(
                                filename=file_data['filename'],
                                current_artist=best_fallback.get('artist'),
                                current_title=best_fallback.get('title'),
                                current_album=best_fallback.get('album')
                            )
                            
                            if fallback_online_meta and fallback_online_meta.get('confidence', 0) > 0.5:
                                online_meta = fallback_online_meta
                                online_meta['fallback_method'] = best_fallback.get('method', 'unknown')
                                online_meta['service'] = best_fallback.get('service')
                                # Behalte Audio-Fingerprinting IDs
                                if best_fallback.get('acoustid'):
                                    online_meta['acoustid'] = best_fallback['acoustid']
                                if best_fallback.get('musicbrainz_id'):
                                    online_meta['musicbrainz_id'] = best_fallback['musicbrainz_id']
                                if best_fallback.get('shazam_track_id'):
                                    online_meta['shazam_track_id'] = best_fallback['shazam_track_id']
                                # WICHTIG: Bevorzuge Shazam Cover wenn MusicBrainz keins hat
                                if best_fallback.get('cover_url') and not online_meta.get('cover_url'):
                                    online_meta['cover_url'] = best_fallback['cover_url']
                                    logging.info(f"🎨 Verwende Shazam Cover: {best_fallback['cover_url'][:60]}...")
                                # Bevorzuge Shazam Streaming-Links
                                if best_fallback.get('spotify_url'):
                                    online_meta['spotify_url'] = best_fallback['spotify_url']
                                if best_fallback.get('youtube_url'):
                                    online_meta['youtube_url'] = best_fallback['youtube_url']
                                logging.info(f"✅ Fallback → Online erfolgreich: {online_meta['source']}")
                            else:
                                # Verwende Fallback-Daten direkt
                                online_meta = {
                                    'artist': best_fallback.get('artist'),
                                    'title': best_fallback.get('title'),
                                    'album': best_fallback.get('album'),
                                    'genre': best_fallback.get('genre'),
                                    'year': best_fallback.get('year'),
                                    'confidence': best_fallback.get('confidence', 0),
                                    'source': f"Fallback ({best_fallback.get('method', 'unknown')})",
                                    'fallback_method': best_fallback.get('method', 'unknown'),
                                    'service': best_fallback.get('service'),
                                    
                                    # Audio-Fingerprinting IDs
                                    'acoustid': best_fallback.get('acoustid'),
                                    'musicbrainz_id': best_fallback.get('musicbrainz_id'),
                                    'shazam_track_id': best_fallback.get('shazam_track_id'),
                                    
                                    # Cover und Streaming-Links (besonders von Shazam)
                                    'cover_url': best_fallback.get('cover_url'),
                                    'spotify_url': best_fallback.get('spotify_url'),
                                    'youtube_url': best_fallback.get('youtube_url')
                                }
                                logging.info(f"📋 Verwende Fallback-Daten direkt ({best_fallback.get('service', 'unknown')})")
                        else:
                            # Auch niedrige Confidence verwenden
                            logging.info(f"🔍 Niedrige Fallback-Confidence ({best_fallback.get('confidence', 0):.2f}) - verwende trotzdem")
                            online_meta = {
                                'artist': best_fallback.get('artist'),
                                'title': best_fallback.get('title'),
                                'album': best_fallback.get('album'),
                                'confidence': best_fallback.get('confidence', 0),
                                'source': f"Fallback ({best_fallback.get('service', 'unknown')})",
                                'fallback_method': best_fallback.get('method', 'unknown'),
                                'service': best_fallback.get('service'),
                                'acoustid': best_fallback.get('acoustid'),
                                'musicbrainz_id': best_fallback.get('musicbrainz_id'),
                                'shazam_track_id': best_fallback.get('shazam_track_id'),
                                'cover_url': best_fallback.get('cover_url'),
                                'spotify_url': best_fallback.get('spotify_url'),
                                'youtube_url': best_fallback.get('youtube_url')
                            }
                    else:
                        logging.warning(f"❌ Keine Fallback-Strategien erfolgreich für: {file_data['filename']}")
                
                # Verarbeite Ergebnisse
                if online_meta and online_meta.get('confidence', 0) > 0.3:
                        # Erstelle erweiterte Metadaten-Anzeige
                        suggested_tags = self._format_enhanced_suggested_tags(online_meta)
                        
                        file_data.update({
                            'suggested_artist': online_meta.get('artist'),
                            'suggested_title': online_meta.get('title'),
                            'suggested_album': online_meta.get('album'),
                            'suggested_genre': online_meta.get('genre'),
                            'suggested_cover_url': online_meta.get('cover_url'),
                            'suggested_full_tags': suggested_tags,
                            'online_metadata': online_meta  # Vollständige Metadaten für erweiterte Anzeige
                        })
                        
                        source_info = online_meta.get('source', 'Unknown')
                        if online_meta.get('fallback_method'):
                            source_info += f" (via {online_meta['fallback_method']})"
                        
                        logging.info(f"✓ Metadaten gesetzt: {online_meta.get('artist')} - {online_meta.get('title')} "
                                   f"via {source_info} (Vertrauen: {online_meta.get('confidence', 0):.2f})")
                else:
                    if online_meta and online_meta.get('confidence'):
                        logging.warning(f"✗ Niedrige Konfidenz ({online_meta['confidence']:.2f}) für: {file_data['filename']}")
                    else:
                        logging.warning(f"✗ Keine verwertbaren Metadaten für: {file_data['filename']}")
                    # Setze Fallback-Werte für eine saubere Anzeige
                    file_data.update({
                        'suggested_artist': None,
                        'suggested_title': None,
                        'suggested_album': None,
                        'suggested_genre': None,
                        'suggested_cover_url': None,
                        'suggested_full_tags': None,
                        'online_metadata': None
                    })
                
                results.append(file_data)
                
            except Exception as e:
                logging.error(f"Metadatenabfrage fehlgeschlagen für {file_data['filename']}: {str(e)}")
                results.append(file_data)
        
        return results

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
        if online_meta.get('year'):
            tags.append(f"Year: {online_meta['year']}")
        
        # Erweiterte Metadaten
        if online_meta.get('track_number'):
            tags.append(f"Track: {online_meta['track_number']}")
        if online_meta.get('total_tracks'):
            tags.append(f"Total Tracks: {online_meta['total_tracks']}")
        
        # Eindeutige IDs
        if online_meta.get('musicbrainz_recording_id'):
            tags.append(f"MusicBrainz Recording ID: {online_meta['musicbrainz_recording_id']}")
        if online_meta.get('musicbrainz_artist_id'):
            tags.append(f"MusicBrainz Artist ID: {online_meta['musicbrainz_artist_id']}")
        if online_meta.get('musicbrainz_release_id'):
            tags.append(f"MusicBrainz Release ID: {online_meta['musicbrainz_release_id']}")
        
        # Genres
        if online_meta.get('genre'):
            tags.append(f"Genre: {online_meta['genre']}")
        if online_meta.get('additional_genres'):
            additional = ', '.join(online_meta['additional_genres'])
            tags.append(f"Additional Genres: {additional}")
        
        # Erweiterte Klassifizierung
        if online_meta.get('era'):
            tags.append(f"Era: {online_meta['era']}")
        if online_meta.get('mood') and online_meta['mood']:
            mood_str = ', '.join(online_meta['mood'])
            tags.append(f"Mood: {mood_str}")
        if online_meta.get('style') and online_meta['style']:
            style_str = ', '.join(online_meta['style'])
            tags.append(f"Style: {style_str}")
        if online_meta.get('similar_artists') and online_meta['similar_artists']:
            similar_str = ', '.join(online_meta['similar_artists'])
            tags.append(f"Similar Artists: {similar_str}")
        if online_meta.get('instrumentation') and online_meta['instrumentation']:
            instr_str = ', '.join(online_meta['instrumentation'])
            tags.append(f"Instrumentation: {instr_str}")
        if online_meta.get('energy_level'):
            tags.append(f"Energy Level: {online_meta['energy_level']}")
        if online_meta.get('tempo_description'):
            tags.append(f"Tempo: {online_meta['tempo_description']}")
        
        # Metainformationen
        tags.append(f"Source: {online_meta.get('source', 'Unknown')}")
        tags.append(f"Confidence: {online_meta.get('confidence', 0.0):.1%}")
        
        return '\n'.join(tags)

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

def group_by_directory(files_data):
    grouped = defaultdict(list)
    for file in files_data:
        grouped[file['directory']].append(file)
    return dict(grouped)
