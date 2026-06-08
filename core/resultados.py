"""
Obtención del marcador REAL de un partido, con cadena de fuentes:

  1) API-Football (datos estructurados, fuente principal)
  2) football-data.org (respaldo estructurado)
  3) Búsqueda web Tavily / Serper (último recurso)

PRINCIPIO DE SEGURIDAD: si ninguna fuente devuelve un marcador con confianza,
se devuelve None -> la celda queda "pendiente". Nunca se inventa un resultado,
para no contaminar las estadísticas de acierto.
"""

from __future__ import annotations
import re
from typing import Optional, Tuple

import requests

from core.deportes_api import apifootball_resultado, footballdata_resultado


_PATRON_MARCADOR = re.compile(r"(\d{1,2})\s*[-:\u2013]\s*(\d{1,2})")


def _parsear_marcador(texto: str) -> Optional[Tuple[int, int]]:
    for m in _PATRON_MARCADOR.finditer(texto or ""):
        a, b = int(m.group(1)), int(m.group(2))
        if 0 <= a <= 15 and 0 <= b <= 15:
            return a, b
    return None


# --- Último recurso: búsqueda web -----------------------------------------
def _resultado_tavily(local, visitante, fecha, api_key) -> Optional[Tuple[int, int]]:
    if not api_key:
        return None
    try:
        resp = requests.post(
            "https://api.tavily.com/search",
            json={"api_key": api_key,
                  "query": f"resultado final {local} vs {visitante} {fecha} Mundial 2026 marcador",
                  "search_depth": "advanced", "max_results": 5, "include_answer": True},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get("answer"):
            r = _parsear_marcador(data["answer"])
            if r:
                return r
        for item in data.get("results", []):
            r = _parsear_marcador(item.get("content", "") + " " + item.get("title", ""))
            if r:
                return r
    except Exception:
        return None
    return None


def _resultado_serper(local, visitante, fecha, api_key) -> Optional[Tuple[int, int]]:
    if not api_key:
        return None
    try:
        resp = requests.post(
            "https://google.serper.dev/search",
            headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
            json={"q": f"{local} vs {visitante} {fecha} resultado final marcador"},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        if "answerBox" in data:
            r = _parsear_marcador(str(data["answerBox"]))
            if r:
                return r
        for item in data.get("organic", []):
            r = _parsear_marcador(item.get("snippet", "") + " " + item.get("title", ""))
            if r:
                return r
    except Exception:
        return None
    return None


# --- Orquestador ----------------------------------------------------------
def obtener_resultado_real(
    local: str, visitante: str, fecha: str = "",
    apifootball_key: str = "", footballdata_key: str = "",
    tavily_key: str = "", serper_key: str = "",
) -> Optional[Tuple[int, int]]:
    """Recorre las fuentes en orden de fiabilidad. Devuelve None si ninguna acierta."""
    # 1) API-Football
    r = apifootball_resultado(apifootball_key, local, visitante)
    if r:
        return r
    # 2) football-data.org
    r = footballdata_resultado(footballdata_key, local, visitante)
    if r:
        return r
    # 3) búsqueda web
    r = _resultado_tavily(local, visitante, fecha, tavily_key)
    if r:
        return r
    return _resultado_serper(local, visitante, fecha, serper_key)
