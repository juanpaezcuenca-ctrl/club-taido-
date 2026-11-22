import os
import mysql.connector
from mysql.connector import Error

_conexion_global = None


def get_conexion():
    global _conexion_global
    try:
        if _conexion_global is None or not _conexion_global.is_connected():
            _conexion_global = mysql.connector.connect(
                host=os.environ.get("DB_HOST", "localhost"),
                port=int(os.environ.get("DB_PORT", 3306)),
                user=os.environ.get("DB_USER", "root"),
                password=os.environ.get("DB_PASSWORD", ""),
                database=os.environ.get("DB_NAME", "taekwondo"),
                autocommit=False
            )
        else:
            _conexion_global.ping(reconnect=True, attempts=5, delay=1)
    except Error as e:
        print(f"Error MySQL: {e}")
        _conexion_global = None
    return _conexion_global


def get_cursor():
    conexion = get_conexion()
    if conexion is None:
        raise Exception("Sin conexion a MySQL.")
    try:
        cursor = conexion.cursor()
        return cursor, conexion
    except Error:
        global _conexion_global
        _conexion_global = None
        conexion = get_conexion()
        return conexion.cursor(), conexion


class ConexionMysql:
    def __init__(self):
        self.conexion = get_conexion()
        if self.conexion:
            self.cursor = self.conexion.cursor()
        else:
            self.cursor = None
        self._bd = self

    def get_cursor(self):
        cursor, conexion = get_cursor()
        self.conexion = conexion
        self.cursor = cursor
        return self.cursor