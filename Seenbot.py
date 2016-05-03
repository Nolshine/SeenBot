from datetime import datetime
import json
import os.path
import sys
import string
import time
import PasteService

# "person" is a group of nicks
#   TODO: may be "official" with registration
#       official persons cannot be merged with one another accidentally
#       todo: a force merge command
# "nick" is one username
#   has first and last seen
#   has memos associated with it

# TODO: keep history of join/fjoin/move/split 
# TODO: !merge, !split, !move, !forget, !info <nick|gid>

# person is keyed on group id (int)
# nick is keyed on nick (string)

# TODO: better cross network?

class PersonDatabase:
    def __init__(self):
        self.people = { }
        self.nicks = { }
        self.cgid = 0

    @staticmethod
    def fromDict(d):
        pd = PersonDatabase()
        pd.people = { gid: Person.fromDict(d['people'][gid]) for gid in d['people'] }
        pd.nicks = { nick: Nick.fromDict(d['nicks'][nick]) for nick in d['nicks'] }
        pd.cgid = d['cgid']
        return pd

    def getPerson(self, gid):
        if str(gid) not in self.people:
            return None
        return self.people[str(gid)]

    def getNick(self, nick):
        if nick not in self.nicks:
            # create group
            group = Person(self.cgid)
            self.cgid += 1
            self.people[str(group.gid)] = group

            # create nick
            user = Nick(group.gid, nick)
            self.nicks[nick] = user

            # add user to group
            group.nicks += [nick]

        return self.nicks[nick]

    def getGroup(self, nick):
        user = self.getNick(nick)
        return [self.getNick(n) for n in self.people[str(user.gid)].nicks]

    def move(self, nick, gid):
        user = self.getNick(nick)
        if user.gid == gid:
            return
        person = self.getPerson(user.gid)
        person.nicks.remove(nick)

        nperson = self.getPerson(gid)
        nperson.nicks += [nick]
        user.gid = gid

        if len(user.memos) > 0:
            nperson.alert = True

        # if old group has no memos, make sure it doesn't alert
        og = [self.getNick(n) for n in person.nicks]
        totalMemos = reduce(lambda l, r: l + r, [len(o.memos) for o in og], 0)
        if totalMemos == 0:
            person.alert = False

        # if the old group is now empty, delete it
        if len(person.nicks) < 1:
            self.people.pop(str(person.gid), None)

class Person:
    def __init__(self, gid):
        self.gid = gid
        self.nicks = []
        self.official = False
        self.alert = False

    @staticmethod
    def fromDict(d):
        p = Person(d['gid'])
        p.nicks = d['nicks']
        p.official = d['official']
        p.alert = d['alert']
        return p

class Nick:
    def __init__(self, gid, nick):
        self.gid = gid
        self.nick = nick
        self.firstSeen = 0
        self.lastSeen = 0
        self.memos = []

    @staticmethod
    def fromDict(d):
        n = Nick(d['gid'], d['nick'])
        n.firstSeen = d['firstSeen']
        n.lastSeen = d['lastSeen']
        n.memos = [Memo.fromDict(m) for m in d['memos']]
        return n

class Memo:
    def __init__(self, network, when, where, who, to, what):
        self.network = network
        self.when = when
        self.where = where
        self.who = who
        self.to = to
        self.what = what

    @staticmethod
    def fromDict(d):
        m = Memo(d['network'], d['when'], d['where'], d['who'], d['to'], d['what'])
        return m

def formatTimestamp(ts):
    return datetime.fromtimestamp(ts).strftime("%c") + " UTC"

class Seenbot(object):
    """handles storing and tracking 'last seen' data of users in the channel."""

    def __init__(self, botnick, paste, filename = "SolSeer.json"):
        self.botnick = botnick
        self.paste = paste
        self.database = PersonDatabase()
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
        self.database = PersonDatabase.fromDict(o['database'])
        sys.stderr.write(self.toJson() + "\n")

    def process(self, network, raw):
        data_raw = raw.split() # for rickrolling!
        data_lower = raw.lower().split()
        case = None
        nick = data_lower[0].strip(':').split('!')[0]
        outgoing = []

        if nick == self.botnick:
            sys.stderr.write("ignoring own actions.")
            return None

        user = self.database.getNick(nick)
        if user.firstSeen == 0:
            user.firstSeen = time.time()
        user.lastSeen = time.time()

        if len(data_lower) > 1:
            case = data_lower[1]
        if case == None:
            return None

        if case == 'nick':
            outgoing += self.handleNick(network, nick, data_raw, data_lower)

        if case == 'privmsg':
            outgoing += self.handlePRIVMSG(network, nick, data_raw, data_lower)

        # if the person has memos, let them know
        person = self.database.getPerson(user.gid)
        if person.alert:
            person.alert = False
            outgoing += [nick + ": You have memos!"]

        self.save()

        if outgoing != []:
            return outgoing
        else:
            return None

    def handleNick(self, network, nick, data_raw, data_lower):
        sys.stderr.write("NICK detected.\n")

        new_nick = data_lower[2].strip(':')

        # round up both nicks and groups
        user = self.database.getNick(nick)
        user.lastSeen = time.time()

        nuser = self.database.getNick(new_nick)
        if nuser.firstSeen == 0:
            nuser.firstSeen = time.time()
        nuser.lastSeen = time.time()

        lhs = self.database.getPerson(user.gid)
        rhs = self.database.getPerson(nuser.gid)

        # if they're already the same group, do nothing
        if lhs.gid == rhs.gid:
            return []

        # if they're both "official", abort
        if lhs.official and rhs.official:
            sys.stderr.write(
                "Refusing to merge %s (%s) and %s (%s): both official\n"
                    % (user.nick, lhs.gid, nuser.nick, rhs.gid)
            )
            return []

        # if lhs is the official one, merge rhs into lhs instead
        if lhs.official:
            lhs, rhs = rhs, lhs

        # move everybody from old group to new group
        for nick in lhs.nicks:
            self.database.move(nick, rhs.gid)

        return []

    def handlePRIVMSG(self, network, nick, data_raw, data_lower):
        sys.stderr.write("PRIVMSG detected.\n")
        outgoing = []
        if len(data_lower) < 4:
            return outgoing
        if data_lower[3] == ":!seen":
            return self.handleSeenCommand(network, nick, data_raw, data_lower)
        elif data_lower[3] == ":!tell":
            return self.handleTellCommand(network, nick, data_raw, data_lower)
        elif data_lower[3] == ":!memos":
            return self.handleMemosCommand(network, nick, data_raw, data_lower)
        elif "!time" in data_lower[3]:
            return self.handleTimeCommand(network, nick, data_raw, data_lower)
        elif data_lower[3] == ":!aliases":
            return self.handleAliasesCommand(network, nick, data_raw, data_lower)
        return []

    def handleSeenCommand(self, network, nick, data_raw, data_lower):
        if len(data_lower) == 4:
            return ["'!seen' requires a target. (!seen <TARGET>)"]
        query = data_lower[4]
        if query == self.botnick.lower():
            return ["Last seen %s on %s, when looking at the mirror."
                    % (query, formatTimestamp(time.time()))]

        user = self.database.getNick(query)

        group = self.database.getGroup(query)
        lastSeen = reduce(lambda l, r: l if l.lastSeen > r.lastSeen else r,
                group, group[0])

        if lastSeen.lastSeen == 0:
            return ["I have not seen " + query + " yet."]
        return ["Last seen %s on %s, as %s"
                % (query, formatTimestamp(lastSeen.lastSeen), lastSeen.nick)]

    def handleTellCommand(self, network, nick, data_raw, data_lower):
        if len(data_lower) < 6:
            return ["'!tell' requires two arguments. (!tell <TARGET> <MESSAGE>)"]

        where = data_raw[2]

        target = data_lower[4]
        if target == self.botnick.lower():
            return ["I cannot receive memos."]

        memo = string.join(data_raw[5:]).decode('UTF-8', 'replace')

        tuser = self.database.getNick(target)
        tuser.memos.append(Memo(network, time.time(), where, nick, target, memo))

        person = self.database.getPerson(tuser.gid)
        person.alert = True

        sys.stderr.write("Added memo to cell " + target + ". see: Seenbot.json.\n")
        return ["I will tell them when I next see them."]

    def handleMemosCommand(self, network, nick, data_raw, data_lower):
        user = self.database.getNick(nick)
        person = self.database.getPerson(user.gid)
        group = self.database.getGroup(nick)

        memos = []
        for n in group:
            memos += n.memos

        if len(memos) == 0:
            return [nick + ": You have no memos."]

        pb_api_paste_code = ""
        for memo in memos:
            msg = "%s - %s said to you: %s\n" \
                % (formatTimestamp(memo.when), memo.who, memo.what)
            pb_api_paste_code += msg

        # this portion will convert memo list to a pastebin post
        try:
            pasteUrl = self.paste.create(pb_api_paste_code)
        except PasteService.CannotConnect as err:
            return [
                "Please inform the developer that there is an issue with the memos url.",
                "Your memos have been kept in the system."
            ]
        except PasteService.HttpError as err:
            return [
                "Please inform the developer that there is an issue with the memos request.",
                "Your memos have been kept in the system."
            ]

        # clear memos/alert light
        for n in group:
            n.memos = []
        person.alert = False

        return ["Here is a link to your memos:", pasteUrl]

    def handleTimeCommand(self, network, nick, data_raw, data_lower):
        return ["The time is: " + formatTimestamp(time.time())]

    def handleAliasesCommand(self, network, nick, data_raw, data_lower):
        if len(data_lower) == 4:
            return ["'!aliases' requires a nick. (!seen <NICK>)"]

        query = data_lower[4]
        if query == self.botnick.lower():
            return ["If I tell you, I'll have to kill you."]

        user = self.database.getNick(query)
        person = self.database.getPerson(user.gid)
        aliases = list(person.nicks)
        aliases.remove(query)

        if len(aliases) == 0:
            return ["%s has no known aliases" % query]
        return ["%s is also known as: %s" % (query, ", ".join(aliases))]

