"""
chola-dates demo app.

    streamlit run streamlit_app.py

Tabs:
  Solve      enter an inscription's clues, get every matching day (live solver)
  Detective  the accession model for Kulottunga III, with Kielhorn for comparison
  Map        where the inscriptions are, through the king's reign
  Sky        the sun, moon, tithi and nakshatra on any medieval day
  Method     how it works, in brief
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd
import streamlit as st

from app import visuals as v
from chola import astro, dataset, detective as dt, panchang as p
from chola.search import find_matches

st.set_page_config(page_title="chola-dates", page_icon="🛕", layout="wide")

ERA = ((1170, 1, 1), (1230, 12, 31))          # calendar range the demo pre-computes
GRID = ((1176, 1, 1), (1180, 12, 31))         # candidate accession days for the detective
K1903 = ((1178, 6, 8), (1178, 7, 8))
K1906 = ((1178, 7, 6), (1178, 7, 8))
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# ------------------------------------------------------------------ style

st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&family=Space+Grotesk:wght@400;600&display=swap" rel="stylesheet">
<style>
html, body, [class*="css"], .stMarkdown, .stText { font-family: 'Space Grotesk', sans-serif; }
code, .mono { font-family: 'JetBrains Mono', monospace !important; }
.block-container { padding-top: 1.6rem; max-width: 1250px; }
.kicker { font-family: 'JetBrains Mono', monospace; color: #4fd1e8; letter-spacing: .18em; font-size: .78rem; }
.title { font-size: 3.1rem; font-weight: 600; line-height: 1.05; margin: .3rem 0 .6rem; color: #e6e4dc; }
.title span { color: #e8b04a; }
.lede { color: #b9b7ae; font-size: 1.05rem; max-width: 38rem; }
.chips { display: flex; flex-wrap: wrap; gap: .6rem; margin-top: 1.2rem; }
.chip { border: 1px solid rgba(232,176,74,.45); border-radius: 6px; padding: .55rem .8rem; min-width: 9.5rem; background: rgba(18,24,34,.7); }
.chip b { display: block; font-family: 'JetBrains Mono', monospace; color: #e8b04a; font-size: 1.15rem; }
.chip small { color: #9a998f; font-size: .76rem; }
.panel { border: 1px solid rgba(79,209,232,.25); border-radius: 8px; padding: .9rem 1rem; background: rgba(18,24,34,.6); font-family: 'JetBrains Mono', monospace; font-size: .86rem; line-height: 1.75; }
.panel .k { color: #9a998f; } .panel .v { color: #e6e4dc; } .panel .hl { color: #e8b04a; }
.note { color: #9a998f; font-size: .85rem; }
div[data-baseweb="tab-list"] button p { font-family: 'JetBrains Mono', monospace; letter-spacing: .06em; }
</style>
""", unsafe_allow_html=True)


# ------------------------------------------------------------------ data (cached)

@st.cache_resource(show_spinner="Computing 60 years of sunrises, tithis and nakshatras over Thanjavur…")
def era_calendar():
    n0, n1 = (astro.day_number(*d) for d in ERA)
    return p.build_calendar(n0, n1)


@st.cache_data
def inscriptions():
    df = dataset.load("kulottunga3")
    places = pd.read_csv(ROOT / "data" / "places.csv")
    df["place_key"] = df["place"].str.split(",").str[0].str.strip()
    return df.merge(places, left_on="place_key", right_on="place", how="left", suffixes=("", "_p")), places


@st.cache_data(show_spinner="Running the detective…")
def detective(mode: str):
    cal = era_calendar()
    df = dataset.load("kulottunga3")
    a0, a1 = (astro.day_number(*d) for d in GRID)
    acc_idx = np.arange(a0, a1 + 1) - cal["n"].iat[0]
    evs = [dt.evidence(cal, r, mode=mode) for _, r in df.iterrows()]
    post = dt.fit(cal, evs, acc_idx)
    votes = dt.votes(cal, evs, acc_idx)
    expl = [dt.explain(cal, ev, post, acc_idx) for ev in evs]
    rows = []
    for (_, r), x in zip(df.iterrows(), expl):
        best = x["dates"][0] if x["dates"] else {"date": "", "prob": 0.0, "wrong": ""}
        rows.append({"no": int(r["ei_no"]), "id": r["id"], "year": r["regnal_year"], "verdict": r["kielhorn_verdict"],
                     "kielhorn_date": r["kielhorn_date"] or "–", "kielhorn_error": r["kielhorn_error_field"] or "–",
                     "p": round(x["p_miscarved"], 3), "date": best["date"], "p_date": round(best["prob"], 2),
                     "wrong": best["wrong"]})
    lo50, hi50 = post.interval(0.5)
    lo95, hi95 = post.interval(0.95)
    return {"acc_n": post.acc_n, "acc_p": post.accession, "votes": votes, "mode": post.mode(),
            "i50": (lo50, hi50), "i95": (lo95, hi95), "eps": float(post.eps @ post.eps_grid),
            "log_ev": post.log_evidence, "table": pd.DataFrame(rows).sort_values("no")}


def jdate(n):
    """Julian day number -> pandas Timestamp (proleptic Gregorian, for plotting only)."""
    y, m, d = astro.date_from_day_number(int(n), "gregorian")
    return pd.Timestamp(year=y, month=m, day=d)


def nice(n):
    y, m, d = astro.date_from_day_number(int(n))
    return f"{d} {MONTHS[m-1]} {y}"


def panel(rows):
    html = "".join(f'<span class="k">{k:<22}</span> <span class="{cls}">{val}</span><br>'
                   for k, val, cls in rows)
    st.markdown(f'<div class="panel">{html}</div>', unsafe_allow_html=True)


def day_panel(n):
    d = p.describe_day(n)
    ch_t = ", ".join(f"{t} from +{h:.1f} h" for t, h in d["tithi_changes"]) or "none"
    ch_n = ", ".join(f"{t} from +{h:.1f} h" for t, h in d["nakshatra_changes"]) or "none"
    panel([("date (Julian)", d["date"].split(" ")[0], "hl"), ("weekday", d["weekday"], "v"),
           ("sunrise, Thanjavur", d["sunrise_local"] + " local mean time", "v"),
           ("solar month", f'{d["sign_at_sunset"]} ({p.TAMIL_MONTHS[p.SIGNS.index(d["sign_at_sunset"])]})', "v"),
           ("tithi at sunrise", d["tithi_at_sunrise"], "hl"), ("  later that day", ch_t, "v"),
           ("nakshatra at sunrise", d["nakshatra_at_sunrise"], "hl"), ("  later that day", ch_n, "v")])
    return d


# ------------------------------------------------------------------ hero

det = detective("day")
left, right = st.columns([1.35, 1])
with left:
    st.markdown('<div class="kicker">24-HOUR BUILD · ARCHAEOASTRONOMY · BAYESIAN INFERENCE</div>', unsafe_allow_html=True)
    st.markdown('<div class="title">Dating the <span>Chola kings</span><br>from the sky</div>', unsafe_allow_html=True)
    st.markdown('<div class="lede">Medieval Tamil temple inscriptions date themselves with the sun, the moon and the '
                'weekday instead of a calendar year. This app solves those clues against a modern ephemeris, then '
                'infers when Kulottunga III began his reign while working out which inscriptions were miscarved.</div>',
                unsafe_allow_html=True)
    st.markdown(f"""<div class="chips">
      <div class="chip"><b>{nice(det['mode'])}</b><small>most likely accession</small></div>
      <div class="chip"><b>14 / 14</b><small>Kielhorn's correct dates reproduced</small></div>
      <div class="chip"><b>5 / 5</b><small>his error diagnoses matched</small></div>
      <div class="chip"><b>10^6.4</b><small>evidence for the "later in the day" convention</small></div>
    </div>""", unsafe_allow_html=True)
with right:
    st.markdown(v.vimana_svg(), unsafe_allow_html=True)

st.write("")
tab_solve, tab_det, tab_map, tab_sky, tab_how = st.tabs(["SOLVE", "DETECTIVE", "MAP", "SKY", "METHOD"])

# ------------------------------------------------------------------ SOLVE

with tab_solve:
    df, places = inscriptions()
    st.markdown("#### Enter an inscription's clues")
    st.markdown('<span class="note">Leave any clue blank if the inscription does not give it. '
                'Pick one of the 24 real inscriptions to load its clues as carved.</span>', unsafe_allow_html=True)

    presets = ["Custom"] + [f"No. {r.ei_no} · year {r.regnal_year} · {r.place}" for r in df.itertuples()]

    def load_preset():
        sel = st.session_state["preset"]
        if sel == "Custom":
            return
        r = df.iloc[presets.index(sel) - 1]
        st.session_state.update({
            "month": r["solar_month"] or "—", "sday": int(r["solar_day"] or 0),
            "paksha": r["paksha"] or "—", "tithi": int(r["tithi"] or 0),
            "nak": r["nakshatra"] or "—", "wday": r["weekday"] or "—"})

    st.selectbox("Load an inscription", presets, key="preset", on_change=load_preset)
    c1, c2, c3 = st.columns(3)
    c1.selectbox("Solar month", ["—"] + p.SIGNS, key="month",
                 format_func=lambda s: s if s == "—" else f"{s} · {p.TAMIL_MONTHS[p.SIGNS.index(s)]}")
    c1.number_input("Day of solar month (0 = not given)", 0, 32, key="sday")
    c2.selectbox("Paksha (fortnight)", ["—", "shukla", "krishna"], key="paksha",
                 format_func=lambda s: {"—": "—", "shukla": "shukla · bright, waxing", "krishna": "krishna · dark, waning"}[s])
    c2.number_input("Tithi (1–15, 0 = not given)", 0, 15, key="tithi")
    c3.selectbox("Nakshatra", ["—"] + p.NAKSHATRAS, key="nak")
    c3.selectbox("Weekday", ["—"] + p.WEEKDAYS, key="wday")

    c4, c5, c6 = st.columns(3)
    years = c4.slider("Search years (Julian)", ERA[0][0], ERA[1][0], (1176, 1222))
    mode = c5.radio("Tithi / nakshatra must be current…", ["during the day", "at sunrise"], horizontal=True)
    mism = c6.radio("Allow wrong clues", [0, 1, 2], horizontal=True,
                    help="1 = also show days where every clue but one fits: candidate carving errors")

    clues = {"solar_month": st.session_state.month if st.session_state.month != "—" else "",
             "solar_day": st.session_state.sday or "", "paksha": st.session_state.paksha if st.session_state.paksha != "—" else "",
             "tithi": st.session_state.tithi or "", "nakshatra": st.session_state.nak if st.session_state.nak != "—" else "",
             "weekday": st.session_state.wday if st.session_state.wday != "—" else ""}
    given = {k: x for k, x in clues.items() if x}
    if not given:
        st.info("Add at least one clue.")
    else:
        cal = era_calendar()
        n0, n1 = astro.day_number(years[0], 1, 1), astro.day_number(years[1], 12, 31)
        sub = cal[(cal["n"] >= n0) & (cal["n"] <= n1)]
        hits = find_matches(sub, given, mode="day" if mode == "during the day" else "sunrise", max_mismatches=mism)
        exact = int((hits["n_mismatch"] == 0).sum())
        st.markdown(f"**{exact}** exact match{'es' if exact != 1 else ''} in {years[0]}–{years[1]}"
                    + (f", **{len(hits) - exact}** with {mism} wrong clue(s)" if mism else ""))
        if len(hits):
            left_r, right_r = st.columns([1, 1.25])
            with left_r:
                show = hits.rename(columns={"date": "date (Julian)", "n_mismatch": "wrong clues", "failed": "which"})
                show["which"] = show["which"].replace("", "–")
                st.dataframe(show[["date (Julian)", "wrong clues", "which"]], hide_index=True, height=330,
                             width="stretch")
                pick = st.selectbox("Inspect a day", hits["date"].tolist()[:200])
            with right_r:
                n = int(hits.loc[hits["date"] == pick, "n"].iloc[0])
                d = day_panel(n)
                rise = astro.sunrise(n)
                st.plotly_chart(v.sky_dial(astro.sun_longitude(rise), astro.moon_longitude(rise), height=360),
                                width="stretch")

# ------------------------------------------------------------------ DETECTIVE

with tab_det:
    conv = st.radio("Reading of the tithi", ["Current at any time during the day (this project)",
                                             "Must be current at sunrise (Kielhorn's practice)"], horizontal=True)
    D = detective("day" if conv.startswith("Current") else "kielhorn")
    bf = (det["log_ev"] - detective("kielhorn")["log_ev"]) / np.log(10)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Most likely accession", nice(D["mode"]))
    m2.metric("50% interval", f"{nice(D['i50'][0])[:-5]} – {nice(D['i50'][1])}")
    m3.metric("95% interval", f"{nice(D['i95'][0])[:-5]} – {nice(D['i95'][1])}")
    m4.metric("Error rate per carved clue", f"{D['eps']:.3f}", help="Estimated from the data: about 1 clue in "
              f"{round(1 / D['eps'])} is wrong")
    if not conv.startswith("Current"):
        st.warning(f"Under Kielhorn's practice the data are 10^{bf:.1f} times less probable, the model needs more "
                   "errors, and the accession widens to his earlier (1903) window.")

    zoom = (D["acc_n"] >= astro.day_number(1178, 5, 15)) & (D["acc_n"] <= astro.day_number(1178, 9, 15))
    x = [jdate(n) for n in D["acc_n"][zoom]]
    k3 = tuple(jdate(astro.day_number(*d)) for d in K1903)
    k6 = tuple(jdate(astro.day_number(*d)) for d in K1906)
    st.markdown("#### When did the reign begin?")
    st.plotly_chart(v.accession_chart(x, D["acc_p"][zoom], k3, k6), width="stretch")
    st.markdown('<span class="note">Dates on this chart\'s axis are drawn on the modern (Gregorian) scale, '
                '7 days ahead of the Julian dates quoted elsewhere.</span>', unsafe_allow_html=True)

    a, b = st.columns([1, 1.1])
    with a:
        st.markdown("#### Votes: start dates that explain the most inscriptions")
        st.plotly_chart(v.votes_chart([jdate(n) for n in D["acc_n"]], D["votes"], 24), width="stretch")
        st.markdown('<span class="note">Each candidate start date scores one point per inscription it explains with '
                    'no errors at all. The peak is the simple answer; the Bayesian model refines it.</span>',
                    unsafe_allow_html=True)
    with b:
        st.markdown("#### Which inscriptions were miscarved?")
        st.plotly_chart(v.miscarve_chart(D["table"]), width="stretch")
    st.markdown("#### Every inscription")
    st.dataframe(D["table"].rename(columns={"p": "P(miscarved)", "date": "model's most likely date",
                                            "p_date": "P(that date)", "wrong": "wrong clues on that date"})
                 .drop(columns=["id"]), hide_index=True, width="stretch")

# ------------------------------------------------------------------ MAP

with tab_map:
    df, places = inscriptions()
    st.markdown("#### Kulottunga III's inscriptions across the Chola country")
    yr = st.slider("Regnal year", 1, 39, 39)
    acc = astro.day_number(1178, 7, 6)
    c_y = astro.date_from_day_number(acc + round((yr - 1) * dt.YEAR))[0]
    D = detective("day")
    pm = dict(zip(D["table"]["id"], D["table"]["p"]))
    shown = df[df["regnal_year"] <= yr].copy()
    shown["label"] = [f"No. {r.ei_no} · year {r.regnal_year} · {r.place}<br>Kielhorn: {r.kielhorn_date or 'unresolved'}"
                      f" · P(miscarved) {pm[r.id]:.2f}" for r in shown.itertuples()]
    now = df[df["regnal_year"] == yr]
    a, b = st.columns([2.2, 1])
    with a:
        st.plotly_chart(v.sites_map(places, shown, set(now["id"])), width="stretch")
    with b:
        st.markdown(f'<div class="kicker">YEAR {yr} · FROM JULY {c_y}</div>', unsafe_allow_html=True)
        if len(now):
            for r in now.itertuples():
                status = "miscarved" if pm[r.id] > 0.5 else "clean"
                panel([("inscription", f"No. {r.ei_no}", "hl"), ("place", r.place, "v"),
                       ("date (Kielhorn)", r.kielhorn_date or "unresolved", "v"),
                       ("model says", f"{status} (P = {pm[r.id]:.2f})", "hl")])
                st.write("")
        else:
            st.markdown('<span class="note">No dated inscription from this year in the dataset.</span>',
                        unsafe_allow_html=True)
        st.markdown(f'<span class="note">{len(shown)} of 24 inscriptions dated up to year {yr}. '
                    'Site positions are approximate (village level); the dataset gives temple and village names only.</span>',
                    unsafe_allow_html=True)

# ------------------------------------------------------------------ SKY

with tab_sky:
    st.markdown("#### The sky over Thanjavur at sunrise")
    a, b, c = st.columns(3)
    y = a.number_input("Year (Julian calendar)", ERA[0][0], ERA[1][0], 1192)
    m = b.number_input("Month", 1, 12, 1)
    d = c.number_input("Day", 1, 31, 2)
    try:
        n = astro.day_number(int(y), int(m), int(d))
        left_s, right_s = st.columns([1, 1.25])
        with left_s:
            day_panel(n)
            st.markdown('<span class="note">The arc from the sun to the moon is the elongation: each 12° is one '
                        'tithi. The highlighted segment is the nakshatra the moon is in. The 12 labels are the '
                        'solar months, the sun\'s position against the stars.</span>', unsafe_allow_html=True)
        with right_s:
            rise = astro.sunrise(n)
            st.plotly_chart(v.sky_dial(astro.sun_longitude(rise), astro.moon_longitude(rise)), width="stretch")
    except Exception as e:  # e.g. 31 February
        st.error(f"Not a valid date: {e}")

# ------------------------------------------------------------------ METHOD

with tab_how:
    st.markdown("""
#### How it works

**1 · Solver.** For each day, the Swiss Ephemeris gives the sun's and moon's positions at sunrise over Thanjavur.
From those: the solar month (the sun's sign against the stars), the tithi (the moon's lead over the sun, in 12° steps),
the nakshatra (the moon's position, in 27 steps) and the weekday. Dates before 1582 use the Julian calendar.
The star frame is calibrated to Kielhorn's own published sankranti times (1.69° ± 0.14° from modern Lahiri).

**2 · Dataset.** All 24 dated inscriptions of Kulottunga III examined by F. Kielhorn in *Epigraphia Indica*
IV–VIII (1896–1906), with every clue as carved and his verdict. The solver reproduces all 14 dates he judged correct,
each as the only matching day in its regnal year.

**3 · Detective.** For every candidate start date, each inscription's true date is some day of its regnal year, and
each clue was carved correctly or wrongly with an unknown error rate (wrong values follow realistic patterns: the other
fortnight, a neighbouring tithi, a slipped digit). The model returns the start date with uncertainty, the error rate,
and each inscription's probability of being miscarved.

**Result.** 6 July 1178 (50%: 6–8 July), matching Kielhorn's 1906 conclusion. The model flags exactly his five genuine
errors, with the same diagnosis each time, and shows that four more "errors" are better read as the tithi current later
that day (Bayes factor 10^6.4).

Source code, data and tests: [github.com/sanjayashokbuilds/chola-dates](https://github.com/sanjayashokbuilds/chola-dates)
""")
