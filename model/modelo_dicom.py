# MODELO - modelo_dicom.py (Versión Mejorada y Robusta)
import os
import numpy as np
import pandas as pd
import pydicom
import nibabel as nib
import cv2
from pathlib import Path
from collections import defaultdict


class ModeloDICOM:
    def __init__(self):
        self.ruta_carpeta = None
        self.archivos_dcm = []
        self.volumen_3d = None
        self.metadata = {}                  # Metadata completa del estudio
        self.modality = "UNKNOWN"
        self.pixel_spacing = [1.0, 1.0]
        self.slice_thickness = 1.0
        self.is_hu = False                  # Indica si ya está en Hounsfield Units

    def cargar_dicom(self, ruta_carpeta: str):
        """Carga carpeta DICOM de forma robusta con detección de modalidad"""
        self.ruta_carpeta = ruta_carpeta
        self.archivos_dcm = []

        for archivo in sorted(os.listdir(ruta_carpeta)):
            if archivo.lower().endswith('.dcm'):
                ds = pydicom.dcmread(os.path.join(ruta_carpeta, archivo))
                self.archivos_dcm.append(ds)

        if not self.archivos_dcm:
            raise ValueError("No se encontraron archivos .dcm en la carpeta.")

        # Detectar modalidad
        self.modality = self.archivos_dcm[0].get("Modality", "UNKNOWN")
        print(f"Modalidad detectada: {self.modality}")

        # Ordenar por posición espacial (mejor para CT/MR)
        try:
            self.archivos_dcm.sort(key=lambda x: float(x.ImagePositionPatient[2]))
        except:
            print("Advertencia: Ordenando por InstanceNumber")
            self.archivos_dcm.sort(key=lambda x: int(x.get("InstanceNumber", 0)))

        # Construir volumen 3D
        slices = []
        for ds in self.archivos_dcm:
            pixel_array = ds.pixel_array.astype(np.float32)
            
            if self.modality == "CT":
                slope = float(ds.get("RescaleSlope", 1.0))
                intercept = float(ds.get("RescaleIntercept", 0.0))
                hu_array = pixel_array * slope + intercept
                slices.append(hu_array)
                self.is_hu = True
            else:
                slices.append(pixel_array)

        self.volumen_3d = np.stack(slices, axis=0)

        # Extraer metadata
        self._extraer_metadata_completo()
        print(f"Volumen 3D cargado: {self.volumen_3d.shape} | Modalidad: {self.modality} | HU: {self.is_hu}")

        return self.volumen_3d.shape

    def _extraer_metadata_completo(self):
        """Extrae metadata rica del primer archivo"""
        ds = self.archivos_dcm[0]
        def get_val(tag, default="N/A"):
            try:
                return str(getattr(ds, tag, default))
            except:
                return default

        self.metadata = {
            "PatientID": get_val("PatientID"),
            "PatientName": get_val("PatientName"),
            "PatientAge": get_val("PatientAge"),
            "PatientSex": get_val("PatientSex"),
            "StudyDate": get_val("StudyDate"),
            "StudyTime": get_val("StudyTime"),
            "Modality": self.modality,
            "StudyDescription": get_val("StudyDescription"),
            "SeriesDescription": get_val("SeriesDescription"),
            "Manufacturer": get_val("Manufacturer"),
            "StationName": get_val("StationName"),
            "NumSlices": str(len(self.archivos_dcm)),
            "Shape": str(self.volumen_3d.shape),
            "HU_Converted": str(self.is_hu),
        }

        # Pixel spacing y thickness
        try:
            self.pixel_spacing = [float(ds.PixelSpacing[0]), float(ds.PixelSpacing[1])]
        except:
            pass
        try:
            self.slice_thickness = float(ds.SliceThickness)
        except:
            pass

    def is_ct(self):
        return self.modality == "CT"

    def get_corte_axial(self, indice):   
        return self.volumen_3d[indice, :, :]

    def get_corte_coronal(self, indice): 
        return self.volumen_3d[:, indice, :]

    def get_corte_sagital(self, indice): 
        return self.volumen_3d[:, :, indice]

    def normalizar_uint8(self, imagen):
        """Normaliza cualquier imagen (HU o nativa) a uint8"""
        img = imagen.astype(np.float32)
        img_min, img_max = img.min(), img.max()
        if img_max - img_min == 0:
            return np.zeros_like(img, dtype=np.uint8)
        return ((img - img_min) / (img_max - img_min) * 255).astype(np.uint8)
    
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

    def transformacion_morfologica(self, indice_axial, tipo, tam_kernel):
        """Corregido typo + robustez"""
        corte = self.get_corte_axial(indice_axial)
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
        return operacion(corte_u8) if operacion else corte_u8

    def convertir_a_nifti(self, ruta_salida="salida.nii.gz"):
        if self.volumen_3d is None:
            raise ValueError("No hay volumen cargado.")
        try:
            nifti_img = nib.Nifti1Image(self.volumen_3d.astype(np.float32), affine=np.eye(4))
            nib.save(nifti_img, ruta_salida)
            return ruta_salida
        except Exception as e:
            raise RuntimeError(f"Error al guardar NIfTI: {str(e)}")

    def explore_folder(self):
        """Exploración completa del folder (inspirado en los snippets)"""
        if not self.ruta_carpeta:
            return {}
        # Aquí puedes implementar count_patients_and_studies o explore_modalities
        print(f"Exploración del folder: {self.ruta_carpeta}")
        print(f"Modalidad: {self.modality} | Slices: {len(self.archivos_dcm)}")
        return self.metadata

    def get_full_metadata(self):
        return self.metadata