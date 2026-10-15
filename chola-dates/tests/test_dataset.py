"""
Regression test for the headline validation numbers (see scripts/validate.py).
If a change to the solver alters these, the test fails and we find out why.
"""

from chola import astro, dataset, panchang as p
from chola.search import check_clues


def _kielhorn_day_results():
    df = dataset.load("kulottunga3")
    out = []
    for _, r in df[df["kielhorn_date"] != ""].iterrows():
        n = dataset.day_number_of(r["kielhorn_date"])
        res = check_clues(p.build_calendar(n, n), dataset.clues(r), mode="day").iloc[0]
        out.append((r["id"], r["kielhorn_verdict"], int(res["n_mismatch"])))
    return out


def test_dataset_loads():
    df = dataset.load("kulottunga3")
    assert len(df) == 24
    assert set(df["kielhorn_verdict"]) == {"correct", "error", "unresolved"}


def test_every_date_kielhorn_calls_correct_satisfies_all_clues():
    res = _kielhorn_day_results()
    correct = [(i, m) for i, v, m in res if v == "correct"]
    assert len(correct) == 14
    assert all(m == 0 for _, m in correct), correct


def test_kielhorn_errors_split():
    # 5 of his 9 'errors' genuinely fail on his day; 4 hold if the tithi
    # current later in the day is meant (Nos. 108, 109, 113, 114).
    res = {i: m for i, v, m in _kielhorn_day_results() if v == "error"}
    assert sorted(i for i, m in res.items() if m == 0) == ["K3-108", "K3-109", "K3-113", "K3-114"]
    assert sorted(i for i, m in res.items() if m > 0) == ["K3-111", "K3-16", "K3-24", "K3-60", "K3-90"]
