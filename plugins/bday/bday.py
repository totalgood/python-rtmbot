"""Simple chatbot to notify the channel when it comes online"""
from __future__ import print_function, division

import datetime
import json

from ...main import log

outputs = []


def process_message(data):
    if data['type'] == 'hello':
        process_hello(data)


def catch_all(data):
    print("CAUGHT A SLACK EVENT IN {}.{}.catch_all():".format(__file__, __name__))
    print(data)


def process_hello(data=None):
    """Queues up a message with the time the bot started

    TODO:
      - query slack api for a list of channels and users
      - use slack api to figure out what this bot's first namd and last name are
      - use the first, last name in the bday greeting
      - get python process info (from `sys` module?) and figure out who to thank for being run
      - display a more human-like string for the date, including holidays
      - display a fact about the date (famous birthdays)
      - persist some data between lives and use that to display somthing useful (like this is my 10th bday)
      - create a util.slackout function that utilizes persistent data to populate the default channel
    """
    channel = data.get('channel', None)
    outputs.append([channel, "Hi! I'm Eliza."])
    outputs.append([channel, "I'm responding to a message from Slack at {} with data:\n{}".format(
                   datetime.datetime.now(), json.dumps(data, indent=2))])


def process_presence_change(data=None):
    """Queues up a message with the time the bot joined the channel"""
    channel = data.get('channel', None)
    log.debug('Not responding on channel {} to data: {}'.format(channel, data))
    # outputs.append([channel, "Hi! I'm Eliza Bot. I'm joining channel {} at {}".format(channel, datetime.datetime.now())])


if __name__ == '__main__':
    process_hello()
