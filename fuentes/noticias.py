"""Menciones en portales de noticias: diarios nacionales, medios del interior y Google Noticias."""
import json
import logging
import re
from calendar import timegm
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from urllib.parse import quote_plus, urlparse

import feedparser
import requests

from fuentes import es_link_web, limpiar_html, menciona_massa

log = logging.getLogger(__name__)

NACIONALES = {
    "Clarín": "https://www.clarin.com/rss/politica/",
    "La Nación": "https://www.lanacion.com.ar/arc/outboundfeeds/rss/category/politica/?outputType=xml",
    "Infobae": "https://www.infobae.com/arc/outboundfeeds/rss/category/politica/",
    "Página/12": "https://www.pagina12.com.ar/arc/outboundfeeds/rss/?outputType=xml",
    "Ámbito": "https://www.ambito.com/rss/pages/politica.xml",
    "Perfil": "https://www.perfil.com/feed/politica",
    "TN": "https://tn.com.ar/arc/outboundfeeds/rss/category/politica/?outputType=xml",
    "La Política Online": "https://www.lapoliticaonline.com/files/rss/politica.xml",
    "El Cronista": "https://www.cronista.com/arc/outboundfeeds/rss/?outputType=xml",
    "C5N": "https://www.c5n.com/rss/pages/politica.xml",
    "Minuto Uno": "https://www.minutouno.com/rss/pages/politica.xml",
}

INTERIOR = {
    "Los Andes (Mendoza)": "https://www.losandes.com.ar/rss/pages/politica.xml",
    "Diario Uno (Mendoza)": "https://www.diariouno.com.ar/rss/pages/politica.xml",
    "MDZ (Mendoza)": "https://www.mdzol.com/rss/pages/politica.xml",
    "Sitio Andino (Mendoza)": "https://www.sitioandino.com.ar/rss/pages/politica.xml",
    "La Capital (Rosario)": "https://www.lacapital.com.ar/rss/pages/politica.xml",
    "La Gaceta (Tucumán)": "https://feeds.feedburner.com/LaGacetaUltimoMomento?format=xml",
    "El Tribuno (Salta)": "https://www.eltribuno.com/feed/",
    "El Tribuno (Jujuy)": "https://www.eltribuno.com/jujuy/feed/",
    "Todo Jujuy": "https://www.todojujuy.com/rss/pages/politica.xml",
    "Río Negro": "https://www.rionegro.com.ar/feed/",
    "LM Neuquén": "https://www.lmneuquen.com/rss/pages/ultimas-noticias.xml",
    "El Día (La Plata)": "https://www.eldia.com/rss/pages/politica.xml",
    "0221 (La Plata)": "https://www.0221.com.ar/rss/pages/home.xml",
    "0223 (Mar del Plata)": "https://www.0223.com.ar/rss",
    "InfoCielo (Buenos Aires)": "https://www.infocielo.com/feed",
    "El Litoral (Corrientes)": "https://www.ellitoral.com.ar/feed/",
    "Época (Corrientes)": "https://www.diarioepoca.com/rss",
    "Misiones Online": "https://misionesonline.net/feed/",
    "Diario Norte (Chaco)": "https://www.diarionorte.com/rss",
    "Chaco Día por Día": "https://www.chacodiapordia.com/feed/",
    "Diario Panorama (Santiago del Estero)": "https://www.diariopanorama.com/rss",
    "El Ancasti (Catamarca)": "https://www.elancasti.com.ar/rss/pages/home.xml",
    "Tiempo de San Juan": "https://www.tiempodesanjuan.com/rss/pages/politica.xml",
    "Diario de Cuyo (San Juan)": "https://www.diariodecuyo.com.ar/rss/pages/politica.xml",
    "Diario Huarpe (San Juan)": "https://www.diariohuarpe.com/rss/portada.xml",
    "El Diario de la República (San Luis)": "https://www.eldiariodelarepublica.com/rss/portada.xml",
    "La Arena (La Pampa)": "https://www.laarena.com.ar/rss/portada.xml",
    "El Chubut": "https://www.elchubut.com.ar/rss/portada.xml",
    "El Sureño (Tierra del Fuego)": "https://www.surenio.com.ar/feed/",
    "Uno Entre Ríos": "https://www.unoentrerios.com.ar/rss/pages/politica.xml",
}

# Para clasificar lo que llega por Google Noticias según el dominio de la nota.
DOMINIOS_NACIONALES = {
    "clarin.com", "lanacion.com.ar", "infobae.com", "pagina12.com.ar", "ambito.com", "perfil.com",
    "tn.com.ar", "lapoliticaonline.com", "cronista.com", "c5n.com", "minutouno.com",
    "eldestapeweb.com", "iprofesional.com", "eleconomista.com.ar", "noticiasargentinas.com",
    "a24.com", "cronica.com.ar", "tiempoar.com.ar", "baenegocios.com", "letrap.com.ar",
    "laizquierdadiario.com", "elintransigente.com", "diarioar.com", "infonews.com", "canal26.com",
    "eldiarioar.com", "radiomitre.cienradios.com",
    "parlamentario.com", "politicaymedios.com.ar", "realpolitik.com.ar",
    "noticiasurbanas.com.ar", "bigbangnews.com", "politicargentina.com", "diagonales.com",
    "elargentinodiario.com.ar", "nexofin.com",
}
DOMINIOS_INTERIOR = {urlparse(u).hostname.removeprefix("www.") for u in INTERIOR.values()} | {
    "lavoz.com.ar", "cadena3.com", "elsol.com.ar", "rosario3.com", "ellitoral.com", "lanueva.com", "lacapitalmdp.com",
    "elterritorio.com.ar", "elliberal.com.ar", "nuevarioja.com.ar", "diariojornada.com.ar",
    "laopinionaustral.com.ar", "analisisdigital.com.ar", "elonce.com", "eldiario.com.ar",
    "laopiniondeformosa.com.ar", "canalc.com.ar", "elbonaerense.news", "informenorte.com",
    "eldiariodecarlospaz.com.ar", "eldoce.tv", "airedesantafe.com.ar", "lmcipolletti.com",
    "jujuyalmomento.com", "quepasasalta.com.ar", "infoban.com.ar", "primerapagina.info",
    "lagaceta.com.ar", "informenorte.com.ar", "agencianova.com",
    # Salta, Jujuy, Tucumán, Santiago del Estero, Catamarca, La Rioja
    "holasalta.com", "gentedesalta.com", "nuevodiariodesalta.com.ar", "agendasalta.com.ar",
    "infonoasalta.com.ar", "diariojujuy.com.ar", "pregon.com.ar", "lapostadelnoroeste.com.ar",
    "infonoroeste.com.ar", "contextotucuman.com", "canal10.com.ar", "infodelestero.com",
    "elesquiu.com", "launion.digital", "riojavirtual.com.ar",
    # NEA y Litoral
    "corrienteshoy.com", "identidadcorrentina.com.ar", "diariochaco.com", "lamanana.com.ar",
    "guauformosa.com.ar", "cuestionentrerriana.com.ar", "0343.com.ar", "reconquistaradios.com.ar",
    # Cuyo
    "mendozatoday.com.ar", "mendoza24.com.ar", "diariomendoza.com.ar", "canal13sanjuan.com",
    # Patagonia y La Pampa
    "neuquenpost.com", "minutoneuquen.com", "lmdiario.com.ar", "noticiasdebariloche.com.ar",
    "adnsur.com.ar", "lu17.com", "cholilaonline.ar", "lateclapatagonia.com.ar", "infofueguina.com",
    "eldiariodelapampa.com.ar", "infotecrealico.com.ar",
    # Provincia de Buenos Aires
    "diarioelnorte.com.ar", "laplata1.com", "eleditorplatense.com", "junindigital.com",
    "semanariodejunin.com.ar", "hoyrojas.com.ar", "larazondechivilcoy.com.ar", "noticiasmercedinas.com",
    "opinandosannicolas.ar", "eleco.com.ar", "lu9mardelplata.com.ar", "pinamar24.com.ar",
}

GOOGLE_NEWS = "https://news.google.com/rss/search?q={q}&hl=es-419&gl=AR&ceid=AR:es-419"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/130 Safari/537.36"}


def _fecha(entrada):
    t = entrada.get("published_parsed") or entrada.get("updated_parsed")
    return datetime.fromtimestamp(timegm(t), tz=timezone.utc) if t else None


def _leer(url):
    r = requests.get(url, headers=HEADERS, timeout=20)
    r.raise_for_status()
    return feedparser.parse(r.content)


def _dominio(url):
    return (urlparse(url).hostname or "").removeprefix("www.")


def clasificar(url):
    d = _dominio(url)
    if any(d == x or d.endswith("." + x) for x in DOMINIOS_INTERIOR):
        return "interior"
    if any(d == x or d.endswith("." + x) for x in DOMINIOS_NACIONALES):
        return "nacional"
    return "portal"


def recolectar(horas_atras=24):
    limite = datetime.now(timezone.utc) - timedelta(hours=horas_atras)
    fuentes = [(m, u, "nacional") for m, u in NACIONALES.items()]
    fuentes += [(m, u, "interior") for m, u in INTERIOR.items()]
    # Google Noticias va al final: cubre portales sin RSS y la deduplicación prioriza los feeds directos.
    fuentes.append(("Google Noticias",
                    GOOGLE_NEWS.format(q=quote_plus('"Sergio Massa" OR Massa when:1d')), None))

    def leer(fuente):
        medio, url, _ = fuente
        try:
            return _leer(url), None
        except Exception as e:  # un medio caído no frena al resto
            log.warning("No se pudo leer %s: %s", medio, e)
            return None, f"{medio}: {e}"

    with ThreadPoolExecutor(max_workers=10) as ex:
        resultados = list(ex.map(leer, fuentes))

    menciones, errores = [], []
    for (medio, _, categoria), (feed, error) in zip(fuentes, resultados):
        if error:
            errores.append(error)
            continue
        if not feed.entries:
            log.warning("%s respondió sin notas (¿cambió la dirección del RSS?)", medio)
            errores.append(f"{medio}: respondió sin notas")
            continue
        for e in feed.entries:
            titulo = limpiar_html(e.get("title", ""))
            bajada = limpiar_html(e.get("summary", ""))[:1500]
            if not menciona_massa(f"{titulo} {bajada}"):
                continue
            publicado = _fecha(e)
            if not publicado or publicado < limite or not es_link_web(e.get("link")):
                continue
            fuente = medio
            if medio == "Google Noticias":
                fuente = (e.get("source") or {}).get("title") or medio
                if titulo.endswith(f" - {fuente}"):
                    titulo = titulo[: -len(f" - {fuente}")]
                bajada = ""  # en Google Noticias la bajada repite el título
            menciones.append({
                "plataforma": categoria,  # None = se define al resolver el link de Google
                "fuente": fuente,
                "autor": fuente,
                "tipo": "nota",
                "titulo": titulo,
                "texto": bajada,
                "url": e["link"],
                "publicado": publicado.isoformat(timespec="seconds"),
            })
    return menciones, errores


def _resolver_google(url):
    """Convierte un link news.google.com/rss/articles/... en el link original de la nota."""
    gid = urlparse(url).path.rstrip("/").split("/")[-1]
    pagina = requests.get(url, headers=HEADERS, timeout=10).text
    sg = re.search(r'data-n-a-sg="([^"]+)"', pagina).group(1)
    ts = re.search(r'data-n-a-ts="([^"]+)"', pagina).group(1)
    interno = (
        '["garturlreq",[["X","X",["X","X"],null,null,1,1,"US:en",null,1,null,null,null,null,null,0,1],'
        f'"X","X",1,[1,1,1],1,1,null,0,0,null,0],"{gid}",{ts},"{sg}"]'
    )
    r = requests.post(
        "https://news.google.com/_/DotsSplashUi/data/batchexecute",
        headers={**HEADERS, "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"},
        data={"f.req": json.dumps([[["Fbv4je", interno, None, "generic"]]])},
        timeout=10,
    )
    datos = json.loads(r.text.split("\n\n", 1)[1])
    return json.loads(datos[0][2])[1]


def _bajada_de_la_nota(url):
    """Lee la descripción (og:description) de la página de la nota."""
    r = requests.get(url, headers=HEADERS, timeout=8)
    r.raise_for_status()  # una página de error no es la bajada de la nota
    if "charset" not in r.headers.get("Content-Type", "").lower():
        r.encoding = r.apparent_encoding  # evita acentos rotos
    for patron in (r'<meta[^>]+property="og:description"[^>]+content="([^"]*)"',
                   r'<meta[^>]+content="([^"]*)"[^>]+property="og:description"',
                   r'<meta[^>]+name="description"[^>]+content="([^"]*)"'):
        m = re.search(patron, r.text, re.IGNORECASE)
        if m:
            return limpiar_html(m.group(1))[:1500]
    return ""


def completar(menciones):
    """Para las menciones nuevas: link directo, categoría y bajada cuando falta."""
    def una(m):
        if "news.google.com" in m["url"]:
            try:
                directo = _resolver_google(m["url"])
                if es_link_web(directo):
                    m["url"] = directo
            except Exception as e:
                log.info("No se pudo resolver el link de Google (%s): %s", m["fuente"], e)
        if m["plataforma"] is None:
            m["plataforma"] = clasificar(m["url"])
        if not m["texto"] and "news.google.com" not in m["url"]:
            try:
                m["texto"] = _bajada_de_la_nota(m["url"])
            except Exception:
                pass
        return m

    with ThreadPoolExecutor(max_workers=8) as ex:
        return list(ex.map(una, menciones))
