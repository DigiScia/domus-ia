import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Configuration SMTP (à charger depuis .env)
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SENDER_EMAIL = os.getenv("SENDER_EMAIL", SMTP_USER)

def send_email(to_email: str, subject: str, body_html: str, attachment_path: Optional[str] = None) -> bool:
    """
    Envoie un email HTML avec une pièce jointe optionnelle via SMTP.
    """
    if not SMTP_USER or not SMTP_PASSWORD:
        logger.warning(f"⚠️ SMTP non configuré. Simulation d'envoi d'email à {to_email}")
        logger.info(f"📧 SUJET: {subject}")
        # logger.info(f"📄 CORPS: {body_html[:200]}...")
        return True

    try:
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = to_email
        msg['Subject'] = subject

        # Corps HTML
        msg.attach(MIMEText(body_html, 'html'))

        # Pièce jointe
        if attachment_path and os.path.exists(attachment_path):
            with open(attachment_path, "rb") as f:
                part = MIMEApplication(
                    f.read(),
                    Name=os.path.basename(attachment_path)
                )
            # Ajouter le header pour le téléchargement
            part['Content-Disposition'] = f'attachment; filename="{os.path.basename(attachment_path)}"'
            msg.attach(part)
        elif attachment_path:
            logger.warning(f"⚠️ Pièce jointe introuvable : {attachment_path}")

        # Connexion SMTP
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        
        logger.info(f"✅ Email envoyé avec succès à {to_email}")
        return True

    except Exception as e:
        logger.error(f"❌ Erreur lors de l'envoi de l'email à {to_email}: {e}")
        return False
