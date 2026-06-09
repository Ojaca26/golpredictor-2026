"""
Motor de prediccion de marcadores basado en el modelo de Poisson bivariado.

El futbol se modela bien con distribuciones de Poisson: el numero de goles que
marca un equipo en un partido sigue aproximadamente una Poisson cuya media (lambda)
depende de la fuerza ofensiva del equipo, la debilidad defensiva del rival, y la
ventaja de jugar como local.

Este modulo NO inventa certezas. Calcula la probabilidad de cada marcador posible
y luego ELIGE el pronostico que maximiza el valor esperado de puntos segun las
reglas de Golpredictor (acertar ganador vale mucho mas que el marcador exacto).
"""

from __future__ import annotations
import math
from dataclasses import dataclass, field
from typing import Dict, List, Tuple


# ----------------------------------------------------------------------------
# Reglas de puntuacion de Golpredictor
# ----------------------------------------------------------------------------
@dataclass
class Reglas:
    """Puntos por cada tipo de acierto. Cambian entre primera ronda y eliminatorias."""
    pts_resultado: int
    pts_goles_local: int
    pts_goles_visitante: int
    pts_diferencia: int

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
    """Calcula cuantos puntos daria un pronostico contra un resultado real."""
    pts = 0
    signo_pred = (pred_local > pred_visit) - (pred_local < pred_visit)
    signo_real = (real_local > real_visit) - (real_local < real_visit)
    if signo_pred == signo_real:
        pts += reglas.pts_resultado
    if pred_local == real_local:
        pts += reglas.pts_goles_local
    if pred_visit == real_visit:
        pts += reglas.pts_goles_visitante
    if (pred_local - pred_visit) == (real_local - real_visit):
        pts += reglas.pts_diferencia
    return pts


# ----------------------------------------------------------------------------
# Modelo de Poisson + correccion Dixon-Coles
# ----------------------------------------------------------------------------
def _poisson_pmf(k: int, lam: float) -> float:
    """Probabilidad de exactamente k goles dado un promedio lam."""
    return math.exp(-lam) * (lam ** k) / math.factorial(k)


# Parametro de correlacion Dixon-Coles estimado en partidos de futbol
# (negativo: los marcadores bajos son mas frecuentes de lo que predice Poisson puro)
RHO_DC = -0.13


def _tau_dc(gl: int, gv: int, lam: float, mu: float, rho: float = RHO_DC) -> float:
    """
    Factor de correccion Dixon-Coles para marcadores bajos (0-0, 1-0, 0-1, 1-1).
    Corrige la subestimacion/sobreestimacion del modelo Poisson puro
    en partidos de bajo marcador.
    """
    if gl == 0 and gv == 0:
        return 1.0 - lam * mu * rho
    elif gl == 1 and gv == 0:
        return 1.0 + mu * rho
    elif gl == 0 and gv == 1:
        return 1.0 + lam * rho
    elif gl == 1 and gv == 1:
        return 1.0 - rho
    return 1.0


@dataclass
class FuerzaEquipo:
    """Parametros de fuerza de un equipo (normalizados ~1.0 = promedio mundial)."""
    ataque: float = 1.0
    defensa: float = 1.0


@dataclass
class Prediccion:
    local: str
    visitante: str
    marcadores: List[Tuple[int, int, float]] = field(default_factory=list)
    optimo: Tuple[int, int] = (0, 0)
    pts_esperados_optimo: float = 0.0
    prob_victoria_local: float = 0.0
    prob_empate: float = 0.0
    prob_victoria_visit: float = 0.0


class PoissonPredictor:
    """
    Predice marcadores combinando un modelo de Poisson con la optimizacion
    de puntos esperados segun las reglas del juego.
    Incluye correccion Dixon-Coles para marcadores bajos.
    """

    PROMEDIO_GOLES_LIGA = 1.35
    VENTAJA_LOCAL = 1.10
    MAX_GOLES = 8

    def __init__(self, fuerzas: Dict[str, FuerzaEquipo] | None = None):
        self.fuerzas = fuerzas or {}

    def _fuerza(self, equipo: str) -> FuerzaEquipo:
        return self.fuerzas.get(equipo, FuerzaEquipo())

    def _lambdas(self, local: str, visitante: str) -> Tuple[float, float]:
        """Calcula los goles esperados (lambda) de cada lado."""
        fl, fv = self._fuerza(local), self._fuerza(visitante)
        lam_local = self.PROMEDIO_GOLES_LIGA * fl.ataque * fv.defensa * self.VENTAJA_LOCAL
        lam_visit = self.PROMEDIO_GOLES_LIGA * fv.ataque * fl.defensa
        return max(0.2, min(lam_local, 4.5)), max(0.2, min(lam_visit, 4.5))

    def matriz_probabilidades(self, lam_local: float, lam_visit: float,
                               rho: float = RHO_DC):
        """
        Devuelve P[gl][gv] = probabilidad de ese marcador exacto.
        Aplica la correccion Dixon-Coles para marcadores bajos (rho=-0.13 por defecto).
        La matriz se renormaliza para que sume exactamente 1.0.
        """
        pl = [_poisson_pmf(i, lam_local) for i in range(self.MAX_GOLES + 1)]
        pv = [_poisson_pmf(j, lam_visit) for j in range(self.MAX_GOLES + 1)]
        M = [
            [pl[i] * pv[j] * _tau_dc(i, j, lam_local, lam_visit, rho)
             for j in range(self.MAX_GOLES + 1)]
            for i in range(self.MAX_GOLES + 1)
        ]
        total = sum(M[i][j] for i in range(self.MAX_GOLES + 1)
                    for j in range(self.MAX_GOLES + 1))
        if total > 0:
            M = [[M[i][j] / total for j in range(self.MAX_GOLES + 1)]
                 for i in range(self.MAX_GOLES + 1)]
        return M

    def matriz_heatmap(self, lam_local: float, lam_visit: float, max_g: int = 5):
        """
        Devuelve una sub-matriz max_g x max_g con porcentajes redondeados,
        lista para mostrar como mapa de calor en la UI.
        """
        M = self.matriz_probabilidades(lam_local, lam_visit)
        return [[round(M[i][j] * 100, 1) for j in range(max_g + 1)]
                for i in range(max_g + 1)]

    def predecir(self, local: str, visitante: str, reglas: Reglas) -> Prediccion:
        lam_l, lam_v = self._lambdas(local, visitante)
        M = self.matriz_probabilidades(lam_l, lam_v)

        marcadores = []
        for i in range(self.MAX_GOLES + 1):
            for j in range(self.MAX_GOLES + 1):
                marcadores.append((i, j, M[i][j]))
        marcadores.sort(key=lambda x: x[2], reverse=True)

        p_local = sum(M[i][j] for i in range(self.MAX_GOLES + 1)
                      for j in range(self.MAX_GOLES + 1) if i > j)
        p_empate = sum(M[i][i] for i in range(self.MAX_GOLES + 1))
        p_visit = sum(M[i][j] for i in range(self.MAX_GOLES + 1)
                      for j in range(self.MAX_GOLES + 1) if i < j)

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
        Devuelve dos opciones de pronostico:
          - Opcion 1: la que maximiza puntos esperados (recomendada).
          - Opcion 2: el marcador mas probable individualmente (si difiere).
        """
        pred = self.predecir(local, visitante, reglas)
        lam_l, lam_v = self._lambdas(local, visitante)
        M = self.matriz_probabilidades(lam_l, lam_v)

        op1 = pred.optimo
        prob_op1 = M[op1[0]][op1[1]]

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
    fuerzas = {
        "Brasil": FuerzaEquipo(ataque=1.6, defensa=0.7),
        "Serbia": FuerzaEquipo(ataque=0.9, defensa=1.2),
    }
    pred = PoissonPredictor(fuerzas)
    r = pred.top_dos_pronosticos("Brasil", "Serbia", Reglas.primera_ronda())
    p = r["prediccion"]
    print(p.local + " vs " + p.visitante)
    print("  P(gana local)=" + str(round(p.prob_victoria_local, 2)) +
          "  P(empate)=" + str(round(p.prob_empate, 2)) +
          "  P(gana visit)=" + str(round(p.prob_victoria_visit, 2)))
    print("  Opcion 1 (optima): " + str(r["opcion_1"]["marcador"]) +
          "  prob=" + str(round(r["opcion_1"]["prob"], 3)) +
          "  EV=" + str(r["opcion_1"]["pts_esperados"]) + " pts")
    print("  Opcion 2: " + str(r["opcion_2"]["marcador"]) +
          "  prob=" + str(round(r["opcion_2"]["prob"], 3)))
