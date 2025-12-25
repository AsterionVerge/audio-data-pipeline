import pandas as pd
from pathlib import Path

# ---------- CONFIG ----------
# Adjust these only if you rename or move the files
BASE_DIR = Path(r"C:\Users\fulmi\Downloads\Set Lists")
MIK_PATH = BASE_DIR / "mik_full_export.csv"
ESSENTIAL_PATH = BASE_DIR / "essential_mix_final_enriched.csv"
OUTPUT_PATH = BASE_DIR / "essential_mix_final_with_mik.csv"
LOG_PATH = BASE_DIR / "mik_merge_log.txt"
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

    Expected energy format examples:
        "8A - 123.00 - 6"
        "7A-128.00-8"
    Energy is the *last* piece (6, 8, etc).

    If the value looks like a comment (e.g. "Purchased on Beatport"),
    or cannot be parsed into a final integer, return None so that
    Essential Mix's Energy is left untouched.
    """
    if pd.isna(val):
        return None

    text = str(val).strip()
    if not text:
        return None

    # Try to split on '-' and look at the last part
    parts = [p.strip() for p in text.split('-')]
    if len(parts) < 3:
        # Not in "key - bpm - energy" format → treat as comment, skip
        return None

    last = parts[-1]

    # Keep only digits (and optionally one decimal point), then test
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
    if "isrc" not in mik.columns:
        raise KeyError("MIK CSV must have an 'isrc' column (lowercase).")

    if "ISRC" not in essential.columns:
        raise KeyError("Essential Mix CSV must have an 'ISRC' column (uppercase).")

    mik["__ISRC"] = mik["isrc"].apply(normalize_isrc)
    essential["__ISRC"] = essential["ISRC"].apply(normalize_isrc)

    mik_valid_isrc = mik["__ISRC"].notna().sum()
    essential_valid_isrc = essential["__ISRC"].notna().sum()
    print(f"MIK tracks with valid ISRC: {mik_valid_isrc}")
    print(f"Essential Mix tracks with valid ISRC: {essential_valid_isrc}")

    # ----- Log duplicates in MIK -----
    dup_mask = mik["__ISRC"].duplicated(keep=False) & mik["__ISRC"].notna()
    dups = mik.loc[dup_mask].sort_values("__ISRC")

    with open(LOG_PATH, "w", encoding="utf-8") as log:
        if len(dups) == 0:
            log.write("No duplicate ISRCs found in MIK.\n")
        else:
            log.write("Duplicate ISRCs found in MIK:\n")
            for isrc_val, group in dups.groupby("__ISRC"):
                log.write(f"{isrc_val} → {len(group)} rows\n")
            log.write("\n")

    # ----- Build lookup from MIK keyed by normalized ISRC -----
    lookup = {}
    for _, row in mik.iterrows():
        key = row["__ISRC"]
        if not key:
            continue

        # Keep the FIRST occurrence for each ISRC
        if key in lookup:
            continue

        lookup[key] = {
            "bpm": row.get("bpm"),
            "key": row.get("key"),
            "genre": row.get("genre"),
            "label": row.get("label"),
            "energy": parse_energy(row.get("energy")),
        }

    print(f"Unique ISRCs in MIK lookup: {len(lookup)}")

    # ----- Update Essential Mix from lookup -----
    # Convert target columns to object dtype to avoid FutureWarning
    essential["Key (Camelot)"] = essential["Key (Camelot)"].astype("object")
    essential["Release Label"] = essential["Release Label"].astype("object")
    essential["Genre"] = essential["Genre"].astype("object")
    essential["Track BPM"] = essential["Track BPM"].astype("object")
    essential["Energy"] = essential["Energy"].astype("object")

    updated_rows = 0
    updated_energy_count = 0
    matched_isrcs = set()

    for idx, row in essential.iterrows():
        key = row["__ISRC"]
        if not key or key not in lookup:
            continue

        matched_isrcs.add(key)
        mik_row = lookup[key]
        updated_rows += 1

        # bpm → Track BPM
        bpm_val = mik_row["bpm"]
        if pd.notna(bpm_val):
            essential.at[idx, "Track BPM"] = bpm_val

        # key → Key (Camelot)
        key_val = mik_row["key"]
        if pd.notna(key_val):
            essential.at[idx, "Key (Camelot)"] = key_val

        # genre → Genre
        genre_val = mik_row["genre"]
        if pd.notna(genre_val):
            essential.at[idx, "Genre"] = genre_val

        # label → Release Label
        label_val = mik_row["label"]
        if pd.notna(label_val):
            essential.at[idx, "Release Label"] = label_val

        # parsed energy → Energy (only if parsed successfully)
        energy_val = mik_row["energy"]
        if energy_val is not None:
            essential.at[idx, "Energy"] = energy_val
            updated_energy_count += 1

    unmatched_in_mik = set(lookup.keys()) - matched_isrcs
    print(f"Tracks matched (ISRC in both): {len(matched_isrcs)}")
    print(f"Tracks in MIK but not in Essential: {len(unmatched_in_mik)}")

    # ----- Finalize & save -----
    # Drop helper column
    essential = essential.drop(columns=["__ISRC"])

    essential.to_csv(OUTPUT_PATH, index=False)

    # Append summary to log
    with open(LOG_PATH, "a", encoding="utf-8") as log:
        log.write(f"\n=== MERGE SUMMARY ===\n")
        log.write(f"MIK total tracks: {len(mik)}\n")
        log.write(f"Essential Mix total tracks: {len(essential)}\n")
        log.write(f"MIK tracks with valid ISRC: {mik_valid_isrc}\n")
        log.write(f"Essential Mix tracks with valid ISRC: {essential_valid_isrc}\n")
        log.write(f"Unique ISRCs in MIK: {len(lookup)}\n")
        log.write(f"Tracks matched (found in both): {len(matched_isrcs)}\n")
        log.write(f"Tracks in MIK but not in Essential: {len(unmatched_in_mik)}\n")
        log.write(f"Essential Mix rows updated: {updated_rows}\n")
        log.write(f"Rows with Energy overwritten from MIK: {updated_energy_count}\n")
        log.write(f"Output written to: {OUTPUT_PATH}\n")

    print(f"\nLog written to: {LOG_PATH}")


if __name__ == "__main__":
    main()
