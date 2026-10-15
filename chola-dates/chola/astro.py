"""
Low-level astronomy: calendar dates, sun and moon positions, sunrise and sunset.

Everything else in the project is built on the handful of functions here.

Key choices (explained in the README):
- Positions come from the Swiss Ephemeris (pyswisseph) using its built-in
  Moshier formulas, accurate to a few arcseconds for medieval dates, far more
  than we need. It also corrects automatically for Earth's slowing rotation (Delta-T).
- Positions are sidereal (measured against the fixed stars, the Indian way).
  The ayanamsa (where 0 degrees sits) is a setting: "lahiri" by default.
- Dates before 1582 are in the Julian calendar, as in Kielhorn.
- The place is Thanjavur, the Chola capital.
"""

import math
import swisseph as swe

# (longitude east, latitude north, altitude in metres)
THANJAVUR = (79.1378, 10.7870, 0.0)

AYANAMSAS = {
    "lahiri": swe.SIDM_LAHIRI,
    "suryasiddhanta": swe.SIDM_SURYASIDDHANTA,
}

_EPHEMERIS = swe.FLG_MOSEPH  # built-in formulas, no data files needed
_ayanamsa = None
_shift = 0.0


def set_ayanamsa(name: str = "lahiri", shift: float = 0.0) -> None:
    """
    Choose where sidereal 0 degrees sits. Affects solar months and nakshatras, not tithis.
    `shift` (degrees) is added to the named ayanamsa, for calibrating against Kielhorn.
    """
    global _ayanamsa, _shift
    swe.set_sid_mode(AYANAMSAS[name])
    _ayanamsa, _shift = name, shift


def get_ayanamsa() -> str:
    return _ayanamsa if _shift == 0 else f"{_ayanamsa}{_shift:+.2f}"


# PROVISIONAL default: Lahiri shifted by -1.5 deg. With this shift both the
# sunrise and the sunset rule reproduce Kielhorn's solar-day numbers for the
# two dates checked so far (No. 60, 2 Jan 1192 = Makara 8; No. 16, 21 Nov 1197
# = day 25). To be recalibrated on the full dataset in the validation stage.
DEFAULT_AYANAMSA = ("lahiri", -1.5)

set_ayanamsa(*DEFAULT_AYANAMSA)


# ---------------------------------------------------------------- dates

def _cal(calendar: str) -> int:
    if calendar == "julian":
        return swe.JUL_CAL
    if calendar == "gregorian":
        return swe.GREG_CAL
    raise ValueError("calendar must be 'julian' or 'gregorian'")


def day_number(y: int, m: int, d: int, calendar: str = "julian") -> int:
    """
    The Julian Day Number of a civil date: a plain count of days since 4713 BC.
    Working in day numbers avoids all month/leap-year bookkeeping.
    """
    return int(round(swe.julday(y, m, d, 12.0, _cal(calendar))))


def date_from_day_number(n: int, calendar: str = "julian") -> tuple:
    y, m, d, _ = swe.revjul(float(n), _cal(calendar))
    return int(y), int(m), int(d)


def weekday(n: int) -> int:
    """Weekday of a day number, 0 = Sunday ... 6 = Saturday."""
    return (n + 1) % 7


def local_midnight_ut(n: int, place=THANJAVUR) -> float:
    """
    The moment (as a Universal Time Julian Date) when civil day n begins at
    local mean midnight at `place`. Thanjavur is about 5h17m ahead of UT.
    """
    return n - 0.5 - place[0] / 360.0


# ------------------------------------------------------- sun and moon

def sun_longitude(jd_ut: float) -> float:
    """Sidereal longitude of the sun, 0-360 degrees, at a UT moment."""
    return (swe.calc_ut(jd_ut, swe.SUN, _EPHEMERIS | swe.FLG_SIDEREAL)[0][0] - _shift) % 360.0


def moon_longitude(jd_ut: float) -> float:
    """Sidereal longitude of the moon, 0-360 degrees, at a UT moment."""
    return (swe.calc_ut(jd_ut, swe.MOON, _EPHEMERIS | swe.FLG_SIDEREAL)[0][0] - _shift) % 360.0


def elongation(jd_ut: float) -> float:
    """How far the moon is ahead of the sun, 0-360 degrees. Independent of ayanamsa."""
    return (moon_longitude(jd_ut) - sun_longitude(jd_ut)) % 360.0


# ------------------------------------------------- sunrise and sunset

def _rise_or_set(jd_start: float, which: int, place) -> float:
    res, tret = swe.rise_trans(jd_start, swe.SUN, which, place, 0.0, 0.0, _EPHEMERIS)
    if res != 0:
        raise RuntimeError("Sun event not found")
    return tret[0]


def sunrise(n: int, place=THANJAVUR) -> float:
    """UT moment of sunrise on civil day n (upper limb, standard refraction)."""
    return _rise_or_set(local_midnight_ut(n, place), swe.CALC_RISE, place)


def sunset(n: int, place=THANJAVUR) -> float:
    """UT moment of sunset on civil day n."""
    return _rise_or_set(local_midnight_ut(n, place), swe.CALC_SET, place)


def find_crossing(f, target: float, t0: float, t1: float, tol_days: float = 1 / 1440) -> float:
    """
    Find the moment between t0 and t1 when the angle f(t) (degrees, increasing)
    passes `target`, by repeatedly halving the interval (bisection).
    Used to report when a tithi or nakshatra starts or ends.
    """
    def ahead(t):
        return ((f(t) - target + 180.0) % 360.0) - 180.0  # >0 once past target

    lo, hi = t0, t1
    while hi - lo > tol_days:
        mid = (lo + hi) / 2
        if ahead(mid) >= 0:
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2
