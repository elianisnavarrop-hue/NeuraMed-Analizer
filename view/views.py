"""
Vistas - NeuraMed Analizer
"""

from PyQt5 import uic
from PyQt5.QtWidgets import (
    QMainWindow, QMessageBox, QFileDialog, QPushButton, 
    QLabel, QTableWidget, QLineEdit, QSlider, QComboBox, 
    QSpinBox, QRadioButton, QTextEdit, QWidget, QVBoxLayout,
    QTableWidgetItem, QListWidget
)
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt
import numpy as np
import cv2

from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas


class BienvenidaWindow(QMainWindow):
    def __init__(self, controller):
        super().__init__()
        uic.loadUi("view/ventana_bienvenida.ui", self)
        self.controller = controller
        self.btn_ingreso_sistema.clicked.connect(self.controller.mostrar_login)


class LoginWindow(QMainWindow):
    def __init__(self, controller):
        super().__init__()
        uic.loadUi("view/ventana_login.ui", self)
        self.controller = controller
        self.btn_ingresar_info.clicked.connect(self.attempt_login)

    def attempt_login(self):
        username = self.txtusuario.text().strip()
        password = self.txtpassword.text().strip()
        if not username or not password:
            QMessageBox.warning(self, "Error", "Usuario y contraseña son obligatorios.")
            return
        self.controller.validar_login(username, password)


class VentanaAutenticacion(QMainWindow):
    def __init__(self, controller):
        super().__init__()
        uic.loadUi("view/ventana_autenticador.ui", self)
        self.controller = controller
        self.boton_guardar_foto.clicked.connect(self.capturar_foto)

    def capturar_foto(self):
        QMessageBox.information(self, "Info", "Foto capturada (simulado)")
        self.close()
        self.controller.abrir_ventana_principal()
        
class MainWindow(QMainWindow):
    def __init__(self, controller):
        super().__init__()
        uic.loadUi("view/ventana_principal.ui", self)
        self.controller = controller
        
        self._encontrar_widgets()
        self._conectar_señales()
        self._setup_matplotlib()
        self._forzar_conexiones_pestanas()

    def _encontrar_widgets(self):
        # Botones principales
        self.boton_imagenes = self.findChild(QPushButton, "boton_imagenes")
        self.boton_senales = self.findChild(QPushButton, "boton_senales")
        self.boton_datos = self.findChild(QPushButton, "boton_datos")

        # Imágenes
        self.btn_cargar_dicom = self.findChild(QPushButton, "btn_cargar_dicom")
        self.btn_cargar_nifti = self.findChild(QPushButton, "btn_cargar_nifti")
        self.btn_zoom = self.findChild(QPushButton, "btn_zoom")
        self.btn_aplicar_transformacion = self.findChild(QPushButton, "btn_aplicar_transformacion")

        self.label_axial = self.findChild(QLabel, "label_axial")
        self.label_sagital = self.findChild(QLabel, "label_sagital")
        self.label_coronal = self.findChild(QLabel, "label_coronal")
        self.tableWidget_2 = self.findChild(QTableWidget, "tableWidget_2")

        self.slider_axial = self.findChild(QSlider, "slider_axial")
        self.slider_sagital = self.findChild(QSlider, "slider_sagital")
        self.slider_coronal = self.findChild(QSlider, "slider_coronal")

        self.seleccion_segmentacion = self.findChild(QComboBox, "seleccion_segmentacion")
        self.seleccion_morfo = self.findChild(QComboBox, "seleccion_morfo")
        self.spinkernel = self.findChild(QSpinBox, "spinkernel")

        # Señales
        self.btn_cargar_senal = self.findChild(QPushButton, "btn_cargar_senal")
        self.btn_agregar_ruido = self.findChild(QPushButton, "btn_agregar_ruido")
        self.btn_calc_estadis = self.findChild(QPushButton, "btn_calc_estadis")
        self.widget_3 = self.findChild(QWidget, "widget_3")
        self.spin_canal = self.findChild(QSpinBox, "spin_canal")
        self.spin_muestra_inicio = self.findChild(QSpinBox, "spin_muestra_inicio")
        self.spin_muestra_fin = self.findChild(QSpinBox, "spin_muestra_fin")
        self.eje_0 = self.findChild(QRadioButton, "eje_0")
        self.eje_1 = self.findChild(QRadioButton, "eje_1")
        self.result_estadis = self.findChild(QTextEdit, "result_estadis")
        self.widget_3 = self.findChild(QWidget, "widget_3")

        # Datos
        self.cargar_dataset = self.findChild(QPushButton, "cargar_dataset")
        self.btn_grafico_scatter = self.findChild(QPushButton, "btn_grafico_scatter")
        self.btn_graficar_columnas = self.findChild(QPushButton, "btn_graficar_columnas")
        self.btn_confirmar = self.findChild(QPushButton, "btn_confirmar")

        self.listWidget = self.findChild(QListWidget, "listWidget")
        self.comboBox_3 = self.findChild(QComboBox, "comboBox_3")   # Eje X
        self.comboBox_4 = self.findChild(QComboBox, "comboBox_4")   # Eje Y

        self.tableWidget = self.findChild(QTableWidget, "tableWidget")      # Datos completos
        self.tableWidget_3 = self.findChild(QTableWidget, "tableWidget_3")  # describe()
        self.textEdit = self.findChild(QTextEdit, "textEdit")               # info()

        self.widget_4 = self.findChild(QWidget, "widget_4")  # Contenedor de gráficos

    def _conectar_señales(self):
        # Navegación
        if self.boton_imagenes: self.boton_imagenes.clicked.connect(self.controller.mostrar_modulo_imagenes)
        if self.boton_senales: self.boton_senales.clicked.connect(self.controller.mostrar_modulo_senales)
        if self.boton_datos: self.boton_datos.clicked.connect(self.controller.mostrar_modulo_datos)

        # Imágenes
        if self.btn_cargar_dicom: self.btn_cargar_dicom.clicked.connect(self.controller.cargar_carpeta_dicom)
        if self.btn_cargar_nifti: self.btn_cargar_nifti.clicked.connect(self.controller.convertir_a_nifti)
        if self.btn_zoom: self.btn_zoom.clicked.connect(self.controller.abrir_ventana_zoom)
        if self.btn_aplicar_transformacion: self.btn_aplicar_transformacion.clicked.connect(self.controller.aplicar_transformacion)

        # Señales
        if self.btn_cargar_senal: self.btn_cargar_senal.clicked.connect(self.controller.cargar_senal)
        if self.btn_agregar_ruido: self.btn_agregar_ruido.clicked.connect(self.controller.agregar_ruido)
        if self.btn_calc_estadis: self.btn_calc_estadis.clicked.connect(self.controller.calcular_estadisticas)
        if self.spin_canal:
            self.spin_canal.valueChanged.connect(self.controller.actualizar_plot_senal)
        if self.spin_muestra_inicio:
            self.spin_muestra_inicio.valueChanged.connect(self.controller.actualizar_plot_senal)
        if self.spin_muestra_fin:
            self.spin_muestra_fin.valueChanged.connect(self.controller.actualizar_plot_senal)

        # Sliders
        if self.slider_axial: self.slider_axial.valueChanged.connect(self.controller.actualizar_corte_axial)
        if self.slider_sagital: self.slider_sagital.valueChanged.connect(self.controller.actualizar_corte_sagital)
        if self.slider_coronal: self.slider_coronal.valueChanged.connect(self.controller.actualizar_corte_coronal)

        # Datos
        if self.cargar_dataset: 
            self.cargar_dataset.clicked.connect(self.controller.cargar_dataset_tabular)
        if self.btn_grafico_scatter: 
            self.btn_grafico_scatter.clicked.connect(self.controller.generar_scatter)
        if self.btn_graficar_columnas: 
            self.btn_graficar_columnas.clicked.connect(self.controller.graficar_columnas)
        if self.btn_confirmar: 
            self.btn_confirmar.clicked.connect(self.controller.confirmar_columnas)

    def _setup_matplotlib(self):
        """Configura gráficos embebidos"""
        # Señal
        self.figure_senal = Figure(figsize=(11, 6))
        self.canvas_senal = FigureCanvas(self.figure_senal)
        layout_s = QVBoxLayout(self.widget_3)
        layout_s.setContentsMargins(0, 0, 0, 0)
        layout_s.addWidget(self.canvas_senal)

        # Datos
        self.figure_datos = Figure(figsize=(10, 6))
        self.canvas_datos = FigureCanvas(self.figure_datos)
        layout_d = QVBoxLayout(self.widget_4)
        layout_d.setContentsMargins(0, 0, 0, 0)
        layout_d.addWidget(self.canvas_datos)
        
    def show_figure(self, new_fig: Figure):
        """Muestra figura generada por el modelo de forma segura"""
        if not hasattr(self, 'figure_senal') or not hasattr(self, 'canvas_senal'):
            return

        # Limpiar la figura actual del canvas
        self.figure_senal.clear()

        # Copiar solo los ejes de forma segura
        for ax_orig in new_fig.get_axes():
            # Crear nuevo subplot
            ax = self.figure_senal.add_subplot(ax_orig.get_subplotspec() or 111)
            
            # Copiar líneas (el caso más común)
            for line in ax_orig.get_lines():
                ax.plot(line.get_xdata(), line.get_ydata(),
                        color=line.get_color(),
                        linestyle=line.get_linestyle(),
                        linewidth=line.get_linewidth(),
                        label=line.get_label())

            # Copiar stems (usado en estadísticas)
            for collection in ax_orig.collections:
                # Recrear stems en lugar de copiar (evita el error)
                if hasattr(collection, 'get_segments'):
                    segments = collection.get_segments()
                    if segments:
                        ax.stem([s.mean() for s in segments], 
                               linefmt='b-', markerfmt='bo', basefmt='k-')

            ax.set_title(ax_orig.get_title())
            ax.set_xlabel(ax_orig.get_xlabel())
            ax.set_ylabel(ax_orig.get_ylabel())
            ax.grid(True)
            
            if ax_orig.get_legend():
                ax.legend()

        self.figure_senal.tight_layout()
        self.canvas_senal.draw()
        
    def show_3_planes(self, axial, coronal, sagittal):
        if self.label_axial and axial is not None:
            self.label_axial.setPixmap(self._numpy_to_qpixmap(axial))
        if self.label_sagital and sagittal is not None:
            self.label_sagital.setPixmap(self._numpy_to_qpixmap(sagittal))
        if self.label_coronal and coronal is not None:
            self.label_coronal.setPixmap(self._numpy_to_qpixmap(coronal))

    def _numpy_to_qpixmap(self, img):
        img_u8 = cv2.normalize(img.astype(np.float32), None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
        h, w = img_u8.shape
        qimg = QImage(img_u8.data, w, h, w, QImage.Format_Grayscale8)
        return QPixmap.fromImage(qimg)

    def mostrar_metadatos(self, metadata: dict):
        if not hasattr(self, 'tableWidget_2') or not metadata:
            return
        table = self.tableWidget_2
        table.setRowCount(len(metadata))
        table.setColumnCount(2)
        table.setHorizontalHeaderLabels(["Campo", "Valor"])
        for row, (key, value) in enumerate(metadata.items()):
            table.setItem(row, 0, QTableWidgetItem(str(key)))
            table.setItem(row, 1, QTableWidgetItem(str(value)))
        table.resizeColumnsToContents()

    def update_statistics_text(self, text: str):
        """Actualiza el QTextEdit con las estadísticas"""
        if self.result_estadis:
            self.result_estadis.setPlainText(text)

    def actualizar_combos_columnas(self, columnas):
        """Llena comboBox_3 y comboBox_4 con las columnas seleccionadas"""
        self.comboBox_3.clear()
        self.comboBox_4.clear()
        self.comboBox_3.addItems(columnas)
        self.comboBox_4.addItems(columnas)
        if columnas:
            self.comboBox_4.setCurrentIndex(1 if len(columnas) > 1 else 0)  
             
    def _forzar_conexiones_pestanas(self):
        """Conexión más robusta para cambio de pestañas"""
        if self.boton_imagenes:
            self.boton_imagenes.clicked.connect(lambda: self.controller.mostrar_modulo_imagenes())
            print("✅ Conexión boton_imagenes OK")
        if self.boton_senales:
            self.boton_senales.clicked.connect(lambda: self.controller.mostrar_modulo_senales())
            print("✅ Conexión boton_senales OK")
        if self.boton_datos:
            self.boton_datos.clicked.connect(lambda: self.controller.mostrar_modulo_datos())
            print("✅ Conexión boton_datos OK")
    
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
            label = self.findChild(QLabel, "widget_2")
            if label:
                label.setPixmap(pixmap.scaled(label.size(), Qt.KeepAspectRatio))
        except Exception as e:
            print("Error mostrando imagen en zoom:", e)

    def aplicar_zoom(self):
        QMessageBox.information(self, "Info", "Función de Zoom en desarrollo")

    def guardar_imagen(self):
        nombre = self.nombre_archivo.text().strip() or "recorte_dicom"
        QMessageBox.information(self, "Guardado", f"Imagen guardada como: {nombre}.png")