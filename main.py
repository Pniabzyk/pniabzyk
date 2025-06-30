import hashlib
import json
import requests
import time
from flask import Flask, request
import telegram
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
import os

app = Flask(__name__)

# Конфігурація
TELEGRAM_TOKEN = '7971113554:AAEHlyaoqnKDT7pLSCKjpKi4pYDfrwy7S7E'
WFP_MERCHANT = 'forms_gle7'
WFP_SECRET = '7921e3bad21153d0e467066b5285511d390a16d4'
WFP_URL = 'https://secure.wayforpay.com/pay'
BOT = telegram.Bot(token=TELEGRAM_TOKEN)

# Випуски й посилання
DROPBOX_LINKS = {
    'issue1': 'https://www.dropbox.com/scl/fi/qm5hiudd87tpyljw89v83/1-27.01.pdf?rlkey=ij38rwju1owjrhm9ngnbe4em6&st=iw7rfoua&dl=0',
    'issue2': 'https://www.dropbox.com/scl/fi/nq957bo5ukp7axg1e9y5q/2-28.02.pdf?rlkey=1hfnpx1dqje36j3b66hjpfppc&st=vos3iv46&dl=0',
    'issue3': 'https://www.dropbox.com/scl/fi/hpg0gf9lh207hiw1uw50x/3-09.04.pdf?rlkey=d6s3iiup02aye3xul8898lg3c&st=ute9v9tz&dl=0'
}

# Генерація підпису для Wayforpay
def generate_signature(data, secret):
    keys = ['merchantAccount','orderReference','orderDate','amount','currency','productName','productCount','productPrice']
    signature_str = ';'.join(str(data[k]) for k in keys)
    return hashlib.sha1((signature_str + secret).encode('utf-8')).hexdigest()

# Статичні кнопки Wayforpay для випусків
WFP_BUTTON_LINKS = {
    'issue1': 'https://secure.wayforpay.com/button/b56513f8db1e1',
    'issue2': 'https://secure.wayforpay.com/button/bbed55197b5f4',
    'issue3': 'https://secure.wayforpay.com/button/b91af44205f4f'
}

# Відправка кнопки оплати
def send_payment_button(chat_id, issue_number):
    link = WFP_BUTTON_LINKS[f'issue{issue_number}']
    BOT.send_message(
        chat_id,
        f"Оплатіть випуск №{issue_number}:",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton(f"💳 Оплатити 50 грн — №{issue_number}", url=link)
        ]])
    )

# Telegram webhook
@app.route('/telegram', methods=['POST'])
def telegram_webhook():
    update = telegram.Update.de_json(request.get_json(force=True), BOT)
    if not update.message or not update.message.text:
        return 'ok'
    chat_id = update.message.chat_id
    text = update.message.text

    if text == '/start':
        BOT.send_message(
            chat_id,
            'Привіт! Оберіть випуск, який хочете купити:',
            reply_markup=telegram.ReplyKeyboardMarkup(
                [['📘 Пнябзик №1','📘 Пнябзик №2','📘 Пнябзик №3']],
                one_time_keyboard=True
            )
        )
    elif text == '📘 Пнябзик №1':
        send_payment_button(chat_id, 1)
    elif text == '📘 Пнябзик №2':
        send_payment_button(chat_id, 2)
    elif text == '📘 Пнябзик №3':
        send_payment_button(chat_id, 3)

    return 'ok' 
def send_payment_button(chat_id, issue_number, link):
    BOT.send_message(
        chat_id,
        f"Оплатіть випуск №{issue_number}:",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton(f"💳 Оплатити 50 грн — №{issue_number}", url=link)
        ]])
    )

# Telegram webhook
@app.route('/telegram', methods=['POST'])
def telegram_webhook():
    update = telegram.Update.de_json(request.get_json(force=True), BOT)
    if not update.message or not update.message.text:
        return 'ok'
    chat_id = update.message.chat_id
    text = update.message.text

    if text == '/start':
        BOT.send_message(
            chat_id,
            'Привіт! Оберіть випуск, який хочете купити:',
            reply_markup=telegram.ReplyKeyboardMarkup(
                [['📘 Пнябзик №1','📘 Пнябзик №2','📘 Пнябзик №3']],
                one_time_keyboard=True
            )
        )
    elif text == '📘 Пнябзик №1':
        link = create_invoice(chat_id, 'issue1')
        send_payment_button(chat_id, 1, link)
    elif text == '📘 Пнябзик №2':
        link = create_invoice(chat_id, 'issue2')
        send_payment_button(chat_id, 2, link)
    elif text == '📘 Пнябзик №3':
        link = create_invoice(chat_id, 'issue3')
        send_payment_button(chat_id, 3, link)

    return 'ok'

# Wayforpay webhook
@app.route('/webhook', methods=['POST'])
def wfp_webhook():
    data = request.get_json()
    if data.get('transactionStatus') == 'Approved':
        ref = data.get('orderReference')
        parts = ref.split('_')
        if len(parts) == 3 and parts[0] == 'pnzbz':
            issue = parts[1]
            chat_id = int(parts[2])
            link = DROPBOX_LINKS.get(issue)
            if link:
                BOT.send_message(chat_id, f"Дякуємо за оплату! Ось ваше посилання:\n{link}")
    return 'OK'

# Запуск сервера
@app.route('/', methods=['GET'])
def index():
    return 'PniabzykBot is running.'

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
