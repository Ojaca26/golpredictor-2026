"""
Base de datos de fuerzas por equipo para el Mundial 2026.

Valores calibrados con:
  - Ranking FIFA (junio 2026)
  - Historial en Copas del Mundo (goles por partido en últimas 3 ediciones)
  - Rendimiento en clasificatorias al Mundial 2026

Escala Poisson (referencia: promedio WC ~1.25 goles/equipo por partido):
  ataque  > 1.0 → marca más goles que el promedio mundial
  ataque  < 1.0 → marca menos goles
  defensa > 1.0 → encaja más (peor defensa)
  defensa < 1.0 → encaja menos (mejor defensa)
"""

from __future__ import annotations
from core.predictor import FuerzaEquipo

# ---------------------------------------------------------------------------
# Base de fuerzas — nombres en español (como aparecen en la app)
# ---------------------------------------------------------------------------
EQUIPOS: dict[str, FuerzaEquipo] = {

    # ── CONMEBOL ──────────────────────────────────────────────────────
    "Brasil":           FuerzaEquipo(ataque=1.95, defensa=0.78),
    "Argentina":        FuerzaEquipo(ataque=1.92, defensa=0.80),
    "Colombia":         FuerzaEquipo(ataque=1.55, defensa=0.98),
    "Uruguay":          FuerzaEquipo(ataque=1.52, defensa=0.90),  # Actualizado: 2-0 vs Arabia J1 (portería a cero)
    "Ecuador":          FuerzaEquipo(ataque=1.25, defensa=1.10),
    "Paraguay":         FuerzaEquipo(ataque=1.10, defensa=1.22),
    "Venezuela":        FuerzaEquipo(ataque=1.05, defensa=1.25),
    "Bolivia":          FuerzaEquipo(ataque=0.85, defensa=1.42),
    "Chile":            FuerzaEquipo(ataque=1.20, defensa=1.15),
    "Perú":             FuerzaEquipo(ataque=1.10, defensa=1.20),
    "Peru":             FuerzaEquipo(ataque=1.10, defensa=1.20),

    # ── UEFA ───────────────────────────────────────────────────────────────
    "Francia":          FuerzaEquipo(ataque=2.00, defensa=0.75),
    "España":           FuerzaEquipo(ataque=1.95, defensa=0.75),  # Actualizado: 4-0 vs Cabo Verde J1
    "Inglaterra":       FuerzaEquipo(ataque=1.82, defensa=0.82),
    "Alemania":         FuerzaEquipo(ataque=1.85, defensa=0.85),
    "Portugal":         FuerzaEquipo(ataque=1.80, defensa=0.88),
    "Países Bajos":     FuerzaEquipo(ataque=1.72, defensa=0.88),
    "Holanda":          FuerzaEquipo(ataque=1.72, defensa=0.88),
    "Bélgica":          FuerzaEquipo(ataque=1.68, defensa=0.92),  # Actualizado: 3-1 vs Egipto J1
    "Croacia":          FuerzaEquipo(ataque=1.50, defensa=0.95),
    "Dinamarca":        FuerzaEquipo(ataque=1.45, defensa=0.90),
    "Suiza":            FuerzaEquipo(ataque=1.42, defensa=0.92),
    "Austria":          FuerzaEquipo(ataque=1.38, defensa=1.00),
    "Escocia":          FuerzaEquipo(ataque=1.30, defensa=1.05),
    "Turquía":          FuerzaEquipo(ataque=1.25, defensa=1.10),
    "Polonia":          FuerzaEquipo(ataque=1.22, defensa=1.12),
    "Serbia":           FuerzaEquipo(ataque=1.20, defensa=1.10),
    "Hungría":          FuerzaEquipo(ataque=1.18, defensa=1.12),
    "Rumania":          FuerzaEquipo(ataque=1.15, defensa=1.15),
    "República Checa":  FuerzaEquipo(ataque=1.18, defensa=1.10),
    "Bosnia y Herzegovina": FuerzaEquipo(ataque=1.05, defensa=1.22),
    "Eslovenia":        FuerzaEquipo(ataque=1.10, defensa=1.15),
    "Albania":          FuerzaEquipo(ataque=1.05, defensa=1.20),
    "Georgia":          FuerzaEquipo(ataque=1.00, defensa=1.20),
    "Ucrania":          FuerzaEquipo(ataque=1.25, defensa=1.08),
    "Grecia":           FuerzaEquipo(ataque=1.10, defensa=1.15),
    "Gales":            FuerzaEquipo(ataque=1.15, defensa=1.10),
    "Irlanda":          FuerzaEquipo(ataque=1.05, defensa=1.20),
    "Noruega":          FuerzaEquipo(ataque=1.35, defensa=1.00),
    "Suecia":           FuerzaEquipo(ataque=1.38, defensa=0.98),

    # ── CONCACAF ──────────────────────────────────────────────────────────
    "México":           FuerzaEquipo(ataque=1.52, defensa=1.05),
    "Estados Unidos":   FuerzaEquipo(ataque=1.45, defensa=1.05),
    "Canadá":           FuerzaEquipo(ataque=1.38, defensa=1.08),
    "Panamá":           FuerzaEquipo(ataque=1.10, defensa=1.18),
    "Costa Rica":       FuerzaEquipo(ataque=1.05, defensa=1.20),
    "Honduras":         FuerzaEquipo(ataque=0.98, defensa=1.28),
    "Jamaica":          FuerzaEquipo(ataque=0.95, defensa=1.30),
    "Haití":            FuerzaEquipo(ataque=0.82, defensa=1.45),
    "El Salvador":      FuerzaEquipo(ataque=0.88, defensa=1.38),
    "Guatemala":        FuerzaEquipo(ataque=0.85, defensa=1.42),
    "Curazao":          FuerzaEquipo(ataque=0.65, defensa=1.65),
    "Trinidad y Tobago": FuerzaEquipo(ataque=0.85, defensa=1.40),

    # ── AFC ────────────────────────────────────────────────────────────────
    "Japón":            FuerzaEquipo(ataque=1.50, defensa=0.95),
    "Corea del Sur":    FuerzaEquipo(ataque=1.38, defensa=1.00),
    "Arabia Saudita":   FuerzaEquipo(ataque=0.95, defensa=1.22),  # Actualizado: 0-2 vs Uruguay J1 (sin gol)
    "Irán":             FuerzaEquipo(ataque=1.10, defensa=1.08),  # Actualizado: 1-0 vs NZ J1 (portería a cero)
    "Australia":        FuerzaEquipo(ataque=1.20, defensa=1.10),
    "Catar":            FuerzaEquipo(ataque=0.88, defensa=1.42),
    "Qatar":            FuerzaEquipo(ataque=0.88, defensa=1.42),
    "Irak":             FuerzaEquipo(ataque=0.95, defensa=1.30),
    "Uzbekistán":       FuerzaEquipo(ataque=0.90, defensa=1.32),
    "Jordania":         FuerzaEquipo(ataque=0.88, defensa=1.35),
    "Indonesia":        FuerzaEquipo(ataque=0.78, defensa=1.50),
    "China":            FuerzaEquipo(ataque=0.80, defensa=1.45),
    "Tailandia":        FuerzaEquipo(ataque=0.75, defensa=1.52),

    # ── CAF ────────────────────────────────────────────────────────────────
    "Marruecos":        FuerzaEquipo(ataque=1.42, defensa=0.92),
    "Senegal":          FuerzaEquipo(ataque=1.35, defensa=1.00),
    "Egipto":           FuerzaEquipo(ataque=1.28, defensa=1.05),
    "Nigeria":          FuerzaEquipo(ataque=1.25, defensa=1.10),
    "Costa de Marfil":  FuerzaEquipo(ataque=1.42, defensa=1.00),
    "Ghana":            FuerzaEquipo(ataque=1.18, defensa=1.15),
    "Camerún":          FuerzaEquipo(ataque=1.15, defensa=1.18),
    "Argelia":          FuerzaEquipo(ataque=1.20, defensa=1.12),
    "Túnez":            FuerzaEquipo(ataque=1.10, defensa=1.15),
    "Sudáfrica":        FuerzaEquipo(ataque=0.95, defensa=1.25),
    "Mali":             FuerzaEquipo(ataque=1.05, defensa=1.20),
    "Burkina Faso":     FuerzaEquipo(ataque=1.00, defensa=1.25),

    # ── OFC / OTROS ──────────────────────────────────────────────────────────
    "Nueva Zelanda":    FuerzaEquipo(ataque=0.95, defensa=1.30),
    "Tahítí":           FuerzaEquipo(ataque=0.60, defensa=1.75),
    "Cabo Verde":       FuerzaEquipo(ataque=0.85, defensa=1.40),  # Debutante. 0-4 vs España J1
}

# ---------------------------------------------------------------------------
# Mapeo inglés (API-Football) → español (nuestra app)
# ---------------------------------------------------------------------------
EN_A_ES: dict[str, str] = {
    "Mexico": "México",
    "South Africa": "Sudáfrica",
    "South Korea": "Corea del Sur",
    "Korea Republic": "Corea del Sur",
    "Czech Republic": "República Checa",
    "Czechia": "República Checa",
    "Canada": "Canadá",
    "Bosnia and Herzegovina": "Bosnia y Herzegovina",
    "Bosnia & Herzegovina": "Bosnia y Herzegovina",
    "Qatar": "Catar",
    "Switzerland": "Suiza",
    "Brazil": "Brasil",
    "Morocco": "Marruecos",
    "Haiti": "Haití",
    "Scotland": "Escocia",
    "Australia": "Australia",
    "Turkey": "Turquía",
    "Germany": "Alemania",
    "Curacao": "Curazao",
    "United States": "Estados Unidos",
    "USA": "Estados Unidos",
    "US": "Estados Unidos",
    "Paraguay": "Paraguay",
    "France": "Francia",
    "Spain": "España",
    "England": "Inglaterra",
    "Portugal": "Portugal",
    "Netherlands": "Países Bajos",
    "Belgium": "Bélgica",
    "Croatia": "Croacia",
    "Denmark": "Dinamarca",
    "Austria": "Austria",
    "Poland": "Polonia",
    "Serbia": "Serbia",
    "Hungary": "Hungría",
    "Romania": "Rumania",
    "Slovenia": "Eslovenia",
    "Albania": "Albania",
    "Georgia": "Georgia",
    "Ukraine": "Ucrania",
    "Greece": "Grecia",
    "Wales": "Gales",
    "Colombia": "Colombia",
    "Uruguay": "Uruguay",
    "Ecuador": "Ecuador",
    "Venezuela": "Venezuela",
    "Bolivia": "Bolivia",
    "Chile": "Chile",
    "Peru": "Perú",
    "Japan": "Japón",
    "Iran": "Irán",
    "Saudi Arabia": "Arabia Saudita",
    "Iraq": "Irak",
    "Uzbekistan": "Uzbekistán",
    "Jordan": "Jordania",
    "Indonesia": "Indonesia",
    "China": "China",
    "Senegal": "Senegal",
    "Egypt": "Egipto",
    "Nigeria": "Nigeria",
    "Ivory Coast": "Costa de Marfil",
    "Côte d'Ivoire": "Costa de Marfil",
    "Ghana": "Ghana",
    "Cameroon": "Camerún",
    "Algeria": "Argelia",
    "Tunisia": "Túnez",
    "New Zealand": "Nueva Zelanda",
    "Cape Verde": "Cabo Verde",
    "Panama": "Panamá",
    "Costa Rica": "Costa Rica",
    "Honduras": "Honduras",
    "Jamaica": "Jamaica",
    "El Salvador": "El Salvador",
    "Guatemala": "Guatemala",
    "Norway": "Noruega",
    "Sweden": "Suecia",
    "Finland": "Finlandia",
    "Ireland": "Irlanda",
    "Slovakia": "Eslovaquia",
    "Bulgaria": "Bulgaria",
    "North Macedonia": "Macedonia del Norte",
    "Montenegro": "Montenegro",
    "Kosovo": "Kosovo",
}


def normalizar(nombre: str) -> str:
    """Convierte nombre en inglés a español, o devuelve el original si ya está mapeado."""
    return EN_A_ES.get(nombre, nombre)


def get_fuerza(nombre: str) -> FuerzaEquipo:
    """
    Devuelve la fuerza del equipo por nombre (español o inglés).
    Si no está en la base, asume fuerza promedio (1.0/1.0).
    """
    # Intento directo
    if nombre in EQUIPOS:
        return EQUIPOS[nombre]
    # Intento después de normalizar
    nombre_es = normalizar(nombre)
    if nombre_es in EQUIPOS:
        return EQUIPOS[nombre_es]
    # Fallback: promedio mundial
    return FuerzaEquipo(ataque=1.0, defensa=1.0)


def razonamiento_fuerza(local: str, visitante: str) -> str:
    """
    Genera un texto corto explicando la ventaja estadística entre los dos equipos.
    """
    fl = get_fuerza(local)
    fv = get_fuerza(visitante)

    lineas = []

    # Ventaja ofensiva
    if fl.ataque > fv.ataque + 0.25:
        lineas.append(f"⚡ {local} tiene ataque muy superior ({fl.ataque:.2f} vs {fv.ataque:.2f}).")
    elif fv.ataque > fl.ataque + 0.25:
        lineas.append(f"⚡ {visitante} tiene ataque superior ({fv.ataque:.2f} vs {fl.ataque:.2f}).")
    else:
        lineas.append(f"⚖️ Ataques equiparados ({local}: {fl.ataque:.2f} · {visitante}: {fv.ataque:.2f}).")

    # Ventaja defensiva
    if fl.defensa < fv.defensa - 0.15:
        lineas.append(f"🛡️ {local} tiene mejor defensa ({fl.defensa:.2f} vs {fv.defensa:.2f}).")
    elif fv.defensa < fl.defensa - 0.15:
        lineas.append(f"🛡️ {visitante} tiene mejor defensa ({fv.defensa:.2f} vs {fl.defensa:.2f}).")

    # Favorito global
    ventaja_local = (fl.ataque / fv.defensa) - (fv.ataque / fl.defensa)
    if ventaja_local > 0.4:
        lineas.append(f"📊 Favorito estadístico: **{local}** (ventaja combinada {ventaja_local:+.2f}).")
    elif ventaja_local < -0.4:
        lineas.append(f"📊 Favorito estadístico: **{visitante}** (ventaja combinada {-ventaja_local:+.2f}).")
    else:
        lineas.append("📊 Partido muy igualado estadísticamente.")

    lineas.append("_Ajustado por ventaja de local (+15% ataque efectivo)._")

    return "\n".join(lineas)
