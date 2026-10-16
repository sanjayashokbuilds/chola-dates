"""
Run the detective on Kulottunga III and write the results.

  1. Votes: which accession days explain the most inscriptions with zero errors.
  2. Bayesian model: posterior over the accession day and the scribal error rate;
     for each inscription, P(miscarved) and the most likely true date and error.
  3. Robustness: rerun under different assumptions and check the answer holds.
  4. Charts and a markdown report in results/.

Run from the repository root:   python scripts/detective.py
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from chola import astro, dataset, detective as dt, panchang as p

GRID = ((1174, 1, 1), (1182, 12, 31))     # candidate accession days (uniform prior)
KIELHORN_1903 = ((1178, 6, 8), (1178, 7, 8))  # EI VII summary list
KIELHORN_1906 = ((1178, 7, 6), (1178, 7, 8))  # EI VIII, after more dates

# chart colours (validated reference palette, light mode)
BLUE, ORANGE, GREY, INK, MUTED, GRIDC = "#2a78d6", "#eb6834", "#a3a29c", "#0b0b0b", "#52514e", "#e6e5e1"
OUT = ROOT / "results"


def iso(n):
    return "%04d-%02d-%02d" % astro.date_from_day_number(int(n))


def nice(n):
    y, m, d = astro.date_from_day_number(int(n))
    return f"{d} {['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'][m-1]} {y}"


def top_range(post):
    """'6–8 Jul 1178 (75%)': days tied for the highest probability, and their combined probability."""
    a, b, mass = post.top_days()
    (ya, ma, da), (yb, mb, db) = astro.date_from_day_number(a), astro.date_from_day_number(b)
    months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
    span = f"{da}–{db} {months[mb-1]} {yb}" if (ya, ma) == (yb, mb) else f"{nice(a)} – {nice(b)}"
    return span if a != b else nice(a), mass


def setup():
    df = dataset.load("kulottunga3")
    a0, a1 = (astro.day_number(*d) for d in GRID)
    cal = p.build_calendar(a0 - 5, a1 + round(41 * dt.YEAR))
    acc_idx = np.arange(a0, a1 + 1) - cal["n"].iat[0]
    return df, cal, acc_idx


def run(df, cal, acc_idx, mode="day", structured=True, eps_year=0.05):
    evs = [dt.evidence(cal, r, mode=mode, structured=structured) for _, r in df.iterrows()]
    return evs, dt.fit(cal, evs, acc_idx, eps_year=eps_year)


def style(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(GREY)
    ax.tick_params(colors=MUTED, labelsize=9)
    ax.grid(axis="y", color=GRIDC, linewidth=0.8)
    ax.set_axisbelow(True)


def main():
    OUT.mkdir(exist_ok=True)
    df, cal, acc_idx = setup()
    acc_n = cal["n"].to_numpy()[acc_idx]

    # ---- 1. votes
    evs, post = run(df, cal, acc_idx)
    v = dt.votes(cal, evs, acc_idx)
    top = acc_n[v == v.max()]

    # ---- 2. Bayes (main run) + explanations
    expl = [dt.explain(cal, ev, post, acc_idx) for ev in evs]
    lo50, hi50 = post.interval(0.5)
    lo95, hi95 = post.interval(0.95)
    eps_mean = float(post.eps @ post.eps_grid)

    rows = []
    for (_, r), x in zip(df.iterrows(), expl):
        best = x["dates"][0] if x["dates"] else {"date": "", "prob": 0, "wrong": ""}
        rows.append({
            "id": r["id"], "year": r["regnal_year"],
            "kielhorn_date": r["kielhorn_date"] or "-", "kielhorn_verdict": r["kielhorn_verdict"],
            "kielhorn_error": r["kielhorn_error_field"] or "-",
            "P(miscarved)": round(x["p_miscarved"], 2),
            "most_likely_date": best["date"], "P(date)": round(best["prob"], 2),
            "wrong_clues_if_so": best["wrong"],
            "alternatives": "; ".join(f"{d['date']} ({d['prob']:.2f}, wrong: {d['wrong']})" for d in x["dates"][1:]),
        })
    ins = pd.DataFrame(rows)
    ins.to_csv(OUT / "detective_inscriptions.csv", index=False)

    # ---- 3. robustness
    variants = [
        ("Main: during-day tithi/nakshatra, structured errors, year error 5%", {}),
        ("Kielhorn's practice: tithi at sunrise, nakshatra any time in the day", {"mode": "kielhorn"}),
        ("Sunrise-only tithi and nakshatra", {"mode": "sunrise"}),
        ("Every wrong value equally likely (no error structure)", {"structured": False}),
        ("Regnal-year error 2%", {"eps_year": 0.02}),
        ("Regnal-year error 10%", {"eps_year": 0.10}),
    ]
    rob = []
    for name, kw in variants:
        e2, p2 = run(df, cal, acc_idx, **kw) if kw else (evs, post)
        flagged = [x["id"] for x in (dt.explain(cal, ev, p2, acc_idx) for ev in e2) if x["p_miscarved"] > 0.5]
        a, b = p2.interval(0.95)
        c, d = p2.interval(0.5)
        rob.append({"assumption": name, "top days (tied)": f"{top_range(p2)[0]} ({top_range(p2)[1]:.0%})",
                    "50% interval": f"{nice(c)} – {nice(d)}", "95% interval": f"{nice(a)} – {nice(b)}",
                    "eps (mean)": round(float(p2.eps @ p2.eps_grid), 3),
                    "log10 Bayes factor vs main": round((p2.log_evidence - post.log_evidence) / np.log(10), 1),
                    "flagged (P>0.5)": ", ".join(i.replace("K3-", "") for i in flagged)})
    rob = pd.DataFrame(rob)

    # ---- 4a. chart: votes
    fig, ax = plt.subplots(figsize=(8, 3))
    years = 1174 + (acc_n - acc_n[0]) / dt.YEAR
    ax.plot(years, v, color=BLUE, linewidth=2, drawstyle="steps-mid")
    ax.set_xlim(years[0], years[-1])
    ax.set_ylim(0, len(evs) + 1)
    ax.set_ylabel("inscriptions explained\nwith no errors", color=MUTED, fontsize=9)
    ax.set_title("Votes: how many of the 24 inscriptions each candidate start date explains",
                 loc="left", fontsize=11, color=INK)
    peak = years[v == v.max()].mean()
    ax.annotate(f"{v.max()} of 24 at {nice(top.min())}–{nice(top.max())}",
                xy=(peak, v.max()), xytext=(peak + 0.6, v.max() + 0.3), fontsize=9, color=INK,
                arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8))
    style(ax)
    fig.tight_layout()
    fig.savefig(OUT / "votes.png", dpi=160)
    plt.close(fig)

    # ---- 4b. chart: posterior, zoomed on mid-1178
    z0, z1 = astro.day_number(1178, 5, 15), astro.day_number(1178, 9, 15)
    sel = (acc_n >= z0) & (acc_n <= z1)
    fig, ax = plt.subplots(figsize=(8, 3.2))
    x = acc_n[sel] - z0
    for (s, e), alpha, label in ((KIELHORN_1903, 0.10, "Kielhorn 1903"), (KIELHORN_1906, 0.25, "Kielhorn 1906")):
        ax.axvspan(astro.day_number(*s) - z0 - 0.5, astro.day_number(*e) - z0 + 0.5,
                   color=ORANGE, alpha=alpha, linewidth=0, label=label)
    ax.bar(x, post.accession[sel], width=0.85, color=BLUE, label="This model: P(start date)")
    ticks = [astro.day_number(1178, m, 1) - z0 for m in (6, 7, 8, 9)]
    ax.set_xticks(ticks, ["1 Jun 1178", "1 Jul", "1 Aug", "1 Sep"])
    ax.set_xlim(-1, z1 - z0 + 1)
    ax.set_ylabel("probability", color=MUTED, fontsize=9)
    ax.set_title(f"Kulottunga III's accession: {top_range(post)[0]}, three equally likely days "
                 f"(95%: {nice(lo95)} – {nice(hi95)})", loc="left", fontsize=11, color=INK)
    ax.legend(frameon=False, fontsize=8, loc="upper right")
    style(ax)
    fig.tight_layout()
    fig.savefig(OUT / "accession.png", dpi=160)
    plt.close(fig)

    # ---- 4c. chart: per-inscription miscarving probability
    order = ins.assign(no=ins["id"].str.replace("K3-", "").astype(int)).sort_values("no")
    colors = {"correct": BLUE, "error": ORANGE, "unresolved": GREY}
    fig, ax = plt.subplots(figsize=(8, 6))
    yy = np.arange(len(order))[::-1]
    ax.barh(yy, order["P(miscarved)"], height=0.7, color=[colors[k] for k in order["kielhorn_verdict"]])
    ax.set_yticks(yy, [f"No. {n}" for n in order["no"]], fontsize=8)
    ax.set_xlim(0, 1)
    ax.set_xlabel("P(miscarved) — this model", color=MUTED, fontsize=9)
    ax.set_title("Which inscriptions were miscarved? Colour = Kielhorn's verdict", loc="left",
                 fontsize=11, color=INK)
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color=BLUE, label="Kielhorn: correct"), Patch(color=ORANGE, label="Kielhorn: error"),
                       Patch(color=GREY, label="Kielhorn: unresolved")], frameon=False, fontsize=8, loc="lower right")
    for y_, (_, r) in zip(yy, order.iterrows()):
        if r["P(miscarved)"] > 0.5:
            ax.text(r["P(miscarved)"] - 0.01, y_, r["wrong_clues_if_so"].replace("_", " "),
                    va="center", ha="right", fontsize=7.5, color="white")
    style(ax)
    ax.grid(axis="x", color=GRIDC, linewidth=0.8)
    ax.grid(axis="y", visible=False)
    fig.tight_layout()
    fig.savefig(OUT / "inscriptions.png", dpi=160)
    plt.close(fig)

    # ---- report
    with open(OUT / "detective.md", "w") as f:
        f.write("# The detective: Kulottunga III's accession\n\n")
        f.write(f"Candidate start dates: every day {nice(acc_n[0])} – {nice(acc_n[-1])} (uniform prior). "
                f"Frame: {astro.get_ayanamsa()}.\n\n")
        f.write("## 1. Votes (interval intersection that tolerates errors)\n\n")
        f.write(f"The best start dates explain **{v.max()} of {len(evs)}** inscriptions with no error: "
                f"**{nice(top.min())} – {nice(top.max())}** (one unbroken run). "
                f"Kielhorn (EI VIII, 1906): about 6–8 July 1178.\n\n![votes](votes.png)\n\n")
        f.write("## 2. Bayesian model\n\n")
        f.write(f"- Top days: **{top_range(post)[0]}**, equally likely (each about a quarter, "
                f"{top_range(post)[1]:.0%} together); the evidence cannot separate them\n")
        f.write(f"- 50% credible interval: **{nice(lo50)} – {nice(hi50)}**\n")
        f.write(f"- 95% credible interval: **{nice(lo95)} – {nice(hi95)}**\n")
        f.write(f"- Estimated error rate per carved clue: **{eps_mean:.3f}** (about 1 in {round(1/eps_mean)})\n\n")
        f.write("![accession](accession.png)\n\n![inscriptions](inscriptions.png)\n\n")
        f.write("### Per inscription\n\n" + ins.to_markdown(index=False) + "\n\n")
        f.write("## 3. Robustness\n\n" + rob.to_markdown(index=False) + "\n")
    print(open(OUT / "detective.md").read())


if __name__ == "__main__":
    main()
