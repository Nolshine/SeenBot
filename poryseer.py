#!/usr/bin/env python2
import sys
import SEENBOT


#### CONFIG ####
config = {}
config["nick"] = "SolSeer"
config["channel"] = "#3dpe"
config["debug"] = False

def debug(text):
    if config["debug"]:
        sys.stderr.write(text + '\n')

seenBot = SEENBOT.SEENBOT() # initialize the bot

for line in iter(sys.stdin.readline, b''):
# strip network name
    line = ' '.join(line.split(' ')[1:])

    if ("PRIVMSG" in line) or ("NICK" in line):
        console = "\n-X- ATTENTION -X- " + line + "\n"
        seen = seenBot.process(line, config["nick"])
        if seen != None:
            print "esper PRIVMSG " + config["channel"] + " :" + seen
        debug(console)

