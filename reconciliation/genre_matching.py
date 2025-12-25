import pandas as pd
import os

# Mapping: playlist CSV filename to its genre label
genre_csvs = {
    'best_of_proghouse.csv': 'Progressive House',
    'best_of_melodic_house.csv': 'Melodic House',
    'best_of_melodic_techno.csv': 'Melodic Techno',
    'best_of_organic_house.csv': 'Organic House',
    'best_of_deep_house.csv': 'Deep House',
    'best_of_house.csv': 'House',
    'best_of_disco.csv': 'Disco',
    'best_of_tech_house.csv': 'Tech House',
    'best_of_techno.csv': 'Techno',
    'best_of_hard_techno.csv': 'Hard Techno',
    'best_of_trance.csv': 'Trance',
    'best_of_edm_dubstep.csv': 'EDM/Dubstep',
    'best_of_indie_dance.csv': 'Indie Dance',
    'best_of_other.csv': 'Other'
}
acid_csv = 'best_of_acid.csv'  # Separate file for 'acid-tinged' tag

def tag_by_genre_with_acid(master_csv, genre_csvs, acid_csv):
    master_df = pd.read_csv(master_csv)
    track_to_genre = {}

    # Step 1: Tag by genre playlists
    for genre_csv, genre_name in genre_csvs.items():
        genre_df = pd.read_csv(genre_csv)
        for _, row in genre_df.iterrows():
            track_name = str(row.get('Track Name') or row.get('name', '')).strip().lower()
            isrc = str(row.get('ISRC') or row.get('isrc', '')).strip().upper()
            for id_key in [track_name, isrc]:
                if id_key:
                    track_to_genre.setdefault(id_key, set()).add(genre_name)

    # Step 2: Add 'acid-tinged' tag from acid playlist
    acid_df = pd.read_csv(acid_csv)
    for _, row in acid_df.iterrows():
        track_name = str(row.get('Track Name') or row.get('name', '')).strip().lower()
        isrc = str(row.get('ISRC') or row.get('isrc', '')).strip().upper()
        for id_key in [track_name, isrc]:
            if id_key:
                track_to_genre.setdefault(id_key, set()).add('acid-tinged')

    # Step 3: Assign genre/multi-genre for each track in master file
    genres_out = []
    for _, row in master_df.iterrows():
        name = str(row.get('Track Name') or row.get('name', '')).strip().lower()
        isrc = str(row.get('ISRC') or row.get('isrc', '')).strip().upper()
        found_genres = set()
        for id_key in [name, isrc]:
            if id_key and id_key in track_to_genre:
                found_genres.update(track_to_genre[id_key])
        genres_out.append(', '.join(sorted(found_genres)) if found_genres else '')
    master_df['Genre'] = genres_out

    # Step 4: Save the tagged file
    out_filename = os.path.splitext(master_csv)[0] + '_genre_tagged.csv'
    master_df.to_csv(out_filename, index=False)
    return out_filename

# Example usage:
result = tag_by_genre_with_acid('essential_mix_clean_final.csv', genre_csvs, acid_csv)
print(f"Output written to {result}")
