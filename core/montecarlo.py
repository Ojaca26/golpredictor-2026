"""
core/montecarlo.py
Simulacion Monte Carlo del Mundial 2026.

Flujo:
  1. Fase de grupos: para partidos YA JUGADOS usa el marcador real;
     solo simula los pendientes.
  2. Eliminatorias: bracket estandar hasta la final.
  3. Estadisticas: % de veces que cada equipo clasifica, semis, final, campeon.

Parametros nuevos en simular_torneo():
  resultados_reales  — {partido_id: (goles_local, goles_visit)}
  fuerzas_bayes      — {equipo: FuerzaEquipo} ajustadas por Bayes post-torneo
"""

from __future__ import annotations
import math
import random
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

from core.equipos import get_fuerza
from core.predictor import FuerzaEquipo


# ---------------------------------------------------------------------------
# Poisson (algoritmo Knuth — sin dependencias externas)
# ---------------------------------------------------------------------------
def _muestra_poisson(lam: float) -> int:
    L = math.exp(-max(0.01, lam))
    k, p = 0, 1.0
    while p > L:
        k += 1
        p *= random.random()
    return k - 1


def _simular_goles(local: str, visitante: str,
                   fuerzas: Optional[Dict[str, FuerzaEquipo]] = None) -> Tuple[int, int]:
    """Devuelve (gl, gv) simulados. Usa fuerzas Bayesianas si están disponibles."""
    fl = (fuerzas.get(local)     if fuerzas else None) or get_fuerza(local)
    fv = (fuerzas.get(visitante) if fuerzas else None) or get_fuerza(visitante)
    MEDIA   = 1.35
    VENTAJA = 1.10
    lam_l = max(0.2, min(MEDIA * fl.ataque * fv.defensa * VENTAJA, 4.5))
    lam_v = max(0.2, min(MEDIA * fv.ataque * fl.defensa,           4.5))
    return _muestra_poisson(lam_l), _muestra_poisson(lam_v)


# ---------------------------------------------------------------------------
# Grupos
# ---------------------------------------------------------------------------
def _clasificar(equipos: List[str],
                matches: List[Tuple[str, str, Optional[Tuple[int, int]]]],
                fuerzas: Optional[Dict[str, FuerzaEquipo]] = None) -> List[str]:
    """
    Clasifica un grupo.
    matches: lista de (local, visitante, resultado_conocido_o_None)
    Si resultado_conocido no es None → usa el marcador real, no simula.
    """
    pts: Dict[str, int] = defaultdict(int)
    gf:  Dict[str, int] = defaultdict(int)
    gc:  Dict[str, int] = defaultdict(int)

    for loc, vis, known in matches:
        if known is not None:
            gl, gv = known
        else:
            gl, gv = _simular_goles(loc, vis, fuerzas)

        gf[loc] += gl;  gc[loc] += gv
        gf[vis] += gv;  gc[vis] += gl
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


def _construir_partidos_grupo(
    fixture_grupo: List[Dict],
    resultados_reales: Dict[int, Tuple[int, int]],
    equipos: List[str],
) -> List[Tuple[str, str, Optional[Tuple[int, int]]]]:
    """
    Construye la lista completa de partidos del grupo anotando el resultado real
    cuando ya se jugó. Si falta algún cruce (no debería con fixture correcto),
    lo agrega sin resultado conocido.
    """
    cubiertos: set = set()
    resultado: List[Tuple[str, str, Optional[Tuple[int, int]]]] = []

    for p in fixture_grupo:
        loc, vis = p["local"], p["visitante"]
        known = resultados_reales.get(p["id"])
        resultado.append((loc, vis, known))
        cubiertos.add((loc, vis))

    # Asegurar round-robin completo (seguridad)
    for i in range(len(equipos)):
        for j in range(i + 1, len(equipos)):
            par = (equipos[i], equipos[j])
            if par not in cubiertos and (par[1], par[0]) not in cubiertos:
                resultado.append((par[0], par[1], None))

    return resultado


# ---------------------------------------------------------------------------
# Eliminatorias
# ---------------------------------------------------------------------------
def _ganador_partido(a: str, b: str,
                     fuerzas: Optional[Dict[str, FuerzaEquipo]] = None) -> str:
    gl, gv = _simular_goles(a, b, fuerzas)
    if gl > gv:   return a
    elif gv > gl: return b
    else:         return a if random.random() < 0.5 else b


def _simular_bracket(clasificados: List[str],
                     fuerzas: Optional[Dict[str, FuerzaEquipo]] = None) -> Dict[str, str]:
    logros: Dict[str, str] = {}
    ronda = list(clasificados)
    nombres = {32: "dieciseisavos", 16: "octavos", 8: "cuartos", 4: "semis", 2: "final"}

    while len(ronda) > 1:
        n = len(ronda)
        etapa = nombres.get(n, f"ronda_{n}")
        for e in ronda:
            logros[e] = etapa
        siguiente = []
        for i in range(0, n, 2):
            ganador = (_ganador_partido(ronda[i], ronda[i + 1], fuerzas)
                       if i + 1 < n else ronda[i])
            siguiente.append(ganador)
        ronda = siguiente

    if ronda:
        logros[ronda[0]] = "campeon"
    return logros


# ---------------------------------------------------------------------------
# Función principal
# ---------------------------------------------------------------------------
def simular_torneo(
    partidos:          List[dict],
    n_sims:            int = 5000,
    resultados_reales: Optional[Dict[int, Tuple[int, int]]] = None,
    fuerzas_bayes:     Optional[Dict[str, FuerzaEquipo]]    = None,
) -> Dict[str, Dict[str, float]]:
    """
    Simula el torneo n_sims veces.

    Parámetros:
        partidos          — fixture completo.
        n_sims            — número de simulaciones.
        resultados_reales — {id_partido: (gl, gv)} ya jugados (no se simulan).
        fuerzas_bayes     — {equipo: FuerzaEquipo} actualizadas por Bayes.

    Retorna:
        {equipo: {"clasifica": p, "octavos": p, "cuartos": p,
                  "semis": p, "final": p, "campeon": p}}
    """
    resultados_reales = resultados_reales or {}
    fuerzas           = fuerzas_bayes     or {}

    # ── 1. Construir estructura de grupos ──────────────────────────────────
    grupos_equipos:  Dict[str, List[str]]   = defaultdict(list)
    grupos_fixture:  Dict[str, List[Dict]]  = defaultdict(list)

    for p in partidos:
        if p.get("fase", "grupos") != "grupos":
            continue
        g = p.get("grupo", "")
        if not g:
            continue
        loc, vis = p["local"], p["visitante"]
        grupos_fixture[g].append(p)
        if loc not in grupos_equipos[g]:
            grupos_equipos[g].append(loc)
        if vis not in grupos_equipos[g]:
            grupos_equipos[g].append(vis)

    if not grupos_equipos:
        return {}

    # ── 2. Pre-construir lista de partidos con resultados conocidos ─────────
    grupos_matches: Dict[str, List] = {}
    for g, equipos in grupos_equipos.items():
        grupos_matches[g] = _construir_partidos_grupo(
            grupos_fixture[g], resultados_reales, equipos
        )

    # ── 3. Simulaciones ─────────────────────────────────────────────────────
    conteos: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))

    for _ in range(n_sims):
        primeros: List[str] = []
        segundos: List[str] = []

        for g in sorted(grupos_equipos.keys()):
            eq = grupos_equipos[g]
            clasificados = _clasificar(eq, grupos_matches[g], fuerzas)
            primeros.append(clasificados[0])
            segundos.append(clasificados[1])
            for e in clasificados[:2]:
                conteos[e]["clasifica"] += 1

        # Bracket: 1A vs 2B, 1B vs 2A, ...
        grupos_ord = sorted(grupos_equipos.keys())
        n_grupos   = len(grupos_ord)
        bracket: List[str] = []
        for i in range(0, n_grupos, 2):
            idx_a = i
            idx_b = i + 1 if i + 1 < n_grupos else 0
            bracket.append(primeros[idx_a])
            bracket.append(segundos[idx_b])

        while len(bracket) < 16:
            bracket.append(bracket[-1])
        bracket = bracket[:16]

        logros = _simular_bracket(bracket, fuerzas)
        for equipo, etapa in logros.items():
            conteos[equipo][etapa] += 1

    # ── 4. Normalizar ────────────────────────────────────────────────────────
    return {
        equipo: {k: round(v / n_sims, 4) for k, v in c.items()}
        for equipo, c in conteos.items()
    }
