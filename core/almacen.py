"""
Almacén simple en JSON para predicciones, resultados reales y análisis post-partido.
Cada predicción se indexa por el id del partido.
"""

from __future__ import annotations
import json
import os
from typing import Dict

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
