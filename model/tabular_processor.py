"""
Procesador de Datos Tabulares - Optimizado
"""

import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from typing import List, Optional


class TabularProcessor:
    """
    Procesador optimizado para datasets grandes.
    """

    def __init__(self):
        self.df: Optional[pd.DataFrame] = None
        self.filename = None
        self.cached_describe = None

    def load_file(self, file_path: str) -> bool:
        """Carga archivo CSV o Excel de forma optimizada."""
        try:
            path = Path(file_path)
            self.filename = path.name

            if path.suffix.lower() == '.csv':
                self.df = pd.read_csv(path, low_memory=False)
            elif path.suffix.lower() in ['.xlsx', '.xls']:
                self.df = pd.read_excel(path)
            else:
                raise ValueError("Formato no soportado. Use .csv o .xlsx")

            # Optimización de tipos
            numeric_cols = self.df.select_dtypes(include=['number']).columns
            if len(numeric_cols) > 0:
                self.df[numeric_cols] = self.df[numeric_cols].astype('float32', errors='ignore')

            print(f"✅ Dataset cargado: {self.filename} | Shape: {self.df.shape}")
            return True

        except Exception as e:
            print(f"❌ Error al cargar archivo: {e}")
            return False

    def get_sample(self, n: int = 1000):
        """Retorna una muestra para mostrar en tabla (mejor rendimiento)."""
        if self.df is None:
            return pd.DataFrame()
        return self.df.head(n)

    def get_column_names(self) -> List[str]:
        """Columnas numéricas disponibles."""
        if self.df is None:
            return []
        return self.df.select_dtypes(include=['number']).columns.tolist()

    def plot_individual_columns(self, columns: List[str], fig=None):
        """Grafica columnas dentro de un Figure existente (para widget_4)"""
        if self.df is None or not columns:
            return False

        cols_to_plot = columns[:6]  # Máximo recomendado
        n = len(cols_to_plot)
        plot_cols = min(3, n)
        plot_rows = (n + plot_cols - 1) // plot_cols

        if fig is None:
            fig = plt.figure(figsize=(plot_cols*5.5, plot_rows*4))

        fig.clear()
        axes = fig.subplots(plot_rows, plot_cols)
        if n == 1:
            axes = [axes]
        else:
            axes = axes.ravel()

        for i, col in enumerate(cols_to_plot):
            self.df[col].plot(ax=axes[i], title=col, grid=True, linewidth=1.2)
            axes[i].set_xlabel("Índice")
            axes[i].set_ylabel("Valor")

        for j in range(i + 1, len(axes)):
            axes[j].axis('off')

        fig.suptitle(f"Gráficos Individuales - {self.filename}", fontsize=14)
        fig.tight_layout()
        return True

    def scatter_plot(self, col_x: str, col_y: str, fig=None):
        """Scatter dentro de un Figure existente"""
        if self.df is None:
            return False

        if fig is None:
            fig = plt.figure(figsize=(8, 6))

        fig.clear()
        ax = fig.add_subplot(111)
        ax.scatter(self.df[col_x], self.df[col_y], alpha=0.7, s=25)
        ax.set_title(f"Scatter: {col_x} vs {col_y}")
        ax.set_xlabel(col_x)
        ax.set_ylabel(col_y)
        ax.grid(True, alpha=0.3)
        fig.tight_layout()
        return True

    def get_info_describe(self):
        """Retorna info() y describe()."""
        if self.df is None:
            return None, None

        if self.cached_describe is None:
            self.cached_describe = self.df.describe()

        return self.df.info(buf=None), self.cached_describe