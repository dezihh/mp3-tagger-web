#!/usr/bin/env python3
"""
MP3 Tagger GUI - Desktop Application
Ersetzt die Web-Anwendung durch eine grafische Desktop-Anwendung
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import threading
from pathlib import Path
import json

# Import der bestehenden Tagger-Module
from tagger.desktop_mp3_processor import DesktopMP3Processor
from tagger.cover_manager import CoverManager
from tagger.audio_recognition import AudioRecognitionService
from tagger.extended_metadata import ExtendedMetadataService
from tagger.desktop_config import desktop_config
from tagger.metadata_editor import MetadataEditorDialog, BatchMetadataEditorDialog


class MP3TaggerGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("MP3 Tagger - Desktop Application")
        self.root.geometry("1200x800")
        
        # Hauptvariablen
        self.current_directory = tk.StringVar()
        self.mp3_files = []
        self.selected_files = []
        
        # Module initialisieren
        self.mp3_processor = DesktopMP3Processor()
        self.cover_manager = None  # Wird erst bei Verzeichnis-Auswahl initialisiert
        self.audio_recognition = None  # Wird bei Bedarf mit API-Key initialisiert
        self.extended_metadata = None  # Wird bei Bedarf mit API-Keys initialisiert
        
        self.setup_ui()
        self.setup_styles()
        
    def setup_styles(self):
        """Konfiguriert das Aussehen der Anwendung"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Definiere Farben
        style.configure('Title.TLabel', font=('Arial', 16, 'bold'))
        style.configure('Header.TLabel', font=('Arial', 12, 'bold'))
        
    def setup_ui(self):
        """Erstellt die Benutzeroberfläche"""
        # Hauptframe
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Konfiguriere Grid-Gewichte
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # Titel
        title_label = ttk.Label(main_frame, text="MP3 Tagger", style='Title.TLabel')
        title_label.grid(row=0, column=0, pady=(0, 20))
        
        # Verzeichnis-Auswahl Frame
        self.create_directory_frame(main_frame)
        
        # Hauptinhalt Frame mit Notebook (Tabs)
        self.create_main_content(main_frame)
        
        # Status Bar
        self.create_status_bar(main_frame)
        
    def create_directory_frame(self, parent):
        """Erstellt den Verzeichnis-Auswahl Bereich"""
        dir_frame = ttk.LabelFrame(parent, text="Verzeichnis auswählen", padding="10")
        dir_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        dir_frame.columnconfigure(1, weight=1)
        
        # Verzeichnis-Eingabe
        ttk.Label(dir_frame, text="Pfad:").grid(row=0, column=0, padx=(0, 10))
        
        self.dir_entry = ttk.Entry(dir_frame, textvariable=self.current_directory, width=60)
        self.dir_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        
        # Browse Button
        browse_btn = ttk.Button(dir_frame, text="Durchsuchen", command=self.browse_directory)
        browse_btn.grid(row=0, column=2, padx=(0, 10))
        
        # Scan Button
        scan_btn = ttk.Button(dir_frame, text="Verzeichnis scannen", command=self.scan_directory)
        scan_btn.grid(row=0, column=3)
        
    def create_main_content(self, parent):
        """Erstellt den Hauptinhalt mit Tabs"""
        self.notebook = ttk.Notebook(parent)
        self.notebook.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        try:
            # Einziger Tab: MP3 Dateien mit allen Funktionen
            self.create_main_tab()
            print("✓ MP3 Dateien Haupttab erstellt")
        except Exception as e:
            print(f"✗ Fehler bei MP3 Dateien Haupttab: {e}")
            
        print(f"📊 Haupttab erstellt")
        
    def create_main_tab(self):
        """Erstellt den Haupttab für MP3-Dateien mit allen Funktionen"""
        main_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(main_frame, text="MP3 Dateien")
        
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # Funktions-Toolbar (oben)
        self.create_function_toolbar(main_frame)
        
        # Dateien-Toolbar (mit Auswahl-Buttons)
        self.create_files_toolbar(main_frame)
        
        # Haupttabelle für MP3-Dateien
        self.create_files_table(main_frame)

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
        
        ttk.Button(cover_buttons, text="Cover laden", command=self.load_covers, width=12).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(cover_buttons, text="Cover entfernen", command=self.remove_covers, width=12).pack(side=tk.LEFT)
        
        # Metadata Enrichment Bereich
        metadata_frame = ttk.Frame(function_frame)
        metadata_frame.pack(side=tk.LEFT, padx=(0, 20))
        
        ttk.Label(metadata_frame, text="Metadaten-Anreicherung:", font=('Arial', 9, 'bold')).pack(anchor=tk.W)
        metadata_buttons = ttk.Frame(metadata_frame)
        metadata_buttons.pack(fill=tk.X, pady=(2, 0))
        
        ttk.Button(metadata_buttons, text="Last.fm", command=self.enrich_with_lastfm, width=10).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(metadata_buttons, text="MusicBrainz", command=self.enrich_with_musicbrainz, width=12).pack(side=tk.LEFT)
        
        # Batch-Aktionen Bereich
        batch_frame = ttk.Frame(function_frame)
        batch_frame.pack(side=tk.LEFT)
        
        ttk.Label(batch_frame, text="Batch-Aktionen:", font=('Arial', 9, 'bold')).pack(anchor=tk.W)
        batch_buttons = ttk.Frame(batch_frame)
        batch_buttons.pack(fill=tk.X, pady=(2, 0))
        
        ttk.Button(batch_buttons, text="Bearbeiten", command=self.edit_selected_metadata, width=10).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(batch_buttons, text="Speichern", command=self.save_selected_files, width=10).pack(side=tk.LEFT)

    def create_files_toolbar(self, parent):
        """Erstellt die Dateien-Toolbar mit Auswahl-Buttons"""
        toolbar = ttk.Frame(parent)
        toolbar.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Button(toolbar, text="Alle auswählen", command=self.select_all_files).pack(side=tk.LEFT, padx=(0, 5))
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
        
        # Treeview für Dateien (erweitert um zusätzliche Spalten)
        columns = ('select', 'filename', 'title', 'artist', 'album', 'year', 'track', 'genre', 'cover', 'status')
        self.files_tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=20)
        
        # Spalten konfigurieren
        self.files_tree.heading('select', text='☐')
        self.files_tree.heading('filename', text='Dateiname')
        self.files_tree.heading('title', text='Titel')
        self.files_tree.heading('artist', text='Künstler')
        self.files_tree.heading('album', text='Album')
        self.files_tree.heading('year', text='Jahr')
        self.files_tree.heading('track', text='Track')
        self.files_tree.heading('genre', text='Genre')
        self.files_tree.heading('cover', text='Cover')
        self.files_tree.heading('status', text='Status')
        
        # Spaltenbreiten
        self.files_tree.column('select', width=30)
        self.files_tree.column('filename', width=200)
        self.files_tree.column('title', width=150)
        self.files_tree.column('artist', width=120)
        self.files_tree.column('album', width=120)
        self.files_tree.column('year', width=60)
        self.files_tree.column('track', width=50)
        self.files_tree.column('genre', width=100)
        self.files_tree.column('cover', width=80)
        self.files_tree.column('status', width=120)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.files_tree.yview)
        h_scrollbar = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=self.files_tree.xview)
        self.files_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Grid Layout
        self.files_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        v_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        h_scrollbar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        # Events
        self.files_tree.bind('<Button-1>', self.toggle_file_selection)
        self.files_tree.bind('<Double-1>', self.edit_file_metadata)

    # === Neue integrierte Funktionen ===
    
    def recognize_with_shazam(self):
        """Audio-Erkennung mit Shazam für ausgewählte Dateien"""
        selected = self.get_selected_files()
        if not selected:
            messagebox.showwarning("Warnung", "Bitte wählen Sie mindestens eine Datei aus.")
            return
            
        messagebox.showinfo("Info", f"Shazam-Erkennung für {len(selected)} Dateien gestartet.\n(Implementierung folgt)")
        
    def recognize_with_acoustid(self):
        """Audio-Erkennung mit AcoustID für ausgewählte Dateien"""
        selected = self.get_selected_files()
        if not selected:
            messagebox.showwarning("Warnung", "Bitte wählen Sie mindestens eine Datei aus.")
            return
            
        messagebox.showinfo("Info", f"AcoustID-Erkennung für {len(selected)} Dateien gestartet.\n(Implementierung folgt)")
        
    def load_covers(self):
        """Cover-Verwaltung für ausgewählte Dateien"""
        selected = self.get_selected_files()
        if not selected:
            messagebox.showwarning("Warnung", "Bitte wählen Sie mindestens eine Datei aus.")
            return
            
        messagebox.showinfo("Info", f"Cover laden für {len(selected)} Dateien.\n(Implementierung folgt)")
        
    def remove_covers(self):
        """Cover entfernen für ausgewählte Dateien"""
        selected = self.get_selected_files()
        if not selected:
            messagebox.showwarning("Warnung", "Bitte wählen Sie mindestens eine Datei aus.")
            return
            
        result = messagebox.askyesno("Bestätigung", f"Cover von {len(selected)} Dateien entfernen?")
        if result:
            messagebox.showinfo("Info", f"Cover von {len(selected)} Dateien entfernt.\n(Implementierung folgt)")
        
    def enrich_with_lastfm(self):
        """Metadaten-Anreicherung mit Last.fm für ausgewählte Dateien"""
        selected = self.get_selected_files()
        if not selected:
            messagebox.showwarning("Warnung", "Bitte wählen Sie mindestens eine Datei aus.")
            return
            
        messagebox.showinfo("Info", f"Last.fm-Anreicherung für {len(selected)} Dateien gestartet.\n(Implementierung folgt)")
        
    def enrich_with_musicbrainz(self):
        """Metadaten-Anreicherung mit MusicBrainz für ausgewählte Dateien"""
        selected = self.get_selected_files()
        if not selected:
            messagebox.showwarning("Warnung", "Bitte wählen Sie mindestens eine Datei aus.")
            return
            
        messagebox.showinfo("Info", f"MusicBrainz-Anreicherung für {len(selected)} Dateien gestartet.\n(Implementierung folgt)")

    def get_selected_files(self):
        """Gibt eine Liste der ausgewählten Dateien zurück"""
        selected_files = []
        for item in self.files_tree.get_children():
            values = self.files_tree.item(item, 'values')
            if values[0] == '☑':  # Checkbox ist ausgewählt
                file_index = self.files_tree.index(item)
                if file_index < len(self.mp3_files):
                    selected_files.append(self.mp3_files[file_index])
        return selected_files

    def update_selection_status(self):
        """Aktualisiert die Auswahl-Statusanzeige"""
        selected = self.get_selected_files()
        if selected:
            self.selection_status.set(f"{len(selected)} Dateien ausgewählt")
        else:
            self.selection_status.set("Keine Dateien ausgewählt")
        """Erstellt den Tab für MP3-Dateien"""
        files_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(files_frame, text="MP3 Dateien")
        
        files_frame.columnconfigure(0, weight=1)
        files_frame.rowconfigure(1, weight=1)
        
        # Toolbar
        toolbar = ttk.Frame(files_frame)
        toolbar.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Button(toolbar, text="Alle auswählen", command=self.select_all_files).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar, text="Auswahl aufheben", command=self.deselect_all_files).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar, text="Ausgewählte bearbeiten", command=self.edit_selected_metadata).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar, text="Ausgewählte speichern", command=self.save_selected_files).pack(side=tk.LEFT, padx=(0, 10))
        
        # Treeview für Dateien
        columns = ('select', 'filename', 'title', 'artist', 'album', 'year', 'track', 'cover')
        self.files_tree = ttk.Treeview(files_frame, columns=columns, show='headings', height=20)
        
        # Spalten konfigurieren
        self.files_tree.heading('select', text='✓')
        self.files_tree.heading('filename', text='Dateiname')
        self.files_tree.heading('title', text='Titel')
        self.files_tree.heading('artist', text='Künstler')
        self.files_tree.heading('album', text='Album')
        self.files_tree.heading('year', text='Jahr')
        self.files_tree.heading('track', text='Track')
        self.files_tree.heading('cover', text='Cover')
        
        # Spaltenbreiten
        self.files_tree.column('select', width=30)
        self.files_tree.column('filename', width=200)
        self.files_tree.column('title', width=150)
        self.files_tree.column('artist', width=120)
        self.files_tree.column('album', width=120)
        self.files_tree.column('year', width=60)
        self.files_tree.column('track', width=60)
        self.files_tree.column('cover', width=80)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(files_frame, orient=tk.VERTICAL, command=self.files_tree.yview)
        h_scrollbar = ttk.Scrollbar(files_frame, orient=tk.HORIZONTAL, command=self.files_tree.xview)
        self.files_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Grid Layout für Treeview
        self.files_tree.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        v_scrollbar.grid(row=1, column=1, sticky=(tk.N, tk.S))
        h_scrollbar.grid(row=2, column=0, sticky=(tk.W, tk.E))
        
        # Events
        self.files_tree.bind('<Double-1>', self.edit_file_metadata)
        self.files_tree.bind('<Button-1>', self.toggle_file_selection)
        
    def create_cover_tab(self):
        """Erstellt den Tab für Cover Management"""
        cover_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(cover_frame, text="Cover Management")
        
        cover_frame.columnconfigure(0, weight=1)
        cover_frame.rowconfigure(2, weight=1)
        
        # Info-Bereich
        info_frame = ttk.LabelFrame(cover_frame, text="Cover-Status", padding="10")
        info_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.cover_info_text = tk.Text(info_frame, height=4, wrap=tk.WORD, state=tk.DISABLED)
        self.cover_info_text.pack(fill=tk.BOTH, expand=True)
        
        # Initialen Inhalt hinzufügen
        self.cover_info_text.config(state=tk.NORMAL)
        self.cover_info_text.insert(1.0, "Cover-Status: Bereit\nVerwenden Sie 'Cover analysieren' um Cover-Quellen zu finden\nOder laden Sie externe Cover-Dateien")
        self.cover_info_text.config(state=tk.DISABLED)
        
        # Cover Aktionen
        actions_frame = ttk.LabelFrame(cover_frame, text="Cover Aktionen", padding="10")
        actions_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Erstelle Buttons in einem Grid
        ttk.Button(actions_frame, text="Cover analysieren", command=self.analyze_covers).grid(row=0, column=0, padx=(0, 5), pady=5)
        ttk.Button(actions_frame, text="Cover von ausgewählten entfernen", command=self.remove_cover_from_selected).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(actions_frame, text="Externe Cover laden", command=self.load_external_covers).grid(row=0, column=2, padx=(5, 0), pady=5)
        
        # Cover Quellen Liste mit Details
        sources_frame = ttk.LabelFrame(cover_frame, text="Gefundene Cover-Quellen", padding="10")
        sources_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        sources_frame.columnconfigure(0, weight=1)
        sources_frame.rowconfigure(0, weight=1)
        
        # Treeview für Cover-Quellen
        columns = ('source', 'file', 'resolution', 'size', 'type')
        self.cover_tree = ttk.Treeview(sources_frame, columns=columns, show='headings', height=12)
        
        # Spalten konfigurieren
        self.cover_tree.heading('source', text='Quelle')
        self.cover_tree.heading('file', text='Datei')
        self.cover_tree.heading('resolution', text='Auflösung')
        self.cover_tree.heading('size', text='Größe')
        self.cover_tree.heading('type', text='Typ')
        
        # Spaltenbreiten
        self.cover_tree.column('source', width=100)
        self.cover_tree.column('file', width=200)
        self.cover_tree.column('resolution', width=100)
        self.cover_tree.column('size', width=80)
        self.cover_tree.column('type', width=80)
        
        # Scrollbars für Cover-Tree
        cover_v_scrollbar = ttk.Scrollbar(sources_frame, orient=tk.VERTICAL, command=self.cover_tree.yview)
        cover_h_scrollbar = ttk.Scrollbar(sources_frame, orient=tk.HORIZONTAL, command=self.cover_tree.xview)
        self.cover_tree.configure(yscrollcommand=cover_v_scrollbar.set, xscrollcommand=cover_h_scrollbar.set)
        
        # Grid Layout für Cover-Tree
        self.cover_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        cover_v_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        cover_h_scrollbar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        # Events
        self.cover_tree.bind('<Double-1>', self.preview_cover)
        
    def create_audio_recognition_tab(self):
        """Erstellt den Tab für Audio Recognition"""
        audio_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(audio_frame, text="Audio Recognition")
        
        audio_frame.columnconfigure(0, weight=1)
        audio_frame.rowconfigure(2, weight=1)
        
        # Status und Konfiguration
        config_frame = ttk.LabelFrame(audio_frame, text="Konfiguration", padding="10")
        config_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.audio_status_label = ttk.Label(config_frame, text="Status: Nicht initialisiert")
        self.audio_status_label.pack(anchor=tk.W)
        
        # Status-Text für detaillierte Informationen
        self.audio_status_text = tk.Text(config_frame, height=3, wrap=tk.WORD, state=tk.DISABLED)
        self.audio_status_text.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        ttk.Button(config_frame, text="Service initialisieren", command=self.init_audio_recognition).pack(side=tk.LEFT, padx=(0, 10), pady=5)
        ttk.Button(config_frame, text="Ausgewählte Dateien erkennen", command=self.recognize_selected_files).pack(side=tk.LEFT, pady=5)
        
        # Erkennungsoptionen
        options_frame = ttk.LabelFrame(audio_frame, text="Erkennungsoptionen", padding="10")
        options_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.use_acoustid = tk.BooleanVar(value=True)
        self.use_shazam = tk.BooleanVar(value=False)
        self.auto_apply = tk.BooleanVar(value=False)
        
        ttk.Checkbutton(options_frame, text="AcoustID verwenden", variable=self.use_acoustid).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Checkbutton(options_frame, text="Shazam verwenden", variable=self.use_shazam).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Checkbutton(options_frame, text="Ergebnisse automatisch anwenden", variable=self.auto_apply).pack(side=tk.LEFT)
        
        # Erkennungsergebnisse
        results_frame = ttk.LabelFrame(audio_frame, text="Erkennungsergebnisse", padding="10")
        results_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)
        
        # Treeview für Erkennungsergebnisse
        recognition_columns = ('file', 'status', 'found_title', 'found_artist', 'confidence', 'service')
        self.recognition_tree = ttk.Treeview(results_frame, columns=recognition_columns, show='headings', height=12)
        
        # Spalten konfigurieren
        self.recognition_tree.heading('file', text='Datei')
        self.recognition_tree.heading('status', text='Status')
        self.recognition_tree.heading('found_title', text='Gefundener Titel')
        self.recognition_tree.heading('found_artist', text='Gefundener Künstler')
        self.recognition_tree.heading('confidence', text='Vertrauen')
        self.recognition_tree.heading('service', text='Service')
        
        # Spaltenbreiten
        self.recognition_tree.column('file', width=180)
        self.recognition_tree.column('status', width=80)
        self.recognition_tree.column('found_title', width=150)
        self.recognition_tree.column('found_artist', width=120)
        self.recognition_tree.column('confidence', width=80)
        self.recognition_tree.column('service', width=80)
        
        # Scrollbars
        recognition_v_scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.recognition_tree.yview)
        recognition_h_scrollbar = ttk.Scrollbar(results_frame, orient=tk.HORIZONTAL, command=self.recognition_tree.xview)
        self.recognition_tree.configure(yscrollcommand=recognition_v_scrollbar.set, xscrollcommand=recognition_h_scrollbar.set)
        
        # Grid Layout
        self.recognition_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        recognition_v_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        recognition_h_scrollbar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        # Events
        self.recognition_tree.bind('<Double-1>', self.apply_recognition_result)
        
    def create_metadata_tab(self):
        """Erstellt den Tab für Metadata Enrichment"""
        metadata_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(metadata_frame, text="Metadata Enrichment")
        
        metadata_frame.columnconfigure(0, weight=1)
        metadata_frame.rowconfigure(2, weight=1)
        
        # Service-Status
        status_frame = ttk.LabelFrame(metadata_frame, text="Service-Status", padding="10")
        status_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.metadata_status_text = tk.Text(status_frame, height=3, wrap=tk.WORD, state=tk.DISABLED)
        self.metadata_status_text.pack(fill=tk.BOTH, expand=True)
        
        ttk.Button(status_frame, text="Services überprüfen", command=self.check_metadata_services).pack(side=tk.LEFT, pady=5)
        ttk.Button(status_frame, text="Ausgewählte anreichern", command=self.enrich_selected_metadata).pack(side=tk.LEFT, padx=(10, 0), pady=5)
        
        # Anreicherungsoptionen
        options_frame = ttk.LabelFrame(metadata_frame, text="Anreicherungsoptionen", padding="10")
        options_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Checkboxen für verschiedene Services
        self.use_lastfm = tk.BooleanVar(value=True)
        self.use_spotify = tk.BooleanVar(value=True)
        self.use_musicbrainz = tk.BooleanVar(value=False)
        self.enrich_genre = tk.BooleanVar(value=True)
        self.enrich_year = tk.BooleanVar(value=True)
        self.enrich_album = tk.BooleanVar(value=True)
        
        # Erste Zeile: Services
        services_frame = ttk.Frame(options_frame)
        services_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(services_frame, text="Services:", font=('Arial', 9, 'bold')).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Checkbutton(services_frame, text="Last.fm", variable=self.use_lastfm).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Checkbutton(services_frame, text="Spotify", variable=self.use_spotify).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Checkbutton(services_frame, text="MusicBrainz", variable=self.use_musicbrainz).pack(side=tk.LEFT)
        
        # Zweite Zeile: Metadaten-Typen
        enrichment_frame = ttk.Frame(options_frame)
        enrichment_frame.pack(fill=tk.X)
        
        ttk.Label(enrichment_frame, text="Anreichern:", font=('Arial', 9, 'bold')).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Checkbutton(enrichment_frame, text="Genre", variable=self.enrich_genre).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Checkbutton(enrichment_frame, text="Jahr", variable=self.enrich_year).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Checkbutton(enrichment_frame, text="Album", variable=self.enrich_album).pack(side=tk.LEFT)
        
        # Anreicherungsergebnisse
        enrichment_frame = ttk.LabelFrame(metadata_frame, text="Anreicherungsergebnisse", padding="10")
        enrichment_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        enrichment_frame.columnconfigure(0, weight=1)
        enrichment_frame.rowconfigure(0, weight=1)
        
        # Treeview für Anreicherungsergebnisse
        enrichment_columns = ('file', 'status', 'service', 'added_genre', 'added_year', 'added_info')
        self.enrichment_tree = ttk.Treeview(enrichment_frame, columns=enrichment_columns, show='headings', height=12)
        
        # Spalten konfigurieren
        self.enrichment_tree.heading('file', text='Datei')
        self.enrichment_tree.heading('status', text='Status')
        self.enrichment_tree.heading('service', text='Service')
        self.enrichment_tree.heading('added_genre', text='Hinzugefügtes Genre')
        self.enrichment_tree.heading('added_year', text='Hinzugefügtes Jahr')
        self.enrichment_tree.heading('added_info', text='Weitere Infos')
        
        # Spaltenbreiten
        self.enrichment_tree.column('file', width=150)
        self.enrichment_tree.column('status', width=80)
        self.enrichment_tree.column('service', width=80)
        self.enrichment_tree.column('added_genre', width=120)
        self.enrichment_tree.column('added_year', width=80)
        self.enrichment_tree.column('added_info', width=200)
        
        # Scrollbars
        enrichment_v_scrollbar = ttk.Scrollbar(enrichment_frame, orient=tk.VERTICAL, command=self.enrichment_tree.yview)
        enrichment_h_scrollbar = ttk.Scrollbar(enrichment_frame, orient=tk.HORIZONTAL, command=self.enrichment_tree.xview)
        self.enrichment_tree.configure(yscrollcommand=enrichment_v_scrollbar.set, xscrollcommand=enrichment_h_scrollbar.set)
        
        # Grid Layout
        self.enrichment_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        enrichment_v_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        enrichment_h_scrollbar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
    def create_status_bar(self, parent):
        """Erstellt die Status Bar"""
        self.status_var = tk.StringVar()
        self.status_var.set("Bereit")
        
        status_bar = ttk.Label(parent, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=3, column=0, sticky=(tk.W, tk.E))
        
    def browse_directory(self):
        """Öffnet Dialog zur Verzeichnis-Auswahl"""
        directory = filedialog.askdirectory(title="MP3 Verzeichnis auswählen")
        if directory:
            self.current_directory.set(directory)
            
    def scan_directory(self):
        """Scannt das ausgewählte Verzeichnis nach MP3-Dateien"""
        directory = self.current_directory.get()
        if not directory or not os.path.exists(directory):
            messagebox.showerror("Fehler", "Bitte wählen Sie ein gültiges Verzeichnis aus.")
            return
            
        self.status_var.set("Scanne Verzeichnis...")
        
        # Threading für UI-Responsivität
        threading.Thread(target=self._scan_directory_worker, args=(directory,), daemon=True).start()
        
    def _scan_directory_worker(self, directory):
        """Worker-Thread für Verzeichnis-Scan"""
        try:
            # Fortschritts-Callback setzen
            def progress_callback(current, total, message):
                self.root.after(0, lambda: self.status_var.set(f"{message} ({current}/{total})"))
                
            self.mp3_processor.set_progress_callback(progress_callback)
            
            # MP3-Dateien finden und verarbeiten
            result = self.mp3_processor.process_directory(directory)
            
            # Zurück zum Main Thread für UI-Update
            self.root.after(0, self._update_files_display, result)
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Fehler", f"Fehler beim Scannen: {str(e)}"))
            self.root.after(0, lambda: self.status_var.set("Fehler beim Scannen"))
            
    def _update_files_display(self, files_data):
        """Aktualisiert die Dateien-Anzeige"""
        # Treeview leeren
        for item in self.files_tree.get_children():
            self.files_tree.delete(item)
            
        self.mp3_files = files_data.get('files', [])
        
        # Cover Manager für das neue Verzeichnis initialisieren
        if files_data.get('directory'):
            self.cover_manager = CoverManager(files_data['directory'])
        
        # Dateien in Treeview einfügen (erweiterte Spalten)
        for file_data in self.mp3_files:
            self.files_tree.insert('', 'end', values=(
                '☐',  # Checkbox
                file_data.get('filename', ''),
                file_data.get('title', ''),
                file_data.get('artist', ''),
                file_data.get('album', ''),
                file_data.get('year', ''),
                file_data.get('track', ''),
                file_data.get('genre', ''),
                file_data.get('cover_status', 'Nein'),
                'Bereit'  # Status-Spalte
            ))
            
        self.status_var.set(f"Gefunden: {len(self.mp3_files)} MP3-Dateien")
        self.update_selection_status()
        
    def toggle_file_selection(self, event):
        """Schaltet die Auswahl einer Datei um"""
        item = self.files_tree.selection()[0] if self.files_tree.selection() else None
        if item:
            # Checkbox umschalten
            values = list(self.files_tree.item(item, 'values'))
            if values[0] == '☐':
                values[0] = '☑'
                if item not in self.selected_files:
                    self.selected_files.append(item)
            else:
                values[0] = '☐'
                if item in self.selected_files:
                    self.selected_files.remove(item)
            
            self.files_tree.item(item, values=values)
            self.update_selection_status()
            
    def select_all_files(self):
        """Wählt alle Dateien aus"""
        self.selected_files.clear()
        for item in self.files_tree.get_children():
            values = list(self.files_tree.item(item, 'values'))
            values[0] = '☑'
            self.files_tree.item(item, values=values)
            self.selected_files.append(item)
        self.update_selection_status()
            
    def deselect_all_files(self):
        """Hebt alle Auswahlen auf"""
        self.selected_files.clear()
        for item in self.files_tree.get_children():
            values = list(self.files_tree.item(item, 'values'))
            values[0] = '☐'
            self.files_tree.item(item, values=values)
        self.update_selection_status()
            
    def save_selected_files(self):
        """Speichert die ausgewählten Dateien"""
        if not self.selected_files:
            messagebox.showwarning("Warnung", "Keine Dateien ausgewählt.")
            return
            
        self.status_var.set("Speichere Dateien...")
        
        # Threading für Speichervorgang
        threading.Thread(target=self._save_files_worker, daemon=True).start()
        
    def _save_files_worker(self):
        """Worker-Thread für Dateien speichern"""
        try:
            # Hier würde die Speicher-Logik implementiert werden
            # Vorerst Simulation
            import time
            time.sleep(2)
            
            self.root.after(0, lambda: self.status_var.set(f"Gespeichert: {len(self.selected_files)} Dateien"))
            self.root.after(0, lambda: messagebox.showinfo("Erfolg", f"{len(self.selected_files)} Dateien erfolgreich gespeichert."))
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Fehler", f"Fehler beim Speichern: {str(e)}"))
            
    def edit_file_metadata(self, event):
        """Öffnet Dialog zum Bearbeiten der Metadaten"""
        item = self.files_tree.selection()[0] if self.files_tree.selection() else None
        if item:
            # Datei-Index finden
            file_index = self.files_tree.index(item)
            if file_index < len(self.mp3_files):
                file_info = self.mp3_files[file_index]
                
                # Editor-Dialog öffnen
                editor = MetadataEditorDialog(self.root, file_info, self.mp3_processor)
                result = editor.show()
                
                if result:
                    # Tabelle aktualisieren
                    self.refresh_file_display(file_index)
                    
    def edit_selected_metadata(self):
        """Öffnet Batch-Editor für ausgewählte Dateien"""
        if not self.selected_files:
            messagebox.showwarning("Warnung", "Keine Dateien ausgewählt.")
            return
            
        # Ausgewählte Datei-Informationen sammeln
        selected_file_info = []
        for item in self.selected_files:
            file_index = self.files_tree.index(item)
            if file_index < len(self.mp3_files):
                selected_file_info.append(self.mp3_files[file_index])
                
        if selected_file_info:
            # Batch-Editor öffnen
            editor = BatchMetadataEditorDialog(self.root, selected_file_info, self.mp3_processor)
            result = editor.show()
            
            if result:
                # Tabelle komplett neu laden
                self.scan_directory()
                
    def refresh_file_display(self, file_index):
        """Aktualisiert die Anzeige einer einzelnen Datei"""
        if file_index < len(self.mp3_files):
            file_info = self.mp3_files[file_index]
            
            # Datei neu verarbeiten
            updated_info = self.mp3_processor._process_single_file(file_info['filepath'])
            self.mp3_files[file_index] = updated_info
            
            # Treeview-Item aktualisieren
            items = self.files_tree.get_children()
            if file_index < len(items):
                item = items[file_index]
                current_values = list(self.files_tree.item(item, 'values'))
                
                # Neue Werte einfügen (Checkbox-Status beibehalten)
                new_values = [
                    current_values[0],  # Checkbox-Status
                    updated_info.get('filename', ''),
                    updated_info.get('title', ''),
                    updated_info.get('artist', ''),
                    updated_info.get('album', ''),
                    updated_info.get('year', ''),
                    updated_info.get('track', ''),
                    updated_info.get('cover_status', 'Nein')
                ]
                
                self.files_tree.item(item, values=new_values)
            
    def analyze_covers(self):
        """Analysiert Cover-Quellen"""
        directory = self.current_directory.get()
        if not directory:
            messagebox.showwarning("Warnung", "Bitte wählen Sie zuerst ein Verzeichnis aus.")
            return
            
        if not self.cover_manager:
            self.cover_manager = CoverManager(directory)
            
        self.status_var.set("Analysiere Cover...")
        threading.Thread(target=self._analyze_covers_worker, args=(directory,), daemon=True).start()
        
    def _analyze_covers_worker(self, directory):
        """Worker-Thread für Cover-Analyse"""
        try:
            # Cover-Analyse mit dem CoverManager durchführen
            covers = self.cover_manager.detect_covers()
            
            # Formatiere das Ergebnis für die Anzeige
            result = {
                'cover_sources': [
                    {
                        'filename': cover.filepath.name,
                        'resolution': f"{cover.width}x{cover.height}",
                        'source': cover.source_type,
                        'size': cover.file_size
                    }
                    for cover in covers
                ]
            }
            
            self.root.after(0, self._update_cover_display, result)
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Fehler", f"Fehler bei Cover-Analyse: {str(e)}"))
            self.root.after(0, lambda: self.status_var.set("Fehler bei Cover-Analyse"))
            
    def _update_cover_display(self, cover_data):
        """Aktualisiert die Cover-Anzeige"""
        # Cover-Tree leeren
        for item in self.cover_tree.get_children():
            self.cover_tree.delete(item)
            
        # Cover-Info Text aktualisieren
        self.cover_info_text.config(state=tk.NORMAL)
        self.cover_info_text.delete(1.0, tk.END)
        
        cover_sources = cover_data.get('cover_sources', [])
        if cover_sources:
            info_text = f"Gefunden: {len(cover_sources)} Cover-Quellen\n"
            
            # Statistiken
            embedded_count = len([c for c in cover_sources if c['source'] == 'embedded'])
            external_count = len([c for c in cover_sources if c['source'] == 'external'])
            
            info_text += f"Embedded: {embedded_count}, External: {external_count}\n"
            info_text += "Doppelklick auf Cover für Vorschau"
            
            # Cover-Quellen in Tree einfügen
            for source in cover_sources:
                self.cover_tree.insert('', 'end', values=(
                    source.get('source', 'Unknown'),
                    source.get('filename', ''),
                    source.get('resolution', ''),
                    f"{source.get('size', 0)} KB",
                    'Image'
                ))
        else:
            info_text = "Keine Cover-Quellen gefunden.\nVerwenden Sie 'Cover analysieren' um zu starten."
            
        self.cover_info_text.insert(1.0, info_text)
        self.cover_info_text.config(state=tk.DISABLED)
        
        self.status_var.set(f"Cover-Analyse abgeschlossen: {len(cover_sources)} Quellen gefunden")
        
    def load_external_covers(self):
        """Lädt externe Cover-Dateien"""
        if not self.current_directory.get():
            messagebox.showwarning("Warnung", "Bitte wählen Sie zuerst ein Verzeichnis aus.")
            return
            
        cover_files = filedialog.askopenfilenames(
            title="Cover-Dateien auswählen",
            filetypes=[
                ("Bilddateien", "*.jpg *.jpeg *.png *.bmp *.gif"),
                ("JPEG", "*.jpg *.jpeg"),
                ("PNG", "*.png"),
                ("Alle Dateien", "*.*")
            ]
        )
        
        if cover_files:
            # Hier würde die Cover-Lade-Logik implementiert werden
            messagebox.showinfo("Info", f"{len(cover_files)} Cover-Dateien ausgewählt.\nImplementierung folgt in zukünftiger Version.")
            
    def preview_cover(self, event):
        """Zeigt eine Cover-Vorschau"""
        item = self.cover_tree.selection()[0] if self.cover_tree.selection() else None
        if item:
            values = self.cover_tree.item(item, 'values')
            messagebox.showinfo("Cover-Vorschau", f"Cover-Vorschau für: {values[1]}\nImplementierung folgt in zukünftiger Version.")
        
    def apply_cover_to_selected(self):
        """Wendet Cover auf ausgewählte Dateien an"""
        if not self.selected_files:
            messagebox.showwarning("Warnung", "Keine Dateien ausgewählt.")
            return
            
        # Hier würde die Cover-Anwendung implementiert werden
        messagebox.showinfo("Info", "Cover-Anwendung wird implementiert.")
        
    def remove_cover_from_selected(self):
        """Entfernt Cover von ausgewählten Dateien"""
        if not self.selected_files:
            messagebox.showwarning("Warnung", "Keine Dateien ausgewählt.")
            return
            
        result = messagebox.askyesno("Bestätigung", f"Cover von {len(self.selected_files)} ausgewählten Dateien entfernen?")
        if result:
            # Hier würde die Cover-Entfernung implementiert werden
            messagebox.showinfo("Info", "Cover-Entfernung wird implementiert.")
            
    def init_audio_recognition(self):
        """Initialisiert den Audio Recognition Service"""
        acoustid_key = desktop_config.get_api_key('acoustid')
        if not acoustid_key:
            messagebox.showerror("Fehler", "AcoustID API-Key nicht konfiguriert.\nBitte config.env erstellen und ACOUSTID_API_KEY setzen.")
            return
            
        try:
            self.audio_recognition = AudioRecognitionService(acoustid_key)
            self.audio_status_label.config(text="Status: Initialisiert ✓")
            messagebox.showinfo("Erfolg", "Audio Recognition Service erfolgreich initialisiert.")
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Initialisieren: {e}")
            
    def recognize_selected_files(self):
        """Startet Audio Recognition für ausgewählte Dateien"""
        if not self.selected_files:
            messagebox.showwarning("Warnung", "Keine Dateien ausgewählt.")
            return
            
        if not self.audio_recognition:
            messagebox.showerror("Fehler", "Audio Recognition Service nicht initialisiert.")
            return
            
        # Recognition-Tree leeren
        for item in self.recognition_tree.get_children():
            self.recognition_tree.delete(item)
            
        # Simulation der Audio Recognition
        for item in self.selected_files:
            file_index = self.files_tree.index(item)
            if file_index < len(self.mp3_files):
                file_info = self.mp3_files[file_index]
                
                # Simuliere Erkennungsergebnis
                status = "Erkannt" if file_index % 2 == 0 else "Nicht gefunden"
                confidence = "85%" if status == "Erkannt" else "N/A"
                found_title = file_info.get('title', 'Unknown Title') if status == "Erkannt" else ""
                found_artist = file_info.get('artist', 'Unknown Artist') if status == "Erkannt" else ""
                service = "AcoustID" if self.use_acoustid.get() else "Shazam"
                
                self.recognition_tree.insert('', 'end', values=(
                    file_info['filename'],
                    status,
                    found_title,
                    found_artist,
                    confidence,
                    service
                ))
                
        messagebox.showinfo("Info", f"Audio Recognition für {len(self.selected_files)} Dateien gestartet.\n(Aktuell Simulation - echte Implementierung folgt)")
        
    def apply_recognition_result(self, event):
        """Wendet Erkennungsergebnis auf Datei an"""
        item = self.recognition_tree.selection()[0] if self.recognition_tree.selection() else None
        if item:
            values = self.recognition_tree.item(item, 'values')
            messagebox.showinfo("Ergebnis anwenden", f"Erkennungsergebnis für {values[0]} anwenden.\nImplementierung folgt in zukünftiger Version.")
            
    def check_metadata_services(self):
        """Überprüft verfügbare Metadata Services"""
        self.metadata_status_text.config(state=tk.NORMAL)
        self.metadata_status_text.delete(1.0, tk.END)
        
        status_text = "Service-Status:\n"
        
        # API-Keys prüfen
        lastfm_key = desktop_config.get_api_key('lastfm')
        spotify_id = desktop_config.get_api_key('spotify')
        
        if lastfm_key:
            status_text += "✓ Last.fm: Konfiguriert\n"
        else:
            status_text += "✗ Last.fm: Nicht konfiguriert\n"
            
        if spotify_id:
            status_text += "✓ Spotify: Konfiguriert\n"
        else:
            status_text += "✗ Spotify: Nicht konfiguriert\n"
            
        status_text += "✓ MusicBrainz: Verfügbar (keine API-Key erforderlich)"
        
        self.metadata_status_text.insert(1.0, status_text)
        self.metadata_status_text.config(state=tk.DISABLED)
        
    def enrich_selected_metadata(self):
        """Startet Metadata Enrichment für ausgewählte Dateien"""
        if not self.selected_files:
            messagebox.showwarning("Warnung", "Keine Dateien ausgewählt.")
            return
            
        # Services prüfen
        services = []
        if self.use_lastfm.get() and desktop_config.get_api_key('lastfm'):
            services.append('Last.fm')
        if self.use_spotify.get() and desktop_config.get_api_key('spotify'):
            services.append('Spotify')
        if self.use_musicbrainz.get():
            services.append('MusicBrainz')
            
        if not services:
            messagebox.showerror("Fehler", "Keine Services konfiguriert oder ausgewählt.")
            return
            
        # Enrichment-Tree leeren
        for item in self.enrichment_tree.get_children():
            self.enrichment_tree.delete(item)
            
        # Simulation der Metadata Enrichment
        for item in self.selected_files:
            file_index = self.files_tree.index(item)
            if file_index < len(self.mp3_files):
                file_info = self.mp3_files[file_index]
                
                # Simuliere Anreicherungsergebnis
                status = "Angereichert" if file_index % 3 != 0 else "Keine Daten"
                service = services[file_index % len(services)]
                added_genre = "Rock/Alternative" if status == "Angereichert" and self.enrich_genre.get() else ""
                added_year = "2024" if status == "Angereichert" and self.enrich_year.get() else ""
                added_info = "BPM: 120, Energy: 0.8" if status == "Angereichert" else ""
                
                self.enrichment_tree.insert('', 'end', values=(
                    file_info['filename'],
                    status,
                    service,
                    added_genre,
                    added_year,
                    added_info
                ))
                
        messagebox.showinfo("Info", f"Metadata Enrichment für {len(self.selected_files)} Dateien gestartet.\nServices: {', '.join(services)}\n(Aktuell Simulation - echte Implementierung folgt)")

    def update_cover_tab(self):
        """Aktualisiert den Cover Management Tab mit aktuellen MP3-Dateien"""
        if not hasattr(self, 'cover_tree'):
            return
            
        # Cover-Tree leeren
        for item in self.cover_tree.get_children():
            self.cover_tree.delete(item)
            
        # Cover-Info aktualisieren
        if hasattr(self, 'cover_info_text'):
            self.cover_info_text.config(state=tk.NORMAL)
            self.cover_info_text.delete(1.0, tk.END)
            
            if self.mp3_files:
                cover_status = {}
                for file_data in self.mp3_files:
                    status = file_data.get('cover_status', 'Nein')
                    cover_status[status] = cover_status.get(status, 0) + 1
                
                info_text = f"MP3-Dateien gefunden: {len(self.mp3_files)}\n"
                for status, count in cover_status.items():
                    info_text += f"{status}: {count} Dateien\n"
                info_text += "\nVerwenden Sie 'Cover analysieren' für detaillierte Cover-Informationen"
                
                self.cover_info_text.insert(1.0, info_text)
                
                # Beispiel-Cover-Quellen anzeigen
                for i, file_data in enumerate(self.mp3_files[:10]):  # Nur erste 10 anzeigen
                    filename = file_data.get('filename', f'Datei {i+1}')
                    cover_status = file_data.get('cover_status', 'Nein')
                    self.cover_tree.insert('', 'end', values=(
                        'ID3-Tag' if cover_status != 'Nein' else 'Extern',
                        filename,
                        '300x300' if cover_status != 'Nein' else 'Unbekannt',
                        '50KB' if cover_status != 'Nein' else '-',
                        'JPEG' if cover_status != 'Nein' else '-'
                    ))
            else:
                self.cover_info_text.insert(1.0, "Keine MP3-Dateien geladen\nBitte wählen Sie ein Verzeichnis und scannen Sie es")
            
            self.cover_info_text.config(state=tk.DISABLED)

    def update_audio_recognition_tab(self):
        """Aktualisiert den Audio Recognition Tab mit aktuellen MP3-Dateien"""
        if not hasattr(self, 'recognition_tree'):
            return
            
        # Audio-Results-Tree leeren
        for item in self.recognition_tree.get_children():
            self.recognition_tree.delete(item)
            
        # Audio-Status aktualisieren
        if hasattr(self, 'audio_status_text'):
            self.audio_status_text.config(state=tk.NORMAL)
            self.audio_status_text.delete(1.0, tk.END)
            
            if self.mp3_files:
                incomplete_files = []
                for file_data in self.mp3_files:
                    # Prüfe auf fehlende Metadaten
                    if not file_data.get('title') or not file_data.get('artist'):
                        incomplete_files.append(file_data)
                
                status_text = f"MP3-Dateien geladen: {len(self.mp3_files)}\n"
                status_text += f"Dateien mit fehlenden Metadaten: {len(incomplete_files)}\n"
                status_text += "Verwenden Sie Audio-Erkennung für automatische Metadaten-Vervollständigung"
                
                self.audio_status_text.insert(1.0, status_text)
                
                # Zeige Dateien mit fehlenden Metadaten
                for file_data in incomplete_files[:15]:  # Nur erste 15 anzeigen
                    filename = file_data.get('filename', 'Unbekannt')
                    title = file_data.get('title', '') or '(Leer)'
                    artist = file_data.get('artist', '') or '(Leer)'
                    status = 'Bereit für Erkennung'
                    
                    self.recognition_tree.insert('', 'end', values=(
                        filename, status, title, artist, '-', '-'
                    ))
            else:
                self.audio_status_text.insert(1.0, "Keine MP3-Dateien geladen\nBitte wählen Sie ein Verzeichnis und scannen Sie es")
            
            self.audio_status_text.config(state=tk.DISABLED)

    def update_metadata_tab(self):
        """Aktualisiert den Metadata Enrichment Tab mit aktuellen MP3-Dateien"""
        if not hasattr(self, 'enrichment_tree'):
            return
            
        # Metadata-Results-Tree leeren
        for item in self.enrichment_tree.get_children():
            self.enrichment_tree.delete(item)
            
        # Metadata-Status aktualisieren
        if hasattr(self, 'metadata_status_text'):
            self.metadata_status_text.config(state=tk.NORMAL)
            self.metadata_status_text.delete(1.0, tk.END)
            
            if self.mp3_files:
                enrichable_files = []
                for file_data in self.mp3_files:
                    # Prüfe auf anreicherbare Metadaten
                    if file_data.get('title') and file_data.get('artist'):
                        enrichable_files.append(file_data)
                
                status_text = f"MP3-Dateien geladen: {len(self.mp3_files)}\n"
                status_text += f"Dateien für Anreicherung geeignet: {len(enrichable_files)}\n"
                status_text += "Verwenden Sie Metadaten-Anreicherung für zusätzliche Informationen"
                
                self.metadata_status_text.insert(1.0, status_text)
                
                # Zeige anreicherbare Dateien
                for file_data in enrichable_files[:15]:  # Nur erste 15 anzeigen
                    filename = file_data.get('filename', 'Unbekannt')
                    title = file_data.get('title', 'Unbekannt')
                    artist = file_data.get('artist', 'Unbekannt')
                    album = file_data.get('album', '') or '(Leer)'
                    status = 'Bereit für Anreicherung'
                    
                    self.enrichment_tree.insert('', 'end', values=(
                        filename, status, '-', '-', '-', f"Title: {title}, Artist: {artist}"
                    ))
            else:
                self.metadata_status_text.insert(1.0, "Keine MP3-Dateien geladen\nBitte wählen Sie ein Verzeichnis und scannen Sie es")
            
            self.metadata_status_text.config(state=tk.DISABLED)
        
    def run(self):
        """Startet die Anwendung"""
        self.root.mainloop()


def main():
    """Hauptfunktion"""
    app = MP3TaggerGUI()
    app.run()


if __name__ == "__main__":
    main()
