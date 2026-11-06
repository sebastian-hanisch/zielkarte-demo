"""Kern an Handwerten (1 Person, 3 Aufgaben, drei zulässige Pläne): Ziele, Spielraum, Schädlichkeit, nicht gemessene Größen, Rang, Alarm und Ziehungen."""

from fractions import Fraction

import numpy as np
import pytest

import zka_algorithm as A
import zka_evaluation as ev


def test_the_hand_example_has_three_feasible_plans(hand_problem):
    p = hand_problem
    assert p.n_plans == 8 and np.flatnonzero(p.ok).tolist() == [1, 4, 6]
    assert p.kpi[[1, 4, 6]].tolist() == [10, 9, 3] and p.zcost[[1, 4, 6]].tolist() == [3, 4, 10]
    assert A.true_cost(p, 125)[[1, 4, 6]].tolist() == [13.75, 14.0, 15.5]


def test_goals_and_their_optima(hand_problem):
    p = hand_problem
    assert A.goal_values(p, "kpi", 125)[[1, 4, 6]].tolist() == [10.0, 9.0, 3.0]
    assert A.goal_values(p, "kpiz", 125)[[1, 4, 6]].tolist() == [13.0, 13.0, 13.0]       # ohne Zuschlag kosten alle drei 13
    assert A.goal_values(p, "true", 125)[[1, 4, 6]].tolist() == [13.75, 14.0, 15.5]
    assert [A.best(p, A.goal_values(p, g, 125)) for g in ("kpi", "kpiz", "true")] == [6, 1, 1]  # bei Gleichstand der kleinste Index
    with pytest.raises(ValueError):
        A.goal_values(p, "x", 125)


def test_the_playroom_of_each_goal(hand_problem):
    p = hand_problem
    assert A.playroom(p, "kpi", 125, 0).tolist() == [6] and A.playroom(p, "kpi", 125, 5).tolist() == [6]
    assert A.playroom(p, "kpi", 125, 6).tolist() == [4, 6] and A.playroom(p, "kpi", 125, 7).tolist() == [1, 4, 6]
    assert A.playroom(p, "kpiz", 125, 0).tolist() == [1, 4, 6]                           # drei Gleichstände
    assert A.playroom(p, "true", 125, 0).tolist() == [1] and A.playroom(p, "true", 125, 1).tolist() == [1, 4]


def test_harmfulness_is_exact(hand_problem):
    p = hand_problem
    idx = np.array([1, 4, 6])
    assert A.harmful(p, 125, idx, 13.75).tolist() == [False, False, False]              # 14 und 15,5 sind das 1,018- und 1,127-fache
    assert A.harmful(p, 125, idx, 12.4).tolist() == [False, False, True]                # 15,5 >= 1,25 * 12,4 = 15,5: genau auf der Grenze zählt als schädlich
    assert A.harmful(p, 125, idx, 12.5).tolist() == [False, False, False]


def test_shadow_quantities_of_the_feasible_plans(hand_problem):
    sh = A.shadow(hand_problem)
    ok = [1, 4, 6]
    assert sh["zhours"][ok].tolist() == [4, 3, 5] and sh["nz"][ok].tolist() == [1, 1, 2] and sh["zcost"][ok].tolist() == [3, 4, 10] and sh["zmax"][ok].tolist() == [4, 3, 5]


def test_rank_and_alarm_of_the_kpi_optimum(hand_problem):
    p = hand_problem
    sh = A.shadow(p)
    counts = A.rank_counts(sh["zhours"], p.ok, sh["zhours"][6])
    assert counts == (2, 1, 3) and A.rank_value(*counts) == pytest.approx(5 / 6)
    assert A.rank_alarm(*counts, 80) and A.rank_alarm(*counts, 83) and not A.rank_alarm(*counts, 84) and not A.rank_alarm(*counts, 90)   # 500 gegen thr * 6
    assert A.rank_counts(sh["nz"], p.ok, 2) == (2, 1, 3) and A.rank_counts(sh["zcost"], p.ok, 10) == (2, 1, 3)
    assert A.rank_counts(sh["zhours"], p.ok, sh["zhours"][1]) == (1, 1, 3) and A.rank_value(1, 1, 3) == pytest.approx(0.5)


def test_draws_for_a_confidence_is_exact():
    assert A.draws_for(Fraction(0)) is None and A.draws_for(Fraction(1)) == 1 and A.draws_for(Fraction(1, 2)) == 5
    assert (Fraction(1, 2)) ** 5 <= Fraction(1, 20) < (Fraction(1, 2)) ** 4
    assert A.draws_for(Fraction(1, 47)) == 140 and (Fraction(46, 47)) ** 140 <= Fraction(1, 20) < (Fraction(46, 47)) ** 139
    assert A.draws_for(Fraction(1, 2), 99) == 7


def test_the_card_of_the_hand_example(make_hand_analysis):
    c = ev.card(make_hand_analysis(goal=0, s=0, thr=80))
    assert (c["n_ok"], c["pick"]["idx"], c["pick"]["kpi"], c["t_opt"]) == (3, 6, 3, 13.75) and c["alarm"] and c["max_rank_possible"] == pytest.approx(5 / 6)
    assert [r["alarm"] for r in c["rows"]] == [True, True, True, True] and [round(r["rank"], 3) for r in c["rows"]] == [0.833] * 4
    assert c["space"]["size"] == 1 and c["space"]["worst"]["idx"] == 6 and c["space"]["harmful"] == 0 and c["space"]["k95"] is None
    assert c["loss"] == pytest.approx(15.5 / 13.75 - 1)
    c = ev.card(make_hand_analysis(goal=0, s=0, thr=90))
    assert not c["alarm"] and ev.verdict_card(c, 90)[0] == "info" and "kann hier nicht anschlagen" in ev.verdict_card(c, 90)[1]


def test_the_card_of_the_repaired_goal(make_hand_analysis):
    c = ev.card(make_hand_analysis(goal=2, s=0, thr=50))
    assert c["pick"]["idx"] == 1 and c["loss"] == 0 and c["space"]["size"] == 1
    assert [round(r["rank"], 3) for r in c["rows"]] == [0.5, 0.333, 0.167, 0.5]             # Ü-Stunden 4 gegen (4, 3, 5): 1/3 + 1/6; Aufgaben 1 gegen (1, 1, 2): 2/6; Kosten 3 gegen (3, 4, 10): 1/6
    c = ev.card(make_hand_analysis(goal=0, s=7, thr=90))
    assert c["space"]["size"] == 3 and c["space"]["harmful"] == 0 and round(c["space"]["ratio_worst"], 3) == 1.127 and round(c["space"]["ratio_best"], 3) == 1.0 and round(c["space"]["ratio_pick"], 3) == 1.127
    assert c["space"]["pick_is_worst"] and not c["space"]["pick_is_best"]


def test_cards_for_all_three_goals(make_hand_analysis):
    allc = ev.cards(make_hand_analysis(s=7))
    assert list(allc) == ["kpi", "kpiz", "true"] and [allc[g]["pick"]["idx"] for g in allc] == [6, 1, 1]
