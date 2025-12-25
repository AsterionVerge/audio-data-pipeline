import os
import pandas as pd
from pathlib import Path

print("="*70)
print("FINAL MASTER LIBRARY BUILD")
print("="*70)

# ==========================================
# PATHS
# ==========================================
base_dir = r"C:\Users\fulmi\Downloads\Set Lists"

enriched_file = base_dir + r"\essential_mix_final_enriched.csv"
mik_export = base_dir + r"\mik_full_export.csv"
crate_tags_file = base_dir + r"\all_tracks_crate_tags.csv"
mapping_file = base_dir + r"\setlists_crates_mapping.xlsx"

output_master = base_dir + r"\master_library_final.csv"

# ==========================================

print("\n" + "="*70)
print("STEP 1: LOAD MAPPING")
print("="*70)

# Load crate mapping
mapping_crates = pd.read_excel(mapping_file, sheet_name='Crates')
mapping_crates = mapping_crates[mapping_crates['mapped_header'].notna()]

print(f"✓ Loaded {len(mapping_crates)} crate mappings")

# Build mapping: crate_name → list of (header, selection) tuples
crate_to_categories = {}
for idx, row in mapping_crates.iterrows():
    crate_name = row['crate_filename'].replace('.crate', '')
    header = row['mapped_header']
    selections = row['mapped_selection']
    
    if pd.isna(selections):
        continue
    
    # Split on semicolon for multiple selections
    selection_list = [s.strip() for s in str(selections).split(';')]
    
    crate_to_categories[crate_name] = [(header.strip(), sel) for sel in selection_list]

print(f"✓ Built crate→category mapping")

print("\n" + "="*70)
print("STEP 2: LOAD ENRICHED (MASTER)")
print("="*70)

master_df = pd.read_csv(enriched_file)
print(f"✓ Enriched master: {len(master_df)} tracks")

# Create track key
master_df['track_key'] = (master_df['Artist Name(s)'].fillna('') + ' | ' + master_df['Track Name'].fillna('')).str.lower().str.strip()

print("\n" + "="*70)
print("STEP 3: MERGE MIK DATA")
print("="*70)

mik_df = pd.read_csv(mik_export)
print(f"✓ MIK export: {len(mik_df)} tracks")

# Extract energy: "4A - 123.00 - 6" → "6"
def extract_energy(energy_str):
    if pd.isna(energy_str):
        return None
    energy_str = str(energy_str).strip()
    if 'Purchased' in energy_str or energy_str == '':
        return None
    parts = energy_str.split(' - ')
    if len(parts) >= 3:
        try:
            return int(parts[-1].strip())
        except:
            return None
    return None

mik_df['energy_extracted'] = mik_df['energy'].apply(extract_energy)
mik_df['track_key'] = (mik_df['artist'].fillna('') + ' | ' + mik_df['title'].fillna('')).str.lower().str.strip()

merged_count = 0
for idx, mik_row in mik_df.iterrows():
    if mik_row['track_key'] in master_df['track_key'].values:
        master_idx = master_df[master_df['track_key'] == mik_row['track_key']].index[0]
        
        # Fill Track BPM
        if pd.isna(master_df.loc[master_idx, 'Track BPM']) and pd.notna(mik_row['bpm']):
            master_df.loc[master_idx, 'Track BPM'] = mik_row['bpm']
            merged_count += 1
        
        # Fill Energy
        if pd.isna(master_df.loc[master_idx, 'Energy']) and pd.notna(mik_row['energy_extracted']):
            master_df.loc[master_idx, 'Energy'] = mik_row['energy_extracted']
        
        # Fill other MIK fields if enriched is empty
        if pd.isna(master_df.loc[master_idx, 'Release Label']) and pd.notna(mik_row['label']):
            master_df.loc[master_idx, 'Release Label'] = mik_row['label']
        
        if pd.isna(master_df.loc[master_idx, 'ISRC']) and pd.notna(mik_row['isrc']):
            master_df.loc[master_idx, 'ISRC'] = mik_row['isrc']

print(f"✓ Merged MIK data into {merged_count} tracks")

print("\n" + "="*70)
print("STEP 4: PARSE CRATE TAGS INTO COLUMNS")
print("="*70)

crate_tags_df = pd.read_csv(crate_tags_file)
print(f"✓ Crate tags: {len(crate_tags_df)} tracks")

# For each track in crate_tags, parse and add to appropriate column
crate_count = 0
for idx, crate_row in crate_tags_df.iterrows():
    filename = crate_row['filename']
    crate_tags_str = str(crate_row['crate_tags']).strip()
    
    if pd.isna(crate_tags_str) or crate_tags_str == '':
        continue
    
    # Split crate tags
    crates = [c.strip() for c in crate_tags_str.split(';')]
    
    # Find matching track in master by filepath
    matching = master_df[master_df['filepath'] == filename]
    
    if matching.empty:
        continue
    
    match_idx = matching.index[0]
    
    # For each crate this track is in, add its categories
    for crate_name in crates:
        if crate_name in crate_to_categories:
            for header, selection in crate_to_categories[crate_name]:
                col_name = header.strip()
                
                # Get current value
                current = master_df.loc[match_idx, col_name]
                
                # Append selection if not already there
                if pd.isna(current) or current == '':
                    master_df.loc[match_idx, col_name] = selection
                elif selection not in str(current):
                    master_df.loc[match_idx, col_name] = f"{current}; {selection}"
                
                crate_count += 1

print(f"✓ Populated {crate_count} crate category entries")

# Remove temporary columns
master_df = master_df.drop(columns=['track_key'])

# Save
master_df.to_csv(output_master, index=False)
print(f"\n✓ Master dataset saved: {output_master}")
print(f"  Total tracks: {len(master_df)}")
print(f"  Total columns: {len(master_df.columns)}")

print("\n" + "="*70)
print("COMPLETE")
print("="*70)
