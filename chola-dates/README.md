# chola-dates

Re-dating medieval Chola kings from the astronomical clues carved into their
temple inscriptions, with an explicit model of scribal errors.

> Status: **work in progress** (24-hour build, Oct 2026). Solver, dataset and
> validation are done; the accession-date model is next.

## The problem

Chola inscriptions (c. 850–1280 CE) don't give calendar dates. They say things like
*"in the 14th year of king Kulottunga, on a Thursday, the day of the nakshatra Pushya,
the first tithi of the first fortnight of the month of Makara."* Around 1900,
F. Kielhorn solved hundreds of these by hand (*Epigraphia Indica*, vols IV–VIII) and used
them to fix when each king began to reign. Many carvings contain mistakes.

This project rebuilds that work computationally:

1. **Solver**: turns an inscription's clues into every matching day.
2. **Dataset**: every Kulottunga III date Kielhorn examined, machine-readable.
3. **Detective** *(next)*: estimates the accession date with uncertainty, while
   working out which inscriptions are probably miscarved and how.

## The solver

For any day it computes, at Thanjavur:

| Clue | How |
|---|---|
| Weekday | from the Julian Day Number |
| Solar month and day | the sun's sidereal sign at sunset, and days since it entered it |
| Tithi and paksha | the moon's lead over the sun, in 12° steps |
| Nakshatra | the moon's sidereal position, in 27 steps of 13°20′ |

Positions come from the Swiss Ephemeris (`pyswisseph`). Dates before 1582 are Julian.
An Indian day runs from sunrise to sunrise; the solver records the tithi and nakshatra
at sunrise *and* every one current during the day, so both readings can be tested.

**Calibration.** Kielhorn computed with the traditional *Surya-siddhanta*, not modern
astronomy. Five sankranti times he publishes for 1193–1225 imply our sidereal frame should
sit **1.69° ± 0.14°** from modern Lahiri (`scripts/calibrate.py`). With that, his 20
published solar-day numbers are reproduced exactly in 15 cases and within one day in all 20;
the remaining differences come from the traditional sun model's different equation of
centre, so a stated solar day is accepted ±1.

## The dataset

[`data/kulottunga3.csv`](data/kulottunga3.csv): **24 dated inscriptions of Kulottunga III**
(r. 1178–1218) from Kielhorn's "Dates of Chola Kings" in *EI* IV, V, VI, VII and VIII. For
each: place, regnal year, every astronomical clue *as carved*, Kielhorn's computed date and
his verdict (correct, or which detail he judged wrong).

## Validation against Kielhorn

`python scripts/validate.py` → [`results/validation.md`](results/validation.md)

| | |
|---|---|
| Dates Kielhorn calls **correct** | 14 |
| ... all clues hold on his day, and it is the **only** matching day in that regnal year | **14 / 14** |
| Dates Kielhorn calls **erroneous** | 9 |
| ... clues genuinely fail on his day (wrong fortnight ×2, nakshatra, tithi 4-for-14, solar day 15-for-25) | 5 |
| ... **all clues hold** if the tithi current *later in the day* is meant | **4** (Nos. 108, 109, 113, 114) |

**Finding.** Kielhorn marks Nos. 108/109, 113 and 114 as "wrong tithi" (12 for 11, 5 for 4,
9 for 8). In each case the carved tithi is the *next* one, which began during that same
day. That is a consistent pattern, more like a recording convention (the tithi current at
the time of the event) than random carving errors. The detective will weigh both readings.

Also checked: weekdays of **38/38** dated Chola inscriptions in Kielhorn's summary list
(*EI* VII pp. 6–8), and a modern tithi boundary against a published panchang (to the minute).

## Worked example: No. 60

`python examples/no60.py`. As carved ("first fortnight"), no day matches. Allowing one
error, two candidates appear: 2 Jan 1192 (fortnight wrong; Kielhorn's answer) and
16 Jan 1192 (nakshatra wrong). Choosing between them is the detective's job.

## Run it

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest                         # 49 tests
python scripts/validate.py     # dataset vs Kielhorn
python scripts/calibrate.py    # frame calibration
```

## Limitations (so far)

- One king. Kielhorn's own corpus for Kulottunga III is ~24 dates, not hundreds.
- Data extracted from OCR'd transcriptions of Kielhorn; each row is cross-checked by
  the solver, but readings of damaged originals are his (or his sources').
- Only the equal-space nakshatra system; Garga and Brahma-siddhanta are not yet implemented.
- Our sun is modern; a full Surya-siddhanta sun would remove the ±1 solar-day tolerance.

## Sources

- F. Kielhorn, "Dates of Chola Kings", *Epigraphia Indica* IV (1896–97), V, VI (1900–01),
  VII (1902–03), VIII (1905–06); transcriptions at whatisindia.com and jainqq.org
- Swiss Ephemeris (Astrodienst), via `pyswisseph`; AGPL-3.0, hence this repository's licence
