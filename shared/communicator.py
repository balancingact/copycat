#!/usr/bin/python
"""Communication methods for using and editing records data."""

from __future__ import generators
import os
import sys
import pymysql
import records
import traceback
from datetime import datetime, timedelta
from sortedcontainers import SortedSet


def ResultIter(cursor, arraysize=5000000):
    """
    Read database in chunks.

    @type   cursor: pymyslq.connect().cursor()
    @param  cursor: PyMySQL cursor
    @type   arraysize:  int
    @param  arraysize:  Size of each db fetch chunk
    @return Yeilds each record
    """
    while True:
        results = cursor.fetchmany(arraysize)
        if not results:
            break
        for result in results:
            yield result


def dbToFile(params, ns_file, a_file, ptr_file, log):
    """
    Read DB and dumps directly to the given conf files.

    @type   params:     dict
    @param  params:     DB connection parameters. Dict of style: {
                            'host': '',
                            'port': -1,
                            'user': '',
                            'password': '',
                            'db': ''
                        }
    @type   ns_file:    string
    @param  ns_file:    Address of the NS record's conf file
    """
    conn = pymysql.connect(
        host=params['host'],
        port=params['port'],
        user=params['user'],
        password=params['password'],
        db=params['db']
    )
    cur = conn.cursor()

    cur.execute("SELECT * FROM records")

    # Remove old conf files
    try:
        os.remove(ns_file)
    except:
        log.warning("NS file (" + ns_file + ") has already been deleted.")
    try:
        os.remove(a_file)
    except:
        log.warning("A file (" + a_file + ") has already been deleted.")
    try:
        os.remove(ptr_file)
    except:
        log.warning("PTR file (" + ptr_file + ") has already been deleted.")

    # Recreate conf files
    ns_f = open(ns_file, 'a')
    a_f = open(a_file, 'a')
    ptr_f = open(ptr_file, 'a')

    # Write the headers
    ns_f.write("######### NS Records #########\n\n")
    a_f.write("######### A Records #########\n\n")
    ptr_f.write("######### PTR Records #########\n\n")

    # Close the files
    ns_f.close()
    a_f.close()
    ptr_f.close()

    temp = None
    try:
        # Loop through records and write each record to the corresponding conf file
        for record in cur:
            temp = record
            if record[3] == "NS":
                if 'storage.byu.edu' not in record[2]:
                    continue
                temp = records.NS({'name': record[2], 'ip': record[4], 'disabled': record[8]})
                addToFile([temp], ns_file, {}, log)
            elif record[3] == "A":
                temp = records.A({'addr': record[2], 'ip': record[4], 'disabled': record[8]})
                addToFile([temp], a_file, {}, log)
            elif record[3] == "PTR":
                temp = records.PTR({'ip': record[2], 'addr': record[4], 'disabled': record[8]})
                addToFile([temp], ptr_file, {}, log)
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
        error = ''.join('!! ' + line for line in lines)
        raise RuntimeError(
            "Database dump to file failed\n" + error + "\n\nFailed for the following record:\n" + temp.__str__()
            + "\nOnce this is fixed restart the service with 'systemctl start copycat-master'"
        )

    cur.close()
    conn.close()


def fromDB(params, full):
    """
    Retrieve records from database.

    @type   params:     dict
    @param  params:     DB connection parameters. Dict of style: {
                            'host': '',
                            'port': -1,
                            'user': '',
                            'password': '',
                            'db': ''
                        }
    @type   full:       boolean
    @param  full:       Whether to retrieve latest records or all records

    @return Dict containing retrieved records of style: {
        'ns_records': SortedSet([records.NS]),
        'a_records': SortedSet([records.A]),
        'ptr_records': SortedSet([records.PTR])
    }
    """
    ns_records = SortedSet([])
    a_records = SortedSet([])
    ptr_records = SortedSet([])

    conn = pymysql.connect(
        host=params['host'],
        port=params['port'],
        user=params['user'],
        password=params['password'],
        db=params['db']
    )
    cur = conn.cursor()

    if full:
        cur.execute("SELECT * FROM records")
    else:
        cur.execute("SELECT * FROM records WHERE change_date >= " + (
            datetime.now() - timedelta(days=1)).strftime("%Y%m%d") + "00"
        )

    row = None
    try:
        for record in ResultIter(cur):
            row = record
            if record[3] == "NS":
                if 'storage.byu.edu' not in record[2]:
                    continue
                temp = records.NS({'name': record[2], 'ip': record[4], 'disabled': record[8]})
                ns_records.add(temp)
            elif record[3] == "A":
                temp = records.A({'addr': record[2], 'ip': record[4], 'disabled': record[8]})
                a_records.add(temp)
            elif record[3] == "PTR":
                temp = records.PTR({'ip': record[2], 'addr': record[4], 'disabled': record[8]})
                ptr_records.add(temp)
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
        error = ''.join('!! ' + line for line in lines)
        raise RuntimeError(
            "Database retrieval failed\n" + error + "\n\nFailed for the following record:\n" + printRecord(row)
            + "\nOnce this is fixed restart the service with 'systemctl start copycat-master'"
        )

    cur.close()
    conn.close()

    return {'ns_records': ns_records, 'a_records': a_records, 'ptr_records': ptr_records}


def fromDBdeletes(params, log):
    """
    Retrieve records from database that have been deleted (found in records_remove table).

    Also truncates the table after records have been retrieved.

    @type   params:     dict
    @param  params:     DB connection parameters. Dict of style: {
                            'host': '',
                            'port': -1,
                            'user': '',
                            'password': '',
                            'db': ''
                        }

    @return Dict containing retrieved records of style: {
        'ns_records': SortedSet([records.NS]),
        'a_records': SortedSet([records.A]),
        'ptr_records': SortedSet([records.PTR])
    }
    """
    ns_records = SortedSet([])
    a_records = SortedSet([])
    ptr_records = SortedSet([])

    conn = pymysql.connect(
        host=params['host'],
        port=params['port'],
        user=params['user'],
        password=params['password'],
        db=params['db']
    )
    cur = conn.cursor()

    cur.execute("SELECT * FROM records_remove")

    for record in ResultIter(cur):
        try:
            if record[3] == "NS":
                temp = records.NS({'name': record[2], 'ip': record[4], 'disabled': record[8]})
                ns_records.add(temp)
            elif record[3] == "A":
                temp = records.A({'addr': record[2], 'ip': record[4], 'disabled': record[8]})
                a_records.add(temp)
            elif record[3] == "PTR":
                temp = records.PTR({'ip': record[2], 'addr': record[4], 'disabled': record[8]})
                ptr_records.add(temp)
        except:
            log.warning("Could not properly evaluate the following record:")
            log.warning(record)
            continue

    # Delete records after retrieved
    cur.execute("TRUNCATE records_remove")

    cur.close()
    conn.close()

    return {'ns_records': ns_records, 'a_records': a_records, 'ptr_records': ptr_records}


def fromDBadds(params, log):
    """
    Retrieve records from database that have been deleted (found in records_add table).

    Also truncates the table after records have been retrieved.

    @type   params:     dict
    @param  params:     DB connection parameters. Dict of style: {
                            'host': '',
                            'port': -1,
                            'user': '',
                            'password': '',
                            'db': ''
                        }

    @return Dict containing retrieved records of style: {
        'ns_records': SortedSet([records.NS]),
        'a_records': SortedSet([records.A]),
        'ptr_records': SortedSet([records.PTR])
    }
    """
    ns_records = SortedSet([])
    a_records = SortedSet([])
    ptr_records = SortedSet([])

    conn = pymysql.connect(
        host=params['host'],
        port=params['port'],
        user=params['user'],
        password=params['password'],
        db=params['db']
    )
    cur = conn.cursor()

    cur.execute("SELECT * FROM records_add")

    for record in ResultIter(cur):
        try:
            if record[3] == "NS":
                temp = records.NS({'name': record[2], 'ip': record[4], 'disabled': record[8]})
                ns_records.add(temp)
            elif record[3] == "A":
                temp = records.A({'addr': record[2], 'ip': record[4], 'disabled': record[8]})
                a_records.add(temp)
            elif record[3] == "PTR":
                temp = records.PTR({'ip': record[2], 'addr': record[4], 'disabled': record[8]})
                ptr_records.add(temp)
        except:
            log.warning("Could not properly evaluate the following record:")
            log.warning(record)
            continue

    # Delete records after retrieved
    cur.execute("TRUNCATE records_add")

    cur.close()
    conn.close()

    return {'ns_records': ns_records, 'a_records': a_records, 'ptr_records': ptr_records}


def fromJSON(reqJSON, log):
    """
    Convert JSON dict to dict of records objects.

    @type   reqJSON:    JSON dict (must contain key of 'ns_records', 'a_records', or 'ptr_records')
    @param  reqJSON:    JSON to be converted
    @type   log:        logger
    @param  log:        Logger object for logging

    @return Dict containing retrieved records of style: {
        'ns_records': SortedSet([records.NS]),
        'a_records': SortedSet([records.A]),
        'ptr_records': SortedSet([records.PTR])
    }
    """
    ns_records = SortedSet([])
    a_records = SortedSet([])
    ptr_records = SortedSet([])

    if 'ns_records' in reqJSON:
        log.debug(reqJSON['ns_records'])
        for ns in reqJSON['ns_records']:
            ns_records.add(records.NS({'name': ns['name'], 'ip': ns['ip'], 'disabled': ns['disabled']}))
    if 'a_records' in reqJSON:
        log.debug(reqJSON['a_records'])
        for a in reqJSON['a_records']:
            a_records.add(records.A({'addr': a['addr'], 'ip': a['ip'], 'disabled': a['disabled']}))
    if 'ptr_records' in reqJSON:
        log.debug(reqJSON['ptr_records'])
        for p in reqJSON['ptr_records']:
            ptr_records.add(records.PTR({'ip': p['ip'], 'addr': p['addr'], 'disabled': p['disabled']}))

    return {'ns_records': ns_records, 'a_records': a_records, 'ptr_records': ptr_records}

def fromJSONset(reqJSON, recordType, log):
    """
    Converts JSON set to set of records objects.

    @type   reqJSON:    JSON set
    @param  reqJSON:    JSON to be converted
    @type   recordType: string
    @param  recordType: Type of records to convert (must be "NS", "A", or "PTR")
    @type   log:        logger
    @param  log:        Logger object for logging

    @return Dict containing retrieved records of style: {'ns_records': SortedSet([records.NS]), 'a_records': SortedSet([records.A]), 'ptr_records': SortedSet([records.PTR])}
    """
    ret = SortedSet([])
    for rec in reqJSON:
        if recordType == "NS":
            ret.add(records.NS({'name': rec['name'], 'ip': rec['ip'], 'disabled': rec['disabled']}))
        elif recordType == "A":
            ret.add(records.A({'addr': rec['addr'], 'ip': rec['ip'], 'disabled': rec['disabled']}))
        elif recordType == "PTR":
            ret.add(records.PTR({'ip': rec['ip'], 'addr': rec['addr'], 'disabled': rec['disabled']}))
    return ret

def sendFromFile(fl):
    """
    Yields each record from the given conf file.

    @type   fl: string
    @param  fl: Address of conf file to read.

    @return Yields each record entry from conf file
    """
    with open(fl, 'r') as f:
        headers = False
        for line in f.readlines():
            if not headers: # Skip headers
                headers = True
                continue
            if line != '' and line != '\n': # Skip empty lines
                yield line.strip()

def receiveFromFile(fl, records, filters):
    """
    Append list of record strings to the end of the given conf file.

    @type   fl:         string
    @param  fl:         Address of conf file to read.
    @type   records:    list
    @param  records:    List of record strings. Strings are created from a record object's __str__() method
    @type   filters:    list
    @param  filters:    List of Filter objects to compare records against
    """
    with open(fl, 'a') as f:
        for r in records:
            should_add = True
            for filt in filters:
                if not filters[filt].shouldAddString(r):
                    should_add = False
            if should_add:
                f.write(r + '\n')

def deleteFromFile(rec, fl, log):
    """
    Delete list of record objects to the given conf file.

    @type   rec:    list
    @param  rec:    List of record objects to be removed
    @type   fl:     string
    @param  fl:     Address of conf file to read.
    @type   log:    logger
    @param  log:    Logger object for logging
    """
    f = open(fl, 'r')
    current = f.readlines()
    f.close()

    for r in rec:
        try:
            current.remove(r.__str__() + '\n')
        except:
            log.warning(r.__str__() + " not found in file.")
            continue

    with open(fl, 'w') as f:
        for line in current:
            f.write(line)

def addToFile(rec, fl, filters, log):
    """
    Write list of record objects to the given conf file in sorted order.

    @type   rec:    list
    @param  rec:    List of record objects to be added
    @type   fl:     string
    @param  fl:     Address of conf file to read.
    @type   log:    logger
    @param  log:    Logger object for logging
    """

    # Retrieve all lines from file
    f = open(fl, 'r')
    current = f.readlines()
    f.close()

    with open(fl, 'w') as f:
        i = 0
        fl_class = rec[i].__class__.__name__
        headers = False
        for line in current:
            if not headers: # Rewrite the headers
                f.write(line)
                headers = True
                continue

            if i < len(rec) and line != '' and line != '\n': # Skip for empty lines and if there are no more records
                should_add = True
                for filt in filters:
                    if not filters[filt].shouldAddRecord(rec[i]):
                        should_add = False
                if should_add:
                    # recIpTuple = []
                    # lineIpTuple = []
                    #
                    # # This all needs fixed!
                    # try:
                    #     # For PTR records - Parse and compare IP address in line to sort by
                    #     recIpTuple = rec[i].getIp().split(".")[:4]
                    #     recIpTuple.reverse()
                    #     recIpTuple = tuple(int(part) for part in recIpTuple)
                    #     lineIpTuple = re.match('.*?=([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)', line).group(1).split(".")
                    #     lineIpTuple.reverse()
                    #     lineIpTuple = tuple(int(part) for part in lineIpTuple)
                    # except:
                    #     # For other records - Parse and compare IP address in line to sort by
                    #     recIpTuple = rec[i].getIp().split(".")
                    #     recIpTuple = tuple(int(part) for part in recIpTuple)
                    #     lineIpTuple = re.match('.*?([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)$', line).group(1).split(".")
                    #     lineIpTuple = tuple(int(part) for part in lineIpTuple)

                    linerec = getRecordFromLine(line, fl_class)

                    # If the record is less than the line than write the record to the file
                    if rec < linerec:
                    #if recIpTuple < lineIpTuple:
                        log.debug("Adding line: " + rec[i].__str__())
                        f.write(rec[i].__str__() + '\n')
                        i += 1

            f.write(line)
        # If all lines have been written but there are remaining records
        while i < len(rec):
            should_add = True
            for filt in filters:
                if not filters[filt].shouldAddRecord(rec[i]):
                    should_add = False
            if should_add:
                f.write(rec[i].__str__() + '\n')
            i += 1

def getRecordFromLine(line, fl_class):
    if fl_class == 'NS':
        return records.NS({'string': line})
    elif fl_class == 'A':
        return records.A({'string': line})
    elif fl_class == 'PTR':
        return records.PTR({'string': line})

def getLineFromFile(lineNumber, fl):
    with open(fl) as fp:
        for i, line in enumerate(fp):
            if i == lineNumber:
                return line.strip()
    return None

def printAllToFile(master, ns_file, a_file, ptr_file):
    """
    Writes a master dict of records to the corresponding conf files.

    @type   master:     dict
    @param  master:     Dict containing records of style: {'ns_records': SortedSet([records.NS]), 'a_records': SortedSet([records.A]), 'ptr_records': SortedSet([records.PTR])}
    @type   ns_file:    string
    @param  ns_file:    Address of the NS record's conf file
    @type   a_file:     string
    @param  a_file:     Address of the A record's conf file
    @type   ptr_file:   string
    @param  ptr_file:   Address of the PTR record's conf file
    """
    with open(ns_file, 'w') as ns:
        ns.write("######### NS Records #########\n\n")
        if 'ns_records' in master and master['ns_records'] != '':
            for n in master['ns_records']:
                ns.write(n.__str__() + '\n')

    with open(a_file, 'w') as ar:
        ar.write("######### A Records ##########\n\n")
        if 'a_records' in master and master['a_records'] != '':
            for a in master['a_records']:
                ar.write(a.__str__() + '\n')

    with open(ptr_file, 'w') as ptr:
        ptr.write("######### PTR Records ########\n\n")
        if 'ptr_records' in master and master['ptr_records'] != '':
            for p in master['ptr_records']:
                ptr.write(p.__str__() + '\n')

def printAll(master):
    """
    Creates a string of the data in the given master dict of records.
    Used in debugging.

    @type   master: dict
    @param  master: Dict containing records of style: {'ns_records': SortedSet([records.NS]), 'a_records': SortedSet([records.A]), 'ptr_records': SortedSet([records.PTR])}

    @return String of the data in the given master dict of records.
    """

    ret = ""

    if 'ns_records' in master and master['ns_records'] != '':
        ret += "\n######### NS Records #########"
        for n in master['ns_records']:
            ret += n.__str__() + '\n'

    if 'a_records' in master and master['a_records'] != '':
        ret += "\n######### A Records ##########"
        for a in master['a_records']:
            ret += a.__str__() + '\n'

    if 'ptr_records' in master and master['ptr_records'] != '':
        ret += "\n######### PTR Records ########"
        for p in master['ptr_records']:
            ret += p.__str__() + '\n'

    return ret

def printSet(recSet):
    """
    Creates a string of the data in the given set of records
    Used in debugging.

    @type   recSet: list
    @param  recSet: List of record objects

    @return String of the data in the given set of records
    """
    ret = ""
    for rec in recSet:
        ret += rec.__str__() + "\n"

    return ret[:-2]

def logAll(master, log):
    """
    Logs the data in the given master dict of records.
    Used in debugging.

    @type   master: dict
    @param  master: Dict containing records of style: {'ns_records': SortedSet([records.NS]), 'a_records': SortedSet([records.A]), 'ptr_records': SortedSet([records.PTR])}
    @type   log:    logger
    @param  log:    Logger object for logging
    """
    if log.getEffectiveLevel() == 10:
        if 'ns_records' in master and master['ns_records'] != '':
            log.debug("######### NS Records #########")
            for n in master['ns_records']:
                log.debug(n)

        if 'a_records' in master and master['a_records'] != '':
            log.debug("######### A Records ##########")
            for a in master['a_records']:
                log.debug(a)

        if 'ptr_records' in master and master['ptr_records'] != '':
            log.debug("######### PTR Records ########")
            for p in master['ptr_records']:
                log.debug(p)

def logSet(recSet, log, prepend=""):
    """
    Logs the data in the given set of records
    Used in debugging.

    @type   recSet:     list
    @param  recSet:     List of record objects
    @type   log:        logger
    @param  log:        Logger object for logging
    @type   prepend:    string
    @param  prepend:    String to prepend each line with (such as '-' for removing or '+' for adding)
    """
    for rec in recSet:
        log.info(prepend + rec.__str__())

def nsdiff(master, current):
    """
    Finds the differences between the two given dict's ns_records

    @type   master:     dict
    @param  master:     Dict containing the key 'ns_records' paired with a SortedSet of records
    @type   current:    dict
    @param  current:    Dict containing the key 'ns_records' paired with a SortedSet of records

    @return First set - second set, second set - first set
    """
    return master['ns_records'] - current['ns_records'], current['ns_records'] - master['ns_records']
def adiff(master, current):
    """
    Finds the differences between the two given dict's ns_records

    @type   master:     dict
    @param  master:     Dict containing the key 'a_records' paired with a SortedSet of records
    @type   current:    dict
    @param  current:    Dict containing the key 'a_records' paired with a SortedSet of records

    @return First set - second set, second set - first set
    """
    return master['a_records'] - current['a_records'], current['a_records'] - master['a_records']
def ptrdiff(master, current):
    """
    Finds the differences between the two given dict's ns_records

    @type   master:     dict
    @param  master:     Dict containing the key 'ptr_records' paired with a SortedSet of records
    @type   current:    dict
    @param  current:    Dict containing the key 'ptr_records' paired with a SortedSet of records

    @return First set - second set, second set - first set
    """
    return master['ptr_records'] - current['ptr_records'], current['ptr_records'] - master['ptr_records']

def printRecord(record):
    """
    Formats a DB record into an ASCII table for printing out

    @type   record: list
    @param  record: DB record of the powerdns database schema
    """

    # Trim record to contain only id, name, type, content, change_date and disabled
    record = {
        'id': str(record[0]),
        'name': str(record[2]),
        'type': str(record[3]),
        'content': str(record[4]),
        'change_date': str(record[7]),
        'disabled': str(record[8])
    }

    headers = "|"
    div = "+"
    row = "|"

    for k, v in record.iteritems():
        if len(k) > len(v):
            div += fill("", "-", len(k)) + "--+"
            row += " " + fill(v, " ", len(k)) + " |"
            headers += " " + k + " |"
        else:
            div += fill("", "-", len(v)) + "--+"
            row += " " + v + " |"
            headers += " " + fill(k, " ", len(v)) + " |"

    return div + '\n' + headers + '\n' + div + '\n' + row + '\n' + div

def fill(s, c, i):
    """
    Fills the given string with the given character to the given length

    @type   s:  String
    @param  s:  String to append to
    @type   c:  String
    @param  c:  Character to append. (Generally len(c) == 1, but if it doesn't, it won't break anything)
    @type   i:  int
    @param  i:  Final lenght of s
    """
    while len(s) < i:
        s += c
    return s[:i]

if __name__ == '__main__':
    """
    main:
        - Imports all from DB

    Used for testing
    """

    # DB info
    db_params = {
        'host': 'localhost',
        'port': 3306,
        'user': 'python_usr',
        'password': 'python_usr_pass',
        'db': 'powerdns'
    }

    master = fromDB(db_params, True)
