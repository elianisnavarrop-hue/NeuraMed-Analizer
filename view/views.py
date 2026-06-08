"""
Vistas - NeuraMed Analizer
"""

from PyQt5 import uic
from PyQt5.QtWidgets import (
    QMainWindow, QMessageBox, QFileDialog, QPushButton, 
    QLabel, QTableWidget, QLineEdit, QSlider, QComboBox, 
    QSpinBox, QRadioButton, QTextEdit, QWidget, QVBoxLayout,
    QTableWidgetItem, QListWidget, QDoubleSpinBox, QLabel
)
from PyQt5.QtGui import QPixmap, QImage, QPainter, QPen, QColor
from PyQt5.QtCore import Qt, QRect, QTimer
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

        self._encontrar_widgets()
        self._conectar_señales()

        self.timer = QTimer()
        self.timer.timeout.connect(self.actualizar_frame_camara)

        # Iniciar cámara automáticamente al abrir la ventana
        self.iniciar_camara()

    def _encontrar_widgets(self):
        self.visualizador_camara = self.findChild(QLabel, "visualizador_camara")
        self.boton_guardar_foto = self.findChild(QPushButton, "boton_guardar_foto")
        self.lbltitulo = self.findChild(QLabel, "lbltitulo")

    def _conectar_señales(self):
        if self.boton_guardar_foto:
            self.boton_guardar_foto.clicked.connect(self.controller.guardar_foto_autenticacion)

    def iniciar_camara(self):
        """Inicia la cámara y el timer de actualización"""
        if self.controller.modelo_camara.iniciar_camara():
            self.timer.start(30)  # ~33 FPS
            print("✅ Cámara iniciada en ventana de autenticación")
        else:
            QMessageBox.warning(self, "Error", "No se pudo acceder a la cámara")

    def actualizar_frame_camara(self):
        """Actualiza el QLabel con el frame en vivo"""
        exito, frame_rgb = self.controller.modelo_camara.get_frame()
        if exito and frame_rgb is not None and self.visualizador_camara:
            h, w, ch = frame_rgb.shape
            bytes_per_line = ch * w
            qimg = QImage(frame_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(qimg).scaled(
                self.visualizador_camara.size(), 
                Qt.KeepAspectRatio, 
                Qt.SmoothTransformation
            )
            self.visualizador_camara.setPixmap(pixmap)

    def closeEvent(self, event):
        """Detener cámara al cerrar la ventana"""
        self.timer.stop()
        self.controller.modelo_camara.detener_camara()
        event.accept()
        
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
        self.label_coronal = self.findChild(QLabel, "label_coronal")
        self.label_sagital = self.findChild(QLabel, "label_sagital")

        self.tableWidget_2 = self.findChild(QTableWidget, "tableWidget_2")

        self.slider_axial = self.findChild(QSlider, "slider_axial")
        self.slider_coronal = self.findChild(QSlider, "slider_coronal")
        self.slider_sagital = self.findChild(QSlider, "slider_sagital")

        # Procesamiento
        self.seleccion_segmentacion = self.findChild(QComboBox, "seleccion_segmentacion")  # Filtros
        self.seleccion_morfo = self.findChild(QComboBox, "seleccion_morfo")
        self.spinkernel = self.findChild(QSpinBox, "spinkernel")

        # Estado
        self.lblEstadoConversion = self.findChild(QLabel, "lblEstadoConversion")  # o lbl_archvio_convertido

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

        # Imágenes - DICOM
        if self.btn_cargar_dicom:
            self.btn_cargar_dicom.clicked.connect(self.controller.cargar_carpeta_dicom)
        if self.btn_cargar_nifti:
            self.btn_cargar_nifti.clicked.connect(self.controller.convertir_a_nifti)
        if self.btn_zoom:
            self.btn_zoom.clicked.connect(self.controller.abrir_ventana_zoom)
        if self.btn_aplicar_transformacion:
            self.btn_aplicar_transformacion.clicked.connect(self.controller.aplicar_transformacion)

        # Procesamiento en tiempo real
        if self.seleccion_segmentacion:
            self.seleccion_segmentacion.currentIndexChanged.connect(self.controller.aplicar_transformacion)
        if self.seleccion_morfo:
            self.seleccion_morfo.currentIndexChanged.connect(self.controller.aplicar_transformacion)


        # Sliders
        if self.slider_axial:
            self.slider_axial.valueChanged.connect(self.controller.actualizar_corte_axial)
        if self.slider_coronal:
            self.slider_coronal.valueChanged.connect(self.controller.actualizar_corte_coronal)
        if self.slider_sagital:
            self.slider_sagital.valueChanged.connect(self.controller.actualizar_corte_sagital)

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
                        linewidth=line.get_linewidth() or 1.8,
                        label=line.get_label())

            # Copiar stems (usado en estadísticas)
            for collection in ax_orig.collections:
                # Recrear stems en lugar de copiar (evita el error)
                if hasattr(collection, 'get_segments'):
                    segments = collection.get_segments()
                    if segments:
                        ax.stem([s.mean() for s in segments], 
                               linefmt='b-', markerfmt='bo', basefmt='k-')

            ax.set_title(ax_orig.get_title(), fontsize=14, fontweight='bold')
            ax.set_xlabel(ax_orig.get_xlabel(), fontsize=12, fontweight='bold')
            ax.set_ylabel(ax_orig.get_ylabel(), fontsize=12, fontweight='bold')
            ax.grid(True, alpha=0.3)
            
            if ax_orig.get_legend():
                ax.legend(fontsize=11)

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
    """Ventana de Zoom y Recorte - Versión con escalado forzado"""

    def __init__(self, dicom_model):
        super().__init__()
        uic.loadUi("view/ventana_zoom.ui", self)
        self.dicom_model = dicom_model
        
        self.original_image = None
        self.current_roi = None
        self.indice_axial = 0
        self.drawing = False
        self.start_point = None
        self.end_point = None
        self.original_pixmap = None

        self.label_original = None
        self.label_zoom = None

        self._encontrar_widgets()
        self._conectar_botones()
        self._setup_mouse_interaction()

    def _encontrar_widgets(self):
        self.widget_original = self.findChild(QWidget, "widget_2")
        self.widget_zoom = self.findChild(QWidget, "widget_3")

        self.btn_aplicar_zoom = self.findChild(QPushButton, "btn_aplicar_zoom")
        self.btn_guardar_img = self.findChild(QPushButton, "btn_guardar_img")
        self.nombre_archivo = self.findChild(QLineEdit, "nombre_archivo")

        self.lbl_pixel = self.findChild(QLabel, "lblpixel")
        self.lbl_slice = self.findChild(QLabel, "lblslice")

    def _conectar_botones(self):
        if self.btn_aplicar_zoom:
            self.btn_aplicar_zoom.clicked.connect(self.aplicar_zoom_y_dibujar)
        if self.btn_guardar_img:
            self.btn_guardar_img.clicked.connect(self.guardar_imagen)

    def _setup_mouse_interaction(self):
        if not self.widget_original:
            return

        self.label_original = QLabel(self.widget_original)
        layout = QVBoxLayout(self.widget_original)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.label_original)
        self.label_original.setAlignment(Qt.AlignCenter)
        self.label_original.setScaledContents(False)   # Importante
        self.label_original.setMouseTracking(True)

        self.label_original.mousePressEvent = self.mouse_press
        self.label_original.mouseMoveEvent = self.mouse_move
        self.label_original.mouseReleaseEvent = self.mouse_release

    def mostrar_imagen(self, corte, indice_axial=0):
        self.indice_axial = indice_axial
        self.original_image = corte.copy()

        try:
            img_u8 = self.dicom_model.normalizar_uint8(corte)
            img_bgr = cv2.cvtColor(img_u8, cv2.COLOR_GRAY2BGR)
            h, w = img_bgr.shape[:2]
            qimg = QImage(img_bgr.data, w, h, w*3, QImage.Format_RGB888)
            self.original_pixmap = QPixmap.fromImage(qimg)

            # Forzar escalado inmediato y después del resize
            self._update_displayed_image()
            
            # Conectar evento de resize para que se actualice si la ventana cambia de tamaño
            self.widget_original.resizeEvent = self._on_original_resize

            # Metadatos
            if self.lbl_pixel and self.dicom_model.pixel_spacing:
                ps = self.dicom_model.pixel_spacing
                self.lbl_pixel.setText(f"Pixel Spacing (X,Y): {ps[0]:.2f} x {ps[1]:.2f} mm")
            if self.lbl_slice:
                self.lbl_slice.setText(f"Slice Thickness: {self.dicom_model.slice_thickness:.2f} mm")

        except Exception as e:
            print(f"Error en mostrar_imagen: {e}")

    def _update_displayed_image(self):
        """Escala la imagen para que ocupe todo el espacio disponible"""
        if not self.original_pixmap or not self.label_original:
            return

        # Escalar manteniendo proporción y llenando el widget
        scaled = self.original_pixmap.scaled(
            self.widget_original.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        self.label_original.setPixmap(scaled)

    def _on_original_resize(self, event):
        """Se llama cuando el widget cambia de tamaño"""
        self._update_displayed_image()
        # Llamar al resize original si es necesario
        if hasattr(QWidget, 'resizeEvent'):
            QWidget.resizeEvent(self.widget_original, event)

    # ==================== MOUSE ROI ====================
    def mouse_press(self, event):
        if event.button() == Qt.LeftButton and self.label_original.pixmap():
            self.drawing = True
            self.start_point = event.pos()

    def mouse_move(self, event):
        if self.drawing and self.start_point:
            self.end_point = event.pos()
            self._draw_temporary_roi()

    def mouse_release(self, event):
        if event.button() == Qt.LeftButton and self.drawing:
            self.drawing = False
            self.end_point = event.pos()
            self._finalize_roi()

    def _draw_temporary_roi(self):
        if not (self.start_point and self.end_point):
            return
        temp_pixmap = self.original_pixmap.copy()
        painter = QPainter(temp_pixmap)
        painter.setPen(QPen(QColor(0, 255, 255), 3, Qt.SolidLine))
        rect = QRect(self.start_point, self.end_point).normalized()
        painter.drawRect(rect)
        painter.end()

        scaled = temp_pixmap.scaled(self.widget_original.size(), Qt.KeepAspectRatio)
        self.label_original.setPixmap(scaled)

    def _finalize_roi(self):
        if not (self.start_point and self.end_point):
            return

        scaled_pixmap = self.label_original.pixmap()
        if not scaled_pixmap:
            return

        scale_x = self.original_pixmap.width() / scaled_pixmap.width()
        scale_y = self.original_pixmap.height() / scaled_pixmap.height()

        x1 = int(self.start_point.x() * scale_x)
        y1 = int(self.start_point.y() * scale_y)
        x2 = int(self.end_point.x() * scale_x)
        y2 = int(self.end_point.y() * scale_y)

        x = min(x1, x2)
        y = min(y1, y2)
        ancho = abs(x2 - x1)
        alto = abs(y2 - y1)

        if ancho < 20 or alto < 20:
            QMessageBox.warning(self, "Error", "El ROI es demasiado pequeño")
            return

        self.current_roi = (x, y, ancho, alto)
        QMessageBox.information(self, "ROI Seleccionado", 
                              f"Región: {ancho}×{alto} píxeles\nPosición: ({x}, {y})")

    # ==================== Zoom y Guardar ====================
    def aplicar_zoom_y_dibujar(self):
        if not self.current_roi or self.original_image is None:
            QMessageBox.warning(self, "Error", "Primero dibuja un ROI con el mouse")
            return

        x, y, ancho, alto = self.current_roi
        recorte = self.original_image[y:y+alto, x:x+ancho]
        recorte_u8 = self.dicom_model.normalizar_uint8(recorte)
        recorte_zoom = cv2.resize(recorte_u8, (int(ancho * 3), int(alto * 3)), cv2.INTER_LINEAR)

        img_zoom_bgr = cv2.cvtColor(recorte_zoom, cv2.COLOR_GRAY2BGR)
        qimg_zoom = QImage(img_zoom_bgr.data, img_zoom_bgr.shape[1], img_zoom_bgr.shape[0], 
                          img_zoom_bgr.shape[1]*3, QImage.Format_RGB888)

        if not self.label_zoom:
            self.label_zoom = QLabel(self.widget_zoom)
            layout = QVBoxLayout(self.widget_zoom)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.addWidget(self.label_zoom)

        scaled_zoom = QPixmap.fromImage(qimg_zoom).scaled(
            self.widget_zoom.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.label_zoom.setPixmap(scaled_zoom)

    def guardar_imagen(self):
        if not self.current_roi or self.original_image is None:
            QMessageBox.warning(self, "Error", "Primero selecciona un ROI")
            return

        nombre = self.nombre_archivo.text().strip() or f"recorte_axial_{self.indice_axial}"
        try:
            x, y, ancho, alto = self.current_roi
            recorte = self.original_image[y:y+alto, x:x+ancho]
            recorte_u8 = self.dicom_model.normalizar_uint8(recorte)
            ruta = f"{nombre}.png"
            cv2.imwrite(ruta, recorte_u8)
            QMessageBox.information(self, "Éxito", f"Imagen guardada como:\n{ruta}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al guardar: {e}")