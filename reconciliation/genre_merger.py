#!/usr/bin/env python3
"""
GENRE PLAYLIST MERGER
Merges "Best Of" genre playlists into master file using ISRC matching
Populates the Genre column based on which "best_of_X" playlist each track appears in
"""

import pandas as pd
import json
import os
from pathlib import Path
from collections import defaultdict
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class GenreMerger:
    def __init__(self, master_file: str, playlists_directory: str):
        """
        Initialize the genre merger.
        
        Args:
            master_file: Path to your enriched master CSV
            playlists_directory: Path to directory containing best_of_*.csv files
        """
        self.master_file = master_file
        self.playlists_dir = playlists_directory
        
        # Genre mapping extracted from filename
        # Format: best_of_X.csv -> Genre Name
        self.genre_mappings = {
            'best_of_acid.csv': 'Acid',
            'best_of_deep_house.csv': 'Deep House',
            'best_of_disco.csv': 'Disco',
            'best_of_edm_dubstep.csv': 'EDM/Dubstep',
            'best_of_hard_techno.csv': 'Hard Techno',
            'best_of_house.csv': 'House',
            'best_of_indie_dance.csv': 'Indie Dance',
            'best_of_melodic_house.csv': 'Melodic House',
            'best_of_melodic_techno.csv': 'Melodic Techno',
            'best_of_organic_house.csv': 'Organic House',
            'best_of_other.csv': 'Other',
            'best_of_progressive.csv': 'Progressive House',
            'best_of_tech_house.csv': 'Tech House',
            'best_of_techno.csv': 'Techno',
            'best_of_trance.csv': 'Trance',
            'best_of_trance_deep_raw_hypnotic.csv': 'Trance (Deep/Raw/Hypnotic)'
        }
        
        # Load master file
        logger.info(f"Loading master file: {master_file}")
        self.master_df = pd.read_csv(master_file)
        
        # Ensure ISRC column exists
        if 'ISRC' not in self.master_df.columns:
            raise ValueError("Master file must contain ISRC column")
        
        # Initialize Genre column if it doesn't exist
        if 'Genre' not in self.master_df.columns:
            self.master_df['Genre'] = ""
            logger.info("Created new Genre column")
        
        # Create ISRC lookup index
        self.isrc_index = self.master_df.set_index('ISRC')
        logger.info(f"Loaded {len(self.master_df)} tracks in master file")
        
        # Track genre assignments
        self.genre_data = defaultdict(list)
        self.merge_report = {
            'total_playlists': 0,
            'playlists_processed': 0,
            'total_playlist_tracks': 0,
            'matched_in_master': 0,
            'unmatched_tracks': [],
            'genre_distribution': defaultdict(int)
        }
    
    def load_genre_playlists(self) -> dict:
        """Load all best_of_*.csv files from directory."""
        playlists = {}
        csv_files = list(Path(self.playlists_dir).glob('best_of_*.csv'))
        self.merge_report['total_playlists'] = len(csv_files)
        
        logger.info(f"Found {len(csv_files)} genre playlist files")
        
        for csv_file in csv_files:
            playlist_name = csv_file.name
            
            # Check if this playlist is in our mapping
            if playlist_name not in self.genre_mappings:
                logger.warning(f"Skipping unmapped file: {playlist_name}")
                continue
            
            try:
                df = pd.read_csv(csv_file)
                if 'ISRC' in df.columns:
                    playlists[playlist_name] = df
                    self.merge_report['playlists_processed'] += 1
                    logger.info(f"Loaded: {playlist_name} ({len(df)} tracks)")
                else:
                    logger.warning(f"Skipping {playlist_name}: no ISRC column")
            except Exception as e:
                logger.error(f"Error loading {playlist_name}: {e}")
        
        logger.info(f"Successfully loaded {len(playlists)} genre playlists")
        return playlists
    
    def process_genre_playlists(self, playlists: dict):
        """Process all genre playlists and apply genre mappings."""
        for playlist_name, playlist_df in playlists.items():
            genre = self.genre_mappings[playlist_name]
            logger.info(f"Processing: {playlist_name} → Genre: {genre}")
            
            matched = 0
            unmatched = []
            
            for _, row in playlist_df.iterrows():
                isrc = str(row['ISRC']).strip() if pd.notna(row['ISRC']) else None
                
                if not isrc or isrc == 'nan':
                    continue
                
                self.merge_report['total_playlist_tracks'] += 1
                
                # Check if ISRC is in master file
                if isrc in self.isrc_index.index:
                    matched += 1
                    self.merge_report['matched_in_master'] += 1
                    
                    # Add genre to this ISRC
                    self.genre_data[isrc].append(genre)
                    self.merge_report['genre_distribution'][genre] += 1
                else:
                    unmatched.append({
                        'playlist': playlist_name,
                        'genre': genre,
                        'isrc': isrc,
                        'track_name': row.get('Track Name', 'Unknown'),
                        'artist': row.get('Artist Name(s)', 'Unknown')
                    })
            
            logger.info(f"  Matched: {matched}/{len(playlist_df)}")
            if unmatched:
                self.merge_report['unmatched_tracks'].extend(unmatched)
    
    def enrich_master(self):
        """Enrich master dataframe with genre data."""
        logger.info("Enriching master file with genre data...")
        
        self.master_df['Genre'] = self.master_df['ISRC'].apply(
            lambda isrc: self._aggregate_genres(isrc)
        )
    
    def _aggregate_genres(self, isrc: str) -> str:
        """
        Aggregate genre values for an ISRC.
        Preserves existing genre and adds new ones.
        """
        existing = self.master_df.loc[self.master_df['ISRC'] == isrc, 'Genre'].values
        existing_value = existing[0] if len(existing) > 0 else ""
        
        new_genres = self.genre_data.get(isrc, [])
        
        # Combine existing and new values
        combined = []
        
        if pd.notna(existing_value) and str(existing_value).strip():
            combined.append(str(existing_value).strip())
        
        combined.extend(new_genres)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_genres = []
        for genre in combined:
            if genre not in seen:
                seen.add(genre)
                unique_genres.append(genre)
        
        # Return as pipe-delimited string
        return '|'.join(unique_genres) if unique_genres else ""
    
    def save_enriched_file(self, output_file: str):
        """Save enriched master file."""
        logger.info(f"Saving enriched file to: {output_file}")
        self.master_df.to_csv(output_file, index=False, encoding='utf-8')
        logger.info("✓ File saved successfully")
    
    def generate_report(self, output_file: str = 'genre_merge_report.json'):
        """Generate detailed merge report."""
        logger.info(f"Generating merge report: {output_file}")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.merge_report, f, indent=2, ensure_ascii=False)
        
        # Print summary
        print("\n" + "="*80)
        print("GENRE MERGE REPORT SUMMARY")
        print("="*80)
        print(f"Total genre playlists found: {self.merge_report['total_playlists']}")
        print(f"Genre playlists processed: {self.merge_report['playlists_processed']}")
        print(f"Total tracks in genre playlists: {self.merge_report['total_playlist_tracks']}")
        print(f"Tracks matched in master: {self.merge_report['matched_in_master']}")
        print(f"Match rate: {(self.merge_report['matched_in_master'] / max(1, self.merge_report['total_playlist_tracks']) * 100):.1f}%")
        print(f"Unmatched tracks: {len(self.merge_report['unmatched_tracks'])}")
        
        print("\nGenre distribution (assignments made):")
        for genre, count in sorted(self.merge_report['genre_distribution'].items(), 
                                   key=lambda x: -x[1]):
            print(f"  {genre}: {count}")
        
        print(f"\n✓ Full report saved to: {output_file}")
    
    def run(self, output_file: str, report_file: str = 'genre_merge_report.json'):
        """Execute the complete genre merge pipeline."""
        logger.info("="*80)
        logger.info("STARTING GENRE MERGE PROCESS")
        logger.info("="*80)
        
        try:
            # Load all genre playlists
            playlists = self.load_genre_playlists()
            
            # Process and apply genre mappings
            self.process_genre_playlists(playlists)
            
            # Enrich master file
            self.enrich_master()
            
            # Save results
            self.save_enriched_file(output_file)
            
            # Generate report
            self.generate_report(report_file)
            
            logger.info("="*80)
            logger.info("✓ GENRE MERGE COMPLETE")
            logger.info("="*80)
            
        except Exception as e:
            logger.error(f"Error during genre merge process: {e}", exc_info=True)
            raise


if __name__ == '__main__':
    # Configuration
    MASTER_FILE = 'essential_mix_final_enriched.csv'  # Your current enriched file
    PLAYLISTS_DIR = './'  # Directory containing best_of_*.csv files
    OUTPUT_FILE = 'essential_mix_final_enriched.csv'  # Overwrite or use new name
    REPORT_FILE = 'genre_merge_report.json'
    
    # Run genre merger
    merger = GenreMerger(MASTER_FILE, PLAYLISTS_DIR)
    merger.run(OUTPUT_FILE, REPORT_FILE)
