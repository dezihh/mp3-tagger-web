"""
Flask Webserver für MP3 Tagger Web Application

Haupteinstiegspunkt der Webanwendung mit Historie-Funktionalität für
zuletzt verwendete Verzeichnisse und modularer MP3-Verzeichnis-Verarbeitung.
"""

from flask import Flask, render_template, request, redirect, url_for
import os
from tagger.directory_history import get_directory_history

app = Flask(__name__)

def is_valid_mp3_dir(path):
    """
    Prüft, ob das angegebene Verzeichnis existiert und MP3-Dateien enthält (rekursiv).
    
    Args:
        path: Pfad zum zu prüfenden Verzeichnis
        
    Returns:
        bool: True wenn Verzeichnis existiert und MP3-Dateien enthält, sonst False
    """
    if not path or not os.path.isdir(path):
        return False
        
    # Rekursive Suche nach MP3-Dateien
    for root, dirs, files in os.walk(path):
        for fname in files:
            if fname.lower().endswith('.mp3'):
                return True
    return False


def count_mp3_files(path):
    """
    Zählt die Anzahl der MP3-Dateien in einem Verzeichnis (rekursiv).
    
    Args:
        path: Pfad zum Verzeichnis
        
    Returns:
        int: Anzahl der gefundenen MP3-Dateien in allen Unterverzeichnissen
    """
    if not os.path.isdir(path):
        return 0
        
    count = 0
    for root, dirs, files in os.walk(path):
        for fname in files:
            if fname.lower().endswith('.mp3'):
                count += 1
    return count

@app.route('/', methods=['GET', 'POST'])
def index():
    """
    Einstiegsseite: Quellverzeichnis für MP3-Dateien eingeben.
    
    Unterstützt:
    - Manuelle Eingabe von Verzeichnispfaden
    - Historie der letzten 5 verwendeten Verzeichnisse mit One-Click-Auswahl
    - Automatische Pfad-Validierung und MP3-Zählung
    
    Returns:
        Gerenderte index.html Vorlage mit Historie und Fehlermeldungen
    """
    error = None
    mp3_dir = ''
    
    # Historie der letzten Verzeichnisse laden
    history = get_directory_history()
    recent_directories = history.get_recent_directories()
    
    if request.method == 'POST':
        mp3_dir = request.form.get('mp3_dir', '').strip()
        
        if not mp3_dir:
            error = 'Bitte geben Sie einen Verzeichnispfad an.'
        elif not is_valid_mp3_dir(mp3_dir):
            error = 'Ungültiges Verzeichnis oder keine MP3-Dateien gefunden.'
        else:
            # Absoluten Pfad sicherstellen
            abs_path = os.path.abspath(mp3_dir)
            
            # MP3-Dateien zählen und zur Historie hinzufügen
            mp3_count = count_mp3_files(abs_path)
            history.add_directory(abs_path, mp3_count)
            
            # Weiterleitung zur Ergebnisseite
            return redirect(url_for('results', mp3_dir=abs_path))
    
    return render_template('index.html', 
                         error=error, 
                         mp3_dir=mp3_dir,
                         recent_directories=recent_directories)

@app.route('/results')
def results():
    """
    Ergebnisseite nach Verzeichniswahl.
    
    Zeigt die gefundenen MP3-Dateien aus dem gewählten Verzeichnis an.
    
    Returns:
        Gerenderte results.html Vorlage oder Weiterleitung bei Fehlern
    """
    mp3_dir = request.args.get('mp3_dir', '')
    
    if not mp3_dir or not os.path.isdir(mp3_dir):
        return redirect(url_for('index', error='Verzeichnis nicht gefunden'))
    
    # Sammle MP3-Dateiformationen
    mp3_files = []
    mp3_count = 0
    
    try:
        for filename in os.listdir(mp3_dir):
            if filename.lower().endswith('.mp3'):
                file_path = os.path.join(mp3_dir, filename)
                mp3_files.append({
                    'name': filename,
                    'path': file_path,
                    'size': os.path.getsize(file_path)
                })
                mp3_count += 1
        
        # Sortiere nach Dateinamen
        mp3_files.sort(key=lambda x: x['name'].lower())
        
    except (OSError, PermissionError) as e:
        return redirect(url_for('index', error=f'Fehler beim Lesen des Verzeichnisses: {e}'))
    
    return render_template('results.html', 
                         mp3_dir=mp3_dir, 
                         mp3_files=mp3_files,
                         mp3_count=mp3_count)

if __name__ == '__main__':
    app.run(debug=True)
