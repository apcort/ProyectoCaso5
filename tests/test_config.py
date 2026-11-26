from pathlib import Path

from app import config


def _trabajo(tmp_path, **cambios):
    origen = tmp_path / "origen"
    origen.mkdir(exist_ok=True)
    trabajo = {
        "nombre": "web",
        "origen": str(origen),
        "destino": str(tmp_path / "destino"),
        "copias": 3,
    }
    trabajo.update(cambios)
    return trabajo


def test_trabajo_valido(tmp_path):
    assert config.validar_trabajo(_trabajo(tmp_path)) == []


def test_rechaza_raiz_y_carpeta_personal(tmp_path):
    assert config.validar_trabajo(_trabajo(tmp_path, origen="/"))
    assert config.validar_trabajo(_trabajo(tmp_path, origen=str(Path.home())))
    assert config.validar_trabajo(_trabajo(tmp_path, destino="/"))


def test_rechaza_nombre_y_copias_invalidos(tmp_path):
    assert config.validar_trabajo(_trabajo(tmp_path, nombre=""))
    assert config.validar_trabajo(_trabajo(tmp_path, nombre="mi web!"))
    assert config.validar_trabajo(_trabajo(tmp_path, copias=0))
    assert config.validar_trabajo(_trabajo(tmp_path, copias="abc"))


def test_rechaza_destino_dentro_del_origen(tmp_path):
    trabajo = _trabajo(tmp_path)
    trabajo["destino"] = str(Path(trabajo["origen"]) / "respaldos")
    assert config.validar_trabajo(trabajo)


def test_guardar_y_cargar(tmp_path):
    ruta = tmp_path / "datos" / "trabajos.json"
    trabajos = [_trabajo(tmp_path)]
    config.guardar_trabajos(trabajos, ruta)
    assert config.cargar_trabajos(ruta) == trabajos


def test_cargar_archivo_inexistente_o_danado(tmp_path):
    assert config.cargar_trabajos(tmp_path / "no_existe.json") == []
    roto = tmp_path / "roto.json"
    roto.write_text("{esto no es json", encoding="utf-8")
    assert config.cargar_trabajos(roto) == []


def test_agregar_guarda_y_rechaza_nombre_duplicado(tmp_path):
    ruta = tmp_path / "trabajos.json"
    trabajos = []
    assert config.agregar_trabajo(trabajos, _trabajo(tmp_path), ruta=ruta) == []
    assert len(config.cargar_trabajos(ruta)) == 1
    errores = config.agregar_trabajo(trabajos, _trabajo(tmp_path), ruta=ruta)
    assert "Ya existe un trabajo con ese nombre." in errores
    assert len(config.cargar_trabajos(ruta)) == 1
