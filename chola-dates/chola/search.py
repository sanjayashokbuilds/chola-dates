"""
The solver: given an inscription's clues and a date range, return the matching days.

Clues are a dict; any clue may be left out:
    {"solar_month": "Makara", "solar_day": 8, "paksha": "krishna", "tithi": 1,
     "nakshatra": "Pushya", "weekday": "Thursday"}

Two strictness modes:
    "sunrise"  the tithi / nakshatra must be the one in force at sunrise
    "day"      it may be any tithi / nakshatra current at some point during the day
               (Kielhorn accepts such cases, so this is the default)

`max_mismatches` returns near-misses too: days matching every clue but one (or two).
That is the raw material for the detective: a carving with one wrong detail.
"""

import pandas as pd

from . import astro, panchang as p


def _parse(clues: dict) -> dict:
    """Turn names into the numbers used in the calendar table."""
    out = {}
    if clues.get("solar_month"):
        out["solar_month"] = p.sign_index(clues["solar_month"])
    if clues.get("solar_day"):
        out["solar_day"] = int(clues["solar_day"])
    if clues.get("tithi"):
        t = int(clues["tithi"])
        if clues.get("paksha"):
            out["tithi"] = {p.tithi_number(clues["paksha"], t)}
        else:  # fortnight not stated: either half of the month
            out["tithi"] = {t, 15 + t}
    if clues.get("nakshatra"):
        out["nakshatra"] = p.nakshatra_index(clues["nakshatra"])
    if clues.get("weekday"):
        out["weekday"] = p.weekday_index(clues["weekday"])
    return out


# Kielhorn's solar-day numbers come from the traditional Surya-siddhanta sun,
# whose sankranti times differ from ours by a few hours, sign-dependently.
# Against his 20 published solar-day numbers: 15 match exactly, all 20 within
# one day (tests/test_solver.py). So a stated solar day is accepted +/- 1.
SOLAR_DAY_TOLERANCE = 1


def check_clues(cal: pd.DataFrame, clues: dict, mode: str = "day",
                month_rule: str = "set", solar_day_tolerance: int = SOLAR_DAY_TOLERANCE) -> pd.DataFrame:
    """
    For every day in the calendar table, whether each clue holds (True/False).
    Returns one boolean column per clue given, plus `n_mismatch`.
    """
    c = _parse(clues)
    res = pd.DataFrame({"n": cal["n"], "date": cal["date"]})
    if "solar_month" in c:
        res["solar_month"] = cal[f"sign_{month_rule}"] == c["solar_month"]
    if "solar_day" in c:
        res["solar_day"] = (cal[f"sday_{month_rule}"] - c["solar_day"]).abs() <= solar_day_tolerance
    if "tithi" in c:
        if mode == "sunrise":
            res["tithi"] = cal["tithi"].isin(c["tithi"])
        else:
            res["tithi"] = cal["tithis"].apply(lambda ts: bool(c["tithi"] & set(ts)))
    if "nakshatra" in c:
        if mode == "sunrise":
            res["nakshatra"] = cal["nakshatra"] == c["nakshatra"]
        else:
            res["nakshatra"] = cal["nakshatras"].apply(lambda ns: c["nakshatra"] in ns)
    if "weekday" in c:
        res["weekday"] = cal["weekday"] == c["weekday"]
    clue_cols = [k for k in c]
    res["n_mismatch"] = (~res[clue_cols]).sum(axis=1)
    return res


def find_matches(cal: pd.DataFrame, clues: dict, mode: str = "day",
                 month_rule: str = "set", max_mismatches: int = 0) -> pd.DataFrame:
    """Days where at most `max_mismatches` clues fail, best matches first."""
    res = check_clues(cal, clues, mode, month_rule)
    hits = res[res["n_mismatch"] <= max_mismatches].copy()
    clue_cols = [k for k in res.columns if k not in ("n", "date", "n_mismatch")]
    hits["failed"] = hits[clue_cols].apply(
        lambda row: ", ".join(k for k in clue_cols if not row[k]), axis=1)
    return hits[["n", "date", "n_mismatch", "failed"]].sort_values(["n_mismatch", "n"]).reset_index(drop=True)


def search(clues: dict, start: tuple, end: tuple, calendar: str = "julian", **kw) -> pd.DataFrame:
    """Convenience: build the calendar for start..end (y, m, d) and find matches."""
    n0 = astro.day_number(*start, calendar)
    n1 = astro.day_number(*end, calendar)
    cal = p.build_calendar(n0, n1)
    return find_matches(cal, clues, **kw)
