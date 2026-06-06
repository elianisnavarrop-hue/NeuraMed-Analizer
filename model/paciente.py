"""
Modelo de Paciente.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Paciente:
    """Representa un paciente con sus signos vitales."""
    id_paciente: str
    nombre: str
    edad: int
    bpm: float = 0.0
    spo2: float = 0.0
    temperatura: float = 0.0
    id_db: Optional[int] = None

    def calcular_riesgo(self) -> str:
        """Calcula el nivel de riesgo biomédico."""
        if self.spo2 < 90 or self.bpm > 120 or self.bpm < 50 or self.temperatura > 39.0:
            return "Crítico"
        elif self.spo2 < 94 or self.bpm > 100 or self.temperatura > 37.5:
            return "Alerta"
        return "Normal"

    def get_color(self) -> str:
        """Retorna estilo CSS según el riesgo."""
        riesgo = self.calcular_riesgo()
        if riesgo == "Crítico":
            return "background-color: #ff4444; color: white;"
        elif riesgo == "Alerta":
            return "background-color: #ffaa00; color: black;"
        return "background-color: #44ff88; color: black;"