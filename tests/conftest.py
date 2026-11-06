"""Gemeinsame Fixtures: das Handbeispiel (1 Person, 3 Aufgaben, wie in Stück 10), an dem jede Einheit von Hand geprüft wird (DEMO-PLAYBOOK §1b)."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import zka_algorithm as A  # noqa: E402
import zka_evaluation as ev  # noqa: E402
from zka_scenario import Instance  # noqa: E402


def make_hand() -> Instance:
    return Instance(n=1, m=3, a=((4, 6, 3),), b=((3, 2, 4),), cap_r=6, cap_z=5)


@pytest.fixture
def hand() -> Instance:
    """Handbeispiel: Kosten (4, 6, 3), Zeit (3, 2, 4), Regelkapazität 6 h, Überstundenkapazität 5 h. Zulässig sind nur drei der acht Pläne:
    1 (R,R,Z): KPI 10, Ü-Kosten 3, Ü-Stunden 4, 1 Aufgabe in Ü, wahr (1,25) 13,75; 4 (Z,R,R): KPI 9, Ü-Kosten 4, Ü-Stunden 3, 1 Aufgabe, wahr 14; 6 (Z,Z,R): KPI 3, Ü-Kosten 10, Ü-Stunden 5, 2 Aufgaben, wahr 15,5."""
    return make_hand()


@pytest.fixture
def hand_problem(hand) -> A.Problem:
    return A.build(hand)


def hand_analysis(p, **kw) -> ev.Analysis:
    return ev.Analysis(ev.Settings(1, 3, 0, 0, 80, 50, 125, **kw), p)


@pytest.fixture
def make_hand_analysis(hand_problem):
    return lambda **kw: hand_analysis(hand_problem, **kw)
