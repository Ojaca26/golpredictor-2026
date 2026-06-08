"""
Análisis post-partido: compara el marcador predicho contra el real y explica
qué pasó, cuántos puntos se habrían obtenido, y por qué.
"""

from __future__ import annotations
from typing import Optional, Tuple, Dict

from core.predictor import Reglas, puntos_de_pronostico


def analizar_resultado(
    pred: Tuple[int, int],
    real: Tuple[int, int],
    en_eliminatorias: bool,
) -> Dict:
    """Devuelve desglose de puntos y un veredicto legible."""
    reglas = Reglas.eliminatorias() if en_eliminatorias else Reglas.primera_ronda()
    pl, pv = pred
    rl, rv = real

    pts = puntos_de_pronostico(pl, pv, rl, rv, reglas)

    acerto_resultado = ((pl > pv) - (pl < pv)) == ((rl > rv) - (rl < rv))
    acerto_local = pl == rl
    acerto_visit = pv == rv
    acerto_dif = (pl - pv) == (rl - rv)
    exacto = (pl, pv) == (rl, rv)

    if exacto:
        veredicto = "MARCADOR EXACTO — puntaje pleno."
    elif acerto_resultado and acerto_dif:
        veredicto = "Acertaste ganador y diferencia de goles."
    elif acerto_resultado:
        veredicto = "Acertaste el ganador/empate."
    elif acerto_local or acerto_visit:
        veredicto = "Fallaste el resultado, pero acertaste goles de un equipo."
    else:
        veredicto = "No hubo acierto en este partido."

    return {
        "puntos": pts,
        "max_posible": 20 if en_eliminatorias else 10,
        "exacto": exacto,
        "acerto_resultado": acerto_resultado,
        "acerto_goles_local": acerto_local,
        "acerto_goles_visitante": acerto_visit,
        "acerto_diferencia": acerto_dif,
        "veredicto": veredicto,
    }
