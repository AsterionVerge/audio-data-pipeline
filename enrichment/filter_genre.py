import pandas as pd

# Load the dataset
df = pd.read_csv('spotify_data.csv')

# Check what the genre column is called
print(df.columns)

# Filter for specific genres (adjust column name as needed)
filtered = df[df['genre'].str.contains('progressive|melodic|techno|house|trance|electronica|indie dance|breakbeat', case=False, na=False)]

# Save the filtered subset
filtered.to_csv('filtered_spotify_tracks.csv', index=False)

print(f"Filtered down to {len(filtered)} tracks")
