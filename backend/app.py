import os
from datetime import date
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from flask_login import LoginManager, logout_user, login_required

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
except ImportError:
    pass

from ConexionBaseDatos import get_cursor
from UserLogin import User
from ModelMaestro import Model_Maestro
from ModelPracticante import Model_Practicante
from ModelFamilia import Model_Familia
from ModelFormularioContacto import Model_FormularioContacto
from mail_contacto import enviar_aviso_formulario

app = Flask(__name__)
_secret = os.environ.get('SECRET_KEY')
if not _secret:
    import secrets
    _secret = secrets.token_hex(32)
    print('AVISO: define SECRET_KEY en .env (las sesiones se reinician con cada arranque).')
app.config['SECRET_KEY'] = _secret
CORS(app)
login_manager = LoginManager()
login_manager.init_app(app)

maestro_model       = Model_Maestro()
practicante_model   = Model_Practicante()
familia_model       = Model_Familia()
formulario_contacto = Model_FormularioContacto()
NOTIFY_CONTACT_EMAIL = os.environ.get("CONTACT_NOTIFY_EMAIL", "")


def db(sql, params=None, commit=False):
    """Ejecuta SQL y retorna resultados. Maneja reconexión automática."""
    cursor, conexion = get_cursor()
    try:
        cursor.execute(sql, params or ())
        if commit:
            conexion.commit()
            return cursor.lastrowid
        return cursor.fetchall()
    except Exception as e:
        if commit:
            try: conexion.rollback()
            except Exception: pass
        raise e
    finally:
        try: cursor.close()
        except Exception: pass


def calcular_estado(fecha_str):
    try:
        fecha = date.fromisoformat(str(fecha_str))
        hoy = date.today()
        if fecha > hoy:    return "Proximo"
        elif fecha == hoy: return "En curso"
        else:              return "Pasado"
    except Exception:
        return "Proximo"


def sincronizar_estados_eventos():
    """Recalcula y persiste el estado de todos los eventos según la fecha actual."""
    filas = db("SELECT id, fecha_evento, estado FROM eventos WHERE fecha_evento IS NOT NULL")
    for id_ev, fecha_ev, estado_actual in filas:
        nuevo = calcular_estado(fecha_ev)
        if nuevo != estado_actual:
            db("UPDATE eventos SET estado=%s WHERE id=%s", (nuevo, id_ev), commit=True)


def format_torneo(val):
    s = str(val).strip() if val else ""
    if not s or s in ("None", "0000-00-00"):
        return "Sin torneo"
    return s


def ensure_informe_schema():
    """Añade nombre_torneo si la tabla aún usa solo fecha_informe."""
    cols = {r[0] for r in db("SHOW COLUMNS FROM informe_rendimiento")}
    if "nombre_torneo" not in cols:
        db("ALTER TABLE informe_rendimiento ADD COLUMN nombre_torneo VARCHAR(200) NULL AFTER id_practicante", commit=True)


# ── CONTACTO ─────────────────────────────────────────────────────────────────

@app.route("/publico/formulario-contacto", methods=["POST"])
def publico_formulario_contacto():
    data = request.get_json(silent=True) or {}
    nombre   = (data.get("nombre")   or "").strip()
    correo   = (data.get("correo")   or "").strip()
    telefono = (data.get("telefono") or "").strip()
    sede     = (data.get("sede")     or "").strip()
    texto    = (data.get("texto")    or "").strip()
    if not all([nombre, correo, telefono, sede, texto]):
        return jsonify({"error": "Por favor completa todos los campos."}), 400
    try:
        formulario_contacto.insertar(nombre, correo, telefono, texto, sede)
    except Exception:
        return jsonify({"error": "No se pudo guardar el mensaje."}), 500
    if not enviar_aviso_formulario(NOTIFY_CONTACT_EMAIL, nombre, correo, telefono, sede, texto):
        return jsonify({"error": "No se pudo enviar el correo."}), 500
    return jsonify({"mensaje": "¡Gracias! Recibimos tu mensaje y te contactaremos pronto."})


# ── LOGIN ────────────────────────────────────────────────────────────────────

@app.route("/login", methods=["POST"])
def login_usuario():
    data       = request.get_json(silent=True) or {}
    correo     = (data.get("correo")     or "").strip()
    contrasena = (data.get("contrasena") or "").strip()
    rol        = (data.get("rol")        or "").strip()

    if not correo or not contrasena or not rol:
        return jsonify({"error": "Ingresa correo, contraseña y rol."}), 400

    tablas = {"maestro": "maestros", "familia": "familia", "practicante": "practicantes"}
    if rol not in tablas:
        return jsonify({"error": "Rol no válido."}), 400

    try:
        if rol == "practicante":
            filas = db("SELECT id, nombre, correo, actividad FROM practicantes WHERE correo=%s AND contrasena=%s", (correo, contrasena))
            if not filas:
                return jsonify({"error": "Rol, correo o contraseña no válidos."}), 401
            r = filas[0]
            if r[3] and r[3].lower() == "no activo":
                return jsonify({"error": "Tu cuenta está desactivada. Contacta al maestro."}), 403
            return jsonify({"usuario": {"tipo": "practicante", "id": r[0], "nombre": r[1], "correo": r[2]}})

        tabla = tablas[rol]
        filas = db(f"SELECT id, nombre, correo FROM {tabla} WHERE correo=%s AND contrasena=%s", (correo, contrasena))
        if not filas:
            return jsonify({"error": "Rol, correo o contraseña no válidos."}), 401
        r = filas[0]
        return jsonify({"usuario": {"tipo": rol, "id": r[0], "nombre": r[1], "correo": r[2]}})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── MAESTROS ─────────────────────────────────────────────────────────────────

@app.route('/maestros', methods=['GET'])
def listar_maestros():
    try:
        q = (request.args.get('q') or '').strip()
        if q:
            filas = db("SELECT id, nombre, correo FROM maestros WHERE nombre LIKE %s", (f'%{q}%',))
        else:
            filas = db("SELECT id, nombre, correo FROM maestros")
        return jsonify([{"id": r[0], "nombre": r[1], "correo": r[2]} for r in filas])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/maestros', methods=['POST'])
def crear_maestro():
    data = request.get_json(silent=True) or {}
    nombre = data.get('nombre'); correo = data.get('correo'); contrasena = data.get('contrasena')
    if not nombre or not correo or not contrasena:
        return jsonify({"error": "Campos obligatorios faltantes"}), 400
    try:
        db("INSERT INTO maestros (nombre, correo, contrasena) VALUES (%s,%s,%s)", (nombre, correo, contrasena), commit=True)
        return jsonify({"mensaje": "Maestro creado exitosamente"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/actualizar_maestro/<int:id>', methods=['PUT'])
def actualizar_maestro(id):
    data = request.get_json(silent=True) or {}
    try:
        if data.get('contrasena'):
            db("UPDATE maestros SET nombre=%s, correo=%s, contrasena=%s WHERE id=%s",
               (data.get('nombre'), data.get('correo'), data.get('contrasena'), id), commit=True)
        else:
            db("UPDATE maestros SET nombre=%s, correo=%s WHERE id=%s",
               (data.get('nombre'), data.get('correo'), id), commit=True)
        return jsonify({"mensaje": "Maestro actualizado correctamente"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/eliminar_maestro/<int:id>', methods=['DELETE'])
def eliminar_maestro(id):
    try:
        db("DELETE FROM maestros WHERE id=%s", (id,), commit=True)
        return jsonify({"mensaje": "Maestro eliminado correctamente"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── PRACTICANTES ─────────────────────────────────────────────────────────────

@app.route('/practicantes', methods=['GET'])
def listar_practicantes():
    try:
        q = (request.args.get('q') or '').strip()
        if q:
            filas = db("SELECT id, nombre, correo, actividad, id_familia FROM practicantes WHERE nombre LIKE %s", (f'%{q}%',))
        else:
            filas = db("SELECT id, nombre, correo, actividad, id_familia FROM practicantes")
        return jsonify([{"id": r[0], "nombre": r[1], "correo": r[2], "actividad": r[3], "id_familia": r[4]} for r in filas])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/nuevo_practicante', methods=['POST'])
def crear_practicante():
    data       = request.get_json(silent=True) or {}
    nombre     = (data.get('NOMBRE')     or "").strip()
    correo     = (data.get('CORREO')     or "").strip()
    actividad  = data.get('ACTIVIDAD', 'Activo')
    id_maestro = data.get('ID_MAESTRO')
    contrasena = (data.get('CONTRASENA') or "").strip()
    if not nombre or not correo or not contrasena:
        return jsonify({"error": "Campos obligatorios faltantes"}), 400
    partes   = nombre.strip().split()
    apellido = partes[-1] if partes else nombre
    nombre_familia = f"Familia {apellido}"
    try:
        id_familia = db("INSERT INTO familia (nombre, correo, contrasena) VALUES (%s,%s,%s)",
                        (nombre_familia, correo, contrasena), commit=True)
        db("INSERT INTO practicantes (nombre, correo, actividad, id_maestro, id_familia, contrasena) VALUES (%s,%s,%s,%s,%s,%s)",
        (nombre, correo, actividad, id_maestro, id_familia, contrasena), commit=True)
        return jsonify({
            "mensaje": f"Practicante '{nombre}' creado exitosamente.",
            "practicante": {"nombre": nombre, "correo": correo, "contrasena": contrasena},
            "familia": {"id": id_familia, "nombre": nombre_familia, "correo": correo, "contrasena": contrasena}
        }), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/actualizar_practicante/<int:id>', methods=['PUT'])
def actualizar_practicante(id):
    data = request.get_json(silent=True) or {}
    try:
        if data.get('CONTRASENA'):
            db("UPDATE practicantes SET nombre=%s, correo=%s, actividad=%s, contrasena=%s WHERE id=%s",
            (data.get('NOMBRE'), data.get('CORREO'), data.get('ACTIVIDAD'), data.get('CONTRASENA'), id), commit=True)
        else:
            db("UPDATE practicantes SET nombre=%s, correo=%s, actividad=%s WHERE id=%s",
            (data.get('NOMBRE'), data.get('CORREO'), data.get('ACTIVIDAD'), id), commit=True)
        return jsonify({"mensaje": "Practicante actualizado correctamente"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/eliminar_practicante/<int:id>', methods=['DELETE'])
def eliminar_practicante(id):
    try:
        filas = db("SELECT id_familia FROM practicantes WHERE id=%s", (id,))
        db("DELETE FROM practicantes WHERE id=%s", (id,), commit=True)
        if filas and filas[0][0]:
            db("DELETE FROM familia WHERE id=%s", (filas[0][0],), commit=True)
        return jsonify({"mensaje": "Practicante y familia eliminados correctamente"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/buscar_practicantes', methods=['GET'])
def buscar_practicantes_nombre():
    q = (request.args.get('q') or '').strip()
    if not q:
        return jsonify([])
    try:
        filas = db("SELECT id, nombre FROM practicantes WHERE nombre LIKE %s LIMIT 10", (f'%{q}%',))
        return jsonify([{"id": r[0], "nombre": r[1]} for r in filas])
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── EVENTOS ──────────────────────────────────────────────────────────────────

@app.route('/eventos', methods=['GET'])
def listar_eventos():
    try:
        sincronizar_estados_eventos()
        q = (request.args.get('q') or '').strip()
        if q:
            filas = db("SELECT id, titulo, estado, tipo, fecha_evento FROM eventos WHERE titulo LIKE %s", (f'%{q}%',))
        else:
            filas = db("SELECT id, titulo, estado, tipo, fecha_evento FROM eventos")
        return jsonify([{"id": r[0], "titulo": r[1], "estado": r[2], "tipo": r[3], "fecha": str(r[4]) if r[4] else ""} for r in filas])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/postear_evento', methods=['POST'])
def postear_evento():
    data = request.get_json(silent=True) or {}
    nombre = data.get('NOMBRE'); tipo = data.get('TIPO'); fecha = data.get('FECHA')
    if not nombre or not tipo or not fecha:
        return jsonify({"error": "Faltan campos obligatorios"}), 400
    estado = calcular_estado(fecha)
    try:
        db("INSERT INTO eventos (titulo, estado, tipo, fecha_evento) VALUES (%s,%s,%s,%s)", (nombre, estado, tipo, fecha), commit=True)
        return jsonify({"mensaje": f"Evento publicado como '{estado}'"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/actualizar_evento/<int:id>', methods=['PUT'])
def actualizar_evento(id):
    data = request.get_json(silent=True) or {}
    fecha = data.get('FECHA')
    estado = calcular_estado(fecha) if fecha else 'Proximo'
    try:
        db("UPDATE eventos SET titulo=%s, estado=%s, tipo=%s, fecha_evento=%s WHERE id=%s",
        (data.get('NOMBRE'), estado, data.get('TIPO'), fecha, id), commit=True)
        return jsonify({"mensaje": "Evento actualizado correctamente"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/eliminar_evento/<int:id>', methods=['DELETE'])
def eliminar_evento(id):
    try:
        db("DELETE FROM eventos WHERE id=%s", (id,), commit=True)
        return jsonify({"mensaje": "Evento eliminado correctamente"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/eventos_actuales',  methods=['GET'])
def listar_eventos_actuales():
    sincronizar_estados_eventos()
    filas = db("SELECT id, titulo, estado, tipo FROM eventos WHERE estado='En curso'")
    return jsonify([{"id": r[0], "titulo": r[1], "estado": r[2], "tipo": r[3]} for r in filas])

@app.route('/eventos_proximos',  methods=['GET'])
def listar_eventos_proximos():
    sincronizar_estados_eventos()
    filas = db("SELECT id, titulo, estado, tipo FROM eventos WHERE estado='Proximo'")
    return jsonify([{"id": r[0], "titulo": r[1], "estado": r[2], "tipo": r[3]} for r in filas])

@app.route('/eventos_pasados',   methods=['GET'])
def listar_eventos_pasados():
    sincronizar_estados_eventos()
    filas = db("SELECT id, titulo, estado, tipo FROM eventos WHERE estado='Pasado'")
    return jsonify([{"id": r[0], "titulo": r[1], "estado": r[2], "tipo": r[3]} for r in filas])

@app.route('/familia/eventos_actuales', methods=['GET'])
def familia_eventos_actuales():
    sincronizar_estados_eventos()
    filas = db("SELECT id, titulo, estado, tipo FROM eventos WHERE estado='En curso'")
    return jsonify([{"id": r[0], "titulo": r[1], "estado": r[2], "tipo": r[3]} for r in filas])

@app.route('/familia/eventos_proximos', methods=['GET'])
def familia_eventos_proximos():
    sincronizar_estados_eventos()
    filas = db("SELECT id, titulo, estado, tipo FROM eventos WHERE estado='Proximo'")
    return jsonify([{"id": r[0], "titulo": r[1], "estado": r[2], "tipo": r[3]} for r in filas])

@app.route('/familia/eventos_pasados',  methods=['GET'])
def familia_eventos_pasados():
    sincronizar_estados_eventos()
    filas = db("SELECT id, titulo, estado, tipo FROM eventos WHERE estado='Pasado'")
    return jsonify([{"id": r[0], "titulo": r[1], "estado": r[2], "tipo": r[3]} for r in filas])


# ── INFORMES ─────────────────────────────────────────────────────────────────

@app.route("/publicar_rendimiento", methods=["POST"])
def publicar_rendimiento():
    ensure_informe_schema()
    data = request.get_json(silent=True) or {}
    id_practicante = data.get("id_practicante")
    nombre_torneo  = (data.get("nombre_torneo") or data.get("fecha_informe") or "").strip()
    comentarios    = data.get("comentarios")
    if not id_practicante or not nombre_torneo or not comentarios:
        return jsonify({"error": "Faltan campos obligatorios (practicante, torneo y comentarios)"}), 400
    try:
        db("INSERT INTO informe_rendimiento (id_practicante, nombre_torneo, fecha_informe, comentarios) VALUES (%s,%s,CURDATE(),%s)",
           (int(id_practicante), nombre_torneo, comentarios), commit=True)
        return jsonify({"mensaje": "Informe publicado con éxito"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/informes', methods=['GET'])
def listar_informes():
    try:
        ensure_informe_schema()
        filas = db("""SELECT ir.id, p.nombre, ir.nombre_torneo, ir.comentarios
                      FROM informe_rendimiento ir
                      LEFT JOIN practicantes p ON ir.id_practicante = p.id
                      ORDER BY ir.id DESC""")
        return jsonify([{"practicante": r[1] or "", "torneo": format_torneo(r[2]), "comentarios": r[3]} for r in filas])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/familia/rendimiento/<int:id_practicante>', methods=['GET'])
def familia_rendimiento(id_practicante):
    try:
        ensure_informe_schema()
        filas = db("""SELECT ir.id, p.nombre, ir.nombre_torneo, ir.comentarios
                      FROM informe_rendimiento ir
                      LEFT JOIN practicantes p ON ir.id_practicante = p.id
                      WHERE ir.id_practicante = %s ORDER BY ir.id DESC""", (id_practicante,))
        return jsonify([{"practicante": r[1] or "", "torneo": format_torneo(r[2]), "comentarios": r[3]} for r in filas])
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── PAGOS ─────────────────────────────────────────────────────────────────────

@app.route('/pagos', methods=['GET'])
def listar_pagos():
    try:
        q = (request.args.get('q') or '').strip()
        if q:
            filas = db("""SELECT p.id, pr.nombre, p.pago_de, p.monto, p.comprobante
                          FROM pagos p LEFT JOIN practicantes pr ON p.id_practicante=pr.id
                          WHERE pr.nombre LIKE %s ORDER BY p.id DESC""", (f'%{q}%',))
        else:
            filas = db("""SELECT p.id, pr.nombre, p.pago_de, p.monto, p.comprobante
                          FROM pagos p LEFT JOIN practicantes pr ON p.id_practicante=pr.id
                          ORDER BY p.id DESC""")
        return jsonify([{"practicante": r[1] or "", "concepto": r[2], "monto": r[3]} for r in filas])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/familia/pagos/<int:id_practicante>', methods=['GET'])
def familia_pagos(id_practicante):
    try:
        filas = db("""SELECT p.id, pr.nombre, p.pago_de, p.monto, p.comprobante
                      FROM pagos p LEFT JOIN practicantes pr ON p.id_practicante=pr.id
                      WHERE p.id_practicante=%s ORDER BY p.id DESC""", (id_practicante,))
        return jsonify([{"practicante": r[1] or "", "concepto": r[2], "monto": r[3], "comprobante": r[4]} for r in filas])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/familia/pago', methods=['POST'])
def familia_crear_pago():
    id_practicante = request.form.get('id_practicante')
    pago_de        = request.form.get('pago_de')
    monto          = request.form.get('monto')
    comprobante    = None
    if not id_practicante or not pago_de or not monto:
        return jsonify({"error": "Faltan datos obligatorios"}), 400
    if 'comprobante' in request.files:
        archivo = request.files['comprobante']
        if archivo and archivo.filename:
            ruta = os.path.join(os.path.dirname(__file__), 'uploads', 'pagos')
            os.makedirs(ruta, exist_ok=True)
            nombre_archivo = f"pago_{id_practicante}_{archivo.filename}"
            archivo.save(os.path.join(ruta, nombre_archivo))
            comprobante = f"pagos/{nombre_archivo}"
    try:
        db("INSERT INTO pagos (id_practicante, pago_de, monto, comprobante) VALUES (%s,%s,%s,%s)",
           (int(id_practicante), pago_de, float(monto), comprobante), commit=True)
        return jsonify({"mensaje": "Pago registrado correctamente"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── GUÍAS ─────────────────────────────────────────────────────────────────────

@app.route('/publicar_guias', methods=['POST'])
def publicar_guias():
    titulo = request.form.get('titulo'); nivel = request.form.get('nivel'); id_maestro = request.form.get('id_maestro')
    if 'url_recursos' not in request.files:
        return jsonify({"error": "No se ha seleccionado ningún archivo"}), 400
    archivo = request.files['url_recursos']
    if not archivo.filename or not titulo or not nivel or not id_maestro:
        return jsonify({"error": "Faltan campos obligatorios"}), 400
    try:
        ruta = os.path.join(os.path.dirname(__file__), 'uploads', 'guias')
        os.makedirs(ruta, exist_ok=True)
        archivo.save(os.path.join(ruta, archivo.filename))
        db("INSERT INTO guia_fundamento (titulo, url_recurso, nivel, id_maestro) VALUES (%s,%s,%s,%s)",
           (titulo, archivo.filename, nivel, int(id_maestro)), commit=True)
        return jsonify({"mensaje": "Guía publicada con éxito"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/guias', methods=['GET'])
def listar_guias_maestro():
    try:
        filas = db("SELECT id, titulo, nivel, url_recurso FROM guia_fundamento ORDER BY id DESC")
        return jsonify([{"id": r[0], "titulo": r[1], "nivel": r[2], "url_recurso": r[3]} for r in filas])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/obtener/guias', methods=['GET'])
def obtener_guias():
    try:
        filas = db("SELECT id, titulo, nivel, url_recurso FROM guia_fundamento ORDER BY id DESC")
        return jsonify([{"id": r[0], "titulo": r[1], "nivel": r[2], "url_recurso": r[3]} for r in filas])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/familia/guias', methods=['GET'])
def familia_guias():
    try:
        filas = db("SELECT id, titulo, nivel, url_recurso FROM guia_fundamento ORDER BY id DESC")
        return jsonify([{"id": r[0], "titulo": r[1], "nivel": r[2], "url_recurso": r[3]} for r in filas])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/eliminar_guia/<int:id>', methods=['DELETE'])
def eliminar_guia(id):
    try:
        db("DELETE FROM guia_fundamento WHERE id=%s", (id,), commit=True)
        return jsonify({"mensaje": "Guía eliminada correctamente"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/uploads/<path:filename>', methods=['GET'])
def descargar_archivo(filename):
    ruta_uploads = os.path.join(os.path.dirname(__file__), 'uploads')
    return send_from_directory(ruta_uploads, filename)


# ── PANEL PRACTICANTE ─────────────────────────────────────────────────────────

@app.route('/actualizar', methods=['PUT'])
def actualizar_practicante_self():
    data = request.get_json(silent=True) or {}
    try:
        db("UPDATE practicantes SET contrasena=%s WHERE correo=%s", (data.get('CONTRASENA'), data.get('CORREO')), commit=True)
        return jsonify({"mensaje": "Información actualizada correctamente"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── PANEL FAMILIA ─────────────────────────────────────────────────────────────

@app.route('/familia/mi_practicante/<int:id_familia>', methods=['GET'])
def familia_mi_practicante(id_familia):
    try:
        filas = db("SELECT id, nombre FROM practicantes WHERE id_familia=%s LIMIT 1", (id_familia,))
        if not filas:
            return jsonify({"error": "No se encontró practicante vinculado"}), 404
        return jsonify({"id": filas[0][0], "nombre": filas[0][1]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/familia/actualizar', methods=['PUT'])
def actualizar_familia():
    data = request.get_json(silent=True) or {}
    correo_actual = data.get('CORREO_ACTUAL')
    nuevo_correo  = data.get('CORREO_NUEVO') or correo_actual
    contrasena    = data.get('CONTRASENA')
    if not correo_actual:
        return jsonify({"error": "Falta el correo actual"}), 400
    try:
        if contrasena and nuevo_correo:
            db("UPDATE familia SET correo=%s, contrasena=%s WHERE correo=%s", (nuevo_correo, contrasena, correo_actual), commit=True)
        elif nuevo_correo and nuevo_correo != correo_actual:
            db("UPDATE familia SET correo=%s WHERE correo=%s", (nuevo_correo, correo_actual), commit=True)
        elif contrasena:
            db("UPDATE familia SET contrasena=%s WHERE correo=%s", (contrasena, correo_actual), commit=True)
        return jsonify({"mensaje": "Datos actualizados correctamente"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/eliminar_familia/<int:id>', methods=['DELETE'])
def eliminar_familia(id):
    try:
        db("DELETE FROM practicantes WHERE id_familia=%s", (id,), commit=True)
        db("DELETE FROM familia WHERE id=%s", (id,), commit=True)
        return jsonify({"mensaje": "Familia y practicante(s) eliminados correctamente"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── LOGOUT ────────────────────────────────────────────────────────────────────

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return jsonify({"mensaje": "Sesión cerrada"})


if __name__ == "__main__":
    app.run(debug=os.environ.get('FLASK_DEBUG', '0') == '1', port=5000, host='127.0.0.1')