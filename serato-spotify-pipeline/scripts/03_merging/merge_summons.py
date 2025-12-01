import pandas as pd
from pathlib import Path

TRACKLIST_PATH = Path("tracklist_full.csv")
SETS_FOLDER = Path(".")
OUTPUT_PATH = Path("tracklist_full_with_sets.csv")

ISRC_COL_TRACKS = "ISRC"
SET_COL_TRACKS = "Set"
ISRC_COL_SETFILES = "ISRC"

set_file_to_name = {
    "global_scale.csv": "Global Scale",
    "spire_abyss.csv": "Spire / Abyss",
    "summons_viii.csv": "Summons VIII",
    "summons_xi.csv": "Summons XI",
    "summons_xii.csv": "Summons XII",
    "summons_xiii_-inundate.csv": "Summons XIII - Inundate",
    "summons_xiv-interstellar_love_story.csv": "Summons XIV - Interstellar Love Story",
    "summons_xv-halloween_2023.csv": "Summons XV - Halloween 2023",
    "summons_xvi-what_wilds_whistle.csv": "Summons XVI - What Whistles Wild Wild",
    "summons_xvii-_the_homosexual_urge.csv": "Summons XVII - The Homosexual Urge",
}


def normalize_isrc(x):
    if pd.isna(x):
        return None
    s = str(x).strip().upper()
    return s if s else None


def main():
    tracks = pd.read_csv(TRACKLIST_PATH, dtype="unicode")

    if ISRC_COL_TRACKS not in tracks.columns:
        raise ValueError(f"tracklist file missing '{ISRC_COL_TRACKS}' column")

    if SET_COL_TRACKS not in tracks.columns:
        tracks[SET_COL_TRACKS] = ""

    tracks[SET_COL_TRACKS] = tracks[SET_COL_TRACKS].astype("object")
    tracks["__ISRC"] = tracks[ISRC_COL_TRACKS].apply(normalize_isrc)

    isrc_to_sets = {}

    for filename, set_name in set_file_to_name.items():
        set_path = SETS_FOLDER / filename
        if not set_path.exists():
            print(f"WARNING: Set file not found: {set_path}")
            continue

        df = pd.read_csv(set_path, dtype="unicode")

        if ISRC_COL_SETFILES not in df.columns:
            raise ValueError(f"Set file '{filename}' missing '{ISRC_COL_SETFILES}' column")

        df["__ISRC"] = df[ISRC_COL_SETFILES].apply(normalize_isrc)
        df_valid = df[df["__ISRC"].notna()]

        for isrc in df_valid["__ISRC"]:
            if isrc not in isrc_to_sets:
                isrc_to_sets[isrc] = []
            isrc_to_sets[isrc].append(set_name)

    updated_rows = 0

    for idx, row in tracks.iterrows():
        isrc = row["__ISRC"]
        if not isrc:
            continue
        if isrc not in isrc_to_sets:
            continue

        set_names = ", ".join(isrc_to_sets[isrc])
        current = tracks.at[idx, SET_COL_TRACKS]
        current_str = str(current).strip() if pd.notna(current) else ""

        if current_str != set_names:
            tracks.at[idx, SET_COL_TRACKS] = set_names
            updated_rows += 1

    tracks = tracks.drop(columns=["__ISRC"])
    tracks.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")

    print(f"Tracks updated with Set: {updated_rows}")
    print(f"Output written to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
