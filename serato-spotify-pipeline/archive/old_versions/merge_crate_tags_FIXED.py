import pandas as pd
import re

def normalize_track_name(track_name):
    """
    Normalize track name for fuzzy matching.
    Handles possessives, remix info in both parentheses and dash formats.
    """
    if pd.isna(track_name):
        return ""
    
    track_name = str(track_name).strip()
    
    # Remove file extensions
    track_name = re.sub(r'\.(mp3|wav|flac|m4a|aac|ogg|wma)$', '', track_name, flags=re.IGNORECASE)
    
    # CRITICAL: Normalize possessives FIRST (before removing underscores)
    # This handles "umai_s dance" vs "umai's dance" mismatch
    track_name = re.sub(r"_s\b", "s", track_name)  # umai_s → umais
    track_name = re.sub(r"'s\b", "s", track_name)  # umai's → umais
    
    # Remove remix/mix info in PARENTHESES format: (original mix), _(extended mix), etc.
    # This must happen BEFORE underscore replacement
    track_name = re.sub(r'[\s_]*\(.*?\)[\s_]*$', '', track_name)
    track_name = re.sub(r'_\(.*$', '', track_name)  # Catch _( without closing paren
    
    # Remove remix/mix info in DASH format: - Extended Mix, - Durante Remix, etc.
    # Common in Spotify/tracklist formatting
    track_name = re.sub(r'\s*-\s*(extended|original|club|radio|vocal|instrumental|dub|edit|mix|remix).*$', '', track_name, flags=re.IGNORECASE)
    track_name = re.sub(r'\s*-\s*\w+\s+(remix|mix|edit|rework|version).*$', '', track_name, flags=re.IGNORECASE)
    
    # Now replace remaining underscores with spaces
    track_name = track_name.replace('_', ' ')
    
    # Remove apostrophes (for remaining cases like "don't")
    track_name = track_name.replace("'", '')
    
    # Remove "feat." and "ft." patterns (keep the artist but remove the prefix)
    track_name = re.sub(r'\s+feat\.?\s+', ' ', track_name, flags=re.IGNORECASE)
    track_name = re.sub(r'\s+ft\.?\s+', ' ', track_name, flags=re.IGNORECASE)
    
    # Remove all special characters except spaces and alphanumerics
    track_name = re.sub(r'[^\w\s]', '', track_name)
    
    # Convert to lowercase
    track_name = track_name.lower()
    
    # Remove extra whitespace
    track_name = re.sub(r'\s+', ' ', track_name).strip()
    
    return track_name


# INPUT FILES
print("="*60)
print("INPUT FILES:")
print("  - crate_tags.csv")
print("  - tracklist_full.csv")
print("="*60)

# Read the datasets
print("\nReading datasets...")
crate_tags = pd.read_csv('crate_tags.csv')
tracklist_full = pd.read_csv('tracklist_full.csv')

print(f"Crate tags rows: {len(crate_tags)}")
print(f"Tracklist full rows: {len(tracklist_full)}")

# Convert metadata columns to object dtype to allow overwrites
metadata_columns = ['Subgenre', 'Emotionality', 'Genre', 'Prominent Instruments', 'Sound', 'Set', 'Vibe', 'Placement']
for col in metadata_columns:
    if col in tracklist_full.columns:
        tracklist_full[col] = tracklist_full[col].astype('object')

print("Normalizing track names...")
# Create normalized columns for matching
crate_tags['_normalized_track'] = crate_tags['Track Name'].apply(normalize_track_name)
tracklist_full['_normalized_track'] = tracklist_full['Track Name'].apply(normalize_track_name)

# Create a dictionary for fast lookups
tracklist_dict = {}
for idx, row in tracklist_full.iterrows():
    normalized = row['_normalized_track']
    if normalized not in tracklist_dict:
        tracklist_dict[normalized] = []
    tracklist_dict[normalized].append(idx)

# Track statistics
exact_matches = 0
unmatched_rows = []

# Define columns to overwrite (metadata only, NOT Track Name or Artist Name(s))
columns_to_overwrite = ['Subgenre', 'Emotionality', 'Genre', 'Prominent Instruments', 'Sound', 'Set', 'Vibe', 'Placement']

print("Processing matches...")
# Iterate through crate_tags and find matches in tracklist_full
for progress_idx, (idx, crate_row) in enumerate(crate_tags.iterrows()):
    # Progress indicator every 500 rows
    if progress_idx % 500 == 0:
        print(f"  Processing row {progress_idx}/{len(crate_tags)}...")
    
    normalized_crate = crate_row['_normalized_track']
    
    match_idx = None
    
    # Try exact match using dictionary lookup (track name only, no artist matching)
    if normalized_crate in tracklist_dict:
        potential_matches_indices = tracklist_dict[normalized_crate]
        # Use first match
        match_idx = potential_matches_indices[0]
        exact_matches += 1
    else:
        # No exact match found
        unmatched_rows.append({
            'Track Name (crate)': crate_row['Track Name'],
            'Artist Name (s) (crate)': crate_row.get('Artist Name (s)', ''),
            'Normalized Name': normalized_crate,
            'Set': crate_row.get('Set', ''),
            'Subgenre': crate_row.get('Subgenre', ''),
        })
    
    if match_idx is not None:
        # Overwrite ONLY metadata columns, NOT Track Name or Artist Name(s)
        # EXCEPT Track BPM
        for col in columns_to_overwrite:
            if col in crate_tags.columns and col in tracklist_full.columns:
                if col == 'Track BPM':
                    # DO NOT OVERWRITE Track BPM
                    pass
                else:
                    tracklist_full.at[match_idx, col] = crate_row[col]

print("Finalizing...")

# Drop the temporary normalized columns
tracklist_full = tracklist_full.drop('_normalized_track', axis=1)

# OUTPUT FILES
print("\n" + "="*60)
print("OUTPUT FILES:")

# Save the merged tracklist
tracklist_full.to_csv('tracklist_full_merged.csv', index=False)
print(f"  ✓ tracklist_full_merged.csv ({len(tracklist_full)} rows)")

# Save unmatched tracks
if len(unmatched_rows) > 0:
    unmatched_df = pd.DataFrame(unmatched_rows)
    unmatched_df.to_csv('crate_tags_unmatched.csv', index=False)
    print(f"  ⚠ crate_tags_unmatched.csv ({len(unmatched_rows)} unmatched tracks)")
else:
    print(f"  ✓ All tracks matched! No unmatched file needed.")

print("="*60)

# Summary
print(f"\nMERGE SUMMARY:")
print(f"  Total crate tags processed: {len(crate_tags)}")
print(f"  Exact matches: {exact_matches}")
print(f"  Unmatched: {len(unmatched_rows)}")
print(f"  Success rate: {((len(crate_tags) - len(unmatched_rows)) / len(crate_tags) * 100):.1f}%")
print(f"\nOVERWRITTEN COLUMNS (metadata only):")
print(f"  {', '.join(columns_to_overwrite)}")
print(f"\nPRESERVED COLUMNS (from tracklist_full):")
print(f"  Track Name, Artist Name(s), Track BPM, and all other columns")
