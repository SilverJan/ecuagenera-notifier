import glob
import os
import smtplib
import socket
from email.message import EmailMessage
import subprocess

import yaml

config_file_path = f'{os.path.dirname(os.path.realpath(__file__))}/config.yml'
if not os.path.isfile(config_file_path):
    raise Exception("Please create config.yml first")

config = None
with open(config_file_path, 'r') as stream:
    try:
        config = yaml.safe_load(stream)
    except yaml.YAMLError as exc:
        print(exc)

# get logs
log = subprocess.check_output(["sudo", "systemctl", "status", "ecuagenera-bot.service", "--no-pager"])

# send email to admin
mailserver = None
try:
    mailserver = smtplib.SMTP(
        config['smtp_server'], config['smtp_port'])
    mailserver.ehlo()
    mailserver.starttls()
    mailserver.login(config['smtp_user'], config['smtp_pw'])

    from_email_address = config['from_email']
    to_email_address = "jan.bissinger@outlook.de"

    msg = EmailMessage()
    msg.set_content(
        "Error while running service! Here is the last log:\n\n" "----------\n\n" f"{log}" "\n\n----------")
    msg['From'] = from_email_address
    msg['To'] = to_email_address
    msg['Subject'] = f"Ecuagenera Systemd Service Error"

    print(f"Sending out email to {to_email_address}")
    mailserver.sendmail(from_addr=from_email_address,
                        to_addrs=to_email_address, msg=msg.as_string())
except socket.gaierror:
    print("Socket issue while sending email - Are you in VPN/proxy?")
except Exception as e:
    print(f"Something went wrong while sending an email: {e}")
finally:
    if mailserver != None:
        mailserver.quit()
