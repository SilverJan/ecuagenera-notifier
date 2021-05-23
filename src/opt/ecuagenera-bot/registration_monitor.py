#!/usr/bin/env python3

"""
Monitoring for new registration requests (website -> submitted to formspree.io -> trello board).
Once a new request is submitted via website, formspree will automatically create a new card in the "new" list in the trello board.
This script (triggered by systemd service timer every minute) will detect this and try to create a monoDB (atlas) entry and move the card in the done or problem list.

Autostarted via systemd service timer.
"""

import requests
import json
from datetime import datetime
from dateutil.relativedelta import relativedelta

from ecua_utils.util import reload_config_yml
from ecua_utils.db_utils import get_db_col, get_db_users_field

# API documentation in https://developer.atlassian.com/cloud/trello/rest/
base_url = "https://api.trello.com/1"
# retrieve from https://trello.com/b/W3nV8ZQh/ecuagenera-bot-registrations.json
board_id = "60a0c18aef107c11a87f30fb"
done_idList = "60a0c18aef107c11a87f30fd"
new_idList = "60a0c18aef107c11a87f30fc"
problem_idList = "60a0c18aef107c11a87f30fe"


def get_cards() -> list:
    response = requests.request(
        "GET",
        f"{base_url}/boards/{board_id}/cards",
        headers={
            "Accept": "application/json"
        },
        params={
            'key': config['trello_key'],
            'token': config['trello_token']
        }
    )

    return json.loads(response.text)


def register_user(card):
    username = ''
    pw = ''
    real_name = ''
    email = ''

    data_raw: list = card["desc"].split("\n")
    for entry in data_raw:
        if "__:" in entry:
            key = entry.split("__")[1].strip()
            val = entry.split(":")[1].strip()
            if key == "name":
                real_name = val
            elif key == "email":
                email = val
            elif key == "pw":
                pw = val

    new_user = dict(
        email=email.lower(),
        pw=pw,
        real_name=real_name
    )
    print(f"Trying to add new user {new_user} to db")
    users_col = get_db_col()
    if email in get_db_users_field("email"):
        print("User exists already in db - aborting")
        return False
    result = users_col.insert_one(new_user)
    if result.acknowledged:
        print("Successfully added user to db")
        send_welcome_email(email, real_name)
        return True
    else:
        print("User could not be added to db")
        return False


def send_welcome_email(to_email_address, name):
    # send email
    mailserver = None
    try:
        import smtplib
        import socket
        from email.message import EmailMessage
        mailserver = smtplib.SMTP(
            config['smtp_server'], config['smtp_port'])
        mailserver.ehlo()
        mailserver.starttls()
        mailserver.login(config['smtp_user'], config['smtp_pw'])

        from_email_address = config['from_email']

        msg = EmailMessage()
        msg.set_content(
            f"""Hello {name},

Thank you for registering for the ecuagenera bot.

Please link your account with the @ecuagenera_bot Telegram bot (https://telegram.me/ecuagenera_bot).

Have a great day ahead! :)

Your ecuagenera-bot team.""")
        msg['From'] = from_email_address
        msg['To'] = to_email_address
        msg['Subject'] = f"Welcome to the Ecuagenera Bot"

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


def move_card(card, idList):
    response = requests.request(
        "PUT",
        f"{base_url}/cards/{card['id']}",
        headers={
            "Accept": "application/json"
        },
        params={
            'key': config['trello_key'],
            'token': config['trello_token'],
            'idList': idList
        },
    )
    if response.status_code != 200:
        print("Card could not be moved")
    else:
        print("Card moved")


if __name__ == '__main__':
    global config
    config = reload_config_yml()

    cards = get_cards()
    for card in cards:
        # skip cards in done or problem list
        if card["idList"] != new_idList:
            continue
        # move card into done or problem list
        if register_user(card):
            move_card(card, done_idList)
        else:
            move_card(card, problem_idList)
