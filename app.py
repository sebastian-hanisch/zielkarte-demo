"""Zielkarte - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Stück 13 der Reihe „Zielfunktionsdesign“: Wie findet man vor dem Einsatz, was ein Ziel zulässt, wenn man die Wahrheit nicht kennt? Dasselbe Beispiel wie in Stück 10 (Aufgaben in Regelzeit oder Überstunden).
Die Demo zeigt den Spielraum eines Ziels, das Red Team (die Suche nach dem schlimmsten Plan darin), den Extremwert-Test auf nicht gemessene Größen und die Zielkarte.

Lauffähig mit: streamlit run app.py
"""

import streamlit as st

import zka_constants as C
from zka_evaluation import (
    Settings,
    analyse,
    card,
    cards,
    de,
    pct,
    person_text,
    summary_alarm,
    summary_dose,
    summary_space,
    sweep_all,
    verdict_alarm_sweep,
    verdict_card,
    verdict_dose_sweep,
    verdict_redteam,
    verdict_space,
    verdict_space_sweep,
    vtext,
)
from zka_layout import dunkles_design, kopf_css
from zka_pdf_export import build_pdf
from zka_presets import (
    bounds,
    init_session_state_defaults,
    load_permalink_settings,
    randomize_seed,
    sidebar_presets,
    sync_query_params,
)
from zka_visualization import build_alarm_sweep, build_cloud, build_dose_sweep, build_ranks, build_space

st.set_page_config(page_title="Zielkarte – Sebastian Hanisch", layout="wide")


@st.cache_data(show_spinner=False)
def _analysis(settings):
    return analyse(settings)


@st.cache_data(show_spinner="40 feste Instanzen werden gerechnet (je 279 936 Pläne, zwei Familien) ...")
def _sweep():
    return sweep_all()


@st.cache_data(show_spinner="40 weitere feste Instanzen werden gerechnet (zweite Seed-Menge) ...")
def _holdout():
    return sweep_all(seeds=C.HOLDOUT_SEEDS, dose=False)


# Fester Kopf: nur der Titel bleibt beim Scrollen oben (Stylesheet in zka_layout.py).
st.html(kopf_css(dunkles_design()))
with st.container(key="kopf"):
    st.title("🗺️ Zielkarte")
st.markdown(
    """
**Was lässt das Ziel zu, und wie findet man das vor dem Einsatz?** Dasselbe Beispiel wie in Stück 10: **m Aufgaben** auf **n Personen**, jede in der **Regelzeit** oder in **Überstunden**; die **Kennzahl** misst nur die Regelzeit,
die **wahren Kosten** zählen die Überstunden mit Zuschlag. Meist kennt man die Wahrheit vorher nicht. Zwei Wege: das **Red Team** sucht im **Spielraum** des Ziels (alle zulässigen Pläne, die höchstens `s` über dem Optimum liegen)
den schlimmsten Plan (das setzt voraus, dass man die wahren Kosten der Pläne kennt oder schätzen kann; die Demo bewertet mit den wahren Kosten); der **Extremwert-Test** fragt, **wo das Optimum in den Größen liegt, die das Ziel nicht misst**, und braucht die wahren Kosten nicht. Die **Zielkarte** fasst beides auf einer Seite zusammen.

Weiter unten: **🔬 Die Zielkarte**, **🔬 Der Spielraum**, **🔬 Das Red Team**, **🔬 Trefferquote und Fehlalarm**, **🔬 Alarm und Schaden**, **🚧 Wo die Annahmen enden** und der Expander **📐 Mathematische Formulierung**.
"""
)

with st.expander("So funktioniert der Vergleich", expanded=True):
    st.markdown(
        """
1. **Drei Ziele:** „nur Kennzahl“ (Kosten der Regelzeit-Aufgaben), „Kennzahl plus Überstundenkosten“ (ohne Zuschlag, teilweise repariert) und „wahre Kosten“ (mit Zuschlag). Das gewählte Ziel bestimmt den Plan (bei Gleichstand der kleinste Index der Aufzählung).
2. **Spielraum:** alle zulässigen Pläne mit Zielwert höchstens Optimum plus `s`. **Schädlich** ist ein Plan mit wahren Kosten von mindestens dem 1,25-fachen des wahren Optimums.
3. **Extremwert-Test:** für vier Größen, die das Ziel nicht misst (Überstunden-Stunden, Aufgaben in Überstunden, Kosten in Überstunden, höchste Überstundenlast einer Person), steht der **Rang** des Optimums unter allen zulässigen Plänen (Mittelwert-Rang). **Alarm**, wenn der Rang mindestens die Schwelle erreicht.
4. **Messungen, kein Satz:** Alle Zahlen sind Zählungen und Spannen über feste Instanzen dieses Zufallsmodells; sie sagen nichts über echte Schichtpläne.
        """
    )

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    sidebar_presets()  # Schnellstart oben, das aktive Preset ist hervorgehoben
    st.header("⚙️ Einstellungen")
    st.markdown("**Instanz**")
    n = st.slider("Personen n", *bounds("n_slider"), key="n_slider", help="Alle (2n)^m Pläne werden aufgezählt (bis 279 936).")
    m = st.slider("Aufgaben m", *bounds("m_slider"), key="m_slider")
    family = st.selectbox("Kosten", list(range(len(C.FAMILIES))), key="family_select", format_func=lambda i: C.FAMILIES[i], help="Beim Personeneffekt ist eine Person im Mittel bei etwa 60 % der Aufgaben die billigste (bei 3 Personen und 7 Aufgaben, über die 20 festen Instanzen gemessen).")
    seed = st.number_input("Zufalls-Seed der Instanz", *bounds("seed_input"), key="seed_input", step=1)
    st.button("🎲 Neue Instanz generieren", width="stretch", on_click=randomize_seed)
    st.markdown("**Kapazität und Preis**")
    fr = st.slider("Regelkapazität in % des Durchschnittsbedarfs", *bounds("fr_slider"), key="fr_slider", step=C.FR_STEP)
    fz = st.slider("Überstundenkapazität in % der Regelkapazität", *bounds("fz_slider"), key="fz_slider", step=C.FZ_STEP, help="Der Ort, in den man ausweichen kann: bei 0 % gibt es keinen, und nichts wandert.")
    g = st.slider("Zuschlag der Überstunden in %", *bounds("g_slider"), key="g_slider", step=C.G_STEP, help="Nur für die wahren Kosten; das teilweise reparierte Ziel zählt die Überstunden ohne Zuschlag.")
    st.markdown("**Das Ziel**")
    goal = st.selectbox("Der Optimierer minimiert", list(range(len(C.GOALS))), key="goal_select", format_func=lambda i: C.GOAL_NAMES[C.GOALS[i]])
    st.markdown("**Der Test**")
    s_slack = st.slider("Toleranz des Spielraums (Kosteneinheiten)", *bounds("s_slider"), key="s_slider", help="Alle zulässigen Pläne mit Zielwert höchstens Optimum plus Toleranz gehören zum Spielraum.")
    thr = st.slider("Schwelle des Rangs in %", *bounds("thr_slider"), key="thr_slider", help="Alarm, wenn das Optimum in einer nicht gemessenen Größe mindestens diesen Rang unter allen zulässigen Plänen hat.")

sync_query_params({"n_slider": int(n), "m_slider": int(m), "family_select": int(family), "seed_input": int(seed), "fr_slider": int(fr), "fz_slider": int(fz), "g_slider": int(g), "goal_select": int(goal),
                   "s_slider": int(s_slack), "thr_slider": int(thr)})

settings = Settings(int(n), int(m), int(family), int(seed), int(fr), int(fz), int(g), int(goal), int(s_slack), int(thr))
a = _analysis(settings)
c = card(a)

# --- Ergebnis ------------------------------------------------------------------------------------------------------------------------------

st.markdown("## 🎯 Ergebnis: schlägt der Test an?")
m1, m2, m3 = st.columns(3)
if c is None:
    m1.metric("Gewählter Plan", "unlösbar")
else:
    m1.metric("Alarm", "ja" if c["alarm"] else "nein", delta=f"höchster Rang {pct(c['max_rank'], 0)}, Schwelle {settings.thr} %", delta_color="off")
    m2.metric("Wahre Kosten des Plans", vtext(c["pick"]["true"]), delta=f"Schaden {pct(c['loss'])} gegen das wahre Optimum {vtext(c['t_opt'])}", delta_color="off")
    m3.metric("Spielraum", f"{c['space']['size']} {'Plan' if c['space']['size'] == 1 else 'Pläne'}", delta=f"schlechtestes Mitglied {de(c['space']['ratio_worst'], 2)}-fach", delta_color="off")
    st.plotly_chart(build_cloud(a.p, c, settings.g), width="stretch", key="cloud_chart")
    st.caption("Jeder Punkt ist ein zulässiger Plan: Zielwert waagerecht, wahre Kosten senkrecht. Blau der Spielraum des Ziels, die Raute der gewählte Plan, das Kreuz der schlimmste Plan im Spielraum; über der gestrichelten Linie ist ein Plan schädlich.")
    st.download_button("📄 Zielkarte als PDF", data=build_pdf(a), file_name="zielkarte.pdf", mime="application/pdf", key="pdf_download")

# --- Kernfrage -----------------------------------------------------------------------------------------------------------------------------

st.markdown("## ❓ Kernfrage: Was verrät das Optimum über das, was das Ziel nicht misst?")
kind, text = verdict_card(c, settings.thr)
getattr(st, kind)(text)

st.markdown("---")

# --- Experimente ---------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Die Zielkarte")
st.caption(f"Der Plan des gewählten Ziels ({C.GOAL_NAMES[C.GOALS[settings.goal]]}) in den vier Größen, die es nicht misst: Wert, was typisch ist (Median aller {0 if c is None else c['n_ok']} zulässigen Pläne), und der Rang des Optimums.")
if c is not None:
    rows_md = ["| Größe (nicht gemessen) | Wert im Optimum | Median aller zulässigen | Maximum | Rang | Alarm |", "|---|---|---|---|---|---|"]
    for r in c["rows"]:
        rows_md.append(f"| {r['label']} | {r['value']} | {de(r['median'], 1)} | {r['max']} | {pct(r['rank'], 1)} | {'**ja**' if r['alarm'] else 'nein'} |")
    st.markdown("\n".join(rows_md))
    st.plotly_chart(build_ranks(c, settings.thr), width="stretch", key="ranks_chart")
    allc = cards(a)
    cmp_md = ["| Ziel | Kennzahl des Optimums | Wahre Kosten | Schaden | Höchster Rang | Alarm | Spielraum: Pläne, schlechtestes Mitglied |", "|---|---|---|---|---|---|---|"]
    for goal_key, cc in allc.items():
        cmp_md.append(f"| {C.GOAL_NAMES[goal_key]} | {cc['pick']['kpi']} | {vtext(cc['pick']['true'])} | {pct(cc['loss'])} | {pct(cc['max_rank'], 0)} | {'**ja**' if cc['alarm'] else 'nein'} | {cc['space']['size']}, {de(cc['space']['ratio_worst'], 2)}-fach |")
    st.markdown("\n".join(cmp_md))
    st.caption("Die drei Ziele nebeneinander (gleiche Instanz, gleiche Schwelle und Toleranz): in der Voreinstellung schlägt ein gebrochenes Ziel an und hat einen schädlichen Spielraum, ein repariertes meist nicht (bei Schwelle 90 % in 0 bis 2 von 20 Instanzen); die Presets zeigen Ausnahmen.")
st.markdown("---")

st.subheader("🔬 Der Spielraum")
st.caption(f"Alle zulässigen Pläne, die der Zielwert von dem Optimum nicht unterscheidet (höchstens {settings.s} Kosteneinheiten darüber): wie viele es sind und was sie wirklich kosten. Rot: schädlich (mindestens das 1,25-fache des wahren Optimums).")
if c is not None:
    st.plotly_chart(build_space(c), width="stretch", key="space_chart")
kind, text = verdict_space(c)
getattr(st, kind)(text)
if st.toggle("Den Spielraum über feste Instanzen nachrechnen (je Ziel und Toleranz)", value=False, key="sweep_space"):
    sw = _sweep()
    kind, text = verdict_space_sweep({fam: {goal_key: summary_space(recs, goal_key) for goal_key in C.GOALS} for fam, recs in sw.items()})
    getattr(st, kind)(text)

st.markdown("---")

st.subheader("🔬 Das Red Team")
st.caption("Der Optimierer wird gegen das Ziel gesucht: aus dem Spielraum der Plan mit den größten wahren Kosten, gegen den gewählten Plan.")
if c is not None:
    sp = c["space"]
    red_md = ["| | Kennzahl | Wahre Kosten | Aufgaben in Ü | Stunden in Ü | Plan |", "|---|---|---|---|---|---|"]
    for label, info in (("**Gewählter Plan**", c["pick"]), ("**Schlimmster Plan im Spielraum**", sp["worst"]), ("**Bester Plan im Spielraum**", sp["best"])):
        red_md.append(f"| {label} | {info['kpi']} | {vtext(info['true'])} | {info['nz']} | {info['zhours']} | {person_text(info)} |")
    st.markdown("\n".join(red_md))
kind, text = verdict_redteam(c)
getattr(st, kind)(text)

st.markdown("---")

st.subheader("🔬 Trefferquote und Fehlalarm")
st.caption("Wie oft schlägt der Test an, wenn das Ziel gebrochen ist (Treffer), und wie oft, wenn es repariert ist (Fehlalarm)? Je Schwelle, über 20 feste Instanzen je Familie; die Größe „höchste Überstundenlast einer Person“ ist der blinde Fleck: sie schlägt bei Schwelle 90 % und 50 % Überstundenkapazität nicht an, weil sie an der Kapazitätsgrenze mit vielen Plänen gleichauf liegt.")
if st.toggle("Trefferquote und Fehlalarm über feste Instanzen nachrechnen (je Ziel und Schwelle)", value=False, key="sweep_alarm"):
    sw = _sweep()
    res = {fam: summary_alarm(recs) for fam, recs in sw.items()}
    kind, text = verdict_alarm_sweep(res, f"Alarm je Schwelle, {C.SWEEP_N} Personen, {C.SWEEP_M} Aufgaben, je {len(C.SWEEP_SEEDS)} feste Instanzen")
    getattr(st, kind)(text)
    for fam in res:
        st.caption(C.FAMILIES[fam])
        st.plotly_chart(build_alarm_sweep(res, fam), width="stretch", key=f"alarm_chart_{fam}")
if st.toggle("Die Schwelle an einer zweiten Menge fester Instanzen gegenprüfen (Hold-out)", value=False, key="sweep_holdout"):
    sw = _holdout()
    res = {fam: summary_alarm(recs) for fam, recs in sw.items()}
    kind, text = verdict_alarm_sweep(res, f"Hold-out: andere Seeds {C.HOLDOUT_SEEDS[0]} bis {C.HOLDOUT_SEEDS[-1]}")
    getattr(st, kind)(text)

st.markdown("---")

st.subheader("🔬 Alarm und Schaden")
st.caption("Folgt der Alarm dem Schaden? Der Überstundenanteil von 0 bis 100 % der Regelkapazität, Ziel „nur Kennzahl“: Alarm bei Rang 90 % und wirklicher Schaden.")
if st.toggle("Alarm und Schaden über feste Instanzen nachrechnen (je Überstundenanteil)", value=False, key="sweep_dose"):
    sw = _sweep()
    res = {fam: summary_dose(recs) for fam, recs in sw.items()}
    kind, text = verdict_dose_sweep(res)
    getattr(st, kind)(text)
    st.plotly_chart(build_dose_sweep(res), width="stretch", key="dose_chart")

st.markdown("---")

# --- Grenzen -------------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Das Beispiel von Stück 10** | Der Fehler „Last wandert in eine nicht gemessene Größe“ ist durch den Aufbau groß; andere Fehlerarten (fehlende Nebenbedingung, Rauschen, Instabilität) sind hier nicht getestet | Stück 9, 11 |
| **Die Liste der Größen steht fest** | Der Test sieht nur, was auf der Liste steht; eine Größe, deren Wert an eine Grenze stößt (hier die höchste Überstundenlast), kann bei hoher Schwelle nicht anschlagen: ein blinder Fleck | Stück 8 (Überoptimierung) |
| **Schwelle 90 %** | Sie wurde an denselben Instanzen gewählt wie die Zählung; die zweite Seed-Menge prüft sie gegen, ersetzt aber keine Prüfung am echten Betrieb | – |
| **Genug zulässige Pläne** | Bei N zulässigen Plänen ist der höchste Rang 1 − 1/(2N): bei wenigen Plänen kann der Test nicht anschlagen | – |
| **Spielraum = Zielwert nah am Optimum** | Die Toleranz in Kosteneinheiten ist gewählt; mit größerer Toleranz ist der Spielraum größer, und das Red Team findet mehr (in diesem Modell bei unabhängigen Kosten im Mittel 0,19-fach des Optimums mehr bei Toleranz 10 gegen 0,04 bei Toleranz 0) | Stück 5 (Gleichstände) |
| **Alle Pläne aufgezählt** | Bis 279 936 Pläne; bei großen Problemen braucht es einen Löser für die Spielraum-Suche | Dokumentation des Lösers |
"""
)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Problem (wie Stück 10).** $m$ Aufgaben, $n$ Personen, jede Aufgabe in Regelzeit $R$ oder Überstunden $Z$; zulässig sind Pläne mit Regellast $\le \mathrm{cap}_R$ und Überstundenlast $\le \mathrm{cap}_Z$ je Person.
$\mathrm{KPI}(x) = \sum_{j \in R} a_{x_j j}$, $T_g(x) = \mathrm{KPI}(x) + g \sum_{j \in Z} a_{x_j j}$.

**Ziele.** $f_1 = \mathrm{KPI}$, $f_2 = T_{1}$ (Überstundenkosten ohne Zuschlag), $f_3 = T_g$. Der gewählte Plan $x^*$ minimiert das Ziel (bei Gleichstand der kleinste Index).

**Spielraum und Red Team.** $\mathrm{S}_s(f) = \{\, x \text{ zulässig} : f(x) \le \min f + s \,\}$. Schädlich: $T_g(x) \ge 1{,}25\, \min T_g$. Das Red Team wählt $\arg\max_{x \in \mathrm{S}_s} T_g(x)$. Mit Anteil $q$ schädlicher Pläne braucht eine Stichprobe mit Zurücklegen $k$ Ziehungen, damit $1 - (1 - q)^k \ge 0{,}95$ (exakt mit Brüchen).

**Extremwert-Test.** Für eine nicht gemessene Größe $h$ (Überstunden-Stunden, Aufgaben in $Z$, Kosten in $Z$, höchste Überstundenlast) ist der **Mittelwert-Rang** von $x^*$ unter den $N$ zulässigen Plänen $r = \bigl(\#\{h(x) < h(x^*)\} + \tfrac12 \#\{h(x) = h(x^*)\}\bigr) / N$. Alarm bei $r \ge \theta$, ganzzahlig exakt als $(2\,\#_{<} + \#_{=}) \cdot 100 \ge \theta \cdot 2N$. Der höchste erreichbare Rang ist $1 - 1/(2N)$.

**Literatur.** Keine Aussage dieser Demo stützt sich auf gelesene Literatur; alle Zahlen sind Messungen an dem Zufallsmodell der Demo.
        """
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zur Reihe: [Zielfunktionsdesign: das Ziel ist das Modell](https://sebastianhanisch.net/konzepte-zielfunktionsdesign.html)."
)
