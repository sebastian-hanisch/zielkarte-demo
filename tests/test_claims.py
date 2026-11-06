"""Jede Zahl aus dem README wird hier nachgerechnet (DEMO-PLAYBOOK §4). Aufzählung und feste Instanzerzeugung sind deterministisch."""

from pathlib import Path

import pytest

import zka_constants as C
import zka_evaluation as ev

README = (Path(__file__).resolve().parent.parent / "README.md").read_text(encoding="utf-8")
(P_ALARM, P_TRUE, P_PARTIAL, P_NOPLACE, P_FALSE, P_WIDE, P_WORST, P_SMALL) = list(C.PRESETS)

d2 = lambda x: ev.de(x, 2)
p0 = lambda x: ev.de(x * 100, 0)


def _claim(text):
    assert text in README, text


def _slash(values, fmt=str):
    return " / ".join(fmt(v) for v in values)


@pytest.fixture(scope="module")
def sw():
    return ev.sweep_all()


@pytest.fixture(scope="module")
def space(sw):
    return {f: {g: ev.summary_space(r, g) for g in C.GOALS} for f, r in sw.items()}


@pytest.fixture(scope="module")
def alarm(sw):
    return {f: ev.summary_alarm(r) for f, r in sw.items()}


def _card(name, **over):
    return ev.card(ev.analyse(ev.Settings(**{**C.PRESETS[name], **over})))


def test_sweep_instances_are_the_documented_ones():
    assert C.SWEEP_SEEDS == tuple(range(100000, 100020)) and (C.SWEEP_N, C.SWEEP_M, C.SWEEP_FR, C.SWEEP_FZ, C.SWEEP_G) == (3, 7, 80, 50, 125) and C.HOLDOUT_SEEDS == tuple(range(100100, 100120))
    _claim("Seeds 100000 bis 100019")
    _claim("Seeds 100100 bis 100119")
    _claim("3 Personen, 7 Aufgaben, `f_R = 80 %`, `f_Z = 50 %`, `g = 125 %`")


def test_playroom_size_claims(space):
    size = lambda f: " / ".join(f"{ev.de(space[f]['kpi'][s]['size'][1], 0)} ({ev.de(space[f]['kpi'][s]['size'][0], 0)} bis {ev.de(space[f]['kpi'][s]['size'][2], 0)})" for s in C.SWEEP_SLACKS)
    assert size(0) == "1 (1 bis 20) / 2 (1 bis 20) / 3 (1 bis 25) / 5 (1 bis 25)" and size(1) == "3 (1 bis 6) / 3 (1 bis 8) / 3 (1 bis 15) / 5 (1 bis 15)"
    _claim("unabhängig **1** (1 bis 20) / **2** (1 bis 20) / **3** (1 bis 25) / **5** (1 bis 25); Person 3 (1 bis 6) / 3 (1 bis 8) / 3 (1 bis 15) / 5 (1 bis 15)")


def test_playroom_cost_claims(space):
    cell = lambda f, goal, s: f"{d2(space[f][goal][s]['worst'])} / {d2(space[f][goal][s]['pick'])} / {d2(space[f][goal][s]['best'])} ({d2(space[f][goal][s]['worst_max'])})"
    assert cell(0, "kpi", 0) == "1,87 / 1,73 / 1,66 (2,50)" and cell(1, "kpi", 0) == "1,57 / 1,49 / 1,44 (2,02)"
    _claim("unabhängig **1,87 / 1,73 / 1,66** (2,50); Person 1,57 / 1,49 / 1,44 (2,02)")
    assert cell(0, "kpi", 10) == "1,92 / 1,73 / 1,53 (3,07)" and cell(1, "kpi", 10) == "1,63 / 1,49 / 1,43 (2,26)"
    _claim("unabhängig 1,92 / 1,73 / 1,53 (3,07); Person 1,63 / 1,49 / 1,43 (2,26)")
    share = lambda f, s: " / ".join(ev.de(x * 100, 1) + " %" for x in space[f]["kpi"][s]["share"])
    assert share(0, 0) == "88,9 % / 100,0 % / 100,0 %" and share(0, 10) == "33,3 % / 100,0 % / 100,0 %" and all(share(1, s) == "66,7 % / 100,0 % / 100,0 %" for s in C.SWEEP_SLACKS)
    _claim("unabhängig 88,9 % / **100,0 %** / 100,0 % und 33,3 % / 100,0 % / 100,0 %; Person 66,7 % / 100,0 % / 100,0 % (bei jedem `s`)")
    k95 = lambda f, s: " / ".join(ev.de(x, 0) for x in space[f]["kpi"][s]["k95"])
    assert (k95(0, 0), k95(0, 10), k95(1, 0)) == ("1 / 1 / 2", "1 / 1 / 8", "1 / 1 / 3") and all(space[f]["kpi"][s]["k95"][2] <= 8 for f in (0, 1) for s in C.SWEEP_SLACKS)
    _claim("unabhängig 1 / **1** / 2 und 1 / 1 / 8; Person 1 / 1 / 3")
    pw = lambda f: " / ".join(str(space[f]["kpi"][s]["pick_worst"]) for s in C.SWEEP_SLACKS)
    pb = lambda f: " / ".join(str(space[f]["kpi"][s]["pick_best"]) for s in C.SWEEP_SLACKS)
    assert (pw(0), pb(0), pw(1), pb(1)) == ("1 / 3 / 3 / 3", "1 / 2 / 3 / 2", "2 / 2 / 4 / 3", "3 / 5 / 5 / 7")
    _claim("unabhängig 1 / 3 / 3 / 3 und 1 / 2 / 3 / 2; Person 2 / 2 / 4 / 3 und 3 / 5 / 5 / 7")


def test_repaired_playroom_claims(space):
    cell = lambda f, goal, s: f"{d2(space[f][goal][s]['worst'])} / {d2(space[f][goal][s]['pick'])} / {d2(space[f][goal][s]['best'])} ({d2(space[f][goal][s]['worst_max'])})"
    assert cell(0, "kpiz", 0) == "1,05 / 1,00 / 1,00 (1,17)" and cell(0, "kpiz", 10) == "1,07 / 1,00 / 1,00 (1,26)" and cell(1, "kpiz", 0) == "1,08 / 1,01 / 1,00 (1,17)" and cell(1, "kpiz", 10) == "1,11 / 1,01 / 1,00 (1,20)"
    _claim("unabhängig **1,05** / 1,00 / 1,00 (1,17) und 1,07 / 1,00 / 1,00 (1,26); Person 1,08 / 1,01 / 1,00 (1,17) und 1,11 / 1,01 / 1,00 (1,20)")
    harm = lambda f: " / ".join(str(space[f]["kpiz"][s]["n_harm"]) for s in C.SWEEP_SLACKS)
    assert (harm(0), harm(1)) == ("0 / 0 / 0 / 1", "0 / 0 / 0 / 0") and space[0]["kpiz"][10]["k95"] == (140.0, 140.0, 140.0) and ev.de(space[0]["kpiz"][10]["share"][2] * 100, 1) == "2,1"
    _claim("unabhängig 0 / 0 / 0 / **1** (ein Plan unter 47, 2,1 %, 140 Ziehungen); Person 0 / 0 / 0 / 0")
    assert (cell(0, "true", 0), cell(0, "true", 10), cell(1, "true", 0), cell(1, "true", 10)) == ("1,00 / 1,00 / 1,00 (1,00)", "1,04 / 1,00 / 1,00 (1,07)", "1,00 / 1,00 / 1,00 (1,00)", "1,04 / 1,00 / 1,00 (1,06)")
    assert all(space[f]["true"][s]["n_harm"] == 0 for f in (0, 1) for s in C.SWEEP_SLACKS)
    _claim("unabhängig 1,00 (1,00) und 1,04 (1,07); Person 1,00 (1,00) und 1,04 (1,06); schädlich in keinem von 20")


def test_rank_claims(alarm):
    ranks = lambda f, goal: ", ".join("/".join(p0(x) for x in alarm[f][goal]["ranks"][q]) for q in C.QUANTITIES).replace("/", " / ")
    assert ranks(0, "kpi") == "52 / 98 / 100, 92 / 100 / 100, 83 / 98 / 100, 14 / 73 / 85" and ranks(1, "kpi") == "88 / 95 / 100, 93 / 100 / 100, 91 / 99 / 100, 29 / 75 / 86"
    _claim("unabhängig 52 / **98** / 100, 92 / 100 / 100, 83 / 98 / 100, 14 / 73 / 85; Person 88 / 95 / 100, 93 / 100 / 100, 91 / 99 / 100, 29 / 75 / 86")
    assert ranks(0, "kpiz") == "14 / 48 / 90, 7 / 26 / 88, 2 / 14 / 49, 14 / 71 / 85" and ranks(1, "kpiz") == "11 / 37 / 96, 4 / 24 / 68, 1 / 9 / 44, 31 / 72 / 86"
    _claim("unabhängig 14 / 48 / 90, 7 / 26 / 88, 2 / 14 / 49, 14 / 71 / 85; Person 11 / 37 / 96, 4 / 24 / 68, 1 / 9 / 44, 31 / 72 / 86")
    assert ranks(0, "true") == "2 / 47 / 90, 4 / 25 / 58, 1 / 7 / 19, 2 / 70 / 83" and ranks(1, "true") == "3 / 20 / 75, 3 / 7 / 65, 1 / 3 / 12, 7 / 67 / 86"
    _claim("unabhängig 2 / 47 / 90, 4 / 25 / 58, 1 / 7 / 19, 2 / 70 / 83; Person 3 / 20 / 75, 3 / 7 / 65, 1 / 3 / 12, 7 / 67 / 86")


def test_alarm_claims(alarm):
    al = lambda f, goal: " / ".join(str(alarm[f][goal]["alarm"][t]) for t in C.SWEEP_THRESHOLDS)
    assert al(0, "kpi") == "20 / 20 / 20 / 19 / 17" and al(1, "kpi") == "20 / 20 / 20 / 19 / 19"
    _claim("unabhängig 20 / 20 / **20** / 19 / 17; Person 20 / 20 / **20** / 19 / 19")
    assert al(0, "kpiz") == "12 / 5 / 0 / 0 / 0" and al(1, "kpiz") == "13 / 8 / 2 / 1 / 0"
    _claim("unabhängig 12 / 5 / **0** / 0 / 0; Person 13 / 8 / **2** / 1 / 0")
    assert al(0, "true") == "10 / 4 / 0 / 0 / 0" and al(1, "true") == "10 / 5 / 0 / 0 / 0"
    _claim("unabhängig 10 / 4 / **0** / 0 / 0; Person 10 / 5 / **0** / 0 / 0")
    per = lambda f: " / ".join(str(alarm[f]["kpi"]["alarm_q"][q]) for q in C.QUANTITIES)
    assert (per(0), per(1)) == ("16 / 20 / 19 / 0", "18 / 20 / 20 / 0") and all(alarm[f][g]["alarm_q"]["zmax"] == 0 for f in (0, 1) for g in C.GOALS)
    _claim("unabhängig 16 / 20 / 19 / **0**; Person 18 / 20 / 20 / **0**: die gedeckelte Größe schlägt nie an (blinder Fleck)")
    _claim("Fehlalarm 0 bis 2 von 20 bei Schwelle 90 %")
    _claim("Bei Schwelle 70 % schlägt der Test auch bei reparierten Zielen oft an (bis 13 von 20)")
    assert max(alarm[f][g]["alarm"][70] for f in (0, 1) for g in ("kpiz", "true")) == 13


def test_holdout_claims():
    ho = {f: ev.summary_alarm(r) for f, r in ev.sweep_all(seeds=C.HOLDOUT_SEEDS, dose=False).items()}
    al = lambda f, goal: " / ".join(str(ho[f][goal]["alarm"][t]) for t in C.SWEEP_THRESHOLDS)
    assert al(0, "kpi") == "20 / 20 / 20 / 20 / 15" and al(1, "kpi") == "20 / 20 / 20 / 20 / 17"
    _claim("unabhängig 20 / 20 / **20** / 20 / 15; Person 20 / 20 / **20** / 20 / 17")
    assert (al(0, "kpiz"), al(0, "true"), al(1, "kpiz"), al(1, "true")) == ("8 / 4 / 2 / 1 / 0", "9 / 2 / 0 / 0 / 0", "11 / 7 / 2 / 1 / 0", "8 / 5 / 2 / 1 / 0")
    _claim("unabhängig 8 / 4 / **2** / 1 / 0 und 9 / 2 / **0** / 0 / 0; Person 11 / 7 / **2** / 1 / 0 und 8 / 5 / **2** / 1 / 0")
    _claim("im **Hold-out** bleibt der Treffer bei 20 von 20, der Fehlalarm liegt aber bei 0 bis 2 von 20 (Person: 2 von 20 auch beim wahren Ziel)")


def test_dose_claims(sw):
    d = {f: ev.summary_dose(r) for f, r in sw.items()}
    cell = lambda f: f"{_slash([d[f][fz]['alarm'] for fz in C.SWEEP_FZS])}; " + _slash([ev.pct(d[f][fz]["loss"][1]) for fz in C.SWEEP_FZS])
    assert cell(0) == "0 / 19 / 20 / 20; 0,0 % / 29,8 % / 73,1 % / 135,7 %" and cell(1) == "0 / 20 / 20 / 20; 0,0 % / 29,0 % / 49,1 % / 83,2 %"
    _claim("unabhängig 0 / 19 / 20 / 20; 0,0 % / 29,8 % / 73,1 % / 135,7 %; Person 0 / 20 / 20 / 20; 0,0 % / 29,0 % / 49,1 % / 83,2 %")
    assert all(d[f][0]["rank"] == (0.5, 0.5, 0.5) for f in (0, 1)) and [d[f]["spearman"] for f in (0, 1)] == pytest.approx([0.913, 0.915], abs=0.001) and d[0]["n"] == d[1]["n"] == 80
    _claim("überall 50 %; **0,91** über 80 Instanzen (unabhängig und Person je)")


def test_preset_claims():
    c = _card(P_ALARM)
    assert c["n_ok"] == 2218 and [round(r["rank"] * 100) for r in c["rows"]] == [98, 100, 95, 69] and c["space"]["size"] == 2 and c["space"]["harmful"] == 2 and d2(c["space"]["ratio_worst"]) == "1,97"
    assert (ev.vtext(c["pick"]["true"]), ev.vtext(c["t_opt"]), ev.pct(c["loss"]), c["space"]["pick_is_worst"]) == ("311,5", "157,75", "97,5 %", True)
    _claim("2218 zulässige Pläne; Rang des Optimums 98 % / 100 % / 95 % / 69 %: **Alarm**; Spielraum **2** Pläne, beide schädlich (**1,97**-fach), wahre Kosten **311,5** statt **157,75** (97,5 % mehr); der gewählte Plan ist der schlimmste")
    c = _card(P_TRUE)
    assert not c["alarm"] and round(c["max_rank"] * 100) == 69 and c["space"]["size"] == 1
    _claim("höchster Rang **69 %**: kein Alarm; Spielraum 1 Plan (1,00-fach)")
    c = _card(P_PARTIAL)
    assert c["alarm"] and round(c["rows"][0]["rank"] * 100) == 96 and ev.pct(c["loss"]) == "2,1 %" and d2(c["space"]["ratio_worst"]) == "1,06"
    _claim("Überstunden-Stunden Rang **96 %**: Alarm bei nur **2,1 %** Schaden; schlechtestes Mitglied 1,06-fach")
    c = _card(P_NOPLACE)
    assert c["n_ok"] == 18 and not c["alarm"] and all(r["value"] == 0 and r["rank"] == 0.5 for r in c["rows"])
    _claim("**18** zulässige Pläne, alle Größen 0, Rang 50 %: kein Alarm, kein Schaden")
    c = _card(P_FALSE)
    assert c["alarm"] and round(c["rows"][3]["rank"] * 100) == 71 and c["loss"] == 0 and not _card(P_FALSE, thr=90)["alarm"]
    _claim("höchste Überstundenlast Rang **71 %**: Alarm ohne Schaden (bei Schwelle 90 % keiner)")
    c = _card(P_WIDE)
    assert (c["space"]["size"], c["space"]["harmful"], c["space"]["k95"], d2(c["space"]["ratio_worst"]), d2(c["space"]["ratio_pick"]), c["alarm"]) == (47, 1, 140, "1,26", "1,02", False)
    assert (ev.vtext(c["space"]["worst"]["true"]), ev.vtext(c["pick"]["true"])) == ("170", "136,75")
    _claim("**47** Pläne, **1** schädlich (**1,26**-fach), Optimum selbst 1,02-fach, kein Alarm; **140** Ziehungen für 95 % Treffer; Red Team: 170 statt 136,75")
    sp = _card(P_WORST)["space"]
    assert sp["size"] == 3 and d2(sp["ratio_worst"]) == "2,21" and d2(sp["ratio_best"]) == "1,71" and sp["pick_is_worst"]
    _claim("**3** Pläne, gewählter **2,21**-fach, bester 1,71-fach")
    c = _card(P_SMALL)
    assert c["n_ok"] == 3 and not c["alarm"] and ev.pct(c["max_rank_possible"]) == "83,3 %" and ev.pct(c["loss"]) == "18,4 %"
    _claim("**3** zulässige Pläne, höchster Rang **83,3 %**: der Test kann bei Schwelle 90 % nicht anschlagen, das Optimum ist 18,4 % zu teuer")


def test_correction_claims(space, alarm):
    assert space[0]["kpi"][0]["worst"] > space[0]["kpi"][0]["pick"] and d2(space[0]["kpi"][0]["worst"]) == "1,87" and d2(space[0]["kpi"][0]["pick"]) == "1,73"
    _claim("(1,87 gegen 1,73)")
    assert d2(space[0]["kpiz"][0]["worst"]) == "1,05" and d2(space[0]["true"][0]["worst"]) == "1,00"
    _claim("(1,87-fach beim gebrochenen, 1,05 beim teilweise reparierten, 1,00 beim wahren Ziel)")
    _claim("(Median 1 bis 5 Pläne)")
    _claim("(Treffer 20 von 20, Fehlalarm 0 bis 2 von 20 bei Schwelle 90 %)")
    _claim("`1 − 1/(2N)`")
