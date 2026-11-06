"""Randfälle: nichts zulässig, genau ein zulässiger Plan, Überstundenkapazität null, Toleranz größer als die Spanne, Schwelle an den Grenzen, jede Familie und jeder Regler an den Grenzen."""

import numpy as np
import pytest

import zka_algorithm as A
import zka_constants as C
import zka_evaluation as ev
import zka_scenario as S
from zka_scenario import Instance


def _analysis(inst, **kw):
    return ev.Analysis(ev.Settings(inst.n, inst.m, 0, 0, 80, 50, 125, **kw), A.build(inst))


def test_nothing_feasible_gives_no_card_and_clear_verdicts():
    a = _analysis(Instance(1, 3, ((4, 6, 3),), ((3, 2, 4),), 1, 1))
    assert not a.p.ok.any() and ev.card(a) is None and ev.cards(a) is None
    assert ev.verdict_card(None, 90) == ("warning", "Mit diesen Kapazitäten ist kein Plan zulässig.") and ev.verdict_space(None)[0] == "warning" and ev.verdict_redteam(None)[0] == "warning"
    assert A.playroom(a.p, "kpi", 125, 5).size == 0 and A.best(a.p, A.goal_values(a.p, "kpi", 125)) is None


def test_exactly_one_feasible_plan_has_rank_one_half_and_cannot_alarm():
    a = _analysis(Instance(1, 3, ((4, 6, 3),), ((3, 2, 4),), 5, 4))                       # nur (R, R, Z)
    c = ev.card(a)
    assert c["n_ok"] == 1 and all(r["rank"] == 0.5 for r in c["rows"]) and c["max_rank_possible"] == 0.5 and not c["alarm"]
    assert ev.verdict_card(c, 90)[0] == "info" and c["space"]["size"] == 1 and c["loss"] == 0 and ev.verdict_redteam(c)[0] == "info"


def test_a_tolerance_beyond_the_spread_gives_every_feasible_plan(make_hand_analysis):
    c = ev.card(make_hand_analysis(goal=0, s=10))
    assert c["space"]["size"] == c["n_ok"] == 3 and c["space"]["idx"].tolist() == [1, 4, 6]


def test_the_threshold_at_its_bounds(make_hand_analysis):
    for thr in (C.THR_MIN, C.THR_MAX):
        c = ev.card(make_hand_analysis(goal=0, s=0, thr=thr))
        assert c["alarm"] == (thr <= 83)                                              # Rang 0,833: Alarm nur unterhalb von 83,3 %
        ev.verdict_card(c, thr)


def test_the_two_hundred_percent_surcharge_changes_the_true_goal_only():
    base = ev.analyse(ev.Settings(seed=100003, g=100))
    high = ev.analyse(ev.Settings(seed=100003, g=200))
    assert A.best(base.p, A.goal_values(base.p, "kpi", 100)) == A.best(high.p, A.goal_values(high.p, "kpi", 200))
    assert A.best(base.p, A.goal_values(base.p, "kpiz", 100)) == A.best(high.p, A.goal_values(high.p, "kpiz", 200))   # das teilweise reparierte Ziel hängt nicht von g ab


@pytest.mark.parametrize("n,m", [(1, 3), (1, 7), (2, 4), (3, 3), (3, 7)])
@pytest.mark.parametrize("family", range(len(C.FAMILIES)))
def test_every_size_and_family_runs_every_experiment(n, m, family):
    for goal in range(3):
        a = ev.analyse(ev.Settings(n, m, family, 5, 80, 50, 125, goal, 2, 90))
        c = ev.card(a)
        ev.verdict_card(c, 90)
        ev.verdict_space(c)
        ev.verdict_redteam(c)
        ev.cards(a)


def test_the_slider_extremes_are_valid_settings():
    for fr in (C.FR_MIN, C.FR_MAX):
        for fz in (C.FZ_MIN, C.FZ_MAX):
            for g in (C.G_MIN, C.G_MAX):
                for s in (C.S_MIN, C.S_MAX):
                    for thr in (C.THR_MIN, C.THR_MAX):
                        a = ev.analyse(ev.Settings(2, 4, 0, 7, fr, fz, g, 0, s, thr))
                        c = ev.card(a)
                        ev.verdict_card(c, thr)
                        ev.verdict_space(c)


def test_text_helpers_format_numbers_and_the_plural_of_the_space():
    assert ev.vtext(0.0) == "0" and ev.vtext(2.5) == "2,5" and ev.vtext(311.5) == "311,5" and ev.vtext(157.75) == "157,75" and ev.de(-0.0001, 1) == "0,0" and ev.pct(0.833, 1) == "83,3 %"
    a = ev.analyse(ev.Settings())
    one = ev.verdict_space(ev.card(ev.analyse(ev.Settings(goal=2))))[1]
    assert "hat **1** Plan;" in one
    assert "hat **2** Pläne;" in ev.verdict_space(ev.card(a))[1]
    assert "**1 von 47** Plänen ist schädlich" in ev.verdict_space(ev.card(ev.analyse(ev.Settings(seed=100004, goal=1, s=10))))[1]
    assert "**2 von 2** Plänen sind schädlich" in ev.verdict_space(ev.card(a))[1]
