import pandas as pd

# Load your Essential Mix data
ess = pd.read_csv('essential_mix_final_enriched.csv')  # or 'essential_mix_enriched.csv'

# Load the new 1M dataset
new_data = pd.read_csv('filtered_spotify_tracks.csv')

# Filter by your genres first (optional, speeds things up)
genre_filter = 'progressive|melodic|techno|house|trance|electronica|indie dance|breakbeat'
filtered = new_data[new_data['genre'].str.contains(genre_filter, case=False, na=False)]

# Merge using Spotify Track ID
merged = ess.merge(filtered, left_on='Spotify Track ID', right_on='track_id', how='left')

# Save the result
merged.to_csv('essential_mix_ultimate_enriched.csv', index=False)

print(f"Merge complete! {len(merged)} rows in output.")
