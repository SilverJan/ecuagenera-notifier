import logging
import sys
from datetime import datetime
from logging import FileHandler

logFormatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')


class Logger:
    logger = logging.getLogger("ecuagenera-logger")
    logger.setLevel(logging.INFO)

    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(logFormatter)
    logger.addHandler(ch)

    fh = FileHandler(
        f"/var/log/ecuagenera-bot/ecuagenera_bot_{datetime.today().strftime('%Y-%m-%d_%H-%M')}.log")
    fh.setFormatter(logFormatter)
    logger.addHandler(fh)


class TelegramLogger:
    logger = logging.getLogger("ecuagenera-telegram-logger")
    logger.setLevel(logging.DEBUG)

    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(logFormatter)
    logger.addHandler(ch)

    fh = FileHandler(
        "/var/log/ecuagenera-bot/telegram_bot.log")
    fh.setFormatter(logFormatter)
    logger.addHandler(fh)
