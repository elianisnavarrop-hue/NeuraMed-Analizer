"""
Procesador de Datos Tabulares (CSV / Excel)
"""

import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from typing import List, Tuple, Optional


class TabularProcessor:
    """
    Clase responsable de cargar y visualizar datos tabulares.
    """

    def __init__(self):
        self.df: Optional[pd.DataFrame] = None
        self.filename = None

    def load_file(self, file_path: str) -> bool:
        """
        Carga archivo CSV o Excel.
        """
        try:
            path = Path(file_path)
            self.filename = path.name

            if path.suffix.lower() == '.csv':
                self.df = pd.read_csv(path)
            elif path.suffix.lower() in ['.xlsx', '.xls']:
                self.df = pd.read_excel(path)
            else:
                raise ValueError("Formato no soportado. Use .csv o .xlsx")

            print(f"✅ Archivo tabular cargado: {self.filename} | Shape: {self.df.shape}")
            return True

        except Exception as e:
            print(f"Error cargando archivo tabular: {e}")
            return False

    def get_column_names(self) -> List[str]:
        """Retorna columnas numéricas disponibles."""
        if self.df is None:
            return []
        return self.df.select_dtypes(include=['number']).columns.tolist()

    def plot_individual_columns(self, columns: List[str]):
        """Grafica cada columna seleccionada de forma individual."""
        if self.df is None:
            return

        n = len(columns)
        cols = min(3, n)
        rows = (n + cols - 1) // cols

        fig, axes = plt.subplots(rows, cols, figsize=(cols*5, rows*4))
        if n == 1:
            axes = [axes]
        else:
            axes = axes.ravel()

        for i, col in enumerate(columns):
            self.df[col].plot(ax=axes[i], title=col, grid=True)
            axes[i].set_xlabel("Índice")
            axes[i].set_ylabel("Valor")

        for j in range(i + 1, len(axes)):
            axes[j].axis('off')

        plt.tight_layout()
        plt.suptitle(f"Análisis Individual - {self.filename}", fontsize=14)
        plt.show()

    def scatter_plot(self, col_x: str, col_y: str):
        """Genera gráfico de dispersión."""
        if self.df is None:
            return
        plt.figure(figsize=(8, 6))
        plt.scatter(self.df[col_x], self.df[col_y], alpha=0.7)
        plt.title(f"Scatter: {col_x} vs {col_y}")
        plt.xlabel(col_x)
        plt.ylabel(col_y)
        plt.grid(True)
        plt.show()

    def get_info_describe(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Retorna info() y describe()."""
        if self.df is None:
            return pd.DataFrame(), pd.DataFrame()

        info_data = {
            'Column': self.df.columns,
            'Non-Null Count': self.df.count().values,
            'Dtype': self.df.dtypes.values
        }
        info_df = pd.DataFrame(info_data)
        describe_df = self.df.describe()

        return info_df, describe_df