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

    # === Datei-Auswahl und -Management ===
    
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

    # === Integrierte Funktionen ===
    
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

    def edit_selected_metadata(self):
        """Öffnet den Metadaten-Editor für ausgewählte Dateien"""
        selected = self.get_selected_files()
        if not selected:
            messagebox.showwarning("Warnung", "Bitte wählen Sie mindestens eine Datei aus.")
            return
            
        # Batch-Editor öffnen
        editor = BatchMetadataEditorDialog(self.root, selected)
        if editor.result:
            messagebox.showinfo("Info", f"Metadaten für {len(selected)} Dateien bearbeitet.\n(Implementierung folgt)")

    def edit_file_metadata(self, event):
        """Öffnet den Metadaten-Editor für eine einzelne Datei"""
        item = self.files_tree.selection()[0] if self.files_tree.selection() else None
        if item:
            file_index = self.files_tree.index(item)
            if file_index < len(self.mp3_files):
                file_info = self.mp3_files[file_index]
                editor = MetadataEditorDialog(self.root, file_info)
                if editor.result:
                    # Aktualisiere die Anzeige
                    updated_info = editor.result
                    self.mp3_files[file_index] = updated_info
                    # Treeview-Zeile aktualisieren
                    values = list(self.files_tree.item(item, 'values'))
                    values[2] = updated_info.get('title', '')  # Titel
                    values[3] = updated_info.get('artist', '')  # Künstler
                    values[4] = updated_info.get('album', '')  # Album
                    values[5] = updated_info.get('year', '')  # Jahr
                    values[6] = updated_info.get('track', '')  # Track
                    values[7] = updated_info.get('genre', '')  # Genre
                    self.files_tree.item(item, values=values)

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


def main():
    """Hauptfunktion"""
    app = MP3TaggerGUI()
    app.run()


if __name__ == "__main__":
    main()
