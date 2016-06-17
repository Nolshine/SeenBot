
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

