"""
GOLPREDICTOR 2026 - Sala de analisis predictivo del Mundial.

Dashboard que:
  - Lista todos los partidos ordenados por fecha (scroll).
  - Muestra para cada uno: Prediccion 1 (optima por valor esperado) + %,
    Prediccion 2 (alternativa) + %, probabilidades 1X2, marcador real y analisis IA.
  - Mapa de calor de probabilidades por marcador (Dixon-Coles).
  - Simulacion Monte Carlo del torneo completo.
  - Chatbot al pie para preguntar / dar contexto (human in the loop).

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
from core import almacen
from core.montecarlo import simular_torneo


# ---------------------------------------------------------------------------
# Configuracion y secretos
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
    "gemini":       secreto("GEMINI_API_KEY"),
}


# ---------------------------------------------------------------------------
# Estilo visual
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
.equipos { font-family:'Barlow Condensed',sans-serif; font-size:1.35rem; font-weight:600; color:#eef2f6; }
.meta { color:#7d8a99; font-size:.8rem; font-family:'Inter',sans-serif; }
.pred-1 { color:#3ddc84; font-weight:700; font-size:1.5rem; font-family:'Barlow Condensed',sans-serif; }
.pred-2 { color:#9aa7b4; font-weight:600; font-size:1.15rem; font-family:'Barlow Condensed',sans-serif; }
.real-pend { color:#5a6776; font-style:italic; }
.real-ok { color:#ffd25a; font-weight:700; font-size:1.5rem; font-family:'Barlow Condensed',sans-serif; }
.chip { display:inline-block; padding:2px 9px; border-radius:20px; font-size:.72rem;
        font-family:'Inter',sans-serif; font-weight:600; }
.chip-pts  { background:#13361f; color:#3ddc84; border:1px solid #1d5230; }
.chip-azul { background:#0e2040; color:#6ab4ff; border:1px solid #1a3560; }
.barra-wrap { background:#1e2a38; border-radius:4px; height:6px; width:100%; }
.barra-fill { background:#3ddc84; border-radius:4px; height:6px; }
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
st.markdown("# Golpredictor 2026")
st.markdown(
    "<span class='meta'>Motor predictivo Poisson + Dixon-Coles + IA · optimizado para maximizar "
    "puntos segun las reglas del juego. Las probabilidades son estimaciones, "
    "no certezas.</span>", unsafe_allow_html=True,
)

_keys_ok = [k for k, v in KEYS.items() if v]
_keys_ko = [k for k, v in KEYS.items() if not v]
col_s1, col_s2 = st.columns(2)
with col_s1:
    if _keys_ok:
        st.success("APIs activas: " + ", ".join(_keys_ok))
with col_s2:
    if _keys_ko:
        st.warning("Sin configurar: " + ", ".join(_keys_ko))

with st.expander("Como funciona?"):
    st.markdown("""
**Base**: ranking FIFA 2026 -> fuerzas de ataque/defensa por equipo.
**Modelo**: Poisson bivariado con correccion Dixon-Coles (corrige marcadores bajos).
**Ajuste IA**: Tavily busca noticias/lesiones, Gemini calibra con ese contexto (+-20% max).
**Optimizacion**: elige el marcador que maximiza puntos esperados segun las reglas de Golpredictor.
**Mapa de calor**: tabla de probabilidades para cada marcador posible (0-5 por lado).
**Monte Carlo**: simula el torneo completo miles de veces para calcular probabilidades de clasificacion.
""")

col_a, col_b, col_c = st.columns([1, 1, 2])
with col_a:
    usar_api = st.toggle("Fixture desde API-Football", value=bool(KEYS["apifootball"]))
with col_b:
    if st.button("Recalcular todo"):
        st.cache_data.clear()
        for k in list(st.session_state.keys()):
            if k.startswith("pred_") or k.startswith("anal_") or k == "mc_result":
                del st.session_state[k]
        st.rerun()

try:
    partidos = _fixture_cacheado(usar_api)
except Exception as e:
    st.error("Error cargando fixture: " + str(e))
    st.stop()

predictor = PoissonPredictor()


# ---------------------------------------------------------------------------
# Calculo perezoso de prediccion + analisis (cacheado en sesion)
# ---------------------------------------------------------------------------
def calcular_partido(p: dict) -> dict:
    """Calcula prediccion + analisis y lo guarda en session_state."""
    clave = "pred_" + str(p["id"])
    if clave in st.session_state:
        return st.session_state[clave]

    anal = analizar_partido_completo(
        p["local"], p["visitante"], KEYS["tavily"], KEYS["gemini"]
    )
    fuerzas = anal["fuerzas"]
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
# Helpers de UI
# ---------------------------------------------------------------------------
por_fecha = defaultdict(list)
for p in partidos:
    por_fecha[p.get("fecha", "Sin fecha")].append(p)

MESES = ["", "ene", "feb", "mar", "abr", "may", "jun",
         "jul", "ago", "sep", "oct", "nov", "dic"]


def fecha_bonita(iso: str) -> str:
    try:
        d = dt.date.fromisoformat(iso)
        return str(d.day) + " " + MESES[d.month] + " " + str(d.year)
    except Exception:
        return iso


def _barra(val: float, max_val: float = 2.2, color: str = "#3ddc84") -> str:
    pct = min(100, int(val / max_val * 100))
    return ("<div class='barra-wrap'>"
            "<div class='barra-fill' style='width:" + str(pct) + "%;background:" + color + "'></div>"
            "</div>")


def _heatmap_html(M, local: str, visitante: str, max_g: int = 5) -> str:
    """Genera tabla HTML de calor con % de probabilidad por marcador."""
    max_prob = max(M[i][j] for i in range(max_g + 1) for j in range(max_g + 1))
    rows = ["<table style='border-collapse:separate;border-spacing:2px;font-size:.72rem'>"]
    rows.append("<tr>")
    rows.append("<td style='color:#5a6776;padding:3px 6px;font-size:.65rem'>L \\ V</td>")
    for j in range(max_g + 1):
        rows.append(
            "<td style='color:#6ab4ff;text-align:center;padding:3px 8px;font-weight:700'>"
            + str(j) + "</td>"
        )
    rows.append("</tr>")
    for i in range(max_g + 1):
        rows.append("<tr>")
        rows.append(
            "<td style='color:#3ddc84;padding:3px 6px;font-weight:700'>" + str(i) + "</td>"
        )
        for j in range(max_g + 1):
            prob = M[i][j]
            pct = prob * 100
            intens = (prob / max_prob) if max_prob > 0 else 0
            r_c = int(15 + intens * (61 - 15))
            g_c = int(42 + intens * (220 - 42))
            b_c = int(25 + intens * (132 - 25))
            bg = "rgb(" + str(r_c) + "," + str(g_c) + "," + str(b_c) + ")"
            txt = "#eef2f6" if intens > 0.45 else "#7d8a99"
            border = "1px solid #3ddc84" if i == j else "1px solid #1e2a38"
            rows.append(
                "<td style='background:" + bg + ";color:" + txt + ";text-align:center;"
                "padding:4px 7px;border-radius:4px;border:" + border + "'>"
                + str(round(pct, 1)) + "%</td>"
            )
        rows.append("</tr>")
    rows.append("</table>")
    rows.append(
        "<div style='color:#5a6776;font-size:.65rem;margin-top:3px'>"
        "Filas = goles " + local + " &nbsp;|&nbsp; Columnas = goles " + visitante +
        " &nbsp;|&nbsp; Diagonal resaltada = empate</div>"
    )
    return "\n".join(rows)


# ---------------------------------------------------------------------------
# Seccion Monte Carlo
# ---------------------------------------------------------------------------
st.markdown("---")
with st.expander("Simulacion Monte Carlo del torneo", expanded=False):
    st.markdown(
        "<span class='meta'>Simula el torneo completo miles de veces con el modelo "
        "Poisson + Dixon-Coles. Calcula la probabilidad de que cada equipo clasifique "
        "de grupos, llegue a semis, a la final y salga campeon.</span>",
        unsafe_allow_html=True,
    )
    col_mc1, col_mc2 = st.columns([1, 3])
    with col_mc1:
        n_sims = st.select_slider(
            "Simulaciones", options=[1000, 2000, 5000, 10000], value=5000
        )
    with col_mc2:
        run_mc = st.button("Correr simulacion", key="btn_mc")

    if run_mc or "mc_result" in st.session_state:
        if run_mc:
            with st.spinner("Simulando " + str(n_sims) + " torneos..."):
                st.session_state["mc_result"] = simular_torneo(partidos, n_sims)
                st.session_state["mc_n"] = n_sims

        mc = st.session_state.get("mc_result", {})
        mc_n = st.session_state.get("mc_n", n_sims)

        if mc:
            st.markdown(
                "<span class='meta'>" + str(mc_n) + " simulaciones completadas.</span>",
                unsafe_allow_html=True,
            )

            equipos_ord = sorted(
                mc.items(),
                key=lambda x: x[1].get("campeon", 0),
                reverse=True,
            )

            etapas = [
                ("clasifica", "Clasifica"),
                ("octavos",   "Octavos"),
                ("cuartos",   "Cuartos"),
                ("semis",     "Semifinal"),
                ("final",     "Final"),
                ("campeon",   "Campeon"),
            ]

            header_cols = st.columns([2] + [1] * len(etapas))
            header_cols[0].markdown(
                "<span style='color:#7d8a99;font-size:.75rem'>EQUIPO</span>",
                unsafe_allow_html=True)
            for idx, (_, label) in enumerate(etapas):
                header_cols[idx + 1].markdown(
                    "<span style='color:#7d8a99;font-size:.75rem'>" + label + "</span>",
                    unsafe_allow_html=True,
                )

            for equipo, datos in equipos_ord[:20]:
                row_cols = st.columns([2] + [1] * len(etapas))
                row_cols[0].markdown(
                    "<span style='color:#eef2f6;font-size:.85rem'>" + equipo + "</span>",
                    unsafe_allow_html=True,
                )
                for idx, (clave, _) in enumerate(etapas):
                    val = datos.get(clave, 0)
                    if val > 0:
                        color = "#3ddc84" if val > 0.3 else ("#ffd25a" if val > 0.1 else "#9aa7b4")
                        row_cols[idx + 1].markdown(
                            "<span style='color:" + color + ";font-size:.85rem'>"
                            + str(round(val * 100)) + "%</span>",
                            unsafe_allow_html=True,
                        )
                    else:
                        row_cols[idx + 1].markdown(
                            "<span style='color:#2a3340;font-size:.85rem'>-</span>",
                            unsafe_allow_html=True,
                        )

            st.markdown(
                "<div style='margin-top:16px;color:#3ddc84;font-size:.9rem;"
                "font-weight:600;letter-spacing:.5px'>FAVORITOS AL TITULO</div>",
                unsafe_allow_html=True,
            )
            podio = [(e, d.get("campeon", 0)) for e, d in equipos_ord[:5]]
            p_cols = st.columns(5)
            medallas = ["1ro", "2do", "3ro", "4to", "5to"]
            for idx, (equipo, prob) in enumerate(podio):
                p_cols[idx].markdown(
                    "<div style='text-align:center;background:#0e1c2a;border-radius:8px;"
                    "padding:10px 4px;border:1px solid #1e2a38'>"
                    "<div style='color:#7d8a99;font-size:.75rem'>" + medallas[idx] + "</div>"
                    "<div style='color:#eef2f6;font-size:.85rem;font-weight:600'>" + equipo + "</div>"
                    "<div style='color:#3ddc84;font-size:1.1rem;font-weight:700'>"
                    + str(round(prob * 100, 1)) + "%</div>"
                    "</div>",
                    unsafe_allow_html=True,
                )
        else:
            st.info("No hay grupos con fixture definido para simular.")

st.markdown("---")
st.markdown(
    "<span class='meta'>Mostrando " + str(len(partidos)) + " partidos</span>",
    unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Lista de partidos por fecha
# ---------------------------------------------------------------------------
for fecha in sorted(por_fecha.keys()):
    st.markdown("<div class='bloque-fecha'>" + fecha_bonita(fecha) + "</div>",
                unsafe_allow_html=True)

    for p in por_fecha[fecha]:
        guardado = almacen.get_prediccion(p["id"])
        ya = ("pred_" + str(p["id"])) in st.session_state

        with st.container():
            c1, c2, c3, c4 = st.columns([3, 2, 2, 2])

            with c1:
                grupo = " · Grupo " + p["grupo"] if p.get("grupo") else ""
                sede  = " · " + p["sede"]        if p.get("sede")  else ""
                fase  = "Eliminatoria" if _es_eliminatoria(p) else "Grupos"
                st.markdown(
                    "<div class='equipos'>" + p["local"] +
                    " <span style='color:#5a6776'>vs</span> " + p["visitante"] + "</div>"
                    "<div class='meta'>" + fase + grupo + sede + "</div>",
                    unsafe_allow_html=True,
                )

                fl = get_fuerza(p["local"])
                fv = get_fuerza(p["visitante"])
                with st.expander("Analisis de la IA", expanded=False):
                    if ya:
                        r = st.session_state["pred_" + str(p["id"])]
                        fl = r.get("fuerza_local", fl)
                        fv = r.get("fuerza_visitante", fv)
                        if r.get("nota_ia"):
                            st.markdown(r["nota_ia"])
                        st.markdown(r.get("razonamiento", ""))
                    else:
                        st.markdown(razonamiento_fuerza(p["local"], p["visitante"]))

                    col_fl, col_fv = st.columns(2)
                    with col_fl:
                        st.markdown("**" + p["local"] + "**")
                        st.markdown(
                            "<span class='meta'>Ataque: " + str(round(fl.ataque, 2)) + "</span>",
                            unsafe_allow_html=True)
                        st.markdown(_barra(fl.ataque), unsafe_allow_html=True)
                        st.markdown(
                            "<span class='meta'>Defensa: " + str(round(fl.defensa, 2)) +
                            " (" + ("debil" if fl.defensa > 1.1 else "solida") + ")</span>",
                            unsafe_allow_html=True)
                        st.markdown(_barra(fl.defensa, color="#e05a5a"), unsafe_allow_html=True)
                    with col_fv:
                        st.markdown("**" + p["visitante"] + "**")
                        st.markdown(
                            "<span class='meta'>Ataque: " + str(round(fv.ataque, 2)) + "</span>",
                            unsafe_allow_html=True)
                        st.markdown(_barra(fv.ataque), unsafe_allow_html=True)
                        st.markdown(
                            "<span class='meta'>Defensa: " + str(round(fv.defensa, 2)) +
                            " (" + ("debil" if fv.defensa > 1.1 else "solida") + ")</span>",
                            unsafe_allow_html=True)
                        st.markdown(_barra(fv.defensa, color="#e05a5a"), unsafe_allow_html=True)

                    # Mapa de calor (solo si hay prediccion calculada)
                    if ya:
                        r_hm = st.session_state["pred_" + str(p["id"])]
                        fl_hm = r_hm.get("fuerza_local", fl)
                        fv_hm = r_hm.get("fuerza_visitante", fv)
                        predictor.fuerzas = {p["local"]: fl_hm, p["visitante"]: fv_hm}
                        lam_l_hm, lam_v_hm = predictor._lambdas(p["local"], p["visitante"])
                        M_hm = predictor.matriz_probabilidades(lam_l_hm, lam_v_hm)
                        st.markdown(
                            "<div style='margin-top:12px;color:#9aa7b4;font-size:.8rem;"
                            "font-weight:600;letter-spacing:.5px'>MAPA DE PROBABILIDADES</div>",
                            unsafe_allow_html=True,
                        )
                        st.markdown(_heatmap_html(M_hm, p["local"], p["visitante"]),
                                    unsafe_allow_html=True)

            if not ya:
                with c2:
                    if st.button("Calcular", key="btn_" + str(p["id"])):
                        with st.spinner("Analizando..."):
                            calcular_partido(p)
                        st.rerun()
                with c3:
                    st.markdown(
                        "<span class='meta'>Haz clic en Calcular<br>para ver la prediccion de la IA</span>",
                        unsafe_allow_html=True)
            else:
                r = st.session_state["pred_" + str(p["id"])]
                o1, o2 = r["opcion_1"], r["opcion_2"]
                pred = r["prediccion"]
                with c2:
                    st.markdown(
                        "<div class='pred-1'>" + str(o1["marcador"][0]) +
                        " - " + str(o1["marcador"][1]) + "</div>"
                        "<div class='meta'>Prediccion 1 · " + str(round(o1["prob"] * 100)) + "% · "
                        "<span class='chip chip-pts'>" + str(o1["pts_esperados"]) + " pts esp.</span></div>",
                        unsafe_allow_html=True,
                    )
                with c3:
                    st.markdown(
                        "<div class='pred-2'>" + str(o2["marcador"][0]) +
                        " - " + str(o2["marcador"][1]) + "</div>"
                        "<div class='meta'>Prediccion 2 · " + str(round(o2["prob"] * 100)) + "%</div>"
                        "<div class='meta'>"
                        "<span class='chip chip-azul'>1: " + str(round(pred.prob_victoria_local * 100)) + "%</span> "
                        "<span class='chip chip-azul'>X: " + str(round(pred.prob_empate * 100)) + "%</span> "
                        "<span class='chip chip-azul'>2: " + str(round(pred.prob_victoria_visit * 100)) + "%</span>"
                        "</div>",
                        unsafe_allow_html=True,
                    )

            with c4:
                real = guardado.get("real")
                if real:
                    rl, rv = real
                    st.markdown(
                        "<div class='real-ok'>" + str(rl) + " - " + str(rv) + "</div>"
                        "<div class='meta'>Marcador real</div>",
                        unsafe_allow_html=True,
                    )
                    if ya:
                        an = analizar_resultado(
                            st.session_state["pred_" + str(p["id"])]["opcion_1"]["marcador"],
                            (rl, rv), _es_eliminatoria(p),
                        )
                        st.markdown(
                            "<div class='meta'>" + an["veredicto"] + "<br>"
                            "<span class='chip chip-pts'>" + str(an["puntos"]) +
                            "/" + str(an["max_posible"]) + " pts</span></div>",
                            unsafe_allow_html=True,
                        )
                else:
                    st.markdown("<div class='real-pend'>pendiente</div>",
                                unsafe_allow_html=True)
                    if st.button("Buscar resultado", key="res_" + str(p["id"])):
                        with st.spinner("Buscando..."):
                            r_res = obtener_resultado_real(
                                p["local"], p["visitante"], p.get("fecha", ""),
                                KEYS["apifootball"], KEYS["footballdata"],
                                KEYS["tavily"], KEYS["serper"],
                            )
                        if r_res:
                            almacen.set_prediccion(p["id"], {"real": list(r_res)})
                            st.rerun()
                        else:
                            st.toast("Aun no hay resultado confiable. Sigue pendiente.")

        st.markdown("<hr style='border:0;border-top:1px solid #1e2a38;margin:4px 0'>",
                    unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Chatbot human-in-the-loop
# ---------------------------------------------------------------------------
st.markdown("---")
st.markdown("## Mesa de analisis")
st.markdown(
    "<span class='meta'>Pregunta sobre cualquier partido, aporta contexto (lesiones, "
    "clima, noticias) o pide que recalcule con nueva informacion.</span>",
    unsafe_allow_html=True,
)

if "chat" not in st.session_state:
    st.session_state.chat = []

for msg in st.session_state.chat:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if entrada := st.chat_input("Escribe aqui... ej: Quien gana Brasil vs Marruecos?"):
    st.session_state.chat.append({"role": "user", "content": entrada})
    with st.chat_message("user"):
        st.markdown(entrada)

    with st.chat_message("assistant"):
        with st.spinner("Analizando..."):
            ctx = buscar_contexto_tavily(entrada, KEYS["tavily"], max_resultados=4)
            respuesta = responder_chat(entrada, ctx, KEYS["gemini"])
        st.markdown(respuesta)
    st.session_state.chat.append({"role": "assistant", "content": respuesta})
