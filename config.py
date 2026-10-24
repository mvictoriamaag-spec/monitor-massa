"""Configuración general del Monitor de menciones a Sergio Massa."""
import os
from datetime import timedelta, timezone
from pathlib import Path

from dotenv import load_dotenv

BASE = Path(__file__).resolve().parent
load_dotenv(BASE / ".env")

# Argentina no tiene horario de verano: UTC-3 fijo.
TZ = timezone(timedelta(hours=-3), "ART")

DATOS_DIR = BASE / "datos"   # historial (se guarda en el repositorio)
SITIO_DIR = BASE / "sitio"   # página web generada (se publica en GitHub Pages)

# Repositorio de GitHub (para el botón "Actualizar ahora"). En Actions lo completa GitHub solo.
REPO = os.getenv("GITHUB_REPOSITORY", "mvictoriamaag-spec/monitor-massa")

# --- Resúmenes con tu plan de Claude (vía Claude Code) ---
RESUMENES_IA = os.getenv("RESUMENES_IA", "si").lower() in ("si", "sí", "true", "1")
RESUMEN_MODELO = os.getenv("RESUMEN_MODELO", "haiku")
