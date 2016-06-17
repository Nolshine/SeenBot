from Memo import Memo

# "person" is a group of nicks (NickGroup)
#   TODO: may be "official" with registration
#       official persons cannot be merged with one another accidentally
#       TODO: a force merge command
# "nick" is one username (Nick)
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
        pd.people = { gid: NickGroup.fromDict(d['people'][gid]) for gid in d['people'] }
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
            group = NickGroup(self.cgid)
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

class NickGroup:
    def __init__(self, gid):
        self.gid = gid
        self.nicks = []
        self.official = False
        self.alert = False

    @staticmethod
    def fromDict(d):
        p = NickGroup(d['gid'])
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

