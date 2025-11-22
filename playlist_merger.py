#!/usr/bin/env python3
"""
ESSENTIAL MIX PLAYLIST MERGER
Merges all playlist datasets into essential_mix_final_enriched.csv using ISRC as key
Applies complex taxonomy mapping to populate metadata columns
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

class PlaylistMerger:
    def __init__(self, master_file: str, playlists_directory: str, taxonomy_file: str):
        """
        Initialize the merger.

        Args:
            master_file: Path to essential_mix_final_enriched.csv
            playlists_directory: Path to directory containing all playlist CSVs
            taxonomy_file: Path to taxonomy_mapping_final.json
        """
        self.master_file = master_file
        self.playlists_dir = playlists_directory
        self.taxonomy_file = taxonomy_file

        # Load taxonomy mapping
        with open(taxonomy_file, 'r', encoding='utf-8') as f:
            self.taxonomy = json.load(f)

        # Columns to initialize for enrichment
        self.enrichment_columns = {
            'vibe': [],
            'sound': [],
            'culture': [],
            'emotional_layers': [],
            'prominent_instruments': [],
            'placement': []
        }

        # Load master file
        logger.info(f"Loading master file: {master_file}")
        self.master_df = pd.read_csv(master_file)

        # Ensure ISRC column exists
        if 'ISRC' not in self.master_df.columns:
            raise ValueError("Master file must contain ISRC column")

        # Create ISRC lookup index
        self.isrc_index = self.master_df.set_index('ISRC')
        logger.info(f"Loaded {len(self.master_df)} tracks in master file")

        # Initialize enrichment tracking
        self.enrichment_data = defaultdict(lambda: defaultdict(list))
        self.merge_report = {
            'total_playlists': 0,
            'playlists_processed': 0,
            'total_playlist_tracks': 0,
            'matched_in_master': 0,
            'unmatched_tracks': [],
            'enrichment_summary': defaultdict(int)
        }

    def load_playlists(self) -> dict:
        """Load all playlist CSV files from directory."""
        playlists = {}
        csv_files = list(Path(self.playlists_dir).glob('*.csv'))
        self.merge_report['total_playlists'] = len(csv_files)

        logger.info(f"Found {len(csv_files)} playlist files")

        for csv_file in csv_files:
            playlist_name = csv_file.name

            # Skip master file
            if 'essential_mix' in playlist_name.lower():
                logger.info(f"Skipping master file: {playlist_name}")
                continue

            # Skip ignored files
            if playlist_name in ['liked.csv', 'beatport.csv', 'it's_a_fast'un.csv', 
                                'set_161_-_rain.csv', 'spire_abyss.csv', 'set_139_-_biome.csv',
                                'set_162_-_unique_instrument.csv']:
                logger.info(f"Skipping ignored file: {playlist_name}")
                continue

            try:
                df = pd.read_csv(csv_file)
                if 'ISRC' in df.columns:
                    playlists[playlist_name] = df
                    self.merge_report['playlists_processed'] += 1
                else:
                    logger.warning(f"Skipping {playlist_name}: no ISRC column")
            except Exception as e:
                logger.error(f"Error loading {playlist_name}: {e}")

        logger.info(f"Successfully loaded {len(playlists)} playlists")
        return playlists

    def apply_taxonomy(self, playlist_name: str, isrc: str):
        """Apply taxonomy mapping for a playlist to an ISRC."""
        if playlist_name not in self.taxonomy:
            return

        mappings = self.taxonomy[playlist_name]

        for column, value in mappings.items():
            if column != 'notes':
                self.enrichment_data[isrc][column].append(value)
                self.merge_report['enrichment_summary'][column] += 1

    def process_playlists(self, playlists: dict):
        """Process all playlists and apply taxonomy mappings."""
        for playlist_name, playlist_df in playlists.items():
            logger.info(f"Processing: {playlist_name}")

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

                    # Apply taxonomy mapping
                    self.apply_taxonomy(playlist_name, isrc)
                else:
                    unmatched.append({
                        'playlist': playlist_name,
                        'isrc': isrc,
                        'track_name': row.get('Track Name', 'Unknown'),
                        'artist': row.get('Artist Name(s)', 'Unknown')
                    })

            logger.info(f"  Matched: {matched}/{len(playlist_df)}")
            if unmatched:
                self.merge_report['unmatched_tracks'].extend(unmatched)

    def enrich_master(self):
        """Enrich master dataframe with aggregated metadata."""
        logger.info("Enriching master file with aggregated metadata...")

        for column in self.enrichment_columns.keys():
            self.master_df[column] = self.master_df['ISRC'].apply(
                lambda isrc: self._aggregate_values(isrc, column)
            )

    def _aggregate_values(self, isrc: str, column: str) -> str:
        """
        Aggregate values for a column, handling multi-value fields.
        Existing values in master are preserved and new values appended.
        """
        existing = self.master_df.loc[self.master_df['ISRC'] == isrc, column].values
        existing_value = existing[0] if len(existing) > 0 else ""

        new_values = self.enrichment_data.get(isrc, {}).get(column, [])

        # Combine existing and new values
        combined = []

        if pd.notna(existing_value) and str(existing_value).strip():
            combined.append(str(existing_value).strip())

        combined.extend(new_values)

        # Remove duplicates while preserving order
        seen = set()
        unique_values = []
        for val in combined:
            if val not in seen:
                seen.add(val)
                unique_values.append(val)

        # Return as pipe-delimited string for multi-value fields
        return '|'.join(unique_values) if unique_values else ""

    def save_enriched_file(self, output_file: str):
        """Save enriched master file."""
        logger.info(f"Saving enriched file to: {output_file}")
        self.master_df.to_csv(output_file, index=False, encoding='utf-8')
        logger.info("✓ File saved successfully")

    def generate_report(self, output_file: str = 'merge_report.json'):
        """Generate detailed merge report."""
        logger.info(f"Generating merge report: {output_file}")

        # Convert unmatched tracks to list for JSON serialization
        self.merge_report['unmatched_tracks'] = self.merge_report['unmatched_tracks']

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.merge_report, f, indent=2, ensure_ascii=False)

        # Print summary
        print("\n" + "="*80)
        print("MERGE REPORT SUMMARY")
        print("="*80)
        print(f"Total playlists found: {self.merge_report['total_playlists']}")
        print(f"Playlists processed: {self.merge_report['playlists_processed']}")
        print(f"Total tracks in playlists: {self.merge_report['total_playlist_tracks']}")
        print(f"Tracks matched in master: {self.merge_report['matched_in_master']}")
        print(f"Match rate: {(self.merge_report['matched_in_master'] / max(1, self.merge_report['total_playlist_tracks']) * 100):.1f}%")
        print(f"Unmatched tracks: {len(self.merge_report['unmatched_tracks'])}")

        print("\nEnrichment summary (values added):")
        for column, count in sorted(self.merge_report['enrichment_summary'].items(), 
                                   key=lambda x: -x[1]):
            print(f"  {column}: {count}")

        print(f"\n✓ Full report saved to: {output_file}")

    def run(self, output_file: str, report_file: str = 'merge_report.json'):
        """Execute the complete merge pipeline."""
        logger.info("="*80)
        logger.info("STARTING PLAYLIST MERGE PROCESS")
        logger.info("="*80)

        try:
            # Load all playlists
            playlists = self.load_playlists()

            # Process and apply taxonomy
            self.process_playlists(playlists)

            # Enrich master file
            self.enrich_master()

            # Save results
            self.save_enriched_file(output_file)

            # Generate report
            self.generate_report(report_file)

            logger.info("="*80)
            logger.info("✓ MERGE COMPLETE")
            logger.info("="*80)

        except Exception as e:
            logger.error(f"Error during merge process: {e}", exc_info=True)
            raise


if __name__ == '__main__':
    # Configuration
    MASTER_FILE = 'essential_mix_clean_final.csv'  # Update path as needed
    PLAYLISTS_DIR = './'  # Directory containing playlist CSVs
    TAXONOMY_FILE = 'taxonomy_mapping_final.json'
    OUTPUT_FILE = 'essential_mix_final_enriched.csv'
    REPORT_FILE = 'merge_report.json'

    # Run merger
    merger = PlaylistMerger(MASTER_FILE, PLAYLISTS_DIR, TAXONOMY_FILE)
    merger.run(OUTPUT_FILE, REPORT_FILE)
