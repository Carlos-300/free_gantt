from __future__ import annotations

import os
import tempfile
from datetime import date, timedelta
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QKeySequence
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QToolBar,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from .chart import HEADER_H, ROW_H, GanttChart
from .dialogs import TaskDialog
from .drawio import save_drawio
from .models import PALETA, Project, sample_project

Filtro = "Proyecto Gantt (*.gantt.json);;Todos los archivos (*)"


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.project = sample_project(date.today())
        self.file_path: Path | None = None
        self._sync_tabla = False

        self.chart = GanttChart()
        self.chart.set_project(self.project)
        self.chart.taskSelected.connect(self._seleccion_desde_chart)
        self.chart.tasksEdited.connect(self._marcar_sucio)
        self.chart.requestEdit.connect(self._editar_tarea)

        self.scroll = QScrollArea()
        self.scroll.setWidget(self.chart)
        self.scroll.setWidgetResizable(False)

        self._crear_panel_tareas()
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self.panel_tareas)
        splitter.addWidget(self._crear_panel_carta())
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)
        splitter.setChildrenCollapsible(False)
        self.setCentralWidget(splitter)

        self._crear_toolbar()
        self._crear_estado()
        self._actualizar_todo()

        self.resize(1440, 760)
        splitter.setSizes([540, 900])

    def _crear_panel_tareas(self) -> None:
        self.tabla = QTableWidget(0, 6)
        self.tabla.setHorizontalHeaderLabels(["Tarea", "Responsable", "Inicio", "Fin", "Duración", "Progreso"])
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.verticalHeader().setDefaultSectionSize(30)
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for col in range(1, 6):
            self.tabla.horizontalHeader().setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
        self.tabla.cellDoubleClicked.connect(lambda *_: self._editar_tarea(self.chart.selected_id))
        self.tabla.currentCellChanged.connect(self._seleccion_desde_tabla)

        btn_add = QPushButton("Añadir tarea")
        btn_add.clicked.connect(self._anadir_tarea)
        btn_edit = QPushButton("Editar")
        btn_edit.clicked.connect(lambda *_: self._editar_tarea(self.chart.selected_id))
        btn_del = QPushButton("Eliminar")
        btn_del.clicked.connect(self._eliminar_tarea)

        botones = QHBoxLayout()
        botones.addWidget(btn_add)
        botones.addWidget(btn_edit)
        botones.addWidget(btn_del)
        botones.addStretch(1)
        for texto, delta, atajo in (("▲ Subir", -1, "Alt+Up"), ("▼ Bajar", 1, "Alt+Down")):
            botones.addWidget(self._boton_accion(texto, lambda *_, d=delta: self._mover_tarea(d), atajo))

        layout = QVBoxLayout()
        layout.setContentsMargins(4, 4, 4, 4)
        layout.addLayout(botones)
        layout.addWidget(self.tabla)

        self.panel_tareas = QWidget()
        self.panel_tareas.setLayout(layout)
        self.panel_tareas.setMinimumWidth(480)

    def _boton_accion(self, texto, slot, atajo) -> QToolButton:
        # The action lives on the window so its shortcut works regardless of focus.
        act = QAction(texto, self)
        act.triggered.connect(slot)
        act.setShortcut(QKeySequence(atajo))
        act.setToolTip(f"{texto} ({atajo})")
        self.addAction(act)
        boton = QToolButton()
        boton.setDefaultAction(act)
        return boton

    def _crear_panel_carta(self) -> QWidget:
        barra = QHBoxLayout()
        barra.addWidget(QLabel("Vista de la carta:"))
        for texto, slot, atajo in (
            ("Zoom −", self.chart.zoom_out, "Ctrl+-"),
            ("Zoom +", self.chart.zoom_in, "Ctrl++"),
            ("Ajustar", self._ajustar, "Ctrl+0"),
        ):
            barra.addWidget(self._boton_accion(texto, slot, atajo))
        barra.addStretch(1)

        layout = QVBoxLayout()
        layout.setContentsMargins(4, 4, 4, 4)
        layout.addLayout(barra)
        layout.addWidget(self.scroll)
        panel = QWidget()
        panel.setLayout(layout)
        return panel

    def _mover_tarea(self, delta: int) -> None:
        tarea = self.project.get_task(self.chart.selected_id)
        if tarea is None:
            return
        i = self.project.tasks.index(tarea)
        j = i + delta
        if not 0 <= j < len(self.project.tasks):
            return
        tareas = self.project.tasks
        tareas[i], tareas[j] = tareas[j], tareas[i]
        self._marcar_sucio()
        self._centrar_en_tarea(tarea.id)

    def _crear_toolbar(self) -> None:
        tb = QToolBar("Principal")
        tb.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        tb.setMovable(False)
        self.addToolBar(tb)

        def accion(texto, slot, atajo=None):
            act = QAction(texto, self)
            act.triggered.connect(slot)
            if atajo:
                act.setShortcut(QKeySequence(atajo))
            tb.addAction(act)
            return act

        accion("Nuevo", self._nuevo, "Ctrl+N")
        accion("Abrir…", self._abrir, "Ctrl+O")

        btn_guardar = QToolButton()
        btn_guardar.setText("Guardar ▾")
        btn_guardar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        btn_guardar.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        menu_guardar = QMenu(btn_guardar)
        for texto, slot, atajo in (
            ("Guardar proyecto", self._guardar, "Ctrl+S"),
            ("Guardar proyecto como…", self._guardar_como, "Ctrl+Shift+S"),
            ("Guardar como Excel…", self._exportar_excel, None),
            ("Guardar como Excel nativo…", self._exportar_excel_nativo, None),
            ("Guardar como PNG…", self._exportar_png, None),
            ("Guardar como draw.io…", self._exportar_drawio, None),
        ):
            act = QAction(texto, self)
            act.triggered.connect(slot)
            if atajo:
                act.setShortcut(QKeySequence(atajo))
                self.addAction(act)
            menu_guardar.addAction(act)
            if texto == "Guardar proyecto como…":
                menu_guardar.addSeparator()
        btn_guardar.setMenu(menu_guardar)
        tb.addWidget(btn_guardar)

    def _crear_estado(self) -> None:
        self.status = QLabel("")
        self.statusBar().addPermanentWidget(self.status)
        ayuda = QLabel("Doble clic = editar · Arrastrar barra = mover · Bordes = redimensionar · Ctrl+rueda = zoom")
        self.statusBar().addWidget(ayuda)

    def _actualizar_todo(self) -> None:
        self.chart.sync_size()
        self.chart.update()
        self._refrescar_tabla()
        modificado = " *" if self.isWindowModified() else ""
        nombre_archivo = str(self.file_path) if self.file_path else "sin guardar"
        self.setWindowTitle(f"Carta Gantt — {self.project.name}{modificado}")
        self.status.setText(f"{len(self.project.tasks)} tareas · {nombre_archivo}")

    def _refrescar_tabla(self) -> None:
        self._sync_tabla = True
        self.tabla.setRowCount(len(self.project.tasks))
        for i, t in enumerate(self.project.tasks):
            valores = [
                t.name,
                t.responsible,
                t.start.strftime("%d/%m/%Y"),
                t.end.strftime("%d/%m/%Y"),
                f"{t.duration} d",
                f"{t.progress} %",
            ]
            for j, valor in enumerate(valores):
                item = QTableWidgetItem(valor)
                if j == 0:
                    item.setData(Qt.ItemDataRole.UserRole, t.id)
                self.tabla.setItem(i, j, item)
            if t.id == self.chart.selected_id:
                self.tabla.selectRow(i)
        self._sync_tabla = False

    def _marcar_sucio(self) -> None:
        self.setWindowModified(True)
        self.chart.sync_size()
        self.chart.update()
        self._refrescar_tabla()
        self.status.setText(f"{len(self.project.tasks)} tareas · {self.file_path or 'sin guardar'}")

    def _centrar_en_tarea(self, tid: int) -> None:
        tarea = self.project.get_task(tid)
        if tarea is None:
            return
        try:
            indice = self.project.tasks.index(tarea)
        except ValueError:
            return
        x = int(self.chart._x(tarea.start) + self.chart.day_width * tarea.duration / 2)
        y = int(HEADER_H + indice * ROW_H + ROW_H / 2)
        ancho_vp = self.scroll.viewport().width()
        alto_vp = self.scroll.viewport().height()
        self.scroll.horizontalScrollBar().setValue(max(0, x - ancho_vp // 2))
        self.scroll.verticalScrollBar().setValue(max(0, y - alto_vp // 2))

    def _seleccion_desde_chart(self, tid) -> None:
        if self._sync_tabla:
            return
        self._sync_tabla = True
        if tid is None:
            self.tabla.clearSelection()
            self.tabla.setCurrentCell(-1, -1)
        else:
            for i in range(self.tabla.rowCount()):
                item = self.tabla.item(i, 0)
                if item and item.data(Qt.ItemDataRole.UserRole) == tid:
                    self.tabla.selectRow(i)
                    break
        self._sync_tabla = False

    def _seleccion_desde_tabla(self, fila: int, _col: int, _prev_f: int, _prev_c: int) -> None:
        if self._sync_tabla or fila < 0:
            return
        item = self.tabla.item(fila, 0)
        if item:
            self.chart.selected_id = item.data(Qt.ItemDataRole.UserRole)
            self.chart.update()

    def _anadir_tarea(self) -> None:
        if self.project.tasks:
            ultimo = max(t.end for t in self.project.tasks)
            inicio_defecto = ultimo + timedelta(days=1)
        else:
            inicio_defecto = date.today()
        provisional = self.project.add_task(
            name="", start=inicio_defecto, duration=5, color=PALETA[len(self.project.tasks) % len(PALETA)]
        )
        dialogo = TaskDialog(self, provisional)
        if dialogo.exec():
            valores = dialogo.values()
            provisional.name = valores["name"]
            provisional.start = valores["start"]
            provisional.duration = valores["duration"]
            provisional.progress = valores["progress"]
            provisional.color = valores["color"]
            provisional.responsible = valores["responsible"]
            self.chart.selected_id = provisional.id
            self._marcar_sucio()
            self._centrar_en_tarea(provisional.id)
        else:
            self.project.remove_task(provisional.id)

    def _editar_tarea(self, tid) -> None:
        if tid is None:
            return
        tarea = self.project.get_task(tid)
        if tarea is None:
            return
        dialogo = TaskDialog(self, tarea)
        if dialogo.exec():
            valores = dialogo.values()
            tarea.name = valores["name"]
            tarea.start = valores["start"]
            tarea.duration = valores["duration"]
            tarea.progress = valores["progress"]
            tarea.color = valores["color"]
            tarea.responsible = valores["responsible"]
            self._marcar_sucio()
            self._centrar_en_tarea(tarea.id)

    def _eliminar_tarea(self) -> None:
        tid = self.chart.selected_id
        if tid is None:
            return
        tarea = self.project.get_task(tid)
        if tarea is None:
            return
        if QMessageBox.question(self, "Eliminar tarea", f"¿Eliminar «{tarea.name}»?") != QMessageBox.StandardButton.Yes:
            return
        self.project.remove_task(tid)
        self.chart.selected_id = None
        self._marcar_sucio()

    def _ajustar(self) -> None:
        self.chart.fit_to_width(self.scroll.viewport().width())
        self.scroll.horizontalScrollBar().setValue(0)

    def _nuevo(self) -> None:
        if not self._confirmar_perder_cambios():
            return
        self.project = Project("Proyecto sin nombre")
        self.file_path = None
        self.chart.set_project(self.project)
        self.setWindowModified(False)
        self._actualizar_todo()
        self._anadir_tarea()

    def _abrir(self) -> None:
        if not self._confirmar_perder_cambios():
            return
        ruta, _ = QFileDialog.getOpenFileName(self, "Abrir proyecto", "", Filtro)
        if not ruta:
            return
        try:
            self.project = Project.load(ruta)
        except Exception as exc:
            QMessageBox.critical(self, "Error al abrir", f"No se pudo leer el archivo:\n{exc}")
            return
        self.file_path = Path(ruta)
        self.chart.set_project(self.project)
        self.setWindowModified(False)
        self._actualizar_todo()

    def _guardar(self) -> bool:
        if self.file_path is None:
            return self._guardar_como()
        self.project.save(self.file_path)
        self.setWindowModified(False)
        self._actualizar_todo()
        return True

    def _guardar_como(self) -> bool:
        ruta, _ = QFileDialog.getSaveFileName(self, "Guardar proyecto", "proyecto.gantt.json", Filtro)
        if not ruta:
            return False
        if not ruta.endswith(".gantt.json"):
            ruta += ".gantt.json"
        self.file_path = Path(ruta)
        return self._guardar()

    def _exportar_excel_nativo(self) -> None:
        try:
            import openpyxl  # noqa: F401
        except ImportError:
            QMessageBox.warning(
                self,
                "Falta dependencia",
                "Para exportar a Excel instala openpyxl con:\n.venv\\Scripts\\pip install openpyxl",
            )
            return
        ruta, _ = QFileDialog.getSaveFileName(self, "Guardar como Excel nativo", "carta_gantt.xlsx", "Libro de Excel (*.xlsx)")
        if not ruta:
            return
        if not ruta.lower().endswith(".xlsx"):
            ruta += ".xlsx"
        if not self._guardar_excel_nativo(ruta):
            QMessageBox.critical(self, "Error", "No se pudo exportar el archivo de Excel.")

    def _guardar_excel_nativo(self, ruta: str) -> bool:
        try:
            from openpyxl import Workbook
            from openpyxl.chart import BarChart, Reference
            from openpyxl.chart.series import DataPoint
            from openpyxl.chart.shapes import GraphicalProperties
            from openpyxl.drawing.line import LineProperties
            from openpyxl.styles import Alignment, Font, PatternFill

            wb = Workbook()
            ws = wb.active
            ws.title = "Carta Gantt"
            ws.append([f"Proyecto: {self.project.name}"])
            ws["A1"].font = Font(bold=True)
            ws.append([])
            ws.append(["Tarea", "Inicio", "Fin", "Duración (días)", "Progreso (%)", "Inicio (días)", "Hecho (días)", "Restante (días)", "Responsable"])
            for celda in ws[3]:
                celda.font = Font(bold=True, color="FFFFFF")
                celda.fill = PatternFill("solid", fgColor="2F3640")
                celda.alignment = Alignment(horizontal="center")

            inicio_proj = min((t.start for t in self.project.tasks), default=date.today())
            epoch = date(1899, 12, 30)  # Excel date serial origin
            filas = []
            for t in self.project.tasks:
                hecho = round(t.duration * t.progress / 100)
                filas.append((t, (t.start - epoch).days, hecho, t.duration - hecho))
            for t, offset, hecho, resto in filas:
                ws.append([t.name, t.start, t.end, t.duration, t.progress, offset, hecho, resto, t.responsible])
                fila = ws.max_row
                ws.cell(row=fila, column=2).number_format = "DD/MM/YYYY"
                ws.cell(row=fila, column=3).number_format = "DD/MM/YYYY"
                for col in (4, 5, 6, 7, 8):
                    ws.cell(row=fila, column=col).alignment = Alignment(horizontal="center")
            for col, ancho in zip("ABCDEFGHI", (36, 13, 13, 15, 13, 13, 12, 14, 24)):
                ws.column_dimensions[col].width = ancho
            for col in "FGH":
                ws.column_dimensions[col].hidden = True

            n = len(self.project.tasks)
            if n:
                chart = BarChart()
                chart.type = "bar"
                chart.grouping = "stacked"
                chart.overlap = 100
                chart.gapWidth = 30
                chart.title = self.project.name
                chart.legend = None

                ref_cat = Reference(ws, min_col=1, min_row=4, max_row=3 + n)
                chart.add_data(Reference(ws, min_col=6, min_row=3, max_row=3 + n), titles_from_data=True)
                chart.add_data(Reference(ws, min_col=7, min_row=3, max_row=3 + n), titles_from_data=True)
                chart.add_data(Reference(ws, min_col=8, min_row=3, max_row=3 + n), titles_from_data=True)
                chart.set_categories(ref_cat)

                serie_offset, serie_hecho, serie_resto = chart.series
                serie_offset.graphicalProperties = GraphicalProperties(
                    noFill=True, ln=LineProperties(noFill=True)
                )
                from PyQt6.QtGui import QColor
                from openpyxl.chart.data_source import (
                    AxDataSource, NumData, NumVal, StrData, StrRef, StrVal,
                )

                serie_hecho.data_points = [
                    DataPoint(idx=i, spPr=GraphicalProperties(solidFill=QColor(t.color).darker(140).name().lstrip("#")))
                    for i, t in enumerate(self.project.tasks)
                ]
                serie_resto.data_points = [
                    DataPoint(idx=i, spPr=GraphicalProperties(solidFill=QColor(t.color).lighter(165).name().lstrip("#")))
                    for i, t in enumerate(self.project.tasks)
                ]
                chart.visible_cells_only = False

                cat_f = f"'{ws.title}'!$A$4:$A${3 + n}"
                nombres = [t.name for t in self.project.tasks]
                columnas = [[offset for _, offset, _, _ in filas],
                            [hecho for _, _, hecho, _ in filas],
                            [resto for _, _, _, resto in filas]]
                for s, valores in zip(chart.series, columnas):
                    s.cat = AxDataSource(
                        strRef=StrRef(
                            f=cat_f,
                            strCache=StrData(
                                ptCount=n,
                                pt=[StrVal(idx=i, v=nombre) for i, nombre in enumerate(nombres)],
                            ),
                        )
                    )
                    s.val.numRef.numCache = NumData(
                        formatCode="General",
                        ptCount=n,
                        pt=[NumVal(idx=i, v=valor) for i, valor in enumerate(valores)],
                    )

                fin_proj = max((t.end for t in self.project.tasks), default=inicio_proj) + timedelta(days=5)
                chart.x_axis.scaling.orientation = "maxMin"
                chart.x_axis.axPos = "l"
                chart.y_axis.axPos = "b"
                chart.y_axis.scaling.min = (inicio_proj - epoch).days
                chart.y_axis.scaling.max = (fin_proj - epoch).days
                # openpyxl >= 3.1 hides axes unless delete is explicitly False
                chart.x_axis.delete = False
                chart.y_axis.delete = False
                # keep date axis at the bottom despite reversed task order
                chart.y_axis.crosses = "max"
                chart.y_axis.number_format = "dd-mmm-yy"
                span = (fin_proj - inicio_proj).days
                for paso in (1, 2, 7, 14, 30, 60, 90, 180, 365):
                    if span / paso <= 12:
                        chart.y_axis.majorUnit = paso
                        break
                chart.width = 24
                chart.height = max(8, min(30, n * 0.8))
                ws.add_chart(chart, "K3")
            wb.save(ruta)
            return True
        except Exception:
            return False

    def _exportar_png(self) -> None:
        ruta, _ = QFileDialog.getSaveFileName(self, "Exportar como PNG", "carta_gantt.png", "Imagen PNG (*.png)")
        if not ruta:
            return
        if not ruta.lower().endswith(".png"):
            ruta += ".png"
        if not self._guardar_png(ruta):
            QMessageBox.critical(self, "Error", "No se pudo exportar la imagen.")

    def _exportar_drawio(self) -> None:
        ruta, _ = QFileDialog.getSaveFileName(self, "Guardar como draw.io", "carta_gantt.drawio", "Diagrama draw.io (*.drawio)")
        if not ruta:
            return
        if not ruta.lower().endswith(".drawio"):
            ruta += ".drawio"
        try:
            save_drawio(self.project, ruta)
        except OSError as exc:
            QMessageBox.critical(self, "Error", f"No se pudo guardar el archivo draw.io:\n{exc}")

    def _guardar_png(self, ruta: str) -> bool:
        return self.chart.grab().save(ruta, "PNG")

    def _exportar_excel(self) -> None:
        try:
            import openpyxl  # noqa: F401
        except ImportError:
            QMessageBox.warning(
                self,
                "Falta dependencia",
                "Para exportar a Excel instala openpyxl con:\n.venv\\Scripts\\pip install openpyxl",
            )
            return
        ruta, _ = QFileDialog.getSaveFileName(self, "Exportar como Excel", "carta_gantt.xlsx", "Libro de Excel (*.xlsx)")
        if not ruta:
            return
        if not ruta.lower().endswith(".xlsx"):
            ruta += ".xlsx"
        if not self._guardar_excel(ruta):
            QMessageBox.critical(self, "Error", "No se pudo exportar el archivo de Excel.")

    def _guardar_excel(self, ruta: str) -> bool:
        try:
            from openpyxl import Workbook
            from openpyxl.styles import Alignment, Font, PatternFill

            wb = Workbook()
            ws = wb.active
            ws.title = "Carta Gantt"
            ws.append([f"Proyecto: {self.project.name}"])
            ws["A1"].font = Font(bold=True)
            ws.append([])
            ws.append(["Tarea", "Inicio", "Fin", "Duración (días)", "Progreso (%)", "Responsable"])
            for celda in ws[3]:
                celda.font = Font(bold=True, color="FFFFFF")
                celda.fill = PatternFill("solid", fgColor="2F3640")
                celda.alignment = Alignment(horizontal="center")
            for t in self.project.tasks:
                ws.append([t.name, t.start, t.end, t.duration, t.progress, t.responsible])
                fila = ws.max_row
                ws.cell(row=fila, column=2).number_format = "DD/MM/YYYY"
                ws.cell(row=fila, column=3).number_format = "DD/MM/YYYY"
                for col in (4, 5):
                    ws.cell(row=fila, column=col).alignment = Alignment(horizontal="center")
            for col, ancho in zip("ABCDEF", (36, 13, 13, 15, 13, 24)):
                ws.column_dimensions[col].width = ancho

            ws.cell(row=ws.max_row + 2, column=1, value="Carta Gantt").font = Font(bold=True)
            fila_img = ws.max_row + 1
            fd, tmp_png = tempfile.mkstemp(suffix=".png")
            os.close(fd)
            try:
                if self.chart.grab().save(tmp_png, "PNG"):
                    from openpyxl.drawing.image import Image as XLImage

                    ws.add_image(XLImage(tmp_png), f"A{fila_img}")
                wb.save(ruta)
            finally:
                os.unlink(tmp_png)
            return True
        except Exception:
            return False

    def _confirmar_perder_cambios(self) -> bool:
        if not self.isWindowModified():
            return True
        resp = QMessageBox.question(
            self,
            "Cambios sin guardar",
            "Hay cambios sin guardar. ¿Quieres guardarlos antes?",
            QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel,
        )
        if resp == QMessageBox.StandardButton.Save:
            return self._guardar()
        return resp == QMessageBox.StandardButton.Discard

    def closeEvent(self, event) -> None:
        if self._confirmar_perder_cambios():
            event.accept()
        else:
            event.ignore()
