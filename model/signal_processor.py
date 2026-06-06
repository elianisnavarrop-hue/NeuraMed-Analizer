"""
Procesador de Señales Biomédicas (.mat) - Especializado en EEG
"""

import scipy.io as sio
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Tuple, Optional


class SignalProcessor:
    """
    Clase encargada de cargar, procesar y visualizar señales biomédicas 
    desde archivos .mat (principalmente EEG).
    """

    def __init__(self):
        self.data_3d = None      # Matriz original (ensayos, canales, muestras)
        self.data_2d = None      # Matriz reshapeada (canales, muestras)
        self.fs = 1000.0         # Frecuencia de muestreo por defecto (1kHz)
        self.filename = None

    def load_mat_file(self, file_path: str) -> bool:
        """
        Carga un archivo .mat y prepara las matrices 3D y 2D.
        """
        try:
            mat = sio.loadmat(file_path)
            self.filename = Path(file_path).name

            # Buscar la clave principal que contiene la señal
            key = None
            for k in mat.keys():
                if not k.startswith('__') and isinstance(mat[k], np.ndarray) and mat[k].ndim >= 2:
                    key = k
                    break

            if key is None:
                raise ValueError("No se encontró una señal válida en el archivo .mat")

            self.data_3d = mat[key]

            # Convertir a 2D para facilitar el procesamiento de canales
            if self.data_3d.ndim == 3:
                self.data_2d = self.data_3d.reshape(self.data_3d.shape[0], -1)
            else:
                self.data_2d = self.data_3d

            print(f"✅ Señal cargada correctamente: {self.filename}")
            print(f"   Dimensiones 3D: {self.data_3d.shape} | Dimensiones 2D: {self.data_2d.shape}")
            return True

        except Exception as e:
            print(f"❌ Error al cargar archivo .mat: {e}")
            return False

    def select_channel_segment(self, channel: int, start: int, end: int) -> np.ndarray:
        """Selecciona un segmento de un canal específico."""
        if self.data_2d is None:
            return None
        return self.data_2d[channel, start:end]

    def add_noise_to_channel(self, channel: int, noise_level: float = 0.05) -> Tuple[np.ndarray, np.ndarray]:
        """Añade ruido gaussiano a un canal específico."""
        if self.data_2d is None:
            return None, None
        
        original = self.data_2d[channel].copy()
        noise = np.random.normal(0, noise_level * np.std(original), len(original))
        noisy = original + noise
        
        return original, noisy

    def compute_mean_std(self, axis: int = 0) -> Tuple[np.ndarray, np.ndarray]:
        """Calcula promedio y desviación estándar a lo largo de un eje."""
        if self.data_3d is None:
            return None, None
        mean = np.mean(self.data_3d, axis=axis)
        std = np.std(self.data_3d, axis=axis)
        return mean, std

    def plot_channel(self, channel: int, start: int = 0, end: Optional[int] = None):
        """Visualiza un canal específico de la señal."""
        if self.data_2d is None:
            return
        segment = self.data_2d[channel, start:end]
        plt.figure(figsize=(12, 5))
        plt.plot(segment)
        plt.title(f"Canal {channel} - {self.filename}")
        plt.xlabel("Muestras")
        plt.ylabel("Amplitud (µV)")
        plt.grid(True)
        plt.show()

    def plot_mean_std(self):
        """Grafica promedio y desviación estándar por canal (stem plots)."""
        if self.data_3d is None:
            return
        mean, std = self.compute_mean_std(axis=1)  # Promedio por canal

        fig, axs = plt.subplots(1, 2, figsize=(12, 5))
        
        axs[0].stem(mean)
        axs[0].set_title("Promedio por Canal")
        axs[0].set_xlabel("Canal")
        axs[0].set_ylabel("Amplitud Media (µV)")
        axs[0].grid(True)

        axs[1].stem(std)
        axs[1].set_title("Desviación Estándar por Canal")
        axs[1].set_xlabel("Canal")
        axs[1].set_ylabel("Desviación Estándar (µV)")
        axs[1].grid(True)

        plt.tight_layout()
        plt.show()