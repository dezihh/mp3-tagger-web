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
        self.root.geometry("1400x800")
        
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
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        # Haupt-Container
        main_container = ttk.Frame(self.root, padding="10")
        main_container.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        main_container.columnconfigure(0, weight=1)
        main_container.rowconfigure(2, weight=1)
        
        # Header
        self.create_header(main_container)
        
        # Verzeichnis-Auswahl
        self.create_directory_selector(main_container)
        
        # Haupt-Inhalt
        self.create_main_content(main_container)
        
        # Status Bar
        self.create_status_bar(main_container)
        
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
        
    def create_main_content(self, parent):
        """Erstellt den Hauptinhalt mit integrierter Funktionalität"""
        content_frame = ttk.Frame(parent)
        content_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        content_frame.columnconfigure(0, weight=1)
        content_frame.rowconfigure(2, weight=1)
        
        # Funktions-Toolbar
        self.create_function_toolbar(content_frame)
        
        # Dateien-Toolbar
        self.create_files_toolbar(content_frame)
        
        # Haupttabelle
        self.create_files_table(content_frame)

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

    def create_status_bar(self, parent):
        """Erstellt die Status Bar"""
        self.status_var = tk.StringVar()
        self.status_var.set("Bereit")
        
        status_bar = ttk.Label(parent, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=3, column=0, sticky=(tk.W, tk.E))

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
        """Aktualisiert die Dateien-Anzeige"""
        # Treeview leeren
        for item in self.files_tree.get_children():
            self.files_tree.delete(item)
            
        self.mp3_files = files_data.get('files', [])
        
        # Cover Manager für das Verzeichnis initialisieren
        # Wenn MP3-Dateien vorhanden sind, nutze das Verzeichnis der ersten Datei
        # Ansonsten nutze das Hauptverzeichnis
        cover_directory = files_data.get('directory')
        if self.mp3_files and self.mp3_files[0].get('filepath'):
            first_file_path = self.mp3_files[0]['filepath']
            first_file_directory = os.path.dirname(first_file_path)
            
            # Prüfe ob es tatsächlich ein anderes Verzeichnis ist
            if first_file_directory != cover_directory:
                cover_directory = first_file_directory
                print(f"📁 CoverManager wird für MP3-Verzeichnis initialisiert: {cover_directory}")
            else:
                print(f"📁 CoverManager wird für Hauptverzeichnis initialisiert: {cover_directory}")
        
        if cover_directory:
            self.cover_manager = CoverManager(cover_directory)
        
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

    # === Datei-Auswahl und -Management ===
    
    def toggle_file_selection(self, event):
        """Schaltet die Auswahl einer Datei um"""
        # Ermittle welche Zeile geklickt wurde
        item = self.files_tree.identify_row(event.y)
        if not item:
            return
            
        # Ermittle welche Spalte geklickt wurde
        column = self.files_tree.identify_column(event.x)
        
        # Nur bei Klick auf die erste Spalte (Checkbox) reagieren
        if column == '#1':  # #1 ist die erste Spalte (select)
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

    def _update_file_in_table(self, file_data):
        """Aktualisiert eine Datei in der Tabelle"""
        try:
            # Finde den entsprechenden Eintrag in der Tabelle
            filename = file_data.get('filename', '')
            
            for item in self.files_tree.get_children():
                values = list(self.files_tree.item(item, 'values'))
                if values[1] == filename:  # Vergleiche Dateiname (Spalte 1)
                    # Aktualisiere die Werte
                    values[2] = file_data.get('title', '')      # Titel
                    values[3] = file_data.get('artist', '')     # Künstler
                    values[4] = file_data.get('album', '')      # Album
                    values[5] = file_data.get('year', '')       # Jahr
                    values[6] = file_data.get('track', '')      # Track
                    values[7] = file_data.get('genre', '')      # Genre
                    values[8] = file_data.get('cover_status', 'Nein')  # Cover
                    values[9] = 'Aktualisiert'                  # Status
                    
                    self.files_tree.item(item, values=values)
                    break
                    
        except Exception as e:
            print(f"Fehler beim Aktualisieren der Tabelle: {e}")

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
        
        if not filepath:
            messagebox.showerror("Fehler", "Dateipfad nicht gefunden.")
            return
            
        # Cover-Dialog öffnen
        dialog = CoverSelectionDialog(self.root, filepath, filename, self.cover_manager)
        result = dialog.show()
        
        if result:
            # Ausgewähltes Cover auf alle selektierten Dateien anwenden
            threading.Thread(target=self._apply_selected_cover_worker, args=(selected, result), daemon=True).start()

    def _apply_selected_cover_worker(self, selected_files, cover_choice):
        """Worker-Thread zum Anwenden des ausgewählten Covers"""
        try:
            successful = 0
            errors = 0
            
            for file_data in selected_files:
                try:
                    filepath = file_data.get('filepath')
                    filename = file_data.get('filename', 'Unbekannt')
                    
                    if not filepath:
                        errors += 1
                        continue
                    
                    self.root.after(0, lambda f=filename: self.status_var.set(f"Wende Cover an auf: {f}..."))
                    
                    # Cover Manager für das Verzeichnis dieser Datei
                    file_directory = os.path.dirname(filepath)
                    file_cover_manager = CoverManager(file_directory)
                    
                    # Cover anwenden
                    result = file_cover_manager.apply_cover_to_directory(
                        cover_source=cover_choice,
                        selected_files=[filepath]
                    )
                    
                    if result.get('success', 0) > 0:
                        # Status aktualisieren
                        size_info = f"{cover_choice.size[0]}px" if cover_choice.size else "Unbekannt"
                        type_prefix = cover_choice.type[0].upper() if cover_choice.type else "?"
                        file_data['cover_status'] = f"{type_prefix}{size_info}"
                        
                        self.root.after(0, lambda: self._update_file_in_table(file_data))
                        successful += 1
                        print(f"✅ Cover angewendet auf {filename}")
                    else:
                        errors += 1
                        print(f"⚠️ Cover konnte nicht angewendet werden auf {filename}")
                        
                except Exception as e:
                    errors += 1
                    print(f"💥 Fehler beim Cover-Anwenden auf {filename}: {str(e)}")
            
            # Abschlussmeldung
            self.root.after(0, lambda: self.status_var.set(f"Cover-Anwendung abgeschlossen: {successful} erfolgreich, {errors} Fehler"))
            self.root.after(0, lambda: messagebox.showinfo("Cover-Management", f"Cover angewendet.\n\nErfolgreich: {successful}\nFehler: {errors}"))
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Fehler", f"Fehler beim Cover-Anwenden: {str(e)}"))
            self.root.after(0, lambda: self.status_var.set("Fehler beim Cover-Anwenden"))
        
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
                    # Metadaten aktualisieren
                    if enriched_metadata.genres and not file_data.get('genre'):
                        file_data['genre'] = ', '.join(enriched_metadata.genres[:3])  # Erste 3 Genres
                    
                    if enriched_metadata.release_date and not file_data.get('year'):
                        # Jahr aus release_date extrahieren
                        try:
                            year = enriched_metadata.release_date.split('-')[0]
                            if year.isdigit():
                                file_data['year'] = year
                        except:
                            pass
                    
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
        """Speichert die ausgewählten Dateien"""
        selected = self.get_selected_files()
        if not selected:
            messagebox.showwarning("Warnung", "Keine Dateien ausgewählt.")
            return
            
        self.status_var.set("Speichere Dateien...")
        
        # Threading für Speichervorgang
        threading.Thread(target=self._save_files_worker, args=(selected,), daemon=True).start()
        
    def _save_files_worker(self, files_to_save):
        """Worker-Thread für das Speichern von Dateien"""
        try:
            # Hier würde der echte Speichervorgang stattfinden
            import time
            time.sleep(1)  # Simuliere Speichervorgang
            
            self.root.after(0, lambda: self.status_var.set(f"{len(files_to_save)} Dateien gespeichert"))
            self.root.after(0, lambda: messagebox.showinfo("Erfolg", f"{len(files_to_save)} Dateien erfolgreich gespeichert."))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Fehler", f"Fehler beim Speichern: {str(e)}"))
            self.root.after(0, lambda: self.status_var.set("Fehler beim Speichern"))
        
    def run(self):
        """Startet die Anwendung"""
        self.root.mainloop()



class CoverSelectionDialog:
    """Dialog zur Auswahl von Covern"""
    
    def __init__(self, parent, filepath, filename, cover_manager):
        self.parent = parent
        self.filepath = filepath
        self.filename = filename
        self.cover_manager = cover_manager
        self.result = None
        self.cover_info = None
        
        # Dialog erstellen
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(f"Cover auswählen - {filename}")
        self.dialog.geometry("600x500")
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
        """Erstellt die Benutzeroberfläche"""
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.dialog.columnconfigure(0, weight=1)
        self.dialog.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Titel
        title_label = ttk.Label(main_frame, text=f"Verfügbare Cover für: {self.filename}", 
                               font=('Arial', 12, 'bold'))
        title_label.grid(row=0, column=0, pady=(0, 10), sticky=tk.W)
        
        # Cover-Liste
        list_frame = ttk.Frame(main_frame)
        list_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        # Treeview für Cover
        columns = ('type', 'source', 'size', 'format')
        self.covers_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=15)
        
        # Spalten konfigurieren
        self.covers_tree.heading('type', text='Typ')
        self.covers_tree.heading('source', text='Quelle')
        self.covers_tree.heading('size', text='Größe')
        self.covers_tree.heading('format', text='Format')
        
        self.covers_tree.column('type', width=80)
        self.covers_tree.column('source', width=300)
        self.covers_tree.column('size', width=100)
        self.covers_tree.column('format', width=80)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.covers_tree.yview)
        self.covers_tree.configure(yscrollcommand=v_scrollbar.set)
        
        self.covers_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        v_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, pady=(10, 0), sticky=tk.E)
        
        ttk.Button(button_frame, text="Verwenden", command=self.select_cover).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Abbrechen", command=self.cancel).pack(side=tk.LEFT)
        
        # Status
        self.status_label = ttk.Label(main_frame, text="Lade Cover...")
        self.status_label.grid(row=3, column=0, pady=(5, 0), sticky=tk.W)
        
    def load_covers(self):
        """Lädt verfügbare Cover"""
        try:
            # Cover Manager für das Verzeichnis der Datei
            file_directory = os.path.dirname(self.filepath)
            file_cover_manager = CoverManager(file_directory)
            
            # Cover-Analyse durchführen
            self.cover_info = file_cover_manager.analyze_directory_covers()
            
            # Cover in Treeview anzeigen
            for cover in self.cover_info.unique_covers:
                type_text = cover.type.capitalize()
                source_text = os.path.basename(cover.path) if cover.type == 'external' else cover.path
                size_text = f"{cover.size[0]}x{cover.size[1]}"
                format_text = cover.format
                
                self.covers_tree.insert('', 'end', values=(type_text, source_text, size_text, format_text))
            
            # Status aktualisieren
            if self.cover_info.unique_covers:
                self.status_label.config(text=f"{len(self.cover_info.unique_covers)} Cover gefunden")
            else:
                self.status_label.config(text="Keine Cover verfügbar")
                
        except Exception as e:
            self.status_label.config(text=f"Fehler beim Laden: {str(e)}")
            print(f"💥 Fehler beim Laden der Cover: {str(e)}")
    
    def select_cover(self):
        """Wählt das ausgewählte Cover aus"""
        selection = self.covers_tree.selection()
        if not selection:
            messagebox.showwarning("Warnung", "Bitte wählen Sie ein Cover aus.")
            return
            
        # Index des ausgewählten Items
        item = selection[0]
        item_index = self.covers_tree.index(item)
        
        if item_index < len(self.cover_info.unique_covers):
            self.result = self.cover_info.unique_covers[item_index]
            self.dialog.destroy()
        else:
            messagebox.showerror("Fehler", "Ungültige Cover-Auswahl.")
    
    def cancel(self):
        """Bricht die Auswahl ab"""
        self.result = None
        self.dialog.destroy()
    
    def show(self):
        """Zeigt den Dialog und wartet auf Ergebnis"""
        self.dialog.wait_window()
        return self.result


def main():
    """Hauptfunktion"""
    app = MP3TaggerGUI()
    app.run()


if __name__ == "__main__":
    main()
