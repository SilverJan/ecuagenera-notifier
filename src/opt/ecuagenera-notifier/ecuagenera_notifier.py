import os
import platform
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

    headless = False
    if "arm" in platform.machine():
        headless = True

    # Step 1: Gather item availability information from website
    with EcuageneraWebsite(username=config['username'], password=config['password'], headless=headless) as ew:
        ew.open_website()

        # login only if checkout is enabled
        if config['do_checkout']:
            ew.login()
            ew.clear_basket()

        available_items = {}

        for i, item_id in enumerate(config['item_ids']):
            if ew.is_item_available(item_id):
                print(f"Item {item_id} is in stock")
                available_items[item_id] = ew.get_item_name(item_id)
                ew.add_to_basket(quantity=config['item_quantities'][i])
            else:
                print(f"Item {item_id} is not in stock")

        if len(available_items) == 0:
            print("No item is available yet")
            quit()

        mail_body += f"The following items are now available in ecuagenera.com:\n\n"

        for i, (item_id, item_name) in enumerate(available_items.items()):
            mail_body += f"- #{i}: {item_name} (ID: {item_id})\n"

        def checkout():
            global mail_body

            # check if item has been ordered before
            # TODO: this won't work on GitHub Actions
            ordered_items_file_path = '/tmp/ordered_items'
            print('Check if available items have been ordered before')
            if os.path.exists(ordered_items_file_path):
                with open(ordered_items_file_path, 'r+') as stream:
                    ordered_items = stream.read()
                    for (item_id, _) in available_items.items():
                        if str(item_id) in ordered_items:
                            mail_body += f"\nItem {item_id} has already been ordered before. Not proceeding with order."
                            return

            print('Trying to checkout')
            if ew.checkout():
                mail_body += "\nItems have been checked out, but not being paid for yet. Please proceed to pay!"
                with open(ordered_items_file_path, 'a') as stream:
                    for (item_id, _) in available_items.items():
                        stream.write(f"{item_id}\n")
            else:
                mail_body += "\nTried to checkout but it failed."

        if config['do_checkout']:
            checkout()

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
