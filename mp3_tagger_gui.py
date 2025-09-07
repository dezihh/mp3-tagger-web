#!/usr/bin/env python3
"""
MP3 Tagger GUI - Desktop Application (Vereinfachte Version)
Alle Funktionen in einem einzigen Tab integriert, wie in der Web-Version
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import threading
from pathlib import Path
import json
from PIL import Image, ImageTk  # Für Cover-Vorschauen
import io

# Import der bestehenden Tagger-Module
from tagger.desktop_mp3_processor import DesktopMP3Processor
from tagger.cover_manager import CoverManager
from tagger.audio_recognition import AudioRecognitionService
from tagger.album_recognition import create_album_recognition_service
from tagger.extended_metadata import ExtendedMetadataService
from tagger.desktop_config import desktop_config
from tagger.metadata_editor import MetadataEditorDialog, BatchMetadataEditorDialog
from tagger.audio_player_widget import AudioPlayerWidget


class MP3TaggerGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("MP3 Tagger - Desktop Application")
        self.root.geometry("1400x800")
        
        # Hauptvariablen
        self.current_directory = tk.StringVar()
        self.mp3_files = []
        self.selected_files = []
        
        # Module initialisieren
        self.mp3_processor = DesktopMP3Processor()
        self.cover_manager = None  # Wird erst bei Verzeichnis-Auswahl initialisiert
        self.audio_recognition = None  # Wird bei Bedarf mit API-Key initialisiert
        self.album_recognition = None  # Wird bei Bedarf mit API-Keys initialisiert
        self.extended_metadata = None  # Wird bei Bedarf mit API-Keys initialisiert
        self.audio_player_widget = None  # Audio-Player Widget
        
        self.setup_ui()
        self.setup_styles()
        self.setup_keyboard_shortcuts()
        
    def setup_keyboard_shortcuts(self):
        """Konfiguriert Keyboard-Shortcuts"""
        # Ctrl+A für "Alle auswählen"
        self.root.bind('<Control-a>', lambda e: self.select_all_files())
        # Ctrl+D für "Alle abwählen"  
        self.root.bind('<Control-d>', lambda e: self.deselect_all_files())
        # Ctrl+S für "Speichern"
        self.root.bind('<Control-s>', lambda e: self.save_selected_files())
        # F5 für "Verzeichnis neu scannen"
        self.root.bind('<F5>', lambda e: self.scan_directory())
        # Ctrl+O für "Verzeichnis öffnen"
        self.root.bind('<Control-o>', lambda e: self.browse_directory())
        # Leertaste für "Vorhören"
        self.root.bind('<space>', lambda e: self.play_selected_file())
        # Enter für "Play/Pause"
        self.root.bind('<Return>', lambda e: self.toggle_audio_playback())
        
    def setup_styles(self):
        """Konfiguriert das Aussehen der Anwendung"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Definiere Farben
        style.configure('Title.TLabel', font=('Arial', 16, 'bold'))
        style.configure('Header.TLabel', font=('Arial', 12, 'bold'))
        
    def setup_ui(self):
        """Erstellt die Benutzeroberfläche"""
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        # Haupt-Container
        main_container = ttk.Frame(self.root, padding="10")
        main_container.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        main_container.columnconfigure(0, weight=1)
        main_container.rowconfigure(3, weight=1)  # Angepasst für Audio-Player
        
        # Header
        self.create_header(main_container)
        
        # Verzeichnis-Auswahl
        self.create_directory_selector(main_container)
        
        # Audio-Player
        self.create_audio_player(main_container)
        
        # Haupt-Inhalt
        self.create_main_content(main_container)
        
        # Status Bar
        self.create_status_bar(main_container, row=4)  # Angepasst für Audio-Player
        
    def create_header(self, parent):
        """Erstellt den Header"""
        header_frame = ttk.Frame(parent)
        header_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(header_frame, text="MP3 Tagger", style='Title.TLabel').pack(side=tk.LEFT)
        
    def create_directory_selector(self, parent):
        """Erstellt die Verzeichnis-Auswahl"""
        dir_frame = ttk.LabelFrame(parent, text="Verzeichnis", padding="10")
        dir_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        dir_frame.columnconfigure(1, weight=1)
        
        ttk.Button(dir_frame, text="Durchsuchen", command=self.browse_directory).grid(row=0, column=0, padx=(0, 10))
        ttk.Entry(dir_frame, textvariable=self.current_directory, state='readonly').grid(row=0, column=1, sticky=(tk.W, tk.E))
        ttk.Button(dir_frame, text="Verzeichnis scannen", command=self.scan_directory).grid(row=0, column=2, padx=(10, 0))
        
    def create_audio_player(self, parent):
        """Erstellt das Audio-Player Widget"""
        self.audio_player_widget = AudioPlayerWidget(parent)
        
    def create_main_content(self, parent):
        """Erstellt den Hauptinhalt mit verschiebarer Trennlinie zwischen Tabelle und Metadaten"""
        content_frame = ttk.Frame(parent)
        content_frame.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        content_frame.columnconfigure(0, weight=1)
        content_frame.rowconfigure(0, weight=1)
        
        # PanedWindow für verschiebbare Trennlinie
        self.main_paned = ttk.PanedWindow(content_frame, orient=tk.HORIZONTAL)
        self.main_paned.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Linker Bereich: Funktionen und Tabelle
        left_frame = ttk.Frame(self.main_paned)
        left_frame.columnconfigure(0, weight=1)
        left_frame.rowconfigure(2, weight=1)
        
        # Funktions-Toolbar
        self.create_function_toolbar(left_frame)
        
        # Dateien-Toolbar
        self.create_files_toolbar(left_frame)
        
        # Haupttabelle
        self.create_files_table(left_frame)
        
        # Rechter Bereich: Metadaten-Panel mit Scrollbar
        metadata_container = ttk.Frame(self.main_paned)
        metadata_container.rowconfigure(0, weight=1)
        metadata_container.columnconfigure(0, weight=1)
        
        # Canvas für Scrolling
        self.metadata_canvas = tk.Canvas(metadata_container, highlightthickness=0)
        self.metadata_scrollbar = ttk.Scrollbar(metadata_container, orient="vertical", command=self.metadata_canvas.yview)
        self.metadata_scrollable_frame = ttk.Frame(self.metadata_canvas)
        
        # Scrollable Frame konfigurieren
        self.metadata_scrollable_frame.bind(
            "<Configure>",
            lambda e: self.metadata_canvas.configure(scrollregion=self.metadata_canvas.bbox("all"))
        )
        
        # Canvas konfigurieren
        self.metadata_canvas.create_window((0, 0), window=self.metadata_scrollable_frame, anchor="nw")
        self.metadata_canvas.configure(yscrollcommand=self.metadata_scrollbar.set)
        
        # Layout
        self.metadata_canvas.grid(row=0, column=0, sticky=(tk.N, tk.S, tk.E, tk.W))
        self.metadata_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Mausrad-Support für Scrolling
        def _on_mousewheel(event):
            self.metadata_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        self.metadata_canvas.bind("<MouseWheel>", _on_mousewheel)
        
        # Metadaten-Panel erstellen (jetzt im scrollbaren Frame)
        self.create_metadata_panel(self.metadata_scrollable_frame)
        
        # Panels zu PanedWindow hinzufügen
        self.main_paned.add(left_frame, weight=3)  # Tabelle bekommt mehr Platz
        self.main_paned.add(metadata_container, weight=1)  # Metadaten-Panel bekommt weniger Platz

    def create_function_toolbar(self, parent):
        """Erstellt die Funktions-Toolbar mit allen Hauptfunktionen"""
        function_frame = ttk.LabelFrame(parent, text="Funktionen für ausgewählte Dateien", padding="10")
        function_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Audio Recognition Bereich
        audio_frame = ttk.Frame(function_frame)
        audio_frame.pack(side=tk.LEFT, padx=(0, 20))
        
        ttk.Label(audio_frame, text="Audio Erkennung:", font=('Arial', 9, 'bold')).pack(anchor=tk.W)
        audio_buttons = ttk.Frame(audio_frame)
        audio_buttons.pack(fill=tk.X, pady=(2, 0))
        
        ttk.Button(audio_buttons, text="Shazam", command=self.recognize_with_shazam, width=10).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(audio_buttons, text="AcoustID", command=self.recognize_with_acoustid, width=10).pack(side=tk.LEFT)
        
        # Cover Management Bereich
        cover_frame = ttk.Frame(function_frame)
        cover_frame.pack(side=tk.LEFT, padx=(0, 20))
        
        ttk.Label(cover_frame, text="Cover Management:", font=('Arial', 9, 'bold')).pack(anchor=tk.W)
        cover_buttons = ttk.Frame(cover_frame)
        cover_buttons.pack(fill=tk.X, pady=(2, 0))
        
        ttk.Button(cover_buttons, text="Cover anzeigen", command=self.show_covers, width=12).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(cover_buttons, text="Cover laden", command=self.load_covers, width=12).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(cover_buttons, text="Cover entfernen", command=self.remove_covers, width=12).pack(side=tk.LEFT)
        
        # Album Recognition Bereich
        album_frame = ttk.Frame(function_frame)
        album_frame.pack(side=tk.LEFT, padx=(0, 20))
        
        ttk.Label(album_frame, text="Album-Erkennung:", font=('Arial', 9, 'bold')).pack(anchor=tk.W)
        album_buttons = ttk.Frame(album_frame)
        album_buttons.pack(fill=tk.X, pady=(2, 0))
        
        ttk.Button(album_buttons, text="Album erkennen", command=self.recognize_album, width=12).pack(side=tk.LEFT)
        
        # Metadata Enrichment Bereich
        metadata_frame = ttk.Frame(function_frame)
        metadata_frame.pack(side=tk.LEFT, padx=(0, 20))
        
        ttk.Label(metadata_frame, text="Metadaten-Anreicherung:", font=('Arial', 9, 'bold')).pack(anchor=tk.W)
        metadata_buttons = ttk.Frame(metadata_frame)
        metadata_buttons.pack(fill=tk.X, pady=(2, 0))
        
        ttk.Button(metadata_buttons, text="Last.fm", command=self.enrich_with_lastfm, width=10).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(metadata_buttons, text="MusicBrainz", command=self.enrich_with_musicbrainz, width=12).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(metadata_buttons, text="Discogs", command=self.enrich_with_discogs, width=10).pack(side=tk.LEFT)
        
        # Batch-Aktionen Bereich
        batch_frame = ttk.Frame(function_frame)
        batch_frame.pack(side=tk.LEFT)
        
        ttk.Label(batch_frame, text="Batch-Aktionen:", font=('Arial', 9, 'bold')).pack(anchor=tk.W)
        batch_buttons = ttk.Frame(batch_frame)
        batch_buttons.pack(fill=tk.X, pady=(2, 0))
        
        ttk.Button(batch_buttons, text="Bearbeiten", command=self.edit_selected_metadata, width=10).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(batch_buttons, text="Speichern", command=self.save_selected_files, width=10).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(batch_buttons, text="Track-Nr.", command=self.auto_number_tracks, width=10).pack(side=tk.LEFT)

    def create_files_toolbar(self, parent):
        """Erstellt die Dateien-Toolbar mit Auswahl-Buttons"""
        toolbar = ttk.Frame(parent)
        toolbar.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Button(toolbar, text="Alles markieren", command=self.select_all_files).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar, text="Verzeichnis markieren", command=self.select_current_directory).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar, text="Auswahl aufheben", command=self.deselect_all_files).pack(side=tk.LEFT, padx=(0, 5))
        
        # Status-Info
        self.selection_status = tk.StringVar()
        self.selection_status.set("Keine Dateien ausgewählt")
        ttk.Label(toolbar, textvariable=self.selection_status).pack(side=tk.RIGHT)

    def create_files_table(self, parent):
        """Erstellt die Haupttabelle für MP3-Dateien"""
        table_frame = ttk.Frame(parent)
        table_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)
        
        # Treeview für Dateien (ohne filename-Spalte)
        columns = ('title', 'artist', 'album', 'year', 'track', 'genre')
        self.files_tree = ttk.Treeview(table_frame, columns=columns, show='tree headings', height=20)
        
        # Spalten konfigurieren
        self.files_tree.heading('#0', text='Verzeichnis/Datei')  # Tree-Spalte für Verzeichnisse
        self.files_tree.heading('title', text='Titel')
        self.files_tree.heading('artist', text='Künstler')
        self.files_tree.heading('album', text='Album')
        self.files_tree.heading('year', text='Jahr')
        self.files_tree.heading('track', text='Track')
        self.files_tree.heading('genre', text='Genre')
        
        # Spaltenbreiten (ohne filename-Spalte)
        self.files_tree.column('#0', width=250, minwidth=200)  # Tree-Spalte für Verzeichnis/Datei
        self.files_tree.column('title', width=200, minwidth=150)  # Mehr Platz
        self.files_tree.column('artist', width=150, minwidth=120)  # Mehr Platz
        self.files_tree.column('album', width=150, minwidth=120)  # Mehr Platz
        self.files_tree.column('year', width=60, minwidth=50)
        self.files_tree.column('track', width=50, minwidth=40)
        self.files_tree.column('genre', width=120, minwidth=80)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.files_tree.yview)
        h_scrollbar = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=self.files_tree.xview)
        self.files_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Grid Layout
        self.files_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        v_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        h_scrollbar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        # Events - Zeilen-basierte Markierung statt Checkbox
        self.files_tree.bind('<Button-1>', self.toggle_row_selection)
        self.files_tree.bind('<Double-1>', self.edit_file_metadata)
        self.files_tree.bind('<Button-3>', self.show_context_menu)  # Rechtsklick für Kontextmenü
        self.files_tree.bind('<<TreeviewSelect>>', self.on_file_selection)  # Auswahl für Metadaten-Panel
        
        # Kontextmenü erstellen
        self.create_context_menu()
        
        # Tracking für markierte Zeilen
        self.selected_items = set()  # Set der markierten Item-IDs
        
        # Zuordnung von Tree-Item-IDs zu Dateipfaden
        self.item_to_path = {}  # Mapping für Pfad-Ermittlung
        
        # System für vorgemerkte Änderungen
        self.pending_changes = {}  # Dict: {file_path: {field: new_value}}
        self.current_file_path = None  # Aktuell angezeigte Datei
        self.changed_entry_fields = set()  # Set der geänderten Felder für Styling

    def create_metadata_panel(self, parent):
        """Erstellt das permanente Metadaten-Panel rechts"""
        # Haupt-Frame für Metadaten-Panel
        metadata_frame = ttk.LabelFrame(parent, text="📋 Metadaten", padding=10)
        metadata_frame.pack(fill='both', expand=True)
        metadata_frame.columnconfigure(1, weight=1)
        
        # Datei-Info Bereich (mit Rahmen)
        file_info_frame = ttk.LabelFrame(metadata_frame, text="📁 Datei-Information", padding=8)
        file_info_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 5))
        file_info_frame.columnconfigure(1, weight=1)
        file_info_frame.columnconfigure(3, weight=1)
        file_info_frame.columnconfigure(5, weight=1)
        
        # Dateiname (ganze Breite)
        ttk.Label(file_info_frame, text="📁", font=('Arial', 10)).grid(row=0, column=0, sticky=tk.W, pady=2)
        self.metadata_filename = tk.StringVar(value="Keine Datei ausgewählt")
        filename_label = ttk.Label(file_info_frame, textvariable=self.metadata_filename, 
                                  foreground='gray', font=('Arial', 9, 'bold'))
        filename_label.grid(row=0, column=1, columnspan=5, sticky=(tk.W, tk.E), pady=2, padx=(5, 0))
        
        # Größe, Dauer und Bitrate nebeneinander
        ttk.Label(file_info_frame, text="💾", font=('Arial', 9)).grid(row=1, column=0, sticky=tk.W, pady=2)
        self.metadata_filesize = tk.StringVar(value="-")
        ttk.Label(file_info_frame, textvariable=self.metadata_filesize, font=('Arial', 8)).grid(row=1, column=1, sticky=tk.W, pady=2, padx=(5, 10))
        
        ttk.Label(file_info_frame, text="⏱️", font=('Arial', 9)).grid(row=1, column=2, sticky=tk.W, pady=2)
        self.metadata_duration = tk.StringVar(value="-")
        ttk.Label(file_info_frame, textvariable=self.metadata_duration, font=('Arial', 8)).grid(row=1, column=3, sticky=tk.W, pady=2, padx=(5, 10))
        
        ttk.Label(file_info_frame, text="🎵", font=('Arial', 9)).grid(row=1, column=4, sticky=tk.W, pady=2)
        self.metadata_bitrate = tk.StringVar(value="-")
        ttk.Label(file_info_frame, textvariable=self.metadata_bitrate, font=('Arial', 8)).grid(row=1, column=5, sticky=tk.W, pady=2, padx=(5, 0))
        
        # Metadaten Bereich (editierbar)
        meta_frame = ttk.LabelFrame(metadata_frame, text="🏷️ ID3 Tags (editierbar)", padding=8)
        meta_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 5))
        meta_frame.columnconfigure(1, weight=1)
        
        # Track (jetzt zuerst)
        ttk.Label(meta_frame, text="Track:", font=('Arial', 9, 'bold')).grid(row=0, column=0, sticky=tk.W, pady=3)
        self.metadata_track = tk.StringVar(value="-")
        self.track_entry = ttk.Entry(meta_frame, textvariable=self.metadata_track, font=('Arial', 9), width=8)
        self.track_entry.grid(row=0, column=1, sticky=tk.W, pady=3, padx=(10, 0))
        self.track_entry.bind('<KeyRelease>', lambda e: self.on_metadata_change('track'))
        
        # Titel (jetzt nach Track)
        ttk.Label(meta_frame, text="Titel:", font=('Arial', 9, 'bold')).grid(row=1, column=0, sticky=tk.W, pady=3)
        self.metadata_title = tk.StringVar(value="-")
        self.title_entry = ttk.Entry(meta_frame, textvariable=self.metadata_title, font=('Arial', 9))
        self.title_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=3, padx=(10, 0))
        self.title_entry.bind('<KeyRelease>', lambda e: self.on_metadata_change('title'))
        
        # Künstler
        ttk.Label(meta_frame, text="Künstler:", font=('Arial', 9, 'bold')).grid(row=2, column=0, sticky=tk.W, pady=3)
        self.metadata_artist = tk.StringVar(value="-")
        self.artist_entry = ttk.Entry(meta_frame, textvariable=self.metadata_artist, font=('Arial', 9))
        self.artist_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=3, padx=(10, 0))
        self.artist_entry.bind('<KeyRelease>', lambda e: self.on_metadata_change('artist'))
        
        # Album
        ttk.Label(meta_frame, text="Album:", font=('Arial', 9, 'bold')).grid(row=3, column=0, sticky=tk.W, pady=3)
        self.metadata_album = tk.StringVar(value="-")
        self.album_entry = ttk.Entry(meta_frame, textvariable=self.metadata_album, font=('Arial', 9))
        self.album_entry.grid(row=3, column=1, sticky=(tk.W, tk.E), pady=3, padx=(10, 0))
        self.album_entry.bind('<KeyRelease>', lambda e: self.on_metadata_change('album'))
        
        # Jahr
        ttk.Label(meta_frame, text="Jahr:", font=('Arial', 9, 'bold')).grid(row=4, column=0, sticky=tk.W, pady=3)
        self.metadata_year = tk.StringVar(value="-")
        self.year_entry = ttk.Entry(meta_frame, textvariable=self.metadata_year, font=('Arial', 9), width=8)
        self.year_entry.grid(row=4, column=1, sticky=tk.W, pady=3, padx=(10, 0))
        self.year_entry.bind('<KeyRelease>', lambda e: self.on_metadata_change('year'))
        
        # Genre
        ttk.Label(meta_frame, text="Genre:", font=('Arial', 9, 'bold')).grid(row=5, column=0, sticky=tk.W, pady=3)
        self.metadata_genre = tk.StringVar(value="-")
        self.genre_entry = ttk.Entry(meta_frame, textvariable=self.metadata_genre, font=('Arial', 9))
        self.genre_entry.grid(row=5, column=1, sticky=(tk.W, tk.E), pady=3, padx=(10, 0))
        self.genre_entry.bind('<KeyRelease>', lambda e: self.on_metadata_change('genre'))
        
        # Advanced Tags Bereich
        advanced_frame = ttk.LabelFrame(metadata_frame, text="🔧 Advanced Tags", padding=8)
        advanced_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 5))
        advanced_frame.columnconfigure(1, weight=1)
        advanced_frame.columnconfigure(3, weight=1)  # Zusätzliche Spalte konfigurieren
        
        # Row 0: Erscheinungsjahr (TDRL) & Rating
        ttk.Label(advanced_frame, text="Erscheinungsjahr:", font=('Arial', 8, 'bold')).grid(row=0, column=0, sticky=tk.W, pady=2)
        self.metadata_release_year = tk.StringVar()
        self.release_year_entry = ttk.Entry(advanced_frame, textvariable=self.metadata_release_year, font=('Arial', 8), width=8)
        self.release_year_entry.grid(row=0, column=1, sticky=tk.W, pady=2, padx=(5, 8))
        self.release_year_entry.bind('<KeyRelease>', lambda e: self.on_advanced_metadata_change('release_year'))
        
        ttk.Label(advanced_frame, text="Rating:", font=('Arial', 8, 'bold')).grid(row=0, column=2, sticky=tk.W, pady=2)
        self.metadata_rating = tk.StringVar()
        rating_frame = ttk.Frame(advanced_frame)
        rating_frame.grid(row=0, column=3, sticky=tk.W, pady=2, padx=(5, 0))
        self.rating_entry = ttk.Entry(rating_frame, textvariable=self.metadata_rating, font=('Arial', 8), width=4)
        self.rating_entry.pack(side=tk.LEFT)
        ttk.Label(rating_frame, text="/5⭐", font=('Arial', 8)).pack(side=tk.LEFT, padx=(2, 0))
        self.rating_entry.bind('<KeyRelease>', lambda e: self.on_advanced_metadata_change('rating'))
        
        # Row 1: Tempo (BPM) & Energie
        ttk.Label(advanced_frame, text="Tempo (BPM):", font=('Arial', 8, 'bold')).grid(row=1, column=0, sticky=tk.W, pady=2)
        self.metadata_bpm = tk.StringVar()
        self.bpm_entry = ttk.Entry(advanced_frame, textvariable=self.metadata_bpm, font=('Arial', 8), width=8)
        self.bpm_entry.grid(row=1, column=1, sticky=tk.W, pady=2, padx=(5, 8))
        self.bpm_entry.bind('<KeyRelease>', lambda e: self.on_advanced_metadata_change('bpm'))
        
        ttk.Label(advanced_frame, text="Energie:", font=('Arial', 8, 'bold')).grid(row=1, column=2, sticky=tk.W, pady=2)
        self.metadata_energy = tk.StringVar()
        energy_frame = ttk.Frame(advanced_frame)
        energy_frame.grid(row=1, column=3, sticky=tk.W, pady=2, padx=(5, 0))
        self.energy_entry = ttk.Entry(energy_frame, textvariable=self.metadata_energy, font=('Arial', 8), width=4)
        self.energy_entry.pack(side=tk.LEFT)
        ttk.Label(energy_frame, text="/10⚡", font=('Arial', 8)).pack(side=tk.LEFT, padx=(2, 0))
        self.energy_entry.bind('<KeyRelease>', lambda e: self.on_advanced_metadata_change('energy'))
        
        # Row 2: Mood & Danceability (getauscht)
        ttk.Label(advanced_frame, text="Mood:", font=('Arial', 8, 'bold')).grid(row=2, column=0, sticky=tk.W, pady=2)
        self.metadata_mood = tk.StringVar()
        self.mood_entry = ttk.Entry(advanced_frame, textvariable=self.metadata_mood, font=('Arial', 8), width=15)
        self.mood_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=2, padx=(5, 8))
        self.mood_entry.bind('<KeyRelease>', lambda e: self.on_advanced_metadata_change('mood'))
        
        ttk.Label(advanced_frame, text="Danceability:", font=('Arial', 8, 'bold')).grid(row=2, column=2, sticky=tk.W, pady=2)
        self.metadata_danceability = tk.StringVar()
        dance_frame = ttk.Frame(advanced_frame)
        dance_frame.grid(row=2, column=3, sticky=tk.W, pady=2, padx=(5, 0))
        self.danceability_entry = ttk.Entry(dance_frame, textvariable=self.metadata_danceability, font=('Arial', 8), width=4)
        self.danceability_entry.pack(side=tk.LEFT)
        ttk.Label(dance_frame, text="/10💃", font=('Arial', 8)).pack(side=tk.LEFT, padx=(2, 0))
        self.danceability_entry.bind('<KeyRelease>', lambda e: self.on_advanced_metadata_change('danceability'))
        
        # Row 3: Era & Energy Level (getauscht) 
        ttk.Label(advanced_frame, text="Era:", font=('Arial', 8, 'bold')).grid(row=3, column=0, sticky=tk.W, pady=2)
        self.metadata_era = tk.StringVar()
        self.era_entry = ttk.Entry(advanced_frame, textvariable=self.metadata_era, font=('Arial', 8), width=15)
        self.era_entry.grid(row=3, column=1, sticky=(tk.W, tk.E), pady=2, padx=(5, 8))
        self.era_entry.bind('<KeyRelease>', lambda e: self.on_advanced_metadata_change('era'))
        
        ttk.Label(advanced_frame, text="Energy Level:", font=('Arial', 8, 'bold')).grid(row=3, column=2, sticky=tk.W, pady=2)
        self.metadata_energy_level = tk.StringVar()
        energy_level_frame = ttk.Frame(advanced_frame)
        energy_level_frame.grid(row=3, column=3, sticky=tk.W, pady=2, padx=(5, 0))
        self.energy_level_entry = ttk.Entry(energy_level_frame, textvariable=self.metadata_energy_level, font=('Arial', 8), width=4)
        self.energy_level_entry.pack(side=tk.LEFT)
        ttk.Label(energy_level_frame, text="/10⚡", font=('Arial', 8)).pack(side=tk.LEFT, padx=(2, 0))
        self.energy_level_entry.bind('<KeyRelease>', lambda e: self.on_advanced_metadata_change('energy_level'))
        
        # Row 4: URL (volle Breite)
        ttk.Label(advanced_frame, text="URL:", font=('Arial', 8, 'bold')).grid(row=4, column=0, sticky=tk.W, pady=2)
        self.metadata_url = tk.StringVar()
        self.url_entry = ttk.Entry(advanced_frame, textvariable=self.metadata_url, font=('Arial', 8))
        self.url_entry.grid(row=4, column=1, columnspan=3, sticky=(tk.W, tk.E), pady=2, padx=(5, 0))
        self.url_entry.bind('<KeyRelease>', lambda e: self.on_advanced_metadata_change('url'))
        
        # Row 5: Style (volle Breite)
        ttk.Label(advanced_frame, text="Style:", font=('Arial', 8, 'bold')).grid(row=5, column=0, sticky=tk.W, pady=2)
        self.metadata_style = tk.StringVar()
        self.style_entry = ttk.Entry(advanced_frame, textvariable=self.metadata_style, font=('Arial', 8))
        self.style_entry.grid(row=5, column=1, columnspan=3, sticky=(tk.W, tk.E), pady=2, padx=(5, 0))
        self.style_entry.bind('<KeyRelease>', lambda e: self.on_advanced_metadata_change('style'))
        
        # Row 6: Ähnlicher Künstler
        ttk.Label(advanced_frame, text="Ähnl. Künstler:", font=('Arial', 8, 'bold')).grid(row=6, column=0, sticky=tk.W, pady=2)
        self.metadata_similar_artist = tk.StringVar()
        self.similar_artist_entry = ttk.Entry(advanced_frame, textvariable=self.metadata_similar_artist, font=('Arial', 8))
        self.similar_artist_entry.grid(row=6, column=1, columnspan=3, sticky=(tk.W, tk.E), pady=2, padx=(5, 0))
        self.similar_artist_entry.bind('<KeyRelease>', lambda e: self.on_advanced_metadata_change('similar_artist'))
        
        # Row 7: Kommentar
        ttk.Label(advanced_frame, text="Kommentar:", font=('Arial', 8, 'bold')).grid(row=7, column=0, sticky=tk.W, pady=2)
        self.metadata_comment = tk.StringVar()
        self.comment_entry = ttk.Entry(advanced_frame, textvariable=self.metadata_comment, font=('Arial', 8))
        self.comment_entry.grid(row=7, column=1, columnspan=3, sticky=(tk.W, tk.E), pady=2, padx=(5, 0))
        self.comment_entry.bind('<KeyRelease>', lambda e: self.on_advanced_metadata_change('comment'))
        
        # Row 8: Songtext (mehrzeilig)
        ttk.Label(advanced_frame, text="Songtext:", font=('Arial', 8, 'bold')).grid(row=8, column=0, sticky=(tk.W, tk.N), pady=2)
        self.metadata_lyrics = tk.StringVar()
        # Verwende Text-Widget für mehrzeilige Lyrics
        lyrics_frame = ttk.Frame(advanced_frame)
        lyrics_frame.grid(row=8, column=1, columnspan=3, sticky=(tk.W, tk.E), pady=2, padx=(5, 0))
        lyrics_frame.columnconfigure(0, weight=1)
        
        self.lyrics_text = tk.Text(lyrics_frame, height=3, wrap=tk.WORD, font=('Arial', 8))
        lyrics_scrollbar = ttk.Scrollbar(lyrics_frame, orient=tk.VERTICAL, command=self.lyrics_text.yview)
        self.lyrics_text.configure(yscrollcommand=lyrics_scrollbar.set)
        self.lyrics_text.grid(row=0, column=0, sticky=(tk.W, tk.E))
        lyrics_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.lyrics_text.bind('<KeyRelease>', lambda e: self.on_lyrics_change())
        
        # Vorgemerkte Änderungen anzeigen
        self.changes_frame = ttk.LabelFrame(metadata_frame, text="📝 Vorgemerkte Änderungen", padding=8)
        self.changes_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 5))
        self.changes_frame.columnconfigure(0, weight=1)
        
        self.changes_text = tk.Text(self.changes_frame, height=3, wrap=tk.WORD, font=('Arial', 8))
        self.changes_text.pack(fill='both', expand=True)
        self.changes_text.config(state='disabled')  # Nur anzeigen, nicht editieren
        
        # Cover Bereich
        cover_frame = ttk.LabelFrame(metadata_frame, text="🖼️ Cover", padding=8)
        cover_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 5))
        cover_frame.columnconfigure(0, weight=1)
        
        # Vorgemerkte Änderungen anzeigen (vor Cover-Bereich)
        self.changes_frame = ttk.LabelFrame(metadata_frame, text="📝 Vorgemerkte Änderungen", padding=8)
        self.changes_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        self.changes_frame.columnconfigure(0, weight=1)
        
        self.changes_text = tk.Text(self.changes_frame, height=3, wrap=tk.WORD, font=('Arial', 8))
        self.changes_text.pack(fill='both', expand=True)
        self.changes_text.config(state='disabled')  # Nur anzeigen, nicht editieren
        
        # Cover Status
        self.metadata_cover_status = tk.StringVar(value="Kein Cover")
        ttk.Label(cover_frame, textvariable=self.metadata_cover_status, 
                 foreground='gray').grid(row=0, column=0, pady=5)
        
        # Cover Vorschau mit Bild-Label
        self.cover_preview_frame = ttk.Frame(cover_frame)
        self.cover_preview_frame.grid(row=1, column=0, pady=5)
        
        # Cover-Image-Label mit angemessener Größe für Vorschau
        self.metadata_cover_image = tk.Label(self.cover_preview_frame, 
                                           width=190, height=190,  # Etwas größer als Thumbnail
                                           bg='lightgray', 
                                           text='Kein Cover\nverfügbar', 
                                           compound='center',
                                           relief='sunken',
                                           borderwidth=2,
                                           font=('Arial', 10),
                                           anchor='center')
        self.metadata_cover_image.pack()
        
        # Aktionen Bereich
        actions_frame = ttk.LabelFrame(metadata_frame, text="⚡ Aktionen", padding=8)
        actions_frame.grid(row=6, column=0, columnspan=2, sticky=(tk.W, tk.E))
        actions_frame.columnconfigure(0, weight=1)
        
        # Buttons
        ttk.Button(actions_frame, text="🎵 Vorhören", 
                  command=self.play_selected_file).grid(row=0, column=0, sticky=(tk.W, tk.E), pady=2)
        ttk.Button(actions_frame, text="✏️ Bearbeiten", 
                  command=self.edit_file_metadata_from_context).grid(row=1, column=0, sticky=(tk.W, tk.E), pady=2)
        ttk.Button(actions_frame, text="🖼️ Cover wählen", 
                  command=self.select_cover_for_file).grid(row=2, column=0, sticky=(tk.W, tk.E), pady=2)

    def update_metadata_panel(self, file_path=None):
        """Aktualisiert das Metadaten-Panel mit Informationen zur ausgewählten Datei"""
        if not file_path or not os.path.exists(file_path):
            # Keine Datei ausgewählt - Panel zurücksetzen
            self.current_file_path = None
            self.clear_metadata_panel()
            return
        
        # Aktuellen Dateipfad setzen
        self.current_file_path = file_path
        
        try:
            # Datei-Information
            filename = os.path.basename(file_path)
            self.metadata_filename.set(filename)
            
            # Dateigröße
            file_size = os.path.getsize(file_path)
            size_mb = file_size / (1024 * 1024)
            self.metadata_filesize.set(f"{size_mb:.1f} MB")
            
            # Metadaten laden
            from mutagen.mp3 import MP3
            mp3_file = MP3(file_path)
            
            # Dauer und Bitrate
            if hasattr(mp3_file, 'info') and mp3_file.info.length:
                duration = mp3_file.info.length
                minutes = int(duration // 60)
                seconds = int(duration % 60)
                self.metadata_duration.set(f"{minutes}:{seconds:02d}")
            else:
                self.metadata_duration.set("-")
            
            # Bitrate
            if hasattr(mp3_file, 'info') and hasattr(mp3_file.info, 'bitrate'):
                bitrate = mp3_file.info.bitrate
                self.metadata_bitrate.set(f"{bitrate} kbps")
            else:
                self.metadata_bitrate.set("-")
            
            # Tags (mit vorgemerkten Änderungen)
            original_title = mp3_file.get('TIT2', [''])[0] if mp3_file.get('TIT2') else ""
            original_artist = mp3_file.get('TPE1', [''])[0] if mp3_file.get('TPE1') else ""
            original_album = mp3_file.get('TALB', [''])[0] if mp3_file.get('TALB') else ""
            original_year = mp3_file.get('TDRC', [''])[0] if mp3_file.get('TDRC') else ""
            original_track = mp3_file.get('TRCK', [''])[0] if mp3_file.get('TRCK') else ""
            original_genre = mp3_file.get('TCON', [''])[0] if mp3_file.get('TCON') else ""
            
            # Vorgemerkte Änderungen berücksichtigen
            pending = self.pending_changes.get(file_path, {})
            
            self.metadata_title.set(pending.get('title', original_title))
            self.metadata_artist.set(pending.get('artist', original_artist))
            self.metadata_album.set(pending.get('album', original_album))
            self.metadata_year.set(pending.get('year', original_year))
            self.metadata_track.set(pending.get('track', original_track))
            self.metadata_genre.set(pending.get('genre', original_genre))
            
            # Entry-Felder styling (kursiv für geänderte Werte)
            entry_fields = {
                'title': self.title_entry,
                'artist': self.artist_entry,
                'album': self.album_entry,
                'year': self.year_entry,
                'track': self.track_entry,
                'genre': self.genre_entry
            }
            
            for field, entry_widget in entry_fields.items():
                if field in pending:
                    # Geändert - kursiv
                    entry_widget.configure(font=('Arial', 9, 'italic'))
                else:
                    # Unverändert - normal
                    entry_widget.configure(font=('Arial', 9))
            
            # Advanced Tags laden
            if hasattr(self, 'metadata_release_year'):
                original_release_year = self.get_original_advanced_metadata_value(file_path, 'release_year')
                original_rating = self.get_original_advanced_metadata_value(file_path, 'rating')
                original_bpm = self.get_original_advanced_metadata_value(file_path, 'bpm')
                original_energy = self.get_original_advanced_metadata_value(file_path, 'energy')
                original_danceability = self.get_original_advanced_metadata_value(file_path, 'danceability')
                original_mood = self.get_original_advanced_metadata_value(file_path, 'mood')
                original_similar_artist = self.get_original_advanced_metadata_value(file_path, 'similar_artist')
                original_comment = self.get_original_advanced_metadata_value(file_path, 'comment')
                
                # Neue erweiterte Felder
                original_url = self.get_original_advanced_metadata_value(file_path, 'url')
                original_era = self.get_original_advanced_metadata_value(file_path, 'era')
                original_style = self.get_original_advanced_metadata_value(file_path, 'style')
                original_energy_level = self.get_original_advanced_metadata_value(file_path, 'energy_level')
                original_lyrics = self.get_original_advanced_metadata_value(file_path, 'lyrics')
                
                # Vorgemerkte Änderungen berücksichtigen
                self.metadata_release_year.set(pending.get('release_year', original_release_year))
                self.metadata_rating.set(pending.get('rating', original_rating))
                self.metadata_bpm.set(pending.get('bpm', original_bpm))
                self.metadata_energy.set(pending.get('energy', original_energy))
                self.metadata_danceability.set(pending.get('danceability', original_danceability))
                self.metadata_mood.set(pending.get('mood', original_mood))
                self.metadata_similar_artist.set(pending.get('similar_artist', original_similar_artist))
                self.metadata_comment.set(pending.get('comment', original_comment))
                
                # Neue erweiterte Felder setzen
                self.metadata_url.set(pending.get('url', original_url))
                self.metadata_era.set(pending.get('era', original_era))
                self.metadata_style.set(pending.get('style', original_style))
                self.metadata_energy_level.set(pending.get('energy_level', original_energy_level))
                
                # Lyrics in Text-Widget setzen
                self.lyrics_text.delete('1.0', tk.END)
                lyrics_content = pending.get('lyrics', original_lyrics)
                if lyrics_content:
                    self.lyrics_text.insert('1.0', lyrics_content)
                
                # Advanced Entry-Felder styling
                advanced_entry_fields = {
                    'release_year': self.release_year_entry,
                    'rating': self.rating_entry,
                    'bpm': self.bpm_entry,
                    'energy': self.energy_entry,
                    'danceability': self.danceability_entry,
                    'mood': self.mood_entry,
                    'similar_artist': self.similar_artist_entry,
                    'comment': self.comment_entry,
                    'url': self.url_entry,
                    'era': self.era_entry,
                    'style': self.style_entry,
                    'energy_level': self.energy_level_entry
                }
                
                for field, entry_widget in advanced_entry_fields.items():
                    if field in pending:
                        # Geändert - kursiv
                        entry_widget.configure(font=('Arial', 8, 'italic'))
                    else:
                        # Unverändert - normal
                        entry_widget.configure(font=('Arial', 8))
                
                # Lyrics Text-Widget Styling
                if 'lyrics' in pending:
                    self.lyrics_text.configure(font=('Arial', 8, 'italic'))
                else:
                    self.lyrics_text.configure(font=('Arial', 8))
            
            # Cover Status und Anzeige
            cover_found = False
            cover_image = None
            
            # 1. Priorität: Cover aus pending_changes (falls vorhanden)
            if file_path in self.pending_changes and 'cover' in self.pending_changes[file_path]:
                try:
                    from PIL import Image, ImageTk
                    import io
                    
                    cover_data = self.pending_changes[file_path]['cover']
                    if cover_data:
                        # Cover-Daten extrahieren (kann Tupel oder direkte Bytes sein)
                        if isinstance(cover_data, tuple) and len(cover_data) == 2:
                            mime_type, image_bytes = cover_data
                        else:
                            image_bytes = cover_data
                        
                        # Cover-Bild aus pending_changes laden und anzeigen
                        image = Image.open(io.BytesIO(image_bytes))
                        # Bild auf passende Größe skalieren (max 180x180)
                        image.thumbnail((180, 180), Image.Resampling.LANCZOS)
                        cover_image = ImageTk.PhotoImage(image)
                        
                        # Bild im Label anzeigen
                        self.metadata_cover_image.configure(image=cover_image, text="")
                        self.metadata_cover_image.image = cover_image  # Referenz halten
                        
                        # Status setzen (als Änderung markiert)
                        self.metadata_cover_status.set(f"🔄 Neues Cover ({image.size[0]}x{image.size[1]}) - Änderung")
                        cover_found = True
                except Exception as e:
                    print(f"Fehler beim Laden des Cover aus pending_changes: {e}")
                    self.metadata_cover_status.set("🔄 Neues Cover (Fehler beim Anzeigen)")
            
            # 2. Priorität: Internes Cover prüfen
            if not cover_found:
                try:
                    from PIL import Image, ImageTk
                    import io
                    
                    # Alle APIC-Tags prüfen (nicht nur 'APIC:')
                    apic_tag = None
                    if mp3_file.tags:
                        for tag_name in mp3_file.tags.keys():
                            if tag_name.startswith('APIC'):
                                apic_tag = mp3_file.tags[tag_name]
                                break
                    
                    if apic_tag and apic_tag.data:
                        # Cover-Bild laden und anzeigen
                        image = Image.open(io.BytesIO(apic_tag.data))
                        # Bild auf passende Größe skalieren (max 180x180)
                        image.thumbnail((180, 180), Image.Resampling.LANCZOS)
                        cover_image = ImageTk.PhotoImage(image)
                        
                        # Bild im Label anzeigen
                        self.metadata_cover_image.configure(image=cover_image, text="")
                        self.metadata_cover_image.image = cover_image  # Referenz halten
                        
                        # Status setzen
                        self.metadata_cover_status.set(f"✅ Internes Cover ({image.size[0]}x{image.size[1]})")
                        cover_found = True
                except Exception as e:
                    print(f"Fehler beim Laden des internen Covers: {e}")
                    self.metadata_cover_status.set("✅ Internes Cover (Fehler beim Anzeigen)")
            
            # Externes Cover prüfen (wenn kein internes gefunden oder angezeigt)
            if not cover_found:
                try:
                    from PIL import Image, ImageTk
                    
                    cover_extensions = ['.jpg', '.jpeg', '.png', '.bmp']
                    directory = os.path.dirname(file_path)
                    
                    # Standard Cover-Namen prüfen
                    cover_names = ['cover', 'folder', 'album', 'front']
                    for cover_name in cover_names:
                        for ext in cover_extensions:
                            cover_path = os.path.join(directory, f"{cover_name}{ext}")
                            if os.path.exists(cover_path):
                                try:
                                    image = Image.open(cover_path)
                                    image.thumbnail((180, 180), Image.Resampling.LANCZOS)
                                    cover_image = ImageTk.PhotoImage(image)
                                    
                                    self.metadata_cover_image.configure(image=cover_image, text="")
                                    self.metadata_cover_image.image = cover_image
                                    
                                    self.metadata_cover_status.set(f"📁 Externes Cover ({image.size[0]}x{image.size[1]})")
                                    cover_found = True
                                    break
                                except Exception as e:
                                    print(f"Fehler beim Laden des externen Covers: {e}")
                        if cover_found:
                            break
                except ImportError:
                    print("PIL nicht verfügbar für Cover-Anzeige")
            
            # Kein Cover gefunden
            if not cover_found:
                self.metadata_cover_image.configure(image="", text="Kein Cover\nverfügbar")
                self.metadata_cover_image.image = None
                self.metadata_cover_status.set("❌ Kein Cover")
            
            print(f"📋 Metadaten-Panel aktualisiert: {filename}")
            
            # Änderungen-Panel aktualisieren
            self.update_changes_display()
            
        except Exception as e:
            print(f"🚨 Fehler beim Laden der Metadaten: {e}")
            self.metadata_filename.set(f"Fehler: {os.path.basename(file_path)}")
            self.metadata_filesize.set("Fehler")
            self.metadata_duration.set("Fehler")
            self.metadata_title.set("Fehler beim Laden")
            self.metadata_artist.set("-")
            self.metadata_album.set("-")
            self.metadata_year.set("-")
            self.metadata_track.set("-")
            self.metadata_genre.set("-")
            self.metadata_cover_status.set("❌ Fehler")

    def create_status_bar(self, parent, row=3):
        """Erstellt die Status Bar"""
        self.status_var = tk.StringVar()
        self.status_var.set("Bereit")
        
        status_bar = ttk.Label(parent, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=row, column=0, sticky=(tk.W, tk.E))
        
    def create_context_menu(self):
        """Erstellt das Kontextmenü für die Datei-Tabelle"""
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="🎵 Vorhören", command=self.play_selected_file)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="✏️ Metadaten bearbeiten", command=self.edit_file_metadata_from_context)
        self.context_menu.add_command(label="🖼️ Cover auswählen", command=self.select_cover_for_file)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="✅ Markieren", command=self.mark_selected_file)
        self.context_menu.add_command(label="❌ Markierung entfernen", command=self.unmark_selected_file)

    def on_file_selection(self, event):
        """Event-Handler für Datei-Auswahl - aktualisiert Metadaten-Panel"""
        selection = self.files_tree.selection()
        if selection:
            selected_item = selection[0]
            file_path = self.get_file_path_from_tree_item(selected_item)
            if file_path:
                self.update_metadata_panel(file_path)
            else:
                self.clear_metadata_panel()
        else:
            self.clear_metadata_panel()
    
    def on_metadata_change(self, field):
        """Wird aufgerufen wenn ein Metadaten-Feld geändert wird"""
        if not self.current_file_path:
            return
            
        # Aktuellen Wert aus dem Entry-Feld holen
        field_vars = {
            'title': self.metadata_title,
            'artist': self.metadata_artist, 
            'album': self.metadata_album,
            'year': self.metadata_year,
            'track': self.metadata_track,
            'genre': self.metadata_genre
        }
        
        if field not in field_vars:
            return
            
        new_value = field_vars[field].get()
        
        # Vorgemerkte Änderungen verwalten
        if self.current_file_path not in self.pending_changes:
            self.pending_changes[self.current_file_path] = {}
            
        # Originalwert aus der Datei laden (zur Vergleich)
        original_value = self.get_original_metadata_value(self.current_file_path, field)
        
        if new_value != original_value:
            # Änderung vormerken
            self.pending_changes[self.current_file_path][field] = new_value
            self.changed_entry_fields.add(field)
            
            # Entry-Feld kursiv markieren 
            entry_widgets = {
                'title': self.title_entry,
                'artist': self.artist_entry,
                'album': self.album_entry,
                'year': self.year_entry,
                'track': self.track_entry,
                'genre': self.genre_entry
            }
            if field in entry_widgets:
                entry_widgets[field].configure(font=('Arial', 9, 'italic'))
                
            print(f"📝 Änderung vorgemerkt: {field} = '{new_value}' für {os.path.basename(self.current_file_path)}")
        else:
            # Änderung zurückgenommen
            if field in self.pending_changes.get(self.current_file_path, {}):
                del self.pending_changes[self.current_file_path][field]
            self.changed_entry_fields.discard(field)
            
            # Entry-Feld normal markieren
            entry_widgets = {
                'title': self.title_entry,
                'artist': self.artist_entry,
                'album': self.album_entry,
                'year': self.year_entry,
                'track': self.track_entry,
                'genre': self.genre_entry
            }
            if field in entry_widgets:
                entry_widgets[field].configure(font=('Arial', 9))
        
        # Änderungen-Panel aktualisieren
        self.update_changes_display()
        
        # Bei mehreren ausgewählten Dateien auch auf diese anwenden
        selected = self.files_tree.selection()
        if len(selected) > 1:
            self.apply_change_to_multiple_files(field, new_value)
    
    def on_advanced_metadata_change(self, field):
        """Wird aufgerufen wenn ein Advanced-Metadaten-Feld geändert wird"""
        if not self.current_file_path:
            return
            
        # Aktuellen Wert aus dem Entry-Feld holen
        field_vars = {
            'release_year': self.metadata_release_year,
            'rating': self.metadata_rating,
            'bpm': self.metadata_bpm,
            'energy': self.metadata_energy,
            'danceability': self.metadata_danceability,
            'mood': self.metadata_mood,
            'similar_artist': self.metadata_similar_artist,
            'comment': self.metadata_comment,
            'url': self.metadata_url,
            'era': self.metadata_era,
            'style': self.metadata_style,
            'energy_level': self.metadata_energy_level
        }
        
        if field not in field_vars:
            return
            
        new_value = field_vars[field].get()
        
        # Vorgemerkte Änderungen verwalten
        if self.current_file_path not in self.pending_changes:
            self.pending_changes[self.current_file_path] = {}
            
        # Originalwert aus der Datei laden (zur Vergleich)
        original_value = self.get_original_advanced_metadata_value(self.current_file_path, field)
        
        if new_value != original_value:
            # Änderung vormerken
            self.pending_changes[self.current_file_path][field] = new_value
            self.changed_entry_fields.add(field)
            
            # Entry-Feld kursiv markieren 
            entry_widgets = {
                'release_year': self.release_year_entry,
                'rating': self.rating_entry,
                'bpm': self.bpm_entry,
                'energy': self.energy_entry,
                'danceability': self.danceability_entry,
                'mood': self.mood_entry,
                'similar_artist': self.similar_artist_entry,
                'comment': self.comment_entry,
                'url': self.url_entry,
                'era': self.era_entry,
                'style': self.style_entry,
                'energy_level': self.energy_level_entry
            }
            if field in entry_widgets:
                entry_widgets[field].configure(font=('Arial', 8, 'italic'))
                
            print(f"📝 Advanced-Änderung vorgemerkt: {field} = '{new_value}' für {os.path.basename(self.current_file_path)}")
        else:
            # Änderung zurückgenommen
            if field in self.pending_changes.get(self.current_file_path, {}):
                del self.pending_changes[self.current_file_path][field]
            self.changed_entry_fields.discard(field)
            
            # Entry-Feld normal markieren
            entry_widgets = {
                'release_year': self.release_year_entry,
                'rating': self.rating_entry,
                'bpm': self.bpm_entry,
                'energy': self.energy_entry,
                'danceability': self.danceability_entry,
                'mood': self.mood_entry,
                'similar_artist': self.similar_artist_entry,
                'comment': self.comment_entry,
                'url': self.url_entry,
                'era': self.era_entry,
                'style': self.style_entry,
                'energy_level': self.energy_level_entry
            }
            if field in entry_widgets:
                entry_widgets[field].configure(font=('Arial', 8))
        
        # Änderungen-Panel aktualisieren
        self.update_changes_display()
        
        # Bei mehreren ausgewählten Dateien auch auf diese anwenden
        selected = self.files_tree.selection()
        if len(selected) > 1:
            self.apply_change_to_multiple_files(field, new_value)
    
    def on_lyrics_change(self):
        """Wird aufgerufen wenn das Lyrics-Textfeld geändert wird"""
        if not self.current_file_path:
            return
            
        # Aktuellen Wert aus dem Text-Widget holen
        new_value = self.lyrics_text.get('1.0', tk.END).strip()
        
        # Vorgemerkte Änderungen verwalten
        if self.current_file_path not in self.pending_changes:
            self.pending_changes[self.current_file_path] = {}
            
        # Originalwert aus der Datei laden (zur Vergleich)
        original_value = self.get_original_advanced_metadata_value(self.current_file_path, 'lyrics')
        
        if new_value != original_value:
            # Änderung vormerken
            self.pending_changes[self.current_file_path]['lyrics'] = new_value
            self.changed_entry_fields.add('lyrics')
            
            # Text-Widget kursiv markieren 
            self.lyrics_text.configure(font=('Arial', 8, 'italic'))
                
            print(f"📝 Lyrics-Änderung vorgemerkt für {os.path.basename(self.current_file_path)}")
        else:
            # Änderung zurückgenommen
            if 'lyrics' in self.pending_changes.get(self.current_file_path, {}):
                del self.pending_changes[self.current_file_path]['lyrics']
            self.changed_entry_fields.discard('lyrics')
            
            # Text-Widget normal markieren
            self.lyrics_text.configure(font=('Arial', 8))
        
        # Änderungen-Panel aktualisieren
        self.update_changes_display()
    
    
    def get_original_advanced_metadata_value(self, file_path, field):
        """Holt den ursprünglichen Advanced-Metadaten-Wert aus der Datei oder aus angereicherten Daten"""
        # Erst aus angereicherten Daten schauen (falls vorhanden)
        if hasattr(self, 'files_data') and self.files_data:
            for file_data in self.files_data:
                if file_data.get('path') == file_path:
                    # Aus angereicherten advanced_tags lesen
                    if 'advanced_tags' in file_data and field in file_data['advanced_tags']:
                        return file_data['advanced_tags'][field]
                    break
        
        # Fallback: Aus ID3-Tags der Datei lesen
        try:
            from mutagen.mp3 import MP3
            mp3_file = MP3(file_path)
            
            # Advanced Field Mapping - nutzt TXXX für Custom Tags
            field_map = {
                'release_year': 'TDRL',  # Release Date
                'rating': 'POPM',        # Popularimeter (vereinfacht)
                'bpm': 'TBPM',           # BPM
                'tempo': 'TBPM',         # Alias für BPM
                'energy': 'TXXX:ENERGY',
                'danceability': 'TXXX:DANCEABILITY',
                'mood': 'TXXX:MOOD',
                'similar_artist': 'TXXX:SIMILAR_ARTIST',
                'comment': 'COMM::eng',  # Comment
                'url': 'TXXX:URL',
                'era': 'TXXX:ERA',
                'style': 'TXXX:STYLE',
                'energy_level': 'TXXX:ENERGY_LEVEL',
                'lyrics': 'USLT::eng'   # Unsychronized Lyrics
            }
            
            if field in field_map:
                tag_name = field_map[field]
                
                if tag_name.startswith('TXXX:'):
                    # Custom TXXX Tag
                    for key in mp3_file.keys():
                        if key.startswith('TXXX:') and tag_name.split(':')[1] in key:
                            return str(mp3_file[key].text[0])
                elif tag_name == 'POPM':
                    # Rating - vereinfacht
                    if tag_name in mp3_file:
                        rating = mp3_file[tag_name].rating
                        return str(int(rating / 51)) if rating else ""  # 0-255 -> 0-5
                elif tag_name == 'COMM::eng':
                    # Comment
                    if tag_name in mp3_file:
                        return str(mp3_file[tag_name].text[0])
                elif tag_name == 'USLT::eng':
                    # Lyrics
                    if tag_name in mp3_file:
                        return str(mp3_file[tag_name].text)
                elif tag_name in mp3_file:
                    # Standard Tags
                    return str(mp3_file[tag_name].text[0])
                        
        except Exception as e:
            print(f"Fehler beim Lesen der Advanced Metadata: {e}")
        
        return ""

    def get_original_metadata_value(self, file_path, field):
        """Holt den ursprünglichen Metadaten-Wert aus der Datei"""
        try:
            from mutagen.mp3 import MP3
            mp3_file = MP3(file_path)
            
            field_map = {
                'title': 'TIT2',
                'artist': 'TPE1', 
                'album': 'TALB',
                'year': 'TDRC',
                'track': 'TRCK',
                'genre': 'TCON'
            }
            
            if field in field_map:
                tag_value = mp3_file.get(field_map[field])
                if tag_value:
                    return str(tag_value[0])
            return ""
        except:
            return ""
    
    def apply_change_to_multiple_files(self, field, new_value):
        """Wendet Änderung auf alle ausgewählten Dateien an"""
        selected = self.files_tree.selection()
        for item in selected:
            file_path = self.get_file_path_from_tree_item(item)
            if file_path and file_path != self.current_file_path:
                # Änderung für andere Dateien vormerken
                if file_path not in self.pending_changes:
                    self.pending_changes[file_path] = {}
                self.pending_changes[file_path][field] = new_value
                
                # In der Tabelle kursiv anzeigen (wenn geändert)
                original_value = self.get_original_metadata_value(file_path, field)
                if new_value != original_value:
                    self.mark_table_field_as_changed(item, field)
                    
        print(f"📝 Änderung '{field}={new_value}' auf {len(selected)} Dateien angewendet")
    
    def mark_table_field_as_changed(self, item, field):
        """Markiert ein Feld in der Tabelle als geändert (durch Prefix)"""
        try:
            # Aktuelle Werte holen
            values = list(self.files_tree.item(item, 'values'))
            if not values:
                return
                
            # Field-Mapping für die Spalten
            field_map = {
                'title': 1,    # filename ist hidden, title ist Index 1
                'artist': 2,
                'album': 3,
                'year': 4,
                'track': 5,
                'genre': 6
            }
            
            if field in field_map:
                col_index = field_map[field]
                if col_index < len(values):
                    current_value = values[col_index]
                    # Markierung hinzufügen wenn noch nicht vorhanden
                    if not current_value.startswith('⚠️ '):
                        values[col_index] = f"⚠️ {current_value}"
                        self.files_tree.item(item, values=tuple(values))
                        
            # Auch den Dateinamen markieren wenn Änderungen vorhanden
            current_text = self.files_tree.item(item, 'text')
            if not current_text.startswith('⚠️ ') and not current_text.startswith('🖼️ ⚠️'):
                if current_text.startswith('🖼️ '):
                    # Cover-Symbol vorhanden - nach dem Cover-Symbol einfügen
                    new_text = current_text.replace('🖼️ ', '🖼️ ⚠️ ')
                else:
                    # Kein Cover-Symbol - am Anfang einfügen
                    new_text = f"⚠️ {current_text}"
                self.files_tree.item(item, text=new_text)
                
        except Exception as e:
            print(f"🚨 Fehler beim Markieren des Tabellenfelds: {e}")
    
    def update_changes_display(self):
        """Aktualisiert die Anzeige der vorgemerkten Änderungen"""
        self.changes_text.config(state='normal')
        self.changes_text.delete(1.0, tk.END)
        
        if not self.pending_changes:
            self.changes_text.insert(tk.END, "Keine Änderungen vorgemerkt.")
        else:
            total_files = len(self.pending_changes)
            total_changes = sum(len(changes) for changes in self.pending_changes.values())
            
            self.changes_text.insert(tk.END, f"📝 {total_changes} Änderungen in {total_files} Dateien:\n\n")
            
            for file_path, changes in self.pending_changes.items():
                if changes:  # Nur wenn wirklich Änderungen vorhanden
                    filename = os.path.basename(file_path)
                    change_list = [f"{field}='{value}'" for field, value in changes.items()]
                    self.changes_text.insert(tk.END, f"• {filename}: {', '.join(change_list)}\n")
        
        self.changes_text.config(state='disabled')
    
    def clear_metadata_panel(self):
        """Leert das Metadaten-Panel wenn keine Datei ausgewählt ist"""
        self.current_file_path = None
        self.metadata_filename.set("Keine Datei ausgewählt")
        self.metadata_filesize.set("-")
        self.metadata_duration.set("-")
        self.metadata_title.set("-")
        self.metadata_artist.set("-")
        self.metadata_album.set("-")
        self.metadata_year.set("-")
        self.metadata_track.set("-")
        self.metadata_genre.set("-")
        self.metadata_cover_status.set("Kein Cover")
        
        # Advanced Felder zurücksetzen
        if hasattr(self, 'metadata_release_year'):
            self.metadata_release_year.set("-")
        if hasattr(self, 'metadata_rating'):
            self.metadata_rating.set("-")
        if hasattr(self, 'metadata_bpm'):
            self.metadata_bpm.set("-")
        if hasattr(self, 'metadata_energy'):
            self.metadata_energy.set("-")
        if hasattr(self, 'metadata_danceability'):
            self.metadata_danceability.set("-")
        if hasattr(self, 'metadata_mood'):
            self.metadata_mood.set("-")
        if hasattr(self, 'metadata_similar_artist'):
            self.metadata_similar_artist.set("-")
        if hasattr(self, 'metadata_comment'):
            self.metadata_comment.set("-")
        
        # Cover-Bild zurücksetzen
        if hasattr(self, 'metadata_cover_image'):
            self.metadata_cover_image.configure(image="", text="Kein Cover\nverfügbar")
            self.metadata_cover_image.image = None
            
        # Entry-Felder normal formatieren (nicht kursiv)
        if hasattr(self, 'title_entry'):
            self.title_entry.configure(font=('Arial', 9))
        if hasattr(self, 'artist_entry'):
            self.artist_entry.configure(font=('Arial', 9))
        if hasattr(self, 'album_entry'):
            self.album_entry.configure(font=('Arial', 9))
        if hasattr(self, 'year_entry'):
            self.year_entry.configure(font=('Arial', 9))
        if hasattr(self, 'track_entry'):
            self.track_entry.configure(font=('Arial', 9))
        if hasattr(self, 'genre_entry'):
            self.genre_entry.configure(font=('Arial', 9))
            
        # Advanced Entry-Felder normal formatieren
        if hasattr(self, 'release_year_entry'):
            self.release_year_entry.configure(font=('Arial', 8))
        if hasattr(self, 'rating_entry'):
            self.rating_entry.configure(font=('Arial', 8))
        if hasattr(self, 'bpm_entry'):
            self.bpm_entry.configure(font=('Arial', 8))
        if hasattr(self, 'energy_entry'):
            self.energy_entry.configure(font=('Arial', 8))
        if hasattr(self, 'danceability_entry'):
            self.danceability_entry.configure(font=('Arial', 8))
        if hasattr(self, 'mood_entry'):
            self.mood_entry.configure(font=('Arial', 8))
        if hasattr(self, 'similar_artist_entry'):
            self.similar_artist_entry.configure(font=('Arial', 8))
        if hasattr(self, 'comment_entry'):
            self.comment_entry.configure(font=('Arial', 8))
            
        # Änderungen-Panel aktualisieren
        if hasattr(self, 'changes_text'):
            self.update_changes_display()

    def show_context_menu(self, event):
        """Zeigt das Kontextmenü"""
        # Item unter Mauszeiger ermitteln
        item = self.files_tree.identify_row(event.y)
        if item:
            # Item auswählen
            self.files_tree.selection_set(item)
            
            # Prüfe ob es eine Datei ist (nicht Verzeichnis)
            item_tags = self.files_tree.item(item, 'tags')
            if 'file' in item_tags:  # Vereinfacht: nur 'file' Tag prüfen
                # Kontextmenü anzeigen
                try:
                    self.context_menu.tk_popup(event.x_root, event.y_root)
                finally:
                    self.context_menu.grab_release()

    def play_selected_file(self):
        """Spielt die ausgewählte Datei ab"""
        selection = self.files_tree.selection()
        if not selection:
            messagebox.showinfo("Info", "Bitte wählen Sie eine MP3-Datei aus.")
            return
        
        selected_item = selection[0]
        full_path = self.get_file_path_from_tree_item(selected_item)
        
        if full_path:
            # Audio-Player verwenden
            if self.audio_player_widget:
                if self.audio_player_widget.load_file(full_path):
                    filename = os.path.basename(full_path)
                    self.status_var.set(f"🎵 Spielt ab: {filename}")
                    print(f"🎵 Datei für Vorhören geladen: {filename}")
                    
                    # Automatisch starten
                    self.audio_player_widget.toggle_play()
                else:
                    self.status_var.set("❌ Fehler beim Laden der Datei")
                    messagebox.showerror("Fehler", f"Datei konnte nicht geladen werden:\n{os.path.basename(full_path)}")
            else:
                messagebox.showerror("Fehler", "Audio-Player nicht verfügbar")
        else:
            messagebox.showerror("Fehler", "Datei nicht gefunden oder ungültiges Format")

    def mark_selected_file(self):
        """Markiert die ausgewählte Datei"""
        selection = self.files_tree.selection()
        if selection:
            item = selection[0]
            item_tags = self.files_tree.item(item, 'tags')
            if 'file' in item_tags or 'selected' in item_tags:
                self.selected_items.add(item)
                self.files_tree.item(item, tags=['selected'])
                self.update_selection_status()

    def unmark_selected_file(self):
        """Entfernt Markierung der ausgewählten Datei"""
        selection = self.files_tree.selection()
        if selection:
            item = selection[0]
            if item in self.selected_items:
                self.selected_items.remove(item)
                self.files_tree.item(item, tags=['file'])
                self.update_selection_status()

    def get_file_path_from_tree_item(self, item):
        """Ermittelt den vollständigen Dateipfad aus einem Tree-Item"""
        try:
            # Prüfe ob es eine Datei ist
            item_tags = self.files_tree.item(item, 'tags')
            if 'file' not in item_tags and 'selected' not in item_tags:
                return None
            
            # Verwende das Mapping, falls verfügbar
            if item in self.item_to_path:
                full_path = self.item_to_path[item]
                print(f"🔍 Pfad aus Mapping: {full_path}")
                return full_path if os.path.exists(full_path) else None
            
            # Fallback: Versuch über Tree-Struktur (für Kompatibilität)
            parent_item = self.files_tree.parent(item)
            if not parent_item:
                return None
            
            # Extrahiere echten Verzeichnisnamen aus formatiertem Text
            directory_text = self.files_tree.item(parent_item, 'text')
            # Entferne Format: "📁 NAME (X Dateien)" -> "NAME"
            if directory_text.startswith('📁 ') and ' (' in directory_text:
                directory_name = directory_text[2:].split(' (')[0]
            else:
                directory_name = directory_text
            
            filename = self.files_tree.item(item, 'text')
            
            print(f"🔍 Tree Fallback:")
            print(f"  - Directory name: {directory_name}")
            print(f"  - Filename: {filename}")
            
            # Versuche Pfad aus current_directory zu konstruieren
            if hasattr(self, 'current_directory') and self.current_directory.get():
                base_dir = self.current_directory.get()
                # Prüfe verschiedene Pfad-Kombinationen
                possible_paths = [
                    os.path.join(base_dir, directory_name, filename),
                    os.path.join(base_dir, filename),
                    os.path.join(directory_name, filename)
                ]
                
                for path in possible_paths:
                    if os.path.exists(path):
                        print(f"🔍 Gefunden: {path}")
                        return path
            
            return None
            
        except Exception as e:
            print(f"🚨 Fehler bei Pfad-Ermittlung: {e}")
            return None

    def toggle_audio_playback(self):
        """Wechselt zwischen Play und Pause für den Audio-Player"""
        if self.audio_player_widget:
            self.audio_player_widget.toggle_play()

    def select_cover_for_file(self):
        """Wählt Cover für die ausgewählte Datei"""
        selection = self.files_tree.selection()
        if not selection:
            messagebox.showinfo("Info", "Bitte wählen Sie eine MP3-Datei aus.")
            return
        
        selected_item = selection[0]
        full_path = self.get_file_path_from_tree_item(selected_item)
        
        if full_path and self.cover_manager:
            try:
                filename = os.path.basename(full_path)
                # Cover-Dialog öffnen mit Callback
                dialog = CoverSelectionDialog(self.root, full_path, filename, self.cover_manager, 
                                            callback=self.on_cover_selected)
                print(f"🖼️ Cover-Dialog für {filename} geöffnet")
            except Exception as e:
                print(f"🚨 Cover-Dialog Fehler: {e}")
                messagebox.showerror("Fehler", f"Cover-Dialog konnte nicht geöffnet werden:\n{str(e)}")
        else:
            if not full_path:
                messagebox.showerror("Fehler", "Datei nicht gefunden oder ungültiges Format")
            else:
                messagebox.showerror("Fehler", "Cover-Manager nicht verfügbar")

    def on_cover_selected(self, file_path, cover_source):
        """Callback wenn Cover aus Dialog ausgewählt wurde"""
        print(f"📞 Callback wird aufgerufen mit: {file_path}, {cover_source}")
        if cover_source and self.cover_manager:
            print(f"🎨 Starte Cover-Anwendung für: {os.path.basename(file_path)}")
            # Cover anwenden
            threading.Thread(target=self._apply_selected_cover_worker, 
                           args=(file_path, cover_source), daemon=True).start()
        else:
            print("❌ Kein Cover ausgewählt oder Cover-Manager nicht verfügbar")

    def _apply_selected_cover_worker(self, file_path, cover_source):
        """Worker-Thread für Cover-Anwendung auf eine einzelne Datei"""
        try:
            print(f"🔄 Wende Cover an auf: {os.path.basename(file_path)}")
            
            # Cover-Daten von CoverSource abrufen
            if cover_source.type == 'url':
                if hasattr(cover_source, 'preview_data') and cover_source.preview_data:
                    cover_data = cover_source.preview_data
                else:
                    # URL-Cover herunterladen falls preview_data nicht verfügbar
                    import requests
                    response = requests.get(cover_source.path)
                    response.raise_for_status()
                    cover_data = response.content
                    
                # MIME-Type bestimmen
                if cover_data.startswith(b'\xff\xd8\xff'):
                    mime_type = 'image/jpeg'
                elif cover_data.startswith(b'\x89PNG'):
                    mime_type = 'image/png'
                else:
                    mime_type = 'image/jpeg'  # Fallback
                    
            elif cover_source.type == 'external':
                with open(cover_source.path, 'rb') as f:
                    cover_data = f.read()
                    
                # MIME-Type aus Dateierweiterung
                if cover_source.path.lower().endswith('.png'):
                    mime_type = 'image/png'
                else:
                    mime_type = 'image/jpeg'
                    
            elif cover_source.type == 'internal':
                # Cover aus anderer MP3-Datei extrahieren
                from mutagen.mp3 import MP3
                audio = MP3(cover_source.path)
                if audio.tags and 'APIC:' in audio.tags:
                    apic = audio.tags['APIC:']
                    cover_data = apic.data
                    mime_type = apic.mime
                else:
                    raise Exception("Kein Cover in Quell-MP3 gefunden")
            else:
                raise Exception(f"Unbekannter Cover-Typ: {cover_source.type}")
            
            # Cover mit MIME-Type in pending_changes registrieren
            cover_with_mime = (mime_type, cover_data)
            self.root.after(0, lambda: self._register_cover_change(file_path, cover_with_mime))
            
        except Exception as e:
            print(f"🚨 Fehler beim Cover-Anwenden: {e}")
            self.root.after(0, lambda: self._on_cover_applied(file_path, False))

    def _register_cover_change(self, file_path, cover_data):
        """Registriert Cover-Änderung in pending_changes"""
        try:
            # Cover in pending_changes eintragen
            if file_path not in self.pending_changes:
                self.pending_changes[file_path] = {}
            
            # Cover-Daten in pending_changes speichern
            self.pending_changes[file_path]['cover'] = cover_data
            
            print(f"📝 Cover-Änderung registriert für: {os.path.basename(file_path)}")
            
            # GUI-Update
            self._on_cover_applied(file_path, True)
            
        except Exception as e:
            print(f"🚨 Fehler beim Registrieren der Cover-Änderung: {e}")
            self._on_cover_applied(file_path, False)

    def _on_cover_applied(self, file_path, success):
        """GUI-Update nach Cover-Anwendung"""
        if success:
            print(f"✅ Cover erfolgreich angewendet auf: {os.path.basename(file_path)}")
            # Metadaten-Panel aktualisieren
            if self.current_file_path == file_path:
                self.update_metadata_panel(file_path)
            messagebox.showinfo("Erfolg", "Cover wurde erfolgreich angewendet!")
        else:
            print(f"❌ Cover-Anwendung fehlgeschlagen für: {os.path.basename(file_path)}")
            messagebox.showerror("Fehler", "Cover konnte nicht angewendet werden")

    def edit_file_metadata_from_context(self):
        """Öffnet den Metadaten-Editor für die ausgewählte Datei (Kontextmenü)"""
        selection = self.files_tree.selection()
        if not selection:
            messagebox.showinfo("Info", "Bitte wählen Sie eine MP3-Datei aus.")
            return
        
        selected_item = selection[0]
        full_path = self.get_file_path_from_tree_item(selected_item)
        
        if full_path:
            # Erstelle file_info Dictionary für den Editor
            try:
                from mutagen.mp3 import MP3
                mp3_file = MP3(full_path)
                
                # Erstelle Dictionary mit den erwarteten Feldern
                file_info = {
                    'filepath': full_path,
                    'filename': os.path.basename(full_path),
                    'title': mp3_file.get('TIT2', [''])[0] if mp3_file.get('TIT2') else '',
                    'artist': mp3_file.get('TPE1', [''])[0] if mp3_file.get('TPE1') else '',
                    'album': mp3_file.get('TALB', [''])[0] if mp3_file.get('TALB') else '',
                    'track': mp3_file.get('TRCK', [''])[0] if mp3_file.get('TRCK') else '',
                    'year': mp3_file.get('TDRC', [''])[0] if mp3_file.get('TDRC') else '',
                    'genre': mp3_file.get('TCON', [''])[0] if mp3_file.get('TCON') else ''
                }
                
                # Finde item_id für Tabellen-Updates
                for item_id, path in self.item_to_path.items():
                    if path == full_path:
                        file_info['item_id'] = item_id
                        break
                
                self.edit_single_file_metadata(file_info)
                
            except Exception as e:
                print(f"🚨 Metadaten-Editor Fehler: {e}")
                messagebox.showerror("Fehler", f"Metadaten konnten nicht geladen werden:\n{str(e)}")
        else:
            messagebox.showerror("Fehler", "Datei nicht gefunden oder ungültiges Format")

    # === Verzeichnis- und Datei-Management ===
    
    def browse_directory(self):
        """Öffnet Dialog zur Verzeichnis-Auswahl"""
        directory = filedialog.askdirectory(title="MP3 Verzeichnis auswählen")
        if directory:
            self.current_directory.set(directory)
            
    def scan_directory(self):
        """Scannt das ausgewählte Verzeichnis nach MP3-Dateien"""
        directory = self.current_directory.get()
        if not directory:
            messagebox.showwarning("Warnung", "Bitte wählen Sie zuerst ein Verzeichnis aus.")
            return
            
        if not os.path.exists(directory):
            messagebox.showerror("Fehler", "Das ausgewählte Verzeichnis existiert nicht.")
            return
            
        self.status_var.set("Scanne Verzeichnis...")
        threading.Thread(target=self._scan_directory_worker, args=(directory,), daemon=True).start()
        
    def _scan_directory_worker(self, directory):
        """Worker-Thread für das Scannen von Verzeichnissen"""
        try:
            files_data = self.mp3_processor.process_directory(directory)
            # UI-Update im Hauptthread
            self.root.after(0, lambda: self._update_files_display(files_data))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Fehler", f"Fehler beim Scannen: {str(e)}"))
            self.root.after(0, lambda: self.status_var.set("Fehler beim Scannen"))
            
    def _update_files_display(self, files_data):
        """Aktualisiert die Dateien-Anzeige mit Verzeichnis-Gruppierung"""
        # Treeview leeren
        for item in self.files_tree.get_children():
            self.files_tree.delete(item)
            
        self.mp3_files = files_data.get('files', [])
        self.selected_items = set()  # Reset der Auswahl
        self.item_to_path = {}  # Reset des Mappings
        
        # Cover Manager für das Verzeichnis initialisieren
        cover_directory = files_data.get('directory')
        if self.mp3_files and self.mp3_files[0].get('filepath'):
            first_file_path = self.mp3_files[0]['filepath']
            first_file_directory = os.path.dirname(first_file_path)
            
            if first_file_directory != cover_directory:
                cover_directory = first_file_directory
                print(f"📁 CoverManager wird für MP3-Verzeichnis initialisiert: {cover_directory}")
            else:
                print(f"📁 CoverManager wird für Hauptverzeichnis initialisiert: {cover_directory}")
        
        if cover_directory:
            self.cover_manager = CoverManager(cover_directory)
        
        # Dateien nach Verzeichnissen gruppieren
        directories = {}
        for file_data in self.mp3_files:
            file_path = file_data.get('filepath', '')
            if file_path:
                file_dir = os.path.dirname(file_path)
                dir_name = os.path.basename(file_dir) if file_dir else 'Root'
                
                if dir_name not in directories:
                    directories[dir_name] = []
                directories[dir_name].append(file_data)
        
        # Verzeichnisse und Dateien in Treeview einfügen
        for dir_name, files in sorted(directories.items()):
            # Verzeichnis-Knoten erstellen
            dir_item = self.files_tree.insert('', 'end', 
                text=f"📁 {dir_name} ({len(files)} Dateien)",
                values=('', '', '', '', '', ''),
                tags=('directory',))
            
            # Dateien unter Verzeichnis-Knoten einfügen
            for file_data in sorted(files, key=lambda f: f.get('filename', '')):
                # Cover-Status für Symbol bestimmen
                filename = file_data.get('filename', '')
                filepath = file_data.get('filepath', '')
                has_cover = False
                
                try:
                    # Schnelle Cover-Prüfung
                    if filepath:
                        from mutagen.mp3 import MP3
                        mp3_file = MP3(filepath)
                        # Prüfe auf alle APIC-Tags (nicht nur 'APIC:')
                        if mp3_file.tags:
                            apic_tags = [k for k in mp3_file.tags.keys() if k.startswith('APIC')]
                            if apic_tags:
                                has_cover = True
                        
                        if not has_cover:
                            # Externes Cover prüfen (nur häufigste Namen)
                            directory = os.path.dirname(filepath)
                            for cover_name in ['cover.jpg', 'folder.jpg', 'album.jpg']:
                                if os.path.exists(os.path.join(directory, cover_name)):
                                    has_cover = True
                                    break
                except:
                    pass
                
                # Dateiname mit Cover-Symbol wenn vorhanden
                display_name = filename
                if has_cover:
                    display_name = f"🖼️ {filename}"
                
                item_id = self.files_tree.insert(dir_item, 'end',
                    text=display_name,  # Dateiname mit optionalem Cover-Symbol
                    values=(
                        file_data.get('title', ''),
                        file_data.get('artist', ''),
                        file_data.get('album', ''),
                        file_data.get('year', ''),
                        file_data.get('track', ''),
                        file_data.get('genre', '')
                    ),
                    tags=('file',))
                
                # Item-ID in file_data speichern für spätere Referenz
                file_data['item_id'] = item_id
                
                # Zuordnung für Pfad-Ermittlung speichern
                self.item_to_path[item_id] = file_data.get('filepath', '')
            
            # Verzeichnis-Knoten standardmäßig ausgeklappt
            self.files_tree.item(dir_item, open=True)
            
        self.status_var.set(f"Gefunden: {len(self.mp3_files)} MP3-Dateien")
        self.update_selection_status()
        
        # Tags für visuelle Unterscheidung konfigurieren (vereinfacht)
        self.files_tree.tag_configure('directory', background='#f0f0f0', font=('Arial', 9, 'bold'), foreground='black')
        self.files_tree.tag_configure('file', background='white', foreground='black', font=('Arial', 9))
        self.files_tree.tag_configure('selected', background='#e6f3ff', foreground='black', font=('Arial', 9, 'bold'))
        
        # ENTFERNT: Verwirrende 'selected' Tags - wir nutzen die Standard TreeView Auswahl
        print("🎨 Tags konfiguriert - Standard TreeView Auswahl")

    # === Datei-Auswahl und -Management (vereinfacht) ===
    
    def toggle_row_selection(self, event):
        """Zeilen-basierte Markierung statt Checkbox-Klick"""
        # Item unter Mauszeiger ermitteln
        item = self.files_tree.identify('item', event.x, event.y)
        if not item:
            return
            
        # Nur Dateien markierbar, nicht Verzeichnis-Knoten
        item_tags = self.files_tree.item(item, 'tags')
        if 'file' not in item_tags and 'selected' not in item_tags:
            return
            
        # Markierung umschalten
        if item in self.selected_items:
            # Abwählen
            self.selected_items.remove(item)
            # Zurück zu 'file' Tag
            self.files_tree.item(item, tags=['file'])
            print(f"🔘 Datei abgewählt: {self.files_tree.item(item, 'text')}")
        else:
            # Auswählen
            self.selected_items.add(item)
            # Zu 'selected' Tag wechseln
            self.files_tree.item(item, tags=['selected'])
            print(f"🔵 Datei gewählt: {self.files_tree.item(item, 'text')}")
        
        self.update_selection_status()

    def select_all_files(self):
        """Wählt alle Dateien aus"""
        self.selected_items.clear()
        
        # Alle Datei-Items in allen Verzeichnissen finden und markieren
        for dir_item in self.files_tree.get_children():
            for file_item in self.files_tree.get_children(dir_item):
                item_tags = self.files_tree.item(file_item, 'tags')
                if 'file' in item_tags or 'selected' in item_tags:
                    self.selected_items.add(file_item)
                    # Nur 'selected' Tag setzen
                    self.files_tree.item(file_item, tags=['selected'])
                    # Debug: Bestätige dass Tag gesetzt wurde
                    new_tags = self.files_tree.item(file_item, 'tags')
                    print(f"🔵 Datei markiert - Tags: {new_tags}")
        
        self.update_selection_status()
        print(f"🔵 Alle Dateien markiert: {len(self.selected_items)} Dateien")
        
        # Debug: Teste Tag-Konfiguration
        self.debug_tag_configuration()
        
    def select_current_directory(self):
        """Markiert alle Dateien im aktuell ausgewählten Verzeichnis"""
        # Aktuell ausgewähltes Item ermitteln
        selection = self.files_tree.selection()
        if not selection:
            messagebox.showinfo("Info", "Bitte wählen Sie zuerst ein Verzeichnis oder eine Datei aus.")
            return
            
        selected_item = selection[0]
        
        # Ermittle Verzeichnis-Knoten
        item_tags = self.files_tree.item(selected_item, 'tags')
        if 'directory' in item_tags:
            # Direkt ein Verzeichnis ausgewählt
            dir_item = selected_item
        elif 'file' in item_tags or 'selected' in item_tags:
            # Eine Datei ausgewählt - parent ist das Verzeichnis
            dir_item = self.files_tree.parent(selected_item)
        else:
            return
            
        # Alle Dateien in diesem Verzeichnis markieren
        files_marked = 0
        for file_item in self.files_tree.get_children(dir_item):
            item_tags = self.files_tree.item(file_item, 'tags')
            if 'file' in item_tags or 'selected' in item_tags:
                self.selected_items.add(file_item)
                # Nur 'selected' Tag setzen
                self.files_tree.item(file_item, tags=['selected'])
                files_marked += 1
        
        dir_name = self.files_tree.item(dir_item, 'text')
        messagebox.showinfo("Verzeichnis markiert", f"{files_marked} Dateien in '{dir_name}' markiert.")
        self.update_selection_status()
        print(f"🔵 Verzeichnis markiert: {files_marked} Dateien")
        
    def deselect_all_files(self):
        """Hebt alle Auswahlen auf"""
        for item in self.selected_items.copy():
            # Tags zurücksetzen - zu 'file' Tag zurück
            self.files_tree.item(item, tags=['file'])
        
        self.selected_items.clear()
        self.update_selection_status()
        print(f"🔘 Alle Markierungen entfernt")

    def get_selected_files(self):
        """Gibt eine Liste der ausgewählten Dateien zurück"""
        selected_files = []
        
        for item_id in self.selected_items:
            # Finde entsprechende file_data über item_id
            for file_data in self.mp3_files:
                if file_data.get('item_id') == item_id:
                    selected_files.append(file_data)
                    break
        
        return selected_files

    def debug_tag_configuration(self):
        """Debug-Funktion zur Überprüfung der Tag-Konfiguration"""
        try:
            print("🔍 Tag-Konfiguration Debug:")
            
            # ttk.Treeview hat keine tag_cget Methode, verwende tag_has
            configured_tags = ['directory', 'file', 'selected', 'selected_highlight']
            for tag in configured_tags:
                try:
                    # Prüfe ob Tag existiert
                    exists = hasattr(self.files_tree, 'tag_has')
                    print(f"Tag '{tag}' verfügbar: {exists}")
                    
                    # Prüfe Konfiguration durch Anwendung auf Test-Item
                    if self.files_tree.get_children():
                        first_dir = self.files_tree.get_children()[0]
                        if self.files_tree.get_children(first_dir):
                            test_file = self.files_tree.get_children(first_dir)[0]
                            
                            # Wende Tag temporär an und prüfe
                            old_tags = self.files_tree.item(test_file, 'tags')
                            self.files_tree.item(test_file, tags=[tag])
                            new_tags = self.files_tree.item(test_file, 'tags')
                            print(f"Tag '{tag}' Test - Vorher: {old_tags}, Nachher: {new_tags}")
                            
                            # Stelle ursprüngliche Tags wieder her
                            self.files_tree.item(test_file, tags=old_tags)
                            
                except Exception as e:
                    print(f"Tag '{tag}' Debug-Fehler: {e}")
                    
        except Exception as e:
            print(f"Debug-Fehler: {e}")

    def update_selection_status(self):
        """Aktualisiert den Auswahlstatus"""
        count = len(self.selected_items)
        total = len(self.mp3_files)
        
        if count == 0:
            self.selection_status.set("Keine Dateien ausgewählt")
        elif count == 1:
            self.selection_status.set("1 Datei ausgewählt")
        else:
            self.selection_status.set(f"{count} von {total} Dateien ausgewählt")

    def _update_file_in_table(self, file_data):
        """Aktualisiert eine Datei in der Tabelle"""
        try:
            # Verwende item_id für direkte Aktualisierung
            item_id = file_data.get('item_id')
            if not item_id:
                print(f"⚠️ Keine item_id für Datei {file_data.get('filename', 'Unbekannt')}")
                return
                
            # Alle aktuellen Spaltenwerte sammeln
            current_values = list(self.files_tree.item(item_id, 'values'))
            
            # Cover-Status aktualisieren (Spalte 6 - Cover)
            if 'cover_status' in file_data:
                if len(current_values) > 6:
                    current_values[6] = file_data['cover_status']
                else:
                    # Falls zu wenig Spalten, erweitern
                    while len(current_values) <= 6:
                        current_values.append('')
                    current_values[6] = file_data['cover_status']
                
                print(f"📊 Cover-Status aktualisiert: {file_data.get('filename')} → {file_data['cover_status']}")
            
            # Aktualisiere die Werte direkt über item_id
            self.files_tree.item(item_id, values=(
                file_data.get('title', current_values[0] if len(current_values) > 0 else ''),
                file_data.get('artist', current_values[1] if len(current_values) > 1 else ''),
                file_data.get('album', current_values[2] if len(current_values) > 2 else ''),
                file_data.get('year', current_values[3] if len(current_values) > 3 else ''),
                file_data.get('track', current_values[4] if len(current_values) > 4 else ''),
                file_data.get('genre', current_values[5] if len(current_values) > 5 else ''),
                file_data.get('cover_status', current_values[6] if len(current_values) > 6 else '')
            ))
            
            # Checkbox automatisch aktivieren bei Änderungen
            if item_id not in self.selected_items:
                self.selected_items.add(item_id)
                # Nur 'file' Tag setzen - keine verwirrende rote Markierung
                self.files_tree.item(item_id, tags=['file'])
                self.update_selection_status()
                
        except Exception as e:
            print(f"💥 Fehler beim Aktualisieren der Tabelle: {str(e)}")
            import traceback
            traceback.print_exc()

    # === Integrierte Funktionen ===
    
    def recognize_with_shazam(self):
        """Audio-Erkennung mit Shazam für ausgewählte Dateien"""
        selected = self.get_selected_files()
        if not selected:
            messagebox.showwarning("Warnung", "Bitte wählen Sie mindestens eine Datei aus.")
            return
            
        # Audio Recognition Service initialisieren wenn nötig
        if not self.audio_recognition:
            acoustid_key = desktop_config.get_api_key('acoustid')
            if not acoustid_key:
                messagebox.showerror("Fehler", "AcoustID API-Key nicht konfiguriert. Bitte in config.env eintragen.")
                return
            self.audio_recognition = AudioRecognitionService(acoustid_key)
        
        self.status_var.set("Starte Shazam-Erkennung...")
        
        # Threading für Audio-Erkennung
        threading.Thread(target=self._recognize_audio_worker, args=(selected, 'shazam'), daemon=True).start()
        
    def recognize_with_acoustid(self):
        """Audio-Erkennung mit AcoustID für ausgewählte Dateien"""
        selected = self.get_selected_files()
        if not selected:
            messagebox.showwarning("Warnung", "Bitte wählen Sie mindestens eine Datei aus.")
            return
            
        # Audio Recognition Service initialisieren wenn nötig
        if not self.audio_recognition:
            acoustid_key = desktop_config.get_api_key('acoustid')
            if not acoustid_key:
                messagebox.showerror("Fehler", "AcoustID API-Key nicht konfiguriert. Bitte in config.env eintragen.")
                return
            self.audio_recognition = AudioRecognitionService(acoustid_key)
        
        self.status_var.set("Starte AcoustID-Erkennung...")
        
        # Threading für Audio-Erkennung
        threading.Thread(target=self._recognize_audio_worker, args=(selected, 'acoustid'), daemon=True).start()

    def _recognize_audio_worker(self, selected_files, service_type):
        """Worker-Thread für Audio-Erkennung"""
        import asyncio
        
        async def process_files():
            successful = 0
            errors = 0
            
            for i, file_data in enumerate(selected_files):
                try:
                    filepath = file_data.get('filepath')
                    filename = file_data.get('filename', 'Unbekannt')
                    
                    self.root.after(0, lambda f=filename: self.status_var.set(f"Erkenne: {f}..."))
                    
                    # Audio-Erkennung durchführen
                    if service_type == 'shazam':
                        # Für Shazam nutzen wir den Fallback-Mechanismus
                        result = await self.audio_recognition._recognize_with_shazam(filepath)
                    else:
                        # Für AcoustID direkt
                        result = await self.audio_recognition._recognize_with_acoustid(filepath)
                    
                    if result.get('success'):
                        # Metadaten aktualisieren
                        file_data['title'] = result.get('title', file_data.get('title', ''))
                        file_data['artist'] = result.get('artist', file_data.get('artist', ''))
                        if result.get('album'):
                            file_data['album'] = result['album']
                        if result.get('year'):
                            file_data['year'] = str(result['year'])
                        
                        # UI aktualisieren
                        self.root.after(0, lambda: self._update_file_in_table(file_data))
                        successful += 1
                        
                        print(f"✅ {service_type} erfolgreich für {filename}: {result.get('artist')} - {result.get('title')}")
                    else:
                        errors += 1
                        print(f"❌ {service_type} fehlgeschlagen für {filename}: {result.get('error')}")
                        
                except Exception as e:
                    errors += 1
                    print(f"💥 Fehler bei {filename}: {str(e)}")
            
            # Abschlussmeldung
            self.root.after(0, lambda: self.status_var.set(f"{service_type} abgeschlossen: {successful} erfolgreich, {errors} Fehler"))
            self.root.after(0, lambda: messagebox.showinfo("Audio-Erkennung", f"{service_type} Erkennung abgeschlossen.\n\nErfolgreich: {successful}\nFehler: {errors}"))
        
        try:
            # Event Loop erstellen oder verwenden
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(process_files())
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Fehler", f"Fehler bei Audio-Erkennung: {str(e)}"))
            self.root.after(0, lambda: self.status_var.set("Fehler bei Audio-Erkennung"))
    
    def show_covers(self):
        """Zeigt verfügbare Cover für ausgewählte Dateien"""
        selected = self.get_selected_files()
        if not selected:
            messagebox.showwarning("Warnung", "Bitte wählen Sie mindestens eine Datei aus.")
            return
            
        # Für die erste ausgewählte Datei Cover anzeigen
        first_file = selected[0]
        filepath = first_file.get('filepath')
        filename = first_file.get('filename', 'Unbekannt')
        
        print(f"🖼️ Cover-Dialog für {filename} geöffnet")
        print(f"   Dateipfad: {filepath}")
        print(f"   Anzahl ausgewählte Dateien: {len(selected)}")
        
        if not filepath:
            messagebox.showerror("Fehler", "Dateipfad nicht gefunden.")
            return
            
        # Cover-Dialog öffnen mit Callback
        def on_cover_selected(result):
            print(f"📋 Cover-Callback aufgerufen: {result}")
            if result:
                print(f"✅ Cover ausgewählt - starte Anwendung")
                print(f"   Cover-Typ: {result.type}")
                print(f"   Cover-Pfad: {result.path}")
                # Ausgewähltes Cover auf alle selektierten Dateien anwenden
                threading.Thread(target=self._apply_selected_cover_worker, args=(selected, result), daemon=True).start()
            else:
                print("❌ Kein Cover ausgewählt oder Dialog abgebrochen")
        
        dialog = CoverSelectionDialog(self.root, filepath, filename, self.cover_manager, on_cover_selected)
        # Dialog wird asynchron verarbeitet

    def load_covers(self):
        """Cover-Verwaltung für ausgewählte Dateien"""
        selected = self.get_selected_files()
        if not selected:
            messagebox.showwarning("Warnung", "Bitte wählen Sie mindestens eine Datei aus.")
            return
            
        if not self.cover_manager:
            messagebox.showwarning("Warnung", "Bitte scannen Sie zuerst ein Verzeichnis.")
            return
            
        self.status_var.set("Analysiere Cover...")
        
        # Threading für Cover-Analyse
        threading.Thread(target=self._load_covers_worker, args=(selected,), daemon=True).start()
        
    def remove_covers(self):
        """Cover entfernen für ausgewählte Dateien"""
        selected = self.get_selected_files()
        if not selected:
            messagebox.showwarning("Warnung", "Bitte wählen Sie mindestens eine Datei aus.")
            return
            
        result = messagebox.askyesno("Bestätigung", f"Cover von {len(selected)} Dateien entfernen?")
        if result:
            self.status_var.set("Entferne Cover...")
            
            # Threading für Cover-Entfernung
            threading.Thread(target=self._remove_covers_worker, args=(selected,), daemon=True).start()

    def _load_covers_worker(self, selected_files):
        """Worker-Thread für Cover-Laden"""
        try:
            successful = 0
            errors = 0
            
            for file_data in selected_files:
                try:
                    filepath = file_data.get('filepath')
                    filename = file_data.get('filename', 'Unbekannt')
                    
                    if not filepath:
                        print(f"⚠️ Kein Dateipfad für {filename}")
                        errors += 1
                        continue
                    
                    self.root.after(0, lambda f=filename: self.status_var.set(f"Lade Cover für: {f}..."))
                    
                    # Cover Manager für das Verzeichnis dieser spezifischen Datei erstellen
                    file_directory = os.path.dirname(filepath)
                    file_cover_manager = CoverManager(file_directory)
                    
                    # Cover-Analyse für dieses spezifische Verzeichnis durchführen
                    cover_info = file_cover_manager.analyze_directory_covers()
                    
                    print(f"🔍 Gefundene externe Cover für {filename}: {len(cover_info.external_cover_files)}")
                    if cover_info.external_cover_files:
                        print(f"📋 Cover-Dateien: {cover_info.external_cover_files}")
                    
                    # Prüfe, ob bereits Cover vorhanden
                    current_status = file_data.get('cover_status', 'Nein')
                    if current_status == 'Nein':
                        # Versuche externe Cover zu finden und zuzuweisen
                        if cover_info.external_cover_files:
                            # Nehme das erste verfügbare externe Cover
                            external_cover_path = cover_info.external_cover_files[0]
                            
                            # Finde die entsprechende CoverSource
                            cover_source = None
                            for source in cover_info.unique_covers:
                                if source.type == 'external' and external_cover_path in source.path:
                                    cover_source = source
                                    break
                            
                            if cover_source:
                                # Cover zu MP3 hinzufügen
                                try:
                                    result = file_cover_manager.apply_cover_to_directory(
                                        cover_source=cover_source,
                                        selected_files=[filepath]
                                    )
                                    
                                    if result.get('success', 0) > 0:
                                        # Status aktualisieren
                                        file_data['cover_status'] = f"E{cover_source.size[0]}px"
                                        self.root.after(0, lambda: self._update_file_in_table(file_data))
                                        successful += 1
                                        print(f"✅ Cover geladen für {filename}")
                                    else:
                                        print(f"⚠️ Cover konnte nicht angewendet werden für {filename}")
                                        print(f"   Ergebnis: {result}")
                                        errors += 1
                                except Exception as cover_error:
                                    print(f"⚠️ Fehler beim Anwenden des Covers für {filename}: {cover_error}")
                                    errors += 1
                            else:
                                # Versuche direkt mit Dateipfad zu arbeiten
                                try:
                                    from tagger.cover_manager import CoverSource
                                    from PIL import Image
                                    
                                    # Erstelle temporäre CoverSource
                                    img = Image.open(external_cover_path)
                                    temp_cover = CoverSource(
                                        type='external',
                                        path=external_cover_path,
                                        size=img.size,
                                        format=img.format,
                                        hash='temp',
                                        usage_count=0
                                    )
                                    
                                    result = file_cover_manager.apply_cover_to_directory(
                                        cover_source=temp_cover,
                                        selected_files=[filepath]
                                    )
                                    
                                    if result.get('success', 0) > 0:
                                        file_data['cover_status'] = f"E{img.size[0]}px"
                                        self.root.after(0, lambda: self._update_file_in_table(file_data))
                                        successful += 1
                                        print(f"✅ Cover geladen für {filename}")
                                    else:
                                        errors += 1
                                        print(f"⚠️ Cover konnte nicht angewendet werden für {filename}")
                                        print(f"   Ergebnis: {result}")
                                except Exception as direct_error:
                                    print(f"⚠️ Auch direkter Ansatz fehlgeschlagen für {filename}: {direct_error}")
                                    errors += 1
                        else:
                            print(f"⚠️ Keine externen Cover gefunden für {filename}")
                            errors += 1
                    else:
                        print(f"ℹ️ {filename} hat bereits Cover: {current_status}")
                        
                except Exception as e:
                    errors += 1
                    print(f"💥 Fehler beim Cover-Laden für {filename}: {str(e)}")
            
            # Abschlussmeldung
            self.root.after(0, lambda: self.status_var.set(f"Cover-Laden abgeschlossen: {successful} erfolgreich, {errors} Fehler"))
            self.root.after(0, lambda: messagebox.showinfo("Cover-Management", f"Cover-Laden abgeschlossen.\n\nErfolgreich: {successful}\nFehler: {errors}"))
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Fehler", f"Fehler beim Cover-Laden: {str(e)}"))
            self.root.after(0, lambda: self.status_var.set("Fehler beim Cover-Laden"))

    def _remove_covers_worker(self, selected_files):
        """Worker-Thread für Cover-Entfernung"""
        try:
            successful = 0
            errors = 0
            
            # Sammle alle Dateipfade
            file_paths = [file_data.get('filepath') for file_data in selected_files]
            
            # Entferne Cover von allen Dateien auf einmal
            result = self.cover_manager.remove_covers_from_files(file_paths)
            
            if result.get('success'):
                successful = result.get('files_processed', 0)
                errors = result.get('errors', 0)
                
                # Aktualisiere die Datei-Daten
                for file_data in selected_files:
                    file_data['cover_status'] = 'Nein'
                    self.root.after(0, lambda: self._update_file_in_table(file_data))
            else:
                errors = len(selected_files)
            
            # Abschlussmeldung
            self.root.after(0, lambda: self.status_var.set(f"Cover-Entfernung abgeschlossen: {successful} erfolgreich, {errors} Fehler"))
            self.root.after(0, lambda: messagebox.showinfo("Cover-Management", f"Cover-Entfernung abgeschlossen.\n\nErfolgreich: {successful}\nFehler: {errors}"))
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Fehler", f"Fehler beim Cover-Entfernen: {str(e)}"))
            self.root.after(0, lambda: self.status_var.set("Fehler beim Cover-Entfernen"))
        
    def enrich_with_lastfm(self):
        """Metadaten-Anreicherung mit Last.fm für ausgewählte Dateien"""
        selected = self.get_selected_files()
        if not selected:
            messagebox.showwarning("Warnung", "Bitte wählen Sie mindestens eine Datei aus.")
            return
            
        # Extended Metadata Service initialisieren wenn nötig
        if not self.extended_metadata:
            self.extended_metadata = ExtendedMetadataService()
            
            # Prüfe ob Service verfügbar ist
            if not self.extended_metadata.lastfm:
                messagebox.showerror("Fehler", "Last.fm API-Key nicht konfiguriert. Bitte in config.env eintragen.")
                return
        
        self.status_var.set("Starte Last.fm-Anreicherung...")
        
        # Threading für Metadaten-Anreicherung
        threading.Thread(target=self._enrich_metadata_worker, args=(selected, 'lastfm'), daemon=True).start()
        
    def enrich_with_musicbrainz(self):
        """Metadaten-Anreicherung mit MusicBrainz für ausgewählte Dateien"""
        selected = self.get_selected_files()
        if not selected:
            messagebox.showwarning("Warnung", "Bitte wählen Sie mindestens eine Datei aus.")
            return
            
        # Extended Metadata Service initialisieren wenn nötig
        if not self.extended_metadata:
            self.extended_metadata = ExtendedMetadataService()
            
            # Prüfe ob Service verfügbar ist
            if not self.extended_metadata.lastfm and not self.extended_metadata.spotify:
                messagebox.showerror("Fehler", "Keine Metadata-Services konfiguriert. Bitte API-Keys in config.env eintragen.")
                return
        
        self.status_var.set("Starte MusicBrainz-Anreicherung...")
        
        # Threading für Metadaten-Anreicherung
        threading.Thread(target=self._enrich_metadata_worker, args=(selected, 'musicbrainz'), daemon=True).start()
    
    def enrich_with_discogs(self):
        """Metadaten-Anreicherung mit Discogs für ausgewählte Dateien"""
        selected = self.get_selected_files()
        if not selected:
            messagebox.showwarning("Warnung", "Bitte wählen Sie mindestens eine Datei aus.")
            return
            
        # Extended Metadata Service initialisieren wenn nötig
        if not self.extended_metadata:
            self.extended_metadata = ExtendedMetadataService()
            
            # Prüfe ob Discogs Service verfügbar ist
            if not self.extended_metadata.discogs:
                messagebox.showerror("Fehler", "Discogs API-Token nicht konfiguriert. Bitte DISCOGS_API in config.env eintragen.")
                return
        
        self.status_var.set("Starte Discogs-Anreicherung...")
        
        # Threading für Metadaten-Anreicherung
        threading.Thread(target=self._enrich_metadata_worker, args=(selected, 'discogs'), daemon=True).start()
    
    def recognize_album(self):
        """Startet Album-Erkennung für ausgewählte Dateien"""
        selected = self.get_selected_files()
        if not selected:
            messagebox.showwarning("Warnung", "Bitte wählen Sie mindestens eine Datei aus.")
            return
        
        # Album Recognition Service initialisieren
        if not self.album_recognition:
            try:
                self.album_recognition = create_album_recognition_service()
            except Exception as e:
                messagebox.showerror("Fehler", f"Album-Erkennungs-Service konnte nicht initialisiert werden: {str(e)}")
                return
        
        # Worker-Thread starten
        self.update_status(f"Album-Erkennung für {len(selected)} Dateien gestartet...")
        threading.Thread(target=self._recognize_album_worker, args=(selected,), daemon=True).start()

    def _enrich_metadata_worker(self, selected_files, service_type):
        """Worker-Thread für Metadaten-Anreicherung"""
        from tagger.extended_metadata import get_extended_metadata_sync
        
        successful = 0
        errors = 0
        
        for i, file_data in enumerate(selected_files):
            try:
                filename = file_data.get('filename', 'Unbekannt')
                title = file_data.get('title', '')
                artist = file_data.get('artist', '')
                
                if not title or not artist:
                    print(f"⚠️ Überspringe {filename}: Titel oder Künstler fehlt")
                    errors += 1
                    continue
                
                self.root.after(0, lambda f=filename: self.status_var.set(f"Anreicherung für: {f}..."))
                
                # Metadaten-Anreicherung durchführen
                enriched_metadata = get_extended_metadata_sync(
                    artist=artist,
                    title=title,
                    album=file_data.get('album', '')
                )
                
                if enriched_metadata:
                    file_path = file_data.get('path')
                    
                    # Grunddaten aktualisieren und in pending_changes speichern
                    if enriched_metadata.genres and not file_data.get('genre'):
                        new_genre = ', '.join(enriched_metadata.genres[:3])  # Erste 3 Genres
                        file_data['genre'] = new_genre
                        
                        # In pending_changes speichern
                        if file_path not in self.pending_changes:
                            self.pending_changes[file_path] = {}
                        self.pending_changes[file_path]['genre'] = new_genre
                        print(f"📋 Genre gesetzt und vorgemerkt: {new_genre}")
                    
                    if enriched_metadata.release_date and not file_data.get('year'):
                        # Jahr aus release_date extrahieren
                        try:
                            year = enriched_metadata.release_date.split('-')[0]
                            if year.isdigit():
                                file_data['year'] = year
                                
                                # In pending_changes speichern
                                if file_path not in self.pending_changes:
                                    self.pending_changes[file_path] = {}
                                self.pending_changes[file_path]['year'] = year
                                print(f"📅 Jahr gesetzt und vorgemerkt: {year}")
                        except:
                            pass
                    
                    # Advanced Tags aktualisieren
                    advanced_data = {}
                    
                    # Mood
                    if enriched_metadata.mood:
                        advanced_data['mood'] = ', '.join(enriched_metadata.mood[:2])  # Erste 2 Moods
                    
                    # Audio Features
                    if enriched_metadata.audio_features:
                        af = enriched_metadata.audio_features
                        
                        # BPM/Tempo
                        if af.tempo and af.tempo > 0:
                            advanced_data['tempo'] = str(int(af.tempo))
                        
                        # Energy Level (0.0-1.0 → 1-10)
                        if af.energy is not None:
                            advanced_data['energy_level'] = str(int(af.energy * 10))
                        
                        # Danceability (0.0-1.0 → 1-10)
                        if af.danceability is not None:
                            advanced_data['danceability'] = str(int(af.danceability * 10))
                    
                    # Similar Artists
                    if enriched_metadata.similar_artists:
                        advanced_data['similar_artist'] = ', '.join(enriched_metadata.similar_artists[:3])
                        print(f"📋 Similar Artists gesetzt: {advanced_data['similar_artist']}")
                    
                    # Tags als Style verwenden
                    if enriched_metadata.tags:
                        # Filtere relevante Style-Tags
                        style_tags = [tag for tag in enriched_metadata.tags[:5] if len(tag) > 2]
                        if style_tags:
                            advanced_data['style'] = ', '.join(style_tags)
                            print(f"🎨 Style gesetzt: {advanced_data['style']}")
                            
                            # Mood aus Style-Tags ableiten
                            mood_mapping = {
                                'dance': 'Energetic',
                                'disco': 'Fun',
                                'pop': 'Upbeat',
                                'rock': 'Energetic', 
                                'ballad': 'Romantic',
                                'blues': 'Melancholic',
                                'jazz': 'Smooth',
                                'classical': 'Peaceful',
                                'electronic': 'Energetic',
                                'chill': 'Relaxed',
                                'ambient': 'Peaceful',
                                'sad': 'Melancholic',
                                'happy': 'Joyful',
                                'love': 'Romantic'
                            }
                            
                            # Suche nach Mood-Hinweisen in den Tags
                            detected_moods = []
                            for tag in style_tags:
                                tag_lower = tag.lower()
                                for keyword, mood in mood_mapping.items():
                                    if keyword in tag_lower and mood not in detected_moods:
                                        detected_moods.append(mood)
                            
                            if detected_moods:
                                advanced_data['mood'] = ', '.join(detected_moods[:2])  # Max 2 Moods
                                print(f"🎭 Mood abgeleitet: {advanced_data['mood']}")
                    
                    # Release Date als Erscheinungsjahr
                    if enriched_metadata.release_date:
                        try:
                            # Jahr aus verschiedenen Datumsformaten extrahieren
                            release_date = enriched_metadata.release_date
                            if release_date:
                                # Versuche verschiedene Formate
                                import re
                                year_match = re.search(r'(\d{4})', release_date)
                                if year_match:
                                    year = year_match.group(1)
                                    advanced_data['release_year'] = year
                                    print(f"📅 Release Year gesetzt: {advanced_data['release_year']}")
                                    
                                    # Era aus Jahr ableiten
                                    try:
                                        year_int = int(year)
                                        if year_int >= 2020:
                                            era = "2020s"
                                        elif year_int >= 2010:
                                            era = "2010s"
                                        elif year_int >= 2000:
                                            era = "2000s"
                                        elif year_int >= 1990:
                                            era = "1990s"
                                        elif year_int >= 1980:
                                            era = "1980s"
                                        elif year_int >= 1970:
                                            era = "1970s"
                                        elif year_int >= 1960:
                                            era = "1960s"
                                        else:
                                            era = f"{year_int//10*10}s"
                                        
                                        advanced_data['era'] = era
                                        print(f"🕰️ Era abgeleitet: {era}")
                                    except:
                                        pass
                        except Exception as e:
                            print(f"⚠️ Fehler bei Release Date: {e}")
                    
                    # Debug: Zeige alle advanced_data
                    print(f"🔍 Advanced Data für {file_data.get('filename', 'Unknown')}: {advanced_data}")
                    
                    # Advanced Tags in die file_data integrieren
                    if advanced_data:
                        if 'advanced_tags' not in file_data:
                            file_data['advanced_tags'] = {}
                        file_data['advanced_tags'].update(advanced_data)
                        
                        # GUI IMMER aktualisieren, wenn Advanced Tags empfangen werden
                        print(f"🔄 Aktualisiere GUI für Advanced Tags: {advanced_data}")
                        self.root.after(0, lambda ad=advanced_data, fd=file_data: self._update_advanced_tags_in_gui(ad, fd))
                        
                        # Zusätzlich prüfen ob es die aktuell ausgewählte Datei ist
                        current_selection = self.get_current_file_selection()
                        print(f"🔍 Current Selection: {current_selection.get('path') if current_selection else 'None'}")
                        print(f"🔍 File Data Path: {file_data.get('path')}")
                        
                        if current_selection and current_selection.get('path') == file_data.get('path'):
                            print(f"✅ Pfade stimmen überein - ist aktuell ausgewählte Datei")
                        else:
                            print(f"ℹ️ Pfade stimmen nicht überein - andere Datei angereichert")
                    
                    # UI aktualisieren
                    self.root.after(0, lambda: self._update_file_in_table(file_data))
                    successful += 1
                    
                    print(f"✅ {service_type} erfolgreich für {filename}")
                else:
                    errors += 1
                    print(f"❌ {service_type} fehlgeschlagen für {filename}")
                    
            except Exception as e:
                errors += 1
                print(f"💥 Fehler bei {filename}: {str(e)}")
        
        # Abschlussmeldung
        self.root.after(0, lambda: self.status_var.set(f"{service_type} abgeschlossen: {successful} erfolgreich, {errors} Fehler"))
        self.root.after(0, lambda: messagebox.showinfo("Metadaten-Anreicherung", f"{service_type} Anreicherung abgeschlossen.\n\nErfolgreich: {successful}\nFehler: {errors}"))

    def _recognize_album_worker(self, selected_files):
        """Worker-Thread für Album-Erkennung"""
        try:
            import asyncio
            
            successful = 0
            total = len(selected_files)
            
            # Erstelle Loop für asynchrone Verarbeitung
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            for i, file_data in enumerate(selected_files, 1):
                try:
                    self.root.after(0, lambda i=i, total=total: self.status_var.set(f"Album-Erkennung: {i}/{total}"))
                    
                    # Album-Erkennung durchführen
                    candidates, confidence = loop.run_until_complete(
                        self.album_recognition.recognize_album([file_data])
                    )
                    
                    if candidates and confidence > 0.7:  # Mindest-Konfidenz
                        best_candidate = candidates[0]
                        
                        # Album-Informationen anwenden
                        if best_candidate.title and not file_data.get('album'):
                            file_data['album'] = best_candidate.title
                        if best_candidate.artist and not file_data.get('albumartist'):
                            file_data['albumartist'] = best_candidate.artist
                        if best_candidate.year and not file_data.get('year'):
                            file_data['year'] = best_candidate.year
                        
                        # Track-Nummer aus Album-Info suchen
                        if best_candidate.tracks:
                            current_title = file_data.get('title', '').lower()
                            for track in best_candidate.tracks:
                                if track.get('title', '').lower() == current_title:
                                    if track.get('position') and not file_data.get('track'):
                                        file_data['track'] = str(track['position']).zfill(2)
                                    break
                        
                        # UI aktualisieren
                        self.root.after(0, lambda: self._update_file_in_table(file_data))
                        successful += 1
                        
                        print(f"✅ Album erkannt für {file_data['filename']}: {best_candidate.title} (Konfidenz: {confidence:.2f})")
                    else:
                        print(f"⚠️ Keine Album-Übereinstimmung für {file_data['filename']}")
                    
                except Exception as e:
                    print(f"💥 Fehler bei Album-Erkennung für {file_data['filename']}: {str(e)}")
            
            loop.close()
            
            # Erfolgsmeldung
            self.root.after(0, lambda: self.status_var.set(f"Album-Erkennung abgeschlossen: {successful}/{total}"))
            self.root.after(0, lambda: messagebox.showinfo("Album-Erkennung", 
                f"Album-Erkennung abgeschlossen.\n\nErfolgreich: {successful}/{total}"))
                
        except Exception as e:
            print(f"💥 Fehler bei Album-Erkennung: {str(e)}")
            self.root.after(0, lambda: messagebox.showerror("Fehler", f"Fehler bei der Album-Erkennung: {str(e)}"))
        finally:
            self.root.after(0, lambda: self.status_var.set("Bereit"))

    def auto_number_tracks(self):
        """Automatische Track-Nummerierung für ausgewählte Dateien"""
        selected = self.get_selected_files()
        if not selected:
            messagebox.showwarning("Warnung", "Bitte wählen Sie mindestens eine Datei aus.")
            return
        
        # Bestätigung vom Benutzer
        result = messagebox.askyesno("Track-Nummerierung", 
            f"Track-Nummern für {len(selected)} Dateien automatisch vergeben?\n\n"
            "Die Dateien werden in alphabetischer Reihenfolge nummeriert (01, 02, 03, ...)")
        
        if result:
            try:
                # Dateien nach Dateiname sortieren
                sorted_files = sorted(selected, key=lambda f: f['filename'])
                
                # Track-Nummern vergeben
                for i, file_data in enumerate(sorted_files, 1):
                    file_data['track'] = str(i).zfill(2)
                    # Checkbox aktivieren für veränderte Datei
                    item_id = file_data.get('item_id')
                    if item_id:
                        self.files_tree.set(item_id, 'selected', '✓')
                    # UI aktualisieren
                    self._update_file_in_table(file_data)
                
                self.update_selection_status()
                self.update_status(f"Track-Nummern für {len(selected)} Dateien vergeben")
                
            except Exception as e:
                messagebox.showerror("Fehler", f"Fehler bei der Track-Nummerierung: {str(e)}")

    def edit_selected_metadata(self):
        """Öffnet den Metadaten-Editor für ausgewählte Dateien"""
        selected = self.get_selected_files()
        if not selected:
            messagebox.showwarning("Warnung", "Bitte wählen Sie mindestens eine Datei aus.")
            return
            
        if len(selected) == 1:
            # Einzeldatei-Editor
            self.edit_single_file_metadata(selected[0])
        else:
            # Batch-Editor
            self.edit_batch_metadata(selected)

    def edit_single_file_metadata(self, file_data):
        """Öffnet den Einzeldatei-Metadaten-Editor"""
        try:
            editor = MetadataEditorDialog(self.root, file_data, self.mp3_processor)
            
            # Modal warten
            self.root.wait_window(editor.dialog)
            
            if editor.result:
                # Datei-Daten aktualisieren
                file_data.update(editor.result)
                
                # UI aktualisieren
                self._update_file_in_table(file_data)
                
                self.status_var.set(f"Metadaten für {file_data['filename']} aktualisiert")
                
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Öffnen des Metadaten-Editors: {str(e)}")

    def edit_batch_metadata(self, selected_files):
        """Öffnet den Batch-Metadaten-Editor"""
        try:
            editor = BatchMetadataEditorDialog(self.root, selected_files, self.mp3_processor)
            
            # Modal warten
            self.root.wait_window(editor.dialog)
            
            if editor.result:
                # Alle Dateien aktualisieren
                for i, file_data in enumerate(selected_files):
                    if i < len(editor.result):
                        file_data.update(editor.result[i])
                        
                        # UI aktualisieren
                        self._update_file_in_table(file_data)
                
                self.status_var.set(f"Metadaten für {len(selected_files)} Dateien aktualisiert")
                
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Öffnen des Batch-Editors: {str(e)}")

    def edit_file_metadata(self, event):
        """Öffnet den Metadaten-Editor für eine einzelne Datei (Doppelklick)"""
        item = self.files_tree.selection()[0] if self.files_tree.selection() else None
        if item:
            file_index = self.files_tree.index(item)
            if file_index < len(self.mp3_files):
                file_info = self.mp3_files[file_index]
                self.edit_single_file_metadata(file_info)

    def save_selected_files(self):
        """Speichert alle vorgemerkten Änderungen"""
        if not self.pending_changes:
            messagebox.showinfo("Info", "Keine Änderungen zum Speichern.")
            return
            
        # Bestätigung vom Benutzer
        total_files = len(self.pending_changes)
        total_changes = sum(len(changes) for changes in self.pending_changes.values())
        
        result = messagebox.askyesno("Änderungen speichern", 
            f"Sollen {total_changes} Änderungen in {total_files} Dateien gespeichert werden?\n\n"
            "Diese Aktion kann nicht rückgängig gemacht werden!")
        
        if result:
            self.status_var.set("Speichere Änderungen...")
            
            # Threading für Speichervorgang
            threading.Thread(target=self._save_pending_changes_worker, daemon=True).start()
        
    def _save_pending_changes_worker(self):
        """Worker-Thread für das Speichern von vorgemerkten Änderungen"""
        try:
            success_count = 0
            error_count = 0
            
            for file_path, changes in self.pending_changes.items():
                try:
                    # Metadaten in die MP3-Datei schreiben
                    from mutagen.mp3 import MP3
                    from mutagen.id3 import ID3, TIT2, TPE1, TALB, TDRC, TRCK, TCON
                    
                    # MP3-Datei laden
                    mp3_file = MP3(file_path)
                    
                    # Änderungen anwenden
                    if 'title' in changes:
                        mp3_file['TIT2'] = TIT2(encoding=3, text=changes['title'])
                    if 'artist' in changes:
                        mp3_file['TPE1'] = TPE1(encoding=3, text=changes['artist'])
                    if 'album' in changes:
                        mp3_file['TALB'] = TALB(encoding=3, text=changes['album'])
                    if 'year' in changes:
                        mp3_file['TDRC'] = TDRC(encoding=3, text=changes['year'])
                    if 'track' in changes:
                        mp3_file['TRCK'] = TRCK(encoding=3, text=changes['track'])
                    if 'genre' in changes:
                        mp3_file['TCON'] = TCON(encoding=3, text=changes['genre'])
                    
                    # Advanced Tags anwenden
                    if 'release_year' in changes:
                        from mutagen.id3 import TDRL
                        mp3_file['TDRL'] = TDRL(encoding=3, text=changes['release_year'])
                    if 'rating' in changes:
                        from mutagen.id3 import POPM
                        rating_value = int(float(changes['rating']) * 51) if changes['rating'].isdigit() else 0  # 0-5 -> 0-255
                        mp3_file['POPM'] = POPM(email="user@example.com", rating=rating_value, count=1)
                    if 'bpm' in changes:
                        from mutagen.id3 import TBPM
                        mp3_file['TBPM'] = TBPM(encoding=3, text=changes['bpm'])
                    if 'energy' in changes:
                        from mutagen.id3 import TXXX
                        mp3_file['TXXX:ENERGY'] = TXXX(encoding=3, desc='ENERGY', text=changes['energy'])
                    if 'danceability' in changes:
                        from mutagen.id3 import TXXX
                        mp3_file['TXXX:DANCEABILITY'] = TXXX(encoding=3, desc='DANCEABILITY', text=changes['danceability'])
                    if 'mood' in changes:
                        from mutagen.id3 import TXXX
                        mp3_file['TXXX:MOOD'] = TXXX(encoding=3, desc='MOOD', text=changes['mood'])
                    if 'similar_artist' in changes:
                        from mutagen.id3 import TXXX
                        mp3_file['TXXX:SIMILAR_ARTIST'] = TXXX(encoding=3, desc='SIMILAR_ARTIST', text=changes['similar_artist'])
                    if 'comment' in changes:
                        from mutagen.id3 import COMM
                        mp3_file['COMM::eng'] = COMM(encoding=3, lang='eng', desc='', text=changes['comment'])
                    
                    # Neue erweiterte Tags
                    if 'url' in changes:
                        from mutagen.id3 import TXXX
                        mp3_file['TXXX:URL'] = TXXX(encoding=3, desc='URL', text=changes['url'])
                    if 'era' in changes:
                        from mutagen.id3 import TXXX
                        mp3_file['TXXX:ERA'] = TXXX(encoding=3, desc='ERA', text=changes['era'])
                    if 'style' in changes:
                        from mutagen.id3 import TXXX
                        mp3_file['TXXX:STYLE'] = TXXX(encoding=3, desc='STYLE', text=changes['style'])
                    if 'energy_level' in changes:
                        from mutagen.id3 import TXXX
                        mp3_file['TXXX:ENERGY_LEVEL'] = TXXX(encoding=3, desc='ENERGY_LEVEL', text=changes['energy_level'])
                    if 'lyrics' in changes:
                        from mutagen.id3 import USLT
                        mp3_file['USLT::eng'] = USLT(encoding=3, lang='eng', desc='', text=changes['lyrics'])
                    
                    # Cover anwenden falls vorhanden
                    if 'cover' in changes:
                        from mutagen.id3 import APIC
                        
                        # MIME-Type aus Cover-Daten ermitteln
                        cover_data = changes['cover']
                        if isinstance(cover_data, tuple) and len(cover_data) == 2:
                            # Cover-Daten mit MIME-Type
                            mime_type, actual_data = cover_data
                        else:
                            # Legacy: Nur Cover-Daten, MIME-Type erraten
                            actual_data = cover_data
                            # MIME-Type basierend auf Datei-Header bestimmen
                            if actual_data.startswith(b'\xff\xd8\xff'):
                                mime_type = 'image/jpeg'
                            elif actual_data.startswith(b'\x89PNG'):
                                mime_type = 'image/png'
                            else:
                                mime_type = 'image/jpeg'  # Fallback
                        
                        print(f"💾 Speichere Cover ({mime_type}, {len(actual_data)} Bytes) in {os.path.basename(file_path)}")
                        
                        # Sicherstellen, dass ID3-Tags existieren
                        if mp3_file.tags is None:
                            mp3_file.add_tags()
                        
                        # Bestehende APIC-Tags entfernen
                        mp3_file.tags.delall('APIC')
                        
                        # Neues Cover hinzufügen
                        mp3_file.tags.add(APIC(
                            encoding=3,
                            mime=mime_type,
                            type=3,  # Cover (front)
                            desc='Cover',
                            data=actual_data
                        ))
                        
                        print(f"✅ Cover-Tag hinzugefügt, Tags gesamt: {len(mp3_file.tags)}")
                    
                    # Datei speichern
                    mp3_file.save()
                    success_count += 1
                    
                    print(f"✅ Gespeichert: {os.path.basename(file_path)}")
                    
                except Exception as e:
                    error_count += 1
                    print(f"❌ Fehler bei {os.path.basename(file_path)}: {e}")
            
            # UI-Updates im Hauptthread
            self.root.after(0, self._on_save_complete, success_count, error_count)
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Fehler", f"Fehler beim Speichern: {str(e)}"))
            self.root.after(0, lambda: self.status_var.set("Fehler beim Speichern"))
    
    def _on_save_complete(self, success_count, error_count):
        """Wird nach erfolgreichem Speichern aufgerufen"""
        # Vorgemerkte Änderungen leeren
        self.pending_changes.clear()
        self.changed_entry_fields.clear()
        
        # Tabellen-Markierungen entfernen
        self.clear_table_change_markers()
        
        # Metadaten-Panel aktualisieren (normale Schrift)
        if self.current_file_path:
            self.update_metadata_panel(self.current_file_path)
        
        # Dateitabelle aktualisieren (neues Scannen)
        if hasattr(self, 'current_directory') and self.current_directory.get():
            self.scan_directory()
        
        # Status und Meldung
        if error_count == 0:
            self.status_var.set(f"✅ {success_count} Dateien erfolgreich gespeichert")
            messagebox.showinfo("Erfolg", f"{success_count} Dateien erfolgreich gespeichert!")
        else:
            self.status_var.set(f"⚠️ {success_count} gespeichert, {error_count} Fehler")
            messagebox.showwarning("Teilweise erfolgreich", 
                f"{success_count} Dateien gespeichert\n{error_count} Dateien mit Fehlern")
        
        print(f"💾 Speichervorgang abgeschlossen: {success_count} erfolgreich, {error_count} Fehler")
    
    def clear_table_change_markers(self):
        """Entfernt alle Änderungs-Markierungen aus der Tabelle"""
        try:
            for dir_item in self.files_tree.get_children():
                for file_item in self.files_tree.get_children(dir_item):
                    # Text-Markierungen entfernen
                    current_text = self.files_tree.item(file_item, 'text')
                    if '⚠️' in current_text:
                        clean_text = current_text.replace('⚠️ ', '').replace(' ⚠️', '')
                        self.files_tree.item(file_item, text=clean_text)
                    
                    # Werte-Markierungen entfernen
                    values = list(self.files_tree.item(file_item, 'values'))
                    clean_values = []
                    for value in values:
                        if isinstance(value, str) and value.startswith('⚠️ '):
                            clean_values.append(value[3:])  # '⚠️ ' entfernen
                        else:
                            clean_values.append(value)
                    self.files_tree.item(file_item, values=tuple(clean_values))
        except Exception as e:
            print(f"🚨 Fehler beim Entfernen der Tabellen-Markierungen: {e}")
        
    def run(self):
        """Startet die Anwendung"""
        try:
            # Cleanup-Handler für ordnungsgemäße Beendigung
            self.root.protocol("WM_DELETE_WINDOW", self.cleanup_and_exit)
            self.root.mainloop()
        except KeyboardInterrupt:
            self.cleanup_and_exit()
    
    def cleanup_and_exit(self):
        """Räumt Ressourcen auf und beendet die Anwendung"""
        try:
            # Audio-Player beenden
            if self.audio_player_widget:
                self.audio_player_widget.destroy()
            
            # Weitere Cleanup-Operationen
            from tagger.audio_player import cleanup_audio_player
            cleanup_audio_player()
            
            print("🧹 Anwendung bereinigt")
        except Exception as e:
            print(f"🚨 Cleanup-Fehler: {e}")
        finally:
            self.root.destroy()

    def get_current_file_selection(self):
        """Gibt die aktuell in der GUI angezeigten Datei-Daten zurück"""
        print(f"🔍 get_current_file_selection: current_file_path = {getattr(self, 'current_file_path', 'NOT_SET')}")
        
        if not hasattr(self, 'current_file_path') or not self.current_file_path:
            print(f"🔍 Kein current_file_path gesetzt")
            return None
        
        # Suche die file_data für den aktuellen Pfad
        if hasattr(self, 'files_data') and self.files_data:
            print(f"🔍 Durchsuche {len(self.files_data)} files_data Einträge")
            for i, file_data in enumerate(self.files_data):
                file_path = file_data.get('path')
                print(f"🔍 [{i}] Vergleiche:\n    Current: '{self.current_file_path}'\n    Data:    '{file_path}'\n    Equal: {file_path == self.current_file_path}")
                if file_path == self.current_file_path:
                    print(f"🔍 Gefunden: {file_data.get('filename', 'Unknown')}")
                    return file_data
        else:
            print(f"🔍 Keine files_data verfügbar")
        
        print(f"🔍 Keine passende file_data gefunden")
        return None
    
    def _update_advanced_tags_in_gui(self, advanced_data, file_data=None):
        """Aktualisiert die Advanced Tags in der GUI mit angereicherten Daten"""
        try:
            print(f"🔄 GUI Update für Advanced Tags: {advanced_data}")
            print(f"🔄 Für Datei: {file_data.get('filename') if file_data else 'Unknown'}")
            
            # Prüfe ob die Datei gerade ausgewählt ist
            current_selection = self.get_current_file_selection()
            if file_data and current_selection and current_selection.get('path') != file_data.get('path'):
                print(f"ℹ️ Datei {file_data.get('filename')} ist nicht aktuell ausgewählt - GUI-Update übersprungen")
                return
                
            print(f"✅ Aktualisiere GUI für aktuell ausgewählte Datei")
            
            # Mapping von internen Namen zu GUI-Variablen
            gui_mapping = {
                'mood': self.metadata_mood,
                'danceability': self.metadata_danceability,
                'energy': self.metadata_energy,  # Energy hinzugefügt
                'energy_level': self.metadata_energy_level,
                'tempo': self.metadata_bpm,  # BPM wird als tempo geliefert
                'bpm': self.metadata_bpm,    # Direktes BPM Mapping
                'similar_artist': self.metadata_similar_artist,
                'style': self.metadata_style,
                'url': self.metadata_url,
                'era': self.metadata_era,
                'release_year': self.metadata_release_year,
                'rating': self.metadata_rating,  # Rating hinzugefügt
                'comment': self.metadata_comment,  # Comment hinzugefügt
                'lyrics': self.metadata_lyrics  # Lyrics hinzugefügt
            }
            
            # Mapping von internen Namen zu pending_changes Keys
            pending_mapping = {
                'mood': 'mood',
                'danceability': 'danceability',
                'energy': 'energy',  # Energy hinzugefügt
                'energy_level': 'energy_level',
                'tempo': 'bpm',  # BPM als tempo geliefert, aber als 'bpm' gespeichert
                'bpm': 'bpm',    # Direktes BPM Mapping
                'similar_artist': 'similar_artist',
                'style': 'style',
                'url': 'url',
                'era': 'era',
                'release_year': 'release_year',
                'rating': 'rating',  # Rating hinzugefügt
                'comment': 'comment',  # Comment hinzugefügt
                'lyrics': 'lyrics'  # Lyrics hinzugefügt
            }
            
            # Pfad für pending_changes bestimmen
            file_path = None
            if file_data:
                file_path = file_data.get('filepath') or file_data.get('path')  # Unterstütze beide Keys
            elif hasattr(self, 'current_file_path'):
                file_path = self.current_file_path
                
            # Advanced Tags setzen
            for field, value in advanced_data.items():
                if field in gui_mapping and value:
                    # GUI aktualisieren
                    gui_mapping[field].set(str(value))
                    print(f"✅ Advanced Tag gesetzt: {field} = {value}")
                    
                    # Pending changes aktualisieren (für Speichern)
                    if file_path and field in pending_mapping:
                        if file_path not in self.pending_changes:
                            self.pending_changes[file_path] = {}
                        self.pending_changes[file_path][pending_mapping[field]] = str(value)
                        print(f"💾 Pending change gesetzt: {pending_mapping[field]} = {value}")
                        
                elif field not in gui_mapping:
                    print(f"⚠️ Unmapped field: {field} = {value}")
                    
        except Exception as e:
            print(f"❌ Fehler beim Aktualisieren der Advanced Tags in GUI: {e}")


class CoverSelectionDialog:
    """Dialog zur Auswahl von Covern mit Vorschau"""
    
    def __init__(self, parent, filepath, filename, cover_manager, callback=None):
        self.parent = parent
        self.filepath = filepath
        self.filename = filename
        self.cover_manager = cover_manager
        self.callback = callback  # Callback-Funktion für Cover-Auswahl
        self.result = None
        self.cover_info = None
        self.cover_previews = {}  # Cache für Cover-Vorschauen
        
        # Dialog erstellen
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(f"Cover auswählen - {filename}")
        self.dialog.geometry("800x600")  # Größer für Vorschauen
        self.dialog.resizable(True, True)
        
        # Modal machen - mit Fehlerbehandlung
        self.dialog.transient(parent)
        try:
            self.dialog.grab_set()
        except tk.TclError:
            pass
        
        # Zentrieren
        self.center_dialog()
        
        # UI erstellen
        self.create_ui()
        
        # Cover laden
        self.load_covers()
        
    def center_dialog(self):
        """Zentriert den Dialog"""
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (self.dialog.winfo_width() // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")
        
    def create_ui(self):
        """Erstellt die Benutzeroberfläche mit Cover-Vorschau"""
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.dialog.columnconfigure(0, weight=1)
        self.dialog.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)  # Cover-Liste bekommt mehr Platz
        main_frame.rowconfigure(1, weight=1)
        
        # Titel
        title_label = ttk.Label(main_frame, text=f"Verfügbare Cover für: {self.filename}", 
                               font=('Arial', 12, 'bold'))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 10), sticky=tk.W)
        
        # Linke Seite: Cover-Vorschau
        preview_frame = ttk.LabelFrame(main_frame, text="Vorschau", padding="10")
        preview_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        preview_frame.columnconfigure(0, weight=1)
        
        # Cover-Vorschau-Label
        self.preview_label = ttk.Label(preview_frame, text="Kein Cover ausgewählt", 
                                      background='lightgray', anchor='center')
        self.preview_label.grid(row=0, column=0, pady=(0, 10), sticky=(tk.W, tk.E))
        
        # Cover-Details
        self.details_frame = ttk.Frame(preview_frame)
        self.details_frame.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        self.detail_labels = {}
        detail_fields = ['Typ:', 'Größe:', 'Format:', 'Quelle:']
        for i, field in enumerate(detail_fields):
            ttk.Label(self.details_frame, text=field, font=('Arial', 9, 'bold')).grid(
                row=i, column=0, sticky=tk.W, pady=1)
            label = ttk.Label(self.details_frame, text="-")
            label.grid(row=i, column=1, sticky=tk.W, padx=(10, 0), pady=1)
            self.detail_labels[field] = label
        
        # Rechte Seite: Cover-Liste
        list_frame = ttk.LabelFrame(main_frame, text="Verfügbare Cover", padding="10")
        list_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        # Treeview für Cover (vereinfacht)
        columns = ('type', 'size', 'source')
        self.covers_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=15)
        
        # Spalten konfigurieren
        self.covers_tree.heading('type', text='Typ')
        self.covers_tree.heading('size', text='Größe')
        self.covers_tree.heading('source', text='Quelle')
        
        self.covers_tree.column('type', width=80)
        self.covers_tree.column('size', width=100)
        self.covers_tree.column('source', width=200)
        
        # Selection-Event für Vorschau
        self.covers_tree.bind('<<TreeviewSelect>>', self.on_cover_select)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.covers_tree.yview)
        self.covers_tree.configure(yscrollcommand=v_scrollbar.set)
        
        self.covers_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        v_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=(10, 0), sticky=tk.E)
        
        ttk.Button(button_frame, text="Verwenden", command=self.select_cover).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Abbrechen", command=self.cancel).pack(side=tk.LEFT)
        
        # Status
        self.status_label = ttk.Label(main_frame, text="Lade Cover...")
        self.status_label.grid(row=3, column=0, columnspan=2, pady=(5, 0), sticky=tk.W)
        
    def load_covers(self):
        """Lädt verfügbare Cover mit Vorschau-Generierung"""
        try:
            print(f"🔍 Lade Cover für Dialog: {self.filename}")
            
            # Cover Manager für das Verzeichnis der Datei
            file_directory = os.path.dirname(self.filepath)
            file_cover_manager = CoverManager(file_directory)
            
            print(f"   Verzeichnis: {file_directory}")
            
            # Cover-Analyse durchführen
            self.cover_info = file_cover_manager.analyze_directory_covers()
            
            print(f"   Gefundene Cover: {len(self.cover_info.unique_covers)}")
            
            # Cover in Treeview anzeigen und Vorschauen erstellen
            for i, cover in enumerate(self.cover_info.unique_covers):
                print(f"   Cover {i+1}: {cover.type} - {cover.path} - {cover.size}")
                
                # Typ-Text optimieren
                type_map = {'internal': 'Intern', 'external': 'Extern', 'url': 'Online'}
                type_text = type_map.get(cover.type, cover.type.capitalize())
                
                # Quelle-Text kürzen
                if cover.type == 'external':
                    source_text = os.path.basename(cover.path)
                elif cover.type == 'url':
                    source_text = "Online-Cover"
                else:
                    source_text = "MP3-Datei"
                
                size_text = f"{cover.size[0]}×{cover.size[1]}px"
                
                # In Treeview einfügen
                item_id = self.covers_tree.insert('', 'end', values=(type_text, size_text, source_text))
                print(f"   TreeView Item-ID: {item_id}")
                
                # Vorschau-Thumbnail erstellen/laden
                self.create_cover_preview(cover, item_id)
            
            print(f"   Preview-Cache-Items: {len(self.cover_previews)}")
            
            # Status aktualisieren
            if self.cover_info.unique_covers:
                self.status_label.config(text=f"{len(self.cover_info.unique_covers)} Cover gefunden")
                # Erstes Cover automatisch auswählen
                if self.covers_tree.get_children():
                    first_item = self.covers_tree.get_children()[0]
                    self.covers_tree.selection_set(first_item)
                    self.covers_tree.focus(first_item)
                    self.on_cover_select(None)
                    print(f"   Erstes Cover automatisch ausgewählt: {first_item}")
            else:
                self.status_label.config(text="Keine Cover verfügbar")
                print("   ⚠️ Keine Cover verfügbar")
                
        except Exception as e:
            error_msg = f"Fehler beim Laden: {str(e)}"
            self.status_label.config(text=error_msg)
            print(f"💥 {error_msg}")
            import traceback
            traceback.print_exc()
    
    def create_cover_preview(self, cover, item_id):
        """Erstellt Vorschau-Thumbnail für ein Cover"""
        try:
            if cover.preview_data:
                # Bereits vorhandene Vorschau nutzen
                thumbnail_data = cover.preview_data
            else:
                # Neue Vorschau erstellen
                thumbnail_data = self.generate_thumbnail(cover)
            
            if thumbnail_data:
                # PIL Image aus Daten erstellen
                from PIL import Image, ImageTk
                import io
                
                image = Image.open(io.BytesIO(thumbnail_data))
                
                # Für tkinter optimieren (150x150 max)
                image.thumbnail((150, 150), Image.Resampling.LANCZOS)
                
                # Zu PhotoImage konvertieren
                photo = ImageTk.PhotoImage(image)
                
                # Im Cache speichern (wichtig: Referenz behalten!)
                self.cover_previews[item_id] = {
                    'photo': photo,
                    'cover': cover,
                    'image_data': thumbnail_data
                }
            
        except Exception as e:
            print(f"⚠️ Fehler beim Erstellen der Vorschau für {cover.path}: {e}")
    
    def generate_thumbnail(self, cover):
        """Generiert Thumbnail für Cover ohne preview_data"""
        try:
            from PIL import Image
            import io
            
            if cover.type == 'external':
                # Aus Datei laden
                with open(cover.path, 'rb') as f:
                    image_data = f.read()
            elif cover.type == 'internal':
                # Aus MP3 extrahieren
                from mutagen.mp3 import MP3
                audio = MP3(cover.path)
                if 'APIC:' in audio:
                    image_data = audio['APIC:'].data
                else:
                    # Suche nach anderen APIC Tags
                    apic_tags = [tag for tag in audio.tags.values() 
                               if hasattr(tag, 'type') and hasattr(tag, 'data')]
                    if apic_tags:
                        image_data = apic_tags[0].data
                    else:
                        return None
            elif cover.type == 'url':
                # Von URL laden (mit Timeout)
                import requests
                response = requests.get(cover.path, timeout=5)
                response.raise_for_status()
                image_data = response.content
            else:
                return None
            
            # Thumbnail erstellen
            image = Image.open(io.BytesIO(image_data))
            image.thumbnail((100, 100), Image.Resampling.LANCZOS)
            
            # Als JPEG bytes zurückgeben
            output = io.BytesIO()
            image.save(output, format='JPEG', quality=85)
            return output.getvalue()
            
        except Exception as e:
            print(f"⚠️ Fehler beim Generieren der Vorschau: {e}")
            return None
    
    def on_cover_select(self, event):
        """Wird aufgerufen wenn Cover ausgewählt wird - aktualisiert Vorschau"""
        selection = self.covers_tree.selection()
        if not selection:
            return
            
        item_id = selection[0]
        
        # Cover-Daten finden
        if item_id in self.cover_previews:
            preview_data = self.cover_previews[item_id]
            cover = preview_data['cover']
            photo = preview_data['photo']
            
            # Vorschau-Bild aktualisieren
            self.preview_label.config(image=photo, text="")
            self.preview_label.image = photo  # Referenz behalten!
            
            # Details aktualisieren
            type_map = {'internal': 'Intern (in MP3)', 'external': 'Extern (Datei)', 'url': 'Online (URL)'}
            self.detail_labels['Typ:'].config(text=type_map.get(cover.type, cover.type))
            self.detail_labels['Größe:'].config(text=f"{cover.size[0]} × {cover.size[1]} Pixel")
            self.detail_labels['Format:'].config(text=cover.format or "Unbekannt")
            
            # Quelle kürzen falls zu lang
            source_text = cover.path
            if len(source_text) > 40:
                source_text = "..." + source_text[-37:]
            self.detail_labels['Quelle:'].config(text=source_text)
        else:
            # Fallback: Kein Vorschau verfügbar
            self.preview_label.config(image="", text="Vorschau nicht verfügbar")
            if hasattr(self.preview_label, 'image'):
                delattr(self.preview_label, 'image')
                
            for label in self.detail_labels.values():
                label.config(text="-")
    
    def select_cover(self):
        """Wählt das ausgewählte Cover aus"""
        selection = self.covers_tree.selection()
        if not selection:
            messagebox.showwarning("Warnung", "Bitte wählen Sie ein Cover aus.")
            return
            
        print(f"🎯 Cover-Auswahl gestartet")
        print(f"   Selection: {selection}")
        
        # Cover aus Preview-Cache holen
        item_id = selection[0]
        print(f"   Item-ID: {item_id}")
        print(f"   Preview-Cache-Keys: {list(self.cover_previews.keys())}")
        
        if item_id in self.cover_previews:
            self.result = self.cover_previews[item_id]['cover']
            print(f"✅ Cover aus Preview-Cache geladen:")
            print(f"   Typ: {self.result.type}")
            print(f"   Pfad: {self.result.path}")
            print(f"   Größe: {self.result.size}")
        else:
            # Fallback: Index-basierte Auswahl
            print(f"⚠️ Fallback: Index-basierte Auswahl")
            item_index = self.covers_tree.index(item_id)
            print(f"   Item-Index: {item_index}")
            print(f"   Verfügbare Cover: {len(self.cover_info.unique_covers) if self.cover_info else 0}")
            
            if self.cover_info and item_index < len(self.cover_info.unique_covers):
                self.result = self.cover_info.unique_covers[item_index]
                print(f"✅ Cover über Index-Fallback geladen:")
                print(f"   Typ: {self.result.type}")
                print(f"   Pfad: {self.result.path}")
            else:
                print(f"❌ Ungültige Cover-Auswahl")
                messagebox.showerror("Fehler", "Ungültige Cover-Auswahl.")
                return
        
        # Callback aufrufen falls vorhanden
        if self.callback:
            print(f"📞 Callback wird aufgerufen...")
            self.callback(self.filepath, self.result)
        
        # Dialog schließen NACH erfolgreicher Auswahl
        print(f"🏁 Dialog wird geschlossen mit Ergebnis: {self.result}")
        self.dialog.destroy()
    
    def cancel(self):
        """Bricht die Auswahl ab"""
        print("❌ Cover-Auswahl abgebrochen")
        if self.callback:
            self.callback(self.filepath, None)
        self.result = None
        self.dialog.destroy()
    
    def show(self):
        """Zeigt den Dialog und wartet auf Ergebnis"""
        print(f"🎭 Cover-Dialog wird angezeigt für: {self.filename}")
        self.dialog.wait_window()
        print(f"📤 Dialog-Ergebnis: {self.result}")
        return self.result

def main():
    """Hauptfunktion"""
    app = MP3TaggerGUI()
    app.run()


if __name__ == "__main__":
    main()
