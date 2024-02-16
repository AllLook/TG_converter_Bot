import telebot
import requests
from bs4 import BeautifulSoup
import logging
from datetime import datetime

# Установка токена вашего бота от BotFather
TOKEN = ''
bot = telebot.TeleBot(TOKEN)
available_currencies = ["USD", "EUR", "GBP", "JPY", "AUD", "CAD", "CHF", "CNY", "SEK", "NZD"]
# Настройка логгера
logging.basicConfig(filename='bot.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


# Функция для логирования
def log_user_action(priority, command):
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    logging.info(f'{now} - Priority {priority}: User executed command: {command}')


# Функция для получения курса валют из ЦБР
def get_exchange_rate(currency):
    url = f'https://www.cbr.ru/currency_base/daily/?UniDbQuery.Posted=True&UniDbQuery.To={currency}'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    rows = soup.find_all('tr')

    for row in rows:
        columns = row.find_all('td')
        if len(columns) >= 5 and columns[1].text.strip() == currency:
            return float(columns[4].text.replace(',', '.'))


# Обработчик команды /start
@bot.message_handler(commands=['start'])
def handle_start(message):
    bot.send_message(message.chat.id,
                     "Привет! Я бот для конвертации валют. Используй /help для получения списка команд.")
    log_user_action('INFO', '/start')


# Обработчик команды /help
@bot.message_handler(commands=['help'])
def handle_help(message):
    help_text = "/start - Начать взаимодействие с ботом\n/help - Получить список команд\n/convert <сумма> <валюта_from> to <валюта_to> - Конвертировать валюту\n/currencies - наименование валюты для конвертации"
    bot.send_message(message.chat.id, help_text)
    log_user_action('INFO', '/help')


def get_available_currencies():
    return "\n".join(sorted(available_currencies))


@bot.message_handler(commands=['currencies'])
def handle_currencies(message):
    currencies_text = get_available_currencies()
    bot.send_message(message.chat.id, f"Доступные валюты для конвертации:\n{currencies_text}")
    log_user_action('INFO', '/currencies')


# Обработчик команды /convert
# Функция для получения курса валют через API
# Функция для получения курса валют через API
def get_exchange_rate_api(currency_from, currency_to):
    base_url = 'https://api.exchangerate-api.com/v4/latest/USD'

    try:
        response = requests.get(base_url)
        data = response.json()

        if 'rates' in data:
            rate_from = data['rates'].get(currency_from)
            rate_to = data['rates'].get(currency_to)

            if rate_from is not None and rate_to is not None:
                return rate_to / rate_from
    except requests.RequestException as e:
        print(f"Error fetching exchange rates: {e}")

    return None


# Обработчик команды /convert
@bot.message_handler(commands=['convert'])
def handle_convert(message):
    try:
        _, amount, currency_from, _, currency_to = message.text.split()
        amount = float(amount)

        if currency_from.upper() not in available_currencies or currency_to.upper() not in available_currencies:
            bot.send_message(message.chat.id,
                             "Одна из валют не поддерживается. Пожалуйста, используйте /currencies для списка поддерживаемых валют.")
            return

        rate = get_exchange_rate_api(currency_from.upper(), currency_to.upper())

        if rate is None:
            bot.send_message(message.chat.id, "Не удалось получить курс валют. Пожалуйста, попробуйте позже.")
            return

        result = amount * rate
        bot.send_message(message.chat.id, f"{amount} {currency_from} = {result:.2f} {currency_to}")
        log_user_action('INFO', f'/convert {amount} {currency_from} to {currency_to}')
    except ValueError:
        bot.send_message(message.chat.id,
                         "Некорректный формат команды. Используйте /convert <сумма> <валюта_from> to <валюта_to>")
        log_user_action('ERROR', '/convert - Invalid format')


# Обработчик текстовых сообщений
@bot.message_handler(func=lambda message: True)
def handle_text(message):
    text = message.text.lower()
    if 'привет' and 'здравствуйте' and 'здорово' and 'hello' and 'hi' in text:
        bot.send_message(message.chat.id, "Привет! Как я могу помочь?")
        log_user_action('INFO', 'Greetings')
    elif 'пока' and 'до свидания' and 'досвидания' and 'goodbye' and 'good bye' and 'bye' in text:
        bot.send_message(message.chat.id, "До свидания! Если у вас есть еще вопросы, используйте /help.")
        log_user_action('INFO', 'Goodbye')



# Запуск бота
bot.polling(none_stop=True)
