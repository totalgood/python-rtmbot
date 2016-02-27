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

import os
import sys
import logging
from copy import deepcopy
import argparse
import glob
import yaml
import time
from traceback import format_exc

from slackclient import SlackClient

# Put your real channel, user, and slack_token values in `rtmbot.conf` in YAML format like this
EXAMPLE_RTMBOT_CONF_FILE = """
PLUGINS: ""
DEBUG: 1
LOGFILE: "bot.log"
INTERVAL: 2.0
PING_INTERVAL: 4.11
CHANNEL: "C0LL4CHAN"
USER: "U0XX4USER"
SLACK_TOKEN: "xoxb-20161225042-slackTOKEN1234567xyzabcd"
"""
CONFIG = yaml.load(EXAMPLE_RTMBOT_CONF_FILE)
CONFIG.update(yaml.load(open('rtmbot.conf')))
CONFIG["PLUGINS"] = (CONFIG["PLUGINS"] or os.path.join(os.getcwd(), 'plugins')).rstrip(os.path.sep)

BOT = None

__author__ = "Hack University Machine Learning class of 2016"
__copyright__ = "Hack Oregon"
__license__ = "MIT"
__version__ = '0.0.1'

log = logging.getLogger(__name__)
# default logging level is overridden later based on CONFIG
log.setLevel(logging.DEBUG)
verbose_formatter = logging.Formatter('%(asctime)s %(levelname)s: %(name)s.%(module)s.%(funcName)s:%(lineno)d: %(message)s',
                                      datefmt='%a %b %d %y %H:%M:%S')
debug_formatter = logging.Formatter('%(name)s.%(module)s.%(funcName)s:%(lineno)d: %(message)s')
# create file handler which logs even debug messages
log_file_handler = logging.FileHandler(CONFIG.get('LOGFILE', 'bot.log'))
log_file_handler.setLevel(logging.INFO - 10 * CONFIG['DEBUG'])
# create console handler with a higher log level
log_console_handler = logging.StreamHandler()
log_console_handler.setLevel(logging.ERROR - 10 * CONFIG['DEBUG'])
# create formatter and add it to the handlers
log_file_handler.setFormatter(verbose_formatter)
log_console_handler.setFormatter(debug_formatter)
# add the handlers to the logger
log.addHandler(log_file_handler)
log.addHandler(log_console_handler)
# sys.dont_write_bytecode = True


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
                log.debug('Slack replied to RTM read with: {}'.format(reply))
                self.input(reply)
            self.crons()
            self.output()
            self.autoping()
            time.sleep(self.interval)

    def autoping(self):
        """Automatically ping the server every 3 seconds"""
        now = int(time.time())
        if now > self.last_ping + self.ping_interval:
            self.first_ping = self.first_ping or now
            self.slack_client.server.ping()
            log.debug('Next ping in {}s'.format(self.ping_interval))
            self.last_ping = now

    def input(self, data):
        if "type" in data:
            function_name = "process_" + data["type"]
            log.debug("Slack reply contained function call for {}".format(function_name))
            for plugin in self.bot_plugins:
                plugin.register_jobs()
                plugin.do(function_name, data)
                plugin.do("catch_all", data)

    def output(self):
        for plugin in self.bot_plugins:
            plugin_outputs = plugin.do_output()
            log.debug('Got outputs from {}: '.format(plugin.name, plugin_outputs))
            limit = False
            for output in plugin_outputs:
                log.debug('Found {} output: {}'.format(plugin, output))
                channel = self.slack_client.server.channels.find(output[0])
                if channel is not None and output[1] is not None:
                    if limit:
                        time.sleep(1)
                        limit = False
                    message = output[1].encode('ascii', 'ignore')
                    channel.send_message("{}".format(message))
                    self.last_output = time.time()
                    limit = True

    def crons(self):
        for plugin in self.bot_plugins:
            plugin.do_jobs()

    def load_plugins(self):
        # add all the directories and files in the plugins folder to the PYTHONPATH for importing within the plugins
        for plugin in glob.glob(os.path.join(CONFIG['PLUGINS'], '*')):
            sys.path.insert(0, plugin)
        sys.path.insert(0, CONFIG['PLUGINS'] + os.path.sep)
        # add all python files in the plugins director and subdir to the list of modules to load
        for plugin in glob.glob(os.path.join(CONFIG['PLUGINS'], '*.py')) + glob.glob(os.path.join(CONFIG['PLUGINS'], '*', '*.py')):
            log.info("Adding {} to the plugins to be loaded.".format(plugin))
            name = plugin.split('/')[-1][:-3]
            self.bot_plugins.append(Plugin(name))
        print('Loaded: {}'.format([pi.name for pi in self.bot_plugins]))


class Plugin(object):
    def __init__(self, name, plugin_config={}):
        self.name = name
        self.jobs = []
        self.module = __import__(name)
        self.register_jobs()
        self.outputs = []
        config = deepcopy(CONFIG)
        # allow plugin.conf files to override global rtmbot.conf settings
        try:
            config.update(yaml.load(open(name + '.conf')))
        except:
            pass
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
            """Run the function found in the plugin module"""
            try:
                eval("self.module." + function_name)(data)
            except:
                # In DEBUG mode you want the exception to be thrown when a plugin fails.
                if CONFIG['DEBUG']:
                    raise
                # Otherwise continue with other plugins and log traceback and error message
                log.error(format_exc())
                log.error("Problem in module {} {}".format(function_name, data))
            else:
                eval("self.module." + function_name)(data)
        else:
            log.debug("Unable to find {} function in {} module among these functions: {}".format(
                      function_name, self.module.__name__, dir(self.module)))

    def do_jobs(self):
        for job in self.jobs:
            job.check()

    def do_output(self):
        output = []
        while True:
            if 'outputs' in dir(self.module):
                if len(self.module.outputs) > 0:
                    channel_message = self.module.outputs.pop(0)
                    log.info("Trying to output {} from {}".format(channel_message, self.module))
                    output.append(channel_message)
                else:
                    log.debug("Empty outputs in {}".format(self.module))
                    break
            else:
                log.debug("No outputs attribute in {}".format(self.module))
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
                    log.debug("Problem running {}".format(self.function))
            else:
                self.function()
            self.lastrun = time.time()
            pass


class UnknownChannel(Exception):
    pass


def main_loop():
    global CONFIG, BOT
    log.debug(CONFIG['PLUGINS'])
    try:
        BOT.start()
    except KeyboardInterrupt:
        sys.exit(0)
    except:
        log.error(format_exc())
        log.error('Unable to start `main_loop()`')


def parse_args(args):
    """Parse shell script command line parameters (arguments)

    args (list of str): command line parameters with args[0] as the command or name string

    Returns:
      parsed_args (argparse.Namespace): Command line parameters
        Individual args are accessible as attributes with `parsed_args.verbose` for the argument named `verbose`
    """
    parser = argparse.ArgumentParser(
        description="SlackBot demonstration")
    parser.add_argument(
        '--version',
        action='version',
        version='huml {ver}'.format(ver=__version__))
    parser.add_argument("-v", "--verbose", action="count", default=0,
                        help="Verbose output. May be repeated for greater verbosity")
    parser.add_argument(
        '-c',
        '--config',
        help='Full path to config file.',
        metavar='path'
    )
    return parser.parse_args(args)


def main(args=None, config=CONFIG):
    """Called by `run` which parses argsv[1:] and passes them as args.

    If this module is run as a script rather than imported as a module, then
    `run()` is called without any args, and run() then calls `main()` with a list of command line arg strings
    (except for argsv[0]). So here we need to...

    1. parse command line arguments (a list of strings) using the argparse package (inside `parse_args` function).
    2. update the global CONFIG, DEBUG, etc
    3. Instantiate a bot (which loads all the plugins it can find)
    """
    global BOT

    args = parse_args(args or sys.argv[1:])

    BOT = RtmBot(config["SLACK_TOKEN"],
                 channel=config.get("CHANNEL", CONFIG['CHANNEL']),
                 interval=config.get("INTERVAL", CONFIG['CHANNEL']),
                 ping_interval=config.get("PING_INTERVAL", CONFIG['CHANNEL']))
    # site_plugins = []
    # files_currently_downloading = []
    # job_hash = {}

    if config.get("DAEMON", None):
        import daemon
        with daemon.DaemonContext():
            main_loop()
    else:
        main_loop()

    log.info("Finished running `main(args={})`".format(args))


def run():
    global CONFIG
    # set the default or root log level and destination
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    CONFIG['PLUGINS'] = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), 'plugins')
    main(sys.argv[1:], config=CONFIG)


if __name__ == "__main__":
    run()
