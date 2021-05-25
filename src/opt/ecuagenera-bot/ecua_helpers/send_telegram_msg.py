#!/usr/bin/env python3

"""
Small helper script to send ad-hoc messages to registered users

Execute via `python3 -m ecua_helpers.send_telegram_msg` from project root
"""

from telegram import Bot
from telegram.ext import PicklePersistence
from ecua_utils.util import reload_config_yml


def send_message():
    persistence = PicklePersistence(
        filename=config["telegram_persistence_file"])
    bot = Bot(config['telegram_bot_token'])

    msg = """
Hi fellow plant-lovers,

Thanks for registering for the ecuagenera bot. It's great to see how many of you are interested in the bot.

I would like to announce that besides the basic and premium plan, a free plan has been added.

With the free plan you can add up to 1 plant in your wish-list and get notified whenever the plant is available on ecuagenera.com.

Just type /configure and try it out now! :)
"""

    for k, v in persistence.get_user_data().items():
        try:
            chat = bot.getChat(k)
            if v[k] == "plantlover@ecua.com":
                chat.send_message(text=msg)
            # if v[k] == "phangkiankok@yahoo.com":
            #     continue
            chat.send_message(text=msg)
        except:
            pass


if __name__ == '__main__':
    global config
    config = reload_config_yml()

    send_message()
