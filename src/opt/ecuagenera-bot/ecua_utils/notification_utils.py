import smtplib
import socket
from email.message import EmailMessage

from .util import reload_config_yml


def send_email(mail_body, to_email_address, subject):
    mailserver = None
    config = reload_config_yml()
    try:
        mailserver = smtplib.SMTP(
            config['smtp_server'], config['smtp_port'])
        mailserver.ehlo()
        mailserver.starttls()
        mailserver.login(config['smtp_user'], config['smtp_pw'])

        from_email_address = config['from_email']

        msg = EmailMessage()
        msg.set_content(mail_body)
        msg['From'] = from_email_address
        msg['To'] = to_email_address
        msg['Subject'] = subject

        print(f"Sending out email to {to_email_address}")
        mailserver.sendmail(from_addr=from_email_address,
                            to_addrs=to_email_address, msg=msg.as_string())
    except socket.gaierror:
        print(
            "Socket issue while sending email - Are you in VPN/proxy?")
    except Exception as e:
        print(f"Something went wrong while sending an email: {e}")
    finally:
        if mailserver != None:
            try:
                mailserver.quit()
            except smtplib.SMTPServerDisconnected:
                # This exception is raised when the server unexpectedly disconnects,
                # or when an attempt is made to use the SMTP instance before connecting it to a server
                pass
