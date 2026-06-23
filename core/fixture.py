"""
Carga el fixture (calendario) del Mundial 2026.

Estrategia:
  1. Lee data/fixture.json si existe (editable / guardado desde la app).
  2. Si no, usa SEMILLA con los 72 partidos de fase de grupos del sorteo real.
  3. El toggle "Fixture desde API-Football" trae el calendario completo (104 partidos)
     y normaliza los nombres del inglés al español.
"""

from __future__ import annotations
import json
import os
from typing import List, Dict

FIXTURE_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "fixture.json")

# Cabezas de serie confirmadas (grupos A–L) del Mundial 2026.
GRUPOS = {
    "A": "México",        "B": "Canadá",         "C": "Brasil",         "D": "Estados Unidos",
    "E": "Alemania",      "F": "Países Bajos",    "G": "Bélgica",        "H": "España",
    "I": "Francia",       "J": "Argentina",       "K": "Portugal",       "L": "Inglaterra",
}

# ---------------------------------------------------------------------------
# SEMILLA — 72 partidos de fase de grupos del Mundial 2026 (sorteo real)
# ---------------------------------------------------------------------------
SEMILLA: List[Dict] = [

    # ── GRUPO A: México · Corea del Sur · Sudáfrica · República Checa ───────
    {"id":  1, "fecha": "2026-06-11", "fase": "grupos", "grupo": "A",
     "sede": "Ciudad de México",  "local": "México",          "visitante": "Sudáfrica"},
    {"id":  2, "fecha": "2026-06-11", "fase": "grupos", "grupo": "A",
     "sede": "Guadalajara",       "local": "Corea del Sur",   "visitante": "República Checa"},
    {"id":  3, "fecha": "2026-06-18", "fase": "grupos", "grupo": "A",
     "sede": "Monterrey",         "local": "México",          "visitante": "Corea del Sur"},
    {"id":  4, "fecha": "2026-06-18", "fase": "grupos", "grupo": "A",
     "sede": "Guadalajara",       "local": "Sudáfrica",       "visitante": "República Checa"},
    {"id":  5, "fecha": "2026-06-26", "fase": "grupos", "grupo": "A",
     "sede": "Ciudad de México",  "local": "República Checa", "visitante": "México"},
    {"id":  6, "fecha": "2026-06-26", "fase": "grupos", "grupo": "A",
     "sede": "Monterrey",         "local": "Corea del Sur",   "visitante": "Sudáfrica"},

    # ── GRUPO B: Canadá · Bosnia y Herzegovina · Suiza · Catar ─────────────
    {"id":  7, "fecha": "2026-06-12", "fase": "grupos", "grupo": "B",
     "sede": "Toronto",           "local": "Canadá",              "visitante": "Bosnia y Herzegovina"},
    {"id":  8, "fecha": "2026-06-13", "fase": "grupos", "grupo": "B",
     "sede": "San Francisco",     "local": "Suiza",               "visitante": "Catar"},
    {"id":  9, "fecha": "2026-06-18", "fase": "grupos", "grupo": "B",
     "sede": "Vancouver",         "local": "Canadá",              "visitante": "Catar"},
    {"id": 10, "fecha": "2026-06-18", "fase": "grupos", "grupo": "B",
     "sede": "Nueva York",        "local": "Bosnia y Herzegovina","visitante": "Suiza"},
    {"id": 11, "fecha": "2026-06-26", "fase": "grupos", "grupo": "B",
     "sede": "Vancouver",         "local": "Suiza",               "visitante": "Canadá"},
    {"id": 12, "fecha": "2026-06-26", "fase": "grupos", "grupo": "B",
     "sede": "Toronto",           "local": "Bosnia y Herzegovina","visitante": "Catar"},

    # ── GRUPO C: Brasil · Marruecos · Escocia · Haití ───────────────────────
    {"id": 13, "fecha": "2026-06-13", "fase": "grupos", "grupo": "C",
     "sede": "Nueva Jersey",      "local": "Brasil",    "visitante": "Marruecos"},
    {"id": 14, "fecha": "2026-06-13", "fase": "grupos", "grupo": "C",
     "sede": "Miami",             "local": "Escocia",   "visitante": "Haití"},
    {"id": 15, "fecha": "2026-06-19", "fase": "grupos", "grupo": "C",
     "sede": "Los Ángeles",       "local": "Brasil",    "visitante": "Haití"},
    {"id": 16, "fecha": "2026-06-19", "fase": "grupos", "grupo": "C",
     "sede": "Boston",            "local": "Marruecos", "visitante": "Escocia"},
    {"id": 17, "fecha": "2026-06-27", "fase": "grupos", "grupo": "C",
     "sede": "Kansas City",       "local": "Escocia",   "visitante": "Brasil"},
    {"id": 18, "fecha": "2026-06-27", "fase": "grupos", "grupo": "C",
     "sede": "Miami",             "local": "Haití",     "visitante": "Marruecos"},

    # ── GRUPO D: Estados Unidos · Paraguay · Australia · Turquía ────────────
    {"id": 19, "fecha": "2026-06-12", "fase": "grupos", "grupo": "D",
     "sede": "Los Ángeles",       "local": "Estados Unidos","visitante": "Paraguay"},
    {"id": 20, "fecha": "2026-06-13", "fase": "grupos", "grupo": "D",
     "sede": "Vancouver",         "local": "Australia",     "visitante": "Turquía"},
    {"id": 21, "fecha": "2026-06-19", "fase": "grupos", "grupo": "D",
     "sede": "Seattle",           "local": "Estados Unidos","visitante": "Australia"},
    {"id": 22, "fecha": "2026-06-19", "fase": "grupos", "grupo": "D",
     "sede": "Dallas",            "local": "Turquía",       "visitante": "Paraguay"},
    {"id": 23, "fecha": "2026-06-26", "fase": "grupos", "grupo": "D",
     "sede": "Chicago",           "local": "Turquía",       "visitante": "Estados Unidos"},
    {"id": 24, "fecha": "2026-06-26", "fase": "grupos", "grupo": "D",
     "sede": "Houston",           "local": "Australia",     "visitante": "Paraguay"},

    # ── GRUPO E: Alemania · Costa de Marfil · Ecuador · Curazao ────────────
    {"id": 25, "fecha": "2026-06-20", "fase": "grupos", "grupo": "E",
     "sede": "Atlanta",           "local": "Alemania",       "visitante": "Costa de Marfil"},
    {"id": 26, "fecha": "2026-06-20", "fase": "grupos", "grupo": "E",
     "sede": "Kansas City",       "local": "Ecuador",        "visitante": "Curazao"},
    {"id": 27, "fecha": "2026-06-25", "fase": "grupos", "grupo": "E",
     "sede": "Seattle",           "local": "Ecuador",        "visitante": "Alemania"},
    {"id": 28, "fecha": "2026-06-25", "fase": "grupos", "grupo": "E",
     "sede": "Boston",            "local": "Costa de Marfil","visitante": "Curazao"},
    {"id": 29, "fecha": "2026-06-28", "fase": "grupos", "grupo": "E",
     "sede": "Miami",             "local": "Alemania",       "visitante": "Curazao"},
    {"id": 30, "fecha": "2026-06-28", "fase": "grupos", "grupo": "E",
     "sede": "Chicago",           "local": "Ecuador",        "visitante": "Costa de Marfil"},

    # ── GRUPO F: Países Bajos · Japón · Suecia · Túnez ──────────────────────
    {"id": 31, "fecha": "2026-06-14", "fase": "grupos", "grupo": "F",
     "sede": "Dallas",            "local": "Países Bajos",  "visitante": "Japón"},
    {"id": 32, "fecha": "2026-06-14", "fase": "grupos", "grupo": "F",
     "sede": "San Francisco",     "local": "Suecia",        "visitante": "Túnez"},
    {"id": 33, "fecha": "2026-06-20", "fase": "grupos", "grupo": "F",
     "sede": "Nueva York",        "local": "Países Bajos",  "visitante": "Suecia"},
    {"id": 34, "fecha": "2026-06-20", "fase": "grupos", "grupo": "F",
     "sede": "Seattle",           "local": "Túnez",         "visitante": "Japón"},
    {"id": 35, "fecha": "2026-06-25", "fase": "grupos", "grupo": "F",
     "sede": "Boston",            "local": "Túnez",         "visitante": "Países Bajos"},
    {"id": 36, "fecha": "2026-06-25", "fase": "grupos", "grupo": "F",
     "sede": "Chicago",           "local": "Japón",         "visitante": "Suecia"},

    # ── GRUPO G: Bélgica · Egipto · Irán · Nueva Zelanda ────────────────────
    {"id": 37, "fecha": "2026-06-15", "fase": "grupos", "grupo": "G",
     "sede": "Atlanta",           "local": "Bélgica",        "visitante": "Egipto"},
    {"id": 38, "fecha": "2026-06-15", "fase": "grupos", "grupo": "G",
     "sede": "Kansas City",       "local": "Irán",           "visitante": "Nueva Zelanda"},
    {"id": 39, "fecha": "2026-06-21", "fase": "grupos", "grupo": "G",
     "sede": "Chicago",           "local": "Bélgica",        "visitante": "Irán"},
    {"id": 40, "fecha": "2026-06-21", "fase": "grupos", "grupo": "G",
     "sede": "Dallas",            "local": "Nueva Zelanda",  "visitante": "Egipto"},
    {"id": 41, "fecha": "2026-06-25", "fase": "grupos", "grupo": "G",
     "sede": "Los Ángeles",       "local": "Bélgica",        "visitante": "Nueva Zelanda"},
    {"id": 42, "fecha": "2026-06-25", "fase": "grupos", "grupo": "G",
     "sede": "Miami",             "local": "Irán",           "visitante": "Egipto"},

    # ── GRUPO H: España · Cabo Verde · Arabia Saudita · Uruguay ─────────────
    {"id": 43, "fecha": "2026-06-15", "fase": "grupos", "grupo": "H",
     "sede": "San Francisco",     "local": "España",        "visitante": "Cabo Verde"},
    {"id": 44, "fecha": "2026-06-15", "fase": "grupos", "grupo": "H",
     "sede": "Houston",           "local": "Arabia Saudita","visitante": "Uruguay"},
    {"id": 45, "fecha": "2026-06-21", "fase": "grupos", "grupo": "H",
     "sede": "Atlanta",           "local": "España",        "visitante": "Arabia Saudita"},
    {"id": 46, "fecha": "2026-06-21", "fase": "grupos", "grupo": "H",
     "sede": "Los Ángeles",       "local": "Uruguay",       "visitante": "Cabo Verde"},
    {"id": 47, "fecha": "2026-06-26", "fase": "grupos", "grupo": "H",
     "sede": "Nueva York",        "local": "España",        "visitante": "Uruguay"},
    {"id": 48, "fecha": "2026-06-26", "fase": "grupos", "grupo": "H",
     "sede": "Dallas",            "local": "Cabo Verde",    "visitante": "Arabia Saudita"},

    # ── GRUPO I: Francia · Senegal · Noruega · Irak ──────────────────────────
    {"id": 49, "fecha": "2026-06-16", "fase": "grupos", "grupo": "I",
     "sede": "Chicago",           "local": "Francia",  "visitante": "Senegal"},
    {"id": 50, "fecha": "2026-06-16", "fase": "grupos", "grupo": "I",
     "sede": "Seattle",           "local": "Noruega",  "visitante": "Irak"},
    {"id": 51, "fecha": "2026-06-22", "fase": "grupos", "grupo": "I",
     "sede": "Houston",           "local": "Noruega",  "visitante": "Senegal"},
    {"id": 52, "fecha": "2026-06-22", "fase": "grupos", "grupo": "I",
     "sede": "Miami",             "local": "Francia",  "visitante": "Irak"},
    {"id": 53, "fecha": "2026-06-26", "fase": "grupos", "grupo": "I",
     "sede": "Boston",            "local": "Francia",  "visitante": "Noruega"},
    {"id": 54, "fecha": "2026-06-26", "fase": "grupos", "grupo": "I",
     "sede": "Kansas City",       "local": "Senegal",  "visitante": "Irak"},

    # ── GRUPO J: Argentina · Argelia · Austria · Jordania ───────────────────
    {"id": 55, "fecha": "2026-06-16", "fase": "grupos", "grupo": "J",
     "sede": "Dallas",            "local": "Argentina","visitante": "Argelia"},
    {"id": 56, "fecha": "2026-06-16", "fase": "grupos", "grupo": "J",
     "sede": "Nueva York",        "local": "Austria",  "visitante": "Jordania"},
    {"id": 57, "fecha": "2026-06-22", "fase": "grupos", "grupo": "J",
     "sede": "San Francisco",     "local": "Argentina","visitante": "Austria"},
    {"id": 58, "fecha": "2026-06-22", "fase": "grupos", "grupo": "J",
     "sede": "Atlanta",           "local": "Jordania", "visitante": "Argelia"},
    {"id": 59, "fecha": "2026-06-26", "fase": "grupos", "grupo": "J",
     "sede": "Chicago",           "local": "Argentina","visitante": "Jordania"},
    {"id": 60, "fecha": "2026-06-26", "fase": "grupos", "grupo": "J",
     "sede": "Seattle",           "local": "Austria",  "visitante": "Argelia"},

    # ── GRUPO K: Portugal · Colombia · R.D. Congo · Uzbekistán ──────────────
    {"id": 61, "fecha": "2026-06-17", "fase": "grupos", "grupo": "K",
     "sede": "Kansas City",       "local": "Portugal",   "visitante": "R.D. Congo"},
    {"id": 62, "fecha": "2026-06-17", "fase": "grupos", "grupo": "K",
     "sede": "Houston",           "local": "Colombia",   "visitante": "Uzbekistán"},
    {"id": 63, "fecha": "2026-06-23", "fase": "grupos", "grupo": "K",
     "sede": "Dallas",            "local": "Portugal",   "visitante": "Uzbekistán"},
    {"id": 64, "fecha": "2026-06-23", "fase": "grupos", "grupo": "K",
     "sede": "Los Ángeles",       "local": "Colombia",   "visitante": "R.D. Congo"},
    {"id": 65, "fecha": "2026-06-27", "fase": "grupos", "grupo": "K",
     "sede": "Nueva York",        "local": "Portugal",   "visitante": "Colombia"},
    {"id": 66, "fecha": "2026-06-27", "fase": "grupos", "grupo": "K",
     "sede": "Chicago",           "local": "R.D. Congo", "visitante": "Uzbekistán"},

    # ── GRUPO L: Inglaterra · Croacia · Ghana · Panamá ──────────────────────
    {"id": 67, "fecha": "2026-06-17", "fase": "grupos", "grupo": "L",
     "sede": "Dallas",            "local": "Inglaterra","visitante": "Croacia"},
    {"id": 68, "fecha": "2026-06-17", "fase": "grupos", "grupo": "L",
     "sede": "Toronto",           "local": "Ghana",     "visitante": "Panamá"},
    {"id": 69, "fecha": "2026-06-23", "fase": "grupos", "grupo": "L",
     "sede": "Boston",            "local": "Inglaterra","visitante": "Ghana"},
    {"id": 70, "fecha": "2026-06-23", "fase": "grupos", "grupo": "L",
     "sede": "Atlanta",           "local": "Panamá",   "visitante": "Croacia"},
    {"id": 71, "fecha": "2026-06-27", "fase": "grupos", "grupo": "L",
     "sede": "Nueva York",        "local": "Panamá",   "visitante": "Inglaterra"},
    {"id": 72, "fecha": "2026-06-27", "fase": "grupos", "grupo": "L",
     "sede": "Seattle",           "local": "Croacia",  "visitante": "Ghana"},
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
    formato interno (nombres en español). Si falla, devuelve [] y se usa la semilla.
    """
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
            fase = "eliminatorias" if any(
                k in ronda for k in ("16", "8", "quarter", "semi", "final", "round of")
            ) else "grupos"
            partidos.append({
                "id": fx["id"],
                "fecha": fx.get("fecha", ""),
                "fase": fase,
                "grupo": "",
                "sede": "",
                "local":     normalizar(local_raw),
                "visitante": normalizar(visit_raw),
            })
        return sorted(partidos, key=lambda p: (p["fecha"], p["id"]))
    except Exception:
        return []


def guardar_fixture(partidos: List[Dict]) -> None:
    os.makedirs(os.path.dirname(FIXTURE_PATH), exist_ok=True)
    with open(FIXTURE_PATH, "w", encoding="utf-8") as f:
        json.dump(partidos, f, ensure_ascii=False, indent=2)
