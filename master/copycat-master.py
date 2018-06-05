#!/usr/bin/python
"""Master for the Copycat phpipam/pdns/dnsmasq solution."""

__author__ = "J Lyons"
__copyright__ = "Copyright 2017, BYU Broadcasting"
__credits__ = ["J Lyons"]
__version__ = "3.0.0"

try:
    import re
    import sys
    import time
    import json
    import util
    import emailer
    import urllib2
    import logging
    import traceback
    import communicator
    import logging.handlers
    from os import mkdir
    from time import sleep
    from agent import Agent
    from filters import Filter
    from threading import Thread, Timer, RLock
    from twisted.internet import reactor
    from twisted.web import resource, server
    from ConfigParser import SafeConfigParser
    from signal import signal, SIGTERM, SIGHUP, SIGINT
    from os.path import dirname, realpath, join, isdir, isfile
except ImportError:
    print(('\n' * 2).join([
        "Error importing a module:",
        '\t' + str(sys.exc_info()[1]),
        'Install the module and try again.'
    ]))
    raise SystemExit(1)

# Name of the config file. Must be in the same directory as this script
configFile = 'master.cfg'

# lock for responsible threading
lock = RLock()


class HelloResource(resource.Resource):
    """Class for the Copycat API server."""

    isLeaf = True

    def render_GET(self, request):
        """Handle GET requests."""
        global master, log, key, agents, filters
        if request.path == "/init":  # If a new agent turns on
            # agent_addr = "http://" + request.getClientIP() + ":" + request.args['port'][0]
            a = findAgent(request.args['name'][0])
            log.info("Initializing " + a.getName())

            # Spin off thread to initialize
            t = Thread(target=init_one, args=(a, log,))
            t.daemon = True
            t.start()
            request.responseHeaders.addRawHeader(b"content-type", b"application/json")
            return json.dumps({'success': True})
        elif request.path == '/filters' and request.getClientIP() == "127.0.0.1":
            filters_json = {}
            lock.acquire()
            try:
                for fltr in filters:
                    filters_json[fltr] = filters[fltr].__dict__
            except:
                lock.release()
            request.responseHeaders.addRawHeader(b"content-type", b"application/json")
            request.responseHeaders.addRawHeader(b"Access-Control-Allow-Origin", b"*")
            return json.dumps(filters_json)
        elif request.path == '/agents' and request.getClientIP() == "127.0.0.1":
            agents_json = []
            for agent in agents:
                agents_json.append(agent.getDict())

            request.responseHeaders.addRawHeader(b"content-type", b"application/json")
            request.responseHeaders.addRawHeader(b"Access-Control-Allow-Origin", b"*")
            return json.dumps(agents_json)
        elif request.path == '/test':
            request.responseHeaders.addRawHeader(b"content-type", b"application/json")
            request.responseHeaders.addRawHeader(b"Access-Control-Allow-Origin", b"*")
            return json.dumps({'success': True})
        else:
            request.setResponseCode(501)
            return ""

    def render_POST(self, request):
        """Handle POST requests."""
        global master, log, key, agents, filters, lock
        log.info(request.path)

        reqJSON = json.loads(request.content.getvalue())
        if request.path == "/handshake":  # New agent initializes secret key
            # Retrieve public key
            agent_pub = long(reqJSON['key'])

            # Parse agent address
            agent_addr = request.getClientIP() + ":" + str(reqJSON['port'])

            # Find the agent
            ret = ""
            lock.acquire()
            try:
                for x in range(0, len(agents)):
                    if agents[x].getName() == reqJSON['name']:  # If found
                        if not agents[x]:  # If was dead
                            log.info("Recognized new agent: " + agents[x].getName() + " is now alive.")

                        # Turn on agent and generate secret key
                        agents[x].setStatus(True)
                        agents[x].generateKey(agent_pub)
                        log.debug(agents[x].getKey())
                        ret = agents[x].getPublicKey()
            finally:
                lock.release()

            # If agent was not recognized
            if not ret:
                temp = Agent(agent_addr, reqJSON['name'], True)
                temp.generateKey(agent_pub)
                ret = temp.getPublicKey()
                log.debug(temp.getKey())
                lock.acquire()
                try:
                    agents.append(temp)
                finally:
                    lock.release()
                log.info("Recognized new agent: " + temp.getName() + " is now alive.")

                dumpContent()

            # Return master's public key
            return str(ret)
        elif request.path == "/newagent" and request.getClientIP() == "127.0.0.1":
            a = Agent(reqJSON['ip'] + ":" + reqJSON['port'], reqJSON['name'], True)

            shakeHands(a)

            lock.acquire()
            try:
                agents.append(a)
            finally:
                lock.release()

            if a:
                init_one(a, log)

            dumpContent()
            log.info('Agent \'' + reqJSON['name'] + '\' has been added from web manager.')

            request.setHeader("content-type", "application/json")
            return json.JSONEncoder().encode({'success': True})
        elif request.path == "/delagent" and request.getClientIP() == "127.0.0.1":
            lock.acquire()
            try:
                for x in range(0, len(agents)):
                    if agents[x].getName() == reqJSON['name']:
                        del agents[x]
                        break
            finally:
                lock.release()

            dumpContent()
            log.info('Agent \'' + reqJSON['name'] + '\' has been deleted from web manager.')

            request.setHeader("content-type", "application/json")
            return json.JSONEncoder().encode({'success': True})
        elif request.path == "/newfilter" and request.getClientIP() == "127.0.0.1":
            lock.acquire()
            try:
                filters[reqJSON['name']] = Filter(reqJSON['filt'])
                for agent in agents:
                    if agent and filters[reqJSON['name']].isUsed(agent.getName()):
                        init_one(agent, log)
            finally:
                lock.release()

            dumpContent()
            log.info('Filter \'' + reqJSON['name'] + '\' has been added from web manager.')

            request.setHeader("content-type", "application/json")
            return json.JSONEncoder().encode({'success': True})
        elif request.path == "/delfilter" and request.getClientIP() == "127.0.0.1":
            reloads = []
            for agent in agents:
                lock.acquire()
                try:
                    if agent and filters[reqJSON['name']].isUsed(agent.getName()):
                        reloads.append(agent)
                    else:
                        lock.release()
                finally:
                    lock.release()

            lock.acquire()
            try:
                del filters[reqJSON['name']]
            finally:
                lock.release()

            dumpContent()
            for agent in reloads:
                init_one(agent, log)

            log.info('Filter \'' + reqJSON['name'] + '\' has been deleted from web manager.')

            request.setHeader("content-type", "application/json")
            return json.JSONEncoder().encode({'success': True})
        else:
            request.setResponseCode(501)
            return ""


def dumpContent():
    """Dump agent and filter content to the content file."""
    global log
    log.info("Dumping content.")
    filters_list = {}
    lock.acquire()
    try:
        for filt in filters:
            filters_list[filt] = filters[filt].__dict__['filt']
    finally:
        lock.release()

    agents_list = []
    for agent in agents:
        log.info(agent.getName())
        agents_list.append({'name': agent.getName(), 'addr': agent.getAddr()})

    log.info(json_fl)
    with open(json_fl, 'w') as outfile:
        outfile.write(json.dumps({'filters': filters_list, 'agents': agents_list}, indent=4))
    log.info("Dumping complete.")


def statusCheck():
    """
    Thread for confirming agents are alive.

    Runs every checkInterval (set in conf file).
    """
    global agents
    checker = Timer(checkInterval, statusCheck)
    checker.daemon = True
    checker.start()

    lock.acquire()
    try:
        # For each agent
        for x in range(0, len(agents)):
            try:  # Try to connect
                util.send_get(agents[x].getAddress() + '/alive', '', log)
                if not agents[x]:  # If agent was dead
                    log.info("Recognized new agent: " + agents[x].getName() + " is now alive.")

                    # Spin off thread to initialize
                    t = Thread(target=init_one, args=(agents[x], log,))
                    t.daemon = True
                    t.start()

                agents[x].setStatus(True)
            except:  # If could not connect
                if agents[x]:  # If agent was alive
                    log.warning(agents[x].getName() + " is no longer alive.")
                log.debug("Agent at " + agents[x].getName() + " is not alive.")
                agents[x].setStatus(False)
    finally:
        lock.release()


def handshake():
    """
    Thread for reinitializing secret key with each agent.

    Runs every shakeInterval (set in conf file)
    """
    global agents
    shaker = Timer(60.0*shakeInterval, handshake)
    shaker.daemon = True
    shaker.start()

    lock.acquire()
    try:
        for x in range(0, len(agents)):
            if agents[x]:
                shakeHands(agents[x])
    finally:
        lock.release()


def shakeHands(agent):
    """
    Run handshake.

    @type   agent:  Agent
    @param  agent:  Agent to shake hands with
    """
    try:
        agent.generateNewKey()
        agent.generateKey(util.send_post(agent.getAddress() + '/handshake', agent.getPublicKey(), log))
        log.debug("Handshake complete. New secret key for " + agent.getName())
    except:
        log.warning("Agent at " + agent.getName() + " is no longer alive.")
        agent.setStatus(False)


def findAgent(name):
    """
    Find and agent by address.

    @type   addr:   string
    @param  addr:   The address of the agent to be found (i.e. 'http://127.0.0.1:23456')

    @return:        The agent, if found, else False
    """
    global agents
    for agent in agents:
        log.debug(agent.getName())
        log.debug(name)
        if agent.getName() == name:
            return agent
    return False


def toJSON(master):
    """
    Convert the given dict from lists of records objects to JSON.

    Each records object becomes JSON by returning its native __dict__ value.

    @type   master: dict
    @param  master: The dict of records in the format
                    {'ns_records': [records.NS], 'a_records': [records.A], 'ptr_records': [records.PTR]}

    @return:        The converted JSON
    """
    ret = {}
    if 'ns_records' in master:
        temp = []
        """ NS Records """
        for n in master['ns_records']:
            temp.append(n.__dict__)
        ret['ns_records'] = temp

    if 'a_records' in master:
        temp = []
        """A Records"""
        for a in master['a_records']:
            temp.append(a.__dict__)
        ret['a_records'] = temp

    if 'ptr_records' in master:
        temp = []
        """PTR Records"""
        for p in master['ptr_records']:
            temp.append(p.__dict__)
        ret['ptr_records'] = temp

    return ret


def init_one(agent, log):
    """
    Initialize one newly recognized agent.

    Runs on a thread and sends all records.

    @type   agent:  Agent
    @param  agent:  New agent to initialize
    @type   log:    logger
    @param  log:    Logger object for logging
    """
    # Attempt to connect three times before giving up on the agent.
    tries = 3
    while tries > 0:
        try:
            util.send_post(agent.getAddress() + '/init', util.encode('[]', agent.getKey()), log)
            break
        except:
            # If could not connect, decrement remaining tries and sleep 2 seconds
            tries -= 1
            sleep(2)
            continue

    # Send all the records to the new agent and then reload its DNSMasq
    log.info("Filters with " + agent.getAddress())
    send_filters_one(agent, log)
    log.info("NS with " + agent.getAddress())
    send_records_one(agent, 'ns', ns_file, log)
    log.info("A with " + agent.getAddress())
    send_records_one(agent, 'a', a_file, log)
    log.info("PTR with " + agent.getAddress())
    send_records_one(agent, 'ptr', ptr_file, log)
    log.info("Reloading " + agent.getAddress())
    util.send_post(agent.getAddress() + '/reload', util.encode('[]', agent.getKey()), log)
    log.info("Done with " + agent.getAddress())


def send_records_one(agent, rtype, fl, log):
    """
    Send all of the records of one type from the local file to the given agent.

    @type   agent:  Agent
    @param  agent:  New agent to initialize
    @type   rtype:  string
    @param  rtype:  Defines the records type ('ns', 'a', or 'ptr')
    @type   fl:     string
    @param  fl:     Address of the file
    @type   log:    logger
    @param  log:    Logger object for logging
    """
    ret = []
    for r in communicator.sendFromFile(fl):
        ret.append(r)
        if len(ret) > 1000:  # Send 1000 records at a time
            body = util.encode(json.dumps(ret), agent.getKey())
            util.send_post(agent.getAddress() + '/init/' + rtype, body, log)
            ret = []

    # Send remaining records
    body = util.encode(json.dumps(ret), agent.getKey())
    util.send_post(agent.getAddress() + '/init/' + rtype, body, log)


def send_filters_one(agent, log):
    """
    Send filters to each agent that needs it.

    @type   agent:  Agent
    @param  agent:  Agent to send filters to
    @type   log:    logger
    @param  log:    Logger object for logging
    """
    global agents, filters
    for filt in filters:
        log.debug("Agent -- " + agent.__str__())
        if agent and filters[filt].isUsed(agent.getName()):
            try:
                # Encode the body
                body = util.encode(json.dumps({'code': filt, 'filter': filters[filt].getInfo()}), agent.getKey())
                util.send_post(agent.getAddress() + '/filters', body, log)  # Send the body
            except:
                log.warning("Agent at " + agent.getName() + " is no longer alive.")
                agent.setStatus(False)


def del_filters(agent, filt, log):
    """
    Delete the filter at the given agent.

    @type   agent:  Agent
    @param  agent:  Agent to contact
    @type   filt:   string
    @param  filt:   Name of the filter to be deleted
    @type   log:    logger
    @param  log:    Logger object for logging
    """
    try:
        body = util.encode(json.dumps({'name': filt}), agent.getKey())  # Encode the body
        util.send_post(agent.getAddress() + '/delfilter', body, log)  # Send the body
    except:
        log.warning("Agent at " + agent.getName() + " is no longer alive.")
        agent.setStatus(False)


def send_init(log):
    """
    Send all records to each agent. Runs when master is first turned on.

    @type   log:    logger
    @param  log:    Logger object for logging
    """
    log.info("Init")
    send_post('/init', '[]', log)
    log.info("Filters")
    send_filters(log)
    log.info("NS")
    send_records('ns', ns_file, log)
    log.info("A")
    send_records('a', a_file, log)
    log.info("PTR")
    send_records('ptr', ptr_file, log)
    log.info("Reloading")
    send_post('/reload', '[]', log)
    log.info("Done")


def send_records(rtype, fl, log):
    """
    Send all of the records of one type from the local file to each agent.

    @type   rtype:  string
    @param  rtype:  Defines the records type ('ns', 'a', or 'ptr')
    @type   fl:     string
    @param  fl:     Address of the file
    @type   log:    logger
    @param  log:    Logger object for logging
    """
    ret = []
    for r in communicator.sendFromFile(fl):
        ret.append(r)
        if len(ret) > 1000:  # Sends 1000 records at a time
            send_post('/init/' + rtype, json.dumps(ret), log)
            ret = []

    send_post('/init/' + rtype, json.dumps(ret), log)


def send_filters(log, tag=None):
    """
    Send filters to each agent that needs it.

    @type   log:    logger
    @param  log:    Logger object for logging
    @type   tag:    string
    @param  tag:    None if send all filters, otherwise the tag of the specific filter to send
    """
    global agents, filters

    lock.acquire()
    try:
        for filt in filters:
            if tag:
                filt = tag
            for x in range(0, len(agents)):
                log.debug("Agent -- " + agents[x].__str__())
                if agents[x] and filters[filt].isUsed(agents[x].getName()):
                    # try:
                    dump = {'code': filt, 'filter': filters[filt].getInfo()}
                    body = util.encode(json.dumps(dump), agents[x].getKey())  # Encode the body
                    util.send_post(agents[x].getAddress() + '/filters', body, log)  # Send the body
                    # except:
                    #     log.warning("Agent at " + agents[x].getAddress() + " is no longer alive.")
                    #     agents[x].setStatus(False)
            if tag:
                break
    finally:
        lock.release()


def send_post(path, args, log):
    """
    Send a given body to each agent at the given path.

    Encodes each body with the agent's corresponding secret
    key before sending

    @type   path:   string
    @param  path:   The path to send the body to
    @type   args:   JSON parsable object (dict, list, string, etc)
    @param  args:   Body to be encoded and sent
    @type   log:    logger
    @param  log:    Logger object for logging
    """
    global agents

    lock.acquire()
    try:
        for x in range(0, len(agents)):
            log.debug("Agent -- " + agents[x].__str__())
            if agents[x]:
                try:
                    body = util.encode(args, agents[x].getKey())  # Encode the body
                    util.send_post(agents[x].getAddress() + path, body, log)  # Send the body
                except:
                    log.warning("Agent at " + agents[x].getName() + " is no longer alive.")
                    agents[x].setStatus(False)
    finally:
        lock.release()


def fromDB(db_params, full):
    """Load information from Database."""
    try:
        return communicator.fromDB(db_params, full)
    except:
        # Log the error
        error = 'Failure: ' + str(sys.exc_info()[0])
        log.critical(error)
        exc_type, exc_value, exc_traceback = sys.exc_info()
        lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
        tracebk = ''.join('!! ' + line for line in lines)
        log.critical(tracebk)
        util.sendEmail(receivers, "[copycat] CRITICAL -- communicator.py", email_sender, emailer.getEmailBody(
            error + "\n" + tracebk
        ))
        # Exit
        raise SystemExit(1)


def test():
    """
    Test any new changes to the DNSMasq conf files.

    If an error is thrown - the test failed - then the error is logged
    and the master exits.
    """
    try:
        # Executes the shell command to test the DNSMasq conf files.
        util.execute("dnsmasq --test")
        log.debug("Config file test passed.")
        util.execute("systemctl restart dnsmasq")
        log.debug("Restarting DNSMasq")
        util.execute("systemctl is-active dnsmasq")
        log.debug("DNSMasq restarted.")

        for record in test_records:
            cmd = "dig @localhost " + record + " -p " + dnsmasq_port + " +short"
            log.debug("Executing: " + cmd)
            start = time.time()
            ret = util.execute(cmd)
            end = time.time()
            passed = end - start
            log.debug("Returned: \n" + ret.strip())
            log.debug("Processed in " + str(passed) + " seconds.")
            if ret == "":
                raise RuntimeError("Dig at %r failed: No result" % (record))
            if passed > 2:
                raise RuntimeError("Dig at %r failed: Long return time" % (record))
    except:
        # Log the error
        error = 'Failure: ' + str(sys.exc_info()[0])
        log.critical(error)
        exc_type, exc_value, exc_traceback = sys.exc_info()
        lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
        tracebk = ''.join('!! ' + line for line in lines)
        log.critical(tracebk)
        try:
            fl = re.match('.*?(/.*)\'$', lines[len(lines)-1]).group(1)
            lineNumber = int(re.match('.*?line ([0-9]+) of', lines[len(lines)-1]).group(1))
            line = communicator.getLineFromFile(lineNumber-1, fl)
            fl_info = fl + " at line " + str(lineNumber) + ":\n\t" + line
            log.critical(fl_info)
        except:
            fl_info = ""
        util.sendEmail(receivers, "[copycat] CRITICAL -- copycat-master.py", email_sender, emailer.getEmailBody(
            error + "\n" + tracebk + "\n\n" + fl_info
        ))
        # Exit
        raise SystemExit(1)


def sendUpdates():
    """
    Check the database for changes and sends all changes to each agent.

    Also updates the global master dict with up to date data.
    """
    # Get the lastest data
    add_list = communicator.fromDBadds(db_params, log)
    delete_list = communicator.fromDBdeletes(db_params, log)

    changed = False
    if delete_list['ns_records']:
        communicator.logSet(delete_list['ns_records'], log, "- ")
        communicator.deleteFromFile(delete_list['ns_records'], ns_file, log)  # Make changes locally
        test()  # Test changes
        # If successful, send changes
        send_post('/ns/delete', json.dumps(toJSON({'ns_records': delete_list['ns_records']})), log)
        changed = True
    if delete_list['a_records']:
        communicator.logSet(delete_list['a_records'], log, "- ")
        communicator.deleteFromFile(delete_list['a_records'], a_file, log)  # Make changes locally
        test()  # Test changes
        # If successful, send changes
        send_post('/a/delete', json.dumps(toJSON({'a_records': delete_list['a_records']})), log)
        changed = True
    if delete_list['ptr_records']:
        communicator.logSet(delete_list['ptr_records'], log, "- ")
        communicator.deleteFromFile(delete_list['ptr_records'], ptr_file, log)  # Make changes locally
        test()  # Test changes
        # If successful, send changes
        send_post('/ptr/delete', json.dumps(toJSON({'ptr_records': delete_list['ptr_records']})), log)
        changed = True
    if add_list['ns_records']:
        communicator.logSet(add_list['ns_records'], log, "+ ")
        communicator.addToFile(add_list['ns_records'], ns_file, {}, log)  # Make changes locally
        test()  # Test changes
        # If successful, send changes
        send_post('/ns/add', json.dumps(toJSON({'ns_records': add_list['ns_records']})), log)
        changed = True
    if add_list['a_records']:
        communicator.logSet(add_list['a_records'], log, "+ ")
        communicator.addToFile(add_list['a_records'], a_file, {}, log)  # Make changes locally
        test()  # Test changes
        # If successful, send changes
        send_post('/a/add', json.dumps(toJSON({'a_records': add_list['a_records']})), log)
        changed = True
    if add_list['ptr_records']:
        communicator.logSet(add_list['ptr_records'], log, "+ ")
        communicator.addToFile(add_list['ptr_records'], ptr_file, {}, log)  # Make changes locally
        test()  # Test changes
        # If successful, send changes
        send_post('/ptr/add', json.dumps(toJSON({'ptr_records': add_list['ptr_records']})), log)
        changed = True

    # If changes were made, send the DNSMasq reload command to each agent.
    if changed:
        log.info("Updates sent. Reloading agents.")
        send_post('/reload', '[]', log)


def shutdown(sigNum, frame):
    """Shutdown."""
    print ""  # Newline for visual clarity in console
    if log is not None:
        log.info('Shutdown has been initiated. Shutting down.')
    raise SystemExit(0)


if __name__ == '__main__':
    """
    main:
        - Initializes global variables (master, agent)
        - Loads all config settings from configFile
        - Initializes the logger
        - Starts the statusCheck and handshake threads
        - Reads all records from DB into conf files
        - Test all records
        - Sends all records to each agent
        - Starts the local server thread
        - Checks for updates every pollInterval
    """
    global master, agents, filters

    installPath = dirname(realpath(__file__))
    configFilePath = join(installPath, configFile)

    if not isfile(configFilePath):
        print 'CRITICAL: The ' + configFile + ' file is missing. It should be in ' + installPath + '/'
        exit(1)
    cfg = SafeConfigParser()
    cfg.read(configFilePath)

    # Read in config settings to gloabl variables
    section = 'Logging'
    completeLog = cfg.get(section, 'completeLog')
    errorLog = cfg.get(section, 'errorLog')
    logToConsole = cfg.getboolean(section, 'logToConsole')
    cfgLogLevel = cfg.get(section, 'cfgLogLevel')
    log_max_size = cfg.getint(section, 'log_max_size')
    log_max_backup = cfg.getint(section, 'log_max_backup')

    section = 'Settings'
    serverIP = cfg.get(section, 'serverIP')
    port = cfg.getint(section, 'port')
    shakeInterval = cfg.getint(section, 'handshake')
    checkInterval = cfg.getint(section, 'statusCheck')
    pollInterval = cfg.getint(section, 'poll')
    filters = {}
    json_fl = join(installPath, cfg.get(section, 'content'))
    json_from_fl = json.load(open(json_fl))
    for filt in json_from_fl['filters']:
        filters[filt] = Filter(json_from_fl['filters'][filt])
    agents = []
    for agent in json_from_fl['agents']:
        agents.append(Agent(agent['addr'], agent['name']))

    section = 'Email Settings'
    email_sender = cfg.get(section, 'from')
    receivers = cfg.get(section, 'receivers').split(',')

    section = 'Database'
    host = cfg.get(section, 'host')
    db_port = cfg.getint(section, 'port')
    user = cfg.get(section, 'user')
    password = cfg.get(section, 'password')
    db = cfg.get(section, 'db')

    # DB info
    db_params = {
        'host': host,
        'port': db_port,
        'user': user,
        'password': password,
        'db': db
    }

    section = 'DNSMasq'
    dnsmasq_port = cfg.get(section, 'dnsmasq_port')
    dnsmasq = cfg.get(section, 'dnsmasq')
    ns_file = join(dnsmasq, cfg.get(section, 'ns_file'))
    a_file = join(dnsmasq, cfg.get(section, 'a_file'))
    ptr_file = join(dnsmasq, cfg.get(section, 'ptr_file'))
    test_records = cfg.get(section, 'test_records').split(",")

    # Add handler to system terminate signal
    signal(SIGINT, shutdown)
    signal(SIGHUP, shutdown)
    signal(SIGTERM, shutdown)

    """----- Logging Configuration ------
    Logging Levels:
        logging.CRITICAL
        logging.WARNING
        logging.INFO
        logging.DEBUG
    """

    # Logger
    if cfgLogLevel == 'critical':
        logLevel = logging.CRITICAL
    elif cfgLogLevel == 'error':
        logLevel = logging.ERROR
    elif cfgLogLevel == 'warning':
        logLevel = logging.WARNING
    elif cfgLogLevel == 'debug':
        logLevel = logging.DEBUG
    else:
        logLevel = logging.INFO

    # Name of log file
    installPath = dirname(realpath(__file__))
    logFile = join(installPath, 'log', completeLog + '.log')
    errFile = join(installPath, 'log', errorLog + '.log')
    if not isdir(join(installPath, 'log')):
        mkdir(join(installPath, 'log'))

    # Log size in Bytes
    # logSize = 1048576
    # Number of log files to keep
    # logBackupCount = 5
    # Text prior to message...which is a timestamp in this case.
    logFormat = '[%(asctime)s] - %(levelname)s - %(message)s'
    """-------------------------------"""

    log = logging.getLogger('copycat-master')
    log.setLevel(logLevel)

    # Create custom handler to manage rotating logs and auto log cleanup
    mainHandler = logging.handlers.RotatingFileHandler(logFile, maxBytes=log_max_size, backupCount=log_max_backup)
    mainHandler.setFormatter(logging.Formatter(logFormat))

    # Create custom handler for the errors only
    errHandler = logging.handlers.RotatingFileHandler(errFile, maxBytes=log_max_size, backupCount=log_max_backup)
    errHandler.setFormatter(logging.Formatter(logFormat))
    errHandler.setLevel(logging.ERROR)

    # Create stream handler for logging to the console
    if logToConsole:
        stdHandler = logging.StreamHandler()
        stdHandler.setFormatter(logging.Formatter(logFormat))
        stdHandler.setLevel(logLevel)
        log.addHandler(stdHandler)

    # Add handlers to log instance
    log.addHandler(mainHandler)
    log.addHandler(errHandler)

    log.info("Initializing with " + configFile + " and DB '" + db_params['db'] + "'")

    # Read all records and write them to the corresponding conf files
    communicator.dbToFile(db_params, ns_file, a_file, ptr_file, log)
    test()  # Test all records

    # Start thread to check agent status
    statusCheck()

    # Start thread to re-initialize secret key every given number of minutes
    handshake()

    # Send initial DB dump to each agent
    send_init(log)
    # master = fromDB(db_params, False)
    log.info("Finished.")

    try:
        # Start server on thread
        reactor.listenTCP(port, server.Site(HelloResource()))
        serve = Thread(target=reactor.run, args=(False,))
        serve.daemon = True
        serve.start()
        log.info("Server started on port " + str(port))
    except:
        log.critical("Could not start home server.")

    while True:
        try:
            # Every pollInterval updates are checked for and sent to agents
            sleep(pollInterval)
            log.debug("Sending updates")
            sendUpdates()
            log.debug("Updates sent")
        except urllib2.URLError:
            log.warning("Could not connect to agent " + agent)
        except SystemExit:
            exit(0)
        except:
            error = 'Failure: ' + str(sys.exc_info()[0])
            log.critical(error)
            exc_type, exc_value, exc_traceback = sys.exc_info()
            lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
            error = ''.join('!! ' + line for line in lines)
            log.critical(error)
            continue
