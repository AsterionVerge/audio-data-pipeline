import pandas as pd
import re

def parse_crate_hierarchy(crate_tag):
    """
    Parse crate tags into parent category and subcategory.
    
    Examples:
        'BPM_121-123' -> ('BPM', '121-123')
        'Genres_Melodic House' -> ('Genres', 'Melodic House')
        'Sound_Instruments_Piano' -> ('Instruments', 'Piano')
        'Vibe_Emotional_Sexy' -> ('Vibe', 'Emotional_Sexy')
    """
    # Special handling for nested categories
    if crate_tag.startswith('Sound_Instruments_'):
        return ('Instruments', crate_tag.replace('Sound_Instruments_', ''))
    
    if crate_tag.startswith('Vibe_Emotional_'):
        return ('Vibe', crate_tag.replace('Vibe_', ''))
    
    # Handle standard parent_child format
    parts = crate_tag.split('_', 1)
    
    if len(parts) == 2:
        parent, child = parts
        
        # Consolidate similar parents
        if parent in ['Summons Sets', 'Special Sets', 'Sets (in dev)']:
            return ('Sets', child)
        
        if parent == 'Sound':
            return ('Sound', child)
        
        return (parent, child)
    
    # Single-level crates (like 'Sort', 'Recorded')
    return ('Other', crate_tag)


def restructure_crate_tags(input_csv, output_csv):
    """
    Convert flat crate_tags column into structured categorical columns.
    
    Input format:
        filename, crate_tags
        track.mp3, "BPM_124-125, Genres_Deep House, Vibe_Epic"
    
    Output format:
        filename, BPM, Genres, Vibe, Instruments, Sound, Placement, Sets, Sort, Other
        track.mp3, 124-125, Deep House, Epic, [empty], [empty], [empty], [empty], [empty], [empty]
    """
    print(f"Loading {input_csv}...")
    df = pd.read_csv(input_csv)
    
    print(f"Loaded {len(df)} tracks")
    
    # Initialize category columns
    categories = {
        'BPM': [],
        'Genres': [],
        'Vibe': [],
        'Instruments': [],
        'Sound': [],
        'Placement': [],
        'Sets': [],
        'Sort': [],
        'Other': []
    }
    
    # Process each row
    for idx, row in df.iterrows():
        if idx % 1000 == 0:
            print(f"Processing row {idx}/{len(df)}...")
        
        filename = row['filename']
        crate_tags_str = row['crate_tags']
        
        # Parse tags
        crate_tags = [tag.strip() for tag in crate_tags_str.split(',')]
        
        # Build category dict for this track
        track_categories = {cat: [] for cat in categories.keys()}
        
        for tag in crate_tags:
            parent, child = parse_crate_hierarchy(tag)
            if parent in track_categories:
                track_categories[parent].append(child)
        
        # Convert lists to pipe-separated strings (easier for filtering later)
        for cat in categories.keys():
            if track_categories[cat]:
                categories[cat].append(' | '.join(track_categories[cat]))
            else:
                categories[cat].append('')
    
    # Build output dataframe
    output_df = pd.DataFrame({
        'filename': df['filename'],
        **categories
    })
    
    # Add summary stats
    print("\n=== Category Coverage ===")
    for cat in categories.keys():
        non_empty = output_df[cat].astype(bool).sum()
        pct = (non_empty / len(output_df)) * 100
        print(f"{cat}: {non_empty}/{len(output_df)} tracks ({pct:.1f}%)")
    
    # Save
    output_df.to_csv(output_csv, index=False)
    print(f"\n✓ Saved restructured data to {output_csv}")
    
    return output_df


# === USAGE ===
if __name__ == "__main__":
    input_csv = 'all_tracks_crate_tags.csv'
    output_csv = 'crate_tags_structured.csv'
    
    df = restructure_crate_tags(input_csv, output_csv)
    
    # Show sample
    print("\n=== Sample Output (first 5 rows) ===")
    print(df.head())
    
    print("\nDone!")