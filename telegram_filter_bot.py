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

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from PIL import Image
from PIL import ImageFilter
from PIL import ImageOps
import logging

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

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
    file_id = update.message.photo[-1].file_id

    newFile = bot.getFile(file_id)
    applied_filters = []
    invalid_filters = []
    newFile.download('./download.jpg')
    img = Image.open('./download.jpg')
    img_inv = Image.open('./download.jpg')

    # No filter provided. Use a default filter.
    reply = ', '.join(filters.keys())
    if not update.message.caption:
        msg_part_1 = 'Please provide the name of the filter you would like to'
        msg_part_2 = 'use in the image\'s caption. Filters:\n\n'
        reply = msg_part_1 + msg_part_2 + reply

        # Notify the user of invalid input
        bot.sendMessage(update.message.chat_id, text=reply)

        img = img.convert('L')
        img.save('./filtered.jpg')
        bot.sendPhoto(update.message.chat_id,
                      photo=open('./filtered.jpg', 'rb'),
                      caption=('Meanwhile, here\'s your image in greyscale.'))

        # make sepia ramp (tweak color as necessary)
        sepia = make_linear_ramp((255, 220, 192))
        # optional: apply contrast enhancement here, e.g.
        img_sepia = ImageOps.autocontrast(img)
        # apply sepia palette
        img_sepia.putpalette(sepia)
        # convert back to RGB so we can save it as JPEG
        # (alternatively, save it in PNG or similar)
        img_sepia = img_sepia.convert("RGB")
        img_sepia.save("./sepia_image.jpg")
        bot.sendPhoto(update.message.chat_id,
                      photo=open('./sepia_image.jpg', 'rb'),
                      caption=('...and, here\'s your image in sepia.'))

        img_inv = ImageOps.invert(img_inv)
        img_inv.save('./inverted_image.jpg')
        bot.sendPhoto(update.message.chat_id,
                      photo=open('./inverted_image.jpg', 'rb'),
                      caption=('...and, here\'s your image inverted.'))

        return

    caption = update.message.caption.lower().replace(',', '').split(' ')
    for f in caption:

        # Image.convert can easily turn an image into greyscale
        if f == 'greyscale':
            img = img.convert('L')
            applied_filters.append(f)

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

    img.save('./filtered.jpg')
    if applied_filters:
        bot.sendPhoto(update.message.chat_id,
                      photo=open('./filtered.jpg', 'rb'),
                      caption=' '.join(applied_filters))


def list_filters(bot, update):
    """
    Show all available filters.

    This function will simply show the user all the filters he/she can choose
    """
    bot.sendMessage(update.message.chat_id, text=', '.join(filters.keys()))


def make_linear_ramp(white):
    # putpalette expects [r,g,b,r,g,b,...]
    ramp = []
    r, g, b = white
    for i in range(255):
        ramp.extend((r*i/255, g*i/255, b*i/255))
    return ramp


def main():
    """
    Execute all commands in this function (the brains of the bot).

    This function contains all the general features of the bot
    """
    # Create the EventHandler and pass it your bot's token.
    updater = Updater("225364376:AAHQYlhLB0EomsJpy5EbICkSmyOFg9SB4Ww")

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler("filters", list_filters))

    # on noncommand i.e message - echo the message on Telegram
    dp.add_handler(MessageHandler([Filters.text], echo))

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
    main()
