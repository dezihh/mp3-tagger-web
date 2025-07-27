"""
Metadata Enrichment Module
Modul für die Anreicherung von MP3-Dateien mit erweiterten Metadaten
"""

import logging
import asyncio
import requests
from .online_metadata import OnlineMetadataProvider

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class MetadataEnrichmentService:
    """Service für die intelligente Anreicherung von Metadaten"""
    
    def __init__(self):
        self.online_provider = OnlineMetadataProvider()
        # Lazy imports um zirkuläre Abhängigkeiten zu vermeiden
        self._audio_recognition = None
        self._fingerprint_service = None
        
    @property
    def audio_recognition(self):
        """Lazy loading für AudioRecognitionService"""
        if self._audio_recognition is None:
            from .audio_recognition import AudioRecognitionService
            self._audio_recognition = AudioRecognitionService()
        return self._audio_recognition
        
    @property
    def fingerprint_service(self):
        """Lazy loading für AudioFingerprintService"""
        if self._fingerprint_service is None:
            from .fingerprinting import AudioFingerprintService
            self._fingerprint_service = AudioFingerprintService()
        return self._fingerprint_service
        
    def enrich_file_metadata(self, file_data):
        """
        Reichert eine einzelne Datei mit erweiterten Metadaten an
        
        Args:
            file_data (dict): Dateiinformationen mit aktuellen Metadaten
            
        Returns:
            dict: Angereicherte Dateiinformationen
        """
        try:
            # Prüfe ob bereits grundlegende Informationen vorhanden sind
            has_basic_info = (
                file_data['current_artist'] and 
                file_data['current_title']
            )
            
            enriched_data = {}
            
            if has_basic_info:
                logging.info(f"🌐 Starte umfassende Datenanreicherung für: {file_data['filename']}")
                
                # 1. Basis-Metadaten über Online-Provider
                online_meta = self.online_provider.search_metadata(
                    filename=file_data['filename'],
                    current_artist=file_data['current_artist'],
                    current_title=file_data['current_title'],
                    current_album=file_data['current_album']
                )
                
                if online_meta:
                    logging.info(f"✅ Basis-Metadaten gefunden")
                    enriched_data.update({
                        'artist': online_meta.get('artist', file_data['current_artist']),
                        'title': online_meta.get('title', file_data['current_title']),
                        'album': online_meta.get('album', file_data['current_album']),
                        'genre': online_meta.get('genre'),
                        'release_date': online_meta.get('release_date'),
                        'musicbrainz_id': online_meta.get('musicbrainz_id')
                    })
                
                # 2. Erweiterte Genre-Analyse über Last.fm
                try:
                    detailed_genre = self.online_provider.get_detailed_genre_analysis(
                        file_data['current_artist'], 
                        file_data['current_title']
                    )
                    if detailed_genre:
                        enriched_data['detailed_genre'] = detailed_genre
                        logging.info(f"🎭 Detaillierte Genre-Analyse: {detailed_genre.get('primary_genre')}")
                except Exception as e:
                    logging.warning(f"Genre-Analyse fehlgeschlagen: {str(e)}")
                
                # 3. Mood und Era Analyse
                try:
                    mood_era = self.online_provider.get_mood_and_era_analysis(
                        file_data['current_artist'], 
                        file_data['current_title']
                    )
                    if mood_era:
                        enriched_data.update({
                            'mood': mood_era.get('mood'),
                            'era': mood_era.get('era'),
                            'atmospheric_tags': mood_era.get('atmospheric_tags', [])
                        })
                        logging.info(f"🎵 Mood/Era: {mood_era.get('mood')} / {mood_era.get('era')}")
                except Exception as e:
                    logging.warning(f"Mood/Era-Analyse fehlgeschlagen: {str(e)}")
                
                # 4. Ähnliche Künstler für Kontext
                try:
                    similar_artists = self.online_provider.get_similar_artists(file_data['current_artist'])
                    if similar_artists:
                        enriched_data['similar_artists'] = similar_artists[:5]  # Top 5
                        logging.info(f"👥 Ähnliche Künstler: {', '.join(similar_artists[:3])}")
                except Exception as e:
                    logging.warning(f"Ähnliche-Künstler-Analyse fehlgeschlagen: {str(e)}")
                
                # 5. Cover-Art Sammlung (URLs sammeln)
                cover_candidates = []
                
                # Cover-Kandidat 1: MusicBrainz/Last.fm - immer sammeln
                if online_meta and online_meta.get('cover_url'):
                    cover_candidates.append({
                        'url': online_meta['cover_url'],
                        'source': 'MusicBrainz/Last.fm',
                        'quality': 'high'
                    })
                    logging.info(f"🎨 Cover-URL von MusicBrainz/Last.fm gefunden")
                
                # Cover-Kandidat 2: Audio-Fingerprinting - immer versuchen
                try:
                    audio_result = self.fingerprint_service.get_audio_fingerprint_metadata(file_data['path'])
                    if audio_result and audio_result.get('cover_url'):
                        cover_candidates.append({
                            'url': audio_result['cover_url'],
                            'source': 'Audio-Fingerprinting',
                            'quality': 'medium'
                        })
                        logging.info(f"🎨 Cover-URL von Audio-Fingerprinting gefunden")
                except Exception as e:
                    logging.warning(f"Audio-Fingerprinting Cover-Suche fehlgeschlagen: {str(e)}")
                
                # Prüfe vorhandenes Cover in der MP3-Datei
                existing_cover = self._get_existing_cover_info(file_data['path'])
                has_existing_cover = existing_cover and existing_cover.get('has_cover', False)
                
                # Setze suggested_cover_url für automatische Einbettung wenn kein Cover vorhanden
                if not has_existing_cover and cover_candidates:
                    # Wähle bestes verfügbares Cover (erstes = höchste Qualität)
                    enriched_data['suggested_cover_url'] = cover_candidates[0]['url']
                    logging.info(f"🎨 Cover-URL für automatische Einbettung gesetzt: {cover_candidates[0]['source']}")
                
                enriched_data.update({
                    'cover_candidates': cover_candidates,
                    'existing_cover': existing_cover,
                    'cover_preview_available': len(cover_candidates) > 0  # Immer verfügbar wenn Cover gefunden
                })
                
            else:
                # Fallback: Audio-Erkennung wenn keine grundlegenden Infos vorhanden
                logging.info(f"🔍 Keine grundlegenden ID3-Tags - verwende intelligente Fallback-Analyse")
                fallback_meta = self._get_fallback_metadata(file_data)
                if fallback_meta:
                    enriched_data = fallback_meta
                
            return enriched_data if enriched_data else None
            
        except Exception as e:
            logging.error(f"Fehler bei umfassender Anreicherung für {file_data['filename']}: {str(e)}")
            return None
    
    def _get_existing_cover_info(self, file_path):
        """Prüft ob bereits ein Cover in der MP3-Datei vorhanden ist"""
        try:
            import eyed3
            from tagger.core import MusicTagger
            tagger = MusicTagger()
            
            # Lade ID3-Tags und prüfe auf vorhandenes Cover
            audiofile = eyed3.load(file_path)
            if audiofile and audiofile.tag:
                images = audiofile.tag.images
                if images:
                    # Erstes gefundenes Bild analysieren
                    image = list(images)[0]
                    return {
                        'has_cover': True,
                        'size': len(image.image_data) if image.image_data else 0,
                        'format': image.mime_type,
                        'description': image.description or 'Vorhandenes Cover'
                    }
            
            return {'has_cover': False}
            
        except Exception as e:
            logging.error(f"Fehler beim Prüfen des vorhandenen Covers: {str(e)}")
            return {'has_cover': False}

    def _download_and_embed_cover(self, file_path, cover_url):
        """Download und Einbettung von Cover-Art"""
        try:
            from tagger.core import MusicTagger
            tagger = MusicTagger()
            
            # Download Cover
            response = requests.get(cover_url, timeout=10)
            if response.status_code == 200:
                cover_data = response.content
                
                # Einbettung in MP3
                success = tagger.embed_cover_art(file_path, cover_data)
                return success
            return False
        except Exception as e:
            logging.error(f"Cover-Download/-Einbettung fehlgeschlagen: {str(e)}")
            return False
    
    def enrich_multiple_files(self, files_data):
        """
        Reichert mehrere Dateien mit erweiterten Metadaten an
        
        Args:
            files_data (list): Liste von Dateiinformationen
            
        Returns:
            list: Liste angereicherte Dateiinformationen
        """
        results = []
        
        for file_data in files_data:
            enriched_file = self.enrich_file_metadata(file_data)
            results.append(enriched_file)
            
        return results
    
    def _get_fallback_metadata(self, file_data):
        """
        Intelligente Fallback-Analyse für Dateien ohne grundlegende Metadaten
        
        Args:
            file_data (dict): Dateiinformationen
            
        Returns:
            dict: Gefundene Metadaten oder None
        """
        try:
            # 1. Versuche Pfad-Analyse
            path_metadata = self._analyze_file_path(file_data)
            if path_metadata:
                logging.info(f"✅ Metadaten über Pfad-Analyse gefunden")
                return path_metadata
            
            # 2. Prüfe ob Dateiname aussagekräftig ist
            if not self._has_meaningful_filename(file_data['filename']):
                logging.info(f"📂 Aussagekräftiger Dateiname erkannt - verwende bestehende Suche")
                return self.online_provider.search_metadata(
                    filename=file_data['filename'],
                    current_artist=file_data['current_artist'],
                    current_title=file_data['current_title'],
                    current_album=file_data['current_album']
                )
            
            # 3. Audio-Erkennung als letzter Fallback
            logging.info(f"🎵 Verwende Audio-Erkennung für unbekannte Datei")
            return self.audio_recognition.recognize_audio_file(file_data['path'])
            
        except Exception as e:
            logging.error(f"Fehler bei Fallback-Analyse: {str(e)}")
            return None
    
    def _analyze_file_path(self, file_data):
        """Analysiert den Dateipfad auf Album/Artist Informationen"""
        try:
            path_parts = file_data['directory'].split('/')
            
            # Suche nach "Artist - Album" Pattern
            for part in reversed(path_parts[-3:]):
                if ' - ' in part:
                    parts = part.split(' - ', 1)
                    if len(parts) == 2:
                        artist, album = parts
                        
                        # Verwende Online-Suche mit Pfad-Informationen
                        return self.online_provider.search_metadata(
                            filename=file_data['filename'],
                            current_artist=artist.strip(),
                            current_title=None,
                            current_album=album.strip()
                        )
            
            return None
            
        except Exception as e:
            logging.error(f"Fehler bei Pfad-Analyse: {str(e)}")
            return None
    
    def _has_meaningful_filename(self, filename):
        """Prüft ob ein Dateiname aussagekräftig ist"""
        import re
        
        meaningless_patterns = [
            r'^track[\s_-]*\d+',
            r'^audio[\s_-]*\d+',
            r'^song[\s_-]*\d+',
            r'^untitled',
            r'^ohne.*id3',
            r'^noname',
            r'^\d+$',
            r'^[a-f0-9]{8,}$'  # Hex-Strings
        ]
        
        filename_lower = filename.lower().replace('.mp3', '')
        
        for pattern in meaningless_patterns:
            if re.match(pattern, filename_lower):
                return True
                
        return False


def enrich_file_metadata(file_data):
    """
    Standalone-Funktion für die Anreicherung einer einzelnen Datei
    
    Args:
        file_data (dict): Dateiinformationen
        
    Returns:
        dict: Angereicherte Dateiinformationen
    """
    service = MetadataEnrichmentService()
    return service.enrich_file_metadata(file_data)


def enrich_multiple_files(files_data):
    """
    Standalone-Funktion für die Anreicherung mehrerer Dateien
    
    Args:
        files_data (list): Liste von Dateiinformationen
        
    Returns:
        list: Liste angereicherte Dateiinformationen
    """
    service = MetadataEnrichmentService()
    return service.enrich_multiple_files(files_data)
