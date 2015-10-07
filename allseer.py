import select
import socket
import SEENBOT


#### CONFIG ####
config = {}
config["server"] = "irc.esper.net"
config["port"] = 6666
config["nick"] = "SolSeer"
config["channel"] = "#3dpe"
config["debug"] = False

def debug(text):
    if config["debug"]:
        print text

seenBot = SEENBOT.SEENBOT() # initialize the bot

debug("connecting")
# start up IRC (might delegate all this to a handler later
irc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
irc.connect((config["server"], config["port"]))
debug("connected.")

debug("sending identity")
irc.send('NICK ' + config["nick"] + '\r\n') #Send our Nick(Notice the Concatenation)
irc.send('USER '+ config["nick"] + ' 0 ' + config["nick"] + ' :Solshine\r\n') #Send User Info to the server

debug("waiting for initial ping")
while True:
    stop = False
    if select.select([irc],[irc],[], 1)[0] != []:
        buffer = irc.recv(1024)
        for line in buffer.split("\n"):
            print line
            if "PING" in line:
                pong = "PONG " + line.split()[1] + '\r\n'
                irc.send(pong)
            if "End of /MOTD command." in line:
                stop = True
    if stop:
        break
irc.send('JOIN ' + config["channel"] + '\r\n') # Join the pre defined channel
irc.send('PRIVMSG ' + config["channel"] + ' :Hello.\r\n') #Send a Message to the  channel

try:
    while True:
        stop = False
        if select.select([irc],[irc],[], 1)[0] != []:
            buffer = irc.recv(1024)
            for line in buffer.split("\n"):
                console = line
                if "PING" in line:
                    pong = "PONG " + line.split()[1] + '\r\n'
                    irc.send(pong)
                if ("PRIVMSG" in line) or ("NICK" in line):
                    console = "\n-X- ATTENTION -X- " + line + "\n"
                    seen = seenBot.process(line, config["nick"])
                    if seen != None:
                        irc.send("PRIVMSG " + config["channel"] + " :" + seen + "\r\n")
                debug(console)
                print line
        if stop:
            break;
except KeyboardInterrupt:
    pass

#quit after test
irc.send('QUIT :bom\r\n')
irc.close()