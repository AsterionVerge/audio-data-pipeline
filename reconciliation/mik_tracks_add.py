import pandas as pd
from pathlib import Path

# ---------- CONFIG ----------
BASE_DIR = Path(r"C:\Users\fulmi\Downloads\Set Lists")
MIK_PATH = BASE_DIR / "mik_full_export.csv"
ESSENTIAL_PATH = BASE_DIR / "essential_mix_final_enriched.csv"
OUTPUT_PATH = BASE_DIR / "essential_mix_final_with_mik_complete.csv"
LOG_PATH = BASE_DIR / "mik_append_log.txt"
# ----------------------------


def normalize_isrc(val):
    """Normalize ISRC to uppercase, stripped string, or None."""
    if pd.isna(val):
        return None
    s = str(val).strip()
    if not s:
        return None
    return s.upper()


def parse_energy(val):
    """
    Parse MIK's 'energy' field.
    Returns the last numeric component, or None if not in expected format.
    """
    if pd.isna(val):
        return None

    text = str(val).strip()
    if not text:
        return None

    parts = [p.strip() for p in text.split('-')]
    if len(parts) < 3:
        return None

    last = parts[-1]
    cleaned = "".join(ch for ch in last if (ch.isdigit()))
    if not cleaned:
        return None

    try:
        return int(cleaned)
    except ValueError:
        return None


def main():
    # ----- Load CSVs -----
    mik = pd.read_csv(MIK_PATH)
    essential = pd.read_csv(ESSENTIAL_PATH)

    print(f"MIK loaded: {len(mik)} tracks")
    print(f"Essential Mix loaded: {len(essential)} tracks")

    # ----- Normalize ISRC columns -----
    mik["__ISRC"] = mik["isrc"].apply(normalize_isrc)
    essential["__ISRC"] = essential["ISRC"].apply(normalize_isrc)

    # ----- Build set of ISRCs in Essential Mix -----
    essential_isrcs = set(essential["__ISRC"].dropna())
    print(f"Unique ISRCs in Essential Mix: {len(essential_isrcs)}")

    # ----- Find unmatched MIK tracks -----
    unmatched_mik = mik[~mik["__ISRC"].isin(essential_isrcs)].copy()
    print(f"Unmatched MIK tracks to append: {len(unmatched_mik)}")

    # ----- Map MIK columns to Essential Mix columns -----
    # Create a new dataframe with Essential Mix structure
    new_rows = []
    for _, mik_row in unmatched_mik.iterrows():
        new_row = {
            "Track Name": mik_row.get("title"),
            "Artist Name(s)": mik_row.get("artist"),
            "Album Name": mik_row.get("album"),
            "Album Image URL": None,
            "Album Release Date": None,
            "Genre": mik_row.get("genre"),
            "Key (Camelot)": mik_row.get("key"),
            "Key (Open)": None,
            "Language": None,
            "Liminality": None,
            "Popularity": None,
            "Release Label": mik_row.get("label"),
            "Spotify Track ID": None,
            "ISRC": mik_row.get("isrc"),
            "Track Duration (min)": None,
            "Track Preview URL": None,
            "Acousticness": None,
            "Danceability": None,
            "Energy": parse_energy(mik_row.get("energy")),
            "Instrumentalness": None,
            "Key (#)": None,
            "Liveness": None,
            "Loudness": None,
            "Mode": None,
            "Speechiness": None,
            "Track BPM": mik_row.get("bpm"),
            "Valence": None,
            "Vibe": None,
            "Motif": None,
            "Sound": None,
            "Culture": None,
            "Emotionality": None,
            "Prominent Instruments": None,
            "Placement": None,
            "Notes": None,
        }
        new_rows.append(new_row)

    # Create dataframe from new rows
    new_df = pd.DataFrame(new_rows)

    print(f"New rows created: {len(new_df)}")

    # ----- Append to Essential Mix -----
    combined = pd.concat([essential, new_df], ignore_index=True)

    print(f"Combined total: {len(combined)} tracks")

    # ----- Save -----
    combined.to_csv(OUTPUT_PATH, index=False)

    # ----- Log -----
    with open(LOG_PATH, "w", encoding="utf-8") as log:
        log.write(f"=== MIK APPEND SUMMARY ===\n")
        log.write(f"MIK total tracks: {len(mik)}\n")
        log.write(f"Essential Mix original: {len(essential)} tracks\n")
        log.write(f"Unmatched MIK tracks appended: {len(new_df)}\n")
        log.write(f"Combined total: {len(combined)} tracks\n")
        log.write(f"Output written to: {OUTPUT_PATH}\n")

    print(f"\nLog written to: {LOG_PATH}")


if __name__ == "__main__":
    main()
