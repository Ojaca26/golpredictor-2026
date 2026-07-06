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
# Orden de pares para cada mitad (izquierda / derecha)
# ---------------------------------------------------------------------------
#   Izquierda                   Derecha
#   75 vs 78 → R16-A (r16_l0)   84 vs 83 → R16-E (r16_r0)
#   73 vs 76 → R16-B (r16_l1)   86 vs 85 → R16-F (r16_r1)
#   74 vs 77 → R16-C (r16_l2)   87 vs 88 → R16-G (r16_r2)
#   79 vs 80 → R16-D (r16_l3)   81 vs 82 → R16-H (r16_r3)
#   R16-A vs R16-B → QF-1       R16-E vs R16-F → QF-3
#   R16-C vs R16-D → QF-2       R16-G vs R16-H → QF-4
#   QF-1 vs QF-2 → SF-IZQ      QF-3 vs QF-4 → SF-DER
#   SF-IZQ vs SF-DER → FINAL

BRACKET_LEFT  = [(75, 78), (73, 76), (74, 77), (79, 80)]
BRACKET_RIGHT = [(84, 83), (86, 85), (87, 88), (81, 82)]


# ---------------------------------------------------------------------------
# Helper HTML
# ---------------------------------------------------------------------------
_CSS = """
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{background:#0f1419;color:#eef2f6;font-family:Arial,sans-serif;padding:12px;overflow-x:auto}
h2{text-align:center;color:#3ddc84;letter-spacing:2px;font-size:1rem;margin-bottom:16px;text-transform:uppercase}
.bracket{display:flex;align-items:center;justify-content:center;gap:0;min-width:1100px}
.half{display:flex;align-items:center;gap:0}
.round-col{display:flex;flex-direction:column;align-items:center}
.round-label{color:#5a6776;font-size:.6rem;letter-spacing:1px;text-transform:uppercase;margin-bottom:6px;text-align:center}
.matches-col{display:flex;flex-direction:column;justify-content:space-around;height:100%}
.match{background:#0e1c2a;border:1px solid #1e2a38;border-radius:5px;padding:5px 8px;min-width:130px;max-width:150px;margin:3px 0;cursor:default}
.match:hover{border-color:#2a3a50}
.team{display:flex;justify-content:space-between;align-items:center;padding:2px 0;font-size:.72rem;color:#9aa7b4}
.team.win{color:#3ddc84;font-weight:700}
.team .tname{flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:90px}
.team .tpct{font-size:.6rem;color:#5a6776;margin-left:4px}
.divider{border-top:1px solid #1e2a38;border-bottom:1px solid #1e2a38;margin:2px 0;padding:2px 0;text-align:center;font-size:.7rem}
.pred-sc{color:#7d8a99}
.real-sc{color:#ffd25a;font-weight:700;margin-left:4px}
.connector{display:flex;flex-direction:column;justify-content:space-around;width:12px}
.conn-line{flex:1;border-right:1px solid #2a3340}
.conn-top{border-top:1px solid #2a3340;border-right:1px solid #2a3340;border-bottom:none}
.conn-bot{border-bottom:1px solid #2a3340;border-right:1px solid #2a3340;border-top:none}
.conn-mid{border-top:none;border-right:none;border-bottom:none;border-left:none;width:12px;height:1px;background:#2a3340;margin:auto 0}
.final-col{display:flex;flex-direction:column;align-items:center;margin:0 8px}
.final-label{color:#3ddc84;font-size:.65rem;letter-spacing:2px;text-transform:uppercase;margin-bottom:6px}
.final-box{background:#13361f;border:1.5px solid #3ddc84;border-radius:6px;padding:6px 10px;min-width:140px;text-align:center}
.cup{font-size:1.5rem;text-align:center;margin-bottom:4px}
.tbd{color:#3a4a5a;font-style:italic;font-size:.7rem}
</style>
"""


def _abrev(nombre: str, max_len: int = 13) -> str:
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

    pred_html = f"<span class='pred-sc'>{pred[0]}–{pred[1]}</span>"
    if real:
        pen_lbl = " <span style='color:#6ab4ff;font-size:.6rem'>(pen.)</span>" if penaltis else ""
        real_html = f"<span class='real-sc'>({real[0]}–{real[1]})</span>" + pen_lbl
    else:
        real_html = ""

    p1_str = f"{p1}%" if p1 else ""
    p2_str = f"{p2}%" if p2 else ""

    if t1 == "TBD" and t2 == "TBD":
        return "<div class='match'><div class='tbd'>pendiente</div></div>"

    return (
        f"<div class='match'>"
        f"<div class='{t1_cls}'><span class='tname'>{t1s}</span><span class='tpct'>{p1_str}</span></div>"
        f"<div class='divider'>{pred_html}{real_html}</div>"
        f"<div class='{t2_cls}'><span class='tname'>{t2s}</span><span class='tpct'>{p2_str}</span></div>"
        f"</div>"
    )


def _connector_pair(count: int, side: str = "right") -> str:
    """Genera líneas conectoras entre rondas."""
    lines = []
    border = "right" if side == "right" else "left"
    for _ in range(count):
        lines.append(
            f"<div style='flex:1;display:flex;flex-direction:column'>"
            f"<div style='flex:1;border-{border}:1px solid #2a3340;border-top:1px solid #2a3340'></div>"
            f"<div style='flex:1;border-{border}:1px solid #2a3340;border-bottom:1px solid #2a3340'></div>"
            f"</div>"
        )
    spacer_h = 20 if count == 4 else (40 if count == 2 else 120)
    return (
        f"<div style='display:flex;flex-direction:column;justify-content:space-around;"
        f"width:14px;height:{spacer_h * count * 2}px'>"
        + "".join(lines)
        + "</div>"
    )


def _h_line(side: str = "right") -> str:
    """Línea horizontal de salida del conector."""
    return (
        f"<div style='display:flex;flex-direction:column;justify-content:space-around;"
        f"width:12px;height:100%'>"
        f"<div style='height:1px;background:#2a3340'></div>"
        f"</div>"
    )


def _round_col(label: str, boxes: list[str], gap_px: int) -> str:
    items = f"<div style='display:flex;flex-direction:column;gap:{gap_px}px;justify-content:space-around'>"
    items += "".join(boxes)
    items += "</div>"
    return (
        f"<div style='display:flex;flex-direction:column;align-items:center'>"
        f"<div class='round-label'>{label}</div>"
        f"{items}"
        f"</div>"
    )


# ---------------------------------------------------------------------------
# Función principal
# ---------------------------------------------------------------------------
def generar_html_llave(
    r32_partidos: list,
    get_almacen_result,       # callable(id) -> dict con .get("real")
    get_pred,                 # callable(local, visitante) -> (pred_score, p1, p2, winner_name)
) -> str:
    """
    Genera el HTML completo del bracket.

    Args:
        r32_partidos: lista de 16 partidos R32 del fixture.
        get_almacen_result: función que recibe id y devuelve dict guardado.
        get_pred: función(local, visitante) → ([g_local, g_visit], p1, p2, winner_str)
    """
    # Indexar partidos por ID
    by_id: Dict[int, dict] = {p["id"]: p for p in r32_partidos}

    def _info(pid: int) -> dict:
        p = by_id.get(pid)
        if not p:
            return {"t1": "TBD", "t2": "TBD", "pred": [1,1], "p1": 50, "p2": 50, "real": None, "penaltis": None, "winner": "TBD"}
        stored = get_almacen_result(pid)
        real = stored.get("real") if stored else None
        penaltis = stored.get("penaltis") if stored else None  # "local" o "visitante"
        pred, p1, p2, pred_winner = get_pred(p["local"], p["visitante"])
        # Determinar ganador: penaltis > resultado real > predicción
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
        return {
            "t1": p["local"], "t2": p["visitante"],
            "pred": pred, "p1": p1, "p2": p2,
            "real": real, "penaltis": penaltis, "winner": winner,
        }

    def _future(t1, t2, bracket_key=None):
        if t1 in ("TBD", None) or t2 in ("TBD", None):
            return {"t1": t1 or "TBD", "t2": t2 or "TBD",
                    "pred": [1,1], "p1": 0, "p2": 0, "real": None, "penaltis": None, "winner": "TBD"}
        pred, p1, p2, pred_winner = get_pred(t1, t2)
        real = None
        penaltis = None
        winner = pred_winner if pred_winner else t1
        if bracket_key:
            stored = get_almacen_result(bracket_key)
            if stored:
                real = stored.get("real")
                penaltis = stored.get("penaltis")
                if penaltis == "local":
                    winner = t1
                elif penaltis == "visitante":
                    winner = t2
                elif real and real[0] > real[1]:
                    winner = t1
                elif real and real[1] > real[0]:
                    winner = t2
        return {"t1": t1, "t2": t2, "pred": pred, "p1": p1, "p2": p2, "real": real, "penaltis": penaltis, "winner": winner}

    # ── R32 data ────────────────────────────────────────────────────────────
    r32_left  = [(_info(a), _info(b)) for a, b in BRACKET_LEFT]   # 4 pares
    r32_right = [(_info(a), _info(b)) for a, b in BRACKET_RIGHT]  # 4 pares

    # ── R16 ─────────────────────────────────────────────────────────────────
    r16_left  = [_future(m1["winner"], m2["winner"], f"r16_l{i}") for i, (m1, m2) in enumerate(r32_left)]
    r16_right = [_future(m1["winner"], m2["winner"], f"r16_r{i}") for i, (m1, m2) in enumerate(r32_right)]

    # ── Cuartos ──────────────────────────────────────────────────────────────
    qf_left  = [_future(r16_left[i]["winner"],  r16_left[i+1]["winner"])  for i in range(0,4,2)]
    qf_right = [_future(r16_right[i]["winner"], r16_right[i+1]["winner"]) for i in range(0,4,2)]

    # ── Semis ────────────────────────────────────────────────────────────────
    sf_left  = _future(qf_left[0]["winner"],  qf_left[1]["winner"])
    sf_right = _future(qf_right[0]["winner"], qf_right[1]["winner"])

    # ── Final ────────────────────────────────────────────────────────────────
    final = _future(sf_left["winner"], sf_right["winner"])

    # ── Construir HTML ───────────────────────────────────────────────────────
    def _box(m: dict) -> str:
        return _match_box(m["t1"], m["t2"], m["pred"], m["p1"], m["p2"], m["real"], m["winner"], m.get("penaltis"))

    def _round_div(label: str, boxes: list, gap: int) -> str:
        return _round_col(label, boxes, gap)

    # LEFT half: R32 → R16 → QF → SF (flowing right toward center)
    r32L_boxes = []
    for m1, m2 in r32_left:
        r32L_boxes.append(_box(m1))
        r32L_boxes.append(_box(m2))

    r16L_boxes = [_box(m) for m in r16_left]
    qfL_boxes  = [_box(m) for m in qf_left]
    sfL_box    = [_box(sf_left)]

    # RIGHT half: R32 → R16 → QF → SF (mirrored, flowing left toward center)
    r32R_boxes = []
    for m1, m2 in r32_right:
        r32R_boxes.append(_box(m1))
        r32R_boxes.append(_box(m2))

    r16R_boxes = [_box(m) for m in r16_right]
    qfR_boxes  = [_box(m) for m in qf_right]
    sfR_box    = [_box(sf_right)]

    # Final box
    final_t1 = _abrev(final["t1"]) if final["t1"] != "TBD" else "?"
    final_t2 = _abrev(final["t2"]) if final["t2"] != "TBD" else "?"
    pred_f   = f"{final['pred'][0]}–{final['pred'][1]}" if final["t1"] != "TBD" else "?"
    win_f    = _abrev(final["winner"]) if final["winner"] not in ("TBD", None) else "?"

    final_html = (
        f"<div class='final-col'>"
        f"<div class='final-label'>\U0001f3c6 Final</div>"
        f"<div class='final-box'>"
        f"<div class='cup'>\U0001f3c6</div>"
        f"<div style='color:#3ddc84;font-weight:700;font-size:.8rem;margin-bottom:4px'>{win_f}</div>"
        f"<div style='color:#7d8a99;font-size:.7rem'>{final_t1} vs {final_t2}</div>"
        f"<div style='color:#9aa7b4;font-size:.65rem;margin-top:2px'>pred: {pred_f}</div>"
        f"</div>"
        f"</div>"
    )

    GAP = {32: 2, 16: 18, 8: 52, 4: 160}

    html = (
        _CSS
        + "<h2>\U0001f3c6 Llave del Mundial 2026</h2>"
        + "<div class='bracket'>"
        + "<div class='half' style='flex-direction:row'>"
        + _round_div("1/16",    r32L_boxes, GAP[32])
        + _round_div("1/8",     r16L_boxes, GAP[16])
        + _round_div("Cuartos", qfL_boxes,  GAP[8])
        + _round_div("Semis",   sfL_box,    GAP[4])
        + "</div>"
        + final_html
        + "<div class='half' style='flex-direction:row-reverse'>"
        + _round_div("1/16",    r32R_boxes, GAP[32])
        + _round_div("1/8",     r16R_boxes, GAP[16])
        + _round_div("Cuartos", qfR_boxes,  GAP[8])
        + _round_div("Semis",   sfR_box,    GAP[4])
        + "</div>"
        + "</div>"
    )

    return html
