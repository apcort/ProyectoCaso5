"""Motor de respaldo: crea el .tar.gz con tar, rota copias y registra el historial."""

import subprocess
import time
from datetime import datetime
from pathlib import Path

from app import almacenamiento, historial


def nombre_respaldo(nombre, ahora=None, incremental=False):
    """Ejemplo: web_2026-11-30_1430.tar.gz (o ..._inc.tar.gz si es incremental)."""
    ahora = ahora or datetime.now()
    sufijo = "_inc" if incremental else ""
    return f"{nombre}_{ahora:%Y-%m-%d_%H%M}{sufijo}.tar.gz"
