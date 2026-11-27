"""Dirigentes y temas que sigue el monitor. Cada uno tiene su pestaña en la página.

Para sumar o sacar a alguien, editá la lista TEMAS: (identificador, nombre visible, patrones).
Los patrones se buscan sin distinguir mayúsculas ni acentos. Para la mayoría se pide nombre y
apellido, para no confundir con otras personas de mismo apellido (por ejemplo, Leopoldo Moreau).
"""
import re
import unicodedata

TEMAS = [
    ("massa", "Sergio Massa", [r"\bmassa\b", r"@?sergiomassa\b"]),
    ("massismo", "Massismo", [r"\bmassismo\b", r"\bmassistas?\b"]),
    ("frente-renovador", "Frente Renovador", [r"\bfrente renovador\b", r"@?frenterenovador\b"]),
    ("fundacion-encuentro", "Fundación Encuentro", [r"\bfundacion encuentro\b"]),
    ("malena-galmarini", "Malena Galmarini", [r"\bmalena galmarini\b", r"@?malegalmarini\b"]),
    ("sebastian-galmarini", "Sebastián Galmarini", [r"\bsebastian galmarini\b"]),
    ("cecilia-moreau", "Cecilia Moreau", [r"\bcecilia moreau\b", r"@?cecimoreau\b"]),
    ("diego-giuliano", "Diego Giuliano", [r"\bdiego giuliano\b"]),
    ("alexis-guerrera", "Alexis Guerrera", [r"\balexis guerrera\b"]),
    ("guillermo-michel", "Guillermo Michel", [r"\bguillermo michel\b"]),
    ("sabrina-selva", "Sabrina Selva", [r"\bsabrina selva\b"]),
    ("marina-salzmann", "Marina Salzmann", [r"\bsalzmann\b"]),
    ("jimena-lopez", "Jimena López", [r"\bjimena lopez\b"]),
    ("ramiro-gutierrez", "Ramiro Gutiérrez", [r"\bramiro gutierrez\b"]),
    ("sofia-vannelli", "Sofía Vannelli", [r"\bvannelli\b"]),
    ("ayelen-rasquetti", "Ayelén Rasquetti", [r"\brasquetti\b"]),
    ("luciana-padulo", "Luciana Padulo", [r"\bpadulo\b"]),
    ("martin-marinucci", "Martín Marinucci", [r"\bmarinucci\b"]),
    ("juan-martin-malpeli", "Juan Martín Malpeli", [r"\bmalpeli\b"]),
    ("de-mendiguren", "José Ignacio De Mendiguren", [r"\bmendiguren\b"]),
]

# Se borran antes de buscar: no son el Massa que nos interesa.
_EXCLUIR = re.compile(r"\bfelipe\s+massa\b")

_PATRONES = [(slug, re.compile("|".join(p))) for slug, _, p in TEMAS]
NOMBRES = {slug: nombre for slug, nombre, _ in TEMAS}


def _normalizar(texto):
    texto = unicodedata.normalize("NFKD", (texto or "").lower())
    return "".join(c for c in texto if not unicodedata.combining(c))


def temas_de(texto):
    """Identificadores de los dirigentes/temas que nombra el texto, en el orden de TEMAS."""
    t = _EXCLUIR.sub(" ", _normalizar(texto))
    return [slug for slug, patron in _PATRONES if patron.search(t)]


def menciona_alguno(texto):
    return bool(temas_de(texto))


# Cómo se busca en Google Noticias y X a quienes suelen aparecer sólo por el apellido.
_EN_BUSCADORES = {
    "massismo": "massismo", "marina-salzmann": "Salzmann", "sofia-vannelli": "Vannelli",
    "ayelen-rasquetti": "Rasquetti", "luciana-padulo": "Padulo", "martin-marinucci": "Marinucci",
    "juan-martin-malpeli": "Malpeli", "de-mendiguren": "Mendiguren",
}


def frase(slug):
    """Cómo se busca a un dirigente en Google Noticias o X."""
    return _EN_BUSCADORES.get(slug, f'"{NOMBRES[slug]}"')


def busquedas(max_largo=400, sin_massa=False):
    """Frases para buscadores (Google Noticias, X), agrupadas para no pasarse de largo."""
    frases = [_EN_BUSCADORES.get(slug, f'"{n}"') for slug, n in NOMBRES.items()
              if not (sin_massa and slug == "massa")]
    grupos, actual = [], []
    for f in frases:
        if actual and len(" OR ".join(actual + [f])) > max_largo:
            grupos.append(" OR ".join(actual))
            actual = []
        actual.append(f)
    if actual:
        grupos.append(" OR ".join(actual))
    return grupos
