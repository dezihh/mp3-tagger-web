"""
Metadaten-Editor Dialog für die Desktop-Anwendung
"""

import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path


class MetadataEditorDialog:
    """Dialog zum Bearbeiten von MP3-Metadaten"""
    
    def __init__(self, parent, file_info, mp3_processor):
        self.parent = parent
        self.file_info = file_info
        self.mp3_processor = mp3_processor
        self.result = None
        
        # Dialog erstellen
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(f"Metadaten bearbeiten - {file_info['filename']}")
        self.dialog.geometry("500x600")
        self.dialog.resizable(True, True)
        
        # Modal machen - mit Fehlerbehandlung
        self.dialog.transient(parent)
        try:
            self.dialog.grab_set()
        except tk.TclError:
            # Fallback wenn grab_set fehlschlägt
            pass
        
        # Zentrieren
        self.center_dialog()
        
        # UI erstellen
        self.create_ui()
        
        # Aktuelle Werte laden
        self.load_current_values()
        
    def center_dialog(self):
        """Zentriert den Dialog über dem Hauptfenster"""
        self.dialog.update_idletasks()
        x = self.parent.winfo_x() + (self.parent.winfo_width() // 2) - (500 // 2)
        y = self.parent.winfo_y() + (self.parent.winfo_height() // 2) - (600 // 2)
        self.dialog.geometry(f"500x600+{x}+{y}")
        
    def create_ui(self):
        """Erstellt die Benutzeroberfläche"""
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Datei-Info
        info_frame = ttk.LabelFrame(main_frame, text="Datei-Information", padding="10")
        info_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(info_frame, text=f"Datei: {self.file_info['filename']}", font=('Arial', 10, 'bold')).pack(anchor=tk.W)
        ttk.Label(info_frame, text=f"Pfad: {self.file_info['filepath']}").pack(anchor=tk.W)
        
        # Metadaten-Felder
        fields_frame = ttk.LabelFrame(main_frame, text="Metadaten", padding="10")
        fields_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        # Grid konfigurieren
        fields_frame.columnconfigure(1, weight=1)
        
        # Eingabefelder erstellen
        self.entries = {}
        fields = [
            ('title', 'Titel'),
            ('artist', 'Künstler'),
            ('album', 'Album'),
            ('year', 'Jahr'),
            ('track', 'Track-Nummer'),
            ('genre', 'Genre')
        ]
        
        for i, (field_name, field_label) in enumerate(fields):
            ttk.Label(fields_frame, text=f"{field_label}:").grid(row=i, column=0, sticky=tk.W, padx=(0, 10), pady=5)
            
            entry = ttk.Entry(fields_frame, width=50)
            entry.grid(row=i, column=1, sticky=(tk.W, tk.E), pady=5)
            self.entries[field_name] = entry
            
        # Cover-Information
        cover_frame = ttk.LabelFrame(main_frame, text="Cover-Information", padding="10")
        cover_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.cover_info_label = ttk.Label(cover_frame, text="")
        self.cover_info_label.pack(anchor=tk.W)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        ttk.Button(button_frame, text="Abbrechen", command=self.cancel).pack(side=tk.RIGHT, padx=(10, 0))
        ttk.Button(button_frame, text="Speichern", command=self.save).pack(side=tk.RIGHT)
        ttk.Button(button_frame, text="Zurücksetzen", command=self.reset).pack(side=tk.LEFT)
        
    def load_current_values(self):
        """Lädt die aktuellen Werte in die Eingabefelder"""
        for field_name, entry in self.entries.items():
            value = self.file_info.get(field_name, '')
            entry.delete(0, tk.END)
            entry.insert(0, str(value))
            
        # Cover-Info anzeigen
        cover_status = self.file_info.get('cover_status', 'Nein')
        self.cover_info_label.config(text=f"Cover-Status: {cover_status}")
        
    def reset(self):
        """Setzt alle Felder auf die ursprünglichen Werte zurück"""
        self.load_current_values()
        
    def save(self):
        """Speichert die Änderungen"""
        # Neue Metadaten sammeln
        new_metadata = {}
        for field_name, entry in self.entries.items():
            new_metadata[field_name] = entry.get().strip()
            
        # Validierung
        if not self.validate_metadata(new_metadata):
            return
            
        try:
            # Metadaten aktualisieren
            success = self.mp3_processor.update_file_metadata(
                self.file_info['filepath'], 
                new_metadata
            )
            
            if success:
                self.result = new_metadata
                messagebox.showinfo("Erfolg", "Metadaten erfolgreich gespeichert.")
                self.dialog.destroy()
            else:
                messagebox.showerror("Fehler", "Fehler beim Speichern der Metadaten.")
                
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Speichern: {str(e)}")
            
    def validate_metadata(self, metadata):
        """Validiert die eingegebenen Metadaten"""
        # Jahr validieren
        year = metadata.get('year', '').strip()
        if year and not year.isdigit():
            messagebox.showerror("Validierungsfehler", "Jahr muss eine Zahl sein.")
            return False
            
        # Track-Nummer validieren
        track = metadata.get('track', '').strip()
        if track and not track.isdigit():
            messagebox.showerror("Validierungsfehler", "Track-Nummer muss eine Zahl sein.")
            return False
            
        return True
        
    def cancel(self):
        """Bricht den Dialog ab"""
        self.dialog.destroy()
        
    def show(self):
        """Zeigt den Dialog an und wartet auf das Ergebnis"""
        self.dialog.wait_window()
        return self.result


class BatchMetadataEditorDialog:
    """Dialog zum Batch-Bearbeiten von Metadaten mehrerer Dateien"""
    
    def __init__(self, parent, files_info, mp3_processor):
        self.parent = parent
        self.files_info = files_info
        self.mp3_processor = mp3_processor
        self.result = None
        
        # Dialog erstellen
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(f"Batch-Metadaten bearbeiten - {len(files_info)} Dateien")
        self.dialog.geometry("600x500")
        self.dialog.resizable(True, True)
        
        # Modal machen - mit Fehlerbehandlung
        self.dialog.transient(parent)
        try:
            self.dialog.grab_set()
        except tk.TclError:
            # Fallback wenn grab_set fehlschlägt
            pass
        
        # Zentrieren
        self.center_dialog()
        
        # UI erstellen
        self.create_ui()
        
    def center_dialog(self):
        """Zentriert den Dialog über dem Hauptfenster"""
        self.dialog.update_idletasks()
        x = self.parent.winfo_x() + (self.parent.winfo_width() // 2) - (600 // 2)
        y = self.parent.winfo_y() + (self.parent.winfo_height() // 2) - (500 // 2)
        self.dialog.geometry(f"600x500+{x}+{y}")
        
    def create_ui(self):
        """Erstellt die Benutzeroberfläche"""
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Info
        info_label = ttk.Label(main_frame, 
                              text=f"Metadaten für {len(self.files_info)} ausgewählte Dateien bearbeiten",
                              font=('Arial', 12, 'bold'))
        info_label.pack(pady=(0, 20))
        
        # Warnung
        warning_frame = ttk.Frame(main_frame)
        warning_frame.pack(fill=tk.X, pady=(0, 20))
        
        warning_text = ("Hinweis: Nur ausgefüllte Felder werden auf alle ausgewählten Dateien angewendet. "
                       "Leere Felder bleiben unverändert.")
        warning_label = ttk.Label(warning_frame, text=warning_text, wraplength=550, 
                                 foreground="red", font=('Arial', 9))
        warning_label.pack()
        
        # Metadaten-Felder
        fields_frame = ttk.LabelFrame(main_frame, text="Metadaten (nur ausgefüllte Felder werden angewendet)", padding="10")
        fields_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        # Grid konfigurieren
        fields_frame.columnconfigure(1, weight=1)
        
        # Eingabefelder erstellen
        self.entries = {}
        fields = [
            ('title', 'Titel (wird für alle gleich gesetzt)'),
            ('artist', 'Künstler'),
            ('album', 'Album'),
            ('year', 'Jahr'),
            ('genre', 'Genre')
        ]
        
        for i, (field_name, field_label) in enumerate(fields):
            ttk.Label(fields_frame, text=f"{field_label}:").grid(row=i, column=0, sticky=tk.W, padx=(0, 10), pady=5)
            
            entry = ttk.Entry(fields_frame, width=50)
            entry.grid(row=i, column=1, sticky=(tk.W, tk.E), pady=5)
            self.entries[field_name] = entry
            
        # Fortschrittsbalken
        self.progress_frame = ttk.Frame(main_frame)
        self.progress_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.progress_label = ttk.Label(self.progress_frame, text="")
        self.progress_label.pack()
        
        self.progress_bar = ttk.Progressbar(self.progress_frame, mode='determinate')
        self.progress_bar.pack(fill=tk.X, pady=(5, 0))
        
        # Zunächst verstecken
        self.progress_frame.pack_forget()
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        ttk.Button(button_frame, text="Abbrechen", command=self.cancel).pack(side=tk.RIGHT, padx=(10, 0))
        self.save_button = ttk.Button(button_frame, text="Auf alle anwenden", command=self.save)
        self.save_button.pack(side=tk.RIGHT)
        
    def progress_callback(self, current, total, message):
        """Callback für Fortschrittsanzeige"""
        progress = (current / total) * 100
        self.progress_bar['value'] = progress
        self.progress_label.config(text=f"{message} ({current}/{total})")
        self.dialog.update()
        
    def save(self):
        """Wendet die Änderungen auf alle ausgewählten Dateien an"""
        # Nur ausgefüllte Felder sammeln
        new_metadata = {}
        for field_name, entry in self.entries.items():
            value = entry.get().strip()
            if value:  # Nur nicht-leere Werte
                new_metadata[field_name] = value
                
        if not new_metadata:
            messagebox.showwarning("Warnung", "Bitte füllen Sie mindestens ein Feld aus.")
            return
            
        # Bestätigung
        field_names = list(new_metadata.keys())
        result = messagebox.askyesno("Bestätigung", 
                                   f"Folgende Felder werden für {len(self.files_info)} Dateien aktualisiert:\n" +
                                   ", ".join(field_names) + "\n\nFortfahren?")
        if not result:
            return
            
        # Fortschrittsbalken anzeigen
        self.progress_frame.pack(fill=tk.X, pady=(0, 20))
        self.save_button.config(state='disabled')
        
        # Batch-Update durchführen
        file_metadata_pairs = [(file_info['filepath'], new_metadata) for file_info in self.files_info]
        
        try:
            import threading
            
            def update_worker():
                result = self.mp3_processor.batch_update_metadata(file_metadata_pairs, self.progress_callback)
                self.dialog.after(0, lambda: self.update_complete(result))
                
            thread = threading.Thread(target=update_worker, daemon=True)
            thread.start()
            
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Batch-Update: {str(e)}")
            self.progress_frame.pack_forget()
            self.save_button.config(state='normal')
            
    def update_complete(self, result):
        """Wird aufgerufen, wenn das Batch-Update abgeschlossen ist"""
        self.progress_frame.pack_forget()
        self.save_button.config(state='normal')
        
        success_rate = result['success_rate'] * 100
        message = (f"Batch-Update abgeschlossen:\n"
                  f"Erfolgreich: {result['successful_updates']}\n"
                  f"Fehlgeschlagen: {len(result['failed_updates'])}\n"
                  f"Erfolgsrate: {success_rate:.1f}%")
        
        if result['failed_updates']:
            message += f"\n\nFehlgeschlagene Dateien:\n" + "\n".join([Path(f).name for f in result['failed_updates'][:5]])
            if len(result['failed_updates']) > 5:
                message += f"\n... und {len(result['failed_updates']) - 5} weitere"
                
        messagebox.showinfo("Batch-Update abgeschlossen", message)
        
        if result['successful_updates'] > 0:
            self.result = result
            self.dialog.destroy()
            
    def cancel(self):
        """Bricht den Dialog ab"""
        self.dialog.destroy()
        
    def show(self):
        """Zeigt den Dialog an und wartet auf das Ergebnis"""
        self.dialog.wait_window()
        return self.result
