"""
Controlador Principal - NeuraMed Analizer (MVC)
"""

from PyQt5.QtWidgets import QMessageBox, QFileDialog, QTableWidgetItem
from model.modelo_dicom import ModeloDICOM
from model.signal_processor import SignalProcessor
from model.tabular_processor import TabularProcessor
from model.database import DatabaseManager
from model.modelo_camara import ModeloCamara
from model.modelo_usuario import ModeloUsuario

from view.views import (
    BienvenidaWindow, LoginWindow, VentanaAutenticacion, 
    MainWindow, VentanaZoom
)


class BioMonitorController:
    """Controlador central"""

    def __init__(self):
        self.db = DatabaseManager()
        self.modelo_usuario = ModeloUsuario()
        self.modelo_camara = ModeloCamara()
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
        # Login con SQLite (ya existente)
        if self.db.login(username, password):
            # Sincronizar con ModeloUsuario (MongoDB)
            if self.modelo_usuario.validar_login(username, password):
                self.login_window.close()
                self.mostrar_autenticacion()
            else:
                QMessageBox.warning(self.login_window, "Error", 
                                  "Error al sincronizar usuario en MongoDB")
        else:
            QMessageBox.warning(self.login_window, "Error", "Usuario o contraseña incorrectos.")

    def mostrar_autenticacion(self):
        self.autenticacion = VentanaAutenticacion(self)
        self.autenticacion.show()

    def guardar_foto_autenticacion(self):
        """Captura foto, guarda y registra sesión en MongoDB"""
        try:
            # Obtener usuario activo desde ModeloUsuario (MongoDB)
            usuario_activo = self.modelo_usuario.get_usuario_activo()
            if not usuario_activo:
                QMessageBox.warning(self.autenticacion, "Error", "No hay usuario activo")
                return

            nombre_usuario = usuario_activo.get("nombre", "usuario")

            # Capturar y guardar foto
            ruta_foto = self.modelo_camara.capturar_y_guardar(nombre_usuario)

            # Registrar sesión
            self.modelo_usuario.registrar_sesion(ruta_foto)

            QMessageBox.information(self.autenticacion, "Éxito", 
                                  f"✅ Fotografía guardada correctamente\n"
                                  f"Usuario: {nombre_usuario}")

            # Cerrar autenticación y abrir principal
            if self.autenticacion:
                self.autenticacion.close()
            self.abrir_ventana_principal()

        except Exception as e:
            QMessageBox.critical(self.autenticacion, "Error", 
                               f"No se pudo guardar la foto:\n{str(e)}")

    def abrir_ventana_principal(self):
        self.main_window = MainWindow(self)
        if self.autenticacion:
            self.autenticacion.close()
        self.main_window.show()

    # ====================== NAVEGACIÓN PESTAÑAS VENTANA PRINCIPAL ======================
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
        if not folder:
            return
        try:
            shape = self.dicom_model.cargar_dicom(folder)

            # Mostrar planos centrales
            axial = self.dicom_model.get_corte_axial(shape[0]//2)
            coronal = self.dicom_model.get_corte_coronal(shape[1]//2)
            sagittal = self.dicom_model.get_corte_sagital(shape[2]//2)

            self.main_window.show_3_planes(axial, coronal, sagittal)
            self.main_window.mostrar_metadatos(self.dicom_model.metadata)

            # Configurar sliders
            self.main_window.slider_axial.setMaximum(shape[0]-1)
            self.main_window.slider_coronal.setMaximum(shape[1]-1)
            self.main_window.slider_sagital.setMaximum(shape[2]-1)

            self.main_window.slider_axial.setValue(shape[0]//2)
            self.main_window.slider_coronal.setValue(shape[1]//2)
            self.main_window.slider_sagital.setValue(shape[2]//2)

            QMessageBox.information(self.main_window, "Éxito", 
                                  f"DICOM cargado correctamente\n"
                                  f"Volumen: {shape} | Cortes: {len(self.dicom_model.archivos_dcm)}")

        except Exception as e:
            QMessageBox.critical(self.main_window, "Error", f"Error al cargar DICOM:\n{str(e)}")

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

    def aplicar_procesamiento(self):
        """Aplica filtros/segmentación en tiempo real"""
        if self.dicom_model.volumen_3d is None:
            return

        tipo = self.main_window.seleccion_segmentacion.currentText()
        if tipo == "Seleccione una opcion..." or tipo == "":
            return

        try:
            idx = self.main_window.slider_axial.value()  # Usamos el corte axial actual
            resultado = self.dicom_model.segmentar(idx, tipo)

            # Actualizar solo el plano axial (más eficiente)
            self.main_window.label_axial.setPixmap(
                self.main_window._numpy_to_qpixmap(resultado)
            )
            QMessageBox.information(self.main_window, "Procesado", f"Aplicado: {tipo}")
        except Exception as e:
            QMessageBox.warning(self.main_window, "Error", str(e))

    def aplicar_morfologia(self):
        """Aplica transformación morfológica"""
        if self.dicom_model.volumen_3d is None:
            return

        tipo = self.main_window.seleccion_morfo.currentText()
        if tipo == "Seleccione una transformacion Morfologica..." or tipo == "":
            return

        kernel_size = self.main_window.spinkernel.value()

        try:
            idx = self.main_window.slider_axial.value()
            resultado = self.dicom_model.transformacion_morfologica(idx, tipo, kernel_size)

            self.main_window.label_axial.setPixmap(
                self.main_window._numpy_to_qpixmap(resultado)
            )
        except Exception as e:
            QMessageBox.warning(self.main_window, "Error", str(e))

    def aplicar_transformacion(self):
        """Aplica segmentación o transformación morfológica según selección"""
        if self.dicom_model.volumen_3d is None:
            QMessageBox.warning(self.main_window, "Advertencia", "Primero cargue un estudio DICOM")
            return

        try:
            # Usamos el corte axial actual
            indice = self.main_window.slider_axial.value() if hasattr(self.main_window, 'slider_axial') else 0

            tipo_seg = self.main_window.seleccion_segmentacion.currentText()
            tipo_morfo = self.main_window.seleccion_morfo.currentText()
            kernel = self.main_window.spinkernel.value() if hasattr(self.main_window, 'spinkernel') else 3

            resultado = None
            mensaje = ""

            if tipo_seg and tipo_seg not in ["Seleccione una opcion...", ""]:
                resultado = self.dicom_model.segmentar(indice, tipo_seg)
                mensaje = f"Segmentación aplicada: {tipo_seg}"

            elif tipo_morfo and tipo_morfo not in ["Seleccione una transformacion Morfologica...", ""]:
                resultado = self.dicom_model.transformacion_morfologica(indice, tipo_morfo, kernel)
                mensaje = f"Morfología aplicada: {tipo_morfo} (Kernel {kernel}px)"

            else:
                QMessageBox.warning(self.main_window, "Advertencia", "Seleccione un tipo de procesamiento")
                return

            if resultado is not None:
                # Actualizar solo el plano axial (el que el usuario está viendo)
                self.main_window.label_axial.setPixmap(
                    self.main_window._numpy_to_qpixmap(resultado)
                )
                QMessageBox.information(self.main_window, "Éxito", mensaje)

        except Exception as e:
            QMessageBox.critical(self.main_window, "Error", f"Error al aplicar transformación:\n{str(e)}")

    def convertir_a_nifti(self):
        """Convierte el volumen cargado a formato NIfTI con extensión correcta"""
        if self.dicom_model.volumen_3d is None:
            QMessageBox.warning(self.main_window, "Advertencia", 
                              "Primero cargue un estudio DICOM")
            return

        # Sugerir nombre con extensión correcta
        default_name = "volumen_dicom.nii.gz"
        
        path, _ = QFileDialog.getSaveFileName(
            self.main_window, 
            "Guardar como NIfTI", 
            default_name, 
            "NIfTI (*.nii.gz);;NIfTI (*.nii)"
        )
        
        if not path:
            return

        # Asegurar extensión correcta
        if not path.lower().endswith(('.nii', '.nii.gz')):
            path += '.nii.gz'

        try:
            ruta = self.dicom_model.convertir_a_nifti(path)
            QMessageBox.information(self.main_window, "Éxito", 
                                  f"NIfTI guardado correctamente en:\n{ruta}")
        except Exception as e:
            QMessageBox.critical(self.main_window, "Error", 
                               f"No se pudo guardar el NIfTI:\n{str(e)}")

    def abrir_ventana_zoom(self):
        if self.dicom_model.volumen_3d is None:
            QMessageBox.warning(self.main_window, "Advertencia", "Cargue primero un estudio DICOM")
            return

        try:
            indice = self.main_window.slider_axial.value() if hasattr(self.main_window, 'slider_axial') else 0
            corte = self.dicom_model.get_corte_axial(indice)

            self.zoom_window = VentanaZoom(self.dicom_model, controller=self)  # ← Pasar controller
            self.zoom_window.mostrar_imagen(corte, indice)
            self.zoom_window.show()
        except Exception as e:
            QMessageBox.critical(self.main_window, "Error", f"No se pudo abrir zoom:\n{str(e)}")

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
        if not self.main_window or self.signal_proc.data_2d is None:
            return

        canal = self.main_window.spin_canal.value()
        inicio = self.main_window.spin_muestra_inicio.value()
        fin = self.main_window.spin_muestra_fin.value()

        if fin <= inicio:
            fin = inicio + 1000

        # Detectar eventos automáticamente
        self.signal_proc.detect_events(canal, signal_type="ECG")

        fig = self.signal_proc.plot_signal(canal, inicio, fin, detect_events=True)
        self.main_window.show_figure(fig)

    def agregar_ruido(self):
        if self.signal_proc.data_2d is None:
            QMessageBox.warning(self.main_window, "Advertencia", "Cargue primero una señal")
            return

        canal = self.main_window.spin_canal.value()
        inicio = self.main_window.spin_muestra_inicio.value()
        fin = self.main_window.spin_muestra_fin.value()

        if fin <= inicio:
            fin = inicio + 1000

        # Aplicar ruido persistentemente
        original, noisy = self.signal_proc.agregar_ruido(canal, noise_level=0.22)

        # Graficar
        fig = self.signal_proc.plot_original_vs_noisy(canal, inicio, fin, noise_level=0.22)
        self.main_window.show_figure(fig)

        QMessageBox.information(self.main_window, "Ruido Aplicado", 
                              f"Ruido aplicado correctamente en Canal {canal}\n"
                              f"Nivel: 22% | Rango: {inicio}-{fin} muestras")

    def calcular_estadisticas(self):
        if self.signal_proc.data_3d is None:
            QMessageBox.warning(self.main_window, "Advertencia", "Cargue primero una señal")
            return

        eje = 0 if self.main_window.eje_0.isChecked() else 1
        mean, std, stats_text = self.signal_proc.compute_statistics(axis=eje)

        # Aplicar formato visible
        if hasattr(self.main_window, 'result_estadis'):
            self.main_window.result_estadis.setStyleSheet("""
                QTextEdit {
                    background-color: #1e1e1e;
                    color: #00ffcc;
                    font-family: Arial;
                    font-size: 11pt;
                    padding: 8px;
                    border: 1px solid #00d4ff;
                }
            """)
            self.main_window.result_estadis.setPlainText(stats_text)

        # Actualizar gráfico
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