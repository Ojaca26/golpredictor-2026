from __future__ import annotations
import json
import os
from typing import List, Dict

FIXTURE_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "fixture.json")

# Equipo cabeza de serie de cada grupo (el favorito / anfitrion)
GRUPOS = {
    "A": "Mexico",          "B": "Canada",
    "C": "Brasil",          "D": "Estados Unidos",
    "E": "Alemania",        "F": "Paises Bajos",
    "G": "Espana",          "H": "Belgica",
    "I": "Francia",         "J": "Argentina",
    "K": "Portugal",        "L": "Inglaterra",
}

# Resultados reales confirmados: {id: {"local": goles, "visitante": goles}}
# Se llena a medida que se juegan los partidos. Vacio al inicio del torneo.
RESULTADOS_CONOCIDOS: Dict[int, Dict[str, int]] = {}

SEMILLA: List[Dict] = [
    # ============================================================
    # JORNADA 1
    # ============================================================
    # GRUPO A
    {"id": 1,  "fecha": "2026-06-11", "fase": "grupos", "grupo": "A", "sede": "Ciudad de Mexico",  "local": "Mexico",              "visitante": "Sudafrica"},
    {"id": 2,  "fecha": "2026-06-11", "fase": "grupos", "grupo": "A", "sede": "Guadalajara",        "local": "Corea del Sur",        "visitante": "Republica Checa"},
    # GRUPO B
    {"id": 3,  "fecha": "2026-06-11", "fase": "grupos", "grupo": "B", "sede": "Toronto",            "local": "Canada",               "visitante": "Bosnia y Herzegovina"},
    {"id": 4,  "fecha": "2026-06-11", "fase": "grupos", "grupo": "B", "sede": "Vancouver",          "local": "Catar",                "visitante": "Suiza"},
    # GRUPO C
    {"id": 5,  "fecha": "2026-06-12", "fase": "grupos", "grupo": "C", "sede": "Nueva Jersey",       "local": "Brasil",               "visitante": "Marruecos"},
    {"id": 6,  "fecha": "2026-06-12", "fase": "grupos", "grupo": "C", "sede": "Los Angeles",        "local": "Haiti",                "visitante": "Escocia"},
    # GRUPO D
    {"id": 7,  "fecha": "2026-06-12", "fase": "grupos", "grupo": "D", "sede": "Los Angeles",        "local": "Estados Unidos",       "visitante": "Paraguay"},
    {"id": 8,  "fecha": "2026-06-12", "fase": "grupos", "grupo": "D", "sede": "Dallas",             "local": "Australia",            "visitante": "Turquia"},
    # GRUPO E
    {"id": 9,  "fecha": "2026-06-13", "fase": "grupos", "grupo": "E", "sede": "Atlanta",            "local": "Alemania",             "visitante": "Curazao"},
    {"id": 10, "fecha": "2026-06-13", "fase": "grupos", "grupo": "E", "sede": "Houston",            "local": "Costa de Marfil",      "visitante": "Ecuador"},
    # GRUPO F
    {"id": 11, "fecha": "2026-06-13", "fase": "grupos", "grupo": "F", "sede": "Seattle",            "local": "Paises Bajos",         "visitante": "Japon"},
    {"id": 12, "fecha": "2026-06-13", "fase": "grupos", "grupo": "F", "sede": "San Francisco",      "local": "Suecia",               "visitante": "Tunez"},
    # GRUPO G
    {"id": 13, "fecha": "2026-06-14", "fase": "grupos", "grupo": "G", "sede": "Miami",              "local": "Espana",               "visitante": "Cabo Verde"},
    {"id": 14, "fecha": "2026-06-14", "fase": "grupos", "grupo": "G", "sede": "Kansas City",        "local": "Arabia Saudita",       "visitante": "Uruguay"},
    # GRUPO H
    {"id": 15, "fecha": "2026-06-14", "fase": "grupos", "grupo": "H", "sede": "Boston",             "local": "Belgica",              "visitante": "Egipto"},
    {"id": 16, "fecha": "2026-06-14", "fase": "grupos", "grupo": "H", "sede": "Nueva York",         "local": "Iran",                 "visitante": "Nueva Zelanda"},
    # GRUPO I
    {"id": 17, "fecha": "2026-06-15", "fase": "grupos", "grupo": "I", "sede": "Dallas",             "local": "Francia",              "visitante": "Senegal"},
    {"id": 18, "fecha": "2026-06-15", "fase": "grupos", "grupo": "I", "sede": "Chicago",            "local": "Irak",                 "visitante": "Noruega"},
    # GRUPO J
    {"id": 19, "fecha": "2026-06-15", "fase": "grupos", "grupo": "J", "sede": "Houston",            "local": "Argentina",            "visitante": "Argelia"},
    {"id": 20, "fecha": "2026-06-15", "fase": "grupos", "grupo": "J", "sede": "Atlanta",            "local": "Austria",              "visitante": "Jordania"},
    # GRUPO K
    {"id": 21, "fecha": "2026-06-16", "fase": "grupos", "grupo": "K", "sede": "Nueva Jersey",       "local": "Portugal",             "visitante": "RD Congo"},
    {"id": 22, "fecha": "2026-06-16", "fase": "grupos", "grupo": "K", "sede": "Los Angeles",        "local": "Uzbekistan",           "visitante": "Colombia"},
    # GRUPO L
    {"id": 23, "fecha": "2026-06-16", "fase": "grupos", "grupo": "L", "sede": "Miami",              "local": "Inglaterra",           "visitante": "Croacia"},
    {"id": 24, "fecha": "2026-06-16", "fase": "grupos", "grupo": "L", "sede": "Seattle",            "local": "Ghana",                "visitante": "Panama"},
    # ============================================================
    # JORNADA 2
    # ============================================================
    # GRUPO A
    {"id": 25, "fecha": "2026-06-17", "fase": "grupos", "grupo": "A", "sede": "Monterrey",          "local": "Mexico",               "visitante": "Corea del Sur"},
    {"id": 26, "fecha": "2026-06-17", "fase": "grupos", "grupo": "A", "sede": "Ciudad de Mexico",   "local": "Sudafrica",            "visitante": "Republica Checa"},
    # GRUPO B
    {"id": 27, "fecha": "2026-06-17", "fase": "grupos", "grupo": "B", "sede": "Vancouver",          "local": "Canada",               "visitante": "Catar"},
    {"id": 28, "fecha": "2026-06-17", "fase": "grupos", "grupo": "B", "sede": "Toronto",            "local": "Bosnia y Herzegovina", "visitante": "Suiza"},
    # GRUPO C
    {"id": 29, "fecha": "2026-06-18", "fase": "grupos", "grupo": "C", "sede": "Boston",             "local": "Brasil",               "visitante": "Haiti"},
    {"id": 30, "fecha": "2026-06-18", "fase": "grupos", "grupo": "C", "sede": "San Francisco",      "local": "Marruecos",            "visitante": "Escocia"},
    # GRUPO D
    {"id": 31, "fecha": "2026-06-18", "fase": "grupos", "grupo": "D", "sede": "Kansas City",        "local": "Estados Unidos",       "visitante": "Australia"},
    {"id": 32, "fecha": "2026-06-18", "fase": "grupos", "grupo": "D", "sede": "Houston",            "local": "Paraguay",             "visitante": "Turquia"},
    # GRUPO E
    {"id": 33, "fecha": "2026-06-19", "fase": "grupos", "grupo": "E", "sede": "Nueva Jersey",       "local": "Alemania",             "visitante": "Costa de Marfil"},
    {"id": 34, "fecha": "2026-06-19", "fase": "grupos", "grupo": "E", "sede": "Atlanta",            "local": "Curazao",              "visitante": "Ecuador"},
    # GRUPO F
    {"id": 35, "fecha": "2026-06-19", "fase": "grupos", "grupo": "F", "sede": "Los Angeles",        "local": "Paises Bajos",         "visitante": "Suecia"},
    {"id": 36, "fecha": "2026-06-19", "fase": "grupos", "grupo": "F", "sede": "Dallas",             "local": "Japon",                "visitante": "Tunez"},
    # GRUPO G
    {"id": 37, "fecha": "2026-06-20", "fase": "grupos", "grupo": "G", "sede": "Chicago",            "local": "Espana",               "visitante": "Arabia Saudita"},
    {"id": 38, "fecha": "2026-06-20", "fase": "grupos", "grupo": "G", "sede": "Miami",              "local": "Uruguay",              "visitante": "Cabo Verde"},
    # GRUPO H
    {"id": 39, "fecha": "2026-06-20", "fase": "grupos", "grupo": "H", "sede": "Seattle",            "local": "Belgica",              "visitante": "Iran"},
    {"id": 40, "fecha": "2026-06-20", "fase": "grupos", "grupo": "H", "sede": "Boston",             "local": "Egipto",               "visitante": "Nueva Zelanda"},
    # GRUPO I
    {"id": 41, "fecha": "2026-06-21", "fase": "grupos", "grupo": "I", "sede": "San Francisco",      "local": "Francia",              "visitante": "Irak"},
    {"id": 42, "fecha": "2026-06-21", "fase": "grupos", "grupo": "I", "sede": "Nueva Jersey",       "local": "Senegal",              "visitante": "Noruega"},
    # GRUPO J
    {"id": 43, "fecha": "2026-06-21", "fase": "grupos", "grupo": "J", "sede": "Houston",            "local": "Argentina",            "visitante": "Austria"},
    {"id": 44, "fecha": "2026-06-21", "fase": "grupos", "grupo": "J", "sede": "Kansas City",        "local": "Argelia",              "visitante": "Jordania"},
    # GRUPO K
    {"id": 45, "fecha": "2026-06-22", "fase": "grupos", "grupo": "K", "sede": "Dallas",             "local": "Portugal",             "visitante": "Uzbekistan"},
    {"id": 46, "fecha": "2026-06-22", "fase": "grupos", "grupo": "K", "sede": "Atlanta",            "local": "RD Congo",             "visitante": "Colombia"},
    # GRUPO L
    {"id": 47, "fecha": "2026-06-22", "fase": "grupos", "grupo": "L", "sede": "Los Angeles",        "local": "Inglaterra",           "visitante": "Ghana"},
    {"id": 48, "fecha": "2026-06-22", "fase": "grupos", "grupo": "L", "sede": "Chicago",            "local": "Croacia",              "visitante": "Panama"},
    # ============================================================
    # JORNADA 3 (simultaneos por grupo)
    # ============================================================
    # GRUPO A
    {"id": 49, "fecha": "2026-06-26", "fase": "grupos", "grupo": "A", "sede": "Ciudad de Mexico",   "local": "Mexico",               "visitante": "Republica Checa"},
    {"id": 50, "fecha": "2026-06-26", "fase": "grupos", "grupo": "A", "sede": "Guadalajara",        "local": "Sudafrica",            "visitante": "Corea del Sur"},
    # GRUPO B
    {"id": 51, "fecha": "2026-06-26", "fase": "grupos", "grupo": "B", "sede": "Vancouver",          "local": "Canada",               "visitante": "Suiza"},
    {"id": 52, "fecha": "2026-06-26", "fase": "grupos", "grupo": "B", "sede": "Toronto",            "local": "Bosnia y Herzegovina", "visitante": "Catar"},
    # GRUPO C
    {"id": 53, "fecha": "2026-06-27", "fase": "grupos", "grupo": "C", "sede": "Nueva Jersey",       "local": "Brasil",               "visitante": "Escocia"},
    {"id": 54, "fecha": "2026-06-27", "fase": "grupos", "grupo": "C", "sede": "Los Angeles",        "local": "Marruecos",            "visitante": "Haiti"},
    # GRUPO D
    {"id": 55, "fecha": "2026-06-27", "fase": "grupos", "grupo": "D", "sede": "Dallas",             "local": "Estados Unidos",       "visitante": "Turquia"},
    {"id": 56, "fecha": "2026-06-27", "fase": "grupos", "grupo": "D", "sede": "Houston",            "local": "Paraguay",             "visitante": "Australia"},
    # GRUPO E
    {"id": 57, "fecha": "2026-06-28", "fase": "grupos", "grupo": "E", "sede": "Atlanta",            "local": "Alemania",             "visitante": "Ecuador"},
    {"id": 58, "fecha": "2026-06-28", "fase": "grupos", "grupo": "E", "sede": "Miami",              "local": "Curazao",              "visitante": "Costa de Marfil"},
    # GRUPO F
    {"id": 59, "fecha": "2026-06-28", "fase": "grupos", "grupo": "F", "sede": "Seattle",            "local": "Paises Bajos",         "visitante": "Tunez"},
    {"id": 60, "fecha": "2026-06-28", "fase": "grupos", "grupo": "F", "sede": "San Francisco",      "local": "Japon",                "visitante": "Suecia"},
    # GRUPO G
    {"id": 61, "fecha": "2026-06-29", "fase": "grupos", "grupo": "G", "sede": "Boston",             "local": "Espana",               "visitante": "Uruguay"},
    {"id": 62, "fecha": "2026-06-29", "fase": "grupos", "grupo": "G", "sede": "Kansas City",        "local": "Arabia Saudita",       "visitante": "Cabo Verde"},
    # GRUPO H
    {"id": 63, "fecha": "2026-06-29", "fase": "grupos", "grupo": "H", "sede": "Chicago",            "local": "Belgica",              "visitante": "Nueva Zelanda"},
    {"id": 64, "fecha": "2026-06-29", "fase": "grupos", "grupo": "H", "sede": "Nueva Jersey",       "local": "Egipto",               "visitante": "Iran"},
    # GRUPO I
    {"id": 65, "fecha": "2026-06-30", "fase": "grupos", "grupo": "I", "sede": "Los Angeles",        "local": "Francia",              "visitante": "Noruega"},
    {"id": 66, "fecha": "2026-06-30", "fase": "grupos", "grupo": "I", "sede": "Dallas",             "local": "Senegal",              "visitante": "Irak"},
    # GRUPO J
    {"id": 67, "fecha": "2026-06-30", "fase": "grupos", "grupo": "J", "sede": "Houston",            "local": "Argentina",            "visitante": "Jordania"},
    {"id": 68, "fecha": "2026-06-30", "fase": "grupos", "grupo": "J", "sede": "Atlanta",            "local": "Argelia",              "visitante": "Austria"},
    # GRUPO K
    {"id": 69, "fecha": "2026-07-01", "fase": "grupos", "grupo": "K", "sede": "Miami",              "local": "Portugal",             "visitante": "Colombia"},
    {"id": 70, "fecha": "2026-07-01", "fase": "grupos", "grupo": "K", "sede": "Seattle",            "local": "RD Congo",             "visitante": "Uzbekistan"},
    # GRUPO L
    {"id": 71, "fecha": "2026-07-01", "fase": "grupos", "grupo": "L", "sede": "San Francisco",      "local": "Inglaterra",           "visitante": "Panama"},
    {"id": 72, "fecha": "2026-07-01", "fase": "grupos", "grupo": "L", "sede": "Vancouver",          "local": "Croacia",              "visitante": "Ghana"},
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
