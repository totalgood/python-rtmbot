#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Console app that parses args, loads plugins, and starts the infinite-loop python-rtmbot to interact with slackbot using callbacks

FIXME: Get this to work (based on scaffolding skeleton.py)
To run this script uncomment the following line in the entry_points section
in setup.cfg:

    console_scripts =
        eliza = huml.module:function

Then run `python setup.py install` which will install the command `eliza`
inside your current environment.
"""
from __future__ import division, print_function, absolute_import

import argparse
import sys
import logging

import glob
import yaml
# import json
import os
import time
from slackclient import SlackClient

_logger = logging.getLogger(__name__)
__author__ = "Hack University Machine Learning class of 2016"
__copyright__ = "Hack Oregon"
__license__ = "MIT"
__version__ = '0.0.1'

sys.dont_write_bytecode = True
DEBUG = 1


def dbg(debug_string):
    """Print and/or log a message to stdout and/or stderr, or do nothing"""
    if DEBUG:
        print(debug_string)
        logging.info(debug_string)


class RtmBot(object):
    """Run plugins and check slack for status periodically"""

    def __init__(self, token, channel="C0LL5MDKN", interval=0.3, ping_interval=5):
        self.channel = channel or "C0LL5MDKN"
        self.interval = interval
        self.ping_interval = min(max(ping_interval, 2), 3600)
        self.first_ping = 0
        self.last_ping = 0
        self.token = token
        self.bot_plugins = []
        self.slack_client = None
        self.last_output = None

    def connect(self):
        """Convenience method that creates Server instance"""
        self.slack_client = SlackClient(self.token)
        self.slack_client.rtm_connect()

    def start(self):
        self.connect()
        self.load_plugins()
        while True:
            for reply in self.slack_client.rtm_read():
                dbg('reply: {}'.format(reply))
                self.input(reply)
            self.crons()
            self.output()
            self.autoping()
            time.sleep(self.interval)
            if DEBUG and (10 < (time.time() - self.first_ping) < (10 + self.interval)) and not self.last_output:
                ans = self.slack_client.rtm_send_message(self.channel, "I'm alive!")
                dbg('Answer to send_message: {}'.format(ans))

    def autoping(self):
        """Automatically ping the server every 3 seconds"""
        now = int(time.time())
        if now > self.last_ping + self.ping_interval:
            self.first_ping = self.first_ping or now
            self.slack_client.server.ping()
            dbg('Next ping in {}s'.format(self.ping_interval))
            self.last_ping = now

    def input(self, data):
        if "type" in data:
            function_name = "process_" + data["type"]
            dbg("got {}".format(function_name))
            for plugin in self.bot_plugins:
                plugin.register_jobs()
                plugin.do(function_name, data)

    def output(self):
        if DEBUG:
            print(self.bot_plugins)
        for plugin in self.bot_plugins:
            if DEBUG:
                print(plugin)
            limiter = False
            for output in plugin.do_output():
                dbg('Found {} output: {}'.format(plugin, output))
                channel = self.slack_client.server.channels.find(output[0])
                if channel is not None and output[1] is None:
                    if limiter is True:
                        time.sleep(.1)
                        limiter = False
                    message = output[1].encode('ascii', 'ignore')
                    channel.send_message("{}".format(message))
                    self.last_output = time.time()
                    limiter = True

    def crons(self):
        for plugin in self.bot_plugins:
            plugin.do_jobs()

    def load_plugins(self):
        for plugin in glob.glob(directory + '/plugins/*'):
            sys.path.insert(0, plugin)
            sys.path.insert(0, directory + '/plugins/')
        for plugin in glob.glob(directory + '/plugins/*.py') + glob.glob(directory + '/plugins/*/*.py'):
            logging.info(plugin)
            name = plugin.split('/')[-1][:-3]
            self.bot_plugins.append(Plugin(name))
        print('Loaded: {}'.format(self.bot_plugins))


class Plugin(object):
    def __init__(self, name, plugin_config={}):
        self.name = name
        self.jobs = []
        self.module = __import__(name)
        self.register_jobs()
        self.outputs = []
        if name in config:
            logging.info("config found for: " + name)
            self.module.config = config[name]
        if 'setup' in dir(self.module):
            self.module.setup()

    def register_jobs(self):
        if 'crontable' in dir(self.module):
            for interval, function in self.module.crontable:
                self.jobs.append(Job(interval, eval("self.module." + function)))
            logging.info(self.module.crontable)
            self.module.crontable = []
        else:
            self.module.crontable = []

    def do(self, function_name, data):
        if function_name in dir(self.module):
            """this makes the plugin fail with stack trace in DEBUG mode"""
            if DEBUG:
                try:
                    eval("self.module." + function_name)(data)
                except:
                    dbg("problem in module {} {}".format(function_name, data))
            else:
                eval("self.module." + function_name)(data)
        if "catch_all" in dir(self.module):
            try:
                self.module.catch_all(data)
            except:
                dbg("problem in catch all")

    def do_jobs(self):
        for job in self.jobs:
            job.check()

    def do_output(self):
        output = []
        while True:
            if 'outputs' in dir(self.module):
                if len(self.module.outputs) > 0:
                    logging.info("output from {}".format(self.module))
                    output.append(self.module.outputs.pop(0))
                else:
                    break
            else:
                self.module.outputs = []
        return output


class Job(object):

    def __init__(self, interval, function):
        self.function = function
        self.interval = interval
        self.lastrun = 0

    def __str__(self):
        return "{} {} {}".format(self.function, self.interval, self.lastrun)

    def __repr__(self):
        return self.__str__()

    def check(self):
        if self.lastrun + self.interval < time.time():
            if not DEBUG:
                try:
                    self.function()
                except:
                    dbg("problem")
            else:
                self.function()
            self.lastrun = time.time()
            pass


class UnknownChannel(Exception):
    pass


def main_loop():
    if "LOGFILE" in config:
        logging.basicConfig(filename=config["LOGFILE"], level=logging.INFO, format='%(asctime)s %(message)s')
    logging.info(directory)
    try:
        bot.start()
    except KeyboardInterrupt:
        sys.exit(0)
    except:
        logging.exception('OOPS')


def parse_args(args):
    """
    Parse command line parameters

    :param args: command line parameters as list of strings
    :return: command line parameters as :obj:`argparse.Namespace`
    """
    parser = argparse.ArgumentParser(
        description="Just a Hello World demonstration")
    parser.add_argument(
        '-v',
        '--version',
        action='version',
        version='huml {ver}'.format(ver=__version__))
    parser.add_argument(
        '-c',
        '--config',
        help='Full path to config file.',
        metavar='path'
    )
    return parser.parse_args(args)


if __name__ == "__main__":

    args = parse_args(sys.argv[1:])
    directory = os.path.dirname(sys.argv[0])
    if not directory.startswith('/'):
        directory = os.path.abspath("{}/{}".format(os.getcwd(), directory))

    config = yaml.load(file(args.config or 'rtmbot.conf', 'r'))
    global DEBUG
    DEBUG = config.get("DEBUG", 1)
    bot = RtmBot(config["SLACK_TOKEN"],
                 channel=config.get("CHANNEL", "C0LL5MDKN"),
                 interval=config.get("INTERVAL", 0.3),
                 ping_interval=config.get("PING_INTERVAL", 5.0))
    site_plugins = []
    files_currently_downloading = []
    job_hash = {}

    if "DAEMON" in config:
        if config["DAEMON"]:
            import daemon
            with daemon.DaemonContext():
                main_loop()
    main_loop()


def main(args=None):
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    args = args or sys.argv[1:]
    args = parse_args(args)
    _logger.info("Script ends here")


def run(args=None):
    main(args)
