"""Almacenamiento de menciones: un archivo JSON por día (datos/AAAA-MM-DD.json).

Se guarda como texto para que el historial quede versionado en el repositorio de GitHub.
"""
import hashlib
import json
import re
from datetime import date, datetime, timedelta, timezone

from config import DATOS_DIR, TZ
from fuentes.temas import temas_de


X_DIR = DATOS_DIR / "x"  # X e Instagram van aparte: los sube la PC, no GitHub Actions, y así no chocan
REDES_PC = ("x", "instagram")


def _ruta(fecha, carpeta=None):
    return (carpeta or DATOS_DIR) / f"{fecha.isoformat()}.json"


def _leer(ruta):
    return json.loads(ruta.read_text(encoding="utf-8")) if ruta.exists() else []


def _leer_dia(fecha):
    return _leer(_ruta(fecha)) + _leer(_ruta(fecha, X_DIR))


def _escribir_dia(fecha, menciones):
    menciones.sort(key=lambda m: m["publicado"], reverse=True)
    for carpeta, grupo in ((DATOS_DIR, [m for m in menciones if m.get("plataforma") not in REDES_PC]),
                           (X_DIR, [m for m in menciones if m.get("plataforma") in REDES_PC])):
        ruta = _ruta(fecha, carpeta)
        if grupo or ruta.exists():
            carpeta.mkdir(parents=True, exist_ok=True)
            ruta.write_text(json.dumps(grupo, ensure_ascii=False, indent=1), encoding="utf-8")


def _fecha_local(m):
    return datetime.fromisoformat(m["publicado"]).astimezone(TZ).date()


def id_para(url):
    return hashlib.sha1(url.encode("utf-8")).hexdigest()[:16]


def normalizar_titulo(titulo):
    return re.sub(r"[^a-z0-9áéíóúñü]+", " ", (titulo or "").lower()).strip()[:120]


def filtrar_nuevas(menciones):
    """Descarta las ya guardadas (misma URL, o misma nota vista por otra fuente)."""
    hoy = datetime.now(TZ).date()
    guardadas = [m for d in range(3) for m in _leer_dia(hoy - timedelta(days=d))]
    ids = {m["id"] for m in guardadas}
    titulos = {m["titulo_norm"] for m in guardadas if m.get("titulo_norm")}

    nuevas = []
    for m in menciones:
        m["id"] = id_para(m["url"])
        m["titulo_norm"] = normalizar_titulo(m.get("titulo"))
        if m["id"] in ids or (m["titulo_norm"] and m["titulo_norm"] in titulos):
            continue
        ids.add(m["id"])
        if m["titulo_norm"]:
            titulos.add(m["titulo_norm"])
        nuevas.append(m)
    return nuevas


def guardar(menciones):
    """Agrega las menciones al archivo de su día."""
    ahora = datetime.now(timezone.utc).isoformat(timespec="seconds")
    por_dia = {}
    for m in menciones:
        por_dia.setdefault(_fecha_local(m), []).append({**m, "recolectado": ahora})
    for fecha, nuevas in por_dia.items():
        _escribir_dia(fecha, _leer_dia(fecha) + nuevas)


def sin_resumen_ia(dias=2):
    """Menciones de los últimos días cuyo resumen de Claude falló (tienen el resumen simple)."""
    hoy = datetime.now(TZ).date()
    return [m for d in range(dias) for m in _leer_dia(hoy - timedelta(days=d)) if m.get("resumen_ia") is False]


def actualizar(menciones):
    """Reemplaza menciones ya guardadas (mismo id) por su versión nueva."""
    por_dia = {}
    for m in menciones:
        por_dia.setdefault(_fecha_local(m), {})[m["id"]] = m
    for fecha, cambios in por_dia.items():
        _escribir_dia(fecha, [cambios.get(m["id"], m) for m in _leer_dia(fecha)])


def _preparar(m):
    """Agrega lo que usa la página: hora local, red, alcance y de quiénes habla."""
    plataforma = m.get("plataforma")
    red = plataforma if plataforma in REDES_PC else "portales"
    alcance = m.get("alcance") or (plataforma if red == "portales" else "")
    temas = temas_de(f"{m.get('titulo', '')} {m.get('texto', '')}") or ["massa"]
    return {**m, "publicado_local": datetime.fromisoformat(m["publicado"]).astimezone(TZ),
            "red": red, "alcance": alcance, "temas": temas}


def del_dia(fecha, incluir_descartadas=False):
    return [_preparar(m) for m in _leer_dia(fecha) if incluir_descartadas or m.get("relevante", 1)]


def recientes(horas=24):
    """Menciones relevantes publicadas en las últimas `horas`, más reciente primero."""
    desde = datetime.now(timezone.utc) - timedelta(hours=horas)
    hoy = datetime.now(TZ).date()
    menciones = del_dia(hoy) + del_dia(hoy - timedelta(days=1))
    return [m for m in menciones if datetime.fromisoformat(m["publicado"]) >= desde]


def dias_guardados():
    archivos = [*DATOS_DIR.glob("*.json"), *X_DIR.glob("*.json")]
    return sorted({date.fromisoformat(p.stem) for p in archivos}, reverse=True)


def resumen_por_dia():
    """Por día con menciones (más reciente primero): {fecha, total, conteos}.

    conteos es una lista de [tema, red, alcance, cantidad] para que la página muestre los
    totales del dirigente y los filtros elegidos.
    """
    resultado = []
    for fecha in dias_guardados():
        conteos = {}
        menciones = del_dia(fecha)
        for m in menciones:
            for t in ["", *m["temas"]]:  # "" = todas (cada mención cuenta una sola vez)
                clave = (t, m["red"], m["alcance"])
                conteos[clave] = conteos.get(clave, 0) + 1
        if menciones:
            resultado.append({"fecha": fecha, "total": len(menciones),
                              "conteos": [[*k, n] for k, n in conteos.items()]})
    return resultado
