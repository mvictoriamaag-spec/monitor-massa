"""Busca menciones nuevas y regenera la página web. Lo ejecuta GitHub Actions cada 15 minutos.

Para probarlo en esta PC:  python actualizar.py   (después abrí sitio/index.html)
"""
import logging

import recolector
import sitio

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

if __name__ == "__main__":
    _, avisos = recolector.ciclo()
    sitio.generar(avisos)
