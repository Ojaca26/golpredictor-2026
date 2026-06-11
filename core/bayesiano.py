"""
core/bayesiano.py
Actualización Bayesiana de fuerzas de equipos usando prior conjugado Gamma-Poisson.

Lógica:
  Prior:     lambda ~ Gamma(alpha, beta)
  Datos:     k goles en n partidos
  Posterior: lambda ~ Gamma(alpha + k, beta + n)
  Media:     E[lambda | datos] = (alpha + k) / (beta + n)

Las fuerzas estáticas de EQUIPOS sirven como prior:
  lambda_ataque_prior = MEDIA_BASE * ataque_base
  alpha = lambda_prior * PRIOR_N  (PRIOR_N = peso en "partidos equivalentes")

Con PRIOR_N=5: el prior equivale a 5 partidos históricos.
Tras 3 partidos reales del torneo, los datos ya empiezan a mover las fuerzas.
Tras 6 partidos, el modelo es mayormente data-driven.
"""

from __future__ import annotations
from collections import defaultdict
from typing import Dict, List

from core.predictor import FuerzaEquipo
from core.equipos import get_fuerza

MEDIA_BASE = 1.35        # promedio goles por equipo/partido en mundiales
PRIOR_N    = 5           # peso del prior (partidos equivalentes)
MAX_ATK    = 3.5         # tope de ataque para evitar explosiones
MIN_ATK    = 0.30        # piso de ataque
MAX_DEF    = 3.5
MIN_DEF    = 0.30


def actualizar(resultados: List[Dict]) -> Dict[str, FuerzaEquipo]:
    """
    Recibe lista de resultados jugados y devuelve fuerzas actualizadas por Bayes.

    Parámetros:
        resultados: lista de dicts con claves
                    'local', 'visitante', 'goles_local', 'goles_visit'

    Retorna:
        {equipo: FuerzaEquipo} — solo para los equipos con al menos 1 partido jugado.
        Los demás siguen usando get_fuerza() (base FIFA).
    """
    if not resultados:
        return {}

    goles_favor:  Dict[str, List[int]] = defaultdict(list)
    goles_contra: Dict[str, List[int]] = defaultdict(list)

    for r in resultados:
        local = r["local"]
        visit = r["visitante"]
        gl    = int(r["goles_local"])
        gv    = int(r["goles_visit"])
        goles_favor[local].append(gl)
        goles_contra[local].append(gv)
        goles_favor[visit].append(gv)
        goles_contra[visit].append(gl)

    fuerzas_nuevas: Dict[str, FuerzaEquipo] = {}
    todos = set(goles_favor.keys()) | set(goles_contra.keys())

    for equipo in todos:
        base = get_fuerza(equipo)

        # ── Ataque ────────────────────────────────────────────────────────
        lam_prior_atk   = MEDIA_BASE * base.ataque
        alpha_atk       = lam_prior_atk * PRIOR_N
        beta_atk        = float(PRIOR_N)
        obs_gf          = goles_favor.get(equipo, [])
        alpha_post_atk  = alpha_atk + sum(obs_gf)
        beta_post_atk   = beta_atk  + len(obs_gf)
        nuevo_ataque    = (alpha_post_atk / beta_post_atk) / MEDIA_BASE

        # ── Defensa ───────────────────────────────────────────────────────
        lam_prior_def   = MEDIA_BASE * base.defensa
        alpha_def       = lam_prior_def * PRIOR_N
        beta_def        = float(PRIOR_N)
        obs_gc          = goles_contra.get(equipo, [])
        alpha_post_def  = alpha_def + sum(obs_gc)
        beta_post_def   = beta_def  + len(obs_gc)
        nuevo_defensa   = (alpha_post_def / beta_post_def) / MEDIA_BASE

        fuerzas_nuevas[equipo] = FuerzaEquipo(
            ataque  = round(max(MIN_ATK, min(nuevo_ataque,  MAX_ATK)), 4),
            defensa = round(max(MIN_DEF, min(nuevo_defensa, MAX_DEF)), 4),
        )

    return fuerzas_nuevas


def resumen_cambios(fuerzas_base: Dict[str, FuerzaEquipo],
                    fuerzas_bayes: Dict[str, FuerzaEquipo]) -> List[Dict]:
    """
    Devuelve lista de cambios ordenados por magnitud de variación,
    útil para mostrar en la UI cuánto movió el Bayes a cada equipo.
    """
    cambios = []
    for equipo, f_new in fuerzas_bayes.items():
        f_old = fuerzas_base.get(equipo, get_fuerza(equipo))
        delta_atk = round(f_new.ataque  - f_old.ataque,  3)
        delta_def = round(f_new.defensa - f_old.defensa, 3)
        magnitud  = abs(delta_atk) + abs(delta_def)
        if magnitud > 0.01:
            cambios.append({
                "equipo":     equipo,
                "atk_antes":  f_old.ataque,
                "atk_ahora":  f_new.ataque,
                "def_antes":  f_old.defensa,
                "def_ahora":  f_new.defensa,
                "delta_atk":  delta_atk,
                "delta_def":  delta_def,
                "magnitud":   round(magnitud, 3),
            })
    return sorted(cambios, key=lambda x: x["magnitud"], reverse=True)
