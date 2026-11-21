from src.retrieval import LocalCatalog, distance


def song(id, artist, energy, valence, acousticness, tempo=100.0, instrumentalness=0.0):
    return {"id": id, "title": f"Song {id}", "artist": artist, "energy": energy, "valence": valence,
            "acousticness": acousticness, "tempo_bpm": tempo, "instrumentalness": instrumentalness}


INTENT = {"target": {"energy": 0.2, "valence": 0.3, "acousticness": 0.7}, "prefer": []}


def test_closest_song_comes_first():
    catalog = LocalCatalog(songs=[song(1, "A", 0.9, 0.9, 0.1), song(2, "B", 0.2, 0.3, 0.7)])
    assert [s["id"] for s, _ in catalog.search(INTENT, k=2)] == [2, 1]


def test_at_most_one_song_per_artist():
    catalog = LocalCatalog(songs=[song(1, "A", 0.2, 0.3, 0.7), song(2, "A", 0.21, 0.3, 0.7), song(3, "B", 0.5, 0.5, 0.5)])
    assert [s["id"] for s, _ in catalog.search(INTENT, k=3)] == [1, 3]


def test_preferred_range_penalty_reorders():
    fast = song(1, "A", 0.2, 0.3, 0.7, tempo=150)
    slow = song(2, "B", 0.25, 0.3, 0.7, tempo=70)
    intent = dict(INTENT, prefer=[("tempo_bpm", 60.0, 80.0)])
    assert distance(fast, intent) > distance(slow, intent)
    assert LocalCatalog(songs=[fast, slow]).search(intent, k=1)[0][0]["id"] == 2


def test_missing_instrumentalness_defaults_to_zero():
    catalog = LocalCatalog(songs=[{**song(1, "A", 0.2, 0.3, 0.7), "instrumentalness": ""}])
    assert catalog.songs[0]["instrumentalness"] == 0.0


def test_real_catalog_returns_eight_distinct_artists():
    results = LocalCatalog().search(INTENT)
    assert len(results) == 8
    assert len({s["artist"] for s, _ in results}) == 8
    assert [d for _, d in results] == sorted(d for _, d in results)
