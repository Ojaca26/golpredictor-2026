from __future__ import annotations
import json
import os
from typing import List, Dict

FIXTURE_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "fixture.json")

GRUPOS = {
    "A": "México",       "B": "Canadá",        "C": "Brasil",       "D": "Estados Unidos",
    "E": "Alemania",     "F": "Países Bajos",   "G": "Bélgica",      "H": "España",
    "I": "Francia",      "J": "Argentina",      "K": "Portugal",     "L": "Inglaterra",
}

SEMILLA: List[Dict] = [
    {"id": 1,  "fecha": "2026-06-11", "fase": "grupos", "grupo": "A", "sede": "Ciudad de México",  "local": "México",         "visitante": "Sudáfrica"},
    {"id": 2,  "fecha": "2026-06-11", "fase": "grupos", "grupo": "A", "sede": "Guadalajara",       "local": "Corea del Sur",   "visitante": "República Checa"},
    {"id": 3,  "fecha": "2026-06-12", "fase": "grupos", "grupo": "B", "sede": "Toronto",           "local": "Canadá",          "visitante": "Bosnia y Herzegovina"},
    {"id": 4,  "fecha": "2026-06-12", "fase": "grupos", "grupo": "D", "sede": "Los Ángeles",       "local": "Estados Unidos",  "visitante": "Paraguay"},
    {"id": 5,  "fecha": "2026-06-13", "fase": "grupos", "grupo": "E", "sede": "Miami",             "local": "Haití",           "visitante": "Escocia"},
    {"id": 6,  "fecha": "2026-06-13", "fase": "grupos", "grupo": "F", "sede": "Seattle",           "local": "Australia",       "visitante": "Turquía"},
    {"id": 7,  "fecha": "2026-06-13", "fase": "grupos", "grupo": "C", "sede": "Nueva Jersey",      "local": "Brasil",          "visitante": "Marruecos"},
    {"id": 8,  "fecha": "2026-06-13", "fase": "grupos", "grupo": "B", "sede": "San Francisco",     "local": "Catar",           "visitante": "Suiza"},
    {"id": 9,  "fecha": "2026-06-14", "fase": "grupos", "grupo": "G", "sede": "Atlanta",           "local": "Bélgica",         "visitante": "Croacia"},
    {"id": 10, "fecha": "2026-06-14", "fase": "grupos", "grupo": "E", "sede": "Atlanta",           "local": "Alemania",        "visitante": "Curazao"},
    {"id": 11, "fecha": "2026-06-14", "fase": "grupos", "grupo": "H", "sede": "Dallas",            "local": "España",          "visitante": "Senegal"},
    {"id": 12, "fecha": "2026-06-14", "fase": "grupos", "grupo": "D", "sede": "Houston",           "local": "Ecuador",         "visitante": "Venezuela"},
    {"id": 13, "fecha": "2026-06-15", "fase": "grupos", "grupo": "F", "sede": "Boston",            "local": "Países Bajos",    "visitante": "Uruguay"},
    {"id": 14, "fecha": "2026-06-15", "fase": "grupos", "grupo": "J", "sede": "Chicago",           "local": "Argentina",       "visitante": "Nigeria"},
    {"id": 15, "fecha": "2026-06-15", "fase": "grupos", "grupo": "I", "sede": "Nueva York",        "local": "Francia",         "visitante": "Arabia Saudita"},
    {"id": 16, "fecha": "2026-06-15", "fase": "grupos", "grupo": "C", "sede": "Los Ángeles",       "local": "Colombia",        "visitante": "Japón"},
    {"id": 17, "fecha": "2026-06-16", "fase": "grupos", "grupo": "K", "sede": "Kansas City",       "local": "Portugal",        "visitante": "Costa de Marfil"},
    {"id": 18, "fecha": "2026-06-16", "fase": "grupos", "grupo": "L", "sede": "Miami",             "local": "Inglaterra",      "visitante": "Irán"},
    {"id": 19, "fecha": "2026-06-16", "fase": "grupos", "grupo": "H", "sede": "San Francisco",     "local": "Austria",         "visitante": "Ghana"},
    {"id": 20, "fecha": "2026-06-16", "fase": "grupos", "grupo": "G", "sede": "Seattle",           "local": "Polonia",         "visitante": "Chile"},
    {"id": 21, "fecha": "2026-06-17", "fase": "grupos", "grupo": "A", "sede": "Monterrey",         "local": "México",          "visitante": "Corea del Sur"},
    {"id": 22, "fecha": "2026-06-17", "fase": "grupos", "grupo": "A", "sede": "Ciudad de México",  "local": "Sudáfrica",       "visitante": "República Checa"},
    {"id": 23, "fecha": "2026-06-17", "fase": "grupos", "grupo": "I", "sede": "Houston",           "local": "Francia",         "visitante": "Dinamarca"},
    {"id": 24, "fecha": "2026-06-17", "fase": "grupos", "grupo": "K", "sede": "Dallas",            "local": "Portugal",        "visitante": "Turquía"},
    {"id": 25, "fecha": "2026-06-18", "fase": "grupos", "grupo": "B", "sede": "Vancouver",         "local": "Canadá",          "visitante": "Catar"},
    {"id": 26, "fecha": "2026-06-18", "fase": "grupos", "grupo": "B", "sede": "Nueva York",        "local": "Bosnia y Herzegovina", "visitante": "Suiza"},
    {"id": 27, "fecha": "2026-06-18", "fase": "grupos", "grupo": "D", "sede": "Chicago",           "local": "Estados Unidos",  "visitante": "Ecuador"},
    {"id": 28, "fecha": "2026-06-18", "fase": "grupos", "grupo": "C", "sede": "Boston",            "local": "Brasil",          "visitante": "Colombia"},
    {"id": 29, "fecha": "2026-06-19", "fase": "grupos", "grupo": "J", "sede": "Atlanta",           "local": "Argentina",       "visitante": "Perú"},
    {"id": 30, "fecha": "2026-06-19", "fase": "grupos", "grupo": "L", "sede": "Kansas City",       "local": "Inglaterra",      "visitante": "Marruecos"},
    {"id": 31, "fecha": "2026-06-19", "fase": "grupos", "grupo": "E", "sede": "Houston",           "local": "Alemania",        "visitante": "Escocia"},
    {"id": 32, "fecha": "2026-06-19", "fase": "grupos", "grupo": "F", "sede": "Los Ángeles",       "local": "Países Bajos",    "visitante": "Australia"},
]

def cargar_fixture() -> List[Dict]:
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
    if not apifootball_key:
        return []
    try:
        from core.deportes_api import apifootball_fixtures
        from core.equipos import normalizar
        crudos = apifootball_fixtures(apifootball_key)
        partidos = []
        for fx in crudos:
            local_raw = fx.get("local") or ""
            visit_raw = fx.get("visitante") or ""
            if not local_raw or not visit_raw:
                continue
            ronda = (fx.get("fase") or "").lower()
            fase = "eliminatorias" if any(k in ronda for k in ("16", "8", "quarter", "semi", "final", "round of")) else "grupos"
            partidos.append({"id": fx["id"], "fecha": fx.get("fecha", ""), "fase": fase,
                             "grupo": "", "sede": "",
                             "local": normalizar(local_raw), "visitante": normalizar(visit_raw)})
        return sorted(partidos, key=lambda p: (p["fecha"], p["id"]))
    except Exception:
        return []

def guardar_fixture(partidos: List[Dict]) -> None:
    os.makedirs(os.path.dirname(FIXTURE_PATH), exist_ok=True)
    with open(FIXTURE_PATH, "w", encoding="utf-8") as f:
        json.dump(partidos, f, ensure_ascii=False, indent=2)
