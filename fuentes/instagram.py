"""Menciones en Instagram: publicaciones públicas de medios nacionales y del interior.

No usa ninguna cuenta (no hay sesión que se pueda suspender) ni la API paga. Abre el perfil
público de cada medio, como cualquier visitante, y lee el texto de sus 12 últimas
publicaciones. Se quedan las que nombran a Massa o a los demás dirigentes (fuentes/temas.py).

Corre desde esta PC junto con la búsqueda de X (x_buscar.py), cada 30 minutos.
Para sumar o sacar un medio, editá las listas de abajo con el usuario de Instagram.
"""
import json
import logging
import re
import time
from datetime import datetime, timedelta, timezone

from fuentes import menciona_alguno

log = logging.getLogger(__name__)

NACIONALES = [
    "infobae", "clarincom", "lanacioncom", "todonoticias", "c5n", "pagina12", "eldestapeweb",
    "perfilcom", "canal26ok", "letra.p", "lapoliticaonline", "eldiarioar", "radiomitre",
    "telefenoticias", "elcronistacom", "iprofesional", "tiempoarg", "urgente24", "a24noticias",
    "cronicatv", "minutouno", "eltrecetv", "radio10", "noticiasargentinas",
]
INTERIOR = [
    "losandesdiario", "lagacetatucuman", "eltribunosalta", "rionegrocomar", "lmneuquen",
    "diarioellitoral", "unoentrerios", "eldocetv", "tiempodesanjuan", "misionesonline",
    "eltribunodejujuy", "infocielo", "elonce", "airedesantafe", "lanuevacom", "diariopanorama",
    "diarioconclusion", "lmcipolletti",
]

_EPOCA_IG = 1314220021721  # ms; los números de publicación de Instagram llevan la hora adentro
_AGENTE = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
           "Chrome/131.0.0.0 Safari/537.36")


def _hora(pk):
    return datetime.fromtimestamp(((int(pk) >> 23) + _EPOCA_IG) / 1000, tz=timezone.utc)


def _publicaciones(html):
    """Publicaciones que vienen dentro de la página del perfil: [{code, pk, texto, tipo}]."""
    encontradas = {}
    for bloque in re.findall(r'<script type="application/json"[^>]*>(.*?)</script>', html, re.S):
        if '"caption"' not in bloque:
            continue
        try:
            pila = [json.loads(bloque)]
        except ValueError:
            continue
        while pila:
            o = pila.pop()
            if isinstance(o, dict):
                if o.get("code") and o.get("pk") and isinstance(o.get("caption"), dict):
                    encontradas[o["code"]] = {"code": o["code"], "pk": o["pk"],
                                              "texto": o["caption"].get("text") or "",
                                              "tipo": o.get("product_type")}
                pila.extend(o.values())
            elif isinstance(o, list):
                pila.extend(o)
    return list(encontradas.values())


def recolectar(horas_atras=24):
    """Devuelve (menciones, avisos), igual que las demás fuentes."""
    from playwright.sync_api import sync_playwright

    limite = datetime.now(timezone.utc) - timedelta(hours=horas_atras)
    cuentas = [(c, "nacional") for c in NACIONALES] + [(c, "interior") for c in INTERIOR]
    menciones, sin_datos = [], []
    with sync_playwright() as p:
        navegador = p.chromium.launch(channel="chrome", headless=True)
        try:
            pagina = navegador.new_context(locale="es-AR", user_agent=_AGENTE).new_page()
            for cuenta, alcance in cuentas:
                try:
                    pagina.goto(f"https://www.instagram.com/{cuenta}/", wait_until="domcontentloaded",
                                timeout=45_000)
                    try:
                        pagina.wait_for_function(
                            "document.documentElement.innerHTML.includes('\"caption\"')", timeout=12_000)
                    except Exception:
                        pass
                    nombre = (pagina.title().split(" (@")[0] or cuenta).strip()
                    publicaciones = _publicaciones(pagina.content())
                except Exception as e:
                    log.info("Instagram: no se pudo abrir @%s: %s", cuenta, e)
                    publicaciones, nombre = [], cuenta
                if not publicaciones:
                    sin_datos.append(cuenta)
                for pub in publicaciones:
                    publicado = _hora(pub["pk"])
                    if publicado < limite or not menciona_alguno(pub["texto"]):
                        continue
                    ruta = "reel" if pub["tipo"] == "clips" else "p"
                    menciones.append({
                        "plataforma": "instagram",
                        "alcance": alcance,
                        "fuente": f"{nombre} (@{cuenta})",
                        "autor": nombre,
                        "tipo": "post",
                        "titulo": "",
                        "texto": pub["texto"][:1500],
                        "url": f"https://www.instagram.com/{ruta}/{pub['code']}/",
                        "publicado": publicado.isoformat(timespec="seconds"),
                    })
                time.sleep(1.5)  # de a poco, como una persona
        finally:
            navegador.close()

    avisos = []
    if len(sin_datos) > len(cuentas) // 2:
        avisos.append(f"Instagram: no se pudieron leer {len(sin_datos)} de {len(cuentas)} cuentas "
                      "(puede ser un límite temporal de Instagram).")
    log.info("Instagram: %d cuentas revisadas, %d sin datos, %d menciones",
             len(cuentas), len(sin_datos), len(menciones))
    return menciones, avisos
