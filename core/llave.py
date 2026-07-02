"""
core/llave.py — Generador de HTML para la Llave del Torneo.

Produce un bloque HTML/CSS autocontenido que muestra el bracket
R32 → R16 → Cuartos → Semis → Final con predicciones y resultados reales.
"""

from __future__ import annotations
from typing import Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Estructura del bracket (basada en el sorteo oficial)
# IDs de fixture: 73-88 = R32
# ---------------------------------------------------------------------------
#   Izquierda                  Derecha
#   75 vs 74 -> R16-A           84 vs 87 -> R16-E
#   78 vs 77 -> R16-B           83 vs 86 -> R16-F
#   73 vs 79 -> R16-C           82 vs 85 -> R16-G
#   76 vs 80 -> R16-D           81 vs 88 -> R16-H

BRACKET_LEFT  = [(75, 74), (78, 77), (73, 79), (76, 80)]
BRACKET_RIGHT = [(84, 87), (83, 86), (82, 85), (81, 88)]


_CSS = """
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{background:#ffffff;color:#0d2b52;font-family:Arial,sans-serif;padding:12px;overflow-x:auto}
h2{text-align:center;color:#0d2b52;letter-spacing:2px;font-size:1rem;margin-bottom:16px;text-transform:uppercase}
.bracket{display:flex;align-items:center;justify-content:center;gap:0;min-width:1100px}
.half{display:flex;align-items:center;gap:0}
.round-col{display:flex;flex-direction:column;align-items:center}
.round-label{color:#8a97a6;font-size:.6rem;letter-spacing:1px;text-transform:uppercase;margin-bottom:6px;text-align:center}
.match{background:#f5f8fc;border:1px solid #dbe6f2;border-radius:5px;padding:5px 8px;min-width:130px;max-width:150px;margin:3px 0;cursor:default}
.match:hover{border-color:#b8d4f0}
.team{display:flex;justify-content:space-between;align-items:center;padding:2px 0;font-size:.72rem;color:#4a5a6b}
.team.win{color:#0d2b52;font-weight:700}
.team .tname{flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:90px}
.team .tpct{font-size:.6rem;color:#8a97a6;margin-left:4px}
.divider{border-top:1px solid #dbe6f2;border-bottom:1px solid #dbe6f2;margin:2px 0;padding:2px 0;text-align:center;font-size:.7rem}
.pred-sc{color:#5a6b7d}
.real-sc{color:#0d2b52;font-weight:700;margin-left:4px}
.final-col{display:flex;flex-direction:column;align-items:center;margin:0 8px}
.final-label{color:#0d2b52;font-size:.65rem;letter-spacing:2px;text-transform:uppercase;margin-bottom:6px}
.final-box{background:#e3edf9;border:1.5px solid #1a4d8f;border-radius:6px;padding:6px 10px;min-width:140px;text-align:center}
.cup{font-size:1.5rem;text-align:center;margin-bottom:4px}
.tbd{color:#a0abb8;font-style:italic;font-size:.7rem}
</style>
"""


def _abrev(nombre, max_len=13):
    nombres_cortos = {
        "Bosnia y Herzegovina": "Bosnia",
        "Costa de Marfil": "C. de Marfil",
        "Países Bajos": "P. Bajos",
        "Estados Unidos": "EE. UU.",
        "R.D. Congo": "RD Congo",
        "Nueva Zelanda": "N. Zelanda",
        "Arabia Saudita": "Arabia S.",
        "República Checa": "R. Checa",
    }
    return nombres_cortos.get(nombre, nombre[:max_len])


def _match_box(t1, t2, pred, p1, p2, real, winner, penaltis=None):
    t1s = _abrev(t1)
    t2s = _abrev(t2)
    t1_cls = "team win" if winner == t1 else "team"
    t2_cls = "team win" if winner == t2 else "team"
    pred_html = "<span class='pred-sc'>" + str(pred[0]) + "–" + str(pred[1]) + "</span>"
    if real:
        pen_lbl = " <span style='color:#1a4d8f;font-size:.6rem'>(pen.)</span>" if penaltis else ""
        real_html = "<span class='real-sc'>(" + str(real[0]) + "–" + str(real[1]) + ")</span>" + pen_lbl
    else:
        real_html = ""
    p1_str = str(p1) + "%" if p1 else ""
    p2_str = str(p2) + "%" if p2 else ""
    if t1 == "TBD" and t2 == "TBD":
        return "<div class='match'><div class='tbd'>pendiente</div></div>"
    return (
        "<div class='match'>"
        + "<div class='" + t1_cls + "'><span class='tname'>" + t1s + "</span><span class='tpct'>" + p1_str + "</span></div>"
        + "<div class='divider'>" + pred_html + real_html + "</div>"
        + "<div class='" + t2_cls + "'><span class='tname'>" + t2s + "</span><span class='tpct'>" + p2_str + "</span></div>"
        + "</div>"
    )


def _round_col(label, boxes, gap_px):
    items = "<div style='display:flex;flex-direction:column;gap:" + str(gap_px) + "px;justify-content:space-around'>"
    items += "".join(boxes)
    items += "</div>"
    return (
        "<div style='display:flex;flex-direction:column;align-items:center'>"
        + "<div class='round-label'>" + label + "</div>"
        + items
        + "</div>"
    )


def generar_html_llave(r32_partidos, get_almacen_result, get_pred):
    by_id = {p["id"]: p for p in r32_partidos}

    def _info(pid):
        p = by_id.get(pid)
        if not p:
            return {"t1": "TBD", "t2": "TBD", "pred": [1, 1], "p1": 50, "p2": 50, "real": None, "penaltis": None, "winner": "TBD"}
        stored = get_almacen_result(pid)
        real = stored.get("real") if stored else None
        penaltis = stored.get("penaltis") if stored else None
        pred, p1, p2, pred_winner = get_pred(p["local"], p["visitante"])
        if penaltis == "local":
            winner = p["local"]
        elif penaltis == "visitante":
            winner = p["visitante"]
        elif real and real[0] > real[1]:
            winner = p["local"]
        elif real and real[1] > real[0]:
            winner = p["visitante"]
        else:
            winner = pred_winner if pred_winner else p["local"]
        return {"t1": p["local"], "t2": p["visitante"], "pred": pred, "p1": p1, "p2": p2, "real": real, "penaltis": penaltis, "winner": winner}

    def _future(t1, t2):
        if not t1 or not t2 or t1 == "TBD" or t2 == "TBD":
            return {"t1": t1 or "TBD", "t2": t2 or "TBD", "pred": [1, 1], "p1": 0, "p2": 0, "real": None, "penaltis": None, "winner": "TBD"}
        pred, p1, p2, winner = get_pred(t1, t2)
        return {"t1": t1, "t2": t2, "pred": pred, "p1": p1, "p2": p2, "real": None, "penaltis": None, "winner": winner}

    r32_left  = [(_info(a), _info(b)) for a, b in BRACKET_LEFT]
    r32_right = [(_info(a), _info(b)) for a, b in BRACKET_RIGHT]
    r16_left  = [_future(m1["winner"], m2["winner"]) for m1, m2 in r32_left]
    r16_right = [_future(m1["winner"], m2["winner"]) for m1, m2 in r32_right]
    qf_left   = [_future(r16_left[i]["winner"],  r16_left[i+1]["winner"])  for i in range(0, 4, 2)]
    qf_right  = [_future(r16_right[i]["winner"], r16_right[i+1]["winner"]) for i in range(0, 4, 2)]
    sf_left   = _future(qf_left[0]["winner"],  qf_left[1]["winner"])
    sf_right  = _future(qf_right[0]["winner"], qf_right[1]["winner"])
    final     = _future(sf_left["winner"], sf_right["winner"])

    def _box(m):
        return _match_box(m["t1"], m["t2"], m["pred"], m["p1"], m["p2"], m["real"], m["winner"], m.get("penaltis"))

    r32L_boxes = []
    for m1, m2 in r32_left:
        r32L_boxes.append(_box(m1))
        r32L_boxes.append(_box(m2))
    r16L_boxes = [_box(m) for m in r16_left]
    qfL_boxes  = [_box(m) for m in qf_left]
    sfL_box    = [_box(sf_left)]

    r32R_boxes = []
    for m1, m2 in r32_right:
        r32R_boxes.append(_box(m1))
        r32R_boxes.append(_box(m2))
    r16R_boxes = [_box(m) for m in r16_right]
    qfR_boxes  = [_box(m) for m in qf_right]
    sfR_box    = [_box(sf_right)]

    final_t1 = _abrev(final["t1"]) if final["t1"] != "TBD" else "?"
    final_t2 = _abrev(final["t2"]) if final["t2"] != "TBD" else "?"
    pred_f   = str(final["pred"][0]) + "–" + str(final["pred"][1]) if final["t1"] != "TBD" else "?"
    win_f    = _abrev(final["winner"]) if final["winner"] not in ("TBD", None) else "?"

    final_html = (
        "<div class='final-col'>"
        + "<div class='final-label'>\U0001f3c6 Final</div>"
        + "<div class='final-box'>"
        + "<div class='cup'>\U0001f3c6</div>"
        + "<div style='color:#0d2b52;font-weight:700;font-size:.8rem;margin-bottom:4px'>" + win_f + "</div>"
        + "<div style='color:#5a6b7d;font-size:.7rem'>" + final_t1 + " vs " + final_t2 + "</div>"
        + "<div style='color:#4a5a6b;font-size:.65rem;margin-top:2px'>pred: " + pred_f + "</div>"
        + "</div></div>"
    )

    GAP = {32: 2, 16: 18, 8: 52, 4: 160}

    html = (
        _CSS
        + "<h2>\U0001f3c6 Llave del Mundial 2026</h2>"
        + "<div class='bracket'>"
        + "<div class='half' style='flex-direction:row'>"
        + _round_col("1/16",    r32L_boxes, GAP[32])
        + _round_col("1/8",     r16L_boxes, GAP[16])
        + _round_col("Cuartos", qfL_boxes,  GAP[8])
        + _round_col("Semis",   sfL_box,    GAP[4])
        + "</div>"
        + final_html
        + "<div class='half' style='flex-direction:row-reverse'>"
        + _round_col("1/16",    r32R_boxes, GAP[32])
        + _round_col("1/8",     r16R_boxes, GAP[16])
        + _round_col("Cuartos", qfR_boxes,  GAP[8])
        + _round_col("Semis",   sfR_box,    GAP[4])
        + "</div>"
        + "</div>"
    )
    return html
