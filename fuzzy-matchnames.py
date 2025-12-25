# RECONCILIATION STAGE (representative)
# Illustrates confidence-aware fuzzy matching and traceable join decisions
# used to reconcile inconsistent creative metadata across sources.

import pandas as pd
import re
from difflib import SequenceMatcher

def parse_filename(filename):
    """
    Extract track and artist from filename.
    
    Common patterns:
        "01 - baba yetu [feat. soweto gospel choir].mp3"
        "12345678_Artist Name_Track Name_(Remix).mp3"
        "Artist - Track Name.mp3"
        "Track Name (Artist Remix).mp3"
    
    Returns: (artist, track, confidence)
    """
    # Remove extension
    name = filename.rsplit('.', 1)[0]
    
    # Pattern 1: Number_Artist_Track format (Beatport style)
    match = re.match(r'^\d+_([^_]+)_(.+?)(?:_\(([^)]+)\))?$', name)
    if match:
        artist = match.group(1).replace('_', ' ').strip()
        track = match.group(2).replace('_', ' ').strip()
        remix = match.group(3) if match.group(3) else None
        if remix:
            track = f"{track} ({remix})"
        return (artist, track, 0.9)
    
    # Pattern 2: "Artist - Track" or "Track - Artist"
    if ' - ' in name:
        parts = name.split(' - ', 1)
        # Could be either direction, return both possibilities
        return (parts[0].strip(), parts[1].strip(), 0.7)
    
    # Pattern 3: Track name with [feat. Artist]
    feat_match = re.search(r'\[feat\. ([^\]]+)\]', name, re.IGNORECASE)
    if feat_match:
        artist = feat_match.group(1).strip()
        track = re.sub(r'\[feat\. [^\]]+\]', '', name, flags=re.IGNORECASE).strip()
        return (artist, track, 0.6)
    
    # Pattern 4: Just the track name
    return (None, name.strip(), 0.3)


def fuzzy_match_score(str1, str2):
    """Calculate similarity between two strings (0-1)"""
    if not str1 or not str2:
        return 0
    return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()


def match_to_essential_mix(crate_df, essential_df, threshold=0.7):
    """
    Attempt to match crate filenames to Essential Mix tracks.
    
    Args:
        crate_df: Restructured crate tags (with filename column)
        essential_df: Essential Mix data (with Track Name, Artist Name columns)
        threshold: Minimum fuzzy match score to consider (0-1)
    
    Returns:
        DataFrame with matches and confidence scores
    """
    results = []
    
    print(f"Matching {len(crate_df)} filenames to {len(essential_df)} Essential Mix tracks...")
    
    for idx, crate_row in crate_df.iterrows():
        if idx % 500 == 0:
            print(f"  Processed {idx}/{len(crate_df)}...")
        
        filename = crate_row['filename']
        parsed_artist, parsed_track, parse_confidence = parse_filename(filename)
        
        best_match = None
        best_score = 0
        
        # Try to match against Essential Mix tracks
        for _, em_row in essential_df.iterrows():
            em_track = str(em_row.get('Track Name', ''))
            em_artist = str(em_row.get('Artist Name', ''))
            
            # Calculate match scores
            track_score = fuzzy_match_score(parsed_track, em_track)
            
            # If we have artist info, factor that in
            if parsed_artist:
                artist_score = fuzzy_match_score(parsed_artist, em_artist)
                combined_score = (track_score * 0.7) + (artist_score * 0.3)
            else:
                combined_score = track_score
            
            if combined_score > best_score:
                best_score = combined_score
                best_match = em_row
        
        # Build result row
        result = {
            'filename': filename,
            'parsed_artist': parsed_artist,
            'parsed_track': parsed_track,
            'parse_confidence': parse_confidence,
            'match_score': best_score,
            'match_confidence': 'high' if best_score >= 0.85 else 'medium' if best_score >= threshold else 'low',
            **crate_row.to_dict()
        }
        
        # Add Essential Mix data if match found
        if best_match is not None and best_score >= threshold:
            result.update({
                'matched_track': best_match.get('Track Name'),
                'matched_artist': best_match.get('Artist Name'),
                'matched_isrc': best_match.get('ISRC'),
                'matched_spotify_id': best_match.get('Spotify Track ID'),
                'matched_bpm': best_match.get('BPM'),
                'matched_genre': best_match.get('Genre'),
            })
        else:
            result.update({
                'matched_track': None,
                'matched_artist': None,
                'matched_isrc': None,
                'matched_spotify_id': None,
                'matched_bpm': None,
                'matched_genre': None,
            })
        
        results.append(result)
    
    result_df = pd.DataFrame(results)
    
    # Stats
    high_conf = (result_df['match_confidence'] == 'high').sum()
    med_conf = (result_df['match_confidence'] == 'medium').sum()
    low_conf = (result_df['match_confidence'] == 'low').sum()
    
    print(f"\n=== Matching Results ===")
    print(f"High confidence matches: {high_conf} ({high_conf/len(result_df)*100:.1f}%)")
    print(f"Medium confidence matches: {med_conf} ({med_conf/len(result_df)*100:.1f}%)")
    print(f"Low/no matches: {low_conf} ({low_conf/len(result_df)*100:.1f}%)")
    
    return result_df


# === USAGE ===
if __name__ == "__main__":
    # Load restructured crate tags
    crate_df = pd.read_csv('crate_tags_structured.csv')
    
    # Load Essential Mix data
    essential_df = pd.read_csv('essential_mix_final_enriched.csv')
    
    # Attempt matching
    matched_df = match_to_essential_mix(crate_df, essential_df, threshold=0.7)
    
    # Save results
    matched_df.to_csv('crate_tags_matched.csv', index=False)
    print(f"\n✓ Saved matched data to crate_tags_matched.csv")
    
    # Save low-confidence matches separately for manual review
    low_conf = matched_df[matched_df['match_confidence'] == 'low']
    low_conf.to_csv('crate_tags_unmatched.csv', index=False)
    print(f"✓ Saved {len(low_conf)} unmatched tracks to crate_tags_unmatched.csv for manual review")
    

    print("\nDone!")
