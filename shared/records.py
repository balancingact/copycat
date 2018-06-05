"""Class declarations for Records of type NS, A, and PTR."""


class NS:
    """
    Class for handling and containing individual NS records.

    @type   name:       string
    @ivar   name:       The name of the NS record (i.e. 'byu.edu')
    @type   ip:         string
    @ivar   ip:         IP address of the NS record (i.e. '192.168.0.2')
    @type   disabled:   int (0 or 1)
    @ivar   disabled:   Whether (0) or not (1) the record is enabled.
    """

    # Variables
    name = ""
    ip = ""
    disabled = 0

    # Constructor
    def __init__(self, params):
        """
        Initialize NS record object.

        @type   params: dict
        @param  params: Dict contain the key 'string' paired with an NS object string
                        (i.e. 'server=/byu.edu/192.168.21.78') or the keys 'name', 'ip', and 'disabled' paired
                        with their appropriate values
        """
        if 'string' in params:
            if params['string'][0] == '#':
                self.disabled = 1
            else:
                self.disabled = 0
            params = params['string'].split("/")
            self.name = params[1]
            self.ip = params[2]
        else:
            self.name = params['name']
            self.ip = params['ip']
            self.disabled = int(params['disabled'])

    # Getters and Setters
    def getName(self):
        """Return record name."""
        return self.name

    def getIp(self):
        """Return record IP."""
        return self.ip

    def getDisabled(self):
        """Return disabled boolean."""
        return self.disabled

    def setName(self, name):
        """Set record name."""
        self.name = name

    def setIp(self, ip):
        """Set record IP."""
        self.ip = ip

    def setDisabled(self, disabled):
        """Set disabled boolean."""
        self.disabled = int(disabled)

    # toString
    def __str__(self):
        """Return pretty string of record information."""
        ret = "server=/" + self.name + "/" + self.ip
        if self.disabled:
            ret = "#" + ret
        return ret

    # Comparrison
    def __eq__(self, ns2):
        """Return record 'is equal to' boolean."""
        if (isinstance(ns2, NS)):
            return self.name == ns2.getName() and self.ip == ns2.getIp() and self.disabled == ns2.getDisabled()
        else:
            return False

    def __lt__(self, ns2):
        """Return record 'is less than' boolean."""
        if isinstance(ns2, NS):
            selfTuple = tuple(int(part) for part in self.getIp().split('.'))
            compTuple = tuple(int(part) for part in ns2.getIp().split('.'))
            return selfTuple < compTuple
        else:
            return False

    # Hash
    def __hash__(self):
        """Return hash representation of record."""
        i = 0
        for d in self.ip.split("."):
            i += int(d)
        return i


class A:
    """
    Class for handling and containing individual A records.

    @type   subdomain:  string
    @ivar   subdomain:  Subdomain of the A record (i.e. 'byub-test')
    @type   addr:       string
    @ivar   addr:       The address of the A record (i.e. 'byub-test.byu.edu')
    @type   ip:         string
    @ivar   ip:         IP address of the NS record (i.e. '192.168.0.2')
    @type   disabled:   int (0 or 1)
    @ivar   disabled:   Whether (0) or not (1) the record is enabled.
    """

    # Variables
    subdomain = ""
    addr = ""
    ip = ""
    disabled = 0

    # Constructor
    def __init__(self, params):
        """
        Initialize A record object.

        @type   params: dict
        @param  params: Dict contain the key 'string' paired with an A object string
                        (i.e. 'host-record=byub-test,byub-test.byu.edu,192.168.0.2') or the keys 'addr', 'ip',
                        and 'disabled' paired with their appropriate values
        """
        if 'string' in params:
            if params['string'][0] == '#':
                self.disabled = 1
            else:
                self.disabled = 0
            params = params['string'].split("=")[1].split(",")
            if len(params) == 3:
                self.subdomain = params[0]
                self.addr = params[1]
                self.ip = params[2]
            else:
                self.subdomain = ""
                self.addr = params[0]
                self.ip = params[1]
        else:
            self.addr = params['addr']
            self.ip = params['ip']
            self.subdomain = ".".join(self.addr.split(".")[:-2])
            self.disabled = int(params['disabled'])

    # Getters and Setters
    def getSubdomain(self):
        """Return record subdomain."""
        return self.subdomain

    def getAddr(self):
        """Return record address."""
        return self.addr

    def getIp(self):
        """Return record IP."""
        return self.ip

    def getDisabled(self):
        """Return disabled boolean."""
        return self.disabled

    def setAddr(self, addr):
        """Set record address."""
        self.subdomain = ".".join(addr.split(".")[:-2])
        self.addr = addr

    def setIp(self, ip):
        """Set record IP."""
        self.ip = ip

    def setDisabled(self, disabled):
        """Set disabled boolean."""
        self.disabled = int(disabled)

    # toString
    def __str__(self):
        """Return pretty string of record information."""
        ret = "host-record="
        if self.subdomain:
            ret += self.subdomain + ","
        ret += self.addr + "," + self.ip
        if self.disabled:
            ret = "#" + ret
        return ret

    # Comparrison
    def __eq__(self, a2):
        """Return record 'is equal to' boolean."""
        if (isinstance(a2, A)):
            return self.addr == a2.getAddr() and self.ip == a2.getIp() and self.disabled == a2.getDisabled()
        else:
            return False

    def __lt__(self, a2):
        """Return record 'less than' boolean."""
        if isinstance(a2, A):
            selfTuple = tuple(int(part) for part in self.getIp().split('.'))
            compTuple = tuple(int(part) for part in a2.getIp().split('.'))
            return selfTuple < compTuple
        else:
            return False

    # Hash
    def __hash__(self):
        """Return hash representation of record."""
        i = 0
        for d in self.ip.split("."):
            i += int(d)
        return i


class PTR:
    """
    Class for handling and containing individual PTR records.

    @type   addr:       string
    @ivar   addr:       The address of the PTR record (i.e. 'byub-test')
    @type   ip:         string
    @ivar   ip:         IP address of the PTR record (i.e. '2.0.168.192.in-addr.arpa)
    @type   disabled:   int (0 or 1)
    @ivar   disabled:   Whether (0) or not (1) the record is enabled.
    """

    # Variables
    addr = ""
    ip = ""
    disabled = 0

    # Constructor
    def __init__(self, params):
        """
        Initialize PTR record object.

        @type   params: dict
        @param  params: Dict contain the key 'string' paired with a PTR object string
                        (i.e. 'ptr-record=/2.0.168.192.in-addr.arpa,"byub-test"') or the keys 'addr', 'ip', and
                        'disabled' paired with their appropriate values
        """
        if 'string' in params:
            if params['string'][0] == '#':
                self.disabled = 1
            else:
                self.disabled = 0
            params = params['string'].split("=")[1].split(",")
            self.ip = params[0]
            self.addr = params[1].replace("\"", "")
        else:
            self.addr = params['addr']
            self.ip = params['ip']
            self.disabled = int(params['disabled'])

    # Getters and Setters
    def getAddr(self):
        """Return record address."""
        return self.addr

    def getIp(self):
        """Return record IP."""
        return self.ip

    def getDisabled(self):
        """Return disabled boolean."""
        return self.disabled

    def setAddr(self, addr):
        """Set record address."""
        self.addr = addr

    def setIp(self, ip):
        """Set record IP."""
        self.ip = ip

    def setDisabled(self, disabled):
        """Set disabled boolean."""
        self.disabled = int(disabled)

    # toString
    def __str__(self):
        """Return pretty string of record information."""
        ret = "ptr-record=" + self.ip + ",\"" + self.addr + "\""
        if self.disabled:
            ret = "#" + ret
        return ret

    # Comparrison
    def __eq__(self, ptr2):
        """Return record 'is equal to' boolean."""
        if (isinstance(ptr2, PTR)):
            return self.addr == ptr2.getAddr() and self.ip == ptr2.getIp() and self.disabled == ptr2.getDisabled()
        else:
            return False

    def __lt__(self, ptr2):
        """Return record 'less than' boolean."""
        if isinstance(ptr2, PTR):
            selfTuple = self.getIp().split('.')[:4]
            selfTuple.reverse()
            selfTuple = tuple(int(part) for part in selfTuple)
            compTuple = self.getIp().split('.')[:4]
            compTuple.reverse()
            compTuple = tuple(int(part) for part in compTuple)
            return selfTuple < compTuple
        else:
            return False

    # Hash
    def __hash__(self):
        """Return hash representation of record."""
        i = 0
        for d in self.ip.split("."):
            try:
                i += int(d)
            except:
                break
        return i


if __name__ == '__main__':
    print "Nothing to see here..."
    exit(0)
