"""Almacenamiento de menciones: un archivo JSON por día (datos/AAAA-MM-DD.json).

Se guarda como texto para que el historial quede versionado en el repositorio de GitHub.
"""
import hashlib
import json
import re
from datetime import date, datetime, timedelta, timezone

from config import DATOS_DIR, TZ


def _ruta(fecha):
    return DATOS_DIR / f"{fecha.isoformat()}.json"


def _leer_dia(fecha):
    ruta = _ruta(fecha)
    return json.loads(ruta.read_text(encoding="utf-8")) if ruta.exists() else []


def _escribir_dia(fecha, menciones):
    DATOS_DIR.mkdir(parents=True, exist_ok=True)
    menciones.sort(key=lambda m: m["publicado"], reverse=True)
    _ruta(fecha).write_text(json.dumps(menciones, ensure_ascii=False, indent=1), encoding="utf-8")


def _fecha_local(m):
    return datetime.fromisoformat(m["publicado"]).astimezone(TZ).date()


def id_para(url):
    return hashlib.sha1(url.encode("utf-8")).hexdigest()[:16]


def normalizar_titulo(titulo):
    t = re.sub(r"\s+-\s+[^-]+$", "", titulo or "")  # quita " - Medio" de Google Noticias
    return re.sub(r"[^a-z0-9áéíóúñü]+", " ", t.lower()).strip()[:120]


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


def _preparar(m):
    return {**m, "publicado_local": datetime.fromisoformat(m["publicado"]).astimezone(TZ)}


def del_dia(fecha, incluir_descartadas=False):
    return [_preparar(m) for m in _leer_dia(fecha) if incluir_descartadas or m.get("relevante", 1)]


def recientes(horas=24):
    """Menciones relevantes publicadas en las últimas `horas`, más reciente primero."""
    desde = datetime.now(timezone.utc) - timedelta(hours=horas)
    hoy = datetime.now(TZ).date()
    menciones = del_dia(hoy) + del_dia(hoy - timedelta(days=1))
    return [m for m in menciones if datetime.fromisoformat(m["publicado"]) >= desde]


def dias_guardados():
    return sorted((date.fromisoformat(p.stem) for p in DATOS_DIR.glob("*.json")), reverse=True)


def resumen_por_dia():
    """[{fecha, total, nacional, interior, portal}] de los días con menciones, más reciente primero."""
    resultado = []
    for fecha in dias_guardados():
        d = {"fecha": fecha, "total": 0, "nacional": 0, "interior": 0, "portal": 0}
        for m in del_dia(fecha):
            d["total"] += 1
            d[m["plataforma"]] = d.get(m["plataforma"], 0) + 1
        if d["total"]:
            resultado.append(d)
    return resultado
