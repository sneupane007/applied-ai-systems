"""VibeMatch: songs for the moment you're in.

Run from the project root:  streamlit run app.py
"""
import re
from datetime import datetime

import streamlit as st

from src import weather as weather_api
from src.context import ENERGY_LEVELS, GOALS, MOOD_CARDS, NOTE_MAX, PLACES, WEATHER, Moment
from src.history import PERSONAS, load_history, plays_for
from src.manual import load_manual
from src.retrieval import LocalCatalog
from src.vibe import default_parser, default_reasoner, logger, recommend_for_moment, setup_logging

TIME_CHOICES = {"now": "Now", "morning": "Morning", "afternoon": "Afternoon", "evening": "Evening", "night": "Night"}
TIME_HOURS = {"morning": 8, "afternoon": 14, "evening": 19, "night": 23}
AUTO = "auto"
LABEL_TEXT = {
    "low_mood": "low mood", "tense_mood": "tense mood", "hr_high_resting": "heart rate up (at rest)",
    "hr_active": "heart rate up (working out)", "notifications_many": "lots of notifications",
    "sleep_short": "short sleep", "work_study": "work / study", "clear": "clear sky",
    "avoid_sad": "nothing too sad", "no_lyrics": "no lyrics",
}
FIELD_TEXT = {"mood_card": "mood", "energy_level": "energy", "goal": "goal", "place": "place", "weather": "weather"}
SPOTIFY_ID = re.compile(r"[A-Za-z0-9]{22}")

st.set_page_config(page_title="VibeMatch", page_icon="🎧")
setup_logging()


@st.cache_resource
def catalog():
    return LocalCatalog()


@st.cache_resource
def manual():
    return load_manual()


@st.cache_resource
def reasoner():
    return default_reasoner()


@st.cache_resource
def parser():
    return default_parser()


@st.cache_resource
def history():
    return load_history()


@st.cache_data(ttl=600, show_spinner=False)
def conditions_for(city: str):
    return weather_api.get_conditions(city)


def label_text(label: str) -> str:
    if label.startswith("goal_"):
        return "goal: " + GOALS[label[5:]].lower()
    return LABEL_TEXT.get(label, label)


def spotify_id(song):
    """The song's Spotify track ID, if it has a well-formed one."""
    track_id = song.get("track_id") or ""
    return track_id if SPOTIFY_ID.fullmatch(track_id) else None


st.title("🎧 VibeMatch")
st.caption("Songs for the moment you're in. Say what you want to hear, and VibeMatch finds real songs that fit "
           "your moment and your listening history.")
if reasoner() is None:
    st.info("Offline mode: no `ANTHROPIC_API_KEY` found, so keywords read your prompt and the reasons come "
            "from templates. See the README to add a key.", icon="🔌")

# --- Inputs ---------------------------------------------------------------
prompt = st.text_area("What do you want to hear?", max_chars=NOTE_MAX, height=80, key="prompt",
                      placeholder="e.g. rainy night, need to focus, no lyrics · pump me up for the gym, no country")

persona = st.selectbox("Listening history", ["none", *PERSONAS], key="persona",
                       format_func=lambda p: "None" if p == "none" else f"{PERSONAS[p]} (demo)")
plays = plays_for(history(), persona) if persona != "none" else []
if plays:
    songs_by_id = {s["id"]: s for s in catalog().songs}
    st.caption(f"{len(plays)} made-up plays from {plays[0].played_at:%b %d} to {plays[-1].played_at:%b %d}. "
               "Your history stays on this device: the AI only sees a one-line summary.")
    with st.expander("Recent plays"):
        st.dataframe(
            [{"when": f"{p.played_at:%a %b %d %H:%M}", "weather": p.weather, "place": PLACES[p.place],
              "song": songs_by_id[p.song_id]["title"], "artist": songs_by_id[p.song_id]["artist"],
              "finished": "yes" if p.completed else "skipped"} for p in reversed(plays[-15:])],
            hide_index=True, width="stretch",
        )

city_col, weather_col, time_col = st.columns([2, 1, 1])
city = city_col.text_input("City (optional, only used to look up the weather)", max_chars=weather_api.CITY_MAX)
weather_choice = weather_col.selectbox("Weather", [AUTO, *WEATHER],
                                       format_func=lambda w: "Auto (from city)" if w == AUTO else w.capitalize(), key="weather")
time_choice = time_col.selectbox("Time of day", list(TIME_CHOICES), format_func=TIME_CHOICES.get, key="time")

if "mood_card" not in st.session_state:
    st.session_state.mood_card = None
with st.expander("🎛️ Fine-tune (optional): anything you set here wins over the prompt"):
    st.caption("Mood picture (click again to clear)")
    cards = list(MOOD_CARDS.items())
    for row in (cards[:4], cards[4:]):
        for column, (key, card) in zip(st.columns(4), row):
            selected = st.session_state.mood_card == key
            if column.button(f"{card['emoji']} {card['label']}", key=f"card_{key}", width="stretch",
                             type="primary" if selected else "secondary"):
                st.session_state.mood_card = None if selected else key
                st.rerun()
    energy_level = st.select_slider("How much energy do you have?", options=["Auto", *ENERGY_LEVELS],
                                    value="Auto", key="energy")
    goal = st.radio("What do you want from the music?", [AUTO, *GOALS], horizontal=True, key="goal",
                    format_func=lambda g: "Auto" if g == AUTO else GOALS[g])
    place = st.radio("Where are you?", [AUTO, *PLACES], horizontal=True, key="place",
                     format_func=lambda p: "Auto" if p == AUTO else PLACES[p])

with st.expander("📱 Simulated phone signals"):
    st.caption("In a real app these would come from your phone or watch. Here you set them by hand. "
               "Either way they become coarse labels like \"heart rate up\" before anything leaves your device.")
    use_phone = st.toggle("Use simulated phone signals", key="use_phone")
    heart_rate = st.slider("Heart rate (bpm)", 50, 180, 72, disabled=not use_phone, key="heart_rate")
    notifications = st.slider("Unread notifications", 0, 50, 3, disabled=not use_phone)
    sleep_hours = st.slider("Sleep last night (hours)", 0.0, 12.0, 7.5, step=0.5, disabled=not use_phone)

show_players = st.toggle("Show Spotify players", key="players",
                         help="Loads Spotify's player for each pick in your browser, so Spotify sees which songs are shown.")
ready = bool(prompt.strip()) or st.session_state.mood_card is not None or persona != "none"
go = st.button("Find my songs", type="primary", disabled=not ready, key="go")
if not ready:
    st.caption("Type what you want to hear, pick a listening history, or choose a mood picture to start.")

# --- Run ------------------------------------------------------------------
if go:
    hour = datetime.now().hour if time_choice == "now" else TIME_HOURS[time_choice]
    weather = None
    if weather_choice != AUTO:
        weather = weather_choice
        logger.info("weather source=manual value=%s", weather)
    elif city.strip():
        with st.spinner("Checking the weather..."):
            conditions, reason = conditions_for(city.strip())
        if conditions:
            weather = conditions.weather
            if time_choice == "now":
                hour = conditions.hour
            logger.info("weather source=city ok=True value=%s", weather)
        else:
            st.warning(reason, icon="🌥️")
            logger.info("weather source=city ok=False reason=%s", reason)

    moment = Moment(
        hour=hour, mood_card=st.session_state.mood_card,
        energy_level=None if energy_level == "Auto" else energy_level,
        goal=None if goal == AUTO else goal, place=None if place == AUTO else place,
        weather=weather, note=prompt.strip(),
        heart_rate=heart_rate if use_phone else None,
        notifications=notifications if use_phone else None,
        sleep_hours=sleep_hours if use_phone else None,
    )
    try:
        with st.spinner("Finding songs..."):
            result = recommend_for_moment(moment, catalog=catalog(), reasoner=reasoner(), rules=manual(),
                                          history=plays or None, parser=parser())
    except ValueError as e:
        st.error(f"Couldn't use that input: {e}")
        st.stop()

    explanation = result.explanation
    st.divider()
    if result.support_message:
        st.warning(result.support_message, icon="💛")
    if explanation.mode == "ai":
        st.success("AI mode: Claude picked these from the 8 closest songs, following the manual.", icon="✨")
    else:
        st.info("Offline mode: the songs closest to your target sound, with template reasons.", icon="🔌")

    if result.prompt_mode != "none":
        read = result.intent.describe()
        how = "Claude" if result.prompt_mode == "ai" else "keywords"
        st.markdown(f"**How I read your prompt** ({how}): " + (" · ".join(read) if read else "nothing I could use"))
        overruled = [FIELD_TEXT[f] for f in FIELD_TEXT
                     if getattr(result.intent, f) and getattr(result.intent, f) != getattr(result.moment, f)]
        if overruled:
            st.caption("Your own settings won over the prompt for: " + ", ".join(overruled) + ".")
        for note in result.prompt_notes:
            st.caption(note)

    profile = result.history
    if profile:
        if not profile.centroid:
            st.markdown("**From your history:** no past plays like this moment, so history wasn't used.")
        elif result.moment.mood_card:
            st.markdown(f"**From your history:** {profile.summary()}. They pulled the starting point "
                        f"{profile.strength:.0%} of the way toward your usual sound.")
        else:
            st.markdown(f"**From your history:** {profile.summary()}. With no mood picture, "
                        "VibeMatch started from your usual sound here.")

    t = result.target
    st.markdown(f"**Target sound:** energy {t['energy']:.2f} · valence {t['valence']:.2f} · "
                f"acoustic {t['acousticness']:.2f}")
    st.caption("What VibeMatch noticed: " + " · ".join(label_text(label) for label in result.labels))
    if result.nudges:
        st.caption("How the manual moved the target: " + " · ".join(result.nudges))
    st.caption("Manual rules used: " + " · ".join(f"{r.id} {r.title}" for r in result.rules))

    if explanation.intro:
        st.markdown(f"_{explanation.intro}_")
    familiar = profile.familiar if profile else set()
    for number, pick in enumerate(explanation.picks, start=1):
        song = pick.song
        track_id = spotify_id(song)
        link = f" · [Open in Spotify](https://open.spotify.com/track/{track_id})" if track_id else ""
        st.markdown(f"**{number}. {song['title']}** · {song['artist']}{link}")
        st.caption(f"{song['genre']} · energy {song['energy']:.2f} · valence {song['valence']:.2f} · "
                   f"{song['tempo_bpm']:.0f} bpm" + (" · played before" if song["id"] in familiar else "")
                   + (f" · rules {', '.join(pick.rule_ids)}" if pick.rule_ids else ""))
        st.write(pick.reason)
        if show_players and track_id:
            st.iframe(f"https://open.spotify.com/embed/track/{track_id}", height=80)

    if explanation.notes:
        st.caption("What the check changed: " + " ".join(explanation.notes))

    with st.expander("How this was picked: the 8 closest songs"):
        st.dataframe(
            [{"title": s["title"], "artist": s["artist"], "genre": s["genre"], "energy": s["energy"],
              "valence": s["valence"], "acoustic": s["acousticness"], "tempo": s["tempo_bpm"],
              "instrumental": s["instrumentalness"], "played before": s["id"] in familiar, "distance": d}
             for s, d in result.candidates],
            hide_index=True, width="stretch",
        )
    with st.expander("The manual rules behind these picks"):
        for rule in result.rules:
            st.markdown(f"**{rule.id} · {rule.title}** ({rule.evidence})")
            st.caption(rule.why)
            st.caption(f"Sources: {rule.sources}")

st.caption("Not therapy or medical advice. Phone signals are simulated and listening histories are made-up demo data. "
           "Songs: Spotify Tracks Dataset (Hugging Face). Weather: Open-Meteo (CC-BY 4.0).")
