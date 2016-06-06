#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Simple Bot to reply to Telegram messages and especially photos, when it
# replies to photos, it should return a filtered version of the photo
# according to the the filters you have selected

"""
This Bot uses simple conditional responses to webhook messages.

Using a simple chain of if/else statements, we have built basic logic into
the bot to handle different commands. This bot runs on a flask server so
unless Heroku dies, it shall not.
"""

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

        current_state = None
        try:
            firebase_dict = firebase.get('/users/' + str(chat_id), None)
            for k, v in firebase_dict.iteritems():
                if k == "state":
                    current_state = v
            print "THIS IS THE CURRENT STATE"
            print current_state
        except Exception as e:
            print "FAILURE TO ASSIGN STATE"
            print current_state
            print str(e)
        print update.message
        print update.message.text.encode('utf-8')
        print update.message.photo
        print "-----------------"
        print "-----------------"
        print "-----------------"
        print "-----------------"
        print "-----------------"

        # Telegram understands UTF-8, so encode text for unicode compatibility
        text = update.message.text.encode('utf-8')
        photo = update.message.photo

        if text:
            # text_array = text.split()
            print chat_id
            print text
            handle_text(text, update, current_state, chat_id)
            # handle_command(text_array[0], update)
        elif photo:
            try:
                change_attribute(str(chat_id), "chat_id", str(chat_id))
                change_attribute(str(chat_id), "state", "input_feeling")
            except Exception as e:
                print str(e)
            filter_image(bot, update)
            full_message = "How are you feeling today?"
            bot.sendMessage(update.message.chat_id, text=full_message)

        # try:
        #     change_attribute("test_subject", "test_key", text)
        # except Exception as e:
        #     print "firebase patch failed"
        #     print str(e)
    return 'ok'


# @app.route('/set_webhook', methods=['GET', 'POST'])
def set_webhook():
    s = bot.setWebhook('https://pacific-dusk-98067.herokuapp.com/HOOK')
    if s:
        return "webhook setup ok"
    else:
        return "webhook setup failed"


def change_attribute(subject, key, value):
    firebase.patch('/users/' + subject + '/', data={key: value})


def handle_text(text, update, current_state=None, chat_id=None):
    if current_state == "input_feeling":
        change_attribute(str(chat_id), "state", "input_weight")
        change_attribute(str(chat_id), "feeling", text)
        full_message = "What's your weight today?"
        bot.sendMessage(update.message.chat_id, text=full_message)
    elif current_state == "input_weight":
        change_attribute(str(chat_id), "state", "input_memo")
        change_attribute(str(chat_id), "weight", text)
        full_message = "Leave some comments on your photo!"
        bot.sendMessage(update.message.chat_id, text=full_message)
    elif current_state == "input_memo":
        change_attribute(str(chat_id), "state", "input_tags")
        change_attribute(str(chat_id), "memo", text)
        full_message = "Leave some tags on this photo!"
        bot.sendMessage(update.message.chat_id, text=full_message)
    elif current_state == "input_tags":
        change_attribute(str(chat_id), "state", "complete")
        change_attribute(str(chat_id), "tags", text.split())
        full_message = "Great! Here is a link with all your photos."
        bot.sendMessage(update.message.chat_id, text=full_message)
    elif current_state == "/list_filters":
        list_filters(bot, update)
    else:
        echo(bot, update)


def handle_command(command, update):
    if command == "/help":
        help(bot, update)
    elif command == "/list_filters":
        list_filters(bot, update)
    else:
        echo(bot, update)


def filter_image(bot, update):
    """
    Return images processed using the PIL and matplotlib libraries.

    This function should apply filters similar to Instagram and return images
    """
    chat_id = str(update.message.chat_id)
    file_id = update.message.photo[-1].file_id
    change_attribute(str(chat_id), "file_id", file_id)
    if not os.path.exists(chat_id):
        os.makedirs(chat_id)
    bot.getFile(file_id).download(chat_id+'/download.jpg')

    bot.sendPhoto(update.message.chat_id,
                  photo=open(chat_id+'/download.jpg', 'rb'),
                  caption=('...and, here\'s your image inverted.'))
    return


def echo(bot, update):
    """
    Repeat any text message as this bot's default behavior.

    This function only serves the purpose of making sure the bot is activated
    """
    bot.sendMessage(update.message.chat_id, text=update.message.text)


@app.route('/')
def index():
    return '.'

if __name__ == "__main__":
    set_webhook()
