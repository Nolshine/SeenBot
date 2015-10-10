#!/usr/bin/env python2
import sys
import SEENBOT
from config import Config

config = Config("bot.conf")
config.load("secret.conf")

print config.network
print config.channel

def debug(text):
    if config.debug:
        sys.stderr.write(text + '\n')

seenBot = SEENBOT.SEENBOT() # initialize the bot

for line in iter(sys.stdin.readline, b''):
# strip network name
    line = ' '.join(line[:-1].split(' ')[1:])

    if ("PRIVMSG" in line) or ("NICK" in line):
        debug(config.nick + " in: " + line)
        seen = seenBot.process(line, config.nick, config.dev_key)
        if seen != None:
            for msg in seen:
                ircMessage = config.network + " PRIVMSG " + config.channel + " :" + msg
                debug(config.nick + " out: " + ircMessage)
                print ircMessage
                sys.stdout.flush()

