# chola-dates

Re-dating medieval Chola kings from the astronomical clues carved into their
temple inscriptions, with an explicit model of scribal errors.

> Status: **work in progress** (24-hour build, Oct 2026). The date solver is working
> and tested; the dataset and the accession-date model are next.

## The problem

Chola inscriptions (c. 850–1280 CE) don't give calendar dates. They say things like
*"in the 14th year of king Kulottunga, on a Thursday, the day of the nakshatra Pushya,
the first tithi of the first fortnight of the month of Makara."* Around 1900,
F. Kielhorn solved hundreds of these by hand (*Epigraphia Indica*, vols 4–10) and used
them to fix when each king began to reign. Many carvings contain mistakes.

This project rebuilds that work computationally:

1. **Solver**: turns an inscription's clues into every matching day.
2. **Dataset**: dated inscriptions for one king (Kulottunga III) in a clean CSV.
3. **Detective**: estimates the accession date with uncertainty, while
   working out which inscriptions are probably miscarved and how.

## What the solver does

For any day it computes, at Thanjavur:

| Clue | How |
|---|---|
| Weekday | from the Julian Day Number |
| Solar month and day | the sun's sidereal sign (and days since it entered it) |
| Tithi and paksha | moon's lead over the sun, in 12° steps |
| Nakshatra | moon's sidereal position, in 27 steps of 13°20′ |

Positions come from the Swiss Ephemeris (`pyswisseph`). Dates before 1582 are Julian.
An Indian day runs from sunrise to sunrise; the solver records both the tithi and
nakshatra at sunrise and every one current during the day.

## Results so far

- Weekdays: **38 / 38** dated Chola inscriptions in Kielhorn's summary list
  (*EI* VII, pp. 6–8) reproduced.
- Modern check: today's (15 Oct 2026) tithi boundary matches a published panchang
  to the minute.
- Kielhorn's inscription No. 60: as carved, **no day matches**. Allowing one error,
  two candidates appear: 2 Jan 1192 (fortnight wrong, Kielhorn's answer) and
  16 Jan 1192 (nakshatra wrong). Choosing between them is the detective's job.
- Solar-day numbering: Kielhorn's day counts are reproduced with the star frame
  shifted 1.5° from modern Lahiri. This is **provisional** (two dates) and will be
  recalibrated on the full dataset.

## Run it

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest                      # 46 tests
python examples/no60.py     # the worked example above
```

## Sources

- F. Kielhorn, "Dates of Chola Kings", *Epigraphia Indica* vols IV–VIII
  (transcriptions: whatisindia.com, jainqq.org)
- Swiss Ephemeris (Astrodienst), via `pyswisseph`; AGPL-3.0, hence this repository's licence
