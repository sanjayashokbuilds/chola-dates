"""
Regression tests for the detective's headline results on Kulottunga III.
Slow-ish (~30 s): builds a 50-year calendar.
"""

import numpy as np
import pytest

from chola import astro, dataset, detective as dt, panchang as p


@pytest.fixture(scope="module")
def model():
    df = dataset.load("kulottunga3")
    a0, a1 = astro.day_number(1176, 1, 1), astro.day_number(1180, 12, 31)
    cal = p.build_calendar(a0 - 5, a1 + round(41 * dt.YEAR))
    acc_idx = np.arange(a0, a1 + 1) - cal["n"].iat[0]
    evs = [dt.evidence(cal, r) for _, r in df.iterrows()]
    post = dt.fit(cal, evs, acc_idx)
    return cal, evs, post, acc_idx


def test_votes_peak_matches_kielhorn_1906(model):
    cal, evs, post, acc_idx = model
    v = dt.votes(cal, evs, acc_idx)
    best = post.acc_n[v == v.max()]
    assert v.max() == 18
    assert best.min() == astro.day_number(1178, 7, 6)
    assert best.max() == astro.day_number(1178, 7, 8)


def test_posterior_50pct_inside_kielhorn_window(model):
    _, _, post, _ = model
    lo, hi = post.interval(0.5)
    assert lo >= astro.day_number(1178, 7, 6) and hi <= astro.day_number(1178, 7, 8)


def test_top_days_are_6_to_8_july(model):
    # 6, 7 and 8 July 1178 are tied; reporting one of them alone would be rounding noise.
    _, _, post, _ = model
    a, b, mass = post.top_days()
    assert (a, b) == (astro.day_number(1178, 7, 6), astro.day_number(1178, 7, 8))
    assert 0.7 < mass < 0.8


def test_flags_exactly_kielhorns_genuine_errors(model):
    cal, evs, post, acc_idx = model
    res = {ev.id: dt.explain(cal, ev, post, acc_idx) for ev in evs}
    flagged = {i for i, x in res.items() if x["p_miscarved"] > 0.5}
    assert flagged == {"K3-16", "K3-24", "K3-31", "K3-60", "K3-90", "K3-111"}
    # and diagnoses the same error Kielhorn did
    assert res["K3-60"]["dates"][0] == {"date": "1192-01-02", "prob": pytest.approx(res["K3-60"]["dates"][0]["prob"]), "wrong": "paksha"}
    assert res["K3-111"]["dates"][0]["wrong"] == "nakshatra"
    assert res["K3-16"]["dates"][0]["wrong"] == "solar_day, regnal_year"
