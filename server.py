import telegram
import os
from flask import Flask, request
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import ForceReply, ReplyKeyboardMarkup, KeyboardButton
from PIL import Image
from PIL import ImageFilter
from PIL import ImageOps
import sendgrid
import logging

app = Flask(__name__)

global bot
bot = telegram.Bot(token=os.environ['TELEGRAM_KEY'])

sg = sendgrid.SendGridClient(os.environ['SENDGRID_KEY'])

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

# Define the different states a chat can be in
MENU, AWAIT_FILTER_INPUT, AWAIT_FILTER_CONFIRMATION = range(3)
AWAIT_EMAIL_INPUT, AWAIT_EMAIL_CONFIRMATION = range(3, 5)

# Define the filter names here
FILTER_1, FILTER_2, FILTER_3 = ("FILTER_1", "FILTER_2", "FILTER_3")
YES, NO = ("YES", "NO")

# States are saved in a dict that maps chat_id -> state
state = dict()
# Sometimes you need to save data temporarily
context = dict()
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


def error(bot, update, error):
    """
    Yield any error to the console.

    Pretty self-explanatory, just check the console for error reports
    """
    logger.warn('Update "%s" caused error "%s"' % (update, error))


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
    html_message = "<b>Random Message</b>"
    message = sendgrid.Mail()
    message.add_to(email_address)
    message.set_subject('Random Message Test')
    message.set_html(html_message)
    # message.set_text('Body')
    message.set_from('josephchoi@ateamventures.com')
    message.add_attachment('filtered.jpg', open('filtered.jpg', 'rb'))
    message.add_attachment('sepia_image.jpg', open('sepia_image.jpg', 'rb'))
    message.add_attachment('inverted_image.jpg', open('inverted_image.jpg', 'rb'))
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
                        text="Okay, just to confirm, your email is: " + text + ", is that correct?",
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


# def handle(update):
#     message = update.message.text.encode('utf-8')

#     if message == '/start':
#         pass
#     elif message == '/help':
#         pass
#     elif message == '/list_filters':
#         pass
#     elif message == '/test':
#         pass
#     elif message == '/use_sendgrid':
#         pass
#     elif message == '/email':
#         pass

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

    # No filter provided. Use a default filter.
    reply = ', '.join(filters.keys())
    if not update.message.caption:
        msg_part_1 = 'Please provide the name of the filter you would like to'
        msg_part_2 = 'use in the image\'s caption. Filters:\n\n'
        reply = msg_part_1 + msg_part_2 + reply

        # Notify the user of invalid input
        bot.sendMessage(update.message.chat_id, text=reply)

        img_greyscale = img.convert('L')
        img_greyscale.save('./filtered.jpg')
        bot.sendPhoto(update.message.chat_id,
                      photo=open('./filtered.jpg', 'rb'),
                      caption=('Meanwhile, here\'s your image in greyscale.'))

        # make sepia ramp (tweak color as necessary)
        sepia = make_linear_ramp((255, 220, 192))
        # optional: apply contrast enhancement here, e.g.
        img_sepia = ImageOps.autocontrast(img_greyscale)
        # apply sepia palette
        img_sepia.putpalette(sepia)
        # convert back to RGB so we can save it as JPEG
        # (alternatively, save it in PNG or similar)
        img_sepia = img_sepia.convert("RGB")
        img_sepia.save("./sepia_image.jpg")
        bot.sendPhoto(update.message.chat_id,
                      photo=open('./sepia_image.jpg', 'rb'),
                      caption=('...and, here\'s your image in sepia.'))

        img_inv = ImageOps.invert(img)
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


@app.route('/HOOK', methods=['POST'])
def webhook_handler():
    if request.method == "POST":
        # retrieve the message in JSON and then transform it to Telegram object
        update = telegram.Update.de_json(request.get_json(force=True))

        chat_id = update.message.chat.id

        # # Telegram understands UTF-8, so encode text for unicode compatibility
        # text = update.message.text.encode('utf-8')

        # Create the EventHandler and pass it your bot's token.
        updater = Updater(os.environ['TELEGRAM_KEY'])

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

        # # repeat the same message back (echo)
        # bot.sendMessage(chat_id=chat_id, text=text)


if __name__ == '__main__':
    bot.setWebhook('https://pacific-basin-72105.herokuapp.com/HOOK')
    app.run(host='0.0.0.0', port=3000)
