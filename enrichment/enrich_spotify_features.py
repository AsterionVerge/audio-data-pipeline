# enrich_spotify_features.py
# Run from PowerShell (in Downloads):
#   py .\enrich_spotify_features.py
# Requires .env with:
#   SPOTIFY_CLIENT_ID=your_id
#   SPOTIFY_CLIENT_SECRET=your_secret

import os
import time
import pandas as pd
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from spotipy.exceptions import SpotifyException

KEY_MAP = ['C','C♯/D♭','D','D♯/E♭','E','F','F♯/G♭','G','G♯/A♭','A','A♯/B♭','B']

def camelot_key(key_index, mode):
    CAMELOT = ['8B','3B','10B','5B','12B','7B','2B','9B','4B','11B','6B','1B',
               '5A','12A','7A','2A','9A','4A','11A','6A','1A','8A','3A','10A']
    try:
        i = int(key_index)
        m = int(mode)  # 1=major, 0=minor
        return CAMELOT[i + (0 if m == 1 else 12)]
    except Exception:
        return ""

def load_csv_any_encoding(path: str) -> pd.DataFrame:
    last_err = None
    for enc in ["utf-8", "utf-8-sig", "latin1", "cp1252"]:
        try:
            df = pd.read_csv(path, encoding=enc)
            print(f"✅ Loaded CSV with encoding: {enc}")
            return df
        except Exception as e:
            last_err = e
            print(f"Failed with {enc}: {e}")
    raise last_err

def safe_audio_features(sp, track_id: str, retry_sleep=3.0):
    # Use single-item endpoint to avoid batch 403s
    path = f"audio-features/{track_id}"
    try:
        feat = sp._get(path)  # single-item, returns dict or {}
        return feat if feat and isinstance(feat, dict) and feat.get("id") else None
    except SpotifyException as e:
        if e.http_status == 403:
            print(f"   ↪ single audio_features 403 for {track_id}, retrying after {retry_sleep:.0f}s…")
            time.sleep(retry_sleep)
            try:
                feat = sp._get(path)
                return feat if feat and isinstance(feat, dict) and feat.get("id") else None
            except SpotifyException as e2:
                if e2.http_status == 403:
                    print(f"   ↪ still 403; skipping audio features for {track_id}")
                    return None
                else:
                    print(f"   ↪ Spotify {e2.http_status} on retry: {e2.msg}")
                    return None
        else:
            print(f"   ↪ Spotify {e.http_status}: {e.msg}")
            return None
    except Exception as e:
        print(f"   ↪ Other error on single audio_features: {repr(e)}")
        return None

def enrich_spotify(input_csv: str, output_csv: str, market: str = "US", per_row_delay_sec: float = 1.5) -> None:
    print(f"Loading CSV file: {input_csv}")
    df = load_csv_any_encoding(input_csv)

    required_cols = [
        "Spotify Track ID",
        "Genre",
        "Key (Camelot)",
        "Key (Open)",
        "Energy Level",
        "Track BPM",
        "Popularity",
        "Release Label"
    ]
    for col in required_cols:
        if col not in df.columns:
            df[col] = pd.Series(dtype="string")
        else:
            df[col] = df[col].astype("string")

    load_dotenv()
    CID = os.getenv("SPOTIFY_CLIENT_ID")
    SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
    if not CID or not SECRET:
        raise SystemExit("ERROR: SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET not found in .env")

    sp = spotipy.Spotify(
        auth_manager=SpotifyClientCredentials(client_id=CID, client_secret=SECRET),
        requests_timeout=20,
        retries=3
    )

    print(f"Processing {len(df)} rows…")
    updated = 0

    for idx, row in df.iterrows():
        track_id = row.get("Spotify Track ID")
        if pd.isna(track_id) or not isinstance(track_id, str) or not track_id.strip():
            continue
        track_id = track_id.strip()

        # 1) Track metadata first (reduces relinking weirdness)
        try:
            meta = sp.track(track_id, market=market)
        except SpotifyException as e:
            print(f"[{idx+1}] Spotify {e.http_status}: {e.msg} (id={track_id}) — skipping row")
            time.sleep(per_row_delay_sec)
            continue
        except Exception as e:
            print(f"[{idx+1}] Other error {repr(e)} (id={track_id}) — skipping row")
            time.sleep(per_row_delay_sec)
            continue

        # 2) Audio features (tolerate 403s)
        features = safe_audio_features(sp, track_id, retry_sleep=3.0)

        # Genre via primary artist
        genre = ""
        try:
            artists = meta.get("artists", [])
            if artists:
                artist_id = artists[0]["id"]
                artist_obj = sp.artist(artist_id)
                genre = ", ".join(artist_obj.get("genres", [])) or ""
        except Exception:
            genre = ""

        # Keys / energy / tempo
        open_key = ""
        camelot = ""
        energy = ""
        tempo = ""
        if features:
            key_index = features.get("key", None)
            mode = features.get("mode", 1)
            open_key = KEY_MAP[key_index] if isinstance(key_index, int) and 0 <= key_index < 12 else ""
            camelot = camelot_key(key_index, mode) if open_key else ""
            energy = features.get("energy", "")
            tempo = features.get("tempo", "")

        popularity = meta.get("popularity", "")
        label = ""
        try:
            label = meta.get("album", {}).get("label", "") or ""
        except Exception:
            label = ""

        # Write back
        df.at[idx, "Genre"] = str(genre)
        df.at[idx, "Key (Open)"] = str(open_key)
        df.at[idx, "Key (Camelot)"] = str(camelot)
        df.at[idx, "Energy Level"] = (f"{float(energy):.3f}" if str(energy) not in ("", "None") else "")
        df.at[idx, "Track BPM"] = (f"{float(tempo):.2f}" if str(tempo) not in ("", "None") else "")
        df.at[idx, "Popularity"] = str(popularity if popularity != "" else "")
        df.at[idx, "Release Label"] = str(label)

        updated += 1
        if updated % 25 == 0:
            print(f"…{updated} rows updated so far")
        time.sleep(per_row_delay_sec)

    df.to_csv(output_csv, index=False)
    print(f"\n✓ Spotify feature enrichment complete. Updated {updated} rows.")
    print(f"✓ Output file saved: {output_csv}")

if __name__ == "__main__":
    in_csv = "essential_mix_enriched.csv"
    out_csv = "essential_mix_final_enriched.csv"
    enrich_spotify(in_csv, out_csv, market="US", per_row_delay_sec=1.5)