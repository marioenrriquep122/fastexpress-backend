"""
Plugin de pytest usado por ejecutar_qa.py.

Guarda, por cada prueba: archivo, nombre, marcadores (caja_negra, caja_blanca, api),
resultado, duracion y mensaje de error. Lo escribe en un JSON que luego se
convierte en el reporte HTML. No cambia como se ejecutan las pruebas.
"""

import json
import os

_resultados = {}


def pytest_collection_modifyitems(items):
    for item in items:
        _resultados[item.nodeid] = {
            "nodeid": item.nodeid,
            "archivo": item.nodeid.split("::")[0],
            "nombre": item.nodeid.split("::", 1)[-1],
            "marcadores": sorted({m.name for m in item.iter_markers()} & {"caja_negra", "caja_blanca", "api"}),
            "docstring": (getattr(item.obj, "__doc__", None) or "").strip().splitlines()[0:1],
            "resultado": "no ejecutada",
            "duracion": 0.0,
            "mensaje": "",
        }


def pytest_runtest_logreport(report):
    r = _resultados.get(report.nodeid)
    if r is None:
        return
    r["duracion"] += report.duration
    if report.when == "call" or (report.when == "setup" and report.outcome != "passed"):
        if hasattr(report, "wasxfail"):
            r["resultado"] = "xfail" if report.skipped else "xpass"
            r["mensaje"] = report.wasxfail
        else:
            r["resultado"] = {"passed": "aprobada", "failed": "fallida", "skipped": "omitida"}[report.outcome]
            if report.failed:
                r["mensaje"] = str(report.longrepr)[-1500:]


def pytest_sessionfinish(session):
    destino = os.environ.get("QA_RESULTADOS_JSON")
    if destino:
        with open(destino, "w", encoding="utf-8") as f:
            json.dump(list(_resultados.values()), f, ensure_ascii=False, indent=1)
