# mp3-tagger-web
# Eine Web Applikation zum finden und erweitern von id3 und id3v2 Metadaten in MP3 Dateien.
# Zum starten muss das venv geladen werden
# Abhängigkeiten sind in der packages.lst definiert und können mit pip installiert werden


from flask import Flask, render_template, request, redirect, url_for, jsonify, send_from_directory, make_response
from tagger.core import MusicTagger, group_by_directory
from tagger.metadata_enrichment import enrich_multiple_files
from tagger.audio_recognition import recognize_audio_file
from tagger.fingerprinting import get_audio_fingerprint_metadata
import os
import logging

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
        
        # Keine Online-Metadaten in der ersten Ansicht - nur IST-Daten
        enhanced_files = files_data
        print(f"DEBUG: Verarbeitete Ergebnisse: {len(enhanced_files)}")
        
        grouped_results = group_by_directory(enhanced_files)
        print(f"DEBUG: Gruppierte Ergebnisse: {list(grouped_results.keys())}")
        
        return render_template('results.html', 
                            results=grouped_results,
                            directory=full_path)
    
    except Exception as e:
        return f"Fehler: {str(e)}", 500

@app.route('/recognize_audio', methods=['POST'])
def recognize_audio_endpoint():
    """API-Endpunkt für Audio-Erkennung"""
    try:
        data = request.get_json()
        file_path = data.get('file_path')
        
        if not file_path or not os.path.exists(file_path):
            return jsonify({'success': False, 'error': 'Datei nicht gefunden'})
        
        # Audio-Erkennung durchführen
        result = recognize_audio_file(file_path)
        
        if result:
            return jsonify({
                'success': True,
                'result': {
                    'artist': result.get('artist'),
                    'title': result.get('title'),
                    'album': result.get('album'),
                    'service': result.get('service'),
                    'confidence': result.get('confidence', 0)
                }
            })
        else:
            return jsonify({'success': False, 'error': 'Keine Erkennung möglich'})
            
    except Exception as e:
        logging.error(f"Audio-Erkennung fehlgeschlagen: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/get_file_details', methods=['POST'])
def get_file_details():
    """API-Endpunkt für detaillierte Datei-Informationen"""
    try:
        data = request.get_json()
        file_path = data.get('file_path')
        
        if not file_path or not os.path.exists(file_path):
            return jsonify({'success': False, 'error': 'Datei nicht gefunden'})
        
        tagger = MusicTagger()
        # Erstelle temporäre file_data für Details
        file_data = {
            'path': file_path,
            'filename': os.path.basename(file_path)
        }
        
        # Lade detaillierte Informationen
        files_data = tagger.scan_directory(os.path.dirname(file_path))
        file_details = next((f for f in files_data if f['path'] == file_path), None)
        
        if file_details:
            # Formatiere Details für Anzeige
            details = {
                'Dateiname': file_details.get('filename'),
                'Pfad': file_details.get('path'),
                'Artist (aktuell)': file_details.get('current_artist') or 'Nicht gesetzt',
                'Titel (aktuell)': file_details.get('current_title') or 'Nicht gesetzt',
                'Album (aktuell)': file_details.get('current_album') or 'Nicht gesetzt',
                'Genre (aktuell)': file_details.get('current_genre') or 'Nicht gesetzt',
                'Cover': 'Ja' if file_details.get('current_has_cover') else 'Nein'
            }
            
            # Füge ID3-Details hinzu wenn verfügbar
            if file_details.get('current_full_tags'):
                for key, value in file_details['current_full_tags'].items():
                    if value and key not in details:
                        details[f'ID3 {key}'] = value
            
            return jsonify({'success': True, 'details': details})
        else:
            return jsonify({'success': False, 'error': 'Datei-Details nicht verfügbar'})
            
    except Exception as e:
        logging.error(f"Datei-Details fehlgeschlagen: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/get_cover_preview')
def get_cover_preview():
    """GET-Endpunkt für Cover-Vorschau - lädt Cover direkt aus MP3"""
    try:
        file_path = request.args.get('file_path')
        
        if not file_path or not os.path.exists(file_path):
            return "Cover nicht gefunden", 404
        
        # Versuche Cover direkt aus MP3 zu extrahieren
        import eyed3
        eyed3.log.setLevel("ERROR")  # Weniger Logging
        
        audiofile = eyed3.load(file_path)
        if audiofile and audiofile.tag and audiofile.tag.images:
            # Erstes Bild verwenden
            image = audiofile.tag.images[0]
            cover_data = image.image_data
            
            # Bestimme MIME-Type
            mime_type = 'image/jpeg'  # Standard
            if image.mime_type:
                mime_type = image.mime_type
            elif image.image_data[:3] == b'\x89PN':
                mime_type = 'image/png'
            
            response = make_response(cover_data)
            response.headers['Content-Type'] = mime_type
            response.headers['Content-Disposition'] = 'inline'
            response.headers['Cache-Control'] = 'public, max-age=3600'  # Cache für 1 Stunde
            return response
        else:
            return "Kein internes Cover gefunden", 404
            
    except Exception as e:
        logging.error(f"Cover-Preview fehlgeschlagen: {str(e)}")
        return f"Fehler: {str(e)}", 500

@app.route('/get_cover_preview_old', methods=['POST'])
def get_cover_preview_old():
    """API-Endpunkt für Cover-Vorschau"""
    try:
        data = request.get_json()
        file_path = data.get('file_path')
        
        if not file_path or not os.path.exists(file_path):
            return jsonify({'success': False, 'error': 'Datei nicht gefunden'})
        
        tagger = MusicTagger()
        files_data = tagger.scan_directory(os.path.dirname(file_path))
        file_details = next((f for f in files_data if f['path'] == file_path), None)
        
        if file_details:
            # Versuche Cover zu finden
            cover_url = None
            source = None
            size = None
            
            # Interne Cover
            if file_details.get('current_cover_preview'):
                cover_url = f"data:image/jpeg;base64,{file_details['current_cover_preview']}"
                source = "Intern (MP3)"
                if file_details.get('current_cover_info'):
                    size = file_details['current_cover_info'].get('size')
            
            # Externe Cover oder Online-Cover
            elif file_details.get('suggested_cover_url'):
                cover_url = file_details['suggested_cover_url']
                source = "Online"
            
            if cover_url:
                return jsonify({
                    'success': True,
                    'cover_url': cover_url,
                    'source': source,
                    'size': size
                })
            else:
                return jsonify({'success': False, 'error': 'Kein Cover verfügbar'})
        else:
            return jsonify({'success': False, 'error': 'Datei nicht gefunden'})
            
    except Exception as e:
        logging.error(f"Cover-Vorschau fehlgeschlagen: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/process_files', methods=['POST'])
def process_files():
    """API-Endpunkt für Datei-Verarbeitung"""
    try:
        data = request.get_json()
        files = data.get('files', [])
        
        if not files:
            return jsonify({'success': False, 'error': 'Keine Dateien ausgewählt'})
        
        tagger = MusicTagger()
        processed_count = 0
        
        for file_info in files:
            file_path = file_info.get('path')
            
            if not file_path or not os.path.exists(file_path):
                continue
            
            try:
                # Aktualisiere ID3-Tags
                success = tagger.update_id3_tags(
                    file_path,
                    artist=file_info.get('artist'),
                    title=file_info.get('title'),
                    album=file_info.get('album'),
                    track=file_info.get('track')
                )
                
                if success:
                    processed_count += 1
                    
            except Exception as e:
                logging.error(f"Fehler bei Verarbeitung von {file_path}: {str(e)}")
                continue
        
        return jsonify({
            'success': True,
            'processed_count': processed_count,
            'total_files': len(files)
        })
        
    except Exception as e:
        logging.error(f"Datei-Verarbeitung fehlgeschlagen: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/static/audio/<path:filename>')
def serve_audio(filename):
    """Serve audio files for playback"""
    try:
        # Decode filename and construct full path
        file_path = os.path.abspath(os.path.join('/', filename))
        directory = os.path.dirname(file_path)
        filename = os.path.basename(file_path)
        
        if os.path.exists(file_path) and file_path.endswith('.mp3'):
            return send_from_directory(directory, filename, mimetype='audio/mpeg')
        else:
            return "Datei nicht gefunden", 404
            
    except Exception as e:
        logging.error(f"Audio-Serve fehlgeschlagen: {str(e)}")
        return f"Fehler: {str(e)}", 500

@app.route('/enhanced_search', methods=['POST'])
def enhanced_search():
    """Erweiterte Online-Suche für ausgewählte Dateien"""
    try:
        selected_files = request.form.getlist('selected_files')
        
        if not selected_files:
            return "Keine Dateien ausgewählt", 400
        
        tagger = MusicTagger()
        
        # Erstelle file_data für ausgewählte Dateien
        files_data = []
        for file_path in selected_files:
            if os.path.exists(file_path):
                file_data = {
                    'path': file_path,
                    'filename': os.path.basename(file_path)
                }
                # Lade aktuelle ID3-Tags
                tagger.load_current_tags(file_data)
                files_data.append(file_data)
        
        # Führe Online-Metadaten-Suche durch
        enhanced_files = tagger.get_metadata_for_files(files_data)
        
        # Gruppiere Ergebnisse
        grouped_results = group_by_directory(enhanced_files)
        
        # Extrahiere das ursprüngliche Verzeichnis für den Zurück-Button
        first_file_path = selected_files[0] if selected_files else ''
        directory = os.path.dirname(first_file_path)
        
        return render_template('results_enhanced.html', 
                            results=grouped_results,
                            directory=directory)
        
    except Exception as e:
        logging.error(f"Enhanced Search fehlgeschlagen: {str(e)}")
        return f"Fehler bei der erweiterten Suche: {str(e)}", 500

if __name__ == '__main__':
    app.run(debug=True)
