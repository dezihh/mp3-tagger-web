"""
Audio Fingerprinting Module
Modul für Audio-Fingerprinting Funktionalitäten
"""

import logging
import subprocess
import json
import os
import tempfile

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class AudioFingerprintService:
    """Service für Audio-Fingerprinting und verwandte Funktionen"""
    
    def __init__(self):
        # Lazy import um zirkuläre Abhängigkeiten zu vermeiden
        self._audio_recognition = None
        self.min_confidence = 0.6
        
    @property
    def audio_recognition(self):
        """Lazy loading für AudioRecognitionService"""
        if self._audio_recognition is None:
            from .audio_recognition import AudioRecognitionService
            self._audio_recognition = AudioRecognitionService()
        return self._audio_recognition
        
    def get_audio_fingerprint_metadata(self, file_path):
        """
        Holt Metadaten über Audio-Fingerprinting
        
        Args:
            file_path (str): Pfad zur Audio-Datei
            
        Returns:
            dict: Gefundene Metadaten oder None
        """
        try:
            # Verwende Audio-Recognition Service
            result = self.audio_recognition.recognize_audio_file(file_path)
            
            if result and result.get('confidence', 0) >= self.min_confidence:
                logging.info(f"✅ Audio-Fingerprinting erfolgreich mit {result.get('service')}")
                return result
            
            logging.warning(f"❌ Audio-Fingerprinting fehlgeschlagen für {file_path}")
            return None
            
        except Exception as e:
            logging.error(f"Fehler bei Audio-Fingerprinting: {str(e)}")
            return None
    
    def create_audio_fingerprint(self, file_path):
        """
        Erstellt einen Audio-Fingerprint für eine Datei
        
        Args:
            file_path (str): Pfad zur Audio-Datei
            
        Returns:
            dict: Fingerprint-Daten oder None
        """
        try:
            # Verwende fpcalc für Fingerprint-Erstellung
            cmd = ['fpcalc', '-json', file_path]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                return {
                    'fingerprint': data.get('fingerprint'),
                    'duration': data.get('duration'),
                    'file_path': file_path
                }
            else:
                logging.error(f"fpcalc Fehler: {result.stderr}")
                return None
                
        except subprocess.TimeoutExpired:
            logging.error(f"fpcalc Timeout für {file_path}")
            return None
        except Exception as e:
            logging.error(f"Fingerprint-Erstellung fehlgeschlagen: {str(e)}")
            return None
    
    def compare_audio_fingerprints(self, file_path1, file_path2):
        """
        Vergleicht Audio-Fingerprints von zwei Dateien
        
        Args:
            file_path1 (str): Pfad zur ersten Audio-Datei
            file_path2 (str): Pfad zur zweiten Audio-Datei
            
        Returns:
            dict: Vergleichsergebnis mit Similarity-Score
        """
        try:
            fp1 = self.create_audio_fingerprint(file_path1)
            fp2 = self.create_audio_fingerprint(file_path2)
            
            if not fp1 or not fp2:
                return None
            
            # Einfacher Fingerprint-Vergleich (vereinfacht)
            similarity = self._calculate_fingerprint_similarity(
                fp1['fingerprint'], 
                fp2['fingerprint']
            )
            
            return {
                'file1': file_path1,
                'file2': file_path2,
                'similarity': similarity,
                'duration1': fp1['duration'],
                'duration2': fp2['duration'],
                'is_similar': similarity > 0.8
            }
            
        except Exception as e:
            logging.error(f"Fingerprint-Vergleich fehlgeschlagen: {str(e)}")
            return None
    
    def _calculate_fingerprint_similarity(self, fp1, fp2):
        """Berechnet Ähnlichkeit zwischen zwei Fingerprints (vereinfacht)"""
        try:
            # Vereinfachter Vergleich basierend auf String-Ähnlichkeit
            from difflib import SequenceMatcher
            
            matcher = SequenceMatcher(None, fp1, fp2)
            return matcher.ratio()
            
        except Exception:
            return 0.0
    
    def extract_audio_features(self, file_path):
        """
        Extrahiert Audio-Features aus einer Datei
        
        Args:
            file_path (str): Pfad zur Audio-Datei
            
        Returns:
            dict: Audio-Features oder None
        """
        try:
            # Verwende ffprobe für Audio-Analyse
            cmd = [
                'ffprobe', '-v', 'quiet', '-print_format', 'json',
                '-show_format', '-show_streams', file_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                
                # Extrahiere Audio-Stream Informationen
                audio_stream = None
                for stream in data.get('streams', []):
                    if stream.get('codec_type') == 'audio':
                        audio_stream = stream
                        break
                
                if audio_stream:
                    format_info = data.get('format', {})
                    
                    return {
                        'duration': float(format_info.get('duration', 0)),
                        'bitrate': int(format_info.get('bit_rate', 0)),
                        'sample_rate': int(audio_stream.get('sample_rate', 0)),
                        'channels': int(audio_stream.get('channels', 0)),
                        'codec': audio_stream.get('codec_name'),
                        'file_size': int(format_info.get('size', 0)),
                        'format_name': format_info.get('format_name'),
                        'file_path': file_path
                    }
            
            return None
            
        except Exception as e:
            logging.error(f"Audio-Feature-Extraktion fehlgeschlagen: {str(e)}")
            return None
    
    def create_audio_segment(self, file_path, start_seconds=30, duration_seconds=30):
        """
        Erstellt einen Audio-Segment für bessere Erkennung
        
        Args:
            file_path (str): Pfad zur Audio-Datei
            start_seconds (int): Start-Zeit in Sekunden
            duration_seconds (int): Dauer des Segments in Sekunden
            
        Returns:
            str: Pfad zum temporären Segment oder None
        """
        try:
            # Erstelle temporäre Datei
            temp_fd, temp_path = tempfile.mkstemp(suffix='.mp3', prefix='audio_segment_')
            os.close(temp_fd)
            
            # Verwende ffmpeg für Segment-Erstellung
            cmd = [
                'ffmpeg', '-i', file_path,
                '-ss', str(start_seconds),
                '-t', str(duration_seconds),
                '-acodec', 'copy',
                '-y', temp_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0 and os.path.exists(temp_path):
                return temp_path
            else:
                # Aufräumen bei Fehler
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                return None
                
        except Exception as e:
            logging.error(f"Audio-Segment-Erstellung fehlgeschlagen: {str(e)}")
            return None
    
    def cleanup_temp_file(self, temp_path):
        """Räumt temporäre Datei auf"""
        try:
            if temp_path and os.path.exists(temp_path):
                os.unlink(temp_path)
                logging.debug(f"Temporäre Datei gelöscht: {temp_path}")
        except Exception as e:
            logging.error(f"Fehler beim Löschen der temporären Datei: {str(e)}")


def get_audio_fingerprint_metadata(file_path):
    """
    Standalone-Funktion für Audio-Fingerprinting Metadaten
    
    Args:
        file_path (str): Pfad zur Audio-Datei
        
    Returns:
        dict: Gefundene Metadaten oder None
    """
    service = AudioFingerprintService()
    return service.get_audio_fingerprint_metadata(file_path)


def create_audio_fingerprint(file_path):
    """
    Standalone-Funktion für Fingerprint-Erstellung
    
    Args:
        file_path (str): Pfad zur Audio-Datei
        
    Returns:
        dict: Fingerprint-Daten oder None
    """
    service = AudioFingerprintService()
    return service.create_audio_fingerprint(file_path)


def compare_audio_files(file_path1, file_path2):
    """
    Standalone-Funktion für Audio-Datei-Vergleich
    
    Args:
        file_path1 (str): Pfad zur ersten Audio-Datei
        file_path2 (str): Pfad zur zweiten Audio-Datei
        
    Returns:
        dict: Vergleichsergebnis oder None
    """
    service = AudioFingerprintService()
    return service.compare_audio_fingerprints(file_path1, file_path2)


def extract_audio_features(file_path):
    """
    Standalone-Funktion für Audio-Feature-Extraktion
    
    Args:
        file_path (str): Pfad zur Audio-Datei
        
    Returns:
        dict: Audio-Features oder None
    """
    service = AudioFingerprintService()
    return service.extract_audio_features(file_path)
