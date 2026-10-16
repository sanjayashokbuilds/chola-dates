"""
chola-dates: demo app.

    streamlit run streamlit_app.py

Written for someone who has never heard of any of this:
  THE STORY     a guided walk through one real inscription, then the whole reign
  TRY IT        pick any of the 24 inscriptions (or type your own clues) and solve it live
  THE VERDICT   when Kulottunga III's reign began, and which carvings were wrong
  MAP           where the inscriptions are, year by year through the reign
  SKY           the sun, moon, tithi and nakshatra over Thanjavur on any day
  HOW IT WORKS  the method, a glossary and the sources
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
from chola.search import check_clues, find_matches

st.set_page_config(page_title="Dating the Chola kings from the sky", page_icon="🛕", layout="wide")

ERA = ((1170, 1, 1), (1230, 12, 31))      # days the app pre-computes
GRID = ((1176, 1, 1), (1180, 12, 31))     # candidate start dates for the verdict
ACCESSION = (1178, 7, 6)                  # the model's answer, used to place regnal years
K1903, K1906 = ((1178, 6, 8), (1178, 7, 8)), ((1178, 7, 6), (1178, 7, 8))
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
REPO = "https://github.com/sanjayashokbuilds/chola-dates"
GLYPH = {"regnal_year": "♛", "solar_month": "☉", "tithi": "☾", "paksha": "☾", "nakshatra": "✦",
         "weekday": "◷", "solar_day": "☉"}

# ------------------------------------------------------------------ style

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&family=Space+Grotesk:wght@400;500;600;700&display=swap');
html, body, .stApp, .stMarkdown, p, li, label, .stRadio, .stSelectbox { font-family: 'Space Grotesk', sans-serif !important; }
h1, h2, h3, h4 { font-family: 'Space Grotesk', sans-serif !important; letter-spacing: -0.01em; }
code, .mono { font-family: 'JetBrains Mono', monospace !important; }
#MainMenu, footer { visibility: hidden; }
.block-container { padding-top: 1.4rem; max-width: 1180px; }

.kicker { font-family: 'JetBrains Mono', monospace; color: #4fd1e8; letter-spacing: .16em; font-size: .74rem; text-transform: uppercase; }
.title { font-size: 3.2rem; font-weight: 700; line-height: 1.04; margin: .35rem 0 .8rem; color: #f1efe7; }
.title span { color: #e8b04a; }
.lede { color: #c3c1b8; font-size: 1.12rem; line-height: 1.6; max-width: 36rem; }
.cta { margin-top: 1.1rem; color: #e8b04a; font-family: 'JetBrains Mono', monospace; font-size: .85rem; }

.chips { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: .7rem; margin-top: 1.4rem; max-width: 36rem; }
.chip { border: 1px solid rgba(232,176,74,.35); border-radius: 10px; padding: .75rem .9rem; background: rgba(18,24,34,.75); }
.chip b { display: block; font-family: 'JetBrains Mono', monospace; color: #e8b04a; font-size: 1.15rem; margin-bottom: .15rem; }
.chip small { color: #a9a79e; font-size: .82rem; line-height: 1.35; display: block; }

.card { border: 1px solid rgba(79,209,232,.22); border-radius: 12px; padding: 1.1rem 1.2rem; background: rgba(18,24,34,.72); margin-bottom: .8rem; }
.card h4 { margin: 0 0 .35rem; color: #f1efe7; font-size: 1.05rem; }
.card p { margin: 0; color: #c3c1b8; line-height: 1.55; }
.card .big { font-family: 'JetBrains Mono', monospace; color: #e8b04a; font-size: 1.5rem; margin: .2rem 0 .3rem; }
.card.gold { border-color: rgba(232,176,74,.55); }
.card.warn { border-color: rgba(217,89,38,.6); }

.stone { border-radius: 12px; padding: 1.4rem 1.5rem; background: linear-gradient(180deg, #2a2723, #1d1b18);
         border: 1px solid #4a4439; box-shadow: inset 0 0 40px rgba(0,0,0,.45); }
.stone .orig { font-family: 'JetBrains Mono', monospace; color: #d8cfbd; font-size: .9rem; line-height: 1.8; letter-spacing: .02em; }
.stone .tr { color: #f1efe7; font-size: 1.1rem; line-height: 1.6; margin-top: .9rem; font-style: italic; }
.stone .src { color: #8f887a; font-size: .78rem; margin-top: .8rem; font-family: 'JetBrains Mono', monospace; }
mark.c { background: rgba(232,176,74,.18); color: #e8b04a; padding: 0 .15rem; border-radius: 3px; font-style: normal; }

.clue { border: 1px solid rgba(232,176,74,.3); border-radius: 12px; padding: .9rem 1rem; background: rgba(18,24,34,.75); height: 100%; }
.clue .g { font-size: 1.6rem; color: #e8b04a; line-height: 1; }
.clue .n { font-family: 'JetBrains Mono', monospace; color: #4fd1e8; font-size: .72rem; letter-spacing: .12em; text-transform: uppercase; margin: .45rem 0 .2rem; }
.clue .v { color: #f1efe7; font-weight: 600; margin-bottom: .25rem; }
.clue .m { color: #b3b1a8; font-size: .88rem; line-height: 1.45; }

table.check { width: 100%; border-collapse: collapse; font-family: 'JetBrains Mono', monospace; font-size: .86rem; }
table.check th { text-align: left; color: #9a998f; font-weight: 400; border-bottom: 1px solid rgba(230,228,220,.12); padding: .45rem .5rem; }
table.check td { padding: .5rem; border-bottom: 1px solid rgba(230,228,220,.06); color: #e6e4dc; }
table.check td.ok { color: #4fd1e8; } table.check td.no { color: #d95926; }
table.check tr.win td { background: rgba(232,176,74,.08); }

.panel { border: 1px solid rgba(79,209,232,.22); border-radius: 12px; padding: .9rem 1.1rem; background: rgba(18,24,34,.7);
         font-family: 'JetBrains Mono', monospace; font-size: .84rem; line-height: 1.8; }
.panel .k { color: #9a998f; display: inline-block; min-width: 11rem; } .panel .v { color: #e6e4dc; } .panel .hl { color: #e8b04a; }
.note { color: #a3a198; font-size: .9rem; line-height: 1.55; }
.dots { font-family: 'JetBrains Mono', monospace; color: #6d6b64; letter-spacing: .3em; }
.dots b { color: #e8b04a; }
.foot { margin-top: 3rem; padding-top: 1.2rem; border-top: 1px solid rgba(230,228,220,.08); color: #8a887f; font-size: .85rem; }
.foot a { color: #e8b04a; text-decoration: none; }
[data-testid="stMetricValue"] { font-family: 'JetBrains Mono', monospace !important; font-size: 1.55rem !important; color: #e8b04a; }
div[data-baseweb="tab-list"] { gap: .4rem; }
div[data-baseweb="tab-list"] button p { font-family: 'JetBrains Mono', monospace !important; letter-spacing: .08em; font-size: .84rem; }
</style>
""", unsafe_allow_html=True)


# ------------------------------------------------------------------ data (cached)

@st.cache_resource(show_spinner="Computing 60 years of sunrises, moons and stars over Thanjavur…")
def era_calendar():
    n0, n1 = (astro.day_number(*d) for d in ERA)
    return p.build_calendar(n0, n1)


@st.cache_data
def inscriptions():
    df = dataset.load("kulottunga3")
    places = pd.read_csv(ROOT / "data" / "places.csv")
    df["place_key"] = df["place"].str.split(",").str[0].str.strip()
    df = df.merge(places, left_on="place_key", right_on="place", how="left", suffixes=("", "_p"))
    return df, places


@st.cache_data(show_spinner="Weighing all 24 inscriptions…")
def verdict(mode: str = "day"):
    cal = era_calendar()
    df = dataset.load("kulottunga3")
    a0, a1 = (astro.day_number(*d) for d in GRID)
    acc_idx = np.arange(a0, a1 + 1) - cal["n"].iat[0]
    evs = [dt.evidence(cal, r, mode=mode) for _, r in df.iterrows()]
    post = dt.fit(cal, evs, acc_idx)
    votes = dt.votes(cal, evs, acc_idx)
    rows, alts = [], {}
    for (_, r), ev in zip(df.iterrows(), evs):
        x = dt.explain(cal, ev, post, acc_idx)
        alts[r["id"]] = x["dates"]
        best = x["dates"][0] if x["dates"] else {"date": "", "prob": 0.0, "wrong": ""}
        rows.append({"no": int(r["ei_no"]), "id": r["id"], "year": r["regnal_year"], "place": r["place"],
                     "verdict": r["kielhorn_verdict"], "kielhorn_date": r["kielhorn_date"] or "–",
                     "p": round(x["p_miscarved"], 3), "date": best["date"], "p_date": round(best["prob"], 2),
                     "wrong": best["wrong"]})
    return {"acc_n": post.acc_n, "acc_p": post.accession, "votes": votes, "top": post.top_days(),
            "i50": post.interval(0.5), "i95": post.interval(0.95), "eps": float(post.eps @ post.eps_grid),
            "log_ev": post.log_evidence, "table": pd.DataFrame(rows).sort_values("no"), "alts": alts}


# ------------------------------------------------------------------ helpers

def ymd(n):
    return astro.date_from_day_number(int(n))


def nice(n, weekday=False):
    y, m, d = ymd(n)
    s = f"{d} {MONTHS[m-1]} {y}"
    return f"{p.WEEKDAYS[astro.weekday(int(n))]} {s}" if weekday else s


def iso_to_n(iso):
    return dataset.day_number_of(iso)


def short_range(a, b):
    ya, ma, da = ymd(a)
    yb, mb, db = ymd(b)
    if (ya, ma) == (yb, mb):
        return f"{da}–{db} {MONTHS[ma-1]}"
    return f"{da} {MONTHS[ma-1]} – {db} {MONTHS[mb-1]}"


def top_label(D):
    """'6–8 Jul 1178': the run of days tied for the highest probability."""
    a, b, _ = D["top"]
    return f"{short_range(a, b)} {ymd(b)[0]}" if a != b else nice(a)


def jdate(n):
    """Julian date as a Timestamp for chart axes (Julian/Gregorian leap years agree 1101–1299)."""
    y, m, d = ymd(n)
    return pd.Timestamp(year=y, month=m, day=d)


def card(title, body, big=None, kind=""):
    big_html = f'<div class="big">{big}</div>' if big else ""
    st.markdown(f'<div class="card {kind}"><h4>{title}</h4>{big_html}<p>{body}</p></div>', unsafe_allow_html=True)


def ordinal(k):
    return f"{k}{'th' if 10 <= k % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(k % 10, 'th')}"


def plain_clue(name, row):
    """(value as carved, what it means in plain English) for one clue of an inscription."""
    if name == "regnal_year":
        return f"{ordinal(int(row['regnal_year']))} year of the reign", "Counted from the day the king took the throne. This is what we want to pin down."
    if name == "solar_month":
        s = row["solar_month"]
        return f"Month of {s}", f"The sun was in the {s} part of the sky, the Tamil month of {p.TAMIL_MONTHS[p.SIGNS.index(s)]}."
    if name == "solar_day":
        return f"Day {row['solar_day']} of the month", "Days counted since the sun entered that part of the sky."
    if name == "tithi":
        k = int(row["tithi"])
        if row["paksha"] == "shukla":
            return f"{ordinal(k)} tithi, bright fortnight", f"The {ordinal(k)} lunar day after the new moon, while the moon was growing."
        if row["paksha"] == "krishna":
            return f"{ordinal(k)} tithi, dark fortnight", f"The {ordinal(k)} lunar day after the full moon, while the moon was shrinking."
        return f"{ordinal(k)} tithi", "A lunar day; the fortnight is not stated."
    if name == "nakshatra":
        return row["nakshatra"], f"The moon was passing in front of the {row['nakshatra']} group of stars (one of 27)."
    if name == "weekday":
        return row["weekday"], "The same seven-day week we use today."
    return "", ""


def clue_cards(row):
    names = ["regnal_year"] + [k for k in ("solar_month", "solar_day", "tithi", "nakshatra", "weekday") if row[k] != ""]
    cols = st.columns(len(names))
    for c, nm in zip(cols, names):
        val, mean = plain_clue(nm, row)
        label = {"regnal_year": "king's year", "solar_month": "sun", "solar_day": "sun", "tithi": "moon phase",
                 "nakshatra": "moon & stars", "weekday": "weekday"}[nm]
        c.markdown(f'<div class="clue"><div class="g">{GLYPH[nm]}</div><div class="n">{label}</div>'
                   f'<div class="v">{val}</div><div class="m">{mean}</div></div>', unsafe_allow_html=True)


def checklist(cal_rows, clues, mode="day", highlight=None):
    """HTML table: one row per day, a tick or cross per clue."""
    res = check_clues(cal_rows, clues, mode=mode)
    cols = [c for c in res.columns if c not in ("n", "date", "n_mismatch")]
    head = "".join(f"<th>{GLYPH.get(c, '')} {c.replace('_', ' ')}</th>" for c in cols)
    body = []
    for _, r in res.iterrows():
        cls = ' class="win"' if highlight and r["n"] in highlight else ""
        cells = "".join(f'<td class="{"ok" if r[c] else "no"}">{"✓" if r[c] else "✗"}</td>' for c in cols)
        body.append(f"<tr{cls}><td>{nice(r['n'], weekday=True)}</td>{cells}</tr>")
    st.markdown(f'<table class="check"><tr><th>day</th>{head}</tr>{"".join(body)}</table>', unsafe_allow_html=True)


def day_panel(n):
    d = p.describe_day(n)
    later_t = ", ".join(f"{t} from {h:.1f} h after sunrise" for t, h in d["tithi_changes"]) or "none"
    later_n = ", ".join(f"{t} from {h:.1f} h after sunrise" for t, h in d["nakshatra_changes"]) or "none"
    rows = [("date (Julian)", nice(n, weekday=True), "hl"),
            ("sunrise at Thanjavur", d["sunrise_local"] + " local time", "v"),
            ("sun's month", f'{d["sign_at_sunset"]} · {p.TAMIL_MONTHS[p.SIGNS.index(d["sign_at_sunset"])]}', "v"),
            ("moon phase at sunrise", d["tithi_at_sunrise"], "hl"), ("…changes to", later_t, "v"),
            ("moon's stars at sunrise", d["nakshatra_at_sunrise"], "hl"), ("…changes to", later_n, "v")]
    html = "".join(f'<span class="k">{k}</span><span class="{c}">{val}</span><br>' for k, val, c in rows)
    st.markdown(f'<div class="panel">{html}</div>', unsafe_allow_html=True)


def sky(n, height=380):
    rise = astro.sunrise(n)
    st.plotly_chart(v.sky_dial(astro.sun_longitude(rise), astro.moon_longitude(rise), height=height),
                    width="stretch", config={"displayModeBar": False})


def regnal_window(year):
    acc = astro.day_number(*ACCESSION)
    return dataset.regnal_year_window(acc, int(year), pad_days=3)


# ------------------------------------------------------------------ hero

det = verdict("day")
df_all, places_all = inscriptions()
no60 = df_all[df_all["ei_no"] == "60"].iloc[0]

left, right = st.columns([1.3, 1], gap="large")
with left:
    st.markdown('<div class="kicker">A 900-year-old date puzzle</div>', unsafe_allow_html=True)
    st.markdown('<div class="title">Dating the <span>Chola kings</span><br>from the sky</div>', unsafe_allow_html=True)
    st.markdown('<div class="lede">The temples of medieval South India record their gifts and grants in stone, '
                'but they never give a year. Instead they describe the sky: the month, the phase of the moon, the stars '
                'it was passing, the day of the week. This app recomputes the sky over Thanjavur for every day of the '
                '12th and 13th centuries to turn those clues back into dates, and works out when King Kulottunga III '
                'took the throne, even though some of the stone carvers made mistakes.</div>', unsafe_allow_html=True)
    st.markdown(f"""<div class="chips">
      <div class="chip"><b>{top_label(det)}</b><small>when Kulottunga III became king: three equally likely days</small></div>
      <div class="chip"><b>24 stones</b><small>dated inscriptions decoded, from Nellore to Vedaranyam</small></div>
      <div class="chip"><b>5 mistakes</b><small>found in the carvings: the same five a scholar found by hand in 1900</small></div>
      <div class="chip"><b>4 that weren't</b><small>old "mistakes" that turn out to follow a consistent rule</small></div>
    </div>""", unsafe_allow_html=True)
    st.markdown('<div class="cta">New here? Start with THE STORY below ↓</div>', unsafe_allow_html=True)
with right:
    st.markdown(v.vimana_svg(), unsafe_allow_html=True)

st.write("")
t_story, t_try, t_verdict, t_map, t_sky, t_how = st.tabs(
    ["THE STORY", "TRY IT", "THE VERDICT", "MAP", "SKY", "HOW IT WORKS"])

# ------------------------------------------------------------------ THE STORY

STEPS = ["A message in stone", "Five clues", "Checking the sky", "A slip of the chisel",
         "From one stone to a king", "What's new"]
st.session_state.setdefault("step", 0)


def go(k):
    st.session_state.step = max(0, min(len(STEPS) - 1, k))


with t_story:
    s = st.session_state.step
    dots = "".join("<b>●</b>" if i == s else "○" for i in range(len(STEPS)))
    st.markdown(f'<div class="kicker">Step {s + 1} of {len(STEPS)}</div>'
                f'<h2 style="margin:.2rem 0 .2rem">{STEPS[s]}</h2><div class="dots">{dots}</div>',
                unsafe_allow_html=True)
    st.write("")
    cal = era_calendar()
    lo, hi = regnal_window(14)
    yr14 = cal[(cal["n"] >= lo) & (cal["n"] <= hi)]

    if s == 0:
        a, b = st.columns([1.25, 1], gap="large")
        with a:
            st.markdown("""<div class="stone">
              <div class="orig">… Tribhuvanachchakravarttigaḷ Maduraiyum Îlamuṅ goṇḍaruḷina śrī-Kulôttuṅga-Śôḷadêvarku
              yâṇḍu 14âvadu Magara-nâyarru pûrvva-pakshattu Viyâḷa-kkiḻamaiyum Pûśamum prathamaiyum ânav anru …</div>
              <div class="tr">"In the <mark class="c">14th year</mark> of the emperor of the three worlds, the glorious
              Kulottunga-Chola, who took Madurai and Ceylon, on a day which was <mark class="c">Thursday</mark>, the day of
              <mark class="c">Pushya</mark>, and the <mark class="c">first tithi of the first fortnight</mark> of the month of
              <mark class="c">Makara</mark>."</div>
              <div class="src">Somanathesvara temple, Somangalam (near Chennai) · translated by F. Kielhorn,
              Epigraphia Indica VII (1902), No. 60</div></div>""", unsafe_allow_html=True)
        with b:
            card("Thousands of these survive",
                 "Chola kings ruled much of South India from about 850 to 1280 CE. Their temples are covered in "
                 "inscriptions recording land grants, gifts of gold and lamps, and temple rules.")
            card("None of them gives a year",
                 "Instead of “1192 CE”, each one names the year of the king's reign and describes the sky "
                 "that day. If you know the king's first year, the sky tells you the exact day, and the other way round.")
            card("Around 1900, a German scholar solved them by hand",
                 "Franz Kielhorn spent years doing the astronomy with pen and printed tables. "
                 "This project rebuilds his work with modern astronomy and statistics, and checks his answers.")

    elif s == 1:
        st.markdown('<p class="note">The highlighted words in the stone are five clues. '
                    'Each one rules out most days of the year. Together they should leave just one.</p>',
                    unsafe_allow_html=True)
        clue_cards(no60)
        st.write("")
        a, b = st.columns([1, 1.2], gap="large")
        with a:
            card("Why the sky?",
                 "Everyone used the same almanac, so every reader knew which day “Thursday, Pushya, first day of "
                 "the bright fortnight of Makara” meant. Today we can recompute that almanac: the sun, moon and stars "
                 "move like clockwork, and we can run the clock backwards 900 years.")
        with b:
            st.markdown('<p class="note">This dial shows the sky at sunrise. The sun and moon move around the circle of '
                        'stars. The cyan arc between them sets the <b>tithi</b> (moon phase); the highlighted segment is '
                        'the <b>nakshatra</b> (the moon\'s star group). Shown: sunrise on 16 January 1192, a new '
                        'moon: the moon sits right beside the sun. Later that day it pulls ahead and the first lunar '
                        'day of the bright fortnight begins.</p>', unsafe_allow_html=True)
            sky(iso_to_n("1192-01-16"), height=330)

    elif s == 2:
        st.markdown('<p class="note">The 14th year of Kulottunga\'s reign ran from July 1191 to July 1192. '
                    'Here is every Thursday in the month of Makara that year, checked against every clue:</p>',
                    unsafe_allow_html=True)
        thursdays = yr14[(yr14["weekday"] == 4) & (yr14["sign_set"] == p.sign_index("Makara"))]
        checklist(thursdays, dataset.clues(no60))
        st.write("")
        hits = find_matches(yr14, dataset.clues(no60))
        card("No day fits every clue." if hits.empty else f"{len(hits)} day(s) fit.",
             "Not one day in the whole 14th year matches all five clues. On the Thursday with the right stars "
             "(2 January 1192) the moon was just past <b>full</b>, the opposite of what the stone says. "
             "So at least one clue must have been carved wrong.", kind="warn")

    elif s == 3:
        st.markdown('<p class="note">So we let one clue be wrong and look again. Two days fit everything but one clue:</p>',
                    unsafe_allow_html=True)
        near = find_matches(yr14, dataset.clues(no60), max_mismatches=1)
        alts = {d["date"]: d["prob"] for d in det["alts"]["K3-60"]}
        cols = st.columns(len(near))
        for c, (_, r) in zip(cols, near.iterrows()):
            wrong = "fortnight (bright written for dark)" if r["failed"] == "tithi" else r["failed"]
            with c:
                card(nice(r["n"], weekday=True),
                     f"Wrong clue: <b>{wrong}</b>. Probability this is the true date: "
                     f"<b>{alts.get(r['date'], 0):.0%}</b>.",
                     big=f"{alts.get(r['date'], 0):.0%}", kind="gold" if alts.get(r["date"], 0) > 0.5 else "")
        a, b = st.columns([1, 1.2], gap="large")
        with a:
            card("The model's call",
                 "Swapping the two fortnights is one of the commonest carving slips, while the stars named on the stone "
                 f"fit 2 January exactly. So the model puts {alts.get('1192-01-02', 0):.0%} on <b>Thursday 2 January "
                 "1192</b>, the same answer Kielhorn reached by hand in 1902.")
        with b:
            sky(iso_to_n("1192-01-02"), height=330)

    elif s == 4:
        D = det
        a, b = st.columns([1, 1.25], gap="large")
        with a:
            card("24 stones, one king",
                 "Each correctly carved inscription says “the reign began within this particular 12-month window”. "
                 "Line up all 24 windows and look for the start date that fits the most stones.")
            card("The answer", f"18 of the 24 stones agree with no errors at all on a start date of 6–8 July 1178. "
                               f"Weighing all 24, mistakes included, those three days come out equally likely, "
                               f"{D['top'][2]:.0%} together:", big=top_label(D), kind="gold")
            st.markdown(f'<p class="note">Very likely between {short_range(*D["i50"])} 1178; almost certainly between '
                        f'{short_range(*D["i95"])} 1178. Kielhorn, after a decade of work on these dates (1906): '
                        f'“about 6–8 July 1178”.</p>', unsafe_allow_html=True)
        with b:
            st.plotly_chart(v.votes_chart([jdate(n) for n in D["acc_n"]], D["votes"], 24), width="stretch",
                            config={"displayModeBar": False})
            st.markdown('<p class="note">Each possible start date (1176–1180) scored by how many of the 24 stones it '
                        'explains perfectly. One sharp peak.</p>', unsafe_allow_html=True)

    elif s == 5:
        a, b, c = st.columns(3, gap="medium")
        with a:
            card("The carvers were good, not perfect",
                 "About 1 clue in 11 was carved wrong. The model finds exactly the five faulty stones Kielhorn found, "
                 "and the same mistake in each: two swapped fortnights, a wrong star group, a 4 carved for a 14, "
                 "and a 15 for a 25.", big="1 in 11")
        with b:
            card("Four “mistakes” that weren't",
                 "Kielhorn marked four more stones as wrong because their moon phase was one day ahead. In every case, "
                 "that moon phase began later the same day. The scribes were naming the moon phase at the time of the "
                 "gift, not at sunrise.", big="4 of 9", kind="gold")
        with c:
            card("…and the numbers back it",
                 "Read that way, the 24 inscriptions are about 2.5 million times more likely than under the sunrise "
                 "rule. That reading is also what pins the start date to 6–8 July.", big="2.5 million ×")
        st.markdown('<p class="note">Now try any of the 24 stones yourself in TRY IT, or see the full verdict in '
                    'THE VERDICT.</p>', unsafe_allow_html=True)

    st.write("")
    n1, n2, n3 = st.columns([1, 1, 4])
    n1.button("← Back", on_click=go, args=(s - 1,), disabled=s == 0, width="stretch")
    n2.button("Next →" if s < len(STEPS) - 1 else "Start over", on_click=go,
              args=(s + 1 if s < len(STEPS) - 1 else 0,), type="primary", width="stretch")

# ------------------------------------------------------------------ TRY IT

with t_try:
    df = df_all
    presets = [f"No. {r.ei_no} · year {r.regnal_year} of the reign · {r.place_key}" for r in df.itertuples()]
    presets.append("✎ Enter my own clues")
    CUSTOM = presets[-1]

    def load_preset():
        sel = st.session_state["preset"]
        if sel == CUSTOM:
            return
        r = df.iloc[presets.index(sel)]
        st.session_state.update({"month": r["solar_month"] or "—", "sday": int(r["solar_day"] or 0),
                                 "paksha": r["paksha"] or "—", "tithi": int(r["tithi"] or 0),
                                 "nak": r["nakshatra"] or "—", "wday": r["weekday"] or "—"})

    if "preset" not in st.session_state:
        st.session_state["preset"] = presets[list(df["ei_no"]).index("60")]
        load_preset()

    st.markdown("#### Decode an inscription")
    st.selectbox("Pick one of the 24 real inscriptions, or enter your own clues", presets, key="preset",
                 on_change=load_preset)
    custom = st.session_state["preset"] == CUSTOM
    row = None if custom else df.iloc[presets.index(st.session_state["preset"])]

    with st.expander("The clues (edit them to experiment)", expanded=custom):
        c1, c2, c3 = st.columns(3)
        c1.selectbox("☉ Sun's month", ["—"] + p.SIGNS, key="month",
                     format_func=lambda s: s if s == "—" else f"{s} · {p.TAMIL_MONTHS[p.SIGNS.index(s)]}",
                     help="Which part of the sky the sun was in. Each lasts about a month.")
        c1.number_input("☉ Day of that month (0 = not given)", 0, 32, key="sday")
        c2.selectbox("☾ Fortnight", ["—", "shukla", "krishna"], key="paksha",
                     format_func=lambda s: {"—": "—", "shukla": "bright (moon growing)", "krishna": "dark (moon shrinking)"}[s],
                     help="Bright = after the new moon; dark = after the full moon.")
        c2.number_input("☾ Tithi, lunar day 1–15 (0 = not given)", 0, 15, key="tithi",
                        help="Which lunar day of the fortnight. Each is one-thirtieth of the moon's cycle.")
        c3.selectbox("✦ Moon's star group (nakshatra)", ["—"] + p.NAKSHATRAS, key="nak",
                     help="The 27 star groups the moon passes through each month.")
        c3.selectbox("◷ Weekday", ["—"] + p.WEEKDAYS, key="wday")

    clues = {"solar_month": "" if st.session_state.month == "—" else st.session_state.month,
             "solar_day": st.session_state.sday or "", "paksha": "" if st.session_state.paksha == "—" else st.session_state.paksha,
             "tithi": st.session_state.tithi or "", "nakshatra": "" if st.session_state.nak == "—" else st.session_state.nak,
             "weekday": "" if st.session_state.wday == "—" else st.session_state.wday}
    given = {k: x for k, x in clues.items() if x}

    with st.expander("Search settings"):
        whole = st.toggle("Search every year 1170–1230 (instead of just this inscription's regnal year)", value=custom)
        rule = st.radio("The moon phase / star group must be current…", ["at any time that day", "at sunrise"],
                        horizontal=True)
    mode = "day" if rule == "at any time that day" else "sunrise"

    cal = era_calendar()
    if row is not None and not whole:
        lo, hi = regnal_window(row["regnal_year"])
        where = f"the {ordinal(int(row['regnal_year']))} year of the reign ({nice(lo + 3)} – {nice(hi - 3)})"
    else:
        lo, hi = cal["n"].iat[0], cal["n"].iat[-1]
        where = "every day from 1170 to 1230"
    sub = cal[(cal["n"] >= lo) & (cal["n"] <= hi)]

    if not given:
        st.info("Add at least one clue.")
    else:
        hits = find_matches(sub, given, mode=mode)
        st.write("")
        if len(hits) == 1:
            n = int(hits["n"].iat[0])
            card("✓ Exactly one day fits every clue", f"Searched {where}.", big=nice(n, weekday=True), kind="gold")
            pick = n
        elif len(hits) == 0:
            near = find_matches(sub, given, mode=mode, max_mismatches=1)
            near = near[near["n_mismatch"] == 1]
            card("✗ No day fits every clue",
                 f"Searched {where}. So at least one clue was carved wrong. "
                 f"{len(near)} day(s) fit all but one clue: pick one below to see which clue would be the mistake.",
                 kind="warn")
            pick = int(near["n"].iat[0]) if len(near) else None
            hits = near
        else:
            card(f"{len(hits)} days fit every clue",
                 f"Searched {where}. Add more clues (or search a single regnal year) to narrow it down.")
            pick = int(hits["n"].iat[0])

        if pick is not None and len(hits):
            a, b = st.columns([1, 1.15], gap="large")
            with a:
                choice = st.selectbox("Inspect a day", hits["n"].tolist()[:300],
                                      format_func=lambda n: nice(n, weekday=True) + (
                                          f"  ·  wrong: {hits.loc[hits['n'] == n, 'failed'].iat[0]}"
                                          if hits.loc[hits['n'] == n, 'failed'].iat[0] else ""))
                checklist(cal[cal["n"] == choice], given, mode=mode)
                st.write("")
                day_panel(choice)
            with b:
                sky(choice)
            if row is not None and row["kielhorn_date"]:
                kn = iso_to_n(row["kielhorn_date"])
                verdict_txt = {"correct": "judged it correctly carved",
                               "error": f"judged it miscarved ({row['kielhorn_error_detail']})",
                               "unresolved": "could not resolve it"}[row["kielhorn_verdict"]]
                st.markdown(f'<p class="note">For comparison: Kielhorn dated this inscription to '
                            f'<b>{nice(kn, weekday=True)}</b> and {verdict_txt}.</p>', unsafe_allow_html=True)

# ------------------------------------------------------------------ THE VERDICT

with t_verdict:
    D = det
    st.markdown("#### When did Kulottunga III become king?")
    st.markdown(f'<p class="lede" style="max-width:none">Between <b style="color:#e8b04a">{top_label(D)}</b>. '
                f'Those three days are equally likely, {D["top"][2]:.0%} together; the evidence cannot separate them. '
                f'There is a 95% chance the reign began between {short_range(*D["i95"])} 1178. '
                f'Franz Kielhorn concluded “about 6–8 July 1178” in 1906.</p>', unsafe_allow_html=True)
    zoom = (D["acc_n"] >= astro.day_number(1178, 5, 15)) & (D["acc_n"] <= astro.day_number(1178, 9, 15))
    k3 = tuple(jdate(astro.day_number(*d)) for d in K1903)
    k6 = tuple(jdate(astro.day_number(*d)) for d in K1906)
    st.plotly_chart(v.accession_chart([jdate(n) for n in D["acc_n"][zoom]], D["acc_p"][zoom], k3, k6),
                    width="stretch", config={"displayModeBar": False})
    st.markdown('<p class="note">Blue bars: the probability of each day being the first day of the reign. '
                'Shaded: Kielhorn\'s estimates from 1903 and, after more inscriptions were found, 1906. '
                'All dates are in the Julian calendar, which was in use at the time.</p>', unsafe_allow_html=True)

    st.write("")
    a, b = st.columns([1, 1.15], gap="large")
    with a:
        st.markdown("#### Which stones were carved wrong?")
        st.markdown('<p class="note">The model finds the same five faulty inscriptions Kielhorn did (orange bars '
                    'reaching 1.0), plus No. 31, which he could not solve. Four more that he marked as errors '
                    '(Nos. 108, 109, 113, 114) come out clean: their moon phase began later the same day.</p>',
                    unsafe_allow_html=True)
        st.markdown('<p class="note"><span style="color:#3987e5">■</span> Kielhorn said correct &nbsp; '
                    '<span style="color:#d95926">■</span> Kielhorn said error &nbsp; '
                    '<span style="color:#7d7c76">■</span> unresolved</p>', unsafe_allow_html=True)
    with b:
        st.plotly_chart(v.miscarve_chart(D["table"]), width="stretch", config={"displayModeBar": False})

    with st.expander("Every inscription in detail"):
        st.dataframe(D["table"].rename(columns={
            "no": "No.", "year": "reign year", "verdict": "Kielhorn", "kielhorn_date": "Kielhorn's date",
            "p": "P(miscarved)", "date": "model's date", "p_date": "P(date)", "wrong": "wrong clues"})
                     .drop(columns=["id"]), hide_index=True, width="stretch")

    with st.expander("Change the assumption: what if the moon phase had to be the one at sunrise?"):
        K = verdict("kielhorn")
        bf = (D["log_ev"] - K["log_ev"]) / np.log(10)
        m1, m2, m3 = st.columns(3)
        m1.metric("Top days", top_label(K))
        m2.metric("50% interval", short_range(*K["i50"]))
        m3.metric("Inscriptions flagged", int((K["table"]["p"] > 0.5).sum()))
        st.markdown(f'<p class="note">Under Kielhorn\'s sunrise rule the model needs 11 faulty stones instead of 6, '
                    f'and the data are 10^{bf:.1f} (about {10 ** bf / 1e6:.1f} million) times less likely. '
                    f'The start date widens to Kielhorn\'s own earlier estimate of 8 June – 8 July 1178.</p>',
                    unsafe_allow_html=True)

# ------------------------------------------------------------------ MAP

with t_map:
    df = df_all
    st.markdown("#### Where the 24 inscriptions are")
    st.markdown('<p class="note">Drag the slider through Kulottunga III\'s reign. Each dot is a temple with a dated '
                'inscription; the cyan dots were carved in the year you have selected.</p>', unsafe_allow_html=True)
    yr = st.slider("Year of the reign", 1, 39, 14)
    acc = astro.day_number(*ACCESSION)
    start_y = ymd(acc + round((yr - 1) * dt.YEAR))[0]
    pm = dict(zip(det["table"]["id"], det["table"]["p"]))
    shown = df[df["regnal_year"] <= yr].copy()
    shown["label"] = [f"<b>No. {r.ei_no}</b> · year {r.regnal_year}<br>{r.place}<br>"
                      f"{'carved wrong' if pm[r.id] > 0.5 else 'carved correctly'} (P = {pm[r.id]:.2f})"
                      for r in shown.itertuples()]
    now = df[df["regnal_year"] == yr]
    a, b = st.columns([2.2, 1], gap="large")
    with a:
        st.plotly_chart(v.sites_map(places_all, shown, set(now["id"])), width="stretch")
    with b:
        st.markdown(f'<div class="kicker">Year {yr} of the reign · from July {start_y}</div>', unsafe_allow_html=True)
        st.write("")
        if len(now):
            for r in now.itertuples():
                card(f"No. {r.ei_no} · {r.place_key}",
                     f"{r.place.split(',', 1)[-1].strip()}<br>Date: {nice(iso_to_n(r.kielhorn_date), weekday=True) if r.kielhorn_date else 'unresolved'}"
                     f"<br>{'⚠ carved with a mistake' if pm[r.id] > 0.5 else '✓ carved correctly'}")
        else:
            st.markdown('<p class="note">No dated inscription from this year in the dataset.</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="note">{len(shown)} of 24 inscriptions carved by year {yr}. Positions are approximate '
                    '(village level).</p>', unsafe_allow_html=True)

# ------------------------------------------------------------------ SKY

with t_sky:
    st.markdown("#### The sky over Thanjavur, any morning from 1170 to 1230")
    st.markdown('<p class="note">Pick a date (Julian calendar) and see what an almanac-maker would have recorded. '
                'Try 2 January 1192, the day of inscription No. 60.</p>', unsafe_allow_html=True)
    a, b, c = st.columns(3)
    y = a.number_input("Year", ERA[0][0], ERA[1][0], 1192)
    m = b.selectbox("Month", list(range(1, 13)), index=0, format_func=lambda k: MONTHS[k - 1])
    d = c.number_input("Day", 1, 31, 2)
    try:
        n = astro.day_number(int(y), int(m), int(d))
        if ymd(n) != (int(y), int(m), int(d)):
            raise ValueError
        l2, r2 = st.columns([1, 1.15], gap="large")
        with l2:
            day_panel(n)
            st.write("")
            st.markdown('<p class="note"><b>Reading the dial.</b> The circle is the sky the sun and moon travel '
                        'through, labelled with the 12 solar months. Gold dot: the sun. White dot: the moon. '
                        'The cyan arc is how far the moon is ahead of the sun: every 12° is one tithi (lunar day), '
                        'so 0° is new moon and 180° is full moon. The highlighted segment is the moon\'s star group.</p>',
                        unsafe_allow_html=True)
        with r2:
            sky(n, height=440)
    except Exception:
        st.error("That date doesn't exist (e.g. 31 February).")

# ------------------------------------------------------------------ HOW IT WORKS

with t_how:
    a, b = st.columns([1.3, 1], gap="large")
    with a:
        st.markdown("""
#### How it works

**1 · The sky calculator.** For every morning from 1170 to 1230, a high-precision astronomy library (the Swiss
Ephemeris) gives the positions of the sun and moon at sunrise over Thanjavur.
From those come the month, the tithi, the nakshatra and the weekday. Kielhorn worked with a traditional Indian
astronomy textbook; his figures show it ran a steady 1.7° away from modern astronomy, so the calculator is calibrated
to match.

**2 · The data.** All 24 dated inscriptions of Kulottunga III that Kielhorn examined in *Epigraphia Indica*
(1896–1906), with every clue exactly as carved. The calculator reproduces all 14 dates he judged correct, and each
is the only day in its year that fits.

**3 · The detective.** For each possible start date, every inscription's true date is somewhere in its year of the
reign, and every clue was carved either correctly or wrongly. Wrong clues tend to be wrong in typical ways (swapped
fortnights, a neighbouring star group, a slipped digit). Adding up the evidence from all 24 stones gives a probability
for every start date, the carvers' error rate, and the chance each stone was miscarved. This is Bayesian inference.

**Checks.** 54 automated tests; the weekdays of 38 dated Chola inscriptions; a modern almanac matched to the minute;
the answer barely moves when the assumptions change.
""")
    with b:
        st.markdown("#### Glossary")
        for term, meaning in [
            ("Chola", "A dynasty that ruled much of South India from about 850 to 1280, from their capital at Thanjavur."),
            ("Regnal year", "Years counted from a king's accession: “the 14th year of Kulottunga”."),
            ("Tithi", "A lunar day: one-thirtieth of the moon's cycle, measured by how far the moon is ahead of the sun (12° each)."),
            ("Paksha", "A fortnight: shukla (bright, moon growing) or krishna (dark, moon shrinking)."),
            ("Nakshatra", "One of 27 star groups the moon passes through each month."),
            ("Solar month", "Which of 12 parts of the sky the sun is in; Makara is roughly late December to January."),
            ("Julian calendar", "The calendar in use in the 12th century; dates run 7 days behind ours at that time."),
        ]:
            st.markdown(f'<div class="card"><h4>{term}</h4><p>{meaning}</p></div>', unsafe_allow_html=True)

st.markdown(f"""<div class="foot">Built by Sanjay Ashok in a 24-hour build · code, data and tests:
<a href="{REPO}">{REPO.replace('https://', '')}</a> · inscription texts and translations from F. Kielhorn,
<i>Epigraphia Indica</i> IV–VIII (1896–1906) · astronomy: Swiss Ephemeris</div>""", unsafe_allow_html=True)
