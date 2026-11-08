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
def ejecutar_respaldo(trabajo, incremental=False, ahora=None):

    """Crea el .tar.gz llamando a tar con subprocess.run(). Devuelve un diccionario."""
    ahora = ahora or datetime.now()
    resultado = {
        "ok": False,
        "archivo": "",
        "duracion": 0.0,
        "tamano": 0,
        "codigo": -1,
        "mensaje": "",
    }
    origen = Path(trabajo["origen"]).expanduser()
    destino = Path(trabajo["destino"]).expanduser()

    if not origen.is_dir():
        resultado["mensaje"] = "La carpeta de origen no existe."
        return resultado
    destino.mkdir(parents=True, exist_ok=True)

    hay_espacio, aviso = almacenamiento.revisar_espacio(origen, destino)
    if not hay_espacio:
        resultado["mensaje"] = aviso
        return resultado

    filtro = _filtro_incremental(trabajo) if incremental else None
    es_incremental = filtro is not None
    archivo = destino / nombre_respaldo(trabajo["nombre"], ahora, es_incremental)
    comando = ["tar", "-czf", str(archivo)] + (filtro or []) + ["-C", str(origen), "."]

    inicio = time.monotonic()
    try:
        proceso = subprocess.run(comando, capture_output=True, text=True, check=False)
    except FileNotFoundError:
        resultado["mensaje"] = "No se encontró el comando tar."
        return resultado

    resultado["duracion"] = round(time.monotonic() - inicio, 2)
    resultado["codigo"] = proceso.returncode

    if proceso.returncode != 0:
        archivo.unlink(missing_ok=True)
        error = (proceso.stderr.strip().splitlines() or ["error desconocido"])[-1]
        resultado["mensaje"] = f"tar terminó con error: {error}"
        return resultado

    resultado.update(ok=True, archivo=archivo.name, tamano=archivo.stat().st_size)
    tipo = "incremental" if es_incremental else "completo"
    resultado["mensaje"] = f"Respaldo {tipo} creado: {archivo.name}"
    if incremental and not es_incremental:
        resultado["mensaje"] += " (no había respaldo previo, se hizo completo)"
    return resultado
def rotar(trabajo):
    """Elimina los respaldos más antiguos si hay más de `copias`. Devuelve los borrados."""
    copias = int(trabajo["copias"])
    eliminados = []
    for r in almacenamiento.listar_respaldos(trabajo)[copias:]:
        Path(r["ruta"]).unlink(missing_ok=True)
        eliminados.append(r["nombre"])
    return eliminados

