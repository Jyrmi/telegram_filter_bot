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
# import numpy as np
from PIL import Image
import matplotlib.image as mpimg
import logging
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


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
    bot.sendMessage(update.message.chat_id, text='Hi!')


def help(bot, update):
    """
    Some helpful text with the /help command.

    This function should just provide an overview of what commands to use
    """
    message = "Simply upload a photo (as a photo, not a file) to get started"
    bot.sendMessage(update.message.chat_id, text=message)


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


def image_download(bot, update):
    """
    Return images processed using the PIL and matplotlib libraries.

    This function should apply filters similar to Instagram and return images
    """
    bot.sendMessage(update.message.chat_id, text='upload successful')
    print update.message.photo[2]
    file_id = update.message.photo[2].file_id
    newFile = bot.getFile(file_id)
    newFile.download('./download.jpg')
    Image.open('./download.jpg').convert('RGB').save('./greyscale.jpg')

    img = Image.open('download.jpg').convert('L')
    img.save('./greyscale.jpg')

    img = mpimg.imread('./download.jpg')
    # gray = np.dot(img[...,:3], [0.299, 0.587, 0.114])
    # plt.imshow(gray, cmap = plt.get_cmap('gray'))
    # plt.imshow(gray, cmap = ('Greys_r'))
    # rawData = open("./greyscale.jpg" 'rb').read()
    # imgSize = (100,100)
    # img = Image.fromstring('L', imgSize, rawData, 'raw', 'F;16')
    # img.save("./greyscale.jpg")

    bot.sendPhoto(update.message.chat_id, photo=open('./greyscale.jpg', 'rb'))
    print update.message


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

    # on noncommand i.e message - echo the message on Telegram
    dp.add_handler(MessageHandler([Filters.text], echo))

    # on file upload
    dp.add_handler(MessageHandler([Filters.photo], image_download))

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
