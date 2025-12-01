import pandas as pd
from pathlib import Path
import unicodedata

# ---------- CONFIG ----------
BASE_DIR = Path(r"C:\Users\fulmi\Downloads")
INPUT_PATH = BASE_DIR / "crate_tags_unmatched_COMPLETE.csv"
OUTPUT_PATH = BASE_DIR / "crate_tags_unmatched.csv"
# ----------------------------


def fix_mojibake(text):
    """
    Fix UTF-8 text that was misread as Latin-1/Windows-1252.
    """
    if pd.isna(text):
        return text
    if not isinstance(text, str):
        return text

    try:
        # Encode back to Latin-1 bytes, then decode as UTF-8
        fixed = text.encode('latin-1').decode('utf-8')
        return fixed
    except (UnicodeDecodeError, UnicodeEncodeError):
        # If it fails, the text is probably fine or broken beyond repair
        return text


def normalize_unicode(text):
    """
    Normalize Unicode to NFC (Canonical Decomposition, followed by Canonical Composition).
    This ensures consistent representation of accented characters.
    E.g., é can be represented as a single character or as e + combining accent mark.
    """
    if pd.isna(text):
        return text
    if not isinstance(text, str):
        return text

    return unicodedata.normalize('NFC', text)


def main():
    # Read with UTF-8 first (pandas default)
    df = pd.read_csv(INPUT_PATH, encoding='utf-8')

    print(f"Loaded: {len(df)} rows")

    # Apply fixes to all string columns
    text_columns = df.select_dtypes(include=['object']).columns
    mojibake_fixed = 0
    unicode_normalized = 0

    for col in text_columns:
        original = df[col].copy()

        # First pass: fix mojibake
        df[col] = df[col].apply(fix_mojibake)
        mojibake_fixed += ((original != df[col]) & original.notna()).sum()

        # Second pass: normalize Unicode
        pre_norm = df[col].copy()
        df[col] = df[col].apply(normalize_unicode)
        unicode_normalized += ((pre_norm != df[col]) & pre_norm.notna()).sum()

    print(f"Fixed {mojibake_fixed} cells with mojibake encoding issues")
    print(f"Normalized {unicode_normalized} cells for Unicode consistency")

    # Save with explicit UTF-8 encoding
    df.to_csv(OUTPUT_PATH, index=False, encoding='utf-8-sig')

    print(f"Output written to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
