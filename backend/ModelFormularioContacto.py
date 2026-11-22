from ConexionBaseDatos import ConexionMysql


class Model_FormularioContacto:
    def __init__(self):
        self.mibasededatos = ConexionMysql()
        self.conexion = self.mibasededatos.conexion
        self.cursor = self.mibasededatos.cursor

    def insertar(self, nombre, correo, telefono, texto, sede):
        sql = "INSERT INTO formulario_contacto (nombre, correo, telefono, texto, sede) VALUES (%s, %s, %s, %s, %s)"
        self.cursor.execute(sql, (nombre, correo, telefono, texto, sede))
        self.conexion.commit()
