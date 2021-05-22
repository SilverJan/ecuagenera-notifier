#!/usr/bin/env python3

"""
Small helper script to send ad-hoc messages to registered users

Execute via `python3 -m helpers.send_telegram_msg` from project root
"""

from telegram import Bot
from telegram.ext import PicklePersistence
from ecua_utils.util import reload_config_yml


def send_message():
    persistence = PicklePersistence(
        filename=config["telegram_persistence_file"])
    bot = Bot(config['telegram_bot_token'])

#     msg = """
# Hi there,

# I have two great news for you\\:

# __1\\) Massive performance update__

# In the recent update\\, the average time per user has been reduced from \\~2\\-3 minutes to \\~5 seconds\\. 
# This means that the bot can run now *several times per hour*\\, instead of just once or twice like before\\. 
# With this improvement\\, the bot should be able to find every single available slot for you\\! \\:\\)

# __2\\) Referrals__

# Ever talked to a fellow learner who is struggling to find slots \\(in person or in a Telegram group\\)\\?
# Share the sg\\-dc\\-booking\\-bot with them\\, and you get a *free 2 weeks account extension* for every successfully registered user\\. 

# Just tell them to mention your CDC username \\(00xxxxxx\\) in the text field when registering\\.

# Have a great long weekend ahead\\! \\:\\)
# """

    msg = """
There are the following available sessions for your (00482785) next 2B practical lesson (2BL3) @ CDC:

- Available session #1: 20/05/2021 @ 16:25 - 18:05 (reserved)

You have already booked the following session(s):

- Booked session #1: 03/06/2021 @ 16:25 - 18:05

-> There is an earlier session available - Consider rebooking!

Session(s) in the list have been auto-reserved (see above) - Don't forget to book or cancel the session(s) within 15mins!
"""

    for k, v in persistence.get_user_data().items():
        try:
            chat = bot.getChat(k)
            if v[k] == "00482785":
                chat.send_message(text=msg)
        except:
            pass


if __name__ == '__main__':
    global config
    config = reload_config_yml()

    send_message()
