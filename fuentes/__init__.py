"""Fuentes de menciones: portales de noticias nacionales y del interior."""
import html
import re

_PATRON = re.compile(r"\bmassa\b|@sergiomassa\b|#sergiomassa\b", re.IGNORECASE)
_EXCLUIR = re.compile(r"\bfelipe\s+massa\b", re.IGNORECASE)


def menciona_massa(texto):
    """True si el texto nombra a Massa (y no se trata de Felipe Massa, el piloto)."""
    return bool(_PATRON.search(_EXCLUIR.sub(" ", texto or "")))


def es_link_web(url):
    """True si es un link http(s); descarta javascript:, data:, etc. que podrían venir en un feed."""
    return isinstance(url, str) and re.match(r"https?://", url, re.IGNORECASE) is not None


def limpiar_html(texto):
    texto = re.sub(r"<[^>]+>", " ", texto or "")
    return re.sub(r"\s+", " ", html.unescape(texto)).strip()
