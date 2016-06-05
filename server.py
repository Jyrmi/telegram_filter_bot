#!/usr/bin/env python

import telegram
from flask import Flask, request
import os
from PIL import Image, ImageFilter, ImageOps
import logging
import sendgrid
from firebase import firebase

# Firebase is used to track user state and information
firebase_db = os.environ['FIREBASE_DB']
firebase = firebase.FirebaseApplication(firebase_db, None)

app = Flask(__name__)

global bot
bot = telegram.Bot(token=os.environ['TELEGRAM_KEY'])


@app.route('/HOOK', methods=['POST'])
def webhook_handler():
    if request.method == "POST":
        # retrieve the message in JSON and then transform it to Telegram object
        update = telegram.Update.de_json(request.get_json(force=True))

        chat_id = update.message.chat.id

        # Telegram understands UTF-8, so encode text for unicode compatibility
        text = update.message.text.encode('utf-8')
        try:
            change_attribute("test_subject", "test_key", text)
        except Exception as e:
            print "firebase patch failed"
            print str(e)
        # repeat the same message back (echo)
        bot.sendMessage(chat_id=chat_id, text=text)

    return 'ok'


# @app.route('/set_webhook', methods=['GET', 'POST'])
def set_webhook():
    s = bot.setWebhook('https://telegram-filter-bot.herokuapp.com/HOOK')
    if s:
        return "webhook setup ok"
    else:
        return "webhook setup failed"


def change_attribute(subject, key, value):
    firebase.patch('/users/' + subject + '/', data={key: value})


@app.route('/')
def index():
    return '.'

if __name__ == "__main__":
    set_webhook()
