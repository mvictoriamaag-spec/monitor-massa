"""Ciclo de recolección: busca en todas las fuentes, resume y guarda."""
import logging

import db
import resumen
from fuentes import noticias

log = logging.getLogger(__name__)


MAX_REINTENTOS = 50  # por corrida, para no pasarse del tiempo del job


def reintentar_resumenes():
    """Vuelve a pedirle a Claude el resumen de las notas en las que falló antes."""
    if not resumen.disponible():
        return
    pendientes = db.sin_resumen_ia()[:MAX_REINTENTOS]
    if not pendientes:
        return
    resumen.resumir(pendientes)
    listas = [m for m in pendientes if m["resumen_ia"]]
    db.actualizar(listas)
    log.info("Reintento de resúmenes: %d de %d resueltos", len(listas), len(pendientes))


def ciclo():
    """Ejecuta una recolección completa. Devuelve (cantidad_de_nuevas, avisos)."""
    encontradas, avisos = noticias.recolectar()
    nuevas = db.filtrar_nuevas(encontradas)
    # Ya con el link directo de cada nota, se vuelve a chequear que no esté repetida.
    nuevas = db.filtrar_nuevas(noticias.completar(nuevas))
    resumen.resumir(nuevas)
    db.guardar(nuevas)
    reintentar_resumenes()
    log.info("Ciclo terminado: %d encontradas, %d nuevas, %d avisos",
             len(encontradas), len(nuevas), len(avisos))
    return len(nuevas), avisos
