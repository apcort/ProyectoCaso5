from app import historial


def test_registrar_y_cargar(tmp_path):
    ruta = tmp_path / "historial.csv"
    historial.registrar(
        {
            "trabajo": "web",
            "archivo": "a.tar.gz",
            "duracion": 0.5,
            "tamano": 100,
            "resultado": "OK",
            "codigo": 0,
        },
        ruta,
    )
    historial.registrar({"trabajo": "web", "resultado": "ERROR", "codigo": 2}, ruta)
    filas = historial.cargar_historial(ruta)
    assert len(filas) == 2
    assert filas[0]["resultado"] == "OK"
    assert filas[0]["fecha"] != ""  # se llena sola
    assert filas[1]["codigo"] == "2"


def test_historial_vacio(tmp_path):
    assert historial.cargar_historial(tmp_path / "no_existe.csv") == []
