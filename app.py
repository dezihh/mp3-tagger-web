"""
Flask Webserver für MP3 Tagger Web Application
Einstiegsseite: Quellverzeichnis-Eingabe
"""

from flask import Flask, render_template, request, redirect, url_for
import os

app = Flask(__name__)

# Hilfsfunktion: Prüft, ob ein Verzeichnis existiert
# Gibt True zurück, wenn das Verzeichnis existiert und MP3-Dateien enthält
# Inline-Dokumentation für bessere Wartbarkeit
def is_valid_mp3_dir(path):
    """Prüft, ob das angegebene Verzeichnis existiert und MP3-Dateien enthält."""
    if not os.path.isdir(path):
        return False
    for fname in os.listdir(path):
        if fname.lower().endswith('.mp3'):
            return True
    return False

@app.route('/', methods=['GET', 'POST'])
def index():
    """Einstiegsseite: Quellverzeichnis für MP3-Dateien eingeben."""
    error = None
    mp3_dir = ''
    if request.method == 'POST':
        mp3_dir = request.form.get('mp3_dir', '').strip()
        if not is_valid_mp3_dir(mp3_dir):
            error = 'Ungültiges Verzeichnis oder keine MP3-Dateien gefunden.'
        else:
            # Weiterleitung zur nächsten Seite (Platzhalter)
            return redirect(url_for('results', mp3_dir=mp3_dir))
    return render_template('index.html', error=error, mp3_dir=mp3_dir)

@app.route('/results')
def results():
    """Platzhalter für die Ergebnisseite nach Verzeichniswahl."""
    mp3_dir = request.args.get('mp3_dir', '')
    return f"Gewähltes Verzeichnis: {mp3_dir} (Ergebnisse folgen...)"

if __name__ == '__main__':
    app.run(debug=True)
