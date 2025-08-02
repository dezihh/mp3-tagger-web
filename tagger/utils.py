"""
Utility-Funktionen für MP3 Tagger Web Application

Gemeinsame Hilfsfunktionen für verschiedene Module.
"""

import os
from typing import List


def is_mp3_file(filename: str) -> bool:
    """
    Prüft, ob eine Datei eine MP3-Datei ist.
    
    Args:
        filename: Name der zu prüfenden Datei
        
    Returns:
        bool: True wenn die Datei eine .mp3 Endung hat
    """
    return filename.lower().endswith('.mp3')


def find_mp3_files_in_directory(directory: str) -> List[str]:
    """
    Findet alle MP3-Dateien in einem Verzeichnis (rekursiv).
    
    Args:
        directory: Pfad zum zu durchsuchenden Verzeichnis
        
    Returns:
        Liste der vollständigen Pfade zu allen gefundenen MP3-Dateien
    """
    mp3_files = []
    
    if not os.path.isdir(directory):
        return mp3_files
        
    for root, dirs, files in os.walk(directory):
        for filename in files:
            if is_mp3_file(filename):
                mp3_files.append(os.path.join(root, filename))
    
    return mp3_files


def count_mp3_files_in_directory(directory: str) -> int:
    """
    Zählt die Anzahl der MP3-Dateien in einem Verzeichnis (rekursiv).
    
    Args:
        directory: Pfad zum Verzeichnis
        
    Returns:
        int: Anzahl der gefundenen MP3-Dateien
    """
    return len(find_mp3_files_in_directory(directory))


def has_mp3_files(directory: str) -> bool:
    """
    Prüft, ob ein Verzeichnis MP3-Dateien enthält (rekursiv).
    
    Args:
        directory: Pfad zum zu prüfenden Verzeichnis
        
    Returns:
        bool: True wenn MP3-Dateien gefunden wurden
    """
    if not os.path.isdir(directory):
        return False
        
    # Optimierte Suche - stoppt bei der ersten gefundenen MP3-Datei
    for root, dirs, files in os.walk(directory):
        for filename in files:
            if is_mp3_file(filename):
                return True
    return False
