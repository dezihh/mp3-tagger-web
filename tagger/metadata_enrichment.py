"""
Metadata Enrichment Module
Modul für die Anreicherung von MP3-Dateien mit erweiterten Metadaten
"""

import logging
import asyncio
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
            
            online_meta = None
            
            if has_basic_info:
                logging.info(f"Suche erweiterte Online-Metadaten für: {file_data['filename']}")
                
                # Verwende Online-Provider für MusicBrainz/Last.fm Suche
                online_meta = self.online_provider.search_metadata(
                    filename=file_data['filename'],
                    current_artist=file_data['current_artist'],
                    current_title=file_data['current_title'],
                    current_album=file_data['current_album']
                )
                
                # Erweiterte Cover-Suche wenn kein Cover gefunden
                if online_meta and not online_meta.get('cover_url'):
                    logging.info(f"🎨 Kein Cover in MusicBrainz/Last.fm - versuche Audio-Fingerprinting für Cover")
                    audio_result = self.fingerprint_service.get_audio_fingerprint_metadata(file_data['path'])
                    if audio_result and audio_result.get('cover_url'):
                        online_meta['cover_url'] = audio_result['cover_url']
                        logging.info(f"✅ Cover über Audio-Fingerprinting gefunden")
            
            # Fallback: Audio-Erkennung wenn keine grundlegenden Infos vorhanden
            if not has_basic_info:
                logging.info(f"Keine grundlegenden ID3-Tags - verwende intelligente Fallback-Analyse für: {file_data['filename']}")
                online_meta = self._get_fallback_metadata(file_data)
            
            # Aktualisiere file_data mit gefundenen Metadaten
            if online_meta:
                file_data.update({
                    'suggested_artist': online_meta.get('artist'),
                    'suggested_title': online_meta.get('title'),
                    'suggested_album': online_meta.get('album'),
                    'suggested_genre': online_meta.get('genre'),
                    'suggested_cover_url': online_meta.get('cover_url'),
                    'suggested_full_tags': online_meta
                })
                
            return file_data
            
        except Exception as e:
            logging.error(f"Fehler bei Metadaten-Anreicherung für {file_data['filename']}: {str(e)}")
            return file_data
    
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
