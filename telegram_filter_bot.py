#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Simple Bot to reply to Telegram messages
# This program is dedicated to the public domain under the CC0 license.

"""
This Bot uses the Updater class to handle the bot.

First, a few handler functions are defined. Then, those functions are passed to
the Dispatcher and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.
Usage:
Basic Echobot example, repeats messages.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""

import os
import logging
import sendgrid
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import ForceReply, ReplyKeyboardMarkup, KeyboardButton
from PIL import Image
from PIL import ImageFilter
from PIL import ImageOps
# import thread
# from flask import Flask

# is_prod = os.environ.get('IS_HEROKU', None)

# app = Flask(__name__)

# sg = sendgrid.SendGridClient(os.environ['SENDGRID_KEY'])
sg = sendgrid.SendGridClient('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')

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

# Define the different states a chat can be in
MENU, AWAIT_FILTER_INPUT, AWAIT_FILTER_CONFIRMATION = range(3)
AWAIT_EMAIL_INPUT, AWAIT_EMAIL_CONFIRMATION = range(3, 5)

# Define the filter names here
FILTER_1, FILTER_2, FILTER_3 = ("FILTER_1", "FILTER_2", "FILTER_3")
YES, NO = ("YES", "NO")

state = dict() # States are saved in a dict that maps chat_id -> state
context = dict() # Sometimes you need to save data temporarily
# This dict is used to store the settings value for the chat.
# Usually, you'd use persistence for this (e.g. sqlite).
values = dict()

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

# Enable logging
logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO)

logger = logging.getLogger(__name__)

# @app.route('/')
# def hello_world():
#     return 'Hello World!'

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


def echo(bot, update):
    """
    Repeat any text message as this bot's default behavior.

    This function only serves the purpose of making sure the bot is activated
    """
    bot.sendMessage(update.message.chat_id, text=update.message.text)


def error(bot, update, error):
    """
    Yield any error to the console.

    Pretty self-explanatory, just check the console for error reports
    """
    logger.warn('Update "%s" caused error "%s"' % (update, error))


def filter_image(bot, update):
    """
    Return images processed using the PIL and matplotlib libraries.

    This function should apply filters similar to Instagram and return images
    """
    # bot.sendMessage(update.message.chat_id, text='upload successful')
    # img = Image.open('download.jpg').convert('L')

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
    if not update.message.caption:
        msg_part_1 = 'Please provide the name of the filter you would like to '
        msg_part_2 = 'use in the image\'s caption. Filters:\n\n'
        reply = msg_part_1 + msg_part_2 + reply

        # Notify the user of invalid input
        bot.sendMessage(update.message.chat_id, text=reply)

        # Send sample filtered images in this scenario
        img_greyscale = img.convert('L')
        img_greyscale.save(chat_id+'/filtered.jpg')
        bot.sendPhoto(update.message.chat_id,
                      photo=open(chat_id+'/filtered.jpg', 'rb'),
                      caption=('Meanwhile, here\'s your image in greyscale.'))

        # make sepia ramp (tweak color as necessary)
        sepia = make_linear_ramp((255, 220, 192))
        # optional: apply contrast enhancement here, e.g.
        img_sepia = ImageOps.autocontrast(img_greyscale)
        # apply sepia palette
        img_sepia.putpalette(sepia)
        # convert back to RGB so we can save it as JPEG
        # (alternatively, save it in PNG or similar)
        img_sepia = img_sepia.convert('RGB')
        img_sepia.save(chat_id+'/sepia.jpg')
        bot.sendPhoto(update.message.chat_id,
                      photo=open(chat_id+'/sepia.jpg', 'rb'),
                      caption=('...and, here\'s your image in sepia.'))

        img_inv = ImageOps.invert(img)
        img_inv.save(chat_id+'/inverted.jpg')
        bot.sendPhoto(update.message.chat_id,
                      photo=open(chat_id+'/inverted.jpg', 'rb'),
                      caption=('...and, here\'s your image inverted.'))

        return

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

def cancel(bot, update):
    """
    Cancel out this user's state, whatever the current operation.

    This function will clear out the state and context key-value pairs for this
    user
    """
    chat_id = update.message.chat_id
    del state[chat_id]
    del context[chat_id]

def set_value(bot, update):
    chat_id = update.message.chat_id
    user_id = update.message.from_user.id
    text = update.message.text
    chat_state = state.get(chat_id, MENU)
    chat_context = context.get(chat_id, None)

    # Since the handler will also be called on messages, we need to check if
    # the message is actually a command
    if chat_state == MENU and 'test' in text:
        state[chat_id] = AWAIT_FILTER_INPUT # set the state
        context[chat_id] = user_id  # save the user id to context
        bot.sendMessage(chat_id,
                        text="Hi there, what filter(s) would you like to apply?\n"
                        "type /cancel to end this conversation",
                        reply_markup=ForceReply())
    # If we are waiting for input and the right user answered
    # MENU, AWAIT_FILTER_INPUT, AWAIT_FILTER_CONFIRMATION
    elif chat_state == AWAIT_FILTER_INPUT and chat_context == user_id:
        state[chat_id] = AWAIT_FILTER_CONFIRMATION
        # Save the user id and the answer to context
        context[chat_id] = (user_id, update.message.text)
        reply_markup = ReplyKeyboardMarkup(
            [[KeyboardButton(FILTER_1), KeyboardButton(FILTER_2), KeyboardButton(FILTER_3)]],
            one_time_keyboard=True)
        bot.sendMessage(chat_id,
                        text="Okay, just to confirm, you would like the following filters: " + text + ", is that correct?",
                        reply_markup=reply_markup)
    # If we are waiting for confirmation and the right user answered
    elif chat_state == AWAIT_FILTER_CONFIRMATION and chat_context[0] == user_id:
        del state[chat_id]
        del context[chat_id]
        if text == FILTER_1:
            values[chat_id] = chat_context[1]
            bot.sendMessage(chat_id, text="FILTER_1 has been selected.")
        elif text == FILTER_2:
            values[chat_id] = chat_context[1]
            bot.sendMessage(chat_id, text="FILTER_2 has been selected.")
        elif text == FILTER_3:
            values[chat_id] = chat_context[1]
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
    chat_state = state.get(chat_id, MENU)
    chat_context = context.get(chat_id, None)

    # Since the handler will also be called on messages, we need to check if
    # the message is actually a command
    if chat_state == MENU and 'email' in text:
        state[chat_id] = AWAIT_EMAIL_INPUT # set the state
        context[chat_id] = user_id  # save the user id to context
        bot.sendMessage(chat_id,
                        text="Hi there, please input your email!\n"
                        "type /cancel to end this conversation",
                        reply_markup=ForceReply())
    # If we are waiting for input and the right user answered
    # MENU, AWAIT_FILTER_INPUT, AWAIT_FILTER_CONFIRMATION
    elif chat_state == AWAIT_EMAIL_INPUT and chat_context == user_id:
        state[chat_id] = AWAIT_EMAIL_CONFIRMATION
        # Save the user id and the answer to context
        context[chat_id] = (user_id, update.message.text)
        reply_markup = ReplyKeyboardMarkup(
            [[KeyboardButton(YES), KeyboardButton(NO)]],
            one_time_keyboard=True)
        bot.sendMessage(chat_id,
                        text="Okay, just to confirm, I'm sending your photos to: " + text + ", is that correct?",
                        reply_markup=reply_markup)
    # If we are waiting for confirmation and the right user answered
    elif chat_state == AWAIT_EMAIL_CONFIRMATION and chat_context[0] == user_id:
        del state[chat_id]
        del context[chat_id]
        if text == YES:
            values[chat_id] = chat_context[1]
            use_sendgrid(bot, update, values[chat_id])
            bot.sendMessage(chat_id, text="An email has been sent to " + values[chat_id])
        else:
            values[chat_id] = chat_context[1]
            bot.sendMessage(chat_id, text="Okay, no email was sent.")


# def set_webhook(bot):
#     s = bot.setWebhook('https://shrouded-everglades-90342.herokuapp.com/HOOK')
#     if s:
#         return "webhook setup ok"
#     else:
#         return "webhook setup failed"


def main():
    """
    Execute all commands in this function (the brains of the bot).

    This function contains all the general features of the bot
    """
    # Create the EventHandler and pass it your bot's token.
    # updater = Updater(os.environ['TELEGRAM_KEY'])
    updater = Updater('225364376:AAHQYlhLB0EomsJpy5EbICkSmyOFg9SB4Ww')

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler("filters", list_filters))
    dp.add_handler(CommandHandler('test', set_value))
    dp.add_handler(CommandHandler('use_sendgrid', use_sendgrid))
    dp.add_handler(CommandHandler('email', get_email))

    # The answer and confirmation
    dp.add_handler(MessageHandler([Filters.text], get_email))

    # on image upload
    dp.add_handler(MessageHandler([Filters.photo], filter_image))

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Run the bot until the you presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()

if __name__ == '__main__':
    # thread.start_new_thread(app.run, ('0.0.0.0', 3000))
    main()
