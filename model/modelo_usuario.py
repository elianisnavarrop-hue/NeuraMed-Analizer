#Maneja la conexión con MongoDB y la validación de usuarios.

from pymongo import MongoClient
from datetime import datetime

class ModeloUsuario:      #se conecta a MongoDB y maneja: validación de login, registro de sesiones con foto
    def __init__(self):
        # Conectamos a MongoDB Atlas (nube)
        CADENA_CONEXION = (
            "mongodb+srv://neuramed:neuramed2026"
            "@cluster0.sjxwdxi.mongodb.net/"
            "?retryWrites=true&w=majority&appName=Cluster0"
        )
        self.cliente = MongoClient(CADENA_CONEXION)
        self.db = self.cliente["neuramed_db"]

        # Colecciones
        self.col_usuarios = self.db["usuarios"]
        self.col_sesiones = self.db["sesiones"]

        # Usuario activo después del login
        self.usuario_activo = None

        # Creamos usuarios de prueba si la colección está vacía
        self._crear_usuarios_iniciales()

    def _crear_usuarios_iniciales(self):     #Crea usuarios de prueba en MongoDB si no existen.

        if self.col_usuarios.count_documents({}) == 0:
            usuarios = [
                {
                    "id": "001",
                    "nombre": "admin",
                    "contrasena": "admin123",
                    "rol": "administrador"
                },
                {
                    "id": "002",
                    "nombre": "usuario1",
                    "contrasena": "user123",
                    "rol": "usuario"
                }
            ]
            self.col_usuarios.insert_many(usuarios)
            print("Usuarios iniciales creados en MongoDB.")

    def validar_login(self, usuario, contrasena):    #Busca el usuario en MongoDB y valida la contraseña.
    
        # Buscamos por nombre de usuario O por id
        resultado = self.col_usuarios.find_one({
            "$or": [
                {"nombre": usuario},
                {"id": usuario}
            ],
            "contrasena": contrasena
        })

        if resultado:
            self.usuario_activo = resultado
            return resultado
        
    def registrar_sesion(self, ruta_foto):    #guarda en MongoDB el registro de la sesión con la ruta de la foto y la fecha/hora.
        if self.usuario_activo is None:
            raise ValueError("No hay usuario activo.")
        sesion = {
            "id_usuario": self.usuario_activo["id"],
            "nombre": self.usuario_activo["nombre"],
            "ruta_foto": ruta_foto,
            "fecha_sesion": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.col_sesiones.insert_one(sesion)
        return sesion   
        
    def get_usuario_activo(self):
        return self.usuario_activo
