from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import aiosmtplib

from app.core.config import settings
from app.domain.interfaces.providers.email_provider import IEmailProvider


class SmtpEmailProvider(IEmailProvider):
    def __init__(self):
        self.host = settings.SMTP_HOST
        self.port = settings.SMTP_PORT
        self.user = settings.SMTP_USER
        self.password = settings.SMTP_PASSWORD
        self.use_tls = settings.SMTP_USE_TLS
        self.frontend_url = settings.FRONTEND_URL
        self.verification_expire_hours = (
            settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS
        )
        self.reset_expire_hours = settings.PASSWORD_RESET_TOKEN_EXPIRE_HOURS

    async def _send(
        self, to_email: str, subject: str, html_content: str, text_content: str
    ):
        msg = MIMEMultipart("alternative")
        msg["From"] = self.user
        msg["To"] = to_email
        msg["Subject"] = subject

        part_text = MIMEText(text_content, "plain", "utf-8")
        part_html = MIMEText(html_content, "html", "utf-8")
        msg.attach(part_text)
        msg.attach(part_html)

        try:
            await aiosmtplib.send(
                msg,
                hostname=self.host,
                port=self.port,
                username=self.user,
                password=self.password,
                start_tls=self.use_tls,
            )
            return True
        except Exception as e:
            print(f"FAILED TO SEND EMAIL: {e}")
            return False

    async def send_verification(
        self, email: str, name: str, token: str
    ) -> bool:
        url = f"{self.frontend_url}/auth/verify-email?token={token}"
        subject = "Подтверждение email адреса"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
        </head>
        <body style="font-family: Arial, sans-serif;">
            <h2>Подтверждение email адреса</h2>
            <p>Здравствуйте, {name}!</p>
            <p>Для подтверждения вашего email адреса, пожалуйста, перейдите по ссылке:</p>
            <p><a href="{url}">{url}</a></p>
            <p>Ссылка действительна в течение {self.verification_expire_hours} часов.</p>
            <p>Если вы не регистрировались на нашем сайте, просто проигнорируйте это письмо.</p>
            <br>
            <p>С уважением,<br>Команда ТутПроблема</p>
        </body>
        </html>
        """

        text_content = f"""
Подтверждение email адреса

Здравствуйте, {name}!

Для подтверждения вашего email адреса, перейдите по ссылке: {url}

Ссылка действительна в течение {self.verification_expire_hours} часов.

Если вы не регистрировались на нашем сайте, просто проигнорируйте это письмо.

С уважением,
Команда ТутПроблема
"""

        return await self._send(email, subject, html_content, text_content)

    async def send_password_reset(
        self, email: str, name: str, token: str
    ) -> bool:
        url = f"{self.frontend_url}/auth/reset-password?token={token}"
        subject = "Сброс пароля"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
        </head>
        <body style="font-family: Arial, sans-serif;">
            <h2>Сброс пароля</h2>
            <p>Здравствуйте, {name}!</p>
            <p>Мы получили запрос на сброс пароля для вашей учетной записи.</p>
            <p>Для сброса пароля, пожалуйста, перейдите по ссылке:</p>
            <p><a href="{url}">{url}</a></p>
            <p>Ссылка действительна в течение {self.reset_expire_hours} часа.</p>
            <p>Если вы не запрашивали сброс пароля, просто проигнорируйте это письмо.</p>
            <br>
            <p>С уважением,<br>Команда ТутПроблема</p>
        </body>
        </html>
        """

        text_content = f"""
Сброс пароля

Здравствуйте, {name}!

Мы получили запрос на сброс пароля для вашей учетной записи.

Для сброса пароля перейдите по ссылке: {url}

Ссылка действительна в течение {self.reset_expire_hours} часа.

Если вы не запрашивали сброс пароля, просто проигнорируйте это письмо.

С уважением,
Команда ТутПроблема
"""

        return await self._send(email, subject, html_content, text_content)
