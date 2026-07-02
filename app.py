"""
GOLPREDICTOR 2026 — Sala de análisis predictivo del Mundial.

Dashboard que:
  - Lista todos los partidos ordenados por fecha (scroll).
  - Muestra para cada uno: Predicción 1 (más probable según Poisson+DC) + %,
    Predicción 2 (óptima para puntos Golpredictor) + %, probabilidades 1X2, marcador real y análisis IA.
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
from core.inteligencia import (
    analizar_partido_completo, buscar_contexto_tavily, responder_chat
)
from core.resultados import obtener_resultado_real
from core.analisis import analizar_resultado
from core.equipos import get_fuerza, razonamiento_fuerza
from core import almacen, bayesiano
from core.montecarlo import simular_torneo
from core.llave import generar_html_llave
import streamlit.components.v1 as stc


# ---------------------------------------------------------------------------
# Configuración y secretos
# ---------------------------------------------------------------------------
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
    "deepseek":     secreto("DEEPSEEK_API_KEY"),
}


# ---------------------------------------------------------------------------
# Estilo visual — fondo claro, texto azul oscuro
# ---------------------------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@500;600;700&family=Inter:wght@400;500;600&display=swap');
.stApp { background: #ffffff; }
h1, h2, h3 { font-family: 'Barlow Condensed', sans-serif !important; letter-spacing: .5px; color: #0d2b52; }
.bloque-fecha {
  font-family: 'Barlow Condensed', sans-serif; font-size: 1.3rem; font-weight: 700;
  color: #0d2b52; text-transform: uppercase; letter-spacing: 2px;
  border-bottom: 1px solid #d7e0ea; padding: 14px 0 6px; margin-top: 18px;
}
.equipos { font-family:'Barlow Condensed',sans-serif; font-size:1.35rem; font-weight:600; color:#0d2b52; }
.meta { color:#5a6b7d; font-size:.8rem; font-family:'Inter',sans-serif; }
.pred-1 { color:#0d2b52; font-weight:700; font-size:1.5rem; font-family:'Barlow Condensed',sans-serif; }
.pred-2 { color:#4a5a6b; font-weight:600; font-size:1.15rem; font-family:'Barlow Condensed',sans-serif; }
.real-pend { color:#8a97a6; font-style:italic; }
.real-ok { color:#b8860b; font-weight:700; font-size:1.5rem; font-family:'Barlow Condensed',sans-serif; }
.chip { display:inline-block; padding:2px 9px; border-radius:20px; font-size:.72rem;
        font-family:'Inter',sans-serif; font-weight:600; }
.chip-pts  { background:#e3edf9; color:#0d2b52; border:1px solid #b8d4f0; }
.chip-azul { background:#eef3fa; color:#1a4d8f; border:1px solid #c9dbf0; }
.barra-wrap { background:#e2e8f0; border-radius:4px; height:6px; width:100%; }
.barra-fill { background:#1a4d8f; border-radius:4px; height:6px; }
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

# Indicadores de estado
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
**Base de predicción**: ranking FIFA 2026 → fuerzas de ataque/defensa por equipo.
**Ajuste IA**: Tavily busca noticias/lesiones · Gemini calibra con ese contexto (±20% max).
**Optimización**: el marcador elegido es el que maximiza tus puntos esperados, no el más probable.

**Predicción 1** = marcador más probable según Poisson + Dixon-Coles (varía mucho por partido).
**Predicción 2** = marcador óptimo para maximizar puntos Golpredictor (el estratégico).
El **%** es la probabilidad de ese marcador exacto (suele ser baja: el fútbol es impredecible).
""")

col_a, col_b, col_c = st.columns([1, 1, 2])
with col_a:
    usar_api = st.toggle("Fixture desde API-Football", value=bool(KEYS["apifootball"]))
with col_b:
    if st.button("🔄 Recalcular todo"):
        st.cache_data.clear()
        for k in list(st.session_state.keys()):
            if k.startswith("pred_") or k.startswith("anal_"):
                del st.session_state[k]
        st.rerun()

try:
    partidos = _fixture_cacheado(usar_api)
except Exception as e:
    st.error(f"Error cargando fixture: {e}")
    st.stop()

predictor = PoissonPredictor()

# ── Fuerzas Bayesianas ────────────────────────────────────────────────────────
# Se recalculan una vez por sesión y se invalidan cuando entra un resultado nuevo.
if "fuerzas_bayes" not in st.session_state:
    _res_bayes = almacen.get_resultados_para_bayes(partidos)
    st.session_state["fuerzas_bayes"] = bayesiano.actualizar(_res_bayes)

_n_bayes = len(st.session_state["fuerzas_bayes"])
if _n_bayes:
    st.success(f"🧠 Bayes activo: {_n_bayes} equipos con fuerzas ajustadas por resultados reales.")


# ---------------------------------------------------------------------------
# Cálculo perezoso de predicción + análisis (cacheado en sesión)
# ---------------------------------------------------------------------------
def calcular_partido(p: dict) -> dict:
    """Calcula predicción + análisis y lo guarda en session_state."""
    clave = f"pred_{p['id']}"
    if clave in st.session_state:
        return st.session_state[clave]

    # Análisis completo (fuerzas + razonamiento)
    anal = analizar_partido_completo(
        p["local"], p["visitante"], KEYS["tavily"], KEYS["deepseek"]
    )
    fuerzas = anal["fuerzas"]

    # Aplicar fuerzas Bayesianas como línea base post-torneo
    # (los datos reales del torneo superan al ranking FIFA estático)
    fb = st.session_state.get("fuerzas_bayes", {})
    for eq in [p["local"], p["visitante"]]:
        if eq in fb:
            fuerzas[eq] = fb[eq]

    predictor.fuerzas = fuerzas

    reglas = Reglas.eliminatorias() if _es_eliminatoria(p) else Reglas.primera_ronda()
    pred_res = predictor.top_dos_pronosticos(p["local"], p["visitante"], reglas)
    pred_res["razonamiento"] = anal.get("razonamiento", "")
    pred_res["nota_ia"] = anal.get("nota_ia", "")
    pred_res["fuerza_local"] = fuerzas.get(p["local"], FuerzaEquipo())
    pred_res["fuerza_visitante"] = fuerzas.get(p["visitante"], FuerzaEquipo())

    st.session_state[clave] = pred_res
    return pred_res


# ---------------------------------------------------------------------------
# Render: agrupar por fecha y mostrar con scroll
# ---------------------------------------------------------------------------
MESES = ["", "ene", "feb", "mar", "abr", "may", "jun",
         "jul", "ago", "sep", "oct", "nov", "dic"]


def fecha_bonita(iso: str) -> str:
    try:
        d = dt.date.fromisoformat(iso)
        return f"{d.day} {MESES[d.month]} {d.year}"
    except Exception:
        return iso


def _barra(val: float, max_val: float = 2.2, color: str = "#1a4d8f") -> str:
    pct = min(100, int(val / max_val * 100))
    return (f"<div class='barra-wrap'>"
            f"<div class='barra-fill' style='width:{pct}%;background:{color}'></div>"
            f"</div>")


def _heatmap_html(M, local: str, visitante: str, max_g: int = 5) -> str:
    """Genera tabla HTML de calor con % de probabilidad por marcador (max_g x max_g)."""
    max_prob = max(M[i][j] for i in range(max_g + 1) for j in range(max_g + 1))
    rows = ["<table style='border-collapse:separate;border-spacing:2px;font-size:.72rem'>"]
    # Cabecera: goles visitante
    rows.append("<tr>")
    rows.append("<td style='color:#8a97a6;padding:3px 6px;font-size:.65rem'>LOC\\ VIS</td>")
    for j in range(max_g + 1):
        rows.append(
            f"<td style='color:#1a4d8f;text-align:center;padding:3px 8px;"
            f"font-weight:700'>{j}</td>"
        )
    rows.append("</tr>")
    for i in range(max_g + 1):
        rows.append("<tr>")
        rows.append(
            f"<td style='color:#0d2b52;padding:3px 6px;font-weight:700'>{i}</td>"
        )
        for j in range(max_g + 1):
            prob = M[i][j]
            pct = prob * 100
            intens = (prob / max_prob) if max_prob > 0 else 0
            # Gradiente blanco -> azul oscuro
            r_c = int(255 - intens * (255 - 13))
            g_c = int(255 - intens * (255 - 43))
            b_c = int(255 - intens * (255 - 82))
            bg = f"rgb({r_c},{g_c},{b_c})"
            txt = "#ffffff" if intens > 0.45 else "#3a4a5a"
            border = "1px solid #1a4d8f" if i == j else "1px solid #e2e8f0"
            rows.append(
                f"<td style='background:{bg};color:{txt};text-align:center;"
                f"padding:4px 7px;border-radius:4px;border:{border}'>"
                f"{pct:.1f}%</td>"
            )
        rows.append("</tr>")
    rows.append("</table>")
    rows.append(
        f"<div style='color:#8a97a6;font-size:.65rem;margin-top:3px'>"
        f"Filas = goles {local} &nbsp;|&nbsp; Columnas = goles {visitante} "
        f"&nbsp;|&nbsp; Diagonal = empate</div>"
    )
    return "\n".join(rows)


# ---------------------------------------------------------------------------
# Sección Monte Carlo
# ---------------------------------------------------------------------------
st.markdown("---")
with st.expander("🎲 Simulacion Monte Carlo del torneo", expanded=True):
    st.markdown(
        "<span class='meta'>Simula el torneo completo miles de veces con el modelo "
        "de Poisson + Dixon-Coles. Muestra la probabilidad de que cada equipo clasifique "
        "de grupos, llegue a semis, a la final y salga campeon.</span>",
        unsafe_allow_html=True,
    )
    col_mc1, col_mc2 = st.columns([1, 3])
    with col_mc1:
        n_sims = st.select_slider(
            "Simulaciones", options=[1000, 2000, 5000, 10000], value=10000
        )
    with col_mc2:
        run_mc = st.button("▶ Correr simulacion", key="btn_mc")

    if run_mc or "mc_result" in st.session_state:
        if run_mc:
            with st.spinner(f"Simulando {n_sims:,} torneos..."):
                _res_reales = almacen.get_todos_resultados()
                _pen_reales = almacen.get_todos_penaltis()
                _fb_mc      = st.session_state.get("fuerzas_bayes") or None
                st.session_state["mc_result"] = simular_torneo(
                    partidos, n_sims, _res_reales, _fb_mc, _pen_reales
                )
                st.session_state["mc_n"]      = n_sims
                st.session_state["mc_fijos"]  = len(_res_reales)

        mc = st.session_state.get("mc_result", {})
        mc_n = st.session_state.get("mc_n", n_sims)

        if mc:
            _fijos_lbl = st.session_state.get("mc_fijos", 0)
            _bayes_lbl = len(st.session_state.get("fuerzas_bayes", {}))
            st.markdown(
                f"<span class='meta'>{mc_n:,} simulaciones · "
                f"<span style='color:#b8860b'>{_fijos_lbl} partidos con resultado real fijo</span> · "
                f"<span style='color:#1a4d8f'>Bayes: {_bayes_lbl} equipos ajustados</span></span>",
                unsafe_allow_html=True,
            )

            # Ordenar por probabilidad de campeon
            equipos_ord = sorted(
                mc.items(),
                key=lambda x: x[1].get("campeon", 0),
                reverse=True,
            )

            # Tabla resumen
            etapas = [
                ("clasifica", "Clasifica grupos"),
                ("octavos",   "Octavos"),
                ("cuartos",   "Cuartos"),
                ("semis",     "Semifinal"),
                ("final",     "Final"),
                ("campeon",   "Campeon"),
            ]

            # Cabecera
            header_cols = st.columns([2] + [1] * len(etapas))
            header_cols[0].markdown("<span style='color:#5a6b7d;font-size:.75rem'>EQUIPO</span>",
                                    unsafe_allow_html=True)
            for idx, (_, label) in enumerate(etapas):
                header_cols[idx + 1].markdown(
                    f"<span style='color:#5a6b7d;font-size:.75rem'>{label}</span>",
                    unsafe_allow_html=True,
                )

            # Filas (top 20)
            for equipo, datos in equipos_ord[:20]:
                row_cols = st.columns([2] + [1] * len(etapas))
                row_cols[0].markdown(
                    f"<span style='color:#0d2b52;font-size:.85rem'>{equipo}</span>",
                    unsafe_allow_html=True,
                )
                for idx, (clave, _) in enumerate(etapas):
                    val = datos.get(clave, 0)
                    if val > 0:
                        color = "#1a4d8f" if val > 0.3 else ("#b8860b" if val > 0.1 else "#5a6b7d")
                        row_cols[idx + 1].markdown(
                            f"<span style='color:{color};font-size:.85rem'>{val*100:.0f}%</span>",
                            unsafe_allow_html=True,
                        )
                    else:
                        row_cols[idx + 1].markdown(
                            "<span style='color:#c2cad4;font-size:.85rem'>—</span>",
                            unsafe_allow_html=True,
                        )

            # Podio top 5 campeons
            st.markdown(
                "<div style='margin-top:16px;color:#0d2b52;font-size:.9rem;"
                "font-weight:600;letter-spacing:.5px'>FAVORITOS AL TITULO</div>",
                unsafe_allow_html=True,
            )
            podio = [(e, d.get("campeon", 0)) for e, d in equipos_ord[:5]]
            p_cols = st.columns(5)
            medallas = ["🥇", "🥈", "🥉", "4o", "5o"]
            for idx, (equipo, prob) in enumerate(podio):
                p_cols[idx].markdown(
                    f"<div style='text-align:center;background:#f5f8fc;border-radius:8px;"
                    f"padding:10px 4px;border:1px solid #dbe6f2'>"
                    f"<div style='font-size:1.4rem'>{medallas[idx]}</div>"
                    f"<div style='color:#0d2b52;font-size:.85rem;font-weight:600'>{equipo}</div>"
                    f"<div style='color:#1a4d8f;font-size:1.1rem;font-weight:700'>{prob*100:.1f}%</div>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
        else:
            st.info("No hay grupos con fixture definido para simular.")

st.markdown("---")

# ---------------------------------------------------------------------------
# Llave del torneo (R32 → Final)
# ---------------------------------------------------------------------------
with st.expander("🏆 Llave del torneo — 1/16 a Final", expanded=True):
    _r32_partidos = sorted(
        [p for p in partidos if p.get("ronda") == "R32"],
        key=lambda x: x["id"],
    )
    if len(_r32_partidos) < 16:
        st.info("Faltan partidos de eliminatoria en el fixture para mostrar la llave.")
    else:
        _fb_llave = st.session_state.get("fuerzas_bayes", {})

        def _get_pred_llave(local: str, visitante: str):
            """Devuelve ([g_local, g_visit], p1, p2, winner_name) usando Poisson+Bayes."""
            _fl = _fb_llave.get(local, get_fuerza(local))
            _fv = _fb_llave.get(visitante, get_fuerza(visitante))
            predictor.fuerzas = {local: _fl, visitante: _fv}
            try:
                qr = predictor.top_dos_pronosticos(local, visitante, Reglas.eliminatorias())
                pred = qr["prediccion"]
                o1  = qr["opcion_1"]
                pm  = list(o1["marcador"])
                p1  = round(pred.prob_victoria_local * 100)
                p2  = round(pred.prob_victoria_visit * 100)
                winner = local if pm[0] > pm[1] else visitante
            except Exception as e:
                # Fallback SIN esconder el problema: si el motor Poisson falla
                # para este cruce, usamos la fuerza cruda (ataque/defensa) para
                # decidir un ganador razonable en vez de asumir siempre "local".
                st.session_state.setdefault("_errores_llave", []).append(
                    f"{local} vs {visitante}: {e}"
                )
                ventaja_local = (_fl.ataque / _fv.defensa) - (_fv.ataque / _fl.defensa)
                winner = local if ventaja_local >= 0 else visitante
                pm, p1, p2 = [1, 1], 50, 50
            return pm, p1, p2, winner

        _html_llave = generar_html_llave(
            _r32_partidos[:16],
            lambda pid: almacen.get_prediccion(pid),
            _get_pred_llave,
        )
        stc.html(_html_llave, height=680, scrolling=True)

        if st.session_state.get("_errores_llave"):
            with st.expander("⚠️ Cruces con error en el motor de predicción", expanded=False):
                for msg in st.session_state["_errores_llave"]:
                    st.markdown(f"<span class='meta'>{msg}</span>", unsafe_allow_html=True)

st.markdown("---")

# ---------------------------------------------------------------------------
# Lista de partidos — la fase de grupos (ronda 1) se oculta por defecto.
# Los resultados reales de esos partidos siguen intactos en la base de datos
# (data/predicciones.json) y se siguen usando en Bayes / Monte Carlo / Llave;
# esto solo afecta qué se dibuja en esta lista.
# ---------------------------------------------------------------------------
_col_f1, _col_f2 = st.columns([1, 3])
with _col_f1:
    mostrar_grupos = st.toggle("Mostrar fase de grupos (ronda 1)", value=False)

_partidos_lista = partidos if mostrar_grupos else [p for p in partidos if _es_eliminatoria(p)]

por_fecha = defaultdict(list)
for p in _partidos_lista:
    por_fecha[p.get("fecha", "Sin fecha")].append(p)

st.markdown(f"<span class='meta'>Mostrando {len(_partidos_lista)} de {len(partidos)} partidos · "
            f"{sum(1 for p in partidos if almacen.get_prediccion(p['id']).get('real'))} con resultado real en total</span>",
            unsafe_allow_html=True)

for fecha in sorted(por_fecha.keys()):
    st.markdown(f"<div class='bloque-fecha'>{fecha_bonita(fecha)}</div>",
                unsafe_allow_html=True)

    for p in por_fecha[fecha]:
        guardado = almacen.get_prediccion(p["id"])
        ya = f"pred_{p['id']}" in st.session_state

        with st.container():
            c1, c2, c3, c4 = st.columns([3, 2, 2, 2])

            # ── Columna 1: equipos + análisis base ─────────────────
            with c1:
                grupo = f" · Grupo {p['grupo']}" if p.get("grupo") else ""
                sede  = f" · {p['sede']}"         if p.get("sede")  else ""
                fase  = "Eliminatoria" if _es_eliminatoria(p) else "Grupos"
                st.markdown(
                    f"<div class='equipos'>{p['local']} "
                    f"<span style='color:#8a97a6'>vs</span> {p['visitante']}</div>"
                    f"<div class='meta'>{fase}{grupo}{sede}</div>",
                    unsafe_allow_html=True,
                )

                # Fuerzas base (siempre visibles, sin necesidad de calcular)
                fl = get_fuerza(p["local"])
                fv = get_fuerza(p["visitante"])
                with st.expander("📊 Análisis de la IA", expanded=False):
                    if ya:
                        r = st.session_state[f"pred_{p['id']}"]
                        # Fuerzas ajustadas
                        fl = r.get("fuerza_local", fl)
                        fv = r.get("fuerza_visitante", fv)
                        if r.get("nota_ia"):
                            st.markdown(r["nota_ia"])
                        st.markdown(r.get("razonamiento", ""))
                    else:
                        st.markdown(razonamiento_fuerza(p["local"], p["visitante"]))

                    col_fl, col_fv = st.columns(2)
                    with col_fl:
                        st.markdown(f"**{p['local']}**")
                        st.markdown(f"<span class='meta'>Ataque: {fl.ataque:.2f}</span>",
                                    unsafe_allow_html=True)
                        st.markdown(_barra(fl.ataque), unsafe_allow_html=True)
                        st.markdown(f"<span class='meta'>Defensa: {fl.defensa:.2f} "
                                    f"({'débil' if fl.defensa>1.1 else 'sólida'})</span>",
                                    unsafe_allow_html=True)
                        st.markdown(_barra(fl.defensa, color="#c0392b"), unsafe_allow_html=True)
                    with col_fv:
                        st.markdown(f"**{p['visitante']}**")
                        st.markdown(f"<span class='meta'>Ataque: {fv.ataque:.2f}</span>",
                                    unsafe_allow_html=True)
                        st.markdown(_barra(fv.ataque), unsafe_allow_html=True)
                        st.markdown(f"<span class='meta'>Defensa: {fv.defensa:.2f} "
                                    f"({'débil' if fv.defensa>1.1 else 'sólida'})</span>",
                                    unsafe_allow_html=True)
                        st.markdown(_barra(fv.defensa, color="#c0392b"), unsafe_allow_html=True)

                    # ── Mapa de calor de probabilidades (solo si hay prediccion) ──
                    if ya:
                        r_hm = st.session_state[f"pred_{p['id']}"]
                        fl_hm = r_hm.get("fuerza_local", fl)
                        fv_hm = r_hm.get("fuerza_visitante", fv)
                        predictor.fuerzas = {p["local"]: fl_hm, p["visitante"]: fv_hm}
                        lam_l_hm, lam_v_hm = predictor._lambdas(p["local"], p["visitante"])
                        M_hm = predictor.matriz_probabilidades(lam_l_hm, lam_v_hm)
                        st.markdown(
                            "<div style='margin-top:12px;color:#4a5a6b;font-size:.8rem;"
                            "font-weight:600;letter-spacing:.5px'>MAPA DE PROBABILIDADES</div>",
                            unsafe_allow_html=True,
                        )
                        st.markdown(_heatmap_html(M_hm, p["local"], p["visitante"]),
                                    unsafe_allow_html=True)

            # ── Columna 2 & 3: predicciones ───────────────
            if not ya:
                # Distribución rápida con fuerzas base FIFA (sin IA, cálculo instantáneo)
                _fb = st.session_state.get("fuerzas_bayes", {})
                _fl_q = _fb.get(p["local"],      get_fuerza(p["local"]))
                _fv_q = _fb.get(p["visitante"],  get_fuerza(p["visitante"]))
                predictor.fuerzas = {p["local"]: _fl_q, p["visitante"]: _fv_q}
                _reglas_q = Reglas.eliminatorias() if _es_eliminatoria(p) else Reglas.primera_ronda()
                _qr    = predictor.top_dos_pronosticos(p["local"], p["visitante"], _reglas_q)
                _pred_q = _qr["prediccion"]
                _o1q   = _qr["opcion_1"]
                _p_emp = _pred_q.prob_empate

                with c2:
                    _m1 = _o1q["marcador"]
                    st.markdown(
                        f"<div class='pred-1' style='color:#4a5a6b'>{_m1[0]} – {_m1[1]}</div>"
                        f"<div class='meta'>📊 Base FIFA · {_o1q['prob']*100:.1f}% · "
                        f"<span class='chip chip-pts'>{_o1q['pts_esperados']:.1f} pts esp.</span></div>",
                        unsafe_allow_html=True,
                    )
                with c3:
                    _alerta = (
                        "<div style='color:#b8860b;font-weight:700;font-size:.8rem;"
                        "margin-top:4px'>⚠️ Riesgo empate alto</div>"
                        if _p_emp > 0.27 else ""
                    )
                    st.markdown(
                        f"<div class='meta'>"
                        f"<span class='chip chip-azul'>1: {_pred_q.prob_victoria_local*100:.0f}%</span> "
                        f"<span class='chip chip-azul'>X: {_p_emp*100:.0f}%</span> "
                        f"<span class='chip chip-azul'>2: {_pred_q.prob_victoria_visit*100:.0f}%</span>"
                        f"</div>{_alerta}",
                        unsafe_allow_html=True,
                    )
                    if st.button("🧮 Calcular IA", key=f"btn_{p['id']}"):
                        with st.spinner("Analizando..."):
                            calcular_partido(p)
                        st.rerun()
            else:
                r = st.session_state[f"pred_{p['id']}"]
                o1, o2 = r["opcion_1"], r["opcion_2"]
                pred = r["prediccion"]
                with c2:
                    st.markdown(
                        f"<div class='pred-1'>{o1['marcador'][0]} – {o1['marcador'][1]}</div>"
                        f"<div class='meta'>📊 Más probable · {o1['prob']*100:.1f}% · "
                        f"<span class='chip chip-pts'>{o1['pts_esperados']:.1f} pts esp.</span></div>",
                        unsafe_allow_html=True,
                    )
                with c3:
                    st.markdown(
                        f"<div class='pred-2'>{o2['marcador'][0]} – {o2['marcador'][1]}</div>"
                        f"<div class='meta'>🎯 Óptimo puntos · {o2['prob']*100:.1f}% · "
                        f"<span class='chip chip-pts'>{o2['pts_esperados']:.1f} pts esp.</span></div>"
                        f"<div class='meta'>"
                        f"<span class='chip chip-azul'>1: {pred.prob_victoria_local*100:.0f}%</span> "
                        f"<span class='chip chip-azul'>X: {pred.prob_empate*100:.0f}%</span> "
                        f"<span class='chip chip-azul'>2: {pred.prob_victoria_visit*100:.0f}%</span>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )

            # ── Columna 4: marcador real + puntos ─────────
            with c4:
                real = guardado.get("real")
                if real:
                    # RESULTADO BLOQUEADO — no se puede editar
                    rl, rv = real
                    etiqueta = "🔒 Oficial" if guardado.get("manual") else "🔒 Marcador real"
                    st.markdown(
                        f"<div class='real-ok'>{rl} – {rv}</div>"
                        f"<div class='meta'>{etiqueta}</div>",
                        unsafe_allow_html=True,
                    )
                    if _es_eliminatoria(p) and rl == rv and not guardado.get("penaltis"):
                        st.markdown(
                            "<div class='meta' style='color:#b8860b;font-weight:600'>"
                            "🥅 Empate — ¿quién avanzó por penales?</div>",
                            unsafe_allow_html=True,
                        )
                        _cp1, _cp2 = st.columns(2)
                        if _cp1.button(f"{p['local'][:10]}", key=f"pen_l_{p['id']}"):
                            almacen.set_penal(p["id"], "local")
                            st.cache_data.clear()
                            st.rerun()
                        if _cp2.button(f"{p['visitante'][:10]}", key=f"pen_v_{p['id']}"):
                            almacen.set_penal(p["id"], "visitante")
                            st.cache_data.clear()
                            st.rerun()
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
                    # Determinar si el partido ya debería haberse jugado
                    try:
                        _fecha_p = dt.date.fromisoformat(p.get("fecha", "9999-12-31"))
                    except Exception:
                        _fecha_p = dt.date(9999, 12, 31)
                    _hoy = dt.date.today()

                    if _fecha_p <= _hoy:
                        # Partido pasado — permitir ingreso manual
                        st.markdown(
                            "<div class='meta' style='color:#b8860b;font-weight:600'>"
                            "📝 Ingresar resultado:</div>",
                            unsafe_allow_html=True,
                        )
                        with st.form(f"form_real_{p['id']}", clear_on_submit=True):
                            _cc1, _cc2 = st.columns(2)
                            _gl_m = _cc1.number_input(
                                p["local"][:9], min_value=0, max_value=20,
                                value=0, step=1, key=f"gl_{p['id']}"
                            )
                            _gv_m = _cc2.number_input(
                                p["visitante"][:9], min_value=0, max_value=20,
                                value=0, step=1, key=f"gv_{p['id']}"
                            )
                            if st.form_submit_button("Guardar"):
                                almacen.set_resultado_manual(p["id"], int(_gl_m), int(_gv_m))
                                # Invalidar Bayes para recalcular con nuevo resultado
                                if "fuerzas_bayes" in st.session_state:
                                    del st.session_state["fuerzas_bayes"]
                                st.cache_data.clear()
                                st.rerun()
                        # También ofrecer búsqueda automática
                        if st.button("🔍 Buscar auto", key=f"res_{p['id']}"):
                            with st.spinner("Buscando..."):
                                r = obtener_resultado_real(
                                    p["local"], p["visitante"], p.get("fecha", ""),
                                    KEYS["apifootball"], KEYS["footballdata"],
                                    KEYS["tavily"], KEYS["serper"],
                                )
                            if r:
                                almacen.set_prediccion(p["id"], {"real": list(r)})
                                if "fuerzas_bayes" in st.session_state:
                                    del st.session_state["fuerzas_bayes"]
                                st.cache_data.clear()
                                st.rerun()
                            else:
                                st.toast("Sin resultado confiable aún.")
                    else:
                        # Partido futuro
                        st.markdown("<div class='real-pend'>⏳ pendiente</div>",
                                    unsafe_allow_html=True)

        st.markdown("<hr style='border:0;border-top:1px solid #e2e8f0;margin:4px 0'>",
                    unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Chatbot human-in-the-loop
# ---------------------------------------------------------------------------
st.markdown("---")
st.markdown("## 💬 Mesa de análisis")
st.markdown(
    "<span class='meta'>Pregunta sobre cualquier partido, aporta contexto (lesiones, "
    "clima, noticias) o pide que recalcule con nueva información.</span>",
    unsafe_allow_html=True,
)

if "chat" not in st.session_state:
    st.session_state.chat = []

for msg in st.session_state.chat:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if entrada := st.chat_input("Escribe aquí... ej: '¿Quién gana Brasil vs Marruecos?'"):
    st.session_state.chat.append({"role": "user", "content": entrada})
    with st.chat_message("user"):
        st.markdown(entrada)

    with st.chat_message("assistant"):
        with st.spinner("Analizando..."):
            ctx = buscar_contexto_tavily(entrada, KEYS["tavily"], max_resultados=4)
            respuesta = responder_chat(entrada, ctx, KEYS["deepseek"])
        st.markdown(respuesta)
    st.session_state.chat.append({"role": "assistant", "content": respuesta})
