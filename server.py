import telegram
import os
from flask import Flask, request

app = Flask(__name__)

global bot
bot = telegram.Bot(token=os.environ['TELEGRAM_KEY'])

@app.route('/')
def hello_world():
    return 'Hello World!'


@app.route('/alternate')
def hello_alternate():
    return 'Hello from the alternate universe!!!!'


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


# @app.route('/', methods=['GET', 'POST'])
def set_webhook():
    s = bot.setWebhook('https://shrouded-everglades-90342.herokuapp.com/HOOK')
    if s:
        return "webhook setup ok"
    else:
        return "webhook setup failed"


if __name__ == '__main__':
    set_webhook()
    app.run(host='0.0.0.0', port=3000)
