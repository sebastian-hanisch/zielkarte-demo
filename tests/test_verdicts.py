"""Verdikte: Art und Wortlaut in den Fällen, die sie unterscheiden (DEMO-PLAYBOOK §6): jede Zahl im Text kommt aus der Rechnung."""

import zka_constants as C
import zka_evaluation as ev

(P_ALARM, P_TRUE, P_PARTIAL, P_NOPLACE, P_FALSE, P_WIDE, P_WORST, P_SMALL) = list(C.PRESETS)


def _a(name):
    return ev.analyse(ev.Settings(**C.PRESETS[name]))


def _card(name):
    return ev.card(_a(name))


def test_card_verdict_distinguishes_alarm_no_alarm_and_the_test_that_cannot_alarm():
    s = C.PRESETS[P_ALARM]["thr"]
    kind, text = ev.verdict_card(_card(P_ALARM), s)
    assert kind == "warning" and text == ("**Alarm:** Das Optimum gehört unter den 2218 zulässigen Plänen zu den obersten 10 % in: Überstunden-Stunden (Rang 98 %), Aufgaben in Überstunden (Rang 100 %), "
                                          "Kosten in Überstunden (Rang 95 %) (Schwelle 90 %). Das Ziel misst diese Größen nicht: der Plan nutzt, was ihm niemand begrenzt hat.")
    assert ev.verdict_card(_card(P_TRUE), 90) == ("success", "Kein Alarm: in keiner der vier nicht gemessenen Größen liegt das Optimum im obersten Bereich (höchster Rang 69 %, Schwelle 90 %).")
    kind, text = ev.verdict_card(_card(P_SMALL), 90)
    assert kind == "info" and text == "Kein Alarm, aber der Test kann hier nicht anschlagen: bei nur 3 zulässigen Plänen ist der höchste Rang 83,3 %, unter der Schwelle von 90 %."
    assert ev.verdict_card(_card(P_NOPLACE), 90)[1].endswith("(höchster Rang 50 %, Schwelle 90 %).")
    assert "Überstunden-Stunden (Rang 96 %)" in ev.verdict_card(_card(P_PARTIAL), 90)[1] and "(Rang 71 %)" in ev.verdict_card(_card(P_FALSE), 70)[1] and "höchste Überstundenlast einer Person (Rang 71 %)" in ev.verdict_card(_card(P_FALSE), 70)[1]


def test_space_verdict_cases():
    kind, text = ev.verdict_space(_card(P_ALARM))
    assert kind == "warning" and text == ("Der Spielraum (zulässige Pläne bis 2 Kosteneinheiten über dem Optimum des Ziels) hat **2** Pläne; die wahren Kosten des schlechtesten Mitglieds sind das **1,97**-fache "
                                          "des wahren Optimums, des gewählten Plans das 1,97-fache, des besten das 1,54-fache. **2 von 2** Plänen sind schädlich (mindestens das 1,25-fache); eine Stichprobe von 1 Plan aus dem Spielraum findet mit 95 % einen.")
    kind, text = ev.verdict_space(_card(P_TRUE))
    assert kind == "success" and text.endswith("Kein Mitglied ist schädlich (mindestens das 1,25-fache).") and "hat **1** Plan;" in text
    kind, text = ev.verdict_space(_card(P_WIDE))
    assert kind == "warning" and "bis 10 Kosteneinheiten" in text and "hat **47** Pläne" in text and "**1 von 47** Plänen ist schädlich" in text and "eine Stichprobe von 140 Plänen" in text and "**1,26**-fache" in text
    assert "**3** Pläne" in ev.verdict_space(_card(P_WORST))[1] and "**2,21**-fache" in ev.verdict_space(_card(P_WORST))[1] and "des besten das 1,71-fache" in ev.verdict_space(_card(P_WORST))[1]


def test_red_team_verdict_cases():
    assert ev.verdict_redteam(_card(P_ALARM)) == ("info", "Der gewählte Plan ist selbst der schlimmste im Spielraum: die Suche findet nichts Neues (wahre Kosten 311,5, 14 Überstunden-Stunden).")
    kind, text = ev.verdict_redteam(_card(P_WIDE))
    assert kind == "info" and text == ("Das Red Team findet im Spielraum als schlimmsten Plan wahre Kosten **170** gegen 136,75 beim gewählten Plan (1,26-fach gegen 1,02-fach des wahren Optimums), "
                                       "10 gegen 4 Überstunden-Stunden und 3 gegen 1 Aufgaben in Überstunden.")
    assert "wahre Kosten **377,75** gegen 365,5" in ev.verdict_redteam(_card(P_PARTIAL))[1]


def test_sweep_verdicts_carry_the_measured_numbers():
    sw = ev.sweep_all()
    alarm = {f: ev.summary_alarm(r) for f, r in sw.items()}
    text = ev.verdict_alarm_sweep(alarm, "Alarm")[1]
    assert "90 %: Treffer 20, Alarm beim teilweise reparierten Ziel 0, beim wahren Ziel 0" in text and "70 %: Treffer 20, Alarm beim teilweise reparierten Ziel 12, beim wahren Ziel 10" in text
    assert "Überstunden-Stunden 16, Aufgaben in Überstunden 20, Kosten in Überstunden 19, höchste Überstundenlast einer Person 0" in text
    space = {f: {g: ev.summary_space(r, g) for g in C.GOALS} for f, r in sw.items()}
    text = ev.verdict_space_sweep(space)[1]
    assert "s = 0: Pläne im Median 1, schlechtestes / gewähltes / bestes Mitglied 1,87 / 1,73 / 1,66-fach, schädlich in 20 von 20" in text
    dose = {f: ev.summary_dose(r) for f, r in sw.items()}
    text = ev.verdict_dose_sweep(dose)[1]
    assert "0 %: Alarm in 0 von 20" in text and "25 %: Alarm in 19 von 20" in text and "Spearman-Korrelation 0,91 über 80 Instanzen" in text
