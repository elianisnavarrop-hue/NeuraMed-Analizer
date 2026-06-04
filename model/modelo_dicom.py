# MODELO - modelo_dicom.py
# Clase encargada de cargar y procesar imágenes médicas DICOM.
# No toca la interfaz, solo maneja datos e imágenes.
import os
import numpy as np
import pandas as pd
import pydicom
import nibabel as nib
import cv2

class ModeloDICOM: 
    def __init__(self):
        #atributos principales 
        self.ruta_carpeta = None            #ruta de la carpeta con los .dcm
        self.archivos_dcm = []              #lista de objetos pydicom leídos
        self.volumen_3d = None              #Matriz 3D reconstruida
        self.metatadata ={}                 #dicionario con info del estudio 
        self.pixel_spacing = [1.0, 1.0]     #espaciado entre píxeles en mm
        self.slice_thickness = 1.0          #grosor de cada corte en mm
    
    #cargar archivos DICOM 
    def cargar_dicom(self, ruta_carpeta):
        self.ruta_carpeta = ruta_carpeta
        self.archivos_dcm = []
        #buscar archivos .dcm en la carpeta
        for archivo in sorted(os.listdir(ruta_carpeta)):
            if archivo.lower().endswith('.dcm'):
                ruta_completa = os.path.join(ruta_carpeta, archivo)
                ds = pydicom.dcmread(ruta_completa)
                self.archivos_dcm.append(ds)

        if not self.archivos_dcm:
            raise ValueError("No se encontraron archivos .dcm en la carpeta.")
        #Ordenamos los slices por su posición espacial 

        try: 
            self.archivos_dcm.sort(key=lambda x: float(x.ImagePositionPatient[2]))
        except: 
            pass  #si no tiene esa info, lo dejamos como está
        #reconstruir volumen 3D
        slices = [ds.pixel_array for ds in self.archivos_dcm]

        #extraer info del espaciado 
        ds0 = self.archivos_dcm[0]
        try: 
            self.pixel_spacing = [float(ds0.PixelSpacing[0]),
                                   float(ds0.PixelSpacing[1])]
        except:
            self.pixel_spacing = [1.0, 1.0]  
        try:
            self.slice_thickness = float(ds0.SliceThickness)
        except:
            self.slice_thickness = 1.0
        
        #Extraer la metadata del estudio
        self._extraer_metadata()
        
        return self.volumen_3d.shape
    
    #Extraer Metadata
    def _extraer_metadata(self):
        ds = self.archivos_dcm[0]

        def get_valor(tag, default="N/A"):
            try: 
                return str(getattr(ds, tag, default))
            except:
                return default
            
        study_time = get_valor("StudyTime")
        series_time = get_valor("SeriesTime")

        #calcular la duración del estudio
        duracion = self._calcular_duracion(study_time, series_time)

        self.metatadata = {
            "Study Date": get_valor("StudyDate"),
            "Study Time": study_time,
            "Study Modality": get_valor("Modality"),
            "Study Description": get_valor("StudyDescription"),
            "Series Time": series_time,
            "Duracion Estudio": duracion,
            "Manufacturer": get_valor("Manufacturer"),
            "Num Slices": str(len(self.archivos_dcm)),

        }
    def _calcular_duracion(self, study_time, series_time):

        try: 
            # tomando solo HHMMSS (primeros 6 caracteres)
            t1 = study_time[:6]
            t2 = series_time[:6]
            h1, m1, s1 = int(t1[0:2]), int(t1[2:4]), int(t1[4:6])
            h2, m2, s2 = int(t2[0:2]), int(t2[2:4]), int(t2[4:6])
            seg1 = h1 * 3600 + m1 * 60 + s1
            seg2 = h2 * 3600 + m2 * 60 + s2
            diff = abs (seg2 - seg1)
            return f"{diff} segundos"
        except:
            return "N/A"
        
    #Exportar Metadata a CSV

    def exportar_metadata_csv(self, ruta_salida="metadata_dicom.csv"):
        df = pd.DataFrame([self.metatadata])
        df.to_csv(ruta_salida, index=False, encoding='utf-8')
        return ruta_salida
    
    #convertir a Hounsefield
    def aplicar_hounsfield(self):
        ds = self.archivos_dcm[0]

        try: 
            slope = float(ds.RescaleSlope)
            intercept = float(ds.RescaleIntercept)
        except:
            slope, intercept = 1.0, 0.0 

        volumen_hu = self.volumen_3d.astype(np.float32) * slope + intercept
        return volumen_hu
    #Normalizar a UINT8
    def normalizar_uint8(self, imagen):
        img = imagen.astype(np.float32)
        img_min = img.min()
        img_max = img.max()
        if img_max - img_min == 0:
            return np.zeros_like(img, dtype=np.uint8)
        normalizada = (img - img_min) / (img_max - img_min) * 255
        return normalizada.astype(np.uint8)
    #Obtener cortes 
    def get_corte_axial(self, indice):     #retorna el corte axial (vista desde arriba) en el índice dado
        return self.volumen_3d[indice, :, :]
    def get_corte_coronal(self, indice):    #retorna el corte coronal (vista desde el frente) en el índice dado
        return self.volumen_3d[:, indice, :]
    def get_corte_sagital(self, indice):     #retorna el corte sagital (vista desde el lado) en el índice dado
        return self.volumen_3d[:, :, indice]
    def get_num_slices(self):
        if self.volumen_3d is not None:
            return (0,0,0)            
        return self.volumen_3d.shape   #Z, Y, X
    
    #ZOOM y recorte 
    def zoom_recorte(self, indice_axial, x, y, ancho, alto):
        #obtenemos el corte y lo normalizamos a uint8 para mostrarlo correctamente
        corte = self.get_corte_axial(indice_axial)
        corte_u8 = self.normalizar_uint8(corte)
        #convertimos a BGR para poder dibujar en color 
        corte_bgr = cv2.cvtColor(corte_u8, cv2.COLOR_GRAY2BGR)
        #calculamos dimensiones en mm para el texto 
        ancho_mm = round(ancho * self.pixel_spacing[1], 2)
        alto_mm = round(alto * self.pixel_spacing[0], 2)
        texto_dim = f"{ancho_mm}mm x {alto_mm}mm"
        
        #dibujamos el cuadro en amarillo sobre la imagen original 
        cv2.rectangle(corte_bgr, (x, y), (x + ancho, y + alto),
                      color= (0, 255, 255), thickness=2)
        cv2.putText(corte_bgr, texto_dim, (x, y - 5),
                     cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
        #recortamos la region de la matriz 3D (en float)
        recorte = corte[y:y+alto, x:x+ancho]
        recorte_u8 = self.normalizar_uint8(recorte)
        #redimensionamos el recorte con OpenCV para mostrarlo con zoom
        nuevo_ancho = int(ancho * 3, 300)
        nuevo_alto = int(alto * 3, 300)
        recorte_resize = cv2.resize(recorte_u8, (nuevo_ancho, nuevo_alto),
                                    interpolation=cv2.INTER_LINEAR)
        return corte_bgr, recorte_resize
    #Segmentación 
    def segmentar (self, indice_axial, tipo_binarizacion):
        corte = self.get_corte_axial(indice_axial)
        corte_u8 = self.normalizar_uint8(corte)

        tipos = {
            "Binario": cv2.THRESH_BINARY,
            "Binario Invertido": cv2.THRESH_BINARY_INV,
            "Truncado": cv2.THRESH_TRUNC,
            "Tozero": cv2.THRESH_TOZERO,
            "Tozero Invertido": cv2.THRESH_TOZERO_INV, 
        }
        tipo = tipos.get(tipo_binarizacion, cv2.THRESH_BINARY)
        _, resultado = cv2.threshold(corte_u8, 127, 255, tipo)
        return resultado
    
    #Transformaciones morfológicas 
    def transformacion_morfologica(self, idice_axial, tipo, tam_kernel):
        corte = self.get_corte_axial(idice_axial)
        corte_u8 = self.normalizar_uint8(corte)
    
        kernel = np.ones((tam_kernel, tam_kernel), np.uint8)
        operaciones = {
            "Erosión": lambda img: cv2.erode(img, kernel),
            "Dilatación": lambda img: cv2.dilate(img, kernel),       
            "Apertura": lambda img: cv2.morphologyEx(img, cv2.MORPH_OPEN, kernel),
            "Cierre": lambda img: cv2.morphologyEx(img, cv2.MORPH_CLOSE, kernel),
            "Gradiente": lambda img: cv2.morphologyEx(img, cv2.MORPH_GRADIENT, kernel),
            "Top Hat": lambda img: cv2.morphologyEx(img, cv2.MORPH_TOPHAT, kernel),
            "Black Hat": lambda img: cv2.morphologyEx(img, cv2.MORPH_BLACKHAT, kernel),
        }
        operacion = operaciones.get(tipo)
        if operacion is None:
            return corte_u8
        resultado = operacion(corte_u8)
    
    #convertir a NIfTI
    def convertir_a_nifti(self, ruta_salida="salida.nii.gz"):
        if self.volumen_3d is None:
            raise ValueError("primero debes cargar un archivo DICOM")
        #crear el objeto NIfTI con el volumen 
        nifti_img = nib.Nifti1Image(
            self.volumen_3d.astype(np.float32),
              affine=np.eye(4)           #matriz de transformación identidad
        )                             
        nib.save(nifti_img, ruta_salida)
        return ruta_salida
        

        