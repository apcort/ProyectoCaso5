#!/usr/bin/env python3
"""Modo sin interfaz, pensado para cron: python3 respaldos.py --ejecutar todos"""

import argparse
import sys

from app import almacenamiento, config, respaldo


def main(argv=None):
    analizador = argparse.ArgumentParser(
        description="Gestor de respaldos (sin interfaz)"
    )
    analizador.add_argument(
        "--ejecutar",
        metavar="TRABAJO",
        help="nombre del trabajo o 'todos'"
    )
    analizador.add_argument(
        "--incremental",
        action="store_true",
        help="solo archivos modificados"
    )
    analizador.add_argument(
        "--listar",
        action="store_true",
        help="muestra los trabajos"
    )
    args = analizador.parse_args(argv)

    trabajos = config.cargar_trabajos()

    if args.listar:
        for t in trabajos:
            print(
                f"{t['nombre']}: {t['origen']} -> {t['destino']} "
                f"(copias: {t['copias']})"
            )
        return 0

    if not args.ejecutar:
        analizador.print_help()
        return 2

    if args.ejecutar == "todos":
        elegidos = trabajos
    else:
        elegidos = [t for t in trabajos if t["nombre"] == args.ejecutar]

    if not elegidos:
        print("No hay trabajos que ejecutar.", file=sys.stderr)
        return 2

    todo_bien = True

    for trabajo in elegidos:
        r = respaldo.ejecutar_y_registrar(
            trabajo,
            incremental=args.incremental
        )
        estado = "OK" if r["ok"] else "ERROR"
        tamano = almacenamiento.formatear_tamano(r["tamano"])

        print(
            f"[{estado}] {trabajo['nombre']}: {r['mensaje']} "
            f"({r['duracion']} s, {tamano})"
        )

        todo_bien = todo_bien and r["ok"]

    return 0 if todo_bien else 1


if __name__ == "__main__":
    sys.exit(main())
