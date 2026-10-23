"""Genera la página web estática (carpeta sitio/) que se publica en GitHub Pages.

sitio/index.html            Última hora
sitio/dia/AAAA-MM-DD.html   Todas las menciones de un día, por hora (también es el archivo del día)
sitio/historial.html        Menciones pasadas
"""
from datetime import datetime

from jinja2 import Environment, FileSystemLoader, select_autoescape

import db
from config import BASE, SITIO_DIR, TZ

jinja = Environment(loader=FileSystemLoader(BASE / "templates"), autoescape=select_autoescape(["html"]))

DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
         "septiembre", "octubre", "noviembre", "diciembre"]


def fecha_larga(fecha):
    return f"{DIAS[fecha.weekday()]} {fecha.day} de {MESES[fecha.month - 1]} de {fecha.year}"


def agrupar_por_hora(menciones):
    """[(etiqueta '14:00 a 14:59', [menciones])] con la hora más reciente primero."""
    grupos = {}
    for m in menciones:
        h = m["publicado_local"].replace(minute=0, second=0, microsecond=0)
        grupos.setdefault(h, []).append(m)
    return [(f"{h:%H}:00 a {h:%H}:59", grupos[h]) for h in sorted(grupos, reverse=True)]


def _escribir(ruta_relativa, plantilla, **contexto):
    ruta = SITIO_DIR / ruta_relativa
    ruta.parent.mkdir(parents=True, exist_ok=True)
    raiz = "../" * ruta_relativa.count("/")
    html = jinja.get_template(plantilla).render(raiz=raiz, **contexto)
    ruta.write_text(html, encoding="utf-8")


def generar(avisos=()):
    ahora = datetime.now(TZ)
    hoy = ahora.date()
    comun = {"generado": ahora, "hoy": hoy, "avisos": list(avisos)}

    # Última hora: se incluyen 3 horas y el navegador oculta lo que tenga más de 60 minutos,
    # así la página sigue siendo correcta aunque se mire un rato después de generada.
    _escribir("index.html", "ultima_hora.html", pestana="ultima",
              menciones=db.recientes(horas=3), **comun)

    for fecha in {hoy, *db.dias_guardados()}:
        menciones = db.del_dia(fecha)
        contexto = dict(fecha=fecha, fecha_larga=fecha_larga(fecha), grupos=agrupar_por_hora(menciones),
                        total=len(menciones), **comun)
        _escribir(f"dia/{fecha.isoformat()}.html", "dia.html",
                  pestana="hoy" if fecha == hoy else "historial", **contexto)
        if fecha == hoy:
            _escribir("hoy.html", "dia.html", pestana="hoy", **contexto)

    resumen = db.resumen_por_dia()
    for d in resumen:
        d["fecha_larga"] = fecha_larga(d["fecha"])
    _escribir("historial.html", "historial.html", pestana="historial", dias=resumen, **comun)
    (SITIO_DIR / ".nojekyll").touch()
