"""Echo any Direct Messages (DMs) sent to the @eliza chatbot user on Slack"""
import datetime


SELF_USER_ID = 'U0LLB3M7C'
crontable = []
outputs = []

from main import log


PLUGIN = (__package__ or '') + '.' + (__name__ or '')


def process_message(data):
    """Echo any Direct Messages (DMs) sent to the @eliza chatbot user on Slack"""
    log.debug('{} heard message: {}'.format(PLUGIN, data))
    channel = data.get('channel', '').upper()
    text = data.get('text', '').lower()
    if channel.startswith("D") or text.startswith('@eliza') or text.startswith('<@{}>'.format(SELF_USER_ID.lower())):
        outputs.append([data['channel'], "{} plugin received '{}' in channel '{}' at {}".format(
                        PLUGIN, data['text'], data['channel'], datetime.datetime.now())])
