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
        try:
            # Erstelle MP3FileInfo Objekt um Tags zu lesen
            mp3_info = mp3_processor.MP3FileInfo(file_path)
            
            # Konvertiere zu Dictionary-Format für GUI-Kompatibilität
            return {
                'title': mp3_info.title or '',
                'artist': mp3_info.artist or '',
                'album': mp3_info.album or '',
                'year': mp3_info.year or '',
                'track': mp3_info.track_number or '',
                'genre': mp3_info.genre or '',
                'extended_metadata': mp3_info.extended_metadata or {}
            }
        except Exception as e:
            print(f"Fehler beim Lesen der ID3-Tags für {file_path}: {e}")
            return {
                'title': '', 'artist': '', 'album': '', 'year': '', 'track': '', 'genre': '',
                'extended_metadata': {}
            }
        
    def write_id3_tags(self, file_path, tags):
        """Schreibt ID3-Tags in eine MP3-Datei"""
        try:
            from mutagen.mp3 import MP3
            from mutagen.id3 import ID3, TIT2, TPE1, TALB, TDRC, TRCK, TCON, TXXX, TBPM, POPM, COMM, USLT, TDRL
            
            # MP3-Datei laden
            mp3_file = MP3(file_path)
            
            # Basis-Tags setzen
            if 'title' in tags and tags['title']:
                mp3_file['TIT2'] = TIT2(encoding=3, text=tags['title'])
            if 'artist' in tags and tags['artist']:
                mp3_file['TPE1'] = TPE1(encoding=3, text=tags['artist'])
            if 'album' in tags and tags['album']:
                mp3_file['TALB'] = TALB(encoding=3, text=tags['album'])
            if 'year' in tags and tags['year']:
                mp3_file['TDRC'] = TDRC(encoding=3, text=tags['year'])
            if 'track' in tags and tags['track']:
                mp3_file['TRCK'] = TRCK(encoding=3, text=tags['track'])
            if 'genre' in tags and tags['genre']:
                mp3_file['TCON'] = TCON(encoding=3, text=tags['genre'])
                
            # Advanced Tags setzen
            if 'release_year' in tags and tags['release_year']:
                mp3_file['TDRL'] = TDRL(encoding=3, text=tags['release_year'])
            if 'rating' in tags and tags['rating']:
                rating_value = int(float(tags['rating']) * 51) if str(tags['rating']).replace('.', '').isdigit() else 0
                mp3_file['POPM'] = POPM(email="user@example.com", rating=rating_value, count=1)
            if 'bpm' in tags and tags['bpm']:
                mp3_file['TBPM'] = TBPM(encoding=3, text=tags['bpm'])
            if 'energy' in tags and tags['energy']:
                mp3_file['TXXX:ENERGY'] = TXXX(encoding=3, desc='ENERGY', text=tags['energy'])
            if 'danceability' in tags and tags['danceability']:
                mp3_file['TXXX:DANCEABILITY'] = TXXX(encoding=3, desc='DANCEABILITY', text=tags['danceability'])
            if 'mood' in tags and tags['mood']:
                mp3_file['TXXX:MOOD'] = TXXX(encoding=3, desc='MOOD', text=tags['mood'])
            if 'similar_artist' in tags and tags['similar_artist']:
                mp3_file['TXXX:SIMILAR_ARTIST'] = TXXX(encoding=3, desc='SIMILAR_ARTIST', text=tags['similar_artist'])
            if 'comment' in tags and tags['comment']:
                mp3_file['COMM::eng'] = COMM(encoding=3, lang='eng', desc='', text=tags['comment'])
            if 'url' in tags and tags['url']:
                mp3_file['TXXX:URL'] = TXXX(encoding=3, desc='URL', text=tags['url'])
            if 'era' in tags and tags['era']:
                mp3_file['TXXX:ERA'] = TXXX(encoding=3, desc='ERA', text=tags['era'])
            if 'style' in tags and tags['style']:
                mp3_file['TXXX:STYLE'] = TXXX(encoding=3, desc='STYLE', text=tags['style'])
            if 'energy_level' in tags and tags['energy_level']:
                mp3_file['TXXX:ENERGY_LEVEL'] = TXXX(encoding=3, desc='ENERGY_LEVEL', text=tags['energy_level'])
            if 'lyrics' in tags and tags['lyrics']:
                mp3_file['USLT::eng'] = USLT(encoding=3, lang='eng', desc='', text=tags['lyrics'])
            
            # Datei speichern
            mp3_file.save()
            return True
            
        except Exception as e:
            print(f"Fehler beim Schreiben der ID3-Tags für {file_path}: {e}")
            return False
        
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
