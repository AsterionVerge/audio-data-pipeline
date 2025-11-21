import pandas as pd
import re

def diagnose_matching_failure(crate_csv, essential_csv):
    """
    Diagnose why fuzzy matching is failing so badly.
    """
    print("="*80)
    print("FUZZY MATCH DIAGNOSTIC")
    print("="*80)
    
    # Load data
    print("\nLoading data...")
    crate_df = pd.read_csv(crate_csv)
    essential_df = pd.read_csv(essential_csv)
    
    print(f"Crate tracks: {len(crate_df)}")
    print(f"Essential Mix tracks: {len(essential_df)}")
    
    # Identify Essential Mix column names
    track_col = None
    artist_col = None
    
    for col in essential_df.columns:
        col_lower = col.lower()
        if 'track' in col_lower and 'name' in col_lower:
            track_col = col
        elif 'artist' in col_lower and 'name' in col_lower:
            artist_col = col
    
    if not track_col or not artist_col:
        print("\n⚠ WARNING: Could not auto-detect track/artist columns")
        print(f"Track column detected: {track_col}")
        print(f"Artist column detected: {artist_col}")
    
    # Show sample filenames
    print("\n" + "="*80)
    print("SAMPLE FILENAMES FROM CRATE DATA (first 10)")
    print("="*80)
    for i, filename in enumerate(crate_df['filename'].head(10), 1):
        print(f"{i}. {filename}")
    
    # Show Essential Mix columns first
    print("\n" + "="*80)
    print("ESSENTIAL MIX DATASET COLUMNS")
    print("="*80)
    print("Available columns:")
    for i, col in enumerate(essential_df.columns, 1):
        print(f"  {i}. {col}")
    
    print(f"\nDetected track column: {track_col}")
    print(f"Detected artist column: {artist_col}")
    
    # Show sample Essential Mix tracks
    print("\n" + "="*80)
    print("SAMPLE ESSENTIAL MIX TRACKS (first 10)")
    print("="*80)
    
    if track_col and artist_col:
        essential_sample = essential_df[[track_col, artist_col]].head(10)
        for i, row in essential_sample.iterrows():
            track = row.get(track_col, 'N/A')
            artist = row.get(artist_col, 'N/A')
            print(f"{i+1}. \"{track}\" by {artist}")
    else:
        print("⚠ Could not identify track/artist columns")
        print("Showing first row as sample:")
        print(essential_df.head(1).to_dict('records'))
    
    # Parse sample filenames
    print("\n" + "="*80)
    print("FILENAME PARSING TEST (first 10)")
    print("="*80)
    
    def parse_filename(filename):
        """Quick version of the parsing logic"""
        name = filename.rsplit('.', 1)[0]
        
        # Pattern 1: Number_Artist_Track
        match = re.match(r'^\d+_([^_]+)_(.+?)(?:_\(([^)]+)\))?$', name)
        if match:
            artist = match.group(1).replace('_', ' ').strip()
            track = match.group(2).replace('_', ' ').strip()
            remix = match.group(3) if match.group(3) else None
            if remix:
                track = f"{track} ({remix})"
            return ('Beatport format', artist, track)
        
        # Pattern 2: Artist - Track
        if ' - ' in name:
            parts = name.split(' - ', 1)
            return ('Dash format', parts[0].strip(), parts[1].strip())
        
        # Pattern 3: [feat. Artist]
        feat_match = re.search(r'\[feat\. ([^\]]+)\]', name, re.IGNORECASE)
        if feat_match:
            artist = feat_match.group(1).strip()
            track = re.sub(r'\[feat\. [^\]]+\]', '', name, flags=re.IGNORECASE).strip()
            return ('Feat format', artist, track)
        
        # Pattern 4: Just track name
        return ('Unknown format', None, name.strip())
    
    for i, filename in enumerate(crate_df['filename'].head(10), 1):
        fmt, artist, track = parse_filename(filename)
        print(f"{i}. {filename}")
        print(f"   Format: {fmt}")
        print(f"   Artist: {artist}")
        print(f"   Track:  {track}")
        print()
    
    # Check for exact artist name matches
    print("\n" + "="*80)
    print("CHECKING FOR EXACT ARTIST NAME OVERLAP")
    print("="*80)
    
    if not artist_col:
        print("⚠ Skipping artist overlap check - could not identify artist column")
        return
    
    # Extract all artists from filenames
    crate_artists = set()
    for filename in crate_df['filename']:
        fmt, artist, track = parse_filename(filename)
        if artist:
            crate_artists.add(artist.lower())
    
    # Get all Essential Mix artists
    essential_artists = set()
    for artist in essential_df[artist_col].dropna():
        essential_artists.add(str(artist).lower())
    
    # Find overlap
    overlap = crate_artists.intersection(essential_artists)
    
    print(f"Unique artists in crate filenames: {len(crate_artists)}")
    print(f"Unique artists in Essential Mix: {len(essential_artists)}")
    print(f"Exact matches: {len(overlap)} ({len(overlap)/len(crate_artists)*100:.1f}%)")
    
    if len(overlap) > 0:
        print(f"\nSample overlapping artists (first 10):")
        for i, artist in enumerate(sorted(overlap)[:10], 1):
            print(f"  {i}. {artist}")
    else:
        print("\n⚠ WARNING: ZERO artist overlap detected!")
        print("This means your DJ library and Essential Mix dataset are completely different.")
    
    # Check for partial artist matches
    print("\n" + "="*80)
    print("CHECKING FOR PARTIAL ARTIST MATCHES")
    print("="*80)
    
    partial_matches = 0
    sample_partials = []
    
    for crate_artist in list(crate_artists)[:100]:  # Sample first 100
        for essential_artist in essential_artists:
            # Check if one is substring of other
            if (crate_artist in essential_artist or essential_artist in crate_artist):
                partial_matches += 1
                if len(sample_partials) < 5:
                    sample_partials.append((crate_artist, essential_artist))
                break
    
    print(f"Partial matches in sample of 100: {partial_matches}")
    if sample_partials:
        print("\nSample partial matches:")
        for crate_a, essential_a in sample_partials:
            print(f"  Crate: '{crate_a}' <-> Essential: '{essential_a}'")
    
    # Final diagnosis
    print("\n" + "="*80)
    print("DIAGNOSIS")
    print("="*80)
    
    if len(overlap) == 0:
        print("❌ PROBLEM: Zero artist overlap")
        print("\nLikely causes:")
        print("1. Your DJ library and Essential Mix are completely different collections")
        print("2. Filename format is not being parsed correctly")
        print("3. Artist names are formatted too differently (e.g., 'The Artist' vs 'Artist')")
        print("\nSolutions:")
        print("- Use Spotify Track IDs instead (if available in both datasets)")
        print("- Use ISRC codes for matching")
        print("- Manually create a mapping file")
        print("- Or: these are just two separate libraries that should stay separate")
    
    elif len(overlap) < 100:
        print("⚠ PROBLEM: Very low artist overlap")
        print(f"Only {len(overlap)} artists match out of {len(crate_artists)} in your library")
        print("\nThis suggests minimal dataset overlap.")
        print("Consider using a different matching key (ISRC, Spotify ID)")
    
    else:
        print("✓ Artist overlap looks good")
        print("The fuzzy matching logic might need tuning.")
        print("Check the filename parsing patterns above.")


if __name__ == "__main__":
    diagnose_matching_failure('crate_tags_structured.csv', 'essential_mix_final_enriched.csv')
