"""
GOLPREDICTOR 2026 — Sala de análisis predictivo del Mundial.

Dashboard que:
  - Lista todos los partidos ordenados por fecha (scroll).
  - Muestra para cada uno: Predicción 1 (óptima por valor esperado) + % ,
    Predicción 2 (alternativa) + %, probabilidades 1X2, y el marcador real
    (autollenado desde API deportiva, con respaldo de scraping).
  - Compara predicho vs real cuando el partido termina, con desglose de puntos.
  - Incluye un chatbot al pie para preguntar / dar contexto (human in the loop).

Ejecutar:  streamlit run app.py
"""

from __future__ import annotations
import os
import datetime as dt
from collections import defaultdict

import streamlit as st

from core.fixture import cargar_fixture, fixture_desde_api, guardar_fixture, GRUPOS
from core.predictor import PoissonPredictor, Reglas, FuerzaEquipo
from core.inteligencia import analizar_partido, buscar_contexto_tavily, responder_chat
from core.resultados import obtener_resultado_real
from core.analisis import analizar_resultado
from core import almacen


# ---------------------------------------------------------------------------
# Configuración y secretos
# ---------------------------------------------------------------------------
st.set_page_config(page_title="Golpredictor 2026", page_icon="⚽", layout="wide")


def secreto(nombre: str) -> str:
    """Lee de st.secrets primero, luego de variables de entorno."""
    try:
        if nombre in st.secrets:
            return st.secrets[nombre]
    except Exception:
        pass
    return os.environ.get(nombre, "")


KEYS = {
    "apifootball": secreto("APIFOOTBALL_KEY"),
    "footballdata": secreto("FOOTBALLDATA_KEY"),
    "tavily": secreto("TAVILY_API_KEY"),
    "serper": secreto("SERPER_API_KEY"),
    "gemini": secreto("GEMINI_API_KEY"),
}


# ---------------------------------------------------------------------------
# Estilo (identidad visual: sala táctica — verde césped sobre pizarra)
# ---------------------------------------------------------------------------
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
.tarjeta {
  background: #161c24; border: 1px solid #232c38; border-radius: 10px;
  padding: 16px 18px; margin: 10px 0;
}
.equipos { font-family:'Barlow Condensed',sans-serif; font-size:1.35rem; font-weight:600; color:#eef2f6; }
.meta { color:#7d8a99; font-size:.8rem; font-family:'Inter',sans-serif; }
.pred-1 { color:#3ddc84; font-weight:700; font-size:1.5rem; font-family:'Barlow Condensed',sans-serif; }
.pred-2 { color:#9aa7b4; font-weight:600; font-size:1.15rem; font-family:'Barlow Condensed',sans-serif; }
.real-pend { color:#5a6776; font-style:italic; }
.real-ok { color:#ffd25a; font-weight:700; font-size:1.5rem; font-family:'Barlow Condensed',sans-serif; }
.chip { display:inline-block; padding:2px 9px; border-radius:20px; font-size:.72rem;
        font-family:'Inter',sans-serif; font-weight:600; }
.chip-pts { background:#13361f; color:#3ddc84; border:1px solid #1d5230; }
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Estado / carga de fixture
# ---------------------------------------------------------------------------
@st.cache_data(ttl=3600)
def _fixture_cacheado(usar_api: bool):
    if usar_api:
        api = fixture_desde_api(KEYS["apifootball"])
        if api:
            return api
    return cargar_fixture()


def _es_eliminatoria(partido) -> bool:
    return partido.get("fase", "grupos") == "eliminatorias"


# ---------------------------------------------------------------------------
# Cabecera
# ---------------------------------------------------------------------------
st.markdown("# ⚽ GOLPREDICTOR 2026")
st.markdown(
    "<span class='meta'>Motor predictivo Poisson + IA · optimizado para maximizar "
    "puntos según las reglas del juego. Las probabilidades son estimaciones, "
    "no certezas.</span>", unsafe_allow_html=True,
)

# Indicador de estado de APIs (visible al arrancar)
_keys_ok = [k for k, v in KEYS.items() if v]
_keys_ko = [k for k, v in KEYS.items() if not v]
if _keys_ok:
    st.success(f"✅ APIs activas: {', '.join(_keys_ok)}", icon=None)
if _keys_ko:
    st.warning(f"⚠️ Sin configurar (modo degradado): {', '.join(_keys_ko)}")

# Aviso honesto de calibración
with st.expander("¿Cómo funciona y qué esperar? (léelo una vez)"):
    st.markdown("""
**Esto NO adivina marcadores exactos con certeza** — nadie puede. El marcador exacto
de un partido de fútbol es de los eventos más difíciles de predecir.

Lo que hace este sistema es **maximizar tu valor esperado de puntos**:
- Modela los goles de cada equipo con distribuciones de Poisson.
- Calibra la fuerza de cada equipo con datos reales (API-Football) + contexto web (Tavily) razonado por IA (Gemini).
- Elige el pronóstico que da **más puntos esperados** según tus reglas (acertar el ganador pesa más que el marcador exacto).

**Predicción 1** = la jugada óptima estadística. **Predicción 2** = alternativa de respaldo.
El **%** es la probabilidad de que ESE marcador exacto ocurra (suele ser baja: el fútbol es así).
""")

col_a, col_b, col_c = st.columns([1, 1, 2])
with col_a:
    usar_api = st.toggle("Fixture desde API-Football", value=bool(KEYS["apifootball"]))
with col_b:
    if st.button("🔄 Recalcular predicciones"):
        st.cache_data.clear()
        for k in list(st.session_state.keys()):
            if k.startswith("pred_"):
                del st.session_state[k]
        st.rerun()

# Estado de las API keys
faltan = [n for n, v in KEYS.items() if not v]
if faltan:
    with col_c:
        st.warning(f"Faltan keys (modo degradado): {', '.join(faltan)}. "
                   "Configúralas en Settings → Secrets.", icon="⚠️")

try:
    partidos = _fixture_cacheado(usar_api)
except Exception as e:
    st.error(f"Error cargando fixture: {e}")
    st.stop()

predictor = PoissonPredictor()


# ---------------------------------------------------------------------------
# Cálculo perezoso de predicción por partido (cacheado en sesión)
# ---------------------------------------------------------------------------
def predecir_partido(p):
    clave = f"pred_{p['id']}"
    if clave in st.session_state:
        return st.session_state[clave]

    # 1) fuerzas calibradas (usa IA si hay keys; si no, neutrales)
    fuerzas = analizar_partido(
        p["local"], p["visitante"], KEYS["tavily"], KEYS["gemini"]
    )
    predictor.fuerzas = fuerzas
    reglas = Reglas.eliminatorias() if _es_eliminatoria(p) else Reglas.primera_ronda()
    res = predictor.top_dos_pronosticos(p["local"], p["visitante"], reglas)
    st.session_state[clave] = res
    return res


# ---------------------------------------------------------------------------
# Render: agrupar por fecha y mostrar con scroll
# ---------------------------------------------------------------------------
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


st.markdown("---")

for fecha in sorted(por_fecha.keys()):
    st.markdown(f"<div class='bloque-fecha'>{fecha_bonita(fecha)}</div>",
                unsafe_allow_html=True)

    for p in por_fecha[fecha]:
        guardado = almacen.get_prediccion(p["id"])
        with st.container():
            c1, c2, c3, c4 = st.columns([3, 2, 2, 2])

            # --- columna equipos ---
            with c1:
                grupo = f" · Grupo {p['grupo']}" if p.get("grupo") else ""
                sede = f" · {p['sede']}" if p.get("sede") else ""
                fase = "Eliminatoria" if _es_eliminatoria(p) else "Grupos"
                st.markdown(
                    f"<div class='equipos'>{p['local']} <span style='color:#5a6776'>vs</span> "
                    f"{p['visitante']}</div>"
                    f"<div class='meta'>{fase}{grupo}{sede}</div>",
                    unsafe_allow_html=True,
                )

            # --- predicción (perezosa: botón para calcular) ---
            ya = f"pred_{p['id']}" in st.session_state
            if not ya:
                with c2:
                    if st.button("Calcular", key=f"btn_{p['id']}"):
                        with st.spinner("Analizando..."):
                            predecir_partido(p)
                        st.rerun()
            else:
                r = st.session_state[f"pred_{p['id']}"]
                o1, o2 = r["opcion_1"], r["opcion_2"]
                pred = r["prediccion"]
                with c2:
                    st.markdown(
                        f"<div class='pred-1'>{o1['marcador'][0]} – {o1['marcador'][1]}</div>"
                        f"<div class='meta'>Predicción 1 · {o1['prob']*100:.0f}% · "
                        f"<span class='chip chip-pts'>{o1['pts_esperados']} pts esp.</span></div>",
                        unsafe_allow_html=True,
                    )
                with c3:
                    st.markdown(
                        f"<div class='pred-2'>{o2['marcador'][0]} – {o2['marcador'][1]}</div>"
                        f"<div class='meta'>Predicción 2 · {o2['prob']*100:.0f}%</div>"
                        f"<div class='meta'>1: {pred.prob_victoria_local*100:.0f}% · "
                        f"X: {pred.prob_empate*100:.0f}% · "
                        f"2: {pred.prob_victoria_visit*100:.0f}%</div>",
                        unsafe_allow_html=True,
                    )

            # --- marcador real + análisis ---
            with c4:
                real = guardado.get("real")
                if real:
                    rl, rv = real
                    st.markdown(
                        f"<div class='real-ok'>{rl} – {rv}</div>"
                        f"<div class='meta'>Marcador real</div>",
                        unsafe_allow_html=True,
                    )
                    if ya:
                        an = analizar_resultado(
                            st.session_state[f"pred_{p['id']}"]["opcion_1"]["marcador"],
                            (rl, rv), _es_eliminatoria(p),
                        )
                        st.markdown(
                            f"<div class='meta'>{an['veredicto']}<br>"
                            f"<span class='chip chip-pts'>{an['puntos']}/{an['max_posible']} pts</span></div>",
                            unsafe_allow_html=True,
                        )
                else:
                    st.markdown("<div class='real-pend'>pendiente</div>",
                                unsafe_allow_html=True)
                    if st.button("Buscar resultado", key=f"res_{p['id']}"):
                        with st.spinner("Buscando..."):
                            r = obtener_resultado_real(
                                p["local"], p["visitante"], p.get("fecha", ""),
                                KEYS["apifootball"], KEYS["footballdata"],
                                KEYS["tavily"], KEYS["serper"],
                            )
                        if r:
                            almacen.set_prediccion(p["id"], {"real": list(r)})
                            st.rerun()
                        else:
                            st.toast("Aún no hay resultado confiable. Sigue pendiente.")


# ---------------------------------------------------------------------------
# Chatbot human-in-the-loop
# ---------------------------------------------------------------------------
st.markdown("---")
st.markdown("## 💬 Mesa de análisis")
st.markdown("<span class='meta'>Pregunta sobre cualquier predicción, o aporta "
            "contexto (lesiones, clima, intuición) para afinar el modelo.</span>",
            unsafe_allow_html=True)

if "chat" not in st.session_state:
    st.session_state.chat = []

for msg in st.session_state.chat:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if entrada := st.chat_input("Escribe aquí..."):
    st.session_state.chat.append({"role": "user", "content": entrada})
    with st.chat_message("user"):
        st.markdown(entrada)

    # contexto web opcional + respuesta de Gemini
    with st.chat_message("assistant"):
        with st.spinner("Pensando..."):
            ctx = buscar_contexto_tavily(entrada, KEYS["tavily"], max_resultados=4)
            respuesta = responder_chat(entrada, ctx, KEYS["gemini"])
        st.markdown(respuesta)
    st.session_state.chat.append({"role": "assistant", "content": respuesta})
