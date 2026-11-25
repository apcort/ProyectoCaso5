"""Historial de ejecuciones (se guarda en datos/historial.csv)."""

import csv
from datetime import datetime
from pathlib import Path

from app.config import DATOS_DIR

ARCHIVO_HISTORIAL = DATOS_DIR / "historial.csv"
CAMPOS = ["fecha", "trabajo", "archivo", "duracion", "tamano", "resultado", "codigo"]


def registrar(entrada, ruta=None):
    """Agrega una fila al historial. Si falta la fecha, usa la actual."""
    ruta = Path(ruta) if ruta else ARCHIVO_HISTORIAL
    ruta.parent.mkdir(parents=True, exist_ok=True)
    es_nuevo = not ruta.exists()
    fila = {campo: entrada.get(campo, "") for campo in CAMPOS}
    if not fila["fecha"]:
        fila["fecha"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with ruta.open("a", newline="", encoding="utf-8") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=CAMPOS)
        if es_nuevo:
            escritor.writeheader()
        escritor.writerow(fila)


def cargar_historial(ruta=None):
    """Devuelve todas las filas del historial (la más antigua primero)."""
    ruta = Path(ruta) if ruta else ARCHIVO_HISTORIAL
    if not ruta.exists():
        return []
    with ruta.open(newline="", encoding="utf-8") as archivo:
        return list(csv.DictReader(archivo))
