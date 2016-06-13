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

img_count = 0

def incr_img_count():
    img_count += 1
    return img_count

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


def handle_text(text, update, current_state=None, chat_id=None):
    text = update.message.text.encode('utf-8')
    if text == '/start':
        start(bot, update)
    elif text == '/help':
        help(bot, update)
    elif text == '/filters':
        list_filters(bot, update)
    elif current_state == "input_feeling":
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


def filter_image(bot, update):
    """
    Return images processed using the PIL and matplotlib libraries.

    This function should apply filters similar to Instagram and return images
    """

    # Get the largest of the three images created by Telegram
    chat_id = str(update.message.chat_id)
    file_id = update.message.photo[-1].file_id
    applied_filters = []
    invalid_filters = []

    if not os.path.exists(chat_id):
        os.makedirs(chat_id)

    bot.getFile(file_id).download(chat_id+'/download.jpg')
    img = Image.open(chat_id+'/download.jpg')

    # No filter provided. Use a default filter.
    reply = ', '.join(filters.keys())

    caption = update.message.caption.lower().replace(',', '').split(' ')
    for f in caption:

        # Image.convert can easily turn an image into greyscale
        if 'greyscale' in f:
            img = img.convert('L')
            applied_filters.append(f)

        # Apply a sepia-tone filter
        elif 'sepia' in f:
            img = img.convert('L')
            # make sepia ramp (tweak color as necessary)
            sepia = make_linear_ramp((255, 220, 192))
            # optional: apply contrast enhancement here, e.g.
            img = ImageOps.autocontrast(img)
            # apply sepia palette
            img.putpalette(sepia)
            img = img.convert("RGB")
            applied_filters.append('sepia-tone')

        elif 'invert' in f:
            img = ImageOps.invert(img)
            applied_filters.append('inverted')

        # The specified filter is one of the ImageFilter module ones
        elif f in filters:
            img = img.filter(filters[f])
            applied_filters.append(f)

        # The filter isn't supported
        else:
            invalid_filters.append(f)

    # Notify the user of unsupported filters
    if invalid_filters:
        reply = ('Sorry, we don\'t have the %s filter(s). Filters:\n\n' %
                 ', '.join(invalid_filters) + reply)

        bot.sendMessage(update.message.chat_id, text=reply)

    img.save(chat_id+'/filtered.jpg')
    if applied_filters:
        bot.sendPhoto(update.message.chat_id,
                      photo=open(chat_id+'/filtered.jpg', 'rb'),
                      caption=' '.join(applied_filters))


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


def change_attribute(subject, key, value):
    firebase.patch('/users/' + subject + '/', data={key: value})


# Define a few command handlers. These usually take the two arguments bot and
# update. Error handlers also receive the raised TelegramError object in error.
def start(bot, update):
    """
    Start the party.

    This function gets da partaaaaayyy started
    Only activated when a new conversation is started with this bot
    """
    message = 'Hi! Do you need /help? Check out my /filters!'
    bot.sendMessage(update.message.chat_id, text=message)


def help(bot, update):
    """
    Some helpful text with the /help command.

    This function should just provide an overview of what commands to use
    """
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


def echo(bot, update):
    """
    Repeat any text message as this bot's default behavior.

    This function only serves the purpose of making sure the bot is activated
    """
    bot.sendMessage(update.message.chat_id, text=update.message.text)


@app.route('/')
def index():
    return '.'


# @app.route('/set_webhook', methods=['GET', 'POST'])
def set_webhook():
    s = bot.setWebhook('https://telegram-filter-bot.herokuapp.com/HOOK')
    # s = bot.setWebhook('https://pacific-dusk-98067.herokuapp.com/HOOK')
    if s:
        return "webhook setup ok"
    else:
        return "webhook setup failed"


if __name__ == "__main__":
    set_webhook()
