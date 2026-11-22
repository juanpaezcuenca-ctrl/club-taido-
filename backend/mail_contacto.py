"""
Envío de correo cuando alguien llena el formulario de contacto.
Indispensable: SMTP_EMAIL y SMTP_APP_PASSWORD en backend/.env (contraseña de aplicación de Gmail).
"""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def enviar_aviso_formulario(destinatario, nombre, correo_usuario, telefono, sede, texto):
    """
    Envía un email al club con los datos del formulario.
    destinatario: normalmente contacto@ejemplo.com (CONTACT_NOTIFY_EMAIL en .env)
    Retorna True si Gmail aceptó el envío, False si falló.
    """
    remitente = os.environ.get("SMTP_EMAIL", "").strip()
    password = os.environ.get("SMTP_APP_PASSWORD", "").replace(" ", "").strip()
    if not remitente or not password:
        return False

    msg = MIMEMultipart()
    msg["From"] = remitente
    msg["To"] = destinatario
    msg["Subject"] = f"NUEVO INTERESADO: {nombre}"
    msg.attach(MIMEText(
        f"Nombre: {nombre}\nCorreo: {correo_usuario}\nTeléfono: {telefono}\nSede: {sede}\n\nMensaje:\n{texto}",
        "plain",
        "utf-8",
    ))

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587, timeout=30)
        server.starttls()
        server.login(remitente, password)
        server.send_message(msg)
        server.quit()
        return True
    except Exception:
        return False
