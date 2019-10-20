# -*- coding: utf-8 -*-


import os
import sys
import errno
from argparse import ArgumentParser
import requests
from flask import Flask, request, abort, json
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
)

app = Flask(__name__)

static_tmp_path = os.path.join(os.path.dirname(__file__), 'static', 'tmp')

channel_secret = 'bd6347ef544d95f709b8d8f716f08907'
channel_access_token = 'P7MEuZKAZsKzvRzc4Ca0unYqFPoWYoSCW5KLWi8RKO5XianHNu/a4yFFawJBS7uZjoV19gwPs8DCJdG5BzWa5NfhbKIfDqPrMJsLeUtMtkjakPrmpa/sEiIEuZ4dVqV+SCVEzOOWA8T5g39H8WXTPwdB04t89/1O/w1cDnyilFU='
if channel_secret is None:
    print('Specify LINE_CHANNEL_SECRET as environment variable.')
    sys.exit(1)
if channel_access_token is None:
    print('Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.')
    sys.exit(1)

line_bot_api = LineBotApi(channel_access_token)
handler = WebhookHandler(channel_secret)


# function

def make_static_tmp_dir():
    try:
        os.makedirs(static_tmp_path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(static_tmp_path):
            pass
        else:
            raise


api_reply = "https://api.line.me/v2/bot/message/reply"
api_push = "https://api.line.me/v2/bot/message/multicast"


def line_message_reply(event, messages):
    payload = {
        'replyToken': event.reply_token,
        "messages": messages
    }
    headers = {
        'Authorization': 'Bearer {0}'.format(channel_access_token),
        'Content-Type': 'application/json'
    }
    r = requests.post(api_reply, data=json.dumps(payload), headers=headers)
    print('reply', r)


def line_message_push(to_line_id, messages):
    payload = {
        'to': to_line_id,
        'messages': messages
    }

    headers = {
        'Authorization': 'Bearer {0}'.format(channel_access_token),
        'Content-Type': 'application/json'
    }
    r = requests.post(api_push, data=json.dumps(payload), headers=headers)
    print('push', r)


# end function

@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'


@handler.add(MessageEvent, message=TextMessage)
def message_text(event):
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=event.message.text)
    )


if __name__ == "__main__":
    app.jinja_env.auto_reload = True
    app.config['TEMPLATES_AUTO_RELOAD'] = True

    make_static_tmp_dir()

    app.run(debug=True, port=8000)
