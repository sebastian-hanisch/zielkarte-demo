"""Plotly-Abbildungen. Alle Achsen sind gesperrt (fixedrange), damit Touch-Geräte beim Scrollen nicht am Diagramm hängen bleiben."""

import numpy as np
import plotly.graph_objects as go

import zka_algorithm as A
import zka_constants as C

FAM_COLORS = {0: "#4c78a8", 1: "#7b5ea7"}
GOAL_COLORS = {"kpi": "#c0504d", "kpiz": "#d8a13a", "true": "#2F6B65"}
SHORT = {"kpi": "nur Kennzahl", "kpiz": "Kennzahl plus Überstundenkosten", "true": "wahre Kosten"}


def lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _base(fig, height=360):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=30, b=10), legend=dict(orientation="h", y=-0.25), plot_bgcolor="rgba(0,0,0,0)")
    return lock_axes(fig)


def build_cloud(p: A.Problem, c: dict, g: int):
    """Alle zulässigen Pläne: Zielwert waagerecht, wahre Kosten senkrecht; der Spielraum, der gewählte Plan und der schlimmste Plan im Spielraum als Marken."""
    ok = p.ok
    v = A.goal_values(p, c["goal"], g)
    t = A.true_cost(p, g)
    fig = go.Figure(go.Scattergl(x=v[ok], y=t[ok], mode="markers", marker=dict(size=3, color=C.COLOR_ALL), name="zulässige Pläne", hovertemplate="Zielwert %{x:.1f} / wahre Kosten %{y:.1f}<extra></extra>"))
    members = c["space"]["idx"]
    fig.add_trace(go.Scatter(x=v[members], y=t[members], mode="markers", marker=dict(size=9, color=C.COLOR_SPACE, line=dict(width=1, color="white")), name="Spielraum", hovertemplate="Spielraum: Zielwert %{x:.1f} / wahre Kosten %{y:.1f}<extra></extra>"))
    pick, worst = c["pick"]["idx"], c["space"]["worst"]["idx"]
    fig.add_trace(go.Scatter(x=[v[pick]], y=[t[pick]], mode="markers", marker=dict(symbol="diamond", size=15, color=C.COLOR_PICK, line=dict(width=1.5, color="white")), name="gewählter Plan"))
    if worst != pick:
        fig.add_trace(go.Scatter(x=[v[worst]], y=[t[worst]], mode="markers", marker=dict(symbol="x", size=13, color=C.COLOR_WORST, line=dict(width=2)), name="schlimmster Plan im Spielraum"))
    fig.add_hline(y=C.HARM_PCT / 100 * c["t_opt"], line_dash="dot", line_color=C.COLOR_WORST, annotation_text="schädlich ab hier", annotation_position="top left")
    fig.update_xaxes(title_text=f"Zielwert: {C.GOAL_NAMES[c['goal']]} (kleiner ist besser)")
    fig.update_yaxes(title_text="Wahre Kosten (mit Zuschlag)")
    return _base(fig, height=420)


def build_space(c: dict):
    """Die Mitglieder des Spielraums nach wahren Kosten (geteilt durch das wahre Optimum); die Linie bei 1,25 trennt schädlich von harmlos."""
    sp = c["space"]
    ratios = sorted(((float(r), i) for i, r in enumerate(sp["ratios"])), reverse=True)[:60]
    fig = go.Figure(go.Bar(x=[str(i + 1) for _, i in ratios], y=[r for r, _ in ratios], marker_color=[C.COLOR_WORST if r * 100 >= C.HARM_PCT else C.COLOR_SPACE for r, _ in ratios],
                           hovertemplate="Mitglied %{x}: %{y:.2f}-fach des wahren Optimums<extra></extra>"))
    fig.add_hline(y=C.HARM_PCT / 100, line_dash="dot", line_color=C.COLOR_WORST, annotation_text="1,25-fach", annotation_position="top left")
    fig.update_xaxes(type="category", title_text="Mitglieder des Spielraums (nach wahren Kosten, höchstens 60 gezeigt)", showticklabels=False)
    fig.update_yaxes(title_text="Wahre Kosten geteilt durch das wahre Optimum", rangemode="tozero")
    return _base(fig, height=300)


def build_ranks(c: dict, thr: int):
    """Rang des Optimums unter allen zulässigen Plänen in den vier nicht gemessenen Größen; die Linie ist die Schwelle."""
    rows = c["rows"]
    fig = go.Figure(go.Bar(y=[r["label"] for r in rows], x=[r["rank"] * 100 for r in rows], orientation="h", marker_color=[C.COLOR_WORST if r["alarm"] else C.COLOR_SPACE for r in rows],
                           hovertemplate="%{y}: Rang %{x:.1f} %<extra></extra>"))
    fig.add_vline(x=thr, line_dash="dot", line_color="rgba(150,150,150,0.9)", annotation_text=f"Schwelle {thr} %", annotation_position="top")
    fig.update_xaxes(range=[0, 100], title_text="Rang des Optimums unter allen zulässigen Plänen (%)")
    fig.update_yaxes(autorange="reversed")
    return _base(fig, height=260)


def build_alarm_sweep(res: dict, fam: int):
    """Alarm je Schwelle und Ziel (Anzahl der Instanzen): Treffer beim gebrochenen Ziel, Fehlalarm bei den anderen."""
    s = res[fam]
    fig = go.Figure([go.Bar(x=[f"{t} %" for t in C.SWEEP_THRESHOLDS], y=[s[goal]["alarm"][t] for t in C.SWEEP_THRESHOLDS], name=SHORT[goal], marker_color=GOAL_COLORS[goal],
                            hovertemplate=f"{SHORT[goal]}, Schwelle %{{x}}: Alarm in %{{y}} Instanzen<extra></extra>") for goal in C.GOALS])
    fig.update_layout(barmode="group")
    fig.update_xaxes(type="category", title_text="Schwelle des Rangs")
    fig.update_yaxes(title_text=f"Alarm (Instanzen von {s['kpi']['seeds']})", range=[0, s["kpi"]["seeds"]])
    return _base(fig, height=320)


def build_dose_sweep(res: dict):
    """Überstundenanteil: Alarm (Anteil der Instanzen) und Schaden (Median) beim Ziel „nur Kennzahl“."""
    fig = go.Figure()
    for fam, s in res.items():
        xs = [f"{fz} %" for fz in C.SWEEP_FZS]
        fig.add_trace(go.Bar(x=xs, y=[s[fz]["alarm"] / s[fz]["seeds"] * 100 for fz in C.SWEEP_FZS], name=f"{C.FAMILIES[fam]}: Alarm (%)", marker_color=FAM_COLORS.get(fam, "#888"),
                             hovertemplate="Überstundenanteil %{x}: Alarm in %{y:.0f} % der Instanzen<extra></extra>"))
        fig.add_trace(go.Scatter(x=xs, y=[s[fz]["loss"][1] * 100 for fz in C.SWEEP_FZS], mode="lines+markers", name=f"{C.FAMILIES[fam]}: Schaden (Median, %)", line=dict(color=FAM_COLORS.get(fam, "#888"), dash="dash"),
                                 hovertemplate="Überstundenanteil %{x}: Schaden im Median %{y:.1f} %<extra></extra>"))
    fig.update_layout(barmode="group")
    fig.update_xaxes(type="category", title_text="Überstundenkapazität (Anteil der Regelkapazität)")
    fig.update_yaxes(title_text="Prozent")
    return _base(fig, height=340)
