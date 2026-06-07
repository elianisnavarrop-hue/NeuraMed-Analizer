"""
SignalProcessor - Modelo (MVC)
"""

import scipy.io as sio
import numpy as np
from scipy import signal
from pathlib import Path
from typing import Tuple, Optional
import matplotlib.pyplot as plt
from matplotlib.figure import Figure


class SignalProcessor:
    def __init__(self):
        self.data_3d = None
        self.data_2d = None
        self.fs = 1000.0
        self.filename = None

    def load_mat_file(self, file_path: str) -> bool:
        try:
            mat = sio.loadmat(file_path)
            self.filename = Path(file_path).name

            key = next((k for k in mat.keys() if not k.startswith('__') 
                       and isinstance(mat[k], np.ndarray) and mat[k].ndim >= 2), None)
            if not key:
                raise ValueError("No se encontró señal válida")

            self.data_3d = mat[key]
            self.data_2d = self.data_3d.reshape(self.data_3d.shape[0], -1) if self.data_3d.ndim == 3 else self.data_3d

            if 'fs' in mat:
                self.fs = float(mat['fs'].flatten()[0])

            print(f"✅ Señal cargada: {self.filename} | Shape: {self.data_2d.shape}")
            return True
        except Exception as e:
            print(f"❌ Error: {e}")
            return False

    def get_signal_segment(self, canal: int = 0, inicio: int = 0, fin: int = None) -> Tuple[np.ndarray, np.ndarray]:
        if self.data_2d is None:
            return None, None
        fin = fin or self.data_2d.shape[1]
        segmento = self.data_2d[canal, inicio:fin].copy()
        tiempo = np.arange(inicio, fin) / self.fs
        return segmento, tiempo

    def agregar_ruido(self, canal: int = 0, noise_level: float = 0.05) -> Tuple[np.ndarray, np.ndarray]:
        if self.data_2d is None:
            return None, None
        original = self.data_2d[canal].copy()
        noise = np.random.normal(0, noise_level * np.std(original), len(original))
        noisy = original + noise
        self.data_2d[canal] = noisy
        return original, noisy

    def compute_statistics(self, axis: int = 0) -> Tuple[np.ndarray, np.ndarray, str]:
        if self.data_3d is None:
            return None, None, ""
        mean = np.mean(self.data_3d, axis=axis)
        std = np.std(self.data_3d, axis=axis)
        
        stats_text = f"""Estadísticas (Eje {axis}):
Promedio:     {mean.mean():.4f} ± {mean.std():.4f}
Desviación:   {std.mean():.4f} ± {std.std():.4f}
Máximo:       {np.max(mean):.4f}
Mínimo:       {np.min(mean):.4f}"""
        return mean, std, stats_text

    def plot_signal(self, canal: int = 0, inicio: int = 0, fin: int = None) -> Figure:
        """Retorna Figure con la señal"""
        segmento, tiempo = self.get_signal_segment(canal, inicio, fin)
        if segmento is None:
            fig = Figure()
            ax = fig.add_subplot(111)
            ax.text(0.5, 0.5, "No hay señal cargada", ha='center')
            return fig

        fig = Figure(figsize=(11, 6))
        ax = fig.add_subplot(111)
        ax.plot(tiempo, segmento, 'b-', linewidth=1.5, label='Señal')
        ax.set_title(f"Canal {canal} - {self.filename or 'Señal'}")
        ax.set_xlabel("Tiempo (segundos)")
        ax.set_ylabel("Amplitud")
        ax.grid(True)
        ax.legend()
        return fig

    def plot_original_vs_noisy(self, original: np.ndarray, noisy: np.ndarray) -> Figure:
        """Retorna Figure comparando original vs ruido"""
        fig = Figure(figsize=(11, 6))
        ax1 = fig.add_subplot(211)
        ax1.plot(original, 'b-', label='Original')
        ax1.set_title("Señal Original")
        ax1.legend()
        ax1.grid(True)

        ax2 = fig.add_subplot(212)
        ax2.plot(noisy, 'r-', label='Con Ruido')
        ax2.set_title("Señal con Ruido")
        ax2.legend()
        ax2.grid(True)

        fig.tight_layout()
        return fig

    def plot_statistics(self, mean: np.ndarray, std: np.ndarray) -> Figure:
        """Retorna Figure con estadísticas"""
        fig = Figure(figsize=(11, 5))
        ax1 = fig.add_subplot(121)
        ax1.stem(mean)
        ax1.set_title("Media por Canal / Muestra")

        ax2 = fig.add_subplot(122)
        ax2.stem(std)
        ax2.set_title("Desviación Estándar")

        fig.tight_layout()
        return fig

    def get_channel_count(self) -> int:
        return self.data_2d.shape[0] if self.data_2d is not None else 0

    def get_sample_count(self) -> int:
        return self.data_2d.shape[1] if self.data_2d is not None else 0