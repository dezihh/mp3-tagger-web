import os
import eyed3
from pathlib import Path
from difflib import SequenceMatcher
import requests
from urllib.parse import quote
import logging
import base64
from collections import defaultdict
import re

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class MusicTagger:
    def __init__(self):
        self.lastfm_key = os.getenv('LASTFM_API_KEY')
        self.discogs_key = os.getenv('DISCOGS_API_KEY')
        self.discogs_secret = os.getenv('DISCOGS_API_SECRET')
        self.min_confidence = 0.6

    def scan_directory(self, directory):
        files = []
        try:
            for mp3_path in Path(directory).rglob('*.mp3'):
                try:
                    audio = eyed3.load(mp3_path)
                    if audio.tag is None:
                        audio.initTag()

                    file_data = {
                        'path': str(mp3_path),
                        'filename': mp3_path.name,
                        'directory': str(mp3_path.parent),
                        'target_path': str(mp3_path),
                        'current_artist': audio.tag.artist,
                        'current_title': audio.tag.title,
                        'current_album': audio.tag.album,
                        'current_has_cover': self._has_cover(audio),
                        'current_full_tags': self._get_full_tag_info(audio),
                        'current_cover_preview': self._get_cover_preview(audio),
                        'suggested_artist': None,
                        'suggested_title': None,
                        'suggested_album': None,
                        'suggested_cover_url': None,
                        'suggested_full_tags': None
                    }
                    files.append(file_data)
                except Exception as e:
                    logging.error(f"Fehler beim Lesen von {mp3_path}: {str(e)}")
        except Exception as e:
            logging.error(f"Verzeichnisscan fehlgeschlagen: {str(e)}")
        return files

    def get_metadata_for_files(self, files_data):
        results = []
        for file_data in files_data:
            try:
                artist, title = self._parse_filename(file_data['filename'])
                online_meta = self._query_online_metadata(
                    artist or file_data['current_artist'],
                    title or file_data['current_title'],
                    file_data['current_album']
                )

                if online_meta:
                    file_data.update({
                        'suggested_artist': online_meta.get('artist'),
                        'suggested_title': online_meta.get('title'),
                        'suggested_album': online_meta.get('album'),
                        'suggested_cover_url': online_meta.get('cover_url'),
                        'suggested_full_tags': self._format_suggested_tags(online_meta)
                    })
                results.append(file_data)
            except Exception as e:
                logging.error(f"Metadatenabfrage fehlgeschlagen für {file_data['filename']}: {str(e)}")
                results.append(file_data)
        return results

    # ... (alle anderen Methoden der MusicTagger-Klasse bleiben gleich wie zuvor)

def group_by_directory(files_data):
    grouped = defaultdict(list)
    for file in files_data:
        grouped[file['directory']].append(file)
    return dict(grouped)
