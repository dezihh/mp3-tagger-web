#!/usr/bin/env python3
"""
Startskript für die MP3 Tagger Desktop-Anwendung
"""

import sys
import os
from pathlib import Path

# Füge das Projektverzeichnis zum Python-Pfad hinzu
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

def check_dependencies():
    """Prüft, ob alle erforderlichen Abhängigkeiten installiert sind"""
    missing_deps = []
    
    try:
        import tkinter
    except ImportError:
        missing_deps.append("tkinter (meist mit Python installiert)")
        
    try:
        import mutagen
    except ImportError:
        missing_deps.append("mutagen")
        
    try:
        import PIL
    except ImportError:
        missing_deps.append("Pillow")
        
    try:
        import requests
    except ImportError:
        missing_deps.append("requests")
        
    if missing_deps:
        print("Fehlende Abhängigkeiten:")
        for dep in missing_deps:
            print(f"  - {dep}")
        print("\nInstallieren Sie diese mit:")
        print("pip install mutagen Pillow requests")
        return False
        
    return True

def check_gui_availability():
    """Prüft, ob GUI-Umgebung verfügbar ist"""
    try:
        import tkinter
        # Teste, ob ein Display verfügbar ist
        test_root = tkinter.Tk()
        test_root.withdraw()  # Verstecke das Test-Fenster
        test_root.destroy()
        return True
    except Exception as e:
        print(f"GUI nicht verfügbar: {e}")
        print("Hinweis: Für die Desktop-Anwendung wird eine grafische Umgebung benötigt.")
        print("Nutzen Sie alternativ die Web-Version mit: python app.py")
        return False
    missing_deps = []
    
    try:
        import tkinter
    except ImportError:
        missing_deps.append("tkinter (meist mit Python installiert)")
        
    try:
        import mutagen
    except ImportError:
        missing_deps.append("mutagen")
        
    try:
        import PIL
    except ImportError:
        missing_deps.append("Pillow")
        
    try:
        import requests
    except ImportError:
        missing_deps.append("requests")
        
    if missing_deps:
        print("Fehlende Abhängigkeiten:")
        for dep in missing_deps:
            print(f"  - {dep}")
        print("\nInstallieren Sie diese mit:")
        print("pip install mutagen Pillow requests")
        return False
        
    return True

def main():
    """Hauptfunktion"""
    print("MP3 Tagger Desktop-Anwendung wird gestartet...")
    
    # Abhängigkeiten prüfen
    if not check_dependencies():
        sys.exit(1)
        
    # GUI-Verfügbarkeit prüfen
    if not check_gui_availability():
        sys.exit(1)
        
    try:
        # GUI importieren und starten
        from mp3_tagger_gui import MP3TaggerGUI
        
        print("Lade Benutzeroberfläche...")
        app = MP3TaggerGUI()
        
        print("Anwendung bereit!")
        app.run()
        
    except ImportError as e:
        print(f"Fehler beim Importieren der Module: {e}")
        print("Stellen Sie sicher, dass Sie sich im richtigen Verzeichnis befinden.")
        sys.exit(1)
        
    except Exception as e:
        print(f"Unerwarteter Fehler: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
