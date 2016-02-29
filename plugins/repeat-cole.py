"""Echo any Direct Messages (DMs) sent to the @eliza chatbot user on Slack"""
import datetime
from collections import defaultdict, Counter
import nltk
nltk.download('all')
sent_detector = nltk.data.load('tokenizers/punkt/english.pickle')

SELF_USER_ID = 'U0LLB3M7C'
crontable = []
outputs = []

from main import log


PLUGIN = (__package__ or '') + '.' + (__name__ or '')


def answer(text):
    tokens = nltk.word_tokenize(text)
    tagged_tokens = nltk.pos_tag(tokens)
    # sents = sent_detector.tokenize(text.strip())

    # for i, sent in enumerate(sents):
    #     # print('-'*80)
    #     sents[i] = sent.replace('\r', ' ').replace('\n', ' ')
    #     print('{:05d}: {}'.format(i, sent))

    # sents = sents[:100]

    return tagged_tokens


def process_message(data):
    """Echo any Direct Messages (DMs) sent to the @eliza chatbot user on Slack"""
    log.debug('{} heard message: {}'.format(PLUGIN, data))
    channel = data.get('channel', '').upper()
    text = data.get('text', '').lower()
    if channel.startswith("D") or "count" in text:
        ans = str(answer(text))
        outputs.append([data['channel'], ans])

    
