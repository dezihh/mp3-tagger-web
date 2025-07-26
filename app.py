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
        full_path = os.path.abspath(os.path.join('/', directory))
        
        if not os.path.isdir(full_path):
            return "Verzeichnis nicht gefunden", 404
        
        tagger = MusicTagger()
        files_data = tagger.scan_directory(full_path)
        results = tagger.get_metadata_for_files(files_data)
        grouped_results = group_by_directory(results)
        
        return render_template('results.html', 
                            results=grouped_results,
                            directory=full_path)
    
    except Exception as e:
        return f"Fehler: {str(e)}", 500

if __name__ == '__main__':
    app.run(debug=True)
