"""Eigenschaftstests (ORACLE-PLAYBOOK §5): Aussagen, die für jede Instanz gelten müssen, an festen Seeds und beiden Familien."""

import numpy as np
import pytest

import zka_algorithm as A
import zka_constants as C
import zka_evaluation as ev
import zka_scenario as S

CASES = [(n, m, family, seed) for (n, m) in ((2, 5), (3, 5), (3, 6)) for family in (0, 1) for seed in (3, 4, 5)]


def _a(n, m, family, seed, **kw):
    return ev.analyse(ev.Settings(n=n, m=m, family=family, seed=seed, **kw))


@pytest.mark.parametrize("n,m,family,seed", CASES)
def test_the_playroom_grows_with_the_tolerance_and_contains_the_optimum(n, m, family, seed):
    p = _a(n, m, family, seed).p
    for goal in C.GOALS:
        v = A.goal_values(p, goal, 125)
        opt = A.best(p, v)
        rooms = [A.playroom(p, goal, 125, s).tolist() for s in range(0, 11)]
        assert all(opt in r for r in rooms) and all(set(rooms[k]) <= set(rooms[k + 1]) for k in range(10))
        assert all(p.ok[i] for i in rooms[-1])


@pytest.mark.parametrize("n,m,family,seed", CASES)
def test_ratios_are_ordered_and_the_true_goal_is_the_reference(n, m, family, seed):
    for goal_idx in range(3):
        c = ev.card(_a(n, m, family, seed, goal=goal_idx, s=5))
        sp = c["space"]
        assert sp["ratio_worst"] >= sp["ratio_pick"] >= sp["ratio_best"] >= 1.0 - 1e-12 and sp["harmful"] <= sp["size"] and abs(c["loss"] - (sp["ratio_pick"] - 1.0)) < 1e-9
        if goal_idx == 2:
            assert c["loss"] == 0 and sp["ratio_best"] == 1.0
    assert ev.card(_a(n, m, family, seed, goal=2, s=0))["space"]["ratio_worst"] == 1.0


@pytest.mark.parametrize("n,m,family,seed", CASES)
def test_ranks_are_probabilities_below_the_ceiling_and_the_alarm_is_monotone_in_the_threshold(n, m, family, seed):
    for goal_idx in range(3):
        flags = []
        for thr in range(C.THR_MIN, C.THR_MAX + 1):
            c = ev.card(_a(n, m, family, seed, goal=goal_idx, thr=thr))
            assert all(0.0 <= r["rank"] <= c["max_rank_possible"] + 1e-12 for r in c["rows"])
            flags.append(c["alarm"])
        assert flags == sorted(flags, reverse=True)                                 # höhere Schwelle: nie mehr Alarm


@pytest.mark.parametrize("n,m,family,seed", CASES)
def test_without_overtime_capacity_every_rank_is_one_half_and_nothing_moves(n, m, family, seed):
    c = ev.card(_a(n, m, family, seed, fz=0))
    if c is None:
        pytest.skip("nichts zulässig")
    assert all(r["value"] == 0 and r["rank"] == 0.5 for r in c["rows"]) and not c["alarm"] and c["loss"] == 0


@pytest.mark.parametrize("n,m,family,seed", CASES)
def test_the_kpi_optimum_never_has_a_lower_kpi_than_the_other_goals(n, m, family, seed):
    cs = ev.cards(_a(n, m, family, seed))
    assert cs["kpi"]["pick"]["kpi"] <= cs["kpiz"]["pick"]["kpi"] and cs["kpi"]["pick"]["kpi"] <= cs["true"]["pick"]["kpi"]
    assert cs["true"]["pick"]["true"] <= cs["kpiz"]["pick"]["true"] <= cs["kpi"]["pick"]["true"] + 1e-9 or cs["true"]["pick"]["true"] <= cs["kpi"]["pick"]["true"]


def test_swapping_the_persons_does_not_change_the_card_values():
    inst = S.make_instance(3, 5, 0, 21, 80, 50)
    perm = (2, 0, 1)
    inst2 = S.Instance(3, 5, tuple(inst.a[i] for i in perm), tuple(inst.b[i] for i in perm), inst.cap_r, inst.cap_z)
    p1, p2 = A.build(inst), A.build(inst2)
    for goal in C.GOALS:
        i1, i2 = A.best(p1, A.goal_values(p1, goal, 125)), A.best(p2, A.goal_values(p2, goal, 125))
        assert A.goal_values(p1, goal, 125)[i1] == A.goal_values(p2, goal, 125)[i2]            # der optimale Zielwert hängt nicht von der Nummerierung ab
        assert len(A.playroom(p1, goal, 125, 3)) == len(A.playroom(p2, goal, 125, 3))


def test_everything_is_deterministic():
    s = ev.Settings(n=2, m=5, seed=9, goal=1, s=4, thr=85)
    c1, c2 = ev.card(ev.analyse(s)), ev.card(ev.analyse(s))
    assert c1["pick"]["idx"] == c2["pick"]["idx"] and c1["space"]["idx"].tolist() == c2["space"]["idx"].tolist() and [r["rank"] for r in c1["rows"]] == [r["rank"] for r in c2["rows"]]
    assert C.SWEEP_THRESHOLDS == (70, 80, 90, 95, 99) and C.HOLDOUT_SEEDS[0] == 100100 and len(C.HOLDOUT_SEEDS) == 20 and not set(C.HOLDOUT_SEEDS) & set(C.SWEEP_SEEDS)
