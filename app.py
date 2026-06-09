"""
GOLPREDICTOR 2026 — Sala de análisis predictivo del Mundial.
"""

from __future__ import annotations
import os
import datetime as dt
from collections import defaultdict

import streamlit as st

from core.fixture import cargar_fixture, fixture_desde_api, guardar_fixture, GRUPOS
from core.predictor import PoissonPredictor, Reglas, FuerzaEquipo
from core.inteligencia import (
    analizar_partido_completo, buscar_contexto_tavily, responder_chat
)
from core.resultados import obtener_resultado_real
from core.analisis import analizar_resultado
from core.equipos import get_fuerza, razonamiento_fuerza
from core import almacen


st.set_page_config(page_title="Golpredictor 2026", page_icon="⚽", layout="wide")


def secreto(nombre: str) -> str:
    try:
        if nombre in st.secrets:
            return st.secrets[nombre]
    except Exception:
        pass
    return os.environ.get(nombre, "")


KEYS = {
    "apifootball": secreto("APIFOOTBALL_KEY"),
    "footballdata": secreto("FOOTBALLDATA_KEY"),
    "tavily":       secreto("TAVILY_API_KEY"),
    "serper":       secreto("SERPER_API_KEY"),
    "gemini":       secreto("GEMINI_API_KEY"),
}

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@500;600;700&family=Inter:wght@400;500;600&display=swap');
.stApp { background: #0f1419; }
h1, h2, h3 { font-family: 'Barlow Condensed', sans-serif !important; letter-spacing: .5px; }
.bloque-fecha {
  font-family: 'Barlow Condensed', sans-serif; font-size: 1.3rem; font-weight: 700;
  color: #3ddc84; text-transform: uppercase; letter-spacing: 2px;
  border-bottom: 1px solid #2a3340; padding: 14px 0 6px; margin-top: 18px;
}
.equipos { font-family:'Barlow Condensed',sans-serif; font-size:1.35rem; font-weight:600; color:#eef2f6; }
.meta { color:#7d8a99; font-size:.8rem; font-family:'Inter',sans-serif; }
.pred-1 { color:#3ddc84; font-weight:700; font-size:1.5rem; font-family:'Barlow Condensed',sans-serif; }
.pred-2 { color:#9aa7b4; font-weight:600; font-size:1.15rem; font-family:'Barlow Condensed',sans-serif; }
.real-pend { color:#5a6776; font-style:italic; }
.real-ok { color:#ffd25a; font-weight:700; font-size:1.5rem; font-family:'Barlow Condensed',sans-serif; }
.chip { display:inline-block; padding:2px 9px; border-radius:20px; font-size:.72rem; font-family:'Inter',sans-serif; font-weight:600; }
.chip-pts  { background:#13361f; color:#3ddc84; border:1px solid #1d5230; }
.chip-azul { background:#0e2040; color:#6ab4ff; border:1px solid #1a3560; }
.barra-wrap { background:#1e2a38; border-radius:4px; height:6px; width:100%; }
.barra-fill { border-radius:4px; height:6px; }
</style>
""", unsafe_allow_html=True)


@st.cache_data(ttl=3600)
def _fixture_cacheado(usar_api: bool):
    if usar_api:
        api = fixture_desde_api(KEYS["apifootball"])
        if api:
            return api
    return cargar_fixture()


def _es_eliminatoria(partido) -> bool:
    return partido.get("fase", "grupos") == "eliminatorias"


st.markdown("# ⚽ GOLPREDICTOR 2026")
st.markdown(
    "<span class='meta'>Motor predictivo Poisson + IA · optimizado para maximizar "
    "puntos según las reglas del juego.</span>", unsafe_allow_html=True)

_keys_ok = [k for k, v in KEYS.items() if v]
_keys_ko = [k for k, v in KEYS.items() if not v]
col_s1, col_s2 = st.columns(2)
with col_s1:
    if _keys_ok:
        st.success(f"✅ APIs activas: {', '.join(_keys_ok)}")
with col_s2:
    if _keys_ko:
        st.warning(f"⚠️ Sin configurar: {', '.join(_keys_ko)}")

with st.expander("ℹ️ ¿Cómo funciona?"):
    st.markdown("""
**Base**: ranking FIFA 2026 → fuerzas de ataque/defensa por equipo (ya diferenciadas).  
**Ajuste IA**: Tavily busca noticias/lesiones · Gemini calibra con ese contexto (±20% máx).  
**Optimización**: elige el marcador que maximiza tus puntos esperados según las reglas de Golpredictor.
""")

col_a, col_b, _ = st.columns([1, 1, 2])
with col_a:
    usar_api = st.toggle("Fixture desde API-Football", value=bool(KEYS["apifootball"]))
with col_b:
    if st.button("🔄 Recalcular todo"):
        st.cache_data.clear()
        for k in list(st.session_state.keys()):
            if k.startswith("pred_"):
                del st.session_state[k]
        st.rerun()

try:
    partidos = _fixture_cacheado(usar_api)
except Exception as e:
    st.error(f"Error cargando fixture: {e}")
    st.stop()

predictor = PoissonPredictor()


def calcular_partido(p: dict) -> dict:
    clave = f"pred_{p['id']}"
    if clave in st.session_state:
        return st.session_state[clave]
    anal = analizar_partido_completo(p["local"], p["visitante"], KEYS["tavily"], KEYS["gemini"])
    predictor.fuerzas = anal["fuerzas"]
    reglas = Reglas.eliminatorias() if _es_eliminatoria(p) else Reglas.primera_ronda()
    res = predictor.top_dos_pronosticos(p["local"], p["visitante"], reglas)
    res["razonamiento"] = anal.get("razonamiento", "")
    res["nota_ia"]      = anal.get("nota_ia", "")
    res["fuerza_local"]     = anal.get("fuerzas_local", FuerzaEquipo())
    res["fuerza_visitante"] = anal.get("fuerzas_visitante", FuerzaEquipo())
    st.session_state[clave] = res
    return res


por_fecha = defaultdict(list)
for p in partidos:
    por_fecha[p.get("fecha", "Sin fecha")].append(p)

MESES = ["", "ene", "feb", "mar", "abr", "may", "jun",
         "jul", "ago", "sep", "oct", "nov", "dic"]


def fecha_bonita(iso: str) -> str:
    try:
        d = dt.date.fromisoformat(iso)
        return f"{d.day} {MESES[d.month]} {d.year}"
    except Exception:
        return iso


def _barra(val: float, max_val: float = 2.2, color: str = "#3ddc84") -> str:
    pct = min(100, int(val / max_val * 100))
    return (f"<div class='barra-wrap'><div class='barra-fill' "
            f"style='width:{pct}%;background:{color}'></div></div>")


st.markdown("---")
st.markdown(f"<span class='meta'>{len(partidos)} partidos cargados</span>",
            unsafe_allow_html=True)

for fecha in sorted(por_fecha.keys()):
    st.markdown(f"<div class='bloque-fecha'>{fecha_bonita(fecha)}</div>",
                unsafe_allow_html=True)

    for p in por_fecha[fecha]:
        guardado = almacen.get_prediccion(p["id"])
        ya = f"pred_{p['id']}" in st.session_state

        with st.container():
            c1, c2, c3, c4 = st.columns([3, 2, 2, 2])

            with c1:
                grupo = f" · Grupo {p['grupo']}" if p.get("grupo") else ""
                sede  = f" · {p['sede']}"         if p.get("sede")  else ""
                fase  = "Eliminatoria" if _es_eliminatoria(p) else "Grupos"
                st.markdown(
                    f"<div class='equipos'>{p['local']} <span style='color:#5a6776'>vs</span> {p['visitante']}</div>"
                    f"<div class='meta'>{fase}{grupo}{sede}</div>",
                    unsafe_allow_html=True)

                fl = (st.session_state[f"pred_{p['id']}"].get("fuerza_local", get_fuerza(p["local"]))
                      if ya else get_fuerza(p["local"]))
                fv = (st.session_state[f"pred_{p['id']}"].get("fuerza_visitante", get_fuerza(p["visitante"]))
                      if ya else get_fuerza(p["visitante"]))

                with st.expander("📊 Análisis de la IA", expanded=False):
                    if ya:
                        r = st.session_state[f"pred_{p['id']}"]
                        if r.get("nota_ia"):
                            st.markdown(r["nota_ia"])
                        st.markdown(r.get("razonamiento", ""))
                    else:
                        st.markdown(razonamiento_fuerza(p["local"], p["visitante"]))

                    cf1, cf2 = st.columns(2)
                    with cf1:
                        st.markdown(f"**{p['local']}**")
                        st.markdown(f"<span class='meta'>Ataque {fl.ataque:.2f}</span>", unsafe_allow_html=True)
                        st.markdown(_barra(fl.ataque), unsafe_allow_html=True)
                        st.markdown(f"<span class='meta'>Defensa {fl.defensa:.2f} "
                                    f"({'débil' if fl.defensa>1.1 else 'sólida'})</span>", unsafe_allow_html=True)
                        st.markdown(_barra(fl.defensa, color="#e05a5a"), unsafe_allow_html=True)
                    with cf2:
                        st.markdown(f"**{p['visitante']}**")
                        st.markdown(f"<span class='meta'>Ataque {fv.ataque:.2f}</span>", unsafe_allow_html=True)
                        st.markdown(_barra(fv.ataque), unsafe_allow_html=True)
                        st.markdown(f"<span class='meta'>Defensa {fv.defensa:.2f} "
                                    f"({'débil' if fv.defensa>1.1 else 'sólida'})</span>", unsafe_allow_html=True)
                        st.markdown(_barra(fv.defensa, color="#e05a5a"), unsafe_allow_html=True)

            if not ya:
                with c2:
                    if st.button("🧠 Calcular", key=f"btn_{p['id']}"):
                        with st.spinner("Analizando..."):
                            calcular_partido(p)
                        st.rerun()
                with c3:
                    st.markdown("<span class='meta'>Abre '📊 Análisis' para ver<br>las fuerzas base, o pulsa Calcular</span>",
                                unsafe_allow_html=True)
            else:
                r = st.session_state[f"pred_{p['id']}"]
                o1, o2 = r["opcion_1"], r["opcion_2"]
                pred = r["prediccion"]
                with c2:
                    st.markdown(
                        f"<div class='pred-1'>{o1['marcador'][0]} – {o1['marcador'][1]}</div>"
                        f"<div class='meta'>Predicción 1 · {o1['prob']*100:.0f}% · "
                        f"<span class='chip chip-pts'>{o1['pts_esperados']:.1f} pts esp.</span></div>",
                        unsafe_allow_html=True)
                with c3:
                    st.markdown(
                        f"<div class='pred-2'>{o2['marcador'][0]} – {o2['marcador'][1]}</div>"
                        f"<div class='meta'>Predicción 2 · {o2['prob']*100:.0f}%</div>"
                        f"<div class='meta'>"
                        f"<span class='chip chip-azul'>1:{pred.prob_victoria_local*100:.0f}%</span> "
                        f"<span class='chip chip-azul'>X:{pred.prob_empate*100:.0f}%</span> "
                        f"<span class='chip chip-azul'>2:{pred.prob_victoria_visit*100:.0f}%</span></div>",
                        unsafe_allow_html=True)

            with c4:
                real = guardado.get("real")
                if real:
                    rl, rv = real
                    st.markdown(
                        f"<div class='real-ok'>{rl} – {rv}</div>"
                        f"<div class='meta'>Marcador real</div>",
                        unsafe_allow_html=True)
                    if ya:
                        an = analizar_resultado(
                            st.session_state[f"pred_{p['id']}"]["opcion_1"]["marcador"],
                            (rl, rv), _es_eliminatoria(p))
                        st.markdown(
                            f"<div class='meta'>{an['veredicto']}<br>"
                            f"<span class='chip chip-pts'>{an['puntos']}/{an['max_posible']} pts</span></div>",
                            unsafe_allow_html=True)
                else:
                    st.markdown("<div class='real-pend'>⏳ pendiente</div>", unsafe_allow_html=True)
                    if st.button("🔍 Buscar resultado", key=f"res_{p['id']}"):
                        with st.spinner("Buscando..."):
                            r2 = obtener_resultado_real(
                                p["local"], p["visitante"], p.get("fecha", ""),
                                KEYS["apifootball"], KEYS["footballdata"],
                                KEYS["tavily"], KEYS["serper"])
                        if r2:
                            almacen.set_prediccion(p["id"], {"real": list(r2)})
                            st.rerun()
                        else:
                            st.toast("Áun no hay resultado confiable.")

        st.markdown("<hr style='border:0;border-top:1px solid #1e2a38;margin:4px 0'>",
                    unsafe_allow_html=True)


st.markdown("---")
st.markdown("## 💬 Mesa de análisis")
st.markdown(
    "<span class='meta'>Pregunta sobre cualquier partido, aporta contexto (lesiones, "
    "noticias) o pide que recalcule con nueva información.</span>",
    unsafe_allow_html=True)

if "chat" not in st.session_state:
    st.session_state.chat = []

for msg in st.session_state.chat:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if entrada := st.chat_input("¿Quién gana Brasil vs Marruecos? / ¿Qué pasa con Messi?"):
    st.session_state.chat.append({"role": "user", "content": entrada})
    with st.chat_message("user"):
        st.markdown(entrada)
    with st.chat_message("assistant"):
        with st.spinner("Analizando..."):
            ctx = buscar_contexto_tavily(entrada, KEYS["tavily"], max_resultados=4)
            respuesta = responder_chat(entrada, ctx, KEYS["gemini"])
        st.markdown(respuesta)
    st.session_state.chat.append({"role": "assistant", "content": respuesta})
