"""
Flask Webserver für MP3 Tagger Web Application

Haupteinstiegspunkt der Webanwendung mit Historie-Funktionalität für
zuletzt verwendete Verzeichnisse und modularer MP3-Verzeichnis-Verarbeitung.
"""

from flask import Flask, render_template, request, redirect, url_for, send_file, abort
import os
import urllib.parse
from tagger.directory_history import get_directory_history
from tagger.mp3_processor import scan_mp3_directory, get_mp3_statistics
from tagger.utils import has_mp3_files, count_mp3_files_in_directory, is_mp3_file

app = Flask(__name__)


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
        elif not has_mp3_files(mp3_dir):
            error = 'Ungültiges Verzeichnis oder keine MP3-Dateien gefunden.'
        else:
            # Absoluten Pfad sicherstellen
            abs_path = os.path.abspath(mp3_dir)
            
            # MP3-Dateien zählen und zur Historie hinzufügen
            mp3_count = count_mp3_files_in_directory(abs_path)
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
    
    Zeigt die gefundenen MP3-Dateien aus dem gewählten Verzeichnis an,
    gruppiert nach Unterverzeichnissen mit vollständigen Metadaten.
    
    Returns:
        Gerenderte results.html Vorlage oder Weiterleitung bei Fehlern
    """
    mp3_dir = request.args.get('mp3_dir', '')
    
    if not mp3_dir or not os.path.isdir(mp3_dir):
        return redirect(url_for('index', error='Verzeichnis nicht gefunden'))
    
    try:
        # Scanne Verzeichnis rekursiv nach MP3-Dateien
        grouped_files = scan_mp3_directory(mp3_dir)
        statistics = get_mp3_statistics(grouped_files)
        
        if not grouped_files:
            return redirect(url_for('index', error='Keine MP3-Dateien im Verzeichnis gefunden'))
        
        return render_template('results.html', 
                             mp3_dir=mp3_dir,
                             grouped_files=grouped_files,
                             statistics=statistics)
        
    except (OSError, PermissionError) as e:
        return redirect(url_for('index', error=f'Fehler beim Lesen des Verzeichnisses: {e}'))
    except Exception as e:
        return redirect(url_for('index', error=f'Unerwarteter Fehler: {e}'))

@app.route('/audio/<path:filepath>')
def serve_audio(filepath):
    """
    Dient MP3-Dateien für das Audio-Streaming.
    
    Args:
        filepath: URL-encodierter Pfad zur MP3-Datei
        
    Returns:
        MP3-Datei als Stream oder 404 bei Fehlern
    """
    try:
        # Dekodiere den Pfad
        decoded_path = urllib.parse.unquote(filepath)
        
        # Füge führende '/' hinzu falls sie fehlt (wegen Flask-Routing)
        if not decoded_path.startswith('/'):
            decoded_path = '/' + decoded_path
        
        # Sicherheitscheck: Datei muss existieren und .mp3 Endung haben
        if not os.path.isfile(decoded_path) or not is_mp3_file(decoded_path):
            abort(404)
        
        return send_file(decoded_path, mimetype='audio/mpeg')
        
    except Exception:
        abort(404)

if __name__ == '__main__':
    app.run(debug=True)
