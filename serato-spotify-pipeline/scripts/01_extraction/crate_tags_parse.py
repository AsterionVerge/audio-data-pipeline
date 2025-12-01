import pandas as pd
import re
import os

INPUT_CSV = "crate_tags_with_titles.csv"
OUTPUT_CSV = "crate_tags_with_titles_2.csv"

def extract_title_from_filename(fname):
    base, _ = os.path.splitext(str(fname))

    # Case 1: "01 - title"
    m = re.match(r"^\s*\d{2}\s*-\s*(.+)$", base)
    if m:
        return m.group(1).strip()

    # Case 2: "NNNNNNN_title"  (digits + underscore)
    m = re.match(r"^\s*\d{5,9}_(.+)$", base)
    if m:
        return m.group(1).strip()

    # Case 3: "artist - track"   (no prefix, artist and track)
    if " - " in base:
        return base.strip()

    # Case 4: Just the file name (e.g. "ambiance")
    return base.strip()

def main():
    df = pd.read_csv(INPUT_CSV)

    # If the filename column is not present, error out with message
    if "filename" not in df.columns:
        raise ValueError("Your CSV must include a 'filename' column to extract track titles.")

    # Apply extraction to build Track_Title_Extracted
    df["Track_Title_Extracted"] = df["filename"].apply(extract_title_from_filename)
    # Save with both original filename and extracted title
    df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")
    print(f"Wrote {OUTPUT_CSV} with both filename and Track_Title_Extracted!")

if __name__ == "__main__":
    main()
