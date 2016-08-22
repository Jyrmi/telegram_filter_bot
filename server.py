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
import requests
import json

from flask.ext.sqlalchemy import SQLAlchemy

# Firebase is used to track user state and information
firebase_db = os.environ['FIREBASE_DB']
firebase = firebase.FirebaseApplication(firebase_db, None)

sg = sendgrid.SendGridClient(os.environ['SENDGRID_KEY'])

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
db = SQLAlchemy(app)
global bot
bot = telegram.Bot(token=os.environ['TELEGRAM_KEY'])

# # Define the different states a chat can be in
# MENU, AWAIT_FILTER_INPUT, AWAIT_FILTER_CONFIRMATION = range(3)
# AWAIT_EMAIL_INPUT, AWAIT_EMAIL_CONFIRMATION = range(3, 5)

# # Define the filter names here
# FILTER_1, FILTER_2, FILTER_3 = ("FILTER_1", "FILTER_2", "FILTER_3")
# YES, NO = ("YES", "NO")


class user(db.Model):
    """
    This is a simple User model.

    For now, it will just hold the current user state
    """
    id = db.Column(db.Integer, primary_key=True)
    identifier = db.Column(db.String(80), unique=True)
    state = db.Column(db.String(80))

    def __init__(self, chat_id, state):
        self.identifier = chat_id
        self.state = state

    def __repr__(self):
        return '<ChatId: %r>' % self.identifier


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


def exists(chat_id):
    try:
        return db.session.query(db.exists().where(user.identifier == chat_id)).scalar()
    except Exception as e:
        print(e)
        return False


def check_or_create_db_entry(chat_id):
    try:
        if not exists(chat_id):
            user = user(chat_id, 'expect_filter')
            db.session.add(user)
            db.session.commit()
        else:
            user = user.query.filter_by(identifier=chat_id).first()
            user.state = 'expect_filter'
            db.session.commit()
    except Exception as e:
        print(e)


def handle_text(text, update, current_state=None, chat_id=None):
    text = update.message.text.encode('utf-8')

    if text == '/start':
        start(bot, update)
    elif text == '/help':
        help(bot, update)
    elif text == '/filters':
        list_filters(bot, update)
    # elif text == 'cancel':
    #     cancel(bot, update)
    elif text.startswith('/set_email'):
        # get_email(bot, update)
        set_email(update, text[7:])
    elif text == '/email':
        use_sendgrid(bot, update)
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

    try:
        files = {'file': open(chat_id+'/download.jpg', 'rb')}
        new_tags = create_tags(files)
        bot.sendMessage(update.message.chat_id, text=new_tags)
    except Exception as e:
        print(e)

    img = Image.open(chat_id+'/download.jpg')

    # No filter provided. Use a default filter.
    reply = ', '.join(filters.keys())
    caption = update.message.text.encode('utf-8').lower().replace(',', '').split(' ')

    for f in caption:
        print("made it into the caption loop")
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

        # elif 'circle' in f:
        #     mask = Image.open('./mask_1.png').convert('L')
        #     img = ImageOps.fit(img, mask.size, centering=(0.5, 0.5))
        #     img.putalpha(mask)
        #     # applied_filters.append('circle')
        #     print('before save okay')
        #     img.save(chat_id+'/filtered.png')
        #     print('after save okay')
        #     bot.sendDocument(update.message.chat_id,
        #                      document=open(chat_id+'/filtered.png', 'rb'))
        #     print('after send okay')
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
                 ', '.join(invalid_filters) + str(reply))

        bot.sendMessage(update.message.chat_id, text=reply)

    # save image to be sent as payload
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


def set_email(update, address):
    chat_id = str(update.message.chat_id)
    change_attribute(str(chat_id), 'email_address', address)


def use_sendgrid(bot, update):
    chat_id = str(update.message.chat_id)
    email_address = firebase_get(chat_id, 'email_address')

    html_message = '<b>Enjoy!</b>'
    message = sendgrid.Mail()
    message.add_to(email_address)
    message.set_subject('your filtered photos')
    message.set_html(html_message)
    # message.set_text('Body')
    message.set_from('telegram_filter_bot')
    message.add_attachment('filtered.jpg', open(chat_id+'/filtered.jpg', 'rb'))
    status, msg = sg.send(message)
    print(status, msg)
    if status == 200:
        success_msg = "<b>Your photos have been emailed successfully!</b>\n"
        bot.sendMessage(update.message.chat_id,
                        text=success_msg,
                        parse_mode="HTML")
    else:
        fail_msg = "<b>There was a problem emailing your photos...</b>\n"
        bot.sendMessage(update.message.chat_id,
                        text=fail_msg,
                        parse_mode="HTML")


def change_attribute(subject, key, value):
    try:
        firebase.patch('/users/' + str(subject), data={key: value})
    except Exception as e:
        print str(e)


def firebase_get(chat_id, value):
    try:
        return firebase.get('/users/' + str(chat_id) + '/' + str(value), None)
    except Exception as e:
        print str(e)


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


def create_tags(files):
    """
    Repeat any text message as this bot's default behavior.

    This function only serves the purpose of making sure the bot is activated
    """
    url = "https://api.projectoxford.ai/vision/v1.0/describe?maxCandidates=1"
    headers = {
        "Ocp-Apim-Subscription-Key": os.environ['MICROSOFT_KEY']
        }
    r = requests.post(url, stream=False, headers=headers, files=files)
    print(r.text)
    json_response = json.loads(r.text)
    print(json_response)
    print(json_response['description']['tags'])
    return json_response['description']['tags']


@app.route('/activate_webhook', methods=['POST'])
def webhook_handler():
    print('hello world')
    if request.method == "POST":
        print('in request.method == post')
        # retrieve the message in JSON and then transform it to Telegram object
        update = telegram.Update.de_json(request.get_json(force=True))
        chat_id = update.message.chat.id

        # Telegram understands UTF-8, so encode text for unicode compatibility
        text = update.message.text.encode('utf-8')
        photo = update.message.photo

        if text and exists(chat_id):
            print("made it into the text function")
            filter_image(bot, update)
        elif photo:
            check_or_create_db_entry(chat_id)
    return 'ok'


@app.route('/set_webhook', methods=['GET', 'POST'])
def set_webhook():
    s = bot.setWebhook('https://stormy-river-76696.herokuapp.com/activate_webhook')
    if s:
        return "webhook setup ok"
    else:
        return "webhook setup failed"


@app.route('/')
def index():
    return 'running'
