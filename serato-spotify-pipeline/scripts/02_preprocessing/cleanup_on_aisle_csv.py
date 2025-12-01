import pandas as pd
import re
import unicodedata

IN_FILE = "mik_clean.csv"   # your pre-cleaned file
OUT_FILE = "mik_rules_applied.csv"

# Columns
SOUND_COL = "Sound"
VIBE_COL = "Vibe"
EMO_COL = "Emotionality"  # for Bliss → Light mapping in Sound
MOTIF_COL = "Motif"       # only used if you flip Robotics & Machinery destination

# Utilities
def norm_str(x):
    if pd.isna(x): return ""
    s = unicodedata.normalize("NFKC", str(x)).replace("\u00A0"," ")
    s = re.sub(r"\s+", " ", s).strip()
    return s

def split_multi(s):
    s = norm_str(s)
    if not s: return []
    return [t.strip() for t in s.split(",") if t.strip()]

def join_multi(items):
    # de-dupe, preserve order, clean commas/spaces
    seen = set()
    out = []
    for t in items:
        tt = norm_str(t)
        key = tt.lower()
        if tt and key not in seen:
            seen.add(key)
            out.append(tt)
    return ", ".join(out)

def remove_token(items, token, case_insensitive=True):
    out = []
    for t in items:
        if case_insensitive:
            if t.lower() == token.lower():  # exact, not substring
                continue
        else:
            if t == token:
                continue
        out.append(t)
    return out

def has_token(items, token):
    return any(t.lower() == token.lower() for t in items)

df = pd.read_csv(IN_FILE, dtype=str).fillna("")

# Parse lists
sound = df.get(SOUND_COL, "").map(split_multi)
vibe = df.get(VIBE_COL, "").map(split_multi)
emo  = df.get(EMO_COL, "").map(split_multi) if EMO_COL in df.columns else pd.Series([[]]*len(df))
motif = df.get(MOTIF_COL, "").map(split_multi) if MOTIF_COL in df.columns else pd.Series([[]]*len(df))

new_sound = []
new_vibe = []
new_motif = []
notes_flag = []  # to tag rows that contain out-of-canon values (Chaotic/Overwhelming)

for i in range(len(df)):
    S = sound.iloc[i][:]
    V = vibe.iloc[i][:]
    M = motif.iloc[i][:] if MOTIF_COL in df.columns else []

    # Clean up commas/spaces handled by join_multi at the end.

    # Deduplicate specific tokens in Vibe
    # - Haunting deduplicated
    # - Whimsy deduplicated
    # (generic de-dupe happens in join_multi; we just ensure exact token handling)
    # Nothing to do here beyond join_multi

    # Remove tokens from Vibe (do not move unless specified)
    # - Arab & Indian removed from Vibe
    V = remove_token(V, "Arab & Indian")

    # Move tokens across columns
    # - Light (delete from Vibe, add to Sound)
    if has_token(V, "Light"):
        V = remove_token(V, "Light")
        if not has_token(S, "Light"):
            S.append("Light")

    # - Dark move from Vibe to Sound
    if has_token(V, "Dark"):
        V = remove_token(V, "Dark")
        if not has_token(S, "Dark"):
            S.append("Dark")

    # - Robotics & Machinery moved to Sound (from Vibe). If you prefer Motif, append to M instead of S.
    if has_token(V, "Robotics & Machinery"):
        V = remove_token(V, "Robotics & Machinery")
        # Choose target: Sound (default)
        if not has_token(S, "Robotics & Machinery"):
            S.append("Robotics & Machinery")
        # If you want Motif instead, comment the two lines above and use:
        # if MOTIF_COL in df.columns and "Robotics & Machinery" not in [m.lower() for m in M]:
        #     M.append("Robotics & Machinery")

    # Remove tokens from Sound
    # - Remove Haunting from Sound
    S = remove_token(S, "Haunting")

    # - Remove Robot (without affecting Robotics & Machinery)
    # exact token match only
    S = remove_token(S, "Robot")

    # Remove tokens from Vibe
    # - Remove Beautiful from Vibe (we're canonically using Beautiful in Sound instead)
    V = remove_token(V, "Beautiful")

    # Global capitalization and canonicalization are assumed already handled in mik_clean.csv.
    # But ensure exact casing for the key terms touched:
    canon_fix = {
        "light":"Light", "dark":"Dark",
        "robot":"Robot", "robotics & machinery":"Robotics & Machinery",
        "beautiful":"Beautiful", "haunting":"Haunting", "whimsy":"Whimsy",
        "arab & indian":"Arab & Indian",
    }
    def canon_list(lst):
        out=[]
        for t in lst:
            c = canon_fix.get(t.lower(), t)
            out.append(c)
        return out

    S = canon_list(S)
    V = canon_list(V)
    M = canon_list(M)

    # Emotionality bridge:
    # - Bliss in Emotionality = add Light in Sound (don’t duplicate)
    if "Bliss" in [t.strip().title() for t in emo.iloc[i]]:
        if not has_token(S, "Light"):
            S.append("Light")

    # Out-of-canon tokens flagging (no change yet):
    # - Chaotic, Overwhelming (not sure what to do)
    # We leave them in place but flag the row for later review.
    if any(tok.lower() in {"chaotic","overwhelming"} for tok in V+S):
        notes_flag.append("Review: Chaotic/Overwhelming present")
    else:
        notes_flag.append("")

    new_sound.append(join_multi(S))
    new_vibe.append(join_multi(V))
    new_motif.append(join_multi(M))

df[SOUND_COL] = new_sound
df[VIBE_COL] = new_vibe
if MOTIF_COL in df.columns:
    df[MOTIF_COL] = new_motif

# Optional: add a column to help you filter remaining out-of-canon tokens
df["QA Flags"] = notes_flag

df.to_csv(OUT_FILE, index=False)
print(f"Wrote {OUT_FILE}")