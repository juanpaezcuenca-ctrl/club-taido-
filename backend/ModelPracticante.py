from ConexionBaseDatos import ConexionMysql


class Model_Practicante:
    def __init__(self):
        bd = ConexionMysql()
        self.conexion = bd.conexion
        self._bd      = bd

    def _cur(self):
        return self._bd.get_cursor()

    def actualizar_practicante(self, correo, contrasena):
        c = self._cur()
        c.execute("UPDATE practicantes SET contrasena = %s WHERE correo = %s", (contrasena, correo))
        self.conexion.commit()

    def obtener_eventos_actuales(self):
        c = self._cur()
        c.execute("SELECT id, titulo, estado, tipo FROM eventos WHERE estado = 'En curso'")
        return [{"id": r[0], "titulo": r[1], "estado": r[2], "tipo": r[3]} for r in c.fetchall()]

    def obtener_eventos_proximos(self):
        c = self._cur()
        c.execute("SELECT id, titulo, estado, tipo FROM eventos WHERE estado = 'Proximo'")
        return [{"id": r[0], "titulo": r[1], "estado": r[2], "tipo": r[3]} for r in c.fetchall()]

    def obtener_eventos_pasado(self):
        c = self._cur()
        c.execute("SELECT id, titulo, estado, tipo FROM eventos WHERE estado = 'Pasado'")
        return [{"id": r[0], "titulo": r[1], "estado": r[2], "tipo": r[3]} for r in c.fetchall()]

    def obtener_galeria(self):
        c = self._cur()
        c.execute("SELECT * FROM galeria ORDER BY id ASC")
        return c.fetchall()

    def obtener_guias(self):
        c = self._cur()
        c.execute("SELECT id, titulo, nivel, url_recurso FROM guia_fundamento")
        return [{"id": r[0], "titulo": r[1], "nivel": r[2], "url_recurso": r[3]} for r in c.fetchall()]

    def obtener_guia(self, titulo):
        c = self._cur()
        c.execute("SELECT * FROM guia_fundamento WHERE titulo = %s", (titulo,))
        return c.fetchone()

    def obtener_rendimiento(self, id_practicante):
        c = self._cur()
        c.execute(
            "SELECT ir.id, p.nombre, ir.fecha_informe, ir.comentarios FROM informe_rendimiento ir LEFT JOIN practicantes p ON ir.id_practicante = p.id WHERE ir.id_practicante = %s ORDER BY ir.id DESC",
            (id_practicante,)
        )
        return [{"id": r[0], "practicante": r[1], "torneo": r[2], "comentarios": r[3]} for r in c.fetchall()]

    def obtener_estado_pagos(self, id_practicante):
        c = self._cur()
        c.execute(
            "SELECT p.id, pr.nombre, p.pago_de, p.monto, p.comprobante FROM pagos p LEFT JOIN practicantes pr ON p.id_practicante = pr.id WHERE p.id_practicante = %s ORDER BY p.id DESC",
            (id_practicante,)
        )
        return [{"id": r[0], "practicante": r[1], "concepto": r[2], "monto": r[3], "comprobante": r[4]} for r in c.fetchall()]

    def crear_pago(self, id_practicante, pago_de, monto, comprobante):
        c = self._cur()
        c.execute("INSERT INTO pagos (id_practicante, pago_de, monto, comprobante) VALUES (%s,%s,%s,%s)",
                  (id_practicante, pago_de, monto, comprobante))
        self.conexion.commit()