#!/usr/bin/env python3

import sys
import os
sys.path.append('/home/dezi/tmp/mp3-tagger-web')

import eyed3
from tagger.core import MusicTagger

def debug_mp3_covers(file_path):
    print(f"=== Debugging MP3 Cover: {file_path} ===")
    
    try:
        # Lade mit verschiedenen ID3-Versionen
        audio = eyed3.load(file_path)
        if not audio:
            print("❌ Could not load audio file")
            return
        
        print("✅ Audio loaded successfully")
        print(f"File size: {audio.info.size_bytes} bytes")
        print(f"Duration: {audio.info.time_secs} seconds")
        
        # ID3 Tag Informationen
        if not audio.tag:
            print("❌ No tag found")
            audio.initTag()
            print("✅ Initialized new tag")
        
        tag = audio.tag
        print(f"Tag version: {tag.version}")
        print(f"Tag type: {type(tag)}")
        
        # Prüfe alle verfügbaren Methoden für Cover
        print("\n=== Checking for cover images ===")
        
        # Methode 1: Images Accessor
        try:
            images = tag.images
            print(f"Images accessor: {images} (type: {type(images)})")
            if images:
                image_list = list(images)
                print(f"Images as list: {len(image_list)} items")
                for i, img in enumerate(image_list):
                    print(f"  Image {i}: {img}")
        except Exception as e:
            print(f"❌ Images accessor error: {e}")
        
        # Methode 2: Frame Set Details
        if hasattr(tag, 'frame_set'):
            frame_set = tag.frame_set
            print(f"\nFrame set: {frame_set} (type: {type(frame_set)})")
            print(f"Frame set length: {len(frame_set)}")
            
            # Prüfe jeden Frame genauer
            for i, frame in enumerate(frame_set):
                print(f"\nFrame {i}:")
                print(f"  Type: {type(frame)}")
                print(f"  Content: {repr(frame)[:100]}...")
                print(f"  Length: {len(frame) if hasattr(frame, '__len__') else 'N/A'}")
                
                # Wenn es bytes sind, schaue nach APIC-Header
                if isinstance(frame, bytes):
                    if b'APIC' in frame[:20]:  # APIC sollte am Anfang stehen
                        print(f"  ✅ Found APIC in frame {i}")
                        print(f"  APIC position: {frame.find(b'APIC')}")
                    if b'PIC' in frame[:20]:  # Ältere ID3v2.2 Format
                        print(f"  ✅ Found PIC in frame {i}")
                        print(f"  PIC position: {frame.find(b'PIC')}")
                    # Schaue nach JPEG/PNG Header
                    if b'\xff\xd8\xff' in frame:  # JPEG header
                        print(f"  ✅ Found JPEG data in frame {i}")
                    if b'\x89PNG' in frame:  # PNG header
                        print(f"  ✅ Found PNG data in frame {i}")
        
        # Methode 3: Versuche raw ID3 parsing
        print(f"\n=== Raw file analysis ===")
        with open(file_path, 'rb') as f:
            # Lese ersten Teil der Datei
            data = f.read(8192)  # Erste 8KB
            
            # Suche nach ID3v2 Header
            if data.startswith(b'ID3'):
                print("✅ Found ID3v2 header")
                version = data[3:5]
                print(f"ID3 version: 2.{version[0]}.{version[1]}")
                
                # Suche nach APIC frames
                apic_pos = data.find(b'APIC')
                if apic_pos != -1:
                    print(f"✅ Found APIC at position {apic_pos}")
                
                # Suche nach PIC frames (ID3v2.2)
                pic_pos = data.find(b'PIC')
                if pic_pos != -1:
                    print(f"✅ Found PIC at position {pic_pos}")
                
                # Suche nach Bildformaten
                jpeg_pos = data.find(b'\xff\xd8\xff')
                if jpeg_pos != -1:
                    print(f"✅ Found JPEG data at position {jpeg_pos}")
                
                png_pos = data.find(b'\x89PNG')
                if png_pos != -1:
                    print(f"✅ Found PNG data at position {png_pos}")
            else:
                print("❌ No ID3v2 header found")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_file = "/home/dezi/tmp/mp3ren/mp3s/America/America - Greates Hits/America - Sister Golden Hair.mp3"
    debug_mp3_covers(test_file)
