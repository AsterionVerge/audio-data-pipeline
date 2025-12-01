# ESSENTIAL MIX PLAYLIST MERGER - SETUP & USAGE GUIDE

## Overview

The **Playlist Merger** is a Python-based system that merges 109 thematically-curated Spotify playlists into your master `essential_mix_final_enriched.csv` file using ISRC codes as the matching key. It applies a sophisticated taxonomy system to intelligently populate metadata columns (Vibe, Sound, Culture, Emotional Layers, Instruments, Placement).

---

## What This Does

✓ **Matches tracks** across all playlists via ISRC (International Standard Recording Code)  
✓ **Applies taxonomy mappings** - Converts playlist names into structured metadata  
✓ **Aggregates multi-value fields** - Handles tracks appearing in multiple playlists  
✓ **Preserves existing data** - Enriches without overwriting  
✓ **Generates detailed reports** - Full merge statistics and unmatched track logs  

---

## Files Included

### 1. `playlist_merger.py`
Main Python script that orchestrates the entire merge process.

**Key Classes:**
- `PlaylistMerger`: Core merger logic
  - `load_playlists()`: Loads all CSV files from directory
  - `apply_taxonomy()`: Maps playlist names to metadata values
  - `process_playlists()`: Iterates through all playlists
  - `enrich_master()`: Populates enriched columns
  - `generate_report()`: Creates detailed merge report

### 2. `taxonomy_mapping_final.json`
Complete mapping of 109 playlists to their target columns and values.

**Example entry:**
```json
"set_28_-_teardrop.csv": {
  "emotional_layers": "sad"
},
"set_84_-_air.csv": {
  "vibe": "air"
}
```

---

## Required Files

Before running the script, ensure you have:

1. **`essential_mix_clean_final.csv`** (Master file)
   - Must contain: `ISRC` column (matching key)
   - Must contain: Target columns (Vibe, Sound, Culture, Emotional Layers, etc.)

2. **All playlist CSVs** in the same directory
   - Each must contain an `ISRC` column
   - Filenames should match the taxonomy mapping keys exactly
   - Example: `arabian.csv`, `set_28_-_teardrop.csv`, `summons_viii.csv`

3. **Both script files** in the working directory

---

## Installation

### Requirements
- Python 3.8+
- `pandas` library

### Setup
```bash
# Install pandas if needed
pip install pandas

# Verify files are in place
ls playlist_merger.py
ls taxonomy_mapping_final.json
ls essential_mix_clean_final.csv
```

---

## Usage

### Basic Execution

```bash
python playlist_merger.py
```

### Advanced Usage (Custom Paths)

Edit the configuration section at the bottom of `playlist_merger.py`:

```python
MASTER_FILE = 'path/to/essential_mix_clean_final.csv'
PLAYLISTS_DIR = 'path/to/playlist/directory'
TAXONOMY_FILE = 'path/to/taxonomy_mapping_final.json'
OUTPUT_FILE = 'path/to/essential_mix_final_enriched.csv'
REPORT_FILE = 'path/to/merge_report.json'
```

Then run normally:
```bash
python playlist_merger.py
```

---

## Output Files

### 1. `essential_mix_final_enriched.csv`
Your enriched master file with populated metadata columns.

**New/Updated Columns:**
- `vibe`: Pipe-delimited (e.g., "arabian|epic")
- `sound`: Pipe-delimited (e.g., "bouncy|acid-tinged")
- `culture`: Values from cultural playlists
- `emotional_layers`: Pipe-delimited emotions
- `prominent_instruments`: Pipe-delimited instrument list
- `placement`: Intro, outro, summons, etc.

### 2. `merge_report.json`
Detailed merge statistics and diagnostics.

**Contains:**
```json
{
  "total_playlists": 109,
  "playlists_processed": 105,
  "total_playlist_tracks": 8,234,
  "matched_in_master": 7,891,
  "unmatched_tracks": [
    {
      "playlist": "set_28_-_teardrop.csv",
      "isrc": "USUM71234567",
      "track_name": "Example Track",
      "artist": "Artist Name"
    }
  ],
  "enrichment_summary": {
    "vibe": 3,456,
    "sound": 2,123,
    "emotional_layers": 1,987,
    ...
  }
}
```

---

## Taxonomy Structure

The mapping is organized by category:

### VIBE (59 playlists)
arabian, forest, dark, jungle, space, robot, air, fire, water, earth, ice, witch, transcendent, otherworldly, stormy, bright, fun, cathartic, epic, chaotic, whimsy, dreamy, party, light, serene, gay, psychedelic, haunting

### SOUND (20 playlists)
haunting, bouncy, banger, beautiful, arcade, classic, acid-tinged, acidic, hypnotic, robotic, rave, rumble

### EMOTIONAL LAYERS (17 playlists)
sad, euphoric, sentimental, romantic, "queer euphoria"

### PROMINENT INSTRUMENTS (12 playlists)
didgeridoo, guitar, piano, cowbell, brass, strings, vocalizations, chime

### CULTURE (5 playlists)
arabian, french

### PLACEMENT (12 playlists)
intro, outro, summons

---

## Key Features

### Multi-Value Aggregation
Tracks appearing in multiple playlists get multiple values:
- Existing: "arabian"
- New from playlists: "epic", "bouncy"
- Result: "arabian|epic|bouncy"

Values are pipe-delimited (`|`) for easy parsing.

### Duplicate Removal
If a track appears in multiple playlists with the same mapping, duplicates are removed while preserving order.

### Preservation of Existing Data
Original master file values are preserved and new enrichment is appended.

### Logging
Real-time console output shows:
- Files being loaded
- Playlists being processed
- Match rates for each playlist
- Progress through enrichment
- Summary statistics

---

## Ignored Files

The following files are automatically skipped:

- `liked.csv` (personal preference flag)
- `beatport.csv` (source metadata)
- `essential_mix_*` (master file reference)
- `set_139_-_biome.csv` (requires manual review - inconsistent data)
- `set_161_-_rain.csv` (user handling separately)
- `set_162_-_unique_instrument.csv` (skip for now)
- `spire_abyss.csv` (user decision)
- `it's_a_fast'un.csv` (user decision)

---

## Troubleshooting

### "ISRC column not found"
**Problem:** Master file doesn't have an ISRC column.  
**Solution:** Verify the column name matches exactly (case-sensitive).

### Low match rate (< 50%)
**Problem:** Many playlist tracks don't match master file.  
**Solution:** Check ISRC formatting - ensure consistency across files.

### Import error: pandas not found
**Problem:** Pandas library not installed.  
**Solution:** Run `pip install pandas`

### File encoding issues
**Problem:** Special characters not displaying correctly.  
**Solution:** The script uses UTF-8 encoding; ensure your CSV files are UTF-8 encoded.

---

## Customization

### Add New Playlists
1. Add entry to `taxonomy_mapping_final.json`:
   ```json
   "new_playlist.csv": {
     "vibe": "new_vibe",
     "sound": "new_sound"
   }
   ```
2. Place `new_playlist.csv` in the playlists directory
3. Re-run the script

### Modify Taxonomy Values
Edit `taxonomy_mapping_final.json` directly. Example:
```json
"set_28_-_teardrop.csv": {
  "emotional_layers": "melancholic"  // Changed from "sad"
}
```

### Change Output Column Delimiter
In `playlist_merger.py`, find the `_aggregate_values()` method and change:
```python
return '|'.join(unique_values)  # Change '|' to your preferred delimiter
```

---

## Performance Notes

- **109 playlists** with an average of ~80 tracks each = ~8,700+ playlist track entries
- Expected runtime: **2-5 minutes** depending on file sizes and system
- Memory usage: Minimal (playlists and master loaded into memory)

---

## Data Quality Notes

### Multi-Value Aggregation
Some tracks may get multiple vibe/sound/emotional tags if they appear in multiple playlists. This is **intentional** - it reflects their multi-faceted nature in your curation.

### Unmatched Tracks
Check `merge_report.json` for unmatched tracks. These are valid playlist tracks that don't appear in the master file (expected for the 40% of playlists not in Essential Mix).

### Culture & Language
Only 5 playlists map to culture, and 2 to language (French). Most enrichment focuses on vibes, sounds, and emotional layers.

---

## Next Steps

1. **Verify the enriched file**: Check a sample of tracks to ensure mappings are correct
2. **Analyze the report**: Review unmatched tracks and enrichment distribution
3. **Manual review**: Check flagged tracks (biome, unique_instrument) manually if needed
4. **Iterate**: Adjust taxonomy if needed and re-run
5. **Use the data**: This enriched file is now ready for analysis, playlisting, or further processing

---

## Questions?

Refer to the detailed comments in `playlist_merger.py` for implementation details.

---

**Last Updated:** 2025-11-21  
**Taxonomy Playlists:** 109  
**Target Columns:** 6 primary + 13 metadata  
**Status:** Ready to deploy
