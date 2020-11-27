import logging
import os
import time

import requests
import telegram
from dotenv import load_dotenv

load_dotenv()

PRAKTIKUM_URL = 'https://praktikum.yandex.ru/api/user_api/homework_statuses/'
PRAKTIKUM_TOKEN = os.getenv("PRAKTIKUM_TOKEN")
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

VERDICTS = {
    'rejected': 'К сожалению в работе нашлись ошибки.',
    'approved': 'Ревьюеру всё понравилось, '
                'можно приступать к следующему уроку.'
}
STATUS_SUCCESS = 'У вас проверили работу "{homework_name}"!''\n\n{verdict}'
STATUS_ERROR = 'Статус работы указан неверно, status: {homework_status}.'
BOT_RESPONSE_ERROR = '{error}, по запросу {url}, с параметрами: {data}'
BOT_ERROR = 'Бот столкнулся с ошибкой: {error}'

bot = telegram.Bot(token=TELEGRAM_TOKEN)


def parse_homework_status(homework):
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    if homework_status not in VERDICTS:
        raise ValueError(STATUS_ERROR.format(
            homework_status=homework_status
        ))
    return STATUS_SUCCESS.format(
        homework_name=homework_name,
        verdict=VERDICTS[homework_status]
    )


def get_homework_statuses(current_timestamp):
    headers = {'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'}
    data = {
        "from_date": current_timestamp,
    }
    try:
        response = requests.get(PRAKTIKUM_URL, headers=headers, params=data)
    except requests.exceptions.RequestException as error:
        raise ConnectionError(BOT_RESPONSE_ERROR.format(
            error=error,
            url=PRAKTIKUM_URL,
            data=data)) from error
    response_json = response.json()
    if 'error' in response_json:
        raise ValueError(BOT_RESPONSE_ERROR.format(
            error=response_json["error"],
            url=PRAKTIKUM_URL,
            data=data))
    return response_json


def send_message(message, bot_client):
    return bot_client.send_message(chat_id=CHAT_ID, text=message)


def main():
    current_timestamp = int(time.time())
    while True:
        try:
            new_homework = get_homework_statuses(current_timestamp)
            if new_homework.get('homeworks'):
                send_message(
                    parse_homework_status(new_homework.get('homeworks')[0]),
                    bot
                )
            current_timestamp = new_homework.get('current_date',
                                                 current_timestamp)
            time.sleep(600)  # 10 минут
        except Exception as error:
            logging.error(BOT_ERROR.format(error=error))
            time.sleep(5)


if __name__ == '__main__':
    logging.basicConfig(filename=__file__ + '.log',
                        filemode='w',
                        level=logging.ERROR,
                        format='%(name)s - %(asctime)s - %(message)s'
                        )
    main()