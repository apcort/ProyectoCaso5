
import os
import subprocess
from datetime import datetime, timedelta

from app import historial, respaldo


def _trabajo(tmp_path, copias=3):
    origen = tmp_path / "origen"
    origen.mkdir(exist_ok=True)
    (origen / "index.html").write_text("hola", encoding="utf-8")
    return {
        "nombre": "web",
        "origen": str(origen),
        "destino": str(tmp_path / "destino"),
        "copias": copias,
    }


def _contenido(ruta):
    salida = subprocess.run(["tar", "-tzf", str(ruta)], capture_output=True, text=True, check=True)
    return salida.stdout


def test_nombre_respaldo_con_fecha():
    momento = datetime(2026, 11, 30, 14, 30)
    assert respaldo.nombre_respaldo("web", momento) == "web_2026-11-30_1430.tar.gz"
    assert respaldo.nombre_respaldo("web", momento, True) == "web_2026-11-30_1430_inc.tar.gz"


def test_ejecutar_crea_targz(tmp_path):
    trabajo = _trabajo(tmp_path)
    r = respaldo.ejecutar_respaldo(trabajo, ahora=datetime(2026, 11, 30, 14, 30))
    assert r["ok"] and r["codigo"] == 0
    assert r["archivo"] == "web_2026-11-30_1430.tar.gz"
    assert r["tamano"] > 0
    assert "index.html" in _contenido(tmp_path / "destino" / r["archivo"])


def test_origen_inexistente(tmp_path):
    trabajo = _trabajo(tmp_path)
    trabajo["origen"] = str(tmp_path / "no_existe")
    r = respaldo.ejecutar_respaldo(trabajo)
    assert r["ok"] is False
    assert "no existe" in r["mensaje"]


def test_rotar_conserva_solo_las_mas_nuevas(tmp_path):
    trabajo = _trabajo(tmp_path, copias=2)
    destino = tmp_path / "destino"
    destino.mkdir()
    for dia in range(1, 6):
        (destino / f"web_2026-11-0{dia}_1000.tar.gz").write_bytes(b"x")
    eliminados = respaldo.rotar(trabajo)
    assert len(eliminados) == 3
    restantes = sorted(p.name for p in destino.iterdir())
    assert restantes == ["web_2026-11-04_1000.tar.gz", "web_2026-11-05_1000.tar.gz"]


def test_ejecutar_y_registrar_rota_y_anota(tmp_path, monkeypatch):
    monkeypatch.setattr(historial, "ARCHIVO_HISTORIAL", tmp_path / "historial.csv")
    trabajo = _trabajo(tmp_path, copias=2)
    inicio = datetime(2026, 11, 30, 10, 0)
    for minuto in range(3):
        r = respaldo.ejecutar_y_registrar(trabajo, ahora=inicio + timedelta(minutes=minuto))
        assert r["ok"]
    assert len(list((tmp_path / "destino").glob("*.tar.gz"))) == 2
    filas = historial.cargar_historial()
    assert len(filas) == 3
    assert filas[-1]["resultado"] == "OK" and filas[-1]["codigo"] == "0"


def test_incremental_solo_incluye_lo_modificado(tmp_path):
    trabajo = _trabajo(tmp_path)
    viejo = tmp_path / "origen" / "index.html"
    os.utime(viejo, (1_500_000_000, 1_500_000_000))
    respaldo.ejecutar_respaldo(trabajo, ahora=datetime(2026, 1, 1, 0, 0))
    (tmp_path / "origen" / "nuevo.txt").write_text("nuevo", encoding="utf-8")
    r = respaldo.ejecutar_respaldo(trabajo, incremental=True, ahora=datetime(2026, 1, 2, 0, 0))
    assert r["ok"] and r["archivo"].endswith("_inc.tar.gz")
    contenido = _contenido(tmp_path / "destino" / r["archivo"])
    assert "nuevo.txt" in contenido
    assert "index.html" not in contenido


def test_incremental_sin_respaldo_previo_hace_completo(tmp_path):
    trabajo = _trabajo(tmp_path)
    r = respaldo.ejecutar_respaldo(trabajo, incremental=True, ahora=datetime(2026, 1, 1, 0, 0))
    assert r["ok"] and not r["archivo"].endswith("_inc.tar.gz")
    assert "se hizo completo" in r["mensaje"]
