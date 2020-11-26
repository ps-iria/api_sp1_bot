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

bot = telegram.Bot(token=TELEGRAM_TOKEN)


def parse_homework_status(homework):
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')

    if homework_status not in VERDICTS:
        raise KeyError(f'Статус работы указан неверно, '
                       f'status: {homework_status}.')
    return (f'У вас проверили работу "{homework_name}"!'
            f'\n\n{VERDICTS[homework_status]}')


def get_homework_statuses(current_timestamp):
    headers = {'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'}
    data = {
        "from_date": current_timestamp,
    }
    try:
        response = requests.get(PRAKTIKUM_URL, headers=headers, params=data)
    except requests.exceptions.RequestException as e:
        raise KeyError(f'Бот столкнулся с ошибкой: {e}, '
                       f'по запросу {PRAKTIKUM_URL}, с параметрами: {data}')
    response_json = response.json()
    if 'error' in response_json:
        raise KeyError(f'Бот столкнулся с ошибкой: {response_json["error"]}, '
                       f'по запросу {PRAKTIKUM_URL}, с параметрами: {data}')
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
        except Exception as e:
            logging.error(f'Бот столкнулся с ошибкой: {e}')
            time.sleep(5)


if __name__ == '__main__':
    logging.basicConfig(filename=__file__ + '.log',
                        filemode='w',
                        level=logging.ERROR,
                        format='%(name)s - %(asctime)s - %(message)s'
                        )
    main()
