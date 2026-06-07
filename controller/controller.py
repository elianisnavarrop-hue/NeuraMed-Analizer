"""
Controlador Principal - NeuraMed Analizer (MVC)
"""

from PyQt5.QtWidgets import QMessageBox, QFileDialog, QTableWidgetItem
from model.modelo_dicom import ModeloDICOM
from model.signal_processor import SignalProcessor
from model.tabular_processor import TabularProcessor
from model.database import DatabaseManager

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

        self.bienvenida = None
        self.login_window = None
        self.autenticacion = None
        self.main_window = None
        self.zoom_window = None

    def run(self):
        self.bienvenida = BienvenidaWindow(self)
        self.bienvenida.show()

    # ====================== FLUJO LOGIN ======================
    def mostrar_login(self):
        self.login_window = LoginWindow(self)
        self.bienvenida.close()
        self.login_window.show()

    def validar_login(self, username: str, password: str):
        if self.db.login(username, password):
            self.login_window.close()
            self.mostrar_autenticacion()
        else:
            QMessageBox.warning(self.login_window, "Error", "Usuario o contraseña incorrectos.")

    def mostrar_autenticacion(self):
        self.autenticacion = VentanaAutenticacion(self)
        self.autenticacion.show()

    def abrir_ventana_principal(self):
        self.main_window = MainWindow(self)
        if self.autenticacion:
            self.autenticacion.close()
        self.main_window.show()

    # ====================== NAVEGACIÓN ROBUSTA ======================
    def mostrar_modulo_imagenes(self):
        if self.main_window and hasattr(self.main_window, 'stackedWidget_principal'):
            self.main_window.stackedWidget_principal.setCurrentIndex(0)
            print("→ Cambiado a pestaña: Imágenes")

    def mostrar_modulo_senales(self):
        if self.main_window and hasattr(self.main_window, 'stackedWidget_principal'):
            self.main_window.stackedWidget_principal.setCurrentIndex(1)
            print("→ Cambiado a pestaña: Señales")

    def mostrar_modulo_datos(self):
        if self.main_window and hasattr(self.main_window, 'stackedWidget_principal'):
            self.main_window.stackedWidget_principal.setCurrentIndex(2)
            print("→ Cambiado a pestaña: Datos")

    # ====================== MÓDULOS IMAGENES ======================
    def cargar_carpeta_dicom(self):
        folder = QFileDialog.getExistingDirectory(self.main_window, "Seleccionar carpeta DICOM")
        if not folder: return
        try:
            self.dicom_model.cargar_dicom(folder)
            axial = self.dicom_model.get_corte_axial(self.dicom_model.volumen_3d.shape[0] // 2)
            coronal = self.dicom_model.get_corte_coronal(self.dicom_model.volumen_3d.shape[1] // 2)
            sagittal = self.dicom_model.get_corte_sagital(self.dicom_model.volumen_3d.shape[2] // 2)

            self.main_window.show_3_planes(axial, coronal, sagittal)
            self.main_window.mostrar_metadatos(self.dicom_model.metadata)

            # Configurar sliders
            if hasattr(self.main_window, 'slider_axial'):
                self.main_window.slider_axial.setMaximum(self.dicom_model.volumen_3d.shape[0]-1)
                self.main_window.slider_axial.setValue(self.dicom_model.volumen_3d.shape[0]//2)

            QMessageBox.information(self.main_window, "Éxito", 
                                  f"✅ DICOM cargado correctamente\n"
                                  f"Dimensiones: {self.dicom_model.volumen_3d.shape}")

        except Exception as e:
            QMessageBox.critical(self.main_window, "Error", f"No se pudo cargar el DICOM:\n{str(e)}")

    def actualizar_corte_axial(self, valor):
        if not self.main_window or self.dicom_model.volumen_3d is None:
            return
        corte = self.dicom_model.get_corte_axial(valor)
        self.main_window.label_axial.setPixmap(self.main_window._numpy_to_qpixmap(corte))

    def actualizar_corte_sagital(self, valor):
        if not self.main_window or self.dicom_model.volumen_3d is None:
            return
        corte = self.dicom_model.get_corte_sagital(valor)
        self.main_window.label_sagital.setPixmap(self.main_window._numpy_to_qpixmap(corte))

    def actualizar_corte_coronal(self, valor):
        if not self.main_window or self.dicom_model.volumen_3d is None:
            return
        corte = self.dicom_model.get_corte_coronal(valor)
        self.main_window.label_coronal.setPixmap(self.main_window._numpy_to_qpixmap(corte))

    def abrir_ventana_zoom(self):
        if not getattr(self.dicom_model, 'volumen_3d', None):
            QMessageBox.warning(self.main_window, "Advertencia", "Cargue primero un DICOM")
            return
        self.zoom_window = VentanaZoom(self.dicom_model)
        corte = self.dicom_model.get_corte_axial(self.dicom_model.volumen_3d.shape[0] // 2)
        self.zoom_window.mostrar_imagen(corte)
        self.zoom_window.show()

    def convertir_a_nifti(self):
        if not self.dicom_model.volumen_3d:
            QMessageBox.warning(self.main_window, "Advertencia", "Cargue primero un DICOM")
            return
        path, _ = QFileDialog.getSaveFileName(self.main_window, "Guardar NIfTI", "", "NIfTI (*.nii.gz)")
        if path:
            self.dicom_model.convertir_a_nifti(path)
            QMessageBox.information(self.main_window, "Éxito", f"Guardado en:\n{path}")

    def aplicar_transformacion(self):
        """Aplica segmentación o transformación morfológica"""
        if self.dicom_model.volumen_3d is None:
            QMessageBox.warning(self.main_window, "Advertencia", "Cargue primero un estudio DICOM")
            return

        try:
            indice = 0 
            tipo_seg = self.main_window.seleccion_segmentacion.currentText()
            tipo_morfo = self.main_window.seleccion_morfo.currentText()
            kernel = self.main_window.spinkernel.value() if hasattr(self.main_window, 'spinkernel') else 3

            if tipo_seg and tipo_seg != "Seleccione una opcion...":
                resultado = self.dicom_model.segmentar(indice, tipo_seg)
                QMessageBox.information(self.main_window, "Éxito", f"Segmentación aplicada: {tipo_seg}")
                
            elif tipo_morfo and tipo_morfo != "Seleccione una transformacion Morfologica...":
                resultado = self.dicom_model.transformacion_morfologica(indice, tipo_morfo, kernel)
                QMessageBox.information(self.main_window, "Éxito", f"Morfología aplicada: {tipo_morfo} (Kernel {kernel}px)")
            else:
                QMessageBox.warning(self.main_window, "Advertencia", "Seleccione un tipo de transformación")
        except Exception as e:
            QMessageBox.critical(self.main_window, "Error", f"Error al aplicar transformación:\n{str(e)}")

    # ====================== MÓDULO SEÑALES ======================
    def cargar_senal(self):
        file, _ = QFileDialog.getOpenFileName(
            self.main_window, "Seleccionar archivo .mat", "", "MAT Files (*.mat)"
        )
        if not file:
            return

        if self.signal_proc.load_mat_file(file):
            # Configurar rangos de los SpinBox
            max_canal = self.signal_proc.get_channel_count() - 1
            max_muestras = self.signal_proc.get_sample_count()

            if hasattr(self.main_window, 'spin_canal'):
                self.main_window.spin_canal.setMaximum(max_canal)
                self.main_window.spin_canal.setValue(0)

            if hasattr(self.main_window, 'spin_muestra_inicio'):
                self.main_window.spin_muestra_inicio.setMaximum(max_muestras - 1)
                self.main_window.spin_muestra_inicio.setValue(0)

            if hasattr(self.main_window, 'spin_muestra_fin'):
                self.main_window.spin_muestra_fin.setMaximum(max_muestras)
                self.main_window.spin_muestra_fin.setValue(max_muestras)

            self.actualizar_plot_senal()
            QMessageBox.information(self.main_window, "Éxito", 
                                  f"Señal cargada: {self.signal_proc.filename}\n"
                                  f"Canales: {max_canal+1} | Muestras: {max_muestras}")
        else:
            QMessageBox.critical(self.main_window, "Error", "No se pudo cargar el archivo .mat")

    def actualizar_plot_senal(self):
        """Actualiza el gráfico cuando cambian los SpinBox"""
        if not self.main_window or self.signal_proc.data_2d is None:
            return

        canal = self.main_window.spin_canal.value()
        inicio = self.main_window.spin_muestra_inicio.value()
        fin = self.main_window.spin_muestra_fin.value()

        # Validar rango
        if fin <= inicio:
            fin = inicio + 1000

        fig = self.signal_proc.plot_signal(canal, inicio, fin)
        self.main_window.show_figure(fig)

    def agregar_ruido(self):
        if self.signal_proc.data_2d is None:
            QMessageBox.warning(self.main_window, "Advertencia", "Cargue primero una señal")
            return

        canal = self.main_window.spin_canal.value()
        original, noisy = self.signal_proc.agregar_ruido(canal)

        fig = self.signal_proc.plot_original_vs_noisy(original, noisy)
        self.main_window.show_figure(fig)

    def calcular_estadisticas(self):
        if self.signal_proc.data_3d is None:
            QMessageBox.warning(self.main_window, "Advertencia", "Cargue primero una señal")
            return

        eje = 0 if self.main_window.eje_0.isChecked() else 1
        mean, std, stats_text = self.signal_proc.compute_statistics(axis=eje)

        self.main_window.update_statistics_text(stats_text)

        fig = self.signal_proc.plot_statistics(mean, std)
        self.main_window.show_figure(fig)
         
    # ====================== MÓDULO DATOS ======================
    def cargar_dataset_tabular(self):
        file, _ = QFileDialog.getOpenFileName(
            self.main_window, "Cargar Dataset", "", "CSV/Excel (*.csv *.xlsx *.xls)"
        )
        if not file:
            return

        if self.tabular_proc.load_file(file):
            self._mostrar_datos_en_tabla()
            self._llenar_lista_columnas()
            self._mostrar_reporte_estadisticas()
            QMessageBox.information(self.main_window, "Éxito", 
                                  f"Dataset cargado: {self.tabular_proc.filename}\n"
                                  f"Filas: {len(self.tabular_proc.df)} | Columnas: {len(self.tabular_proc.df.columns)}")

    def _mostrar_datos_en_tabla(self):
        if not hasattr(self.main_window, 'tableWidget') or self.tabular_proc.df is None:
            return
        sample = self.tabular_proc.get_sample(1000)
        df = sample
        table = self.main_window.tableWidget
        table.setRowCount(df.shape[0])
        table.setColumnCount(df.shape[1])
        table.setHorizontalHeaderLabels(df.columns.tolist())

        for i in range(df.shape[0]):
            for j in range(df.shape[1]):
                table.setItem(i, j, QTableWidgetItem(str(df.iloc[i, j])))

    def _llenar_lista_columnas(self):
        if not hasattr(self.main_window, 'listWidget') or self.tabular_proc.df is None:
            return
        self.main_window.listWidget.clear()
        for col in self.tabular_proc.df.columns:
            self.main_window.listWidget.addItem(col)

    def confirmar_columnas(self):
        selected = self.main_window.listWidget.selectedItems()
        if len(selected) < 4:
            QMessageBox.warning(self.main_window, "Advertencia", "Debe seleccionar mínimo 4 columnas")
            return
        columnas = [item.text() for item in selected]
        self.main_window.actualizar_combos_columnas(columnas)
        QMessageBox.information(self.main_window, "Confirmado", f"{len(columnas)} columnas listas")

    def graficar_columnas(self):
        """Grafica columnas seleccionadas DENTRO de widget_4"""
        if self.tabular_proc.df is None:
            QMessageBox.warning(self.main_window, "Advertencia", "Cargue primero un dataset")
            return

        selected_items = self.main_window.listWidget.selectedItems()
        if len(selected_items) < 4:
            QMessageBox.warning(self.main_window, "Advertencia", "Seleccione al menos 4 columnas")
            return

        columnas = [item.text() for item in selected_items]

        # Dibujar directamente en el canvas embebido
        fig = self.main_window.figure_datos
        success = self.tabular_proc.plot_individual_columns(columnas, fig=fig)
        
        if success:
            self.main_window.canvas_datos.draw()
            QMessageBox.information(self.main_window, "Éxito", 
                                  f"Gráficos de {len(columnas)} columnas generados dentro de la interfaz")
        else:
            QMessageBox.warning(self.main_window, "Error", "No se pudieron generar los gráficos")

    def generar_scatter(self):
        """Scatter DENTRO de widget_4"""
        if self.tabular_proc.df is None:
            QMessageBox.warning(self.main_window, "Advertencia", "Cargue primero un dataset")
            return

        col_x = self.main_window.comboBox_3.currentText()
        col_y = self.main_window.comboBox_4.currentText()

        if not col_x or not col_y:
            QMessageBox.warning(self.main_window, "Error", "Seleccione variables para Eje X e Y")
            return

        fig = self.main_window.figure_datos
        success = self.tabular_proc.scatter_plot(col_x, col_y, fig=fig)
        
        if success:
            self.main_window.canvas_datos.draw()
        else:
            QMessageBox.warning(self.main_window, "Error", "No se pudo generar el scatter")
            
    def _mostrar_reporte_estadisticas(self):
        """Llena Tab 2"""
        if self.tabular_proc.df is None:
            return

        # info() en textEdit
        if hasattr(self.main_window, 'textEdit'):
            from io import StringIO
            buffer = StringIO()
            self.tabular_proc.df.info(buf=buffer)
            self.main_window.textEdit.setPlainText(buffer.getvalue())

        # describe() en tableWidget_3
        if hasattr(self.main_window, 'tableWidget_3'):
            describe_df = self.tabular_proc.df.describe()
            table = self.main_window.tableWidget_3
            table.setRowCount(describe_df.shape[0])
            table.setColumnCount(describe_df.shape[1])
            table.setHorizontalHeaderLabels(describe_df.columns.tolist())
            table.setVerticalHeaderLabels(describe_df.index.tolist())

            for i in range(describe_df.shape[0]):
                for j in range(describe_df.shape[1]):
                    table.setItem(i, j, QTableWidgetItem(f"{describe_df.iloc[i, j]:.4f}"))