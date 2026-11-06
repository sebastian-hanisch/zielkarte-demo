"""Zielkarte, Spielraum, Red Team, Extremwert-Test und Zählungen über feste Instanzen; Verdikte als reine Funktionen (Art, Text): jede Zahl im Text kommt aus der Rechnung.

Gefragt wird: Was lässt ein Ziel zu, und wie findet man das vor dem Einsatz, wenn man die Wahrheit nicht kennt? Der Spielraum eines Ziels ist die Menge der zulässigen Pläne, die höchstens `s`
über dem Optimum liegen; das Red Team sucht darin den Plan mit den größten wahren Kosten; der Extremwert-Test fragt, wo das Optimum in den Größen liegt, die das Ziel nicht misst."""

import math
from dataclasses import dataclass
from fractions import Fraction

import numpy as np
from scipy.stats import spearmanr

import zka_algorithm as A
import zka_constants as C
import zka_scenario as S


def de(x: float, digits: int = 1) -> str:
    """Zahl mit Dezimalkomma; kein „-0,0“."""
    text = f"{x:.{digits}f}"
    if float(text) == 0.0:
        text = f"{0.0:.{digits}f}"
    return text.replace(".", ",")


def pct(x: float, digits: int = 1) -> str:
    """Anteil als Prozent: 0,05 -> „5,0 %“."""
    return de(x * 100.0, digits) + " %"


def vtext(x: float) -> str:
    """Wert ohne Nachkommastellen, wenn ganzzahlig, sonst mit höchstens zwei (Kosten mit Zuschlag 1,25 haben Viertel)."""
    if float(x).is_integer():
        return str(int(x))
    text = de(float(x), 2)
    return text[:-1] if text.endswith("0") else text


@dataclass(frozen=True)
class Settings:
    n: int = C.DEFAULT_N
    m: int = C.DEFAULT_M
    family: int = C.DEFAULT_FAMILY
    seed: int = C.DEFAULT_SEED
    fr: int = C.DEFAULT_FR
    fz: int = C.DEFAULT_FZ
    g: int = C.DEFAULT_G
    goal: int = C.DEFAULT_GOAL
    s: int = C.DEFAULT_S
    thr: int = C.DEFAULT_THR


@dataclass
class Analysis:
    settings: Settings
    p: A.Problem


def analyse(settings: Settings) -> Analysis:
    inst = S.make_instance(settings.n, settings.m, settings.family, settings.seed, settings.fr, settings.fz)
    return Analysis(settings, A.build(inst))


def plan_info(p: A.Problem, idx: int, g: int) -> dict:
    code = p.X[idx].astype(int)
    tasks = [{"task": j + 1, "person": int(c) // 2 + 1, "overtime": bool(int(c) % 2)} for j, c in enumerate(code)]
    return {"idx": idx, "kpi": int(p.kpi[idx]), "true": float(A.true_cost(p, g)[idx]), "zcost": int(p.zcost[idx]), "nz": int(p.nz[idx]), "zhours": int(p.zload[idx].sum()), "zmax": int(p.zload[idx].max()), "tasks": tasks}


def person_text(info: dict) -> str:
    """„A1: P2 R | A2: P1 Ü ...“ (R Regelzeit, Ü Überstunden)."""
    return " | ".join(f"A{t['task']}: P{t['person']} {'Ü' if t['overtime'] else 'R'}" for t in info["tasks"])


def _ratio(x: float, t_opt: float) -> float:
    return x / t_opt if t_opt else 1.0


def card(a: Analysis, goal: str | None = None) -> dict | None:
    """Die Zielkarte eines Ziels: Optimum, nicht gemessene Größen mit Rang und Alarm, Spielraum mit Red-Team-Fund. None, wenn nichts zulässig ist."""
    s, p = a.settings, a.p
    goal = goal or C.GOALS[s.goal]
    ok = p.ok
    if not ok.any():
        return None
    v = A.goal_values(p, goal, s.g)
    pick = A.best(p, v)
    t = A.true_cost(p, s.g)
    t_opt = float(t[ok].min())
    n_ok = int(ok.sum())
    rows = []
    for name, arr in A.shadow(p).items():
        less, equal, total = A.rank_counts(arr, ok, arr[pick])
        rows.append({"name": name, "label": C.QUANTITY_NAMES[name], "value": int(arr[pick]), "median": float(np.median(arr[ok])), "max": int(arr[ok].max()), "rank": A.rank_value(less, equal, total),
                     "alarm": A.rank_alarm(less, equal, total, s.thr)})
    members = A.playroom(p, goal, s.g, s.s)
    bad = A.harmful(p, s.g, members, t_opt)
    worst = int(members[int(np.argmax(t[members]))])
    best_m = int(members[int(np.argmin(t[members]))])
    share = Fraction(int(bad.sum()), len(members))
    return {"goal": goal, "n_plans": p.n_plans, "n_ok": n_ok, "max_rank_possible": 1.0 - 1.0 / (2 * n_ok), "t_opt": t_opt, "pick": plan_info(p, pick, s.g), "rows": rows,
            "alarm": any(r["alarm"] for r in rows), "max_rank": max(r["rank"] for r in rows), "loss": float(t[pick]) / t_opt - 1.0,
            "space": {"size": len(members), "slack": s.s, "idx": members, "ratios": (t[members] / t_opt).tolist(), "ratio_worst": _ratio(float(t[worst]), t_opt), "ratio_pick": _ratio(float(t[pick]), t_opt), "ratio_best": _ratio(float(t[best_m]), t_opt),
                      "harmful": int(bad.sum()), "share": share, "k95": A.draws_for(share), "worst": plan_info(p, worst, s.g), "best": plan_info(p, best_m, s.g), "pick_is_worst": bool(t[pick] == t[worst] and t[worst] > t[best_m]),
                      "pick_is_best": bool(t[pick] == t[best_m] and t[worst] > t[best_m])}}


def cards(a: Analysis) -> dict | None:
    return None if not a.p.ok.any() else {goal: card(a, goal) for goal in C.GOALS}


# --- Zählungen --------------------------------------------------------------------------------------------------------------------------------

def _q3(vals) -> tuple[float, float, float]:
    v = np.asarray(list(vals), dtype=float)
    return (float(v.min()), float(np.median(v)), float(v.max())) if len(v) else (0.0, 0.0, 0.0)


def _goal_record(p: A.Problem, goal: str, g: int, t: np.ndarray, t_opt: float) -> dict:
    ok = p.ok
    v = A.goal_values(p, goal, g)
    pick = A.best(p, v)
    ranks, alarm_q = {}, {}
    counts = {}
    for name, arr in A.shadow(p).items():
        counts[name] = A.rank_counts(arr, ok, arr[pick])
        ranks[name] = A.rank_value(*counts[name])
        alarm_q[name] = A.rank_alarm(*counts[name], 90)
    alarm = {thr: any(A.rank_alarm(*c, thr) for c in counts.values()) for thr in C.SWEEP_THRESHOLDS}
    space = {}
    for slack in C.SWEEP_SLACKS:
        members = A.playroom(p, goal, g, slack)
        bad = A.harmful(p, g, members, t_opt)
        worst, best_m = float(t[members].max()), float(t[members].min())
        space[slack] = {"size": len(members), "ratio_worst": worst / t_opt, "ratio_pick": float(t[pick]) / t_opt, "ratio_best": best_m / t_opt, "harmful": int(bad.sum()),
                        "k95": A.draws_for(Fraction(int(bad.sum()), len(members))), "pick_worst": bool(t[pick] == worst and worst > best_m), "pick_best": bool(t[pick] == best_m and worst > best_m)}
    return {"ranks": ranks, "max_rank": max(ranks.values()), "alarm": alarm, "alarm_q": alarm_q, "space": space}


def _record(family: int, seed: int, dose: bool) -> dict:
    inst = S.make_instance(C.SWEEP_N, C.SWEEP_M, family, seed, C.SWEEP_FR, C.SWEEP_FZ)
    p = A.build(inst)
    g = C.SWEEP_G
    t = A.true_cost(p, g)
    t_opt = float(t[p.ok].min())
    rec = {"family": family, "seed": seed, "goals": {goal: _goal_record(p, goal, g, t, t_opt) for goal in C.GOALS}, "dose": {}}
    if dose:
        for fz in C.SWEEP_FZS:
            q = A.with_caps(p, cap_z=int(math.ceil((fz / 100.0) * p.inst.cap_r)))
            ok = q.ok
            if not ok.any():
                continue
            pick = A.best(q, q.kpi.astype(float))
            counts = [A.rank_counts(arr, ok, arr[pick]) for arr in A.shadow(q).values()]
            to = float(t[ok].min())
            rec["dose"][fz] = {"max_rank": max(A.rank_value(*c) for c in counts), "alarm": any(A.rank_alarm(*c, 90) for c in counts), "loss": float(t[pick]) / to - 1.0}
    return rec


def sweep_all(families=C.SWEEP_FAMILIES, seeds=C.SWEEP_SEEDS, dose: bool = True) -> dict:
    """Je Familie die festen Instanzen (3 Personen, 7 Aufgaben, alle 279 936 Pläne): Ränge, Alarm, Spielraum und Dosis in einem Durchgang."""
    return {fam: [_record(fam, s, dose) for s in seeds] for fam in families}


def summary_space(recs: list[dict], goal: str) -> dict:
    out = {}
    for slack in C.SWEEP_SLACKS:
        sp = [r["goals"][goal]["space"][slack] for r in recs]
        with_harm = [x for x in sp if x["harmful"] > 0]
        out[slack] = {"size": _q3(x["size"] for x in sp), "worst": float(np.median([x["ratio_worst"] for x in sp])), "pick": float(np.median([x["ratio_pick"] for x in sp])), "best": float(np.median([x["ratio_best"] for x in sp])),
                      "worst_max": max(x["ratio_worst"] for x in sp), "share": _q3(x["harmful"] / x["size"] for x in sp), "n_harm": len(with_harm), "k95": _q3(x["k95"] for x in with_harm) if with_harm else None,
                      "pick_worst": sum(x["pick_worst"] for x in sp), "pick_best": sum(x["pick_best"] for x in sp), "seeds": len(sp)}
    return out


def summary_alarm(recs: list[dict]) -> dict:
    out = {}
    for goal in C.GOALS:
        gr = [r["goals"][goal] for r in recs]
        out[goal] = {"alarm": {thr: sum(x["alarm"][thr] for x in gr) for thr in C.SWEEP_THRESHOLDS}, "alarm_q": {q: sum(x["alarm_q"][q] for x in gr) for q in C.QUANTITIES},
                     "ranks": {q: _q3(x["ranks"][q] for x in gr) for q in C.QUANTITIES}, "seeds": len(gr)}
    return out


def summary_dose(recs: list[dict]) -> dict:
    out, all_rank, all_loss = {}, [], []
    for fz in C.SWEEP_FZS:
        d = [r["dose"][fz] for r in recs if fz in r["dose"]]
        out[fz] = {"alarm": sum(x["alarm"] for x in d), "rank": _q3(x["max_rank"] for x in d), "loss": _q3(x["loss"] for x in d), "seeds": len(d)}
        all_rank += [x["max_rank"] for x in d]
        all_loss += [x["loss"] for x in d]
    out["spearman"] = float(spearmanr(all_rank, all_loss)[0])
    out["n"] = len(all_rank)
    return out


# --- Verdikte -------------------------------------------------------------------------------------------------------------------------------------

def verdict_card(c: dict | None, thr: int) -> tuple[str, str]:
    if c is None:
        return "warning", "Mit diesen Kapazitäten ist kein Plan zulässig."
    hits = [r for r in c["rows"] if r["alarm"]]
    if hits:
        cells = ", ".join(f"{r['label']} (Rang {pct(r['rank'], 0)})" for r in hits)
        return "warning", (f"**Alarm:** Das Optimum gehört unter den {c['n_ok']} zulässigen Plänen zu den obersten {100 - thr} % in: {cells} (Schwelle {thr} %). "
                           "Das Ziel misst diese Größen nicht: der Plan nutzt, was ihm niemand begrenzt hat.")
    if c["max_rank_possible"] * 100 < thr:
        return "info", (f"Kein Alarm, aber der Test kann hier nicht anschlagen: bei nur {c['n_ok']} zulässigen Plänen ist der höchste Rang {pct(c['max_rank_possible'], 1)}, unter der Schwelle von {thr} %.")
    return "success", f"Kein Alarm: in keiner der vier nicht gemessenen Größen liegt das Optimum im obersten Bereich (höchster Rang {pct(c['max_rank'], 0)}, Schwelle {thr} %)."


def verdict_space(c: dict | None) -> tuple[str, str]:
    if c is None:
        return "warning", "Mit diesen Kapazitäten ist kein Plan zulässig."
    sp = c["space"]
    base = (f"Der Spielraum (zulässige Pläne bis {sp['slack']} Kosteneinheiten über dem Optimum des Ziels) hat **{sp['size']}** {'Plan' if sp['size'] == 1 else 'Pläne'}; die wahren Kosten des schlechtesten Mitglieds sind das "
            f"**{de(sp['ratio_worst'], 2)}**-fache des wahren Optimums, des gewählten Plans das {de(sp['ratio_pick'], 2)}-fache, des besten das {de(sp['ratio_best'], 2)}-fache. ")
    if sp["harmful"] == 0:
        return "success", base + f"Kein Mitglied ist schädlich (mindestens das {de(C.HARM_PCT / 100, 2)}-fache)."
    return "warning", base + (f"**{sp['harmful']} von {sp['size']}** Plänen {'ist' if sp['harmful'] == 1 else 'sind'} schädlich (mindestens das {de(C.HARM_PCT / 100, 2)}-fache); eine Stichprobe von {sp['k95']} "
                              f"{'Plan' if sp['k95'] == 1 else 'Plänen'} aus dem Spielraum findet mit {C.CONFIDENCE_PCT} % einen.")


def verdict_redteam(c: dict | None) -> tuple[str, str]:
    if c is None:
        return "warning", "Mit diesen Kapazitäten ist kein Plan zulässig."
    sp = c["space"]
    w, p = sp["worst"], c["pick"]
    if w["idx"] == p["idx"]:
        return "info", f"Der gewählte Plan ist selbst der schlimmste im Spielraum: die Suche findet nichts Neues (wahre Kosten {vtext(p['true'])}, {p['zhours']} Überstunden-Stunden)."
    return "info", (f"Das Red Team findet im Spielraum als schlimmsten Plan wahre Kosten **{vtext(w['true'])}** gegen {vtext(p['true'])} beim gewählten Plan "
                    f"({de(sp['ratio_worst'], 2)}-fach gegen {de(sp['ratio_pick'], 2)}-fach des wahren Optimums), {w['zhours']} gegen {p['zhours']} Überstunden-Stunden und {w['nz']} gegen {p['nz']} Aufgaben in Überstunden.")


def verdict_alarm_sweep(res: dict, title: str) -> tuple[str, str]:
    parts = []
    for fam, s in res.items():
        k, z, t = s["kpi"]["alarm"], s["kpiz"]["alarm"], s["true"]["alarm"]
        cells = ", ".join(f"{thr} %: Treffer {k[thr]}, Alarm beim teilweise reparierten Ziel {z[thr]}, beim wahren Ziel {t[thr]}" for thr in C.SWEEP_THRESHOLDS)
        blind = ", ".join(f"{C.QUANTITY_NAMES[q]} {s['kpi']['alarm_q'][q]}" for q in C.QUANTITIES)
        parts.append(f"{C.FAMILIES[fam]}: {cells} (von {s['kpi']['seeds']}); Alarm je Größe beim Ziel „nur Kennzahl“ bei 90 %: {blind}")
    return "info", f"{title}: " + ". ".join(parts) + "."


def verdict_space_sweep(res: dict) -> tuple[str, str]:
    parts = []
    for fam, per_goal in res.items():
        for goal in C.GOALS:
            sp = per_goal[goal]
            cells = ", ".join(f"s = {s}: Pläne im Median {de(sp[s]['size'][1], 0)}, schlechtestes / gewähltes / bestes Mitglied {de(sp[s]['worst'], 2)} / {de(sp[s]['pick'], 2)} / {de(sp[s]['best'], 2)}-fach, schädlich in {sp[s]['n_harm']} von {sp[s]['seeds']}"
                              for s in C.SWEEP_SLACKS)
            parts.append(f"{C.FAMILIES[fam]}, {C.GOAL_NAMES[goal]}: {cells}")
    return "info", "Spielraum (Median über Instanzen, wahre Kosten geteilt durch das wahre Optimum): " + ". ".join(parts) + "."


def verdict_dose_sweep(res: dict) -> tuple[str, str]:
    parts = []
    for fam, s in res.items():
        cells = ", ".join(f"{fz} %: Alarm in {s[fz]['alarm']} von {s[fz]['seeds']}, größter Rang Median {pct(s[fz]['rank'][1], 0)}, Schaden Median {pct(s[fz]['loss'][1])}" for fz in C.SWEEP_FZS)
        parts.append(f"{C.FAMILIES[fam]}: Überstundenanteil {cells}; Spearman-Korrelation {de(s['spearman'], 2)} über {s['n']} Instanzen")
    return "info", "Alarm und Schaden beim Ziel „nur Kennzahl“: " + ". ".join(parts) + "."
