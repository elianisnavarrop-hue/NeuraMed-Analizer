"""
Procesador de Datos Tabulares
"""

import pandas as pd
import numpy as np
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
        """Retorna una muestra para mostrar en tabla."""
        if self.df is None:
            return pd.DataFrame()
        return self.df.head(n)

    def get_column_names(self) -> List[str]:
        """Columnas numéricas disponibles."""
        if self.df is None:
            return []
        return self.df.select_dtypes(include=['number']).columns.tolist()

    def plot_individual_columns(self, columns: List[str], fig=None):
        """
        Grafica columnas individuales de forma inteligente y robusta:
        - Numéricas → Line plot + histograma en el mismo eje
        - Categóricas → Countplot con etiquetas
        """
        if self.df is None or not columns:
            return False

        # Filtrar columnas existentes
        cols_to_plot = [col for col in columns if col in self.df.columns][:6]
        n = len(cols_to_plot)
        if n == 0:
            return False

        plot_cols = min(3, n)
        plot_rows = (n + plot_cols - 1) // plot_cols

        if fig is None:
            fig = plt.figure(figsize=(plot_cols * 6.5, plot_rows * 5), dpi=110)
        else:
            fig.clear()

        axes = fig.subplots(plot_rows, plot_cols, squeeze=False)
        axes = axes.ravel()

        colors = plt.cm.tab10.colors

        for i, col in enumerate(cols_to_plot):
            ax = axes[i]
            data = self.df[col]
            
            if pd.api.types.is_numeric_dtype(data):
                # ==================== VARIABLE NUMÉRICA ====================
                # Line plot principal
                ax.plot(data.index, data.values, 
                       color=colors[i % len(colors)], 
                       linewidth=2.2, alpha=0.9, label='Serie temporal')

                # Histograma en el mismo eje (mejor que twinx)
                ax.hist(data.dropna(), bins=30, alpha=0.35, 
                       color=colors[(i+3) % len(colors)], 
                       label='Distribución')

                ax.set_title(f"{col} (Numérica)", fontsize=13, fontweight='bold')
                ax.set_xlabel("Índice")
                ax.set_ylabel("Valor")
                ax.legend(fontsize=9)
                ax.grid(True, linestyle='--', alpha=0.4)

            else:
                # ==================== VARIABLE CATEGÓRICA ====================
                value_counts = data.value_counts().sort_values(ascending=False)
                
                bars = ax.bar(value_counts.index.astype(str), value_counts.values, 
                             color=colors[i % len(colors)], alpha=0.85, edgecolor='black')

                ax.set_title(f"{col} (Categórica)", fontsize=13, fontweight='bold')
                ax.set_xlabel("Categoría")
                ax.set_ylabel("Frecuencia")
                ax.tick_params(axis='x', rotation=45)

                # Etiquetas de valor encima de las barras
                for bar in bars:
                    height = bar.get_height()
                    ax.annotate(f'{int(height)}', 
                               xy=(bar.get_x() + bar.get_width()/2, height),
                               xytext=(0, 3), textcoords="offset points",
                               ha='center', va='bottom', fontsize=10, fontweight='bold')

            ax.set_facecolor('#f8f9fa')

        # Ocultar ejes sobrantes
        for j in range(i + 1, len(axes)):
            axes[j].axis('off')

        fig.suptitle(f"Análisis Individual de Variables\n{self.filename}", 
                    fontsize=16, fontweight='bold', y=0.98)
        fig.tight_layout(rect=[0, 0, 1, 0.95])

        return True

    def scatter_plot(self, col_x: str, col_y: str, fig=None):
        """
        Scatter Plot inteligente:
        - Ambos numéricos → scatter clásico + regresión
        - Uno categórico → usa colores/grupos o jitter en eje X
        """
        if self.df is None:
            return False

        if col_x not in self.df.columns or col_y not in self.df.columns:
            print(f"❌ Columnas no encontradas: {col_x} o {col_y}")
            return False

        df_clean = self.df[[col_x, col_y]].dropna()

        if len(df_clean) < 2:
            print("❌ No hay suficientes datos después de eliminar NaNs")
            return False

        # Crear figura
        if fig is None:
            fig = plt.figure(figsize=(11, 8), dpi=110)
        else:
            fig.clear()

        ax = fig.add_subplot(111)

        is_x_numeric = pd.api.types.is_numeric_dtype(df_clean[col_x])
        is_y_numeric = pd.api.types.is_numeric_dtype(df_clean[col_y])

        # === CASO 1: Ambos numéricos ===
        if is_x_numeric and is_y_numeric:
            scatter = ax.scatter(
                df_clean[col_x], df_clean[col_y],
                alpha=0.75, s=70, color='#1f77b4', edgecolors='white', linewidth=0.8
            )

            # Regresión lineal
            x = df_clean[col_x].values
            y = df_clean[col_y].values
            A = np.vstack([x, np.ones(len(x))]).T
            m, c = np.linalg.lstsq(A, y, rcond=None)[0]

            x_line = np.linspace(x.min(), x.max(), 100)
            ax.plot(x_line, m * x_line + c, 'r--', linewidth=2.5, 
                   label=f'Tendencia (y = {m:.3f}x + {c:.2f})')

        # === CASO 2: X categórico, Y numérico (el más común) ===
        elif not is_x_numeric and is_y_numeric:
            # Strip plot con jitter + colores por categoría
            categories = df_clean[col_x].astype(str)
            unique_cats = categories.unique()
            
            colors = plt.cm.tab10(np.linspace(0, 1, len(unique_cats)))
            
            for i, cat in enumerate(unique_cats):
                mask = categories == cat
                y_vals = df_clean.loc[mask, col_y]
                x_pos = np.full(len(y_vals), i) + np.random.normal(0, 0.08, len(y_vals))  # jitter
                
                ax.scatter(x_pos, y_vals, alpha=0.8, s=65, 
                          color=colors[i], edgecolors='black', linewidth=0.6, label=cat)

            ax.set_xticks(range(len(unique_cats)))
            ax.set_xticklabels(unique_cats, rotation=45, ha='right')

        # === CASO 3: Y categórico, X numérico ===
        elif is_x_numeric and not is_y_numeric:
            # Similar pero invertido
            categories = df_clean[col_y].astype(str)
            unique_cats = categories.unique()
            colors = plt.cm.tab10(np.linspace(0, 1, len(unique_cats)))
            
            for i, cat in enumerate(unique_cats):
                mask = categories == cat
                x_vals = df_clean.loc[mask, col_x]
                y_pos = np.full(len(x_vals), i) + np.random.normal(0, 0.08, len(x_vals))
                
                ax.scatter(x_vals, y_pos, alpha=0.8, s=65, 
                          color=colors[i], edgecolors='black', linewidth=0.6, label=cat)

            ax.set_yticks(range(len(unique_cats)))
            ax.set_yticklabels(unique_cats)

        else:
            print("❌ Ambas columnas son categóricas. No se puede hacer scatter.")
            return False

        # === Estilo general ===
        corr = df_clean[col_x].corr(df_clean[col_y]) if is_x_numeric and is_y_numeric else None
        
        title = f'Relación entre {col_x} y {col_y}'
        if corr is not None:
            title += f' (Corr: {corr:.3f})'

        ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
        ax.set_xlabel(col_x, fontsize=13, fontweight='bold')
        ax.set_ylabel(col_y, fontsize=13, fontweight='bold')

        ax.grid(True, linestyle='--', alpha=0.5)
        ax.set_facecolor('#f8f9fa')
        
        if len(ax.get_legend_handles_labels()[0]) > 0:
            ax.legend(title="Categorías", fontsize=10, loc='best')

        fig.suptitle(f"Scatter Plot - {self.filename}", fontsize=14, fontweight='bold')
        fig.tight_layout()

        return True

    def get_info_describe(self):
        """Retorna info() y describe()."""
        if self.df is None:
            return None, None

        if self.cached_describe is None:
            self.cached_describe = self.df.describe()

        return self.df.info(buf=None), self.cached_describe