#!/usr/bin/python

import json
import telebot
import settings
import sys
from datetime import datetime
from datetime import timedelta
from datetime import timezone
from collections import defaultdict

START_MESSAGE = '''
Hi! I'm a bot here.
'''
OVER_LIMIT_REPLY_TEMPLATE = '''
This is your {message_count}th message today. Please respect the group's rules by not sending any more messages until tomorrow ({time_until_ban_lift} from now).
'''

bot = telebot.TeleBot(settings.API_TOKEN)
server_start_time = datetime.now()
user_messages = defaultdict(lambda: [])


def clean_up_messages(user_id):
    now = datetime.now(settings.TIMEZONE)

    user_messages[user_id] = [
        message_date for message_date in user_messages[user_id]
        if message_date.date() == now.date()
    ]


@bot.message_handler(commands=['help', 'start'])
def send_welcome(message):
    bot.reply_to(message, START_MESSAGE)


def log(log_dict):
    log_dict['LOG_TIME'] = str(datetime.now(timezone.utc))
    print(json.dumps(log_dict))
    sys.stdout.flush()


def time_until_tomorrow_string():
    now = datetime.now(settings.TIMEZONE)
    tomorrow = (now + timedelta(days=1)).date()
    time_until_tomorrow = settings.TIMEZONE.localize(datetime(tomorrow.year, tomorrow.month, tomorrow.day)) - now
    return '{hours:02}:{minutes:02}'.format(
        hours=int(time_until_tomorrow.total_seconds() // 3600),
        minutes=int((time_until_tomorrow.total_seconds() % 3600) // 60),
    )


def is_sent_after_server_start(message):
    return datetime.fromtimestamp(message.date) >= server_start_time


@bot.message_handler(func=lambda message: True)
def echo_message(message):
    if message.chat.id not in settings.CHAT_IDS_WHITELIST:
        log({
            'event': 'Unauthorized chat id, ignored.', 
            'chat_id': message.chat.id,
            'chat_title': message.chat.title,
        })
        return

    if not is_sent_after_server_start(message):
        log({'event': 'Old message, ignored.', 'timestamp': message.date})
        return

    user_id = message.from_user.id
    message_date = settings.TIMEZONE.localize(datetime.fromtimestamp(message.date))

    log({
        'event': 'Processing the message ...',
        'message_date': str(message_date),
        'user_id': message.from_user.id,
        'username': message.from_user.username,
        'chat_id': message.chat.id,
        'chat_title': message.chat.title,
    })
    
    clean_up_messages(user_id)
    user_messages[user_id].append(message_date)
    
    if len(user_messages[user_id]) == (settings.MESSAGE_LIMIT_COUNT + 1) or \
        len(user_messages[user_id]) == (settings.MESSAGE_LIMIT_COUNT * 2):
        log({
            'event': 'Too many messages reply sent.', 
            'user_id': message.from_user.id, 
            'username': message.from_user.username,
            'message_count': len(user_messages[user_id]),
        })

        bot.reply_to(message, OVER_LIMIT_REPLY_TEMPLATE.format(
            message_count=len(user_messages[user_id]),
            time_until_ban_lift=time_until_tomorrow_string(),
        ))


bot.polling()
