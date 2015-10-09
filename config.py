import os.path

class Config:
    def __init__(self, filename=None):
        self.network = "esper"
        self.nick = "porygit"
        self.channel = "#3dpe"
        self.debug = True
        if not (filename is None):
            self.load(filename)
    def load(self, filename):
        if os.path.isfile(filename):
            with open(filename, "r") as f:
                for line in f.readlines():
                    fs = line.split()
                    if len(fs) != 2:
                        sys.stderr.write("unkown config line: '%s'" % line)
                        continue
                    if fs[0] == "debug":
                        self.debug = (fs[1] == "True")
                    self.__dict__[fs[0]] = fs[1]
        else:
            raise Exception("file not found: " + filename)

