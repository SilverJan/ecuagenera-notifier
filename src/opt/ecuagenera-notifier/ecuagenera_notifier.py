import os
import smtplib
import socket
from email.message import EmailMessage

import yaml

from ecuagenera_website import EcuageneraWebsite

if __name__ == "__main__":
    mail_body = ""
    send_email = False

    config_file_path = f'{os.path.dirname(os.path.realpath(__file__))}/config.yml'
    if not os.path.isfile(config_file_path):
        raise Exception("Please create config.yml first")

    config = None
    with open(config_file_path, 'r') as stream:
        try:
            config = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)

    # Step 1: Gather item availability information from website
    with EcuageneraWebsite(headless=True) as ew:
        ew.open_website()
        available_items = {}

        for item_id in config['item_ids']:
            if ew.is_item_available(item_id):
                available_items[item_id] = ew.get_item_name(item_id)

        if len(available_items) == 0:
            print("No item is available yet")
            quit()
        
        mail_body += f"The following items are now available in ecuagenera.com:\n\n"

        for i, (item_id, item_name) in enumerate(available_items.items()):
            mail_body += f"- #{i}: {item_name} (ID: {item_id})\n"

        send_email = True
        print(mail_body)

    # Step 2: Send email about latest updates
    if send_email:
        mailserver = None
        try:
            mailserver = smtplib.SMTP(
                config['smtp_server'], config['smtp_port'])
            mailserver.ehlo()
            mailserver.starttls()
            mailserver.login(config['smtp_user'], config['smtp_pw'])

            from_email_address = config['from_email']
            to_email_addresses = config['to_email']

            msg = EmailMessage()
            msg.set_content(mail_body)
            msg['From'] = from_email_address
            msg['To'] = to_email_addresses
            msg['Subject'] = 'Ecuagenera Notification'

            mailserver.sendmail(from_addr=from_email_address,
                                to_addrs=to_email_addresses, msg=msg.as_string())
        except socket.gaierror as e:
            print("Socket issue while sending email - Are you in VPN/proxy?")
            raise e
        except Exception as e:
            print(f"Something went wrong while sending an email: {e}")
            raise e
        finally:
            if mailserver != None:
                mailserver.quit()
