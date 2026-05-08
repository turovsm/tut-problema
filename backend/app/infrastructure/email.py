import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.core.config import settings


class EmailService:
    def __init__(self):
        self.enabled = bool(settings.SMTP_USER and settings.SMTP_PASSWORD)

        if not self.enabled:
            print("Email service disabled - no SMTP credentials provided")

    @staticmethod
    def _send_email(
        to_email: str, subject: str, html_content: str, text_content: str
    ) -> bool:
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = settings.SMTP_USER
            msg["To"] = to_email

            part_text = MIMEText(text_content, "plain")
            part_html = MIMEText(html_content, "html")
            msg.attach(part_text)
            msg.attach(part_html)

            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                server.starttls()
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.send_message(msg)

            print(f"Email sent successfully to {to_email}")
            return True

        except Exception as e:
            print(f"Failed to send email to {to_email}: {e}")
            return False

    def send_verification_email(
        self, to_email: str, to_name: str, token: str
    ) -> bool:
        # FIXED: Added /auth/ to the URL path
        verification_url = (
            f"{settings.FRONTEND_URL}/auth/verify-email?token={token}"
        )

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
        </head>
        <body style="font-family: Arial, sans-serif;">
            <h2>Подтверждение email адреса</h2>
            <p>Здравствуйте, {to_name}!</p>
            <p>Для подтверждения вашего email адреса, пожалуйста, перейдите по ссылке:</p>
            <p><a href="{verification_url}">{verification_url}</a></p>
            <p>Ссылка действительна в течение 24 часов.</p>
            <p>Если вы не регистрировались на нашем сайте, просто проигнорируйте это письмо.</p>
            <br>
            <p>С уважением,<br>Команда ТутПроблема</p>
        </body>
        </html>
        """

        text_content = f"""
Подтверждение email адреса

Здравствуйте, {to_name}!

Для подтверждения вашего email адреса, перейдите по ссылке: {verification_url}

Ссылка действительна в течение 24 часов.

Если вы не регистрировались на нашем сайте, просто проигнорируйте это письмо.

С уважением,
Команда ТутПроблема
"""

        return self._send_email(
            to_email, "Подтверждение email адреса", html_content, text_content
        )

    def send_password_reset_email(
        self, to_email: str, to_name: str, token: str
    ) -> bool:
        # FIXED: Added /auth/ to the URL path
        reset_url = f"{settings.FRONTEND_URL}/auth/reset-password?token={token}"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
        </head>
        <body style="font-family: Arial, sans-serif;">
            <h2>Сброс пароля</h2>
            <p>Здравствуйте, {to_name}!</p>
            <p>Мы получили запрос на сброс пароля для вашей учетной записи.</p>
            <p>Для сброса пароля, пожалуйста, перейдите по ссылке:</p>
            <p><a href="{reset_url}">{reset_url}</a></p>
            <p>Ссылка действительна в течение 1 часа.</p>
            <p>Если вы не запрашивали сброс пароля, просто проигнорируйте это письмо.</p>
            <br>
            <p>С уважением,<br>Команда ТутПроблема</p>
        </body>
        </html>
        """

        text_content = f"""
Сброс пароля

Здравствуйте, {to_name}!

Мы получили запрос на сброс пароля для вашей учетной записи.

Для сброса пароля перейдите по ссылке: {reset_url}

Ссылка действительна в течение 1 часа.

Если вы не запрашивали сброс пароля, просто проигнорируйте это письмо.

С уважением,
Команда ТутПроблема
"""

        return self._send_email(
            to_email, "Сброс пароля", html_content, text_content
        )


email_service = EmailService()
