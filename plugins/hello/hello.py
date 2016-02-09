"""Simple chatbot to notify the channel when it comes online"""
import time
outputs = []


def hello():
    """Queues up a message with the time the bot started"""
    outputs.append(["C0LL5MDKN", "Hello Worl! It's good to be alive again at " + str(time.time())])

if __name__ == '__main__':
    hello()
