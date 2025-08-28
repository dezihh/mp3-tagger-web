"""
Audio Player GUI für MP3-Vorhören
Grafische Benutzeroberfläche für den Audio-Player
"""

import tkinter as tk
from tkinter import ttk
import os
from typing import Optional
from .audio_player import get_audio_player


class AudioPlayerWidget:
    """GUI-Widget für Audio-Wiedergabe"""
    
    def __init__(self, parent_frame: tk.Widget):
        self.parent = parent_frame
        self.player = get_audio_player()
        self.current_file: Optional[str] = None
        self.is_updating_position = False
        
        self.create_widgets()
        self.setup_position_callback()
    
    def create_widgets(self):
        """Erstellt die GUI-Elemente"""
        # Haupt-Frame für Player
        self.player_frame = ttk.LabelFrame(self.parent, text="🎵 Audio Vorhören", padding=10)
        self.player_frame.grid(row=2, column=0, sticky='ew', padx=5, pady=5)
        self.player_frame.columnconfigure(2, weight=1)  # Position Frame soll expandieren
        
        # Datei-Info-Label
        self.file_label = ttk.Label(self.player_frame, text="Keine Datei geladen", 
                                   foreground='gray', font=('Arial', 9))
        self.file_label.grid(row=0, column=0, columnspan=4, sticky='ew', pady=(0, 5))
        
        # Play/Pause Button
        self.play_button = ttk.Button(self.player_frame, text="▶️", width=4,
                                     command=self.toggle_play, state='disabled')
        self.play_button.grid(row=1, column=0, padx=(0, 5))
        
        # Stop Button
        self.stop_button = ttk.Button(self.player_frame, text="⏹️", width=4,
                                     command=self.stop_playback, state='disabled')
        self.stop_button.grid(row=1, column=1, padx=(0, 10))
        
        # Position/Fortschritt Frame
        position_frame = ttk.Frame(self.player_frame)
        position_frame.grid(row=1, column=2, sticky='ew', padx=(10, 10))
        position_frame.columnconfigure(0, weight=1)
        
        # Zeit-Labels Frame
        time_frame = ttk.Frame(position_frame)
        time_frame.grid(row=0, column=0, sticky='ew')
        time_frame.columnconfigure(1, weight=1)
        
        self.current_time_label = ttk.Label(time_frame, text="0:00", font=('Arial', 8))
        self.current_time_label.grid(row=0, column=0, sticky='w')
        
        self.duration_label = ttk.Label(time_frame, text="/ 0:00", font=('Arial', 8))
        self.duration_label.grid(row=0, column=2, sticky='e')
        
        # Fortschrittsbalken
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Scale(position_frame, from_=0, to=100, 
                                     orient='horizontal', variable=self.progress_var,
                                     command=self.on_position_change)
        self.progress_bar.grid(row=1, column=0, sticky='ew', pady=(2, 0))
        
        # Lautstärke-Frame
        volume_frame = ttk.Frame(self.player_frame)
        volume_frame.grid(row=1, column=3, padx=(10, 0))
        
        ttk.Label(volume_frame, text="🔊", font=('Arial', 10)).grid(row=0, column=0)
        
        self.volume_var = tk.DoubleVar(value=70)
        self.volume_scale = ttk.Scale(volume_frame, from_=0, to=100, 
                                     orient='horizontal', length=80,
                                     variable=self.volume_var,
                                     command=self.on_volume_change)
        self.volume_scale.grid(row=0, column=1, padx=(5, 0))
        
        # Initialisiere Lautstärke
        self.player.set_volume(0.7)
    
    def load_file(self, file_path: str):
        """Lädt eine neue Audio-Datei"""
        if not os.path.exists(file_path):
            self.file_label.config(text="Datei nicht gefunden", foreground='red')
            return False
        
        if self.player.load_file(file_path):
            self.current_file = file_path
            filename = os.path.basename(file_path)
            self.file_label.config(text=f"🎵 {filename}", foreground='black')
            
            # Buttons aktivieren
            self.play_button.config(state='normal')
            self.stop_button.config(state='normal')
            
            # Dauer aktualisieren
            duration = self.player.get_duration()
            self.duration_label.config(text=f"/ {self.format_time(duration)}")
            
            # Fortschritt zurücksetzen
            self.progress_var.set(0)
            self.current_time_label.config(text="0:00")
            
            print(f"🎵 Audio-Widget: Datei geladen - {filename}")
            return True
        else:
            self.file_label.config(text="Ladefehler", foreground='red')
            return False
    
    def toggle_play(self):
        """Play/Pause umschalten"""
        if not self.current_file:
            return
        
        if self.player.is_playing:
            if self.player.is_paused:
                # Fortsetzen
                self.player.play()
                self.play_button.config(text="⏸️")
            else:
                # Pausieren
                self.player.pause()
                self.play_button.config(text="▶️")
        else:
            # Starten
            if self.player.play():
                self.play_button.config(text="⏸️")
    
    def stop_playback(self):
        """Stoppt die Wiedergabe"""
        self.player.stop()
        self.play_button.config(text="▶️")
        self.progress_var.set(0)
        self.current_time_label.config(text="0:00")
    
    def on_position_change(self, value):
        """Position manuell geändert"""
        if self.is_updating_position or not self.current_file:
            return
        
        try:
            # Prozent zu Sekunden umrechnen
            duration = self.player.get_duration()
            if duration > 0:
                position = float(value) * duration / 100.0
                self.player.seek(position)
                self.current_time_label.config(text=self.format_time(position))
        except Exception as e:
            print(f"🚨 Position-Fehler: {e}")
    
    def on_volume_change(self, value):
        """Lautstärke geändert"""
        try:
            volume = float(value) / 100.0
            self.player.set_volume(volume)
        except Exception as e:
            print(f"🚨 Lautstärke-Fehler: {e}")
    
    def update_position(self, position: float, duration: float):
        """Callback für Position Updates vom Player"""
        try:
            self.is_updating_position = True
            
            # Fortschritt aktualisieren
            if duration > 0:
                progress = (position / duration) * 100.0
                self.progress_var.set(progress)
            
            # Zeit-Label aktualisieren
            self.current_time_label.config(text=self.format_time(position))
            
            # Button-Status aktualisieren
            if not self.player.is_active():
                self.play_button.config(text="▶️")
            
        except Exception as e:
            print(f"🚨 Position-Update-Fehler: {e}")
        finally:
            self.is_updating_position = False
    
    def setup_position_callback(self):
        """Richtet Position-Callback ein"""
        self.player.set_position_callback(self.update_position)
    
    def format_time(self, seconds: float) -> str:
        """Formatiert Sekunden zu MM:SS"""
        try:
            minutes = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{minutes}:{secs:02d}"
        except:
            return "0:00"
    
    def clear(self):
        """Räumt Player auf"""
        self.stop_playback()
        self.current_file = None
        self.file_label.config(text="Keine Datei geladen", foreground='gray')
        self.play_button.config(state='disabled')
        self.stop_button.config(state='disabled')
        self.duration_label.config(text="/ 0:00")
    
    def destroy(self):
        """Bereinigt Widget"""
        self.clear()
        self.player_frame.destroy()
