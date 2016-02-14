from __future__ import absolute_import, unicode_string
from __future__ import division, print_function

import os
import json
import re

outputs = []
crontabs = []

tasks = {}

HOME_CHANNEL = "C0LL5MDKN"
FILE = "plugins/attendance.json"
if os.path.isfile(FILE):
    tasks = json.load(open(FILE, 'rUb'))


def process_message(data):
    """Process TODO reminder requests and attendance rollcall "here" messages."""
    global tasks
    channel = data["channel"]
    text = data["text"]

    # Treat DM (direct message "channels") separately, like the TODO app
    if channel.startswith("D"):
        if channel not in tasks.keys():
            tasks[channel] = []
        # do command stuff
        if text.startswith("todo"):
            tasks[channel].append(text[5:])
            outputs.append([channel, "added"])
        if text == "tasks":
            output = ""
            counter = 1
            for task in tasks[channel]:
                output += "%i) %s\n" % (counter, task)
                counter += 1
            outputs.append([channel, output])
        if text == "fin":
            tasks[channel] = []
        if text.startswith("done"):
            num = int(text.split()[1]) - 1
            tasks[channel].pop(num)
        if text == "show":
            print(tasks)
        json.dump(tasks, open(FILE, "wb"))
    # Treat other messages as roll call commands
    elif channel == HOME_CHANNEL:
        print(text)
        if re.match(r'^\s*here\b|pre?se?nt\b|yo\b', text, flags=re.IGNORECASE):
            tasks[channel].append(text[5:])
            outputs.append([channel, "Welcome to class"])
