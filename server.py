#!/usr/bin/env python

import telegram
from flask import Flask, request

app = Flask(__name__)

global bot
bot = telegram.Bot(token='TOKEN')


@app.route('/HOOK', methods=['POST'])
def webhook_handler():
    if request.method == "POST":
        # retrieve the message in JSON and then transform it to Telegram object
        update = telegram.Update.de_json(request.get_json(force=True))

        chat_id = update.message.chat.id

        # Telegram understands UTF-8, so encode text for unicode compatibility
        text = update.message.text.encode('utf-8')

        # repeat the same message back (echo)
        bot.sendMessage(chat_id=chat_id, text=text)

    return 'ok'


@app.route('/')
def index():
    return '.'

if __name__ == '__main__':
    bot.setWebhook('https://shrouded-everglades-90342.herokuapp.com/HOOK')
    port = int(os.getenv('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
