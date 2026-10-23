"""Fuentes de menciones: portales de noticias nacionales y del interior."""
import html
import re

_PATRON = re.compile(r"\bmassa\b|@sergiomassa\b|#sergiomassa\b", re.IGNORECASE)
_EXCLUIR = re.compile(r"\bfelipe\s+massa\b", re.IGNORECASE)


def menciona_massa(texto):
    """True si el texto nombra a Massa (y no se trata de Felipe Massa, el piloto)."""
    texto = texto or ""
    return bool(_PATRON.search(texto)) and not _EXCLUIR.search(texto)


def limpiar_html(texto):
    texto = re.sub(r"<[^>]+>", " ", texto or "")
    return re.sub(r"\s+", " ", html.unescape(texto)).strip()
