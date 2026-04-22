import smtplib
import ssl
import mimetypes
from email.message import EmailMessage
from flask import current_app
from io import BytesIO


def _build_client():
    host = current_app.config['MAIL_HOST']
    port = current_app.config['MAIL_PORT']
    username = current_app.config['MAIL_USERNAME']
    password = current_app.config['MAIL_PASSWORD']
    timeout = current_app.config.get('MAIL_TIMEOUT', 10)

    if not password:
        raise RuntimeError('Mail password is not configured.')

    if current_app.config.get('MAIL_USE_SSL', True):
        client = smtplib.SMTP_SSL(
            host,
            port,
            timeout=timeout,
            context=ssl.create_default_context()
        )
    else:
        client = smtplib.SMTP(host, port, timeout=timeout)
        client.starttls(context=ssl.create_default_context())

    client.login(username, password)
    return client


def send_email(recipient, subject, text_body, html_body=None, attachments=None):
    """
    Send email with optional attachments
    
    Args:
        recipient: Email address
        subject: Email subject
        text_body: Plain text email body
        html_body: HTML email body (optional)
        attachments: List of tuples (filename, file_data_bytes) (optional)
    """
    if not current_app.config.get('MAIL_ENABLED', False):
        raise RuntimeError('Email sending is disabled.')

    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = current_app.config['MAIL_DEFAULT_SENDER']
    msg['To'] = recipient
    msg.set_content(text_body)
    if html_body:
        msg.add_alternative(html_body, subtype='html')

    for filename, file_data in attachments or []:
        if isinstance(file_data, BytesIO):
            file_data.seek(0)
            file_content = file_data.read()
        else:
            file_content = file_data

        mime_type, _ = mimetypes.guess_type(filename)
        if mime_type:
            maintype, subtype = mime_type.split('/', 1)
        else:
            maintype, subtype = 'application', 'octet-stream'

        msg.add_attachment(file_content, maintype=maintype, subtype=subtype, filename=filename)

    with _build_client() as client:
        client.send_message(msg)
