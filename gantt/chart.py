from __future__ import annotations

from datetime import date, timedelta

from PyQt6.QtCore import QPointF, QRect, QRectF, QSize, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QCursor, QFont, QFontMetrics, QPainter, QWheelEvent
from PyQt6.QtWidgets import QWidget

from .models import Project

LABEL_W = 230
HEADER_MONTH_H = 26
HEADER_DAY_H = 28
HEADER_H = HEADER_MONTH_H + HEADER_DAY_H
ROW_H = 36
PAD_DER = 16
PAD_INF = 10
HANDLE = 7

MESES = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]


def _month_add(y: int, m: int, delta: int) -> tuple[int, int]:
    idx = (y * 12 + (m - 1)) + delta
    return idx // 12, idx % 12 + 1


class GanttChart(QWidget):
    taskSelected = pyqtSignal(object)
    requestEdit = pyqtSignal(int)
    tasksEdited = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.project: Project | None = None
        self.day_width = 26.0
        self.selected_id: int | None = None
        self._origin = date(2000, 1, 1)
        self._days = 1
        self._drag: dict | None = None
        self.setMouseTracking(True)
        self.setMinimumSize(LABEL_W + 160, 220)

    def set_project(self, project: Project) -> None:
        self.project = project
        self.selected_id = None
        self.sync_size()
        self.update()

    def sync_size(self) -> None:
        self.updateGeometry()
        self.resize(self.sizeHint().expandedTo(self.minimumSizeHint()))

    def zoom_in(self) -> None:
        self._set_zoom(self.day_width * 1.25)

    def zoom_out(self) -> None:
        self._set_zoom(self.day_width / 1.25)

    def fit_to_width(self, viewport_width: int) -> None:
        if self.project is None:
            return
        self._recalc_span()
        dias = max(7, self._days)
        disponible = max(80, viewport_width - LABEL_W - 20)
        self._set_zoom(disponible / dias)

    def _set_zoom(self, valor: float) -> None:
        self.day_width = min(80.0, max(2.0, valor))
        self.sync_size()
        self.update()

    def sizeHint(self) -> QSize:
        self._recalc_span()
        return QSize(int(LABEL_W + self._days * self.day_width + PAD_DER), HEADER_H + len(self.project.tasks) * ROW_H + PAD_INF)

    def minimumSizeHint(self) -> QSize:
        return QSize(LABEL_W + 160, HEADER_H + ROW_H + PAD_INF)

    def _recalc_span(self) -> None:
        hoy = date.today()
        bordes = self.project.bounds() if self.project else None
        inicio = bordes[0] if bordes else hoy
        fin = bordes[1] if bordes else hoy
        self._origin = min(inicio - timedelta(days=3), hoy - timedelta(days=3))
        self._days = max(14, (fin - self._origin).days + 5)

    def _x(self, d: date) -> float:
        return LABEL_W + (d - self._origin).days * self.day_width

    def _date_at(self, x: float) -> date:
        return self._origin + timedelta(days=round((x - LABEL_W) / self.day_width))

    def _bar_rect(self, index: int, task) -> QRectF:
        x0 = self._x(task.start)
        x1 = self._x(task.end) + self.day_width
        y = HEADER_H + index * ROW_H + (ROW_H - 18) / 2
        return QRectF(x0, y, max(3.0, x1 - x0), 18)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        self._recalc_span()
        ancho = LABEL_W + self._days * self.day_width + PAD_DER
        alto = HEADER_H + (len(self.project.tasks) if self.project else 0) * ROW_H + PAD_INF

        painter.fillRect(self.rect(), QColor("#ffffff"))
        self._pintar_cuadricula(painter, ancho, alto)
        self._pintar_cabecera(painter)
        if self.project:
            self._pintar_filas(painter)
        painter.end()

    def _pintar_cuadricula(self, p: QPainter, ancho: float, alto: float) -> None:
        p.fillRect(QRectF(0, 0, LABEL_W, alto), QColor("#f8f9fb"))
        p.fillRect(QRectF(0, 0, ancho, HEADER_H), QColor("#2f3640"))

        if self.day_width >= 8:
            fin_semana = True
        else:
            fin_semana = False

        d = self._origin
        while d <= self._origin + timedelta(days=self._days):
            x = self._x(d)
            if fin_semana and d.weekday() >= 5:
                p.fillRect(QRectF(x, HEADER_H, self.day_width, alto - HEADER_H), QColor("#eef0f3"))
            if self.day_width >= 3:
                p.setPen(QColor("#e3e6ea"))
                p.drawLine(QPointF(x, HEADER_H), QPointF(x, alto))
            elif d.day == 1:
                p.setPen(QColor("#c6ccd4"))
                p.drawLine(QPointF(x, HEADER_H), QPointF(x, alto))
            d += timedelta(days=1)

        p.setPen(QColor("#dfe3e8"))
        if self.project:
            for i in range(len(self.project.tasks) + 1):
                y = HEADER_H + i * ROW_H
                p.drawLine(QPointF(0, y), QPointF(ancho, y))

        hoy = date.today()
        if self._origin <= hoy <= self._origin + timedelta(days=self._days):
            x = self._x(hoy) + self.day_width / 2
            p.setPen(QColor("#e74c3c"))
            p.drawLine(QPointF(x, 0), QPointF(x, alto))
            tri = [QPointF(x - 5, 0), QPointF(x + 5, 0), QPointF(x, 8)]
            p.setBrush(QColor("#e74c3c"))
            p.drawPolygon(*tri)

        p.setPen(QColor("#c9ced6"))
        p.drawLine(QPointF(LABEL_W - 1, 0), QPointF(LABEL_W - 1, alto))
        p.drawLine(QPointF(0, HEADER_H - 1), QPointF(ancho, HEADER_H - 1))

    def _pintar_cabecera(self, p: QPainter) -> None:
        p.setPen(QColor("#ffffff"))
        fuente = QFont(self.font())
        fuente.setBold(True)
        p.setFont(fuente)
        fm_mes = QFontMetrics(fuente)

        y, m = self._origin.year, self._origin.month
        for _ in range(80):
            primer = date(y, m, 1)
            ny, nm = _month_add(y, m, 1)
            ultimo = date(ny, nm, 1) - timedelta(days=1)
            x0 = self._x(max(primer, self._origin))
            x1 = self._x(min(ultimo, self._origin + timedelta(days=self._days))) + self.day_width
            if x1 > LABEL_W and x0 < LABEL_W + self._days * self.day_width:
                rect = QRectF(x0, 0, x1 - x0, HEADER_MONTH_H)
                nombre = f"{MESES[m-1]} {y}"
                if fm_mes.horizontalAdvance(nombre) > rect.width():
                    nombre = MESES[m-1][:3]
                if fm_mes.horizontalAdvance(nombre) <= rect.width():
                    p.drawText(rect, Qt.AlignmentFlag.AlignCenter, nombre)
                p.setPen(QColor("#4a5568"))
                p.drawLine(QPointF(x0, 0), QPointF(x0, HEADER_MONTH_H))
                p.setPen(QColor("#ffffff"))
            y, m = ny, nm
            if date(y, m, 1) > self._origin + timedelta(days=self._days):
                break

        p.setFont(self.font())
        p.setPen(QColor("#c9d1d9"))
        for rect, texto in self._etiquetas_dias():
            p.drawText(rect, Qt.AlignmentFlag.AlignCenter, texto)

    def _etiquetas_dias(self) -> list:
        dw = self.day_width
        fm = QFontMetrics(self.font())
        w_num = fm.horizontalAdvance("30") + 8
        w_sem = fm.horizontalAdvance("S52") + 8
        opciones = [
            (1, "num", 1 * dw, w_num),
            (2, "num", 2 * dw, w_num),
            (3, "num", 3 * dw, w_num),
            (5, "num", 5 * dw, w_num),
            (7, "sem", 7 * dw, w_sem),
            (14, "sem", 14 * dw, w_sem),
            (30, "medio", 15 * dw, w_num),
            (60, "primero", 30 * dw, w_num),
        ]
        step = kind = ancho_slot = None
        for st, kd, slot, w in opciones:
            if slot >= w:
                step, kind, ancho_slot = st, kd, slot
                break
        if kind is None:
            return []

        etiquetas = []
        ult_x_fin = -1.0
        d = self._origin
        fin = self._origin + timedelta(days=self._days)
        while d <= fin:
            dibujar, texto = False, ""
            if kind == "num":
                dibujar = step == 1 or d.day % step == 1
                texto = str(d.day)
            elif kind == "sem":
                dibujar = d.weekday() == 0
                texto = f"S{d.isocalendar()[1]}"
            elif kind == "medio":
                dibujar = d.day in (1, 15)
                texto = str(d.day)
            else:
                dibujar = d.day == 1
                texto = str(d.day)
            if dibujar:
                x = self._x(d)
                if x >= ult_x_fin - 0.01:
                    rect = QRectF(x, HEADER_MONTH_H, ancho_slot, HEADER_DAY_H)
                    etiquetas.append((rect, texto))
                    ult_x_fin = rect.right()
            d += timedelta(days=1)
        return etiquetas

    def _pintar_filas(self, p: QPainter) -> None:
        fm = QFontMetrics(self.font())
        for i, task in enumerate(self.project.tasks):
            y = HEADER_H + i * ROW_H
            if task.id == self.selected_id:
                p.fillRect(QRectF(0, y, LABEL_W + self._days * self.day_width + PAD_DER, ROW_H), QColor("#dce9fd"))
            elif i % 2 == 1:
                p.fillRect(QRectF(0, y, LABEL_W + self._days * self.day_width + PAD_DER, ROW_H), QColor("#fafbfc"))

            rect_barra = self._bar_rect(i, task)
            color = QColor(task.color)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(color.lighter(160))
            radio = min(6.0, rect_barra.height() / 2)
            p.drawRoundedRect(rect_barra, radio, radio)

            avance = QRectF(rect_barra)
            avance.setWidth(rect_barra.width() * task.progress / 100)
            p.setBrush(color)
            p.drawRoundedRect(avance, radio, radio)

            if task.id == self.selected_id:
                p.setPen(QColor("#1d4ed8"))
                p.setBrush(Qt.BrushStyle.NoBrush)
                p.drawRoundedRect(rect_barra.adjusted(-1.5, -1.5, 1.5, 1.5), radio + 1, radio + 1)
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(QColor("#1d4ed8"))
                for x in (rect_barra.left(), rect_barra.right() - HANDLE + 2):
                    p.drawRect(QRectF(x, rect_barra.top() + 4, HANDLE - 2, rect_barra.height() - 8))

            texto = fm.elidedText(task.name, Qt.TextElideMode.ElideRight, LABEL_W - 14)
            p.setPen(QColor("#1f2733"))
            p.drawText(QRectF(10, y, LABEL_W - 14, ROW_H), Qt.AlignmentFlag.AlignVCenter, texto)

        if not self.project.tasks:
            p.setPen(QColor("#8a93a0"))
            p.drawText(QRectF(0, HEADER_H, LABEL_W + 400, 60), Qt.AlignmentFlag.AlignCenter, "Sin tareas. Usa «Añadir tarea» para comenzar.")

    def _hit(self, pos) -> tuple[str, int | None]:
        if pos.y() < HEADER_H or self.project is None:
            return "nada", None
        i = int((pos.y() - HEADER_H) // ROW_H)
        if i >= len(self.project.tasks):
            return "nada", None
        task = self.project.tasks[i]
        if pos.x() < LABEL_W:
            return "etiqueta", task.id
        rect = self._bar_rect(i, task)
        if rect.contains(QPointF(pos)):
            if abs(pos.x() - rect.left()) <= HANDLE:
                return "borde_ini", task.id
            if abs(pos.x() - rect.right()) <= HANDLE:
                return "borde_fin", task.id
            return "barra", task.id
        return "fila", task.id

    def mousePressEvent(self, event) -> None:
        if self.project is None or event.button() != Qt.MouseButton.LeftButton:
            return
        zona, tid = self._hit(event.position())
        self.selected_id = tid if zona != "nada" else None
        self.taskSelected.emit(self.selected_id)
        if zona in ("barra", "borde_ini", "borde_fin") and tid is not None:
            task = self.project.get_task(tid)
            self._drag = {
                "zona": zona, "id": tid, "px": event.position().x(),
                "inicio": task.start, "dur": task.duration,
            }
        self.update()

    def mouseMoveEvent(self, event) -> None:
        pos = event.position()
        if self._drag is None:
            zona, _ = self._hit(pos)
            formas = {"barra": Qt.CursorShape.SizeAllCursor, "borde_ini": Qt.CursorShape.SizeHorCursor, "borde_fin": Qt.CursorShape.SizeHorCursor}
            self.setCursor(QCursor(formas.get(zona, Qt.CursorShape.ArrowCursor)))
            return
        delta = round((pos.x() - self._drag["px"]) / self.day_width)
        task = self.project.get_task(self._drag["id"])
        if task is None:
            return
        if self._drag["zona"] == "barra":
            task.start = self._drag["inicio"] + timedelta(days=delta)
        elif self._drag["zona"] == "borde_ini":
            nuevo = self._drag["inicio"] + timedelta(days=delta)
            fin = self._drag["inicio"] + timedelta(days=self._drag["dur"] - 1)
            nuevo = min(nuevo, fin)
            task.start = nuevo
            task.duration = (fin - nuevo).days + 1
        else:
            fin = self._drag["inicio"] + timedelta(days=self._drag["dur"] - 1) + timedelta(days=delta)
            task.duration = max(1, (fin - task.start).days + 1)
        self.tasksEdited.emit()
        self.update()

    def mouseReleaseEvent(self, event) -> None:
        if self._drag is not None:
            self._drag = None
            self.sync_size()
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event) -> None:
        zona, tid = self._hit(event.position())
        if tid is not None and zona in ("barra", "etiqueta", "borde_ini", "borde_fin"):
            self.requestEdit.emit(tid)
        super().mouseDoubleClickEvent(event)

    def wheelEvent(self, event: QWheelEvent) -> None:
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
            self._set_zoom(self.day_width * factor)
            event.accept()
        else:
            event.ignore()
