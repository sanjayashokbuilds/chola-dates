"""
Validation: run the solver on every inscription in the dataset and compare with Kielhorn.

For each inscription:
  1. Check every clue on KIELHORN'S chosen day, under two readings of the tithi /
     nakshatra: in force at sunrise ("sunrise"), or at any time during the day ("day").
  2. Search the regnal year implied by Kielhorn's accession date (about 7 July 1178)
     for days matching ALL clues, and report whether Kielhorn's day is the unique match.

Writes results/validation.csv and results/validation.md.

Run from the repository root:   python scripts/validate.py
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pandas as pd

from chola import astro, dataset, panchang as p
from chola.search import check_clues

KIELHORN_ACCESSION = (1178, 7, 7)  # EI VIII: between about 6 and 8 July 1178


def main():
    df = dataset.load("kulottunga3")
    acc = astro.day_number(*KIELHORN_ACCESSION)
    cal = p.build_calendar(acc - 400, acc + round(40 * 365.25))

    rows = []
    for _, r in df.iterrows():
        cl = dataset.clues(r)
        out = {"id": r["id"], "year": r["regnal_year"], "kielhorn_date": r["kielhorn_date"],
               "kielhorn_verdict": r["kielhorn_verdict"], "kielhorn_error": r["kielhorn_error_field"],
               "fails_sunrise": "n/a", "fails_day": "n/a"}

        # 1. clues on Kielhorn's day
        if r["kielhorn_date"]:
            n = dataset.day_number_of(r["kielhorn_date"])
            day = cal[cal["n"] == n]
            for mode in ("sunrise", "day"):
                res = check_clues(day, cl, mode=mode).iloc[0]
                failed = [k for k in res.index if k not in ("n", "date", "n_mismatch") and not res[k]]
                out[f"fails_{mode}"] = ", ".join(failed) or "-"

        # 2. exact matches in the regnal year
        lo, hi = dataset.regnal_year_window(acc, r["regnal_year"], pad_days=3)
        window = cal[(cal["n"] >= lo) & (cal["n"] <= hi)]
        for mode in ("sunrise", "day"):
            res = check_clues(window, cl, mode=mode)
            out[f"matches_{mode}"] = " ".join(res[res["n_mismatch"] == 0]["date"]) or "-"
        rows.append(out)

    res = pd.DataFrame(rows)
    outdir = ROOT / "results"
    outdir.mkdir(exist_ok=True)
    res.to_csv(outdir / "validation.csv", index=False)

    # summary
    dated = res[res["kielhorn_date"] != ""]
    k_ok = dated[dated["kielhorn_verdict"] == "correct"]
    summary = {
        "inscriptions": len(res),
        "with a Kielhorn date": len(dated),
        "Kielhorn says correct": len(k_ok),
        "...of which all clues hold on his day (sunrise rule)": int((k_ok["fails_sunrise"] == "-").sum()),
        "...of which all clues hold on his day (during-day rule)": int((k_ok["fails_day"] == "-").sum()),
        "Kielhorn says error": int((dated["kielhorn_verdict"] == "error").sum()),
        "...of which all clues hold on his day anyway (during-day rule)":
            int(((dated["kielhorn_verdict"] == "error") & (dated["fails_day"] == "-")).sum()),
    }
    with open(outdir / "validation.md", "w") as f:
        f.write("# Validation against Kielhorn (Kulottunga III)\n\n")
        f.write(f"Ayanamsa: {astro.get_ayanamsa()}; solar month by sun's sign at sunset.\n\n")
        for k, v in summary.items():
            f.write(f"- {k}: **{v}**\n")
        f.write("\n" + res.to_markdown(index=False) + "\n")
    print(open(outdir / "validation.md").read())


if __name__ == "__main__":
    main()
