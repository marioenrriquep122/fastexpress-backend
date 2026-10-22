"""
Ejecuta TODA la suite de pruebas y genera un reporte visual de QA.

Uso (desde la raiz del repo, con el .venv activo):
    python informes-pruebas/ejecutar_qa.py

Genera:
    informes-pruebas/reporte/reporte_qa.html   <- abrir en el navegador
    informes-pruebas/reporte/resultados.json    (datos crudos por prueba)
    informes-pruebas/reporte/coverage.json      (cobertura linea a linea)
    htmlcov/index.html                          (reporte de coverage.py)

El script NO decide si el sistema esta bien: muestra la evidencia y evalua los
criterios de salida definidos abajo (CRITERIOS). Revisarlos es tarea de QA.
"""

import html
import json
import os
import re
import subprocess
import sys
import webbrowser
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CARPETA = Path(__file__).resolve().parent
SALIDA = CARPETA / "reporte"
ARCHIVO_CORE = "principal/modulos/cotizaciones/services/calculadora_service.py"

# Criterios de salida (exit criteria) del plan de pruebas
MIN_COBERTURA_LINEAS = 85.0
MIN_COBERTURA_RAMAS = 85.0
CAMINOS_CFG = 9  # V(G) de calcular_cotizacion


def ejecutar_pytest():
    SALIDA.mkdir(exist_ok=True)
    env = dict(os.environ)
    env["QA_RESULTADOS_JSON"] = str(SALIDA / "resultados.json")
    env["PYTHONPATH"] = os.pathsep.join([str(CARPETA), str(RAIZ), env.get("PYTHONPATH", "")])
    cmd = [
        sys.executable, "-m", "pytest", "-p", "qa_plugin", "-q",
        f"--cov-report=json:{SALIDA / 'coverage.json'}",
    ]
    print("Ejecutando:", " ".join(cmd))
    inicio = datetime.now()
    proc = subprocess.run(cmd, cwd=RAIZ, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace")
    duracion = (datetime.now() - inicio).total_seconds()
    (SALIDA / "salida_pytest.txt").write_text(proc.stdout + proc.stderr, encoding="utf-8")
    print(proc.stdout.strip().splitlines()[-1] if proc.stdout.strip() else proc.stderr)
    return duracion


def cargar():
    pruebas = json.loads((SALIDA / "resultados.json").read_text(encoding="utf-8"))
    cov = json.loads((SALIDA / "coverage.json").read_text(encoding="utf-8"))
    archivos = {k.replace("\\", "/"): v for k, v in cov["files"].items()}
    return pruebas, cov, archivos


def id_caso(p):
    """Saca el ID legible: QA-01, BVA-02, TD-03, C4... del nombre o de los parametros."""
    m = re.search(r"\[(.*?)\]$", p["nombre"])
    if m:
        ident = re.match(r"([A-Z]+-[A-Z0-9]+)", m.group(1))
        return ident.group(1) if ident else m.group(1)[:40]
    m = re.search(r"test_(C\d|QA_\d+)", p["nombre"])
    if m:
        return m.group(1).replace("_", "-")
    return ""


def esc(s):
    return html.escape(str(s))


BADGE = {
    "aprobada": ("ok", "Aprobada"),
    "fallida": ("bad", "Fallida"),
    "xfail": ("warn", "Defecto conocido"),
    "xpass": ("bad", "XPASS (revisar)"),
    "omitida": ("muted", "Omitida"),
    "no ejecutada": ("muted", "No ejecutada"),
}


def fila(p):
    clase, texto = BADGE[p["resultado"]]
    detalle = f"<div class='msg'>{esc(p['mensaje'])}</div>" if p["mensaje"] else ""
    return (
        f"<tr data-estado='{p['resultado']}'><td class='id'>{esc(id_caso(p))}</td>"
        f"<td><code>{esc(p['nombre'])}</code><div class='file'>{esc(p['archivo'])}</div>{detalle}</td>"
        f"<td>{', '.join(p['marcadores']) or '—'}</td>"
        f"<td><span class='badge {clase}'>{texto}</span></td>"
        f"<td class='num'>{p['duracion'] * 1000:.0f} ms</td></tr>"
    )


def tabla(pruebas, vacio="Sin pruebas en esta categoría."):
    if not pruebas:
        return f"<p class='muted'>{vacio}</p>"
    filas = "".join(fila(p) for p in pruebas)
    return (
        "<div class='scroll'><table><thead><tr><th>ID</th><th>Prueba</th><th>Marcadores</th>"
        f"<th>Resultado</th><th>Tiempo</th></tr></thead><tbody>{filas}</tbody></table></div>"
    )


def codigo_core(archivos):
    datos = archivos.get(ARCHIVO_CORE)
    ruta = RAIZ / ARCHIVO_CORE
    if not datos or not ruta.exists():
        return "<p class='muted'>No se encontró la cobertura del archivo core.</p>"
    ejecutadas = set(datos["executed_lines"])
    faltantes = set(datos["missing_lines"])
    lineas = []
    for n, txt in enumerate(ruta.read_text(encoding="utf-8").splitlines(), 1):
        clase = "hit" if n in ejecutadas else "miss" if n in faltantes else ""
        txt = esc(txt)
        txt = re.sub(r"(\[N\d+\])", r"<span class='node'>\1</span>", txt)
        lineas.append(f"<div class='ln {clase}'><span class='n'>{n}</span>{txt or ' '}</div>")
    return "<div class='code'>" + "".join(lineas) + "</div>"


def barras_cobertura(archivos):
    filas = []
    for ruta, d in sorted(archivos.items(), key=lambda kv: kv[1]["summary"]["percent_covered"]):
        s = d["summary"]
        pct = s["percent_covered"]
        lin = f"{s['covered_lines']}/{s['num_statements']}"
        ram = f"{s.get('covered_branches', 0)}/{s.get('num_branches', 0)}"
        faltan = ", ".join(map(str, d["missing_lines"])) or "—"
        clase = "ok" if pct >= MIN_COBERTURA_LINEAS else "bad"
        filas.append(
            f"<tr><td><code>{esc(ruta)}</code></td><td class='num'>{lin}</td><td class='num'>{ram}</td>"
            f"<td><div class='bar'><div class='fill {clase}' style='width:{pct:.1f}%'></div></div></td>"
            f"<td class='num'>{pct:.1f} %</td><td class='num'>{esc(faltan)}</td></tr>"
        )
    return (
        "<div class='scroll'><table><thead><tr><th>Archivo</th><th>Líneas</th><th>Ramas</th><th></th>"
        f"<th>Total</th><th>Líneas sin cubrir</th></tr></thead><tbody>{''.join(filas)}</tbody></table></div>"
    )


def generar_html(pruebas, cov, archivos, duracion):
    t = cov["totals"]
    cob_lineas = 100.0 * t["covered_lines"] / t["num_statements"] if t["num_statements"] else 0
    cob_ramas = 100.0 * t["covered_branches"] / t["num_branches"] if t.get("num_branches") else 100.0
    cuenta = {k: sum(1 for p in pruebas if p["resultado"] == k) for k in BADGE}
    caminos = [p for p in pruebas if re.search(r"test_C\d_", p["nombre"])]
    caminos_ok = sum(1 for p in caminos if p["resultado"] == "aprobada")
    defectos = [p for p in pruebas if p["resultado"] in ("xfail", "xpass")]

    criterios = [
        ("Ninguna prueba fallida", cuenta["fallida"] == 0, f"{cuenta['fallida']} fallidas"),
        ("Ningún defecto corregido sin cerrar (XPASS)", cuenta["xpass"] == 0, f"{cuenta['xpass']} en XPASS"),
        (f"Cobertura de líneas ≥ {MIN_COBERTURA_LINEAS:.0f} %", cob_lineas >= MIN_COBERTURA_LINEAS, f"{cob_lineas:.2f} %"),
        (f"Cobertura de ramas ≥ {MIN_COBERTURA_RAMAS:.0f} %", cob_ramas >= MIN_COBERTURA_RAMAS, f"{cob_ramas:.2f} %"),
        (f"Los {CAMINOS_CFG} caminos independientes del CFG ejecutados", caminos_ok == CAMINOS_CFG, f"{caminos_ok}/{CAMINOS_CFG}"),
    ]
    aprobado = all(c[1] for c in criterios)
    lista_criterios = "".join(
        f"<li class='{'ok' if okc else 'bad'}'><span>{'✔' if okc else '✘'}</span> {esc(n)} <b>{esc(v)}</b></li>"
        for n, okc, v in criterios
    )

    def por(marca):
        return [p for p in pruebas if marca in p["marcadores"]]

    otras = [p for p in pruebas if not p["marcadores"]]

    kpis = [
        ("Pruebas", len(pruebas), ""),
        ("Aprobadas", cuenta["aprobada"], "ok"),
        ("Fallidas", cuenta["fallida"], "bad" if cuenta["fallida"] else ""),
        ("Defectos conocidos", cuenta["xfail"], "warn" if cuenta["xfail"] else ""),
        ("Cobertura líneas", f"{cob_lineas:.1f} %", "ok" if cob_lineas >= MIN_COBERTURA_LINEAS else "bad"),
        ("Cobertura ramas", f"{cob_ramas:.1f} %", "ok" if cob_ramas >= MIN_COBERTURA_RAMAS else "bad"),
    ]
    kpi_html = "".join(f"<div class='kpi {c}'><div class='v'>{esc(v)}</div><div class='l'>{esc(l)}</div></div>" for l, v, c in kpis)

    return f"""<!doctype html><html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Reporte QA FastExpress</title>
<style>
:root{{--bg:#f7f7f5;--card:#fff;--tx:#1d1d1b;--mu:#6b6b66;--bd:#e3e3de;--ok:#1f8a4c;--bad:#c4382b;--warn:#b7791f;--ac:#2a6fdb;--hit:#e6f4ea;--miss:#fbe7e5}}
@media (prefers-color-scheme:dark){{:root{{--bg:#161615;--card:#1f1f1d;--tx:#ecece8;--mu:#a0a09a;--bd:#33332f;--hit:#16301f;--miss:#3a1d1a}}}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--tx);font:14px/1.5 system-ui,Segoe UI,sans-serif}}
main{{max-width:1200px;margin:auto;padding:24px 16px}}h1{{font-size:22px;margin:0}}h2{{font-size:17px;margin:0 0 4px}}
.muted,.sub{{color:var(--mu)}}section{{background:var(--card);border:1px solid var(--bd);border-radius:10px;padding:18px;margin:16px 0}}
.kpis{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin-top:16px}}
.kpi{{background:var(--card);border:1px solid var(--bd);border-radius:10px;padding:12px}}.kpi .v{{font-size:24px;font-weight:650}}.kpi .l{{color:var(--mu);font-size:12px}}
.kpi.ok .v,.ok>span{{color:var(--ok)}}.kpi.bad .v,.bad>span{{color:var(--bad)}}.kpi.warn .v{{color:var(--warn)}}
.veredicto{{font-size:16px;font-weight:650;padding:10px 14px;border-radius:8px;display:inline-block;margin-bottom:10px}}
.veredicto.ok{{background:var(--hit);color:var(--ok)}}.veredicto.bad{{background:var(--miss);color:var(--bad)}}
ul.crit{{list-style:none;padding:0;margin:0}}ul.crit li{{padding:4px 0}}ul.crit span{{font-weight:700;margin-right:6px}}
.scroll{{overflow-x:auto}}table{{border-collapse:collapse;width:100%;font-size:13px}}th,td{{text-align:left;padding:7px 8px;border-bottom:1px solid var(--bd);vertical-align:top}}
th{{color:var(--mu);font-weight:600;font-size:12px}}.num{{text-align:right;white-space:nowrap}}.id{{font-weight:650;white-space:nowrap}}
.file{{color:var(--mu);font-size:11.5px}}.msg{{margin-top:4px;font-size:12px;white-space:pre-wrap;color:var(--warn)}}
.badge{{padding:2px 8px;border-radius:99px;font-size:12px;font-weight:600;white-space:nowrap}}
.badge.ok{{background:var(--hit);color:var(--ok)}}.badge.bad{{background:var(--miss);color:var(--bad)}}.badge.warn{{background:#fdf3e1;color:var(--warn)}}.badge.muted{{color:var(--mu)}}
.bar{{background:var(--bd);height:8px;border-radius:4px;min-width:120px}}.fill{{height:8px;border-radius:4px}}.fill.ok{{background:var(--ok)}}.fill.bad{{background:var(--bad)}}
.code{{font:12px/1.45 ui-monospace,Consolas,monospace;border:1px solid var(--bd);border-radius:8px;overflow-x:auto;max-height:620px}}
.ln{{white-space:pre;padding-right:12px}}.ln .n{{display:inline-block;width:42px;text-align:right;padding-right:10px;color:var(--mu);user-select:none}}
.ln.hit{{background:var(--hit)}}.ln.miss{{background:var(--miss)}}.node{{background:var(--ac);color:#fff;border-radius:4px;padding:0 4px}}
.leyenda span{{display:inline-block;padding:1px 8px;border-radius:4px;margin-right:8px;font-size:12px}}
nav{{display:flex;flex-wrap:wrap;gap:8px;margin-top:14px}}nav a{{color:var(--ac);text-decoration:none;font-size:13px}}
input{{width:100%;padding:8px;border:1px solid var(--bd);border-radius:6px;background:var(--bg);color:var(--tx);margin-bottom:8px}}
</style></head><body><main>
<h1>Reporte de QA — Cotizador FastExpress</h1>
<div class="sub">Generado {datetime.now():%Y-%m-%d %H:%M} · Python {sys.version.split()[0]} · ejecución de {duracion:.1f} s</div>
<div class="kpis">{kpi_html}</div>
<nav><a href="#gate">Criterios de salida</a>·<a href="#negra">Caja negra</a>·<a href="#blanca">Caja blanca</a>·<a href="#api">API</a>·<a href="#defectos">Defectos</a>·<a href="#cobertura">Cobertura</a>·<a href="#todas">Todas</a></nav>

<section id="gate"><h2>1. Criterios de salida</h2>
<p class="sub">Lo que un QA revisa antes de decir "se puede entregar". Si uno falla, hay que investigar antes de aprobar.</p>
<div class="veredicto {'ok' if aprobado else 'bad'}">{'APTO para entregar' if aprobado else 'NO APTO: revisar los criterios en rojo'}</div>
<ul class="crit">{lista_criterios}</ul></section>

<section id="negra"><h2>2. Caja negra — {len(por('caja_negra'))} pruebas</h2>
<p class="sub">Diseñadas solo desde las reglas BR-01 a BR-04: Particiones de Equivalencia (PE), Valores Límite (BVA), Tabla de Decisión (TD) y casos QA. Verifica que para cada entrada el total esperado coincida con el obtenido.</p>
{tabla(por('caja_negra'))}</section>

<section id="blanca"><h2>3. Caja blanca — caminos del CFG ({caminos_ok}/{CAMINOS_CFG})</h2>
<p class="sub">V(G) = 9 ⇒ se necesitan 9 caminos independientes (C1–C9). Abajo, el código real de <code>calcular_cotizacion</code> pintado por la cobertura: verde = se ejecutó durante las pruebas, rojo = nunca se ejecutó. Los marcadores azules <span class="node">[N1]</span> son los nodos del grafo.</p>
{tabla(por('caja_blanca'))}
<p class="leyenda" style="margin-top:14px"><span style="background:var(--hit)">línea ejecutada</span><span style="background:var(--miss)">línea sin ejecutar</span><span class="node">[Nx] nodo CFG</span></p>
{codigo_core(archivos)}</section>

<section id="api"><h2>4. Integración API — {len(por('api'))} pruebas</h2>
<p class="sub">Peticiones HTTP reales contra los endpoints: códigos de estado, formato de error y que los errores no guarden datos.</p>
{tabla(por('api'))}</section>

<section id="defectos"><h2>5. Defectos conocidos — {len(defectos)}</h2>
<p class="sub">Pruebas marcadas como <code>xfail(strict=True)</code>: demuestran un defecto abierto. Si el backend lo corrige, la prueba pasa a XPASS y el criterio de salida se pone en rojo para que QA cierre el defecto.</p>
{tabla(defectos, 'No hay defectos abiertos.')}</section>

<section id="cobertura"><h2>6. Cobertura de código</h2>
<p class="sub">Total: {t['covered_lines']}/{t['num_statements']} líneas y {t.get('covered_branches', 0)}/{t.get('num_branches', 0)} ramas. Detalle navegable en <code>htmlcov/index.html</code>.</p>
{barras_cobertura(archivos)}</section>

<section id="todas"><h2>7. Todas las pruebas — {len(pruebas)}</h2>
<input id="f" placeholder="Filtrar por nombre, ID o archivo…">
{tabla(otras + [p for p in pruebas if p['marcadores']])}</section>
</main><script>
document.getElementById('f').addEventListener('input',e=>{{const q=e.target.value.toLowerCase();
document.querySelectorAll('#todas tbody tr').forEach(r=>r.style.display=r.textContent.toLowerCase().includes(q)?'':'none');}});
</script></body></html>"""


def main():
    duracion = ejecutar_pytest()
    pruebas, cov, archivos = cargar()
    destino = SALIDA / "reporte_qa.html"
    destino.write_text(generar_html(pruebas, cov, archivos, duracion), encoding="utf-8")
    print(f"\nReporte generado: {destino}")
    if "--no-abrir" not in sys.argv:
        webbrowser.open(destino.as_uri())


if __name__ == "__main__":
    main()
