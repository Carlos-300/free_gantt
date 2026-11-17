import sys

from PyQt6.QtWidgets import QApplication

from gantt.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Carta Gantt")
    app.setOrganizationName("proyectos")
    ventana = MainWindow()
    ventana.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
