"""
SignalProcessor - Modelo (MVC)
"""

import scipy.io as sio
import numpy as np
from scipy import signal
from pathlib import Path
from typing import Tuple, List
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from scipy.signal import find_peaks, hilbert


class SignalProcessor:
    def __init__(self):
        self.data_3d = None
        self.data_2d = None
        self.fs = 1000.0
        self.filename = None
        self.events: List[float] = []

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
        
    def detect_events(self, canal: int = 0, signal_type: str = "ECG") -> List[float]:
        """Detecta eventos según el tipo de señal"""
        if self.data_2d is None:
            return []

        data = self.data_2d[canal].copy()

        if signal_type.upper() == "ECG":
            # Detector inspirado en ECGEventDetector
            height = np.mean(data) + 0.6 * np.std(data)
            distance = int(self.fs * 0.6)  # ~600ms entre latidos
            peaks, _ = find_peaks(data, height=height, distance=distance, prominence=0.3)
        else:  # EMG u otros
            # Detector inspirado en EMGEventDetector
            analytic_signal = hilbert(data)
            envelope = np.abs(analytic_signal)
            threshold = np.mean(envelope) + 1.8 * np.std(envelope)
            distance = int(self.fs * 0.15)
            peaks, _ = find_peaks(envelope, height=threshold, distance=distance)

        self.events = (peaks / self.fs).tolist()
        print(f"🔍 Detectados {len(self.events)} eventos en canal {canal}")
        return self.events

    def get_signal_segment(self, canal: int = 0, inicio: int = 0, fin: int = None) -> Tuple[np.ndarray, np.ndarray]:
        if self.data_2d is None:
            return None, None
        fin = fin or self.data_2d.shape[1]
        segmento = self.data_2d[canal, inicio:fin].copy()
        tiempo = np.arange(inicio, fin) / self.fs
        return segmento, tiempo

    def agregar_ruido(self, canal: int = 0, noise_level: float = 0.20) -> Tuple[np.ndarray, np.ndarray]:
        """Aplica ruido de forma persistente en el modelo"""
        if self.data_2d is None:
            return None, None
        
        original = self.data_2d[canal].copy()
        std = np.std(original)
        noise = np.random.normal(0, noise_level * std, len(original))
        noisy = original + noise
        
        # Aplicar persistentemente
        self.data_2d[canal] = noisy
        print(f"Ruido aplicado (nivel {noise_level*100:.0f}%) en canal {canal}")
        return original, noisy

    def plot_original_vs_noisy(self, canal: int = 0, inicio: int = 0, fin: int = None, noise_level: float = 0.20) -> Figure:
        """Genera gráfico comparativo usando los datos actuales del modelo"""
        if self.data_2d is None:
            fig = Figure(figsize=(11, 7))
            ax = fig.add_subplot(111)
            ax.text(0.5, 0.5, "No hay señal cargada", ha='center', va='center', fontsize=14)
            return fig

        fin = fin or self.data_2d.shape[1]
        # Usar los datos ya modificados (con ruido)
        original = self.data_2d[canal, inicio:fin].copy() 
        
        std = np.std(original)
        noise = np.random.normal(0, noise_level * std, len(original))
        noisy = original + noise

        tiempo = np.arange(inicio, fin) / self.fs

        fig = Figure(figsize=(11, 7))
        
        ax1 = fig.add_subplot(211)
        ax1.plot(tiempo, original, 'b-', linewidth=1.8, label='Señal Original')
        ax1.set_title("**Señal Original**", fontsize=14, fontweight='bold')
        ax1.set_xlabel("Tiempo (segundos)", fontsize=12, fontweight='bold')
        ax1.set_ylabel("Amplitud (µV)", fontsize=12, fontweight='bold')
        ax1.grid(True, alpha=0.3)
        ax1.legend()

        ax2 = fig.add_subplot(212)
        ax2.plot(tiempo, noisy, 'r-', linewidth=1.8, label='Señal con Ruido')
        ax2.set_title("**Señal con Ruido Agregado**", fontsize=14, fontweight='bold')
        ax2.set_xlabel("Tiempo (segundos)", fontsize=12, fontweight='bold')
        ax2.set_ylabel("Amplitud (µV)", fontsize=12, fontweight='bold')
        ax2.grid(True, alpha=0.3)
        ax2.legend()

        fig.tight_layout()
        return fig

    def compute_statistics(self, axis: int = 0) -> Tuple[np.ndarray, np.ndarray, str]:
        if self.data_3d is None:
            return None, None, "No hay datos cargados"

        mean = np.mean(self.data_3d, axis=axis)
        std = np.std(self.data_3d, axis=axis)
        
        stats_text = f"""Estadísticas (Eje {axis}):
----------------------------------------
Promedio:     {mean.mean():.4f} ± {mean.std():.4f}
Desviación:   {std.mean():.4f} ± {std.std():.4f}
Máximo:       {np.max(mean):.4f}
Mínimo:       {np.min(mean):.4f}
Total canales: {self.data_3d.shape[0]}
Total muestras: {self.data_3d.shape[1]}"""
        return mean, std, stats_text

    def plot_signal(self, canal: int = 0, inicio: int = 0, fin: int = None, detect_events: bool = True) -> Figure:
        segmento, tiempo = self.get_signal_segment(canal, inicio, fin)
        if segmento is None:
            fig = Figure()
            ax = fig.add_subplot(111)
            ax.text(0.5, 0.5, "No hay señal cargada", ha='center', va='center')
            return fig

        fig = Figure(figsize=(11, 6))
        ax = fig.add_subplot(111)
        ax.plot(tiempo, segmento, 'b-', linewidth=1.8, label='Señal')

        # Marcar eventos/anomalías
        if detect_events and self.events:
            events_in_range = [e for e in self.events if inicio/self.fs <= e <= fin/self.fs]
            for event_time in events_in_range:
                ax.axvline(x=event_time, color='red', linestyle='--', alpha=0.7, linewidth=1.5)
                ax.plot(event_time, segmento[int((event_time*self.fs) - inicio)], 
                       'ro', markersize=8, label='Evento' if events_in_range.index(event_time)==0 else "")

        ax.set_title(f"**Canal {canal} - {self.filename or 'Señal'}**", fontsize=14, fontweight='bold')
        ax.set_xlabel("Tiempo (segundos)", fontsize=12, fontweight='bold')
        ax.set_ylabel("Amplitud (µV)", fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.legend()
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