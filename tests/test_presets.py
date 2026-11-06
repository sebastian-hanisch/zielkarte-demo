"""Presets: Vollständigkeit, gültige Werte, Standard-Preset = Standardeinstellungen, und was jedes Preset zeigen soll."""

import zka_constants as C
import zka_evaluation as ev
import zka_presets as P

(P_ALARM, P_TRUE, P_PARTIAL, P_NOPLACE, P_FALSE, P_WIDE, P_WORST, P_SMALL) = list(C.PRESETS)


def _card(name, **over):
    return ev.card(ev.analyse(ev.Settings(**{**C.PRESETS[name], **over})))


def test_every_preset_has_help_and_all_keys():
    assert set(C.PRESETS) == set(C.PRESET_HELP)
    for name, preset in C.PRESETS.items():
        assert set(preset) == set(P.PRESET_KEYS), name
        assert C.PRESET_HELP[name]


def test_preset_values_are_inside_the_slider_bounds():
    for preset in C.PRESETS.values():
        assert C.N_MIN <= preset["n"] <= C.N_MAX and C.M_MIN <= preset["m"] <= C.M_MAX and 0 <= preset["family"] < len(C.FAMILIES) and 0 <= preset["seed"] <= C.SEED_MAX
        assert C.FR_MIN <= preset["fr"] <= C.FR_MAX and (preset["fr"] - C.FR_MIN) % C.FR_STEP == 0 and C.FZ_MIN <= preset["fz"] <= C.FZ_MAX and (preset["fz"] - C.FZ_MIN) % C.FZ_STEP == 0
        assert C.G_MIN <= preset["g"] <= C.G_MAX and (preset["g"] - C.G_MIN) % C.G_STEP == 0 and 0 <= preset["goal"] < len(C.GOALS) and C.S_MIN <= preset["s"] <= C.S_MAX and C.THR_MIN <= preset["thr"] <= C.THR_MAX


def test_default_preset_equals_the_default_settings():
    assert ev.Settings(**C.PRESETS[P_ALARM]) == ev.Settings()


def test_setting_specs_cover_every_preset_key():
    assert set(P.PRESET_KEYS.values()) == set(P.SETTING_SPECS)


def test_no_non_default_preset_equals_the_default_settings():
    """Lehre aus Stück 4: ein Preset, das den Voreinstellungen gleicht, wäre nicht von „nichts geklickt“ zu unterscheiden."""
    for name, preset in C.PRESETS.items():
        if name != P_ALARM:
            assert ev.Settings(**preset) != ev.Settings(), name
    assert len({tuple(sorted(p.items())) for p in C.PRESETS.values()}) == len(C.PRESETS)


def test_alarm_preset_shows_an_alarm_and_a_harmful_playroom():
    c = _card(P_ALARM)
    assert c["alarm"] and c["n_ok"] == 2218 and [r["alarm"] for r in c["rows"]] == [True, True, True, False] and [round(r["rank"] * 100) for r in c["rows"]] == [98, 100, 95, 69]
    assert c["space"]["size"] == 2 and c["space"]["harmful"] == 2 and round(c["space"]["ratio_worst"], 2) == 1.97 and ev.pct(c["loss"]) == "97,5 %" and ev.vtext(c["pick"]["true"]) == "311,5" and ev.vtext(c["t_opt"]) == "157,75"


def test_true_goal_preset_has_no_alarm_and_no_damage():
    c = _card(P_TRUE)
    assert not c["alarm"] and c["loss"] == 0 and c["space"]["size"] == 1 and round(c["max_rank"] * 100) == 69


def test_partial_preset_alarms_at_a_small_damage():
    c = _card(P_PARTIAL)
    assert c["alarm"] and ev.pct(c["loss"]) == "2,1 %" and [r["alarm"] for r in c["rows"]] == [True, False, False, False] and round(c["rows"][0]["rank"] * 100) == 96 and round(c["space"]["ratio_worst"], 2) == 1.06


def test_no_place_preset_has_eighteen_plans_and_ranks_one_half():
    c = _card(P_NOPLACE)
    assert c["n_ok"] == 18 and not c["alarm"] and all(r["rank"] == 0.5 and r["value"] == 0 for r in c["rows"]) and c["loss"] == 0


def test_false_alarm_preset_alarms_on_the_blind_spot_at_the_low_threshold_only():
    c = _card(P_FALSE)
    assert c["alarm"] and [r["alarm"] for r in c["rows"]] == [False, False, False, True] and c["loss"] == 0
    assert not _card(P_FALSE, thr=90)["alarm"] and not _card(P_FALSE, thr=75)["alarm"]


def test_wide_playroom_preset_finds_one_harmful_plan_without_an_alarm():
    c = _card(P_WIDE)
    sp = c["space"]
    assert not c["alarm"] and (sp["size"], sp["harmful"], sp["k95"]) == (47, 1, 140) and round(sp["ratio_worst"], 2) == 1.26 and round(sp["ratio_pick"], 2) == 1.02


def test_worst_preset_has_the_pick_as_the_worst_member():
    sp = _card(P_WORST)["space"]
    assert sp["size"] == 3 and sp["pick_is_worst"] and round(sp["ratio_worst"], 2) == 2.21 and round(sp["ratio_best"], 2) == 1.71


def test_smallest_example_cannot_alarm():
    c = _card(P_SMALL)
    assert c["n_ok"] == 3 and not c["alarm"] and round(c["max_rank_possible"], 3) == 0.833 and ev.pct(c["loss"]) == "18,4 %" and [round(r["rank"], 3) for r in c["rows"]] == [0.833] * 4
