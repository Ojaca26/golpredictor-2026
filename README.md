# ⚽ Golpredictor 2026

Sala de análisis predictivo para el Mundial 2026. Genera pronósticos de marcadores
optimizados para **maximizar puntos** según las reglas de Golpredictor, muestra dos
opciones con su probabilidad, autollena el marcador real desde APIs deportivas, y
compara predicho vs real partido a partido. Incluye un chatbot para análisis y
contexto (human in the loop).

## Lo que hace y lo que NO hace

Este sistema **no adivina marcadores exactos con certeza** — eso es imposible en
fútbol. Lo que hace es modelar los goles con distribuciones de **Poisson**, calibrar
la fuerza de cada equipo con datos reales + contexto web razonado por IA, y elegir el
pronóstico que da **mayor valor esperado de puntos** (acertar el ganador pesa más que
el marcador exacto, según las reglas).

## Arquitectura

```
app.py                  → interfaz Streamlit (dashboard + chatbot)
core/
  predictor.py          → modelo de Poisson + optimizador de puntos esperados
  inteligencia.py       → Tavily (contexto) + Gemini (razona fuerzas y chat)
  deportes_api.py       → API-Football (principal) + football-data.org (respaldo)
  resultados.py         → cadena de fuentes para el marcador real (nunca inventa)
  fixture.py            → calendario del Mundial (API o semilla local)
  analisis.py           → comparación predicho vs real y desglose de puntos
  almacen.py            → persistencia en JSON
```

**Fuentes de datos (en orden de fiabilidad):**
1. **API-Football** (api-sports.io) — gratis, 100 req/día. Fixtures y resultados.
2. **football-data.org** — gratis. Respaldo de resultados.
3. **Tavily / Serper** — búsqueda web. Contexto y último recurso para resultados.
4. **Gemini** — motor de razonamiento (fuerzas de equipo y chatbot).

## Configuración

1. Registra tokens **gratis**: api-football.com, football-data.org, tavily.com,
   serper.dev, y Google AI Studio (Gemini).
2. Copia `.env.example` → `.env` y rellena las claves (NO subas `.env` a GitHub).

## Ejecutar en local

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy en Streamlit Community Cloud (gratis, recomendado)

1. Sube este repo a GitHub.
2. En share.streamlit.io conecta el repo y elige `app.py`.
3. En **Settings → Secrets** pega tus claves (formato en
   `.streamlit/secrets.toml.example`). Quedan encriptadas, nunca en el código.
4. Cada `git push` actualiza la app automáticamente.

## Seguridad de las claves

Las API keys van **solo** en `.env` (local) o en **Secrets** (Streamlit Cloud).
Nunca en el código ni en el repo. `.gitignore` ya excluye `.env` y `secrets.toml`.
