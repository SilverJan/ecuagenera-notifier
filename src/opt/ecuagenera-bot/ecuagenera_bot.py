import argparse
import datetime
import os
import platform
import random
import smtplib
import socket
import sys
import time
import traceback
from email.message import EmailMessage

import yaml
from telegram import Bot
from telegram.error import Unauthorized
from telegram.ext import PicklePersistence

from ecua_utils.db_utils import (Config, get_db_users, get_db_users_field,
                                 set_user_config, set_user_expiry_date)
from ecua_utils.logger import Logger
from ecua_utils.util import reload_config_yml
from ecuagenera_curl import EcuageneraCurl
from ecuagenera_website import EcuageneraWebsite


def inform_user_if_item_available(user, mail_body):
    # step 1: check for user expiry date and add message if account expires within 7 days
    if 'expiry_date' in user.keys():
        user_expiry_date = datetime.datetime.strptime(
            user['expiry_date'], '%Y-%m-%d')
        diff = datetime.datetime.utcnow() - user_expiry_date

        if diff.days >= -7:
            logger.info(
                f"Inform user {email} that expiry date is within 7 days.")
            mail_body += f"\n\nImportant: Your account is expiring within the next 7 days (on {user_expiry_date.strftime('%Y-%m-%d')}). "
            mail_body += "Please extend via Telegram bot (https://telegram.me/ecuagenera_bot) by typing '/extendbasic' or '/extendpremium'."

    # step 2: send telegram message (if registered)
    if os.path.exists(config['telegram_persistence_file']):
        persistence = PicklePersistence(
            filename=config['telegram_persistence_file'])
        for i, (telegram_id, dataset) in enumerate(persistence.get_user_data().items()):
            dataset_cdc_user = dataset.get(telegram_id)
            if dataset_cdc_user is not None and email in dataset_cdc_user:
                logger.debug(
                    f"User {email} has linked telegram account ({telegram_id})")
                bot = Bot(config['telegram_bot_token'])
                try:
                    bot.send_message(chat_id=telegram_id, text=mail_body)
                except Unauthorized:
                    logger.debug(
                        f"User {email} has blocked Telegram bot")
                    pass


def run_curl(user):
    inform_user = False
    mail_body = ''

    # get some config data
    wishlist = ''
    auto_checkout = False
    user_plan = ''
    if 'config' in user.keys():
        if Config.AUTO_CHECKOUT in user['config'].keys():
            auto_checkout = user['config'][Config.AUTO_CHECKOUT]
        if Config.PLAN in user['config'].keys():
            user_plan = user['config'][Config.PLAN]
        if Config.WISHLIST in user['config'].keys():
            wishlist = user['config'][Config.WISHLIST]

    if wishlist == '' or wishlist == 'na':
        logger.debug("User has no items in wishlist. Exit early")
        return

    # Step 1: Gather item availability information from website
    with EcuageneraCurl(username=user['email'], password=user['pw'], headless=headless) as ec:
        # login only if checkout is enabled
        # TBD tell user that basket is cleared every 5mins
        # if auto_checkout:
        #     if user['pw'] != '':
        #         ew.login()
        #         ew.clear_basket()
        #     else:
        #         logger.warning('Could not auto-checkout because user did not provide pw')

        available_items = {}
        available_ordered_items = []
        for i, wishlist_item in enumerate(wishlist.splitlines()):
            item_id = wishlist_item
            quantity = None
            if ';' in wishlist_item:
                item_id = wishlist_item.split(';')[0]
                quantity = wishlist_item.split(';')[1]
            ec.get_item_name(item_id)
            if ec.is_item_available(item_id):
                logger.info(f"Item {item_id} is in stock")
                available_items[item_id] = ec.get_item_name(item_id)
                if quantity is not None:
                    available_ordered_items.append(item_id)
                    ec.add_to_basket(quantity=quantity)
            else:
                logger.info(f"Item {item_id} is not in stock")

        if len(available_items) == 0:
            logger.info("No item is available yet")
            return

        mail_body += f"The following items are now available in ecuagenera.com:\n\n"

        for i, (item_id, item_name) in enumerate(available_items.items(), start=1):
            mail_body += f"- #{i}: {item_name} (ID: {item_id})\n"

        # if auto_checkout:
        #     if user['pw'] != '':
        #         # do checkout
        #         logger.debug('Trying to checkout')
        #         if ec.checkout():
        #             mail_body += "\nThe following items have been checked out, but not been paid for yet:\n\n"

        #             # remove ordered items from wishlist and update db
        #             # TODO: confirm if they really were ordered
        #             new_wishlist = ''
        #             for old_wishlist_line in wishlist.splitlines():
        #                 old_wishlist_item = old_wishlist_line
        #                 if ";" in old_wishlist_item:
        #                     old_wishlist_item = old_wishlist_line.split(';')[0]
        #                 if old_wishlist_item in available_ordered_items:
        #                     mail_body += f"- {old_wishlist_item}\n"
        #                     continue
        #                 else:
        #                     new_wishlist += f"{old_wishlist_line}\n"
        #             new_wishlist = new_wishlist.strip()
        #             logger.debug(
        #                 f'Attempting to update database entry {Config.WISHLIST} for user {email}:\n{new_wishlist}')
        #             set_user_config(user, Config.WISHLIST, new_wishlist)
        #             mail_body += "\nPlease proceed to pay by sending an email to the ecuagenera.com team."
        #             mail_body += "\n\nHint: You should have received an email with the invoice from ecuagenera.com."
        #         else:
        #             logger.warning("Tried to checkout but it failed")
        #     else:
        #         logger.warning('Could not auto-checkout because user did not provide pw')

        inform_user = True

    # Step 2: Send Telegram message if necessary
    logger.info(mail_body)
    if inform_user:
        inform_user_if_item_available(user, mail_body)


def run_web(user, headless):
    inform_user = False
    mail_body = ''

    # get some config data
    wishlist = ''
    auto_checkout = False
    user_plan = ''
    if 'config' in user.keys():
        if Config.AUTO_CHECKOUT in user['config'].keys():
            auto_checkout = user['config'][Config.AUTO_CHECKOUT]
        if Config.PLAN in user['config'].keys():
            user_plan = user['config'][Config.PLAN]
        if Config.WISHLIST in user['config'].keys():
            wishlist = user['config'][Config.WISHLIST]

    if wishlist == '' or wishlist == 'na':
        logger.info("User has no items in wishlist. Exit early")
        return

    # Step 1: Gather item availability information from website
    with EcuageneraWebsite(username=user['email'], password=user['pw'], headless=headless) as ew:
        ew.open_website()

        # login only if checkout is enabled
        # TBD tell user that basket is cleared every 5mins
        if auto_checkout:
            if user['pw'] != '':
                ew.login()
                ew.clear_basket()
            else:
                logger.warning(
                    'Could not auto-checkout because user did not provide pw')

        available_items = {}
        available_ordered_items = []
        for i, wishlist_item in enumerate(wishlist.splitlines()):
            item_id = wishlist_item
            quantity = None
            if ';' in wishlist_item:
                item_id = wishlist_item.split(';')[0]
                quantity = wishlist_item.split(';')[1]
            if ew.is_item_available(item_id):
                logger.info(f"Item {item_id} is in stock")
                available_items[item_id] = ew.get_item_name(item_id)
                if quantity is not None:
                    available_ordered_items.append(item_id)
                    ew.add_to_basket(quantity=quantity)
            else:
                logger.info(f"Item {item_id} is not in stock")

        if len(available_items) == 0:
            logger.info("No item is available yet")
            return

        mail_body += f"The following items are now available in ecuagenera.com:\n\n"

        for i, (item_id, item_name) in enumerate(available_items.items(), start=1):
            mail_body += f"- #{i}: {item_name} (ID: {item_id})\n"

        if auto_checkout:
            if user['pw'] != '':
                # do checkout
                logger.debug('Trying to checkout')
                if ew.checkout():
                    mail_body += "\nThe following items have been checked out, but not been paid for yet:\n\n"

                    # remove ordered items from wishlist and update db
                    # TODO: confirm if they really were ordered
                    new_wishlist = ''
                    for old_wishlist_line in wishlist.splitlines():
                        old_wishlist_item = old_wishlist_line
                        if ";" in old_wishlist_item:
                            old_wishlist_item = old_wishlist_line.split(';')[0]
                        if old_wishlist_item in available_ordered_items:
                            mail_body += f"- {old_wishlist_item}\n"
                            continue
                        else:
                            new_wishlist += f"{old_wishlist_line}\n"
                    new_wishlist = new_wishlist.strip()
                    logger.debug(
                        f'Attempting to update database entry {Config.WISHLIST} for user {email}:\n{new_wishlist}')
                    set_user_config(user, Config.WISHLIST, new_wishlist)
                    mail_body += "\nPlease proceed to pay by sending an email to the ecuagenera.com team."
                    mail_body += "\n\nHint: You should have received an email with the invoice from ecuagenera.com."
                else:
                    logger.warning("Tried to checkout but it failed")
            else:
                logger.warning(
                    'Could not auto-checkout because user did not provide pw')

        inform_user = True

    # Step 2: Send Telegram message if necessary
    logger.info(mail_body)
    if inform_user:
        inform_user_if_item_available(user, mail_body)


if __name__ == "__main__":
    PARSER = argparse.ArgumentParser()

    PARSER.add_argument('--email', type=str,
                        help='The email to run the bot for', required=False)
    PARSER.add_argument('--method', type=str,
                        help='Method to run (web;curl)', default='curl', required=False)
    PARSER.add_argument('--log_level', type=int,
                        help='The log level (10-50)', default=20, required=False)
    PARSER.add_argument('--headless',
                        help='Headless mode', required=False, action='store_true')
    ARGS = PARSER.parse_args()

    logger = Logger.logger
    logger.setLevel(ARGS.log_level)

    config = reload_config_yml()

    # set headless to default for Raspberry Pi or if passed via commandline
    headless = False
    if ARGS.headless != None:
        headless = ARGS.headless
    if "arm" in platform.machine():
        headless = True

    # get user list from DB
    all_users = get_db_users()

    # filter users who do not have valid account anymore
    users = []
    for user in all_users:
        # also filter email in case ARGS is set
        if ARGS.email is not None:
            if user['email'] == ARGS.email:
                users.append(user)
                break
            else:
                continue
        users.append(user)

    # shuffle order (to ensure everyone gets their turn)
    random.shuffle(users)

    try:
        for user in users:
            logger.info(f"------------------------------")
            email = user['email']
            logger.info(
                f"Running for user {email}")
            logger.info(f"------------------------------")
            if ARGS.method == 'web':
                run_web(user, headless)
            elif ARGS.method == 'curl':
                run_curl(user)

    except Exception as e:
        logger.error(e)
        logger.error(traceback.format_exc())
        sys.exit(1)
