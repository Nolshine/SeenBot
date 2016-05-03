from datetime import datetime
import pytz
import json
import os.path
import sys
import string
import PasteService

class DataCell(object):
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
        dc = DataCell(s['current_nick'], s['recent_timestamp'])
        for nick in s['nick_history']:
            dc.nick_history.append(nick)
        for memo in s['memos']:
            dc.memos.append(memo)
        if s['message_light'] == 'true':
            sys.stderr.write("string 'true' loads correctly")
            dc.message_light = True
        elif s['message_light'] == True:
            sys.stderr.write("actual boolean value loads correctly")
            dc.message_light = True
        return dc

class Seenbot(object):
    """handles storing and tracking 'last seen' data of users in the channel."""

    def __init__(self, paste, filename = "SolSeer.json"):
        self.paste = paste
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
            self.database.append(DataCell.load(cell))

    def process(self, raw, botnick):
        data_raw = raw.split() # for rickrolling!
        data_lower = raw.lower().split()
        case = None
        nick = data_lower[0].strip(':').split('!')[0]
        outgoing = []

        if nick == botnick:
            sys.stderr.write("ignoring own actions.")
            return None

        timestamp = datetime.now(pytz.utc).strftime("%c") + " UTC"
        if len(data_lower) > 1:
            case = data_lower[1]
        if case != None:
            case_join = (case == 'join')
            case_privmsg = (case == 'privmsg')
            case_nick = (case == 'nick')
            if case_join or case_privmsg:
                sys.stderr.write("JOIN or PRIVMSG detected.\n")
                if self.database == []:
                    self.database.append(DataCell(nick, timestamp))
                else:
                    found = False
                    for cell in self.database:
                        if nick in cell.nick_history:
                            cell.current_nick = nick
                            cell.recent_timestamp = timestamp
                            found = True
                        elif nick == cell.current_nick:
                            cell.recent_timestamp = timestamp
                            found = True
                        if found:
                            if cell.memos != [] and cell.message_light:
                                outgoing.append(cell.current_nick + ": You have memos!")
                                cell.message_light = False
                            break
                    if not found:
                        self.database.append(DataCell(nick, timestamp))
                    self.save()

            if case_nick:
                sys.stderr.write("NICK detected.\n")
                new_nick = data_lower[2].strip(':')
                if self.database == []:
                    self.database.append(DataCell(new_nick, timestamp))
                else:
                    found = False
                    for cell in self.database:
                        if nick == cell.current_nick:
                            cell.current_nick = new_nick
                            if not (nick in cell.nick_history):
                                cell.nick_history.append(nick)
                            cell.recent_timestamp = timestamp
                            found = True
                        elif nick in cell.nick_history:
                            cell.current_nick = new_nick
                            cell.recent_timestamp = timestamp
                            found = True
                        elif new_nick == cell.current_nick:
                            cell.recent_timestamp = timestamp
                            if not (nick in cell.nick_history):
                                cell.nick_history.append(nick)
                            found = True
                        elif new_nick in cell.nick_history:
                            cell.current_nick = new_nick
                            cell.recent_timestamp = timestamp
                            found = True
                        if found:
                            if cell.memos != [] and cell.message_light:
                                outgoing.append(cell.current_nick + ": You have memos!")
                                cell.message_light = False
                           
                            repeat = True
                            while repeat:
                                repeat = False
                                for i in range(len(self.database)):
                                    if self.database[i].recent_timestamp == timestamp:
                                        continue
                                    if (self.database[i].current_nick == cell.current_nick) or \
                                        (cell.current_nick in self.database[i].nick_history) or \
                                        (self.database[i].current_nick in cell.nick_history):
                                        for nickname in self.database[i].nick_history:
                                            if not (nickname in cell.nick_history):
                                                cell.nick_history.append(nickname)
                                        self.database.pop(i)
                                        repeat = True
                                        break

                            break
                    if not found:
                        self.database.append(DataCell(new_nick, timestamp))
                self.save()

            if case_privmsg:
                if len(data_lower) >= 4:
                    if data_lower[3] == ":!seen":
                        if len(data_lower) == 4:
                            outgoing.append("'!seen' requires a target. (!seen <TARGET>)")
                            return outgoing
                        query = data_lower[4]
                        if query == botnick.lower():
                            outgoing.append("Last seen " + query + " on " + timestamp + ", when looking at the mirror.")
                            return outgoing
                        for cell in self.database:
                            if (cell.current_nick == query) or (query in cell.nick_history):
                                outgoing.append("Last seen " + query + " on " + cell.recent_timestamp + ", as " + cell.current_nick)
                                return outgoing
                        outgoing.append("I have not seen " + query + " yet.")
                        return outgoing
                    elif data_lower[3] == ":!tell":
                        if len(data_lower) == 4:
                            outgoing.append("'!tell' requires two arguments. (!tell <TARGET> <MESSAGE>)")
                            return outgoing
                        else:
                            target = data_lower[4]
                            if len(data_lower) == 5:
                                outgoing.append("'!tell' requires two arguments. (!tell <TARGET> <MESSAGE>)")
                                return outgoing
                            else:
                                if target == botnick.lower():
                                    outgoing.append("I cannot receive memos.")
                                    return outgoing
                                for cell in self.database:
                                    if (target == cell.current_nick) or (target in cell.nick_history):
                                        memo = string.join(data_raw[5:]).decode('UTF-8', 'replace')
                                        cell.memos.append((timestamp, nick, memo))
                                        outgoing.append("I will tell them when I next see them.")
                                        cell.message_light = True
                                        self.save()
                                        sys.stderr.write("Added memo to cell " + cell.current_nick + ". see: Seenbot.json.\n")
                                        return outgoing
                                outgoing.append("I have not seen "+target+" yet.")
                                return outgoing
                    elif data_lower[3] == ":!memos":
                        if (nick + ": You have memos!") in outgoing:
                            outgoing.remove(nick + ": You have memos!")
                        for cell in self.database:
                            if nick == cell.current_nick:
                                if cell.memos != []:
                                    pb_api_paste_code = ""
                                    for memo in cell.memos:
                                        msg = memo[0] + " - " + memo[1] + " said to you: " + memo[2] + "\n"
                                        pb_api_paste_code += msg

                                    # this portion will convert memo list to a pastebin post
                                    try:
                                        pasteUrl = self.paste.create(pb_api_paste_code)
                                    except PasteService.CannotConnect as err:
                                        outgoing.append("Please inform the developer that there is an issue with the memos url.")
                                        outgoing.append("Your memos have been kept in the system.")
                                        return outgoing
                                    except PasteService.HttpError as err:
                                        outgoing.append("Please inform the developer that there is an issue with the memos request.")
                                        outgoing.append("Your memos have been kept in the system.")
                                        return outgoing

                                    outgoing.append("Here is a link to your memos:")
                                    outgoing.append(pasteUrl)
                                    cell.memos = []
                                    self.save()
                                    return outgoing
                                else:
                                    outgoing.append(nick + ":You have no memos.")
                                    return outgoing
                    elif "!time" in data_lower[3]:
                        outgoing.append("The time is: " + timestamp)
                        return outgoing
        if outgoing != []:
            return outgoing
        else:
            return None
