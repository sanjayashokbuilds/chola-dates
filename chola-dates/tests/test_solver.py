"""
Checks the solver against independent sources:
  1. a modern panchang (today's tithi),
  2. weekdays of every dated Chola inscription in Kielhorn's summary list
     (Epigraphia Indica Vol. VII, pp. 6-8), which tests our Julian-calendar handling,
  3. Kielhorn's full worked example No. 60 (Kulottunga III), including the
     scribal error he identified.

Run with:  pytest
"""

import pytest

from chola import astro, panchang as p
from chola.search import search

# ---------------------------------------------------------------- 1. modern

def test_today_matches_modern_panchang():
    # 15 Oct 2026 (Gregorian): drikpanchang gives Shukla Panchami at sunrise.
    n = astro.day_number(2026, 10, 15, "gregorian")
    day = p.describe_day(n, calendar="gregorian")
    assert day["tithi_at_sunrise"].startswith("Shukla 5")
    assert day["weekday"] == "Thursday"


def test_tithi_end_time_matches_modern_panchang():
    # shubhpanchang.com: Shukla Chaturthi (4th) ends 01:13 AM IST on 15 Oct 2026.
    # The 4th tithi ends when the moon is 48 degrees ahead of the sun.
    import swisseph as swe
    t0 = swe.julday(2026, 10, 14, 0.0, swe.GREG_CAL)
    t = astro.find_crossing(astro.elongation, 48.0, t0, t0 + 1.5)
    published = swe.julday(2026, 10, 14, 19 + 43 / 60, swe.GREG_CAL)  # 01:13 IST = 19:43 UT
    assert abs(t - published) * 1440 < 5  # within 5 minutes


def test_tithi_does_not_depend_on_ayanamsa():
    # Tithi uses moon minus sun, so the zodiac's starting point cancels out.
    n = astro.day_number(1192, 1, 2)
    results = []
    for name in ("lahiri", "suryasiddhanta"):
        astro.set_ayanamsa(name)
        results.append(p.describe_day(n)["tithi_at_sunrise"])
    astro.set_ayanamsa(*astro.DEFAULT_AYANAMSA)
    assert results[0] == results[1]


# ------------------------------------------------- 2. Kielhorn's weekdays

KIELHORN_WEEKDAYS = [
    # (year, month, day) Julian, weekday   -- king, Kielhorn's number
    ((999, 8, 29), "Tuesday"),     # Rajaraja I, No. 25
    ((1000, 5, 15), "Wednesday"),  # Rajaraja I, No. 27
    ((1020, 7, 7), "Thursday"),    # Rajendra I, No. 32
    ((1021, 3, 1), "Wednesday"),   # Rajendra I, No. 4
    ((1032, 10, 23), "Monday"),    # Rajendra I, No. 5
    ((1033, 11, 25), "Sunday"),    # Rajendra I, No. 33
    ((1039, 11, 22), "Thursday"),  # Rajadhiraja, No. 15
    ((1044, 3, 14), "Wednesday"),  # Rajadhiraja, No. 12
    ((1045, 2, 13), "Wednesday"),  # Rajadhiraja, No. 13
    ((1053, 5, 23), "Sunday"),     # Rajadhiraja, No. 35
    ((1055, 8, 17), "Thursday"),   # Rajendradeva, No. 38
    ((1057, 10, 27), "Monday"),    # Rajendradeva, No. 36
    ((1073, 11, 7), "Thursday"),   # Kulottunga I, No. 56
    ((1077, 2, 10), "Friday"),     # Kulottunga I, No. 39
    ((1114, 2, 22), "Sunday"),     # Kulottunga I, No. 9
    ((1114, 3, 13), "Friday"),     # Kulottunga I, No. 7
    ((1114, 10, 8), "Thursday"),   # Kulottunga I, No. 8
    ((1114, 12, 9), "Wednesday"),  # Kulottunga I, No. 40
    ((1118, 1, 7), "Monday"),      # Kulottunga I, No. 26
    ((1118, 1, 25), "Friday"),     # Kulottunga I, Nos. 20, 28
    ((1122, 5, 1), "Monday"),      # Vikrama-Chola, No. 21
    ((1122, 7, 31), "Monday"),     # Vikrama-Chola, No. 22
    ((1123, 5, 31), "Thursday"),   # Vikrama-Chola, No. 57
    ((1123, 6, 3), "Sunday"),      # Vikrama-Chola, No. 10
    ((1128, 4, 14), "Saturday"),   # Vikrama-Chola, No. 59
    ((1129, 1, 5), "Saturday"),    # Vikrama-Chola, No. 58
    ((1134, 4, 16), "Monday"),     # Vikrama-Chola, No. 41
    ((1135, 4, 18), "Thursday"),   # Vikrama-Chola, No. 43
    ((1185, 7, 8), "Monday"),      # Kulottunga III, No. 23
    ((1189, 12, 4), "Monday"),     # Kulottunga III, No. 19
    ((1192, 1, 2), "Thursday"),    # Kulottunga III, No. 60
    ((1194, 6, 4), "Saturday"),    # Kulottunga III, No. 24
    ((1196, 11, 12), "Tuesday"),   # Kulottunga III, No. 17
    ((1197, 11, 21), "Friday"),    # Kulottunga III, No. 16
    ((1205, 5, 5), "Thursday"),    # Kulottunga III, No. 44
    ((1207, 3, 7), "Wednesday"),   # Kulottunga III, No. 29
    ((1211, 9, 19), "Monday"),     # Kulottunga III, No. 18
    ((1215, 6, 7), "Sunday"),      # Kulottunga III, No. 30
]


@pytest.mark.parametrize("ymd,expected", KIELHORN_WEEKDAYS)
def test_weekday_matches_kielhorn(ymd, expected):
    n = astro.day_number(*ymd, "julian")
    assert p.WEEKDAYS[astro.weekday(n)] == expected


# ------------------------------------- 3. Kielhorn No. 60, end to end

# Kulottunga III, year 14: "Thursday, Pushya, the first tithi of the FIRST
# fortnight of the month of Makara". Kielhorn: impossible as written; the
# second (dark) fortnight was meant; the date is Thursday 2 Jan 1192, the 8th
# day of Makara, with Krishna 1 and Pushya at sunrise.
NO60_AS_CARVED = {"solar_month": "Makara", "paksha": "shukla", "tithi": 1,
                  "nakshatra": "Pushya", "weekday": "Thursday"}
NO60_CORRECTED = {**NO60_AS_CARVED, "paksha": "krishna"}
YEAR14_WINDOW = ((1191, 6, 1), (1192, 7, 31))  # Kielhorn: accession June/July 1178


def test_no60_as_carved_has_no_match():
    hits = search(NO60_AS_CARVED, *YEAR14_WINDOW)
    assert len(hits) == 0


def test_no60_corrected_gives_kielhorns_date():
    hits = search(NO60_CORRECTED, *YEAR14_WINDOW)
    assert list(hits["date"]) == ["1192-01-02"]


def test_no60_near_miss_points_to_the_fortnight():
    # Allowing one wrong clue, the as-carved text finds Kielhorn's date with the
    # tithi/paksha clue flagged as the failure: the detective's raw material.
    hits = search(NO60_AS_CARVED, *YEAR14_WINDOW, max_mismatches=1)
    row = hits[hits["date"] == "1192-01-02"].iloc[0]
    assert row["failed"] == "tithi"


def test_no60_details_at_sunrise():
    day = p.describe_day(astro.day_number(1192, 1, 2))
    assert day["sign_at_sunrise"] == "Makara"
    assert day["tithi_at_sunrise"].startswith("Krishna 1")
    assert day["nakshatra_at_sunrise"] == "Pushya"


# Every solar-day number Kielhorn states in EI IV-VIII for the dates we hold:
# (Julian date, solar month, day of month, source)
KIELHORN_SOLAR_DAYS = [
    ((1192, 1, 2), "Makara", 8, "VII No.60"), ((1197, 11, 21), "Vrischika", 25, "IV No.16"),
    ((1205, 5, 5), "Vrishabha", 11, "VI No.44"), ((1213, 6, 2), "Mithuna", 8, "VIII No.91"),
    ((1214, 11, 17), "Vrischika", 21, "VIII No.93"), ((1194, 1, 17), "Makara", 24, "VIII No.110"),
    ((1182, 3, 11), "Mina", 17, "VIII No.107"), ((1184, 7, 5), "Karka", 9, "VIII No.108"),
    ((1198, 5, 3), "Vrishabha", 9, "VIII No.111"), ((1200, 11, 6), "Vrischika", 11, "VIII No.112"),
    ((1202, 7, 24), "Karka", 28, "VIII No.113"), ((1209, 12, 21), "Dhanu", 27, "VIII No.114"),
    ((1188, 1, 5), "Makara", 11, "VIII No.90"), ((1214, 4, 14), "Mesha", 21, "VIII No.92"),
    ((1217, 1, 25), "Kumbha", 3, "VIII No.94"), ((1122, 5, 10), "Vrishabha", 16, "VIII No.103"),
    ((1125, 8, 18), "Simha", 22, "VIII No.105"), ((1218, 1, 29), "Kumbha", 6, "VIII No.115"),
    ((1226, 4, 17), "Mesha", 24, "VIII No.117"), ((1225, 2, 23), "Mina", 1, "VIII No.116"),
]


def test_solar_days_against_kielhorn():
    # Exact for at least 15 of 20; within one day for all 20 (see search.SOLAR_DAY_TOLERANCE).
    exact = 0
    for ymd, month, day, src in KIELHORN_SOLAR_DAYS:
        n = astro.day_number(*ymd)
        r = p.build_calendar(n, n).iloc[0]
        assert p.SIGNS[r["sign_set"]] == month, src
        assert abs(int(r["sday_set"]) - day) <= 1, src
        exact += int(r["sday_set"]) == day
    assert exact >= 15
