"""Punto de entrada: gestor de respaldos con rotación (interfaz curses)."""
import curses
import locale
import os
from app import ui
def main():
    locale.setlocale(locale.LC_ALL, "")
    os.environ.setdefault("ESCDELAY", "25")
    try:
        curses.wrapper(ui.ejecutar) # wrapper() que restaura la terminal al salir
    except KeyboardInterrupt:
        pass
if __name__ == "__main__":
    main()