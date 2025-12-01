# Serato-Spotify Music Metadata Pipeline

A comprehensive Python-based pipeline for extracting, merging, and enriching music metadata from multiple sources.

## Features

### **Serato .crate Parsing**
Extracts track metadata from ~200 Serato playlist files

### **Multi-Source Merging**
Combines Spotify API data with Beatport/local track libraries

### **Intelligent Normalization**
93.8% match accuracy using advanced string normalization:
- Handles possessives (umai_s vs umai's)
- Strips remix info in multiple formats
- Unicode normalization (é→e, ñ→n)
- Multi-word artist name handling

### **Taxonomy Enrichment**
Applies 127 taxonomic mappings across 109 playlists:
- 59 vibe categories (Arabian, Epic, Dark, etc.)
- 20 sound descriptors (Bouncy, Acid-Tinged, Hypnotic)
- 17 emotional layers
- 12 instrument tags
- 12 placement markers

### **ISRC-Based Matching**
Fast, accurate cross-referencing via ISRC codes

## Stats

- **Input**: 2,700 Spotify tracks + 3,000 Beatport/local tracks
- **Output**: 4,438 enriched tracks with 93.8% metadata coverage
- **Playlists**: 109 thematic playlists + 200 Serato crates processed
- **Accuracy**: 2,773/2,955 successful matches (93.8%)

## Quick Start

### Prerequisites

```bash
pip install pandas
```

### Basic Usage

1. **Extract Serato Crate Data**
```bash
python scripts/01_extraction/crate_extractor_corrected.py
```

2. **Clean and Normalize**
```bash
python scripts/02_preprocessing/cleanup_on_aisle_csv.py
python scripts/02_preprocessing/fix_accents.py
```

3. **Merge Datasets**
```bash
# Primary merge: Crate tags → tracklist
python scripts/03_merging/merge_crate_tags_FINAL.py

# Spotify enrichment
python scripts/03_merging/playlist_merger.py
```

4. **Apply Taxonomy**
```bash
python scripts/04_enrichment/genre_merger.py
python scripts/04_enrichment/crate_tag_refinment.py
```

## Pipeline Architecture

```
┌─────────────────┐
│ Serato .crates  │
│  (~200 files)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐      ┌──────────────────┐
│  01_extraction  │      │  Spotify API     │
│                 │      │  (2,700 tracks)  │
└────────┬────────┘      └─────────┬────────┘
         │                         │
         ▼                         ▼
┌─────────────────────────────────────────┐
│       02_preprocessing                  │
│  • Unicode normalization                │
│  • Accent stripping                     │
│  • Cleanup corruption                   │
└────────┬────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│       03_merging                        │
│  • Track name matching (93.8%)          │
│  • ISRC-based linking                   │
│  • Audio features merge                 │
└────────┬────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│       04_enrichment                     │
│  • Taxonomy application (127 mappings)  │
│  • Genre classification                 │
│  • Metadata refinement                  │
└────────┬────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│  Final Output: 4,438 enriched tracks    │
│  with vibe, sound, emotion, placement   │
└─────────────────────────────────────────┘
```

## Repository Structure

```
serato-spotify-pipeline/
├── scripts/
│   ├── 01_extraction/       # Serato .crate parsing
│   ├── 02_preprocessing/    # Data cleanup & normalization
│   ├── 03_merging/          # Multi-source data merging
│   ├── 04_enrichment/       # Taxonomy application
│   └── 05_utilities/        # Helper scripts & diagnostics
├── config/
│   ├── taxonomy_mapping_final.json
│   ├── setlists_mapping.csv
│   └── crates_mapping.csv
├── docs/
│   ├── SETUP_GUIDE.md
│   ├── QUICK_REF.md
│   ├── TAXONOMY_REF.md
│   └── PLAYLIST_CRATE_MAPPINGS.md
└── archive/
    ├── old_versions/        # Previous script iterations
    └── logs/                # Merge reports & execution logs
```

## Documentation

See `/docs` for detailed guides:
- [Setup Guide](docs/SETUP_GUIDE.md) - Installation and configuration
- [Quick Reference](docs/QUICK_REF.md) - Common commands and workflows
- [Taxonomy Reference](docs/TAXONOMY_REF.md) - Complete category mappings
- [Playlist/Crate Mappings](docs/PLAYLIST_CRATE_MAPPINGS.md) - 109 playlists + 107 crates

## Key Scripts

### Core Merging
- `merge_crate_tags_FINAL.py` - Main crate→tracklist merge (93.8% accuracy)
- `playlist_merger.py` - 109 playlist enrichment via ISRC matching
- `merge_audio_features.py` - Spotify audio features integration

### Data Extraction
- `crate_extractor_corrected.py` - Serato .crate parser
- `crate_tags_parse.py` - Tag extraction and structuring

### Utilities
- `diagnose_matching.py` - Debug track matching issues
- `fuzzy-matchnames.py` - Fuzzy string matching utilities
- `split_stack.py` - Dataset segmentation tools

## Configuration

### Taxonomy Mapping
Customize metadata categories in `config/taxonomy_mapping_final.json`:
```json
{
  "vibe": ["Arabian", "Dark", "Epic", "Whimsy"],
  "sound": ["Acid-Tinged", "Bouncy", "Hypnotic"],
  "emotionality": ["Sentimental", "Haunting", "Euphoric"]
}
```

### Playlist Mappings
Edit `config/setlists_mapping.csv` and `config/crates_mapping.csv` to adjust which playlists/crates map to which metadata columns.

## Advanced Features

### String Normalization
The pipeline uses sophisticated normalization to achieve 93.8% match accuracy:

```python
# Handles possessives
"Umai_s Dance" → "umais dance" ✓ matches "Umai's Dance"

# Multi-word artist remixes
"Prescience - Alex O'Rion Remix" → "prescience" ✓

# Unicode normalization
"Salomé's Filth" → "salomes filth" ✓
```

### Taxonomy Application
127 taxonomic mappings across 8 metadata dimensions:
- **Vibe**: Atmospheric characteristics (59 categories)
- **Sound**: Sonic textures (20 categories)
- **Emotionality**: Emotional impact (17 categories)
- **Prominent Instruments**: Lead instruments (12 categories)
- **Placement**: DJ set positioning (12 categories)
- **Motif**: Thematic elements (Fae, Rain, Cosmic)
- **Culture**: Geographic/cultural markers
- **Language**: Track language tags

## Troubleshooting

### Low Match Rate
- Check track name formatting in source CSVs
- Verify ISRC codes are present
- Run `diagnose_matching.py` to identify issues

### Missing Metadata
- Ensure playlists have correct mappings in `config/`
- Check taxonomy JSON for category definitions
- Review merge logs in `archive/logs/`

### Unicode Errors
- Run `fix_accents.py` to normalize diacritics
- Use `cleanup_on_aisle_csv.py` for corruption

## Contributing

This is a personal project, but if you find it useful and want to adapt it:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test with your own dataset
5. Submit a pull request

## License

MIT License - See LICENSE file for details

## Acknowledgments

Built to manage a 4,400+ track electronic music library spanning:
- 109 thematic Spotify playlists
- 200 Serato DJ crates
- 59 vibe categories
- 20 sound descriptors
- Metadata from Spotify API, Beatport, and local libraries

---

**Pipeline Status**: Production-ready  
**Match Accuracy**: 93.8%  
**Total Enriched Tracks**: 4,438  
**Last Updated**: December 2024
