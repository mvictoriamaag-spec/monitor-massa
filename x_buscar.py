"""Busca menciones en X desde esta PC y las sube al monitor. Lo ejecuta una tarea programada de Windows.

1. Trae lo último del repositorio.
2. Lee X con tu sesión, resume con Claude y guarda en datos/x/.
3. Sube los cambios y pide a GitHub que regenere la página.

Para probarlo a mano:  .venv\\Scripts\\python.exe x_buscar.py
"""
import logging
import subprocess
import sys

from config import BASE

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s",
                    handlers=[logging.FileHandler(BASE / "x.log", encoding="utf-8"), logging.StreamHandler()])
log = logging.getLogger("x_buscar")


def git(*args):
    return subprocess.run(["git", *args], cwd=BASE, capture_output=True, text=True, encoding="utf-8",
                          creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0)


def main():
    r = git("pull", "--rebase", "-q", "origin", "main")
    if r.returncode:
        log.error("No se pudo traer lo último de GitHub: %s", r.stderr.strip())
        return

    import db
    import resumen
    from fuentes import x

    encontradas, avisos = x.recolectar()
    for a in avisos:
        log.warning(a)
    nuevas = db.filtrar_nuevas(encontradas)
    resumen.resumir(nuevas)
    db.guardar(nuevas)
    log.info("X: %d encontradas, %d nuevas", len(encontradas), len(nuevas))
    if not nuevas:
        return

    git("add", "datos/x")
    git("commit", "-q", "-m", f"Menciones en X ({len(nuevas)})")
    for _ in range(3):
        if git("pull", "--rebase", "-q", "origin", "main").returncode == 0 and git("push", "-q").returncode == 0:
            # Regenera la página ya, sin esperar a la próxima corrida programada.
            subprocess.run(["gh", "workflow", "run", "actualizar.yml"], cwd=BASE, capture_output=True,
                           creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0)
            return
        git("rebase", "--abort")
    log.error("No se pudieron subir las menciones de X; se reintenta en la próxima corrida.")


if __name__ == "__main__":
    main()
