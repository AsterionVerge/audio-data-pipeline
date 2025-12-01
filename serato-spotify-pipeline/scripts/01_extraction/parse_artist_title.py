import pandas as pd
import re

def parse_artist_title(title_extracted):
    """
    Extract artist and cleaned title from Track_Title_Extracted.
    
    Patterns handled:
    - Artist, Artist - Title (remix) -> Artist, Artist | Title (remix)
    - Artist - Title (mix) -> Artist | Title (mix)
    - Title (original) -> None | Title (original)
    - Title -> None | Title
    
    KEEPS remix/mix info as part of the title!
    Returns tuple (artist, title)
    """
    title_extracted = title_extracted.strip()
    
    # Check if there's a dash that separates artist from title
    if ' - ' in title_extracted:
        parts = title_extracted.split(' - ', 1)  # Split on first dash only
        artist_part = parts[0].strip()
        title_part = parts[1].strip()
    else:
        # No dash, so treat entire string as title (no artist)
        artist_part = None
        title_part = title_extracted
    
    return artist_part, title_part


# Read the CSV
df = pd.read_csv('crate_tags_with_titles.csv')

# Apply the parsing function to Track_Title_Extracted column
df[['Artist_Extracted', 'Track_Title_Cleaned']] = df['Track_Title_Extracted'].apply(
    lambda x: pd.Series(parse_artist_title(x))
)

# Reorder columns for clarity (optional)
column_order = [
    'filename',
    'Artist_Extracted',
    'Track_Title_Cleaned',
    'BPM',
    'Subgenre',
    'Emotional',
    'Genres',
    'Instruments',
    'Placement',
    'Sound',
    'Summons Sets',
    'Vibe',
    'Track_Title_Extracted'
]

df = df[column_order]

# Save
df.to_csv('crate_tags_with_titles_parsed.csv', index=False)

print(f"Done! Processed {len(df)} rows")
print(f"Rows with artist data: {df['Artist_Extracted'].notna().sum()}")
print(f"Rows without artist: {df['Artist_Extracted'].isna().sum()}")
print(f"\nSaved to: crate_tags_with_titles_parsed.csv")
