"""
The calendar elements of a day: weekday, solar month and day, tithi, paksha, nakshatra.

An Indian day runs from sunrise to the next sunrise. For each day we record
  - the element in force AT SUNRISE (the standard rule), and
  - every element that is current at some point DURING the day,
because inscriptions sometimes name a tithi or nakshatra that began after sunrise.
Keeping both lets the search be strict or lenient, and lets us report which one
an inscription used.
"""

import math
import pandas as pd

from . import astro

# ------------------------------------------------------------------ names

SIGNS = ["Mesha", "Vrishabha", "Mithuna", "Karka", "Simha", "Kanya",
         "Tula", "Vrischika", "Dhanu", "Makara", "Kumbha", "Mina"]

TAMIL_MONTHS = ["Chittirai", "Vaikasi", "Ani", "Adi", "Avani", "Purattasi",
                "Aippasi", "Karttigai", "Margazhi", "Tai", "Masi", "Panguni"]

NAKSHATRAS = ["Ashvini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
              "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni",
              "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha",
              "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana",
              "Dhanishtha", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada",
              "Revati"]

TITHI_NAMES = ["Pratipada", "Dvitiya", "Tritiya", "Chaturthi", "Panchami",
               "Shashthi", "Saptami", "Ashtami", "Navami", "Dashami", "Ekadashi",
               "Dvadashi", "Trayodashi", "Chaturdashi"]  # 15th = Purnima / Amavasya

WEEKDAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]

# Spellings found in inscriptions and translations -> canonical names.
_SIGN_ALIASES = {
    "rishabha": "Vrishabha", "vrisha": "Vrishabha", "karkataka": "Karka", "kataka": "Karka",
    "simgha": "Simha", "simha": "Simha", "kanni": "Kanya", "kanni": "Kanya",
    "vrischika": "Vrischika", "vrishchika": "Vrischika", "dhanus": "Dhanu",
    "magara": "Makara", "makara": "Makara", "kumbha": "Kumbha", "mina": "Mina", "meena": "Mina",
}
_NAK_ALIASES = {
    "asvini": "Ashvini", "aswini": "Ashvini", "krittika": "Krittika", "kirttigai": "Krittika",
    "mrigasiras": "Mrigashira", "mrigasira": "Mrigashira", "ardra": "Ardra", "tiruvadirai": "Ardra",
    "pusa": "Pushya", "pusam": "Pushya", "pushya": "Pushya", "tishya": "Pushya",
    "aslesha": "Ashlesha", "ayilyam": "Ashlesha", "makha": "Magha",
    "purva-phalguni": "Purva Phalguni", "uttara": "Uttara Phalguni",
    "uttara-phalguni": "Uttara Phalguni", "uttiram": "Uttara Phalguni",
    "hasta": "Hasta", "attam": "Hasta", "chitra": "Chitra", "svati": "Swati",
    "visakha": "Vishakha", "anuradha": "Anuradha", "jyeshtha": "Jyeshtha", "kettai": "Jyeshtha",
    "mula": "Mula", "purva-ashadha": "Purva Ashadha", "uttara-ashadha": "Uttara Ashadha",
    "sravana": "Shravana", "tiruvonam": "Shravana", "dhanishtha": "Dhanishtha", "sravishtha": "Dhanishtha",
    "satabhishaj": "Shatabhisha", "purva-bhadrapada": "Purva Bhadrapada",
    "uttara-bhadrapada": "Uttara Bhadrapada", "revati": "Revati",
}


def _norm(s: str) -> str:
    return s.strip().lower().replace(" ", "-").replace("ā", "a").replace("ī", "i")


def sign_index(name: str) -> int:
    """'Makara' or 'Magara' or 'Tai' -> 9"""
    key = _norm(name)
    for i, s in enumerate(SIGNS):
        if key == s.lower():
            return i
    for i, s in enumerate(TAMIL_MONTHS):
        if key == s.lower():
            return i
    if key in _SIGN_ALIASES:
        return SIGNS.index(_SIGN_ALIASES[key])
    raise ValueError(f"Unknown solar month: {name}")


def nakshatra_index(name: str) -> int:
    """'Pushya' or 'Pusa' -> 8 (1-based, Ashvini = 1)"""
    key = _norm(name)
    for i, s in enumerate(NAKSHATRAS):
        if key == _norm(s):
            return i + 1
    if key in _NAK_ALIASES:
        return NAKSHATRAS.index(_NAK_ALIASES[key]) + 1
    raise ValueError(f"Unknown nakshatra: {name}")


def weekday_index(name: str) -> int:
    key = _norm(name)[:3]
    for i, w in enumerate(WEEKDAYS):
        if w.lower().startswith(key):
            return i
    raise ValueError(f"Unknown weekday: {name}")


def tithi_number(paksha: str, tithi: int) -> int:
    """('shukla', 1) -> 1 ... ('shukla', 15) -> 15, ('krishna', 1) -> 16 ... ('krishna', 15) -> 30"""
    p = paksha.strip().lower()
    if p in ("shukla", "sukla", "bright", "purva", "first"):
        return tithi
    if p in ("krishna", "krsna", "dark", "apara", "second"):
        return 15 + tithi
    raise ValueError(f"Unknown paksha: {paksha}")


def tithi_label(t: int) -> str:
    paksha = "Shukla" if t <= 15 else "Krishna"
    k = t if t <= 15 else t - 15
    name = TITHI_NAMES[k - 1] if k < 15 else ("Purnima" if t == 15 else "Amavasya")
    return f"{paksha} {k} ({name})"


# --------------------------------------------- dividing the circle

TITHI_WIDTH = 12.0             # 30 tithis of 12 degrees of elongation
NAK_WIDTH = 360.0 / 27.0       # 27 equal nakshatras of 13 deg 20 min

# Nakshatra systems: start longitude (degrees) of each of the 27 nakshatras.
# Only the equal-space system is implemented so far. Garga and Brahma-siddhanta
# (unequal spans, Kielhorn's alternatives) slot in here as further entries.
NAKSHATRA_SYSTEMS = {
    "equal": [i * NAK_WIDTH for i in range(27)],
}


def _segment(value: float, starts: list) -> int:
    """Which segment (1-based) of the circle `value` falls in."""
    value %= 360.0
    idx = 0
    for i, s in enumerate(starts):
        if value >= s:
            idx = i
    return idx + 1


def _segments_spanned(v0: float, v1: float, starts: list) -> tuple:
    """
    All segments passed through as an angle moves forward from v0 to v1
    (less than one full circle). E.g. a tithi that starts mid-day.
    """
    n = len(starts)
    span = (v1 - v0) % 360.0          # how far the angle moved
    k = _segment(v0, starts)
    out = [k]
    pos, travelled = v0 % 360.0, 0.0
    while True:
        dist = (starts[k % n] - pos) % 360.0   # distance to the start of the next segment
        if travelled + dist > span:
            break
        travelled += dist
        pos = starts[k % n]
        k = k % n + 1
        out.append(k)
    return tuple(out)


TITHI_STARTS = [i * TITHI_WIDTH for i in range(30)]


# ------------------------------------------------------- one day

def describe_day(n: int, nak_system: str = "equal", place=astro.THANJAVUR,
                 calendar: str = "julian") -> dict:
    """
    Everything about civil day n (a Julian Day Number), with the times at which
    tithis and nakshatras change, in hours after sunrise. Slow-ish; for display
    and checking. Use `build_calendar` for scanning many days.
    """
    y, m, d = astro.date_from_day_number(n, calendar)
    rise = astro.sunrise(n, place)
    next_rise = astro.sunrise(n + 1, place)
    sset = astro.sunset(n, place)
    starts = NAKSHATRA_SYSTEMS[nak_system]

    def changes(f, seg_starts):
        out = []
        segs = _segments_spanned(f(rise), f(next_rise), seg_starts)
        for k in segs[1:]:
            t = astro.find_crossing(f, seg_starts[k - 1], rise, next_rise)
            out.append((k, round((t - rise) * 24, 2)))
        return segs, out

    tithis, tithi_changes = changes(astro.elongation, TITHI_STARTS)
    naks, nak_changes = changes(astro.moon_longitude, starts)
    sun_r = astro.sun_longitude(rise)

    return {
        "day_number": n,
        "date": f"{y:04d}-{m:02d}-{d:02d} ({calendar})",
        "weekday": WEEKDAYS[astro.weekday(n)],
        "sunrise_local": _local_clock(rise, place),
        "sun_longitude": round(sun_r, 3),
        "sign_at_sunrise": SIGNS[int(sun_r // 30)],
        "sign_at_sunset": SIGNS[int(astro.sun_longitude(sset) // 30)],
        "tithi_at_sunrise": tithi_label(tithis[0]),
        "tithi_changes": [(tithi_label(k), h) for k, h in tithi_changes],
        "nakshatra_at_sunrise": NAKSHATRAS[naks[0] - 1],
        "nakshatra_changes": [(NAKSHATRAS[k - 1], h) for k, h in nak_changes],
        "ayanamsa": astro.get_ayanamsa(),
    }


def _local_clock(jd_ut: float, place) -> str:
    """Local mean time as HH:MM."""
    frac = (jd_ut + 0.5 + place[0] / 360.0) % 1.0
    mins = int(round(frac * 1440))
    return f"{mins // 60:02d}:{mins % 60:02d}"


# --------------------------------------------- many days at once

def build_calendar(n_start: int, n_end: int, nak_system: str = "equal",
                   place=astro.THANJAVUR) -> pd.DataFrame:
    """
    A table with one row per civil day from n_start to n_end inclusive.

    Columns:
      n, date (Julian), weekday (0=Sun),
      tithi            tithi at sunrise (1-30)
      tithis           every tithi current during the day (sunrise to sunrise)
      nakshatra        nakshatra at sunrise (1-27)
      nakshatras       every nakshatra current during the day
      sign_rise        solar month = sun's sign at sunrise (0=Mesha ... 11=Mina)
      sday_rise        day of that solar month, counting from the first sunrise in the sign
      sign_set, sday_set   the same using the sun's sign at sunset
                       (the Tamil rule: if the sun changes sign before sunset,
                        that day is day 1 of the new month)
    """
    starts = NAKSHATRA_SYSTEMS[nak_system]
    pad = 35  # start early so solar-day counts are known from the first real row
    rows = []
    rise = astro.sunrise(n_start - pad, place)
    e0, m0 = astro.elongation(rise), astro.moon_longitude(rise)
    for n in range(n_start - pad, n_end + 1):
        next_rise = astro.sunrise(n + 1, place)
        e1, m1 = astro.elongation(next_rise), astro.moon_longitude(next_rise)
        sset = astro.sunset(n, place)
        tithis = _segments_spanned(e0, e1, TITHI_STARTS)
        naks = _segments_spanned(m0, m1, starts)
        rows.append({
            "n": n,
            "weekday": astro.weekday(n),
            "sunrise_ut": rise,
            "tithi": tithis[0],
            "tithis": tithis,
            "nakshatra": naks[0],
            "nakshatras": naks,
            "sign_rise": int(astro.sun_longitude(rise) // 30),
            "sign_set": int(astro.sun_longitude(sset) // 30),
        })
        rise, e0, m0 = next_rise, e1, m1

    df = pd.DataFrame(rows)
    for rule in ("rise", "set"):
        col, out, count, prev = f"sign_{rule}", [], None, None
        for s in df[col]:
            count = 1 if (prev is not None and s != prev) else (count + 1 if count else None)
            out.append(count)
            prev = s
        df[f"sday_{rule}"] = out
    df = df[df["n"] >= n_start].reset_index(drop=True)
    df.insert(1, "date", [ "%04d-%02d-%02d" % astro.date_from_day_number(n) for n in df["n"]])
    return df
