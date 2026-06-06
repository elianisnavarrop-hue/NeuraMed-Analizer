"""
Controlador Principal - NeuraMed Analizer
"""

import random
from datetime import datetime
from pathlib import Path
from PyQt5.QtWidgets import (
    QMessageBox, QFileDialog, QMainWindow, 
    QTableWidgetItem, QWidget, QPushButton
)
from PyQt5.QtCore import Qt

from model.paciente import Paciente
from model.database import DatabaseManager
from model.modelo_dicom import ModeloDICOM
from model.signal_processor import SignalProcessor
from model.tabular_processor import TabularProcessor
from view.views import (
    BienvenidaWindow, LoginWindow, VentanaAutenticacion, 
    MainWindow, VentanaZoom
)


class BioMonitorController:
    """Controlador central"""

    def __init__(self):
        self.db = DatabaseManager()
        self.dicom_model = ModeloDICOM()
        self.signal_proc = SignalProcessor()
        self.tabular_proc = TabularProcessor()

        # Views will be created on demand
        self.bienvenida = None
        self.login_window = None
        self.autenticacion = None
        self.main_window = None
        self.zoom_window = None

    def run(self):
        """Inicia la aplicación"""
        self.bienvenida = BienvenidaWindow(self)
        self.bienvenida.show()

    # ====================== FLUJO DE VENTANAS ======================
    def mostrar_login(self):
        """Desde Bienvenida"""
        if self.login_window is None:
            self.login_window = LoginWindow(self)
        self.bienvenida.close()
        self.login_window.show()

    def validar_login(self, username: str, password: str):
        user_data = self.db.login(username, password)
        if user_data:
            self.login_window.close()
            self.mostrar_autenticacion()
        else:
            QMessageBox.warning(self.login_window, "Error", "Usuario o contraseña incorrectos.")

    def mostrar_autenticacion(self):
        if self.autenticacion is None:
            self.autenticacion = VentanaAutenticacion(self)
        self.autenticacion.show()

    def abrir_ventana_principal(self):
        if self.main_window is None:
            self.main_window = MainWindow(self)
        if self.autenticacion:
            self.autenticacion.close()
        self.main_window.show()

    # ====================== MÓDULOS ======================
    def mostrar_modulo_imagenes(self):
        if self.main_window:
            self.main_window.stackedWidget_principal.setCurrentWidget(
                self.main_window.findChild(QWidget, "vent_imagenes")
            )

    def mostrar_modulo_senales(self):
        if self.main_window:
            self.main_window.stackedWidget_principal.setCurrentWidget(
                self.main_window.findChild(QWidget, "vent_senales")
            )

    def mostrar_modulo_datos(self):
        if self.main_window:
            self.main_window.stackedWidget_principal.setCurrentWidget(
                self.main_window.findChild(QWidget, "vent_datos")
            )

    def cargar_carpeta_dicom(self):
        folder = QFileDialog.getExistingDirectory(self.main_window, "Seleccionar carpeta DICOM")
        if not folder:
            return
        try:
            self.dicom_model.cargar_dicom(folder)
            axial = self.dicom_model.get_corte_axial(self.dicom_model.volumen_3d.shape[0]//2)
            coronal = self.dicom_model.get_corte_coronal(self.dicom_model.volumen_3d.shape[1]//2)
            sagittal = self.dicom_model.get_corte_sagital(self.dicom_model.volumen_3d.shape[2]//2)

            self.main_window.show_3_planes(axial, coronal, sagittal)
            QMessageBox.information(self.main_window, "Éxito", f"DICOM cargado ({len(self.dicom_model.archivos_dcm)} slices)")
        except Exception as e:
            QMessageBox.critical(self.main_window, "Error", str(e))

    def abrir_ventana_zoom(self):
        if self.dicom_model.volumen_3d is None:
            QMessageBox.warning(self.main_window, "Advertencia", "Cargue primero una serie DICOM")
            return

        self.zoom_window = VentanaZoom(self.dicom_model)
        corte = self.dicom_model.get_corte_axial(self.dicom_model.volumen_3d.shape[0]//2)
        self.zoom_window.mostrar_imagen(corte)
        self.zoom_window.show()


    def convertir_a_nifti(self):
        if self.dicom_model.volumen_3d is None:
            QMessageBox.warning(self.main_window, "Advertencia", "Primero cargue una carpeta DICOM")
            return
        path, _ = QFileDialog.getSaveFileName(self.main_window, "Guardar NIfTI", "", "NIfTI (*.nii.gz)")
        if path:
            self.dicom_model.convertir_a_nifti(path)
            QMessageBox.information(self.main_window, "Éxito", f"NIfTI guardado en:\n{path}")


    def aplicar_transformacion(self):
        """Aplica segmentación o morfología"""
        try:
            indice = 0
            tipo = self.main_window.seleccion_segmentacion.currentText()
            kernel = self.main_window.spinkernel.value()

            if tipo != "Seleccione una opcion...":
                resultado = self.dicom_model.segmentar(indice, tipo)
                QMessageBox.information(self.main_window, "Segmentación", f"Aplicada: {tipo}")
            else:
                QMessageBox.warning(self.main_window, "Advertencia", "Seleccione un tipo de transformación")
        except Exception as e:
            QMessageBox.critical(self.main_window, "Error", str(e))

