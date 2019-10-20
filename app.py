# -*- coding: utf-8 -*-


from __future__ import unicode_literals

import datetime
import errno
import json
import os
import sys
import tempfile
import requests
from argparse import ArgumentParser

from flask import Flask, request, abort, send_from_directory, json
from werkzeug.middleware.proxy_fix import ProxyFix

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    LineBotApiError, InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    SourceUser, SourceGroup, SourceRoom,
    TemplateSendMessage, ConfirmTemplate, MessageAction,
    ButtonsTemplate, ImageCarouselTemplate, ImageCarouselColumn, URIAction,
    PostbackAction, DatetimePickerAction,
    CameraAction, CameraRollAction, LocationAction,
    CarouselTemplate, CarouselColumn, PostbackEvent,
    StickerMessage, StickerSendMessage, LocationMessage, LocationSendMessage,
    ImageMessage, VideoMessage, AudioMessage, FileMessage,
    UnfollowEvent, FollowEvent, JoinEvent, LeaveEvent, BeaconEvent,
    MemberJoinedEvent, MemberLeftEvent,
    FlexSendMessage, BubbleContainer, ImageComponent, BoxComponent,
    TextComponent, SpacerComponent, IconComponent, ButtonComponent,
    SeparatorComponent, QuickReply, QuickReplyButton,
    ImageSendMessage)

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_host=1, x_proto=1)

channel_secret = 'bd6347ef544d95f709b8d8f716f08907'
channel_access_token = 'P7MEuZKAZsKzvRzc4Ca0unYqFPoWYoSCW5KLWi8RKO5XianHNu/a4yFFawJBS7uZjoV19gwPs8DCJdG5BzWa5NfhbKIfDqPrMJsLeUtMtkjakPrmpa/sEiIEuZ4dVqV+SCVEzOOWA8T5g39H8WXTPwdB04t89/1O/w1cDnyilFU='
if channel_secret is None or channel_access_token is None:
    print('Specify LINE_CHANNEL_SECRET and LINE_CHANNEL_ACCESS_TOKEN as environment variables.')
    sys.exit(1)

line_bot_api = LineBotApi(channel_access_token)
handler = WebhookHandler(channel_secret)

static_tmp_path = os.path.join(os.path.dirname(__file__), 'static', 'tmp')


# function for create tmp dir for download content
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
    except LineBotApiError as e:
        print("Got exception from LINE Messaging API: %s\n" % e.message)
        for m in e.error.details:
            print("  %s: %s" % (m.property, m.message))
        print("\n")
    except InvalidSignatureError:
        abort(400)

    return 'OK'


@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    text = event.message.text
    print('text = ', text)
    if text == 'วันลา':
        line_id = event.source.user_id
        msg = {
            "type": "template",
            "altText": "this is a buttons template",
            "template": {
                "type": "buttons",
                "actions": [
                    {
                        "type": "uri",
                        "label": ">> คลิก <<",
                        "uri": "http://google.com?q={}".format(line_id)
                    }
                ],
                "title": "ระบบวันลา",
                "text": "ขอลา-ตรวจสอบวันลา"
            }
        }
        line_message_reply(event, [
            msg
        ])
        print('line_id = ', line_id)

    if text == 'คำอื่น':
        pass


@handler.add(MessageEvent, message=LocationMessage)
def handle_location_message(event):
    line_bot_api.reply_message(
        event.reply_token,
        LocationSendMessage(
            title='Location', address=event.message.address,
            latitude=event.message.latitude, longitude=event.message.longitude
        )
    )


@handler.add(MessageEvent, message=StickerMessage)
def handle_sticker_message(event):
    line_bot_api.reply_message(
        event.reply_token,
        StickerSendMessage(
            package_id=event.message.package_id,
            sticker_id=event.message.sticker_id)
    )


@handler.add(FollowEvent)
def handle_follow(event):
    app.logger.info("Got Follow event:" + event.source.user_id)
    line_bot_api.reply_message(
        event.reply_token, TextSendMessage(text='Got follow event'))


@handler.add(UnfollowEvent)
def handle_unfollow(event):
    app.logger.info("Got Unfollow event:" + event.source.user_id)


@handler.add(JoinEvent)
def handle_join(event):
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text='Joined this ' + event.source.type))


@handler.add(LeaveEvent)
def handle_leave():
    app.logger.info("Got leave event")


@app.route('/static/<path:path>')
def send_static_content(path):
    return send_from_directory('static', path)


if __name__ == "__main__":
    app.jinja_env.auto_reload = True
    app.config['TEMPLATES_AUTO_RELOAD'] = True

    make_static_tmp_dir()

    app.run(debug=True, port=8000)
