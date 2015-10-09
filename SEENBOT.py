import time
import datetime
import json
import os.path
import sys
import string
import requests

class DATA_CELL(object):
    def __init__(self, nick, timestamp):
        sys.stderr.write("added new nick: " + nick + '\n')
        self.current_nick = nick
        self.nick_history = []
        self.recent_timestamp = timestamp
        self.memos = []
        self.message_light = False # this here is a flag that turns on if a person is given a memo.
                                   # when the person is seen the bot will inform them they have memos and turn this flag off.
    @staticmethod
    def load(s):
        dc = DATA_CELL(s['current_nick'], s['recent_timestamp'])
        for nick in s['nick_history']:
            dc.nick_history.append(nick)
        for memo in s['memos']:
            dc.memos.append(memo)
        if s['message_light'] == 'true':
            sys.stderr.write("string 'true' loads correcly")
            dc.message_light = True
        elif s['message_light'] == True:
            sys.stderr.write("actual boolean value loads correctly")
            dc.message_light = True
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

    def process(self, raw, botnick, pb_api_dev_key): # please do remove anything in front of the 'nick!name@hostmask' part of the raw
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
                if cell.memos != [] and cell.message_light:
                    outgoing.append(cell.current_nick + ": You have memos!")
                    cell.message_light = False

        if data[1] == "privmsg":
            if len(data) >= 4:
                if data[3] == ":!seen":
                    if len(data) == 4:
                        outgoing.append("'!seen' requires a target. (!seen <TARGET>)")
                        return outgoing
                    query = data[4]
                    if query == botnick.lower():
                        outgoing.append("Last seen " + query + " on " + timestamp + ", when looking at the mirror.")
                        return outgoing
                    for cell in self.database:
                        if (cell.current_nick == query) or (query in cell.nick_history):
                            outgoing.append("Last seen " + query + " on " + cell.recent_timestamp + ", as " + cell.current_nick)
                            return outgoing
                    outgoing.append("I have not seen " + query + " yet.")
                    return outgoing
                elif data[3] == ":!tell":
                    if len(data) == 4:
                        outgoing.append("'!tell' requires two arguments. (!tell <TARGET> <MESSAGE>)")
                        return outgoing
                    else:
                        target = data[4]
                        if len(data) == 5:
                            outgoing.append("'!tell' requires two arguments. (!tell <TARGET> <MESSAGE>)")
                            return outgoing
                        else:
                            if target == botnick.lower():
                                outgoing.append("I cannot receive memos.")
                                return outgoing
                            for cell in self.database:
                                if (target == cell.current_nick) or (target in cell.nick_history):
                                    memo = string.join(data[5:])
                                    cell.memos.append((timestamp, nick, memo))
                                    sys.stderr.write(timestamp + ": Added memo: " + memo + " to CELL: " + cell.current_nick + "\n".decode('utf-8', 'ignore'))
                                    outgoing.append("I will tell them when I next see them.")
                                    cell.message_light = True
                                    self.save()
                                    return outgoing
                            outgoing.append("I have not seen "+target+" yet.")
                            return outgoing
                elif data[3] == ":!memos":
                    if (nick + ": You have memos!") in outgoing:
                        outgoing.remove(nick + ": You have memos!")
                    for cell in self.database:
                        if nick == cell.current_nick:
                            if cell.memos != []:
                                pb_api_paste_code = ""
                                for memo in cell.memos:
                                    msg = memo[0] + " - " + memo[1] + " said to you: " + memo[2] + "\n"
                                    sys.stderr.write(msg+"\n".decode('utf-8', 'ignore'))
                                    pb_api_paste_code += msg
                                sys.stderr.write(pb_api_paste_code)

                                # this portion will convert memo list to a pastebin post
                                url = "http://pastebin.com/api/api_post.php"
                                pb_payload = {}
                                pb_payload["api_dev_key"] = pb_api_dev_key
                                pb_payload["api_option"] = "paste"
                                pb_payload["api_paste_private"] = "1" # paste an unlisted paste
                                pb_payload["api_paste_expire"] = "1H" # expire new paste in one hour
                                pb_payload["api_paste_code"] = pb_api_paste_code
                                r = requests.post(url, pb_payload)
                                outgoing.append(nick + ": Your link: " + r.text)
                                cell.memos = []
                                self.save()
                                return outgoing
                            else:
                                outgoing.append(nick + ":You have no memos.")
                                return outgoing

        if outgoing == []:
            return None
        else:
            return outgoing
