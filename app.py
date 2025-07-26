from flask import Flask, render_template, request, redirect, url_for
from tagger.core import MusicTagger, group_by_directory
import os

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        directory = request.form['directory'].strip()
        if os.path.isdir(directory):
            norm_path = os.path.normpath(directory).lstrip('/')
            return redirect(url_for('process', directory=norm_path))
    return render_template('index.html')

@app.route('/process/<path:directory>')
def process(directory):
    try:
        # Dekodiere den directory parameter und baue den absoluten Pfad
        full_path = os.path.abspath(os.path.join('/', directory))
        
        if not os.path.isdir(full_path):
            return f"Verzeichnis nicht gefunden: {full_path}", 404
        
        tagger = MusicTagger()
        files_data = tagger.scan_directory(full_path)
        print(f"DEBUG: Gefundene Dateien: {len(files_data)}")
        for file_data in files_data[:2]:  # Zeige nur die ersten 2 für Debug
            print(f"DEBUG: Datei: {file_data}")
        
        results = tagger.get_metadata_for_files(files_data)
        print(f"DEBUG: Verarbeitete Ergebnisse: {len(results)}")
        
        grouped_results = group_by_directory(results)
        print(f"DEBUG: Gruppierte Ergebnisse: {list(grouped_results.keys())}")
        
        return render_template('results.html', 
                            results=grouped_results,
                            directory=full_path)
    
    except Exception as e:
        return f"Fehler: {str(e)}", 500

if __name__ == '__main__':
    app.run(debug=True)
