import time
import datetime
import json
import os.path
import sys
import string

class DATA_CELL(object):
    def __init__(self, nick, timestamp):
        sys.stderr.write("added new nick: " + nick + '\n')
        self.current_nick = nick
        self.nick_history = []
        self.recent_timestamp = timestamp
        self.memos = {}
    @staticmethod
    def load(s):
        dc = DATA_CELL(s['current_nick'], s['recent_timestamp'])
        for nick in s['nick_history']:
            self.nick_history.append(nick)
        return dc

class SEENBOT(object):
    """handles storing and tracking 'last seen' data of users in the channel."""

    def __init__(self, filename = "SolSeer.json"):
        self.database = []
        self.filename = filename
        self.load()

    def toJson(self):
        return json.dumps(self.__dict__, default=lambda o: o.__dict__)

    def save(self):
        f = open(self.filename, 'w')
        f.write(self.toJson() + "\n")

    def load(self):
        if not os.path.isfile(self.filename):
            return
        f = open(self.filename, 'r')
        l = f.readline()
        o = json.loads(l)
        for cell in o['database']:
            self.database.append(DATA_CELL.load(cell))

    def process(self, raw, botnick): # please do remove anything in front of the 'nick!name@hostmask' part of the raw
        data = raw.lower().split()
        sys.stderr.write(str(data) + '\n')
        nick = data[0].strip(':').split('!')[0]
        timestamp = time.time()
        timestamp = datetime.datetime.fromtimestamp(timestamp).strftime('%d/%m/%Y %H:%M:%S')
        if self.database == []:
            self.database.append(DATA_CELL(nick, timestamp))
        else:
            nick_exists = False
            for cell in self.database:
                if cell.current_nick == nick:
                    nick_exists = True
                    cell.recent_timestamp = timestamp
                    if (data[1] == "nick"):
                        newnick = data[2].strip(":")
                        if not (nick in cell.nick_history):
                            cell.nick_history.append(nick)
                        cell.current_nick = newnick
            if not nick_exists:
                self.database.append(DATA_CELL(nick, timestamp))
            self.save()

        outgoing = []

        for cell in self.database:
            if (cell.current_nick == nick) or (nick in cell.nick_history):
                if cell.memos != {}:
                    outgoing.append(cell.current_nick + ": You have memos!")
                    for sender in cell.memos:
                        msg = cell.memos[sender][0] + " - " + sender + " said to you: " + cell.memos[sender][1]
                        outgoing.append(msg)
                cell.memos = {}
                self.save()

        if data[1] == "privmsg":
            if len(data) >= 4:
                if data[3] == ":!seen":
                    if len(data) == 4:
                        outgoing.append("'!seen' requires a target. (!seen <TARGET>)")
                    query = data[4]
                    if query == botnick.lower():
                        outgoing.append("Last seen " + query + " on " + timestamp + ", when looking at the mirror.")
                    for cell in self.database:
                        if (cell.current_nick == query) or (query in cell.nick_history):
                            outgoing.append("Last seen " + query + " on " + cell.recent_timestamp + ", as " + cell.current_nick)
                    outgoing.append("I have not seen " + query + " yet.")
                elif data[3] == ":!tell":
                    if len(data) == 4:
                        outgoing.append("'!tell' requires two arguments. (!tell <TARGET> <MESSAGE>)")
                    else:
                        target = data[4]
                        if len(data) == 5:
                            outgoing.append("'!tell' requires two arguments. (!tell <TARGET> <MESSAGE>)")
                        else:
                            for cell in self.database:
                                if (target == cell.current_nick) or (target in cell.nick_history):
                                    memo = string.join(data[5:])
                                    cell.memos[nick] = (timestamp, memo)
                                    sys.stderr.write(timestamp + ": Added memo: " + memo + " to CELL: " + cell.current_nick + "\n")
                                    outgoing.append("I will tell them when I next see them.")
                                    self.save()
        if outgoing != []:
            return outgoing
        else: return None
