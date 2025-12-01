# PLAYLIST MERGER - QUICK REFERENCE

## 🚀 Quick Start

```bash
python playlist_merger.py
```

That's it. The script will:
1. Load your master file
2. Load all 109 playlists
3. Match via ISRC
4. Apply taxonomy
5. Output enriched file + report

---

## 📊 Taxonomy Summary

| Category | Count | Examples |
|----------|-------|----------|
| **Vibe** | 59 | arabian, forest, dark, space, epic, gay, psychedelic |
| **Sound** | 20 | bouncy, acid-tinged, hypnotic, rave, classic |
| **Emotional** | 17 | euphoric, sad, sentimental, romantic |
| **Instruments** | 12 | guitar, piano, brass, strings, didgeridoo |
| **Culture** | 5 | arabian, french |
| **Placement** | 12 | intro, outro, summons |

---

## 📁 File Structure

```
your_working_directory/
├── playlist_merger.py              ← Main script
├── taxonomy_mapping_final.json     ← Mapping reference
├── essential_mix_clean_final.csv   ← Your master file (INPUT)
├── arabian.csv                     ← Playlists (all 109)
├── set_28_-_teardrop.csv
├── summons_viii.csv
└── ... (100+ more playlist CSVs)
```

---

## 📤 Outputs

After running:

**1. `essential_mix_final_enriched.csv`**
- Your enriched master file
- New columns: vibe, sound, culture, emotional_layers, prominent_instruments, placement
- Multi-value fields use pipe delimiter: `"arabian|epic|bouncy"`

**2. `merge_report.json`**
Statistics:
```json
{
  "playlists_processed": 105,
  "matched_in_master": 7891,
  "unmatched_tracks": 342,
  "enrichment_summary": {
    "vibe": 3456,
    "sound": 2123,
    "emotional_layers": 1987,
    ...
  }
}
```

---

## 🔧 Configuration

Edit these at the bottom of `playlist_merger.py`:

```python
MASTER_FILE = 'essential_mix_clean_final.csv'      # Your master file
PLAYLISTS_DIR = './'                                # Directory with playlists
TAXONOMY_FILE = 'taxonomy_mapping_final.json'       # Taxonomy mapping
OUTPUT_FILE = 'essential_mix_final_enriched.csv'    # Output file
REPORT_FILE = 'merge_report.json'                   # Report output
```

---

## ⚙️ How It Works

1. **Load Phase**
   - Reads master file (with ISRC column)
   - Reads all playlist CSVs
   - Creates ISRC index for fast lookup

2. **Match Phase**
   - For each track in each playlist
   - Finds matching ISRC in master file
   - Applies corresponding taxonomy mapping

3. **Aggregate Phase**
   - Combines multiple values per track
   - Removes duplicates
   - Preserves existing data

4. **Enrich Phase**
   - Populates vibe, sound, emotional_layers, etc.
   - Multi-value fields pipe-delimited
   - Exports to CSV

5. **Report Phase**
   - Generates detailed merge statistics
   - Lists unmatched tracks
   - Shows enrichment summary

---

## 📋 Column Mapping Reference

### Playlists → Columns

**Vibe Examples:**
- arabian.csv → vibe: "arabian" + culture: "arabian"
- set_81_-_dreamscape.csv → vibe: "dreamy"
- set_12_-_whorl_of_light.csv → vibe: "light"

**Sound Examples:**
- set_49_-_bounce.csv → sound: "bouncy"
- set_14_-_ph-14.csv → sound: "acid-tinged"
- set_80_-_classic.csv → sound: "classic"

**Emotional Examples:**
- set_28_-_teardrop.csv → emotional_layers: "sad"
- set_55_-_instant_smile.csv → emotional_layers: "euphoric"
- set_41_-_melt.csv → emotional_layers: "sentimental"

**Instruments Examples:**
- set_63_-_guitar.csv → prominent_instruments: "guitar"
- set_24_-_brass_up_the_ass.csv → prominent_instruments: "brass"
- all_the_vocals.csv → prominent_instruments: "vocalizations"

**Culture/Language Examples:**
- set_76_-_la_touche_française.csv → culture: "french", language: "french"
- oasis.csv → vibe: "arabian", culture: "arabian"

**Placement Examples:**
- intros.csv → placement: "intro"
- outros_&_dips.csv → placement: "outro"
- summons_viii.csv → placement: "summons"

---

## ⚠️ Ignored Files

These are automatically skipped:
- liked.csv
- beatport.csv
- set_139_-_biome.csv (manual review needed)
- set_161_-_rain.csv (user handling)
- set_162_-_unique_instrument.csv
- spire_abyss.csv
- it's_a_fast'un.csv

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| "ISRC column not found" | Verify column exists in master file |
| Low match rate (< 50%) | Check ISRC formatting consistency |
| `ModuleNotFoundError: pandas` | Run `pip install pandas` |
| File encoding errors | Ensure CSVs are UTF-8 encoded |
| Script hangs | Check file sizes; use smaller sample for testing |

---

## 💡 Tips

- **Test run**: Copy a few playlist CSVs to test directory first
- **Backup**: Keep original `essential_mix_clean_final.csv` backed up
- **ISRC format**: Ensure all ISRC codes are consistent (e.g., no extra spaces)
- **Multi-values**: Pipe-delimited allows easy splitting in Excel or Python
- **Unmatched**: Review `merge_report.json` for tracks in playlists but not master

---

## 📈 Expected Results

**Typical stats:**
- 105-109 playlists processed
- 7,500-8,500 playlist tracks matched
- 85-90% match rate (some playlists have tracks not in Essential Mix)
- Average 3-5 values per enriched column per track

---

## 🎯 Next Steps

1. Place all files in same directory
2. Run `python playlist_merger.py`
3. Check `merge_report.json` for statistics
4. Review `essential_mix_final_enriched.csv`
5. Use enriched data for analysis, playlisting, or further processing

---

**Version:** 1.0  
**Total Playlists:** 109  
**Enrichment Columns:** 6  
**Status:** Production Ready
