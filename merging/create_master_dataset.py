# Representative reconciliation stage.
# Demonstrates fuzzy matching + ambiguity surfacing prior to HITL resolution.

import pandas as pd
import numpy as np

def merge_genres(essential_genre, crate_genres):
    """
    Merge genre info from both sources intelligently.
    Priority: Essential Mix genre > Crate genres
    But keep both if different.
    """
    genres = []
    
    if pd.notna(essential_genre) and essential_genre:
        genres.append(str(essential_genre))
    
    if pd.notna(crate_genres) and crate_genres:
        crate_list = [g.strip() for g in str(crate_genres).split('|')]
        genres.extend([g for g in crate_list if g not in genres])
    
    return ' | '.join(genres) if genres else None


def bpm_to_range(bpm):
    """Convert exact BPM to a range category for comparison"""
    if pd.isna(bpm):
        return None
    
    bpm = float(bpm)
    
    if bpm <= 116:
        return '116 or less'
    elif 117 <= bpm <= 120:
        return '117-120'
    elif 121 <= bpm <= 123:
        return '121-123'
    elif 124 <= bpm <= 125:
        return '124-125'
    elif 126 <= bpm <= 129:
        return '126-129'
    elif 130 <= bpm <= 134:
        return '130-134'
    elif 135 <= bpm <= 139:
        return '135-139'
    else:
        return '140+'


def create_master_dataset(matched_csv, essential_csv, output_csv):
    """
    Create the ultimate merged dataset.
    
    Combines:
    - Crate tag categories (Genres, BPM range, Vibe, Instruments, etc.)
    - Essential Mix metadata (Track, Artist, Album, ISRC)
    - Essential Mix audio features (exact BPM, energy, valence, etc.)
    - Match confidence scores
    """
    print("Loading data...")
    matched_df = pd.read_csv(matched_csv)
    essential_df = pd.read_csv(essential_csv)
    
    print(f"Matched tracks: {len(matched_df)}")
    print(f"Essential Mix tracks: {len(essential_df)}")
    
    # Start with matched data (has both filename and Essential Mix IDs)
    master = matched_df.copy()
    
    # For high/medium confidence matches, merge in full Essential Mix data
    print("\nMerging Essential Mix audio features...")
    
    # Merge on Spotify Track ID where available
    master = master.merge(
        essential_df,
        left_on='matched_spotify_id',
        right_on='Spotify Track ID',
        how='left',
        suffixes=('_crate', '_essential')
    )
    
    # Intelligent column selection and merging
    print("Combining metadata intelligently...")
    
    final_columns = {
        # Core identifiers
        'filename': master['filename'],
        'track_name': master['matched_track'].fillna(master.get('Track Name', '')),
        'artist_name': master['matched_artist'].fillna(master.get('Artist Name', '')),
        'album_name': master.get('Album Name', ''),
        'isrc': master['matched_isrc'].fillna(master.get('ISRC', '')),
        'spotify_track_id': master['matched_spotify_id'].fillna(master.get('Spotify Track ID', '')),
        
        # Match quality
        'match_confidence': master['match_confidence'],
        'match_score': master['match_score'],
        
        # BPM - both exact and range
        'bpm_exact': master['matched_bpm'].fillna(master.get('BPM', '')),
        'bpm_range': master['BPM'],
        
        # Genres - merged
        'genre': master.apply(
            lambda row: merge_genres(
                row.get('matched_genre') or row.get('Genre'),
                row.get('Genres')
            ),
            axis=1
        ),
        'genre_crate_tags': master['Genres'],  # Keep original for reference
        
        # Crate categories
        'vibe': master['Vibe'],
        'instruments': master['Instruments'],
        'sound': master['Sound'],
        'placement': master['Placement'],
        'sets': master['Sets'],
        
        # Audio features from Essential Mix (if available)
        'energy': master.get('energy', ''),
        'valence': master.get('valence', ''),
        'danceability': master.get('danceability', ''),
        'acousticness': master.get('acousticness', ''),
        'instrumentalness': master.get('instrumentalness', ''),
        'speechiness': master.get('speechiness', ''),
        'liveness': master.get('liveness', ''),
        'loudness': master.get('loudness', ''),
        'tempo': master.get('tempo', ''),
        'key': master.get('Key', ''),
        'mode': master.get('mode', ''),
        'time_signature': master.get('time_signature', ''),
        'duration_ms': master.get('duration_ms', ''),
        
        # URLs
        'spotify_url': master.get('Spotify Track URL', ''),
        'preview_url': master.get('Spotify Tn Musicdrat', ''),  # Typo from original?
    }
    
    final_df = pd.DataFrame(final_columns)
    
    # Add computed BPM range for verification
    final_df['bpm_range_computed'] = final_df['bpm_exact'].apply(bpm_to_range)
    
    # Stats
    print("\n=== Final Dataset Stats ===")
    print(f"Total tracks: {len(final_df)}")
    print(f"With Spotify IDs: {final_df['spotify_track_id'].notna().sum()}")
    print(f"With exact BPM: {final_df['bpm_exact'].notna().sum()}")
    print(f"With BPM range: {final_df['bpm_range'].notna().sum()}")
    print(f"With genre: {final_df['genre'].notna().sum()}")
    print(f"With vibe tags: {final_df['vibe'].notna().sum()}")
    print(f"With instrument tags: {final_df['instruments'].notna().sum()}")
    print(f"With audio features: {final_df['energy'].notna().sum()}")
    
    # Save
    final_df.to_csv(output_csv, index=False)
    print(f"\n✓ Saved master dataset to {output_csv}")
    
    # Create a "culture" analysis from vibe tags
    print("\nExtracting cultural markers from vibe tags...")
    culture_markers = {
        'African': final_df['vibe'].str.contains('African', case=False, na=False).sum(),
        'Arabian & Indian': final_df['vibe'].str.contains('Arabian|Indian', case=False, na=False).sum(),
        'Asian': final_df['vibe'].str.contains('Asian', case=False, na=False).sum(),
        'Spanish & LatAm': final_df['vibe'].str.contains('Spanish|LatAm', case=False, na=False).sum(),
        'Jungle & Tribal': final_df['vibe'].str.contains('Jungle|Tribal', case=False, na=False).sum(),
    }
    
    print("\nCultural representation:")
    for culture, count in culture_markers.items():
        print(f"  {culture}: {count} tracks")
    
    return final_df


# === USAGE ===
if __name__ == "__main__":
    matched_csv = 'crate_tags_matched.csv'
    essential_csv = 'essential_mix_final_enriched.csv'
    output_csv = 'master_music_library.csv'
    
    master_df = create_master_dataset(matched_csv, essential_csv, output_csv)
    
    print("\n=== Sample Output (first 3 rows) ===")
    print(master_df[['filename', 'track_name', 'artist_name', 'genre', 'bpm_exact', 'bpm_range', 'vibe']].head(3))
    
    print("\nDone!")