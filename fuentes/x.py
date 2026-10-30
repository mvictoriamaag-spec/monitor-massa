"""Menciones en X, leídas con tu propia cuenta desde esta PC (sin la API paga de X).

Usa un perfil de Chrome aparte (carpeta perfil-x/, no se sube a GitHub) en el que iniciás
sesión una vez con `x_login.py`. Después `x_buscar.py` abre la búsqueda de X, junta los posts
recientes que nombran a Massa y los guarda como cualquier otra mención.

Ojo: leer X de esta forma va contra sus términos y X puede limitar o suspender la cuenta.
Por eso se busca pocas veces (cada 30 minutos) y con pocas páginas.
"""
import logging
import time
from datetime import datetime, timedelta, timezone
from urllib.parse import quote

from config import BASE
from fuentes import menciona_massa

log = logging.getLogger(__name__)

PERFIL = BASE / "perfil-x"
BUSQUEDA = '(Massa OR @SergioMassa) -Felipe lang:es'
DESPLAZAMIENTOS = 10  # cuántas veces se baja en la página de resultados
MIN_SEGUIDORES = 5000  # se descartan los posts de cuentas más chicas

# Lee los posts visibles en la página de resultados.
_LEER_POSTS = """() => [...document.querySelectorAll('article[data-testid="tweet"]')].map((a) => {
  const t = a.querySelector('time');
  const link = t && t.closest('a');
  const nombre = a.querySelector('[data-testid="User-Name"]');
  const texto = a.querySelector('[data-testid="tweetText"]');
  return {
    url: link ? link.href : null,
    publicado: t ? t.getAttribute('datetime') : null,
    autor: nombre ? nombre.innerText.split('\\n').slice(0, 2).join(' ') : '',
    texto: texto ? texto.innerText : '',
  };
})"""


def _seguidores_de(respuesta, destino):
    """De una respuesta de la búsqueda de X, anota {id del post: seguidores del autor} en destino."""
    if "SearchTimeline" not in respuesta.url:
        return
    try:
        datos = respuesta.json()
    except Exception:
        return

    def buscar_clave(obj, clave):
        if isinstance(obj, dict):
            if clave in obj:
                return obj[clave]
            obj = list(obj.values())
        if isinstance(obj, list):
            for v in obj:
                r = buscar_clave(v, clave)
                if r is not None:
                    return r
        return None

    def recorrer(obj):
        if isinstance(obj, dict):
            usuario = obj.get("core", {}).get("user_results", {}).get("result") if isinstance(obj.get("core"), dict) else None
            if obj.get("rest_id") and usuario:
                conteos = usuario.get("relationship_counts") or {}  # formato actual de X
                seguidores = conteos.get("followers", buscar_clave(usuario, "followers_count"))
                if seguidores is not None:
                    destino[str(obj["rest_id"])] = int(seguidores)
            for v in obj.values():
                recorrer(v)
        elif isinstance(obj, list):
            for v in obj:
                recorrer(v)

    recorrer(datos)


def abrir(playwright, visible=False):
    """Abre Chrome con el perfil del monitor (donde quedó iniciada la sesión de X)."""
    return playwright.chromium.launch_persistent_context(
        PERFIL, channel="chrome", headless=not visible,
        viewport={"width": 1100, "height": 1400}, locale="es-AR",
    )


def recolectar(horas_atras=24):
    """Devuelve (menciones, avisos), igual que fuentes.noticias.recolectar()."""
    from playwright.sync_api import sync_playwright

    limite = datetime.now(timezone.utc) - timedelta(hours=horas_atras)
    vistos, seguidores = {}, {}
    with sync_playwright() as p:
        navegador = abrir(p)
        try:
            pagina = navegador.new_page()
            pagina.on("response", lambda r: _seguidores_de(r, seguidores))
            pagina.goto(f"https://x.com/search?q={quote(BUSQUEDA)}&src=typed_query&f=live",
                        wait_until="domcontentloaded", timeout=60_000)
            try:
                pagina.wait_for_selector('article[data-testid="tweet"]', timeout=30_000)
            except Exception:
                if "/login" in pagina.url or "/i/flow" in pagina.url:
                    return [], ["X: la sesión se cerró. Volvé a ejecutar x_login.py para iniciar sesión."]
                return [], ["X: no aparecieron resultados (puede ser un límite temporal de X)."]
            for _ in range(DESPLAZAMIENTOS):
                for post in pagina.evaluate(_LEER_POSTS):
                    if post["url"] and "/status/" in post["url"]:
                        vistos[post["url"].split("?")[0]] = post
                pagina.mouse.wheel(0, 2500)
                time.sleep(2.5)
        finally:
            navegador.close()

    if vistos and not seguidores:
        return [], ["X: no se pudo leer la cantidad de seguidores (¿cambió X?); no se guardó ningún post."]

    menciones, chicas = [], 0
    for url, post in vistos.items():
        if not post["publicado"] or not menciona_massa(post["texto"]):
            continue
        cantidad = seguidores.get(url.rstrip("/").split("/status/")[-1].split("/")[0])
        if cantidad is None or cantidad < MIN_SEGUIDORES:
            chicas += 1
            continue
        publicado = datetime.fromisoformat(post["publicado"].replace("Z", "+00:00"))
        if publicado < limite:
            continue
        autor = post["autor"] or "X"
        menciones.append({
            "plataforma": "x",
            "fuente": autor,
            "autor": autor,
            "tipo": "post",
            "titulo": "",
            "texto": post["texto"][:1500],
            "url": url,
            "seguidores": cantidad,
            "publicado": publicado.astimezone(timezone.utc).isoformat(timespec="seconds"),
        })
    log.info("X: %d posts leídos, %d de cuentas con %d+ seguidores (%d descartados por cuentas chicas)",
             len(vistos), len(menciones), MIN_SEGUIDORES, chicas)
    return menciones, []
