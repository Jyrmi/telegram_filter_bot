import telegram
import os
from flask import Flask, request

app = Flask(__name__)

global bot

@app.route('/')
def hello_world():
    return 'Hello World!'


@app.route('/alternate')
def hello_alternate():
    return 'Hello from the alternate universe!!!!'

# Define a few command handlers. These usually take the two arguments bot and
# update. Error handlers also receive the raised TelegramError object in error.
def start(update):
    """
    Start the party.

    This function gets da partaaaaayyy started
    Only activated when a new conversation is started with this bot
    """
    message = 'Hi! Do you need /help? Check out my /filters!'
    bot.sendMessage(update.message.chat_id, text=message)


@app.route('/HOOK', methods=['POST'])
def webhook_handler():
    if request.method == "POST":
        # retrieve the message in JSON and then transform it to Telegram object
        update = telegram.Update.de_json(request.get_json(force=True))

        chat_id = update.message.chat.id

        # Telegram understands UTF-8, so encode text for unicode compatibility
        text = update.message.text.encode('utf-8')

        if text == '/start':
            start(update)

        else:
            # repeat the same message back (echo)
            bot.sendMessage(chat_id=chat_id, text=text)


if __name__ == '__main__':
    # bot.setWebhook('https://shrouded-everglades-90342.herokuapp.com/HOOK')
    bot = telegram.Bot(token=os.environ['TELEGRAM_KEY'])
    bot.setWebhook('https://pacific-basin-72105.herokuapp.com/HOOK')
    app.run(host='0.0.0.0', port=3000)