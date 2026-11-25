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


def _ruta(texto):
    return Path(texto).expanduser().resolve()


def validar_trabajo(trabajo):
    """Devuelve una lista de errores (vacía si el trabajo es válido)."""
    errores = []
    nombre = str(trabajo.get("nombre", "")).strip()
    origen = str(trabajo.get("origen", "")).strip()
    destino = str(trabajo.get("destino", "")).strip()
    prohibidas = {Path("/"), Path.home().resolve()}

    if not nombre:
        errores.append("El nombre es obligatorio.")
    elif not re.fullmatch(r"[A-Za-z0-9_-]+", nombre):
        errores.append("El nombre solo admite letras, números, guion y guion bajo.")

    ruta_origen = ruta_destino = None
    if not origen:
        errores.append("La carpeta de origen es obligatoria.")
    else:
        ruta_origen = _ruta(origen)
        if ruta_origen in prohibidas:
            errores.append("El origen no puede ser / ni la carpeta personal completa.")
        elif not ruta_origen.is_dir():
            errores.append("La carpeta de origen no existe.")

    if not destino:
        errores.append("La carpeta de destino es obligatoria.")
    else:
        ruta_destino = _ruta(destino)
        if ruta_destino in prohibidas:
            errores.append("El destino no puede ser / ni la carpeta personal completa.")

    if ruta_origen and ruta_destino:
        if ruta_destino == ruta_origen or ruta_origen in ruta_destino.parents:
            errores.append("El destino no puede estar dentro del origen.")

    try:
        copias = int(trabajo.get("copias", 0))
    except (TypeError, ValueError):
        copias = 0
    if copias < 1:
        errores.append("Las copias a conservar deben ser un número entero mayor o igual a 1.")
    return errores


def agregar_trabajo(trabajos, nuevo, ruta=None):
    """Valida el trabajo, lo agrega a la lista y la guarda. Devuelve la lista de errores."""
    errores = validar_trabajo(nuevo)
    nombre = str(nuevo.get("nombre", "")).strip()
    if any(t["nombre"] == nombre for t in trabajos):
        errores.append("Ya existe un trabajo con ese nombre.")
    if errores:
        return errores
    trabajos.append(
        {
            "nombre": nombre,
            "origen": str(nuevo["origen"]).strip(),
            "destino": str(nuevo["destino"]).strip(),
            "copias": int(nuevo["copias"]),
        }
    )
    guardar_trabajos(trabajos, ruta)
    return []
