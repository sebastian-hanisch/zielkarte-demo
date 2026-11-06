"""Konstanten: Regler-Grenzen, feste Annahmen, Farben und Presets."""

N_MIN, N_MAX, DEFAULT_N = 1, 3, 3             # Personen
M_MIN, M_MAX, DEFAULT_M = 3, 7, 7             # Aufgaben; alle (2n)^m Pläne werden aufgezählt (bis 6^7 = 279 936)
SEED_MAX, DEFAULT_SEED = 999999, 100000
FAMILIES = ("Kosten unabhängig 1 bis 99", "Personeneffekt")
DEFAULT_FAMILY = 0

FR_MIN, FR_MAX, FR_STEP, DEFAULT_FR = 60, 120, 10, 80          # Regelkapazität: aufgerundet fR * (Summe der mittleren Zeiten) / n, fR in Prozent
FZ_MIN, FZ_MAX, FZ_STEP, DEFAULT_FZ = 0, 100, 25, 50           # Überstundenkapazität: aufgerundet fZ * Regelkapazität, fZ in Prozent
G_MIN, G_MAX, G_STEP, DEFAULT_G = 100, 200, 25, 125            # Zuschlag der Überstunden in den wahren Kosten, in Prozent
GOALS = ("kpi", "kpiz", "true")
GOAL_NAMES = {"kpi": "nur Kennzahl (Regelzeit)", "kpiz": "Kennzahl plus Überstundenkosten (ohne Zuschlag)", "true": "wahre Kosten (mit Zuschlag)"}
DEFAULT_GOAL = 0
KPIZ_G = 100                                                   # das teilweise reparierte Ziel: Überstundenkosten ohne Zuschlag
S_MIN, S_MAX, DEFAULT_S = 0, 10, 2                             # Toleranz des Spielraums in Kosteneinheiten
THR_MIN, THR_MAX, THR_STEP, DEFAULT_THR = 70, 99, 1, 90        # Schwelle des Rangs in Prozent
HARM_PCT = 125                                                 # schädlich: wahre Kosten mindestens 125 % des wahren Optimums
CONFIDENCE_PCT = 95                                            # Trefferwahrscheinlichkeit der Stichprobe

QUANTITIES = ("zhours", "nz", "zcost", "zmax")
QUANTITY_NAMES = {"zhours": "Überstunden-Stunden", "nz": "Aufgaben in Überstunden", "zcost": "Kosten in Überstunden", "zmax": "höchste Überstundenlast einer Person"}

SWEEP_SEEDS = tuple(range(100000, 100020))    # feste Instanzen für alle Zählungen: nie ein einzelner Seed als Befund
HOLDOUT_SEEDS = tuple(range(100100, 100120))  # zweite Seed-Menge: die Schwelle 90 % wurde an SWEEP_SEEDS gewählt, hier gegengeprüft
SWEEP_N, SWEEP_M = 3, 7                       # Größe der Zählungen (alle 279 936 Pläne)
SWEEP_FAMILIES = (0, 1)
SWEEP_FR, SWEEP_FZ, SWEEP_G = 80, 50, 125
SWEEP_SLACKS = (0, 2, 5, 10)
SWEEP_THRESHOLDS = (70, 80, 90, 95, 99)
SWEEP_FZS = (0, 25, 50, 100)

COLOR_ALL = "rgba(150,150,150,0.35)"
COLOR_SPACE = "#4c78a8"
COLOR_PICK = "#d8a13a"
COLOR_WORST = "#c0504d"
COLOR_TRUE = "#2F6B65"

PRESETS = {
    "Das Ziel schlägt an": {"n": 3, "m": 7, "family": 0, "seed": 100000, "fr": 80, "fz": 50, "g": 125, "goal": 0, "s": 2, "thr": 90},
    "Das wahre Ziel schlägt nicht an": {"n": 3, "m": 7, "family": 0, "seed": 100000, "fr": 80, "fz": 50, "g": 125, "goal": 2, "s": 0, "thr": 90},
    "Teilweise repariert, trotzdem Alarm": {"n": 3, "m": 7, "family": 1, "seed": 100010, "fr": 80, "fz": 50, "g": 125, "goal": 1, "s": 2, "thr": 90},
    "Kein Ort, kein Schaden": {"n": 3, "m": 7, "family": 0, "seed": 100000, "fr": 80, "fz": 0, "g": 125, "goal": 0, "s": 2, "thr": 90},
    "Zu niedrige Schwelle: Fehlalarm": {"n": 3, "m": 7, "family": 0, "seed": 100002, "fr": 80, "fz": 50, "g": 125, "goal": 2, "s": 2, "thr": 70},
    "Weiter Spielraum findet einen Schaden": {"n": 3, "m": 7, "family": 0, "seed": 100004, "fr": 80, "fz": 50, "g": 125, "goal": 1, "s": 10, "thr": 90},
    "Der gewählte Plan ist der schlimmste": {"n": 3, "m": 7, "family": 0, "seed": 100011, "fr": 80, "fz": 50, "g": 125, "goal": 0, "s": 2, "thr": 90},
    "Kleinstes Beispiel (1 Person, 3 Aufgaben)": {"n": 1, "m": 3, "family": 0, "seed": 3, "fr": 80, "fz": 50, "g": 125, "goal": 0, "s": 2, "thr": 90},
}
PRESET_HELP = {
    "Das Ziel schlägt an": "Das Optimum von „nur Kennzahl“ liegt unter 2218 zulässigen Plänen in Überstunden-Stunden (Rang 98 %), Aufgaben in Überstunden (100 %) und Kosten in Überstunden (95 %) im obersten Bereich: Alarm. Der Spielraum hat 2 Pläne, beide schädlich (1,97-fach).",
    "Das wahre Ziel schlägt nicht an": "Beim wahren Ziel liegt das Optimum in keiner nicht gemessenen Größe über Rang 69 %: kein Alarm; der Spielraum hat 1 Plan (1,00-fach).",
    "Teilweise repariert, trotzdem Alarm": "Auch das Ziel ohne Zuschlag schlägt hier an (Überstunden-Stunden, Rang 96 %), obwohl der Schaden nur 2,1 % beträgt; das schlechteste Mitglied des Spielraums ist das 1,06-fache.",
    "Kein Ort, kein Schaden": "Ohne Überstundenkapazität gibt es nur 18 zulässige Pläne, alle Größen sind 0 (Rang 50 %): kein Alarm und kein Schaden.",
    "Zu niedrige Schwelle: Fehlalarm": "Beim wahren Ziel schlägt der Test bei der Schwelle 70 % an (höchste Überstundenlast, Rang 71 %), obwohl kein Schaden entsteht.",
    "Weiter Spielraum findet einen Schaden": "Bei 10 Einheiten Toleranz hat der Spielraum 47 Pläne, einer ist schädlich (1,26-fach); das Optimum selbst ist harmlos (1,02-fach), es gibt keinen Alarm, und eine Stichprobe bräuchte 140 Ziehungen.",
    "Der gewählte Plan ist der schlimmste": "Im Spielraum von 3 Plänen hat der gewählte die beste Kennzahl und die höchsten wahren Kosten (2,21-fach gegen 1,71-fach des besten).",
    "Kleinstes Beispiel (1 Person, 3 Aufgaben)": "Nur 3 zulässige Pläne: der höchste mögliche Rang ist 83,3 %, der Test kann bei Schwelle 90 % nicht anschlagen, obwohl das Optimum 18,4 % zu teuer ist.",
}
