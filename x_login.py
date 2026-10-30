"""Iniciar sesión en X para el monitor (se hace una sola vez, o cuando X cierre la sesión).

Abre una ventana de Chrome aparte. Entrá a X con tu usuario y contraseña ahí, y cuando veas
tu inicio de X, cerrá la ventana. La sesión queda guardada en la carpeta perfil-x/ de esta PC.
"""
from playwright.sync_api import sync_playwright

from fuentes import x

if __name__ == "__main__":
    with sync_playwright() as p:
        navegador = x.abrir(p, visible=True)
        pagina = navegador.pages[0] if navegador.pages else navegador.new_page()
        pagina.goto("https://x.com/login")
        print("Iniciá sesión en X en la ventana que se abrió y después cerrala.")
        pagina.wait_for_event("close", timeout=0)
        navegador.close()
    print("Listo: la sesión quedó guardada.")
