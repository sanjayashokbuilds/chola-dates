"""Smoke test: the demo app runs, the story steps through, an inscription solves, every tab renders."""

from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parents[1] / "streamlit_app.py")


def _text(at):
    return " ".join(m.value for m in at.markdown)


def test_app_runs_end_to_end():
    at = AppTest.from_file(APP, default_timeout=300).run()
    assert not at.exception

    # The story: step through all six steps without errors
    for _ in range(5):
        at.button[1].click().run()
        assert not at.exception
    assert "What's new" in _text(at)

    # Try it: No. 60 is loaded by default and is impossible as carved
    assert at.session_state["paksha"] == "shukla" and at.session_state["nak"] == "Pushya"
    assert "No day fits every clue" in _text(at)

    # A correctly carved inscription gives exactly one day
    opt = next(o for o in at.selectbox(key="preset").options if o.startswith("No. 17 "))
    at.selectbox(key="preset").set_value(opt).run()
    assert not at.exception
    assert "Exactly one day fits every clue" in _text(at)
    assert "Tuesday 12 Nov 1196" in _text(at)
