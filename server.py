#!/usr/bin/env python

import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import ForceReply, ReplyKeyboardMarkup, KeyboardButton
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

filters = {
    'blur': ImageFilter.BLUR,
    'contour': ImageFilter.CONTOUR,
    'detail': ImageFilter.DETAIL,
    'edge_enhance': ImageFilter.EDGE_ENHANCE,
    'edge_enhance_more': ImageFilter.EDGE_ENHANCE_MORE,
    'emboss': ImageFilter.EMBOSS,
    'find_edges': ImageFilter.FIND_EDGES,
    'smooth': ImageFilter.SMOOTH,
    'smooth_more': ImageFilter.SMOOTH_MORE
}


@app.route('/HOOK', methods=['POST'])
def webhook_handler():
    if request.method == "POST":
        # retrieve the message in JSON and then transform it to Telegram object
        update = telegram.Update.de_json(request.get_json(force=True))

        chat_id = update.message.chat.id

        print update.message

        # Telegram understands UTF-8, so encode text for unicode compatibility
        text = update.message.text.encode('utf-8')

        text_array = text.split()

        handle_command(text_array[0], update)

        try:
            change_attribute("test_subject", "test_key", text)
        except Exception as e:
            print "firebase patch failed"
            print str(e)
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


def handle_command(command, update):
    if command == "/help":
        help(bot, update)
    elif command == "/list_filters":
        list_filters(bot, update)
    else:
        echo(bot, update)


def echo(bot, update):
    """
    Repeat any text message as this bot's default behavior.

    This function only serves the purpose of making sure the bot is activated
    """
    bot.sendMessage(update.message.chat_id, text=update.message.text)


def help(bot, update):
    """
    Some helpful text with the /help command.

    This function should just provide an overview of what commands to use
    """
    print "attempting to execute help function"
    message = (
        "Simply upload a photo (as a photo, not a file) to get started.\n"
        "Provide the filters you want to use in the caption of your image.\n"
        "You can string filters together and they will be applied in order,\n"
        "e.g. \"detail smooth blur greyscale\"\n"
        "Here are the filters we have:\n\n" + ', '.join(filters.keys()))

    bot.sendMessage(update.message.chat_id, message)


def list_filters(bot, update):
    """
    Show all available filters.

    This function will simply show the user all the filters he/she can choose
    """
    bot.sendMessage(update.message.chat_id, text=', '.join(filters.keys()))


def make_linear_ramp(white):
    """
    Create a general color mask, used for the sepia filter for example.

    This function will simply return a color mask to be used on any filter
    """
    # putpalette expects [r,g,b,r,g,b,...]
    ramp = []
    r, g, b = white
    for i in range(255):
        ramp.extend((r*i/255, g*i/255, b*i/255))
    return ramp


@app.route('/')
def index():
    return '.'

if __name__ == "__main__":
    set_webhook()
