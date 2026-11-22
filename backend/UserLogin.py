from flask_login import UserMixin
from werkzeug.security import check_password_hash


class User(UserMixin):
    def __init__(self, id, nombre, correo, contrasena, tipo_usuario):
        self.id = id
        self.nombre = nombre
        self.correo = correo
        self.password = contrasena
        self.tipo_usuario = tipo_usuario

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def es_maestro(self):
        return self.tipo_usuario == "maestro"

    def es_practicante(self):
        return self.tipo_usuario == "practicante"

    def es_familia(self):
        return self.tipo_usuario == "familia"

    def __repr__(self):
        return f"<User {self.correo} ({self.tipo_usuario})>"