"""Module for Filter class."""

import json
from records import A, NS, PTR


class Filter():
    """
    Class for handling and containing filter information.

    @type   fl:     dict
    @ivar   fl:     The filter information
    """

    filt = {}

    def __init__(self, fl):
        """Initialize filter."""
        self.filt = fl

    def isUsed(self, agent):
        """Check if given agent uses this filter."""
        return agent in self.filt['agents']

    def getInfo(self):
        """Return filter information."""
        return self.filt

    def shouldAddString(self, record):
        """Check if record should be added from a given string representation of the record."""
        if record[0] == 's' or record[1] == 's':
            rec = NS({'string': record})
            return self.shouldAdd(rec.getName(), rec.getIp())
        elif record[0] == 'h' or record[1] == 'h':
            rec = A({'string': record})
            return self.shouldAdd(rec.getAddr(), rec.getIp())
        elif record[0] == 'p' or record[1] == 'p':
            rec = PTR({'string': record})
            return self.shouldAdd(rec.getAddr(), rec.getIp())

    def shouldAddRecord(self, record):
        """Check if record should be added."""
        if isinstance(record, NS):
            return self.shouldAdd(record.getName(), record.getIp())
        else:
            return self.shouldAdd(record.getAddr(), record.getIp())

    def shouldAdd(self, name, ip):
        """Check if record should be added by given name and ip."""
        if 'trigger' in self.filt:
            if self.filt['trigger'] == name:
                if 'condition' in self.filt:
                    if 'ip' in self.filt['condition']:
                        cond = self.filt['condition']['ip']
                        if '*' in cond:
                            return ip[:len(cond)-1] == cond[:len(cond)-1]
                        else:
                            return cond == ip
                else:
                    return False
            else:
                return True

    def __str__(self):
        """Return string representation of the filter."""
        return json.dumps(self.filt, indent=4)
