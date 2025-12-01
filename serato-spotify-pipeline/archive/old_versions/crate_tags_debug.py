import os
import csv
import re

def get_raw_file_paths(crate_file):
    """Extract track filenames from Serato .crate files"""
    # NULL-separated extensions (how Serato encodes them)
    extensions = [
        b'.\x00m\x00p\x003',
        b'.\x00w\x00a\x00v',
        b'.\x00a\x00i\x00f\x00f',
        b'.\x00f\x00l\x00a\x00c',
        b'.\x00m\x00p\x004',
        b'.\x00M\x00P\x003',  # Uppercase variants
        b'.\x00W\x00A\x00V',
        b'.\x00A\x00I\x00F\x00F',
        b'.\x00F\x00L\x00A\x00C',
        b'.\x00M\x00P\x004'
    ]
    
    paths = set()
    
    try:
        with open(crate_file, "rb") as f:
            data = f.read()
        
        # Find otrk markers
        matches = list(re.finditer(b'otrk.{4}ptrk.{4}', data))
        
        for match in matches:
            start_pos = match.end()
            segment = data[start_pos:start_pos + 1000]
            
            # Look for any of our extensions in this segment
            for ext_b in extensions:
                if ext_b in segment:
                    # Find where extension starts
                    ext_idx = segment.find(ext_b)
                    # Extract the path from start to end of extension
                    path_segment = segment[:ext_idx + len(ext_b)]
                    
                    # Decode by removing NULL bytes
                    path_clean = path_segment.replace(b'\x00', b'').decode('utf-8', errors='ignore')
                    
                    if path_clean:
                        # Handle both forward and back slashes
                        filename = path_clean.split('/')[-1].split('\\')[-1].strip()
                        
                        # Use regex to extract valid filename pattern
                        clean_match = re.search(r'([a-zA-Z0-9][\w\s\-\(\)\[\]\{\}\',\.&]+\.(?:mp3|wav|flac|aiff|mp4))', filename, re.IGNORECASE)
                        
                        if clean_match:
                            filename = clean_match.group(1).strip()
                            if filename and len(filename) > 3:
                                paths.add(filename.lower())
                    break
    
    except Exception as e:
        print(f"Error processing {crate_file}: {e}")
    
    return paths


def build_crate_tag_lookup(crate_folder):
    """Build lookup dict of filename -> set of crate tags"""
    crate_tag_lookup = {}
    crate_files = [f for f in os.listdir(crate_folder) if f.endswith('.crate')]
    
    print(f"Found {len(crate_files)} .crate files")
    print("Processing...\n")
    
    for idx, filename in enumerate(crate_files, 1):
        crate_tag = os.path.splitext(filename)[0]
        crate_path = os.path.join(crate_folder, filename)
        
        crate_paths = get_raw_file_paths(crate_path)
        
        if idx % 10 == 0 or idx == len(crate_files):
            print(f"[{idx}/{len(crate_files)}] Processed {crate_tag}: {len(crate_paths)} tracks")
        
        for fname in crate_paths:
            crate_tag_lookup.setdefault(fname, set()).add(crate_tag)
    
    return crate_tag_lookup


def export_crate_tags(crate_tag_lookup, output_csv):
    """Export lookup to CSV"""
    with open(output_csv, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['filename', 'crate_tags'])
        
        # Sort by filename for easier browsing
        for fname in sorted(crate_tag_lookup.keys()):
            tags = crate_tag_lookup[fname]
            writer.writerow([fname, ', '.join(sorted(tags))])
    
    print(f"\n✓ Exported {len(crate_tag_lookup)} unique tracks to {output_csv}")


# === USAGE ===
if __name__ == "__main__":
    # Update this to your crate folder
    crate_folder = r'C:\Users\fulmi\Downloads\GF'
    output_csv = 'all_tracks_crate_tags.csv'
    
    print(f"Scanning crate folder: {crate_folder}\n")
    
    crate_tag_lookup = build_crate_tag_lookup(crate_folder)
    export_crate_tags(crate_tag_lookup, output_csv)
    
    print("\nDone!")