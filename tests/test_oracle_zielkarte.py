"""Orakel (ORACLE-PLAYBOOK §5): reines Python (`itertools.product`, Schleifen, `fractions.Fraction`), keine numpy-Zeile im Referenzweg.

Jeder Plan wird einzeln gerechnet (Schicht je Aufgabe, Lasten, Zulässigkeit, Kennzahl, Kosten in Überstunden), Ziele und Zuschlag exakt als Brüche; daraus Optimum,
Spielraum, Schädlichkeit, nicht gemessene Größen, Mittelwert-Rang und Alarm. Verglichen wird mit dem numpy-Kern und der Zielkarte."""

import itertools
from fractions import Fraction

import pytest

import zka_algorithm as A
import zka_evaluation as ev
import zka_scenario as S

CASES = [(n, m, family, seed) for (n, m) in ((1, 4), (2, 3), (2, 4)) for family in (0, 1) for seed in (1, 2, 3)]


def _ref_plans(inst):
    """Alle Pläne in der Reihenfolge von itertools.product: je Aufgabe (Person, Schicht)."""
    n, m = inst.n, inst.m
    out = []
    for code in itertools.product(range(2 * n), repeat=m):
        kpi = zc = 0
        rl, zl = [0] * n, [0] * n
        for j, c in enumerate(code):
            person, shift = c // 2, c % 2
            if shift == 0:
                kpi += inst.a[person][j]
                rl[person] += inst.b[person][j]
            else:
                zc += inst.a[person][j]
                zl[person] += inst.b[person][j]
        ok = all(x <= inst.cap_r for x in rl) and all(x <= inst.cap_z for x in zl)
        out.append({"kpi": kpi, "zc": zc, "zh": sum(zl), "nz": sum(c % 2 for c in code), "zmax": max(zl), "ok": ok})
    return out


def _goal(pl, goal, g):
    return {"kpi": Fraction(pl["kpi"]), "kpiz": Fraction(pl["kpi"] + pl["zc"]), "true": pl["kpi"] + Fraction(g, 100) * pl["zc"]}[goal]


def _mid(values, x):
    return (Fraction(sum(1 for v in values if v < x)) + Fraction(sum(1 for v in values if v == x), 2)) / len(values)


@pytest.mark.parametrize("n,m,family,seed", CASES)
def test_plans_loads_and_feasibility_match_the_loops(n, m, family, seed):
    inst = S.make_instance(n, m, family, seed, 80, 50)
    ref = _ref_plans(inst)
    p = A.build(inst)
    assert p.kpi.tolist() == [x["kpi"] for x in ref] and p.zcost.tolist() == [x["zc"] for x in ref] and p.nz.tolist() == [x["nz"] for x in ref]
    assert p.zload.sum(axis=1).tolist() == [x["zh"] for x in ref] and p.ok.tolist() == [x["ok"] for x in ref]


@pytest.mark.parametrize("n,m,family,seed", CASES)
@pytest.mark.parametrize("fz", [25, 50, 100])
def test_optimum_playroom_and_harm_match_exact_fractions(n, m, family, seed, fz):
    inst = S.make_instance(n, m, family, seed, 80, fz)
    ref = _ref_plans(inst)
    p = A.build(inst)
    ok = [i for i, x in enumerate(ref) if x["ok"]]
    if not ok:
        pytest.skip("nichts zulässig")
    g = 125
    t_opt = min(_goal(ref[i], "true", g) for i in ok)
    for goal in ("kpi", "kpiz", "true"):
        v = {i: _goal(ref[i], goal, g) for i in ok}
        best = min(ok, key=lambda i: (v[i], i))
        assert A.best(p, A.goal_values(p, goal, g)) == best
        for s in (0, 2, 5, 10):
            room = [i for i in ok if v[i] <= min(v.values()) + s]
            assert A.playroom(p, goal, g, s).tolist() == room
            bad = [i for i in room if _goal(ref[i], "true", g) * 100 >= 125 * t_opt]
            assert A.harmful(p, g, A.playroom(p, goal, g, s), float(t_opt)).tolist() == [i in bad for i in room]


@pytest.mark.parametrize("n,m,family,seed", CASES)
def test_ranks_alarms_and_the_card_match_exact_fractions(n, m, family, seed):
    inst = S.make_instance(n, m, family, seed, 80, 50)
    ref = _ref_plans(inst)
    ok = [i for i, x in enumerate(ref) if x["ok"]]
    if not ok:
        pytest.skip("nichts zulässig")
    a = ev.Analysis(ev.Settings(n, m, family, seed, 80, 50, 125, 0, 2, 90), A.build(inst))
    for goal_idx, goal in enumerate(("kpi", "kpiz", "true")):
        v = {i: _goal(ref[i], goal, 125) for i in ok}
        pick = min(ok, key=lambda i: (v[i], i))
        c = ev.card(ev.Analysis(ev.Settings(n, m, family, seed, 80, 50, 125, goal_idx, 2, 90), a.p))
        assert c["pick"]["idx"] == pick and c["n_ok"] == len(ok)
        for row in c["rows"]:
            key = {"zhours": "zh", "nz": "nz", "zcost": "zc", "zmax": "zmax"}[row["name"]]
            values = [ref[i][key] for i in ok]
            r = _mid(values, ref[pick][key])
            assert row["rank"] == pytest.approx(float(r)) and row["value"] == ref[pick][key]
            for thr in (70, 80, 90, 95, 99):
                less, equal, total = A.rank_counts(A.shadow(a.p)[row["name"]], a.p.ok, ref[pick][key])
                assert A.rank_alarm(less, equal, total, thr) == (r * 100 >= thr)             # ganzzahliger Test gegen den Bruch
        assert c["alarm"] == any(row["alarm"] for row in c["rows"])


def test_draws_for_matches_a_loop_over_k():
    for num in range(1, 60):
        for den in (num, num + 1, 2 * num + 3, 47):
            share = Fraction(num, max(den, num))
            k = A.draws_for(share)
            if share >= 1:
                assert k == 1
            else:
                assert (1 - share) ** k <= Fraction(1, 20) and (k == 1 or (1 - share) ** (k - 1) > Fraction(1, 20))
