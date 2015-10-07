#!/usr/bin/env python2
import sys
import SEENBOT


#### CONFIG ####
config = {}
config["network"] = "esper"
config["nick"] = "porygit"
config["channel"] = "#3dpe"
config["debug"] = True

def debug(text):
    if config["debug"]:
        sys.stderr.write(text + '\n')

seenBot = SEENBOT.SEENBOT() # initialize the bot

for line in iter(sys.stdin.readline, b''):
# strip network name
    line = ' '.join(line[:-1].split(' ')[1:])

    if ("PRIVMSG" in line) or ("NICK" in line):
        debug(config["nick"] + " in: " + line)
        seen = seenBot.process(line, config["nick"])
        if seen != None:
            ircMessage = config["network"] + " PRIVMSG " + config["channel"] + " :" + seen
            debug(config["nick"] + " out: " + ircMessage)
            print ircMessage
            sys.stdout.flush()

