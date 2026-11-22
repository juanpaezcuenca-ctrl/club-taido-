# Taekwondo Taido Hub

Aplicación web para la gestión de un club de taekwondo/taido: portal con acceso por roles (maestros, practicantes y familias), inscripción, formulario de contacto con aviso por correo, guías de fundamentos, registro de pagos con comprobante, eventos y seguimiento del rendimiento.

> Proyecto de portafolio. Las fotos, teléfonos y correos son de ejemplo; no contiene datos reales.

## Tecnologías

- **Backend:** Python, Flask, Flask-Login, Flask-CORS, python-dotenv
- **Base de datos:** MySQL / MariaDB (`mysql-connector-python`)
- **Frontend:** HTML, CSS y JavaScript
- **Correo:** SMTP de Gmail (contraseña de aplicación)

## Funcionalidades

- Inicio de sesión y paneles distintos para **maestro**, **practicante** y **familia**
- Inscripción de practicantes
- Formulario de contacto que envía un aviso por correo
- Publicación y consulta de guías de fundamentos
- Registro de pagos con comprobante adjunto
- Eventos, galería e informes de rendimiento

## Estructura

```
backend/    API Flask, modelos y conexión a la base de datos
frontend/   Páginas HTML, estilos y scripts
database/   Esquema SQL (schema.sql)
docs/       Capturas del modelo de base de datos
```

## Cómo ejecutarlo

1. **Base de datos:** crea una base llamada `taekwondo` e importa `database/schema.sql`.
2. **Backend:**
   ```bash
   cd backend
   python -m venv venv
   venv\Scripts\activate        # En Linux/Mac: source venv/bin/activate
   pip install -r requirements.txt
   cp .env.example .env         # En Windows: copy .env.example .env
   ```
   Abre `.env` y completa tus valores (base de datos, `SECRET_KEY`, correo).
   ```bash
   python app.py
   ```
   La API queda en `http://127.0.0.1:5000`.
3. **Frontend:** abre la carpeta `frontend/` con un servidor estático, por ejemplo la extensión Live Server de VS Code, o `python -m http.server 8000` dentro de `frontend/`.

## Configuración

Las claves se leen de variables de entorno (archivo `.env`, que está en `.gitignore`). Mira `backend/.env.example` para ver cuáles hacen falta.
