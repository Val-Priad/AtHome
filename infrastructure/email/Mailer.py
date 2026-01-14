import os

import resend
from jinja2 import Environment, FileSystemLoader, select_autoescape


class Mailer:
    FROM_EMAIL = "noreply@valpriad.online"

    def __init__(self):
        resend.api_key = os.getenv("RESEND_API_KEY")
        self.env = Environment(
            loader=FileSystemLoader(
                os.path.join(os.path.dirname(__file__), "templates")
            ),
            autoescape=select_autoescape(["html"]),
        )

    def send_verification_email(self, email_to, token):
        verification_url = f"{os.getenv('APP_BASE_URL')}/verify?token={token}"

        template = self.env.get_template("email_verification.html")
        html = template.render(verification_url=verification_url)

        params = {
            "from": self.FROM_EMAIL,
            "to": [email_to],
            "subject": "AtHome: Verify your email!",
            "html": html,
            "text": f"Welcome to our website,\nVerify your email by following the link:\n{verification_url}",
        }
        resend.Emails.send(params)  # type: ignore
