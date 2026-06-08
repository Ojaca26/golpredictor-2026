"""
Motor de predicción de marcadores basado en el modelo de Poisson bivariado.

El fútbol se modela bien con distribuciones de Poisson: el número de goles que
marca un equipo en un partido sigue aproximadamente una Poisson cuya media (lambda)
depende de la fuerza ofensiva del equipo, la debilidad defensiva del rival, y la
ventaja de jugar como local.

Este módulo NO inventa certezas. Calcula la probabilidad de cada marcador posible
y luego ELIGE el pronóstico que maximiza el valor esperado de puntos según las
reglas de Golpredictor (acertar ganador vale mucho más que el marcador exacto).
"""

from __future__ import annotations
import math
from dataclasses import dataclass, field
from typing import Dict, List, Tuple


# ----------------------------------------------------------------------------
# Reglas de puntuación de Golpredictor
# ----------------------------------------------------------------------------
@dataclass
class Reglas:
    """Puntos por cada tipo de acierto. Cambian entre primera ronda y eliminatorias."""
    pts_resultado: int      # acertar ganador o empate
    pts_goles_local: int    # acertar nº de goles del local
    pts_goles_visitante: int  # acertar nº de goles del visitante
    pts_diferencia: int     # acertar diferencia de goles

    @staticmethod
    def primera_ronda() -> "Reglas":
        return Reglas(5, 2, 2, 1)

    @staticmethod
    def eliminatorias() -> "Reglas":
        return Reglas(10, 4, 4, 2)


def puntos_de_pronostico(
    pred_local: int, pred_visit: int,
    real_local: int, real_visit: int,
    reglas: Reglas,
) -> int:
    """Calcula cuántos puntos daría un pronóstico contra un resultado real."""
    pts = 0

    # ¿Acertó el resultado (ganador/empate)?
    signo_pred = (pred_local > pred_visit) - (pred_local < pred_visit)
    signo_real = (real_local > real_visit) - (real_local < real_visit)
    if signo_pred == signo_real:
        pts += reglas.pts_resultado

    # ¿Acertó goles exactos de cada equipo?
    if pred_local == real_local:
        pts += reglas.pts_goles_local
    if pred_visit == real_visit:
        pts += reglas.pts_goles_visitante

    # ¿Acertó la diferencia de goles?
    if (pred_local - pred_visit) == (real_local - real_visit):
        pts += reglas.pts_diferencia

    return pts


# ----------------------------------------------------------------------------
# Modelo de Poisson
# ----------------------------------------------------------------------------
def _poisson_pmf(k: int, lam: float) -> float:
    """Probabilidad de exactamente k goles dado un promedio lam."""
    return math.exp(-lam) * (lam ** k) / math.factorial(k)


@dataclass
class FuerzaEquipo:
    """Parámetros de fuerza de un equipo (normalizados ~1.0 = promedio mundial)."""
    ataque: float = 1.0      # >1 marca más que el promedio
    defensa: float = 1.0     # >1 encaja más que el promedio (es peor defensa)


@dataclass
class Prediccion:
    local: str
    visitante: str
    # marcadores ordenados por probabilidad: [(gl, gv, prob), ...]
    marcadores: List[Tuple[int, int, float]] = field(default_factory=list)
    # pronóstico recomendado para MAXIMIZAR puntos esperados
    optimo: Tuple[int, int] = (0, 0)
    pts_esperados_optimo: float = 0.0
    prob_victoria_local: float = 0.0
    prob_empate: float = 0.0
    prob_victoria_visit: float = 0.0


class PoissonPredictor:
    """
    Predice marcadores combinando un modelo de Poisson con la optimización
    de puntos esperados según las reglas del juego.
    """

    # Promedio de goles por equipo y partido en mundiales (~1.35 por lado).
    PROMEDIO_GOLES_LIGA = 1.35
    # Ventaja de jugar como "local" (en mundial es leve, salvo el anfitrión).
    VENTAJA_LOCAL = 1.10
    MAX_GOLES = 8  # tope de goles a considerar por equipo

    def __init__(self, fuerzas: Dict[str, FuerzaEquipo] | None = None):
        self.fuerzas = fuerzas or {}

    def _fuerza(self, equipo: str) -> FuerzaEquipo:
        return self.fuerzas.get(equipo, FuerzaEquipo())

    def _lambdas(self, local: str, visitante: str) -> Tuple[float, float]:
        """Calcula los goles esperados (lambda) de cada lado."""
        fl, fv = self._fuerza(local), self._fuerza(visitante)
        lam_local = self.PROMEDIO_GOLES_LIGA * fl.ataque * fv.defensa * self.VENTAJA_LOCAL
        lam_visit = self.PROMEDIO_GOLES_LIGA * fv.ataque * fl.defensa
        # acotar para evitar valores absurdos
        return max(0.2, min(lam_local, 4.5)), max(0.2, min(lam_visit, 4.5))

    def matriz_probabilidades(self, lam_local: float, lam_visit: float):
        """Devuelve P[gl][gv] = probabilidad de ese marcador exacto."""
        pl = [_poisson_pmf(i, lam_local) for i in range(self.MAX_GOLES + 1)]
        pv = [_poisson_pmf(j, lam_visit) for j in range(self.MAX_GOLES + 1)]
        return [[pl[i] * pv[j] for j in range(self.MAX_GOLES + 1)]
                for i in range(self.MAX_GOLES + 1)]

    def predecir(self, local: str, visitante: str, reglas: Reglas) -> Prediccion:
        lam_l, lam_v = self._lambdas(local, visitante)
        M = self.matriz_probabilidades(lam_l, lam_v)

        # 1) marcadores más probables (para mostrar como "predicción cruda")
        marcadores = []
        for i in range(self.MAX_GOLES + 1):
            for j in range(self.MAX_GOLES + 1):
                marcadores.append((i, j, M[i][j]))
        marcadores.sort(key=lambda x: x[2], reverse=True)

        # 2) probabilidades de resultado (1X2)
        p_local = sum(M[i][j] for i in range(self.MAX_GOLES + 1)
                      for j in range(self.MAX_GOLES + 1) if i > j)
        p_empate = sum(M[i][i] for i in range(self.MAX_GOLES + 1))
        p_visit = sum(M[i][j] for i in range(self.MAX_GOLES + 1)
                      for j in range(self.MAX_GOLES + 1) if i < j)

        # 3) CLAVE: elegir el pronóstico que MAXIMIZA puntos esperados.
        # Para cada candidato (gl, gv) calculamos el valor esperado de puntos
        # sumando sobre todos los resultados reales posibles ponderados por prob.
        mejor_pron = (0, 0)
        mejor_ev = -1.0
        for cl in range(self.MAX_GOLES + 1):
            for cv in range(self.MAX_GOLES + 1):
                ev = 0.0
                for i in range(self.MAX_GOLES + 1):
                    for j in range(self.MAX_GOLES + 1):
                        ev += M[i][j] * puntos_de_pronostico(cl, cv, i, j, reglas)
                if ev > mejor_ev:
                    mejor_ev = ev
                    mejor_pron = (cl, cv)

        return Prediccion(
            local=local,
            visitante=visitante,
            marcadores=marcadores[:5],
            optimo=mejor_pron,
            pts_esperados_optimo=round(mejor_ev, 2),
            prob_victoria_local=round(p_local, 4),
            prob_empate=round(p_empate, 4),
            prob_victoria_visit=round(p_visit, 4),
        )

    def top_dos_pronosticos(self, local: str, visitante: str, reglas: Reglas):
        """
        Devuelve dos opciones de pronóstico:
          - Opción 1: la que maximiza puntos esperados (recomendada).
          - Opción 2: el marcador más probable individualmente (si difiere),
            o el segundo mejor por valor esperado.
        Cada una con su % de probabilidad de ocurrencia exacta.
        """
        pred = self.predecir(local, visitante, reglas)
        lam_l, lam_v = self._lambdas(local, visitante)
        M = self.matriz_probabilidades(lam_l, lam_v)

        op1 = pred.optimo
        prob_op1 = M[op1[0]][op1[1]]

        # opción 2 = marcador más probable que NO sea igual a op1
        op2 = None
        for (i, j, p) in pred.marcadores:
            if (i, j) != op1:
                op2 = (i, j, p)
                break
        if op2 is None:
            op2 = pred.marcadores[0]

        return {
            "prediccion": pred,
            "opcion_1": {"marcador": op1, "prob": round(prob_op1, 4),
                         "pts_esperados": pred.pts_esperados_optimo},
            "opcion_2": {"marcador": (op2[0], op2[1]), "prob": round(op2[2], 4)},
        }


if __name__ == "__main__":
    # Demo rápida
    fuerzas = {
        "Brasil": FuerzaEquipo(ataque=1.6, defensa=0.7),
        "Serbia": FuerzaEquipo(ataque=0.9, defensa=1.2),
    }
    pred = PoissonPredictor(fuerzas)
    r = pred.top_dos_pronosticos("Brasil", "Serbia", Reglas.primera_ronda())
    p = r["prediccion"]
    print(f"{p.local} vs {p.visitante}")
    print(f"  P(gana local)={p.prob_victoria_local:.0%}  "
          f"P(empate)={p.prob_empate:.0%}  P(gana visit)={p.prob_victoria_visit:.0%}")
    print(f"  Opción 1 (óptima): {r['opcion_1']['marcador']}  "
          f"prob={r['opcion_1']['prob']:.1%}  EV={r['opcion_1']['pts_esperados']} pts")
    print(f"  Opción 2: {r['opcion_2']['marcador']}  prob={r['opcion_2']['prob']:.1%}")
