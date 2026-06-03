#Punto de entrada de la aplicación
#Arranca NeuraMed Analyzer

import sys
from PyQt5.QtWidgets import QApplication
from controller.ctrl_login import CtrlBienvenida


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # La primera ventana es la de bienvenida
    ventana = CtrlBienvenida()
    ventana.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()