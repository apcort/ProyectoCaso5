"""Configuración de los trabajos de respaldo (se guarda en datos/trabajos.json)."""

import json
import os
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DATOS_DIR = Path(os.environ.get("RESPALDOS_DATOS", RAIZ / "datos"))
ARCHIVO_TRABAJOS = DATOS_DIR / "trabajos.json"


def cargar_trabajos(ruta=None):
    """Lee la lista de trabajos. Si el archivo no existe o está dañado, devuelve []."""
    ruta = Path(ruta) if ruta else ARCHIVO_TRABAJOS
    if not ruta.exists():
        return []
    try:
        datos = json.loads(ruta.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    return datos if isinstance(datos, list) else []


def guardar_trabajos(trabajos, ruta=None):
    """Guarda la lista de trabajos en JSON (crea la carpeta datos/ si hace falta)."""
    ruta = Path(ruta) if ruta else ARCHIVO_TRABAJOS
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(trabajos, indent=2, ensure_ascii=False), encoding="utf-8")
