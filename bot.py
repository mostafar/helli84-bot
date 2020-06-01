#!/usr/bin/python

import json
import telebot
import settings
import sys
from datetime import datetime
from datetime import timedelta
from datetime import timezone
from collections import defaultdict
from data import get_message_dates
from data import set_message_dates

START_MESSAGE = '''
Hi! I'm a bot here.
'''
OVER_LIMIT_REPLY_TEMPLATE = '''
This is your {message_count}th message today. Please respect the group's rules by not sending any more messages until tomorrow ({time_until_ban_lift} from now).
'''
REPORT_TEMPLATE = '''
You sent {message_count} messages today. Send times:
{message_dates}
'''

bot = telebot.TeleBot(settings.API_TOKEN, num_threads=1)
server_start_time = datetime.now().timestamp()


def clean_up_message_dates(user_id):
    now = datetime.now(settings.TIMEZONE)
    beginning_of_today = now.replace(hour=0, minute=0, second=0, microsecond=0).timestamp()

    return [
        message_date for message_date in get_message_dates(user_id) 
        if message_date > beginning_of_today
    ]


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
    return message.date >= server_start_time


@bot.message_handler(commands=['help', 'start'])
def send_welcome(message):
    bot.reply_to(message, START_MESSAGE)


@bot.message_handler(commands=['report'])
def send_report(message):
    log({
        'event': 'Processing the command ...',
        'message_date': str(settings.TIMEZONE.localize(datetime.fromtimestamp(message.date))),
        'user_id': message.from_user.id,
        'username': message.from_user.username,
        'chat_id': message.chat.id,
        'chat_title': message.chat.title,
        'command': 'REPORT',
        'ZZZ': 'BBB',
    })

    message_dates = clean_up_message_dates(message.from_user.id)

    bot.reply_to(message, REPORT_TEMPLATE.format(
        message_count=len(message_dates),
        message_dates='\n'.join([
            datetime.utcfromtimestamp(
                message_date
            ).replace(
                tzinfo=timezone.utc
            ).astimezone(
                settings.TIMEZONE
            ).strftime('%a, %b %-d - %I:%M %p (%z)')
            for message_date in message_dates
        ]),
    ))


@bot.message_handler(func=lambda message: True)
def process_message(message):
    if message.chat.id not in settings.CHAT_IDS_WHITELIST:
        log({
            'event': 'Unauthorized chat id, ignored.', 
            'chat_id': message.chat.id,
            'chat_title': message.chat.title,
        })
        return

    log({
        'event': 'Processing the message ...',
        'message_date': str(settings.TIMEZONE.localize(datetime.fromtimestamp(message.date))),
        'user_id': message.from_user.id,
        'username': message.from_user.username,
        'chat_id': message.chat.id,
        'chat_title': message.chat.title,
    })
   
    try:
        message_dates = clean_up_message_dates(message.from_user.id)
    except KeyError as e:
        log({
            'event': 'More than one record found in the storage',
            'user_id': message.from_user.id,
            'error': str(e),
        })
        return

    message_dates.append(message.date)
    message_count = len(message_dates)
    set_message_dates(message.from_user.id, message_dates)
    
    if not is_sent_after_server_start(message):
        log({'event': 'Old message, not going to reply.', 'timestamp': message.date})
        return

    if message_count == (settings.MESSAGE_LIMIT_COUNT + 1) or \
        message_count == (settings.MESSAGE_LIMIT_COUNT * 2):
        log({
            'event': 'Too many messages reply sent.', 
            'user_id': message.from_user.id, 
            'username': message.from_user.username,
            'message_count': message_count,
        })

        bot.reply_to(message, OVER_LIMIT_REPLY_TEMPLATE.format(
            message_count=message_count,
            time_until_ban_lift=time_until_tomorrow_string(),
        ))


bot.polling()
