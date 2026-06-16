"""
Capa de inteligencia: combina una base de datos de fuerzas por equipo (FIFA ranking)
con contexto web (Tavily) y razonamiento de DeepSeek para calibrar predicciones.

Flujo:
  1. equipos.py entrega fuerzas base (FIFA ranking) → predicciones ya diferenciadas.
  2. Tavily busca contexto actualizado (lesiones, forma reciente, noticias).
  3. DeepSeek ajusta las fuerzas base con el contexto encontrado (+/- 20% máx).
  4. Si no hay keys de IA, las fuerzas base ya producen predicciones realistas.
"""

from __future__ import annotations
import json
import re
from typing import Dict, Optional, Tuple

import requests

from core.predictor import FuerzaEquipo
from core.equipos import get_fuerza, razonamiento_fuerza


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
# Razonamiento (DeepSeek) — ajusta sobre las fuerzas base
# ----------------------------------------------------------------------------
DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"
DEEPSEEK_MODEL = "deepseek-chat"


def _deepseek_call(prompt: str, api_key: str, temperature: float = 0.3) -> str:
    """Llama a DeepSeek y devuelve el texto de la respuesta."""
    resp = requests.post(
        DEEPSEEK_URL,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        json={
            "model": DEEPSEEK_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
        },
        timeout=40,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def _extraer_json(texto: str) -> Optional[dict]:
    m = re.search(r"\{.*\}", texto, re.DOTALL)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return None


def _ajustar_con_deepseek(
    equipo_a: str, equipo_b: str,
    fuerza_a: FuerzaEquipo, fuerza_b: FuerzaEquipo,
    contexto: str, api_key: str
) -> Tuple[FuerzaEquipo, FuerzaEquipo, str]:
    """
    Pide a DeepSeek que ajuste las fuerzas base con el contexto actual.
    Devuelve (fuerza_a_ajustada, fuerza_b_ajustada, nota_ia).
    Máximo ±20% de ajuste sobre la base para evitar delirios.
    """
    if not api_key or not contexto or contexto.startswith("[contexto"):
        return fuerza_a, fuerza_b, ""

    prompt = f"""Eres un analista cuantitativo de fútbol. Tienes las fuerzas BASE de cada equipo
(ataque/defensa en escala donde 1.0 = promedio mundial, >1 es mejor ataque, >1 defensa = peor).

BASE:
- {equipo_a}: ataque={fuerza_a.ataque:.2f}, defensa={fuerza_a.defensa:.2f}
- {equipo_b}: ataque={fuerza_b.ataque:.2f}, defensa={fuerza_b.defensa:.2f}

CONTEXTO ACTUAL (lesiones, forma reciente, noticias):
{contexto[:3000]}

Ajusta los valores con el contexto. IMPORTANTE: el ajuste máximo permitido es ±0.20 sobre
la base. Si no hay información relevante, mantén los valores base.

Responde SOLO con JSON exactamente así (sin texto extra):
{{
  "{equipo_a}": {{"ataque": <num>, "defensa": <num>, "nota": "<motivo en 1 línea>"}},
  "{equipo_b}": {{"ataque": <num>, "defensa": <num>, "nota": "<motivo en 1 línea>"}}
}}"""

    try:
        texto = _deepseek_call(prompt, api_key, temperature=0.2)
        parsed = _extraer_json(texto)
        if not parsed:
            return fuerza_a, fuerza_b, ""

        def _clamped(base_val: float, nuevo: float, max_delta: float = 0.20) -> float:
            return max(base_val - max_delta, min(base_val + max_delta, float(nuevo)))

        def _parse_eq(eq_key, base_f: FuerzaEquipo):
            v = parsed.get(eq_key, {})
            return FuerzaEquipo(
                ataque=_clamped(base_f.ataque, v.get("ataque", base_f.ataque)),
                defensa=_clamped(base_f.defensa, v.get("defensa", base_f.defensa)),
            ), str(v.get("nota", ""))

        fa_new, nota_a = _parse_eq(equipo_a, fuerza_a)
        fb_new, nota_b = _parse_eq(equipo_b, fuerza_b)
        nota = f"🤖 DeepSeek: {nota_a} / {nota_b}" if (nota_a or nota_b) else ""
        return fa_new, fb_new, nota

    except Exception:
        return fuerza_a, fuerza_b, ""


def analizar_partido(
    local: str, visitante: str,
    tavily_key: str, deepseek_key: str,
) -> Dict[str, FuerzaEquipo]:
    """
    Devuelve fuerzas calibradas para el partido.
    Base = ranking FIFA (equipos.py). Ajuste = DeepSeek+Tavily si hay keys.
    """
    fuerza_local = get_fuerza(local)
    fuerza_visitante = get_fuerza(visitante)

    if not tavily_key and not deepseek_key:
        return {local: fuerza_local, visitante: fuerza_visitante}

    consulta = (
        f"{local} vs {visitante} Mundial 2026 forma reciente lesiones "
        f"resultados últimos partidos análisis"
    )
    contexto = buscar_contexto_tavily(consulta, tavily_key)
    fl_aj, fv_aj, _ = _ajustar_con_deepseek(
        local, visitante, fuerza_local, fuerza_visitante, contexto, deepseek_key
    )
    return {local: fl_aj, visitante: fv_aj}


def analizar_partido_completo(
    local: str, visitante: str,
    tavily_key: str, deepseek_key: str,
) -> Dict:
    """
    Como analizar_partido pero devuelve también el razonamiento y notas de IA.
    Retorna: {"fuerzas": {local: F, visitante: F}, "razonamiento": str, "nota_ia": str}
    """
    fuerza_local = get_fuerza(local)
    fuerza_visitante = get_fuerza(visitante)

    razonamiento = razonamiento_fuerza(local, visitante)
    nota_ia = ""

    if tavily_key or deepseek_key:
        consulta = (
            f"{local} vs {visitante} Mundial 2026 forma reciente lesiones "
            f"resultados últimos partidos análisis"
        )
        contexto = buscar_contexto_tavily(consulta, tavily_key)
        fl_aj, fv_aj, nota_ia = _ajustar_con_deepseek(
            local, visitante, fuerza_local, fuerza_visitante, contexto, deepseek_key
        )
    else:
        fl_aj, fv_aj = fuerza_local, fuerza_visitante

    return {
        "fuerzas": {local: fl_aj, visitante: fv_aj},
        "razonamiento": razonamiento,
        "nota_ia": nota_ia,
        "fuerzas_local": fl_aj,
        "fuerzas_visitante": fv_aj,
    }


def responder_chat(pregunta: str, contexto: str, api_key: str) -> str:
    """
    Responde una pregunta del usuario en la 'mesa de análisis', usando el
    contexto web encontrado.
    """
    if not api_key:
        return ("No hay clave de DeepSeek configurada. Confígurala en "
                "Environment Variables en Render para activar el chat con IA.")
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
        return _deepseek_call(prompt, api_key, temperature=0.6)
    except Exception as e:
        return f"No pude generar respuesta ahora ({e}). Intenta de nuevo."
