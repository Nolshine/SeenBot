#!/usr/bin/env python2
import sys
import Seenbot
import PasteService
from config import Config

config = Config("bot.conf")
config.load("secret.conf")

config.write(sys.stderr)

def debug(text):
    if config.debug:
        sys.stderr.write(text + '\n')

paste = PasteService.Umiki(config.dev_key)
seenBot = Seenbot.Seenbot(paste) # initialize the bot

for line in iter(sys.stdin.readline, b''):
# strip network name
    line = ' '.join(line[:-1].split(' ')[1:])

    if ("PRIVMSG" in line) or ("NICK" in line):
        debug(config.nick + " in: " + line)
        seen = seenBot.process(line, config.nick)
        if seen != None:
            for msg in seen:
                ircMessage = config.network + " PRIVMSG " + config.channel + " :" + msg
                debug(config.nick + " out: " + ircMessage)
                print ircMessage
                sys.stdout.flush()

