import os
import csv
from pathlib import Path
from mutagen.id3 import ID3

# ==========================================
# CONFIGURE THIS
# ==========================================
music_dir = r"C:\Users\rmmcc\OneDrive\Documents\Music"
output_csv = "mik_full_export.csv"
# ==========================================

tracks = []

print(f"Scanning {music_dir}...\n")

for root, dirs, files in os.walk(music_dir):
    for file in files:
        if file.lower().endswith('.mp3'):
            filepath = os.path.join(root, file)
            
            tags = {
                'filepath': filepath,
                'artist': '',
                'title': '',
                'album': '',
                'bpm': '',
                'key': '',
                'energy': '',
                'genre': '',
                'label': '',
                'year': '',
                'isrc': '',
                'remixer': '',
                'copyright': '',
                'has_cover': ''
            }
            
            try:
                audio = ID3(filepath)
                
                tags['artist'] = str(audio.get('TPE1', '')).strip() or ''
                tags['title'] = str(audio.get('TIT2', '')).strip() or ''
                tags['album'] = str(audio.get('TALB', '')).strip() or ''
                tags['bpm'] = str(audio.get('TBPM', '')).strip() or ''
                tags['key'] = str(audio.get('TKEY', '')).strip() or ''
                tags['genre'] = str(audio.get('TCON', '')).strip() or ''
                tags['label'] = str(audio.get('TPUB', '')).strip() or ''
                tags['year'] = str(audio.get('TDRC', audio.get('TYER', ''))).strip() or ''
                tags['isrc'] = str(audio.get('TSRC', '')).strip() or ''
                tags['remixer'] = str(audio.get('TPE4', '')).strip() or ''
                tags['copyright'] = str(audio.get('TCOP', '')).strip() or ''
                
                # Check for cover art
                tags['has_cover'] = 'Yes' if any(k.startswith('APIC') for k in audio.keys()) else 'No'
                
                # Get comment (energy level)
                for key in audio.keys():
                    if key.startswith('COMM'):
                        tags['energy'] = str(audio.get(key, '')).strip()
                        break
                
                print(f"✓ {file}")
                
            except Exception as e:
                print(f"⚠ {file}: {e}")
            
            tracks.append(tags)

print(f"\n{'='*60}")
print(f"Found {len(tracks)} MP3 tracks")

if tracks:
    with open(output_csv, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['filepath', 'artist', 'title', 'album', 'bpm', 'key', 'energy', 
                      'genre', 'label', 'year', 'isrc', 'remixer', 'copyright', 'has_cover']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(tracks)
    
    print(f"\n✓ Export complete: {os.path.abspath(output_csv)}")
