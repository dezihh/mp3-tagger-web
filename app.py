"""
Flask Webserver für MP3 Tagger Web Application

Haupteinstiegspunkt der Webanwendung mit Historie-Funktionalität,
Audio-Erkennung und erweiterten MP3-Verarbeitungsfunktionen.
"""

from flask import Flask, render_template, request, redirect, url_for, send_file, abort, jsonify
import os
import urllib.parse
import asyncio
import configparser
from tagger.directory_history import get_directory_history
from tagger.mp3_processor import (
    scan_mp3_directory, get_mp3_statistics, get_files_needing_recognition,
    set_recognition_result, get_display_title, get_display_artist
)
from tagger.utils import has_mp3_files, count_mp3_files_in_directory, is_mp3_file, get_detailed_mp3_info, save_mp3_tags
from tagger.audio_recognition import create_recognition_service, AudioRecognitionBatch
from tagger.album_recognition import create_album_recognition_service

app = Flask(__name__)

# Template-Funktionen registrieren
@app.template_global()
def get_display_title_for_template(mp3_file):
    """Template-Funktion für Titel-Anzeige."""
    return get_display_title(mp3_file)

@app.template_global()
def get_display_artist_for_template(mp3_file):
    """Template-Funktion für Artist-Anzeige."""
    return get_display_artist(mp3_file)

# Globale Audio-Recognition Service Instanz
recognition_service = None

def get_recognition_service():
    """Lazy-Loading des Recognition Service."""
    global recognition_service
    if recognition_service is None:
        try:
            recognition_service = create_recognition_service()
        except Exception as e:
            print(f"⚠️ Audio-Recognition Service konnte nicht initialisiert werden: {e}")
    return recognition_service


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


@app.route('/api/mp3-info')
def api_mp3_info():
    """
    API-Endpoint für detaillierte MP3-Informationen (für Hover-Tooltip).
    
    Query Parameter:
        filepath: Pfad zur MP3-Datei
        
    Returns:
        JSON mit allen ID3-Tags und Cover-Informationen
    """
    filepath = request.args.get('filepath', '')
    
    if not filepath:
        return jsonify({'error': 'Kein Dateipfad angegeben'}), 400
    
    try:
        # Dekodiere URL-encoded Pfad
        decoded_path = urllib.parse.unquote(filepath)
        
        # Sicherheitscheck
        if not os.path.isfile(decoded_path) or not is_mp3_file(decoded_path):
            return jsonify({'error': 'Datei nicht gefunden oder keine MP3'}), 404
        
        # Detaillierte Informationen sammeln
        info = get_detailed_mp3_info(decoded_path)
        
        return jsonify(info)
        
    except Exception as e:
        return jsonify({'error': f'Fehler beim Laden der MP3-Informationen: {str(e)}'})


@app.route('/api/save-tags', methods=['POST'])
def save_tags():
    """API-Endpoint zum Speichern der ID3-Tags in ausgewählte MP3-Dateien"""
    try:
        data = request.get_json()
        
        if not data or 'files' not in data:
            return jsonify({'success': False, 'message': 'Keine Dateidaten erhalten'})
        
        files_data = data['files']
        results = []
        success_count = 0
        error_count = 0
        
        for file_data in files_data:
            file_path = file_data.get('filepath')
            tags_data = file_data.get('tags', {})
            
            if not file_path:
                results.append({
                    'file': 'Unbekannt',
                    'success': False,
                    'message': 'Kein Dateipfad angegeben'
                })
                error_count += 1
                continue
            
            # Tags speichern
            result = save_mp3_tags(file_path, tags_data)
            results.append(result)
            
            if result['success']:
                success_count += 1
            else:
                error_count += 1
        
        return jsonify({
            'success': error_count == 0,
            'message': f'{success_count} Dateien erfolgreich gespeichert, {error_count} Fehler',
            'results': results,
            'summary': {
                'total': len(files_data),
                'success': success_count,
                'errors': error_count
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Fehler beim Speichern der Tags: {str(e)}'
        })


@app.route('/api/audio-recognition', methods=['POST'])
def audio_recognition():
    """
    API-Endpoint für Audio-Erkennung einzelner Dateien.
    
    Expected JSON:
    {
        "filepath": "/path/to/file.mp3"
    }
    
    Returns:
        JSON mit Erkennungsergebnissen
    """
    try:
        data = request.get_json()
        
        if not data or 'filepath' not in data:
            return jsonify({
                'success': False,
                'message': 'Dateipfad erforderlich'
            })
        
        file_path = data['filepath']
        
        # Prüfen ob Datei existiert
        if not os.path.isfile(file_path) or not is_mp3_file(file_path):
            return jsonify({
                'success': False,
                'message': 'Datei nicht gefunden oder keine MP3-Datei'
            })
        
        # Recognition Service laden
        service = get_recognition_service()
        if not service:
            return jsonify({
                'success': False,
                'message': 'Audio-Recognition Service nicht verfügbar'
            })
        
        # Asynchrone Erkennung ausführen
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(service.recognize_audio(file_path))
        finally:
            loop.close()
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Fehler bei Audio-Erkennung: {str(e)}'
        })


@app.route('/api/batch-audio-recognition', methods=['POST'])
def batch_audio_recognition():
    """
    API-Endpoint für Batch-Audio-Erkennung.
    
    Expected JSON:
    {
        "mp3_dir": "/path/to/directory"
    }
    
    Returns:
        JSON mit Batch-Erkennungsergebnissen
    """
    try:
        data = request.get_json()
        
        if not data or 'mp3_dir' not in data:
            return jsonify({
                'success': False,
                'message': 'Verzeichnispfad erforderlich'
            })
        
        mp3_dir = data['mp3_dir']
        
        # Verzeichnis scannen
        grouped_files = scan_mp3_directory(mp3_dir)
        files_needing_recognition = get_files_needing_recognition(grouped_files)
        
        if not files_needing_recognition:
            return jsonify({
                'success': True,
                'message': 'Keine Dateien benötigen Audio-Erkennung',
                'results': {},
                'stats': {
                    'total': 0,
                    'processed': 0,
                    'successful': 0
                }
            })
        
        # Recognition Service laden
        service = get_recognition_service()
        if not service:
            return jsonify({
                'success': False,
                'message': 'Audio-Recognition Service nicht verfügbar'
            })
        
        # Batch-Verarbeitung
        batch_processor = AudioRecognitionBatch(service)
        
        # File paths für Batch sammeln
        file_paths = [f.file_path for f in files_needing_recognition]
        
        print(f"🎵 Starte Audio-Erkennung für {len(file_paths)} Dateien...")
        
        # Asynchrone Batch-Verarbeitung
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            batch_results = loop.run_until_complete(batch_processor.process_files(file_paths))
        finally:
            loop.close()
        
        # Ergebnisse zu MP3FileInfo zurückmappen und ausgeben
        processed_count = 0
        successful_count = 0
        recognition_data = {}
        
        for mp3_file in files_needing_recognition:
            if mp3_file.file_path in batch_results:
                result = batch_results[mp3_file.file_path]
                set_recognition_result(mp3_file, result)
                processed_count += 1
                
                if result.get('success'):
                    successful_count += 1
                    print(f"✅ Erkannt: {os.path.basename(mp3_file.file_path)} -> {result.get('artist')} - {result.get('title')}")
                    
                    # Erkennungsdaten für Frontend sammeln
                    recognition_data[mp3_file.file_path] = {
                        'title': result.get('title'),
                        'artist': result.get('artist'),
                        'source': result.get('source')
                    }
                else:
                    print(f"❌ Fehlgeschlagen: {os.path.basename(mp3_file.file_path)} - {result.get('error')}")
        
        # Statistics sammeln
        stats = service.get_recognition_stats()
        
        return jsonify({
            'success': True,
            'message': f'{successful_count} von {processed_count} Dateien erfolgreich erkannt',
            'results': batch_results,
            'recognition_data': recognition_data,
            'stats': {
                'total': len(files_needing_recognition),
                'processed': processed_count,
                'successful': successful_count,
                **stats
            }
        })
        
    except Exception as e:
        print(f"💥 Fehler bei batch audio recognition: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Fehler bei Batch-Audio-Erkennung: {str(e)}'
        })


@app.route('/api/recognition-status/<path:mp3_dir>')
def recognition_status(mp3_dir):
    """
    API-Endpoint für den Status der Audio-Erkennung in einem Verzeichnis.
    
    Args:
        mp3_dir: Pfad zum MP3-Verzeichnis
        
    Returns:
        JSON mit Recognition-Status
    """
    try:
        # URL-decode des Pfads
        mp3_dir = urllib.parse.unquote(mp3_dir)
        
        # Verzeichnis scannen
        grouped_files = scan_mp3_directory(mp3_dir)
        files_needing_recognition = get_files_needing_recognition(grouped_files)
        
        # Dateien mit Erkennungsergebnissen zählen
        files_with_recognition = []
        for files in grouped_files.values():
            for mp3_file in files:
                if mp3_file.recognized_title or mp3_file.recognized_artist:
                    files_with_recognition.append(mp3_file)
        
        return jsonify({
            'success': True,
            'total_files': sum(len(files) for files in grouped_files.values()),
            'needs_recognition': len(files_needing_recognition),
            'has_recognition': len(files_with_recognition),
            'recognition_sources': {}  # Kann später erweitert werden
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Fehler beim Laden des Recognition-Status: {str(e)}'
        })


@app.route('/api/album-recognition', methods=['POST'])
def album_recognition():
    """API-Endpoint für Album-Erkennung"""
    try:
        data = request.get_json()
        if not data or 'directory' not in data:
            return jsonify({
                'success': False,
                'message': 'Verzeichnis-Parameter fehlt'
            })
        
        directory = data['directory']
        selected_files = data.get('selected_files', [])
        
        print(f"Album-Erkennung für Verzeichnis: {directory}")
        print(f"Ausgewählte Dateien: {len(selected_files)}")
        
        if not os.path.exists(directory):
            return jsonify({
                'success': False,
                'message': 'Verzeichnis nicht gefunden'
            })
        
        # MP3-Dateien scannen
        grouped_files = scan_mp3_directory(directory)
        all_files = []
        for group_files in grouped_files.values():
            all_files.extend(group_files)
        
        # Nur ausgewählte Dateien verwenden, falls angegeben
        if selected_files:
            all_files = [f for f in all_files if f.full_path in selected_files]
        
        if not all_files:
            return jsonify({
                'success': False,
                'message': 'Keine MP3-Dateien zur Album-Erkennung gefunden'
            })
        
        # Album-Erkennung durchführen
        recognition_service = create_album_recognition_service()
        
        # Datei-Informationen für die Erkennung vorbereiten
        files_info = []
        for mp3_file in all_files:
            files_info.append({
                'title': mp3_file.title or '',
                'artist': mp3_file.artist or '',
                'filename': mp3_file.filename,
                'full_path': mp3_file.full_path
            })
        
        # Asynchrone Album-Erkennung
        async def recognize_album_async():
            return await recognition_service.recognize_album(files_info)
        
        candidates, max_confidence = asyncio.run(recognize_album_async())
        
        print(f"Album-Erkennung abgeschlossen: {len(candidates)} Kandidaten, Konfidenz: {max_confidence}")
        
        # Ergebnis formatieren
        candidates_data = []
        for candidate in candidates:
            print(f"DEBUG: Kandidat - Titel: '{candidate.title}', Artist: '{candidate.artist}', Jahr: '{candidate.year}'")
            candidates_data.append({
                'title': candidate.title,
                'artist': candidate.artist or 'Unbekannter Künstler',  # Fallback für leere Artists
                'year': candidate.year,
                'track_count': candidate.track_count,
                'confidence': candidate.confidence,
                'source': candidate.source,
                'external_id': candidate.external_id,
                'tracks': candidate.tracks
            })
        
        return jsonify({
            'success': True,
            'candidates': candidates_data,
            'max_confidence': max_confidence,
            'auto_apply': max_confidence >= 0.9,  # Auto-Anwenden bei hoher Konfidenz
            'message': f'{len(candidates)} Album-Kandidaten gefunden'
        })
        
    except Exception as e:
        print(f"Fehler bei Album-Erkennung: {e}")
        return jsonify({
            'success': False,
            'message': f'Album-Erkennung fehlgeschlagen: {str(e)}'
        })


@app.route('/api/apply-album', methods=['POST'])
def apply_album():
    """API-Endpoint zum Anwenden der Album-Daten"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': 'Keine Daten empfangen'
            })
        
        directory = data.get('directory')
        selected_files = data.get('selected_files', [])
        album_data = data.get('album_data')
        
        if not all([directory, album_data]):
            return jsonify({
                'success': False,
                'message': 'Verzeichnis oder Album-Daten fehlen'
            })
        
        print(f"Album-Daten anwenden für Verzeichnis: {directory}")
        
        # MP3-Dateien scannen
        grouped_files = scan_mp3_directory(directory)
        all_files = []
        for group_files in grouped_files.values():
            all_files.extend(group_files)
        
        # Nur ausgewählte Dateien verwenden, falls angegeben
        if selected_files:
            all_files = [f for f in all_files if f.full_path in selected_files]
        
        # Album-Daten auf Dateien anwenden
        applied_files = []
        album_tracks = album_data.get('tracks', [])
        
        for mp3_file in all_files:
            # Passenden Track im Album finden
            best_match = None
            best_score = 0
            
            current_title = (mp3_file.title or '').lower().strip()
            
            for track in album_tracks:
                track_title = track.get('title', '').lower().strip()
                
                if current_title and track_title:
                    # Exakte Übereinstimmung
                    if current_title == track_title:
                        best_match = track
                        best_score = 1.0
                        break
                    # Ähnlichkeits-Matching
                    elif current_title in track_title or track_title in current_title:
                        score = 0.8
                        if score > best_score:
                            best_match = track
                            best_score = score
            
            if best_match:
                # Album-Daten anwenden
                mp3_file.album = album_data.get('title', '')
                mp3_file.year = album_data.get('year', '')
                mp3_file.track_number = str(best_match.get('number', ''))
                
                # Als erkannt markieren
                mp3_file.album_recognized = True
                
                applied_files.append({
                    'filename': mp3_file.filename,
                    'album': mp3_file.album,
                    'year': mp3_file.year,
                    'track_number': mp3_file.track_number
                })
        
        print(f"Album-Daten auf {len(applied_files)} Dateien angewendet")
        
        return jsonify({
            'success': True,
            'applied_files': applied_files,
            'message': f'Album-Daten auf {len(applied_files)} Dateien angewendet'
        })
        
    except Exception as e:
        print(f"Fehler beim Anwenden der Album-Daten: {e}")
        return jsonify({
            'success': False,
            'message': f'Fehler beim Anwenden der Album-Daten: {str(e)}'
        })


if __name__ == '__main__':
    app.run(debug=True)
