"""Runs the Streamlit page headlessly (no browser, no network: offline mode, manual weather)."""
import pytest
from streamlit.testing.v1 import AppTest


@pytest.fixture
def app(monkeypatch):
    monkeypatch.setattr("src.vibe.default_reasoner", lambda: None)  # offline, even if a .env key exists
    monkeypatch.setattr("src.vibe.default_parser", lambda: None)    # prompts read by keywords, never sent
    at = AppTest.from_file("../app.py", default_timeout=30)
    at.run()
    return at


def test_find_button_waits_for_some_input(app):
    assert app.button(key="go").disabled
    app.text_area(key="prompt").set_value("something cozy").run()
    assert not app.button(key="go").disabled


def test_rainy_night_shows_five_offline_picks(app):
    app.button(key="card_rainy_window").click().run()
    app.select_slider(key="energy").set_value("Low")
    app.selectbox(key="weather").set_value("rainy")
    app.selectbox(key="time").set_value("night")
    app.button(key="go").click().run()
    assert not app.exception
    markdown = " ".join(m.value for m in app.markdown)
    assert "Target sound:** energy 0.07" in markdown or "Target sound:** energy 0.08" in markdown
    assert sum(1 for m in app.markdown if m.value.startswith("**") and ". " in m.value[:6]) == 5
    assert any("Offline mode" in i.value for i in app.info)
    captions = " ".join(c.value for c in app.caption)
    assert "M-05" in captions and "M-09" in captions


def test_crisis_note_shows_support_message(app):
    app.button(key="card_foggy_morning").click().run()
    app.selectbox(key="weather").set_value("cloudy")
    app.text_area(key="prompt").set_value("i want to die")
    app.button(key="go").click().run()
    assert any("988" in w.value for w in app.warning)


def test_prompt_and_history_show_how_they_were_used(app):
    app.text_area(key="prompt").set_value("need to focus, no lyrics")
    app.selectbox(key="persona").set_value("student")
    app.selectbox(key="weather").set_value("rainy")
    app.selectbox(key="time").set_value("afternoon").run()
    app.button(key="go").click().run()
    assert not app.exception
    markdown = " ".join(m.value for m in app.markdown)
    assert "How I read your prompt** (keywords): goal: help me focus · no lyrics" in markdown
    assert "From your history:**" in markdown and "similar past plays" in markdown
    assert sum(1 for m in app.markdown if m.value.startswith("**") and ". " in m.value[:6]) == 5
    assert markdown.count("](https://open.spotify.com/track/") == 5
