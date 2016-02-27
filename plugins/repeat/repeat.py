"""Echo any Direct Messages (DMs) sent to the @eliza chatbot user on Slack"""
import datetime
crontable = []
outputs = []

from main import log


PLUGIN = (__package__ or '') + '.' + (__name__ or '')


def process_message(data):
    """Echo any Direct Messages (DMs) sent to the @eliza chatbot user on Slack"""
    log.debug('{} heard message: {}'.format(PLUGIN, data)
    if data['channel'].startswith("D") or data.get('text', '').startswith('@eliza'):
        outputs.append([data['channel'], "{} plugin received '{}' in channel '{}' at {}".format(
                        PLUGIN, data['text'], data['channel'], datetime.datetime.now())])
