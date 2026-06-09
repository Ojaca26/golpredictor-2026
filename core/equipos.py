"""
Base de datos de fuerzas por equipo para el Mundial 2026.
Escala Poisson: ataque>1 marca mas, defensa>1 encaja mas (peor defensa).
"""

from __future__ import annotations
from core.predictor import FuerzaEquipo

EQUIPOS = {
    # CONMEBOL
    "Brasil":           FuerzaEquipo(ataque=1.95, defensa=0.78),
    "Argentina":        FuerzaEquipo(ataque=1.92, defensa=0.80),
    "Colombia":         FuerzaEquipo(ataque=1.55, defensa=0.98),
    "Uruguay":          FuerzaEquipo(ataque=1.50, defensa=0.95),
    "Ecuador":          FuerzaEquipo(ataque=1.25, defensa=1.10),
    "Paraguay":         FuerzaEquipo(ataque=1.10, defensa=1.22),
    "Venezuela":        FuerzaEquipo(ataque=1.05, defensa=1.25),
    "Bolivia":          FuerzaEquipo(ataque=0.85, defensa=1.42),
    "Chile":            FuerzaEquipo(ataque=1.20, defensa=1.15),
    "Peru":             FuerzaEquipo(ataque=1.10, defensa=1.20),
    "Perú":             FuerzaEquipo(ataque=1.10, defensa=1.20),
    # UEFA
    "Francia":          FuerzaEquipo(ataque=2.00, defensa=0.75),
    "España":           FuerzaEquipo(ataque=1.88, defensa=0.78),
    "Inglaterra":       FuerzaEquipo(ataque=1.82, defensa=0.82),
    "Alemania":         FuerzaEquipo(ataque=1.85, defensa=0.85),
    "Portugal":         FuerzaEquipo(ataque=1.80, defensa=0.88),
    "Países Bajos":     FuerzaEquipo(ataque=1.72, defensa=0.88),
    "Holanda":          FuerzaEquipo(ataque=1.72, defensa=0.88),
    "Bélgica":          FuerzaEquipo(ataque=1.65, defensa=0.95),
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
    # CONCACAF
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
    # AFC
    "Japón":            FuerzaEquipo(ataque=1.50, defensa=0.95),
    "Corea del Sur":    FuerzaEquipo(ataque=1.38, defensa=1.00),
    "Arabia Saudita":   FuerzaEquipo(ataque=1.12, defensa=1.15),
    "Irán":             FuerzaEquipo(ataque=1.10, defensa=1.12),
    "Australia":        FuerzaEquipo(ataque=1.20, defensa=1.10),
    "Catar":            FuerzaEquipo(ataque=0.88, defensa=1.42),
    "Qatar":            FuerzaEquipo(ataque=0.88, defensa=1.42),
    "Irak":             FuerzaEquipo(ataque=0.95, defensa=1.30),
    "Uzbekistán":       FuerzaEquipo(ataque=0.90, defensa=1.32),
    "Jordania":         FuerzaEquipo(ataque=0.88, defensa=1.35),
    "Indonesia":        FuerzaEquipo(ataque=0.78, defensa=1.50),
    "China":            FuerzaEquipo(ataque=0.80, defensa=1.45),
    # CAF
    "Marruecos":        FuerzaEquipo(ataque=1.42, defensa=0.92),
    "Senegal":          FuerzaEquipo(ataque=1.35, defensa=1.00),
    "Egipto":           FuerzaEquipo(ataque=1.28, defensa=1.05),
    "Nigeria":          FuerzaEquipo(ataque=1.25, defensa=1.10),
    "Costa de Marfil":  FuerzaEquipo(ataque=1.22, defensa=1.12),
    "Ghana":            FuerzaEquipo(ataque=1.18, defensa=1.15),
    "Camerún":          FuerzaEquipo(ataque=1.15, defensa=1.18),
    "Argelia":          FuerzaEquipo(ataque=1.20, defensa=1.12),
    "Túnez":            FuerzaEquipo(ataque=1.10, defensa=1.15),
    "Sudáfrica":        FuerzaEquipo(ataque=0.95, defensa=1.25),
    "Mali":             FuerzaEquipo(ataque=1.05, defensa=1.20),
    "Burkina Faso":     FuerzaEquipo(ataque=1.00, defensa=1.25),
    # OFC
    "Nueva Zelanda":    FuerzaEquipo(ataque=0.95, defensa=1.30),
}

EN_A_ES = {
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
    "Ghana": "Ghana",
    "Cameroon": "Camerún",
    "Algeria": "Argelia",
    "Tunisia": "Túnez",
    "New Zealand": "Nueva Zelanda",
    "Panama": "Panamá",
    "Costa Rica": "Costa Rica",
    "Honduras": "Honduras",
    "Jamaica": "Jamaica",
    "El Salvador": "El Salvador",
    "Guatemala": "Guatemala",
    "Norway": "Noruega",
    "Sweden": "Suecia",
    "Ireland": "Irlanda",
    "Slovakia": "Eslovaquia",
    "North Macedonia": "Macedonia del Norte",
    "Montenegro": "Montenegro",
    "Kosovo": "Kosovo",
}


def normalizar(nombre):
    return EN_A_ES.get(nombre, nombre)


def get_fuerza(nombre):
    if nombre in EQUIPOS:
        return EQUIPOS[nombre]
    nombre_es = normalizar(nombre)
    if nombre_es in EQUIPOS:
        return EQUIPOS[nombre_es]
    return FuerzaEquipo(ataque=1.0, defensa=1.0)


def razonamiento_fuerza(local, visitante):
    fl = get_fuerza(local)
    fv = get_fuerza(visitante)
    lineas = []

    if fl.ataque > fv.ataque + 0.25:
        lineas.append(local + " tiene ataque superior (" + str(round(fl.ataque, 2)) + " vs " + str(round(fv.ataque, 2)) + ").")
    elif fv.ataque > fl.ataque + 0.25:
        lineas.append(visitante + " tiene ataque superior (" + str(round(fv.ataque, 2)) + " vs " + str(round(fl.ataque, 2)) + ").")
    else:
        lineas.append("Ataques equiparados (" + local + ": " + str(round(fl.ataque, 2)) + " / " + visitante + ": " + str(round(fv.ataque, 2)) + ").")

    if fl.defensa < fv.defensa - 0.15:
        lineas.append(local + " tiene mejor defensa (" + str(round(fl.defensa, 2)) + " vs " + str(round(fv.defensa, 2)) + ").")
    elif fv.defensa < fl.defensa - 0.15:
        lineas.append(visitante + " tiene mejor defensa (" + str(round(fv.defensa, 2)) + " vs " + str(round(fl.defensa, 2)) + ").")

    ventaja = (fl.ataque / fv.defensa) - (fv.ataque / fl.defensa)
    if ventaja > 0.4:
        lineas.append("Favorito estadistico: " + local + " (ventaja combinada " + str(round(ventaja, 2)) + ").")
    elif ventaja < -0.4:
        lineas.append("Favorito estadistico: " + visitante + " (ventaja combinada " + str(round(-ventaja, 2)) + ").")
    else:
        lineas.append("Partido muy igualado estadisticamente.")

    lineas.append("Ataque local tiene +15% efectivo por ventaja de local.")
    return "\n".join(lineas)
