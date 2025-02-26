import asyncio
import logging
import logging.handlers
import os
import socket

import psutil
import telegram

from settings import (
    DISKS,
    WARNING_AFTER,
    CRITICAL_AFTER,
    TOKEN,
    MY_CHAT_ID,
    LOGFILE_PATH,
    LOG_MAX_SIZE,
    NUMBER_OF_LOG_FILES,
)

if not os.path.exists(LOGFILE_PATH):
    os.makedirs(os.path.dirname(LOGFILE_PATH), exist_ok=True)

logging.basicConfig(
    encoding='utf-8',
    format=(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ),
    level=logging.INFO,
    handlers=[
        logging.handlers.RotatingFileHandler(
            filename=LOGFILE_PATH,
            maxBytes=LOG_MAX_SIZE,
            backupCount=NUMBER_OF_LOG_FILES,
            encoding='utf-8',
        )
    ],
)


async def send_telegram(text: str):
    bot: telegram.Bot = telegram.Bot(token=TOKEN)
    try:
        await bot.send_message(MY_CHAT_ID, text)
        logging.debug(f'Отправлено сообщение "{text}"')
    except telegram.TelegramError as error:
        logging.error(f'Ошибка при отправке сообщения "{text}" '
                      f'в Telegram: {error}')


def disk_info(disks):
    hostname = socket.gethostname()
    for disk in disks:
        try:
            disk_usage = psutil.disk_usage(disk)
            if disk_usage.percent <= WARNING_AFTER:
                message = (
                    f'Процент использования диска"{disk}": '
                    f'{disk_usage.percent}%'
                )
                logging.info(message)
            elif disk_usage.percent <= CRITICAL_AFTER:
                message = (
                    f'Высокий процент использования диска"{disk}": '
                    f'{disk_usage.percent}%!'
                )
                logging.warning(message)
                asyncio.run(send_telegram(f'{hostname} - {message}'))
            else:
                message = (
                    f'Критический процент использования диска"{disk}": '
                    f'{disk_usage.percent}%! Возможен отказ '
                    'программ или системы'
                )
                logging.critical(message)
                asyncio.run(send_telegram(f'{hostname} - {message}'))
        except Exception as e:
            logging.error(
                f'Ошибка при получении информации '
                f'о {disk}: {e}'
            )


def main(disks: list):
    if not disks:
        for partition in psutil.disk_partitions():
            try:
                disks.append(partition.mountpoint)
            except Exception as e:
                logging.error(
                    f'Ошибка при получении информации '
                    f'о {partition.mountpoint}: {e}'
                )
    disk_info(disks)


if __name__ == '__main__':
    main(DISKS)
