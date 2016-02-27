"""Simple chatbot to notify the channel when it comes online"""
from __future__ import print_function, division
import datetime
outputs = []

global HOME_CHANNEL
HOME_CHANNEL = "C0LL5MDKN"


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
    print('!!!!!!!!!!!Trying to be born!')
    outputs.append([HOME_CHANNEL, "Hi! I'm Eliza Bot."])
    outputs.append([HOME_CHANNEL, "It's good to be alive... again!"])
    outputs.append([HOME_CHANNEL, "Thanks to whomever I owe for that."])
    outputs.append([HOME_CHANNEL, "I was *revived* at {}".format(datetime.datetime.now())])


if __name__ == '__main__':
    process_hello()
