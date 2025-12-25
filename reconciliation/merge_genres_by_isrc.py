#!/usr/bin/env python3
"""
ISRC-based Genre Merger
Matches tracks from Spotify genre playlist CSVs to essential_mix.csv using ISRC numbers
and merges genre information with special handling for specific categories.
"""

import pandas as pd
import os
from pathlib import Path
from typing import Dict, Set

# Configuration
ESSENTIAL_MIX_PATH = "essential_mix.csv"
GENRE_CSV_PATTERN = "best_of_*.csv"

# Column names in essential_mix.csv
ESSENTIAL_ISRC_COL = "ISRC"
GENRE_COLUMN = "Genre"
SOUND_COLUMN = "Sound"

# Column names in Spotify CSVs (best_of_*.csv)
SPOTIFY_ISRC_COL = "ISRC"

# Special mappings
SPECIAL_MAPPINGS = {
    "acid": {"column": SOUND_COLUMN, "value": "acid-tinged"},
    "edm_dubstep": {"column": GENRE_COLUMN, "value": "EDM/Dubstep"}
}


def extract_genre_from_filename(filename: str) -> str:
    """
    Extract genre name from filename by removing 'best_of_' prefix and '.csv' suffix,
    then replacing underscores with spaces and title-casing.
    
    Args:
        filename: CSV filename like 'best_of_deep_house.csv'
    
    Returns:
        Genre name like 'Deep House'
    """
    # Remove 'best_of_' prefix and '.csv' suffix
    genre = filename.replace("best_of_", "").replace(".csv", "")
    
    # Handle special cases that don't get title-cased
    if genre in SPECIAL_MAPPINGS:
        return genre
    
    # Replace underscores with spaces and title case
    genre = genre.replace("_", " ").title()
    
    return genre


def load_genre_playlists(directory: str = ".") -> Dict[str, Set[str]]:
    """
    Load all best_of_*.csv files (Spotify exports) and map them to their genre names.
    
    Args:
        directory: Directory containing the CSV files
    
    Returns:
        Dictionary mapping genre names to DataFrames with ISRC data
    """
    genre_data = {}
    
    for csv_file in Path(directory).glob(GENRE_CSV_PATTERN):
        genre = extract_genre_from_filename(csv_file.name)
        
        try:
            df = pd.read_csv(csv_file)
        except Exception as e:
            print(f"Warning: Failed to load {csv_file.name}: {e}")
            continue
        
        # Validate ISRC column exists
        if SPOTIFY_ISRC_COL not in df.columns:
            print(f"Warning: {csv_file.name} missing '{SPOTIFY_ISRC_COL}' column. Skipping.")
            continue
        
        # Remove rows with null ISRCs
        df = df.dropna(subset=[SPOTIFY_ISRC_COL])
        
        # Extract just the ISRCs we need
        isrcs = df[SPOTIFY_ISRC_COL].unique()
        
        genre_data[genre] = set(isrcs)
        print(f"Loaded {len(isrcs)} unique ISRCs from {csv_file.name} → {genre}")
    
    return genre_data


def merge_genres_into_essential_mix(
    essential_mix_df: pd.DataFrame,
    genre_data: Dict[str, Set[str]]
) -> pd.DataFrame:
    """
    Merge genre information into essential_mix.csv based on ISRC matching.
    
    Args:
        essential_mix_df: DataFrame of essential_mix.csv
        genre_data: Dictionary mapping genre names to sets of ISRCs
    
    Returns:
        Updated essential_mix DataFrame
    """
    # Ensure required columns exist
    if GENRE_COLUMN not in essential_mix_df.columns:
        print(f"\nWarning: Creating new '{GENRE_COLUMN}' column in essential_mix.csv")
        essential_mix_df[GENRE_COLUMN] = ""
    if SOUND_COLUMN not in essential_mix_df.columns:
        print(f"Warning: Creating new '{SOUND_COLUMN}' column in essential_mix.csv")
        essential_mix_df[SOUND_COLUMN] = ""
    
    # Track ISRCs to genres mapping
    isrc_to_genres: Dict[str, Set[str]] = {}
    isrc_to_sound: Dict[str, str] = {}
    
    # Build mappings from all genre playlists
    for genre, isrc_set in genre_data.items():
        for isrc in isrc_set:
            # Handle special mappings
            if genre in SPECIAL_MAPPINGS:
                mapping = SPECIAL_MAPPINGS[genre]
                if mapping["column"] == SOUND_COLUMN:
                    isrc_to_sound[isrc] = mapping["value"]
                elif mapping["column"] == GENRE_COLUMN:
                    if isrc not in isrc_to_genres:
                        isrc_to_genres[isrc] = set()
                    isrc_to_genres[isrc].add(mapping["value"])
            else:
                # Standard genre tag
                if isrc not in isrc_to_genres:
                    isrc_to_genres[isrc] = set()
                isrc_to_genres[isrc].add(genre)
    
    # Apply mappings to essential_mix
    matches_found = 0
    genres_added = 0
    sounds_added = 0
    skipped_existing_genre = 0
    skipped_existing_sound = 0
    
    for idx, row in essential_mix_df.iterrows():
        isrc = row[ESSENTIAL_ISRC_COL]
        
        if pd.isna(isrc):
            continue
        
        # Add genres (only if current Genre is empty/null to avoid overwriting)
        if isrc in isrc_to_genres:
            existing_genre = row[GENRE_COLUMN]
            if pd.isna(existing_genre) or str(existing_genre).strip() == "":
                new_genres = sorted(isrc_to_genres[isrc])
                essential_mix_df.at[idx, GENRE_COLUMN] = ", ".join(new_genres)
                genres_added += 1
                matches_found += 1
            else:
                skipped_existing_genre += 1
        
        # Add sound descriptor (only if current Sound is empty/null)
        if isrc in isrc_to_sound:
            existing_sound = row[SOUND_COLUMN]
            if pd.isna(existing_sound) or str(existing_sound).strip() == "":
                essential_mix_df.at[idx, SOUND_COLUMN] = isrc_to_sound[isrc]
                sounds_added += 1
                if isrc not in isrc_to_genres:
                    matches_found += 1
            else:
                skipped_existing_sound += 1
    
    print(f"\nMerge Summary:")
    print(f"  Total unique ISRC matches: {matches_found}")
    print(f"  Genre tags added: {genres_added}")
    print(f"  Sound descriptors added: {sounds_added}")
    print(f"  Skipped (existing Genre data): {skipped_existing_genre}")
    print(f"  Skipped (existing Sound data): {skipped_existing_sound}")
    
    return essential_mix_df


def main():
    """Main execution function."""
    print("=" * 60)
    print("ISRC-Based Genre Merger")
    print("=" * 60)
    
    # Load essential_mix.csv
    if not os.path.exists(ESSENTIAL_MIX_PATH):
        print(f"\nError: {ESSENTIAL_MIX_PATH} not found.")
        print("Please ensure essential_mix.csv exists in the current directory.")
        return
    
    print(f"\nLoading {ESSENTIAL_MIX_PATH}...")
    
    # Auto-detect delimiter (could be comma or tab)
    with open(ESSENTIAL_MIX_PATH, 'r', encoding='utf-8') as f:
        first_line = f.readline()
        delimiter = '\t' if '\t' in first_line else ','
    
    essential_mix_df = pd.read_csv(ESSENTIAL_MIX_PATH, sep=delimiter)
    print(f"  Loaded {len(essential_mix_df)} tracks")
    print(f"  Detected delimiter: {'TAB' if delimiter == '\\t' else 'COMMA'}")
    
    # Validate ISRC column
    if ESSENTIAL_ISRC_COL not in essential_mix_df.columns:
        print(f"\nError: '{ESSENTIAL_ISRC_COL}' column not found in {ESSENTIAL_MIX_PATH}")
        print(f"Available columns: {', '.join(essential_mix_df.columns)}")
        return
    
    # Load all genre playlists
    print(f"\nLoading genre playlists...")
    genre_data = load_genre_playlists()
    
    if not genre_data:
        print("\nNo genre playlist CSV files found matching pattern: best_of_*.csv")
        return
    
    print(f"\nFound {len(genre_data)} genre playlists")
    
    # Merge genres into essential_mix
    print(f"\nMerging genres into {ESSENTIAL_MIX_PATH}...")
    updated_df = merge_genres_into_essential_mix(essential_mix_df, genre_data)
    
    # Save updated essential_mix.csv
    backup_path = ESSENTIAL_MIX_PATH.replace(".csv", "_backup.csv")
    print(f"\nCreating backup: {backup_path}")
    essential_mix_df.to_csv(backup_path, sep=delimiter, index=False)
    
    print(f"Saving updated {ESSENTIAL_MIX_PATH}...")
    updated_df.to_csv(ESSENTIAL_MIX_PATH, sep=delimiter, index=False)
    
    print("\n" + "=" * 60)
    print("✓ Genre merge complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
