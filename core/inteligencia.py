"""
Capa de inteligencia: combina base de datos de fuerzas por equipo (FIFA ranking)
con contexto web (Tavily) y razonamiento de Gemini para calibrar predicciones.

Flujo:
  1. equipos.py entrega fuerzas base (FIFA ranking) -> predicciones ya diferenciadas.
  2. Tavily busca contexto actualizado (lesiones, forma reciente, noticias).
  3. Gemini ajusta las fuerzas base con el contexto encontrado (+-20% max).
  4. Sin keys de IA, las fuerzas base ya producen predicciones realistas.
"""

from __future__ import annotations
import json
import re
from typing import Dict, Optional, Tuple

import requests

from core.predictor import FuerzaEquipo
from core.equipos import get_fuerza, razonamiento_fuerza


def buscar_contexto_tavily(consulta: str, api_key: str, max_resultados: int = 5) -> str:
    if not api_key:
        return ""
    try:
        resp = requests.post(
            "https://api.tavily.com/search",
            json={"api_key": api_key, "query": consulta,
                  "search_depth": "advanced", "max_results": max_resultados,
                  "include_answer": True},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        partes = []
        if data.get("answer"):
            partes.append(data["answer"])
        for r in data.get("results", []):
            partes.append("- " + r.get("title", "") + ": " + r.get("content", "")[:300])
        return "\n".join(partes)
    except Exception as e:
        return "[contexto no disponible: " + str(e) + "]"


GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-2.0-flash:generateContent"
)


def _extraer_json(texto: str) -> Optional[dict]:
    m = re.search(r"\{.*\}", texto, re.DOTALL)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return None


def _ajustar_con_gemini(equipo_a, equipo_b, fuerza_a, fuerza_b, contexto, api_key):
    if not api_key or not contexto or contexto.startswith("[contexto"):
        return fuerza_a, fuerza_b, ""

    lineas_prompt = [
        "Eres un analista cuantitativo de futbol. Tienes las fuerzas BASE de cada equipo",
        "(ataque/defensa; 1.0 = promedio mundial, ataque alto = mas goles, defensa alto = encaja mas).",
        "",
        "BASE:",
        "- " + equipo_a + ": ataque=" + str(round(fuerza_a.ataque, 2)) + ", defensa=" + str(round(fuerza_a.defensa, 2)),
        "- " + equipo_b + ": ataque=" + str(round(fuerza_b.ataque, 2)) + ", defensa=" + str(round(fuerza_b.defensa, 2)),
        "",
        "CONTEXTO ACTUAL:",
        contexto[:3000],
        "",
        "Ajusta con el contexto. Maximo +-0.20 sobre la base. Si no hay info relevante, manten los valores.",
        'Responde SOLO con JSON:',
        '{',
        '  "' + equipo_a + '": {"ataque": <num>, "defensa": <num>, "nota": "<motivo en 1 linea>"},',
        '  "' + equipo_b + '": {"ataque": <num>, "defensa": <num>, "nota": "<motivo en 1 linea>"}',
        '}',
    ]
    prompt = "\n".join(lineas_prompt)

    try:
        resp = requests.post(
            GEMINI_URL + "?key=" + api_key,
            headers={"Content-Type": "application/json"},
            json={"contents": [{"parts": [{"text": prompt}]}],
                  "generationConfig": {"temperature": 0.2}},
            timeout=40,
        )
        resp.raise_for_status()
        texto = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
        parsed = _extraer_json(texto)
        if not parsed:
            return fuerza_a, fuerza_b, ""

        def _cl(base, nuevo, d=0.20):
            return max(base - d, min(base + d, float(nuevo)))

        def _pe(key, base_f):
            v = parsed.get(key, {})
            return FuerzaEquipo(
                ataque=_cl(base_f.ataque, v.get("ataque", base_f.ataque)),
                defensa=_cl(base_f.defensa, v.get("defensa", base_f.defensa)),
            ), str(v.get("nota", ""))

        fa_new, nota_a = _pe(equipo_a, fuerza_a)
        fb_new, nota_b = _pe(equipo_b, fuerza_b)
        nota = "Gemini: " + nota_a + " / " + nota_b if (nota_a or nota_b) else ""
        return fa_new, fb_new, nota
    except Exception:
        return fuerza_a, fuerza_b, ""


def analizar_partido(local, visitante, tavily_key, gemini_key):
    fl = get_fuerza(local)
    fv = get_fuerza(visitante)
    if not tavily_key and not gemini_key:
        return {local: fl, visitante: fv}
    consulta = local + " vs " + visitante + " Mundial 2026 forma reciente lesiones"
    contexto = buscar_contexto_tavily(consulta, tavily_key)
    fl_aj, fv_aj, _ = _ajustar_con_gemini(local, visitante, fl, fv, contexto, gemini_key)
    return {local: fl_aj, visitante: fv_aj}


def analizar_partido_completo(local, visitante, tavily_key, gemini_key):
    fl = get_fuerza(local)
    fv = get_fuerza(visitante)
    razonamiento = razonamiento_fuerza(local, visitante)
    nota_ia = ""
    if tavily_key or gemini_key:
        consulta = local + " vs " + visitante + " Mundial 2026 forma reciente lesiones resultados"
        contexto = buscar_contexto_tavily(consulta, tavily_key)
        fl_aj, fv_aj, nota_ia = _ajustar_con_gemini(local, visitante, fl, fv, contexto, gemini_key)
    else:
        fl_aj, fv_aj = fl, fv
    return {
        "fuerzas": {local: fl_aj, visitante: fv_aj},
        "razonamiento": razonamiento,
        "nota_ia": nota_ia,
        "fuerzas_local": fl_aj,
        "fuerzas_visitante": fv_aj,
    }


def responder_chat(pregunta, contexto, api_key):
    if not api_key:
        return "No hay clave de Gemini configurada. Configurala en Environment Variables de Render."

    lineas_prompt = [
        "Eres un analista de futbol experto y honesto para el Mundial 2026.",
        "Se claro y NUNCA prometas certezas sobre marcadores exactos.",
        "",
        "CONTEXTO WEB:",
        contexto[:4000],
        "",
        "PREGUNTA: " + pregunta,
        "",
        "Responde en espanol, conciso.",
    ]
    prompt = "\n".join(lineas_prompt)

    try:
        resp = requests.post(
            GEMINI_URL + "?key=" + api_key,
            headers={"Content-Type": "application/json"},
            json={"contents": [{"parts": [{"text": prompt}]}],
                  "generationConfig": {"temperature": 0.6}},
            timeout=40,
        )
        resp.raise_for_status()
        return resp.json()["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        return "No pude generar respuesta ahora (" + str(e) + "). Intenta de nuevo."
