from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from app.core.config import settings

# Clean up password if it's a Gmail App Password with spaces
smtp_password = settings.MAIL_PASSWORD
if smtp_password and "gmail" in settings.MAIL_SERVER.lower():
    cleaned = smtp_password.replace(" ", "")
    if len(cleaned) == 16:
        smtp_password = cleaned

mail_config = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=smtp_password,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
    MAIL_STARTTLS=settings.MAIL_PORT == 587,
    MAIL_SSL_TLS=settings.MAIL_PORT == 465,
    USE_CREDENTIALS=True,
)


async def send_password_reset_email(
    email: str,
    reset_link: str,
):
    message = MessageSchema(
        subject="Réinitialisation de votre mot de passe - Gilexis",
        recipients=[email],
        body=f"""
Bonjour,

Vous avez demandé la réinitialisation de votre mot de passe Gilexis.

Cliquez sur le lien ci-dessous pour définir un nouveau mot de passe :

{reset_link}

Ce lien est valable pendant 1 heure.

Si vous n'êtes pas à l'origine de cette demande, vous pouvez simplement ignorer cet e-mail.

Cordialement,

L'équipe Gilexis Business
        """,
        subtype=MessageType.plain,
    )

    fm = FastMail(mail_config)

    await fm.send_message(message)
