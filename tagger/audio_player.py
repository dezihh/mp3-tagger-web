"""
Audio Player für MP3-Vorhören
Ermöglicht das Abspielen von MP3-Dateien direkt aus der Anwendung
"""

import pygame
import threading
import time
import os
from typing import Optional, Callable


class AudioPlayer:
    """Audio-Player für MP3-Vorhören mit pygame"""
    
    def __init__(self):
        self.current_file: Optional[str] = None
        self.is_playing: bool = False
        self.is_paused: bool = False
        self.position: float = 0.0
        self.duration: float = 0.0
        self.volume: float = 0.7
        self.position_callback: Optional[Callable] = None
        self._position_thread: Optional[threading.Thread] = None
        self._stop_position_thread: bool = False
        
        # Pygame mixer initialisieren
        try:
            pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=1024)
            pygame.mixer.init()
            self.available = True
            print("🎵 Audio-Player initialisiert")
        except Exception as e:
            print(f"🚨 Audio-Player Fehler: {e}")
            self.available = False
    
    def load_file(self, file_path: str) -> bool:
        """Lädt eine MP3-Datei zum Abspielen"""
        try:
            if not os.path.exists(file_path):
                print(f"🚨 Datei nicht gefunden: {file_path}")
                return False
            
            # Stoppe aktuell laufende Wiedergabe
            self.stop()
            
            # Lade neue Datei
            pygame.mixer.music.load(file_path)
            self.current_file = file_path
            self.position = 0.0
            
            # Versuche Dauer zu ermitteln (pygame hat keine direkte Methode dafür)
            # Verwende mutagen als Fallback
            try:
                from mutagen.mp3 import MP3
                audio = MP3(file_path)
                self.duration = audio.info.length
            except:
                self.duration = 0.0
            
            print(f"🎵 Datei geladen: {os.path.basename(file_path)} ({self.duration:.1f}s)")
            return True
            
        except Exception as e:
            print(f"🚨 Fehler beim Laden: {e}")
            return False
    
    def play(self) -> bool:
        """Startet die Wiedergabe"""
        try:
            if not self.current_file:
                return False
            
            if self.is_paused:
                pygame.mixer.music.unpause()
                self.is_paused = False
            else:
                pygame.mixer.music.play(start=self.position)
            
            self.is_playing = True
            self._start_position_tracking()
            print(f"▶️ Wiedergabe gestartet")
            return True
            
        except Exception as e:
            print(f"🚨 Wiedergabe-Fehler: {e}")
            return False
    
    def pause(self):
        """Pausiert die Wiedergabe"""
        try:
            if self.is_playing and not self.is_paused:
                pygame.mixer.music.pause()
                self.is_paused = True
                self._stop_position_tracking()
                print("⏸️ Wiedergabe pausiert")
        except Exception as e:
            print(f"🚨 Pause-Fehler: {e}")
    
    def stop(self):
        """Stoppt die Wiedergabe"""
        try:
            pygame.mixer.music.stop()
            self.is_playing = False
            self.is_paused = False
            self.position = 0.0
            self._stop_position_tracking()
            print("⏹️ Wiedergabe gestoppt")
        except Exception as e:
            print(f"🚨 Stop-Fehler: {e}")
    
    def set_volume(self, volume: float):
        """Setzt die Lautstärke (0.0 - 1.0)"""
        try:
            self.volume = max(0.0, min(1.0, volume))
            pygame.mixer.music.set_volume(self.volume)
            print(f"🔊 Lautstärke: {int(self.volume * 100)}%")
        except Exception as e:
            print(f"🚨 Lautstärke-Fehler: {e}")
    
    def seek(self, position: float):
        """Springt zu einer bestimmten Position (in Sekunden)"""
        try:
            if self.current_file and 0 <= position <= self.duration:
                was_playing = self.is_playing
                self.stop()
                self.position = position
                
                if was_playing:
                    # pygame hat kein direktes Seek - Neustart an Position
                    # Dies ist eine Limitierung von pygame
                    self.play()
                    
                print(f"⏭️ Position: {position:.1f}s")
        except Exception as e:
            print(f"🚨 Seek-Fehler: {e}")
    
    def get_position(self) -> float:
        """Gibt aktuelle Position zurück"""
        return self.position
    
    def get_duration(self) -> float:
        """Gibt Gesamtdauer zurück"""
        return self.duration
    
    def is_active(self) -> bool:
        """Prüft ob gerade abgespielt wird"""
        try:
            return pygame.mixer.music.get_busy() and self.is_playing
        except:
            return False
    
    def set_position_callback(self, callback: Callable):
        """Setzt Callback für Position Updates"""
        self.position_callback = callback
    
    def _start_position_tracking(self):
        """Startet Position-Tracking Thread"""
        self._stop_position_thread = False
        if self._position_thread is None or not self._position_thread.is_alive():
            self._position_thread = threading.Thread(target=self._position_tracker, daemon=True)
            self._position_thread.start()
    
    def _stop_position_tracking(self):
        """Stoppt Position-Tracking Thread"""
        self._stop_position_thread = True
    
    def _position_tracker(self):
        """Position-Tracking Thread"""
        start_time = time.time()
        
        while not self._stop_position_thread and self.is_playing:
            if not self.is_paused and pygame.mixer.music.get_busy():
                elapsed = time.time() - start_time
                self.position = min(self.position + elapsed, self.duration)
                
                # Callback aufrufen wenn verfügbar
                if self.position_callback:
                    try:
                        self.position_callback(self.position, self.duration)
                    except:
                        pass
                
                start_time = time.time()
            
            time.sleep(0.1)
        
        # Wenn Track zu Ende
        if self.position >= self.duration:
            self.is_playing = False
            self.position = 0.0
            if self.position_callback:
                try:
                    self.position_callback(0.0, self.duration)
                except:
                    pass
    
    def cleanup(self):
        """Räumt Ressourcen auf"""
        try:
            self.stop()
            self._stop_position_tracking()
            if self._position_thread and self._position_thread.is_alive():
                self._position_thread.join(timeout=1.0)
            pygame.mixer.quit()
            print("🎵 Audio-Player bereinigt")
        except Exception as e:
            print(f"🚨 Cleanup-Fehler: {e}")


# Globale Player-Instanz
_player_instance: Optional[AudioPlayer] = None

def get_audio_player() -> AudioPlayer:
    """Gibt globale Audio-Player Instanz zurück"""
    global _player_instance
    if _player_instance is None:
        _player_instance = AudioPlayer()
    return _player_instance

def cleanup_audio_player():
    """Räumt globale Player-Instanz auf"""
    global _player_instance
    if _player_instance:
        _player_instance.cleanup()
        _player_instance = None
