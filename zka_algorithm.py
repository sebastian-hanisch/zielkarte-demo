"""Kern der Demo (numpy): Aufgaben in Regelzeit oder Überstunden (das Vehikel von Stück 10), drei Ziele, der Spielraum eines Ziels und der Rang des Optimums in nicht gemessenen Größen.

  * `plans`, `Problem`, `build`: alle (2n)^m Pläne; Code je Aufgabe = 2 * Person + Schicht (0 Regelzeit, 1 Überstunden), Reihenfolge von itertools.product (Quelle: verlagerung-demo, neu geschrieben).
  * `goal_values`: die drei Ziele (nur Kennzahl; Kennzahl plus Überstundenkosten ohne Zuschlag; wahre Kosten mit Zuschlag), alle in Vielfachen von 0,25 und damit exakt in float64.
  * `best`: das Optimum (bei Gleichstand der kleinste Index der Aufzählung).
  * `playroom`: der Spielraum eines Ziels = alle zulässigen Pläne mit Zielwert höchstens Optimum + s.
  * `shadow`, `rank_counts`, `rank_alarm`: nicht gemessene Größen und der Mittelwert-Rang des Optimums unter allen zulässigen Plänen; der Alarm-Test ist ganzzahlig exakt.
  * `draws_for`: Zahl der Ziehungen für eine Trefferwahrscheinlichkeit, exakt mit Brüchen.
"""

from dataclasses import dataclass, replace
from fractions import Fraction

import numpy as np

import zka_constants as C
from zka_scenario import Instance

_BIG = np.inf


def plans(n: int, m: int) -> np.ndarray:
    """Alle (2n)^m Pläne (Zeile = Code je Aufgabe), in der Reihenfolge von itertools.product (die erste Aufgabe ist die höchste Stelle)."""
    base = 2 * n
    if n < 1 or m < 1 or base ** m > 300_000:
        raise ValueError(f"n = {n}, m = {m}: Aufzählung nur bis 300 000 Pläne")
    return ((np.arange(base ** m)[:, None] // base ** np.arange(m - 1, -1, -1)[None, :]) % base).astype(np.int8)


@dataclass
class Problem:
    inst: Instance
    X: np.ndarray
    kpi: np.ndarray           # Kosten der Aufgaben in der Regelzeit
    zcost: np.ndarray         # Kosten der Aufgaben in Überstunden
    rload: np.ndarray         # Regellast je Person (N x n)
    zload: np.ndarray         # Überstundenlast je Person
    nz: np.ndarray            # Aufgaben in Überstunden

    @property
    def n_plans(self) -> int:
        return len(self.kpi)

    @property
    def ok(self) -> np.ndarray:
        return (self.rload <= self.inst.cap_r).all(axis=1) & (self.zload <= self.inst.cap_z).all(axis=1)


def build(inst: Instance) -> Problem:
    n, m = inst.n, inst.m
    a, b = inst.arrays()
    X = plans(n, m)
    person, shift = X // 2, X % 2
    idx = np.arange(m)
    ac, bt = a[person, idx], b[person, idx]
    kpi = (ac * (shift == 0)).sum(axis=1)
    zcost = (ac * (shift == 1)).sum(axis=1)
    rload = np.stack([(bt * ((person == i) & (shift == 0))).sum(axis=1) for i in range(n)], axis=1)
    zload = np.stack([(bt * ((person == i) & (shift == 1))).sum(axis=1) for i in range(n)], axis=1)
    return Problem(inst, X, kpi, zcost, rload, zload, (shift == 1).sum(axis=1))


def with_caps(p: Problem, cap_r: int | None = None, cap_z: int | None = None) -> Problem:
    """Dieselbe Instanz mit anderen Kapazitäten (die Lasten bleiben)."""
    inst = replace(p.inst, cap_r=p.inst.cap_r if cap_r is None else int(cap_r), cap_z=p.inst.cap_z if cap_z is None else int(cap_z))
    return Problem(inst, p.X, p.kpi, p.zcost, p.rload, p.zload, p.nz)


def true_cost(p: Problem, g_pct: int) -> np.ndarray:
    """KPI + g * Überstundenkosten, g in Prozent (125 heißt 1,25)."""
    return p.kpi + (g_pct / 100.0) * p.zcost


def goal_values(p: Problem, goal: str, g_pct: int) -> np.ndarray:
    """Zielwert je Plan (kleiner ist besser): nur Kennzahl, Kennzahl plus Überstundenkosten ohne Zuschlag, wahre Kosten mit Zuschlag."""
    if goal == "kpi":
        return p.kpi.astype(float)
    if goal == "kpiz":
        return true_cost(p, C.KPIZ_G)
    if goal == "true":
        return true_cost(p, g_pct)
    raise ValueError(goal)


def best(p: Problem, values: np.ndarray, ok: np.ndarray | None = None) -> int | None:
    """Index des kleinsten Wertes unter den zulässigen Plänen (bei Gleichstand der erste); None, wenn nichts zulässig ist."""
    ok = p.ok if ok is None else ok
    if not ok.any():
        return None
    return int(np.argmin(np.where(ok, values, _BIG)))


def playroom(p: Problem, goal: str, g_pct: int, slack: int) -> np.ndarray:
    """Indizes (aufsteigend) der zulässigen Pläne, deren Zielwert höchstens das Optimum plus slack ist; leer, wenn nichts zulässig ist."""
    ok = p.ok
    if not ok.any():
        return np.array([], dtype=np.int64)
    v = goal_values(p, goal, g_pct)
    opt = v[ok].min()
    return np.flatnonzero(ok & (v <= opt + slack))


def harmful(p: Problem, g_pct: int, idx: np.ndarray, t_opt: float) -> np.ndarray:
    """Welche der Pläne idx haben wahre Kosten von mindestens HARM_PCT Prozent des wahren Optimums? (exakt: Vielfache von 0,25)"""
    return true_cost(p, g_pct)[idx] * 100 >= C.HARM_PCT * t_opt - 1e-9


def draws_for(share: Fraction, confidence_pct: int = C.CONFIDENCE_PCT) -> int | None:
    """Kleinste Zahl k von Ziehungen mit Zurücklegen, sodass mit mindestens confidence Prozent ein schädlicher Plan darunter ist; None, wenn es keinen gibt."""
    if share <= 0:
        return None
    if share >= 1:
        return 1
    miss, k, limit = Fraction(1) - share, 1, Fraction(100 - confidence_pct, 100)
    cur = miss
    while cur > limit:
        cur *= miss
        k += 1
    return k


# --- Nicht gemessene Größen und Rang --------------------------------------------------------------------------------------------------------

def shadow(p: Problem) -> dict[str, np.ndarray]:
    """Die Größen, die die Kennzahl nicht misst: Überstunden-Stunden, Aufgaben in Überstunden, Kosten in Überstunden, höchste Überstundenlast einer Person."""
    return {"zhours": p.zload.sum(axis=1), "nz": p.nz, "zcost": p.zcost, "zmax": p.zload.max(axis=1)}


def rank_counts(values: np.ndarray, ok: np.ndarray, x) -> tuple[int, int, int]:
    """(Zahl der zulässigen Pläne mit kleinerem Wert, mit gleichem Wert, zulässige Pläne gesamt)."""
    v = values[ok]
    return int((v < x).sum()), int((v == x).sum()), int(len(v))


def rank_value(less: int, equal: int, total: int) -> float:
    """Mittelwert-Rang: Anteil kleinerer Pläne plus die Hälfte der gleichen (in 0 bis 1)."""
    return (less + 0.5 * equal) / total


def rank_alarm(less: int, equal: int, total: int, thr_pct: int) -> bool:
    """Alarm, wenn der Mittelwert-Rang mindestens thr Prozent ist; ganzzahlig exakt: (2 * kleiner + gleich) * 100 >= thr * 2 * gesamt."""
    return (2 * less + equal) * 100 >= thr_pct * 2 * total
