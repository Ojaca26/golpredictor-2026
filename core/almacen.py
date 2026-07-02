"""
Almacén simple en JSON para predicciones, resultados reales y análisis post-partido.
Cada predicción se indexa por el id del partido.
"""

from __future__ import annotations
import json
import os
from typing import Dict, Optional, Tuple

ALMACEN_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "predicciones.json")


def cargar() -> Dict[str, dict]:
    if os.path.exists(ALMACEN_PATH):
        try:
            with open(ALMACEN_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def guardar(datos: Dict[str, dict]) -> None:
    os.makedirs(os.path.dirname(ALMACEN_PATH), exist_ok=True)
    with open(ALMACEN_PATH, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)


def set_prediccion(partido_id: int, payload: dict) -> None:
    datos = cargar()
    datos[str(partido_id)] = {**datos.get(str(partido_id), {}), **payload}
    guardar(datos)


def get_prediccion(partido_id: int) -> dict:
    return cargar().get(str(partido_id), {})


def set_resultado_manual(partido_id: int, goles_local: int, goles_visit: int) -> None:
    """Guarda el marcador real y lo marca como ingresado manualmente."""
    set_prediccion(partido_id, {
        "real":   [int(goles_local), int(goles_visit)],
        "manual": True,
    })


def set_penal(partido_id: int, ganador: str) -> None:
    """
    Guarda quién ganó una definición por penales en un cruce de eliminatoria.
    ganador debe ser "local" o "visitante".
    """
    if ganador not in ("local", "visitante"):
        return
    set_prediccion(partido_id, {"penaltis": ganador})


def get_todos_resultados() -> Dict[int, Tuple[int, int]]:
    """
    Retorna {partido_id: (goles_local, goles_visit)} para todos los partidos
    que ya tienen resultado real registrado (manual o via API).
    """
    datos = cargar()
    out: Dict[int, Tuple[int, int]] = {}
    for k, v in datos.items():
        real = v.get("real")
        if real and len(real) == 2:
            try:
                out[int(k)] = (int(real[0]), int(real[1]))
            except (ValueError, TypeError):
                pass
    return out


def get_todos_penaltis() -> Dict[int, str]:
    """
    Retorna {partido_id: "local"|"visitante"} para los cruces de eliminatoria
    que terminaron empatados y se resolvieron por penales.
    """
    datos = cargar()
    out: Dict[int, str] = {}
    for k, v in datos.items():
        pen = v.get("penaltis")
        if pen in ("local", "visitante"):
            try:
                out[int(k)] = pen
            except (ValueError, TypeError):
                pass
    return out


def get_resultados_para_bayes(fixture: list) -> list:
    """
    Construye la lista de dicts necesaria para bayesiano.actualizar().
    fixture: lista de partidos (SEMILLA o cargar_fixture()).
    """
    todos = get_todos_resultados()
    if not todos:
        return []
    fixture_map = {p["id"]: p for p in fixture}
    resultados = []
    for mid, (gl, gv) in todos.items():
        p = fixture_map.get(mid)
        if p:
            resultados.append({
                "local":       p["local"],
                "visitante":   p["visitante"],
                "goles_local": gl,
                "goles_visit": gv,
            })
    return resultados
