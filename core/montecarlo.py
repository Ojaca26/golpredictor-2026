"""
core/montecarlo.py
Simulacion Monte Carlo del Mundial 2026.

Simula el torneo N veces usando el modelo de Poisson bivariado y devuelve
probabilidades de clasificacion y campeonato por equipo.

Flujo:
  1. Fase de grupos: simula todos los partidos round-robin de cada grupo.
     Clasifica los 2 primeros por puntos / diferencia de goles / goles a favor.
  2. Eliminatorias: bracket estandar hasta la final.
  3. Estadisticas: % de veces que cada equipo clasifica, llega a semis, final, campeon.
"""

from __future__ import annotations
import math
import random
from collections import defaultdict
from typing import Dict, List, Tuple

from core.equipos import get_fuerza


# ---------------------------------------------------------------------------
# Generador de Poisson (sin dependencias externas)
# ---------------------------------------------------------------------------
def _muestra_poisson(lam: float) -> int:
    """Genera un valor de distribucion de Poisson con media lam (algoritmo Knuth)."""
    L = math.exp(-max(0.01, lam))
    k, p = 0, 1.0
    while p > L:
        k += 1
        p *= random.random()
    return k - 1


def _simular_goles(local: str, visitante: str) -> Tuple[int, int]:
    """Devuelve (goles_local, goles_visitante) simulados con Poisson."""
    fl = get_fuerza(local)
    fv = get_fuerza(visitante)
    MEDIA = 1.35
    VENTAJA = 1.10
    lam_l = max(0.2, min(MEDIA * fl.ataque * fv.defensa * VENTAJA, 4.5))
    lam_v = max(0.2, min(MEDIA * fv.ataque * fl.defensa, 4.5))
    return _muestra_poisson(lam_l), _muestra_poisson(lam_v)


# ---------------------------------------------------------------------------
# Logica de grupos
# ---------------------------------------------------------------------------
def _clasificar(equipos: List[str], matches: List[Tuple[str, str]]) -> List[str]:
    """
    Simula todos los partidos de un grupo y devuelve la lista ordenada
    (1ro, 2do, 3ro, 4to) segun puntos > diferencia de goles > goles a favor.
    """
    pts: Dict[str, int] = defaultdict(int)
    gf: Dict[str, int] = defaultdict(int)
    gc: Dict[str, int] = defaultdict(int)

    for loc, vis in matches:
        gl, gv = _simular_goles(loc, vis)
        gf[loc] += gl
        gc[loc] += gv
        gf[vis] += gv
        gc[vis] += gl
        if gl > gv:
            pts[loc] += 3
        elif gl == gv:
            pts[loc] += 1
            pts[vis] += 1
        else:
            pts[vis] += 3

    return sorted(equipos,
                  key=lambda e: (pts[e], gf[e] - gc[e], gf[e]),
                  reverse=True)


def _partidos_grupo(equipos: List[str]) -> List[Tuple[str, str]]:
    """Genera todos los partidos round-robin del grupo."""
    return [(equipos[i], equipos[j])
            for i in range(len(equipos))
            for j in range(i + 1, len(equipos))]


# ---------------------------------------------------------------------------
# Simulacion de eliminatorias
# ---------------------------------------------------------------------------
def _ganador_partido(a: str, b: str) -> str:
    """Simula un partido de eliminacion (penaltis = 50-50 en empate)."""
    gl, gv = _simular_goles(a, b)
    if gl > gv:
        return a
    elif gv > gl:
        return b
    else:
        return a if random.random() < 0.5 else b


def _simular_bracket(clasificados: List[str]) -> Dict[str, str]:
    """
    Simula las eliminatorias desde la ronda dada hasta la final.
    Devuelve {equipo: ronda_maxima_alcanzada}.
    """
    logros: Dict[str, str] = {}
    ronda = list(clasificados)

    nombres = {
        32: "dieciseisavos",
        16: "octavos",
        8: "cuartos",
        4: "semis",
        2: "final",
    }

    while len(ronda) > 1:
        n = len(ronda)
        etapa = nombres.get(n, "ronda_" + str(n))
        for e in ronda:
            logros[e] = etapa

        siguiente = []
        for i in range(0, n, 2):
            if i + 1 < n:
                ganador = _ganador_partido(ronda[i], ronda[i + 1])
            else:
                ganador = ronda[i]
            siguiente.append(ganador)
        ronda = siguiente

    if ronda:
        logros[ronda[0]] = "campeon"

    return logros


# ---------------------------------------------------------------------------
# Funcion principal
# ---------------------------------------------------------------------------
def simular_torneo(partidos: List[dict], n_sims: int = 5000) -> Dict[str, Dict[str, float]]:
    """
    Simula el torneo completo n_sims veces.

    Parametros:
        partidos: lista de dicts del fixture (formato interno de la app).
        n_sims:   numero de simulaciones (5000 es un buen balance velocidad/precision).

    Retorna:
        {equipo: {"clasifica": p, "octavos": p, "cuartos": p,
                  "semis": p, "final": p, "campeon": p}}
        donde p es probabilidad entre 0 y 1.
    """
    grupos_equipos: Dict[str, List[str]] = defaultdict(list)

    for p in partidos:
        if p.get("fase", "grupos") != "grupos":
            continue
        g = p.get("grupo", "")
        if not g:
            continue
        loc, vis = p["local"], p["visitante"]
        if loc not in grupos_equipos[g]:
            grupos_equipos[g].append(loc)
        if vis not in grupos_equipos[g]:
            grupos_equipos[g].append(vis)

    if not grupos_equipos:
        return {}

    grupos_matches_full: Dict[str, List[Tuple[str, str]]] = {}
    for g, equipos in grupos_equipos.items():
        grupos_matches_full[g] = _partidos_grupo(equipos)

    conteos: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))

    for _ in range(n_sims):
        primeros: List[str] = []
        segundos: List[str] = []

        for g in sorted(grupos_equipos.keys()):
            eq = grupos_equipos[g]
            clasificados = _clasificar(eq, grupos_matches_full[g])
            primeros.append(clasificados[0])
            segundos.append(clasificados[1])
            for e in clasificados[:2]:
                conteos[e]["clasifica"] += 1

        n_grupos = len(primeros)
        bracket: List[str] = []
        grupos_ordenados = sorted(grupos_equipos.keys())

        for i in range(0, n_grupos, 2):
            idx_a = i
            idx_b = i + 1 if i + 1 < n_grupos else 0
            bracket.append(primeros[idx_a])
            bracket.append(segundos[idx_b])

        while len(bracket) < 16:
            bracket.append(bracket[-1])

        bracket = bracket[:16]

        logros = _simular_bracket(bracket)
        for equipo, etapa in logros.items():
            conteos[equipo][etapa] += 1

    resultado: Dict[str, Dict[str, float]] = {}
    for equipo, c in conteos.items():
        resultado[equipo] = {k: round(v / n_sims, 4) for k, v in c.items()}

    return resultado
