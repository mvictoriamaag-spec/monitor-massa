"""Fuentes de menciones: portales de noticias, X e Instagram."""
import html
import re

from fuentes.temas import menciona_alguno, temas_de  # noqa: F401  (Massa y los demás dirigentes)


def es_link_web(url):
    """True si es un link http(s); descarta javascript:, data:, etc. que podrían venir en un feed."""
    return isinstance(url, str) and re.match(r"https?://", url, re.IGNORECASE) is not None


def limpiar_html(texto):
    texto = re.sub(r"<[^>]+>", " ", texto or "")
    return re.sub(r"\s+", " ", html.unescape(texto)).strip()
