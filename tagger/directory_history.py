"""
Verzeichnis-Historie Management für MP3 Tagger Web Application

Dieses Modul verwaltet die Historie der zuletzt verwendeten Verzeichnisse.
Es speichert die letzten 5 verwendeten Pfade persistent in einer JSON-Datei.

Verwendung:
    from tagger.directory_history import DirectoryHistory
    
    history = DirectoryHistory()
    history.add_directory("/path/to/music")
    recent_dirs = history.get_recent_directories()
"""

import json
import os
from typing import List, Dict, Optional
from datetime import datetime


class DirectoryHistory:
    """
    Verwaltet die Historie der zuletzt verwendeten MP3-Verzeichnisse.
    
    Die Historie wird in einer JSON-Datei persistent gespeichert und
    auf maximal 5 Einträge begrenzt. Neue Verzeichnisse werden an den
    Anfang der Liste gesetzt, doppelte Einträge werden vermieden.
    """
    
    def __init__(self, history_file: str = "directory_history.json", max_entries: int = 5):
        """
        Initialisiert die Verzeichnis-Historie.
        
        Args:
            history_file: Dateiname für die Historie-Speicherung
            max_entries: Maximale Anzahl der gespeicherten Verzeichnisse
        """
        self.history_file = history_file
        self.max_entries = max_entries
        self._history_path = self._get_history_path()
        
    def _get_history_path(self) -> str:
        """
        Ermittelt den vollständigen Pfad zur Historie-Datei.
        
        Returns:
            Absoluter Pfad zur Historie-Datei im Projekt-Verzeichnis
        """
        # Historie-Datei im Projektverzeichnis speichern
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(project_root, self.history_file)
    
    def load_history(self) -> List[Dict]:
        """
        Lädt die Historie aus der JSON-Datei.
        
        Returns:
            Liste mit Historie-Einträgen. Jeder Eintrag enthält:
            - path: Verzeichnispfad (absolut)
            - display_name: Benutzerfreundlicher Anzeigename
            - timestamp: ISO-Zeitstempel der letzten Verwendung
            - mp3_count: Anzahl der MP3-Dateien (falls bekannt)
        """
        try:
            if os.path.exists(self._history_path):
                with open(self._history_path, 'r', encoding='utf-8') as f:
                    history = json.load(f)
                    # Validiere und bereinige die Historie
                    return self._validate_history(history)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warnung: Historie konnte nicht geladen werden: {e}")
        
        return []
    
    def _validate_history(self, history: List[Dict]) -> List[Dict]:
        """
        Validiert und bereinigt Historie-Einträge.
        
        Args:
            history: Rohe Historie-Liste
            
        Returns:
            Bereinigte Historie-Liste mit nur existierenden Verzeichnissen
        """
        valid_entries = []
        for entry in history:
            if (isinstance(entry, dict) and 
                'path' in entry and 
                os.path.isdir(entry['path'])):
                # Stelle sicher, dass alle erforderlichen Felder vorhanden sind
                if 'display_name' not in entry:
                    entry['display_name'] = self._create_display_name(entry['path'])
                if 'timestamp' not in entry:
                    entry['timestamp'] = datetime.now().isoformat()
                valid_entries.append(entry)
        
        return valid_entries
    
    def save_history(self, history: List[Dict]) -> None:
        """
        Speichert die Historie in die JSON-Datei.
        
        Args:
            history: Liste mit Historie-Einträgen zum Speichern
        """
        try:
            os.makedirs(os.path.dirname(self._history_path), exist_ok=True)
            with open(self._history_path, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"Warnung: Historie konnte nicht gespeichert werden: {e}")
    
    def add_directory(self, directory_path: str, mp3_count: Optional[int] = None) -> None:
        """
        Fügt ein Verzeichnis zur Historie hinzu.
        
        Das neue Verzeichnis wird an den Anfang der Liste gesetzt.
        Wenn das Verzeichnis bereits existiert, wird es an die erste Position verschoben.
        Die Liste wird auf max_entries begrenzt.
        
        Args:
            directory_path: Absoluter Pfad zum hinzuzufügenden Verzeichnis
            mp3_count: Optionale Anzahl der MP3-Dateien im Verzeichnis
        """
        if not directory_path or not os.path.isdir(directory_path):
            return
            
        # Normalisiere den Pfad für konsistente Vergleiche
        normalized_path = os.path.normpath(os.path.abspath(directory_path))
        
        # Lade aktuelle Historie
        history = self.load_history()
        
        # Entferne vorhandenen Eintrag falls vorhanden
        history = [entry for entry in history if entry.get('path') != normalized_path]
        
        # Erstelle neuen Eintrag
        new_entry = {
            'path': normalized_path,
            'display_name': self._create_display_name(normalized_path),
            'timestamp': datetime.now().isoformat(),
        }
        
        if mp3_count is not None:
            new_entry['mp3_count'] = mp3_count
        
        # Füge an den Anfang hinzu und begrenze auf max_entries
        history.insert(0, new_entry)
        history = history[:self.max_entries]
        
        # Speichere aktualisierte Historie
        self.save_history(history)
    
    def get_recent_directories(self) -> List[Dict]:
        """
        Gibt die zuletzt verwendeten Verzeichnisse zurück.
        
        Returns:
            Liste der zuletzt verwendeten Verzeichnisse, sortiert nach Aktualität.
            Nur existierende Verzeichnisse werden zurückgegeben.
        """
        history = self.load_history()
        
        # Filtere nur existierende Verzeichnisse
        valid_history = [entry for entry in history if os.path.isdir(entry.get('path', ''))]
        
        # Speichere gefilterte Historie wenn sich etwas geändert hat
        if len(valid_history) != len(history):
            self.save_history(valid_history)
            
        return valid_history
    
    def _create_display_name(self, path: str) -> str:
        """
        Erstellt einen benutzerfreundlichen Anzeigenamen für einen Pfad.
        
        Args:
            path: Vollständiger Verzeichnispfad
            
        Returns:
            Benutzerfreundlicher Anzeigename
        """
        # Verwende die letzten 2 Pfad-Komponenten als Anzeigename
        path_parts = path.split(os.sep)
        if len(path_parts) >= 2:
            return os.path.join(path_parts[-2], path_parts[-1])
        else:
            return os.path.basename(path) or path
    
    def clear_history(self) -> None:
        """
        Löscht die komplette Historie.
        """
        if os.path.exists(self._history_path):
            try:
                os.remove(self._history_path)
            except IOError as e:
                print(f"Warnung: Historie konnte nicht gelöscht werden: {e}")


# Globale Instanz für die Anwendung (Singleton-Pattern)
_directory_history_instance: Optional[DirectoryHistory] = None


def get_directory_history() -> DirectoryHistory:
    """
    Gibt die globale DirectoryHistory-Instanz zurück (Singleton-Pattern).
    
    Returns:
        DirectoryHistory-Instanz für die Anwendung
    """
    global _directory_history_instance
    if _directory_history_instance is None:
        _directory_history_instance = DirectoryHistory()
    return _directory_history_instance
