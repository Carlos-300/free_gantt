# Carta Gantt

Aplicación de escritorio para crear y gestionar cartas Gantt, desarrollada con **Python + PyQt6**. Sin dependencias de navegador ni de servidor: es una ventana nativa de Windows.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![PyQt6](https://img.shields.io/badge/PyQt6-GUI-green)

## Características

- **CRUD de tareas**: nombre, inicio, fin, progreso (%) y color.
- **Edición directa sobre el gráfico**:
  - Arrastrar una barra para mover la tarea.
  - Arrastrar los bordes para redimensionarla.
  - Doble clic sobre una barra (o su nombre) para editarla.
- **Tabla de tareas** sincronizada con el gráfico (selección en ambos sentidos).
- **Zoom y navegación**: Ctrl + rueda del mouse, botones Zoom +/− y Ajustar (Ctrl+0).
- **Carta real**: cabecera de fechas adaptativa al zoom (días → semanas → meses), fines de semana sombreados y línea de "hoy".
- **Persistencia**: guardar/cargar proyectos en JSON (`.gantt.json`).
- **Exportaciones**:
  - PNG (imagen idéntica a la app).
  - Excel con imagen (`.xlsx` con la tabla + la carta embebida).
  - **Excel nativo**: gráfico de barras apiladas editable dentro de Excel, con eje de fechas y avance por segmento oscuro/claro.

## Requisitos

- Python 3.10 o superior (probado en 3.13).
- Windows (incluye `run.bat`; en Linux/macOS basta ejecutar `python main.py`).

## Instalación

```bash
python -m venv .venv
.venv\Scripts\activate          # Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
```

## Ejecución

```bash
python main.py
```

O doble clic en **`run.bat`** (Windows).

## Uso

| Acción | Cómo |
|---|---|
| Añadir tarea | Botón «Añadir tarea» del panel Tareas (Ctrl+T) |
| Editar | Doble clic en la barra o botón «Editar» (Ctrl+E) |
| Eliminar | Botón «Eliminar» (Supr) |
| Mover tarea | Arrastrar el cuerpo de la barra |
| Cambiar duración | Arrastrar el borde izquierdo o derecho de la barra |
| Zoom | Ctrl + rueda del mouse |
| Ajustar a la ventana | Botón «Ajustar» (Ctrl+0) |
| Guardar proyecto | Guardar ▾ → «Guardar proyecto» (Ctrl+S) |
| Exportar | Guardar ▾ → Excel / Excel nativo / PNG |

## Estructura del proyecto

```
main.py              Punto de entrada
run.bat              Lanzador para Windows
requirements.txt     Dependencias
gantt/
├── models.py        Modelo de datos (Task/Project) y persistencia JSON
├── chart.py         Widget de la carta Gantt: pintado, zoom e interacción
├── dialogs.py       Diálogo de nueva/edición de tarea
└── main_window.py   Ventana principal: toolbar, tabla, guardar y exportar
```

## Formato de proyecto (`.gantt.json`)

```json
{
  "name": "Mi proyecto",
  "tasks": [
    {
      "id": 1,
      "name": "Diseño UX/UI",
      "start": "2026-11-15",
      "duration": 9,
      "progress": 70,
      "color": "#f7b04f"
    }
  ]
}
```

## Notas sobre el Excel nativo

El gráfico nativo se construye con barras horizontales apiladas (posición invisible + avance + restante) y un **eje de valores con formato de fecha**, por lo que las barras quedan posicionadas según su fecha de calendario. Limitación de los gráficos de Excel: no incluye fines de semana sombreados ni línea de «hoy»; para una réplica exacta de la carta usar la exportación con imagen.

## Subir a GitHub

```bash
git init
git add .
git commit -m "Carta Gantt en PyQt6"
git remote add origin https://github.com/<usuario>/<repo>.git
git push -u origin main
```
