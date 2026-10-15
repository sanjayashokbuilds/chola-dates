"""Smoke test: the demo app runs, a real inscription can be loaded and solved, every tab renders."""

from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parents[1] / "streamlit_app.py")


def test_app_runs_end_to_end():
    at = AppTest.from_file(APP, default_timeout=300).run()
    assert not at.exception

    at.selectbox(key="preset").set_value(
        next(o for o in at.selectbox(key="preset").options if o.startswith("No. 60 "))).run()
    assert at.session_state["paksha"] == "shukla" and at.session_state["nak"] == "Pushya"
    assert any("**0** exact matches" in m.value for m in at.markdown)   # impossible as carved

    at.radio[2].set_value("Must be current at sunrise (Kielhorn's practice)").run()
    assert not at.exception and at.warning
