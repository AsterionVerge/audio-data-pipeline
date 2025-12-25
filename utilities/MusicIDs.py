import os
import re
import pandas as pd
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

print("Spotify enrichment script starting up...")

load_dotenv()
CID = os.getenv("SPOTIFY_CLIENT_ID")
SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

if not CID or not SECRET:
    print("ERROR: SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET not found in .env.")
    exit(1)

sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=CID, client_secret=SECRET))

def spotify_track_id_from_isrc(isrc: str) -> str | None:
    if not isrc:
        return None
    q = f"isrc:{isrc}"
    try:
        res = sp.search(q=q, type="track", limit=1)
        items = res.get("tracks", {}).get("items", [])
        return items[0]["id"] if items else None
    except Exception as e:
        print(f"  [Spotify] Search error for ISRC {isrc}: {e}")
        return None

def enrich_csv(input_csv: str, output_csv: str) -> None:
    print(f"Loading CSV file: {input_csv}")
    for encoding in ["utf-8", "latin1", "cp1252"]:
        try:
            df = pd.read_csv(input_csv, encoding=encoding)
            print(f"✅ Loaded with {encoding}")
            break
        except Exception as e:
            print(f"Failed with {encoding}: {e}")
    else:
        print("❌ Could not read CSV.")
        exit(1)

    # Ensure columns exist and are string dtype
    for col in ["Track Name", "ISRC", "Spotify Track ID"]:
        if col not in df.columns:
            df[col] = pd.Series(dtype="string")
        else:
            df[col] = df[col].astype("string")

    print(f"Processing {len(df)} rows...")
    updated = 0

    for idx, row in df.iterrows():
        raw_isrc = row.get("ISRC")
        if pd.isna(raw_isrc):
            isrc = ""
        else:
            isrc = str(raw_isrc).strip()
        if not re.match(r"^[A-Z0-9]{12}$", isrc, re.IGNORECASE):
            continue

        sp_id = spotify_track_id_from_isrc(isrc)
        if sp_id:
            df.at[idx, "Spotify Track ID"] = sp_id
            print(f"Row {idx+1}: Spotify ID updated: {sp_id}")
            updated += 1

    df.to_csv(output_csv, index=False)
    print(f"\n✓ Spotify enrichment complete. Updated {updated} rows.")
    print(f"✓ Output file saved: {output_csv}")

if __name__ == "__main__":
    in_csv  = "essential_mix_export.csv"
    out_csv = "essential_mix_enriched.csv"
    enrich_csv(in_csv, out_csv)
