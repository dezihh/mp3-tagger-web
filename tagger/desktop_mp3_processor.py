"""
Desktop-spezifische Erweiterungen für den MP3Processor
"""

import os
from pathlib import Path
from tagger import mp3_processor


class DesktopMP3Processor:
    """Desktop-spezifische MP3-Verarbeitung basierend auf den mp3_processor Funktionen"""
    
    def __init__(self):
        self.progress_callback = None
        
    def set_progress_callback(self, callback):
        """Setzt eine Callback-Funktion für Fortschrittsanzeige"""
        self.progress_callback = callback
        
    def read_id3_tags(self, file_path):
        """Liest ID3-Tags einer MP3-Datei"""
        return mp3_processor.read_mp3_file(file_path)
        
    def write_id3_tags(self, file_path, tags):
        """Schreibt ID3-Tags in eine MP3-Datei"""
        # Erstelle das erwartete Format für save_mp3_tags
        file_data = {
            'filepath': file_path,
            **tags
        }
        
        files_data = {'files': [file_data]}
        result = mp3_processor.save_mp3_tags(files_data)
        
        return result.get('success', False)
        
    def process_directory(self, directory_path):
        """
        Verarbeitet ein Verzeichnis und gibt detaillierte Datei-Informationen zurück
        """
        directory = Path(directory_path)
        if not directory.exists():
            raise ValueError(f"Verzeichnis existiert nicht: {directory_path}")
            
        # MP3-Dateien mit scan_mp3_directory finden
        grouped_files = mp3_processor.scan_mp3_directory(directory_path)
        
        # Alle Dateien aus allen Verzeichnissen sammeln
        all_files = []
        for dir_files in grouped_files.values():
            all_files.extend(dir_files)
            
        if self.progress_callback:
            self.progress_callback(0, len(all_files), "Starte Verarbeitung...")
            
        processed_files = []
        
        for i, mp3_file_info in enumerate(all_files):
            try:
                file_info = self._convert_mp3_file_info(mp3_file_info)
                processed_files.append(file_info)
                
                if self.progress_callback:
                    self.progress_callback(i + 1, len(all_files), f"Verarbeitet: {mp3_file_info.filename}")
                    
            except Exception as e:
                print(f"Fehler bei Datei {mp3_file_info.file_path}: {e}")
                # Fehlerhafte Datei trotzdem hinzufügen mit Fehlerinformation
                processed_files.append({
                    'filepath': mp3_file_info.file_path,
                    'filename': mp3_file_info.filename,
                    'error': str(e),
                    'title': '',
                    'artist': '',
                    'album': '',
                    'year': '',
                    'track': '',
                    'cover_status': 'Fehler'
                })
                
        return {
            'directory': directory_path,
            'files': processed_files,
            'total_files': len(processed_files),
            'error_files': len([f for f in processed_files if 'error' in f])
        }
        
    def _convert_mp3_file_info(self, mp3_file_info):
        """Konvertiert MP3FileInfo zu einem Dictionary für die GUI"""
        return {
            'filepath': mp3_file_info.file_path,  # Korrekte Attribut-Bezeichnung
            'filename': mp3_file_info.filename,
            'size': getattr(mp3_file_info, 'size', 0),
            'modified': getattr(mp3_file_info, 'modified', 0),
            'title': mp3_file_info.title or '',
            'artist': mp3_file_info.artist or '',
            'album': mp3_file_info.album or '',
            'year': mp3_file_info.year or '',
            'track': mp3_file_info.track_number or '',
            'genre': mp3_file_info.genre or '',
            'duration': getattr(mp3_file_info, 'duration', 0),
            'cover_status': self._determine_cover_status_from_mp3_info(mp3_file_info),
            'has_embedded_cover': hasattr(mp3_file_info, 'cover_data') and mp3_file_info.cover_data is not None,
            'bitrate': getattr(mp3_file_info, 'bitrate', 0),
            'sample_rate': getattr(mp3_file_info, 'sample_rate', 0)
        }
        
    def _determine_cover_status_from_mp3_info(self, mp3_file_info):
        """Bestimmt den Cover-Status aus MP3FileInfo"""
        if hasattr(mp3_file_info, 'cover_resolution') and mp3_file_info.cover_resolution:
            return mp3_file_info.cover_resolution
        elif hasattr(mp3_file_info, 'cover_data') and mp3_file_info.cover_data:
            return "I??x??"  # Embedded Cover unbekannter Größe
        else:
            return "Nein"
        
    def _process_single_file(self, file_path):
        """Verarbeitet eine einzelne MP3-Datei und extrahiert alle relevanten Informationen"""
        # Erstelle MP3FileInfo Objekt
        mp3_file_info = mp3_processor.MP3FileInfo(file_path)
        return self._convert_mp3_file_info(mp3_file_info)
        
    def _determine_cover_status(self, file_path, tags):
        """Bestimmt den Cover-Status einer Datei"""
        # Diese Methode wird nicht mehr verwendet, da _determine_cover_status_from_mp3_info verwendet wird
        return "Unbekannt"
        
    def update_file_metadata(self, file_path, metadata):
        """Aktualisiert die Metadaten einer einzelnen Datei"""
        try:
            # Bestehende Tags lesen
            current_tags = mp3_processor.read_mp3_file(file_path)
            
            # Mit neuen Metadaten zusammenführen
            updated_tags = {**current_tags, **metadata}
            
            # Tags schreiben
            return self.write_id3_tags(file_path, updated_tags)
            
        except Exception as e:
            print(f"Fehler beim Update der Metadaten für {file_path}: {e}")
            return False
            
    def batch_update_metadata(self, file_metadata_pairs, progress_callback=None):
        """Aktualisiert Metadaten für mehrere Dateien"""
        total_files = len(file_metadata_pairs)
        successful_updates = 0
        failed_updates = []
        
        for i, (file_path, metadata) in enumerate(file_metadata_pairs):
            try:
                if self.update_file_metadata(file_path, metadata):
                    successful_updates += 1
                else:
                    failed_updates.append(file_path)
                    
                if progress_callback:
                    progress_callback(i + 1, total_files, f"Aktualisiert: {Path(file_path).name}")
                    
            except Exception as e:
                failed_updates.append(file_path)
                print(f"Fehler beim Batch-Update für {file_path}: {e}")
                
        return {
            'total_files': total_files,
            'successful_updates': successful_updates,
            'failed_updates': failed_updates,
            'success_rate': successful_updates / total_files if total_files > 0 else 0
        }
