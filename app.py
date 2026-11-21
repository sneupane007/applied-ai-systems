"""VibeMatch 2.0: songs for the moment you're in.

Run from the project root:  streamlit run app.py
"""
from datetime import datetime

import streamlit as st

from src import weather as weather_api
from src.context import ENERGY_LEVELS, GOALS, MOOD_CARDS, PLACES, WEATHER, Moment
from src.manual import load_manual
from src.retrieval import LocalCatalog
from src.vibe import default_reasoner, logger, recommend_for_moment, setup_logging

TIME_CHOICES = {"now": "Now", "morning": "Morning", "afternoon": "Afternoon", "evening": "Evening", "night": "Night"}
TIME_HOURS = {"morning": 8, "afternoon": 14, "evening": 19, "night": 23}
LABEL_TEXT = {
    "low_mood": "low mood", "tense_mood": "tense mood", "hr_high_resting": "heart rate up (at rest)",
    "hr_active": "heart rate up (working out)", "notifications_many": "lots of notifications",
    "sleep_short": "short sleep", "work_study": "work / study", "clear": "clear sky",
}

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


@st.cache_data(ttl=600, show_spinner=False)
def conditions_for(city: str):
    return weather_api.get_conditions(city)


def label_text(label: str) -> str:
    if label.startswith("goal_"):
        return "goal: " + GOALS[label[5:]].lower()
    return LABEL_TEXT.get(label, label)


st.title("🎧 VibeMatch")
st.caption("Songs for the moment you're in. Pick a mood, say where you are, and VibeMatch finds real songs that fit.")
if reasoner() is None:
    st.info("Offline mode: no `ANTHROPIC_API_KEY` found, so the reasons come from templates. "
            "See the README to add a key.", icon="🔌")

# --- Inputs ---------------------------------------------------------------
st.subheader("How do you feel right now?")
if "mood_card" not in st.session_state:
    st.session_state.mood_card = None
cards = list(MOOD_CARDS.items())
for row in (cards[:4], cards[4:]):
    for column, (key, card) in zip(st.columns(4), row):
        selected = st.session_state.mood_card == key
        if column.button(f"{card['emoji']} {card['label']}", key=f"card_{key}", width="stretch",
                         type="primary" if selected else "secondary"):
            st.session_state.mood_card = key
            st.rerun()

energy_level = st.select_slider("How much energy do you have?", options=list(ENERGY_LEVELS), value="Okay", key="energy")
goal = st.radio("What do you want from the music?", list(GOALS), format_func=GOALS.get, horizontal=True, key="goal")
place = st.radio("Where are you?", list(PLACES), format_func=PLACES.get, horizontal=True, key="place")

city_col, weather_col, time_col = st.columns([2, 1, 1])
city = city_col.text_input("City (optional, only used to look up the weather)", max_chars=weather_api.CITY_MAX)
weather_choice = weather_col.selectbox("Weather", ["auto", *WEATHER],
                                       format_func=lambda w: "Auto (from city)" if w == "auto" else w.capitalize(), key="weather")
time_choice = time_col.selectbox("Time of day", list(TIME_CHOICES), format_func=TIME_CHOICES.get, key="time")
note = st.text_input("Anything else? (optional)", max_chars=200,
                     placeholder="e.g. nothing too sad, something to study to", key="note")

with st.expander("📱 Simulated phone signals"):
    st.caption("In a real app these would come from your phone or watch. Here you set them by hand. "
               "Either way they become coarse labels like \"heart rate up\" before anything leaves your device.")
    use_phone = st.toggle("Use simulated phone signals", key="use_phone")
    heart_rate = st.slider("Heart rate (bpm)", 50, 180, 72, disabled=not use_phone, key="heart_rate")
    notifications = st.slider("Unread notifications", 0, 50, 3, disabled=not use_phone)
    sleep_hours = st.slider("Sleep last night (hours)", 0.0, 12.0, 7.5, step=0.5, disabled=not use_phone)

go = st.button("Find my songs", type="primary", disabled=st.session_state.mood_card is None, key="go")
if st.session_state.mood_card is None:
    st.caption("Pick a mood card to start.")

# --- Run ------------------------------------------------------------------
if go:
    hour = datetime.now().hour if time_choice == "now" else TIME_HOURS[time_choice]
    weather = None
    if weather_choice != "auto":
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
        mood_card=st.session_state.mood_card, energy_level=energy_level, goal=goal, place=place, hour=hour,
        weather=weather, note=note.strip(),
        heart_rate=heart_rate if use_phone else None,
        notifications=notifications if use_phone else None,
        sleep_hours=sleep_hours if use_phone else None,
    )
    try:
        with st.spinner("Finding songs..."):
            result = recommend_for_moment(moment, catalog=catalog(), reasoner=reasoner(), rules=manual())
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

    t = result.target
    st.markdown(f"**Target sound:** energy {t['energy']:.2f} · valence {t['valence']:.2f} · "
                f"acoustic {t['acousticness']:.2f}")
    st.caption("What VibeMatch noticed: " + " · ".join(label_text(label) for label in result.labels))
    if result.nudges:
        st.caption("How the manual moved the target: " + " · ".join(result.nudges))
    st.caption("Manual rules used: " + " · ".join(f"{r.id} {r.title}" for r in result.rules))

    if explanation.intro:
        st.markdown(f"_{explanation.intro}_")
    for number, pick in enumerate(explanation.picks, start=1):
        song = pick.song
        st.markdown(f"**{number}. {song['title']}** · {song['artist']}")
        st.caption(f"{song['genre']} · energy {song['energy']:.2f} · valence {song['valence']:.2f} · "
                   f"{song['tempo_bpm']:.0f} bpm" + (f" · rules {', '.join(pick.rule_ids)}" if pick.rule_ids else ""))
        st.write(pick.reason)

    if explanation.notes:
        st.caption("What the check changed: " + " ".join(explanation.notes))

    with st.expander("How this was picked: the 8 closest songs"):
        st.dataframe(
            [{"title": s["title"], "artist": s["artist"], "genre": s["genre"], "energy": s["energy"],
              "valence": s["valence"], "acoustic": s["acousticness"], "tempo": s["tempo_bpm"],
              "instrumental": s["instrumentalness"], "distance": d} for s, d in result.candidates],
            hide_index=True, width="stretch",
        )
    with st.expander("The manual rules behind these picks"):
        for rule in result.rules:
            st.markdown(f"**{rule.id} · {rule.title}** ({rule.evidence})")
            st.caption(rule.why)
            st.caption(f"Sources: {rule.sources}")

st.caption("Not therapy or medical advice. Phone signals are simulated. "
           "Songs: Spotify Tracks Dataset (Hugging Face). Weather: Open-Meteo (CC-BY 4.0).")
