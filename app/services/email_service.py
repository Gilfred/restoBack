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
        <!DOCTYPE html>
        <html lang="fr">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>

        <body style="
            margin: 0;
            padding: 0;
            background-color: #f5f5f5;
            font-family: Arial, Helvetica, sans-serif;
        ">

            <div style="
                max-width: 600px;
                margin: 40px auto;
                background-color: #ffffff;
                padding: 40px;
                border-radius: 10px;
            ">

                <h2 style="
                    margin-top: 0;
                    color: #222222;
                ">
                    Réinitialisation de votre mot de passe
                </h2>

                <p style="
                    color: #555555;
                    font-size: 16px;
                    line-height: 1.6;
                ">
                    Bonjour,
                </p>

                <p style="
                    color: #555555;
                    font-size: 16px;
                    line-height: 1.6;
                ">
                    Vous avez demandé la réinitialisation de votre mot de passe
                    pour votre compte Gilexis Business.
                </p>

                <p style="
                    color: #555555;
                    font-size: 16px;
                    line-height: 1.6;
                ">
                    Cliquez sur le bouton ci-dessous pour définir un nouveau
                    mot de passe :
                </p>

                <div style="
                    text-align: center;
                    margin: 30px 0;
                ">
                    <a href="{reset_link}"
                       style="
                            display: inline-block;
                            padding: 14px 28px;
                            background-color: #1f6feb;
                            color: #ffffff;
                            text-decoration: none;
                            font-size: 16px;
                            font-weight: bold;
                            border-radius: 6px;
                       ">
                        Réinitialiser mon mot de passe
                    </a>
                </div>

                <p style="
                    color: #777777;
                    font-size: 14px;
                    line-height: 1.6;
                ">
                    Ce lien est valable pendant 1 heure.
                </p>

                <p style="
                    color: #777777;
                    font-size: 14px;
                    line-height: 1.6;
                ">
                    Si vous n'êtes pas à l'origine de cette demande,
                    vous pouvez simplement ignorer cet e-mail.
                </p>

                <hr style="
                    border: none;
                    border-top: 1px solid #eeeeee;
                    margin: 30px 0;
                ">

                <p style="
                    color: #999999;
                    font-size: 13px;
                    text-align: center;
                ">
                    L'équipe Gilexis Business
                </p>

            </div>

        </body>
        </html>
        """,
        subtype=MessageType.html,
    )

    fm = FastMail(mail_config)

    await fm.send_message(message)