"""
Vistas - NeuraMed Analizer
"""

import os
os.environ["QT_API"] = "PyQt5"

import matplotlib
matplotlib.use('Qt5Agg')

from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtWidgets import QVBoxLayout

from PyQt5 import uic
from PyQt5.QtWidgets import (
    QMainWindow, QMessageBox, QFileDialog, QPushButton, 
    QLabel, QTableWidget, QLineEdit
)
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt
import numpy as np
import cv2


class BienvenidaWindow(QMainWindow):
    def __init__(self, controller):
        super().__init__()
        uic.loadUi("view/ventana_bienvenida.ui", self)
        self.controller = controller
        
        # Connect button (use the real name from your .ui)
        if hasattr(self, 'btn_ingreso_sistema'):
            self.btn_ingreso_sistema.clicked.connect(self.controller.mostrar_login)
        elif hasattr(self, 'btnIngresar'):
            self.btnIngresar.clicked.connect(self.controller.mostrar_login)


class LoginWindow(QMainWindow):
    def __init__(self, controller):
        super().__init__()
        uic.loadUi("view/ventana_login.ui", self)
        self.controller = controller
        if hasattr(self, 'btn_ingresar_info'):
            self.btn_ingresar_info.clicked.connect(self.attempt_login)

    def attempt_login(self):
        username = self.txtusuario.text().strip() if hasattr(self, 'txtusuario') else ""
        password = self.txtpassword.text().strip() if hasattr(self, 'txtpassword') else ""
        
        if not username or not password:
            QMessageBox.warning(self, "Error", "Usuario y contraseña son obligatorios.")
            return
        self.controller.validar_login(username, password)


class VentanaAutenticacion(QMainWindow):
    def __init__(self, controller):
        super().__init__()
        uic.loadUi("view/ventana_autenticador.ui", self)
        self.controller = controller
        
        if hasattr(self, 'boton_guardar_foto'):
            self.boton_guardar_foto.clicked.connect(self.capturar_foto)

    def capturar_foto(self):
        QMessageBox.information(self, "Info", "Foto capturada (simulado)")
        self.close()
        self.controller.abrir_ventana_principal()


class MainWindow(QMainWindow):
    def __init__(self, controller):
        super().__init__()
        uic.loadUi("view/ventana_principal.ui", self)
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)

        layout = QVBoxLayout(self.widget_4)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.canvas)
        self.controller = controller
        self._encontrar_widgets()
        self._conectar_botones()

    def _encontrar_widgets(self):
        # Use findChild to avoid crashes
        self.boton_imagenes = self.findChild(QPushButton, "boton_imagenes")
        self.boton_senales = self.findChild(QPushButton, "boton_senales")
        self.boton_datos = self.findChild(QPushButton, "boton_datos")

        self.btn_cargar_dicom = self.findChild(QPushButton, "btn_cargar_dicom")
        self.btn_cargar_nifti = self.findChild(QPushButton, "btn_cargar_nifti")
        self.btn_zoom = self.findChild(QPushButton, "btn_zoom")
        self.btn_aplicar_transformacion = self.findChild(QPushButton, "btn_aplicar_transformacion")

        self.label_axial = self.findChild(QLabel, "label_axial")
        self.label_coronal = self.findChild(QLabel, "label_coronal")
        self.label_sagital = self.findChild(QLabel, "label_sagital")

    def _conectar_botones(self):
        if self.boton_imagenes:
            self.boton_imagenes.clicked.connect(self.controller.mostrar_modulo_imagenes)
        if self.boton_senales:
            self.boton_senales.clicked.connect(self.controller.mostrar_modulo_senales)
        if self.boton_datos:
            self.boton_datos.clicked.connect(self.controller.mostrar_modulo_datos)
        if self.btn_cargar_dicom:
            self.btn_cargar_dicom.clicked.connect(self.controller.cargar_carpeta_dicom)
        if self.btn_zoom:
            self.btn_zoom.clicked.connect(self.controller.abrir_ventana_zoom)

    def show_3_planes(self, axial, coronal, sagittal):
        if axial is not None and self.label_axial:
            self.label_axial.setPixmap(self._numpy_to_qpixmap(axial))
        if coronal is not None and self.label_coronal:
            self.label_coronal.setPixmap(self._numpy_to_qpixmap(coronal))
        if sagittal is not None and self.label_sagital:
            self.label_sagital.setPixmap(self._numpy_to_qpixmap(sagittal))

    def _numpy_to_qpixmap(self, img):
        img_u8 = cv2.normalize(img.astype(np.float32), None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
        h, w = img_u8.shape
        qimg = QImage(img_u8.data, w, h, w, QImage.Format_Grayscale8)
        return QPixmap.fromImage(qimg)


class VentanaZoom(QMainWindow):
    def __init__(self, dicom_model):
        super().__init__()
        uic.loadUi("view/ventana_zoom.ui", self)
        self.dicom_model = dicom_model

        self.btn_aplicar_zoom = self.findChild(QPushButton, "btn_aplicar_zoom")
        self.btn_guardar_img = self.findChild(QPushButton, "btn_guardar_img")
        self.nombre_archivo = self.findChild(QLineEdit, "nombre_archivo")

        if self.btn_aplicar_zoom:
            self.btn_aplicar_zoom.clicked.connect(self.aplicar_zoom)
        if self.btn_guardar_img:
            self.btn_guardar_img.clicked.connect(self.guardar_imagen)

    def mostrar_imagen(self, corte):
        try:
            img_u8 = self.dicom_model.normalizar_uint8(corte)
            img_bgr = cv2.cvtColor(img_u8, cv2.COLOR_GRAY2BGR)
            h, w = img_bgr.shape[:2]
            qimg = QImage(img_bgr.data, w, h, w*3, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(qimg)
            # Assuming you have a QLabel called widget_2 or label_imagen
            label = self.findChild(QLabel, "widget_2") or self.findChild(QLabel, "label_imagen")
            if label:
                label.setPixmap(pixmap.scaled(label.size(), Qt.AspectRatioMode.KeepAspectRatio))
        except Exception as e:
            print("Error mostrando imagen:", e)

    def aplicar_zoom(self):
        QMessageBox.information(self, "Info", "Zoom aplicado (simulado)")

    def guardar_imagen(self):
        nombre = self.nombre_archivo.text().strip() or "recorte"
        QMessageBox.information(self, "Guardado", f"Imagen guardada como: {nombre}.png")