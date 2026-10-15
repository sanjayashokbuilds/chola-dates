"""
Calibrate the sidereal frame against Kielhorn's published sankranti times.

Kielhorn gives, for several inscriptions, the moment the sun entered a sign
(in hours after mean sunrise). For each, we find how far our (Lahiri) frame must
be shifted so that our sun crosses the sign boundary at exactly that moment.

Assumption: "mean sunrise" = 6:00 local mean time at Ujjain (75.77 E), the
traditional Indian prime meridian. An error of an hour here moves the shift by
only ~0.04 degrees.

Run from the repository root:   python scripts/calibrate.py
"""

import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import swisseph as swe

from chola import astro, panchang as p

UJJAIN_LON = 75.77

KIELHORN_SANKRANTIS = [
    # (Julian date, hours after mean sunrise, sign entered, source)
    ((1193, 12, 25), 6 + 45 / 60, "Makara", "EI VIII No.110"),
    ((1205, 4, 24), 15 + 44 / 60, "Vrishabha", "EI VI No.44"),
    ((1213, 5, 26), 3 + 1 / 60, "Mithuna", "EI VIII No.91"),
    ((1197, 10, 27), 13 + 0 / 60, "Vrischika", "EI IV No.16 (Surya-siddhanta)"),
    ((1225, 2, 22), 13 + 35 / 60, "Mina", "EI VIII No.116"),
    ((942, 12, 23), 8 + 33 / 60, "Makara", "EI VIII No.101 (Arya-siddhanta)"),
]


def required_shift(ymd, hours, sign) -> float:
    t = swe.julday(*ymd, 6.0, swe.JUL_CAL) - UJJAIN_LON / 360.0 + hours / 24
    lon = astro.sun_longitude(t)
    return ((lon - p.SIGNS.index(sign) * 30 + 180) % 360) - 180


def main():
    astro.set_ayanamsa("lahiri", 0.0)
    era = []
    print(f"{'source':34s} {'sign':10s} required shift")
    for ymd, h, sign, src in KIELHORN_SANKRANTIS:
        s = required_shift(ymd, h, sign)
        print(f"{src:34s} {sign:10s} {s:+.3f} deg")
        if ymd[0] > 1100:
            era.append(s)
    print(f"\nKulottunga III era (n={len(era)}): mean {statistics.mean(era):+.3f}, "
          f"s.d. {statistics.stdev(era):.3f}")
    astro.set_ayanamsa(*astro.DEFAULT_AYANAMSA)


if __name__ == "__main__":
    main()
