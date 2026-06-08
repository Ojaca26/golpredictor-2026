"""
Carga el fixture (calendario) del Mundial 2026.

Estrategia:
  - Trae un archivo data/fixture.json si existe (editable por el usuario).
  - Si no, usa una SEMILLA con los grupos y primeros partidos confirmados.
  - El usuario puede refrescar/ampliar el fixture desde la app vía búsqueda web.

Formato de cada partido:
  {
    "id": 1,
    "fecha": "2026-06-11",
    "fase": "grupos",          # "grupos" | "eliminatorias"
    "grupo": "A",
    "sede": "Ciudad de México",
    "local": "México",
    "visitante": "Sudáfrica"
  }
"""

from __future__ import annotations
import json
import os
from typing import List, Dict

FIXTURE_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "fixture.json")

# Cabezas de serie confirmadas (grupos A–L) del Mundial 2026.
GRUPOS = {
    "A": "México", "B": "Canadá", "C": "Brasil", "D": "Estados Unidos",
    "E": "Alemania", "F": "Países Bajos", "G": "Bélgica", "H": "España",
    "I": "Francia", "J": "Argentina", "K": "Portugal", "L": "Inglaterra",
}

# Semilla de partidos confirmados de la jornada inaugural (ampliable vía web).
SEMILLA: List[Dict] = [
    {"id": 1, "fecha": "2026-06-11", "fase": "grupos", "grupo": "A",
     "sede": "Ciudad de México", "local": "México", "visitante": "Sudáfrica"},
    {"id": 2, "fecha": "2026-06-11", "fase": "grupos", "grupo": "A",
     "sede": "Guadalajara", "local": "Corea del Sur", "visitante": "República Checa"},
    {"id": 3, "fecha": "2026-06-12", "fase": "grupos", "grupo": "B",
     "sede": "Toronto", "local": "Canadá", "visitante": "Bosnia y Herzegovina"},
    {"id": 4, "fecha": "2026-06-12", "fase": "grupos", "grupo": "B",
     "sede": "San Francisco", "local": "Qatar", "visitante": "Suiza"},
    {"id": 5, "fecha": "2026-06-13", "fase": "grupos", "grupo": "C",
     "sede": "Nueva Jersey", "local": "Brasil", "visitante": "Marruecos"},
    {"id": 6, "fecha": "2026-06-13", "fase": "grupos", "grupo": "D",
     "sede": "Los Ángeles", "local": "Estados Unidos", "visitante": "Paraguay"},
]


def cargar_fixture() -> List[Dict]:
    """Carga el fixture desde disco; si no existe, devuelve la semilla."""
    if os.path.exists(FIXTURE_PATH):
        try:
            with open(FIXTURE_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list) and data:
                return data
        except Exception:
            pass
    return list(SEMILLA)


def fixture_desde_api(apifootball_key: str) -> List[Dict]:
    """
    Trae el fixture completo del Mundial desde API-Football y lo normaliza al
    formato interno. Si falla o no hay key, devuelve [] (la app usará la semilla).
    """
    if not apifootball_key:
        return []
    try:
        from core.deportes_api import apifootball_fixtures
        crudos = apifootball_fixtures(apifootball_key)
        partidos = []
        for fx in crudos:
            if not (fx.get("local") and fx.get("visitante")):
                continue
            ronda = (fx.get("fase") or "").lower()
            fase = "eliminatorias" if any(
                k in ronda for k in ("16", "8", "quarter", "semi", "final", "round of")
            ) else "grupos"
            partidos.append({
                "id": fx["id"],
                "fecha": fx.get("fecha", ""),
                "fase": fase,
                "grupo": "",
                "sede": "",
                "local": fx["local"],
                "visitante": fx["visitante"],
            })
        return sorted(partidos, key=lambda p: (p["fecha"], p["id"]))
    except Exception:
        return []


def guardar_fixture(partidos: List[Dict]) -> None:
    os.makedirs(os.path.dirname(FIXTURE_PATH), exist_ok=True)
    with open(FIXTURE_PATH, "w", encoding="utf-8") as f:
        json.dump(partidos, f, ensure_ascii=False, indent=2)
