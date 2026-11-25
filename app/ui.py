"""Interfaz de terminal con curses: menús, ventanas, colores y cambio de tamaño."""

import contextlib
import curses
import textwrap
from app import almacenamiento, config, historial, respaldo

MIN_ALTO, MIN_ANCHO = 12, 50
C_TITULO, C_SELECCION, C_OK, C_ERROR, C_AVISO, C_AYUDA = 1, 2, 3, 4, 5, 6
PIE_MENU = "Flechas: mover / Enter: elegir / Esc: volver / q: salir"

class Salir(Exception):
    """Se lanza al presionar q; sube hasta ejecutar() y cierra el programa."""

def recortar(texto, ancho):
    """Corta el texto para que quepa en `ancho` columnas (agrega ... si lo recorta)."""
    texto = str(texto)
    ancho = max(ancho, 0)
    if len(texto) <= ancho:
        return texto
    if ancho <= 3:
        return texto[:ancho]
    return texto[: ancho - 3] + "..."

def ajustar(lineas, ancho):
    """Parte las líneas largas en varias para que quepan en `ancho` columnas."""
    salida = []
    for linea in lineas:
        salida.extend(textwrap.wrap(str(linea), max(ancho, 10), subsequent_indent="  ") or [""])
    return salida

def iniciar_colores():
    """Oculta el cursor y define los pares de color de la aplicación."""
    with contextlib.suppress(curses.error):
        curses.curs_set(0)
    if not curses.has_colors():
        return
    curses.start_color()
    curses.init_pair(C_TITULO, curses.COLOR_WHITE, curses.COLOR_BLUE)
    curses.init_pair(C_SELECCION, curses.COLOR_BLACK, curses.COLOR_CYAN)
    curses.init_pair(C_OK, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(C_ERROR, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(C_AVISO, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    curses.init_pair(C_AYUDA, curses.COLOR_GREEN, curses.COLOR_BLACK)

def escribir(win, y, x, texto, atributo=0):
    """addstr seguro: recorta el texto y ignora los errores de borde de curses."""
    alto, ancho = win.getmaxyx()
    if y < 0 or y >= alto or x < 0 or x >= ancho - 1:
        return
    with contextlib.suppress(curses.error):
        win.addstr(y, x, recortar(texto, ancho - x - 1), atributo)

def leer_tecla(stdscr):
    """Lee una tecla (str para caracteres, int para teclas especiales)."""
    try:
        return stdscr.get_wch()
    except curses.error:
        return None

def es_enter(tecla):
    return tecla in ("\n", "\r", curses.KEY_ENTER)

def crear_ventana(alto, ancho, y, x, titulo=""):
    """Crea una ventana con curses.newwin, sin borde.
    El título se muestra como una barra de color en la primera fila.
    """
    alto = max(3, min(alto, curses.LINES))
    ancho = max(10, min(ancho, curses.COLS))
    win = curses.newwin(alto, ancho, max(y, 0), max(x, 0))
    win.keypad(True)
    win.erase()
    if titulo:
        escribir(win, 0, 1, titulo)
        win.chgat(0, 0, ancho, curses.color_pair(C_TITULO) | curses.A_BOLD)
    return win

def esperar_tecla(stdscr, dibujar, salir_con_q=True):
    """Dibuja con dibujar(stdscr, alto, ancho) y espera una tecla.
    - Con KEY_RESIZE vuelve a dibujar con el nuevo tamaño.
    - Si la terminal es muy pequeña muestra un aviso en lugar de romperse.
    - La tecla q lanza Salir (salvo donde se escribe texto).
    """
    while True:
        alto, ancho = stdscr.getmaxyx()
        stdscr.erase()
         if alto < MIN_ALTO or ancho < MIN_ANCHO:
            escribir(stdscr, 0, 0, f"Agranda la terminal (minimo {MIN_ANCHO}x{MIN_ALTO})")
            stdscr.noutrefresh()
        else:
            stdscr.noutrefresh()
            dibujar(stdscr, alto, ancho)
        curses.doupdate()
        tecla = leer_tecla(stdscr)
        if tecla == curses.KEY_RESIZE:
            curses.update_lines_cols()
            stdscr.clear()
            continue
        if salir_con_q and tecla in ("q", "Q"):
            raise Salir
        return tecla

def menu_lista(stdscr, titulo, opciones, seleccion=0, ayuda=""):
    """Menú navegable con flechas. Devuelve el índice elegido o None si presiona Esc."""
    estado = {"sel": min(seleccion, max(len(opciones) - 1, 0)), "ini": 0}
    def dibujar(scr, alto, ancho):
        win = crear_ventana(alto, ancho, 0, 0, titulo)
        primera = 2
        if ayuda:
            escribir(win, 2, 2, ayuda, curses.color_pair(C_AYUDA) | curses.A_BOLD)
            primera = 4
        filas = max(alto - primera - 2, 1)
        if estado["sel"] < estado["ini"]:
            estado["ini"] = estado["sel"]
        if estado["sel"] >= estado["ini"] + filas:
            estado["ini"] = estado["sel"] - filas + 1
        visibles = opciones[estado["ini"] : estado["ini"] + filas]
        for i, texto in enumerate(visibles):
            actual = estado["ini"] + i == estado["sel"]
            linea = f"  {texto}".ljust(ancho - 1)
            atributo = curses.color_pair(C_SELECCION) if actual else 0
            escribir(win, primera + i, 0, linea, atributo)
        if not opciones:
            escribir(win, primera, 2, "(sin elementos)")
        escribir(win, alto - 1, 1, PIE_MENU, curses.color_pair(C_AYUDA) | curses.A_BOLD)
        win.noutrefresh()
    while True:
        tecla = esperar_tecla(stdscr, dibujar)
        if tecla == curses.KEY_UP and estado["sel"] > 0:
            estado["sel"] -= 1
        elif tecla == curses.KEY_DOWN and estado["sel"] < len(opciones) - 1:
            estado["sel"] += 1
        elif es_enter(tecla) and opciones:
            return estado["sel"]
        elif tecla in ("\x1b", curses.KEY_LEFT, curses.KEY_BACKSPACE):
            return None
            