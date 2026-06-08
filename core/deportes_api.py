"""
Cliente de datos deportivos para el Mundial 2026.

Fuente principal: API-Football (api-sports.io) — plan gratis 100 req/día.
Respaldo:         football-data.org — plan gratis.
Último recurso:   búsqueda web (Tavily/Serper) vía core.resultados.

Decisión de diseño: SIEMPRE preferimos datos estructurados de una API deportiva
sobre el scraping. El scraping solo entra si ambas APIs no devuelven el dato.
Y si nada lo encuentra con claridad, devolvemos None ("pendiente") en vez de
inventar un marcador.
"""

from __future__ import annotations
from typing import Optional, Tuple, List, Dict

import requests

# ID de la Copa del Mundo en API-Football (la "league" 1 es World Cup).
APIFOOTBALL_LEAGUE_WORLDCUP = 1
APIFOOTBALL_BASE = "https://v3.football.api-sports.io"
FOOTBALLDATA_BASE = "https://api.football-data.org/v4"
FOOTBALLDATA_WC_CODE = "WC"  # competición World Cup en football-data.org


# ---------------------------------------------------------------------------
# API-Football (principal)
# ---------------------------------------------------------------------------
def _apifootball_headers(api_key: str) -> dict:
    return {"x-apisports-key": api_key}


def apifootball_fixtures(api_key: str, season: int = 2026) -> List[Dict]:
    """Trae todos los partidos del Mundial. Devuelve lista normalizada."""
    if not api_key:
        return []
    try:
        resp = requests.get(
            f"{APIFOOTBALL_BASE}/fixtures",
            headers=_apifootball_headers(api_key),
            params={"league": APIFOOTBALL_LEAGUE_WORLDCUP, "season": season},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        partidos = []
        for item in data.get("response", []):
            fx = item.get("fixture", {})
            teams = item.get("teams", {})
            goals = item.get("goals", {})
            league = item.get("league", {})
            partidos.append({
                "id": fx.get("id"),
                "fecha": (fx.get("date") or "")[:10],
                "estado": fx.get("status", {}).get("short"),  # NS, FT, etc.
                "local": teams.get("home", {}).get("name"),
                "visitante": teams.get("away", {}).get("name"),
                "goles_local": goals.get("home"),
                "goles_visitante": goals.get("away"),
                "fase": league.get("round", ""),
            })
        return partidos
    except Exception:
        return []


def apifootball_resultado(
    api_key: str, local: str, visitante: str, season: int = 2026
) -> Optional[Tuple[int, int]]:
    """Busca el marcador FINAL de un partido concreto."""
    for fx in apifootball_fixtures(api_key, season):
        if (fx["local"] and fx["visitante"]
                and local.lower() in fx["local"].lower()
                and visitante.lower() in fx["visitante"].lower()
                and fx["estado"] == "FT"
                and fx["goles_local"] is not None):
            return int(fx["goles_local"]), int(fx["goles_visitante"])
    return None


# ---------------------------------------------------------------------------
# football-data.org (respaldo)
# ---------------------------------------------------------------------------
def footballdata_resultado(
    api_key: str, local: str, visitante: str
) -> Optional[Tuple[int, int]]:
    if not api_key:
        return None
    try:
        resp = requests.get(
            f"{FOOTBALLDATA_BASE}/competitions/{FOOTBALLDATA_WC_CODE}/matches",
            headers={"X-Auth-Token": api_key},
            params={"status": "FINISHED"},
            timeout=30,
        )
        resp.raise_for_status()
        for m in resp.json().get("matches", []):
            h = (m.get("homeTeam", {}).get("name") or "")
            a = (m.get("awayTeam", {}).get("name") or "")
            if local.lower() in h.lower() and visitante.lower() in a.lower():
                ft = m.get("score", {}).get("fullTime", {})
                if ft.get("home") is not None:
                    return int(ft["home"]), int(ft["away"])
    except Exception:
        return None
    return None
