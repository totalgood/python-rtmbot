"""Echo any Direct Messages (DMs) sent to the @eliza chatbot user on Slack"""
# import time
crontable = []
outputs = []


def process_message(data):
    """Echo any Direct Messages (DMs) sent to the @eliza chatbot user on Slack"""
    if data['channel'].startswith("D"):
        outputs.append([data['channel'], "from repeat1 \"{}\" in channel {}".format(data['text'], data['channel'])])
