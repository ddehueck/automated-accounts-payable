
from loguru import logger as log
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, To, From, ReplyTo, Category

from .config import config


def send_reset_pswd_email(email: str, reset_url: str) -> None:
    message = Mail()
    message.to = [To(email=email)]
    message.from_email = From(
        email="hello@easyinvoicemanagement.com",
        name="Easy Invoice Management",
    )

    message.reply_to = ReplyTo(
        email="hello@easyinvoicemanagement.com",
        name="Easy Invoice Management",
    )

    message.template_id = "d-f157bdbf39784edfb1d6a2aae88c80e4"
    message.dynamic_template_data = {
        "reset_url": reset_url
    }

    message.category = [
        Category("reset_password"),
    ]

    sendgrid_client = SendGridAPIClient(config.sendgrid_api_key)
    response = sendgrid_client.send(message)

    log.debug(response.status_code)
    log.debug(response.body)
    log.debug(response.headers)
