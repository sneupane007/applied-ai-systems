"""One-time build of data/catalog.csv from the Hugging Face Spotify Tracks Dataset.

Usage (from the project root):
    python scripts/build_catalog.py                 # downloads dataset.csv (~20 MB)
    python scripts/build_catalog.py path/to/dataset.csv

The output uses the same columns as data/songs.csv plus `instrumentalness`,
so src/recommender.load_songs() can read it. See data/CATALOG_SOURCE.md.
"""
import sys

import pandas as pd

SOURCE_URL = "https://huggingface.co/datasets/maharshipandya/spotify-tracks-dataset/resolve/main/dataset.csv"
OUT_PATH = "data/catalog.csv"
SEED = 42
MIN_POPULARITY = 50
PER_QUADRANT = 38  # 4 quadrants x 38 = 152 songs
MAX_PER_ARTIST = 2
GENRES = [
    "pop", "rock", "hip-hop", "jazz", "classical", "acoustic", "edm", "ambient",
    "blues", "country", "r-n-b", "metal", "indie", "folk", "piano", "soul", "latin", "chill",
]


def mood_for(valence: float, energy: float) -> str:
    """Name the valence/energy quadrant a song sits in."""
    if valence >= 0.5:
        return "happy" if energy >= 0.5 else "chill"
    return "intense" if energy >= 0.5 else "sad"


def main() -> None:
    source = sys.argv[1] if len(sys.argv) > 1 else SOURCE_URL
    print(f"Reading {source} ...")
    df = pd.read_csv(source)
    print(f"Rows in source: {len(df)}")

    missing = [g for g in GENRES if g not in set(df["track_genre"])]
    if missing:
        print(f"Warning: genres not in source, skipped: {missing}")

    df = df[df["track_genre"].isin(GENRES)]
    df = df[(df["popularity"] >= MIN_POPULARITY) & (df["tempo"] > 0)]
    df = df.dropna(subset=["track_name", "artists"])
    df = df.drop_duplicates(subset="track_id").drop_duplicates(subset=["track_name", "artists"])
    df = df.sample(frac=1, random_state=SEED)
    df = df.groupby("artists").head(MAX_PER_ARTIST)
    df["mood"] = [mood_for(v, e) for v, e in zip(df["valence"], df["energy"])]

    picked = []
    for mood in ("happy", "chill", "sad", "intense"):
        quadrant = df[df["mood"] == mood].copy()
        # Interleave genres so no single genre fills a quadrant.
        quadrant["genre_rank"] = quadrant.groupby("track_genre").cumcount()
        quadrant = quadrant.sort_values("genre_rank", kind="stable").head(PER_QUADRANT)
        if len(quadrant) < PER_QUADRANT:
            print(f"Warning: only {len(quadrant)} songs available for '{mood}'")
        picked.append(quadrant)

    catalog = pd.concat(picked).reset_index(drop=True)
    out = pd.DataFrame({
        "id": range(1, len(catalog) + 1),
        "title": catalog["track_name"],
        "artist": catalog["artists"].str.replace(";", ", "),
        "genre": catalog["track_genre"],
        "mood": catalog["mood"],
        "energy": catalog["energy"].round(3),
        "tempo_bpm": catalog["tempo"].round(1),
        "valence": catalog["valence"].round(3),
        "danceability": catalog["danceability"].round(3),
        "acousticness": catalog["acousticness"].round(3),
        "instrumentalness": catalog["instrumentalness"].round(3),
        "track_id": catalog["track_id"],
    })
    out.to_csv(OUT_PATH, index=False)

    print(f"\nWrote {len(out)} songs to {OUT_PATH}")
    print("\nSongs per quadrant:")
    print(out["mood"].value_counts().to_string())
    print("\nSongs per genre:")
    print(out["genre"].value_counts().to_string())
    print(f"\nInstrumental songs (instrumentalness >= 0.5): {(out['instrumentalness'] >= 0.5).sum()}")
    print(f"Tempo range: {out['tempo_bpm'].min()} - {out['tempo_bpm'].max()} bpm")


if __name__ == "__main__":
    main()
