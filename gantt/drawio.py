"""Export a Project as an uncompressed draw.io (diagrams.net) XML file."""
from __future__ import annotations

import html
import xml.etree.ElementTree as ET
from datetime import timedelta
from pathlib import Path

from .models import Project, Task

LABEL_W = 280
DAY_W = 24
ROW_H = 36
TITLE_H = 36
MONTH_H = 26
DAY_H = 28
BAR_PAD = 8

MESES = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]


def task_label(task: Task) -> str:
    return f"{task.name} [{task.responsible}]" if task.responsible else task.name


def _lighten(color: str, amount: float = 0.6) -> str:
    """Mix a #rrggbb color with white; amount=1 gives white."""
    r, g, b = (int(color.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4))
    return "#" + "".join(f"{round(c + (255 - c) * amount):02x}" for c in (r, g, b))


def to_drawio(project: Project) -> str:
    bounds = project.bounds()
    dias = (bounds[1] - bounds[0]).days + 1 if bounds else 0
    ancho_total = LABEL_W + dias * DAY_W
    alto_total = TITLE_H + MONTH_H + DAY_H + len(project.tasks) * ROW_H

    # Layout mirrors files saved by app.diagrams.net, which the web app opens reliably.
    mxfile = ET.Element("mxfile", host="app.diagrams.net")
    diagram = ET.SubElement(mxfile, "diagram", name="Carta Gantt", id="gantt")
    model = ET.SubElement(
        diagram, "mxGraphModel", dx="1200", dy="800", grid="1", gridSize="10", guides="1",
        tooltips="1", connect="1", arrows="1", fold="1", page="1", pageScale="1",
        pageWidth=str(max(1100, ancho_total + 40)), pageHeight=str(max(850, alto_total + 40)),
        math="0", shadow="0",
    )
    root = ET.SubElement(model, "root")
    ET.SubElement(root, "mxCell", id="0")
    ET.SubElement(root, "mxCell", id="1", parent="0")
    ids = iter(range(2, 1_000_000))

    def cell(value: str, style: str, x: float, y: float, w: float, h: float) -> None:
        # html=1 makes draw.io render value as HTML, so user text must be HTML-escaped.
        c = ET.SubElement(root, "mxCell", id=str(next(ids)), parent="1",
                          style=style + "html=1;whiteSpace=wrap;", value=html.escape(value, quote=False), vertex="1")
        ET.SubElement(c, "mxGeometry", x=_num(x), y=_num(y), width=_num(w), height=_num(h), **{"as": "geometry"})

    cell(project.name, "text;strokeColor=none;fillColor=none;fontSize=18;fontStyle=1;align=left;verticalAlign=middle;", 0, 0, LABEL_W + 400, TITLE_H)

    if bounds is None:
        return _serializar(mxfile)
    inicio, fin = bounds
    y_mes = TITLE_H
    y_dia = y_mes + MONTH_H
    y_filas = y_dia + DAY_H
    cabecera = "strokeColor=#d0d5dd;fontSize=11;"

    cell("Tarea [Responsable]", f"{cabecera}fillColor=#2f3640;fontColor=#ffffff;fontStyle=1;align=left;spacingLeft=8;",
         0, y_mes, LABEL_W, MONTH_H + DAY_H)

    # Month band: one cell per (partial) month in range.
    d = inicio
    while d <= fin:
        siguiente = (d.replace(day=28) + timedelta(days=4)).replace(day=1)
        hasta = min(siguiente - timedelta(days=1), fin)
        n = (hasta - d).days + 1
        cell(f"{MESES[d.month - 1]} {d.year}", f"{cabecera}fillColor=#eef1f5;fontStyle=1;",
             LABEL_W + (d - inicio).days * DAY_W, y_mes, n * DAY_W, MONTH_H)
        d = hasta + timedelta(days=1)

    for i in range(dias):
        dia = inicio + timedelta(days=i)
        fondo = "#e4e7ec" if dia.weekday() >= 5 else "#ffffff"
        cell(str(dia.day), f"{cabecera}fillColor={fondo};", LABEL_W + i * DAY_W, y_dia, DAY_W, DAY_H)

    for fila, t in enumerate(project.tasks):
        y = y_filas + fila * ROW_H
        fondo = "#fafbfc" if fila % 2 else "#ffffff"
        cell("", f"strokeColor=#eef1f5;fillColor={fondo};", 0, y, LABEL_W + dias * DAY_W, ROW_H)
        cell(task_label(t), "text;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;spacingLeft=8;fontSize=12;",
             0, y, LABEL_W, ROW_H)
        x = LABEL_W + (t.start - inicio).days * DAY_W
        ancho = t.duration * DAY_W
        barra = "rounded=1;arcSize=20;strokeColor=none;fontSize=11;"
        alto = ROW_H - 2 * BAR_PAD
        cell("", f"{barra}fillColor={_lighten(t.color)};", x, y + BAR_PAD, ancho, alto)
        if t.progress:
            cell("", f"{barra}fillColor={t.color};", x, y + BAR_PAD, ancho * t.progress / 100, alto)
        cell(f"{t.progress} %", "text;strokeColor=none;fillColor=none;align=center;verticalAlign=middle;fontSize=11;", x, y + BAR_PAD, ancho, alto)

    return _serializar(mxfile)


def _num(v: float) -> str:
    return str(int(v)) if float(v).is_integer() else f"{v:.1f}"


def _serializar(mxfile: ET.Element) -> str:
    ET.indent(mxfile, space="  ")
    return ET.tostring(mxfile, encoding="unicode") + "\n"


def save_drawio(project: Project, path: str | Path) -> None:
    Path(path).write_text(to_drawio(project), encoding="utf-8")
