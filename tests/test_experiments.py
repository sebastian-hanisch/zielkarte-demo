"""Experimente der App: jedes Preset, jede Familie, jedes Ziel, jeder Regler an den Grenzen, jede Größe und alle Zählungen laufen ohne Fehler."""

import os
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import zka_constants as C

APP = str(Path(__file__).resolve().parent.parent / "app.py")
TIMEOUT = int(os.environ.get("APPTEST_TIMEOUT", "300"))


def _app() -> AppTest:
    at = AppTest.from_file(APP, default_timeout=TIMEOUT)
    at.run()
    assert not at.exception, [str(e) for e in at.exception]
    return at


def _texts(at) -> str:
    return " ".join(m.value for kind in ("success", "info", "warning") for m in getattr(at, kind))


@pytest.mark.parametrize("name", list(C.PRESETS))
def test_every_preset_runs_and_shows_a_verdict(name):
    at = _app()
    at.sidebar.button(key=f"preset_{name}").click().run()
    assert not at.exception, (name, [str(e) for e in at.exception])
    assert "Der Spielraum" in _texts(at)


def test_default_preset_shows_the_alarm():
    text = _texts(_app())
    assert "**Alarm:**" in text and "2218 zulässigen Plänen" in text and "hat **2** Pläne" in text and "nichts Neues" in text


@pytest.mark.parametrize("goal", range(len(C.GOALS)))
def test_every_goal_runs(goal):
    at = _app()
    at.sidebar.selectbox(key="goal_select").set_value(goal).run()
    assert not at.exception, [str(e) for e in at.exception]
    assert ("**Alarm:**" in _texts(at)) == (goal == 0)


@pytest.mark.parametrize("family", range(len(C.FAMILIES)))
def test_every_family_runs(family):
    at = _app()
    at.sidebar.selectbox(key="family_select").set_value(family).run()
    assert not at.exception, [str(e) for e in at.exception]


@pytest.mark.parametrize("key,value", [("fr_slider", C.FR_MIN), ("fr_slider", C.FR_MAX), ("fz_slider", C.FZ_MIN), ("fz_slider", C.FZ_MAX), ("g_slider", C.G_MIN), ("g_slider", C.G_MAX),
                                       ("s_slider", C.S_MIN), ("s_slider", C.S_MAX), ("thr_slider", C.THR_MIN), ("thr_slider", C.THR_MAX)])
def test_every_parameter_extreme_runs(key, value):
    at = _app()
    at.sidebar.slider(key=key).set_value(value).run()
    assert not at.exception, [str(e) for e in at.exception]


def test_without_overtime_capacity_there_is_no_alarm():
    at = _app()
    at.sidebar.slider(key="fz_slider").set_value(0).run()
    assert not at.exception and "**Alarm:**" not in _texts(at) and "Kein Alarm" in _texts(at)


@pytest.mark.parametrize("n,m", [(1, 3), (1, 7), (2, 4), (3, 4)])
def test_sizes_run(n, m):
    at = _app()
    at.sidebar.slider(key="n_slider").set_value(n).run()
    at.sidebar.slider(key="m_slider").set_value(m).run()
    assert not at.exception, [str(e) for e in at.exception]
    assert "Der Spielraum" in _texts(at)


def test_the_playroom_and_alarm_counts_run_when_switched_on():
    at = _app()
    for key in ("sweep_space", "sweep_alarm", "sweep_dose"):
        at.toggle(key=key).set_value(True).run()
        assert not at.exception, (key, [str(e) for e in at.exception])
    text = _texts(at)
    assert "Spielraum (Median über Instanzen" in text and "Alarm je Schwelle" in text and "Spearman-Korrelation 0,91 über 80 Punkte (20 Instanzen mal 4 Überstundenanteile)" in text


def test_the_holdout_runs_when_switched_on():
    at = _app()
    at.toggle(key="sweep_holdout").set_value(True).run()
    assert not at.exception, [str(e) for e in at.exception]
    assert "Hold-out: andere Seeds 100100 bis 100119" in _texts(at)
