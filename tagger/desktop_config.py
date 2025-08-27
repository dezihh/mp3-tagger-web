"""
Konfiguration für die Desktop-Anwendung
"""

import os
from pathlib import Path


class DesktopConfig:
    """Konfiguration für die MP3 Tagger Desktop-Anwendung"""
    
    def __init__(self):
        self.app_name = "MP3 Tagger Desktop"
        self.version = "1.0.0"
        
        # Verzeichnisse
        self.app_dir = Path.home() / ".mp3tagger"
        self.config_file = self.app_dir / "config.json"
        self.history_file = self.app_dir / "directory_history.json"
        self.cache_dir = self.app_dir / "cache"
        
        # Stelle sicher, dass Verzeichnisse existieren
        self.app_dir.mkdir(exist_ok=True)
        self.cache_dir.mkdir(exist_ok=True)
        
        # Standard-Einstellungen
        self.default_settings = {
            'last_directory': str(Path.home()),
            'window_geometry': '1200x800',
            'remember_window_position': True,
            'auto_save_changes': False,
            'show_cover_previews': True,
            'max_directory_history': 10,
            'default_cover_size': 500,
            'supported_cover_formats': ['.jpg', '.jpeg', '.png'],
            'supported_audio_formats': ['.mp3'],
            'thread_pool_size': 4,
            'enable_audio_recognition': True,
            'enable_metadata_enrichment': True,
            'debug_mode': False
        }
        
        # API-Konfiguration (aus config.env laden wenn vorhanden)
        self.api_config = self._load_api_config()
        
    def _load_api_config(self):
        """Lädt API-Konfiguration aus config.env"""
        config_env_path = Path(__file__).parent.parent / "config.env"
        api_config = {}
        
        if config_env_path.exists():
            try:
                with open(config_env_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            api_config[key.strip()] = value.strip().strip('"\'')
            except Exception as e:
                print(f"Fehler beim Laden der API-Konfiguration: {e}")
                
        return api_config
        
    def get_setting(self, key, default=None):
        """Holt eine Einstellung"""
        settings = self.load_settings()
        return settings.get(key, default or self.default_settings.get(key))
        
    def set_setting(self, key, value):
        """Setzt eine Einstellung"""
        settings = self.load_settings()
        settings[key] = value
        self.save_settings(settings)
        
    def load_settings(self):
        """Lädt Einstellungen aus der Konfigurationsdatei"""
        if not self.config_file.exists():
            return self.default_settings.copy()
            
        try:
            import json
            with open(self.config_file, 'r', encoding='utf-8') as f:
                settings = json.load(f)
                
            # Merge mit Standard-Einstellungen für neue Optionen
            merged_settings = self.default_settings.copy()
            merged_settings.update(settings)
            return merged_settings
            
        except Exception as e:
            print(f"Fehler beim Laden der Einstellungen: {e}")
            return self.default_settings.copy()
            
    def save_settings(self, settings):
        """Speichert Einstellungen in die Konfigurationsdatei"""
        try:
            import json
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Fehler beim Speichern der Einstellungen: {e}")
            
    def get_api_key(self, service):
        """Holt einen API-Schlüssel für einen Service"""
        key_mappings = {
            'shazam': 'RAPIDAPI_KEY',
            'acoustid': 'ACOUSTID_API_KEY',
            'musicbrainz': 'MUSICBRAINZ_USER_AGENT',
            'lastfm': 'LASTFM_API_KEY',
            'discogs': 'DISCOGS_TOKEN',
            'spotify': 'SPOTIFY_CLIENT_ID'
        }
        
        env_key = key_mappings.get(service)
        if env_key:
            return self.api_config.get(env_key)
        return None
        
    def is_api_configured(self, service):
        """Prüft, ob ein API-Service konfiguriert ist"""
        return self.get_api_key(service) is not None


# Globale Konfigurationsinstanz
desktop_config = DesktopConfig()
