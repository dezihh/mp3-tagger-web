import os
import logging
import requests
import time
import re
from urllib.parse import quote
from dotenv import load_dotenv
from pathlib import Path
import musicbrainzngs
import pylast
import discogs_client
import base64
from io import BytesIO
from PIL import Image

# Lade Umgebungsvariablen
from pathlib import Path
config_path = Path(__file__).parent.parent / 'config.env'
load_dotenv(config_path)

class OnlineMetadataProvider:
    """
    Sammelt Metadaten von verschiedenen Online-Diensten:
    - MusicBrainz (kostenlos, Open Source)
    - Last.fm (Track-Info, Ähnlichkeits-Daten)
    - Discogs (Detaillierte Releases, Genres)
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._setup_apis()
        self.rate_limits = {
            'musicbrainz': 1.0,  # 1 Request pro Sekunde
            'lastfm': 0.2,       # 5 Requests pro Sekunde
            'discogs': 1.0       # 1 Request pro Sekunde
        }
        self.last_request = {}
        
    def _setup_apis(self):
        """Initialisiert alle API-Clients"""
        # MusicBrainz Setup
        useragent = os.getenv('MUSICBRAINZ_USERAGENT', 'MP3Tagger/1.0')
        musicbrainzngs.set_useragent(*useragent.split('/'))
        
        # Last.fm Setup
        self.lastfm_key = os.getenv('LASTFM_API_KEY')
        if self.lastfm_key:
            try:
                self.lastfm = pylast.LastFMNetwork(api_key=self.lastfm_key)
            except Exception as e:
                self.logger.error(f"Last.fm Setup fehlgeschlagen: {e}")
                self.lastfm = None
        else:
            self.lastfm = None
            
        # Discogs Setup
        self.discogs_token = os.getenv('DISCOGS_API_KEY')
        if self.discogs_token:
            try:
                self.discogs = discogs_client.Client('MP3Tagger/1.0', user_token=self.discogs_token)
            except Exception as e:
                self.logger.error(f"Discogs Setup fehlgeschlagen: {e}")
                self.discogs = None
        else:
            self.discogs = None
    
    def _respect_rate_limit(self, service):
        """Berücksichtigt Rate Limits der APIs"""
        if service in self.last_request:
            elapsed = time.time() - self.last_request[service]
            required_wait = self.rate_limits[service]
            if elapsed < required_wait:
                wait_time = required_wait - elapsed
                time.sleep(wait_time)
        
        self.last_request[service] = time.time()
    
    def search_metadata(self, filename, current_artist=None, current_title=None, current_album=None):
        """
        Sucht Metadaten für eine Audio-Datei
        
        Args:
            filename: Name der MP3-Datei
            current_artist: Aktueller Künstler (falls vorhanden)
            current_title: Aktueller Titel (falls vorhanden)
            current_album: Aktuelles Album (falls vorhanden)
            
        Returns:
            dict: Erweiterte Metadaten
        """
        # Extrahiere Such-Information aus Dateiname falls nötig
        search_info = self._extract_search_info(filename, current_artist, current_title, current_album)
        
        results = {
            'artist': current_artist,
            'title': current_title, 
            'album': current_album,
            'year': None,
            'genre': None,
            'track_number': None,
            'total_tracks': None,
            'musicbrainz_recording_id': None,
            'musicbrainz_release_id': None,
            'musicbrainz_artist_id': None,
            'cover_url': None,
            'cover_data': None,
            'additional_genres': [],
            'confidence': 0.0,
            'source': None
        }
        
        # Versuche verschiedene Quellen in Reihenfolge der Zuverlässigkeit
        if search_info['artist'] and search_info['title']:
            # 1. MusicBrainz (am zuverlässigsten für IDs)
            mb_result = self._search_musicbrainz(search_info)
            if mb_result and mb_result['confidence'] > 0.6:
                results.update(mb_result)
                results['source'] = 'MusicBrainz'
            
            # 2. Last.fm (gute Track-Informationen)
            elif self.lastfm:
                lastfm_result = self._search_lastfm(search_info)
                if lastfm_result and lastfm_result['confidence'] > 0.6:
                    results.update(lastfm_result)
                    results['source'] = 'Last.fm'
            
            # 3. Discogs (detaillierte Release-Informationen)
            if not results['source'] and self.discogs:
                discogs_result = self._search_discogs(search_info)
                if discogs_result and discogs_result['confidence'] > 0.5:
                    results.update(discogs_result)
                    results['source'] = 'Discogs'
        
        return results
    
    def _extract_search_info(self, filename, artist, title, album):
        """Extrahiert Such-Information aus Dateiname und vorhandenen Tags"""
        search_info = {
            'artist': artist,
            'title': title,
            'album': album,
            'filename': filename
        }
        
        # Falls Artist/Title fehlen, versuche aus Dateiname zu extrahieren
        if not artist or not title:
            # Typische Muster: "Artist - Title.mp3", "01 - Artist - Title.mp3"
            clean_name = os.path.splitext(filename)[0]
            
            # Entferne Track-Nummern am Anfang
            clean_name = re.sub(r'^\d+[\s\-\.]*', '', clean_name)
            
            # Versuche "Artist - Title" Pattern
            if ' - ' in clean_name:
                parts = clean_name.split(' - ', 1)
                if len(parts) == 2:
                    if not artist:
                        search_info['artist'] = parts[0].strip()
                    if not title:
                        search_info['title'] = parts[1].strip()
        
        return search_info
    
    def _search_musicbrainz(self, search_info):
        """Sucht in MusicBrainz Datenbank"""
        try:
            self._respect_rate_limit('musicbrainz')
            
            # Erste Suche mit Album
            query = f'artist:"{search_info["artist"]}" AND recording:"{search_info["title"]}"'
            if search_info['album']:
                query += f' AND release:"{search_info["album"]}"'
            
            self.logger.info(f"MusicBrainz Query: {query}")
            result = musicbrainzngs.search_recordings(query=query, limit=5)
            
            # Falls keine Ergebnisse mit Album, versuche ohne Album
            if not result['recording-list'] and search_info['album']:
                query_fallback = f'artist:"{search_info["artist"]}" AND recording:"{search_info["title"]}"'
                self.logger.info(f"MusicBrainz Fallback Query (ohne Album): {query_fallback}")
                result = musicbrainzngs.search_recordings(query=query_fallback, limit=5)
            
            if result['recording-list']:
                best_match = result['recording-list'][0]
                self.logger.info(f"MusicBrainz gefunden: {best_match.get('title')} von {best_match.get('artist-credit', [{}])[0].get('artist', {}).get('name', 'Unknown')}")
                
                confidence = self._calculate_confidence(
                    search_info, 
                    best_match.get('artist-credit', [{}])[0].get('artist', {}).get('name', ''),
                    best_match.get('title', ''),
                    best_match.get('release-list', [{}])[0].get('title', '') if best_match.get('release-list') else ''
                )
                
                # Hole Cover-Informationen aus Release-Group
                genres = []
                cover_url = None
                try:
                    if best_match.get('release-list'):
                        # Versuche Cover in allen verfügbaren Releases zu finden
                        for release in best_match['release-list'][:3]:  # Erste 3 Releases
                            release_id = release['id']
                            release_title = release.get('title', 'Unknown')
                            self.logger.debug(f"Suche Cover in Release: {release_title} ({release_id})")
                            
                            try:
                                cover_art = musicbrainzngs.get_image_list(release_id)
                                if cover_art.get('images'):
                                    # Nimm das erste Front-Cover
                                    for image in cover_art['images']:
                                        if 'Front' in image.get('types', []):
                                            cover_url = image['image']
                                            self.logger.info(f"Cover-URL gefunden in {release_title}: {cover_url}")
                                            break
                                    # Falls kein Front-Cover, nimm das erste verfügbare
                                    if not cover_url and cover_art['images']:
                                        cover_url = cover_art['images'][0]['image']
                                        self.logger.info(f"Erstes Cover-URL gefunden in {release_title}: {cover_url}")
                                    
                                    if cover_url:
                                        # Konvertiere HTTP zu HTTPS für bessere Browser-Kompatibilität
                                        if cover_url.startswith('http://'):
                                            cover_url = cover_url.replace('http://', 'https://', 1)
                                            self.logger.debug(f"Cover-URL zu HTTPS konvertiert: {cover_url}")
                                        break  # Cover gefunden, stoppe Suche
                            except Exception as cover_e:
                                self.logger.debug(f"Cover-Art Fehler für {release_title}: {cover_e}")
                                
                        # Hole Release-Details für Genre-Informationen (erstes Release)
                        release_detail = musicbrainzngs.get_release_by_id(best_match['release-list'][0]['id'], includes=['release-groups'])
                        
                        if 'release-group' in release_detail['release']:
                            rg_id = release_detail['release']['release-group']['id']
                            self.logger.debug(f"Hole Release-Group-Tags für {rg_id}")
                            rg_detail = musicbrainzngs.get_release_group_by_id(rg_id, includes=['tags'])
                            if 'tag-list' in rg_detail['release-group']:
                                self.logger.debug(f"Release-Group hat {len(rg_detail['release-group']['tag-list'])} Tags")
                                for tag in rg_detail['release-group']['tag-list']:
                                    # Count kann String oder Int sein - beide behandeln
                                    count = tag.get('count', 0)
                                    try:
                                        count_int = int(count) if isinstance(count, str) else count
                                        if count_int > 0:  # Nur Tags mit Bewertungen
                                            genres.append(tag['name'])
                                            self.logger.debug(f"Genre hinzugefügt: {tag['name']} (count: {count})")
                                    except (ValueError, TypeError):
                                        # Auch Tags ohne gültigen Count verwenden
                                        genres.append(tag['name'])
                                        self.logger.debug(f"Genre hinzugefügt (ohne Count): {tag['name']}")
                    
                    # Versuche auch Artist-Genres
                    if best_match.get('artist-credit'):
                        artist_id = best_match['artist-credit'][0]['artist']['id']
                        self.logger.debug(f"Hole Artist-Tags für {artist_id}")
                        artist_detail = musicbrainzngs.get_artist_by_id(artist_id, includes=['tags'])
                        if 'tag-list' in artist_detail['artist']:
                            self.logger.debug(f"Artist hat {len(artist_detail['artist']['tag-list'])} Tags")
                            for tag in artist_detail['artist']['tag-list']:
                                # Count kann String oder Int sein - beide behandeln
                                count = tag.get('count', 0)
                                try:
                                    count_int = int(count) if isinstance(count, str) else count
                                    if count_int > 0 and tag['name'] not in genres:
                                        genres.append(tag['name'])
                                        self.logger.debug(f"Artist-Genre hinzugefügt: {tag['name']} (count: {count})")
                                except (ValueError, TypeError):
                                    # Auch Tags ohne gültigen Count verwenden
                                    if tag['name'] not in genres:
                                        genres.append(tag['name'])
                                        self.logger.debug(f"Artist-Genre hinzugefügt (ohne Count): {tag['name']}")
                        else:
                            self.logger.debug("Keine Artist-Tags gefunden")
                                    
                except Exception as e:
                    self.logger.error(f"MusicBrainz Genre-Abruf fehlgeschlagen: {e}")
                    import traceback
                    self.logger.error(traceback.format_exc())
                
                # Erweiterte Klassifizierung basierend auf Tags
                classification = self._classify_musical_attributes(genres, best_match)
                
                result_data = {
                    'artist': best_match.get('artist-credit', [{}])[0].get('artist', {}).get('name'),
                    'title': best_match.get('title'),
                    'album': best_match.get('release-list', [{}])[0].get('title') if best_match.get('release-list') else None,
                    'year': self._extract_year_from_mb(best_match),
                    'genre': genres[0] if genres else None,  # Hauptgenre
                    'additional_genres': genres[:5],  # Bis zu 5 Genres
                    'cover_url': cover_url,  # Cover-URL hinzugefügt
                    'musicbrainz_recording_id': best_match.get('id'),
                    'musicbrainz_artist_id': best_match.get('artist-credit', [{}])[0].get('artist', {}).get('id'),
                    'musicbrainz_release_id': best_match.get('release-list', [{}])[0].get('id') if best_match.get('release-list') else None,
                    'confidence': confidence,
                    # Erweiterte Klassifizierung
                    'era': classification.get('era'),
                    'mood': classification.get('mood'),
                    'style': classification.get('style'),
                    'similar_artists': classification.get('similar_artists'),
                    'instrumentation': classification.get('instrumentation'),
                    'energy_level': classification.get('energy_level'),
                    'tempo_description': classification.get('tempo_description')
                }
                
                self.logger.info(f"MusicBrainz Ergebnis: Confidence={confidence:.2f}, Artist={result_data['artist']}, Genres={len(genres)}, Cover={cover_url is not None}")
                return result_data
            else:
                self.logger.info("MusicBrainz: Keine Ergebnisse gefunden")
                
        except Exception as e:
            self.logger.error(f"MusicBrainz Suche fehlgeschlagen: {e}")
        
        return None
    
    def _search_lastfm(self, search_info):
        """Sucht in Last.fm"""
        try:
            self._respect_rate_limit('lastfm')
            
            track = self.lastfm.get_track(search_info['artist'], search_info['title'])
            track_info = track.get_correction()
            
            if track_info:
                confidence = self._calculate_confidence(
                    search_info,
                    track_info['artist'],
                    track_info['title'],
                    track_info.get('album', '')
                )
                
                # Hole zusätzliche Informationen
                top_tags = []
                try:
                    tags = track.get_top_tags(limit=5)
                    top_tags = [tag.item.name for tag in tags]
                except:
                    pass
                
                # Hole Cover-Art
                cover_url = None
                try:
                    album_info = track.get_album()
                    if album_info:
                        cover_url = album_info.get_cover_image()
                except:
                    pass
                
                # Erweiterte Klassifizierung für Last.fm
                classification = self._classify_musical_attributes(top_tags, {'year': None})
                
                return {
                    'artist': track_info['artist'],
                    'title': track_info['title'],
                    'album': track_info.get('album'),
                    'additional_genres': top_tags,
                    'cover_url': cover_url,
                    'confidence': confidence,
                    # Erweiterte Klassifizierung
                    'era': classification.get('era'),
                    'mood': classification.get('mood'),
                    'style': classification.get('style'),
                    'similar_artists': classification.get('similar_artists'),
                    'instrumentation': classification.get('instrumentation'),
                    'energy_level': classification.get('energy_level'),
                    'tempo_description': classification.get('tempo_description')
                }
                
        except Exception as e:
            self.logger.error(f"Last.fm Suche fehlgeschlagen: {e}")
        
        return None
    
    def _search_discogs(self, search_info):
        """Sucht in Discogs"""
        try:
            self._respect_rate_limit('discogs')
            
            query = f"{search_info['artist']} {search_info['title']}"
            if search_info['album']:
                query += f" {search_info['album']}"
            
            results = self.discogs.search(query, type='release')
            
            if results:
                best_match = results[0]
                confidence = self._calculate_confidence(
                    search_info,
                    best_match.artists[0].name if best_match.artists else '',
                    best_match.title,
                    ''
                )
                
                # Hole detaillierte Release-Informationen
                try:
                    release = self.discogs.release(best_match.id)
                    
                    genres = []
                    if hasattr(release, 'genres'):
                        genres.extend(release.genres)
                    if hasattr(release, 'styles'):
                        genres.extend(release.styles)
                    
                    cover_url = None
                    if hasattr(release, 'images') and release.images:
                        cover_url = release.images[0]['uri']
                    
                    # Erweiterte Klassifizierung für Discogs
                    classification = self._classify_musical_attributes(genres, {'year': release.year if hasattr(release, 'year') else None})
                    
                    return {
                        'artist': release.artists[0].name if release.artists else None,
                        'title': best_match.title,
                        'album': release.title,
                        'year': release.year if hasattr(release, 'year') else None,
                        'additional_genres': genres,
                        'cover_url': cover_url,
                        'confidence': confidence,
                        # Erweiterte Klassifizierung
                        'era': classification.get('era'),
                        'mood': classification.get('mood'),
                        'style': classification.get('style'),
                        'similar_artists': classification.get('similar_artists'),
                        'instrumentation': classification.get('instrumentation'),
                        'energy_level': classification.get('energy_level'),
                        'tempo_description': classification.get('tempo_description')
                    }
                    
                except Exception as e:
                    self.logger.error(f"Discogs Release-Details fehlgeschlagen: {e}")
                    
        except Exception as e:
            self.logger.error(f"Discogs Suche fehlgeschlagen: {e}")
        
        return None
    
    def _calculate_confidence(self, search_info, found_artist, found_title, found_album):
        """Berechnet Vertrauenswert basierend auf String-Ähnlichkeit"""
        from difflib import SequenceMatcher
        
        scores = []
        
        if search_info['artist'] and found_artist:
            score = SequenceMatcher(None, search_info['artist'].lower(), found_artist.lower()).ratio()
            scores.append(score)
        
        if search_info['title'] and found_title:
            score = SequenceMatcher(None, search_info['title'].lower(), found_title.lower()).ratio()
            scores.append(score)
        
        if search_info['album'] and found_album:
            score = SequenceMatcher(None, search_info['album'].lower(), found_album.lower()).ratio()
            scores.append(score)
        
        return sum(scores) / len(scores) if scores else 0.0
    
    def _extract_year_from_mb(self, recording):
        """Extrahiert Jahr aus MusicBrainz Recording"""
        try:
            if recording.get('release-list'):
                release = recording['release-list'][0]
                if release.get('date'):
                    return int(release['date'][:4])
        except:
            pass
        return None
    
    def download_cover_art(self, cover_url, max_size=(500, 500)):
        """Lädt Cover-Art herunter und konvertiert zu Base64"""
        try:
            response = requests.get(cover_url, timeout=10)
            response.raise_for_status()
            
            # Lade Bild und skaliere falls nötig
            img = Image.open(BytesIO(response.content))
            
            # Skaliere auf maximale Größe
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Konvertiere zu JPEG und Base64
            buffer = BytesIO()
            img.convert('RGB').save(buffer, format='JPEG', quality=85)
            img_data = buffer.getvalue()
            
            return {
                'data': base64.b64encode(img_data).decode('utf-8'),
                'format': 'JPEG',
                'size': img.size
            }
            
        except Exception as e:
            self.logger.error(f"Cover-Download fehlgeschlagen: {e}")
            return None
    
    def _classify_musical_attributes(self, genres, musicbrainz_data):
        """Klassifiziert erweiterte musikalische Eigenschaften basierend auf Genres und Metadaten"""
        classification = {
            'era': None,
            'mood': [],
            'style': [],
            'similar_artists': [],
            'instrumentation': [],
            'energy_level': None,
            'tempo_description': None
        }
        
        # Kombiniere alle verfügbaren Tags für die Analyse
        all_tags = genres.copy() if genres else []
        
        # Zeitliche Einordnung basierend auf Jahr und Genre
        year = self._extract_year_from_mb(musicbrainz_data)
        if year:
            if year < 1960:
                classification['era'] = "Pre-60s"
            elif year < 1970:
                classification['era'] = "60s"
            elif year < 1980:
                classification['era'] = "70s"
            elif year < 1990:
                classification['era'] = "80s"
            elif year < 2000:
                classification['era'] = "90s"
            elif year < 2010:
                classification['era'] = "2000s"
            elif year < 2020:
                classification['era'] = "2010s"
            else:
                classification['era'] = "2020s+"
        
        # Stimmung/Atmosphäre basierend auf Genre-Keywords
        mood_keywords = {
            'energetic': ['punk', 'thrash', 'speed', 'power', 'upbeat', 'dance', 'electronic', 'disco'],
            'melancholic': ['blues', 'sad', 'melancholy', 'depressive', 'doom', 'gothic'],
            'aggressive': ['metal', 'hardcore', 'death', 'black', 'extreme', 'brutal', 'violent'],
            'peaceful': ['ambient', 'chill', 'relaxing', 'meditative', 'new age', 'acoustic'],
            'romantic': ['love', 'romantic', 'ballad', 'soft', 'tender'],
            'rebellious': ['punk', 'alternative', 'grunge', 'protest', 'rebel'],
            'nostalgic': ['classic', 'vintage', 'retro', 'oldies'],
            'spiritual': ['gospel', 'christian', 'religious', 'spiritual', 'sacred'],
            'playful': ['novelty', 'comedy', 'fun', 'party', 'silly'],
            'dark': ['dark', 'gothic', 'black', 'doom', 'death', 'horror']
        }
        
        for mood, keywords in mood_keywords.items():
            for keyword in keywords:
                if any(keyword.lower() in tag.lower() for tag in all_tags):
                    if mood not in classification['mood']:
                        classification['mood'].append(mood)
        
        # Stilistische Klassifizierung
        style_keywords = {
            'progressive': ['progressive', 'prog', 'complex', 'experimental'],
            'acoustic': ['acoustic', 'unplugged', 'folk', 'singer-songwriter'],
            'electronic': ['electronic', 'synth', 'techno', 'house', 'edm', 'electro'],
            'orchestral': ['orchestral', 'symphonic', 'classical', 'chamber'],
            'minimalist': ['minimal', 'simple', 'stripped'],
            'fusion': ['fusion', 'crossover', 'mixed'],
            'traditional': ['traditional', 'classic', 'standard', 'conventional'],
            'avant-garde': ['avant-garde', 'experimental', 'abstract', 'unconventional'],
            'psychedelic': ['psychedelic', 'psych', 'trippy', 'surreal'],
            'garage': ['garage', 'lo-fi', 'raw', 'underground']
        }
        
        for style, keywords in style_keywords.items():
            for keyword in keywords:
                if any(keyword.lower() in tag.lower() for tag in all_tags):
                    if style not in classification['style']:
                        classification['style'].append(style)
        
        # Instrumentierung basierend auf Genre
        instrumentation_keywords = {
            'guitar-driven': ['rock', 'metal', 'punk', 'grunge', 'blues', 'country'],
            'piano-based': ['piano', 'classical', 'jazz', 'ballad', 'singer-songwriter'],
            'electronic': ['electronic', 'synth', 'techno', 'house', 'ambient'],
            'orchestral': ['classical', 'symphonic', 'orchestral', 'chamber'],
            'vocal-focused': ['vocal', 'a cappella', 'choir', 'opera'],
            'percussion-heavy': ['drum', 'tribal', 'afro', 'latin', 'world'],
            'brass-section': ['jazz', 'big band', 'ska', 'swing', 'dixieland'],
            'string-quartet': ['classical', 'chamber', 'string', 'quartet']
        }
        
        for instr, keywords in instrumentation_keywords.items():
            for keyword in keywords:
                if any(keyword.lower() in tag.lower() for tag in all_tags):
                    if instr not in classification['instrumentation']:
                        classification['instrumentation'].append(instr)
        
        # Energy Level basierend auf Genre
        energy_mapping = {
            'high': ['punk', 'metal', 'hardcore', 'dance', 'electronic', 'thrash', 'speed'],
            'medium': ['rock', 'pop', 'alternative', 'indie', 'funk', 'r&b'],
            'low': ['ambient', 'classical', 'folk', 'acoustic', 'ballad', 'new age']
        }
        
        for energy, keywords in energy_mapping.items():
            for keyword in keywords:
                if any(keyword.lower() in tag.lower() for tag in all_tags):
                    classification['energy_level'] = energy
                    break
            if classification['energy_level']:
                break
        
        # Tempo-Beschreibung basierend auf Genre
        tempo_mapping = {
            'very fast': ['thrash', 'speed', 'punk', 'hardcore'],
            'fast': ['rock', 'metal', 'dance', 'electronic'],
            'moderate': ['pop', 'alternative', 'indie', 'folk'],
            'slow': ['ballad', 'blues', 'ambient', 'classical'],
            'very slow': ['doom', 'funeral', 'drone']
        }
        
        for tempo, keywords in tempo_mapping.items():
            for keyword in keywords:
                if any(keyword.lower() in tag.lower() for tag in all_tags):
                    classification['tempo_description'] = tempo
                    break
            if classification['tempo_description']:
                break
        
        # Künstler-Ähnlichkeiten basierend auf Genre (erweitert werden kann)
        similarity_mapping = {
            'beatles': ['british invasion', 'merseybeat', '60s pop'],
            'queen': ['arena rock', 'theatrical rock', 'opera rock'],
            'led zeppelin': ['hard rock', 'blues rock', 'heavy metal'],
            'pink floyd': ['progressive rock', 'psychedelic', 'concept album'],
            'metallica': ['thrash metal', 'heavy metal', 'speed metal'],
            'elvis presley': ['rockabilly', '50s rock', 'classic rock'],
            'bob dylan': ['folk rock', 'protest song', 'singer-songwriter'],
            'david bowie': ['glam rock', 'art rock', 'experimental'],
            'michael jackson': ['pop', 'r&b', 'dance-pop'],
            'nirvana': ['grunge', 'alternative rock', '90s rock']
        }
        
        for artist, keywords in similarity_mapping.items():
            for keyword in keywords:
                if any(keyword.lower() in tag.lower() for tag in all_tags):
                    similarity = f"similar to {artist.title()}"
                    if similarity not in classification['similar_artists']:
                        classification['similar_artists'].append(similarity)
        
        # Limitiere Listen auf sinnvolle Größen
        classification['mood'] = classification['mood'][:3]
        classification['style'] = classification['style'][:3]
        classification['similar_artists'] = classification['similar_artists'][:2]
        classification['instrumentation'] = classification['instrumentation'][:3]
        
        return classification
