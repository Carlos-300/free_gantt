# Carta Gantt

Aplicación de escritorio para crear y gestionar cartas Gantt, desarrollada con **Python + PyQt6**. Sin dependencias de navegador ni de servidor: es una ventana nativa de Windows.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![PyQt6](https://img.shields.io/badge/PyQt6-GUI-green)

## Características

- **CRUD de tareas**: nombre, responsable, inicio, fin, progreso (%) y color.
- **Edición directa sobre el gráfico**:
  - Arrastrar una barra para mover la tarea.
  - Arrastrar los bordes para redimensionarla.
  - Doble clic sobre una barra (o su nombre) para editarla.
- **Tabla de tareas** sincronizada con el gráfico (selección en ambos sentidos).
- **Orden de tareas**: botones «▲ Subir» / «▼ Bajar»; el orden se guarda en el proyecto y se respeta en todas las exportaciones.
- **Zoom y navegación**: barra «Vista de la carta» sobre las fechas con Zoom −/+ y Ajustar (solo afectan a la carta), además de Ctrl + rueda del mouse.
- **Carta real**: cabecera de fechas adaptativa al zoom (días → semanas → meses), fines de semana sombreados y línea de "hoy".
- **Persistencia**: guardar/cargar proyectos en JSON (`.gantt.json`).
- **Exportaciones**:
  - PNG (imagen idéntica a la app).
  - Excel con imagen (`.xlsx` con la tabla + la carta embebida).
  - **Excel nativo**: gráfico de barras apiladas editable dentro de Excel, con eje de fechas y avance por segmento oscuro/claro.
  - **draw.io** (`.drawio`, XML): carta editable en [diagrams.net](https://app.diagrams.net/) (Archivo → Abrir desde → Dispositivo).
- El responsable de cada tarea aparece en la carta como `Tarea [Responsable]` (también en PNG y draw.io).

## Requisitos

- Python 3.10 o superior (probado en 3.13 y 3.14).
- Dependencias (`requirements.txt`): PyQt6 (interfaz), openpyxl (Excel) y Pillow (imagen dentro del Excel). La exportación a draw.io no requiere dependencias extra.
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

O doble clic en **`run.bat`** (Windows; requiere haber creado `.venv` como se indica arriba).

## Pruebas

```bash
python -m unittest discover tests
```

## Uso

| Acción | Cómo |
|---|---|
| Añadir tarea | Botón «Añadir tarea» del panel Tareas (Ctrl+T) |
| Editar | Doble clic en la barra o botón «Editar» (Ctrl+E) |
| Eliminar | Botón «Eliminar» (Supr) |
| Cambiar orden | Seleccionar tarea y «▲ Subir» / «▼ Bajar» (Alt+↑ / Alt+↓) |
| Mover tarea | Arrastrar el cuerpo de la barra |
| Cambiar duración | Arrastrar el borde izquierdo o derecho de la barra |
| Zoom | Botones «Zoom −» / «Zoom +» sobre la carta (Ctrl+- / Ctrl++) o Ctrl + rueda del mouse |
| Ajustar a la ventana | Botón «Ajustar» sobre la carta (Ctrl+0) |
| Guardar proyecto | Guardar ▾ → «Guardar proyecto» (Ctrl+S) |
| Exportar | Guardar ▾ → Excel / Excel nativo / PNG / draw.io |

## Estructura del proyecto

```
main.py              Punto de entrada
run.bat              Lanzador para Windows
requirements.txt     Dependencias
gantt/
├── models.py        Modelo de datos (Task/Project) y persistencia JSON
├── chart.py         Widget de la carta Gantt: pintado, zoom e interacción
├── dialogs.py       Diálogo de nueva/edición de tarea
├── drawio.py        Exportación a draw.io (XML de diagrams.net)
└── main_window.py   Ventana principal: toolbar, tabla, guardar y exportar
tests/               Pruebas: python -m unittest discover tests
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
      "color": "#f7b04f",
      "responsible": "Ana Pérez"
    }
  ]
}
```

## Notas sobre el Excel nativo

El gráfico nativo se construye con barras horizontales apiladas (posición invisible + avance + restante) y un **eje de valores con formato de fecha** (`dd-mmm-yy`), por lo que las barras quedan posicionadas según su fecha de calendario. El responsable se exporta en una columna propia. Limitación de los gráficos de Excel: no incluye fines de semana sombreados ni línea de «hoy»; para una réplica exacta de la carta usar la exportación con imagen.

## Notas sobre draw.io

El archivo `.drawio` es XML sin comprimir, con el mismo formato que guarda diagrams.net. Incluye título, meses, días (fines de semana sombreados), `Tarea [Responsable]` y barras con su % de avance; cada elemento es editable. Es un dibujo estático: no incluye la línea de «hoy» y mover una barra en draw.io no cambia fechas en el proyecto.

## Subir a GitHub

```bash
git init
git add .
git commit -m "Carta Gantt en PyQt6"
git remote add origin https://github.com/<usuario>/<repo>.git
git push -u origin main
```
