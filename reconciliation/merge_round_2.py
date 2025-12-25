import os
import csv
import pandas as pd
from pathlib import Path

print("="*70)
print("MASTER LIBRARY COMPILER")
print("="*70)

# ==========================================
# ALL PATHS - FULLY CONFIGURED
# ==========================================
base_dir = r"C:\Users\fulmi\Downloads\Set Lists"
crates_dir = r"C:\Users\fulmi\Downloads\Set Lists\GF"
music_dir = r"C:\Users\rmmcc\OneDrive\Documents\Music"

# Main data files (in base_dir)
mik_export = base_dir + r"\mik_full_export.csv"
enriched_file = base_dir + r"\essential_mix_final_enriched.csv"
crate_tags_file = base_dir + r"\all_tracks_crate_tags.csv"

# Output files
output_master = base_dir + r"\master_library.csv"
output_mapping = base_dir + r"\setlists_crates_mapping.xlsx"

# ==========================================

print("\n" + "="*70)
print("PHASE 1: EXTRACTING SETLIST TITLES & CRATE FILENAMES")
print("="*70)

# Find all .csv setlist files in base_dir
setlist_csvs = []
for file in os.listdir(base_dir):
    if file.endswith('.csv') and file not in ['all_tracks_crate_tags.csv', 'essential_mix_final_enriched.csv', 'mik_full_export.csv', 'master_library.csv']:
        setlist_csvs.append(file)

print(f"\nSetlist CSV files in {base_dir}:")
for s in sorted(setlist_csvs)[:5]:
    print(f"  - {s}")
if len(setlist_csvs) > 5:
    print(f"  ... and {len(setlist_csvs) - 5} more")

# Find all .crate files in crates_dir
crate_files = []
if os.path.exists(crates_dir):
    for file in os.listdir(crates_dir):
        if file.endswith('.crate'):
            crate_files.append(file)
    print(f"\nCrate files in {crates_dir}:")
    for c in sorted(crate_files)[:5]:
        print(f"  - {c}")
    if len(crate_files) > 5:
        print(f"  ... and {len(crate_files) - 5} more")
else:
    print(f"\n⚠ Crates directory not found: {crates_dir}")

print(f"\n✓ Found {len(setlist_csvs)} setlist CSV files")
print(f"✓ Found {len(crate_files)} crate files\n")

# Create mapping spreadsheet
print("Creating mapping spreadsheet...")
with pd.ExcelWriter(output_mapping, engine='openpyxl') as writer:
    # Sheet 1: Setlist titles
    setlists_df = pd.DataFrame({
        'setlist_filename': sorted(setlist_csvs),
        'mapped_crate': [''] * len(setlist_csvs),
        'notes': [''] * len(setlist_csvs)
    })
    setlists_df.to_excel(writer, sheet_name='Setlists', index=False)
    
    # Sheet 2: Crate filenames
    crates_df = pd.DataFrame({
        'crate_filename': sorted(crate_files),
        'mapped_setlist': [''] * len(crate_files),
        'notes': [''] * len(crate_files)
    })
    crates_df.to_excel(writer, sheet_name='Crates', index=False)

print(f"✓ Mapping spreadsheet created: {output_mapping}")
print(f"  - Sheet 'Setlists': {len(setlist_csvs)} setlist files")
print(f"  - Sheet 'Crates': {len(crate_files)} crate files")

print("\n" + "="*70)
print("PHASE 2: BUILDING MASTER DATASET")
print("="*70)

def get_track_key(df):
    """Create track key from whatever artist/title columns exist"""
    # Look for track name column
    track_col = next((col for col in df.columns if col.lower() in ['track name', 'title']), None)
    # Look for artist column
    artist_col = next((col for col in df.columns if col.lower() in ['artist name', 'artist']), None)
    
    if artist_col and track_col:
        return (df[artist_col].fillna('') + ' | ' + df[track_col].fillna('')).str.lower().str.strip()
    elif artist_col:
        return df[artist_col].fillna('').str.lower().str.strip()
    elif track_col:
        return df[track_col].fillna('').str.lower().str.strip()
    else:
        print("⚠ Could not find artist or title columns")
        return df.index.astype(str)

# Load MIK export (source of truth)
print("\nLoading MIK export...")
if not os.path.exists(mik_export):
    print(f"✗ ERROR: MIK export not found: {mik_export}")
    exit()
mik_df = pd.read_csv(mik_export)
print(f"✓ MIK: {len(mik_df)} tracks")
print(f"  Columns: {list(mik_df.columns[:5])}...")

mik_df['track_key'] = get_track_key(mik_df)

# Load enriched data
print("\nLoading enriched data...")
enriched_df = None
if os.path.exists(enriched_file):
    enriched_df = pd.read_csv(enriched_file)
    print(f"✓ Enriched: {len(enriched_df)} tracks")
    print(f"  Columns: {list(enriched_df.columns[:5])}...")
    
    # Rename enriched columns to match standard names
    enriched_rename = {
        'Track Name': 'title',
        'Artist Name(s)': 'artist',
        'Album Name': 'album',
        'Album Image URL': 'album_image_url',
        'Album Release Date': 'album_release_date',
        'Emotional Layers': 'emotional_layers',
        'Energy Level': 'energy_level',
        'Genre': 'genre',
        'Key (Camelot)': 'key_camelot',
        'Key (Open)': 'key_open',
        'Language': 'language',
        'Liminality': 'liminality',
        'Placement': 'placement',
        'Popularity': 'popularity',
        'Prominent Instruments': 'prominent_instruments',
        'Release Label': 'label',
        'Track BPM': 'bpm',
        'Spotify Track ID': 'spotify_id',
        'MusicBrainz Recording MBID': 'mbid',
        'ISRC': 'isrc',
        'Track Duration (min)': 'duration_min',
        'Track Preview URL': 'preview_url',
    }
    enriched_df = enriched_df.rename(columns=enriched_rename)
    enriched_df['track_key'] = get_track_key(enriched_df)
else:
    print(f"⚠ Enriched file not found: {enriched_file}")

# Load crate tags
print("Loading crate tags...")
crate_tags_df = None
if os.path.exists(crate_tags_file):
    crate_tags_df = pd.read_csv(crate_tags_file)
    print(f"✓ Crate tags: {len(crate_tags_df)} tracks")
    print(f"  Columns: {list(crate_tags_df.columns[:5])}...")
    crate_tags_df['track_key'] = get_track_key(crate_tags_df)
else:
    print(f"⚠ Crate tags file not found: {crate_tags_file}")

# Start with MIK as base (it's the authoritative source)
print("\nMerging datasets...")
master_df = mik_df.copy()

# Add enriched data where MIK doesn't have it
if enriched_df is not None:
    enriched_only_cols = [col for col in enriched_df.columns if col not in mik_df.columns and col != 'track_key']
    
    for idx, row in enriched_df.iterrows():
        if row['track_key'] in master_df['track_key'].values:
            mik_idx = master_df[master_df['track_key'] == row['track_key']].index[0]
            for col in enriched_only_cols:
                if pd.isna(master_df.loc[mik_idx, col]):
                    master_df.loc[mik_idx, col] = row[col]
        else:
            # Track exists in enriched but not in MIK - add it as supplementary
            new_row = enriched_df.iloc[idx].copy()
            master_df = pd.concat([master_df, pd.DataFrame([new_row])], ignore_index=True)
    
    print(f"✓ Merged enriched data ({len(enriched_only_cols)} new columns)")

# Add crate tags if available
if crate_tags_df is not None:
    crate_only_cols = [col for col in crate_tags_df.columns if col not in master_df.columns and col != 'track_key']
    
    for idx, row in crate_tags_df.iterrows():
        if row['track_key'] in master_df['track_key'].values:
            master_idx = master_df[master_df['track_key'] == row['track_key']].index[0]
            for col in crate_only_cols:
                if pd.isna(master_df.loc[master_idx, col]):
                    master_df.loc[master_idx, col] = row[col]
    
    print(f"✓ Merged crate tags ({len(crate_only_cols)} new columns)")

# Remove the temporary track_key column
master_df = master_df.drop(columns=['track_key'])

# Save master
master_df.to_csv(output_master, index=False)
print(f"\n✓ Master dataset saved: {output_master}")
print(f"  Total tracks: {len(master_df)}")
print(f"  Columns: {len(master_df.columns)}")

print("\n" + "="*70)
print("SUMMARY & NEXT STEPS")
print("="*70)
print(f"""
✓ Mapping file created: {output_mapping}
  - Sheet 'Setlists': {len(setlist_csvs)} setlist CSV files to map
  - Sheet 'Crates': {len(crate_files)} crate files to map
  - Fill in the mapping columns to link them (manual step)

✓ Master dataset created: {output_master}
  - MIK data is authoritative (NEVER overwritten)
  - Enriched data fills MIK gaps
  - Crate tags fill remaining gaps
  - {len(master_df)} total tracks
  - {len(master_df.columns)} total columns

NEXT STEPS:
  1. Edit {output_mapping} to map setlists to crates
  2. Once you've mapped them, tell me and I'll create phase 2 script
     to incorporate setlist membership into master dataset
""")
