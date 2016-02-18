"""Echo any Direct Messages (DMs) sent to the @eliza chatbot user on Slack"""
import datetime
crontable = []
outputs = []


def process_message(data):
    """Echo any Direct Messages (DMs) sent to the @eliza chatbot user on Slack"""
    print data['channel']
    if data['channel'].startswith("D") or data['channel'] in ["C0LL5MDKN"] or data['text'].startswith('@eliza'):
        outputs.append([data['channel'], "Received '{}' in channel '{}' at {}".format(
                        data['text'], data['channel'], datetime.datetime.now())])
