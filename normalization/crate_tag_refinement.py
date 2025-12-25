import pandas as pd
from pathlib import Path
import re

INPUT_CSV = Path("crate_tags.csv")
OUTPUT_CSV = Path("crate_tags_aligned.csv")

# Target schema columns (adjust as needed)
TARGET_COLUMNS = [
    "filename", "BPM", "Core", "Emotionality", "Genre", "Prominent Instruments", "Placement", "Sound", "Set", "Vibe"

# Helper function to extract genre/subgenre
def genre_subgenre_split(value):
    if "_" in value:
        main, sub = value.split("_", 1)
        return main, sub
    return value, ""

def parse_crate_tag_row(row):
    # This function aligns each row (from parsed crate tags) to the target schema
    out = {col: "" for col in TARGET_COLUMNS}
    out["filename"] = row.get("filename", "")
    
    # Handle Genre/Subgenre logic
    genre_tags = row.get("Genres", "")
    subgenre_tags = []
    genres = []
    if genre_tags:
        for g in genre_tags.split(";"):
            g_clean = g.strip()
            # Detect 'main_sub' case (ProgHouse_Deep Prog)
            if "_" in g_clean:
                main, sub = genre_subgenre_split(g_clean)
                genres.append(main)
                subgenre_tags.append(sub)
            else:
                genres.append(g_clean)
    out["Genre"] = "; ".join(set(genres))
    out["Subgenre"] = "; ".join(set(subgenre_tags))
    
    # Standard column mappings (copy direct from parsed if present)
    mapping = {
        "BPM": "Track BPM",
        "Vibe": "Vibe",
        "Sound": "Sound",
        "Instruments": "Prominent Instruments",
        "Placement", "Intros", "Outros": "Placement",
        "Emotional": "Emotionality",
        "Summons Sets": "Set",
	"Summons XVIII - Aerodynamix": "Set"
	"Trance", "Techno", "Genres", "Other & Special", "ProgHouse", "Core": "Genre"
	"
        # add others as needed
    }
    for src, tgt in mapping.items():
        if src in row:
            out[tgt] = row[src]

    # All other target columns remain blank for this alignment step
    return out

def main():
    df_raw = pd.read_csv(INPUT_CSV)

    aligned_rows = []
    for idx, row in df_raw.iterrows():
        parsed = parse_crate_tag_row(row)
        aligned_rows.append(parsed)
    
    df_aligned = pd.DataFrame(aligned_rows, columns=TARGET_COLUMNS)
    df_aligned.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")
    print(f"Aligned data written to: {OUTPUT_CSV}")

if __name__ == "__main__":
    main()
