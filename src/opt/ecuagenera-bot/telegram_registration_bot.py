#!/usr/bin/env python3
# pylint: disable=W0613, C0116
# type: ignore[union-attr]

"""
Telegram registration management bot for ecuagenera bot.

Autostarted via systemd service.
"""

import html
import json
import os
import platform
import re
import traceback
from datetime import datetime
from typing import Dict
from urllib import parse
from uuid import uuid4

import yaml
from dateutil.relativedelta import relativedelta
from telegram import (InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice,
                      ParseMode, ReplyKeyboardMarkup, ReplyKeyboardRemove,
                      ShippingOption, Update)
from telegram.error import NetworkError
from telegram.ext import (CallbackContext, CallbackQueryHandler,
                          CommandHandler, ConversationHandler, Filters,
                          MessageHandler, PicklePersistence,
                          PreCheckoutQueryHandler, ShippingQueryHandler,
                          Updater)

from ecua_utils.db_utils import (Config, get_db_users, get_db_users_field,
                                 set_user_config, set_user_expiry_date)
from ecua_utils.logger import TelegramLogger
from ecua_utils.util import reload_config_yml

EMAIL = range(1)
SELECTING_ACTION, CONFIGURE_WISHLIST, CONFIGURE_AUTO_CHECKOUT, RETURN_WISHLIST, RETURN_AUTO_CHECKOUT = map(
    chr, range(1, 6))
AUTO_CHECKOUT_ON, AUTO_CHECKOUT_OFF = map(chr, range(6, 8))


def get_user_data(update: Update, context: CallbackContext) -> tuple:
    key = update.effective_chat.id
    email = context.user_data[key]
    registered_users: list = get_db_users()
    registered_emails: list = get_db_users_field('email')
    index = registered_emails.index(email)
    user = registered_users[index]
    return user, email, registered_users


def link(update: Update, context: CallbackContext) -> int:
    reply_text = ""
    key = update._effective_chat.id
    if key in context.user_data:
        reply_text += (
            f"You already told me your email address ({context.user_data.get(key)}).\n\n"
            "If you want to unlink your account from this Telegram service, please send me a text /unlink.\n\n"
            "If you want to edit your email address, please /unlink and then /link again."
        )
        update.message.reply_text(reply_text)
        return ConversationHandler.END

    else:
        reply_text += (
            "To get notifications, I need to know your ecuagenera.com email address. Please type it now.\n\n"
            "Hint: Type /cancel to abort the registration."
        )
        logger.debug("Waiting for input..")
    update.message.reply_text(reply_text)

    return EMAIL


def unlink_command(update: Update, context: CallbackContext) -> int:
    reply_text = ""
    key = update.effective_chat.id
    if key in context.user_data:
        email = context.user_data.get(key)
        reply_text += (
            "Sad to see you leave!\n\n"
            f"I will unlink your email address ({email}) from this account now.\n\n"
            "If you want to link your account again, please send me a text /link."
        )
        logger.info(f"Deleted entry for user {email}/{key}")
        context.user_data.pop(key)
    else:
        reply_text += (
            "You can't unlink your account, if you haven't linked it yet :)"
        )
    update.message.reply_text(reply_text)
    return ConversationHandler.END


def email(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    key = update.effective_chat.id
    email = update.message.text

    # verify format
    # TODO
    if not "@" in email:
        logger.info(
            f"Entered email ({email}) is not an email address")
        update.message.reply_text(
            "Please enter your ecuagenera.com email address")
        return EMAIL

    # verify if registered
    registered_users: list = get_db_users()
    registered_emails: list = get_db_users_field('email')
    if not email in registered_emails:
        logger.info(
            f"Cannot find entered email ({email}) in registered user list")
        update.message.reply_text(
            "Seems you have not registered your account yet. Please register first at: https://ecuagenera-bot.bss.design\n\n"
            "If you have already registered via the website, please try linking (/link) again in 30 minutes."
        )
        return ConversationHandler.END

    index = registered_emails.index(email)
    logger.info(
        f"Linked chat ID ({user.username}/{key}) with email '{email}'")

    # Store value
    context.user_data[key] = email
    actual_user = registered_users[index]["real_name"]

    update.message.reply_text(
        f'Thank you, {actual_user}! Please /configure your wish-list now, to get notifications :)')

    return ConversationHandler.END


def configure(update: Update, context: CallbackContext) -> int:
    key = update._effective_chat.id
    if not key in context.user_data:
        update.message.reply_text(
            "Hmm, you haven't linked your account yet, so I don't know who you are. Please /link first.")
        return ConversationHandler.END

    buttons = [
        [
            InlineKeyboardButton(text='Configure wish-list',
                                 callback_data=str(CONFIGURE_WISHLIST)),
        ],
        [
            InlineKeyboardButton(text='Configure auto-checkout',
                                 callback_data=str(CONFIGURE_AUTO_CHECKOUT)),
        ],
        [
            InlineKeyboardButton(
                text='Done', callback_data=str(ConversationHandler.END)),
        ],
    ]
    keyboard = InlineKeyboardMarkup(buttons)

    update.message.reply_text(
        "Which setting do you want to configure?", reply_markup=keyboard
    )
    return SELECTING_ACTION


def configure_wishlist(update: Update, context: CallbackContext) -> str:
    user, _, _ = get_user_data(update, context)

    wishlist = ""
    user_plan = ""
    if 'config' in user.keys():
        if Config.WISHLIST in user['config'].keys():
            wishlist = user['config'][Config.WISHLIST]
        if Config.PLAN in user['config'].keys():
            user_plan = user['config'][Config.PLAN]

    if user_plan != "basic" and user_plan != "premium":
        update.effective_message.reply_text(
            'Wishlist is a paid feature. Enable it via /extendbasic or /extendpremium and try again.', reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END

    update.effective_message.reply_text('Edit your ecuagenera bot wish-list\\.\n\n'
                                        'Syntax: `\\<item\\-id\\>\\;\\<quantity\\>`\n\n'
                                        '*Hints*:\n'
                                        '\\- item\\-id can be retrieved from item URL on ecuagenera website\n'
                                        '  \\- Example 1 \\(Anthurium regale\\): www\.ecuagenera\\.com\\/\\[\\.\\.\\]\\/Products\\/PIE2081 \\-\\> `PIE2081`\\)\n'
                                        '  \\- Example 2 \\(Anthurium luxurians\\): www\.ecuagenera\\.com\\/\\[\\.\\.\\]\\/ObjectID\\=471110 \\-\\> `471110`\\)\n'
                                        '\\- Quantity is only relevant for auto\\-checkout feature \\(premium\\)\\\n'
                                        '\\- Quantity can be empty \\(means bot will notify only\\)\n'
                                        '\\- Quantity can not be more than 3\n'
                                        '\\- Wishlist can not exceed more than 3 \\(basic\\) or 6 \\(premium\\) items\n\n'
                                        '*Example*\\:\n'
                                        '```\n'
                                        'PIE2081;1\n'
                                        '471110\n'
                                        '```\n'
                                        'Above example would\n'
                                        '\\- Order one Anthurium regale\n'
                                        '\\- Notify once Anthurium luxurians is available', parse_mode="MarkdownV2", disable_web_page_preview=True)

    if wishlist and wishlist != "":
        update.effective_message.reply_text(
            '*Current wish-list*:', parse_mode='MarkdownV2')
        update.effective_message.reply_text(
            f'```{wishlist.strip()}```', parse_mode='MarkdownV2')
    else:
        update.effective_message.reply_text(
            '*Current wish-list*:\n\empty\n', parse_mode="MarkdownV2")
    update.effective_message.reply_text(
        '\nEnter\\/Modify your wish-list now or \\/cancel\\.', parse_mode='MarkdownV2')

    update.callback_query.answer()
    # update.callback_query.edit_message_text(
    #     text=respond_text, parse_mode="MarkdownV2")

    return RETURN_WISHLIST


def configure_auto_checkout(update: Update, context: CallbackContext) -> str:
    user, _, _ = get_user_data(update, context)

    auto_checkout = False
    user_plan = ''
    if 'config' in user.keys():
        if Config.AUTO_CHECKOUT in user['config'].keys():
            auto_checkout = user['config'][Config.AUTO_CHECKOUT]
        if Config.PLAN in user['config'].keys():
            user_plan = user['config'][Config.PLAN]

    if not user_plan == "premium":
        update.effective_message.reply_text(
            'Auto-checkout is a premium features. Enable it via /extendpremium and try again.', reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END

    respond_text = ('Edit your auto\\-checkout setting \\(bot will try to checkout available plants from the wish-list\\, in the specific quantity\\)\\.\n\n'
                    '*Hint: Please ensure that you have configured your billing \\& delivery address in the ecuagenera\\.com website\\.\\, else the auto\\-checkout will fail\\!*\n\n'
                    'Current setting: ')

    if auto_checkout:
        respond_text += f'`A\\) Auto\\-checkout on`'
    else:
        respond_text += f'`B\\) Auto\\-checkout off \\(default\\)`'

    respond_text += "\n\nSelect your preferred option below:"

    buttons = [
        [
            InlineKeyboardButton(text='A) Enable auto-checkout',
                                 callback_data=str(AUTO_CHECKOUT_ON)),
            InlineKeyboardButton(text='B) Disable auto-checkout (default)',
                                 callback_data=str(AUTO_CHECKOUT_OFF))
        ],
        [
            InlineKeyboardButton(
                text='Exit', callback_data=str(ConversationHandler.END)),
        ],
    ]
    keyboard = InlineKeyboardMarkup(buttons)

    update.callback_query.answer()
    update.callback_query.edit_message_text(
        text=respond_text, reply_markup=keyboard, parse_mode="MarkdownV2")

    return RETURN_AUTO_CHECKOUT


def update_db_auto_checkout(update: Update, context: CallbackContext) -> int:
    user, email, _ = get_user_data(update, context)

    if update.callback_query.data == str(AUTO_CHECKOUT_ON):
        logger.info(
            f'Attempting to update database entry {Config.AUTO_CHECKOUT} for user {email}: True')
        set_user_config(user, Config.AUTO_CHECKOUT, True)
    elif update.callback_query.data == str(AUTO_CHECKOUT_OFF):
        logger.info(
            f'Attempting to update database entry {Config.AUTO_CHECKOUT} for user {email}: False')
        set_user_config(user, Config.AUTO_CHECKOUT, False)
    else:
        update.effective_message.reply_text(
            'Bye!', reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END

    update.effective_message.reply_text(
        'I have updated the configuration for you. Bye!', reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END


def update_db_wishlist(update: Update, context: CallbackContext) -> int:
    user_input = update.message.text
    user, email, _ = get_user_data(update, context)

    user_plan = False
    if 'config' in user.keys():
        if Config.PLAN in user['config'].keys():
            user_plan = user['config'][Config.PLAN]

    # set max quantity based on user's plan
    max_quantity = 3

    # set max wish-list item based on user's plan
    if user_plan == 'basic' and len(user_input.splitlines()) > 3:
        update.effective_message.reply_text(
            f"The basic plan only allows a maximum of 3 items in the wish-list. Reduce and try again!")
        update.effective_message.reply_text(
            f"Hint: If you switch to the premium plan (via /extendpremium) you can add up to 6 items in your wish-list.")
        return RETURN_WISHLIST
    elif user_plan == 'premium' and len(user_input.splitlines()) > 6:
        update.effective_message.reply_text(
            f"You have exceeded the maximum of 6 items in the wish-list. Please reduce and try again!")
        return RETURN_WISHLIST

    items_without_quantity = []
    for line in user_input.splitlines():
        if ';' in line:
            items_without_quantity.append(line.split(';')[0])
        else:
            items_without_quantity.append(line)

    for line in user_input.splitlines():
        # check for valid format and quantity
        if (";" in line and not re.match(r"^[a-zA-Z0-9-]{5,};[1-%s}]$" % (max_quantity), line)) or (not ";" in line and not re.match(r"^[a-zA-Z0-9-]{5,}$", line)):
            update.effective_message.reply_text(
                f"Invalid format or quantity for line '{line}'. Try again!")
            return RETURN_WISHLIST

        # check for multiple occurrences of the same item id
        item_id = line
        if ';' in line:
            item_id = line.split(';')[0]
        if items_without_quantity.count(item_id) > 1:
            update.effective_message.reply_text(
                f"Item '{item_id}' is mentioned multiple times. Try again!")
            return RETURN_WISHLIST

    logger.info(
        f'Attempting to update database entry {Config.WISHLIST} for user {email}:\n{user_input}')
    set_user_config(user, Config.WISHLIST, user_input)

    update.effective_message.reply_text(
        'I have updated the configuration for you. Bye!', reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END


def cancel(update: Update, context: CallbackContext) -> int:
    update.effective_message.reply_text(
        'Bye! I hope we can talk again some day.', reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END


def help_command(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /help is issued."""
    update.message.reply_text(
        'I can listen to the following actions:\n\n'
        '- /link - Link your Telegram account with your registered ecuagenera.com email, to receive notifications\n'
        '- /unlink - Unlink your Telegram account to stop receiving notifications\n'
        '- /configure - Configure settings (e.g. wish-list, auto-checkout)\n'
        '- /userinfo - Show information about your user (name, service expiry date, registered email, etc.)\n'
        '- /extendbasic - Extend service (basic plan)\n'
        '- /extendpremium - Extend service (premium plan)\n'
        '- /support - Get support\n'
        '- /help - Show this help'
    )


def support_command(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /support is issued."""
    update.message.reply_text(
        'If you need any kind of support, write a message to @silverjanx'
    )
    return ConversationHandler.END


def start_command(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /start is issued."""
    update.message.reply_text(
        "Hi, I'm the Ecuagenera Bot, Botti!\n\n"
        "I can send out notifications when your favorite ecuagenera.com plants are available.\n\n"
        'Get started by typing /link.'
    )


def unknown_command(update: Update, context: CallbackContext) -> None:
    """Send a message when an unknown command is issued."""
    update.message.reply_text(
        "Hmm, I don't know what to answer. Please run /help to see what I can do for you.")


def user_info_command(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /userinfo is issued."""
    reply_text = ""
    key = update._effective_chat.id
    if key in context.user_data:
        user, email, _ = get_user_data(update, context)
        try:
            actual_user_name = user['real_name']
            actual_user_expiry_date = user['expiry_date']
            actual_user_registered_email = user['email']
            actual_user_plan = 'n.a.'
            actual_user_auto_checkout = False
            actual_user_wishlist = ''
            if 'config' in user.keys():
                if Config.PLAN in user['config'].keys():
                    actual_user_plan = user['config'][Config.PLAN]
                if Config.WISHLIST in user['config'].keys():
                    actual_user_wishlist = user['config'][Config.WISHLIST]
                if Config.AUTO_CHECKOUT in user['config'].keys():
                    actual_user_auto_checkout = user['config'][Config.AUTO_CHECKOUT]

            reply_text += (
                f"This is the information I got about you:\n\n"
                f"- Name: {actual_user_name}\n"
                f"- Service expiry date: {actual_user_expiry_date}\n"
                f"- Registered email: {actual_user_registered_email}\n"
                f"- Plan: {actual_user_plan}\n"
                f"- Auto-checkout: {actual_user_auto_checkout}\n"
                f"- Wish-list:\n\n{actual_user_wishlist}\n\n"
                "If any of the above data is wrong, please ask for /support."
            )
        except ValueError:
            reply_text += ("Something is wrong the username that you entered. Please /unlink and /link again.")

    else:
        reply_text += (
            "Hmm, you haven't linked your account yet, so I don't know who you are. Please /link first."
        )
    update.message.reply_text(reply_text)
    return ConversationHandler.END


def start_extension_basic_callback(update: Update, context: CallbackContext) -> None:
    key = update.effective_chat.id
    if not key in context.user_data:
        update.message.reply_text(
            "You must first tell me who you are before you can extend your account. Do that via /link.")
        return ConversationHandler.END
    username = context.user_data[key]

    chat_id = update.message.chat_id
    title = "Account Extension (Basic plan)"
    description = f"Extend your ({username}) ecuagenera-bot account validity by one more month from today (basic plan). See https://ecuagenera-bot.bss.design/pricing.html for details."
    # select a payload just for you to recognize its the donation from your bot
    payload = f"username: {username}; extension; basic"
    provider_token = config['telegram_bot_stripe_token_test'] if is_test else config['telegram_bot_stripe_token']
    start_parameter = "extension-basic-payment"
    currency = "SGD"
    # price in dollars
    price = 10
    # price * 100 so as to include 2 decimal points
    prices = [LabeledPrice("1-month account extension (basic)", price * 100)]
    logger.info(f"Trying to invoice user {username} now (extension; basic)")
    context.bot.send_invoice(
        chat_id, title, description, payload, provider_token, start_parameter, currency, prices
    )


def start_extension_premium_callback(update: Update, context: CallbackContext) -> None:
    key = update.effective_chat.id
    if not key in context.user_data:
        update.message.reply_text(
            "You must first tell me who you are before you can extend your account. Do that via /link.")
        return ConversationHandler.END
    username = context.user_data[key]

    chat_id = update.message.chat_id
    title = "Account Extension (Premium plan)"
    description = f"Extend your ({username}) ecuagenera-bot account validity by one more month from today (premium plan). See https://ecuagenera-bot.bss.design/pricing.html for details."
    # select a payload just for you to recognize its the donation from your bot
    payload = f"username: {username}; extension; premium"
    provider_token = config['telegram_bot_stripe_token_test'] if is_test else config['telegram_bot_stripe_token']
    start_parameter = "extension-premium-payment"
    currency = "SGD"
    # price in dollars
    price = 20
    # price * 100 so as to include 2 decimal points
    prices = [LabeledPrice("1-month account extension (premium)", price * 100)]
    logger.info(f"Trying to invoice user {username} now (extension; premium)")
    context.bot.send_invoice(
        chat_id, title, description, payload, provider_token, start_parameter, currency, prices
    )


def precheckout_callback(update: Update, context: CallbackContext) -> None:
    query = update.pre_checkout_query
    # check the payload, is this from your bot?
    if not "username" in query.invoice_payload:
        # answer False pre_checkout_query
        logger.warning(
            f"Something went wrong user tried to pay (payload: '{query.invoice_payload}'')")
        query.answer(ok=False, error_message="Something went wrong...")
    else:
        logger.info(
            f"User successfully paid (payload: '{query.invoice_payload}')")
        query.answer(ok=True)


# finally, after contacting the payment provider...
def successful_payment_callback(update: Update, context: CallbackContext) -> None:
    try:
        payload = update.message.successful_payment.invoice_payload
        user, _, _ = get_user_data(update, context)
        new_expiry_date = datetime.today() + relativedelta(months=+1)
        set_user_expiry_date(user, new_expiry_date.strftime("%Y-%m-%d"))
        if "basic" in payload:
            set_user_config(user, Config.PLAN, 'basic')
            # reset settings in case user downgraded
            set_user_config(user, Config.AUTO_CHECKOUT, False)
        elif "premium" in payload:
            set_user_config(user, Config.PLAN, 'premium')
        else:
            raise Exception(f"Unknown payload: {payload}")
        update.message.reply_text("Thank you for your payment!\n"
                                  "The change has been updated in the database.\n\n"
                                  "Check /userinfo for the latest service expiry date / premium status.")
    except Exception as e:
        logger.error(f"Something happened during database update: {e}")
        update.message.reply_text(
            "An error happened during database update. Please contact /support.")


def error_handler(update: object, context: CallbackContext) -> None:
    """Log the error and send a telegram message to notify the developer."""
    # Log the error before we do anything else, so we can see it even if something breaks.
    logger.error(msg="Exception while handling an update:",
                 exc_info=context.error)

    # traceback.format_exception returns the usual python message about an exception, but as a
    # list of strings rather than a single string, so we have to join them together.
    tb_list = traceback.format_exception(
        None, context.error, context.error.__traceback__)
    tb_string = ''.join(tb_list)

    # Build the message with some markup and additional information about what happened.
    # You might need to add some logic to deal with messages longer than the 4096 character limit.
    update_str = update.to_dict() if isinstance(update, Update) else str(update)
    message = (
        f'An exception was raised while handling an update\n'
        f'<pre>update = {html.escape(json.dumps(update_str, indent=2, ensure_ascii=False))}'
        '</pre>\n\n'
        f'<pre>context.chat_data = {html.escape(str(context.chat_data))}</pre>\n\n'
        f'<pre>context.user_data = {html.escape(str(context.user_data))}</pre>\n\n'
        f'<pre>{html.escape(tb_string)}</pre>'
    )

    # Finally, send the message to admin
    context.bot.send_message(chat_id='1460757250',
                             text=message, parse_mode=ParseMode.HTML)


def main() -> None:
    # Create the Updater and pass it your bot's token.
    persistence = PicklePersistence(
        filename=config['telegram_persistence_file'])
    try:
        updater = Updater(
            config['telegram_bot_token_test'] if is_test else config['telegram_bot_token'], persistence=persistence)
        updater.start_polling()
        updater.stop()
    # handle proxy errors
    except NetworkError:
        REQUEST_KWARGS = {
            'proxy_url': 'http://127.0.0.1:3128/'
        }
        updater = Updater(
            config['telegram_bot_token_test'] if is_test else config['telegram_bot_token'], persistence=persistence, request_kwargs=REQUEST_KWARGS)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Add conversation handler for /link
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('link', link)],
        states={
            EMAIL: [MessageHandler(Filters.text & ~Filters.command, email)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    dispatcher.add_handler(conv_handler)

    # Add conversation handler for /configure
    conv_config_handler = ConversationHandler(
        entry_points=[CommandHandler('configure', configure)],
        states={
            SELECTING_ACTION: [
                CallbackQueryHandler(
                    configure_wishlist, pattern='^' + str(CONFIGURE_WISHLIST) + '$'),
                CallbackQueryHandler(
                    configure_auto_checkout, pattern='^' + str(CONFIGURE_AUTO_CHECKOUT) + '$'),
                CallbackQueryHandler(
                    cancel, pattern='^' + str(ConversationHandler.END) + '$'),
            ],
            RETURN_AUTO_CHECKOUT: [
                CallbackQueryHandler(
                    update_db_auto_checkout, pass_chat_data=True)],
            RETURN_WISHLIST: [MessageHandler(Filters.text & ~Filters.command, update_db_wishlist)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    dispatcher.add_handler(conv_config_handler)

    dispatcher.add_handler(CommandHandler("start", start_command))
    dispatcher.add_handler(CommandHandler("unlink", unlink_command))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("userinfo", user_info_command))
    dispatcher.add_handler(CommandHandler("support", support_command))
    dispatcher.add_handler(CommandHandler(
        "extendbasic", start_extension_basic_callback))
    dispatcher.add_handler(CommandHandler(
        "extendpremium", start_extension_premium_callback))
    dispatcher.add_handler(PreCheckoutQueryHandler(precheckout_callback))
    dispatcher.add_handler(MessageHandler(
        Filters.successful_payment, successful_payment_callback))
    dispatcher.add_handler(MessageHandler(
        Filters.text & (~Filters.command), unknown_command))

    dispatcher.add_error_handler(error_handler)

    # Start the Bot
    updater.start_polling()
    logger.info("Bot started!")

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    logger = TelegramLogger.logger
    logger.setLevel(10)
    config = reload_config_yml()

    # set test mode to false for server hostname
    is_test = True
    if "pi3" in platform.node():
        is_test = False

    main()
