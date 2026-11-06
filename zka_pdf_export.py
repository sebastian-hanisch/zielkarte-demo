"""PDF-Export der Zielkarte (fpdf2). Kernschriften sind latin-1: Umlaute gehen, Sonderzeichen werden ersetzt."""

from __future__ import annotations

from fpdf import FPDF

import zka_constants as C
from zka_evaluation import Analysis, card, de, pct, verdict_card, vtext

_REPLACE = {"→": "->", "–": "-", "—": "-", "−": "-", "≤": "<=", "≥": ">=", "·": "*", "×": "x", "„": '"', "“": '"', "²": "2", "∞": "unendlich"}


def _s(text) -> str:
    out = str(text).replace("**", "").replace("`", "")
    for old, new in _REPLACE.items():
        out = out.replace(old, new)
    return out.encode("latin-1", "replace").decode("latin-1")


def build_pdf(a: Analysis) -> bytes:
    s = a.settings
    c = card(a)
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=12)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 15)
    pdf.cell(0, 9, _s("Zielkarte"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 5, _s(f"{s.n} Personen, {s.m} Aufgaben, Familie: {C.FAMILIES[s.family]}, Seed {s.seed}; Ziel: {C.GOAL_NAMES[C.GOALS[s.goal]]}; Zuschlag {s.g} %. Alles simuliert."), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)
    if c is None:
        pdf.multi_cell(0, 5, _s("Mit diesen Kapazitäten ist kein Plan zulässig."), new_x="LMARGIN", new_y="NEXT")
        return bytes(pdf.output())
    pick = c["pick"]
    pdf.multi_cell(0, 5, _s(f"Optimum: Kennzahl {pick['kpi']}, wahre Kosten {vtext(pick['true'])} (wahres Optimum {vtext(c['t_opt'])}, Schaden {pct(c['loss'])}); {c['n_ok']} zulässige Pläne."), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, _s(f"Nicht gemessene Größen (Schwelle {s.thr} %)"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    for r in c["rows"]:
        pdf.multi_cell(0, 5, _s(f"{r['label']}: Wert {r['value']} (Median aller zulässigen {de(r['median'], 1)}, Maximum {r['max']}), Rang {pct(r['rank'], 1)} - {'ALARM' if r['alarm'] else 'kein Alarm'}"), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    sp = c["space"]
    pdf.multi_cell(0, 5, _s(f"Spielraum (bis {sp['slack']} Kosteneinheiten über dem Optimum): {sp['size']} Pläne; wahre Kosten schlechtestes / gewähltes / bestes Mitglied: "
                            f"{de(sp['ratio_worst'], 2)} / {de(sp['ratio_pick'], 2)} / {de(sp['ratio_best'], 2)}-fach des wahren Optimums; schädlich: {sp['harmful']} von {sp['size']}."), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    pdf.multi_cell(0, 5, _s(verdict_card(c, s.thr)[1]), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)
    pdf.set_font("Helvetica", "I", 8)
    pdf.multi_cell(0, 4, _s("Bei Gleichstand gilt der kleinste Index der Aufzählung. Quelle: zielkarte-demo, Sebastian Hanisch."), new_x="LMARGIN", new_y="NEXT")
    return bytes(pdf.output())
