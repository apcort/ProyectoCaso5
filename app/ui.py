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

    def mostrar_mensaje(stdscr, titulo, lineas, color=C_OK):
    """Muestra un mensaje a pantalla completa. Se cierra con Enter, Esc o espacio."""
    def dibujar(scr, alto, ancho):
        win = crear_ventana(alto, ancho, 0, 0, titulo)
        for i, linea in enumerate(ajustar(lineas, ancho - 6)[: alto - 5]):
            escribir(win, 2 + i, 2, linea, curses.color_pair(color))
        escribir(win, alto - 1, 1, "Enter: continuar", curses.color_pair(C_AYUDA) | curses.A_BOLD)
        win.noutrefresh()
    while True:
        tecla = esperar_tecla(stdscr, dibujar)
        if es_enter(tecla) or tecla in ("\x1b", " "):
            return

def aviso(stdscr, texto):
    """Muestra un mensaje de 'trabajando...' sin esperar ninguna tecla."""
    alto, ancho = stdscr.getmaxyx()
    stdscr.erase()
    stdscr.noutrefresh()
    win = crear_ventana(alto, ancho, 0, 0, "Espera")
    escribir(win, 2, 2, texto, curses.color_pair(C_AVISO))
    win.noutrefresh()
    curses.doupdate()

def preguntar(stdscr, titulo, preguntas, intro=(), al_terminar=None):
    """Preguntas en formato terminal: cada pregunta aparece debajo de la anterior.
    preguntas: lista de (etiqueta, tipo); tipo "texto" (termina con Enter) o "sn" (tecla s/n).
    Devuelve la lista de respuestas, o None si se cancela con Esc.
    Si se da al_terminar(respuestas) -> (lineas, color), ese resultado se muestra
    debajo de las respuestas y se espera Enter.
    """
    estado = {"respuestas": [], "texto": [], "resultado": None}
    def dibujar(scr, alto, ancho):
        win = crear_ventana(alto, ancho, 0, 0, titulo)
        fila = 2
        for linea in intro:
            escribir(win, fila, 2, linea)
            fila += 1
        if intro:
            fila += 1
        respuestas = estado["respuestas"]
        for i in range(min(len(respuestas) + 1, len(preguntas))):
            etiqueta = preguntas[i][0]
            if i 
< len(respuestas):
                escribir(win, fila, 2, f"{etiqueta} {respuestas[i]}")
            else:
                libre = max(ancho - len(etiqueta) - 7, 5)
                escrito = "".join(estado["texto"])[-libre:]
                escribir(win, fila, 2, f"{etiqueta} {escrito}_", curses.A_BOLD)
            fila += 1
        if estado["resultado"] is not None:
            lineas, color = estado["resultado"]
            fila += 1
            for linea in ajustar(lineas, ancho - 6):
                escribir(win, fila, 2, linea, curses.color_pair(color))
                fila += 1
            pie = "Enter: continuar"
        elif len(respuestas) < len(preguntas) and preguntas[len(respuestas)][1] == "sn":
            pie = "s: Sí / n: No / Esc: cancelar"
        else:
            pie = "Enter: aceptar / Esc: cancelar"
        escribir(win, alto - 1, 1, pie, curses.color_pair(C_AYUDA) | curses.A_BOLD)
        win.noutrefresh()
    while True:
        respuestas = estado["respuestas"]
        if len(respuestas) == len(preguntas):
            if al_terminar is None:
                return list(respuestas)
            if estado["resultado"] is None:
                estado["resultado"] = al_terminar(list(respuestas))
            tecla = esperar_tecla(stdscr, dibujar)
            if es_enter(tecla) or tecla in ("\x1b", " "):
                return list(respuestas)
            continue
        es_sn = preguntas[len(respuestas)][1] == "sn"
        tecla = esperar_tecla(stdscr, dibujar, salir_con_q=es_sn)
        if tecla == "\x1b":
            return None
        if es_sn:
            if tecla in ("s", "S", "n", "N"):
                respuestas.append(tecla.lower())
        elif es_enter(tecla):
            respuestas.append("".join(estado["texto"]).strip())
            estado["texto"].clear()
        elif tecla in (curses.KEY_BACKSPACE, "\x7f", "\b"):
            if estado["texto"]:
                estado["texto"].pop()
        elif isinstance(tecla, str) and tecla.isprintable():
            estado["texto"].append(tecla)

def formulario_trabajo(stdscr, trabajos):
    """Pide nombre, origen, destino y copias, una pregunta debajo de otra, y guarda."""
    preguntas = [
        ("Nombre del trabajo:", "texto"),
        ("Carpeta de origen:", "texto"),
        ("Carpeta de destino de los respaldos:", "texto"),
        ("Cuántas copias conservar:", "texto"),
    ]
    def terminar(respuestas):
        nuevo = dict(zip(("nombre", "origen", "destino", "copias"), respuestas))
        errores = config.agregar_trabajo(trabajos, nuevo)
        if errores:
            return ["No se guardó el trabajo:"] + [f"- {e}" for e in errores], C_ERROR
        return ["El trabajo se guardó correctamente."], C_OK
    preguntar(stdscr, "Nuevo trabajo de respaldo", preguntas, al_terminar=terminar)
def pantalla_trabajos(stdscr):
  """Muestra los trabajos configurados y permite agregar uno nuevo."""
    pos = 0
    while True:
        trabajos = config.cargar_trabajos()
        opciones = [
            f"{t['nombre']:<12} > ORIGEN: {t['origen']}"
            for t in trabajos
        ]
        opciones.append(" - Agregar nuevo trabajo")
        ayuda = "Agregue un nuevo trabajo o haga Enter sobre uno ya creado."
        eleccion = menu_lista(stdscr, "Configurar trabajos de respaldo", opciones, pos, ayuda)
        if eleccion is None:
            return
        pos = eleccion
        if eleccion == len(trabajos):
            formulario_trabajo(stdscr, trabajos)
        else:
            t = trabajos[eleccion]
            datos = [
                f"Origen: {t['origen']}",
                f"Destino: {t['destino']}",
                f"Copias a conservar: {t['copias']}",
            ]
            mostrar_mensaje(stdscr, f"Trabajo {t['nombre']}", datos, 0)