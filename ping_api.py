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

app = Flask(__name__)

global bot
bot = telegram.Bot(token="")

# # Define the different states a chat can be in
# MENU, AWAIT_FILTER_INPUT, AWAIT_FILTER_CONFIRMATION = range(3)
# AWAIT_EMAIL_INPUT, AWAIT_EMAIL_CONFIRMATION = range(3, 5)

# # Define the filter names here
# FILTER_1, FILTER_2, FILTER_3 = ("FILTER_1", "FILTER_2", "FILTER_3")
# YES, NO = ("YES", "NO")


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


def set_webhook():
    s = bot.setWebhook('https://stormy-river-76696.herokuapp.com/requests')
    if s:
        return "webhook setup ok"
    else:
        return "webhook setup failed"

set_webhook()
