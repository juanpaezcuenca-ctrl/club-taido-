from ConexionBaseDatos import ConexionMysql


class Model_Maestro:
    def __init__(self):
        bd = ConexionMysql()
        self.conexion = bd.conexion
        self._bd      = bd

    def _cur(self):
        return self._bd.get_cursor()

    # ── Maestros ──────────────────────────────────────────────────────────────

    def obtener_maestros(self):
        c = self._cur()
        c.execute("SELECT id, nombre, correo FROM maestros")
        return [{"id": r[0], "nombre": r[1], "correo": r[2]} for r in c.fetchall()]

    def obtener_maestro(self, id):
        c = self._cur()
        c.execute("SELECT id, nombre, correo FROM maestros WHERE id = %s", (id,))
        return c.fetchone()

    def crear_maestro(self, nombre, correo, contrasena):
        c = self._cur()
        c.execute("INSERT INTO maestros (nombre, correo, contrasena) VALUES (%s, %s, %s)", (nombre, correo, contrasena))
        self.conexion.commit()

    def actualizar_maestro(self, id, nombre, correo, contrasena):
        c = self._cur()
        if contrasena:
            c.execute("UPDATE maestros SET nombre=%s, correo=%s, contrasena=%s WHERE id=%s", (nombre, correo, contrasena, id))
        else:
            c.execute("UPDATE maestros SET nombre=%s, correo=%s WHERE id=%s", (nombre, correo, id))
        self.conexion.commit()

    def eliminar_maestro(self, id):
        c = self._cur()
        c.execute("DELETE FROM maestros WHERE id = %s", (id,))
        self.conexion.commit()

    # ── Practicantes ──────────────────────────────────────────────────────────

    def obtener_practicante(self, id):
        c = self._cur()
        c.execute("SELECT id, nombre, correo, actividad FROM practicantes WHERE id = %s", (id,))
        return c.fetchone()

    def crear_practicante(self, nombre, correo, actividad, id_maestro, id_familia, contrasena):
        c = self._cur()
        c.execute(
            "INSERT INTO practicantes (nombre, correo, actividad, id_maestro, id_familia, contrasena) VALUES (%s,%s,%s,%s,%s,%s)",
            (nombre, correo, actividad, id_maestro, id_familia, contrasena)
        )
        self.conexion.commit()

    def actualizar_practicante(self, id, nombre, correo, actividad, id_maestro, id_familia, contrasena):
        c = self._cur()
        if contrasena:
            c.execute("UPDATE practicantes SET nombre=%s, correo=%s, actividad=%s, id_maestro=%s, id_familia=%s, contrasena=%s WHERE id=%s",
                      (nombre, correo, actividad, id_maestro, id_familia, contrasena, id))
        else:
            c.execute("UPDATE practicantes SET nombre=%s, correo=%s, actividad=%s, id_maestro=%s, id_familia=%s WHERE id=%s",
                      (nombre, correo, actividad, id_maestro, id_familia, id))
        self.conexion.commit()

    def eliminar_practicante(self, id):
        c = self._cur()
        c.execute("DELETE FROM practicantes WHERE id = %s", (id,))
        self.conexion.commit()

    # ── Eventos ───────────────────────────────────────────────────────────────

    def postearEvento(self, titulo, estado, tipo, fecha=None):
        c = self._cur()
        c.execute("INSERT INTO eventos (titulo, estado, tipo, fecha_evento) VALUES (%s,%s,%s,%s)", (titulo, estado, tipo, fecha))
        self.conexion.commit()

    def obtener_eventos(self):
        c = self._cur()
        c.execute("SELECT id, titulo, estado, tipo, fecha_evento FROM eventos")
        return [{"id": r[0], "titulo": r[1], "estado": r[2], "tipo": r[3], "fecha": str(r[4]) if r[4] else ""} for r in c.fetchall()]

    def eliminar_evento(self, id):
        c = self._cur()
        c.execute("DELETE FROM eventos WHERE id = %s", (id,))
        self.conexion.commit()

    # ── Pagos ─────────────────────────────────────────────────────────────────

    def obtener_pago(self, id_practicante):
        c = self._cur()
        c.execute("SELECT * FROM pagos WHERE id_practicante = %s", (id_practicante,))
        return c.fetchall()

    # ── Informes ─────────────────────────────────────────────────────────────

    def infrome_rendimiento(self, id_practicante, fecha_informe, comentarios):
        c = self._cur()
        c.execute("INSERT INTO informe_rendimiento (id_practicante, fecha_informe, comentarios) VALUES (%s,%s,%s)",
                  (id_practicante, fecha_informe, comentarios))
        self.conexion.commit()

    # ── Guías ─────────────────────────────────────────────────────────────────

    def publicar_guias(self, titulo, url_recurso, nivel, id_maestro):
        c = self._cur()
        c.execute("INSERT INTO guia_fundamento (titulo, url_recurso, nivel, id_maestro) VALUES (%s,%s,%s,%s)",
                  (titulo, url_recurso, nivel, id_maestro))
        self.conexion.commit()