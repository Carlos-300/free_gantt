from __future__ import annotations

from datetime import date

from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QColorDialog,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

from .models import Task


def _to_qdate(d: date) -> "QDate":
    from PyQt6.QtCore import QDate

    return QDate(d.year, d.month, d.day)


class TaskDialog(QDialog):
    def __init__(self, parent=None, task: Task | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Editar tarea" if task else "Nueva tarea")
        self.color = task.color if task else "#4f86f7"

        self.nombre = QLineEdit(task.name if task else "")
        self.nombre.setPlaceholderText("Nombre de la tarea")

        self.inicio = QDateEdit(_to_qdate(task.start) if task else _to_qdate(date.today()))
        self.fin = QDateEdit(_to_qdate(task.end) if task else _to_qdate(date.today()))
        for edit in (self.inicio, self.fin):
            edit.setCalendarPopup(True)
            edit.setDisplayFormat("dd/MM/yyyy")

        self.progreso = QSpinBox()
        self.progreso.setRange(0, 100)
        self.progreso.setSuffix(" %")
        self.progreso.setValue(task.progress if task else 0)

        self.btn_color = QPushButton()
        self.btn_color.setFixedWidth(90)
        self.btn_color.clicked.connect(self._elegir_color)
        self._mostrar_color()

        form = QFormLayout()
        form.addRow("Nombre:", self.nombre)
        form.addRow("Inicio:", self.inicio)
        form.addRow("Fin:", self.fin)
        form.addRow("Progreso:", self.progreso)
        form.addRow("Color:", self.btn_color)

        botones = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        botones.accepted.connect(self._validar)
        botones.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(botones)

    def _elegir_color(self) -> None:
        color = QColorDialog.getColor(QColor(self.color), self, "Color de la tarea")
        if color.isValid():
            self.color = color.name()
            self._mostrar_color()

    def _mostrar_color(self) -> None:
        self.btn_color.setStyleSheet(
            f"background-color: {self.color}; color: {'#000' if QColor(self.color).lightness() > 140 else '#fff'};"
        )
        self.btn_color.setText(self.color)

    def _validar(self) -> None:
        if not self.nombre.text().strip():
            self.nombre.setFocus()
            self.nombre.setPlaceholderText("¡El nombre es obligatorio!")
            return
        if self.fin.date() < self.inicio.date():
            self.fin.setFocus()
            return
        self.accept()

    def values(self) -> dict:
        ini = self.inicio.date()
        fin = self.fin.date()
        return {
            "name": self.nombre.text().strip(),
            "start": date(ini.year(), ini.month(), ini.day()),
            "duration": ini.daysTo(fin) + 1,
            "progress": self.progreso.value(),
            "color": self.color,
        }
