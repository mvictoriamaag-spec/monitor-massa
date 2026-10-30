"""Iniciar sesión en X para el monitor (se hace una sola vez, o cuando X cierre la sesión).

Abre un Chrome común (sin control automático, así Google deja entrar con "Iniciar sesión con
Google") usando el perfil del monitor. Entrá a X ahí y, cuando veas tu inicio, cerrá la ventana.
La sesión queda guardada en la carpeta perfil-x/ de esta PC.
"""
import os
import subprocess
from pathlib import Path

from fuentes import x

CHROME = [Path(os.environ.get(v, "")) / "Google/Chrome/Application/chrome.exe"
          for v in ("PROGRAMFILES", "PROGRAMFILES(X86)", "LOCALAPPDATA")]

if __name__ == "__main__":
    chrome = next(str(c) for c in CHROME if c.is_file())
    print("Iniciá sesión en X en la ventana que se abrió y después cerrala.")
    subprocess.run([chrome, f"--user-data-dir={x.PERFIL}", "--no-first-run", "https://x.com/login"])
    print("Listo: la sesión quedó guardada.")
