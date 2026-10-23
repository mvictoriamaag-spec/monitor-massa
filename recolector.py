"""Ciclo de recolección: busca en todas las fuentes, resume y guarda."""
import logging

import db
import resumen
from fuentes import noticias

log = logging.getLogger(__name__)


def ciclo():
    """Ejecuta una recolección completa. Devuelve (cantidad_de_nuevas, avisos)."""
    encontradas, avisos = noticias.recolectar()
    nuevas = db.filtrar_nuevas(encontradas)
    # Ya con el link directo de cada nota, se vuelve a chequear que no esté repetida.
    nuevas = db.filtrar_nuevas(noticias.completar(nuevas))
    resumen.resumir(nuevas)
    db.guardar(nuevas)
    log.info("Ciclo terminado: %d encontradas, %d nuevas, %d avisos",
             len(encontradas), len(nuevas), len(avisos))
    return len(nuevas), avisos
