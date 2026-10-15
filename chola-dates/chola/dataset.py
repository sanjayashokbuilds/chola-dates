"""Loading the inscription dataset and turning each row into solver clues."""

from pathlib import Path

import pandas as pd

from . import astro

DATA = Path(__file__).resolve().parents[1] / "data"
CLUE_FIELDS = ["solar_month", "solar_day", "paksha", "tithi", "nakshatra", "weekday"]


def load(name: str = "kulottunga3") -> pd.DataFrame:
    df = pd.read_csv(DATA / f"{name}.csv", dtype=str).fillna("")
    df["regnal_year"] = df["regnal_year"].astype(int)
    return df


def clues(row) -> dict:
    """The astronomical clues of one inscription, as carved."""
    return {k: row[k] for k in CLUE_FIELDS if row[k] != ""}


def day_number_of(iso: str) -> int:
    """'1192-01-02' (Julian) -> Julian Day Number."""
    y, m, d = (int(x) for x in iso.split("-"))
    return astro.day_number(y, m, d, "julian")


def regnal_year_window(accession_n: int, year: int, pad_days: int = 0) -> tuple:
    """Day numbers [start, end] of regnal year `year` for a given accession day."""
    start = accession_n + round((year - 1) * 365.25) - pad_days
    end = accession_n + round(year * 365.25) - 1 + pad_days
    return start, end
