# Representative reconciliation stage.
# Demonstrates fuzzy matching + ambiguity surfacing prior to HITL resolution.

# PIPELINE ENTRY POINT (representative)
# Demonstrates extraction, normalization, and downstream reconciliation patterns
# used across the broader metadata ETL system.

import os
import re
import csv

def restore_filename(spaced_string):
    """Remove spaces from spaced text, e.g. 'U s e r s' -> 'Users'"""
    return ''.join(spaced_string.split())

def extract_paths_from_crate(crate_file, base_path_only=True):
    """Extract audio file paths from a Serato .crate file"""
    # Pattern: look for paths starting with 'U s e r s' and ending in ') . m p 3' (or other extensions)
    pattern = re.compile(r'(U s e r s [^ -]*?\) \. (m p 3|w a v|a i f f|f l a c|m p 4))', re.DOTALL)
    paths = set()
    with open(crate_file, 'r', encoding='utf-8', errors='ignore') as f_in:
        data = f_in.read()
        for match in re.finditer(pattern, data):
            spaced_path = match.group(1)
            # Remove all spaces to restore the real filename
            path = restore_filename(spaced_path)
            if base_path_only:
                path = os.path.basename(path).strip().lower()
            paths.add(path)
    return paths

def build_crate_tag_lookup(crate_folder):
    """Scan all .crate files and build a mapping: filename -> set of crate tags"""
    crate_tag_lookup = {}
    total_crates = 0
    total_tracks = 0
    for filename in os.listdir(crate_folder):
        if filename.endswith('.crate'):
            total_crates += 1
            crate_tag = os.path.splitext(filename)[0]
            crate_paths = extract_paths_from_crate(os.path.join(crate_folder, filename), base_path_only=True)
            total_tracks += len(crate_paths)
            for fname in crate_paths:
                crate_tag_lookup.setdefault(fname, set()).add(crate_tag)
    print(f"Processed {total_crates} crates, found {total_tracks} total track references")
    print(f"Unique tracks: {len(crate_tag_lookup)}")
    return crate_tag_lookup

def export_crate_tags(crate_tag_lookup, output_csv):
    """Export the lookup table to a CSV file"""
    with open(output_csv, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['filename', 'crate_tags'])
        for fname, tags in crate_tag_lookup.items():
            writer.writerow([fname, ', '.join(sorted(tags))])
    print(f"Exported to {output_csv}")

# Usage:
if __name__ == "__main__":
    crate_folder = r'C:\Users\fulmi\Downloads\GF'  # Change to your folder path
    crate_tag_lookup = build_crate_tag_lookup(crate_folder)
    export_crate_tags(crate_tag_lookup, 'all_tracks_crate_tags.csv')
    print("Done!")
