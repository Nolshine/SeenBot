import time
import datetime
import json
import os.path

class DATA_CELL(object):
    def __init__(self, nick, timestamp):
        print "added new nick: " + nick
        self.current_nick = nick
        self.nick_history = []
        self.recent_timestamp = timestamp
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
        print data
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

        if data[1] == "privmsg":
            if len(data) >= 4:
                if data[3] == ":!seen":
                    if len(data) == 4:
                        return "Invalid use of '!seen'"
                    query = data[4]
                    if query == botnick.lower():
                        return "Last seen " + query + " on " + timestamp + ", when looking at the mirror."
                    for cell in self.database:
                        if (cell.current_nick == query) or (query in cell.nick_history):
                            msg = "Last seen " + query + " on " + cell.recent_timestamp + ", as " + cell.current_nick
                            return msg
                    return "I have not seen " + query + " yet."
                elif data[3] == ":!json":
                    for cell in self.database:
                        if (cell.current_nick == nick) or (nick in cell.nick_history):
                            return json.dumps({cell.current_nick:[cell.nick_history, cell.recent_timestamp]})
                else:
                    return None
