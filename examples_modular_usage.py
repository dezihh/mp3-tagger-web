#!/usr/bin/env python3
"""
Beispiel-Skript für die Verwendung der modularen MP3-Tagger Funktionen
Zeigt die einzelne Verwendung jedes Moduls
"""

import os
import sys

# Pfad zum tagger Modul hinzufügen
sys.path.append('/home/dezi/tmp/mp3-tagger-web')

def example_metadata_enrichment():
    """Beispiel: Metadata Enrichment für einzelne Datei"""
    print("=" * 60)
    print("BEISPIEL 1: Metadaten-Anreicherung (metadata_enrichment.py)")
    print("=" * 60)
    
    from tagger.metadata_enrichment import enrich_file_metadata
    
    # Beispiel Datei-Struktur
    file_data = {
        'path': '/home/dezi/tmp/mp3-tagger-web/test_music/America - Greates Hits/America - A Horse With No Name.mp3',
        'filename': 'America - A Horse With No Name.mp3',
        'directory': '/home/dezi/tmp/mp3-tagger-web/test_music/America - Greates Hits',
        'current_artist': 'America',
        'current_title': 'A Horse With No Name',
        'current_album': 'Greates Hits',
        'current_genre': None,
        'current_has_cover': False
    }
    
    print("📁 Eingabe-Datei:")
    print(f"   Datei: {file_data['filename']}")
    print(f"   Aktueller Künstler: {file_data['current_artist']}")
    print(f"   Aktueller Titel: {file_data['current_title']}")
    
    if os.path.exists(file_data['path']):
        # Metadaten anreichern
        enriched = enrich_file_metadata(file_data)
        
        print("\n🎯 Angereicherte Metadaten:")
        print(f"   Vorgeschlagener Künstler: {enriched.get('suggested_artist')}")
        print(f"   Vorgeschlagener Titel: {enriched.get('suggested_title')}")
        print(f"   Vorgeschlagenes Album: {enriched.get('suggested_album')}")
        print(f"   Vorgeschlagenes Genre: {enriched.get('suggested_genre')}")
        print(f"   Cover verfügbar: {'Ja' if enriched.get('suggested_cover_url') else 'Nein'}")
    else:
        print("❌ Test-Datei nicht gefunden")

def example_audio_recognition():
    """Beispiel: Audio-Erkennung ohne vorhandene Metadaten"""
    print("\n" + "=" * 60)
    print("BEISPIEL 2: Audio-Erkennung (audio_recognition.py)")
    print("=" * 60)
    
    from tagger.audio_recognition import recognize_audio_file, recognize_with_shazam
    
    # Test mit America Song (als Beispiel für funktionierende Erkennung)
    test_file = '/home/dezi/tmp/mp3-tagger-web/test_music/America - Greates Hits/America - A Horse With No Name.mp3'
    
    print(f"📁 Audio-Datei: {os.path.basename(test_file)}")
    print("🎵 Versuche Audio-Erkennung ohne vorhandene Metadaten...")
    
    if os.path.exists(test_file):
        # Vollständige Audio-Erkennung (ShazamIO + AcoustID Fallback)
        result = recognize_audio_file(test_file)
        
        if result:
            print(f"\n✅ Erkannt über {result.get('service')}:")
            print(f"   Künstler: {result.get('artist')}")
            print(f"   Titel: {result.get('title')}")
            print(f"   Album: {result.get('album')}")
            print(f"   Konfidenz: {result.get('confidence', 0):.2f}")
            print(f"   Cover URL: {'Ja' if result.get('cover_url') else 'Nein'}")
            
            if result.get('streaming_links'):
                print(f"   Streaming-Plattformen: {', '.join(result['streaming_links'].keys())}")
        else:
            print("❌ Keine Erkennung möglich")
            
        # Nur ShazamIO testen
        print("\n🎤 Test nur mit ShazamIO:")
        shazam_result = recognize_with_shazam(test_file)
        if shazam_result:
            print(f"   ShazamIO Erfolg: {shazam_result.get('artist')} - {shazam_result.get('title')}")
        else:
            print("   ShazamIO fehlgeschlagen")
    else:
        print("❌ Test-Datei nicht gefunden")

def example_fingerprinting():
    """Beispiel: Audio-Fingerprinting und Feature-Extraktion"""
    print("\n" + "=" * 60)
    print("BEISPIEL 3: Audio-Fingerprinting (fingerprinting.py)")
    print("=" * 60)
    
    from tagger.fingerprinting import (
        create_audio_fingerprint, 
        extract_audio_features,
        get_audio_fingerprint_metadata
    )
    
    test_file = '/home/dezi/tmp/mp3-tagger-web/test_music/America - Greates Hits/America - A Horse With No Name.mp3'
    
    print(f"📁 Datei: {os.path.basename(test_file)}")
    
    if os.path.exists(test_file):
        # 1. Audio-Features extrahieren
        print("\n🔍 Audio-Features:")
        features = extract_audio_features(test_file)
        if features:
            print(f"   Dauer: {features.get('duration', 0):.1f} Sekunden")
            print(f"   Bitrate: {features.get('bitrate', 0):,} bps")
            print(f"   Sample Rate: {features.get('sample_rate', 0):,} Hz")
            print(f"   Kanäle: {features.get('channels', 0)}")
            print(f"   Codec: {features.get('codec', 'Unknown')}")
            print(f"   Dateigröße: {features.get('file_size', 0):,} Bytes")
        
        # 2. Audio-Fingerprint erstellen
        print("\n🔍 Audio-Fingerprint:")
        fingerprint = create_audio_fingerprint(test_file)
        if fingerprint:
            print(f"   Fingerprint erstellt: {len(fingerprint.get('fingerprint', ''))} Zeichen")
            print(f"   Fingerprint (Ausschnitt): {fingerprint.get('fingerprint', '')[:50]}...")
        
        # 3. Metadaten über Fingerprinting
        print("\n🎵 Fingerprint-basierte Metadaten:")
        meta = get_audio_fingerprint_metadata(test_file)
        if meta:
            print(f"   Service: {meta.get('service')}")
            print(f"   Erkannter Track: {meta.get('artist')} - {meta.get('title')}")
    else:
        print("❌ Test-Datei nicht gefunden")

def example_standalone_functions():
    """Beispiel: Standalone-Funktionen ohne Klassen"""
    print("\n" + "=" * 60)
    print("BEISPIEL 4: Standalone-Funktionen")
    print("=" * 60)
    
    # Import der standalone Funktionen
    from tagger.metadata_enrichment import enrich_multiple_files
    from tagger.audio_recognition import recognize_audio_file
    from tagger.fingerprinting import extract_audio_features
    
    print("📋 Alle Module bieten Standalone-Funktionen für einfache Verwendung:")
    print("")
    print("# Metadata Enrichment:")
    print("from tagger.metadata_enrichment import enrich_file_metadata, enrich_multiple_files")
    print("result = enrich_file_metadata(file_data)")
    print("")
    print("# Audio Recognition:")
    print("from tagger.audio_recognition import recognize_audio_file, recognize_with_shazam")  
    print("result = recognize_audio_file('/path/to/audio.mp3')")
    print("")
    print("# Audio Fingerprinting:")
    print("from tagger.fingerprinting import create_audio_fingerprint, extract_audio_features")
    print("features = extract_audio_features('/path/to/audio.mp3')")
    print("")
    print("✅ Alle Funktionen sind modular und unabhängig verwendbar!")

def main():
    """Hauptfunktion mit allen Beispielen"""
    print("🚀 MP3-TAGGER MODULARE FUNKTIONEN - VERWENDUNGSBEISPIELE")
    print("Demonstriert die einzelne Verwendung der separaten Module")
    
    example_metadata_enrichment()
    example_audio_recognition() 
    example_fingerprinting()
    example_standalone_functions()
    
    print("\n" + "=" * 60)
    print("✅ BEISPIELE ABGESCHLOSSEN")
    print("=" * 60)
    print("\nDie Modularisierung ist erfolgreich! Die Funktionen können jetzt")
    print("flexibel und unabhängig in anderen Projekten verwendet werden.")

if __name__ == "__main__":
    main()
