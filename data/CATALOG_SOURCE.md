# Where `catalog.csv` comes from

**Source:** [Spotify Tracks Dataset](https://huggingface.co/datasets/maharshipandya/spotify-tracks-dataset) on Hugging Face (`dataset.csv`, 114,000 rows, 125 genres). Its README says the data "was collected and cleaned using Spotify's Web API and Python."

**License:** the dataset card lists `license: bsd` without saying which BSD version, and there is no license file.

**Caveat:** the audio features (energy, valence, acousticness, instrumentalness, …) came from Spotify's Web API, and Spotify no longer offers them to new apps. I don't know whether Spotify's developer terms allow sharing this data. This sample is included for a class project so the app runs without a download step. Don't use it commercially, and remove it if the source or Spotify asks.

## How it was built

`python scripts/build_catalog.py` (seed 42):

1. Keep 18 genres: pop, rock, hip-hop, jazz, classical, acoustic, edm, ambient, blues, country, r-n-b, metal, indie, folk, piano, soul, latin, chill.
2. Keep songs with popularity ≥ 50 and tempo > 0. Drop duplicate track IDs and duplicate title + artist pairs.
3. Shuffle, and keep at most 2 songs per artist.
4. Sort each song into a quadrant by valence and energy (0.5 cut-offs): **happy** (positive, energetic), **chill** (positive, calm), **sad** (negative, calm), **intense** (negative, energetic). This becomes the `mood` column.
5. Take 38 songs per quadrant, interleaving genres so no single genre fills a quadrant.

**Result:** 152 songs, 38 per quadrant, 7–10 per genre. 19 songs have instrumentalness ≥ 0.5. Tempo ranges from 51 to 200 bpm (17 songs at 60–80 bpm, 35 at 120–140 bpm).

## Columns

The columns match `data/songs.csv` (`id, title, artist, genre, mood, energy, tempo_bpm, valence, danceability, acousticness`), plus `instrumentalness`.

## Known limitations

- `valence`, `energy`, `instrumentalness`, and the other features are Spotify's model estimates, not ground truth.
- Genre labels come from the dataset and are sometimes odd. For example, *Runaway* by Bon Jovi is listed as "metal".
- Popularity ≥ 50 favors mainstream songs, and the sample is small, so many artists and styles are missing.
