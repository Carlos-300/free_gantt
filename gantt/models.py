from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path

FORMATO_FECHA = "%Y-%m-%d"


@dataclass
class Task:
    id: int
    name: str
    start: date
    duration: int = 1
    progress: int = 0
    color: str = "#4f86f7"

    @property
    def end(self) -> date:
        return self.start + timedelta(days=self.duration - 1)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "start": self.start.strftime(FORMATO_FECHA),
            "duration": self.duration,
            "progress": self.progress,
            "color": self.color,
        }

    @staticmethod
    def from_dict(data: dict) -> "Task":
        return Task(
            id=int(data["id"]),
            name=str(data["name"]),
            start=date.fromisoformat(data["start"]),
            duration=max(1, int(data.get("duration", 1))),
            progress=max(0, min(100, int(data.get("progress", 0)))),
            color=str(data.get("color", "#4f86f7")),
        )


@dataclass
class Project:
    name: str = "Proyecto sin nombre"
    tasks: list[Task] = field(default_factory=list)
    _next_id: int = 1

    def add_task(
        self,
        name: str,
        start: date,
        duration: int = 1,
        progress: int = 0,
        color: str = "#4f86f7",
    ) -> Task:
        task = Task(self._next_id, name, start, max(1, duration), progress, color)
        self._next_id += 1
        self.tasks.append(task)
        return task

    def get_task(self, task_id: int) -> Task | None:
        return next((t for t in self.tasks if t.id == task_id), None)

    def remove_task(self, task_id: int) -> bool:
        antes = len(self.tasks)
        self.tasks = [t for t in self.tasks if t.id != task_id]
        return len(self.tasks) < antes

    def bounds(self) -> tuple[date, date] | None:
        if not self.tasks:
            return None
        return (min(t.start for t in self.tasks), max(t.end for t in self.tasks))

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "tasks": [t.to_dict() for t in self.tasks],
        }

    @staticmethod
    def from_dict(data: dict) -> "Project":
        project = Project(name=str(data.get("name", "Proyecto sin nombre")))
        for raw in data.get("tasks", []):
            task = Task.from_dict(raw)
            project.tasks.append(task)
            project._next_id = max(project._next_id, task.id + 1)
        return project

    def save(self, path: str | Path) -> None:
        Path(path).write_text(
            json.dumps(self.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    @staticmethod
    def load(path: str | Path) -> "Project":
        return Project.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))


PALETA = [
    "#4f86f7", "#f7b04f", "#4fc26e", "#e05c5c", "#9b59b6",
    "#1abc9c", "#e67e22", "#607d8b", "#d35400", "#16a085",
]


def sample_project(today: date) -> Project:
    project = Project("Rediseño del sitio web")
    base = today - timedelta(days=7)
    datos = [
        ("Investigación y requisitos", 0, 7, 100),
        ("Diseño UX/UI", 5, 9, 70),
        ("Desarrollo frontend", 12, 12, 30),
        ("Desarrollo backend", 14, 10, 10),
        ("Pruebas QA", 24, 6, 0),
        ("Lanzamiento", 30, 2, 0),
    ]
    for i, (nombre, offset, duracion, progreso) in enumerate(datos):
        project.add_task(
            name=nombre,
            start=base + timedelta(days=offset),
            duration=duracion,
            progress=progreso,
            color=PALETA[i % len(PALETA)],
        )
    return project
