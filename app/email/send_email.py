import smtplib
import ssl

# TODO review setup of logging
from logging import getLogger

from fastapi import BackgroundTasks
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from pydantic import EmailStr

from app.config import settings

log = getLogger(__name__)


# TODO remove unused functions
# TODO remove unused environment variables

# TODO write docstring
# Return ConnectionConfig class extracted from mail environment variables
def get_email_config():

    # TODO review email config
    connection_config = ConnectionConfig(
        MAIL_USERNAME=settings.SMTP_USER,
        MAIL_PASSWORD=settings.SMTP_PASS,
        MAIL_FROM=settings.SMTP_MAIL_FROM,
        MAIL_PORT=settings.SMTP_PORT,  # TODO review port
        MAIL_SERVER=settings.SMTP_SERVER,
        MAIL_FROM_NAME=settings.SMTP_MAIL_FROM_NAME,  # TODO review mail from name
        MAIL_STARTTLS=settings.SMTP_STARTTLS,
        MAIL_SSL_TLS=settings.SMTP_SSL_TLS,
    )
    return connection_config


# TODO remove message
message_test = """\
Subject: Publication Finished
To: test@test.com
From: test@test.com

This is a test e-mail message. WHALEY"""


# TODO remove function
# TODO write docstring
# TODO implement route with background tests
# TODO rename function
# TODO create template for emails, extract variables needed into a function and
#  template that writes message
# TODO refactor so that None is returned in case of error,
#  if success return value or message
def send_email_background():

    port = settings.SMTP_PORT
    mail_server = settings.SMTP_SERVER
    pswd = settings.SMTP_PASS
    username = settings.SMTP_USER
    sender = "test@test.com"
    receiver = "test@test.com"

    # Encrypt message using TLS
    try:
        # Start SMPT server
        with smtplib.SMTP(mail_server, port) as server:

            # Secure the connection
            context = ssl.create_default_context()
            server.starttls(context=context)

            if username and pswd:
                # Login and send email
                server.login(username, pswd)
            server.sendmail(sender, receiver, message_test)
            server.quit()

            # TODO return success message or other success value
            # sucessfully sending mail (not necessarily recieved)
            # will result in empty dictionary {}
            # result = server.sendmail(sender, receiver, message)
            # print(result)

    except smtplib.SMTPException as e:
        log.error(e)
        return None

    except AttributeError as e:
        log.error(e)
        return None


# TODO test function
# TODO refactor function to use updated config
def send_email_background_test(
    background_tasks: BackgroundTasks,
    subject: str,
    email_to: str,
    # body: dict
):
    message = MessageSchema(
        subject=subject,
        recipients=[email_to],
        # body=body,
        body="""
<p>Thanks for using Fastapi-mail</p>
""",
        subtype="html",
    )

    # Assign email config
    conf = get_email_config()
    fm = FastMail(conf)

    background_tasks.add_task(
        fm.send_message,
        message,
        # template_name='email.html'
    )


# TODO test function
# TODO implement try/exception error handling
async def send_email_async(
    subject: str, recipients: list[EmailStr], body: str, subtype: MessageType
):

    # Assign message object
    message = MessageSchema(
        subject=subject, recipients=recipients, body=body, subtype=subtype
    )

    # Assign email config
    conf = get_email_config()
    fm = FastMail(conf)

    # Send email
    await fm.send_message(message)
