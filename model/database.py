"""
Gestor de Base de Datos SQLite
"""

import sqlite3
from pathlib import Path
from model.paciente import Paciente


class DatabaseManager:
    """Maneja la persistencia de usuarios y pacientes."""

    def __init__(self, db_name="database/biomonitor.db"):
        self.db_path = Path(db_name)
        self.db_path.parent.mkdir(exist_ok=True)
        self.conn = sqlite3.connect(self.db_path)
        self._create_tables()

    def _create_tables(self):
        """Crea las tablas necesarias."""
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                rol TEXT NOT NULL CHECK(rol IN ('admin', 'user'))
            );

            CREATE TABLE IF NOT EXISTS pacientes (
                id INTEGER PRIMARY KEY,
                id_paciente TEXT UNIQUE,
                nombre TEXT,
                edad INTEGER,
                bpm REAL,
                spo2 REAL,
                temperatura REAL
            );
        """)
        self.conn.commit()

        # Usuario admin por defecto
        self.conn.execute("INSERT OR IGNORE INTO users (username, password, rol) VALUES ('admin', 'admin123', 'admin')")
        self.conn.commit()

    def login(self, username: str, password: str):
        """Valida usuario."""
        cursor = self.conn.execute("SELECT id, username, rol FROM users WHERE username = ? AND password = ?", 
                                   (username, password))
        return cursor.fetchone()

    def guardar_paciente(self, p: Paciente):
        """Guarda paciente."""
        self.conn.execute("""
            INSERT OR REPLACE INTO pacientes 
            (id_paciente, nombre, edad, bpm, spo2, temperatura)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (p.id_paciente, p.nombre, p.edad, p.bpm, p.spo2, p.temperatura))
        self.conn.commit()

    def cargar_pacientes(self):
        """Carga todos los pacientes."""
        cursor = self.conn.execute("SELECT * FROM pacientes")
        return [Paciente(row[1], row[2], row[3], row[4], row[5], row[6], row[0]) 
                for row in cursor.fetchall()]

    def cerrar(self):
        self.conn.close()