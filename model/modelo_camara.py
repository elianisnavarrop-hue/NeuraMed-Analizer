# Maneja la cámara con OpenCV para capturar fotos del usuario.

import cv2
import os
from datetime import datetime

class ModeloCamara:      #Controla la webcam usando OpenCV.

    def __init__(self):
        self.captura = None        # Objeto VideoCapture de OpenCV
        self.frame_actual = None   # Frame más reciente capturado
        self.carpeta_fotos = "fotos_sesion"

        # Creamos la carpeta donde se guardarán las fotos
        if not os.path.exists(self.carpeta_fotos):
            os.makedirs(self.carpeta_fotos)
    
    def iniciar_camara(self, indice=0):   #Abre la cámara. indice=0 es la cámara principal. Retorna True si se abrió correctamente.
        self.captura = cv2.VideoCapture(indice)
        return self.captura.isOpened()
    
    def get_frame(self):   #Lee un frame de la cámara. Retorna (exito, frame_en_RGB) — RGB para mostrarlo en PyQt.
        if self.captura is None or not self.captura.isOpened():
            return False, None

        exito, frame = self.captura.read()
        if exito:
            # OpenCV captura en BGR, PyQt necesita RGB
            self.frame_actual = frame
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            return True, frame_rgb
        return False, None
    def capturar_y_guardar(self, nombre_usuario):   #Guarda el frame actual como imagen .jpg. El nombre incluye el usuario y la fecha para que sea único. Retorna la ruta del archivo guardado.
        if self.frame_actual is None:
            raise ValueError("No hay frame disponible para guardar.")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nombre_archivo = f"{nombre_usuario}_{timestamp}.jpg"
        ruta_completa = os.path.join(self.carpeta_fotos, nombre_archivo)

        cv2.imwrite(ruta_completa, self.frame_actual)
        return ruta_completa
    
    def detener_camara(self):   #Libera la cámara cuando ya no se necesita.
        if self.captura and self.captura.isOpened():
            self.captura.release()