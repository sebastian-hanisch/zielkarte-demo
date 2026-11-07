# Zielkarte – Streamlit-Demo

<!-- TODO nach dem Deploy: direkt hierher den Live-Link setzen (Leerzeile davor und danach):
**[→ Demo live ausprobieren](https://sebastianhanisch-zielkarte-demo.streamlit.app/)** -->

Stück 13 der Linie **Zielfunktionsdesign** („Das Ziel ist das Modell“) in der „Konzepte“-Reihe für die Website „Sebastian Hanisch – Operations Research und Machine Learning“ (Arbeitsname; Name, Bereich und Themenfeld werden erst bei der Einbindung in die Website festgelegt). Es baut auf Stück 1 bis 11 auf (`zielvergleich-demo`, `preis-der-fairness-demo`, `zwei-kriterien-demo`, `lexikographisch-demo`, `gleichstand-demo`, `hart-gegen-weich-demo`, `goodhart-kurve-demo`, `modellluecken-demo`, `verlagerung-demo`, `planstabilitaet-demo`; Stück 7 und 12 sind zurückgestellt) und nimmt das Beispiel von Stück 10: **m Aufgaben werden auf n Personen verteilt**, jede in **Regelzeit** oder **Überstunden**. Gefragt wird, **wie man vor dem Einsatz findet, was ein Ziel zulässt**. Die Demo misst mit bekannter Wahrheit, wie gut zwei Wege einen Fehler des Ziels erkennen würden: das **Red Team** (im Spielraum des Ziels den schlimmsten Plan suchen; setzt voraus, dass man die wahren Kosten der Pläne kennt oder schätzen kann) und den **Extremwert-Test** (wo liegt das Optimum in den Größen, die das Ziel nicht misst; braucht die wahren Kosten nicht), und fasst beides in einer **Zielkarte** zusammen. Alles ist **simuliert**; keine Aussage über echte Dienstpläne, Personen oder Betriebe.

## Warum dieses Problem

Man bekommt einen Plan und sieht eine Kennzahl; ob der Plan etwas ausnutzt, das niemand gemessen hat, sieht man dem Plan nicht an. Die Fragen: Wie groß ist der **Spielraum** eines Ziels, also wie viele Pläne unterscheidet es vom Optimum nicht, und was kosten die wirklich? Findet das **Red Team** darin mehr als der gewählte Plan? Lässt sich ein Ziel **ohne Kenntnis der Wahrheit** prüfen, und wie oft liegt der Test falsch (Treffer, Fehlalarm)? Folgt der Alarm dem Schaden?

## Modell

Gegeben `n` Personen, `m` Aufgaben, Kosten `a[i][j]` (ganze Zahlen) und Zeit `b[i][j]` (1 bis 9). Jede Aufgabe geht an eine Person und in die Regelzeit oder in Überstunden; **alle `(2n)^m` Pläne werden aufgezählt** (bis `6^7 = 279 936`); Kosten und Zeiten sind ganze Zahlen, die wahren Kosten Vielfache von 0,25 und in `float64` ohne Rundung darstellbar; zulässig ist, wer je Person Regellast höchstens `cap_R` und Überstundenlast höchstens `cap_Z` hat (Quelle des Beispiels: `verlagerung-demo`, neu geschrieben). **Drei Ziele:** „nur Kennzahl“ (Kosten der Regelzeit-Aufgaben), „Kennzahl plus Überstundenkosten ohne Zuschlag“ (teilweise repariert) und „wahre Kosten“ (mit Zuschlag `g`, voreingestellt 125 %); bei Gleichstand gilt der kleinste Index. **Spielraum** eines Ziels zur Toleranz `s`: alle zulässigen Pläne mit Zielwert höchstens Optimum plus `s` (Kosteneinheiten). **Schädlich:** wahre Kosten von mindestens dem 1,25-fachen des wahren Optimums. **Red Team:** der Plan im Spielraum mit den größten wahren Kosten. **Extremwert-Test:** für vier Größen, die das Ziel nicht misst (Überstunden-Stunden, Aufgaben in Überstunden, Kosten in Überstunden, höchste Überstundenlast einer Person), der **Mittelwert-Rang** des Optimums unter allen zulässigen Plänen (Anteil der kleineren plus die Hälfte der gleichen); **Alarm**, wenn der Rang in einer Größe mindestens die Schwelle erreicht (voreingestellt 90 %), ganzzahlig exakt. Formeln stehen im 📐-Expander der App.

## Methodik

Zwei Kostenfamilien: **unabhängig** (1 bis 99) und **Personeneffekt** (Personeneffekt 0 bis 40 plus 1 bis 60). Die App zeigt die Zielkarte (die vier Größen mit Wert, Median, Maximum, Rang und Alarm; die drei Ziele nebeneinander), den Spielraum (Zahl der Pläne, wahre Kosten schlechtestes, gewähltes und bestes Mitglied, schädlicher Anteil, Zahl der Ziehungen für 95 % Treffer), das Red Team (schlimmster gegen gewählten Plan), die Trefferquote und den Fehlalarm je Schwelle und den Alarm gegen den Schaden über den Überstundenanteil. Zählungen über 20 feste Instanzen (3 Personen, 7 Aufgaben, alle 279 936 Pläne, zwei Familien) und eine zweite Menge (Seeds 100100 bis 100119) für die Schwelle liegen hinter Schaltern. Verdikte entstehen live aus der Rechnung, jede Zahl im Text kommt aus dem Ergebnis.

## Befunde (gemessen, keine Behauptungen)

Alle Zahlen stammen aus den Auswertungsfunktionen der App und sind in `tests/test_claims.py` nachgerechnet. „Je 20 feste Instanzen“ heißt `SWEEP_SEEDS` (Seeds 100000 bis 100019), nie ein einzelner Seed; die Zahlen sind **Zählungen und Spannen über Instanzen**, kein Satz und keine Aussage über andere Instanzen. Soweit nicht anders angegeben 3 Personen, 7 Aufgaben, `f_R = 80 %`, `f_Z = 50 %`, `g = 125 %`. Familien: unabhängig / Person. Wahre Kosten werden als Vielfache des wahren Optimums angegeben.

| Frage | Befund |
|---|---|
| Spielraum von „nur Kennzahl“: Pläne (Median; Minimum bis Maximum), Toleranz `s` = 0 / 2 / 5 / 10 | unabhängig **1** (1 bis 20) / **2** (1 bis 20) / **3** (1 bis 25) / **5** (1 bis 25); Person 3 (1 bis 6) / 3 (1 bis 8) / 3 (1 bis 15) / 5 (1 bis 15) |
| dabei: wahre Kosten des schlechtesten / gewählten / besten Mitglieds (Median; höchster Wert des schlechtesten), `s` = 0 | unabhängig **1,87 / 1,73 / 1,66** (2,50); Person 1,57 / 1,49 / 1,44 (2,02) |
| dasselbe bei `s` = 10 | unabhängig 1,92 / 1,73 / 1,53 (3,07); Person 1,63 / 1,49 / 1,43 (2,26) |
| dabei: Anteil schädlicher Pläne im Spielraum (Minimum / Median / Maximum), `s` = 0 / 10 | unabhängig 88,9 % / **100,0 %** / 100,0 % und 33,3 % / 100,0 % / 100,0 %; Person 66,7 % / 100,0 % / 100,0 % (bei jedem `s`) |
| dabei: Ziehungen für 95 % Treffer (Minimum / Median / Maximum), `s` = 0 / 10 | unabhängig 1 / **1** / 2 und 1 / 1 / 8; Person 1 / 1 / 3 |
| dabei: der gewählte Plan ist das schlechteste / das beste Mitglied (Instanzen von 20), `s` = 0 / 2 / 5 / 10 | unabhängig 1 / 3 / 3 / 3 und 1 / 2 / 3 / 2; Person 2 / 2 / 4 / 3 und 3 / 5 / 5 / 7 |
| Spielraum von „Kennzahl plus Überstundenkosten“: schlechtestes / gewähltes / bestes Mitglied (Median; höchster Wert), `s` = 0 / 10 | unabhängig **1,05** / 1,00 / 1,00 (1,17) und 1,07 / 1,00 / 1,00 (1,26); Person 1,08 / 1,01 / 1,00 (1,17) und 1,11 / 1,01 / 1,00 (1,20) |
| dabei: Spielräume mit einem schädlichen Plan (von 20), `s` = 0 / 2 / 5 / 10 | unabhängig 0 / 0 / 0 / **1** (ein Plan unter 47, 2,1 %, 140 Ziehungen); Person 0 / 0 / 0 / 0 |
| Spielraum von „wahre Kosten“: schlechtestes Mitglied (Median; höchster Wert), `s` = 0 / 10 | unabhängig 1,00 (1,00) und 1,04 (1,07); Person 1,00 (1,00) und 1,04 (1,06); schädlich in keinem von 20 |
| Extremwert-Test, Ziel „nur Kennzahl“: Rang des Optimums in %, Überstunden-Stunden / Aufgaben in Ü / Kosten in Ü / höchste Überstundenlast (Minimum / Median / Maximum) | unabhängig 52 / **98** / 100, 92 / 100 / 100, 83 / 98 / 100, 14 / 73 / 85; Person 88 / 95 / 100, 93 / 100 / 100, 91 / 99 / 100, 29 / 75 / 86 |
| dasselbe, „Kennzahl plus Überstundenkosten“ | unabhängig 14 / 48 / 90, 7 / 26 / 88, 2 / 14 / 49, 14 / 71 / 85; Person 11 / 37 / 96, 4 / 24 / 68, 1 / 9 / 44, 31 / 72 / 86 |
| dasselbe, „wahre Kosten“ | unabhängig 2 / 47 / 90, 4 / 25 / 58, 1 / 7 / 19, 2 / 70 / 83; Person 3 / 20 / 75, 3 / 7 / 65, 1 / 3 / 12, 7 / 67 / 86 |
| Alarm bei Schwelle 70 / 80 / 90 / 95 / 99 %: Treffer „nur Kennzahl“ (von 20) | unabhängig 20 / 20 / **20** / 19 / 17; Person 20 / 20 / **20** / 19 / 19 |
| dabei: Fehlalarm bei „Kennzahl plus Überstundenkosten“ (von 20) | unabhängig 12 / 5 / **0** / 0 / 0; Person 13 / 8 / **2** / 1 / 0 |
| dabei: Fehlalarm bei „wahre Kosten“ (von 20) | unabhängig 10 / 4 / **0** / 0 / 0; Person 10 / 5 / **0** / 0 / 0 |
| Alarm je Größe bei 90 %, „nur Kennzahl“: Überstunden-Stunden / Aufgaben in Ü / Kosten in Ü / höchste Überstundenlast (von 20) | unabhängig 16 / 20 / 19 / **0**; Person 18 / 20 / 20 / **0**: die durch die Kapazitätsgrenze gedeckelte Größe schlägt hier (Schwelle 90 %, 50 % Überstundenkapazität) in 0 von 20 Instanzen an (blinder Fleck) |
| **Hold-out** (Seeds 100100 bis 100119): Treffer „nur Kennzahl“ bei 70 / 80 / 90 / 95 / 99 % (von 20) | unabhängig 20 / 20 / **20** / 20 / 15; Person 20 / 20 / **20** / 20 / 17 |
| Hold-out: Fehlalarm bei „Kennzahl plus Überstundenkosten“ / bei „wahre Kosten“ (von 20) | unabhängig 8 / 4 / **2** / 1 / 0 und 9 / 2 / **0** / 0 / 0; Person 11 / 7 / **2** / 1 / 0 und 8 / 5 / **2** / 1 / 0 |
| Alarm und Schaden über den Überstundenanteil 0 / 25 / 50 / 100 %, „nur Kennzahl“: Alarm bei 90 % (von 20); Schaden (Median) | unabhängig 0 / 19 / 20 / 20; 0,0 % / 29,8 % / 73,1 % / 135,7 %; Person 0 / 20 / 20 / 20; 0,0 % / 29,0 % / 49,1 % / 83,2 % |
| dabei: größter Rang bei 0 % Überstundenanteil; Spearman-Korrelation zwischen größtem Rang und Schaden | überall 50 %; **0,91** über 80 Punkte (20 Instanzen mal 4 Überstundenanteile; unabhängig und Person je); sie kommt vor allem aus dem Unterschied zwischen den Anteilen (ohne 0 %: 0,80; innerhalb eines Anteils 0,26 bis 0,71) |
| Preset „Das Ziel schlägt an“ (Seed 100000) | 2218 zulässige Pläne; Rang des Optimums 98 % / 100 % / 95 % / 69 %: **Alarm**; Spielraum **2** Pläne, beide schädlich (**1,97**-fach), wahre Kosten **311,5** statt **157,75** (97,5 % mehr); der gewählte Plan ist der schlimmste |
| Preset „Das wahre Ziel schlägt nicht an“ (Toleranz 0) | höchster Rang **69 %**: kein Alarm; Spielraum 1 Plan (1,00-fach) |
| Preset „Teilweise repariert, trotzdem Alarm“ (Person, Seed 100010) | Überstunden-Stunden Rang **96 %**: Alarm bei nur **2,1 %** Schaden; schlechtestes Mitglied 1,06-fach |
| Preset „Kein Ort, kein Schaden“ (Überstundenkapazität 0) | **18** zulässige Pläne, alle Größen 0, Rang 50 %: kein Alarm, kein Schaden |
| Preset „Zu niedrige Schwelle: Fehlalarm“ (Seed 100002, wahres Ziel, Schwelle 70 %) | höchste Überstundenlast Rang **71 %**: Alarm ohne Schaden (bei Schwelle 90 % keiner) |
| Preset „Weiter Spielraum findet einen Schaden“ (Seed 100004, Toleranz 10) | **47** Pläne, **1** schädlich (**1,26**-fach), Optimum selbst 1,02-fach, kein Alarm; **140** Ziehungen für 95 % Treffer; Red Team: 170 statt 136,75 |
| Preset „Der gewählte Plan ist der schlimmste“ (Seed 100011) | **3** Pläne, gewählter **2,21**-fach, bester 1,71-fach |
| Preset „Kleinstes Beispiel (1 Person, 3 Aufgaben)“ (Seed 3) | **3** zulässige Pläne, höchster Rang **83,3 %**: der Test kann bei Schwelle 90 % nicht anschlagen, das Optimum ist 18,4 % zu teuer |

**Korrektur der Planungshypothese:** Die Gliederung hatte „Red Teaming: den Optimierer gezielt gegen das Ziel suchen lassen“ als Kern gesetzt. **Das trägt hier nicht**: der Spielraum ist klein (Median 1 bis 5 Pläne), beim Ziel nur Kennzahl sind im Median alle Mitglieder schädlich (Median 100 %, Minimum 33,3 % bei Toleranz 10), im Median findet schon eine Stichprobe von einem Plan einen schädlichen Plan (höchstens 8 Ziehungen in 40 Instanzen), und die Suche nach dem schlimmsten Mitglied findet beim gebrochenen Ziel bei Toleranz 0 meist nichts über den gewählten Plan hinaus (Median 1,87 gegen 1,73); bei Toleranz 10 findet sie im Mittel 0,19-fach des Optimums mehr (bei Toleranz 0: 0,04, unabhängig). Der Gewinn liegt eher bei den reparierten Zielen. **Was trägt**, ist der Vergleich mit dem, was das Ziel nicht misst: der Extremwert-Test (Treffer 20 von 20, Fehlalarm 0 bis 2 von 20 bei Schwelle 90 %). Zwei Einschränkungen: Die Schwelle 90 % wurde an denselben Instanzen gewählt wie die Zählung; im **Hold-out** bleibt der Treffer bei 20 von 20, der Fehlalarm liegt aber bei 0 bis 2 von 20 (Person: 2 von 20 auch beim wahren Ziel). Und der Test sieht nur, was auf der Liste steht: die höchste Überstundenlast ist durch die Kapazitätsgrenze gedeckelt und schlägt bei Schwelle 90 % und 50 % Überstundenkapazität in diesen Instanzen nicht an. Der Spielraum zeigt, **wie weit das Ziel vom Wahren abweichen darf** (schlechtestes Mitglied im Median 1,87-fach beim gebrochenen und 1,05-fach beim teilweise reparierten Ziel); beim wahren Ziel ist 1,00 bei Toleranz 0 per Definition. Von der Literatur ist nichts gelesen und nichts zitiert (siehe „Ehrliche Grenzen“).

## Ehrliche Grenzen

- **Ein Beispiel:** Der Fehler „Last wandert in eine nicht gemessene Größe“ ist durch den Aufbau groß (der unsichtbare Ort kostet die Kennzahl nichts); andere Fehlerarten (fehlende Nebenbedingung, Rauschen, Instabilität) sind nicht getestet.
- **Die Liste der Größen steht fest:** Der Test sieht nur vier gewählte Größen; die gedeckelte (höchste Überstundenlast) schlägt bei Schwelle 90 % und 50 % Überstundenkapazität nicht an; bei Schwelle 70 % oder größerer Überstundenkapazität schlägt sie an (nachgemessen, nicht Teil der Tests). Wer die Größen wählt, entscheidet, was der Test findet.
- **Schwelle:** 90 % wurde an denselben Instanzen gewählt wie die Zählung; der Hold-out an zweiten Seeds relativiert das, ersetzt aber keine Prüfung am echten Betrieb. Bei Schwelle 70 % schlägt der Test auch bei reparierten Zielen oft an (bis 13 von 20).
- **Genug zulässige Pläne:** Bei `N` zulässigen Plänen ist der höchste Rang `1 − 1/(2N)`; bei wenigen Plänen kann der Test nicht anschlagen (Preset „Kleinstes Beispiel“).
- **Alle Pläne aufgezählt:** bis 279 936; bei großen Problemen bräuchte der Spielraum einen Löser.
- **Gleichstand: kleinster Index:** Der gewählte Plan unter gleich guten wird von der Regel bestimmt, nicht vom Ziel (Stück 5).
- **Keine Literatur:** Zum Red Teaming und zur Prüfung von Zielen sind keine Primärtexte gelesen; die Demo übernimmt daraus nichts.
- **Kein Satz:** Die Zahlen sind Zählungen über 20 feste Instanzen, nicht allgemein.

## Verifikation

Insgesamt 296 Tests (`pytest tests/`), 283 grün und 13 übersprungen (Orakel- und Eigenschaftstests auf Instanzen, in denen nichts zulässig ist).

- **Kern:** Handbeispiel (1 Person, 3 Aufgaben, drei zulässige Pläne) von Hand: Ziele und Optima, Spielraum je Toleranz, Schädlichkeit exakt an der Grenze, nicht gemessene Größen, Ränge 0,833 und 0,5, Alarm an der Schwelle (83 gegen 84 %), Ziehungen für 95 % exakt mit Brüchen; Pläne, Lasten, Zulässigkeit, Ziele, Spielraum, Schädlichkeit, Rang und Alarm gegen reines Python (`itertools.product`, Schleifen, `fractions.Fraction`).
- **Eigenschaften:** der Spielraum wächst mit der Toleranz und enthält das Optimum; schlechtestes ≥ gewähltes ≥ bestes Mitglied ≥ 1; beim wahren Ziel ist der Schaden 0; Ränge liegen unter `1 − 1/(2N)`; der Alarm ist monoton in der Schwelle; ohne Überstundenkapazität sind alle Ränge 0,5; Umnummerieren der Personen ändert die optimalen Zielwerte nicht; Determinismus.
- **Randfälle:** nichts zulässig, genau ein zulässiger Plan, Toleranz über der Spanne, Schwelle an den Grenzen, jede Familie mal jede Größe, jeder Regler am Minimum und Maximum.
- **Verdikte:** reine Funktionen, jede Verzweigung und jede Zahl im Text an Hand- oder Presetwerten (`tests/test_verdicts.py`).
- **Presets:** Vollständigkeit, Werte innerhalb der Reglergrenzen, Standard-Preset gleich Standardeinstellung, kein anderes Preset gleich den Voreinstellungen, und dass jedes Preset zeigt, was sein Name sagt.
- **Oberfläche:** AppTest-Rauchtest (jeder Button, jeder Regler am Minimum und Maximum), jedes Preset, jedes Ziel, jede Familie, Größen, alle Zählungen und der Hold-out, Footer-Test, Layout.
- **Claims:** die Zahlen der Befundtabelle und der Presets in `tests/test_claims.py` (einzelne Sätze der Korrektur der Planungshypothese und der Grenzen werden dort nur als Text geprüft).

## Dateistruktur

| Datei | Zweck |
|---|---|
| `.github/workflows/tests.yml` | CI: Push, Pull Request, wöchentlicher Canary |
| `.gitignore` | venv, Caches, Streamlit-Secrets |
| `.streamlit/config.toml` | Streamlit-Einstellungen (keine Nutzungsstatistik) |
| `app.py` | Streamlit-App |
| `requirements-dev.txt` | Laufzeit plus pytest |
| `requirements.txt` | Laufzeit-Bibliotheken (ungepinnt) |
| `zka_algorithm.py` | Kern: Pläne, Ziele, Spielraum, Schädlichkeit, nicht gemessene Größen, Rang, Alarm, Ziehungen |
| `zka_constants.py` | Regler-Grenzen, feste Annahmen, Farben, Presets |
| `zka_evaluation.py` | Zielkarte, Zählungen, Verdikte |
| `zka_layout.py` | Fester Kopf (Stylesheet) |
| `zka_pdf_export.py` | PDF-Export der Zielkarte |
| `zka_presets.py` | Permalink (Begrenzen), Presets (Schnellstart in der Seitenleiste), Zufalls-Seed-Button |
| `zka_scenario.py` | Instanzen (Kosten, Zeit, Kapazität) |
| `zka_visualization.py` | Plotly-Abbildungen (Achsen gesperrt) |
| `tests/` | Handbeispiel, Orakel, Eigenschaften, Randfälle, Verdikte, Presets, Claims, Layout, AppTest-Smoke-Test, Footer, Laufzeit-Importe |

## Bewusst nicht umgesetzt

- **Keine Verlagerungsmessung:** Wie viel der Verbesserung nur verschoben ist, wenn man die Wahrheit kennt, ist Stück 10; hier wird gezeigt, wie man sie ohne Wahrheit entdeckt.
- **Keine Tests für andere Fehlerarten:** Fehlende Nebenbedingungen (Stück 9) und Instabilität (Stück 11) sind nicht Teil der Zielkarte dieses Stücks.
- **Keine Wahl des Ziels:** Welches Ziel unter welcher Regel gewählt wird, ist Stück 14.
- **Kein Löser:** Alle Pläne sind aufgezählt.
- **Keine Nachbauten der Literatur.**

## Lokal ausführen

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

Gebaut mit Streamlit, Plotly, NumPy und SciPy.

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html).
