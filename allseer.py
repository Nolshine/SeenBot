import select
import socket
import Seenbot


#### CONFIG ####
config = {}
f = open("bot.conf", 'r')
for line in f.readlines():
    data = line.split()
    config[data[0]] = data[1]
f.close()

def debug(text):
    if config["debug"]:
        print text

debug(str(config))

seenBot = Seenbot.Seenbot() # initialize the bot

debug("connecting")
# start up IRC (might delegate all this to a handler later
irc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
irc.connect((config["server"], int(config["port"])))
debug("connected.")
buffer = ''
debug("sending identity")
irc.send('NICK ' + config["nick"] + '\r\n') #Send our Nick(Notice the Concatenation)
irc.send('USER '+ config["nick"] + ' 0 ' + config["nick"] + ' :Solshine\r\n') #Send User Info to the server

debug("waiting for initial ping")
while True:
    stop = False
    if select.select([irc],[irc],[], 1)[0] != []:
        buffer += irc.recv(1024)
    if "\r\n" in buffer:
        splitbuf = buffer.split("\r\n", 1)
        line, buffer = splitbuf[0], splitbuf[1]
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
        if select.select([irc],[irc],[], 1)[0] != []:
            buffer += irc.recv(1024)
        if "\r\n" in buffer:
            splitbuf = buffer.split("\r\n", 1)
            line, buffer = splitbuf[0], splitbuf[1]
            print line
            if "PING" in line:
                pong = "PONG " + line.split()[1] + '\r\n'
                irc.send(pong)
            else:
                seen = seenBot.process(line, config["nick"], config["dev_key"])
                if seen != None:
                    for line in seen:
                        irc.send("PRIVMSG " + config["channel"] + " :" + line + "\r\n")
except KeyboardInterrupt:
    pass

#quit after test
irc.send('QUIT :bom\r\n')
irc.close()