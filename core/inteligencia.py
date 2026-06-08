"""
Capa de inteligencia: obtiene contexto del mundo real (forma reciente, lesiones,
historial) usando búsqueda web, y lo convierte en parámetros numéricos de fuerza
(ataque/defensa) que alimentan el modelo de Poisson.

Flujo:
  1. Tavily busca contexto actualizado de cada equipo / del partido.
  2. Gemini razona sobre ese contexto y devuelve fuerzas numéricas estructuradas.
  3. El resultado se cachea para no gastar llamadas de API de más.

Si no hay API keys configuradas, el módulo degrada con elegancia a valores
neutrales (1.0) en vez de fallar — así la app siempre arranca.
"""

from __future__ import annotations
import json
import os
import re
from dataclasses import asdict
from typing import Dict, Optional

import requests

from core.predictor import FuerzaEquipo


# ----------------------------------------------------------------------------
# Búsqueda web (Tavily)
# ----------------------------------------------------------------------------
def buscar_contexto_tavily(consulta: str, api_key: str, max_resultados: int = 5) -> str:
    """Devuelve un resumen de texto con el contexto encontrado en la web."""
    if not api_key:
        return ""
    try:
        resp = requests.post(
            "https://api.tavily.com/search",
            json={
                "api_key": api_key,
                "query": consulta,
                "search_depth": "advanced",
                "max_results": max_resultados,
                "include_answer": True,
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        partes = []
        if data.get("answer"):
            partes.append(data["answer"])
        for r in data.get("results", []):
            partes.append(f"- {r.get('title','')}: {r.get('content','')[:300]}")
        return "\n".join(partes)
    except Exception as e:
        return f"[contexto no disponible: {e}]"


# ----------------------------------------------------------------------------
# Razonamiento (Gemini) -> fuerzas numéricas
# ----------------------------------------------------------------------------
GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-2.0-flash:generateContent"
)


def _extraer_json(texto: str) -> Optional[dict]:
    """Extrae el primer objeto JSON de un texto (Gemini a veces lo envuelve)."""
    m = re.search(r"\{.*\}", texto, re.DOTALL)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return None


def estimar_fuerzas_gemini(
    equipo_a: str, equipo_b: str, contexto: str, api_key: str
) -> Dict[str, FuerzaEquipo]:
    """
    Pide a Gemini que, con el contexto dado, asigne fuerza de ataque y defensa
    a cada equipo en escala donde 1.0 = promedio mundial.
    """
    neutral = {equipo_a: FuerzaEquipo(), equipo_b: FuerzaEquipo()}
    if not api_key:
        return neutral

    prompt = f"""Eres un analista cuantitativo de fútbol. Con base en el contexto,
asigna a cada equipo un valor de ATAQUE y DEFENSA en escala donde 1.0 es el
promedio mundial. ATAQUE alto (>1) = marca más goles. DEFENSA alto (>1) = encaja
MÁS goles (peor defensa); DEFENSA bajo (<1) = defensa sólida. Rango razonable 0.5 a 1.8.

Equipos: "{equipo_a}" y "{equipo_b}".

CONTEXTO (forma reciente, lesiones, historial):
{contexto[:4000]}

Responde SOLO con JSON, sin texto adicional, con esta forma exacta:
{{"{equipo_a}": {{"ataque": <num>, "defensa": <num>}}, "{equipo_b}": {{"ataque": <num>, "defensa": <num>}}}}"""

    try:
        resp = requests.post(
            f"{GEMINI_URL}?key={api_key}",
            headers={"Content-Type": "application/json"},
            json={"contents": [{"parts": [{"text": prompt}]}],
                  "generationConfig": {"temperature": 0.3}},
            timeout=40,
        )
        resp.raise_for_status()
        data = resp.json()
        texto = data["candidates"][0]["content"]["parts"][0]["text"]
        parsed = _extraer_json(texto)
        if not parsed:
            return neutral
        out = {}
        for eq in (equipo_a, equipo_b):
            v = parsed.get(eq, {})
            out[eq] = FuerzaEquipo(
                ataque=float(v.get("ataque", 1.0)),
                defensa=float(v.get("defensa", 1.0)),
            )
        return out
    except Exception:
        return neutral


def analizar_partido(
    local: str, visitante: str,
    tavily_key: str, gemini_key: str,
) -> Dict[str, FuerzaEquipo]:
    """Pipeline completo: web -> razonamiento -> fuerzas numéricas."""
    consulta = (
        f"{local} vs {visitante} Mundial 2026 forma reciente lesiones "
        f"resultados últimos partidos análisis"
    )
    contexto = buscar_contexto_tavily(consulta, tavily_key)
    return estimar_fuerzas_gemini(local, visitante, contexto, gemini_key)


def responder_chat(pregunta: str, contexto: str, api_key: str) -> str:
    """
    Responde una pregunta del usuario en la 'mesa de análisis', usando el
    contexto web encontrado. Es el cerebro conversacional del human-in-the-loop.
    """
    if not api_key:
        return ("No hay clave de Gemini configurada, así que no puedo razonar la "
                "respuesta. Configúrala en Settings → Secrets para activar el chat.")
    prompt = f"""Eres un analista de fútbol experto y honesto que ayuda a un usuario
a preparar pronósticos del Mundial 2026. Sé claro, específico y NUNCA prometas
certezas imposibles sobre marcadores exactos. Si el usuario aporta contexto
(lesiones, clima, intuición), incorpóralo y explica cómo cambiaría tu análisis.

CONTEXTO WEB RECIENTE:
{contexto[:4000]}

PREGUNTA DEL USUARIO:
{pregunta}

Responde en español, conciso y útil."""
    try:
        resp = requests.post(
            f"{GEMINI_URL}?key={api_key}",
            headers={"Content-Type": "application/json"},
            json={"contents": [{"parts": [{"text": prompt}]}],
                  "generationConfig": {"temperature": 0.6}},
            timeout=40,
        )
        resp.raise_for_status()
        return resp.json()["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        return f"No pude generar respuesta ahora ({e}). Intenta de nuevo."
