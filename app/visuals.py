"""
Visual pieces for the demo app: the temple wireframe, the sky dial and the charts.
Kept apart from the app so the layout code stays readable.
"""

import math

import numpy as np
import plotly.graph_objects as go

from chola import panchang as p

GOLD = "#e8b04a"
CYAN = "#4fd1e8"
BLUE = "#3987e5"     # categorical slot 1, dark mode (validated reference palette)
ORANGE = "#d95926"   # categorical slot 2, dark mode
GREY = "#7d7c76"
INK = "#e6e4dc"
MUTED = "#9a998f"
GRID = "rgba(230,228,220,0.08)"
FONT = "JetBrains Mono, ui-monospace, monospace"


# ------------------------------------------------------------- temple

def vimana_svg(width: int = 420) -> str:
    """
    A wireframe drawing of the Brihadeeswarar (Periya Kovil) vimana at Thanjavur:
    a square base, 13 diminishing storeys, a neck, the octagonal dome and the
    finial, inside a blueprint grid with the sun's and moon's orbits behind it.
    Schematic, not to scale.
    """
    W, H = 420, 470
    cx, ground = W / 2, 440
    out = [f'<svg viewBox="0 0 {W} {H}" width="{width}" xmlns="http://www.w3.org/2000/svg" '
           f'style="max-width:100%;height:auto" role="img" aria-label="Wireframe of the Thanjavur temple tower">']
    # blueprint grid
    for x in range(0, W + 1, 20):
        out.append(f'<line x1="{x}" y1="0" x2="{x}" y2="{H}" stroke="{CYAN}" stroke-opacity="0.07"/>')
    for y in range(0, H + 1, 20):
        out.append(f'<line x1="0" y1="{y}" x2="{W}" y2="{y}" stroke="{CYAN}" stroke-opacity="0.07"/>')
    # orbits (sun and moon), with their bodies
    out.append(f'<ellipse cx="{cx}" cy="150" rx="190" ry="46" fill="none" stroke="{CYAN}" stroke-opacity="0.35" stroke-dasharray="3 5"/>')
    out.append(f'<ellipse cx="{cx}" cy="150" rx="150" ry="30" fill="none" stroke="{CYAN}" stroke-opacity="0.25" stroke-dasharray="2 6"/>')
    out.append(f'<circle cx="{cx + 190 * math.cos(2.6)}" cy="{150 + 46 * math.sin(2.6)}" r="9" fill="{GOLD}"/>')
    out.append(f'<circle cx="{cx + 150 * math.cos(0.5)}" cy="{150 + 30 * math.sin(0.5)}" r="5.5" fill="{INK}" fill-opacity="0.85"/>')

    line = f'fill="none" stroke="{GOLD}" stroke-width="1.3"'
    # plinth and base walls
    out.append(f'<rect x="{cx-150}" y="{ground-14}" width="300" height="14" {line}/>')
    out.append(f'<rect x="{cx-132}" y="{ground-74}" width="264" height="60" {line}/>')
    for k in range(-3, 4):  # wall pilasters
        x = cx + k * 37
        out.append(f'<line x1="{x}" y1="{ground-74}" x2="{x}" y2="{ground-14}" stroke="{GOLD}" stroke-opacity="0.45"/>')
    # 13 storeys, each a trapezoid slightly narrower than the last
    y, half = ground - 74, 124.0
    for i in range(13):
        h = 17 - i * 0.55
        top = half - 7.6
        out.append(f'<polygon points="{cx-half},{y} {cx+half},{y} {cx+top},{y-h} {cx-top},{y-h}" {line}/>')
        for k in (-1, 1):  # niche markers
            out.append(f'<line x1="{cx+k*half*0.5}" y1="{y}" x2="{cx+k*top*0.5}" y2="{y-h}" stroke="{GOLD}" stroke-opacity="0.35"/>')
        y, half = y - h, top
    # neck, dome and finial
    out.append(f'<rect x="{cx-half+6}" y="{y-10}" width="{2*half-12}" height="10" {line}/>')
    y -= 10
    out.append(f'<path d="M {cx-half-4} {y} Q {cx-half-4} {y-46} {cx} {y-50} Q {cx+half+4} {y-46} {cx+half+4} {y} Z" {line}/>')
    out.append(f'<line x1="{cx}" y1="{y-50}" x2="{cx}" y2="{y-78}" stroke="{GOLD}" stroke-width="1.6"/>')
    out.append(f'<circle cx="{cx}" cy="{y-62}" r="4" {line}/>')
    # dimension line and label
    out.append(f'<line x1="{cx+175}" y1="{ground}" x2="{cx+175}" y2="{y-78}" stroke="{CYAN}" stroke-opacity="0.5"/>')
    out.append(f'<text x="{cx+182}" y="{(ground+y-78)/2}" fill="{CYAN}" fill-opacity="0.7" font-family="{FONT}" font-size="10">66 m</text>')
    out.append(f'<text x="12" y="{H-8}" fill="{CYAN}" fill-opacity="0.6" font-family="{FONT}" font-size="10">'
               f'PERIYA KOVIL · THANJAVUR · 10.78°N 79.13°E</text>')
    out.append("</svg>")
    return "".join(out)


# ------------------------------------------------------------- shared chart styling

def _layout(fig, title=None, height=320):
    fig.update_layout(
        height=height, margin=dict(l=10, r=10, t=40 if title else 10, b=10),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FONT, color=MUTED, size=11),
        title=dict(text=title, font=dict(color=INK, size=13), x=0, xanchor="left") if title else None,
        hoverlabel=dict(bgcolor="#121822", bordercolor=GOLD, font=dict(family=FONT, color=INK)),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=MUTED)),
    )
    fig.update_xaxes(gridcolor=GRID, zeroline=False, linecolor=GRID)
    fig.update_yaxes(gridcolor=GRID, zeroline=False, linecolor=GRID)
    return fig


# ------------------------------------------------------------- sky dial

def sky_dial(sun: float, moon: float, height=440):
    """
    The sky as a circle seen from Earth: 27 nakshatra segments around the rim,
    the sun and moon at their sidereal longitudes, and the arc between them
    (the elongation, which sets the tithi).
    """
    fig = go.Figure()
    nak = int(moon // (360 / 27))
    widths = [360 / 27] * 27
    centres = [(i + 0.5) * 360 / 27 for i in range(27)]
    fig.add_trace(go.Barpolar(
        r=[1] * 27, theta=centres, width=widths, base=[2.6] * 27,
        marker=dict(color=[GOLD if i == nak else "rgba(232,176,74,0.08)" for i in range(27)],
                    line=dict(color="rgba(232,176,74,0.45)", width=1)),
        text=p.NAKSHATRAS, hovertemplate="%{text}<extra></extra>", showlegend=False))
    elong = (moon - sun) % 360
    arc = np.linspace(sun, sun + elong, 80)
    fig.add_trace(go.Scatterpolar(r=[1.4] * len(arc), theta=arc, mode="lines",
                                  line=dict(color=CYAN, width=3), name="elongation → tithi",
                                  hoverinfo="skip"))
    for lon, r, size, col, name in ((sun, 2.0, 22, GOLD, "Sun"), (moon, 2.0, 15, INK, "Moon")):
        fig.add_trace(go.Scatterpolar(r=[0, r], theta=[lon, lon], mode="lines",
                                      line=dict(color=col, width=1, dash="dot"), showlegend=False, hoverinfo="skip"))
        fig.add_trace(go.Scatterpolar(r=[r], theta=[lon], mode="markers", marker=dict(size=size, color=col),
                                      name=name, hovertemplate=f"{name} %{{theta:.1f}}°<extra></extra>"))
    fig.update_layout(polar=dict(
        bgcolor="rgba(0,0,0,0)",
        radialaxis=dict(visible=False, range=[0, 3.7]),
        angularaxis=dict(direction="counterclockwise", rotation=0, gridcolor=GRID, linecolor=GRID,
                         tickvals=[i * 30 for i in range(12)], ticktext=p.SIGNS,
                         tickfont=dict(color=MUTED, size=10))))
    return _layout(fig, height=height)


# ------------------------------------------------------------- detective charts

def accession_chart(dates, probs, kielhorn_1903, kielhorn_1906):
    fig = go.Figure()
    for (a, b), alpha, name in ((kielhorn_1903, 0.10, "Kielhorn 1903"), (kielhorn_1906, 0.28, "Kielhorn 1906")):
        fig.add_vrect(x0=a, x1=b, fillcolor=ORANGE, opacity=alpha, line_width=0, layer="below",
                      annotation_text=name, annotation_position="top left",
                      annotation_font=dict(color=MUTED, size=10))
    fig.add_trace(go.Bar(x=dates, y=probs, marker_color=BLUE, name="P(start date)",
                         hovertemplate="%{x|%d %b %Y}: %{y:.3f}<extra></extra>"))
    fig.update_yaxes(title="probability")
    return _layout(fig, height=300)


def votes_chart(dates, votes, n):
    fig = go.Figure(go.Scatter(x=dates, y=votes, mode="lines", line=dict(color=BLUE, width=2, shape="hv"),
                               hovertemplate="%{x|%d %b %Y}: %{y} of " + str(n) + "<extra></extra>"))
    fig.update_yaxes(title="inscriptions explained", range=[0, n + 1])
    return _layout(fig, height=260)


def miscarve_chart(df):
    colors = {"correct": BLUE, "error": ORANGE, "unresolved": GREY}
    d = df.iloc[::-1]
    fig = go.Figure(go.Bar(
        y=[f"No. {x}" for x in d["no"]], x=d["p"], orientation="h",
        marker_color=[colors[v] for v in d["verdict"]],
        customdata=np.stack([d["verdict"], d["wrong"], d["date"]], axis=1),
        hovertemplate="%{y}: P(miscarved) %{x:.2f}<br>Kielhorn: %{customdata[0]}"
                      "<br>Most likely date %{customdata[2]}, wrong: %{customdata[1]}<extra></extra>"))
    fig.update_xaxes(range=[0, 1], title="P(miscarved)")
    return _layout(fig, height=560)


# ------------------------------------------------------------- map

def sites_map(places, shown, highlight):
    """Inscription sites; `shown` = rows visible so far, `highlight` = ids dated in the selected year."""
    fig = go.Figure()
    cap = places[places["place"] == "Thanjavur"].iloc[0]
    fig.add_trace(go.Scattermap(lat=[cap.lat], lon=[cap.lon], mode="markers+text",
                                marker=dict(size=18, color=GOLD), text=["Thanjavur"],
                                textposition="middle left", textfont=dict(color=GOLD, size=12),
                                hovertemplate="Thanjavur, the Chola capital<extra></extra>", name="Capital"))
    if len(shown):
        hl = shown["id"].isin(highlight)
        for mask, size, col, name in ((~hl, 10, BLUE, "Earlier inscriptions"), (hl, 16, CYAN, "Dated this year")):
            s = shown[mask]
            if len(s):
                fig.add_trace(go.Scattermap(
                    lat=s["lat"], lon=s["lon"], mode="markers", marker=dict(size=size, color=col, opacity=0.9),
                    text=s["label"], hovertemplate="%{text}<extra></extra>", name=name))
    fig.update_layout(map=dict(style="carto-darkmatter", center=dict(lat=12.0, lon=79.6), zoom=5.6),
                      legend=dict(x=0.01, y=0.99))
    return _layout(fig, height=520)
