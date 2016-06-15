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

sg = sendgrid.SendGridClient(os.environ['SENDGRID_KEY'])

app = Flask(__name__)

global bot
bot = telegram.Bot(token=os.environ['TELEGRAM_KEY'])

# Define the different states a chat can be in
MENU, AWAIT_FILTER_INPUT, AWAIT_FILTER_CONFIRMATION = range(3)
AWAIT_EMAIL_INPUT, AWAIT_EMAIL_CONFIRMATION = range(3, 5)

# Define the filter names here
FILTER_1, FILTER_2, FILTER_3 = ("FILTER_1", "FILTER_2", "FILTER_3")
YES, NO = ("YES", "NO")


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
        firebase_dict = firebase_get(chat_id None)
        for k, v in firebase_dict.iteritems():
            if k == "state":
                current_state = v
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
            change_attribute(str(chat_id), "chat_id", str(chat_id))
            # change_attribute(str(chat_id), "state", "input_feeling")
            change_attribute(str(chat_id), "state", "MENU")
            filter_image(bot, update)
            # full_message = "How are you feeling today?"
            # bot.sendMessage(update.message.chat_id, text=full_message)

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
    elif text == 'cancel':
        cancel(bot, update)
    elif text == '/email':
        # echo(bot, update)
        get_email(bot, update)


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


def cancel(bot, update):
    """
    Cancel out this user's state, whatever the current operation.

    This function will clear out the state and context key-value pairs for this
    user
    """
    chat_id = update.message.chat_id
    # del state[chat_id]
    # del context[chat_id]
    change_attribute(str(chat_id), "state", "-1")
    change_attribute(str(chat_id), "context", "-1")


def set_value(bot, update):
    chat_id = update.message.chat_id
    user_id = update.message.from_user.id
    text = update.message.text
    # chat_state = state.get(chat_id, MENU)
    chat_state = firebase_get(chat_id, 'state')

    # chat_context = context.get(chat_id, None)
    chat_context = chat_context = firebase_get(chat_id, 'context')

    # Since the handler will also be called on messages, we need to check if
    # the message is actually a command
    if chat_state == MENU and 'test' in text:
        # state[chat_id] = AWAIT_FILTER_INPUT # set the state
        change_attribute(str(chat_id), "state", AWAIT_FILTER_INPUT)

        # context[chat_id] = user_id  # save the user id to context
        change_attribute(str(chat_id), "context", str(chat_id))
        bot.sendMessage(chat_id,
                        text="Hi there, what filter(s) would you like to apply?\n"
                        "type /cancel to end this conversation",
                        reply_markup=ForceReply())
    # If we are waiting for input and the right user answered
    # MENU, AWAIT_FILTER_INPUT, AWAIT_FILTER_CONFIRMATION
    elif chat_state == AWAIT_FILTER_INPUT and chat_context == user_id:
        # state[chat_id] = AWAIT_FILTER_CONFIRMATION
        change_attribute(str(chat_id), "state", AWAIT_FILTER_CONFIRMATION)
        # Save the user id and the answer to context
        # context[chat_id] = (user_id, update.message.text)
        change_attribute(str(chat_id), "context", {str(chat_id): update.message.text})
        reply_markup = ReplyKeyboardMarkup(
            [[KeyboardButton(FILTER_1), KeyboardButton(FILTER_2), KeyboardButton(FILTER_3)]],
            one_time_keyboard=True)
        bot.sendMessage(chat_id,
                        text="Okay, just to confirm, you would like the following filters: " + text + ", is that correct?",
                        reply_markup=reply_markup)
    # If we are waiting for confirmation and the right user answered
    elif chat_state == AWAIT_FILTER_CONFIRMATION and chat_context[0] == user_id:
        # del state[chat_id]
        # del context[chat_id]
        cancel(bot, update)
        change_attribute(str(chat_id), "value", chat_context[1])

        if text == FILTER_1:
            # values[chat_id] = chat_context[1]
            bot.sendMessage(chat_id, text="FILTER_1 has been selected.")
        elif text == FILTER_2:
            # values[chat_id] = chat_context[1]
            bot.sendMessage(chat_id, text="FILTER_2 has been selected.")
        elif text == FILTER_3:
            # values[chat_id] = chat_context[1]
            bot.sendMessage(chat_id, text="FILTER_3 has been selected.")


def use_sendgrid(bot, update, email_address):
    chat_id = str(update.message.chat_id)
    html_message = '<b>Enjoy!</b>'
    message = sendgrid.Mail()
    message.add_to(email_address)
    message.set_subject('your filtered photos')
    message.set_html(html_message)
    # message.set_text('Body')
    message.set_from('telegram_filter_bot')
    message.add_attachment('filtered.jpg', open(chat_id+'/filtered.jpg', 'rb'))
    # message.add_attachment('filtered.jpg', open(chat_id+'/filtered.jpg', 'rb'))
    # message.add_attachment('sepia.jpg', open(chat_id+'/sepia.jpg', 'rb'))
    # message.add_attachment('inverted.jpg', open(chat_id+'/inverted.jpg', 'rb'))
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


def get_email(bot, update):
    chat_id = update.message.chat_id
    user_id = update.message.from_user.id
    text = update.message.text
    # chat_state = state.get(chat_id, MENU)
    chat_state = firebase_get(chat_id, 'state')

    # chat_context = context.get(chat_id, None)
    chat_context = firebase_get(chat_id, 'context')

    # Since the handler will also be called on messages, we need to check if
    # the message is actually a command
    if chat_state == MENU:
        # state[chat_id] = AWAIT_EMAIL_INPUT # set the state
        change_attribute(str(chat_id), "state", AWAIT_EMAIL_INPUT)

        # context[chat_id] = user_id  # save the user id to context
        change_attribute(str(chat_id), "context", str(chat_id))
        bot.sendMessage(chat_id,
                        text="Hi there, please input your email!\n"
                        "type /cancel to end this conversation",
                        reply_markup=ForceReply())
    # If we are waiting for input and the right user answered
    # MENU, AWAIT_FILTER_INPUT, AWAIT_FILTER_CONFIRMATION
    elif chat_state == AWAIT_EMAIL_INPUT and chat_context == user_id:
        # state[chat_id] = AWAIT_EMAIL_CONFIRMATION
        change_attribute(str(chat_id), "state", AWAIT_EMAIL_CONFIRMATION)
        # Save the user id and the answer to context
        # context[chat_id] = (user_id, update.message.text)
        change_attribute(str(chat_id), "context", {str(chat_id): update.message.text})
        reply_markup = ReplyKeyboardMarkup(
            [[KeyboardButton(YES), KeyboardButton(NO)]],
            one_time_keyboard=True)
        bot.sendMessage(chat_id,
                        text="Okay, just to confirm, I'm sending your photos to: " + text + ", is that correct?",
                        reply_markup=reply_markup)
    # If we are waiting for confirmation and the right user answered
    elif chat_state == AWAIT_EMAIL_CONFIRMATION and chat_context[0] == user_id:
        # del state[chat_id]
        # del context[chat_id]
        cancel(bot, update)
        change_attribute(str(chat_id), "value", chat_context[1])
        value = firebase_get(chat_id, 'value')

        if text == YES:
            # values[chat_id] = chat_context[1]
            # use_sendgrid(bot, update, values[chat_id])
            if value:
                use_sendgrid(bot, update, value)
                bot.sendMessage(chat_id, text="An email has been sent to " + value)
        else:
            # values[chat_id] = chat_context[1]
            bot.sendMessage(chat_id, text="Okay, no email was sent.")


def change_attribute(subject, key, value):
    try:
        firebase.patch('/users/' + subject + '/', data={key: value})
    except Exception as e:
        print str(e)


def firebase_get(chat_id, value):
    try:
        return firebase.get('/users/' + str(chat_id) + '/' + value, None)
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
