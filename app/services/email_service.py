from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from app.core.config import settings


mail_config = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
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