"""
Cover-Management-System für MP3 Tagger Web Application

Dieses Modul bietet umfassende Cover-Verwaltung auf Verzeichnis- und Datei-Ebene:
- Cover-Erkennung und Deduplizierung  
- Größen-Normalisierung (300x300px optimal)
- Batch-Operationen für ganze Verzeichnisse
- Integration mit externen Cover-Quellen

Hauptfunktionen:
- detect_covers(): Erkennt alle verfügbaren Cover-Quellen
- normalize_covers(): Konvertiert Cover zu Zielgröße
- apply_covers(): Wendet Cover-Auswahl auf MP3s an
- extract_covers(): Extrahiert Cover aus MP3s als Dateien

Verwendung:
    manager = CoverManager('/path/to/music')
    sources = manager.detect_covers()
    manager.apply_covers(target_source, target_size=(300, 300))
"""

import os
import hashlib
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from PIL import Image
import io
import requests
from mutagen.mp3 import MP3
from mutagen.id3 import ID3NoHeaderError, APIC
from pathlib import Path


@dataclass
class CoverSource:
    """Repräsentiert eine Cover-Quelle"""
    type: str  # 'internal', 'external', 'url'
    path: str  # Dateipfad oder URL
    size: Tuple[int, int]  # (width, height)
    format: str  # 'JPEG', 'PNG'
    hash: str  # MD5-Hash für Duplikat-Erkennung
    usage_count: int  # Anzahl der MP3s die dieses Cover verwenden
    preview_data: Optional[bytes] = None  # Thumbnail für UI


@dataclass
class DirectoryCoverInfo:
    """Cover-Informationen für ein ganzes Verzeichnis"""
    directory: str
    total_mp3_files: int
    files_with_covers: int
    files_without_covers: int
    unique_covers: List[CoverSource]
    external_cover_files: List[str]


class CoverManager:
    """Hauptklasse für Cover-Management"""
    
    # Unterstützte Bildformate
    SUPPORTED_IMAGE_FORMATS = {'.jpg', '.jpeg', '.png', '.bmp', '.gif'}
    SUPPORTED_COVER_NAMES = {
        'folder.jpg', 'cover.jpg', 'front.jpg', 'album.jpg',
        'folder.png', 'cover.png', 'front.png', 'album.png',
        'albumart.jpg', 'albumartsmall.jpg', 'albumartlarge.jpg'
    }
    
    # Optimale Cover-Größen
    TARGET_SIZES = {
        'small': (150, 150),
        'medium': (300, 300),  # Empfohlen
        'large': (500, 500),
        'xlarge': (800, 800)
    }
    
    def __init__(self, base_directory: str):
        """
        Initialisiert den Cover-Manager für ein Verzeichnis.
        
        Args:
            base_directory: Pfad zum Basis-Verzeichnis mit MP3-Dateien
        """
        self.base_directory = Path(base_directory)
        
        # Prüfe, ob Verzeichnis existiert
        if not self.base_directory.exists():
            raise FileNotFoundError(f"Verzeichnis nicht gefunden: {base_directory}")
        if not self.base_directory.is_dir():
            raise NotADirectoryError(f"Pfad ist kein Verzeichnis: {base_directory}")
            
        self.cover_cache = {}  # Cache für bereits analysierte Cover
        print(f"📁 CoverManager initialisiert für: {self.base_directory}")
        print(f"📊 Verzeichnis existiert: {self.base_directory.exists()}")
        print(f"📂 Ist Verzeichnis: {self.base_directory.is_dir()}")
        
    def analyze_directory_covers(self) -> DirectoryCoverInfo:
        """
        Analysiert alle Cover-Informationen in einem Verzeichnis.
        
        Returns:
            DirectoryCoverInfo mit vollständiger Cover-Analyse
        """
        mp3_files = list(self.base_directory.glob('*.mp3'))
        cover_sources = []
        files_with_covers = 0
        
        # 1. Interne Cover aus MP3s analysieren
        internal_covers = self._analyze_internal_covers(mp3_files)
        cover_sources.extend(internal_covers)
        
        # 2. Externe Cover-Dateien finden
        external_covers = self._find_external_covers()
        cover_sources.extend(external_covers)
        
        # 3. URL-basierte Cover aus MP3-Metadaten
        url_covers = self._extract_url_covers(mp3_files)
        cover_sources.extend(url_covers)
        
        # 4. Duplikate entfernen
        unique_covers = self._deduplicate_covers(cover_sources)
        
        # 5. Usage-Count berechnen
        for cover in unique_covers:
            cover.usage_count = self._count_cover_usage(cover, mp3_files)
        
        # Statistiken
        files_with_covers = sum(1 for f in mp3_files if self._has_internal_cover(f))
        
        return DirectoryCoverInfo(
            directory=str(self.base_directory),
            total_mp3_files=len(mp3_files),
            files_with_covers=files_with_covers,
            files_without_covers=len(mp3_files) - files_with_covers,
            unique_covers=unique_covers,
            external_cover_files=[str(f) for f in self.base_directory.glob('*') 
                                if f.suffix.lower() in self.SUPPORTED_IMAGE_FORMATS]
        )
    
    def _analyze_internal_covers(self, mp3_files: List[Path]) -> List[CoverSource]:
        """Analysiert interne Cover aus MP3-Dateien."""
        internal_covers = []
        processed_hashes = set()
        
        for mp3_file in mp3_files:
            try:
                audio = MP3(mp3_file)
                if 'APIC:' in audio:
                    apic = audio['APIC:']
                elif audio.tags:
                    # Suche nach beliebigen APIC-Tags
                    apic_tags = [tag for tag in audio.tags.values() if hasattr(tag, 'type') and hasattr(tag, 'data')]
                    if apic_tags:
                        apic = apic_tags[0]
                    else:
                        continue
                else:
                    continue
                
                # Bildgröße und Hash ermitteln
                image_data = apic.data
                image_hash = hashlib.md5(image_data).hexdigest()
                
                if image_hash not in processed_hashes:
                    try:
                        image = Image.open(io.BytesIO(image_data))
                        size = image.size
                        format_name = image.format or 'JPEG'
                        
                        # Thumbnail für Preview erstellen
                        thumbnail = image.copy()
                        thumbnail.thumbnail((100, 100), Image.Resampling.LANCZOS)
                        thumb_io = io.BytesIO()
                        thumbnail.save(thumb_io, format='JPEG', quality=85)
                        
                        internal_covers.append(CoverSource(
                            type='internal',
                            path=str(mp3_file),
                            size=size,
                            format=format_name,
                            hash=image_hash,
                            usage_count=0,  # Wird später berechnet
                            preview_data=thumb_io.getvalue()
                        ))
                        processed_hashes.add(image_hash)
                        
                    except Exception as e:
                        print(f"Fehler beim Verarbeiten des internen Covers von {mp3_file}: {e}")
                        
            except Exception as e:
                print(f"Fehler beim Lesen der MP3-Datei {mp3_file}: {e}")
        
        return internal_covers
    
    def _find_external_covers(self) -> List[CoverSource]:
        """Findet externe Cover-Dateien im Verzeichnis."""
        external_covers = []
        
        # Alle Bilddateien im Verzeichnis finden
        for image_file in self.base_directory.glob('*'):
            if image_file.suffix.lower() in self.SUPPORTED_IMAGE_FORMATS:
                try:
                    with Image.open(image_file) as image:
                        size = image.size
                        format_name = image.format
                        
                        # Hash der Datei berechnen
                        with open(image_file, 'rb') as f:
                            image_hash = hashlib.md5(f.read()).hexdigest()
                        
                        # Thumbnail erstellen
                        thumbnail = image.copy()
                        thumbnail.thumbnail((100, 100), Image.Resampling.LANCZOS)
                        thumb_io = io.BytesIO()
                        thumbnail.save(thumb_io, format='JPEG', quality=85)
                        
                        external_covers.append(CoverSource(
                            type='external',
                            path=str(image_file),
                            size=size,
                            format=format_name,
                            hash=image_hash,
                            usage_count=0,
                            preview_data=thumb_io.getvalue()
                        ))
                        
                except Exception as e:
                    print(f"Fehler beim Verarbeiten der externen Cover-Datei {image_file}: {e}")
        
        return external_covers
    
    def _extract_url_covers(self, mp3_files: List[Path]) -> List[CoverSource]:
        """Extrahiert URL-basierte Cover aus MP3-Metadaten."""
        url_covers = []
        processed_urls = set()
        
        for mp3_file in mp3_files:
            try:
                audio = MP3(mp3_file)
                if audio.tags:
                    # Suche nach URL-Tags (TXXX, COMM, etc.)
                    for tag in audio.tags.values():
                        if hasattr(tag, 'desc') and hasattr(tag, 'text'):
                            # TXXX-Tags nach Cover-URLs durchsuchen
                            if 'cover' in str(tag.desc).lower() or 'image' in str(tag.desc).lower():
                                url = str(tag.text[0]) if tag.text else ''
                                if url.startswith('http') and url not in processed_urls:
                                    # URL-Cover-Info erstellen (ohne Download für Performance)
                                    url_covers.append(CoverSource(
                                        type='url',
                                        path=url,
                                        size=(0, 0),  # Unbekannt bis zum Download
                                        format='JPEG',  # Annahme
                                        hash=hashlib.md5(url.encode()).hexdigest(),
                                        usage_count=0,
                                        preview_data=None  # Wird bei Bedarf geladen
                                    ))
                                    processed_urls.add(url)
            except Exception as e:
                print(f"Fehler beim Extrahieren der URL-Cover von {mp3_file}: {e}")
        
        return url_covers
    
    def _deduplicate_covers(self, cover_sources: List[CoverSource]) -> List[CoverSource]:
        """Entfernt Duplikate basierend auf Bild-Hash."""
        unique_covers = {}
        
        for cover in cover_sources:
            if cover.hash not in unique_covers:
                unique_covers[cover.hash] = cover
            else:
                # Bei Duplikaten: Bevorzuge interne Cover, dann externe, dann URLs
                existing = unique_covers[cover.hash]
                if (cover.type == 'internal' and existing.type != 'internal') or \
                   (cover.type == 'external' and existing.type == 'url'):
                    unique_covers[cover.hash] = cover
        
        return list(unique_covers.values())
    
    def _count_cover_usage(self, cover_source: CoverSource, mp3_files: List[Path]) -> int:
        """Zählt, wie viele MP3-Dateien dieses Cover verwenden."""
        if cover_source.type == 'internal':
            # Für interne Cover: Prüfe Hash-Übereinstimmung
            count = 0
            for mp3_file in mp3_files:
                if self._has_matching_internal_cover(mp3_file, cover_source.hash):
                    count += 1
            return count
        elif cover_source.type == 'external':
            # Externe Cover werden potentiell von allen Dateien ohne interne Cover verwendet
            return len([f for f in mp3_files if not self._has_internal_cover(f)])
        else:
            # URL-Cover: Schwer zu bestimmen, Standardwert
            return 0
    
    def _has_internal_cover(self, mp3_file: Path) -> bool:
        """Prüft, ob eine MP3-Datei ein internes Cover hat."""
        try:
            audio = MP3(mp3_file)
            return 'APIC:' in audio or any(hasattr(tag, 'type') and hasattr(tag, 'data') 
                                         for tag in audio.tags.values() if audio.tags)
        except:
            return False
    
    def _has_matching_internal_cover(self, mp3_file: Path, target_hash: str) -> bool:
        """Prüft, ob eine MP3-Datei ein Cover mit dem gegebenen Hash hat."""
        try:
            audio = MP3(mp3_file)
            if 'APIC:' in audio:
                apic = audio['APIC:']
                image_hash = hashlib.md5(apic.data).hexdigest()
                return image_hash == target_hash
        except:
            pass
        return False
    
    def apply_cover_to_directory(self, cover_source: CoverSource, 
                               target_size: Tuple[int, int] = (300, 300),
                               delete_external: bool = False) -> Dict[str, Any]:
        """
        Wendet ein Cover auf alle MP3-Dateien im Verzeichnis an.
        
        Args:
            cover_source: Das zu verwendende Cover
            target_size: Zielgröße für das Cover
            delete_external: Ob externe Cover-Dateien gelöscht werden sollen
            
        Returns:
            Dict mit Ergebnissen der Operation
        """
        mp3_files = list(self.base_directory.glob('*.mp3'))
        results = {
            'success': 0,
            'errors': 0,
            'processed_files': [],
            'error_files': []
        }
        
        # Cover-Daten laden und normalisieren
        try:
            cover_data = self._load_and_normalize_cover(cover_source, target_size)
        except Exception as e:
            return {'error': f'Fehler beim Laden des Covers: {e}'}
        
        # Cover auf alle MP3-Dateien anwenden
        for mp3_file in mp3_files:
            try:
                self._apply_cover_to_file(mp3_file, cover_data)
                results['success'] += 1
                results['processed_files'].append(str(mp3_file))
            except Exception as e:
                results['errors'] += 1
                results['error_files'].append({'file': str(mp3_file), 'error': str(e)})
        
        # Externe Dateien löschen falls gewünscht
        if delete_external and cover_source.type == 'external':
            try:
                os.remove(cover_source.path)
                results['external_file_deleted'] = cover_source.path
            except Exception as e:
                results['external_delete_error'] = str(e)
        
        return results
    
    def _load_and_normalize_cover(self, cover_source: CoverSource, 
                                target_size: Tuple[int, int]) -> bytes:
        """Lädt und normalisiert Cover-Daten."""
        if cover_source.type == 'internal':
            # Aus MP3-Datei extrahieren
            audio = MP3(cover_source.path)
            if 'APIC:' in audio:
                image_data = audio['APIC:'].data
            else:
                apic_tags = [tag for tag in audio.tags.values() 
                           if hasattr(tag, 'type') and hasattr(tag, 'data')]
                image_data = apic_tags[0].data
                
        elif cover_source.type == 'external':
            # Aus Datei laden
            with open(cover_source.path, 'rb') as f:
                image_data = f.read()
                
        elif cover_source.type == 'url':
            # Von URL herunterladen
            response = requests.get(cover_source.path, timeout=10)
            response.raise_for_status()
            image_data = response.content
        else:
            raise ValueError(f"Unbekannter Cover-Typ: {cover_source.type}")
        
        # Größe anpassen
        image = Image.open(io.BytesIO(image_data))
        if image.size != target_size:
            image = image.resize(target_size, Image.Resampling.LANCZOS)
        
        # Als JPEG mit optimaler Qualität speichern
        output = io.BytesIO()
        if image.mode in ('RGBA', 'LA', 'P'):
            # Transparenz entfernen für JPEG
            background = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'P':
                image = image.convert('RGBA')
            background.paste(image, mask=image.split()[-1] if image.mode in ('RGBA', 'LA') else None)
            image = background
        
        image.save(output, format='JPEG', quality=95, optimize=True)
        return output.getvalue()
    
    def _apply_cover_to_file(self, mp3_file: Path, cover_data: bytes):
        """Wendet Cover-Daten auf eine MP3-Datei an."""
        try:
            audio = MP3(mp3_file)
            if audio.tags is None:
                audio.add_tags()
            
            # Bestehende Cover entfernen
            audio.tags.delall('APIC')
            
            # Neues Cover hinzufügen
            audio.tags.add(APIC(
                encoding=3,  # UTF-8
                mime='image/jpeg',
                type=3,  # Cover (front)
                desc='Cover',
                data=cover_data
            ))
            
            audio.save()
            
        except Exception as e:
            raise Exception(f"Fehler beim Speichern des Covers in {mp3_file}: {e}")
    
    def remove_all_covers(self) -> Dict[str, Any]:
        """Entfernt alle Cover aus allen MP3-Dateien im Verzeichnis."""
        mp3_files = list(self.base_directory.glob('*.mp3'))
        results = {
            'success': 0,
            'errors': 0,
            'processed_files': [],
            'error_files': []
        }
        
        for mp3_file in mp3_files:
            try:
                audio = MP3(mp3_file)
                if audio.tags:
                    audio.tags.delall('APIC')
                    audio.save()
                    results['success'] += 1
                    results['processed_files'].append(str(mp3_file))
            except Exception as e:
                results['errors'] += 1
                results['error_files'].append({'file': str(mp3_file), 'error': str(e)})
        
        return results


def create_cover_manager(directory: str) -> CoverManager:
    """Factory-Funktion für CoverManager-Instanzen."""
    return CoverManager(directory)
