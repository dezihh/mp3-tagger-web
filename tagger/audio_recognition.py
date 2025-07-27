"""
Audio Recognition Module
Modul für die Erkennung von Audio-Dateien über ShazamIO und AcoustID
"""

import logging
import asyncio
import os
from shazamio import Shazam
import requests
import aiofiles

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class AudioRecognitionService:
    """Service für Audio-Erkennung mit ShazamIO und AcoustID"""
    
    def __init__(self):
        self.acoustid_api_key = os.getenv('ACOUSTID_API_KEY')
        self.min_confidence = 0.6
        
    def recognize_audio_file(self, file_path):
        """
        Erkennt eine Audio-Datei über verschiedene Services
        
        Args:
            file_path (str): Pfad zur Audio-Datei
            
        Returns:
            dict: Erkannte Metadaten oder None
        """
        try:
            # Versuche zuerst ShazamIO (primär)
            shazam_result = self.recognize_with_shazam(file_path)
            if shazam_result and shazam_result.get('confidence', 0) >= self.min_confidence:
                logging.info(f"✅ ShazamIO erfolgreich: {shazam_result.get('artist')} - {shazam_result.get('title')}")
                return shazam_result
            
            # Fallback auf AcoustID
            logging.info(f"🔄 ShazamIO erfolglos, versuche AcoustID...")
            acoustid_result = self.recognize_with_acoustid(file_path)
            if acoustid_result and acoustid_result.get('confidence', 0) >= self.min_confidence:
                logging.info(f"✅ AcoustID erfolgreich: {acoustid_result.get('artist')} - {acoustid_result.get('title')}")
                return acoustid_result
            
            logging.warning(f"❌ Keine Erkennung für {file_path}")
            return None
            
        except Exception as e:
            logging.error(f"Fehler bei Audio-Erkennung: {str(e)}")
            return None
    
    def recognize_with_shazam(self, file_path):
        """
        Erkennt Audio-Datei mit ShazamIO
        
        Args:
            file_path (str): Pfad zur Audio-Datei
            
        Returns:
            dict: ShazamIO Ergebnis oder None
        """
        try:
            # Verwende async context für ShazamIO
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(self._shazam_recognize_async(file_path))
                return result
            finally:
                loop.close()
                
        except Exception as e:
            logging.error(f"ShazamIO Fehler: {str(e)}")
            return None
    
    async def _shazam_recognize_async(self, file_path):
        """Async ShazamIO Erkennung"""
        try:
            shazam = Shazam()
            
            async with aiofiles.open(file_path, 'rb') as f:
                audio_data = await f.read()
            
            result = await shazam.recognize(audio_data)
            
            if result and 'track' in result:
                track = result['track']
                
                # Extrahiere Cover-URL
                cover_url = None
                if 'images' in track and 'coverart' in track['images']:
                    cover_url = track['images']['coverart']
                elif 'images' in track and 'background' in track['images']:
                    cover_url = track['images']['background']
                
                # Extrahiere Streaming-Links
                streaming_links = {}
                if 'hub' in track and 'providers' in track['hub']:
                    for provider in track['hub']['providers']:
                        if 'caption' in provider and 'actions' in provider:
                            for action in provider['actions']:
                                if 'uri' in action:
                                    streaming_links[provider['caption']] = action['uri']
                
                return {
                    'service': 'ShazamIO',
                    'artist': track.get('subtitle', ''),
                    'title': track.get('title', ''),
                    'album': track.get('sections', [{}])[0].get('metadata', [{}])[0].get('text', '') if track.get('sections') else '',
                    'genre': track.get('genres', {}).get('primary', '') if track.get('genres') else '',
                    'cover_url': cover_url,
                    'streaming_links': streaming_links,
                    'shazam_id': track.get('key'),
                    'confidence': 0.85,  # ShazamIO hat generell hohe Konfidenz
                    'raw_data': result
                }
            
            return None
            
        except Exception as e:
            logging.error(f"Async ShazamIO Fehler: {str(e)}")
            return None
    
    def recognize_with_acoustid(self, file_path):
        """
        Erkennt Audio-Datei mit AcoustID
        
        Args:
            file_path (str): Pfad zur Audio-Datei
            
        Returns:
            dict: AcoustID Ergebnis oder None
        """
        try:
            if not self.acoustid_api_key:
                logging.warning("AcoustID API Key nicht verfügbar")
                return None
            
            # Audio-Fingerprint erstellen
            fingerprint_data = self._create_acoustid_fingerprint(file_path)
            if not fingerprint_data:
                return None
            
            # AcoustID API Anfrage
            url = "https://api.acoustid.org/v2/lookup"
            params = {
                'client': self.acoustid_api_key,
                'duration': int(fingerprint_data['duration']),
                'fingerprint': fingerprint_data['fingerprint'],
                'meta': 'recordings'
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('status') == 'ok' and data.get('results'):
                    best_result = data['results'][0]
                    
                    if 'recordings' in best_result and best_result['recordings']:
                        recording = best_result['recordings'][0]
                        
                        return {
                            'service': 'AcoustID',
                            'artist': recording.get('artists', [{}])[0].get('name', '') if recording.get('artists') else '',
                            'title': recording.get('title', ''),
                            'album': recording.get('releases', [{}])[0].get('title', '') if recording.get('releases') else '',
                            'genre': '',  # AcoustID liefert normalerweise kein Genre
                            'cover_url': None,  # AcoustID hat keine Cover-URLs
                            'acoustid_id': recording.get('id'),
                            'confidence': best_result.get('score', 0),
                            'raw_data': data
                        }
            
            return None
            
        except Exception as e:
            logging.error(f"AcoustID Fehler: {str(e)}")
            return None
    
    def _create_acoustid_fingerprint(self, file_path):
        """Erstellt AcoustID Fingerprint"""
        try:
            import subprocess
            import json
            
            # fpcalc verwenden für Fingerprint-Erstellung
            cmd = ['fpcalc', '-json', file_path]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                return {
                    'fingerprint': data.get('fingerprint'),
                    'duration': data.get('duration')
                }
            
            return None
            
        except Exception as e:
            logging.error(f"Fingerprint-Erstellung fehlgeschlagen: {str(e)}")
            return None


def recognize_audio_file(file_path):
    """
    Standalone-Funktion für Audio-Erkennung
    
    Args:
        file_path (str): Pfad zur Audio-Datei
        
    Returns:
        dict: Erkannte Metadaten oder None
    """
    service = AudioRecognitionService()
    return service.recognize_audio_file(file_path)


def recognize_with_shazam(file_path):
    """
    Standalone-Funktion für ShazamIO Erkennung
    
    Args:
        file_path (str): Pfad zur Audio-Datei
        
    Returns:
        dict: ShazamIO Ergebnis oder None
    """
    service = AudioRecognitionService()
    return service.recognize_with_shazam(file_path)


def recognize_with_acoustid(file_path):
    """
    Standalone-Funktion für AcoustID Erkennung
    
    Args:
        file_path (str): Pfad zur Audio-Datei
        
    Returns:
        dict: AcoustID Ergebnis oder None
    """
    service = AudioRecognitionService()
    return service.recognize_with_acoustid(file_path)
