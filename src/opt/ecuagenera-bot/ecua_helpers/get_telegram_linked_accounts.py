#!/usr/bin/env python3

"""
Small helper script to get a list of user accounts who have linked
their account with the Telegram bot

Execute via `python3 -m ecua_helpers.get_telegram_linked_accounts` from project root
"""

from telegram.ext import PicklePersistence
from telegram import Bot
from tabulate import tabulate

from ecua_utils.util import reload_config_yml
from ecua_utils.db_utils import get_db_users


def print_linked_accounts():
    persistence = PicklePersistence(
        filename=config["telegram_persistence_file"])
    bot = Bot(config['telegram_bot_token'])
    users = get_db_users()

    data = []
    for k, v in persistence.get_user_data().items():
        try:
            chat = bot.getChat(k)
            for user in users:
                if user['email'] in v[k]:
                    expiry_date = user['expiry_date']
                    user_config = None
                    if "config" in user.keys():
                        user_config = user['config']
            data.append([v[k], chat.username,
                         expiry_date, user_config])
        except:
            # print(e)
            pass

    # sort by date
    data = sorted(data, key=lambda x: x[2])
    data_with_index = []

    # add index column
    for i, entry in enumerate(data):
        entry_with_index = [i]
        entry_with_index.extend(entry)
        data_with_index.append(entry_with_index)

    print(tabulate(data_with_index, headers=['#', 'Email',
                                             'Telegram User', 'Expiry', 'Config']))


if __name__ == '__main__':
    global config
    config = reload_config_yml()

    print_linked_accounts()
