"""
The detective: estimate when a king's reign began, allowing for miscarved inscriptions.

Two methods.

1. VOTES (the simple one). For each candidate accession day A, count how many
   inscriptions have at least one day matching ALL their clues inside the regnal
   year A implies. With no carving errors, the true A would score every
   inscription; with errors, it scores the most. The set of top-scoring A is an
   "interval intersection" that tolerates errors.

2. BAYES (the headline). Every candidate A gets a probability, built like this:
   - The inscription's true date d is some day of its regnal year (any day equally likely).
   - Each clue was carved correctly with probability 1 - eps, or wrongly with
     probability eps, in which case the wrong value follows an error model
     (e.g. the other fortnight, the neighbouring tithi or nakshatra, a 4 for a 14).
   - The regnal year itself is miscarved (off by one) with probability eps_year.
   - eps is unknown: we put a grid of values on it and let the data weigh them.
   Multiplying over inscriptions and normalising gives P(A, eps | all inscriptions).
   From the same quantities we get, for each inscription, the probability that it
   was miscarved and its most likely true date and error.
"""

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from . import astro, panchang as p
from .search import _parse, SOLAR_DAY_TOLERANCE

YEAR = 365.25

# ------------------------------------------------------------ error models
# q(carved | true): how a WRONG carving is distributed. These are assumptions,
# stated openly; scripts/detective.py checks the result is not sensitive to them.

def _q_tithi(carved: set, true: tuple) -> float:
    """Wrong tithi: other fortnight (0.3), neighbouring tithi (0.15 each side), anything else (0.4 spread)."""
    best = 0.0
    for c in carved:
        for t in true:
            k_c, k_t = (c - 1) % 15, (t - 1) % 15
            if k_c == k_t and c != t:
                q = 0.30                                   # paksha swapped
            elif min((c - t) % 30, (t - c) % 30) == 1:
                q = 0.15                                   # adjacent tithi
            else:
                q = 0.40 / 27
            best = max(best, q)
    return best


def _q_nakshatra(carved: int, true: tuple) -> float:
    """Wrong nakshatra: neighbouring (0.25 each side), anything else (0.5 spread)."""
    adj = any(min((carved - t) % 27, (t - carved) % 27) == 1 for t in true)
    return 0.25 if adj else 0.50 / 24


def _q_month(carved: int, true: int) -> float:
    adj = min((carved - true) % 12, (true - carved) % 12) == 1
    return 0.35 if adj else 0.30 / 9


def _q_solar_day(carved: int, true: int) -> float:
    """Wrong solar day: a 10 slipped (e.g. 15 for 25; 0.25 each way), anything else."""
    return 0.25 if abs(abs(carved - true) - 10) <= SOLAR_DAY_TOLERANCE else 0.50 / 26


def _q_weekday(carved: int, true: int) -> float:
    return 1.0 / 6


# ------------------------------------------------------- per-day evidence

@dataclass
class Evidence:
    """For one inscription: which clues hold on each calendar day, and q for those that don't."""
    id: str
    year: int
    clue_names: list
    match: np.ndarray          # (days, clues) bool
    log_q: np.ndarray          # (days, clues) log q(carved | true) where not matched
    carved_tithi: set = field(default_factory=set)


UNIFORM_Q = {"solar_month": 1 / 11, "solar_day": 1 / 29, "tithi": 1 / 29,
             "nakshatra": 1 / 26, "weekday": 1 / 6}


def evidence(cal: pd.DataFrame, row, mode: str = "day", month_rule: str = "set",
             structured: bool = True) -> Evidence:
    """
    mode: "day" = a tithi/nakshatra current at any time during the day counts as a match;
          "sunrise" = only the one in force at sunrise;
          "kielhorn" = tithi at sunrise, nakshatra at any time (Kielhorn's practice).
    structured: use the error models above; False = every wrong value equally likely.
    """
    c = _parse({k: row[k] for k in ("solar_month", "solar_day", "paksha", "tithi",
                                     "nakshatra", "weekday") if row[k] != ""})
    names, M, Q = [], [], []
    sign = cal[f"sign_{month_rule}"].to_numpy()
    sday = cal[f"sday_{month_rule}"].to_numpy()
    # "kielhorn": tithi must be the one at sunrise, nakshatra may be any during the day
    tith = cal["tithis"].tolist() if mode == "day" else [(t,) for t in cal["tithi"]]
    naks = cal["nakshatras"].tolist() if mode in ("day", "kielhorn") else [(k,) for k in cal["nakshatra"]]
    wd = cal["weekday"].to_numpy()

    if "solar_month" in c:
        names.append("solar_month")
        M.append(sign == c["solar_month"])
        Q.append([_q_month(c["solar_month"], s) for s in sign])
    if "solar_day" in c:
        names.append("solar_day")
        M.append(np.abs(sday - c["solar_day"]) <= SOLAR_DAY_TOLERANCE)
        Q.append([_q_solar_day(c["solar_day"], s) for s in sday])
    if "tithi" in c:
        names.append("tithi")
        M.append(np.array([bool(c["tithi"] & set(ts)) for ts in tith]))
        Q.append([_q_tithi(c["tithi"], ts) for ts in tith])
    if "nakshatra" in c:
        names.append("nakshatra")
        M.append(np.array([c["nakshatra"] in ns for ns in naks]))
        Q.append([_q_nakshatra(c["nakshatra"], ns) for ns in naks])
    if "weekday" in c:
        names.append("weekday")
        M.append(wd == c["weekday"])
        Q.append([_q_weekday(c["weekday"], w) for w in wd])

    Q = np.column_stack(Q)
    if not structured:
        Q = np.tile([UNIFORM_Q[nm] for nm in names], (len(cal), 1))
    return Evidence(row["id"], int(row["regnal_year"]), names, np.column_stack(M), np.log(Q),
                    c.get("tithi", set()))


def day_likelihood(ev: Evidence, eps: float) -> np.ndarray:
    """P(clues as carved | true date = each calendar day), for error rate eps."""
    lp = np.where(ev.match, np.log1p(-eps), np.log(eps) + ev.log_q)
    return np.exp(lp.sum(axis=1))


# ------------------------------------------------------------- windows

def _window_bounds(acc_idx: np.ndarray, year: int):
    """Calendar-row indices [start, end) of regnal year `year` for each accession index."""
    lo = acc_idx + int(round((year - 1) * YEAR))
    hi = acc_idx + int(round(year * YEAR))
    return lo, hi


def _window_mean(cum: np.ndarray, acc_idx: np.ndarray, year: int) -> np.ndarray:
    lo, hi = _window_bounds(acc_idx, year)
    return (cum[hi] - cum[lo]) / (hi - lo)


# --------------------------------------------------------------- method 1

def votes(cal: pd.DataFrame, evs: list, acc_idx: np.ndarray) -> np.ndarray:
    """For each candidate accession, how many inscriptions it explains with zero errors."""
    total = np.zeros(len(acc_idx), dtype=int)
    for ev in evs:
        exact = ev.match.all(axis=1).astype(float)
        cum = np.concatenate([[0.0], np.cumsum(exact)])
        total += (_window_mean(cum, acc_idx, ev.year) > 0).astype(int)
    return total


# --------------------------------------------------------------- method 2

@dataclass
class Posterior:
    acc_n: np.ndarray            # candidate accession day numbers
    eps_grid: np.ndarray
    joint: np.ndarray            # P(A, eps | data), shape (A, eps)
    eps_year: float
    log_evidence: float = 0.0    # log P(data | model), for comparing modelling choices

    @property
    def accession(self) -> np.ndarray:
        return self.joint.sum(axis=1)

    @property
    def eps(self) -> np.ndarray:
        return self.joint.sum(axis=0)

    def interval(self, mass: float) -> tuple:
        """Shortest set of days holding `mass` of the probability -> (first, last) day numbers."""
        pa = self.accession
        order = np.argsort(pa)[::-1]
        keep = order[: np.searchsorted(np.cumsum(pa[order]), mass) + 1]
        return int(self.acc_n[keep.min()]), int(self.acc_n[keep.max()])

    def mode(self) -> int:
        return int(self.acc_n[np.argmax(self.accession)])

    def top_days(self, rel: float = 0.9) -> tuple:
        """
        The run of days whose probability is within `rel` of the maximum, as
        (first day, last day, combined probability). For Kulottunga III, 6, 7 and
        8 July 1178 are tied to within 0.03 percentage points, so naming a single
        "most likely" day would be reporting rounding noise.
        """
        pa = self.accession
        keep = np.nonzero(pa >= rel * pa.max())[0]
        return int(self.acc_n[keep.min()]), int(self.acc_n[keep.max()]), float(pa[keep].sum())


def fit(cal: pd.DataFrame, evs: list, acc_idx: np.ndarray,
        eps_grid=np.linspace(0.01, 0.30, 30), eps_year: float = 0.05) -> Posterior:
    """
    P(A, eps | data) on a grid. Uniform prior over A (the grid) and over eps.
    A regnal year is taken as miscarved by one (either way) with probability eps_year.
    """
    logj = np.zeros((len(acc_idx), len(eps_grid)))
    for j, eps in enumerate(eps_grid):
        for ev in evs:
            cum = np.concatenate([[0.0], np.cumsum(day_likelihood(ev, eps))])
            L = (1 - eps_year) * _window_mean(cum, acc_idx, ev.year)
            for dy in (-1, 1):
                if ev.year + dy >= 1:
                    L = L + eps_year / 2 * _window_mean(cum, acc_idx, ev.year + dy)
            logj[:, j] += np.log(L)
    top = logj.max()
    joint = np.exp(logj - top)
    log_ev = top + np.log(joint.sum()) - np.log(joint.size)   # average over the uniform prior grid
    return Posterior(cal["n"].to_numpy()[acc_idx], np.asarray(eps_grid), joint / joint.sum(),
                     eps_year, float(log_ev))


def explain(cal: pd.DataFrame, ev: Evidence, post: Posterior, acc_idx: np.ndarray,
            min_mass: float = 1e-6) -> dict:
    """
    For one inscription, averaging over the posterior of (A, eps):
      p_clean    probability that every clue and the regnal year were carved correctly
      dates      posterior probability of each candidate true date, with the clues
                 that would then be wrong
    """
    n_days = len(cal)
    p_date = np.zeros(n_days)
    p_shift = np.zeros(n_days)   # part of p_date that needs a miscarved regnal year
    p_clean = 0.0
    exact = ev.match.all(axis=1)
    for j, eps in enumerate(post.eps_grid):
        dl = day_likelihood(ev, eps)
        for a in np.nonzero(post.joint[:, j] > min_mass)[0]:
            w = post.joint[a, j]
            parts = []
            for dy, py in ((0, 1 - post.eps_year), (-1, post.eps_year / 2), (1, post.eps_year / 2)):
                y = ev.year + dy
                if y < 1:
                    continue
                lo, hi = _window_bounds(np.array([acc_idx[a]]), y)
                lo, hi = int(lo[0]), int(hi[0])
                parts.append((lo, hi, py / (hi - lo), dy))
            L = sum(py * dl[lo:hi].sum() for lo, hi, py, dy in parts)
            for lo, hi, py, dy in parts:
                contrib = py * dl[lo:hi] / L
                p_date[lo:hi] += w * contrib
                if dy != 0:
                    p_shift[lo:hi] += w * contrib
                if dy == 0:
                    p_clean += w * (contrib * exact[lo:hi]).sum()
    top = np.argsort(p_date)[::-1][:3]
    dates = []
    for i in top:
        if p_date[i] < 0.01:
            break
        wrong = [ev.clue_names[k] for k in range(len(ev.clue_names)) if not ev.match[i, k]]
        if "tithi" in wrong and any((c - 1) % 15 == (t - 1) % 15 for c in ev.carved_tithi
                                    for t in cal["tithis"].iat[i]):
            wrong[wrong.index("tithi")] = "paksha"     # right tithi number, wrong fortnight
        if p_shift[i] > 0.5 * p_date[i]:
            wrong.append("regnal_year")
        dates.append({"date": cal["date"].iat[i], "prob": float(p_date[i]),
                      "wrong": ", ".join(wrong) or "-"})
    return {"id": ev.id, "p_miscarved": 1 - p_clean, "dates": dates}
