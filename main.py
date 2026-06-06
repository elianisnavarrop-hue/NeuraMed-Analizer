import sys
import os
from PyQt5.QtWidgets import QApplication

# Matplotlib configuration for PyQt5
os.environ["QT_API"] = "PyQt5"
import matplotlib
matplotlib.use('Qt5Agg')

from view.views import (
    BienvenidaWindow, 
    LoginWindow, 
    VentanaAutenticacion, 
    MainWindow, 
    VentanaZoom
)
from controller.controller import BioMonitorController


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')   # Modern look

    controller = BioMonitorController()
    controller.run()   # Starts with BienvenidaWindow

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()