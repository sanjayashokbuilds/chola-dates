"""
Kielhorn's inscription No. 60 (Kulottunga III, year 14), solved from scratch.

The carving says: "Thursday, Pushya, the first tithi of the first fortnight of
the month of Makara". Kielhorn (1902) judged this impossible as written and
concluded the second fortnight was meant, giving Thursday 2 January 1192.

Run from the repository root:   python examples/no60.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from chola import astro, panchang as p
from chola.search import search

as_carved = {"solar_month": "Makara", "paksha": "shukla", "tithi": 1,
             "nakshatra": "Pushya", "weekday": "Thursday"}
window = ((1191, 6, 1), (1192, 7, 31))  # the 14th regnal year must fall in here

print("Exact matches for the clues as carved:")
exact = search(as_carved, *window)
print("  none" if exact.empty else exact.to_string(index=False))

print("\nDays matching all clues but one:")
print(search(as_carved, *window, max_mismatches=1).to_string(index=False))

print("\nThe day Kielhorn chose, in full:")
for k, v in p.describe_day(astro.day_number(1192, 1, 2)).items():
    print(f"  {k:22s} {v}")
